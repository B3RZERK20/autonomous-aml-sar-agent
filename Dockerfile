# ==============================================================================
# Production All-In-One Container: React JSX + Node Gateway + Python LangGraph
# Ultra-Fast Build Optimized with Astral uv, CPU PyTorch, and Multi-Stage Node
# ==============================================================================

# Stage 1: Fast React Frontend Build
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Runner
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1
ENV UV_SYSTEM_PYTHON=1
ENV NODE_ENV=production

WORKDIR /app

# Install curl for internal container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy official Astral uv binary (10-100x faster pip replacement)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy Node.js runtime directly from official node:20-slim (eliminates slow apt/NodeSource scripts)
COPY --from=node:20-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node:20-slim /usr/local/bin/npm /usr/local/bin/npm

# Ultra-fast Python install using uv + PyTorch CPU index (cuts 2.3+ GB of CUDA download)
COPY requirements.txt .
RUN uv pip install --system \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Install Node.js backend gateway dependencies
COPY backend-node/package*.json ./backend-node/
WORKDIR /app/backend-node
RUN npm ci --only=production
WORKDIR /app

# Copy application source code
COPY agents/ ./agents/
COPY api/ ./api/
COPY data/raw/ ./data/raw/
COPY mcp_server/ ./mcp_server/
COPY observability/ ./observability/
COPY rag/ ./rag/
COPY tests/ ./tests/
COPY backend-node/src/ ./backend-node/src/
COPY .env.example .

# Copy compiled React frontend bundle
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Entrypoint script
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Expose Node.js Gateway (5000), Python API (8000), Phoenix (6006)
EXPOSE 5000 8000 6006

ENTRYPOINT ["./docker-entrypoint.sh"]
