import React from 'react';

const Header = ({ onForceEvent, isAnalyzing }) => {
  return (
    <div className="header">
      <div className="logo">
        <img 
          src="https://upload.wikimedia.org/wikipedia/commons/7/72/Effective_Programming_for_America_logo.svg" 
          alt="EPAM" 
          style={{
            height: '24px',
            width: 'auto',
            marginRight: '12px',
            filter: 'brightness(0) invert(1)'
          }}
        />
        <span style={{ fontSize: '18px' }}>Trading Intelligence Agent</span>
      </div>
      <div className="header-controls">
        <button 
          className="force-event-btn" 
          onClick={onForceEvent}
          disabled={isAnalyzing}
          style={{ 
            opacity: isAnalyzing ? 0.6 : 1,
            cursor: isAnalyzing ? 'not-allowed' : 'pointer'
          }}
        >
          <span style={{
            display: 'inline-block',
            animation: isAnalyzing ? 'spin 1s linear infinite' : 'none'
          }}>
            {isAnalyzing ? '🔄' : '🚨'}
          </span>
          <span>{isAnalyzing ? 'Analyzing...' : 'Force Event'}</span>
        </button>
      </div>
    </div>
  );
};

export default Header;
