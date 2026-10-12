#!/bin/sh
set -e

echo "=========================================================="
echo "Starting FinCEN AML Investigation System in Docker..."
echo "=========================================================="

# 1. Initialize SQLite database & seed AML cases
echo "[1/3] Initializing and seeding SQLite AML database..."
python mcp_server/mock_db.py

# 2. Index FinCEN & FATF regulations into Chroma vector DB
echo "[2/3] Indexing regulatory corpus into local ChromaDB..."
python rag/vector_store.py

# 3. Start Python FastAPI in background
echo "[3/3] Launching Python AI LangGraph core on port 8000..."
uvicorn api.main:app --host 127.0.0.1 --port 8000 &
PYTHON_PID=$!

# Wait for Python core to be responsive
echo "Waiting for Python core to initialize..."
until curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; do
  sleep 1
done
echo "Python AI Core is live and healthy!"

# 4. Start Node.js API Gateway & React frontend on port 5000
echo "Launching Node.js API Gateway & React Suite on port 5000..."
cd /app/backend-node
export PYTHON_AI_URL="http://127.0.0.1:8000"
export NODE_PORT="5000"
exec node src/server.js
