import logging
from app.data.database import handle_sql_search

def sql_search(query):
    """Execute SQL-based search"""
    try:
        sql_results = handle_sql_search(query)
        
        # Format the results
        formatted_results = []
        for row in sql_results:
            formatted_results.append({
                "video_id": row.get("video_id", ""),
                "title": row.get("title", ""),
                "speaker": row.get("speaker", ""),
                "speaker_occupation": row.get("speaker_occupation", ""),
                "description": row.get("description", ""),
                "url": row.get("url", ""),
                "content": row.get("content", ""),
                "tags": row.get("tags", []),
                "views": row.get("views", 0)
            })
        
        logging.info(f"SQL search found {len(formatted_results)} results")
        return formatted_results
        
    except Exception as e:
        logging.error(f"SQL search error: {str(e)}")
        return []