#!/bin/bash

echo "🚀 Installing Podcast Analyzer Dependencies"
echo "=========================================="

# Check OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "📦 Detected Linux - installing system dependencies..."
    
    # Check if running as root or has sudo
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        echo "Installing ffmpeg via apt-get..."
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        echo "Installing ffmpeg via yum..."
        sudo yum install -y ffmpeg
    elif command -v dnf &> /dev/null; then
        # Fedora
        echo "Installing ffmpeg via dnf..."
        sudo dnf install -y ffmpeg
    else
        echo "⚠️  Please install ffmpeg manually for your Linux distribution"
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "🍎 Detected macOS - installing system dependencies..."
    
    if command -v brew &> /dev/null; then
        echo "Installing ffmpeg via Homebrew..."
        brew install ffmpeg
    else
        echo "⚠️  Please install Homebrew first: https://brew.sh"
        echo "Then run: brew install ffmpeg"
    fi
    
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "🪟 Detected Windows"
    echo "Please install ffmpeg manually:"
    echo "1. Download from: https://ffmpeg.org/download.html"
    echo "2. Add to your system PATH"
    echo "Or use chocolatey: choco install ffmpeg"
else
    echo "⚠️  Unknown OS. Please install ffmpeg manually."
fi

echo ""
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "🚀 Quick start:"
echo "  python example.py          # Run demo"
echo "  python demo_data.py        # Generate sample data"
echo ""
echo "📖 For full setup, see QUICK_START.md"