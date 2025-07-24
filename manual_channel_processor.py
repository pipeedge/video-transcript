#!/usr/bin/env python3
"""
Manual channel processor for when YouTube tab extraction fails
"""

def process_individual_videos():
    """Process individual videos from NetworkSecurityLearning channel"""
    
    # Manual list of video IDs from the channel (you can get these by visiting the channel)
    video_urls = [
        "https://www.youtube.com/watch?v=RGaW82k4dK4",  # The one that worked
        # Add more video URLs manually by visiting the channel page
        # "https://www.youtube.com/watch?v=VIDEO_ID_2",
        # "https://www.youtube.com/watch?v=VIDEO_ID_3",
    ]
    
    print("🔧 Manual Channel Processing Workaround")
    print("=" * 50)
    print("Since channel tab extraction is failing, we can process individual videos.")
    print("\nTo get more video URLs:")
    print("1. Visit: https://www.youtube.com/@NetworkSecurityLearning")
    print("2. Copy video URLs manually")
    print("3. Add them to this script")
    
    print(f"\n📹 Processing {len(video_urls)} videos individually:")
    
    for i, url in enumerate(video_urls, 1):
        print(f"\n{i}. Processing: {url}")
        print(f"   Command: python run.py process \"{url}\"")
    
    return video_urls

def get_channel_videos_manually():
    """Instructions for manually getting channel videos"""
    print("\n💡 How to manually get channel videos:")
    print("1. Go to: https://www.youtube.com/@NetworkSecurityLearning")
    print("2. Right-click -> View Page Source")
    print("3. Search for 'watch?v=' to find video IDs")
    print("4. Or use browser dev tools to inspect video links")
    print("5. Copy the URLs and process them individually")
    
    print("\n🔍 Alternative approach - Use YouTube Data API:")
    print("1. Get YouTube Data API v3 key")
    print("2. Use the API to list channel videos")
    print("3. This is more reliable than scraping")

if __name__ == "__main__":
    video_urls = process_individual_videos()
    get_channel_videos_manually()
    
    print(f"\n🚀 Try processing the working video:")
    print('python run.py process "https://www.youtube.com/watch?v=RGaW82k4dK4"')