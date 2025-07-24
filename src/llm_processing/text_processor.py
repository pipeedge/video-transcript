import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .llm_service import LLMService
from ..models.podcast import TranscriptSegment, CleanedSegment, Insight
from ..config.settings import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles all text processing tasks using LLM"""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        
        # Default insight categories - can be customized
        self.insight_categories = [
            "Business Ideas",
            "Mental Models", 
            "Frameworks",
            "Stories",
            "Products Mentioned",
            "Actionable Advice",
            "Quotes",
            "Numbers & Metrics"
        ]
    
    def process_transcript_segments(self, segments: List[TranscriptSegment]) -> List[CleanedSegment]:
        """
        Clean and format transcript segments
        
        Args:
            segments: List of raw transcript segments
            
        Returns:
            List of cleaned segments with titles
        """
        logger.info(f"Processing {len(segments)} transcript segments")
        cleaned_segments = []
        
        for i, segment in enumerate(segments):
            try:
                logger.info(f"Processing segment {i+1}/{len(segments)}")
                
                # Clean the text
                cleaned_text = self.llm.clean_transcript_text(segment.text)
                
                # Generate title
                title = self.llm.generate_segment_title(cleaned_text)
                
                cleaned_segment = CleanedSegment(
                    original_text=segment.text,
                    cleaned_text=cleaned_text,
                    title=title,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    speaker=segment.speaker
                )
                
                cleaned_segments.append(cleaned_segment)
                
            except Exception as e:
                logger.error(f"Error processing segment {i}: {e}")
                # Create a fallback cleaned segment
                fallback_segment = CleanedSegment(
                    original_text=segment.text,
                    cleaned_text=segment.text,  # Use original if cleaning fails
                    title=f"Segment {i+1}",  # Simple fallback title
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    speaker=segment.speaker
                )
                cleaned_segments.append(fallback_segment)
        
        logger.info(f"Successfully processed {len(cleaned_segments)} segments")
        return cleaned_segments
    
    def extract_insights_from_episode(self, cleaned_segments: List[CleanedSegment], video_id: str) -> List[Insight]:
        """
        Extract insights from cleaned transcript segments
        
        Args:
            cleaned_segments: List of cleaned transcript segments
            video_id: Video ID for reference
            
        Returns:
            List of extracted insights
        """
        logger.info(f"Extracting insights from {len(cleaned_segments)} segments")
        
        # Combine all cleaned text
        full_text = " ".join([segment.cleaned_text for segment in cleaned_segments])
        
        # Split into chunks for processing
        chunks = self.llm.chunk_text(full_text, CHUNK_SIZE, CHUNK_OVERLAP)
        logger.info(f"Split text into {len(chunks)} chunks for processing")
        
        all_insights = []
        
        # Process chunks in parallel for efficiency
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_chunk = {
                executor.submit(self._process_chunk, chunk, video_id): chunk 
                for chunk in chunks
            }
            
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    chunk_insights = future.result()
                    all_insights.extend(chunk_insights)
                    logger.info(f"Extracted {len(chunk_insights)} insights from chunk")
                except Exception as e:
                    logger.error(f"Error processing chunk: {e}")
        
        # Deduplicate insights
        deduplicated_insights = self._deduplicate_insights(all_insights)
        
        # Add timestamps to insights
        insights_with_timestamps = self._add_timestamps_to_insights(
            deduplicated_insights, cleaned_segments
        )
        
        logger.info(f"Extracted {len(insights_with_timestamps)} unique insights")
        return insights_with_timestamps
    
    def _process_chunk(self, chunk: str, video_id: str) -> List[Insight]:
        """Process a single chunk and extract insights"""
        try:
            insights_by_category = self.llm.extract_insights(chunk, self.insight_categories)
            
            insights = []
            for category, category_insights in insights_by_category.items():
                for insight_text in category_insights:
                    if insight_text.strip():  # Skip empty insights
                        insight = Insight(
                            category=category,
                            title=self._generate_insight_title(insight_text),
                            content=insight_text,
                            quote=insight_text if len(insight_text) < 200 else None,
                            video_id=video_id,
                            tags=self._extract_tags(insight_text)
                        )
                        insights.append(insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            return []
    
    def _generate_insight_title(self, insight_text: str) -> str:
        """Generate a short title for an insight"""
        try:
            # Use first sentence or first 50 characters as title
            first_sentence = insight_text.split('.')[0]
            if len(first_sentence) > 50:
                return first_sentence[:47] + "..."
            return first_sentence
        except:
            return insight_text[:50] + "..." if len(insight_text) > 50 else insight_text
    
    def _extract_tags(self, insight_text: str) -> List[str]:
        """Extract relevant tags from insight text"""
        # Simple keyword extraction - could be enhanced with NLP
        keywords = []
        
        # Common business/entrepreneurship keywords
        business_keywords = [
            "startup", "business", "revenue", "profit", "growth", "marketing", 
            "sales", "customer", "product", "market", "strategy", "investment",
            "funding", "scaling", "team", "leadership", "innovation", "technology"
        ]
        
        insight_lower = insight_text.lower()
        for keyword in business_keywords:
            if keyword in insight_lower:
                keywords.append(keyword.title())
        
        return keywords[:5]  # Limit to 5 tags
    
    def _deduplicate_insights(self, insights: List[Insight]) -> List[Insight]:
        """Remove duplicate insights based on content similarity"""
        if not insights:
            return []
        
        unique_insights = []
        seen_content = set()
        
        for insight in insights:
            # Simple deduplication based on first 100 characters
            content_key = insight.content[:100].lower().strip()
            
            if content_key not in seen_content:
                unique_insights.append(insight)
                seen_content.add(content_key)
        
        logger.info(f"Deduplicated {len(insights)} insights to {len(unique_insights)}")
        return unique_insights
    
    def _add_timestamps_to_insights(self, insights: List[Insight], segments: List[CleanedSegment]) -> List[Insight]:
        """Add timestamp information to insights by matching with segments"""
        for insight in insights:
            # Find the segment that most likely contains this insight
            best_match_segment = None
            best_match_score = 0
            
            for segment in segments:
                # Simple text matching to find relevant segment
                insight_words = set(insight.content.lower().split())
                segment_words = set(segment.cleaned_text.lower().split())
                
                # Calculate overlap score
                overlap = len(insight_words.intersection(segment_words))
                score = overlap / len(insight_words) if insight_words else 0
                
                if score > best_match_score:
                    best_match_score = score
                    best_match_segment = segment
            
            # Add timestamp if we found a good match (> 30% overlap)
            if best_match_segment and best_match_score > 0.3:
                insight.start_time = best_match_segment.start_time
                insight.end_time = best_match_segment.end_time
                insight.confidence = best_match_score
        
        return insights
    
    def get_insight_categories(self) -> List[str]:
        """Get list of insight categories"""
        return self.insight_categories.copy()
    
    def set_insight_categories(self, categories: List[str]):
        """Set custom insight categories"""
        self.insight_categories = categories
        logger.info(f"Updated insight categories: {categories}")