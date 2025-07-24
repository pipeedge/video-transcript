from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import asyncio
import logging

from ..main import PodcastAnalyzer
from ..models.podcast import Episode, Insight, CleanedSegment

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Podcast Analysis API",
    description="AI-powered podcast analysis and insight extraction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the analyzer
analyzer = PodcastAnalyzer()

# Pydantic models for API requests/responses
class ProcessChannelRequest(BaseModel):
    channel_url: HttpUrl
    max_videos: Optional[int] = None

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    video_id: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 20

class SearchResponse(BaseModel):
    hits: List[Dict[str, Any]]
    total_hits: int
    processing_time_ms: int

# Global variable to track processing status
processing_status = {"is_processing": False, "current_video": "", "progress": 0}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Podcast Analysis API", "status": "running"}


@app.post("/process-channel")
async def process_channel(request: ProcessChannelRequest, background_tasks: BackgroundTasks):
    """
    Start processing a YouTube channel
    
    This endpoint starts the processing in the background and returns immediately.
    Use /status to check progress.
    """
    if processing_status["is_processing"]:
        raise HTTPException(status_code=400, detail="Another channel is currently being processed")
    
    # Start processing in background
    background_tasks.add_task(
        process_channel_background, 
        str(request.channel_url), 
        request.max_videos
    )
    
    return {"message": "Channel processing started", "status": "processing"}


async def process_channel_background(channel_url: str, max_videos: Optional[int]):
    """Background task for channel processing"""
    global processing_status
    
    try:
        processing_status["is_processing"] = True
        processing_status["current_video"] = "Discovering videos..."
        processing_status["progress"] = 0
        
        episodes = await analyzer.process_channel(channel_url, max_videos)
        
        processing_status["is_processing"] = False
        processing_status["current_video"] = "Completed"
        processing_status["progress"] = 100
        
        logger.info(f"Background processing completed: {len(episodes)} episodes")
        
    except Exception as e:
        logger.error(f"Error in background processing: {e}")
        processing_status["is_processing"] = False
        processing_status["current_video"] = f"Error: {str(e)}"
        processing_status["progress"] = 0


@app.get("/status")
async def get_processing_status():
    """Get current processing status"""
    stats = analyzer.get_stats()
    
    return {
        "processing": processing_status,
        "database_stats": stats
    }


@app.post("/search/insights", response_model=SearchResponse)
async def search_insights(request: SearchRequest):
    """Search for insights"""
    try:
        results = analyzer.search_insights(
            query=request.query,
            category=request.category,
            video_id=request.video_id,
            tags=request.tags,
            limit=request.limit
        )
        
        return SearchResponse(
            hits=results.get("hits", []),
            total_hits=results.get("estimatedTotalHits", 0),
            processing_time_ms=results.get("processingTimeMs", 0)
        )
        
    except Exception as e:
        logger.error(f"Error searching insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/segments", response_model=SearchResponse)
async def search_segments(request: SearchRequest):
    """Search for transcript segments"""
    try:
        results = analyzer.search_segments(
            query=request.query,
            video_id=request.video_id,
            speaker=None,  # Could be added to request model
            limit=request.limit
        )
        
        return SearchResponse(
            hits=results.get("hits", []),
            total_hits=results.get("estimatedTotalHits", 0),
            processing_time_ms=results.get("processingTimeMs", 0)
        )
        
    except Exception as e:
        logger.error(f"Error searching segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/episodes", response_model=SearchResponse)
async def search_episodes(request: SearchRequest):
    """Search for episodes"""
    try:
        results = analyzer.search_episodes(
            query=request.query,
            limit=request.limit
        )
        
        return SearchResponse(
            hits=results.get("hits", []),
            total_hits=results.get("estimatedTotalHits", 0),
            processing_time_ms=results.get("processingTimeMs", 0)
        )
        
    except Exception as e:
        logger.error(f"Error searching episodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories")
async def get_insight_categories():
    """Get all available insight categories"""
    try:
        categories = analyzer.search_service.get_insight_categories()
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get database and processing statistics"""
    try:
        stats = analyzer.get_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)