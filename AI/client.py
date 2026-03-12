"""
src/dify_connector/client.py
Dify REST API クライアント
各 WF を API 経由でキックし、結果を受け取る
"""
from __future__ import annotations
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import DIFY_BASE_URL, DIFY_WORKFLOWS


class DifyClient:
    """Dify API ラッパー"""

    def __init__(self):
        self.base_url = DIFY_BASE_URL
        self.workflows = DIFY_WORKFLOWS

    def _get_api_key(self, workflow_key: str) -> str:
        key = self.workflows.get(workflow_key, "")
        if not key:
            raise ValueError(f"Dify WF キーが未設定: {workflow_key}")
        return key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def run_workflow(
        self,
        workflow_key: str,
        inputs: dict,
        user: str = "ai-ceo",
        blocking: bool = True,
    ) -> dict:
        """
        Dify ワークフローを実行する。

        Args:
            workflow_key: "kindle" | "note" | "research" | "kamui"（HOLD中）
            inputs: WFへの入力パラメータ
            user: 実行ユーザー識別子
            blocking: True=同期実行 / False=非同期

        Returns:
            {"success": bool, "output": dict, "error": str}
        """
        # KAMUI は HOLD 中 — 安全チェック
        if workflow_key == "kamui":
            logger.warning("[Dify] KAMUI WF は現在 HOLD 中。スキップします。")
            return {"success": False, "error": "KAMUI WF は HOLD 中", "skipped": True}

        try:
            api_key = self._get_api_key(workflow_key)
        except ValueError as e:
            # APIキー未設定 → 開発時は mock 結果を返す
            logger.warning(f"[Dify] {e} — モック結果を返します")
            return self._mock_result(workflow_key, inputs)

        mode = "blocking" if blocking else "streaming"
        url = f"{self.base_url}/workflows/run"

        payload = {
            "inputs": inputs,
            "response_mode": mode,
            "user": user,
        }

        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            output = data.get("data", {}).get("outputs", {})
            status = data.get("data", {}).get("status", "")

            logger.success(f"[Dify] WF完了: {workflow_key} / status={status}")
            return {"success": status == "succeeded", "output": output, "raw": data}

        except httpx.HTTPStatusError as e:
            logger.error(f"[Dify] HTTP エラー: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"[Dify] 予期せぬエラー: {e}")
            raise

    def _mock_result(self, workflow_key: str, inputs: dict) -> dict:
        """APIキー未設定時の開発用モック"""
        mocks = {
            "research": {
                "success": True,
                "output": {
                    "market_size": "モック: 調査中",
                    "competitors": ["competitor_a", "competitor_b"],
                    "trends": ["トレンド1", "トレンド2", "トレンド3"],
                    "opportunities": ["機会1", "機会2"],
                    "risks": ["リスク1"],
                    "recommended_channels": ["X", "Instagram", "NOTE"],
                    "estimated_monthly_revenue": {"low": 30000, "mid": 100000, "high": 500000},
                    "time_to_launch": "2-4週間",
                },
                "mock": True,
            },
            "kindle": {
                "success": True,
                "output": {"draft_url": "https://drive.google.com/mock", "chapters": 6},
                "mock": True,
            },
            "note": {
                "success": True,
                "output": {"articles": ["記事1", "記事2", "記事3"]},
                "mock": True,
            },
        }
        return mocks.get(workflow_key, {"success": False, "error": "unknown workflow", "mock": True})
