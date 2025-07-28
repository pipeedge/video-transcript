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
    
    def get_channel_videos(self, url: str, max_videos: Optional[int] = None) -> List[VideoInfo]:
        """
        Get list of videos from a YouTube channel or single video URL
        
        Args:
            url: YouTube channel URL or individual video URL
            max_videos: Maximum number of videos to fetch (None for all)
            
        Returns:
            List of VideoInfo objects
        """
        try:
            logger.info(f"Processing URL: {url}")
            
            # Check if it's a single video URL
            if 'watch?v=' in url or 'youtu.be/' in url:
                logger.info("Detected single video URL")
                return self._process_single_video(url)
            
            # Otherwise treat as channel URL
            logger.info("Treating as channel URL")
            
            # Try different URL formats
            channel_urls = self._get_channel_url_variants(url)
            
            for channel_url in channel_urls:
                try:
                    logger.info(f"Trying channel URL format: {channel_url}")
                    return self._process_channel_with_ytdlp(channel_url, max_videos)
                except Exception as e:
                    logger.warning(f"Failed with URL {channel_url}: {str(e)[:100]}...")
                    continue
            
            # If all formats fail
            raise Exception("All channel URL formats failed")
            
        except Exception as e:
            logger.error(f"Error processing URL: {e}")
            return []
    
    def _get_channel_url_variants(self, url: str) -> List[str]:
        """Generate different channel URL formats to try"""
        variants = [url]  # Start with original URL
        
        # Extract channel handle/name/ID from different formats
        if '@' in url:
            # Format: https://www.youtube.com/@ChannelName
            handle = url.split('@')[-1].split('/')[0].split('?')[0]
            variants.extend([
                f"https://www.youtube.com/@{handle}",
                f"https://www.youtube.com/@{handle}/videos",
                f"https://www.youtube.com/c/{handle}",
                f"https://www.youtube.com/c/{handle}/videos",
                f"https://www.youtube.com/user/{handle}",
                f"https://www.youtube.com/user/{handle}/videos",
            ])
        elif '/c/' in url:
            # Format: https://www.youtube.com/c/ChannelName
            channel_name = url.split('/c/')[-1].split('/')[0].split('?')[0]
            variants.extend([
                f"https://www.youtube.com/c/{channel_name}",
                f"https://www.youtube.com/c/{channel_name}/videos",
                f"https://www.youtube.com/@{channel_name}",
                f"https://www.youtube.com/user/{channel_name}",
            ])
        elif '/channel/' in url:
            # Format: https://www.youtube.com/channel/UCxxxxx
            channel_id = url.split('/channel/')[-1].split('/')[0].split('?')[0]
            variants.extend([
                f"https://www.youtube.com/channel/{channel_id}",
                f"https://www.youtube.com/channel/{channel_id}/videos",
            ])
        elif '/user/' in url:
            # Format: https://www.youtube.com/user/UserName
            user_name = url.split('/user/')[-1].split('/')[0].split('?')[0]
            variants.extend([
                f"https://www.youtube.com/user/{user_name}",
                f"https://www.youtube.com/user/{user_name}/videos",
                f"https://www.youtube.com/c/{user_name}",
                f"https://www.youtube.com/@{user_name}",
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)
        
        return unique_variants
    
    def _process_single_video(self, video_url: str) -> List[VideoInfo]:
        """Process a single video URL with anti-bot measures"""
        
        # Web client configuration for terminal/server environments
        ydl_opts = {
            'quiet': True,
            'retries': 3,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],  # Use web client for terminal
                    'skip': ['hls', 'dash'],
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
            
            # Check if video info was successfully extracted
            if not info:
                logger.error(f"Video is unavailable or private: {video_url}")
                return []
                
            video_info = VideoInfo(
                video_id=info['id'],
                title=info.get('title', ''),
                description=info.get('description', ''),
                url=video_url,
                duration=info.get('duration'),
                publish_date=datetime.fromtimestamp(info.get('timestamp', 0)) if info.get('timestamp') else None,
                thumbnail_url=info.get('thumbnail')
            )
            
            logger.info(f"Successfully processed single video: {video_info.title}")
            return [video_info]
            
        except Exception as e:
            logger.error(f"Error processing single video {video_url}: {e}")
            return []
    
    def _process_channel_with_ytdlp(self, channel_url: str, max_videos: Optional[int] = None) -> List[VideoInfo]:
        """Process a channel URL using yt-dlp with multiple anti-bot strategies"""
        
        # Terminal-optimized configurations (prioritize web client)
        configs = [
            # Strategy 1: Web client (best for terminal/server)
            {
                'name': 'Web client',
                'opts': {
                    'quiet': True,
                    'extract_flat': True,
                    'ignoreerrors': True,
                    'retries': 2,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    },
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['web'],
                            'skip': ['hls', 'dash'],
                        }
                    }
                }
            },
            # Strategy 2: Minimal config
            {
                'name': 'Minimal config',
                'opts': {
                    'quiet': True,
                    'extract_flat': True,
                    'ignoreerrors': True,
                    'retries': 1,
                    'extractor_args': {
                        'youtube': {
                            'skip': ['hls', 'dash'],
                        }
                    }
                }
            }
        ]
        
        # Try each configuration
        for config in configs:
            try:
                logger.info(f"Trying {config['name']} strategy for channel extraction")
                return self._try_ytdlp_config(channel_url, config['opts'], max_videos)
            except Exception as e:
                logger.warning(f"{config['name']} failed: {str(e)[:100]}...")
                continue
        
        # If all strategies fail, raise the last error
        raise Exception("All anti-bot strategies failed")
    
    def _try_ytdlp_config(self, channel_url: str, ydl_opts: dict, max_videos: Optional[int] = None) -> List[VideoInfo]:
        """Try a specific yt-dlp configuration"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Extracting channel info with yt-dlp: {channel_url}")
            channel_info = ydl.extract_info(channel_url, download=False)
            
            if not channel_info or 'entries' not in channel_info:
                logger.error("No entries found in channel")
                return []
            
            videos = []
            entries = channel_info['entries']
            
            # Limit the number of videos to process
            if max_videos:
                entries = entries[:max_videos]
            
            logger.info(f"Found {len(entries)} videos to process")
            
            for i, entry in enumerate(entries):
                if not entry:  # Skip None entries
                    continue
                    
                try:
                    # Get full video info
                    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                    
                    # Use the same configuration for individual video extraction
                    with yt_dlp.YoutubeDL(ydl_opts) as video_ydl:
                        video_info_raw = video_ydl.extract_info(video_url, download=False)
                    
                    # Check if video info was successfully extracted
                    if not video_info_raw:
                        logger.warning(f"Video {i+1} ({entry.get('id', 'unknown')}) is unavailable or private - skipping")
                        continue
                    
                    video_info = VideoInfo(
                        video_id=video_info_raw['id'],
                        title=video_info_raw.get('title', entry.get('title', '')),
                        description=video_info_raw.get('description', ''),
                        url=video_url,
                        duration=video_info_raw.get('duration'),
                        publish_date=datetime.fromtimestamp(video_info_raw.get('timestamp', 0)) if video_info_raw.get('timestamp') else None,
                        thumbnail_url=video_info_raw.get('thumbnail')
                    )
                    
                    videos.append(video_info)
                    logger.info(f"Processed video {i+1}/{len(entries)}: {video_info.title}")
                    
                except Exception as e:
                    logger.warning(f"Error processing video {i+1}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(videos)} videos from channel")
            return videos
    
    def _process_channel_with_pytube(self, channel_url: str, max_videos: Optional[int] = None) -> List[VideoInfo]:
        """Fallback method using pytube"""
        try:
            logger.info("Attempting fallback with pytube...")
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
                    
            logger.info(f"Pytube fallback found {len(videos)} videos")
            return videos
            
        except Exception as e:
            logger.error(f"Pytube fallback also failed: {e}")
            return []
    
    def download_audio(self, video_info: VideoInfo) -> Optional[Path]:
        """
        Download and extract audio from a YouTube video with PO token fallback
        
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
            
            # Enhanced web client strategy with fallbacks
            download_strategy = {
                'name': 'Web client',
                'opts': {
                    'format': 'bestaudio[ext=m4a]/bestaudio/best[height<=480]',
                    'extractaudio': True,
                    'audioformat': 'mp3',
                    'audioquality': '192K',
                    'outtmpl': str(self.audio_dir / '%(id)s.%(ext)s'),
                    'quiet': False,  # Enable more verbose output for debugging
                    'no_warnings': False,
                    'retries': 5,
                    'fragment_retries': 5,
                    'ignoreerrors': False,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-us,en;q=0.5',
                        'Sec-Fetch-Mode': 'navigate',
                    },
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['web', 'mweb'],
                            'skip': ['hls'],
                        }
                    }
                }
            }
            
            # Try web client download
            try:
                logger.info(f"Trying {download_strategy['name']} for audio download")
                
                with yt_dlp.YoutubeDL(download_strategy['opts']) as ydl:
                    ydl.download([str(video_info.url)])
                
                # Check for various possible output formats
                possible_paths = [
                    self.audio_dir / f"{video_info.video_id}.mp3",
                    self.audio_dir / f"{video_info.video_id}.m4a",
                    self.audio_dir / f"{video_info.video_id}.mp4",
                    self.audio_dir / f"{video_info.video_id}.webm",
                    self.audio_dir / f"{video_info.video_id}.opus",
                ]
                
                for path in possible_paths:
                    if path.exists():
                        # Convert to mp3 if needed
                        if path.suffix != '.mp3':
                            mp3_path = path.with_suffix('.mp3')
                            logger.info(f"Converting {path} to MP3")
                            audio = AudioSegment.from_file(str(path))
                            audio.export(str(mp3_path), format="mp3", bitrate="192k")
                            path.unlink()  # Remove original file
                            path = mp3_path
                        
                        logger.info(f"Successfully downloaded audio with {download_strategy['name']}: {path}")
                        return path
                
                logger.warning(f"{download_strategy['name']} completed but no audio file found")
                
            except Exception as e:
                error_msg = str(e)
                if "Sign in to confirm you're not a bot" in error_msg:
                    logger.error(f"{download_strategy['name']} failed: Bot detection")
                elif "requires a PO token" in error_msg or "PO token" in error_msg:
                    logger.error(f"{download_strategy['name']} failed: PO token required")
                else:
                    logger.error(f"{download_strategy['name']} failed: {error_msg[:100]}")
            
            # If download fails, provide helpful message
            logger.error(f"Web client download failed for {video_info.video_id}")
            logger.info("This video may require a PO token or different approach. Try using a different video.")
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