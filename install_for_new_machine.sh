#!/bin/bash

echo "🚀 Setting up video-transcript project..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "📍 Python version: $python_version"

if [[ "$python_version" == "3.13" ]]; then
    echo "⚠️  Python 3.13 detected - using compatibility mode"
    # For Python 3.13, avoid audio processing dependencies that use pyaudioop
    SKIP_AUDIO=true
else
    SKIP_AUDIO=false
fi

echo "📦 Installing core dependencies..."

# Essential dependencies (no audio processing)
pip install yt-dlp
pip install youtube-transcript-api
pip install transformers
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install accelerate
pip install fastapi uvicorn
pip install pydantic
pip install requests beautifulsoup4
pip install python-dotenv
pip install pandas numpy
pip install sentencepiece protobuf

if [ "$SKIP_AUDIO" = false ]; then
    echo "🎵 Installing audio processing (Python < 3.13)..."
    pip install openai-whisper pydub
else
    echo "⏭️  Skipping audio processing (Python 3.13 compatibility)"
    echo "   Direct transcript extraction will work fine without audio processing"
fi

echo "✅ Installation complete!"
echo ""
echo "🎯 To test the setup:"
echo "python -c \"from src.data_ingestion.direct_transcript_extractor import DirectTranscriptExtractor; print('✅ Import successful!')\""
echo ""
echo "🚀 To run transcript extraction:"
echo "python run.py process 'CHANNEL_URL' --direct-transcripts --max-videos 1" 