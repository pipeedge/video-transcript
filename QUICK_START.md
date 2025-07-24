# 🚀 Quick Start Guide - No API Keys Required!

This guide gets you running in minutes with **zero API costs**.

## ⚡ 1-Minute Demo

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run demo with sample data (no downloads needed)
python example.py
```

That's it! See the demo output showing how insights are extracted.

## 🎯 Full Setup (5 Minutes)

### Step 1: Setup Environment
```bash
# Clone and enter directory
git clone <repo-url>
cd video-transcript

# Install Python dependencies
pip install -r requirements.txt

# Copy environment config (optional - works without it!)
cp .env.example .env
```

### Step 2: Start Search Engine
```bash
# Start MeiliSearch with Docker (one-time setup)
docker run -d \
  --name meilisearch \
  -p 7700:7700 \
  -v $(pwd)/meili_data:/meili_data \
  getmeili/meilisearch:latest
```

### Step 3: Test with Demo Data
```bash
# Generate and test with sample podcast data
python demo_data.py
python example.py
```

### Step 4: Process Real Podcasts (Optional)
```bash
# Process a real YouTube channel (uses free Whisper transcription)
python run.py process "https://www.youtube.com/@SomeChannel" --max-videos 2

# Start API server
python run.py api

# Visit http://localhost:8000/docs for API interface
```

## 🎛️ What Runs Where

| Component | Location | Cost |
|-----------|----------|------|
| **Transcription** | Your computer (Whisper) | $0 |
| **LLM Processing** | Your computer (Mistral) | $0 |
| **Search** | Local MeiliSearch | $0 |
| **Video Download** | YouTube → Your computer | $0 |

**Total API costs: $0/month** 🎉

## 🔧 Configuration Options

### Whisper Model Sizes
Edit `WHISPER_MODEL` in `.env`:

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `tiny` | 37MB | 10x realtime | Basic | Testing |
| `base` | 142MB | 7x realtime | Good | **Default** |
| `small` | 461MB | 4x realtime | Better | Production |
| `medium` | 1.4GB | 2x realtime | Very Good | High quality |
| `large` | 2.9GB | 1x realtime | Best | Maximum accuracy |

### Demo Mode
Set `DEMO_MODE=True` in `.env` to:
- Limit processing to 2 videos max
- Use smaller models for faster testing
- Skip resource-intensive operations

## 🚨 Troubleshooting

### "No module named 'torch'"
```bash
pip install torch
```

### "MeiliSearch connection failed"
```bash
# Check if MeiliSearch is running
docker ps | grep meilisearch

# Restart if needed
docker restart meilisearch
```

### "Model download taking forever"
- Start with `WHISPER_MODEL=tiny` for fastest setup
- Models are cached after first download
- Use demo mode first: `python example.py`

### "Out of memory"
- Reduce Whisper model size: `WHISPER_MODEL=tiny`
- Enable demo mode: `DEMO_MODE=True`
- Process fewer videos: `--max-videos 1`

## 🎯 Next Steps

1. **Explore the demo**: `python example.py`
2. **Try real processing**: `python run.py process "CHANNEL_URL" --max-videos 1`
3. **Use the API**: `python run.py api` → http://localhost:8000/docs
4. **Customize insights**: Edit categories in `src/llm_processing/text_processor.py`
5. **Add premium features**: Uncomment API keys in `.env` as needed

## 💡 Pro Tips

- Start with demo mode to understand the workflow
- Use `base` Whisper model for good speed/accuracy balance
- Process 1-2 videos first to test your setup
- Check logs if something fails: `tail -f podcast_analyzer.log`
- GPU speeds up processing significantly if available

---

**🎉 You're ready to analyze podcasts for free!**