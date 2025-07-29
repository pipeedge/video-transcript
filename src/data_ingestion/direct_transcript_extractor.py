import logging
import re
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter, JSONFormatter
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    YOUTUBE_TRANSCRIPT_AVAILABLE = False

import yt_dlp
from ..models.podcast import VideoInfo, TranscriptSegment
from ..config.settings import TRANSCRIPTS_DIR

logger = logging.getLogger(__name__)


class DirectTranscriptExtractor:
    """Extract transcripts directly from YouTube videos without downloading audio"""
    
    def __init__(self):
        self.transcripts_dir = Path(TRANSCRIPTS_DIR)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_transcript_from_video(self, video_info: VideoInfo) -> Optional[List[TranscriptSegment]]:
        """
        Extract transcript from a video using multiple methods
        
        Args:
            video_info: VideoInfo object containing video details
            
        Returns:
            List of TranscriptSegment objects or None if failed
        """
        logger.info(f"Attempting to extract transcript for: {video_info.title}")
        
        # Try multiple extraction methods in order of preference
        methods = [
            ("YouTube Transcript API", self._extract_with_youtube_transcript_api),
            ("yt-dlp Auto Subtitles", self._extract_with_ytdlp_auto_subtitles),
            ("yt-dlp Manual Subtitles", self._extract_with_ytdlp_manual_subtitles),
        ]
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying {method_name} for {video_info.video_id}")
                segments = method_func(video_info)
                
                if segments:
                    logger.info(f"✅ Successfully extracted transcript using {method_name}")
                    self._save_transcript(video_info, segments, method_name)
                    return segments
                else:
                    logger.warning(f"❌ {method_name} returned no transcript")
                    
            except Exception as e:
                logger.warning(f"❌ {method_name} failed: {str(e)[:100]}...")
                continue
        
        logger.error(f"❌ All transcript extraction methods failed for {video_info.video_id}")
        return None
    
    def _extract_with_youtube_transcript_api(self, video_info: VideoInfo) -> Optional[List[TranscriptSegment]]:
        """Extract transcript using YouTube Transcript API"""
        if not YOUTUBE_TRANSCRIPT_AVAILABLE:
            raise ImportError("youtube-transcript-api not installed")
        
        try:
            # Try to get transcript in English first, then any available language
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_info.video_id)
            
            # Prefer manual transcripts over auto-generated
            transcript = None
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
            except:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except:
                    # Get any available transcript
                    available_transcripts = list(transcript_list)
                    if available_transcripts:
                        transcript = available_transcripts[0]
            
            if not transcript:
                return None
            
            # Fetch the transcript data
            transcript_data = transcript.fetch()
            
            # Convert to TranscriptSegment objects
            segments = []
            for i, entry in enumerate(transcript_data):
                segment = TranscriptSegment(
                    segment_id=f"{video_info.video_id}_{i}",
                    video_id=video_info.video_id,
                    start_time=entry.get('start', 0),
                    end_time=entry.get('start', 0) + entry.get('duration', 0),
                    text=entry.get('text', '').strip(),
                    speaker=None  # YouTube transcripts don't include speaker info
                )
                segments.append(segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"YouTube Transcript API error: {e}")
            return None
    
    def _extract_with_ytdlp_auto_subtitles(self, video_info: VideoInfo) -> Optional[List[TranscriptSegment]]:
        """Extract auto-generated subtitles using yt-dlp"""
        ydl_opts = {
            'writeautomaticsub': True,
            'writesubtitles': False,
            'subtitleslangs': ['en'],
            'subtitlesformat': 'vtt',
            'skip_download': True,
            'outtmpl': str(self.transcripts_dir / f'{video_info.video_id}.%(ext)s'),
            'quiet': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_info.url])
            
            # Look for the downloaded subtitle file
            subtitle_file = self.transcripts_dir / f"{video_info.video_id}.en.vtt"
            if subtitle_file.exists():
                return self._parse_vtt_file(subtitle_file, video_info.video_id)
            
            return None
            
        except Exception as e:
            logger.error(f"yt-dlp auto subtitles error: {e}")
            return None
    
    def _extract_with_ytdlp_manual_subtitles(self, video_info: VideoInfo) -> Optional[List[TranscriptSegment]]:
        """Extract manual subtitles using yt-dlp"""
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': False,
            'subtitleslangs': ['en'],
            'subtitlesformat': 'vtt',
            'skip_download': True,
            'outtmpl': str(self.transcripts_dir / f'{video_info.video_id}.%(ext)s'),
            'quiet': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_info.url])
            
            # Look for the downloaded subtitle file
            subtitle_file = self.transcripts_dir / f"{video_info.video_id}.en.vtt"
            if subtitle_file.exists():
                return self._parse_vtt_file(subtitle_file, video_info.video_id)
            
            return None
            
        except Exception as e:
            logger.error(f"yt-dlp manual subtitles error: {e}")
            return None
    
    def _parse_vtt_file(self, vtt_file: Path, video_id: str) -> List[TranscriptSegment]:
        """Parse VTT subtitle file into TranscriptSegment objects"""
        segments = []
        
        try:
            with open(vtt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse VTT format
            # VTT format: timestamp --> timestamp \n text
            pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\n(.*?)(?=\n\n|\n\d{2}:\d{2}:\d{2}|$)'
            matches = re.findall(pattern, content, re.DOTALL)
            
            for i, (start_time, end_time, text) in enumerate(matches):
                # Convert timestamp to seconds
                start_seconds = self._timestamp_to_seconds(start_time)
                end_seconds = self._timestamp_to_seconds(end_time)
                
                # Clean text (remove VTT tags)
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                clean_text = re.sub(r'\n+', ' ', clean_text)
                
                if clean_text:
                    segment = TranscriptSegment(
                        segment_id=f"{video_id}_{i}",
                        video_id=video_id,
                        start_time=start_seconds,
                        end_time=end_seconds,
                        text=clean_text,
                        speaker=None
                    )
                    segments.append(segment)
            
            # Clean up the VTT file
            vtt_file.unlink()
            
            return segments
            
        except Exception as e:
            logger.error(f"Error parsing VTT file: {e}")
            return []
    
    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert VTT timestamp (HH:MM:SS.mmm) to seconds"""
        try:
            parts = timestamp.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            return total_seconds
        except:
            return 0.0
    
    def _save_transcript(self, video_info: VideoInfo, segments: List[TranscriptSegment], method: str):
        """Save transcript to JSON file"""
        try:
            transcript_data = {
                'video_id': video_info.video_id,
                'title': video_info.title,
                'url': video_info.url,
                'extraction_method': method,
                'extracted_at': datetime.now().isoformat(),
                'segments': [
                    {
                        'segment_id': seg.segment_id,
                        'start_time': seg.start_time,
                        'end_time': seg.end_time,
                        'text': seg.text,
                        'speaker': seg.speaker
                    }
                    for seg in segments
                ]
            }
            
            output_file = self.transcripts_dir / f"{video_info.video_id}_direct_transcript.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved transcript to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving transcript: {e}")
    
    def process_channel_transcripts(self, channel_url: str, max_videos: Optional[int] = None) -> List[tuple[VideoInfo, List[TranscriptSegment]]]:
        """
        Extract transcripts from all videos in a channel
        
        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to process
            
        Returns:
            List of tuples (VideoInfo, transcript_segments)
        """
        from .youtube_downloader import YouTubeDownloader
        
        # Get video list using existing downloader
        downloader = YouTubeDownloader()
        videos = downloader.get_channel_videos(channel_url, max_videos)
        
        results = []
        for video_info in videos:
            transcript_segments = self.extract_transcript_from_video(video_info)
            if transcript_segments:
                results.append((video_info, transcript_segments))
        
        logger.info(f"Successfully extracted transcripts from {len(results)} videos")
        return results 