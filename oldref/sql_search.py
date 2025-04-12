import logging
from langchain.schema import Document
from app.data.database import handle_sql_search

def sql_search(query):
    """Execute SQL-based search"""
    try:
        sql_results = handle_sql_search(query)
        
        # Format the results
        formatted_results = []
        for row in sql_results:
            formatted_results.append({
                "type": "sql",
                "document": Document(
                    page_content=f"{row.title}\n{row.description}",
                    metadata={
                        "title": row.title,
                        "speaker": row.speaker,
                        "tags": row.tags if hasattr(row, 'tags') else [],
                        "views": row.views if hasattr(row, 'views') else 0
                    }
                ),
                "title": row.title,
                "speaker": row.speaker,
                "description": row.description if hasattr(row, 'description') else "",
                "content": row.description if hasattr(row, 'description') else "",
                "tags": row.tags if hasattr(row, 'tags') else [],
                "views": row.views if hasattr(row, 'views') else 0
            })
        
        logging.info(f"SQL search found {len(formatted_results)} results")
        return formatted_results
        
    except Exception as e:
        logging.error(f"SQL search error: {str(e)}")
        return []