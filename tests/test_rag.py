"""
Tests for Regulatory RAG Knowledge Base.
Verifies semantic retrieval of FinCEN BSA regulations and FATF recommendations.
"""

import pytest
from rag.vector_store import rag_service


def test_rag_query_structuring():
    """Verifies RAG retrieves 31 CFR 1010.311 and CTR threshold rules for structuring queries."""
    results = rag_service.query("What is the legal definition and threshold of structuring and smurfing?")
    assert len(results) >= 1
    combined_text = " ".join(r.get("text", "") for r in results)
    assert "structuring" in combined_text.lower()
    assert "10,000" in combined_text or "CTR" in combined_text


def test_rag_query_tbml():
    """Verifies RAG answers Trade-Based Money Laundering queries."""
    results = rag_service.query("What is trade-based money laundering and over-invoicing?")
    assert len(results) >= 1
    combined_text = " ".join(r.get("text", "") for r in results)
    assert "trade" in combined_text.lower() or "invoicing" in combined_text.lower()


def test_rag_query_fatf_ubo():
    """Verifies RAG retrieves FATF beneficial ownership guidelines."""
    results = rag_service.query("What are FATF recommendations on beneficial ownership and shell companies?")
    assert len(results) >= 1
    combined_text = " ".join(r.get("text", "") for r in results)
    assert "beneficial ownership" in combined_text.lower() or "ubo" in combined_text.lower()
