#!/usr/bin/env python3
"""
Find YouTube videos that don't require PO tokens for testing
"""

import sys
from pathlib import Path
import yt_dlp

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_video_access(video_url):
    """Test if a video can be accessed without PO token"""
    
    # Test configurations (ordered by likelihood to work without PO token)
    configs = [
        {
            'name': 'Web client',
            'opts': {
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web'],
                        'skip': ['hls', 'dash'],
                    }
                }
            }
        },
        {
            'name': 'Mobile web',
            'opts': {
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                },
                'extractor_args': {
                    'youtube': {
                        'player_client': ['mweb'],
                        'skip': ['hls', 'dash'],
                    }
                }
            }
        },
        {
            'name': 'Android client',
            'opts': {
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],
                        'skip': ['hls', 'dash'],
                    }
                }
            }
        }
    ]
    
    print(f"🧪 Testing: {video_url}")
    
    for config in configs:
        try:
            with yt_dlp.YoutubeDL(config['opts']) as ydl:
                info = ydl.extract_info(video_url, download=False)
                if info and 'formats' in info and info['formats']:
                    print(f"   ✅ {config['name']}: Works! ({len(info['formats'])} formats available)")
                    return True, config['name']
                else:
                    print(f"   ❌ {config['name']}: No formats found")
        except Exception as e:
            error_msg = str(e)
            if "PO token" in error_msg or "requires a PO token" in error_msg:
                print(f"   ❌ {config['name']}: PO token required")
            elif "Sign in to confirm" in error_msg:
                print(f"   ❌ {config['name']}: Bot detection")
            elif "Video unavailable" in error_msg:
                print(f"   ❌ {config['name']}: Video unavailable")
            else:
                print(f"   ❌ {config['name']}: {error_msg[:50]}...")
    
    return False, None

def find_working_videos():
    """Test a selection of YouTube videos to find ones that work without PO tokens"""
    
    # Test videos (mix of old and new, popular and less popular)
    test_videos = [
        # Older videos (more likely to work without PO tokens)
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (2009) - very popular
        "https://www.youtube.com/watch?v=kJQP7kiw5Fk",  # Despacito (2017) - popular but newer
        "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",  # Bohemian Rhapsody (2008) - old upload
        "https://www.youtube.com/watch?v=L_jWHffIx5E",  # Smells Like Teen Spirit (2009)
        
        # Educational/Tech videos (often less restricted)
        "https://www.youtube.com/watch?v=aircAruvnKk",  # 3Blue1Brown - Neural Networks
        "https://www.youtube.com/watch?v=RF_LS7BLP9s",  # Harvard CS50 - Algorithms
        "https://www.youtube.com/watch?v=HEfHFsfGXjs",  # MIT OpenCourseWare
        
        # Podcasts/Talks (good for testing our use case)
        "https://www.youtube.com/watch?v=sTBIr65cL_E",  # TED Talk
        "https://www.youtube.com/watch?v=WXuK6gekU1Y",  # Joe Rogan clips (often work)
        "https://www.youtube.com/watch?v=Da-2h2B4faI",  # Business podcast
        
        # Government/Official channels (usually accessible)
        "https://www.youtube.com/watch?v=nlcIKh6sBtc",  # NASA videos
        "https://www.youtube.com/watch?v=CevxZvSJLk8",  # BBC documentaries
    ]
    
    print("🔍 Finding YouTube videos that work without PO tokens...")
    print("=" * 60)
    
    working_videos = []
    
    for video_url in test_videos:
        works, method = test_video_access(video_url)
        if works:
            working_videos.append((video_url, method))
        print()  # Empty line for readability
    
    print("📊 Results:")
    print("=" * 60)
    
    if working_videos:
        print(f"✅ Found {len(working_videos)} working videos:")
        for i, (url, method) in enumerate(working_videos, 1):
            print(f"   {i}. {url} (via {method})")
        
        print(f"\n🎯 Recommended test video:")
        best_video = working_videos[0][0]
        print(f"   {best_video}")
        print(f"\n🚀 Test command:")
        print(f'   python run.py process "{best_video}"')
        
    else:
        print("❌ No working videos found")
        print("\n💡 This suggests YouTube has tightened restrictions.")
        print("   You may need to:")
        print("   1. Implement PO token extraction")
        print("   2. Use a different video platform")
        print("   3. Try videos from smaller/less popular channels")
    
    return working_videos

def test_specific_video():
    """Test a specific video provided as command line argument"""
    if len(sys.argv) != 2:
        print("Usage: python find_working_videos.py <video_url>")
        return
    
    video_url = sys.argv[1]
    works, method = test_video_access(video_url)
    
    if works:
        print(f"\n🎉 Success! This video works with {method}")
        print(f"🚀 Test command: python run.py process \"{video_url}\"")
    else:
        print(f"\n❌ This video doesn't work with current methods")
        print("💡 Try a different video or implement PO token support")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        test_specific_video()
    else:
        working_videos = find_working_videos()