"""
Tests for Hallucination Evaluator Guardrail Agent.
Verifies detection of fabricated numbers, unauthorized accounts, and factual compliance scoring.
"""

import pytest
from agents.evaluator import evaluate_sar_faithfulness


def test_evaluator_approves_faithful_sar():
    """Verifies evaluator gives 100% score to completely faithful SAR draft."""
    sar_draft = {
        "full_sar_text": (
            "Account ACC-883910 conducted cash deposits of $9,400.00, $9,850.00, "
            "$9,200.00, and $9,750.00 totaling $38,200.00. Subject subsequently wired "
            "$37,500.00 to account ACC-992014."
        ),
        "narrative_summary": "Structuring and rapid movement totaling $75,700.00."
    }

    ground_truth_accounts = ["ACC-883910", "ACC-992014"]
    ground_truth_amounts = [9400.0, 9850.0, 9200.0, 9750.0, 37500.0]

    result = evaluate_sar_faithfulness(
        sar_draft=sar_draft,
        ground_truth_accounts=ground_truth_accounts,
        ground_truth_amounts=ground_truth_amounts,
        ground_truth_entities=["Derrick Sterling"],
        ground_truth_sanctions=[]
    )

    assert result["is_faithful"] is True
    assert result["audit_verdict"] == "APPROVED"
    assert result["faithfulness_score"] >= 0.95
    assert len(result["unsupported_numbers"]) == 0
    assert len(result["hallucinated_facts"]) == 0


def test_evaluator_flags_hallucinated_numbers_and_accounts():
    """Verifies evaluator detects fabricated numbers and fake account IDs."""
    hallucinated_sar = {
        "full_sar_text": (
            "Customer wired $999,999.00 to fictitious account ACC-000000 located in Switzerland."
        ),
        "narrative_summary": "Fabricated activity."
    }

    ground_truth_accounts = ["ACC-883910", "ACC-992014"]
    ground_truth_amounts = [9400.0, 9850.0, 37500.0]

    result = evaluate_sar_faithfulness(
        sar_draft=hallucinated_sar,
        ground_truth_accounts=ground_truth_accounts,
        ground_truth_amounts=ground_truth_amounts,
        ground_truth_entities=[],
        ground_truth_sanctions=[]
    )

    assert result["is_faithful"] is False
    assert result["audit_verdict"] == "REVISION_REQUIRED"
    assert len(result["unsupported_numbers"]) >= 1
    assert any("999,999" in n for n in result["unsupported_numbers"])
    assert any("ACC-000000" in h for h in result["hallucinated_facts"])
