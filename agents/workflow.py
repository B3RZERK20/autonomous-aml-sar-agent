"""
LangGraph Multi-Agent Orchestrator.
Constructs and compiles the cyclic state graph connecting:
1. Data Gatherer (MCP)
2. Compliance Analyst (RAG)
3. SAR Writer (FinCEN BSA Narrative)
4. Evaluator Guardrail (Hallucination & Factual Verification)
With automated feedback loop for corrections.
"""

import uuid
import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from agents.state import AMLInvestigationState
from agents.gatherer import data_gatherer_node
from agents.analyst import compliance_analyst_node
from agents.writer import sar_writer_node
from agents.evaluator import evaluator_guardrail_node

logger = logging.getLogger("aml_workflow")


def should_revise_or_end(state: AMLInvestigationState) -> Literal["writer", "__end__"]:
    """
    Conditional routing edge following Evaluator Guardrail check.
    If the SAR draft contains hallucinations and revisions remain, routes back to Writer.
    Otherwise, approves and concludes the workflow.
    """
    evaluation = state.get("evaluation", {})
    is_faithful = evaluation.get("is_faithful", False)
    rev_count = state.get("revision_count", 0)
    max_rev = state.get("max_revisions", 2)

    if is_faithful:
        logger.info("[Workflow Router] SAR draft verified 100% faithful. Moving to END.")
        return END

    if rev_count >= max_rev:
        logger.warning(f"[Workflow Router] Max revisions ({max_rev}) reached. Moving to END.")
        return END

    logger.info(f"[Workflow Router] Hallucination detected. Routing back to SAR Writer for revision #{rev_count + 1}...")
    return "writer"


def create_aml_workflow():
    """Builds and compiles the complete LangGraph StateGraph."""
    builder = StateGraph(AMLInvestigationState)

    # Add agent nodes
    builder.add_node("gatherer", data_gatherer_node)
    builder.add_node("analyst", compliance_analyst_node)
    builder.add_node("writer", sar_writer_node)
    builder.add_node("evaluator", evaluator_guardrail_node)

    # Standard deterministic progression
    builder.add_edge(START, "gatherer")
    builder.add_edge("gatherer", "analyst")
    builder.add_edge("analyst", "writer")
    builder.add_edge("writer", "evaluator")

    # Conditional feedback loop from Evaluator
    builder.add_conditional_edges(
        "evaluator",
        should_revise_or_end,
        {
            "writer": "writer",
            END: END
        }
    )

    return builder.compile()


# Compiled Singleton Graph
aml_graph = create_aml_workflow()


def run_aml_investigation(
    account_id: str = "ACC-883910",
    case_id: str = None
) -> Dict[str, Any]:
    """
    Convenience runner executing the multi-agent investigation pipeline for a given account.
    """
    if not case_id:
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"

    initial_state: AMLInvestigationState = {
        "case_id": case_id,
        "target_account_id": account_id,
        "revision_count": 0,
        "max_revisions": 2,
        "status": "INITIALIZED",
        "audit_log": []
    }

    final_state = aml_graph.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    print("Testing LangGraph Multi-Agent AML Pipeline on suspect account ACC-883910...")
    result = run_aml_investigation("ACC-883910")
    print(f"\nInvestigation Complete for Case: {result['case_id']}")
    print(f"Final Status: {result.get('status')}")
    print(f"Faithfulness Score: {result.get('evaluation', {}).get('faithfulness_score')}")
    print(f"Audit Verdict: {result.get('evaluation', {}).get('audit_verdict')}")
    print("\n--- SAR Narrative Summary ---")
    print(result.get("sar_draft", {}).get("narrative_summary"))
