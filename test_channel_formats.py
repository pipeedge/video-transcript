#!/usr/bin/env python3
"""
Test different channel URL formats for NetworkSecurityLearning
"""

import yt_dlp

def test_channel_formats():
    """Test various URL formats for the specific channel"""
    
    # Different URL formats to try for NetworkSecurityLearning
    urls_to_test = [
        "https://www.youtube.com/@NetworkSecurityLearning",
        "https://www.youtube.com/@NetworkSecurityLearning/videos",
        "https://www.youtube.com/c/NetworkSecurityLearning",
        "https://www.youtube.com/c/NetworkSecurityLearning/videos",
        "https://www.youtube.com/user/NetworkSecurityLearning",
        "https://www.youtube.com/user/NetworkSecurityLearning/videos",
        "https://www.youtube.com/NetworkSecurityLearning",
        "https://www.youtube.com/NetworkSecurityLearning/videos",
        
        # Alternative channel formats (if the above don't work)
        "https://www.youtube.com/@networksecuritylearning",
        "https://www.youtube.com/c/networksecuritylearning",
        "https://www.youtube.com/user/networksecuritylearning",
    ]
    
    print("🧪 Testing NetworkSecurityLearning channel URL formats...")
    print("=" * 60)
    
    working_urls = []
    
    for i, url in enumerate(urls_to_test, 1):
        print(f"\n{i:2d}. Testing: {url}")
        
        try:
            # Minimal configuration for testing
            config = {
                'quiet': True,
                'extract_flat': True,
                'no_warnings': True,
                'playlist_items': '1:3',  # Only get first 3 videos for testing
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],  # Android client works best
                        'skip': ['hls', 'dash'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                }
            }
            
            with yt_dlp.YoutubeDL(config) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info and 'entries' in info:
                    video_count = len([e for e in info['entries'] if e])
                    if video_count > 0:
                        print(f"    ✅ SUCCESS! Found {video_count} videos")
                        working_urls.append(url)
                        
                        # Show first video as proof
                        first_video = next((e for e in info['entries'] if e), None)
                        if first_video:
                            print(f"    📹 Sample video: {first_video.get('title', 'No title')}")
                    else:
                        print(f"    ❌ No videos found")
                else:
                    print(f"    ❌ No channel data found")
                    
        except Exception as e:
            error_msg = str(e)
            if "Unable to recognize tab page" in error_msg:
                print(f"    ❌ Tab page error - format not recognized")
            elif "Sign in to confirm" in error_msg:
                print(f"    ❌ Bot detection triggered")
            elif "channel_name: could not find match" in error_msg:
                print(f"    ❌ Channel name pattern not matched")
            else:
                print(f"    ❌ Error: {error_msg[:80]}...")
    
    print(f"\n" + "=" * 60)
    print("📊 RESULTS:")
    
    if working_urls:
        print(f"✅ Found {len(working_urls)} working URL(s):")
        for url in working_urls:
            print(f"   • {url}")
        
        print(f"\n🎯 RECOMMENDED COMMAND:")
        best_url = working_urls[0]
        print(f"python run.py process \"{best_url}\" --max-videos 2")
        
    else:
        print(f"❌ No working URLs found for NetworkSecurityLearning")
        print(f"\n💡 ALTERNATIVES:")
        print("1. The channel might be private or restricted")
        print("2. Try a different channel for testing:")
        print("   python run.py process \"https://www.youtube.com/@kurzgesagt\" --max-videos 2")
        print("3. Use a single video URL instead:")
        print("   python run.py process \"https://www.youtube.com/watch?v=VIDEO_ID\"")
        print("4. YouTube might be temporarily blocking all automated access")
    
    return working_urls

if __name__ == "__main__":
    test_channel_formats()