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
              {alert.clientId}: Switch Prob ↑ {alert.oldSwitchProb?.toFixed(2)} → {alert.newSwitchProb?.toFixed(2)} (media-driven). 
              Client drifting Risk-Off.
            </div>
          </div>
        </div>
        <button 
          className="action-btn btn-primary" 
          style={{ width: 'auto', flex: 0, alignSelf: 'flex-start', marginTop: 0 }}
          onClick={onDismiss}
        >
          Take Action
        </button>
      </div>
    </div>
  );
};

export default AlertBanner;
