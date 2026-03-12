"""
src/workflows/kindle_chain.py
Kindle 出版 → NOTE リライト → SNS 投稿予約
の連鎖ワークフロー（Phase 3 コア）

実行フロー:
  1. 既存 Kindle 原稿（Drive）から本を選択
  2. DALL-E でカバー画像を生成
  3. [承認] KDP 出版を確認
  4. NOTE 用リライト記事を生成
  5. SNS 用要約を生成
  6. 投稿予約 / LINE 報告
"""
from __future__ import annotations
import httpx
import base64
from loguru import logger
from langchain_openai import ChatOpenAI, OpenAI
from openai import OpenAI as OpenAIClient

from config.settings import OPENAI_API_KEY, DALLE_MODEL, GAS_ENDPOINT
from config.prompts import KINDLE_COVER_PROMPT
from src.dify_connector.client import DifyClient
from src.line_gateway.approval import ApprovalManager
from src.aiceo.state import ApprovalRequest
import uuid


class KindleChain:
    """Kindle 出版連鎖ワークフロー"""

    def __init__(self):
        self.dify = DifyClient()
        self.approval = ApprovalManager()
        self.openai = OpenAIClient(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

    def run(self, book_title: str, book_genre: str, target_audience: str, dry_run: bool = False) -> dict:
        """
        1冊の Kindle 本を対象に全連鎖を実行する。

        Args:
            book_title: Kindle本のタイトル
            book_genre: ジャンル（健康・ビジネス等）
            target_audience: ターゲット読者
            dry_run: True なら実際の API 呼び出しをスキップ

        Returns:
            各ステップの結果をまとめた dict
        """
        results = {
            "book_title": book_title,
            "steps": {},
            "success": False,
        }

        logger.info(f"[KindleChain] 開始: {book_title}")

        # ── Step 1: カバー生成 ────────────────────────────────────
        cover_result = self._generate_cover(book_title, book_genre, target_audience, dry_run)
        results["steps"]["cover_generation"] = cover_result

        if not cover_result.get("success"):
            logger.warning("[KindleChain] カバー生成失敗 → 続行")

        # ── Step 2: KDP 出版承認リクエスト ────────────────────────────────────
        approval_req = ApprovalRequest(
            id=str(uuid.uuid4()),
            action="kdp_publish",
            description=f"KDP出版: {book_title}",
            details={
                "title": book_title,
                "genre": book_genre,
                "cover_url": cover_result.get("image_url", "（未生成）"),
                "note": "承認後、KDP Direct Publishing へ自動送信します",
            }
        )

        if not dry_run:
            self.approval.request(approval_req)
            logger.info(f"[KindleChain] KDP承認リクエスト送信: {approval_req.id}")
            results["steps"]["kdp_approval"] = {"status": "waiting", "request_id": approval_req.id}
        else:
            logger.info("[KindleChain] DRY RUN: KDP承認スキップ")
            results["steps"]["kdp_approval"] = {"status": "skipped_dry_run"}

        # ── Step 3: NOTE リライト（承認と並行して準備） ────────────────────────────────────
        note_result = self._generate_note_articles(book_title, book_genre, dry_run)
        results["steps"]["note_rewrite"] = note_result

        # ── Step 4: SNS 要約生成 ────────────────────────────────────
        sns_result = self._generate_sns_posts(book_title, book_genre, dry_run)
        results["steps"]["sns_posts"] = sns_result

        results["success"] = True
        logger.success(f"[KindleChain] 完了: {book_title}")
        return results

    def _generate_cover(self, title: str, genre: str, target: str, dry_run: bool) -> dict:
        """DALL-E でカバー画像を生成する"""
        if dry_run or not self.openai:
            logger.info("[Cover] DRY RUN または OpenAI未設定 — モック")
            return {"success": True, "image_url": "https://mock-cover-url.example.com", "mock": True}

        try:
            theme_map = {
                "健康": "peaceful nature, wellness, soft green tones",
                "ビジネス": "modern corporate, minimalist, blue and white",
                "節約": "coins, piggy bank, warm orange tones",
                "育児": "gentle pastel, children's warmth, soft pink and blue",
            }
            theme = theme_map.get(genre, "professional, modern, Japanese market")

            prompt = KINDLE_COVER_PROMPT.format(
                title=title, genre=genre, target=target, theme_description=theme
            )

            response = self.openai.images.generate(
                model=DALLE_MODEL,
                prompt=prompt,
                size="1024x1792",  # Kindle縦長に近い比率
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            logger.success(f"[Cover] 生成完了: {image_url[:60]}...")
            return {"success": True, "image_url": image_url}

        except Exception as e:
            logger.error(f"[Cover] エラー: {e}")
            return {"success": False, "error": str(e)}

    def _generate_note_articles(self, title: str, genre: str, dry_run: bool) -> dict:
        """Dify NOTE リライトWFを呼び出す"""
        if dry_run:
            return {"success": True, "articles": ["記事1（モック）", "記事2（モック）"], "mock": True}

        result = self.dify.run_workflow(
            workflow_key="note",
            inputs={"book_title": title, "genre": genre, "article_count": 3}
        )
        return result

    def _generate_sns_posts(self, title: str, genre: str, dry_run: bool) -> dict:
        """SNS 用の要約ポストを生成する"""
        if dry_run:
            return {
                "success": True,
                "posts": {
                    "x": f"📚 新刊『{title}』が出ました！{genre}について分かりやすく解説。 #Kindle #電子書籍",
                    "instagram": f"新刊リリース✨『{title}』#{genre} #本好きな人と繋がりたい",
                    "threads": f"『{title}』を出版しました。{genre}について書いています。",
                },
                "mock": True,
            }

        # 将来: Dify SNS WFを呼び出す
        return {"success": False, "error": "SNS WF 未実装 — Phase 4 で対応"}
