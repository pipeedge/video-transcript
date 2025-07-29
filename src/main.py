import logging
import asyncio
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from .data_ingestion.youtube_downloader import YouTubeDownloader
from .data_ingestion.transcription import TranscriptionService
from .data_ingestion.direct_transcript_extractor import DirectTranscriptExtractor
from .config.settings import USE_WHISPER, WHISPER_MODEL, DEMO_MODE, MAX_DEMO_VIDEOS
from .llm_processing.llm_service import LLMService
from .llm_processing.text_processor import TextProcessor
from .search.search_service import SearchService
from .models.podcast import Episode, VideoInfo
from .config.settings import BASE_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'podcast_analyzer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class PodcastAnalyzer:
    """Main orchestrator for the podcast analysis pipeline"""
    
    def __init__(self):
        self.downloader = YouTubeDownloader()
        
        # Initialize transcription service (optional for Python 3.13)
        try:
            self.transcriber = TranscriptionService(prefer_whisper=USE_WHISPER, whisper_model=WHISPER_MODEL)
            self.transcription_available = True
        except ImportError as e:
            logger.warning(f"Transcription service not available: {e}")
            self.transcriber = None
            self.transcription_available = False
        
        # Direct transcript extractor (no audio download required)
        self.direct_extractor = DirectTranscriptExtractor()
        self.llm_service = LLMService()
        self.text_processor = TextProcessor(self.llm_service)
        self.search_service = SearchService()
    
    async def process_channel(self, channel_url: str, max_videos: Optional[int] = None) -> List[Episode]:
        """
        Complete pipeline: process an entire YouTube channel
        
        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to process (None for all)
            
        Returns:
            List of processed Episode objects
        """
        logger.info(f"Starting channel processing: {channel_url}")
        
        try:
            # Apply demo mode limits
            if DEMO_MODE and (max_videos is None or max_videos > MAX_DEMO_VIDEOS):
                max_videos = MAX_DEMO_VIDEOS
                logger.info(f"Demo mode active: limiting to {max_videos} videos")
            
            # Step 1: Discover and download videos
            video_audio_pairs = self.downloader.process_channel(channel_url, max_videos)
            logger.info(f"Downloaded {len(video_audio_pairs)} videos")
            
            episodes = []
            
            for video_info, audio_path in video_audio_pairs:
                try:
                    episode = await self.process_single_video(video_info, audio_path)
                    if episode:
                        episodes.append(episode)
                        
                        # Index the episode for search
                        self.search_service.index_episode(episode)
                        logger.info(f"Indexed episode: {episode.video_info.title}")
                        
                except Exception as e:
                    logger.error(f"Error processing video {video_info.video_id}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(episodes)} episodes")
            return episodes
            
        except Exception as e:
            logger.error(f"Error processing channel: {e}")
            return []
    
    async def process_channel_direct_transcripts(self, channel_url: str, max_videos: Optional[int] = None) -> List[Episode]:
        """
        Process channel using direct transcript extraction (no audio download required)
        
        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to process (None for all)
            
        Returns:
            List of processed Episode objects
        """
        logger.info(f"Starting direct transcript processing for channel: {channel_url}")
        
        try:
            # Apply demo mode limits
            if DEMO_MODE and (max_videos is None or max_videos > MAX_DEMO_VIDEOS):
                max_videos = MAX_DEMO_VIDEOS
                logger.info(f"Demo mode active: limiting to {max_videos} videos")
            
            # Step 1: Extract transcripts directly from videos
            video_transcript_pairs = self.direct_extractor.process_channel_transcripts(channel_url, max_videos)
            logger.info(f"Extracted transcripts from {len(video_transcript_pairs)} videos")
            
            episodes = []
            
            for video_info, transcript_segments in video_transcript_pairs:
                try:
                    episode = await self.process_single_video_with_transcript(video_info, transcript_segments)
                    if episode:
                        episodes.append(episode)
                        
                        # Index the episode for search
                        self.search_service.index_episode(episode)
                        logger.info(f"Indexed episode: {episode.video_info.title}")
                        
                except Exception as e:
                    logger.error(f"Error processing video {video_info.video_id}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(episodes)} episodes using direct transcripts")
            return episodes
            
        except Exception as e:
            logger.error(f"Error processing channel with direct transcripts: {e}")
            return []
    
    async def process_single_video(self, video_info: VideoInfo, audio_path: Path) -> Optional[Episode]:
        """
        Process a single video through the complete pipeline
        
        Args:
            video_info: Video information
            audio_path: Path to the audio file
            
        Returns:
            Processed Episode object or None if failed
        """
        logger.info(f"Processing video: {video_info.title}")
        
        try:
            # Step 2: Transcribe audio (if transcription service available)
            if not self.transcription_available:
                logger.error("Transcription service not available - use direct transcript extraction instead")
                return None
                
            logger.info("Starting transcription...")
            raw_transcript = self.transcriber.transcribe_audio(audio_path, video_info.video_id)
            
            if not raw_transcript:
                logger.error("Transcription failed")
                return None
            
            logger.info(f"Transcription complete: {len(raw_transcript)} segments")
            
            # Step 3: Process transcript with LLM
            logger.info("Starting LLM processing...")
            
            # Clean segments and generate titles
            cleaned_segments = self.text_processor.process_transcript_segments(raw_transcript)
            logger.info(f"Cleaned {len(cleaned_segments)} segments")
            
            # Extract insights
            insights = self.text_processor.extract_insights_from_episode(
                cleaned_segments, video_info.video_id
            )
            logger.info(f"Extracted {len(insights)} insights")
            
            # Create episode object
            episode = Episode(
                video_info=video_info,
                raw_transcript=raw_transcript,
                cleaned_segments=cleaned_segments,
                insights=insights,
                products=[],  # Will be populated by external product lookup
                processing_status="completed",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            logger.info(f"Successfully processed episode: {video_info.title}")
            return episode
            
        except Exception as e:
            logger.error(f"Error processing video {video_info.video_id}: {e}")
            return None
    
    async def process_single_video_with_transcript(self, video_info: VideoInfo, transcript_segments: List) -> Optional[Episode]:
        """
        Process a single video with existing transcript segments (no audio transcription needed)
        
        Args:
            video_info: Video information
            transcript_segments: Pre-extracted transcript segments
            
        Returns:
            Processed Episode object or None if failed
        """
        logger.info(f"Processing video with existing transcript: {video_info.title}")
        
        try:
            # Convert transcript segments to the expected format if needed
            from .models.podcast import TranscriptSegment
            
            # Ensure we have proper TranscriptSegment objects
            if transcript_segments and not isinstance(transcript_segments[0], TranscriptSegment):
                logger.error("Invalid transcript segment format")
                return None
            
            logger.info(f"Using existing transcript: {len(transcript_segments)} segments")
            
            # Step 2: Process transcript with LLM (skip audio transcription)
            logger.info("Starting LLM processing...")
            
            # Clean segments and generate titles
            cleaned_segments = self.text_processor.process_transcript_segments(transcript_segments)
            logger.info(f"Cleaned {len(cleaned_segments)} segments")
            
            # Extract insights
            insights = self.text_processor.extract_insights_from_episode(
                cleaned_segments, video_info.video_id
            )
            logger.info(f"Extracted {len(insights)} insights")
            
            # Create episode object
            episode = Episode(
                video_info=video_info,
                raw_transcript=transcript_segments,
                cleaned_segments=cleaned_segments,
                insights=insights,
                products=[],  # Will be populated by external product lookup
                processing_status="completed",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            logger.info(f"Successfully processed episode with direct transcript: {video_info.title}")
            return episode
            
        except Exception as e:
            logger.error(f"Error processing video with transcript {video_info.video_id}: {e}")
            return None
    
    def search_insights(self, query: str, **filters) -> dict:
        """Search for insights"""
        return self.search_service.search_insights(query, **filters)
    
    def search_segments(self, query: str, **filters) -> dict:
        """Search for transcript segments"""
        return self.search_service.search_segments(query, **filters)
    
    def search_episodes(self, query: str, **filters) -> dict:
        """Search for episodes"""
        return self.search_service.search_episodes(query, **filters)
    
    def get_stats(self) -> dict:
        """Get processing and search statistics"""
        return self.search_service.get_stats()


async def main():
    """Example usage of the podcast analyzer"""
    analyzer = PodcastAnalyzer()
    
    # Example: Process My First Million podcast channel
    # Note: Replace with actual channel URL
    channel_url = "https://www.youtube.com/@MyFirstMillionPod"
    
    # Process first 5 videos as a test
    episodes = await analyzer.process_channel(channel_url, max_videos=5)
    
    print(f"\nProcessed {len(episodes)} episodes")
    
    # Example searches
    if episodes:
        print("\n=== Example Searches ===")
        
        # Search for business insights
        business_results = analyzer.search_insights("business model", category="Business Ideas")
        print(f"Found {len(business_results['hits'])} business insights")
        
        # Search for frameworks
        framework_results = analyzer.search_insights("framework", category="Frameworks")
        print(f"Found {len(framework_results['hits'])} frameworks")
        
        # Get stats
        stats = analyzer.get_stats()
        print(f"\nStats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())