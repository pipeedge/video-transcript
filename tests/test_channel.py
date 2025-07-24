#!/usr/bin/env python3
"""
Test channel processing with the fixed downloader
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_channel_processing():
    """Test the fixed channel processing"""
    print("🧪 Testing Channel Processing Fix")
    print("=" * 40)
    
    try:
        from src.data_ingestion.youtube_downloader import YouTubeDownloader
        
        downloader = YouTubeDownloader()
        
        # Test the problematic channel URL
        channel_url = "https://www.youtube.com/@NetworkSecurityLearning"
        print(f"Testing with: {channel_url}")
        print("🔄 Attempting to fetch channel videos...")
        
        # Limit to 2 videos for testing
        videos = downloader.get_channel_videos(channel_url, max_videos=2)
        
        if videos:
            print(f"✅ Success! Found {len(videos)} videos:")
            for i, video in enumerate(videos, 1):
                print(f"   {i}. {video.title}")
                print(f"      Duration: {video.duration}s | ID: {video.video_id}")
            return True
        else:
            print("❌ No videos found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_different_url_formats():
    """Test different YouTube URL formats"""
    print("\n🔗 Testing Different URL Formats")
    print("-" * 40)
    
    test_urls = [
        "https://www.youtube.com/@NetworkSecurityLearning",
        "https://www.youtube.com/watch?v=NQtWHOUmqNw",  # Single video
        "https://youtu.be/NQtWHOUmqNw",  # Short single video
    ]
    
    try:
        from src.data_ingestion.youtube_downloader import YouTubeDownloader
        downloader = YouTubeDownloader()
        
        results = []
        for url in test_urls:
            print(f"\n🔍 Testing: {url}")
            try:
                videos = downloader.get_channel_videos(url, max_videos=1)
                if videos:
                    print(f"   ✅ Success: {videos[0].title}")
                    results.append(True)
                else:
                    print(f"   ❌ No videos found")
                    results.append(False)
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append(False)
        
        return results
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return []

def main():
    # Test the specific channel that was failing
    channel_works = test_channel_processing()
    
    # Test different URL formats
    url_results = test_different_url_formats()
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"   Channel Processing: {'✅ Working' if channel_works else '❌ Failed'}")
    
    if url_results:
        working_urls = sum(url_results)
        total_urls = len(url_results)
        print(f"   URL Format Support: {working_urls}/{total_urls} working")
    
    if channel_works:
        print("\n🎉 Great! Channel processing is now fixed!")
        print("\n🚀 You can now run:")
        print('   python run.py process "https://www.youtube.com/@NetworkSecurityLearning" --max-videos 2')
    else:
        print("\n🔧 Channel processing still needs work.")
        print("📖 This might be due to:")
        print("   - YouTube blocking the requests")
        print("   - Network issues")
        print("   - Channel access restrictions")
        print("\n💡 Try with a different channel or single video URL")

if __name__ == "__main__":
    main()