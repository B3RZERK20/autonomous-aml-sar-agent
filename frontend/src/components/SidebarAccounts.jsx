import React from 'react';
import { UserCheck, AlertTriangle, ShieldCheck, Play, Loader2, FlaskConical, ExternalLink } from 'lucide-react';

export default function SidebarAccounts({ 
  accounts, 
  selectedAccountId, 
  onSelectAccount, 
  onInvestigate, 
  loading,
  onRunBenchmark,
  benchmarkLoading,
  benchmarkSuccess
}) {
  return (
    <aside className="sidebar-container">
      <div className="sidebar-header">
        <h2 className="sidebar-title">Suspect Accounts</h2>
        <span className="alert-count-badge">
          {accounts.filter(a => a.risk_rating === 'HIGH').length} High Risk Alerts
        </span>
      </div>

      <div className="accounts-list">
        {accounts.map(acc => {
          const isSelected = acc.account_id === selectedAccountId;
          const isHigh = acc.risk_rating === 'HIGH';

          return (
            <div
              key={acc.account_id}
              className={`account-card ${isSelected ? 'active' : ''}`}
              onClick={() => onSelectAccount(acc.account_id)}
            >
              <div className="card-top-row">
                <span className="card-account-id">{acc.account_id}</span>
                <span className={`risk-tag ${isHigh ? 'risk-high' : 'risk-low'}`}>
                  {isHigh ? (
                    <>
                      <AlertTriangle size={11} />
                      <span>HIGH RISK</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck size={11} />
                      <span>LOW RISK</span>
                    </>
                  )}
                </span>
              </div>

              <div className="card-account-name">{acc.account_name}</div>

              <div className="card-bottom-row">
                <span className="card-country">{acc.country} • {acc.account_type}</span>
                <span className="card-balance">${acc.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="sidebar-actions">
        <button
          className="btn-primary-action"
          onClick={onInvestigate}
          disabled={loading || benchmarkLoading}
        >
          {loading ? (
            <>
              <Loader2 size={18} className="spin-icon" />
              <span>Agents Investigating...</span>
            </>
          ) : (
            <>
              <Play size={18} fill="currentColor" />
              <span>Run Autonomous Investigation</span>
            </>
          )}
        </button>

        <button
          className="btn-secondary-benchmark"
          onClick={onRunBenchmark}
          disabled={loading || benchmarkLoading}
          title="Runs Phoenix evaluation benchmark suite across golden test datasets, populating Datasets, Experiments, Evaluators, and Prompts in Phoenix"
        >
          {benchmarkLoading ? (
            <>
              <Loader2 size={16} className="spin-icon" />
              <span>Running Phoenix Benchmark...</span>
            </>
          ) : (
            <>
              <FlaskConical size={16} />
              <span>Run Phoenix Benchmark & Evals</span>
            </>
          )}
        </button>

        {benchmarkSuccess && (
          <div className="benchmark-success-pill">
            <span>✅ Phoenix Benchmark Complete!</span>
            <a href="http://localhost:6006" target="_blank" rel="noreferrer">
              Open Phoenix Dashboard (:6006) <ExternalLink size={11} style={{ display: 'inline', verticalAlign: 'middle' }} />
            </a>
          </div>
        )}
      </div>
    </aside>
  );
}
