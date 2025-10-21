import React from 'react';

const ProfileCard = ({ profile }) => {
  if (!profile) return null;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">{profile.clientId}</div>
          <div className="card-subtitle">Relationship Manager: {profile.rm}</div>
        </div>
        <div className="badge">{Math.round(profile.confidence * 100)}% Confidence</div>
      </div>

      <div className="metrics-grid">
        <div className="metric">
          <div className="metric-label">Strategy Segment</div>
          <div className="metric-value">{profile.segment}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Switch Probability (14d)</div>
          <div className="metric-value" style={{ color: 'var(--uui-critical-60)' }}>
            {profile.switchProb.toFixed(2)}
          </div>
        </div>
        <div className="metric">
          <div className="metric-label">Primary Exposure</div>
          <div className="metric-value">{profile.primaryExposure}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Risk Flag</div>
          <div className="metric-value" style={{ color: 'var(--uui-warning-60)' }}>
            {profile.riskFlags?.[0] || 'None'}
          </div>
        </div>
      </div>

      <div>
        <div className="section-title">Key Drivers</div>
        <div className="chips">
          {profile.drivers?.map((driver, idx) => (
            <span key={idx} className="chip">
              {driver}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProfileCard;
