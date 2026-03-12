"""
src/aiceo/state.py
LangGraph の State 定義 — 思考ループ全体の状態を管理
"""
from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class BusinessMetrics(BaseModel):
    """事業ごとの収益・KPI"""
    kindle_books_published: int = 0
    kindle_monthly_revenue: int = 0       # 円
    note_articles_published: int = 0
    note_monthly_revenue: int = 0
    sns_followers_total: int = 0
    youtube_subscribers: int = 0
    kamui_status: str = "HOLD"            # 保護中
    last_updated: datetime = Field(default_factory=datetime.now)


class ApprovalRequest(BaseModel):
    """承認待ちタスク"""
    id: str
    action: str
    description: str
    details: dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    status: Literal["pending", "approved", "rejected", "held"] = "pending"


class AICompanyState(BaseModel):
    """
    LangGraph メイン State
    ループを跨いで持続する全情報を保持する
    """
    # ── 現在のタスク ────────────────────────────────────
    current_task: str = ""                # 今ループで何をするか
    task_type: str = ""                   # research / strategy / execute / analyze
    topic: str = ""                       # リサーチ・実行対象のテーマ

    # ── リサーチ結果 ────────────────────────────────────
    research_result: dict[str, Any] = {}

    # ── 戦略 ────────────────────────────────────
    strategy: dict[str, Any] = {}
    requires_approval: bool = False

    # ── 実行 ────────────────────────────────────
    execution_target: str = ""            # どのDify WFを実行するか
    execution_params: dict[str, Any] = {}
    execution_result: dict[str, Any] = {}

    # ── 分析 ────────────────────────────────────
    analysis: dict[str, Any] = {}
    next_action: str = ""

    # ── 承認管理 ────────────────────────────────────
    pending_approvals: list[ApprovalRequest] = []
    approval_status: Literal["none", "waiting", "approved", "rejected"] = "none"

    # ── 事業メトリクス ────────────────────────────────────
    metrics: BusinessMetrics = Field(default_factory=BusinessMetrics)

    # ── ループ制御 ────────────────────────────────────
    loop_count: int = 0
    max_loops: int = 10                   # 暴走防止
    error: Optional[str] = None
    completed: bool = False

    # ── ログ ────────────────────────────────────
    action_log: list[dict[str, Any]] = []

    def add_log(self, action: str, detail: str = "") -> None:
        self.action_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "detail": detail,
            "loop": self.loop_count,
        })
