import logging
import math
from typing import List, Dict, Any

from app.search.vector_search import vector_search
from app.search.sql_search import sql_search

def rerank_results(results, query):
    """Rerank results based on relevance to query with enhanced scoring"""
    query_terms = set(query.lower().split())
    
    def calculate_score(result):
        content = result.get('content', '').lower()
        title = result.get('title', '').lower()
        speaker = result.get('speaker', '').lower()
        occupation = result.get('speaker_occupation', '').lower()
        
        # Calculate basic term matches
        term_matches = sum(1 for term in query_terms if term in content)
        
        # Add metadata-based boosts
        title_boost = 3 if any(term in title for term in query_terms) else 1
        speaker_boost = 2 if any(term in speaker for term in query_terms) else 1
        
        # Add occupation boost
        occupation_boost = 1.5 if occupation and any(term in occupation for term in query_terms) else 1
        
        # Boost for talks with higher views (popularity signal)
        view_boost = 1
        views = result.get('views', 0)
        if views:
            try:
                views = int(views)
                # Logarithmic scaling to prevent very popular talks from dominating
                view_boost = 1 + (0.3 * (math.log10(views) / 7)) if views > 0 else 1
            except (ValueError, TypeError):
                pass
                
        # Combine all factors
        final_score = term_matches * title_boost * speaker_boost * occupation_boost * view_boost
        
        return final_score
    
    return sorted(results, key=calculate_score, reverse=True)

def hybrid_search(query: str) -> Dict[str, Any]:
    """Execute hybrid search using SQL and vector search"""
    try:
        # Get vector results
        logging.info(f"Attempting vector search for: {query}")
        vector_results = vector_search(query)
        logging.info(f"Vector search found {len(vector_results)} results")
        
        # Get SQL results
        logging.info(f"Attempting SQL search for: {query}")
        sql_results = sql_search(query)
        logging.info(f"SQL search found {len(sql_results)} results")
        
        # Combine results
        combined_results = []
        
        # Add vector search results
        for result in vector_results:
            simplified_result = {
                "title": result.get("title", "Unknown Title"),
                "speaker": result.get("speaker", "Unknown Speaker"),
                "speaker_occupation": result.get("speaker_occupation", ""),
                "description": result.get("description", ""),
                "content": result.get("content", ""),
                "url": result.get("url", ""),
                "views": result.get("views", 0),
                "tags": result.get("tags", [])
            }
            combined_results.append(simplified_result)
            
        # Add SQL results (avoiding duplicates by checking titles)
        existing_titles = {r['title'] for r in combined_results}
        for result in sql_results:
            if result.get('title') not in existing_titles:
                simplified_result = {
                    "title": result.get("title", "Unknown Title"),
                    "speaker": result.get("speaker", "Unknown Speaker"),
                    "speaker_occupation": result.get("speaker_occupation", ""),
                    "description": result.get("description", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                    "views": result.get("views", 0),
                    "tags": result.get("tags", [])
                }
                combined_results.append(simplified_result)
                existing_titles.add(result.get('title', ''))
        
        logging.info(f"Combined {len(combined_results)} results")
        
        # Rerank combined results
        ranked_results = rerank_results(combined_results, query)
        
        # Return the final results
        return {
            "results": ranked_results,
            "count": len(ranked_results)
        }
            
    except Exception as e:
        logging.error(f"Hybrid search error: {str(e)}")
        # Return empty results on error
        return {
            "results": [],
            "count": 0
        }