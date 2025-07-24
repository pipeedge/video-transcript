import logging
from typing import List, Dict, Any, Optional
import meilisearch
from datetime import datetime

from ..config.settings import MEILISEARCH_URL, MEILISEARCH_MASTER_KEY
from ..models.podcast import Episode, Insight, CleanedSegment

logger = logging.getLogger(__name__)


class SearchService:
    """Handles search indexing and retrieval using MeiliSearch"""
    
    def __init__(self):
        self.client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_MASTER_KEY)
        
        # Index names
        self.insights_index_name = "insights"
        self.segments_index_name = "segments"
        self.episodes_index_name = "episodes"
        
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Set up MeiliSearch indexes with proper configuration"""
        try:
            # Insights index
            insights_index = self.client.index(self.insights_index_name)
            insights_index.update_searchable_attributes([
                'title', 'content', 'category', 'tags', 'quote'
            ])
            insights_index.update_filterable_attributes([
                'category', 'video_id', 'tags', 'start_time', 'end_time'
            ])
            insights_index.update_sortable_attributes(['start_time', 'confidence'])
            
            # Segments index
            segments_index = self.client.index(self.segments_index_name)
            segments_index.update_searchable_attributes([
                'title', 'cleaned_text', 'speaker'
            ])
            segments_index.update_filterable_attributes([
                'video_id', 'speaker', 'start_time', 'end_time'
            ])
            segments_index.update_sortable_attributes(['start_time'])
            
            # Episodes index
            episodes_index = self.client.index(self.episodes_index_name)
            episodes_index.update_searchable_attributes([
                'title', 'description'
            ])
            episodes_index.update_filterable_attributes([
                'video_id', 'processing_status', 'publish_date'
            ])
            episodes_index.update_sortable_attributes(['publish_date', 'duration'])
            
            logger.info("MeiliSearch indexes configured successfully")
            
        except Exception as e:
            logger.error(f"Error setting up MeiliSearch indexes: {e}")
            raise
    
    def index_episode(self, episode: Episode):
        """Index a complete episode with all its data"""
        try:
            # Index episode metadata
            self._index_episode_metadata(episode)
            
            # Index segments
            self._index_segments(episode.cleaned_segments, episode.video_info.video_id)
            
            # Index insights
            self._index_insights(episode.insights)
            
            logger.info(f"Successfully indexed episode: {episode.video_info.title}")
            
        except Exception as e:
            logger.error(f"Error indexing episode: {e}")
            raise
    
    def _index_episode_metadata(self, episode: Episode):
        """Index episode metadata"""
        episode_doc = {
            'id': episode.video_info.video_id,
            'video_id': episode.video_info.video_id,
            'title': episode.video_info.title,
            'description': episode.video_info.description,
            'url': str(episode.video_info.url),
            'duration': episode.video_info.duration,
            'publish_date': episode.video_info.publish_date.isoformat() if episode.video_info.publish_date else None,
            'thumbnail_url': episode.video_info.thumbnail_url,
            'processing_status': episode.processing_status,
            'insights_count': len(episode.insights),
            'segments_count': len(episode.cleaned_segments),
            'created_at': episode.created_at.isoformat(),
            'updated_at': episode.updated_at.isoformat()
        }
        
        episodes_index = self.client.index(self.episodes_index_name)
        episodes_index.add_documents([episode_doc])
    
    def _index_segments(self, segments: List[CleanedSegment], video_id: str):
        """Index transcript segments"""
        segment_docs = []
        
        for i, segment in enumerate(segments):
            doc = {
                'id': f"{video_id}_{i}",
                'video_id': video_id,
                'title': segment.title,
                'cleaned_text': segment.cleaned_text,
                'original_text': segment.original_text,
                'speaker': segment.speaker,
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'duration': segment.end_time - segment.start_time
            }
            segment_docs.append(doc)
        
        if segment_docs:
            segments_index = self.client.index(self.segments_index_name)
            segments_index.add_documents(segment_docs)
    
    def _index_insights(self, insights: List[Insight]):
        """Index extracted insights"""
        insight_docs = []
        
        for i, insight in enumerate(insights):
            doc = {
                'id': f"{insight.video_id}_{insight.category}_{i}",
                'video_id': insight.video_id,
                'category': insight.category,
                'title': insight.title,
                'content': insight.content,
                'quote': insight.quote,
                'start_time': insight.start_time,
                'end_time': insight.end_time,
                'confidence': insight.confidence,
                'tags': insight.tags or []
            }
            insight_docs.append(doc)
        
        if insight_docs:
            insights_index = self.client.index(self.insights_index_name)
            insights_index.add_documents(insight_docs)
    
    def search_insights(self, 
                       query: str, 
                       category: Optional[str] = None,
                       video_id: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       limit: int = 20) -> Dict[str, Any]:
        """
        Search for insights
        
        Args:
            query: Search query
            category: Filter by category
            video_id: Filter by video ID
            tags: Filter by tags
            limit: Maximum number of results
            
        Returns:
            Search results from MeiliSearch
        """
        try:
            insights_index = self.client.index(self.insights_index_name)
            
            # Build filter
            filters = []
            if category:
                filters.append(f'category = "{category}"')
            if video_id:
                filters.append(f'video_id = "{video_id}"')
            if tags:
                tag_filters = [f'tags = "{tag}"' for tag in tags]
                filters.append(f'({" OR ".join(tag_filters)})')
            
            filter_str = " AND ".join(filters) if filters else None
            
            # Perform search
            results = insights_index.search(
                query,
                {
                    'limit': limit,
                    'filter': filter_str,
                    'attributesToHighlight': ['title', 'content'],
                    'highlightPreTag': '<mark>',
                    'highlightPostTag': '</mark>'
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching insights: {e}")
            return {'hits': [], 'estimatedTotalHits': 0}
    
    def search_segments(self, 
                       query: str,
                       video_id: Optional[str] = None,
                       speaker: Optional[str] = None,
                       limit: int = 20) -> Dict[str, Any]:
        """Search for transcript segments"""
        try:
            segments_index = self.client.index(self.segments_index_name)
            
            # Build filter
            filters = []
            if video_id:
                filters.append(f'video_id = "{video_id}"')
            if speaker:
                filters.append(f'speaker = "{speaker}"')
            
            filter_str = " AND ".join(filters) if filters else None
            
            # Perform search
            results = segments_index.search(
                query,
                {
                    'limit': limit,
                    'filter': filter_str,
                    'attributesToHighlight': ['title', 'cleaned_text'],
                    'highlightPreTag': '<mark>',
                    'highlightPostTag': '</mark>',
                    'sort': ['start_time:asc']
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching segments: {e}")
            return {'hits': [], 'estimatedTotalHits': 0}
    
    def search_episodes(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for episodes"""
        try:
            episodes_index = self.client.index(self.episodes_index_name)
            
            results = episodes_index.search(
                query,
                {
                    'limit': limit,
                    'attributesToHighlight': ['title', 'description'],
                    'highlightPreTag': '<mark>',
                    'highlightPostTag': '</mark>',
                    'sort': ['publish_date:desc']
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching episodes: {e}")
            return {'hits': [], 'estimatedTotalHits': 0}
    
    def get_insight_categories(self) -> List[str]:
        """Get all available insight categories"""
        try:
            insights_index = self.client.index(self.insights_index_name)
            
            # Get facet distribution for categories
            results = insights_index.search(
                "",
                {
                    'limit': 0,
                    'facets': ['category']
                }
            )
            
            categories = list(results.get('facetDistribution', {}).get('category', {}).keys())
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search index statistics"""
        try:
            insights_index = self.client.index(self.insights_index_name)
            segments_index = self.client.index(self.segments_index_name)
            episodes_index = self.client.index(self.episodes_index_name)
            
            stats = {
                'insights_count': insights_index.get_stats()['numberOfDocuments'],
                'segments_count': segments_index.get_stats()['numberOfDocuments'],
                'episodes_count': episodes_index.get_stats()['numberOfDocuments']
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}