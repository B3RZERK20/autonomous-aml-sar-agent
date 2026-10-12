"""
Tests for Model Context Protocol (MCP) Tools.
Verifies secure database access, schema outputs, and prevention of raw SQL hallucinations.
"""

import pytest
from mcp_server.client import mcp_client
from mcp_server.server import db_service


def test_mcp_get_account_history():
    """Verifies get_account_history MCP tool retrieves accurate account profile and transactions."""
    history = mcp_client.get_account_history("ACC-883910")
    assert "account_id" in history
    assert history["account_id"] == "ACC-883910"
    assert history["risk_rating"] == "HIGH"
    assert history["total_transactions"] >= 5
    assert history["flagged_count"] >= 4
    assert len(history["flagged_transactions"]) >= 4


def test_mcp_get_linked_entities():
    """Verifies get_linked_entities MCP tool correctly traverses corporate graph and UBOs."""
    entities = mcp_client.get_linked_entities("ACC-883910")
    assert isinstance(entities, list)
    assert len(entities) >= 1
    names = [e["name"] for e in entities]
    assert any("Apex Horizon" in n or "Derrick Sterling" in n for n in names)


def test_mcp_check_sanctions_list():
    """Verifies check_sanctions_list MCP tool screens against OFAC sanctions watchlists."""
    # Test positive match for designated Russian maritime operator
    matches = mcp_client.check_sanctions_list("Viktor Krumov")
    assert len(matches) >= 1
    assert matches[0]["program"] == "OFAC-RUSSIA-EO14024"
    assert "oil price caps" in matches[0]["notes"].lower()

    # Test negative match for clean subject
    clean_matches = mcp_client.check_sanctions_list("Nonexistent Clean Person")
    assert len(clean_matches) == 0


def test_mcp_get_flagged_transactions():
    """Verifies get_flagged_transactions returns currently open compliance alerts."""
    flagged = mcp_client.get_flagged_transactions()
    assert isinstance(flagged, list)
    assert len(flagged) >= 4
    for tx in flagged:
        assert tx["is_flagged"] == 1
        assert tx["flag_reason"] is not None
