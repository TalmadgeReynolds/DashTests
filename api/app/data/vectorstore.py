import logging
import os
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from app.config import FAISS_INDEX_DIR, OPENAI_API_KEY

def get_retriever():
    """Get or create a vector store retriever."""
    try:
        # Set API key
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        # Check if FAISS index exists
        if not os.path.exists(FAISS_INDEX_DIR):
            logging.warning(f"FAISS index not found at {FAISS_INDEX_DIR}")
            logging.warning("Creating mock vector store for development")
            
            # Create a mock vector store
            mock_docs = [
                Document(
                    page_content="Mock vector content 1",
                    metadata={
                        "video_id": "1",
                        "title": "Mock Vector Talk 1",
                        "speaker": "Jane Doe",
                        "speaker_occupation": "AI Researcher",
                        "description": "Mock vector description 1",
                        "url": "https://example.com/1",
                        "tags": ["AI", "Tech"],
                        "views": 25000
                    }
                ),
                Document(
                    page_content="Mock vector content 2",
                    metadata={
                        "video_id": "2",
                        "title": "Mock Vector Talk 2",
                        "speaker": "John Smith",
                        "speaker_occupation": "Tech Educator",
                        "description": "Mock vector description 2",
                        "url": "https://example.com/2",
                        "tags": ["Education", "Programming"],
                        "views": 15000
                    }
                ),
                Document(
                    page_content="Mock vector content 3",
                    metadata={
                        "video_id": "3",
                        "title": "Mock Vector Talk 3",
                        "speaker": "Alex Johnson",
                        "speaker_occupation": "Senior Developer",
                        "description": "Mock vector description 3",
                        "url": "https://example.com/3",
                        "tags": ["Development", "Leadership"],
                        "views": 8000
                    }
                )
            ]
            
            # Create embeddings using OpenAI
            embeddings = OpenAIEmbeddings()
            
            # Create a vector store from mock docs
            vectorstore = FAISS.from_documents(mock_docs, embeddings)
            
            # Create a retriever
            return vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # Load the existing FAISS index
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.load_local(FAISS_INDEX_DIR, embeddings)
        
        # Create a retriever
        return vectorstore.as_retriever(search_kwargs={"k": 5})
        
    except Exception as e:
        logging.error(f"Failed to get retriever: {str(e)}")
        # Create a fake retriever that returns mock data
        logging.warning("Creating mock vector store retriever")
        
        # Create a mock vector store
        mock_docs = [
            Document(
                page_content="Mock vector content 1",
                metadata={
                    "video_id": "1",
                    "title": "Mock Vector Talk 1",
                    "speaker": "Jane Doe",
                    "speaker_occupation": "AI Researcher",
                    "description": "Mock vector description 1",
                    "url": "https://example.com/1",
                    "tags": ["AI", "Tech"],
                    "views": 25000
                }
            ),
            Document(
                page_content="Mock vector content 2",
                metadata={
                    "video_id": "2",
                    "title": "Mock Vector Talk 2",
                    "speaker": "John Smith",
                    "speaker_occupation": "Tech Educator",
                    "description": "Mock vector description 2",
                    "url": "https://example.com/2",
                    "tags": ["Education", "Programming"],
                    "views": 15000
                }
            ),
            Document(
                page_content="Mock vector content 3",
                metadata={
                    "video_id": "3",
                    "title": "Mock Vector Talk 3",
                    "speaker": "Alex Johnson",
                    "speaker_occupation": "Senior Developer",
                    "description": "Mock vector description 3",
                    "url": "https://example.com/3",
                    "tags": ["Development", "Leadership"],
                    "views": 8000
                }
            )
        ]
        
        # Create embeddings using OpenAI if API key is available
        if OPENAI_API_KEY:
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.from_documents(mock_docs, embeddings)
            return vectorstore.as_retriever(search_kwargs={"k": 3})
        else:
            # Create a dummy retriever that just returns the mock docs
            class MockRetriever:
                def invoke(self, query):
                    return mock_docs
            return MockRetriever()