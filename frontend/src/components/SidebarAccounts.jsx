import React from 'react';
import { UserCheck, AlertTriangle, ShieldCheck, Play, Loader2 } from 'lucide-react';

export default function SidebarAccounts({ 
  accounts, 
  selectedAccountId, 
  onSelectAccount, 
  onInvestigate, 
  loading 
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
          disabled={loading}
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
      </div>
    </aside>
  );
}
