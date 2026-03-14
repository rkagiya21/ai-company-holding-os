"""AI/bot.py Phase 8 LINE Bot - スマート指名モード対応版"""
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    ReplyMessageRequest, PushMessageRequest, TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from loguru import logger
from settings import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from agents import AgentRouter
from memory import save_message, get_history, format_history_for_prompt, save_approval

app = Flask(__name__)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
router = AgentRouter()
_user_mode = {}


def get_mode(user_id):
    return _user_mode.get(user_id, "ceo")


def set_mode(user_id, mode):
    _user_mode[user_id] = mode


def push_text(user_id, text):
    """Push APIで1通送信"""
    config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    with ApiClient(config) as api_client:
        MessagingApi(api_client).push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(type="text", text=text[:2000])],
            )
        )


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
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    save_message(user_id, "user", text, get_mode(user_id))

    mode = get_mode(user_id)
    lower = text.lower()

    # モード切り替え
    if lower in ("経営モード", "ceo", "経営"):
        set_mode(user_id, "ceo")
        reply = "👔 【経営モード】に切り替えました\n\nAI CEOが対応します。\n・状況 — 事業レポート\n・承認 / キャンセル / 保留\n\n「戦略」で戦略ルームへ。"
        _reply_once(reply_token, reply)
        return

    if lower in ("戦略ルームモード", "戦略ルーム", "戦略", "strategy"):
        set_mode(user_id, "strategy")
        reply = (
            "🏛️ 【戦略ルームモード】\n\n"
            "参加メンバー:\n"
            "🔭 経営参謀（Gemini）\n"
            "⚙️ 開発事業部長\n"
            "✍️ コンテンツ事業部長\n"
            "🎬 SNS事業部長\n"
            "👑 AI CEO\n\n"
            "名指しOK例: 「開発さん、Kindleの進捗は？」\n"
            "全員会議: 「全員で議論して」\n"
            "「経営」で経営モードへ。"
        )
        _reply_once(reply_token, reply)
        return

    if lower in ("ヘルプ", "help"):
        mode_label = "👔 経営" if get_mode(user_id) == "ceo" else "🏛️ 戦略ルーム"
        reply = f"現在: {mode_label}\n\n「経営」「戦略」でモード切替\n名指し例: 「開発さん〇〇して」"
        _reply_once(reply_token, reply)
        return

    if get_mode(user_id) == "ceo":
        reply = _handle_ceo(user_id, text, lower)
        _reply_once(reply_token, reply)
        save_message(user_id, "assistant", reply, "ceo")
        return

    # 戦略ルームモード — Push APIで1人ずつ送信
    # まずreply_tokenで即座にACK
    _reply_once(reply_token, "🏛️ 議論中...")

    try:
        results = router.council(text)
        for name, opinion in results:
            msg = f"{name}\n{opinion}"
            push_text(user_id, msg)
            save_message(user_id, "assistant", msg, "strategy")
    except Exception as e:
        logger.error(f"[Bot] 戦略エラー: {e}")
        push_text(user_id, f"⚠️ エラー: {e}")


def _reply_once(reply_token, text):
    config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    with ApiClient(config) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(type="text", text=text[:2000])],
            )
        )


def _handle_ceo(user_id, text, lower):
    if lower in ("状況", "status", "report", "レポート"):
        try:
            from reporter import MorningReporter
            return MorningReporter().build_report()
        except Exception as e:
            return f"⚠️ レポートエラー: {e}"
    if lower in ("承認", "yes", "はい", "ok"):
        save_approval(user_id, "承認", text)
        return "✅ 承認しました。"
    if lower in ("キャンセル", "no", "いいえ"):
        save_approval(user_id, "キャンセル", text)
        return "❌ キャンセルしました。"
    if lower in ("保留", "later"):
        save_approval(user_id, "保留", text)
        return "⏸ 保留にしました。"
    return f"👔 AI CEO: 「{text}」受け取りました。\n承認/キャンセル/保留 または 状況 でコマンドを。"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
