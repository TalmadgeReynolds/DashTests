import logging
from app.data.vectorstore import get_retriever

def vector_search(query):
    """Execute vector-based search."""
    try:
        retriever = get_retriever()
        results = retriever.invoke(query)
        
        processed_results = []
        for doc in results:
            # Extract data from document
            metadata = doc.metadata
            
            processed_results.append({
                "video_id": metadata.get("video_id"),
                "title": metadata.get("title", ""),
                "speaker": metadata.get("speaker", ""),
                "speaker_occupation": metadata.get("speaker_occupation", ""),
                "description": metadata.get("description", ""),
                "url": metadata.get("url", ""),
                "content": doc.page_content,
                "tags": metadata.get("tags", []),
                "views": metadata.get("views", 0),
            })
        
        return processed_results
    except Exception as e:
        logging.error(f"Vector search error: {str(e)}")
        return []