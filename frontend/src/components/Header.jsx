import React from 'react';
import { ShieldAlert, Activity, ExternalLink, Cpu } from 'lucide-react';

export default function Header({ status }) {
  const isReady =
    status?.database === 'CONNECTED' ||
    status?.ai_service?.status === 'CONNECTED' ||
    status?.ai_service?.details?.database === 'CONNECTED' ||
    status?.status === 'HEALTHY';

  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-logo">
          <ShieldAlert size={24} className="logo-icon" />
          <span className="logo-tag">FinCEN AI</span>
        </div>
        <div>
          <h1 className="header-title">Autonomous AML Investigation & SAR Agent</h1>
          <p className="header-subtitle">
            LangGraph Multi-Agent • Model Context Protocol (MCP) • Local RAG • Phoenix Observability
          </p>
        </div>
      </div>

      <div className="header-actions">
        <div className="status-pill">
          <span className="pulsing-dot" />
          <span className="status-text">{isReady ? 'MCP & RAG Ready' : 'Connecting...'}</span>
        </div>

        <div className="zero-model-tag" title="Zero heavy models downloaded locally: Cloud API & Local Embeddings">
          <Cpu size={14} />
          <span>Zero Heavy Local Models</span>
        </div>

        <a 
          href="http://localhost:6006" 
          target="_blank" 
          rel="noreferrer" 
          className="phoenix-button"
          title="Open Arize Phoenix OpenTelemetry tracing dashboard"
        >
          <Activity size={15} />
          <span>Phoenix Traces (:6006)</span>
          <ExternalLink size={12} />
        </a>
      </div>
    </header>
  );
}
