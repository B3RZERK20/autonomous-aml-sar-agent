"""
Arize Phoenix Observability Integration.
Initializes local OpenTelemetry tracing and starts the local Phoenix UI at http://localhost:6006
Captures latency, token counts, agent spans, and multi-agent execution steps (100% Free & Local).
"""

import os
import sys
import logging
from typing import Optional, Any

# Ensure UTF-8 output on Windows to prevent charmap emoji encoding errors
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("aml_phoenix")

_PHOENIX_SESSION = None
_INSTRUMENTED = False


def setup_phoenix_observability(port: int = 6006) -> Optional[Any]:
    """
    Launches the Phoenix local tracing server and instruments LangChain / LangGraph.
    """
    global _PHOENIX_SESSION, _INSTRUMENTED

    if os.getenv("PHOENIX_ENABLE", "true").lower() != "true":
        logger.info("Phoenix observability disabled via environment variable.")
        return None

    if _PHOENIX_SESSION is not None:
        return _PHOENIX_SESSION

    try:
        import phoenix as px
        from openinference.instrumentation.langchain import LangChainInstrumentor
        import io

        # Launch local Phoenix server safely on Windows without charmap crashes
        logger.info(f"Launching Arize Phoenix local telemetry UI on port {port}...")
        
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        try:
            if hasattr(sys.stdout, "buffer"):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "buffer"):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
            host = os.getenv("PHOENIX_HOST", "0.0.0.0")
            _PHOENIX_SESSION = px.launch_app(host=host, port=port)
        finally:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr

        logger.info(f"Arize Phoenix dashboard live at: http://localhost:{port}")

        # Instrument LangChain & LangGraph
        if not _INSTRUMENTED:
            LangChainInstrumentor().instrument()
            _INSTRUMENTED = True
            logger.info("LangChain / LangGraph OpenInference tracing successfully attached.")

        return _PHOENIX_SESSION
    except Exception as e:
        logger.warning(f"Could not initialize Arize Phoenix: {e}. Workflow will run without Phoenix UI.")
        return None


if __name__ == "__main__":
    session = setup_phoenix_observability(6006)
    if session:
        print(f"Phoenix UI is active at: {session.url}")
    else:
        print("Phoenix setup completed.")
