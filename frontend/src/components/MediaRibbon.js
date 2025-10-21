import React from 'react';

const MediaRibbon = ({ media }) => {
  if (!media || !media.headlines) return null;

  const getSentimentClass = (sentiment) => {
    return `sentiment sentiment-${sentiment}`;
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'Just now';
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    return `${Math.floor(diffHours / 24)} days ago`;
  };

  return (
    <div className="card">
      <div className="media-header">
        <div className="media-title">Media Intelligence</div>
        <div className={`media-pressure pressure-${media.pressure.toLowerCase()}`}>
          Media Pressure: {media.pressure}
        </div>
      </div>
      <div className="headlines">
        {media.headlines.slice(0, 3).map((headline, idx) => (
          <div key={idx} className="headline-card">
            <div className="headline-text">{headline.title}</div>
            <div className="headline-meta">
              <span className="headline-time">
                {formatTime(headline.timestamp)}
              </span>
              <span className={getSentimentClass(headline.sentiment)}>
                {headline.sentiment.charAt(0).toUpperCase() + headline.sentiment.slice(1)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MediaRibbon;
