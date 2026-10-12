import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import SidebarAccounts from './components/SidebarAccounts';
import AgentFlowTracker from './components/AgentFlowTracker';
import StatsOverview from './components/StatsOverview';
import AuditTerminal from './components/AuditTerminal';
import TransactionTable from './components/TransactionTable';
import CorporateGraphView from './components/CorporateGraphView';
import SarReportView from './components/SarReportView';
import './App.css';

export default function App() {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccountId, setSelectedAccountId] = useState('ACC-883910');
  const [accountDetails, setAccountDetails] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);

  // Investigation State
  const [investigating, setInvestigating] = useState(false);
  const [activeStep, setActiveStep] = useState(0); // 0 = idle, 1 = gatherer, 2 = analyst, 3 = writer, 4 = evaluator, 5 = done
  const [caseResult, setCaseResult] = useState(null);
  const [activeTab, setActiveTab] = useState('transactions'); // 'transactions' | 'graph'

  // Fetch initial accounts and health status
  useEffect(() => {
    fetchHealth();
    fetchAccounts();
  }, []);

  // Fetch account history & graph when selected account changes
  useEffect(() => {
    if (selectedAccountId) {
      fetchAccountDetails(selectedAccountId);
    }
  }, [selectedAccountId]);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      setHealthStatus(data);
    } catch (err) {
      console.error('Health check failed:', err);
    }
  };

  const fetchAccounts = async () => {
    try {
      const res = await fetch('/api/accounts');
      const data = await res.json();
      setAccounts(data);
      if (data.length > 0 && !selectedAccountId) {
        setSelectedAccountId(data[0].account_id);
      }
    } catch (err) {
      console.error('Failed to load accounts:', err);
    }
  };

  const fetchAccountDetails = async (id) => {
    try {
      const res = await fetch(`/api/accounts/${id}`);
      const data = await res.json();
      setAccountDetails(data);
    } catch (err) {
      console.error('Failed to load account details:', err);
    }
  };

  const handleInvestigate = async () => {
    if (investigating) return;
    setInvestigating(true);
    setActiveStep(1);

    // Dynamic visual step progression
    const t1 = setTimeout(() => setActiveStep(2), 1200);
    const t2 = setTimeout(() => setActiveStep(3), 2400);
    const t3 = setTimeout(() => setActiveStep(4), 3600);

    try {
      const res = await fetch('/api/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_id: selectedAccountId }),
      });
      const data = await res.json();

      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);

      setActiveStep(5);
      setCaseResult(data);
    } catch (err) {
      console.error('Investigation failed:', err);
      alert('Investigation error: ' + err.message);
      setActiveStep(0);
    } finally {
      setInvestigating(false);
    }
  };

  const currentProfile = accountDetails || {
    account_id: selectedAccountId,
    account_name: 'Derrick Sterling / Apex Horizon LLC',
    country: 'USA',
  };

  const transactions = accountDetails?.transactions || [];
  const linkedEntities = accountDetails?.linked_entities || [];
  const sanctions = caseResult?.sanctions_findings || [];
  const auditLogs = caseResult?.audit_log || [];
  const sarDraft = caseResult?.sar_draft;
  const evaluation = caseResult?.evaluation;

  return (
    <div className="aml-app-layout">
      <Header status={healthStatus} />

      <main className="aml-main-content">
        <SidebarAccounts
          accounts={accounts}
          selectedAccountId={selectedAccountId}
          onSelectAccount={(id) => {
            setSelectedAccountId(id);
            setCaseResult(null);
            setActiveStep(0);
          }}
          onInvestigate={handleInvestigate}
          loading={investigating}
        />

        <section className="aml-workspace-area">
          <AgentFlowTracker activeStep={activeStep} />

          <StatsOverview
            accountProfile={currentProfile}
            sarDraft={sarDraft}
            evaluation={evaluation}
            status={caseResult?.status}
          />

          <div className="workspace-split-row">
            <AuditTerminal auditLogs={auditLogs} />

            <div className="panel-tabbed-container">
              <div className="panel-tabs-header">
                <button
                  className={`tab-btn ${activeTab === 'transactions' ? 'active' : ''}`}
                  onClick={() => setActiveTab('transactions')}
                >
                  MCP Transactions ({transactions.length})
                </button>
                <button
                  className={`tab-btn ${activeTab === 'graph' ? 'active' : ''}`}
                  onClick={() => setActiveTab('graph')}
                >
                  Corporate Graph & UBOs ({linkedEntities.length})
                </button>
              </div>

              {activeTab === 'transactions' ? (
                <TransactionTable transactions={transactions} />
              ) : (
                <CorporateGraphView
                  linkedEntities={linkedEntities}
                  sanctionsFindings={sanctions}
                />
              )}
            </div>
          </div>

          <SarReportView
            sarDraft={sarDraft}
            evaluation={evaluation}
          />
        </section>
      </main>
    </div>
  );
}
