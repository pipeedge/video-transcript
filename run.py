#!/usr/bin/env python3
"""
Podcast Analysis Application Runner
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.main import PodcastAnalyzer


async def process_channel(channel_url: str, max_videos: int = None):
    """Process a YouTube channel"""
    print(f"Processing channel: {channel_url}")
    print(f"Max videos: {max_videos if max_videos else 'All'}")
    
    analyzer = PodcastAnalyzer()
    episodes = await analyzer.process_channel(channel_url, max_videos)
    
    print(f"\n✅ Successfully processed {len(episodes)} episodes")
    
    # Show some stats
    total_insights = sum(len(ep.insights) for ep in episodes)
    total_segments = sum(len(ep.cleaned_segments) for ep in episodes)
    
    print(f"📊 Total insights extracted: {total_insights}")
    print(f"📝 Total segments processed: {total_segments}")
    
    # Show search stats
    stats = analyzer.get_stats()
    print(f"🔍 Search index stats: {stats}")


def run_api():
    """Run the FastAPI application"""
    import uvicorn
    from src.api.app import app
    
    print("🚀 Starting Podcast Analysis API...")
    print("📡 API will be available at: http://localhost:8000")
    print("📖 API documentation: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    parser = argparse.ArgumentParser(description="Podcast Analysis Application")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process a YouTube channel")
    process_parser.add_argument("channel_url", help="YouTube channel URL")
    process_parser.add_argument("--max-videos", type=int, help="Maximum number of videos to process")
    
    # API command
    api_parser = subparsers.add_parser("api", help="Run the API server")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search the indexed content")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", choices=["insights", "segments", "episodes"], 
                              default="insights", help="Type of content to search")
    search_parser.add_argument("--category", help="Filter by category")
    
    args = parser.parse_args()
    
    if args.command == "process":
        asyncio.run(process_channel(args.channel_url, args.max_videos))
    
    elif args.command == "api":
        run_api()
    
    elif args.command == "search":
        # Simple search implementation
        analyzer = PodcastAnalyzer()
        
        if args.type == "insights":
            results = analyzer.search_insights(args.query, category=args.category)
        elif args.type == "segments":
            results = analyzer.search_segments(args.query)
        else:
            results = analyzer.search_episodes(args.query)
        
        print(f"Found {len(results['hits'])} results:")
        for hit in results['hits'][:5]:  # Show top 5
            print(f"- {hit.get('title', 'No title')}: {hit.get('content', hit.get('cleaned_text', ''))[:100]}...")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()