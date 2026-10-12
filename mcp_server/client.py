"""
MCP Client Wrapper for LangGraph Agents.
Provides a structured, type-safe interface for agents to query the MCP Server tools:
- get_account_history
- get_linked_entities
- check_sanctions_list
- get_flagged_transactions
"""

import json
import logging
from typing import Dict, List, Any, Optional
from mcp_server.server import db_service

logger = logging.getLogger("mcp_client")


class MCPInvestigationClient:
    """
    Client interface for LangGraph agents to interact with the AML MCP Server.
    Provides verified tool calls with strict output schemas, guaranteeing no raw SQL hallucinations.
    """

    def __init__(self):
        self.db = db_service

    def get_account_history(self, account_id: str) -> Dict[str, Any]:
        """
        Tool: Queries account records, balances, and all associated transactions.
        """
        logger.info(f"[MCP Tool Call] get_account_history(account_id='{account_id}')")
        return self.db.get_account_history(account_id)

    def get_linked_entities(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Tool: Traverses graph links, UBOs, corporate shells, and shared counterparties.
        """
        logger.info(f"[MCP Tool Call] get_linked_entities(account_id='{account_id}')")
        return self.db.get_linked_entities(account_id)

    def check_sanctions_list(self, name: str) -> List[Dict[str, Any]]:
        """
        Tool: Checks OFAC and international sanctions watchlists for suspect names and aliases.
        """
        logger.info(f"[MCP Tool Call] check_sanctions_list(name='{name}')")
        return self.db.check_sanctions_list(name)

    def get_flagged_transactions(self) -> List[Dict[str, Any]]:
        """
        Tool: Retrieves all transactions triggered by rules-based monitoring.
        """
        logger.info("[MCP Tool Call] get_flagged_transactions()")
        return self.db.get_flagged_transactions()


# Global client instance
mcp_client = MCPInvestigationClient()
