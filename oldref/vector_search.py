import logging
from langchain.schema import Document
from app.data.vectorstore import get_retriever
from app.data.database import load_ted_data
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

def vector_search(query):
    """Execute vector-based search."""
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
            "speaker_occupation": metadata.get("speaker_occupation", ""),  # Ensure this field is included
            "description": metadata.get("description", ""),
            "url": metadata.get("url", ""),
            "content": doc.page_content,
            "tags": metadata.get("tags", []),
            "views": metadata.get("views", 0),
        })
    
    return processed_results

def regenerate_faiss_index():
    """Regenerate the FAISS index from database"""
    # Create directory for FAISS index
    os.makedirs("faiss_index", exist_ok=True)

    # Load data from database
    print("Loading data from database...")
    df = load_ted_data()
    print(f"Loaded {len(df)} talks from database")

    # Process the data for vectorization
    print("Processing data for vectorization...")
    documents = []
    for _, row in df.iterrows():
        documents.append({
            "page_content": row["full_transcript"],
            "metadata": {
                "video_id": row["video_id"],
                "title": row["title"],
                "speaker": row["speaker"],
                "description": row["description"],
                "url": row["url"],
                "tags": row["tags"],
                "views": row["views"]
            }
        })

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.create_documents([doc["page_content"] for doc in documents], 
                                            metadatas=[doc["metadata"] for doc in documents])

    # Create embeddings and vectorstore
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(splits, embeddings)

    # Save the index
    vectorstore.save_local("faiss_index")
    print("FAISS index created and saved successfully!")