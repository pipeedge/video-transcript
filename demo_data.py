#!/usr/bin/env python3
"""
Demo data generator for testing the podcast analysis application without API keys
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.models.podcast import VideoInfo, TranscriptSegment, CleanedSegment, Insight, Episode
from src.config.settings import TRANSCRIPTS_DIR, AUDIO_DIR


def create_demo_transcript_segments():
    """Create sample transcript segments for demo"""
    segments = [
        TranscriptSegment(
            text="Welcome to the My First Million podcast. I'm Sam Parr and today we're talking about business ideas that could make you millions.",
            start_time=0.0,
            end_time=8.5,
            speaker="Speaker 0",
            confidence=0.95
        ),
        TranscriptSegment(
            text="One framework I love is the CRAP method - Copy, Replace, Add, Polish. You find a successful business model and improve it.",
            start_time=8.5,
            end_time=18.2,
            speaker="Speaker 0", 
            confidence=0.92
        ),
        TranscriptSegment(
            text="Speaking of successful models, let me tell you about this guy who started a newsletter about finance and sold it for fifty million dollars.",
            start_time=18.2,
            end_time=28.0,
            speaker="Speaker 0",
            confidence=0.94
        ),
        TranscriptSegment(
            text="The key insight here is that information products scale incredibly well. Once you create the content, distribution costs are minimal.",
            start_time=28.0,
            end_time=38.5,
            speaker="Speaker 0",
            confidence=0.91
        ),
        TranscriptSegment(
            text="Another mental model I use is the 'Boring Business' framework. Sometimes the most profitable companies are solving mundane problems.",
            start_time=38.5,
            end_time=48.0,
            speaker="Speaker 0",
            confidence=0.93
        ),
        TranscriptSegment(
            text="For example, there's a company that just organizes documents for law firms and they're doing eight figures in revenue.",
            start_time=48.0,
            end_time=57.5,
            speaker="Speaker 0",
            confidence=0.89
        )
    ]
    return segments


def create_demo_cleaned_segments():
    """Create cleaned and titled segments"""
    segments = [
        CleanedSegment(
            original_text="Welcome to the My First Million podcast. I'm Sam Parr and today we're talking about business ideas that could make you millions.",
            cleaned_text="Welcome to the My First Million podcast. I'm Sam Parr, and today we're talking about business ideas that could make you millions.",
            title="Welcome to My First Million",
            start_time=0.0,
            end_time=8.5,
            speaker="Speaker 0"
        ),
        CleanedSegment(
            original_text="One framework I love is the CRAP method - Copy, Replace, Add, Polish. You find a successful business model and improve it.",
            cleaned_text="One framework I love is the CRAP method: Copy, Replace, Add, Polish. You find a successful business model and improve it.",
            title="The CRAP Framework for Business",
            start_time=8.5,
            end_time=18.2,
            speaker="Speaker 0"
        ),
        CleanedSegment(
            original_text="Speaking of successful models, let me tell you about this guy who started a newsletter about finance and sold it for fifty million dollars.",
            cleaned_text="Speaking of successful models, let me tell you about this guy who started a newsletter about finance and sold it for fifty million dollars.",
            title="Newsletter Success Story - $50M Exit",
            start_time=18.2,
            end_time=28.0,
            speaker="Speaker 0"
        ),
        CleanedSegment(
            original_text="The key insight here is that information products scale incredibly well. Once you create the content, distribution costs are minimal.",
            cleaned_text="The key insight here is that information products scale incredibly well. Once you create the content, distribution costs are minimal.",
            title="Information Products Scale Well",
            start_time=28.0,
            end_time=38.5,
            speaker="Speaker 0"
        ),
        CleanedSegment(
            original_text="Another mental model I use is the 'Boring Business' framework. Sometimes the most profitable companies are solving mundane problems.",
            cleaned_text="Another mental model I use is the 'Boring Business' framework. Sometimes the most profitable companies are solving mundane problems.",
            title="Boring Business Framework",
            start_time=38.5,
            end_time=48.0,
            speaker="Speaker 0"
        ),
        CleanedSegment(
            original_text="For example, there's a company that just organizes documents for law firms and they're doing eight figures in revenue.",
            cleaned_text="For example, there's a company that just organizes documents for law firms, and they're doing eight figures in revenue.",
            title="Document Organization for Law Firms",
            start_time=48.0,
            end_time=57.5,
            speaker="Speaker 0"
        )
    ]
    return segments


def create_demo_insights():
    """Create sample insights for demo"""
    insights = [
        Insight(
            category="Frameworks",
            title="CRAP Method for Business Ideas",
            content="The CRAP method stands for Copy, Replace, Add, Polish. You find a successful business model and improve it rather than starting from scratch.",
            quote="One framework I love is the CRAP method: Copy, Replace, Add, Polish. You find a successful business model and improve it.",
            start_time=8.5,
            end_time=18.2,
            video_id="demo_video_1",
            confidence=0.92,
            tags=["Framework", "Business Model", "Innovation"]
        ),
        Insight(
            category="Stories",
            title="Newsletter Business Sold for $50M",
            content="A successful story about an entrepreneur who started a finance newsletter and eventually sold it for fifty million dollars, demonstrating the potential of information products.",
            quote="Let me tell you about this guy who started a newsletter about finance and sold it for fifty million dollars.",
            start_time=18.2,
            end_time=28.0,
            video_id="demo_video_1",
            confidence=0.94,
            tags=["Newsletter", "Success Story", "Finance"]
        ),
        Insight(
            category="Business Ideas",
            title="Information Products Have Great Scalability",
            content="Information products scale incredibly well because once you create the content, distribution costs are minimal, making them highly profitable business models.",
            quote="Information products scale incredibly well. Once you create the content, distribution costs are minimal.",
            start_time=28.0,
            end_time=38.5,
            video_id="demo_video_1",
            confidence=0.91,
            tags=["Scalability", "Information Products", "Business Model"]
        ),
        Insight(
            category="Mental Models",
            title="Boring Business Framework",
            content="The 'Boring Business' framework suggests that sometimes the most profitable companies are those solving mundane, everyday problems rather than flashy innovations.",
            quote="Another mental model I use is the 'Boring Business' framework. Sometimes the most profitable companies are solving mundane problems.",
            start_time=38.5,
            end_time=48.0,
            video_id="demo_video_1",
            confidence=0.93,
            tags=["Mental Model", "Business Strategy", "Profit"]
        ),
        Insight(
            category="Numbers & Metrics",
            title="Document Organization Company - 8 Figures",
            content="Example of a boring but profitable business: a company that organizes documents for law firms generating eight figures in revenue annually.",
            quote="There's a company that just organizes documents for law firms, and they're doing eight figures in revenue.",
            start_time=48.0,
            end_time=57.5,
            video_id="demo_video_1",
            confidence=0.89,
            tags=["Revenue", "Law Firms", "Document Management"]
        )
    ]
    return insights


def create_demo_episode():
    """Create a complete demo episode"""
    video_info = VideoInfo(
        video_id="demo_video_1",
        title="Business Frameworks That Made Millions - My First Million Demo",
        description="Demo episode showcasing business frameworks, success stories, and mental models for entrepreneurs",
        url="https://youtube.com/watch?v=demo_video_1",
        duration=3600,  # 1 hour
        publish_date=datetime.now() - timedelta(days=7),
        thumbnail_url="https://example.com/thumbnail.jpg"
    )
    
    raw_transcript = create_demo_transcript_segments()
    cleaned_segments = create_demo_cleaned_segments()
    insights = create_demo_insights()
    
    episode = Episode(
        video_info=video_info,
        raw_transcript=raw_transcript,
        cleaned_segments=cleaned_segments,
        insights=insights,
        products=[],
        processing_status="completed",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    return episode


def save_demo_transcript():
    """Save demo transcript to file"""
    segments = create_demo_transcript_segments()
    transcript_path = Path(TRANSCRIPTS_DIR) / "demo_video_1_whisper.json"
    
    with open(transcript_path, 'w', encoding='utf-8') as f:
        json.dump([segment.dict() for segment in segments], f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Saved demo transcript to: {transcript_path}")


def generate_demo_data():
    """Generate all demo data"""
    print("🎭 Generating demo data for podcast analysis...")
    
    # Create demo episode
    episode = create_demo_episode()
    
    # Save transcript
    save_demo_transcript()
    
    # Print summary
    print(f"\n📊 Demo Episode Summary:")
    print(f"Title: {episode.video_info.title}")
    print(f"Segments: {len(episode.cleaned_segments)}")
    print(f"Insights: {len(episode.insights)}")
    print(f"Categories: {set(insight.category for insight in episode.insights)}")
    
    print(f"\n🎯 Sample Insights:")
    for insight in episode.insights[:3]:
        print(f"- [{insight.category}] {insight.title}")
    
    return episode


if __name__ == "__main__":
    generate_demo_data()