#!/usr/bin/env python3
"""
Image-to-Text Workflow Integration - Lite Version
A version that gracefully handles missing dependencies
"""

import os
import json
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import components, but handle failures gracefully
try:
    from image_ocr_processor import OCRManager
    HAS_OCR = True
except ImportError:
    logger.warning("OCR processor not available")
    HAS_OCR = False

try:
    from image_entity_extraction_system import ImageEntityExtractor
    HAS_IMAGE_ENTITY = True
except ImportError:
    logger.warning("Image entity extractor not available")
    HAS_IMAGE_ENTITY = False

try:
    from image_annotation_system import AnnotationManager
    HAS_ANNOTATION = True
except ImportError:
    logger.warning("Annotation manager not available")
    HAS_ANNOTATION = False

try:
    from intelligent_content_search import SemanticSearchEngine, UnifiedSearchEngine
    HAS_SEARCH = True
except ImportError:
    logger.warning("Search engines not available")
    HAS_SEARCH = False

# Import transcription components
try:
    from stt import transcribe_audio
    HAS_STT = True
except ImportError:
    logger.warning("Speech-to-text not available")
    HAS_STT = False

try:
    from ner_basic import extract_entities as extract_entities_basic
    HAS_NER_BASIC = True
except ImportError:
    logger.warning("Basic NER not available")
    HAS_NER_BASIC = False

try:
    from ner_advanced import extract_entities_gpt
    HAS_NER_ADVANCED = True
except ImportError:
    logger.warning("Advanced NER not available")
    HAS_NER_ADVANCED = False

@dataclass
class MediaContent:
    """Unified media content representation"""
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_type: str = ""  # 'audio', 'video', 'image', 'document'
    source_path: str = ""
    
    # Text content from different sources
    transcript_text: Optional[str] = None
    ocr_text: Optional[str] = None
    caption_text: Optional[str] = None
    annotation_text: Optional[str] = None
    
    # Extracted entities
    entities: Dict[str, List[str]] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[np.ndarray] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowResult:
    """Result of the integrated workflow"""
    content_id: str
    original_path: str
    content_type: str
    
    # Extracted text
    all_text: str
    text_sources: Dict[str, str]  # source -> text mapping
    
    # Entities and analysis
    entities: Dict[str, List[str]]
    keywords: List[str]
    summary: Optional[str] = None
    
    # Search and recommendations
    search_embedding: Optional[np.ndarray] = None
    similar_content: List[str] = field(default_factory=list)
    
    # Processing metadata
    processing_time: float = 0.0
    processing_steps: List[str] = field(default_factory=list)

class ImageTextIntegrationPipelineLite:
    """Lite version of the integration pipeline with graceful degradation"""
    
    def __init__(self):
        """Initialize the integration pipeline"""
        # Initialize available components
        self.ocr_processor = OCRManager() if HAS_OCR else None
        self.entity_extractor = ImageEntityExtractor() if HAS_IMAGE_ENTITY else None
        self.annotation_manager = AnnotationManager() if HAS_ANNOTATION else None
        
        # Text processors
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Search engines
        self.semantic_search = SemanticSearchEngine() if HAS_SEARCH else None
        self.unified_search = UnifiedSearchEngine() if HAS_SEARCH else None
        
        # Content storage
        self.media_contents: Dict[str, MediaContent] = {}
        
        # Log available components
        available = []
        if HAS_OCR: available.append("OCR")
        if HAS_IMAGE_ENTITY: available.append("ImageEntity")
        if HAS_ANNOTATION: available.append("Annotation")
        if HAS_SEARCH: available.append("Search")
        if HAS_STT: available.append("STT")
        if HAS_NER_BASIC: available.append("BasicNER")
        if HAS_NER_ADVANCED: available.append("AdvancedNER")
        
        logger.info(f"Image-Text Integration Pipeline Lite initialized with: {', '.join(available)}")
    
    def process_media_file(self, file_path: str, content_type: Optional[str] = None) -> WorkflowResult:
        """Process any media file through the integrated pipeline"""
        start_time = datetime.now()
        processing_steps = []
        
        # Detect content type if not provided
        if not content_type:
            content_type = self._detect_content_type(file_path)
        
        # Create media content object
        media_content = MediaContent(
            content_type=content_type,
            source_path=file_path
        )
        
        # Process based on content type
        if content_type in ['image', 'document']:
            # Process image/document
            self._process_image_content(media_content, processing_steps)
        elif content_type in ['audio', 'video']:
            # Process audio/video
            self._process_audio_content(media_content, processing_steps)
        
        # Extract entities from all text
        all_text = self._combine_text_sources(media_content)
        if all_text:
            media_content.entities = self._extract_entities(all_text)
            processing_steps.append("entity_extraction")
        
        # Generate embeddings for search
        if all_text:
            media_content.embeddings = self.embedding_model.encode(all_text)
            processing_steps.append("embedding_generation")
        
        # Store content
        self.media_contents[media_content.content_id] = media_content
        
        # Add to search engines
        if all_text and self.semantic_search:
            self._index_content(media_content)
            processing_steps.append("search_indexing")
        
        # Find similar content
        similar_content = self._find_similar_content(media_content) if self.semantic_search else []
        
        # Create workflow result
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = WorkflowResult(
            content_id=media_content.content_id,
            original_path=file_path,
            content_type=content_type,
            all_text=all_text,
            text_sources=self._get_text_sources(media_content),
            entities=media_content.entities,
            keywords=self._extract_keywords(all_text),
            summary=self._generate_summary(all_text),
            search_embedding=media_content.embeddings,
            similar_content=similar_content,
            processing_time=processing_time,
            processing_steps=processing_steps
        )
        
        logger.info(f"Processed {content_type} file in {processing_time:.2f}s")
        return result
    
    def _detect_content_type(self, file_path: str) -> str:
        """Detect content type from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
        document_exts = {'.pdf', '.docx', '.doc', '.txt'}
        audio_exts = {'.mp3', '.wav', '.m4a', '.flac', '.aac'}
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        
        if ext in image_exts:
            return 'image'
        elif ext in document_exts:
            return 'document'
        elif ext in audio_exts:
            return 'audio'
        elif ext in video_exts:
            return 'video'
        else:
            return 'unknown'
    
    def _process_image_content(self, media_content: MediaContent, steps: List[str]):
        """Process image content through various analyzers"""
        file_path = media_content.source_path
        
        try:
            # OCR processing
            if self.ocr_processor and HAS_OCR:
                try:
                    ocr_result = self.ocr_processor.process_file(file_path)
                    if hasattr(ocr_result, 'text') and ocr_result.text:
                        media_content.ocr_text = ocr_result.text
                        media_content.metadata['ocr_confidence'] = ocr_result.confidence
                        steps.append("ocr_extraction")
                except Exception as e:
                    logger.warning(f"OCR processing failed: {e}")
            
            # Entity extraction from image
            if self.entity_extractor and HAS_IMAGE_ENTITY:
                try:
                    visual_entities = self.entity_extractor.extract_entities(file_path)
                    if visual_entities:
                        # Convert visual entities to text descriptions
                        captions = []
                        for entity in visual_entities:
                            if hasattr(entity, 'caption') and entity.caption:
                                captions.append(entity.caption)
                        if captions:
                            media_content.caption_text = " ".join(captions)
                            media_content.metadata['visual_entities'] = len(visual_entities)
                            steps.append("visual_entity_extraction")
                except Exception as e:
                    logger.warning(f"Visual entity extraction failed: {e}")
            
        except Exception as e:
            logger.error(f"Error processing image content: {e}")
    
    def _process_audio_content(self, media_content: MediaContent, steps: List[str]):
        """Process audio/video content through transcription"""
        file_path = media_content.source_path
        
        try:
            # Transcribe audio
            if HAS_STT:
                transcript = transcribe_audio(file_path)
                if transcript:
                    media_content.transcript_text = transcript
                    media_content.metadata['transcript_length'] = len(transcript.split())
                    steps.append("audio_transcription")
        except Exception as e:
            logger.error(f"Error processing audio content: {e}")
    
    def _combine_text_sources(self, media_content: MediaContent) -> str:
        """Combine text from all sources"""
        text_parts = []
        
        if media_content.transcript_text:
            text_parts.append(media_content.transcript_text)
        if media_content.ocr_text:
            text_parts.append(media_content.ocr_text)
        if media_content.caption_text:
            text_parts.append(media_content.caption_text)
        if media_content.annotation_text:
            text_parts.append(media_content.annotation_text)
        
        return " ".join(text_parts)
    
    def _get_text_sources(self, media_content: MediaContent) -> Dict[str, str]:
        """Get all text sources as a dictionary"""
        sources = {}
        
        if media_content.transcript_text:
            sources['transcript'] = media_content.transcript_text
        if media_content.ocr_text:
            sources['ocr'] = media_content.ocr_text
        if media_content.caption_text:
            sources['caption'] = media_content.caption_text
        if media_content.annotation_text:
            sources['annotation'] = media_content.annotation_text
        
        return sources
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text using available methods"""
        entities = {}
        
        # Basic entity extraction
        if HAS_NER_BASIC:
            try:
                basic_entities = extract_entities_basic(text)
                entities.update(basic_entities)
            except Exception as e:
                logger.warning(f"Basic NER failed: {e}")
        
        # Advanced entity extraction (if API available)
        if HAS_NER_ADVANCED:
            try:
                advanced_result = extract_entities_gpt(text)
                if advanced_result and 'entities' in advanced_result:
                    # Merge entities
                    for entity_type, values in advanced_result['entities'].items():
                        if entity_type in entities:
                            entities[entity_type].extend(values)
                            entities[entity_type] = list(set(entities[entity_type]))
                        else:
                            entities[entity_type] = values
            except Exception as e:
                logger.warning(f"Advanced NER failed: {e}")
        
        # Fallback: simple pattern matching if no NER available
        if not entities:
            entities = self._extract_entities_fallback(text)
        
        return entities
    
    def _extract_entities_fallback(self, text: str) -> Dict[str, List[str]]:
        """Simple fallback entity extraction"""
        import re
        
        entities = {
            'MONEY': [],
            'PERCENT': [],
            'DATE': []
        }
        
        # Extract money amounts
        money_pattern = r'\$[\d,]+\.?\d*[MBK]?'
        entities['MONEY'] = re.findall(money_pattern, text)
        
        # Extract percentages
        percent_pattern = r'\d+\.?\d*%'
        entities['PERCENT'] = re.findall(percent_pattern, text)
        
        # Extract years
        year_pattern = r'\b(19|20)\d{2}\b'
        entities['DATE'] = re.findall(year_pattern, text)
        
        return {k: v for k, v in entities.items() if v}
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction based on entity counts
        entities = self._extract_entities(text)
        
        keywords = []
        for entity_list in entities.values():
            keywords.extend(entity_list)
        
        # Count frequency and return top keywords
        from collections import Counter
        keyword_counts = Counter(keywords)
        
        return [kw for kw, _ in keyword_counts.most_common(max_keywords)]
    
    def _generate_summary(self, text: str, max_length: int = 200) -> Optional[str]:
        """Generate a summary of the text"""
        if not text or len(text.split()) < 50:
            return None
        
        # Simple extractive summary - take first sentences
        sentences = text.split('. ')
        summary_sentences = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            if current_length + sentence_length <= max_length:
                summary_sentences.append(sentence)
                current_length += sentence_length
            else:
                break
        
        return '. '.join(summary_sentences) + '.'
    
    def _index_content(self, media_content: MediaContent):
        """Index content in search engines"""
        if not self.semantic_search:
            return
            
        # Add to semantic search
        all_text = self._combine_text_sources(media_content)
        
        self.semantic_search.add_document(
            doc_id=media_content.content_id,
            text=all_text,
            metadata={
                'content_type': media_content.content_type,
                'source_path': media_content.source_path,
                'created_at': media_content.created_at.isoformat()
            }
        )
    
    def _find_similar_content(self, media_content: MediaContent, top_k: int = 5) -> List[str]:
        """Find similar content based on embeddings"""
        if not media_content.embeddings or not self.semantic_search:
            return []
        
        # Search for similar content
        results = self.semantic_search.search(
            query_embedding=media_content.embeddings,
            top_k=top_k + 1  # +1 to exclude self
        )
        
        # Filter out self and return content IDs
        similar_ids = []
        for result in results:
            if result['id'] != media_content.content_id:
                similar_ids.append(result['id'])
        
        return similar_ids[:top_k]
    
    def search_across_media(self, query: str, media_types: Optional[List[str]] = None, 
                           top_k: int = 10) -> List[Dict[str, Any]]:
        """Search across all media types"""
        if not self.semantic_search:
            # Fallback to simple text search
            return self._search_fallback(query, media_types, top_k)
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Search with filters
        results = self.semantic_search.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters={'content_type': media_types} if media_types else None
        )
        
        # Enhance results with full content info
        enhanced_results = []
        for result in results:
            content_id = result['id']
            if content_id in self.media_contents:
                content = self.media_contents[content_id]
                enhanced_results.append({
                    'content_id': content_id,
                    'content_type': content.content_type,
                    'source_path': content.source_path,
                    'score': result['score'],
                    'text_preview': self._combine_text_sources(content)[:200] + '...',
                    'entities': content.entities,
                    'created_at': content.created_at.isoformat()
                })
        
        return enhanced_results
    
    def _search_fallback(self, query: str, media_types: Optional[List[str]], top_k: int) -> List[Dict[str, Any]]:
        """Simple text search fallback"""
        results = []
        query_lower = query.lower()
        
        for content_id, content in self.media_contents.items():
            # Filter by media type
            if media_types and content.content_type not in media_types:
                continue
            
            # Check if query appears in text
            all_text = self._combine_text_sources(content).lower()
            if query_lower in all_text:
                results.append({
                    'content_id': content_id,
                    'content_type': content.content_type,
                    'source_path': content.source_path,
                    'score': 1.0,  # Simple binary score
                    'text_preview': self._combine_text_sources(content)[:200] + '...',
                    'entities': content.entities,
                    'created_at': content.created_at.isoformat()
                })
        
        return results[:top_k]
    
    def get_content_analytics(self) -> Dict[str, Any]:
        """Get analytics across all processed content"""
        total_content = len(self.media_contents)
        
        # Count by type
        type_counts = {}
        total_entities = 0
        text_sources = {
            'transcript': 0,
            'ocr': 0,
            'caption': 0,
            'annotation': 0
        }
        
        for content in self.media_contents.values():
            # Count types
            content_type = content.content_type
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
            
            # Count entities
            for entity_list in content.entities.values():
                total_entities += len(entity_list)
            
            # Count text sources
            if content.transcript_text:
                text_sources['transcript'] += 1
            if content.ocr_text:
                text_sources['ocr'] += 1
            if content.caption_text:
                text_sources['caption'] += 1
            if content.annotation_text:
                text_sources['annotation'] += 1
        
        return {
            'total_content': total_content,
            'content_by_type': type_counts,
            'total_entities': total_entities,
            'text_sources': text_sources,
            'average_entities_per_content': total_entities / total_content if total_content > 0 else 0
        }

# Example usage
if __name__ == "__main__":
    # Create pipeline
    pipeline = ImageTextIntegrationPipelineLite()
    
    print("Image-Text Integration Pipeline Lite initialized")
    print(f"Available components: OCR={HAS_OCR}, STT={HAS_STT}, NER={HAS_NER_BASIC}")