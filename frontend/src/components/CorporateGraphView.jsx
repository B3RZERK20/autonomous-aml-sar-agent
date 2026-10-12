import React from 'react';
import { Network, Building2, User, Globe, AlertTriangle } from 'lucide-react';

export default function CorporateGraphView({ linkedEntities, sanctionsFindings }) {
  return (
    <div className="card-panel">
      <div className="panel-header">
        <div className="panel-title-wrap">
          <Network size={17} className="title-icon" />
          <h3 className="panel-title">Corporate Graph & UBO Linkages</h3>
        </div>
        <span className="log-counter">{linkedEntities.length} Entities Discovered</span>
      </div>

      {sanctionsFindings && sanctionsFindings.length > 0 && (
        <div className="sanctions-alert-banner">
          <AlertTriangle size={18} className="alert-icon" />
          <div>
            <strong>CRITICAL OFAC SANCTIONS MATCH:</strong>
            <p>
              Screening identified positive SDN match for {sanctionsFindings[0].name} ({sanctionsFindings[0].program}).
              Designation: {sanctionsFindings[0].notes}
            </p>
          </div>
        </div>
      )}

      <div className="entities-grid">
        {linkedEntities.length === 0 ? (
          <div className="entities-empty">No graph linkages loaded yet.</div>
        ) : (
          linkedEntities.map((ent) => {
            const isShell = ent.entity_type === 'SHELL_CORP' || ent.entity_type === 'OFFSHORE_CORP';
            return (
              <div key={ent.entity_id} className={`entity-node-card ${isShell ? 'high-risk-entity' : ''}`}>
                <div className="entity-card-header">
                  <div className="entity-icon-type">
                    {ent.entity_type === 'INDIVIDUAL' ? <User size={15} /> : <Building2 size={15} />}
                    <span>{ent.entity_type}</span>
                  </div>
                  <span className="entity-jurisdiction">
                    <Globe size={12} />
                    <span>{ent.jurisdiction}</span>
                  </span>
                </div>

                <div className="entity-name">{ent.name}</div>

                <div className="entity-details">
                  <div className="detail-row">
                    <span className="label">Accounts:</span>
                    <span className="mono val">{ent.associated_accounts}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Ultimate Beneficial Owner:</span>
                    <span className="val ubo-highlight">{ent.ultimate_beneficial_owner || 'Undisclosed'}</span>
                  </div>
                  {ent.address && (
                    <div className="detail-row">
                      <span className="label">Address:</span>
                      <span className="val">{ent.address}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
