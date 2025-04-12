import React from 'react';

function Q3ClipBuilder({ className }) {
  return (
    <div className={className}>
      <h2>Q3 Clip Builder</h2>
      <div className="content">
        <p>Create and edit content clips for social media</p>
        <div className="timeline" style={{ 
          height: '60px', 
          background: '#f0f0f0', 
          border: '1px solid #000000',
          borderRadius: '4px',
          position: 'relative',
          marginBottom: '10px'
        }}>
          <div style={{ 
            position: 'absolute', 
            height: '100%', 
            width: '30%', 
            background: '#ff0000', 
            opacity: '0.7' 
          }}></div>
        </div>
        <div className="controls" style={{ display: 'flex', justifyContent: 'space-between' }}>
          <button className="theme-black" style={{ padding: '6px 12px', borderRadius: '4px' }}>Cut</button>
          <button className="theme-red" style={{ padding: '6px 12px', borderRadius: '4px' }}>Export</button>
          <button className="theme-white" style={{ padding: '6px 12px', borderRadius: '4px' }}>Save</button>
        </div>
      </div>
    </div>
  );
}

export default Q3ClipBuilder;
