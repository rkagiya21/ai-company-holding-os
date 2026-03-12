"""
src/workflows/research.py
新規事業リサーチ ワークフロー

対象:
  - 占い事業
  - 外国人向け求人プラットフォーム
  - その他 AI CEO が自律立案するテーマ
"""
from __future__ import annotations
import json
from loguru import logger
from langchain_openai import ChatOpenAI

from config.settings import LLM_MODEL_HEAVY
from config.prompts import RESEARCH_PROMPT, STRATEGY_PROMPT
from src.dify_connector.client import DifyClient


# ── 事前定義リサーチ対象 ────────────────────────────────────
RESEARCH_TARGETS = {
    "uranai": {
        "topic": "占い・スピリチュアル系コンテンツ事業（日本）",
        "keywords": ["占い", "タロット", "スピリチュアル", "四柱推命", "占星術"],
        "channels": ["Instagram", "TikTok", "LINE占い", "有料鑑定"],
        "monetize": ["有料鑑定", "NOTE有料記事", "Kindle", "会員制"],
    },
    "foreign_jobs": {
        "topic": "外国人向け求人プラットフォーム（日本在住外国人向け）",
        "keywords": ["外国人 求人", "日本 外国人 仕事", "在日外国人 転職", "多言語 採用"],
        "channels": ["Google広告", "外国人コミュニティSNS", "企業向け営業"],
        "monetize": ["成功報酬型採用", "掲載料", "プレミアム会員"],
    },
}


class ResearchWorkflow:
    """新規事業リサーチを実行するクラス"""

    def __init__(self):
        self.dify = DifyClient()
        self.llm = ChatOpenAI(model=LLM_MODEL_HEAVY, temperature=0.3)

    def run(self, target_key: str | None = None, custom_topic: str | None = None) -> dict:
        """
        リサーチを実行する。

        Args:
            target_key:   "uranai" | "foreign_jobs" | None
            custom_topic: カスタムテーマ（target_key が None の場合）

        Returns:
            リサーチ結果 + 戦略提案
        """
        if target_key and target_key in RESEARCH_TARGETS:
            config = RESEARCH_TARGETS[target_key]
            topic = config["topic"]
        elif custom_topic:
            topic = custom_topic
            config = {}
        else:
            raise ValueError("target_key または custom_topic を指定してください")

        logger.info(f"[Research] 開始: {topic}")

        # Step 1: Dify リサーチWFを試みる（設定済みなら）
        dify_result = self.dify.run_workflow(
            workflow_key="research",
            inputs={"topic": topic, "keywords": config.get("keywords", [])},
        )

        if dify_result.get("success") and not dify_result.get("mock"):
            research_data = dify_result["output"]
            logger.info("[Research] Dify から結果取得")
        else:
            # LLM で直接リサーチ
            logger.info("[Research] LLM でリサーチ実行")
            research_data = self._llm_research(topic, config)

        # Step 2: 戦略立案
        strategy = self._build_strategy(topic, research_data, config)

        return {
            "topic": topic,
            "research": research_data,
            "strategy": strategy,
            "source": "dify" if dify_result.get("success") else "llm",
        }

    def _llm_research(self, topic: str, config: dict) -> dict:
        """LLM でリサーチを実行する"""
        prompt = RESEARCH_PROMPT.format(topic=topic)
        response = self.llm.invoke(prompt)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"raw": response.content, "parse_error": True}

    def _build_strategy(self, topic: str, research: dict, config: dict) -> dict:
        """リサーチ結果から戦略を立案する"""
        prompt = STRATEGY_PROMPT.format(
            research_result=json.dumps(research, ensure_ascii=False, indent=2)
        )
        response = self.llm.invoke(prompt)
        try:
            strategy = json.loads(response.content)
        except json.JSONDecodeError:
            strategy = {"raw": response.content, "parse_error": True}

        # 既存 Dify WF との接続ポイントを追加
        strategy["dify_integration"] = {
            "existing_wf": ["kindle", "note"],
            "new_wf_needed": config.get("channels", []),
            "automation_ready": ["コンテンツ生成", "SNS投稿"],
            "manual_required": ["有料鑑定対応", "企業営業"],
        }

        return strategy


# ── 便利関数 ────────────────────────────────────
def run_uranai_research() -> dict:
    """占い事業リサーチを実行する"""
    wf = ResearchWorkflow()
    return wf.run(target_key="uranai")


def run_foreign_jobs_research() -> dict:
    """外国人向け求人リサーチを実行する"""
    wf = ResearchWorkflow()
    return wf.run(target_key="foreign_jobs")
