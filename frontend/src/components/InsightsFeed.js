import React, { useState } from 'react';

const InsightsFeed = ({ insights }) => {
  const [filter, setFilter] = useState('All');

  if (!insights || insights.length === 0) return null;

  const filteredInsights = filter === 'All' 
    ? insights 
    : insights.filter(i => i.type === filter.toUpperCase());

  const getIconForType = (type) => {
    switch (type) {
      case 'SIGNAL': return '📊';
      case 'ACTION': return '✅';
      case 'OUTCOME': return '💰';
      default: return '📝';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
    }
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="card">
      <div className="insights-header">
        <div className="insights-title">Insights Feed</div>
        <div className="filter-chips">
          {['All', 'Signals', 'Actions', 'Outcomes'].map(f => (
            <span
              key={f}
              className={`filter-chip ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f}
            </span>
          ))}
        </div>
      </div>
      <div className="insights-list">
        {filteredInsights.map((insight, idx) => (
          <div key={idx} className="insight-item">
            <div className={`insight-icon ${insight.type.toLowerCase()}`}>
              {getIconForType(insight.type)}
            </div>
            <div className="insight-content">
              <div className="insight-header-row">
                <span className="insight-type">{insight.type}</span>
                <span className={`severity-chip severity-${insight.severity.toLowerCase()}`}>
                  {insight.severity}
                </span>
                <span className="timestamp">
                  {formatTimestamp(insight.timestamp)}
                </span>
              </div>
              <div className="insight-message">{insight.message}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default InsightsFeed;
