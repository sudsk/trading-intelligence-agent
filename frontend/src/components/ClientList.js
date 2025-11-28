import React from 'react';

const ClientList = ({ clients, selectedClient, onSelectClient }) => {
  const getProbClass = (prob) => {
    if (prob > 0.5) return 'prob-high';
    if (prob > 0.3) return 'prob-medium';
    return 'prob-low';
  };

  const getProbColor = (prob) => {
    if (prob > 0.5) return 'var(--uui-critical-60)';
    if (prob > 0.3) return 'var(--uui-warning-60)';
    return 'var(--uui-info-60)';
  };

  const getTrendArrow = (prob) => {
    if (prob > 0.5) return '↑';
    if (prob > 0.3) return '→';
    return '↓';
  };

  return (
    <div className="client-list">
      {clients.map((client) => (
        <div
          key={client.client_id}  {/* ← Changed */}
          className={`client-item ${selectedClient === client.client_id ? 'active' : ''}`}  {/* ← Changed */}
          onClick={() => onSelectClient(client.client_id)}  {/* ← Changed */}
        >
          <div className="client-name">{client.name || client.client_id}</div>  {/* ← Changed */}
          <div className="client-segment">{client.segment || 'N/A'}</div>  {/* ← Added fallback */}
          <div className="client-meta">
            <span className="client-tag">{client.sector}</span>  {/* ← Changed from primaryExposure */}
            <div className="switch-prob">
              <span className={`switch-prob-value ${getProbClass(client.switch_prob || 0)}`}>  {/* ← Changed */}
                {(client.switch_prob || 0).toFixed(2)}  {/* ← Changed */}
              </span>
              <span 
                className="trend-arrow" 
                style={{ color: getProbColor(client.switch_prob || 0) }}  {/* ← Changed */}
              >
                {getTrendArrow(client.switch_prob || 0)}  {/* ← Changed */}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ClientList;
