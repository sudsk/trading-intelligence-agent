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
          key={client.client_id}  
          className={`client-item ${selectedClient === client.client_id ? 'active' : ''}`}  
          onClick={() => onSelectClient(client.client_id)}  
        >
          <div className="client-name">{client.name || client.client_id}</div>  
          <div className="client-segment">{client.segment || 'N/A'}</div>  
          <div className="client-meta">
            <span className="client-tag">{client.sector}</span>  
            <div className="switch-prob">
              <span className={`switch-prob-value ${getProbClass(client.switch_prob || 0)}`}>  
                {(client.switch_prob || 0).toFixed(2)}  
              </span>
              <span 
                className="trend-arrow" 
                style={{ color: getProbColor(client.switch_prob || 0) }}  
              >
                {getTrendArrow(client.switch_prob || 0)}  
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ClientList;
