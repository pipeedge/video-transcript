import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent

# API Keys (Optional - will fallback to open-source alternatives)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")  # Optional: Will use Whisper if not provided
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")  # Optional: For private models
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")  # Optional: For product lookup
EXA_API_KEY = os.getenv("EXA_API_KEY")  # Optional: For web search

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/podcast_db")

# MeiliSearch
MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY")

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"

# Create directories if they don't exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, AUDIO_DIR, TRANSCRIPTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# LLM Settings
DEFAULT_LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"  # Open source model
FALLBACK_LLM_MODEL = "microsoft/DialoGPT-medium"  # Simpler fallback model
CHUNK_SIZE = 4000  # For transcript chunking
CHUNK_OVERLAP = 200  # Overlap between chunks

# Transcription Settings
USE_WHISPER = True  # Use open-source Whisper by default
WHISPER_MODEL = "medium"  # Whisper model size: tiny, base, small, medium, large

# Demo Mode Settings
DEMO_MODE = os.getenv("DEMO_MODE", "False").lower() == "true"
MAX_DEMO_VIDEOS = 2  # Limit for demo mode