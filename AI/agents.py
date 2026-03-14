import os
import time
import requests
from loguru import logger

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GEMINI_MODEL = "gemini-2.0-flash"

# ===== 会社コンテキスト（会長の構想・常時参照）=====
COMPANY_CTX = (
    "【会長のビジョンと会社構想】"
    "会長が経営するホールディングス会社。Phase 7完全自律経営を目指す。"
    "【Kindleを起点とした全体戦略】"
    "Kindleは単純収益ではなく検索ツール・入口として機能させる。"
    "99円書籍で大量出版し検索の網を増やす。書籍→NOTE誘導→NOTEから書籍誘導の循環を作る。"
    "この自動化の仕組み自体をNOTEで販売。さらにYouTube/SNSへ展開する。"
    "将来は様々なジャンルの横展開を目指す出版社モデル。複数名義で多ジャンル展開。"
    "田中ザ・ワールド名義でビジネス系Kindle執筆中（既刊2冊、カバー待ち9冊）。"
    "【将来の実業（開発待機中）】"
    "人材派遣、電気工事、SIM事業、オリパ販売（KAMUI）、外国人求人サイト。"
    "実業とコンテンツのシナジーを活用する。"
    "【インフラ】Dify、LINE Bot、GitHub、Supabase、Vercel、Render、Claude API、Gemini API。"
    "月間運営コスト：約3万円。現在Phase 2（Kindle自動化）着手中。"
)

BASE = (
    "あなたは会社の役員。雑談・挨拶禁止。150字以内のチャット形式で発言せよ。"
    "肯定だけはするな。根拠を持って反論・質問・提案をすること。"
)

STYLES = {
    "sanbo": (
        "あなたは【ジェミちゃん】。思考：マクロ視点・リスク先出し型。"
        "市場・法規制・競合動向を踏まえリスクを先に指摘してから好機を語れ。"
        "会長の構想の盲点を積極的に指摘せよ。"
    ),
    "tech": (
        "あなたは【テック君】。思考：懐疑的・コスト現実主義型。"
        "本当に実現できるか・コストに見合うかを常に問え。"
        "Dify/Claude API/GitHub/Renderなど会社のスタックを熟知した前提で発言せよ。"
    ),
    "content": (
        "あなたは【カリスマ】。思考：ユーザー視点・売れるか最優先型。"
        "誰が買うのか・なぜ買うのかを常に問え。"
        "Kindle→NOTE→YouTube→SNSの循環戦略の収益実現可能性を評価せよ。"
    ),
    "sns": (
        "あなたは【映え子さん】。思考：スピード重視・今すぐできるか型。"
        "今月できるか・最速で結果が出る順番かを基準に切れ。"
    ),
    "ceo": (
        "あなたは【ボブ】。思考：最終判断・無駄切り捨て型。"
        "全員の議論を聞いた上で会長が承認すべき唯一の結論を出せ。"
        "会長から説明・宣言・報告を受けた場合は内容を要約して了解した旨を端的に返せ。"
        "わからないことを聞かれたら中学生でも分かるように説明せよ。"
        "YES/NOで答えられる形で締めよ。"
    ),
}

MENTION_MAP = [
    ("テック君", "tech"), ("テック", "tech"), ("tech", "tech"),
    ("開発部長", "tech"), ("開発さん", "tech"), ("開発は", "tech"),
    ("ジェミちゃん", "sanbo"), ("ジェミ", "sanbo"), ("参謀", "sanbo"),
    ("カリスマ", "content"), ("コンテンツ部長", "content"),
    ("映え子さん", "sns"), ("映え子", "sns"), ("映え", "sns"),
    ("ボブ", "ceo"), ("bob", "ceo"), ("ceo", "ceo"), ("社長", "ceo"),
    ("各位", "ceo"),
]


def _call_claude(system, user, max_tokens=500):
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key: return "[API Key Missing]"
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": CLAUDE_MODEL, "max_tokens": max_tokens,
                  "system": system, "messages": [{"role": "user", "content": user}]},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Claude Error: {e}")
        return "[通信エラー]"


def _call_gemini(system, user):
    time.sleep(3)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key: return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
        r = requests.post(url,
            json={"system_instruction": {"parts": [{"text": system}]},
                  "contents": [{"parts": [{"text": user}]}],
                  "generationConfig": {"maxOutputTokens": 500}},
            timeout=15)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except:
        return None


def detect_mention(text):
    lower = text.lower()
    for keyword, agent_id in MENTION_MAP:
        if keyword.lower() in lower:
            return agent_id
    return None


def is_declaration(text):
    """会長からの説明・宣言・報告かどうかを判定（長文かつ依頼形でない）"""
    if len(text) > 80:
        question_markers = ["ください", "ですか", "どう", "？", "?", "してほしい", "意見", "について"]
        for m in question_markers:
            if m in text:
                return False
        return True
    return False


def speak(agent_id, topic, context="", max_tokens=500):
    style = STYLES[agent_id]
    prompt = f"{COMPANY_CTX}\n{BASE}\n{style}"
    user = f"議題: {topic}"
    if context:
        user += f"\n\nここまでの議論:\n{context}"

    if agent_id == "sanbo":
        op = _call_gemini(prompt, user)
        if not op:
            op = _call_claude(prompt, user, max_tokens)
        name = "🔭 ジェミちゃん"
    elif agent_id == "tech":
        op = _call_claude(prompt, user, max_tokens)
        name = "⚙️ テック君"
    elif agent_id == "content":
        op = _call_claude(prompt, user, max_tokens)
        name = "✍️ カリスマ"
    elif agent_id == "sns":
        op = _call_claude(prompt, user, max_tokens)
        name = "🎬 映え子さん"
    else:
        op = _call_claude(prompt, user, 600)
        name = "👑 ボブ"
    return (name, op)


class AgentRouter:

    def council(self, topic):
        # 各位宛て or 説明・宣言はボブが単独で受け取る
        target = detect_mention(topic)
        if target:
            return [speak(target, topic)]

        if is_declaration(topic):
            return [speak("ceo", topic)]

        # B案：全員議論ループ（各発言が前の全発言を文脈として受け取る）
        results = []
        context = ""
        for agent_id in ["sanbo", "tech", "content", "sns"]:
            name, op = speak(agent_id, topic, context)
            results.append((name, op))
            context += f"\n{name}: {op}"

        name, op = speak("ceo", topic, context, max_tokens=600)
        results.append((name, op))

        # ボブがテック君に質問していたら自動返答
        if "テック" in op:
            tech_prompt = f"{COMPANY_CTX}\n{BASE}\n{STYLES['tech']} ボブCEOから質問。YES/NOで即答してから理由を一言。"
            tech_reply = _call_claude(tech_prompt, op, 300)
            results.append(("⚙️ テック君（返答）", tech_reply))

        return results
