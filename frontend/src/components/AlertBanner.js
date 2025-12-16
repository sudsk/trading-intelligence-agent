import React from 'react';

const AlertBanner = ({ alert, onDismiss }) => {
  if (!alert) return null;

  return (
    <div className="alert-banner active">
      <div className="alert-content">
        <div className="alert-text">
          <span className="alert-icon">⚠️</span>
          <div>
            <div className="alert-title">Switch Probability Alert</div>
            <div className="alert-message">
              {alert.clientId}: Switch Prob {alert.change > 0 ? '↑' : '↓'}{' '}
              {(alert.oldSwitchProb * 100).toFixed(0)}% → {(alert.newSwitchProb * 100).toFixed(0)}%{' '}
              ({alert.reason}). Client drifting Risk-Off.
            </div>
          </div>
        </div>
        <button 
          className="alert-close"
          onClick={onDismiss}
          aria-label="Close alert"
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default AlertBanner;
