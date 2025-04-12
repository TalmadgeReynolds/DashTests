import logging
import pandas as pd
from sqlalchemy import create_engine, text
from tenacity import retry, stop_after_attempt, wait_exponential
import time
from functools import wraps

from app.config import DB_CONFIG

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        logging.info(f"Performance - {func.__name__}: {end_time - start_time:.2f} seconds")
        
        return result
    return wrapper

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_db_connection():
    """Get database connection with retry logic"""
    try:
        connection_string = (
            f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        return create_engine(connection_string)
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        # Return a mock engine for development
        return None

@monitor_performance
def load_ted_data():
    """Load TED talks data from database with speaker_occupation."""
    try:
        logging.info("Connecting to TED talks database...")
        engine = get_db_connection()
        
        if engine is None:
            # Return mock data for development
            logging.warning("Using mock data since database connection failed")
            return pd.DataFrame({
                "video_id": ["1", "2", "3"],
                "title": ["Mock Talk 1", "Mock Talk 2", "Mock Talk 3"],
                "speaker": ["Jane Doe", "John Smith", "Alex Johnson"],
                "speaker_occupation": ["AI Researcher", "Tech Educator", "Senior Developer"],
                "description": ["Mock description 1", "Mock description 2", "Mock description 3"],
                "url": ["https://example.com/1", "https://example.com/2", "https://example.com/3"],
                "tags": [["AI", "Tech"], ["Education", "Programming"], ["Development", "Leadership"]],
                "views": [25000, 15000, 8000],
                "published_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "full_transcript": ["Mock transcript 1", "Mock transcript 2", "Mock transcript 3"]
            })
        
        # Query to join videos and transcripts, making sure to include speaker_occupation
        query = text("""
            SELECT 
                v.video_id,
                v.title,
                v.speaker,
                v.speaker_occupation,
                v.description,
                v.url,
                v.tags,
                v.views,
                v.published_date,
                STRING_AGG(t.text, ' ' ORDER BY t.paragraph_index) as full_transcript
            FROM videos v
            JOIN transcripts t ON v.video_id = t.video_id
            GROUP BY 
                v.video_id, v.title, v.speaker, v.speaker_occupation,
                v.description, v.url, v.tags, v.views, v.published_date
        """)
        
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        
        logging.info(f"Successfully loaded {len(df)} talks from database")
        return df
    
    except Exception as e:
        logging.error(f"Failed to load TED talks data: {str(e)}")
        # Return mock data for development
        return pd.DataFrame({
            "video_id": ["1", "2", "3"],
            "title": ["Mock Talk 1", "Mock Talk 2", "Mock Talk 3"],
            "speaker": ["Jane Doe", "John Smith", "Alex Johnson"],
            "speaker_occupation": ["AI Researcher", "Tech Educator", "Senior Developer"],
            "description": ["Mock description 1", "Mock description 2", "Mock description 3"],
            "url": ["https://example.com/1", "https://example.com/2", "https://example.com/3"],
            "tags": [["AI", "Tech"], ["Education", "Programming"], ["Development", "Leadership"]],
            "views": [25000, 15000, 8000],
            "published_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "full_transcript": ["Mock transcript 1", "Mock transcript 2", "Mock transcript 3"]
        })

def handle_sql_search(query, limit=10):
    """
    Execute a SQL-based search against the TED talks database.
    
    Args:
        query (str): The search query string
        limit (int): Maximum number of results to return
        
    Returns:
        list: List of matching TED talks with all metadata
    """
    try:
        engine = get_db_connection()
        
        if engine is None:
            # Return mock data for development
            logging.warning("Using mock data since database connection failed")
            mock_results = []
            for i in range(3):
                mock_results.append({
                    "video_id": f"{i+1}",
                    "title": f"Content about '{query}'",
                    "speaker": ["Jane Doe", "John Smith", "Alex Johnson"][i],
                    "speaker_occupation": ["AI Researcher", "Tech Educator", "Senior Developer"][i],
                    "description": f"This is a discussion about {query} and its implications.",
                    "url": f"https://example.com/{i+1}",
                    "views": [25000, 15000, 8000][i],
                    "tags": [["AI", "Tech"], ["Education", "Programming"], ["Development", "Leadership"]][i],
                    "content": f"Detailed content about {query}... This would be actual transcript content."
                })
            return mock_results
        
        # Create a search pattern for SQL LIKE queries
        search_pattern = f"%{query}%"
        
        sql = """
        SELECT DISTINCT 
            v.video_id, 
            v.title, 
            v.speaker, 
            v.speaker_occupation, 
            v.description, 
            v.url, 
            v.views, 
            v.tags 
        FROM videos v 
        WHERE v.title ILIKE :query 
        OR v.description ILIKE :query 
        OR v.speaker ILIKE :query
        OR v.speaker_occupation ILIKE :query
        LIMIT :limit
        """
        
        with engine.connect() as conn:
            result = conn.execute(
                text(sql), 
                {"query": search_pattern, "limit": limit}
            )
            
            # Format results similarly to vector search results
            formatted_results = []
            for row in result:
                formatted_results.append({
                    "video_id": row.video_id,
                    "title": row.title,
                    "speaker": row.speaker,
                    "speaker_occupation": row.speaker_occupation,
                    "description": row.description,
                    "url": row.url,
                    "views": row.views,
                    "tags": row.tags,
                    "content": row.description,  # Using description as content
                })
                
            return formatted_results
            
    except Exception as e:
        logging.error(f"SQL search error: {str(e)}")
        # Return mock data for development
        mock_results = []
        for i in range(3):
            mock_results.append({
                "video_id": f"{i+1}",
                "title": f"Content about '{query}'",
                "speaker": ["Jane Doe", "John Smith", "Alex Johnson"][i],
                "speaker_occupation": ["AI Researcher", "Tech Educator", "Senior Developer"][i],
                "description": f"This is a discussion about {query} and its implications.",
                "url": f"https://example.com/{i+1}",
                "views": [25000, 15000, 8000][i],
                "tags": [["AI", "Tech"], ["Education", "Programming"], ["Development", "Leadership"]][i],
                "content": f"Detailed content about {query}... This would be actual transcript content."
            })
        return mock_results