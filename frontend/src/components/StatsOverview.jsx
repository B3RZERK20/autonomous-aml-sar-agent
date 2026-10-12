import React from 'react';
import { User, DollarSign, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function StatsOverview({ accountProfile, sarDraft, evaluation, status }) {
  const amount = sarDraft?.suspicious_amount_total_usd || 0;
  const faithfulness = Math.round((evaluation?.faithfulness_score ?? 1.0) * 100);
  const isApproved = evaluation?.audit_verdict === 'APPROVED' || evaluation?.is_faithful;

  return (
    <div className="stats-row">
      <div className="stat-card">
        <div className="stat-icon-wrap cyan">
          <User size={18} />
        </div>
        <div className="stat-details">
          <span className="stat-label">Investigation Subject</span>
          <span className="stat-value">{accountProfile?.account_name || 'Derrick Sterling'}</span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon-wrap rose">
          <DollarSign size={18} />
        </div>
        <div className="stat-details">
          <span className="stat-label">Suspicious Amount</span>
          <span className="stat-value rose-text">
            ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon-wrap emerald">
          <CheckCircle2 size={18} />
        </div>
        <div className="stat-details">
          <span className="stat-label">Faithfulness Score</span>
          <span className="stat-value emerald-text">{faithfulness}% Verified</span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon-wrap purple">
          <ShieldAlert size={18} />
        </div>
        <div className="stat-details">
          <span className="stat-label">Guardrail Verdict</span>
          <span className={`stat-badge ${isApproved ? 'badge-approved' : 'badge-revision'}`}>
            {evaluation?.audit_verdict || status || 'READY'}
          </span>
        </div>
      </div>
    </div>
  );
}
