"""AI/bot.py - 議題記憶+思考スタイルB案対応版"""
import time
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
from memory import save_message, save_approval

app = Flask(__name__)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
router = AgentRouter()
_user_mode = {}
_last_topic = {}  # ユーザーごとの最後の議題を記憶

# 短い・曖昧なメッセージのパターン
FOLLOWUP_PATTERNS = [
    "どうですか", "どう思う", "どうでしょう", "意見は",
    "続けて", "もっと", "他には", "次は", "それで",
    "そうですね", "なるほど", "進めて", "やって",
]


def get_mode(user_id):
    return _user_mode.get(user_id, "ceo")

def set_mode(user_id, mode):
    _user_mode[user_id] = mode

def push_text(user_id, text):
    try:
        config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
        with ApiClient(config) as api_client:
            MessagingApi(api_client).push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(type="text", text=str(text)[:2000])],
                )
            )
    except Exception as e:
        logger.error(f"[Push Error] {e}")

def _reply_once(reply_token, text):
    config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    with ApiClient(config) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(type="text", text=str(text)[:2000])],
            )
        )

def is_followup(text):
    """曖昧な継続メッセージかどうかを判定"""
    if len(text) < 15:  # 短いメッセージ
        return True
    for pat in FOLLOWUP_PATTERNS:
        if pat in text:
            return True
    return False

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
    lower = text.lower()

    save_message(user_id, "user", text, get_mode(user_id))

    # モード切り替え
    if lower in ("経営モード", "ceo", "経営"):
        set_mode(user_id, "ceo")
        _reply_once(reply_token, "👔 【経営モード】に切り替えました\n\n「戦略」で戦略ルームへ。")
        return

    if lower in ("戦略ルームモード", "戦略ルーム", "戦略", "strategy"):
        set_mode(user_id, "strategy")
        _last_topic[user_id] = ""  # 議題リセット
        reply = (
            "🏛️ 【戦略ルームモード】\n\n"
            "メンバー:\n"
            "🔭 ジェミちゃん（参謀）\n"
            "⚙️ テック君（開発）\n"
            "✍️ カリスマ（コンテンツ）\n"
            "🎬 映え子さん（SNS）\n"
            "👑 ボブ（CEO）\n\n"
            "名指しOK: 「テック君、〇〇して」\n"
            "全員会議: そのまま議題を投げる\n"
            "「経営」で経営モードへ。"
        )
        _reply_once(reply_token, reply)
        return

    if lower in ("ヘルプ", "help"):
        mode_label = "👔 経営" if get_mode(user_id) == "ceo" else "🏛️ 戦略ルーム"
        _reply_once(reply_token, f"現在: {mode_label}\n\n「経営」「戦略」でモード切替")
        return

    if get_mode(user_id) == "ceo":
        reply = _handle_ceo(user_id, text, lower)
        _reply_once(reply_token, reply)
        save_message(user_id, "assistant", reply, "ceo")
        return

    # 戦略ルームモード
    # フォローアップメッセージなら前の議題を引き継ぐ
    last = _last_topic.get(user_id, "")
    if is_followup(text) and last:
        topic = f"{last}\n\n（追加指示: {text}）"
    else:
        topic = text
        _last_topic[user_id] = text  # 新しい議題を記憶

    _reply_once(reply_token, "🏛️ 議論中...")

    try:
        results = router.council(topic)
        for name, opinion in results:
            msg = f"{name}\n{opinion}"
            push_text(user_id, msg)
            save_message(user_id, "assistant", msg, "strategy")
            time.sleep(0.3)
    except Exception as e:
        logger.error(f"[Bot] 戦略エラー: {e}")
        push_text(user_id, f"⚠️ エラー: {e}")

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
