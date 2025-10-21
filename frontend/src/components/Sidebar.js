import React from 'react';
import ClientList from './ClientList';

const Sidebar = ({ clients, selectedClient, onSelectClient }) => {
  return (
    <div className="sidebar">
      <div className="list-header">
        <div className="list-title">Clients with Rising Switch Risk</div>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginTop: '12px' 
        }}>
          <div style={{ fontSize: '12px', color: 'var(--uui-text-secondary)' }}>
            1-{Math.min(10, clients.length)} of {clients.length}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', color: 'var(--uui-text-tertiary)' }}>
              Sort by:
            </span>
            <select 
              style={{
                background: 'var(--uui-neutral-70)',
                border: '1px solid var(--uui-neutral-60)',
                color: 'var(--uui-text-primary)',
                padding: '3px 6px',
                borderRadius: '3px',
                fontSize: '12px',
                fontFamily: 'var(--uui-font)',
                cursor: 'pointer'
              }}
            >
              <option>Switch Probability</option>
              <option>Client Name</option>
              <option>Segment</option>
              <option>Risk Level</option>
            </select>
          </div>
        </div>
      </div>
      <ClientList 
        clients={clients}
        selectedClient={selectedClient}
        onSelectClient={onSelectClient}
      />
    </div>
  );
};

export default Sidebar;
