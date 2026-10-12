import React from 'react';
import { Database, AlertOctagon, Check } from 'lucide-react';

export default function TransactionTable({ transactions }) {
  return (
    <div className="card-panel">
      <div className="panel-header">
        <div className="panel-title-wrap">
          <Database size={17} className="title-icon" />
          <h3 className="panel-title">MCP Ground-Truth Transactions</h3>
        </div>
        <span className="log-counter">{transactions.length} Records Extracted</span>
      </div>

      <div className="table-scroll-wrap">
        <table className="mcp-table">
          <thead>
            <tr>
              <th>TX ID</th>
              <th>Type</th>
              <th>Amount (USD)</th>
              <th>Source / Destination</th>
              <th>Timestamp</th>
              <th>Compliance Status</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 ? (
              <tr>
                <td colSpan="6" className="table-empty">
                  No transaction records loaded yet.
                </td>
              </tr>
            ) : (
              transactions.map((tx) => {
                const isFlagged = tx.is_flagged === 1;
                return (
                  <tr key={tx.transaction_id} className={isFlagged ? 'flagged-row' : ''}>
                    <td className="mono font-bold">{tx.transaction_id}</td>
                    <td>
                      <span className="tx-type-pill">{tx.transaction_type}</span>
                    </td>
                    <td className={`mono font-semibold ${isFlagged ? 'amount-flagged' : ''}`}>
                      ${tx.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="mono text-muted-subtle">
                      {tx.source_account} → {tx.dest_account}
                    </td>
                    <td className="mono text-muted-subtle">
                      {tx.timestamp ? tx.timestamp.slice(0, 16).replace('T', ' ') : 'N/A'}
                    </td>
                    <td>
                      {isFlagged ? (
                        <span className="status-flagged-tag" title={tx.flag_reason}>
                          <AlertOctagon size={12} />
                          <span>FLAGGED: {tx.flag_reason?.slice(0, 28)}...</span>
                        </span>
                      ) : (
                        <span className="status-clean-tag">
                          <Check size={12} />
                          <span>CLEAN</span>
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
