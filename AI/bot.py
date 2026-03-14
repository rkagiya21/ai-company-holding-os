"""
AI/bot.py  Phase 8
LINE Messaging API Webhook サーバ（Flask）
- 経営モード  : AI CEO が売上・進捗・承認を管理
- 戦略ルームモード: 複数エージェントが合議して最終案を提出
- Supabase長期記憶: 会話・承認・指示を永続化
"""
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from loguru import logger

from settings import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from agents import AgentRouter
from memory import (
    save_message, get_history, format_history_for_prompt,
    save_approval, set_directive, get_directive,
)

app = Flask(__name__)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
router = AgentRouter()

_user_mode = {}

def get_mode(user_id):
    return _user_mode.get(user_id, "ceo")

def set_mode(user_id, mode):
    _user_mode[user_id] = mode

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
    mode = get_mode(user_id)

    save_message(user_id, "user", text, mode)

    reply = _process(user_id, text)

    save_message(user_id, "assistant", reply, get_mode(user_id))

    config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    with ApiClient(config) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(type="text", text=reply[:2000])],
            )
        )

def _process(user_id, text):
    lower = text.lower()

    if lower in ("経営モード", "ceo", "経営"):
        set_mode(user_id, "ceo")
        return (
            "👔 【経営モード】に切り替えました\n\n"
            "AI CEOが対応します。\n"
            "使えるコマンド:\n"
            "・状況 — 全事業レポート\n"
            "・承認 / キャンセル / 保留\n"
            "・ヘルプ\n\n"
            "戦略ルームへは「戦略」と送ってください。"
        )

    if lower in ("戦略ルームモード", "戦略ルーム", "戦略", "strategy"):
        set_mode(user_id, "strategy")
        return (
            "🏛️ 【戦略ルームモード】に切り替えました\n\n"
            "参加エージェント:\n"
            "① 参謀（Gemini）: 市場分析・トレンド\n"
            "② 制作（Claude）: コンテンツ生成\n"
            "③ 開発（Claude）: システム構築・改修\n"
            "④ Kindle担当: 電子書籍戦略\n"
            "⑤ NOTE担当: 記事・販売戦略\n"
            "⑥ YouTube/SNS担当: 動画・拡散戦略\n"
            "→ AI CEOが合議をまとめて最終案を提出\n\n"
            "テーマや相談を自由に入力してください。\n"
            "経営モードへは「経営」と送ってください。"
        )

    if lower in ("ヘルプ", "help", "?", "？"):
        mode = get_mode(user_id)
        mode_label = "👔 経営モード" if mode == "ceo" else "🏛️ 戦略ルームモード"
        return (
            f"📋 現在: {mode_label}\n\n"
            "【モード切り替え】\n"
            "・「経営」→ 経営モード\n"
            "・「戦略」→ 戦略ルームモード\n\n"
            "【経営モード コマンド】\n"
            "・状況 — 全事業レポート\n"
            "・承認 / キャンセル / 保留\n\n"
            "【戦略ルームモード】\n"
            "・テーマを自由に入力\n"
            "・エージェントが合議して最終案を提出"
        )

    mode = get_mode(user_id)
    if mode == "ceo":
        return _handle_ceo(user_id, text, lower)
    else:
        return _handle_strategy(text)

def _handle_ceo(user_id, text, lower):
    if lower in ("状況", "status", "report", "レポート"):
        try:
            from reporter import MorningReporter
            return MorningReporter().build_report()
        except Exception as e:
            return f"⚠️ レポート取得エラー: {e}"

    if lower in ("承認", "yes", "はい", "ok"):
        save_approval(user_id, "承認", text)
        return "✅ 承認しました。実行を開始します。"

    if lower in ("キャンセル", "no", "いいえ", "拒否"):
        save_approval(user_id, "キャンセル", text)
        return "❌ キャンセルしました。"

    if lower in ("保留", "later", "あとで"):
        save_approval(user_id, "保留", text)
        return "⏸ 保留にしました。後ほど確認してください。"

    history = get_history(user_id, limit=10)
    history_text = format_history_for_prompt(history)

    return (
        f"👔 AI CEO: 「{text}」を受け取りました。\n\n"
        "承認待ち案件があれば「承認」「キャンセル」「保留」で返答ください。\n"
        "全事業状況は「状況」で確認できます。"
    )

def _handle_strategy(text):
    try:
        return router.council(text)
    except Exception as e:
        logger.error(f"[Bot] 戦略ルームエラー: {e}")
        return f"⚠️ 戦略ルームでエラーが発生しました: {e}"

if __name__ == "__main__":
    logger.info("[Bot] LINE Bot サーバ起動 Port=8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
