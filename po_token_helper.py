#!/usr/bin/env python3
"""
PO Token Helper for YouTube downloads
Based on: https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide
"""

import sys
import os
from pathlib import Path
import yt_dlp

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_with_po_token(video_url, po_token=None):
    """Test video download with PO token"""
    
    if not po_token:
        print("❌ No PO token provided")
        return False
    
    # Configuration with PO token
    config = {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb'],  # Use mweb client for PO tokens
                'po_token': f'mweb.gvs+{po_token}',  # Format: mweb.gvs+TOKEN
                'skip': ['hls', 'dash'],
            }
        }
    }
    
    try:
        print(f"🧪 Testing with PO token: {po_token[:20]}...")
        with yt_dlp.YoutubeDL(config) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if info and 'formats' in info and info['formats']:
                print(f"✅ Success with PO token! Found {len(info['formats'])} formats")
                return True
            else:
                print("❌ No formats found even with PO token")
                return False
    except Exception as e:
        print(f"❌ Failed with PO token: {str(e)[:100]}...")
        return False

def extract_po_token_instructions():
    """Provide instructions for manually extracting PO tokens"""
    
    print("🔧 How to Extract PO Token Manually:")
    print("=" * 50)
    print()
    print("1. Open YouTube in Chrome/Firefox")
    print("2. Open Developer Tools (F12)")
    print("3. Go to 'Network' tab")
    print("4. Filter by 'googlevideo.com'")
    print("5. Play any video on YouTube")
    print("6. Look for requests containing 'pot=' parameter")
    print("7. Copy the value after 'pot='")
    print()
    print("Example PO token format:")
    print("   pot=mweb.gvs+AbCdEf123...")
    print("   → Use: AbCdEf123...")
    print()
    print("🚀 Test with extracted token:")
    print(f"   python po_token_helper.py <video_url> <po_token>")
    print()
    print("💡 Alternative: Use bgutil-ytdlp-pot-provider plugin:")
    print("   pip install bgutil-ytdlp-pot-provider")
    print("   yt-dlp --extractor-args 'youtube:player_client=default;po_token=provider:bgutil_ytdlp_pot_provider' <url>")

def update_downloader_with_po_token(po_token):
    """Update the YouTube downloader to use a specific PO token"""
    
    downloader_path = Path(__file__).parent / "src" / "data_ingestion" / "youtube_downloader.py"
    
    if not downloader_path.exists():
        print(f"❌ Downloader not found: {downloader_path}")
        return False
    
    # Create a backup
    backup_path = downloader_path.with_suffix('.py.backup')
    if not backup_path.exists():
        import shutil
        shutil.copy2(downloader_path, backup_path)
        print(f"📁 Created backup: {backup_path}")
    
    # Read current content
    content = downloader_path.read_text()
    
    # Add PO token to the mobile web client strategy
    po_token_line = f"                                'po_token': 'mweb.gvs+{po_token}',"
    
    if "'player_client': ['mweb']," in content and 'po_token' not in content:
        # Insert PO token after player_client line
        updated_content = content.replace(
            "'player_client': ['mweb'],",
            f"'player_client': ['mweb'],\n                                'po_token': 'mweb.gvs+{po_token}',"
        )
        
        downloader_path.write_text(updated_content)
        print(f"✅ Updated downloader with PO token")
        print(f"💡 To revert: cp {backup_path} {downloader_path}")
        return True
    else:
        print("⚠️  Could not update downloader (already has PO token or unexpected format)")
        return False

def main():
    """Main function"""
    
    if len(sys.argv) == 1:
        # No arguments - show instructions
        extract_po_token_instructions()
        
    elif len(sys.argv) == 2:
        # One argument - could be video URL or "install"
        arg = sys.argv[1]
        
        if arg == "install":
            print("📦 Installing PO token provider plugin...")
            os.system("pip install bgutil-ytdlp-pot-provider")
            print("✅ Plugin installed!")
            print("\n🚀 Now you can use:")
            print("yt-dlp --extractor-args 'youtube:player_client=default;po_token=provider:bgutil_ytdlp_pot_provider' <video_url>")
            
        elif arg.startswith("http"):
            # Video URL without PO token - test if it needs one
            from find_working_videos import test_video_access
            works, method = test_video_access(arg)
            if not works:
                print("\n💡 This video likely requires a PO token.")
                extract_po_token_instructions()
            else:
                print(f"\n✅ This video works with {method} - no PO token needed!")
        else:
            print("❌ Invalid argument. Usage:")
            print("   python po_token_helper.py                    # Show instructions")
            print("   python po_token_helper.py install           # Install PO token plugin")
            print("   python po_token_helper.py <video_url>       # Test if video needs PO token")
            print("   python po_token_helper.py <video_url> <token>  # Test with specific PO token")
            
    elif len(sys.argv) == 3:
        # Two arguments - video URL and PO token
        video_url, po_token = sys.argv[1], sys.argv[2]
        
        if test_with_po_token(video_url, po_token):
            # If successful, offer to update the downloader
            response = input("\n🔧 Update downloader with this PO token? (y/N): ")
            if response.lower() == 'y':
                update_downloader_with_po_token(po_token)
        
    else:
        print("❌ Too many arguments. See usage above.")

if __name__ == "__main__":
    main()