import React from 'react';

const ProfileCard = ({ profile, onRefresh }) => {  // ← Add onRefresh prop
  if (!profile) return null;
  
  // Format the timestamp
  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Unknown';
    const now = new Date();
    const analyzed = new Date(timestamp);
    const diffMs = now - analyzed;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };
  
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">{profile.clientId}</div>
          <div className="card-subtitle">Relationship Manager: {profile.rm}</div>
          {/* ← Add Last Analyzed timestamp */}
          {profile.analyzed_at && (
            <div className="card-subtitle" style={{ fontSize: '0.85em', color: 'var(--uui-neutral-50)' }}>
              Last analyzed: {formatTimeAgo(profile.analyzed_at)}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div className="badge">{Math.round(profile.confidence * 100)}% Confidence</div>
        </div>
      </div>
      
      <div className="metrics-grid">
        <div className="metric">
          <div className="metric-label">Strategy Segment</div>
          <div className="metric-value">{profile.segment}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Switch Probability (14d)</div>
          <div className="metric-value" style={{ color: 'var(--uui-critical-60)' }}>
            {profile.switchProb ? profile.switchProb.toFixed(2) : '0'}
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
