#!/bin/bash

echo "🔧 Installing additional dependencies for direct transcript extraction..."

# Install YouTube Transcript API
echo "📦 Installing youtube-transcript-api..."
pip install youtube-transcript-api

# Install any other missing dependencies
echo "📦 Installing additional dependencies..."
pip install requests beautifulsoup4

echo "✅ All transcript extraction dependencies installed!"
echo ""
echo "🚀 You can now use direct transcript extraction with:"
echo "   python run.py process CHANNEL_URL --direct-transcripts"
echo ""
echo "📝 This method will:"
echo "   • Extract transcripts directly from YouTube (no audio download)"
echo "   • Use YouTube's auto-generated or manual subtitles"
echo "   • Fall back to yt-dlp subtitle extraction if needed"
echo "   • Process transcripts with the same LLM analysis pipeline" 