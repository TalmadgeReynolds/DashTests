import React, { useState, useEffect } from 'react';

function Q2ArchiveSearch({ className }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);
  const [showSummary, setShowSummary] = useState(false);
  const [summary, setSummary] = useState('');
  const [apiError, setApiError] = useState(null);

  // API base URL - change this to your FastAPI server URL
  const API_BASE_URL = 'http://localhost:8000';

  // Perform search by calling the API
  const performSearch = async (query) => {
    if (!query.trim()) return;
    
    setIsLoading(true);
    setApiError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      setSearchResults(data.results);
    } catch (error) {
      console.error("Search failed:", error);
      setSearchResults([]);
      setApiError("Failed to fetch search results. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Get summary by calling the API
  const getSummary = async (result, query) => {
    setIsLoading(true);
    setApiError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          results: [result],
          query,
          // Optional parameters:
          // user_profile: { role: "Editor" },
          // context_boost: "audience engagement"
        }),
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      setSummary(data.summary);
      setShowSummary(true);
    } catch (error) {
      console.error("Summary generation failed:", error);
      setSummary("Failed to generate summary. Please try again.");
      setApiError("Failed to generate insights. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setShowSummary(false);
    setSelectedResult(null);
    performSearch(searchQuery);
  };

  const handleResultClick = (result) => {
    setSelectedResult(result);
    setShowSummary(false);
  };

  return (
    <div className={className}>
      <h2>Q2 Archive Search</h2>
      <div className="content">
        <p>Search and browse your content archive</p>
        <form onSubmit={handleSearch} className="search-container">
          <input 
            type="text" 
            placeholder="Search archives..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ 
              border: '1px solid #000000', 
              padding: '8px',
              width: '100%',
              marginBottom: '10px'
            }} 
          />
          <button 
            type="submit"
            disabled={isLoading}
            className="theme-red" 
            style={{ 
              padding: '8px 16px', 
              border: 'none', 
              borderRadius: '4px',
              opacity: isLoading ? 0.7 : 1
            }}
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </form>
        
        <div className="results-container" style={{ marginTop: '10px', overflow: 'auto', maxHeight: '150px' }}>
          {apiError && (
            <div className="error-message theme-white" style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ff0000' }}>
              <p style={{ color: '#ff0000' }}>{apiError}</p>
            </div>
          )}
          
          {isLoading && !showSummary && (
            <div className="loading-indicator theme-white" style={{ padding: '10px', borderRadius: '4px' }}>
              <p>Searching archives...</p>
            </div>
          )}
          
          {!isLoading && searchResults.length === 0 && searchQuery && !apiError && (
            <div className="no-results theme-white" style={{ padding: '10px', borderRadius: '4px' }}>
              <p>No results found for "{searchQuery}"</p>
            </div>
          )}
          
          {!isLoading && !showSummary && searchResults.length > 0 && (
            <div>
              {searchResults.map((result, index) => (
                <div 
                  key={index} 
                  className={`result-item theme-white ${selectedResult === result ? 'selected' : ''}`}
                  onClick={() => handleResultClick(result)}
                  style={{ 
                    padding: '10px', 
                    marginBottom: '8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    border: selectedResult === result ? '2px solid #ff0000' : '1px solid #ff0000',
                    textAlign: 'left'
                  }}
                >
                  <h4 style={{ margin: '0 0 5px 0', fontSize: '1rem', color: '#ff0000' }}>{result.title}</h4>
                  <p style={{ margin: '0 0 5px 0', fontSize: '0.8rem' }}>
                    <strong>{result.speaker}</strong> {result.speaker_occupation ? `· ${result.speaker_occupation}` : ''}
                  </p>
                  <p style={{ margin: '0', fontSize: '0.9rem' }}>{result.description.substring(0, 100)}...</p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '5px' }}>
                    <span style={{ fontSize: '0.8rem' }}>{result.views ? result.views.toLocaleString() : '0'} views</span>
                    <div>
                      {result.tags && result.tags.slice(0, 2).map((tag, i) => (
                        <span 
                          key={i} 
                          style={{ 
                            fontSize: '0.7rem',
                            padding: '2px 5px',
                            backgroundColor: '#f0f0f0',
                            borderRadius: '3px',
                            marginLeft: '5px'
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {selectedResult && !showSummary && (
            <div className="selected-actions" style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px' }}>
              <button 
                className="theme-white"
                style={{ padding: '5px 10px', borderRadius: '4px', fontSize: '0.8rem' }}
                onClick={() => setSelectedResult(null)}
              >
                Back to results
              </button>
              <button 
                className="theme-red"
                style={{ padding: '5px 10px', borderRadius: '4px', fontSize: '0.8rem' }}
                onClick={() => getSummary(selectedResult, searchQuery)}
                disabled={isLoading}
              >
                Generate Insights
              </button>
            </div>
          )}
          
          {showSummary && (
            <div className="summary-container">
              {isLoading ? (
                <div className="loading-indicator theme-white" style={{ padding: '10px', borderRadius: '4px' }}>
                  <p>Generating insights...</p>
                </div>
              ) : (
                <div className="summary-content" style={{ textAlign: 'left' }}>
                  <div className="summary-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <h4 style={{ margin: '0' }}>AI-Generated Insights</h4>
                    <button 
                      className="theme-white"
                      style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '0.8rem' }}
                      onClick={() => setShowSummary(false)}
                    >
                      Back
                    </button>
                  </div>
                  <div className="summary-text theme-white" style={{ padding: '10px', borderRadius: '4px', fontSize: '0.9rem', whiteSpace: 'pre-line' }}>
                    {summary}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Q2ArchiveSearch;
