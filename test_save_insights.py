#!/usr/bin/env python3
"""
Test script to save insights from existing transcript
"""

import json
import asyncio
from pathlib import Path
from src.main import PodcastAnalyzer
from src.models.podcast import TranscriptSegment, VideoInfo
from pydantic import HttpUrl

async def test_save_insights():
    """Test saving insights from existing transcript"""
    
    print("🧪 **TESTING INSIGHTS SAVING**")
    print("=" * 40)
    
    # Initialize analyzer
    analyzer = PodcastAnalyzer()
    
    # Load existing transcript
    video_id = "vCN9-mKBDfQ"
    transcript_file = Path(f"data/transcripts/{video_id}_direct_transcript.json")
    
    if not transcript_file.exists():
        print(f"❌ Transcript file not found: {transcript_file}")
        return
    
    # Read transcript
    with open(transcript_file, 'r') as f:
        transcript_data = json.load(f)
    
    print(f"📄 Video: {transcript_data['title']}")
    print(f"📊 Segments: {len(transcript_data['segments'])}")
    
    # Create VideoInfo object
    video_info = VideoInfo(
        video_id=transcript_data['video_id'],
        title=transcript_data['title'],
        url=HttpUrl(transcript_data['url']),
        description="",
        duration=0,
        publish_date=None,
        thumbnail_url=""
    )
    
    # Convert to transcript segments
    segments = []
    for seg in transcript_data['segments']:
        segment = TranscriptSegment(
            start_time=seg['start_time'],
            end_time=seg['end_time'],
            text=seg['text'],
            speaker=seg.get('speaker')
        )
        segments.append(segment)
    
    print(f"🔄 Processing {len(segments)} segments...")
    
    # Process segments
    cleaned_segments = analyzer.text_processor.process_transcript_segments(segments)
    print(f"✅ Cleaned {len(cleaned_segments)} segments")
    
    # Extract insights
    print("🧠 Extracting insights...")
    insights = analyzer.text_processor.extract_insights_from_episode(cleaned_segments, video_id)
    print(f"✅ Extracted {len(insights)} insights")
    
    # Save insights
    print("💾 Saving insights...")
    analyzer._save_insights(video_info, insights)
    
    # Check if file was created
    insights_file = Path(f"data/processed/{video_id}_insights.json")
    if insights_file.exists():
        print(f"✅ Insights saved to: {insights_file}")
        
        # Show file size
        size = insights_file.stat().st_size
        print(f"📁 File size: {size} bytes")
        
        # Read and show first insight
        with open(insights_file, 'r') as f:
            insights_data = json.load(f)
        
        print(f"\n📊 **SAVED INSIGHTS SUMMARY:**")
        print(f"Video: {insights_data['title']}")
        print(f"Insights Count: {insights_data['insights_count']}")
        print(f"Extracted At: {insights_data['extracted_at']}")
        
        if insights_data['insights']:
            first_insight = insights_data['insights'][0]
            print(f"\n🎯 **FIRST INSIGHT:**")
            print(f"Title: {first_insight['title']}")
            print(f"Category: {first_insight['category']}")
            print(f"Content: {first_insight['content'][:100]}...")
            
    else:
        print(f"❌ Insights file not created: {insights_file}")

if __name__ == "__main__":
    asyncio.run(test_save_insights()) 