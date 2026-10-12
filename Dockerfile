# ==============================================================================
# Production All-In-One Container: React JSX + Node Gateway + Python LangGraph
# ==============================================================================

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Final Production Runner (Python + Node.js)
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1
ENV NODE_ENV=production

WORKDIR /app

# Install system dependencies, curl, and Node.js 20
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js backend dependencies
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

# Expose Node.js Unified Gateway (5000), Python API (8000), Phoenix (6006)
EXPOSE 5000 8000 6006

ENTRYPOINT ["./docker-entrypoint.sh"]
