"""
FastAPI Server for Autonomous AML Investigation & SAR Agent.
Wraps the LangGraph multi-agent system, MCP database tools, RAG knowledge base,
and Arize Phoenix telemetry in a high-performance REST API.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Internal Modules
from mcp_server.server import db_service
from rag.vector_store import rag_service
from agents.workflow import run_aml_investigation
from agents.evaluator import evaluate_sar_faithfulness
from observability.phoenix_tracker import setup_phoenix_observability

# Initialize FastAPI App
app = FastAPI(
    title="Autonomous AML Investigation & FinCEN SAR Agent API",
    description="Enterprise multi-agent system using LangGraph, Model Context Protocol, and local RAG.",
    version="1.0.0"
)

# Enable CORS for external dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

UI_FILE_PATH = Path("ui/index.html")
FRONTEND_DIST = Path("frontend/dist")

# Mount React static assets if built
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


# Request/Response Schemas
class InvestigateRequest(BaseModel):
    account_id: str = Field(default="ACC-883910", description="Target bank account ID to investigate")
    case_id: Optional[str] = Field(default=None, description="Optional custom case ID")


class StandaloneEvalRequest(BaseModel):
    sar_text: str
    ground_truth_accounts: List[str]
    ground_truth_amounts: List[float]
    ground_truth_entities: Optional[List[str]] = []
    ground_truth_sanctions: Optional[List[str]] = []


@app.on_event("startup")
async def startup_event():
    """Initializes RAG knowledge base and starts Arize Phoenix telemetry."""
    print("Initializing Regulatory RAG knowledge base...")
    rag_service.initialize_vector_store()
    
    # Launch Arize Phoenix local telemetry
    port = int(os.getenv("PHOENIX_PORT", 6006))
    setup_phoenix_observability(port=port)
    print("AML Agent service startup sequence complete.")


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the interactive React JSX compliance executive dashboard UI."""
    if (FRONTEND_DIST / "index.html").exists():
        return (FRONTEND_DIST / "index.html").read_text(encoding="utf-8")
    if UI_FILE_PATH.exists():
        return UI_FILE_PATH.read_text(encoding="utf-8")
    return "<h1>Autonomous AML Investigation Dashboard</h1><p>UI file not found.</p>"


@app.get("/api/health")
async def health_check():
    """Returns system status across database, vector store, and agents."""
    return {
        "status": "HEALTHY",
        "database": "CONNECTED",
        "mcp_server": "READY",
        "rag_chroma": "INITIALIZED",
        "phoenix_tracing": "ENABLED" if os.getenv("PHOENIX_ENABLE", "true").lower() == "true" else "DISABLED"
    }


@app.get("/api/accounts")
async def list_accounts():
    """Lists all accounts in the core banking database."""
    return db_service.get_all_accounts()


@app.get("/api/accounts/{account_id}")
async def get_account_details(account_id: str):
    """Retrieves account history and linked graph entities from MCP server."""
    history = db_service.get_account_history(account_id)
    if "error" in history:
        raise HTTPException(status_code=404, detail=history["error"])
    linked = db_service.get_linked_entities(account_id)
    return {
        **history,
        "linked_entities": linked
    }


@app.get("/api/alerts")
async def list_flagged_alerts():
    """Lists all flagged transactions requiring AML investigation."""
    return db_service.get_flagged_transactions()


@app.post("/api/investigate")
async def investigate_account_endpoint(req: InvestigateRequest):
    """
    Executes the autonomous LangGraph 4-agent investigation:
    1. Data Gatherer (MCP)
    2. Compliance Analyst (RAG)
    3. SAR Writer (FinCEN BSA Form 111)
    4. Evaluator Guardrail (Hallucination & Factual Verification)
    """
    try:
        case_result = run_aml_investigation(
            account_id=req.account_id,
            case_id=req.case_id
        )
        return case_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation workflow error: {str(e)}")


@app.post("/api/eval")
async def standalone_evaluation_endpoint(req: StandaloneEvalRequest):
    """
    Standalone endpoint to evaluate faithfulness and detect hallucinations
    in any generated SAR narrative against raw truth data.
    """
    fake_draft = {"full_sar_text": req.sar_text, "narrative_summary": ""}
    result = evaluate_sar_faithfulness(
        sar_draft=fake_draft,
        ground_truth_accounts=req.ground_truth_accounts,
        ground_truth_amounts=req.ground_truth_amounts,
        ground_truth_entities=req.ground_truth_entities,
        ground_truth_sanctions=req.ground_truth_sanctions
    )
    return result


@app.post("/api/benchmark/run")
async def run_benchmark_endpoint():
    """
    Executes the Arize Phoenix offline evaluation benchmark suite across golden datasets,
    populating Datasets, Experiments, Evaluators, and Prompts in Phoenix.
    """
    try:
        from observability.seed_phoenix_benchmarks import seed_phoenix_benchmarks
        phoenix_url = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
        exp = seed_phoenix_benchmarks(base_url=phoenix_url)
        return {
            "status": "SUCCESS",
            "message": "Phoenix Benchmark & Evaluation suite executed successfully.",
            "phoenix_dashboard_url": phoenix_url,
            "experiment_id": getattr(exp, "experiment_id", "completed")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phoenix benchmark failed: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
