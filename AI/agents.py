import os
import time
import requests
from loguru import logger

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GEMINI_MODEL = "gemini-2.0-flash"


def _call_claude(system, user, max_tokens=1000):
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key: return "[API Key Missing]"
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}]
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Claude Error: {e}")
        return f"[Claude Error: {e}]"


def _call_gemini(system, user):
    time.sleep(3)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key: return "[Gemini Key Missing]"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": user}]}],
            "generationConfig": {"maxOutputTokens": 1000}
        }
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"[Gemini Error: {e}]"


class AgentRouter:
    def council(self, topic):
        company_context = (
            "我々はAI開発・コンテンツ販売を行う会社です。"
            "目標: Phase 7 完全自律経営。会長の承認のみで全事業を回す。"
            "現在の主力事業: Kindle出版自動化、NOTE、YouTube/SNS自動化。"
            "リソース: Claude API、Gemini API、Dify、LINE Bot。"
            "重要ルール: APIコスト削減のため雑談・挨拶禁止。結論とビジネス根拠のみ述べること。"
        )

        system_1 = f"{company_context}\nあなたは【経営参謀(Gemini)】です。市場性・収益性・リスクを分析し、戦略を先陣切って提示。250字以内。"
        op_1 = _call_gemini(system_1, f"議題: {topic}")

        system_2 = f"{company_context}\nあなたは【開発事業部長】です。参謀の戦略を受け、DifyやAPIでの自動化実装案を具体的に提言。250字以内。"
        op_2 = _call_claude(system_2, f"議題: {topic}\n\n参謀の戦略:\n{op_1}\n\n開発実装案:")

        system_3 = f"{company_context}\nあなたは【コンテンツ事業部長】です。Kindle/NOTE担当を統括。開発案を受け、収益最大化の制作戦略を提言。250字以内。"
        op_3 = _call_claude(system_3, f"議題: {topic}\n\n開発部長の案:\n{op_2}\n\nコンテンツ戦略:")

        system_4 = f"{company_context}\nあなたは【SNS事業部長】です。YouTube/SNS自動運用を統括。コンテンツ部長の案を受け、集客・拡散フローを提言。250字以内。"
        op_4 = _call_claude(system_4, f"議題: {topic}\n\nコンテンツ部長の案:\n{op_3}\n\n集客戦略:")

        all_opinions = f"参謀: {op_1}\n開発: {op_2}\nコンテンツ: {op_3}\nSNS: {op_4}"
        system_ceo = f"{company_context}\nあなたは【AI CEO】です。各部長の議論を統合し、会長がYES/NOで判断できる最終決済案を提示。余計な言葉不要。"
        final = _call_claude(system_ceo, f"議題: {topic}\n\n議論:\n{all_opinions}\n\n最終決済案:", max_tokens=1000)

        res = "━━━━━━━━━━━━━━━\n🏛️ 経営会議 合議結果\n"
        res += f"テーマ: {topic}\n━━━━━━━━━━━━━━━\n\n"
        res += f"🔭 経営参謀\n{op_1}\n\n"
        res += f"⚙️ 開発事業部長\n{op_2}\n\n"
        res += f"✍️ コンテンツ事業部長\n{op_3}\n\n"
        res += f"🎬 SNS事業部長\n{op_4}\n\n"
        res += f"━━━━━━━━━━━━━━━\n👑 AI CEO 最終決済案\n{final}"
        return res
