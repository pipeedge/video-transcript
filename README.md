# 🎙️ AI-Powered Podcast Analysis Application

A sophisticated application that processes podcast series from YouTube, extracts actionable insights, and provides a rich, searchable interface for users. Built following the architecture of MFM Vault with open-source LLM integration.

## ✨ Features

- **📺 YouTube Integration**: Automatically discover and download podcast episodes from YouTube channels
- **🎯 Audio Transcription**: High-accuracy transcription using **Whisper (open-source)** with fallback to Deepgram
- **🤖 AI-Powered Processing**: Extract insights, frameworks, and stories using **open-source LLMs** (Mistral)
- **🔍 Fast Search**: Lightning-fast search with MeiliSearch indexing
- **📊 Rich Insights**: Categorized extraction of business ideas, mental models, actionable advice, and more
- **⏰ Deep-linking**: Precise timestamps for jumping directly to relevant moments
- **🌐 REST API**: Full-featured API for integration with other applications
- **💰 Cost-Effective**: Works entirely with free/open-source tools (no API keys required for basic functionality)

## 🏗️ Architecture

The application follows a three-phase architecture:

### Phase 1: Data Ingestion and Transcription
- YouTube video discovery and audio extraction using `pytube` and `yt-dlp`
- **Open-source transcription with Whisper** (no API key required)
- Optional Deepgram integration for enhanced speaker diarization
- Automatic timestamp extraction

### Phase 2: LLM-Powered Content Processing  
- **Open-source LLM processing** using Mistral models (runs locally)
- Text cleaning and formatting for readability
- Automatic segment title generation
- Insight extraction across multiple categories
- Chunked processing to handle long transcripts
- Timestamp mapping for deep-linking

### Phase 3: Search and Retrieval
- MeiliSearch integration for fast full-text search
- Optional vector similarity search for related insights
- Optional external product information lookup
- Rich filtering and categorization

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Required Dependencies**:
   - MeiliSearch server (for search functionality) - Free and open-source
3. **Optional Dependencies** (for enhanced features):
   - GPU with CUDA (for faster local LLM processing)
   - API keys for premium services (Deepgram, etc.)
4. **No API Keys Required** for basic functionality! 🎉

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd video-transcript
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** (optional):
```bash
cp .env.example .env
# The default settings work without any API keys!
```

4. **Start MeiliSearch** (using Docker):
```bash
docker run -it --rm \
  -p 7700:7700 \
  -v $(pwd)/meili_data:/meili_data \
  getmeili/meilisearch:latest
```

5. **Test with demo data** (no downloads needed):
```bash
python demo_data.py
python example.py
```

### Usage

#### Quick Demo (No Setup Required)

1. **Run the demo** (uses sample data):
```bash
python example.py
```

#### Command Line Interface

1. **Process a YouTube channel** (requires internet):
```bash
python run.py process "https://www.youtube.com/@YourPodcastChannel" --max-videos 2
# Note: Uses Whisper for free transcription (no API key needed)
```

2. **Start the API server**:
```bash
python run.py api
```

3. **Search for insights**:
```bash
python run.py search "business model" --type insights --category "Business Ideas"
```

#### API Usage

Start the API server:
```bash
python run.py api
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

**Example API calls**:

Process a channel:
```bash
curl -X POST "http://localhost:8000/process-channel" \
  -H "Content-Type: application/json" \
  -d '{"channel_url": "https://www.youtube.com/@YourChannel", "max_videos": 5}'
```

Search for insights:
```bash
curl -X POST "http://localhost:8000/search/insights" \
  -H "Content-Type: application/json" \
  -d '{"query": "startup funding", "category": "Business Ideas", "limit": 10}'
```

## 📁 Project Structure

```
video-transcript/
├── src/
│   ├── data_ingestion/          # YouTube download and transcription
│   │   ├── youtube_downloader.py
│   │   └── transcription.py
│   ├── llm_processing/          # LLM-based text processing
│   │   ├── llm_service.py
│   │   └── text_processor.py
│   ├── search/                  # Search and indexing
│   │   └── search_service.py
│   ├── api/                     # REST API
│   │   └── app.py
│   ├── models/                  # Data models
│   │   └── podcast.py
│   ├── config/                  # Configuration
│   │   └── settings.py
│   └── main.py                  # Main orchestrator
├── data/                        # Data storage
│   ├── raw/
│   ├── processed/
│   ├── audio/
│   └── transcripts/
├── requirements.txt
├── .env.example
├── run.py                       # CLI runner
└── README.md
```

## 🔧 Configuration

### Environment Variables

The application works out-of-the-box with default settings! Create a `.env` file only if you want to customize:

```env
# ===========================================
# BASIC SETTINGS (All Optional!)
# ===========================================

# Demo mode (limits to 2 videos to save resources)
DEMO_MODE=True

# MeiliSearch (defaults to localhost:7700)
MEILISEARCH_URL=http://localhost:7700

# Whisper model size (tiny=fastest, large=most accurate)
WHISPER_MODEL=base

# ===========================================
# PREMIUM FEATURES (Optional API Keys)
# ===========================================

# For enhanced transcription (otherwise uses free Whisper)
# DEEPGRAM_API_KEY=your_deepgram_api_key_here

# For private Hugging Face models (otherwise uses public models)
# HUGGINGFACE_TOKEN=your_huggingface_token_here

# For product lookup features
# PERPLEXITY_API_KEY=your_perplexity_api_key
```

### LLM Configuration

The application uses **free, open-source LLMs** by default:

- **Default**: `mistralai/Mistral-7B-Instruct-v0.3` (runs locally, no API key needed)
- **Transcription**: Whisper `base` model (good balance of speed vs accuracy)

You can customize models in `src/config/settings.py`:

```python
DEFAULT_LLM_MODEL = "your-preferred-model"  # Any Hugging Face model
WHISPER_MODEL = "large"  # For better accuracy: tiny, base, small, medium, large
```

## 📊 Insight Categories

The application extracts insights into the following categories:

- **Business Ideas**: Startup concepts and business opportunities
- **Mental Models**: Frameworks for thinking and decision-making
- **Frameworks**: Structured approaches to problems
- **Stories**: Anecdotes and case studies
- **Products Mentioned**: Tools and products discussed
- **Actionable Advice**: Practical tips and recommendations
- **Quotes**: Memorable quotes and statements
- **Numbers & Metrics**: Important statistics and data points

## 🔍 Search Features

### Full-Text Search
- Search across all content types (insights, segments, episodes)
- Advanced filtering by category, speaker, time range
- Highlighted search results

### Semantic Search
- Find related insights using vector similarity
- Discover connections across different episodes
- Topic clustering and recommendation

## 🚀 Performance

### Optimization Features
- **Parallel Processing**: Concurrent transcription and LLM processing
- **Chunked Processing**: Handle long transcripts efficiently  
- **Caching**: Avoid reprocessing existing content
- **Background Tasks**: Non-blocking API operations
- **Fast Search**: Sub-second search response times

### Hardware Requirements

**Minimum (Demo Mode):**
- **CPU**: 2+ cores
- **RAM**: 4GB
- **Storage**: 2GB free space
- **Internet**: Only for downloading videos

**Recommended (Production):**
- **CPU**: 4+ cores 
- **RAM**: 8GB+ (16GB for large Whisper models)
- **GPU**: Optional - speeds up processing significantly
- **Storage**: ~100MB per hour of audio content

**Cost**: $0 - runs entirely on your hardware!

## 🔗 API Reference

### Endpoints

- `POST /process-channel`: Start processing a YouTube channel
- `GET /status`: Get processing status and statistics
- `POST /search/insights`: Search for insights
- `POST /search/segments`: Search transcript segments
- `POST /search/episodes`: Search episodes
- `GET /categories`: Get available insight categories
- `GET /stats`: Get database statistics

Full API documentation is available at `/docs` when running the server.

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by [MFM Vault](https://www.youtube.com/watch?v=NQtWHOUmqNw&ab_channel=GregKamradt)
- **Built entirely with free, open-source tools:**
  - 🎤 Transcription: OpenAI Whisper
  - 🤖 LLM: Mistral (Hugging Face)
  - 🔍 Search: MeiliSearch
  - 📺 Downloads: yt-dlp & pytube
- Optional premium integrations: Deepgram, Perplexity

## 💡 Why Open Source?

This implementation prioritizes **accessibility and cost-effectiveness**:

- ✅ **No API costs** - runs entirely on your hardware
- ✅ **Privacy-first** - your data never leaves your machine  
- ✅ **Customizable** - modify models and prompts as needed
- ✅ **Educational** - learn how each component works
- ✅ **Scalable** - add premium features when needed

## 📞 Support

For questions and support:
- Open an issue on GitHub
- Check the documentation at `/docs`
- Review the example usage in `run.py` and `example.py`
- Try the demo mode first: `python example.py`

---

**Happy podcast analyzing! 🎧 (No credit card required!)**