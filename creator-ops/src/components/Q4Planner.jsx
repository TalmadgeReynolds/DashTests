import React from 'react';

function Q4Planner({ className }) {
  return (
    <div className={className}>
      <h2>Q4 Planner</h2>
      <div className="content">
        <p>Plan your content schedule for Q4 2025</p>
        <div className="calendar-grid" style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(7, 1fr)',
          gap: '4px',
          marginTop: '10px'
        }}>
          {Array(28).fill().map((_, i) => (
            <div key={i} style={{ 
              height: '25px', 
              border: '1px solid #000', 
              backgroundColor: i % 3 === 0 ? '#ff0000' : i % 5 === 0 ? '#000000' : '#ffffff',
              color: (i % 3 === 0 || i % 5 === 0) ? '#ffffff' : '#000000'
            }}>
              {i + 1}
            </div>
          ))}
        </div>
        <button 
          className="theme-red" 
          style={{ 
            marginTop: '15px', 
            padding: '8px 16px', 
            border: 'none', 
            borderRadius: '4px', 
            width: '100%' 
          }}
        >
          Schedule New Content
        </button>
      </div>
    </div>
  );
}

export default Q4Planner;
