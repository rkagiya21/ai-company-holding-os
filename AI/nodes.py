"""
src/aiceo/nodes.py
LangGraph 各ノードの実装

フロー:
  research → strategy → approval_gate → execute → analyze → (loop)
"""
from __future__ import annotations
import json
import uuid
from loguru import logger
from langchain_openai import ChatOpenAI

from config.settings import LLM_MODEL, LLM_MODEL_HEAVY, APPROVAL_REQUIRED_ACTIONS
from config.prompts import (
    RESEARCH_PROMPT, STRATEGY_PROMPT, ANALYSIS_PROMPT
)
from src.aiceo.state import AICompanyState, ApprovalRequest
from src.dify_connector.client import DifyClient
from src.line_gateway.approval import ApprovalManager


# ── LLM インスタンス ────────────────────────────────────
def _get_llm(heavy: bool = False) -> ChatOpenAI:
    model = LLM_MODEL_HEAVY if heavy else LLM_MODEL
    return ChatOpenAI(model=model, temperature=0.3)


# ══════════════════════════════════════════════════════════
#  Node 1: Research
# ══════════════════════════════════════════════════════════
def research_node(state: AICompanyState) -> AICompanyState:
    """
    Web・市場調査を実行する。
    Dify の リサーチWF を呼び出し、LLM で補完する。
    """
    logger.info(f"[Research] topic={state.topic}")
    state.add_log("research_start", f"topic: {state.topic}")

    try:
        # まず Dify リサーチWFを呼び出す（設定済みなら）
        dify = DifyClient()
        dify_result = dify.run_workflow(
            workflow_key="research",
            inputs={"topic": state.topic, "depth": "detailed"}
        )

        # Dify結果があればそれを使い、なければ LLM で直接リサーチ
        if dify_result.get("success"):
            research_data = dify_result.get("output", {})
        else:
            # LLM フォールバック
            llm = _get_llm()
            prompt = RESEARCH_PROMPT.format(topic=state.topic)
            response = llm.invoke(prompt)
            research_data = json.loads(response.content)

        state.research_result = research_data
        state.add_log("research_done", f"結果取得: {list(research_data.keys())}")
        logger.success(f"[Research] 完了: {state.topic}")

    except Exception as e:
        logger.error(f"[Research] エラー: {e}")
        state.error = str(e)
        state.research_result = {"error": str(e), "topic": state.topic}

    return state


# ══════════════════════════════════════════════════════════
#  Node 2: Strategy
# ══════════════════════════════════════════════════════════
def strategy_node(state: AICompanyState) -> AICompanyState:
    """
    リサーチ結果をもとに戦略を立案する。
    承認が必要かどうかを判定する。
    """
    logger.info("[Strategy] 戦略立案開始")
    state.add_log("strategy_start")

    try:
        llm = _get_llm(heavy=True)  # 戦略は GPT-4o で
        prompt = STRATEGY_PROMPT.format(
            research_result=json.dumps(state.research_result, ensure_ascii=False, indent=2)
        )
        response = llm.invoke(prompt)
        strategy = json.loads(response.content)

        state.strategy = strategy
        state.requires_approval = strategy.get("requires_approval", False)

        # 承認が必要なアクションかチェック
        planned_actions = strategy.get("actions", [])
        for action in planned_actions:
            if action in APPROVAL_REQUIRED_ACTIONS:
                state.requires_approval = True
                break

        state.add_log("strategy_done", f"承認必要: {state.requires_approval}")
        logger.success(f"[Strategy] 完了 / 承認必要={state.requires_approval}")

    except Exception as e:
        logger.error(f"[Strategy] エラー: {e}")
        state.error = str(e)

    return state


# ══════════════════════════════════════════════════════════
#  Node 3: Approval Gate（ゲートキーパー）
# ══════════════════════════════════════════════════════════
def approval_gate_node(state: AICompanyState) -> AICompanyState:
    """
    承認が必要なら LINE へ通知し、承認待ち状態にする。
    承認不要なら即通過。
    """
    logger.info(f"[ApprovalGate] 承認要否チェック: {state.requires_approval}")

    if not state.requires_approval:
        state.approval_status = "approved"  # 承認不要 → 自動通過
        state.add_log("approval_skip", "承認不要 → 自動実行")
        return state

    # 承認リクエスト作成
    req = ApprovalRequest(
        id=str(uuid.uuid4()),
        action=state.execution_target or "strategy_execution",
        description=f"戦略実行: {state.topic}",
        details=state.strategy,
    )
    state.pending_approvals.append(req)
    state.approval_status = "waiting"

    # LINE に承認リクエスト送信
    try:
        approval_mgr = ApprovalManager()
        approval_mgr.request(req)
        state.add_log("approval_requested", f"LINE通知送信: {req.id}")
        logger.info(f"[ApprovalGate] LINE承認待ち: {req.id}")
    except Exception as e:
        logger.error(f"[ApprovalGate] LINE通知エラー: {e}")
        # 通知失敗でも承認待ちを維持（安全側に倒す）
        state.error = f"LINE通知失敗: {e}"

    return state


# ══════════════════════════════════════════════════════════
#  Node 4: Execute（Dify WF キック）
# ══════════════════════════════════════════════════════════
def execute_node(state: AICompanyState) -> AICompanyState:
    """
    Dify の対象ワークフローを API 経由でキックし、結果を受け取る。
    承認が "approved" でなければ何もしない。
    """
    if state.approval_status not in ("approved",):
        logger.info("[Execute] 承認待ちのためスキップ")
        state.add_log("execute_skip", f"status={state.approval_status}")
        return state

    logger.info(f"[Execute] WF実行: {state.execution_target}")
    state.add_log("execute_start", f"target={state.execution_target}")

    try:
        dify = DifyClient()
        result = dify.run_workflow(
            workflow_key=state.execution_target,
            inputs=state.execution_params
        )
        state.execution_result = result
        state.add_log("execute_done", f"success={result.get('success')}")
        logger.success(f"[Execute] 完了: {state.execution_target}")

    except Exception as e:
        logger.error(f"[Execute] エラー: {e}")
        state.error = str(e)
        state.execution_result = {"success": False, "error": str(e)}

    return state


# ══════════════════════════════════════════════════════════
#  Node 5: Analyze（結果分析 + 次ループ決定）
# ══════════════════════════════════════════════════════════
def analyze_node(state: AICompanyState) -> AICompanyState:
    """
    実行結果を分析し、次のアクションを決定する。
    必要に応じてLINEに報告する。
    """
    logger.info("[Analyze] 結果分析開始")
    state.add_log("analyze_start")

    try:
        if state.execution_result:
            llm = _get_llm()
            prompt = ANALYSIS_PROMPT.format(
                workflow_name=state.execution_target,
                result=json.dumps(state.execution_result, ensure_ascii=False),
                expected=json.dumps(state.strategy.get("expected_output", {}), ensure_ascii=False),
            )
            response = llm.invoke(prompt)
            analysis = json.loads(response.content)
        else:
            # 実行なし（承認待ち）の場合
            analysis = {
                "success": False,
                "achievement_rate": 0,
                "issues": ["承認待ちのため未実行"],
                "next_actions": ["承認を待つ"],
                "requires_human_review": True,
            }

        state.analysis = analysis
        state.next_action = analysis.get("next_actions", ["待機"])[0]
        state.loop_count += 1

        # ループ終了判定
        if state.loop_count >= state.max_loops:
            state.completed = True
            state.add_log("loop_max_reached", f"最大ループ数 {state.max_loops} に達した")

        if analysis.get("success") and not analysis.get("next_actions"):
            state.completed = True
            state.add_log("task_completed", "タスク完了")

        state.add_log("analyze_done", f"next={state.next_action}")
        logger.success(f"[Analyze] 完了 / 次={state.next_action}")

    except Exception as e:
        logger.error(f"[Analyze] エラー: {e}")
        state.error = str(e)
        state.completed = True  # エラー時はループ終了

    return state


# ══════════════════════════════════════════════════════════
#  ルーティング関数（条件分岐）
# ══════════════════════════════════════════════════════════
def should_continue(state: AICompanyState) -> str:
    """
    Analyze ノード後のルーティング。
    - completed → END
    - approval_status=waiting → END（次回 LINE 承認後に再開）
    - else → research（次ループ）
    """
    if state.completed or state.error:
        return "end"
    if state.approval_status == "waiting":
        return "end"  # 承認待ちはここで一時停止
    return "research"  # 次のループへ


def route_after_approval(state: AICompanyState) -> str:
    """
    ApprovalGate 後のルーティング。
    - approved → execute
    - waiting → end（承認待ち）
    - rejected → end
    """
    if state.approval_status == "approved":
        return "execute"
    return "end"
