import os
import logging
from typing import List, Optional
from pathlib import Path
from datetime import datetime

import yt_dlp
from pytube import Channel
from pydub import AudioSegment

from ..config.settings import AUDIO_DIR, RAW_DATA_DIR
from ..models.podcast import VideoInfo

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Handles YouTube video discovery and audio extraction"""
    
    def __init__(self):
        self.audio_dir = Path(AUDIO_DIR)
        self.raw_data_dir = Path(RAW_DATA_DIR)
        
        # yt-dlp options for high-quality audio extraction
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192K',
            'outtmpl': str(self.audio_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
    
    def get_channel_videos(self, channel_url: str, max_videos: Optional[int] = None) -> List[VideoInfo]:
        """
        Get list of videos from a YouTube channel
        
        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to fetch (None for all)
            
        Returns:
            List of VideoInfo objects
        """
        try:
            logger.info(f"Fetching videos from channel: {channel_url}")
            
            channel = Channel(channel_url)
            videos = []
            
            for i, video in enumerate(channel.video_urls):
                if max_videos and i >= max_videos:
                    break
                    
                try:
                    # Get video metadata using yt-dlp for more reliable info
                    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                        info = ydl.extract_info(video, download=False)
                        
                    video_info = VideoInfo(
                        video_id=info['id'],
                        title=info.get('title', ''),
                        description=info.get('description', ''),
                        url=video,
                        duration=info.get('duration'),
                        publish_date=datetime.fromtimestamp(info.get('timestamp', 0)) if info.get('timestamp') else None,
                        thumbnail_url=info.get('thumbnail')
                    )
                    videos.append(video_info)
                    logger.info(f"Found video: {video_info.title}")
                    
                except Exception as e:
                    logger.error(f"Error extracting info for video {video}: {e}")
                    continue
                    
            logger.info(f"Found {len(videos)} videos from channel")
            return videos
            
        except Exception as e:
            logger.error(f"Error fetching channel videos: {e}")
            return []
    
    def download_audio(self, video_info: VideoInfo) -> Optional[Path]:
        """
        Download and extract audio from a YouTube video
        
        Args:
            video_info: VideoInfo object containing video details
            
        Returns:
            Path to downloaded audio file or None if failed
        """
        try:
            logger.info(f"Downloading audio for: {video_info.title}")
            
            # Check if audio already exists
            audio_path = self.audio_dir / f"{video_info.video_id}.mp3"
            if audio_path.exists():
                logger.info(f"Audio already exists: {audio_path}")
                return audio_path
            
            # Download using yt-dlp
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([str(video_info.url)])
            
            # Verify the file was created
            if audio_path.exists():
                logger.info(f"Successfully downloaded audio: {audio_path}")
                return audio_path
            else:
                logger.error(f"Audio file not found after download: {audio_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading audio for {video_info.video_id}: {e}")
            return None
    
    def convert_to_wav(self, audio_path: Path) -> Optional[Path]:
        """
        Convert audio file to WAV format for better transcription compatibility
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Path to WAV file or None if failed
        """
        try:
            wav_path = audio_path.with_suffix('.wav')
            
            if wav_path.exists():
                logger.info(f"WAV file already exists: {wav_path}")
                return wav_path
            
            logger.info(f"Converting {audio_path} to WAV format")
            
            # Load and convert audio
            audio = AudioSegment.from_file(str(audio_path))
            audio.export(str(wav_path), format="wav")
            
            logger.info(f"Successfully converted to WAV: {wav_path}")
            return wav_path
            
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {e}")
            return None
    
    def process_channel(self, channel_url: str, max_videos: Optional[int] = None) -> List[tuple[VideoInfo, Path]]:
        """
        Complete pipeline: discover videos and download audio
        
        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to process
            
        Returns:
            List of tuples (VideoInfo, audio_path)
        """
        videos = self.get_channel_videos(channel_url, max_videos)
        results = []
        
        for video_info in videos:
            audio_path = self.download_audio(video_info)
            if audio_path:
                # Convert to WAV for better transcription compatibility
                wav_path = self.convert_to_wav(audio_path)
                if wav_path:
                    results.append((video_info, wav_path))
                    
        logger.info(f"Successfully processed {len(results)} videos")
        return results