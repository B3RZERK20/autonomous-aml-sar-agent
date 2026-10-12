"""
End-to-End Tests for LangGraph Multi-Agent AML Investigation Workflow.
Verifies the complete execution sequence:
Data Gatherer -> Compliance Analyst -> SAR Writer -> Evaluator Guardrail.
"""

import pytest
from agents.workflow import run_aml_investigation


def test_end_to_end_investigation_structuring_case():
    """Runs full 4-agent investigation on suspect structuring account ACC-883910."""
    result = run_aml_investigation("ACC-883910")

    assert result is not None
    assert "case_id" in result
    assert result["status"] in ["VERIFIED", "APPROVED", "SAR_DRAFTED", "REVISION"]

    # Verify Data Gatherer evidence
    account_history = result.get("account_history", {})
    assert account_history.get("account_id") == "ACC-883910"
    assert len(result.get("linked_entities", [])) >= 1
    assert len(result.get("sanctions_findings", [])) >= 1

    # Verify Compliance Analyst RAG results
    retrieved_regs = result.get("retrieved_regulations", [])
    assert len(retrieved_regs) >= 1

    # Verify SAR Writer Draft
    sar = result.get("sar_draft", {})
    assert sar is not None
    assert sar.get("suspicious_amount_total_usd", 0) > 0
    assert "full_sar_text" in sar
    assert "31 U.S.C." in sar["full_sar_text"] or "31 CFR" in sar["full_sar_text"]

    # Verify Evaluator Audit
    evaluation = result.get("evaluation", {})
    assert evaluation is not None
    assert "faithfulness_score" in evaluation
    assert evaluation["faithfulness_score"] >= 0.85

    # Verify Audit Trail
    audit_log = result.get("audit_log", [])
    assert len(audit_log) >= 4
    agents_logged = {entry["agent"] for entry in audit_log}
    assert "Data Gatherer" in agents_logged
    assert "Compliance Analyst" in agents_logged
    assert "SAR Writer" in agents_logged
    assert "Evaluator Guardrail" in agents_logged
