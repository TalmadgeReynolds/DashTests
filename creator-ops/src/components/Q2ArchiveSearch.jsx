import React from 'react';

function Q2ArchiveSearch({ className }) {
  return (
    <div className={className}>
      <h2>Q2 Archive Search</h2>
      <div className="content">
        <p>Search and browse your content archive</p>
        <div className="search-container">
          <input 
            type="text" 
            placeholder="Search archives..." 
            style={{ 
              border: '1px solid #000000', 
              padding: '8px',
              width: '100%',
              marginBottom: '10px'
            }} 
          />
          <button className="theme-red" style={{ padding: '8px 16px', border: 'none', borderRadius: '4px' }}>
            Search
          </button>
        </div>
        <div className="results-preview theme-white" style={{ marginTop: '10px', padding: '10px', borderRadius: '4px' }}>
          <p>Recent archives will appear here</p>
        </div>
      </div>
    </div>
  );
}

export default Q2ArchiveSearch;
