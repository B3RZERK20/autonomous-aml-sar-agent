/**
 * Node.js Backend & API Gateway for Autonomous AML Investigation System
 * Orchestrates requests between React JSX Frontend, Case Repository,
 * and the Python LangGraph Multi-Agent AI Microservice.
 */

const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });

const app = express();
const PORT = process.env.NODE_PORT || 5000;
const PYTHON_AI_URL = process.env.PYTHON_AI_URL || 'http://127.0.0.1:8000';

// In-memory case history database
const casesDatabase = new Map();

// Middleware
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// Static files for production React build if present
const frontendDist = path.resolve(__dirname, '../../frontend/dist');
app.use(express.static(frontendDist));

/**
 * Health check endpoint - aggregates status of Node Gateway & Python AI Service
 */
app.get('/api/health', async (req, res) => {
  let aiServiceStatus = 'DISCONNECTED';
  let aiHealthDetails = null;

  try {
    const response = await fetch(`${PYTHON_AI_URL}/api/health`, { signal: AbortSignal.timeout(3000) });
    if (response.ok) {
      aiServiceStatus = 'CONNECTED';
      aiHealthDetails = await response.json();
    }
  } catch (err) {
    aiServiceStatus = 'UNREACHABLE';
  }

  res.json({
    gateway: 'HEALTHY',
    status: aiServiceStatus === 'CONNECTED' ? 'HEALTHY' : 'DEGRADED',
    database: aiHealthDetails?.database || (aiServiceStatus === 'CONNECTED' ? 'CONNECTED' : 'DISCONNECTED'),
    mcp_server: aiHealthDetails?.mcp_server || 'READY',
    rag_chroma: aiHealthDetails?.rag_chroma || 'INITIALIZED',
    phoenix_tracing: aiHealthDetails?.phoenix_tracing || 'ENABLED',
    node_version: process.version,
    timestamp: new Date().toISOString(),
    ai_service: {
      status: aiServiceStatus,
      url: PYTHON_AI_URL,
      details: aiHealthDetails
    }
  });
});

/**
 * Get all accounts for investigator explorer
 */
app.get('/api/accounts', async (req, res) => {
  try {
    const response = await fetch(`${PYTHON_AI_URL}/api/accounts`);
    if (!response.ok) {
      throw new Error(`AI service returned ${response.status}`);
    }
    const accounts = await response.json();
    res.json(accounts);
  } catch (err) {
    console.error('[Node Gateway] Error fetching accounts:', err.message);
    res.status(502).json({ error: 'Failed to retrieve accounts from AI core', details: err.message });
  }
});

/**
 * Get specific account details, transaction history, and corporate graph links
 */
app.get('/api/accounts/:id', async (req, res) => {
  try {
    const accountId = req.params.id;
    const response = await fetch(`${PYTHON_AI_URL}/api/accounts/${accountId}`);
    if (!response.ok) {
      return res.status(response.status).json(await response.json());
    }
    const data = await response.json();
    res.json(data);
  } catch (err) {
    console.error(`[Node Gateway] Error fetching account ${req.params.id}:`, err.message);
    res.status(502).json({ error: 'Failed to retrieve account details', details: err.message });
  }
});

/**
 * Dispatch Autonomous Multi-Agent Investigation
 * Triggers LangGraph pipeline in Python microservice and persists case record
 */
app.post('/api/investigate', async (req, res) => {
  const { account_id, case_id } = req.body;
  if (!account_id) {
    return res.status(400).json({ error: 'account_id parameter is required.' });
  }

  console.log(`[Node Gateway] Initiating investigation for account: ${account_id}...`);
  const startTime = Date.now();

  try {
    const response = await fetch(`${PYTHON_AI_URL}/api/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account_id, case_id })
    });

    if (!response.ok) {
      const errBody = await response.text();
      throw new Error(`AI Service investigation failed: ${errBody}`);
    }

    const result = await response.json();
    const durationMs = Date.now() - startTime;

    // Enrich and persist case record in gateway memory
    const caseRecord = {
      ...result,
      gateway_received_at: new Date().toISOString(),
      execution_duration_ms: durationMs
    };

    if (result.case_id) {
      casesDatabase.set(result.case_id, caseRecord);
    }

    console.log(`[Node Gateway] Investigation complete for ${result.case_id} (${durationMs}ms). Faithfulness: ${result.evaluation?.faithfulness_score}`);
    res.json(caseRecord);
  } catch (err) {
    console.error('[Node Gateway] Investigation error:', err.message);
    res.status(500).json({ error: 'Investigation pipeline error', message: err.message });
  }
});

/**
 * Get list of past completed cases
 */
app.get('/api/cases', (req, res) => {
  const cases = Array.from(casesDatabase.values()).map(c => ({
    case_id: c.case_id,
    target_account_id: c.target_account_id,
    status: c.status,
    faithfulness_score: c.evaluation?.faithfulness_score,
    audit_verdict: c.evaluation?.audit_verdict,
    suspicious_amount: c.sar_draft?.suspicious_amount_total_usd,
    timestamp: c.gateway_received_at
  }));
  res.json(cases);
});

/**
 * Get full case file by Case ID
 */
app.get('/api/cases/:caseId', (req, res) => {
  const caseRecord = casesDatabase.get(req.params.caseId);
  if (!caseRecord) {
    return res.status(404).json({ error: `Case ${req.params.caseId} not found.` });
  }
  res.json(caseRecord);
});

/**
 * Standalone SAR Hallucination Evaluation Proxy
 */
app.post('/api/eval', async (req, res) => {
  try {
    const response = await fetch(`${PYTHON_AI_URL}/api/eval`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const result = await response.json();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Evaluator proxy error', details: err.message });
  }
});

/**
 * Trigger Arize Phoenix Offline Evaluation Benchmarks & Experiments
 */
app.post('/api/benchmark/run', async (req, res) => {
  try {
    const response = await fetch(`${PYTHON_AI_URL}/api/benchmark/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const result = await response.json();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Benchmark execution failed', details: err.message });
  }
});

// Fallback to React app for client-side routing (Express 5 compatible)
app.use((req, res) => {
  res.sendFile(path.join(frontendDist, 'index.html'), (err) => {
    if (err) {
      res.status(404).send('FinCEN AML Investigation System - React frontend bundle not found.');
    }
  });
});

// Start Express Gateway Server
app.listen(PORT, () => {
  console.log(`=======================================================`);
  console.log(`🚀 Node.js AML API Gateway live on http://127.0.0.1:${PORT}`);
  console.log(`🔗 Connecting to Python AI Core at: ${PYTHON_AI_URL}`);
  console.log(`=======================================================`);
});

module.exports = app;
