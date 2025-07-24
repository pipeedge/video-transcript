from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class VideoInfo(BaseModel):
    """Model for YouTube video information"""
    video_id: str
    title: str
    description: Optional[str] = None
    url: HttpUrl
    duration: Optional[int] = None  # in seconds
    publish_date: Optional[datetime] = None
    thumbnail_url: Optional[str] = None


class TranscriptSegment(BaseModel):
    """Model for individual transcript segments"""
    text: str
    start_time: float  # in seconds
    end_time: float    # in seconds
    speaker: Optional[str] = None
    confidence: Optional[float] = None


class CleanedSegment(BaseModel):
    """Model for cleaned and processed transcript segments"""
    original_text: str
    cleaned_text: str
    title: str
    start_time: float
    end_time: float
    speaker: Optional[str] = None


class InsightCategory(BaseModel):
    """Model for insight categories"""
    name: str
    description: str


class Insight(BaseModel):
    """Model for extracted insights"""
    category: str
    title: str
    content: str
    quote: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    video_id: str
    confidence: Optional[float] = None
    tags: Optional[List[str]] = None


class Product(BaseModel):
    """Model for product mentions"""
    name: str
    description: Optional[str] = None
    website: Optional[HttpUrl] = None
    category: Optional[str] = None
    mentioned_in_insight: str  # insight ID
    context: Optional[str] = None


class Episode(BaseModel):
    """Model for complete podcast episode"""
    video_info: VideoInfo
    raw_transcript: List[TranscriptSegment]
    cleaned_segments: List[CleanedSegment]
    insights: List[Insight]
    products: List[Product]
    processing_status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()