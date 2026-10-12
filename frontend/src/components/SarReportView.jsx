import React, { useState } from 'react';
import { FileCheck, Copy, Download, Check, ShieldCheck, Scale, AlertCircle } from 'lucide-react';

export default function SarReportView({ sarDraft, evaluation }) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('narrative');

  const fullText = sarDraft?.full_sar_text || 'No SAR narrative drafted yet. Run an investigation to generate.';
  const isApproved = evaluation?.audit_verdict === 'APPROVED' || evaluation?.is_faithful;
  const score = Math.round((evaluation?.faithfulness_score ?? 1.0) * 100);

  const handleCopy = () => {
    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadTxt = () => {
    const blob = new Blob([fullText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `FinCEN_SAR_${sarDraft?.subject_name?.replace(/[^a-zA-Z0-9]/g, '_') || 'CASE'}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="sar-card-container">
      <div className="sar-card-header">
        <div className="sar-header-left">
          <div className="sar-icon-wrap">
            <FileCheck size={22} />
          </div>
          <div>
            <h2 className="sar-title">FinCEN Suspicious Activity Report (BSA Form 111)</h2>
            <p className="sar-subtitle">
              Part V Narrative drafted by Agent 3 • Evaluated & Verified by Agent 4 Guardrail
            </p>
          </div>
        </div>

        <div className="sar-header-right">
          <div className={`guardrail-badge ${isApproved ? 'badge-verified' : 'badge-alert'}`}>
            <ShieldCheck size={16} />
            <span>{isApproved ? `✓ ${score}% Faithfulness Approved` : `⚠ Revision Required (${score}%)`}</span>
          </div>

          <button className="sar-btn" onClick={handleCopy} title="Copy full SAR narrative to clipboard">
            {copied ? (
              <>
                <Check size={15} className="text-emerald" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <Copy size={15} />
                <span>Copy SAR</span>
              </>
            )}
          </button>

          <button className="sar-btn primary" onClick={handleDownloadTxt} title="Download official FinCEN filing text">
            <Download size={15} />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      <div className="sar-tabs-bar">
        <button 
          className={`sar-tab ${activeTab === 'narrative' ? 'active' : ''}`}
          onClick={() => setActiveTab('narrative')}
        >
          BSA Form 111 Narrative
        </button>
        <button 
          className={`sar-tab ${activeTab === 'regulations' ? 'active' : ''}`}
          onClick={() => setActiveTab('regulations')}
        >
          <Scale size={14} />
          <span>Statutory Citations ({sarDraft?.regulatory_violations?.length || 0})</span>
        </button>
        <button 
          className={`sar-tab ${activeTab === 'actions' ? 'active' : ''}`}
          onClick={() => setActiveTab('actions')}
        >
          <AlertCircle size={14} />
          <span>Recommended Dispositions ({sarDraft?.recommended_actions?.length || 0})</span>
        </button>
      </div>

      <div className="sar-content-body">
        {activeTab === 'narrative' && (
          <pre className="sar-narrative-text">{fullText}</pre>
        )}

        {activeTab === 'regulations' && (
          <div className="regulations-list">
            {(sarDraft?.regulatory_violations || []).map((reg, idx) => (
              <div key={idx} className="regulation-card">
                <Scale size={18} className="reg-icon" />
                <div className="reg-text">{reg}</div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'actions' && (
          <div className="actions-list">
            {(sarDraft?.recommended_actions || []).map((act, idx) => (
              <div key={idx} className="action-card">
                <span className="action-number">{idx + 1}</span>
                <span className="action-text">{act}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
