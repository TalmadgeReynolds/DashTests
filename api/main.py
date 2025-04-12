import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.search.hybrid_search import hybrid_search
from app.search.llm_summarizer import synthesize_answer

# Create the FastAPI application
app = FastAPI(
    title="Creator-Ops Archive Search API",
    description="API for searching and summarizing content archives",
    version="1.0.0"
)

# Add CORS middleware to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str

class SummaryRequest(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    user_profile: Optional[Dict[str, Any]] = None
    context_boost: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int

class SummaryResponse(BaseModel):
    summary: str

@app.get("/")
async def root():
    """API root endpoint"""
    return {"message": "Creator-Ops Archive Search API"}

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search the content archive using hybrid search"""
    logging.info(f"Search request received with query: {request.query}")
    
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    results = hybrid_search(request.query)
    
    return {
        "results": results["results"],
        "count": results["count"]
    }

@app.post("/summary", response_model=SummaryResponse)
async def get_summary(request: SummaryRequest):
    """Generate a summary for the selected content"""
    logging.info(f"Summary request received for query: {request.query}")
    
    if not request.results:
        raise HTTPException(status_code=400, detail="No results provided for summarization")
    
    summary = synthesize_answer(
        results=request.results,
        query=request.query, 
        user_profile=request.user_profile, 
        context_boost=request.context_boost
    )
    
    return {"summary": summary}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}