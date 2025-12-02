import React from 'react';

const Timeline = ({ timeline }) => {
  if (!timeline || timeline.length === 0) return null;

  return (
    <div className="card">
      <div className="section-title" style={{ marginBottom: '18px' }}>
        Strategy Evolution Timeline
      </div>
      <div className="timeline">
        {Array.isArray(timeline) && timeline.map((item, idx) => (
          <div key={idx} className="timeline-item">
            <div className="timeline-marker"></div>
            <div className="timeline-content">
              <div className="timeline-date">{item.period}</div>
              <div className="timeline-event">
                {item.segment} - {item.description}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Timeline;
