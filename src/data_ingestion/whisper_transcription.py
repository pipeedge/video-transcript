import logging
import json
import os
from typing import List, Optional
from pathlib import Path
try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from ..config.settings import TRANSCRIPTS_DIR
from ..models.podcast import TranscriptSegment

logger = logging.getLogger(__name__)


class WhisperTranscriptionService:
    """Open-source transcription service using OpenAI Whisper"""
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper transcription service
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
                       - tiny: fastest, least accurate
                       - base: good balance for demo
                       - small/medium: better accuracy
                       - large: best accuracy but slower
        """
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisper not available (Python 3.13 compatibility)")
            
        self.model_size = model_size
        self.transcripts_dir = Path(TRANSCRIPTS_DIR)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Initializing Whisper model '{model_size}' on device: {self.device}")
        
        try:
            # Load Whisper model
            self.model = whisper.load_model(model_size, device=self.device)
            logger.info(f"Successfully loaded Whisper model: {model_size}")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise
    
    def transcribe_audio(self, audio_path: Path, video_id: str) -> Optional[List[TranscriptSegment]]:
        """
        Transcribe audio file using Whisper
        
        Args:
            audio_path: Path to the audio file
            video_id: Video ID for caching purposes
            
        Returns:
            List of TranscriptSegment objects or None if failed
        """
        try:
            # Check if transcript already exists
            transcript_path = self.transcripts_dir / f"{video_id}_whisper.json"
            if transcript_path.exists():
                logger.info(f"Loading existing Whisper transcript: {transcript_path}")
                return self._load_transcript(transcript_path)
            
            logger.info(f"Transcribing audio with Whisper: {audio_path}")
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                str(audio_path),
                word_timestamps=True,  # Enable word-level timestamps
                verbose=False
            )
            
            # Extract segments from result
            segments = self._extract_segments(result)
            
            # Save transcript for caching
            self._save_transcript(segments, transcript_path)
            
            logger.info(f"Successfully transcribed audio. Found {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"Error transcribing audio {audio_path}: {e}")
            return None
    
    def _extract_segments(self, whisper_result) -> List[TranscriptSegment]:
        """
        Extract transcript segments from Whisper result
        
        Args:
            whisper_result: Whisper transcription result
            
        Returns:
            List of TranscriptSegment objects
        """
        segments = []
        
        try:
            # Process segments from Whisper result
            for segment_data in whisper_result.get("segments", []):
                # Create segment from Whisper segment
                segment = TranscriptSegment(
                    text=segment_data["text"].strip(),
                    start_time=segment_data["start"],
                    end_time=segment_data["end"],
                    speaker=None,  # Whisper doesn't do speaker diarization by default
                    confidence=segment_data.get("avg_logprob", None)
                )
                segments.append(segment)
            
            # If no segments found, try to create from words
            if not segments and "words" in whisper_result:
                segments = self._create_segments_from_words(whisper_result["words"])
            
            return segments
            
        except Exception as e:
            logger.error(f"Error extracting segments from Whisper result: {e}")
            return []
    
    def _create_segments_from_words(self, words, max_segment_length: int = 30) -> List[TranscriptSegment]:
        """
        Create segments from word-level timestamps
        
        Args:
            words: List of word objects with timestamps
            max_segment_length: Maximum segment length in seconds
            
        Returns:
            List of TranscriptSegment objects
        """
        segments = []
        current_text = ""
        current_start = None
        last_end = 0
        
        for word in words:
            word_start = word.get("start", last_end)
            word_end = word.get("end", word_start + 1)
            word_text = word.get("word", "")
            
            # Start new segment if this is the first word
            if current_start is None:
                current_start = word_start
            
            # Check if we should start a new segment
            should_break = (
                (word_start - current_start) > max_segment_length or  # Time limit
                len(current_text) > 200 or  # Text length limit
                word_text.endswith('.') or word_text.endswith('?') or word_text.endswith('!')  # Sentence end
            )
            
            if should_break and current_text.strip():
                # Create segment from accumulated text
                segment = TranscriptSegment(
                    text=current_text.strip(),
                    start_time=current_start,
                    end_time=last_end,
                    speaker=None
                )
                segments.append(segment)
                
                # Reset for next segment
                current_text = ""
                current_start = word_start
            
            # Add word to current segment
            current_text += word_text + " "
            last_end = word_end
        
        # Add final segment if we have remaining text
        if current_text.strip() and current_start is not None:
            segment = TranscriptSegment(
                text=current_text.strip(),
                start_time=current_start,
                end_time=last_end,
                speaker=None
            )
            segments.append(segment)
        
        return segments
    
    def _save_transcript(self, segments: List[TranscriptSegment], path: Path):
        """Save transcript segments to JSON file"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([segment.dict() for segment in segments], f, indent=2, ensure_ascii=False)
            logger.info(f"Saved Whisper transcript to: {path}")
        except Exception as e:
            logger.error(f"Error saving transcript: {e}")
    
    def _load_transcript(self, path: Path) -> List[TranscriptSegment]:
        """Load transcript segments from JSON file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [TranscriptSegment(**segment) for segment in data]
        except Exception as e:
            logger.error(f"Error loading transcript: {e}")
            return []
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Get list of available Whisper models"""
        return ["tiny", "base", "small", "medium", "large"]
    
    @staticmethod
    def get_model_info() -> dict:
        """Get information about Whisper models"""
        return {
            "tiny": {"size": "~37 MB", "speed": "~10x realtime", "accuracy": "Basic"},
            "base": {"size": "~142 MB", "speed": "~7x realtime", "accuracy": "Good"},
            "small": {"size": "~461 MB", "speed": "~4x realtime", "accuracy": "Better"},
            "medium": {"size": "~1.4 GB", "speed": "~2x realtime", "accuracy": "Very Good"},
            "large": {"size": "~2.9 GB", "speed": "~1x realtime", "accuracy": "Best"}
        }