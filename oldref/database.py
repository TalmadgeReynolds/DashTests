import logging
import pandas as pd
from sqlalchemy import create_engine, text
from tenacity import retry, stop_after_attempt, wait_exponential
import psutil
import time
from functools import wraps

from app.config import DB_CONFIG

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024
        
        logging.info(f"Performance - {func.__name__}:")
        logging.info(f"  Time: {end_time - start_time:.2f} seconds")
        logging.info(f"  Memory: {memory_end - memory_start:.1f}MB increased")
        
        return result
    return wrapper

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_db_connection():
    """Get database connection with retry logic"""
    connection_string = (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    return create_engine(connection_string)

@monitor_performance
def load_ted_data():
    """Load TED talks data from RDS database with speaker_occupation."""
    try:
        logging.info("Connecting to TED talks database...")
        engine = get_db_connection()
        
        # Query to join videos and transcripts, making sure to include speaker_occupation
        query = text("""
            SELECT 
                v.video_id,
                v.title,
                v.speaker,
                v.speaker_occupation,  # Make sure this field is included
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
            
            first_row = None
            for row in df.itertuples(index=False):
                if first_row is None:
                    first_row = row._asdict()
                    print("DEBUG - First row fields:")
                    for key, value in first_row.items():
                        print(f"  {key}: {value}")
        
        logging.info(f"Successfully loaded {len(df)} talks from RDS")
        return df
    
    except Exception as e:
        logging.error(f"Failed to load TED talks data: {str(e)}")
        raise

def sql_search(query, limit=10):
    """Execute SQL-based search with speaker_occupation."""
    try:
        engine = get_db_connection()
        
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
        OR v.speaker_occupation ILIKE :query  # Add speaker_occupation to search criteria
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
        return []

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
        return []