"""
Agent 2: Compliance Analyst (RAG-Powered).
Examines transactional anomalies and graph linkages discovered by Data Gatherer.
Queries the Regulatory RAG Vector Store to pull matching FinCEN regulations,
FATF standards, and statutory citations.
"""

from typing import Dict, Any, List
from datetime import datetime
from rag.vector_store import rag_service
from agents.state import AMLInvestigationState


def compliance_analyst_node(state: AMLInvestigationState) -> Dict[str, Any]:
    """
    Node 2 in LangGraph.
    Queries RAG vector store for FinCEN BSA regulations and FATF guidance
    relevant to the gathered transactions and watchlist findings.
    """
    account_history = state.get("account_history", {})
    flagged_txs = account_history.get("flagged_transactions", [])
    sanctions = state.get("sanctions_findings", [])
    audit_log = list(state.get("audit_log", []))

    audit_log.append({
        "agent": "Compliance Analyst",
        "action": "Analyzing gathered evidence against FinCEN and FATF regulatory guidelines",
        "timestamp": datetime.now().isoformat()
    })

    queries = []
    
    # 1. Detect Structuring / Smurfing Patterns
    cash_deposits = [t for t in flagged_txs if "CASH" in t.get("transaction_type", "").upper() or "below $10,000" in t.get("flag_reason", "")]
    if cash_deposits:
        queries.append("What is the FinCEN regulatory definition and legal threshold for structuring under 31 CFR 1010.311 and CTR reporting?")

    # 2. Detect Offshore Movement / Shell Company Layering
    offshore_txs = [t for t in flagged_txs if "WIRE" in t.get("transaction_type", "").upper() or "offshore" in t.get("flag_reason", "").lower()]
    if offshore_txs or len(state.get("linked_entities", [])) > 1:
        queries.append("What are FATF recommendations 24 and 25 regarding ultimate beneficial ownership and offshore shell company layering?")

    # 3. Detect Sanctions Evasion
    if sanctions:
        queries.append("What are mandatory reporting rules for OFAC Specially Designated Nationals and sanctions evasion?")

    # 4. Standard SAR Filing Requirements
    queries.append("What are the mandatory SAR filing criteria and timelines under 31 CFR 1020.320 for transactions with no lawful purpose?")

    retrieved_regulations = []
    seen_chunks = set()

    for q in queries:
        results = rag_service.query(q, top_k=2)
        for r in results:
            chunk_id = r.get("chunk_id", r.get("text", "")[:30])
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                retrieved_regulations.append(r)

    audit_log.append({
        "agent": "Compliance Analyst",
        "action": f"Retrieved {len(retrieved_regulations)} statutory compliance citations from RAG vector store",
        "timestamp": datetime.now().isoformat()
    })

    return {
        "retrieved_regulations": retrieved_regulations,
        "status": "ANALYSIS_COMPLETE",
        "audit_log": audit_log
    }
