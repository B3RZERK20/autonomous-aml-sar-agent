"""
Agent 1: Data Gatherer (MCP-Powered).
Securely connects to the core banking database via Model Context Protocol (MCP) tools.
Retrieves account profiles, transaction chronologies, graph linkages (UBOs/shells),
and executes watchlist sanctions screening.
"""

from typing import Dict, Any, List
from datetime import datetime
from mcp_server.client import mcp_client
from agents.state import AMLInvestigationState


def data_gatherer_node(state: AMLInvestigationState) -> Dict[str, Any]:
    """
    Node 1 in LangGraph.
    Uses MCP tools instead of raw SQL to safely extract evidence for the suspect account.
    """
    account_id = state.get("target_account_id", "ACC-883910")
    audit_log = list(state.get("audit_log", []))
    
    timestamp = datetime.now().isoformat()
    audit_log.append({
        "agent": "Data Gatherer",
        "action": f"Initiating MCP data collection for target account {account_id}",
        "timestamp": timestamp
    })

    # 1. MCP Tool: Get complete account history
    account_history = mcp_client.get_account_history(account_id)
    audit_log.append({
        "agent": "Data Gatherer",
        "action": f"Retrieved {account_history.get('total_transactions', 0)} transactions ({account_history.get('flagged_count', 0)} flagged) via MCP",
        "timestamp": datetime.now().isoformat()
    })

    # 2. MCP Tool: Get linked entities and graph relationships
    linked_entities = mcp_client.get_linked_entities(account_id)
    audit_log.append({
        "agent": "Data Gatherer",
        "action": f"Identified {len(linked_entities)} linked entities/UBOs in corporate graph via MCP",
        "timestamp": datetime.now().isoformat()
    })

    # 3. Watchlist Screening via MCP check_sanctions_list tool
    names_to_screen = set()
    # Account owner
    if "account_name" in account_history:
        # Split combined names if any e.g. "Derrick Sterling / Apex Horizon LLC"
        for part in account_history["account_name"].split("/"):
            names_to_screen.add(part.strip())

    # Entities and UBOs
    for ent in linked_entities:
        if ent.get("name"):
            names_to_screen.add(ent["name"])
        if ent.get("ultimate_beneficial_owner"):
            names_to_screen.add(ent["ultimate_beneficial_owner"])
        for shared in ent.get("shared_ubo_entities", []):
            if shared.get("name"):
                names_to_screen.add(shared["name"])

    # Counterparty account holders
    for tx in account_history.get("transactions", []):
        dest_acc = tx.get("dest_account")
        if dest_acc and dest_acc != account_id:
            # Check counterparty entities
            cp_entities = mcp_client.get_linked_entities(dest_acc)
            for cp in cp_entities:
                if cp.get("name"):
                    names_to_screen.add(cp["name"])
                if cp.get("ultimate_beneficial_owner"):
                    names_to_screen.add(cp["ultimate_beneficial_owner"])

    sanctions_hits = []
    for name in names_to_screen:
        hits = mcp_client.check_sanctions_list(name)
        if hits:
            sanctions_hits.extend(hits)
            audit_log.append({
                "agent": "Data Gatherer",
                "action": f"CRITICAL WATCHLIST MATCH: '{name}' matched {len(hits)} sanctions records via MCP",
                "timestamp": datetime.now().isoformat()
            })

    return {
        "account_profile": {
            "account_id": account_history.get("account_id"),
            "account_name": account_history.get("account_name"),
            "account_type": account_history.get("account_type"),
            "country": account_history.get("country"),
            "risk_rating": account_history.get("risk_rating"),
            "balance": account_history.get("balance"),
        },
        "account_history": account_history,
        "linked_entities": linked_entities,
        "sanctions_findings": sanctions_hits,
        "status": "DATA_GATHERED",
        "audit_log": audit_log
    }
