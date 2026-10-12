"""
Model Context Protocol (MCP) Server for AML Investigation.
Provides secure, deterministic tool-based access to the banking database
preventing SQL hallucination and ensuring audited data access.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Path to the SQLite AML database
DEFAULT_DB_PATH = Path("data/database/aml_transactions.db")

logger = logging.getLogger("mcp_aml_server")
logging.basicConfig(level=logging.INFO)


class AMLDatabaseService:
    """Encapsulates secure database operations for the AML MCP Server."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            # Auto-initialize if database does not exist yet
            from mcp_server.mock_db import init_database
            init_database(self.db_path)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_account_history(self, account_id: str) -> Dict[str, Any]:
        """
        Retrieves comprehensive account profile, risk rating, balance,
        and chronological transaction history for a specific account.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Fetch Account Details
        cursor.execute(
            "SELECT * FROM accounts WHERE account_id = ?", (account_id,)
        )
        account_row = cursor.fetchone()
        if not account_row:
            conn.close()
            return {"error": f"Account with ID '{account_id}' not found."}

        account = dict(account_row)

        # 2. Fetch Transactions (inbound & outbound)
        cursor.execute(
            """
            SELECT * FROM transactions 
            WHERE source_account = ? OR dest_account = ?
            ORDER BY timestamp DESC
            """,
            (account_id, account_id),
        )
        transactions = [dict(row) for row in cursor.fetchall()]

        # 3. Calculate Aggregates
        total_inflow = sum(
            t["amount"] for t in transactions if t["dest_account"] == account_id
        )
        total_outflow = sum(
            t["amount"] for t in transactions if t["source_account"] == account_id
        )
        flagged_txs = [t for t in transactions if t["is_flagged"] == 1]

        conn.close()
        return {
            "account_id": account["account_id"],
            "account_name": account["account_name"],
            "account_type": account["account_type"],
            "country": account["country"],
            "risk_rating": account["risk_rating"],
            "balance": account["balance"],
            "created_at": account["created_at"],
            "total_transactions": len(transactions),
            "total_inflow_usd": round(total_inflow, 2),
            "total_outflow_usd": round(total_outflow, 2),
            "flagged_count": len(flagged_txs),
            "flagged_transactions": flagged_txs,
            "transactions": transactions,
        }

    def get_linked_entities(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Traverses corporate graph connections, beneficial owners (UBOs),
        and associated counterparties linked to the given account.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Direct entities associated with account
        cursor.execute(
            """
            SELECT * FROM entities 
            WHERE associated_accounts LIKE ?
            """,
            (f"%{account_id}%",),
        )
        direct_entities = [dict(row) for row in cursor.fetchall()]

        # Trace related entities through shared UBOs or shared accounts
        enriched_graph = []
        for ent in direct_entities:
            ubo = ent.get("ultimate_beneficial_owner")
            related_nodes = []
            if ubo:
                cursor.execute(
                    """
                    SELECT entity_id, name, entity_type, jurisdiction, associated_accounts
                    FROM entities 
                    WHERE ultimate_beneficial_owner = ? AND entity_id != ?
                    """,
                    (ubo, ent["entity_id"]),
                )
                related_nodes = [dict(r) for r in cursor.fetchall()]

            enriched_graph.append({
                **ent,
                "shared_ubo_entities": related_nodes
            })

        conn.close()
        return enriched_graph

    def check_sanctions_list(self, name: str) -> List[Dict[str, Any]]:
        """
        Performs watchlist screening against OFAC, UN, and international
        sanctions records, including alias matching.
        """
        if not name or len(name.strip()) < 2:
            return []

        search_term = f"%{name.strip().lower()}%"
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM sanctions_list 
            WHERE LOWER(name) LIKE ? OR LOWER(aliases) LIKE ?
            """,
            (search_term, search_term),
        )
        matches = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return matches

    def get_flagged_transactions(self) -> List[Dict[str, Any]]:
        """
        Returns all transactions currently flagged by automated rules
        awaiting SAR investigation.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.*, a.account_name as source_account_name, d.account_name as dest_account_name
            FROM transactions t
            LEFT JOIN accounts a ON t.source_account = a.account_id
            LEFT JOIN accounts d ON t.dest_account = d.account_id
            WHERE t.is_flagged = 1
            ORDER BY t.timestamp DESC
            """
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Returns all accounts for explorer navigation."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts ORDER BY risk_rating DESC, account_id ASC")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results


# Global Singleton Service
db_service = AMLDatabaseService()


# -------------------------------------------------------------
# Official FastMCP Server Definition
# -------------------------------------------------------------
try:
    from mcp.server.fastmcp import FastMCP
    mcp_app = FastMCP(
        "AML Investigation Database Server",
        dependencies=["sqlite3", "pydantic"]
    )

    @mcp_app.tool()
    def get_account_history(account_id: str) -> str:
        """Retrieve complete transaction history, balances, and risk profile for an account ID."""
        data = db_service.get_account_history(account_id)
        return json.dumps(data, indent=2)

    @mcp_app.tool()
    def get_linked_entities(account_id: str) -> str:
        """Retrieve corporate entities, beneficial owners (UBOs), and graph relationships for an account ID."""
        data = db_service.get_linked_entities(account_id)
        return json.dumps(data, indent=2)

    @mcp_app.tool()
    def check_sanctions_list(name: str) -> str:
        """Screen an individual or company name against OFAC / international sanctions watchlists."""
        data = db_service.check_sanctions_list(name)
        return json.dumps(data, indent=2)

    @mcp_app.tool()
    def get_flagged_transactions() -> str:
        """Retrieve all currently flagged suspicious transactions requiring compliance investigation."""
        data = db_service.get_flagged_transactions()
        return json.dumps(data, indent=2)

except ImportError:
    mcp_app = None


if __name__ == "__main__":
    if mcp_app:
        print("Starting official FastMCP AML Server on stdio...")
        mcp_app.run()
    else:
        print("FastMCP module not available; running standalone database sanity test.")
        flagged = db_service.get_flagged_transactions()
        print(f"Flagged transactions found: {len(flagged)}")
