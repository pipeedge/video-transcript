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
    YouTubeTranscriptApi = None
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
        if not YOUTUBE_TRANSCRIPT_AVAILABLE or YouTubeTranscriptApi is None:
            raise ImportError("youtube-transcript-api not installed")
        
        try:
            # Use the correct API pattern - instantiate and call fetch
            api = YouTubeTranscriptApi()
            transcript_data = api.fetch(video_info.video_id)
            
            # Convert to TranscriptSegment objects
            segments = []
            for i, entry in enumerate(transcript_data):
                segment = TranscriptSegment(
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
            # Convert URL to string if it's a Pydantic URL object
            url_str = str(video_info.url) if video_info.url else f"https://www.youtube.com/watch?v={video_info.video_id}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_str])
            
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
            # Convert URL to string if it's a Pydantic URL object
            url_str = str(video_info.url) if video_info.url else f"https://www.youtube.com/watch?v={video_info.video_id}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_str])
            
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
    
    def _get_channel_videos_direct(self, channel_url: str, max_videos: Optional[int] = None) -> List[VideoInfo]:
        """
        Get channel videos using a simpler approach optimized for transcript extraction
        """
        videos = []
        
        # Simple yt-dlp configuration focused on getting video metadata
        ydl_opts = {
            'quiet': False,  # Show more info for debugging
            'extract_flat': False,  # Get full video info
            'ignoreerrors': True,
            'no_download': True,
            'playlistend': max_videos if max_videos else 20,  # Reasonable default limit
            'retries': 3,
        }
        
        try:
            logger.info(f"Getting channel videos directly for transcript extraction: {channel_url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                if not info:
                    logger.error("No channel info extracted")
                    return []
                
                # Handle both single videos and playlists/channels
                if 'entries' in info:
                    entries = info['entries']
                    logger.info(f"Found {len(entries)} entries in channel")
                    
                    def process_entry(entry, depth=0):
                        """Recursively process entries (handles nested playlists)"""
                        if not entry:
                            return
                            
                        # Skip if we've reached max_videos
                        if max_videos and len(videos) >= max_videos:
                            return
                        
                        # Debug: log entry structure
                        entry_type = entry.get('_type', 'unknown')
                        entry_id = entry.get('id', 'no_id')
                        entry_title = entry.get('title', 'no_title')
                        logger.info(f"Processing entry (depth {depth}): type={entry_type}, id={entry_id}, title={entry_title}")
                        
                        # If this entry has its own entries (nested playlist), process them
                        if 'entries' in entry and entry['entries']:
                            logger.info(f"Found nested playlist with {len(entry['entries'])} entries: {entry_title}")
                            for sub_entry in entry['entries']:
                                process_entry(sub_entry, depth + 1)
                        else:
                            # This is an actual video
                            try:
                                video_id = entry.get('id', '')
                                
                                # Validate video ID (YouTube video IDs are 11 characters)
                                if not video_id or len(video_id) != 11:
                                    logger.warning(f"Invalid video ID length ({len(video_id)}): {video_id}")
                                    return
                                
                                # Create VideoInfo from entry
                                video_info = VideoInfo(
                                    video_id=video_id,
                                    title=entry.get('title', ''),
                                    description=entry.get('description', ''),
                                    url=entry.get('webpage_url', f"https://www.youtube.com/watch?v={video_id}"),
                                    duration=entry.get('duration'),
                                    publish_date=datetime.fromtimestamp(entry.get('timestamp', 0)) if entry.get('timestamp') else None,
                                    thumbnail_url=entry.get('thumbnail')
                                )
                                
                                videos.append(video_info)
                                logger.info(f"✅ Added video {len(videos)}: {video_info.title}")
                                
                            except Exception as e:
                                logger.warning(f"Error processing entry: {e}")
                    
                    # Process all entries (including nested ones)
                    for entry in entries:
                        process_entry(entry)
                else:
                    # Single video
                    if info.get('id'):
                        video_info = VideoInfo(
                            video_id=info['id'],
                            title=info.get('title', ''),
                            description=info.get('description', ''),
                            url=info.get('webpage_url', channel_url),
                            duration=info.get('duration'),
                            publish_date=datetime.fromtimestamp(info.get('timestamp', 0)) if info.get('timestamp') else None,
                            thumbnail_url=info.get('thumbnail')
                        )
                        videos.append(video_info)
                        logger.info(f"Added single video: {video_info.title}")
                
        except Exception as e:
            logger.error(f"Error extracting channel videos: {e}")
            
        logger.info(f"Successfully discovered {len(videos)} videos for transcript extraction")
        return videos
    
    def process_channel_transcripts(self, channel_url: str, max_videos: Optional[int] = None) -> List[tuple[VideoInfo, List[TranscriptSegment]]]:
        """
        Extract transcripts from all videos in a channel
        
        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to process
            
        Returns:
            List of tuples (VideoInfo, transcript_segments)
        """
        # Get video list using our direct method (doesn't rely on audio download logic)
        videos = self._get_channel_videos_direct(channel_url, max_videos)
        
        if not videos:
            logger.error(f"No videos found in channel: {channel_url}")
            return []
        
        results = []
        for video_info in videos:
            transcript_segments = self.extract_transcript_from_video(video_info)
            if transcript_segments:
                results.append((video_info, transcript_segments))
        
        logger.info(f"Successfully extracted transcripts from {len(results)} videos")
        return results 