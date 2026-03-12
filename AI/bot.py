"""
src/line_gateway/bot.py
LINE Messaging API Webhook サーバ（Flask）
ユーザーの返信を受けて承認フローを更新する
"""
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    ReplyMessageRequest, TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from loguru import logger

from config.settings import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from src.line_gateway.approval import ApprovalManager

app = Flask(__name__)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
approval_mgr = ApprovalManager()


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning("[Bot] 無効な署名")
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    """ユーザーの返信を受け取り承認処理を行う"""
    text = event.message.text
    reply_token = event.reply_token

    config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    with ApiClient(config) as api_client:
        messaging = MessagingApi(api_client)

        # 承認ワード判定
        status = approval_mgr.handle_reply(text)

        if status == "approved":
            reply = "✅ 承認しました。実行を開始します。"
            logger.info("[Bot] 承認受信")
        elif status == "rejected":
            reply = "❌ キャンセルしました。"
            logger.info("[Bot] 拒否受信")
        elif status == "held":
            reply = "⏸ 保留にしました。後ほど確認してください。"
            logger.info("[Bot] 保留受信")
        else:
            # 通常の会話 or コマンド
            reply = _handle_command(text)

        messaging.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(type="text", text=reply)],
            )
        )


def _handle_command(text: str) -> str:
    """承認以外のコマンドを処理する"""
    cmd = text.strip().lower()

    if cmd in ("状況", "status", "report"):
        from src.line_gateway.reporter import MorningReporter
        reporter = MorningReporter()
        return reporter.build_report()

    elif cmd.startswith("リサーチ"):
        topic = text.replace("リサーチ", "").strip()
        if topic:
            return f"🔍 「{topic}」のリサーチを開始します...\n結果は後ほど報告します。"
        return "リサーチするテーマを指定してください。例: リサーチ 占い"

    elif cmd in ("ヘルプ", "help", "?"):
        return (
            "📋 使えるコマンド:\n"
            "・承認 — 直前の承認リクエストを承認\n"
            "・キャンセル — 承認リクエストをキャンセル\n"
            "・保留 — 後で決める\n"
            "・状況 — 全事業の状況を表示\n"
            "・リサーチ [テーマ] — リサーチを実行\n"
            "・ヘルプ — このメッセージ"
        )

    return f"受け取りました: 「{text}」\nコマンド一覧は「ヘルプ」と送ってください。"


if __name__ == "__main__":
    logger.info("[Bot] LINE Bot サーバ起動 Port=5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
