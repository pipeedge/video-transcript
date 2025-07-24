#!/usr/bin/env python3
"""
Example usage of the Podcast Analysis Application

This script demonstrates how to use the core functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.main import PodcastAnalyzer


async def demo():
    """Demonstrate the podcast analysis functionality"""
    print("🎙️ Podcast Analysis Demo")
    print("=" * 50)
    
    # Initialize the analyzer
    analyzer = PodcastAnalyzer()
    
    # Example 1: Process a small number of videos from a channel
    print("\n📺 Example 1: Processing Channel Videos")
    print("-" * 30)
    
    # Note: Replace with a real YouTube channel URL for testing
    # For demo purposes, we'll show what the process would look like
    channel_url = "https://www.youtube.com/@MyFirstMillionPod"
    
    print(f"Channel URL: {channel_url}")
    print("Max videos: 2 (for demo)")
    print("\nNote: To run this demo with real data:")
    print("1. Set up your Deepgram API key in .env")
    print("2. Start MeiliSearch server")
    print("3. Uncomment the processing code below")
    
    # Uncomment these lines to actually process videos
    # episodes = await analyzer.process_channel(channel_url, max_videos=2)
    # print(f"✅ Processed {len(episodes)} episodes")
    
    # Example 2: Search functionality (simulated)
    print("\n🔍 Example 2: Search Functionality")
    print("-" * 30)
    
    # Show what search queries would look like
    example_searches = [
        {"query": "business model", "type": "insights", "category": "Business Ideas"},
        {"query": "framework", "type": "insights", "category": "Frameworks"},
        {"query": "startup funding", "type": "insights"},
        {"query": "customer acquisition", "type": "segments"},
    ]
    
    for search in example_searches:
        print(f"Search: '{search['query']}'")
        print(f"  Type: {search['type']}")
        if 'category' in search:
            print(f"  Category: {search['category']}")
        print()
    
    # Example 3: Show available insight categories
    print("📊 Example 3: Available Insight Categories")
    print("-" * 30)
    
    categories = analyzer.text_processor.get_insight_categories()
    for i, category in enumerate(categories, 1):
        print(f"{i}. {category}")
    
    # Example 4: API endpoints demonstration
    print("\n🌐 Example 4: API Endpoints")
    print("-" * 30)
    
    api_examples = [
        "POST /process-channel - Start processing a YouTube channel",
        "GET /status - Get processing status",
        "POST /search/insights - Search for insights",
        "POST /search/segments - Search transcript segments", 
        "POST /search/episodes - Search episodes",
        "GET /categories - Get insight categories",
        "GET /stats - Get database statistics"
    ]
    
    for endpoint in api_examples:
        print(f"• {endpoint}")
    
    print("\n📖 API Documentation available at: http://localhost:8000/docs")
    
    # Example 5: CLI usage
    print("\n💻 Example 5: CLI Usage")
    print("-" * 30)
    
    cli_examples = [
        "python run.py process 'https://youtube.com/channel' --max-videos 5",
        "python run.py api",
        "python run.py search 'business model' --type insights",
    ]
    
    for cmd in cli_examples:
        print(f"$ {cmd}")
    
    print("\n" + "=" * 50)
    print("🚀 Ready to analyze podcasts!")
    print("\nNext steps:")
    print("1. Set up your API keys in .env")
    print("2. Start MeiliSearch: docker run -p 7700:7700 getmeili/meilisearch")
    print("3. Run: python run.py process 'YOUR_CHANNEL_URL' --max-videos 3")
    print("4. Start API: python run.py api")


if __name__ == "__main__":
    asyncio.run(demo())