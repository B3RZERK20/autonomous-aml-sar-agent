"""
State Definition for the Autonomous AML LangGraph Multi-Agent System.
Defines the state schema passed between Data Gatherer, Compliance Analyst,
SAR Writer, and Hallucination Evaluator nodes.
"""

from typing import TypedDict, List, Dict, Any, Optional


class SARDraft(TypedDict, total=False):
    filing_institution: str
    subject_name: str
    subject_accounts: List[str]
    primary_activity: str
    suspicious_amount_total_usd: float
    activity_start_date: str
    activity_end_date: str
    narrative_summary: str
    chronological_events: List[str]
    regulatory_violations: List[str]
    sanctions_nexus: str
    recommended_actions: List[str]
    full_sar_text: str


class EvaluationResult(TypedDict, total=False):
    is_faithful: bool
    faithfulness_score: float  # Scale: 0.0 to 1.0
    verified_facts_count: int
    hallucinated_facts: List[str]
    unsupported_numbers: List[str]
    audit_verdict: str  # "APPROVED" or "REVISION_REQUIRED"
    feedback_notes: str


class AMLInvestigationState(TypedDict, total=False):
    case_id: str
    target_account_id: str
    flagged_alert: Dict[str, Any]
    account_profile: Dict[str, Any]
    account_history: Dict[str, Any]
    linked_entities: List[Dict[str, Any]]
    sanctions_findings: List[Dict[str, Any]]
    retrieved_regulations: List[Dict[str, Any]]
    sar_draft: Optional[SARDraft]
    evaluation: Optional[EvaluationResult]
    revision_count: int
    max_revisions: int
    status: str
    audit_log: List[Dict[str, Any]]
