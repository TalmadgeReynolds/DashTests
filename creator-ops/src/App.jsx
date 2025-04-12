import { useState } from 'react';
import './App.css';
import Q1Trends from './components/Q1Trends';
import Q2ArchiveSearch from './components/Q2ArchiveSearch';
import Q3ClipBuilder from './components/Q3ClipBuilder';
import Q4Planner from './components/Q4Planner';

function App() {
  return (
    <div className="App">
      <header>
        <h1 style={{ color: '#ff0000', marginBottom: '30px' }}>Creator Dashboard</h1>
      </header>
      
      <div className="grid-container">
        <Q1Trends className="grid-item" />
        <Q2ArchiveSearch className="grid-item" />
        <Q3ClipBuilder className="grid-item" />
        <Q4Planner className="grid-item" />
      </div>
    </div>
  );
}

export default App;
