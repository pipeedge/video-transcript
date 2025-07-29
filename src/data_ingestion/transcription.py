import logging
import json
from typing import List, Optional
from pathlib import Path

try:
    from deepgram import DeepgramClient, PrerecordedOptions
    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False
    # Note: logger defined below

from .whisper_transcription import WhisperTranscriptionService
from ..config.settings import DEEPGRAM_API_KEY, TRANSCRIPTS_DIR
from ..models.podcast import TranscriptSegment

logger = logging.getLogger(__name__)

# Log warning about missing Deepgram after logger is defined
if not DEEPGRAM_AVAILABLE:
    logger.warning("Deepgram SDK not available - using Whisper as fallback")


class TranscriptionService:
    """Handles audio transcription using Whisper (open-source) or Deepgram (if API key provided)"""
    
    def __init__(self, prefer_whisper: bool = True, whisper_model: str = "base"):
        self.transcripts_dir = Path(TRANSCRIPTS_DIR)
        self.use_whisper = prefer_whisper or not DEEPGRAM_API_KEY or not DEEPGRAM_AVAILABLE
        
        if self.use_whisper:
            logger.info("Using Whisper (open-source) for transcription")
            self.whisper_service = WhisperTranscriptionService(whisper_model)
            self.deepgram_client = None
        else:
            logger.info("Using Deepgram for transcription")
            self.whisper_service = None
            
            if not DEEPGRAM_API_KEY:
                raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
                
            self.deepgram_client = DeepgramClient(DEEPGRAM_API_KEY)
            
            # Deepgram options for optimal transcription
            self.deepgram_options = PrerecordedOptions(
                model="nova-2",  # Latest, most accurate model
                language="en",
                punctuate=True,
                diarize=True,  # Speaker diarization
                paragraphs=True,
                utterances=True,
                smart_format=True,
                timestamps=True,
            )
    
    def transcribe_audio(self, audio_path: Path, video_id: str) -> Optional[List[TranscriptSegment]]:
        """
        Transcribe audio file using Whisper or Deepgram
        
        Args:
            audio_path: Path to the audio file
            video_id: Video ID for caching purposes
            
        Returns:
            List of TranscriptSegment objects or None if failed
        """
        if self.use_whisper:
            return self.whisper_service.transcribe_audio(audio_path, video_id)
        else:
            return self._transcribe_with_deepgram(audio_path, video_id)
    
    def _transcribe_with_deepgram(self, audio_path: Path, video_id: str) -> Optional[List[TranscriptSegment]]:
        """Transcribe using Deepgram service"""
        try:
            # Check if transcript already exists
            transcript_path = self.transcripts_dir / f"{video_id}_deepgram.json"
            if transcript_path.exists():
                logger.info(f"Loading existing Deepgram transcript: {transcript_path}")
                return self._load_transcript(transcript_path)
            
            logger.info(f"Transcribing audio with Deepgram: {audio_path}")
            
            # Read audio file
            with open(audio_path, "rb") as audio_file:
                buffer_data = audio_file.read()
            
            # Send to Deepgram for transcription
            response = self.deepgram_client.listen.prerecorded.v("1").transcribe_file(
                {"buffer": buffer_data}, self.deepgram_options
            )
            
            # Extract segments from response
            segments = self._extract_segments_deepgram(response)
            
            # Save transcript for caching
            self._save_transcript(segments, transcript_path)
            
            logger.info(f"Successfully transcribed audio with Deepgram. Found {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"Error transcribing audio with Deepgram {audio_path}: {e}")
            return None
    
    def _extract_segments_deepgram(self, response) -> List[TranscriptSegment]:
        """
        Extract transcript segments from Deepgram response
        
        Args:
            response: Deepgram API response
            
        Returns:
            List of TranscriptSegment objects
        """
        segments = []
        
        try:
            # Access the transcript data
            transcript_data = response.results.channels[0].alternatives[0]
            
            # Process utterances (which include speaker diarization)
            if hasattr(transcript_data, 'utterances') and transcript_data.utterances:
                for utterance in transcript_data.utterances:
                    segment = TranscriptSegment(
                        text=utterance.transcript,
                        start_time=utterance.start,
                        end_time=utterance.end,
                        speaker=f"Speaker {utterance.speaker}" if hasattr(utterance, 'speaker') else None,
                        confidence=utterance.confidence if hasattr(utterance, 'confidence') else None
                    )
                    segments.append(segment)
            
            # Fallback to words if utterances not available
            elif hasattr(transcript_data, 'words') and transcript_data.words:
                current_text = ""
                current_start = None
                current_speaker = None
                
                for word in transcript_data.words:
                    # Start new segment if speaker changes or text gets too long
                    if (current_speaker != word.get('speaker') or len(current_text) > 200) and current_text:
                        if current_start is not None:
                            segment = TranscriptSegment(
                                text=current_text.strip(),
                                start_time=current_start,
                                end_time=word.start,
                                speaker=f"Speaker {current_speaker}" if current_speaker is not None else None
                            )
                            segments.append(segment)
                        
                        current_text = ""
                        current_start = word.start
                    
                    if current_start is None:
                        current_start = word.start
                    
                    current_text += word.punctuated_word + " "
                    current_speaker = word.get('speaker')
                
                # Add final segment
                if current_text and current_start is not None:
                    segment = TranscriptSegment(
                        text=current_text.strip(),
                        start_time=current_start,
                        end_time=transcript_data.words[-1].end,
                        speaker=f"Speaker {current_speaker}" if current_speaker is not None else None
                    )
                    segments.append(segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"Error extracting segments from response: {e}")
            return []
    
    def _save_transcript(self, segments: List[TranscriptSegment], path: Path):
        """Save transcript segments to JSON file"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([segment.dict() for segment in segments], f, indent=2, ensure_ascii=False)
            logger.info(f"Saved transcript to: {path}")
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