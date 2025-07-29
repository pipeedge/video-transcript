#!/usr/bin/env python3
"""
Script to extract and display insights from processed videos
"""

import json
import asyncio
from pathlib import Path
from src.main import PodcastAnalyzer
from src.config.settings import CHUNK_SIZE, CHUNK_OVERLAP

async def extract_insights_from_video(video_id: str):
    """Extract insights from a specific video"""
    
    print(f"🔍 **EXTRACTING INSIGHTS FOR VIDEO: {video_id}**")
    print("=" * 60)
    
    # Initialize the analyzer
    analyzer = PodcastAnalyzer()
    
    # Load the transcript
    transcript_file = Path(f"data/transcripts/{video_id}_direct_transcript.json")
    
    if not transcript_file.exists():
        print(f"❌ Transcript file not found: {transcript_file}")
        return
    
    # Read transcript
    with open(transcript_file, 'r') as f:
        transcript_data = json.load(f)
    
    print(f"📄 Video: {transcript_data['title']}")
    print(f"📊 Segments: {len(transcript_data['segments'])}")
    print(f"🔧 Extraction Method: {transcript_data['extraction_method']}")
    print()
    
    # Convert to transcript segments
    from src.models.podcast import TranscriptSegment
    
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
    
    print(f"\n🎯 **EXTRACTED {len(insights)} INSIGHTS:**")
    print("=" * 60)
    
    for i, insight in enumerate(insights, 1):
        print(f"\n{i}. **{insight.title}**")
        print(f"   Category: {insight.category}")
        print(f"   Content: {insight.content}")
        if insight.quote:
            print(f"   Quote: \"{insight.quote}\"")
        if insight.tags:
            print(f"   Tags: {', '.join(insight.tags)}")
        print(f"   Timestamp: {insight.start_time:.1f}s - {insight.end_time:.1f}s")
        print("-" * 40)

async def main():
    """Main function"""
    print("🚀 **VIDEO INSIGHTS EXTRACTOR**")
    print("=" * 50)
    
    # Get the video ID from the latest processing
    video_id = "vCN9-mKBDfQ"  # From your latest processing
    
    await extract_insights_from_video(video_id)

if __name__ == "__main__":
    asyncio.run(main()) 