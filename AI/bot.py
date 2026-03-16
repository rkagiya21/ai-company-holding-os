"""AI/bot.py - 議題記憶+Kindle自動化対応版"""
import os
import time
import threading
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
_last_topic = {}

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
    if len(text) < 15:
        return True
    for pat in FOLLOWUP_PATTERNS:
        if pat in text:
            return True
    return False


def _run_kindle(user_id, theme):
    import requests as req
    DIFY_KEY = os.getenv("DIFY_KINDLE_WF_KEY", "").strip()
    if not DIFY_KEY:
        push_text(user_id, "❌ DIFY_KINDLE_WF_KEY が未設定です")
        return
    try:
        logger.info(f"[Kindle] テーマ: {theme}")
        r = req.post(
            "https://api.dify.ai/v1/workflows/run",
            headers={"Authorization": f"Bearer {DIFY_KEY}", "Content-Type": "application/json"},
            json={
                "inputs": {"book_title": theme},
                "response_mode": "blocking",
                "user": user_id
            },
            timeout=300
        )
        data = r.json()
        outputs = data.get("data", {}).get("outputs", {})
        drive_url = outputs.get("drive_url", "")
        if drive_url:
            msg = f"✅ Kindle原稿完成！\n\nテーマ: {theme}\n\n📄 Googleドライブ:\n{drive_url}\n\nKDPに登録しますか？ YES/NO"
        else:
            msg = f"✅ Kindle生成完了！\n\nテーマ: {theme}\n\n出力: {str(outputs)[:500]}"
        push_text(user_id, msg)
    except Exception as e:
        logger.error(f"[Kindle Error] {e}")
        push_text(user_id, f"❌ Kindleエラー: {e}")


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

    if lower in ("経営モード", "ceo", "経営"):
        set_mode(user_id, "ceo")
        _reply_once(reply_token, "👔 【経営モード】に切り替えました\n\n「戦略」で戦略ルームへ。")
        return

    if lower in ("戦略ルームモード", "戦略ルーム", "戦略", "strategy"):
        set_mode(user_id, "strategy")
        _last_topic[user_id] = ""
        reply = (
            "🏛️ 【戦略ルームモード】\n\n"
            "メンバー:\n"
            "🔭 ジェミちゃん（参謀）\n"
            "⚙️ テック君（開発）\n"
            "✍️ カリスマ（コンテンツ）\n"
            "🎬 映え子さん（SNS）\n"
            "👑 ボブ（CEO）\n\n"
            "名指しOK: 「テック君、〇〇して」\n"
            "Kindleコマンド: 「kindle テーマ名」\n"
            "全員会議: そのまま議題を投げる\n"
            "「経営」で経営モードへ。"
        )
        _reply_once(reply_token, reply)
        return

    if lower in ("ヘルプ", "help"):
        mode_label = "👔 経営" if get_mode(user_id) == "ceo" else "🏛️ 戦略ルーム"
        _reply_once(reply_token, f"現在: {mode_label}\n\n「経営」「戦略」でモード切替\nKindleコマンド: 「kindle テーマ名」")
        return

    # Kindleコマンド（どのモードでも動作）
    if lower.startswith("kindle"):
        theme = text[6:].strip()
        if not theme:
            _reply_once(reply_token, "📚 使い方: 「kindle テーマ名」\n例: kindle AI副業入門")
            return
        _reply_once(reply_token, f"📚 Kindle生成を開始します\n\nテーマ: {theme}\n\n3〜5分お待ちください...")
        threading.Thread(target=_run_kindle, args=(user_id, theme), daemon=True).start()
        return

    if get_mode(user_id) == "ceo":
        reply = _handle_ceo(user_id, text, lower)
        _reply_once(reply_token, reply)
        save_message(user_id, "assistant", reply, "ceo")
        return

    last = _last_topic.get(user_id, "")
    if is_followup(text) and last:
        topic = f"{last}\n\n（追加指示: {text}）"
    else:
        topic = text
        _last_topic[user_id] = text

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
