#!/usr/bin/env python3
"""
Script to display insights from processed videos
"""

import json
import os
from pathlib import Path

def show_insights():
    """Display insights from the latest processing session"""
    
    print("🔍 **INSIGHTS FROM VIDEO PROCESSING**")
    print("=" * 50)
    
    # Check if we have any processed data
    processed_dir = Path("data/processed")
    transcripts_dir = Path("data/transcripts")
    
    print(f"📁 Processed directory: {processed_dir}")
    print(f"📁 Transcripts directory: {transcripts_dir}")
    
    # List transcript files
    transcript_files = list(transcripts_dir.glob("*_direct_transcript.json"))
    print(f"\n📄 Found {len(transcript_files)} transcript files:")
    
    for file in transcript_files:
        print(f"  - {file.name}")
        
        # Read transcript file
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            
            print(f"    Title: {data.get('title', 'Unknown')}")
            print(f"    Video ID: {data.get('video_id', 'Unknown')}")
            print(f"    Segments: {len(data.get('segments', []))}")
            print(f"    Extraction Method: {data.get('extraction_method', 'Unknown')}")
            print()
            
        except Exception as e:
            print(f"    Error reading file: {e}")
            print()

if __name__ == "__main__":
    show_insights() 