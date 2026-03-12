"""
src/line_gateway/approval.py
LINE ゲートキーパー — 承認リクエスト送信・管理
"""
from __future__ import annotations
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    PushMessageRequest, TextMessage,
)
from loguru import logger

from config.settings import LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID
from config.prompts import APPROVAL_REQUEST_TEMPLATE
from src.aiceo.state import ApprovalRequest


class ApprovalManager:
    """LINE への承認リクエスト送受信を管理する"""

    def __init__(self):
        config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
        self._api_client = ApiClient(config)
        self._messaging = MessagingApi(self._api_client)
        self._pending: dict[str, ApprovalRequest] = {}

    def request(self, req: ApprovalRequest) -> None:
        """
        LINE へ承認リクエストを送信する。
        """
        # 金額・詳細を整形
        details_text = ""
        if req.details:
            for k, v in req.details.items():
                if k in ("priority_actions", "budget", "roi"):
                    details_text += f"  • {k}: {v}\n"

        message_text = APPROVAL_REQUEST_TEMPLATE.format(
            action_name=req.action,
            description=req.description,
            reason="AI CEOが戦略に基づき実行を提案",
            details=details_text or "（詳細なし）",
        )

        self._send_line_message(message_text)
        self._pending[req.id] = req
        logger.info(f"[Approval] リクエスト送信: {req.id} / {req.action}")

    def handle_reply(self, reply_text: str, request_id: str | None = None) -> str:
        """
        LINE からの返信を処理して承認状態を更新する。

        Returns:
            "approved" | "rejected" | "held" | "unknown"
        """
        text = reply_text.strip()

        if text in ("承認", "OK", "ok", "yes", "はい"):
            status = "approved"
        elif text in ("キャンセル", "拒否", "no", "NG", "ng"):
            status = "rejected"
        elif text in ("保留", "待って", "later"):
            status = "held"
        else:
            return "unknown"

        if request_id and request_id in self._pending:
            self._pending[request_id].status = status

        logger.info(f"[Approval] 返信処理: {status}")
        return status

    def _send_line_message(self, text: str) -> None:
        """LINE Push メッセージを送信する"""
        if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
            logger.warning("[LINE] トークンまたはユーザーIDが未設定 — コンソール出力にフォールバック")
            print(f"\n{'='*50}\n[LINE Mock] メッセージ:\n{text}\n{'='*50}\n")
            return

        try:
            self._messaging.push_message(
                PushMessageRequest(
                    to=LINE_USER_ID,
                    messages=[TextMessage(type="text", text=text[:2000])],
                )
            )
            logger.success("[LINE] メッセージ送信完了")
        except Exception as e:
            logger.error(f"[LINE] 送信エラー: {e}")
            raise
