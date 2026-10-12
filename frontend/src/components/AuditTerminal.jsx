import React, { useRef, useEffect } from 'react';
import { Terminal, Shield, BookOpen, PenTool, CheckCircle } from 'lucide-react';

export default function AuditTerminal({ auditLogs }) {
  const terminalRef = useRef(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [auditLogs]);

  const getAgentBadge = (agent) => {
    if (agent.includes('Gatherer')) {
      return (
        <span className="log-badge cyan">
          <Shield size={11} />
          <span>Data Gatherer</span>
        </span>
      );
    }
    if (agent.includes('Analyst')) {
      return (
        <span className="log-badge purple">
          <BookOpen size={11} />
          <span>Compliance Analyst</span>
        </span>
      );
    }
    if (agent.includes('Writer')) {
      return (
        <span className="log-badge amber">
          <PenTool size={11} />
          <span>SAR Writer</span>
        </span>
      );
    }
    if (agent.includes('Guardrail') || agent.includes('Evaluator')) {
      return (
        <span className="log-badge emerald">
          <CheckCircle size={11} />
          <span>Evaluator Guardrail</span>
        </span>
      );
    }
    return <span className="log-badge default">{agent}</span>;
  };

  return (
    <div className="card-panel">
      <div className="panel-header">
        <div className="panel-title-wrap">
          <Terminal size={17} className="title-icon" />
          <h3 className="panel-title">LangGraph Multi-Agent Audit Log</h3>
        </div>
        <span className="log-counter">{auditLogs.length} Events Captured</span>
      </div>

      <div className="terminal-body" ref={terminalRef}>
        {auditLogs.length === 0 ? (
          <div className="terminal-placeholder">
            Select an account on the left and click "Run Autonomous Investigation" to observe the agents.
          </div>
        ) : (
          auditLogs.map((log, index) => (
            <div key={index} className="terminal-row">
              <span className="log-timestamp">
                {log.timestamp ? log.timestamp.slice(11, 19) : '00:00:00'}
              </span>
              {getAgentBadge(log.agent)}
              <span className="log-message">{log.action}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
