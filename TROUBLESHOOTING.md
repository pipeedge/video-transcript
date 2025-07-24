# 🛠️ Troubleshooting Guide

Common issues and solutions for the Podcast Analyzer.

## 🎵 Audio Processing Issues

### "Couldn't find ffmpeg or avconv"

**Problem**: pydub can't find ffmpeg for audio processing.

**Solution**:
```bash
# Run the automatic installer
./install_dependencies.sh

# Or install manually:

# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS with Homebrew
brew install ffmpeg

# Windows with Chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

### "No audio data found"

**Problem**: Audio file is corrupted or in unsupported format.

**Solution**:
- Try a different video
- Check if the video has audio
- Ensure internet connection for downloads

## 🤖 LLM Issues

### "SyntaxError: invalid syntax"

**Problem**: Python syntax error in the code.

**Solution**: The error has been fixed. Update your code:
```bash
git pull  # If using git
# Or re-download the fixed files
```

### "CUDA out of memory"

**Problem**: GPU memory insufficient for large models.

**Solutions**:
```bash
# Use smaller models
export WHISPER_MODEL=tiny  # Instead of large

# Or use CPU only
export CUDA_VISIBLE_DEVICES=""
```

### "Model download taking forever"

**Problem**: Large model downloads are slow.

**Solutions**:
1. Start with smaller models:
   ```bash
   export WHISPER_MODEL=base  # 142MB instead of 2.9GB
   ```

2. Use demo mode first:
   ```bash
   python example.py  # No downloads needed
   ```

3. Check available space:
   ```bash
   df -h  # Ensure 3GB+ free space for large models
   ```

## 🔍 Search Issues

### "MeiliSearch connection failed"

**Problem**: Can't connect to MeiliSearch server.

**Solutions**:
1. Check if MeiliSearch is running:
   ```bash
   docker ps | grep meilisearch
   ```

2. Start MeiliSearch:
   ```bash
   docker run -d --name meilisearch -p 7700:7700 getmeili/meilisearch:latest
   ```

3. Check the URL in .env:
   ```bash
   MEILISEARCH_URL=http://localhost:7700
   ```

### "Index not found"

**Problem**: Search index hasn't been created yet.

**Solution**: Process some content first:
```bash
python demo_data.py  # Create demo data
# Or process real videos
python run.py process "CHANNEL_URL" --max-videos 1
```

## 📺 YouTube Download Issues

### "Video unavailable"

**Problem**: Video is private, deleted, or geo-blocked.

**Solutions**:
- Try a different video/channel
- Check if the URL is correct
- Some channels block downloads

### "HTTP Error 403"

**Problem**: YouTube is blocking the download.

**Solutions**:
1. Update yt-dlp:
   ```bash
   pip install --upgrade yt-dlp
   ```

2. Try a different video

3. Use demo mode instead:
   ```bash
   python example.py
   ```

## 💾 Memory Issues

### "Out of memory"

**Problem**: System running out of RAM.

**Solutions**:
1. Enable demo mode:
   ```bash
   export DEMO_MODE=True
   ```

2. Use smaller models:
   ```bash
   export WHISPER_MODEL=tiny
   ```

3. Process fewer videos:
   ```bash
   python run.py process "URL" --max-videos 1
   ```

4. Close other applications

### "Disk space full"

**Problem**: Not enough storage space.

**Solutions**:
1. Clean up old downloads:
   ```bash
   rm -rf data/audio/*  # Remove old audio files
   rm -rf data/transcripts/*  # Remove old transcripts
   ```

2. Use smaller Whisper models

3. Enable demo mode

## 🐍 Python Environment Issues

### "ModuleNotFoundError"

**Problem**: Missing Python packages.

**Solution**:
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install missing package individually
pip install <package_name>
```

### "Permission denied"

**Problem**: Can't write to directories.

**Solutions**:
1. Check directory permissions:
   ```bash
   ls -la data/
   ```

2. Fix permissions:
   ```bash
   chmod -R 755 data/
   ```

3. Run from correct directory:
   ```bash
   cd video-transcript
   python run.py
   ```

## 🌐 Network Issues

### "Connection timeout"

**Problem**: Network requests failing.

**Solutions**:
1. Check internet connection
2. Try different network
3. Use demo mode (works offline):
   ```bash
   python example.py
   ```

### "SSL Certificate error"

**Problem**: HTTPS certificate issues.

**Solutions**:
1. Update certificates:
   ```bash
   pip install --upgrade certifi
   ```

2. Try different network

## 🔧 Configuration Issues

### "Environment variables not loading"

**Problem**: .env file not being read.

**Solutions**:
1. Check file location:
   ```bash
   ls -la .env  # Should be in project root
   ```

2. Check file format:
   ```bash
   cat .env  # Should have KEY=value format
   ```

3. No spaces around =:
   ```bash
   # Wrong: KEY = value
   # Right: KEY=value
   ```

### "Demo mode not working"

**Problem**: Demo mode settings not applied.

**Solution**:
```bash
# Set in environment
export DEMO_MODE=True

# Or in .env file
echo "DEMO_MODE=True" >> .env
```

## 🚨 Emergency Fixes

### "Everything is broken"

**Nuclear option - fresh start**:
```bash
# 1. Clean everything
rm -rf data/
rm -rf .env

# 2. Reinstall
pip install -r requirements.txt

# 3. Test with demo
python example.py

# 4. If that works, try real processing
python run.py process "URL" --max-videos 1
```

### "Need help NOW"

**Quick diagnostic**:
```bash
# Check system
python --version  # Should be 3.8+
pip list | grep torch  # Should show torch
docker --version  # For MeiliSearch

# Test components
python -c "import whisper; print('Whisper OK')"
python -c "import torch; print('Torch OK')"
python -c "from transformers import AutoTokenizer; print('Transformers OK')"

# Run minimal test
python example.py
```

## 📞 Getting Help

If you're still stuck:

1. **Check the logs**:
   ```bash
   tail -f podcast_analyzer.log
   ```

2. **Run with debug mode**:
   ```bash
   export DEBUG=True
   python run.py process "URL" --max-videos 1
   ```

3. **Try demo mode first**:
   ```bash
   python example.py  # Should always work
   ```

4. **Create GitHub issue** with:
   - Your OS and Python version
   - Error message
   - What you were trying to do
   - Log file contents

---

**Remember**: The demo mode (`python example.py`) should always work since it doesn't require any external dependencies!