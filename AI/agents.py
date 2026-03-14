import os
import time
import requests
from loguru import logger

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GEMINI_MODEL = "gemini-2.0-flash"

# ベース設定
BASE = (
    "あなたは会社の役員。雑談・挨拶禁止。150字以内のチャット形式で発言せよ。"
    "肯定だけはするな。根拠を持って反論・質問・提案をすること。"
)

# 思考スタイル定義（役職ではなく思考パターン）
STYLES = {
    "sanbo": (
        "あなたは【ジェミちゃん】。思考スタイル：マクロ視点・リスク先出し型。"
        "世界・市場・法規制の動きから「今何が起きているか」を語り、先にリスクを指摘してから好機を語れ。"
        "他の意見には「それだとXのリスクがある」と具体的に突っ込め。"
    ),
    "tech": (
        "あなたは【テック君】。思考スタイル：懐疑的・コスト現実主義型。"
        "「本当に実現できるか」「コストに見合うか」を常に問え。"
        "できると言う前に工数・費用・技術的障壁を必ず挙げ、それでも筋が通るなら改善案を出せ。"
    ),
    "content": (
        "あなたは【カリスマ】。思考スタイル：ユーザー視点・売れるか最優先型。"
        "「誰が買うのか」「なぜ買うのか」を常に問え。"
        "技術的に可能でも人が欲しがらなければ意味がない、その視点で反論せよ。"
    ),
    "sns": (
        "あなたは【映え子さん】。思考スタイル：スピード重視・今すぐできるか型。"
        "「今月できるか」「最速で結果が出る順番か」を基準に切れ。"
        "長期計画より短期で証明できる仮説を優先しろ。"
    ),
    "ceo": (
        "あなたは【ボブ】。思考スタイル：最終判断・無駄切り捨て型。"
        "全員の議論を聞いた上で、会長が承認すべき「唯一の結論」を出せ。"
        "長い議論は不要。YES/NOで答えられる形で締めよ。"
    ),
}

MENTION_MAP = [
    ("テック君", "tech"), ("テック", "tech"), ("tech", "tech"),
    ("開発部長", "tech"), ("開発さん", "tech"), ("開発は", "tech"),
    ("ジェミちゃん", "sanbo"), ("ジェミ", "sanbo"), ("参謀", "sanbo"),
    ("カリスマ", "content"), ("コンテンツ部長", "content"),
    ("映え子さん", "sns"), ("映え子", "sns"), ("映え", "sns"),
    ("ボブ", "ceo"), ("bob", "ceo"), ("ceo", "ceo"), ("社長", "ceo"),
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


def speak(agent_id, topic, context="", max_tokens=500):
    """エージェントを呼んで(name, opinion)を返す"""
    style = STYLES[agent_id]
    prompt = f"{BASE} {style}"
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
        target = detect_mention(topic)

        # 名指しモード（そのエージェントだけ）
        if target:
            return [speak(target, topic)]

        # B案：本物の議論ループ
        # 各発言が前の全発言を文脈として受け取る
        results = []
        context = ""

        order = ["sanbo", "tech", "content", "sns"]
        for agent_id in order:
            name, op = speak(agent_id, topic, context)
            results.append((name, op))
            context += f"\n{name}: {op}"

        # ボブが全議論を読んで最終判断
        name, op = speak("ceo", topic, context, max_tokens=600)
        results.append((name, op))

        # ボブがテック君に質問していたら自動返答
        if "テック" in op:
            tech_prompt = f"{BASE} {STYLES['tech']} ボブCEOから質問が来た。YES/NOで即答してから理由を一言。"
            tech_reply = _call_claude(tech_prompt, op, 300)
            results.append(("⚙️ テック君（返答）", tech_reply))

        return results
