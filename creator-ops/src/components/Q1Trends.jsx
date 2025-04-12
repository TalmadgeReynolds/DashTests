import React from 'react';

function Q1Trends({ className }) {
  return (
    <div className={className}>
      <h2>Q1 Trends</h2>
      <div className="content">
        <p>Analytics and trending content for Q1 2025</p>
        <div className="stats-container">
          <div className="stat theme-red">
            <h3>Views</h3>
            <p>1.2M</p>
          </div>
          <div className="stat theme-black">
            <h3>Engagement</h3>
            <p>24.5%</p>
          </div>
          <div className="stat theme-white">
            <h3>Growth</h3>
            <p>+12%</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Q1Trends;
