#!/usr/bin/env python3
"""
Channel URL converter to find working formats
"""

import sys
from pathlib import Path
import yt_dlp

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def get_channel_info(url):
    """Get channel information to find alternative URLs"""
    configs = [
        # Minimal config just to get channel info
        {
            'quiet': True,
            'extract_flat': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                    'skip': ['hls', 'dash'],
                }
            }
        },
        # Fallback config
        {
            'quiet': True,
            'extract_flat': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                }
            }
        }
    ]
    
    for i, config in enumerate(configs):
        try:
            print(f"Trying config {i+1}...")
            with yt_dlp.YoutubeDL(config) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return info
        except Exception as e:
            print(f"Config {i+1} failed: {str(e)[:100]}...")
            continue
    
    return None

def convert_channel_url(original_url):
    """Convert channel URL to different formats"""
    print(f"🔍 Analyzing channel URL: {original_url}")
    
    # Generate URL variants
    variants = []
    
    if '@' in original_url:
        handle = original_url.split('@')[-1].split('/')[0].split('?')[0]
        variants = [
            f"https://www.youtube.com/@{handle}",
            f"https://www.youtube.com/@{handle}/videos",
            f"https://www.youtube.com/c/{handle}",
            f"https://www.youtube.com/c/{handle}/videos", 
            f"https://www.youtube.com/user/{handle}",
            f"https://www.youtube.com/user/{handle}/videos",
            # Try without the handle format
            f"https://www.youtube.com/{handle}",
            f"https://www.youtube.com/{handle}/videos",
        ]
    
    print(f"\n📋 URL variants to try:")
    for i, variant in enumerate(variants, 1):
        print(f"   {i}. {variant}")
    
    print(f"\n🧪 Testing each variant...")
    
    working_urls = []
    for i, variant in enumerate(variants, 1):
        print(f"\nTesting {i}/{len(variants)}: {variant}")
        try:
            # Quick test with minimal config
            config = {
                'quiet': True,
                'extract_flat': True,
                'no_warnings': True,
                'playlist_items': '1',  # Only get first video
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],
                        'skip': ['hls', 'dash'],
                    }
                }
            }
            
            with yt_dlp.YoutubeDL(config) as ydl:
                info = ydl.extract_info(variant, download=False)
                if info and 'entries' in info and info['entries']:
                    print(f"   ✅ WORKS! Found {len(info['entries'])} videos")
                    working_urls.append(variant)
                else:
                    print(f"   ❌ No videos found")
                    
        except Exception as e:
            error_msg = str(e)
            if "Unable to recognize tab page" in error_msg:
                print(f"   ❌ Tab page recognition error")
            elif "Sign in to confirm" in error_msg:
                print(f"   ❌ Bot detection")
            else:
                print(f"   ❌ Error: {error_msg[:50]}...")
    
    print(f"\n📊 Results:")
    if working_urls:
        print(f"✅ Found {len(working_urls)} working URLs:")
        for url in working_urls:
            print(f"   • {url}")
        return working_urls[0]  # Return first working URL
    else:
        print(f"❌ No working URLs found")
        return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python channel_url_converter.py <channel_url>")
        print("Example: python channel_url_converter.py 'https://www.youtube.com/@NetworkSecurityLearning'")
        return
    
    channel_url = sys.argv[1]
    working_url = convert_channel_url(channel_url)
    
    if working_url:
        print(f"\n🎯 Use this URL:")
        print(f"python run.py process \"{working_url}\" --max-videos 2")
    else:
        print(f"\n💡 Alternatives to try:")
        print("1. Search for the channel manually and get the channel ID")
        print("2. Use a single video URL instead")
        print("3. Try a different channel for testing")

if __name__ == "__main__":
    main()