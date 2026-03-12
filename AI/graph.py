"""
src/aiceo/graph.py
LangGraph メイングラフ — AI CEO 思考ループ

フロー:
  START
    → research_node
    → strategy_node
    → approval_gate_node  ─── waiting/rejected → END
                          └── approved
    → execute_node
    → analyze_node  ─── completed/error → END
                    └── continue → research_node (次ループ)
"""
from langgraph.graph import StateGraph, END
from loguru import logger

from src.aiceo.state import AICompanyState
from src.aiceo.nodes import (
    research_node,
    strategy_node,
    approval_gate_node,
    execute_node,
    analyze_node,
    should_continue,
    route_after_approval,
)


def build_aiceo_graph() -> StateGraph:
    """AI CEO グラフを構築して返す"""

    # グラフ初期化
    graph = StateGraph(AICompanyState)

    # ── ノード登録 ────────────────────────────────────
    graph.add_node("research",      research_node)
    graph.add_node("strategy",      strategy_node)
    graph.add_node("approval_gate", approval_gate_node)
    graph.add_node("execute",       execute_node)
    graph.add_node("analyze",       analyze_node)

    # ── エッジ（固定） ────────────────────────────────────
    graph.set_entry_point("research")
    graph.add_edge("research",  "strategy")
    graph.add_edge("strategy",  "approval_gate")
    graph.add_edge("execute",   "analyze")

    # ── 条件分岐エッジ ────────────────────────────────────
    # ApprovalGate → approved:execute / else:END
    graph.add_conditional_edges(
        "approval_gate",
        route_after_approval,
        {
            "execute": "execute",
            "end":     END,
        }
    )

    # Analyze → continue:research / end:END
    graph.add_conditional_edges(
        "analyze",
        should_continue,
        {
            "research": "research",
            "end":      END,
        }
    )

    return graph.compile()


# ── シングルトン ────────────────────────────────────
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_aiceo_graph()
        logger.info("[Graph] AI CEO グラフ構築完了")
    return _graph


# ── 実行ヘルパー ────────────────────────────────────
def run_aiceo(topic: str, task_type: str = "research", **kwargs) -> AICompanyState:
    """
    AI CEO を指定トピックで起動する。

    Args:
        topic:     リサーチ・実行のテーマ（例: "占い事業", "Kindle出版"）
        task_type: タスク種別（research / execute / analyze）
        **kwargs:  execution_target, execution_params など追加引数

    Returns:
        実行後の最終 State
    """
    graph = get_graph()

    initial_state = AICompanyState(
        current_task=f"{task_type}: {topic}",
        task_type=task_type,
        topic=topic,
        execution_target=kwargs.get("execution_target", ""),
        execution_params=kwargs.get("execution_params", {}),
    )

    logger.info(f"[AICEO] 起動: topic={topic}, type={task_type}")

    final_state = graph.invoke(initial_state)

    logger.info(f"[AICEO] 完了: loops={final_state.loop_count}, "
                f"approval={final_state.approval_status}")

    return final_state
