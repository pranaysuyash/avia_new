#!/usr/bin/env python3
"""
Advanced Document Analysis System
Professional document analysis, classification, and insights extraction
"""

import os
import logging
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import base64

# Core processing libraries
import pandas as pd
import numpy as np

# Document processing
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    logging.warning("PyMuPDF not available - PDF processing will be limited")

try:
    import PIL.Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logging.warning("PIL not available - image processing will be limited")

# Text processing
import re
from collections import Counter

# ML and NLP
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    logging.warning("spaCy not available - using basic text processing")

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """Document metadata and properties"""
    filename: str
    file_size: int
    file_type: str
    pages: int = 0
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    keywords: List[str] = None
    language: str = "en"
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class DocumentAnalysisResult:
    """Complete document analysis results"""
    metadata: DocumentMetadata
    text_content: str
    word_count: int
    page_count: int
    entities: List[Dict[str, Any]]
    key_phrases: List[str]
    topics: List[Dict[str, Any]]
    sentiment_score: float
    readability_score: float
    classification: Dict[str, Any]
    structure_analysis: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['metadata'] = asdict(self.metadata)
        return result


class AdvancedDocumentAnalyzer:
    """Advanced document analysis with ML-powered insights"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.nlp_model = None
        self._initialize_nlp()
        
        # Document cache
        self.document_cache = {}
        
        # Analysis statistics
        self.stats = {
            'documents_processed': 0,
            'total_pages': 0,
            'total_words': 0,
            'processing_time': 0.0
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration for document analysis"""
        return {
            'max_file_size': 50 * 1024 * 1024,  # 50MB
            'supported_formats': ['.pdf', '.txt', '.docx', '.doc'],
            'extract_entities': True,
            'extract_topics': True,
            'analyze_sentiment': True,
            'analyze_structure': True,
            'cache_results': True,
            'language_detection': True
        }
    
    def _initialize_nlp(self):
        """Initialize NLP models"""
        if HAS_SPACY:
            try:
                # Try to load English model
                self.nlp_model = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy English model")
            except OSError:
                logger.warning("spaCy English model not found - using basic processing")
                self.nlp_model = None
        else:
            logger.info("Using basic text processing (spaCy not available)")
    
    def analyze_document(self, file_path: Union[str, Path], 
                        options: Dict[str, Any] = None) -> DocumentAnalysisResult:
        """Comprehensive document analysis"""
        start_time = datetime.now()
        file_path = Path(file_path)
        
        # Check cache first
        cache_key = self._get_cache_key(file_path)
        if self.config.get('cache_results') and cache_key in self.document_cache:
            logger.info(f"Returning cached results for {file_path.name}")
            return self.document_cache[cache_key]
        
        # Extract document content and metadata
        metadata = self._extract_metadata(file_path)
        text_content = self._extract_text(file_path)
        
        if not text_content.strip():
            raise ValueError(f"No text content extracted from {file_path.name}")
        
        # Perform analysis
        analysis_options = {**self.config, **(options or {})}
        
        # Basic text statistics
        word_count = len(text_content.split())
        
        # Entity extraction
        entities = []
        if analysis_options.get('extract_entities'):
            entities = self._extract_entities(text_content)
        
        # Key phrase extraction
        key_phrases = self._extract_key_phrases(text_content)
        
        # Topic analysis
        topics = []
        if analysis_options.get('extract_topics'):
            topics = self._extract_topics(text_content)
        
        # Sentiment analysis
        sentiment_score = 0.0
        if analysis_options.get('analyze_sentiment'):
            sentiment_score = self._analyze_sentiment(text_content)
        
        # Readability analysis
        readability_score = self._calculate_readability(text_content)
        
        # Document classification
        classification = self._classify_document(text_content, metadata)
        
        # Structure analysis
        structure_analysis = {}
        if analysis_options.get('analyze_structure'):
            structure_analysis = self._analyze_structure(text_content, file_path)
        
        # Create result
        result = DocumentAnalysisResult(
            metadata=metadata,
            text_content=text_content,
            word_count=word_count,
            page_count=metadata.pages,
            entities=entities,
            key_phrases=key_phrases,
            topics=topics,
            sentiment_score=sentiment_score,
            readability_score=readability_score,
            classification=classification,
            structure_analysis=structure_analysis,
            timestamp=datetime.now()
        )
        
        # Cache result
        if self.config.get('cache_results'):
            self.document_cache[cache_key] = result
        
        # Update statistics
        processing_time = (datetime.now() - start_time).total_seconds()
        self.stats['documents_processed'] += 1
        self.stats['total_pages'] += metadata.pages
        self.stats['total_words'] += word_count
        self.stats['processing_time'] += processing_time
        
        logger.info(f"Analyzed {file_path.name} in {processing_time:.2f}s")
        
        return result
    
    def _get_cache_key(self, file_path: Path) -> str:
        """Generate cache key for document"""
        stat = file_path.stat()
        content = f"{file_path.name}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """Extract document metadata"""
        stat = file_path.stat()
        
        metadata = DocumentMetadata(
            filename=file_path.name,
            file_size=stat.st_size,
            file_type=file_path.suffix.lower(),
            creation_date=datetime.fromtimestamp(stat.st_ctime),
            modification_date=datetime.fromtimestamp(stat.st_mtime)
        )
        
        # PDF-specific metadata
        if file_path.suffix.lower() == '.pdf' and HAS_PYMUPDF:
            try:
                doc = fitz.open(file_path)
                metadata.pages = doc.page_count
                
                # Extract PDF metadata
                pdf_metadata = doc.metadata
                metadata.title = pdf_metadata.get('title', '')
                metadata.author = pdf_metadata.get('author', '')
                metadata.subject = pdf_metadata.get('subject', '')
                metadata.keywords = pdf_metadata.get('keywords', '').split(',') if pdf_metadata.get('keywords') else []
                
                doc.close()
            except Exception as e:
                logger.warning(f"Failed to extract PDF metadata: {e}")
                metadata.pages = 1
        else:
            metadata.pages = 1
        
        return metadata
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text content from document"""
        file_type = file_path.suffix.lower()
        
        if file_type == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        elif file_type == '.pdf' and HAS_PYMUPDF:
            try:
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text
            except Exception as e:
                logger.error(f"Failed to extract PDF text: {e}")
                return ""
        
        else:
            # Fallback: try to read as text
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to extract text from {file_path}: {e}")
                return ""
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        entities = []
        
        if self.nlp_model:
            # Use spaCy for entity extraction
            doc = self.nlp_model(text[:1000000])  # Limit text size
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 1.0
                })
        else:
            # Basic regex-based entity extraction
            # Email addresses
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            for email in emails:
                entities.append({
                    'text': email,
                    'label': 'EMAIL',
                    'start': text.find(email),
                    'end': text.find(email) + len(email),
                    'confidence': 0.9
                })
            
            # Phone numbers (basic pattern)
            phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
            for phone in phones:
                entities.append({
                    'text': phone,
                    'label': 'PHONE',
                    'start': text.find(phone),
                    'end': text.find(phone) + len(phone),
                    'confidence': 0.8
                })
        
        return entities
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        # Simple approach: most frequent multi-word phrases
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Create bigrams and trigrams
        phrases = []
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            phrases.append(bigram)
        
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            phrases.append(trigram)
        
        # Count frequencies and return top phrases
        phrase_counts = Counter(phrases)
        return [phrase for phrase, count in phrase_counts.most_common(10)]
    
    def _extract_topics(self, text: str) -> List[Dict[str, Any]]:
        """Extract topics from text"""
        # Simple topic extraction based on keyword frequency
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = Counter(words)
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        topics = []
        for word, count in word_counts.most_common(20):
            if word not in stop_words and len(word) > 3:
                topics.append({
                    'topic': word,
                    'weight': count / len(words),
                    'frequency': count
                })
        
        return topics[:10]
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text"""
        # Simple sentiment analysis based on word lists
        positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'positive', 'happy', 'love', 'like', 'best', 'perfect', 'outstanding', 'brilliant', 'awesome'}
        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike', 'poor', 'negative', 'sad', 'angry', 'disappointed', 'frustrated', 'annoying'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        # Return sentiment score between -1 and 1
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (simplified Flesch reading ease)"""
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(re.findall(r'\b\w+\b', text))
        syllables = sum(self._count_syllables(word) for word in re.findall(r'\b\w+\b', text))
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Simplified Flesch reading ease formula
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0, min(100, score))  # Clamp between 0 and 100
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_char_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_char_was_vowel:
                    syllable_count += 1
                prev_char_was_vowel = True
            else:
                prev_char_was_vowel = False
        
        # Handle silent 'e'
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _classify_document(self, text: str, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Classify document type and content"""
        classification = {
            'document_type': 'unknown',
            'content_category': 'general',
            'confidence': 0.0,
            'indicators': []
        }
        
        # Simple rule-based classification
        text_lower = text.lower()
        
        # Document type classification
        if 'contract' in text_lower or 'agreement' in text_lower:
            classification['document_type'] = 'contract'
            classification['confidence'] = 0.8
        elif 'invoice' in text_lower or 'bill' in text_lower or '$' in text:
            classification['document_type'] = 'financial'
            classification['confidence'] = 0.8
        elif 'report' in text_lower or 'analysis' in text_lower:
            classification['document_type'] = 'report'
            classification['confidence'] = 0.7
        elif 'email' in text_lower or '@' in text:
            classification['document_type'] = 'communication'
            classification['confidence'] = 0.9
        
        # Content category
        if any(word in text_lower for word in ['medical', 'patient', 'diagnosis', 'treatment']):
            classification['content_category'] = 'medical'
        elif any(word in text_lower for word in ['legal', 'court', 'law', 'attorney']):
            classification['content_category'] = 'legal'
        elif any(word in text_lower for word in ['financial', 'money', 'investment', 'bank']):
            classification['content_category'] = 'financial'
        elif any(word in text_lower for word in ['technical', 'software', 'system', 'code']):
            classification['content_category'] = 'technical'
        
        return classification
    
    def _analyze_structure(self, text: str, file_path: Path) -> Dict[str, Any]:
        """Analyze document structure"""
        structure = {
            'has_headers': False,
            'has_lists': False,
            'has_tables': False,
            'paragraph_count': 0,
            'average_paragraph_length': 0,
            'heading_levels': []
        }
        
        lines = text.split('\n')
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        structure['paragraph_count'] = len(paragraphs)
        if paragraphs:
            structure['average_paragraph_length'] = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
        
        # Detect headers (lines that are short and followed by longer text)
        for i, line in enumerate(lines):
            if line.strip() and len(line.split()) < 10:
                if i + 1 < len(lines) and len(lines[i + 1].split()) > 10:
                    structure['has_headers'] = True
                    break
        
        # Detect lists
        list_indicators = ['-', '*', '"', '1.', '2.', 'a)', 'i)']
        for line in lines:
            if any(line.strip().startswith(indicator) for indicator in list_indicators):
                structure['has_lists'] = True
                break
        
        # Detect tables (simple heuristic)
        for line in lines:
            if line.count('|') > 2 or line.count('\t') > 2:
                structure['has_tables'] = True
                break
        
        return structure
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self.stats.copy()
    
    def clear_cache(self):
        """Clear document cache"""
        self.document_cache.clear()
        logger.info("Document cache cleared")


def create_searchable_index(documents: List[DocumentAnalysisResult]) -> Dict[str, Any]:
    """Create a searchable index from analyzed documents"""
    index = {
        'documents': {},
        'terms': {},
        'entities': {},
        'topics': {}
    }
    
    for doc in documents:
        doc_id = hashlib.md5(doc.metadata.filename.encode()).hexdigest()
        
        # Store document
        index['documents'][doc_id] = {
            'filename': doc.metadata.filename,
            'title': doc.metadata.title or doc.metadata.filename,
            'word_count': doc.word_count,
            'page_count': doc.page_count,
            'timestamp': doc.timestamp.isoformat()
        }
        
        # Index terms
        words = re.findall(r'\b\w+\b', doc.text_content.lower())
        for word in set(words):
            if word not in index['terms']:
                index['terms'][word] = []
            index['terms'][word].append(doc_id)
        
        # Index entities
        for entity in doc.entities:
            entity_text = entity['text'].lower()
            if entity_text not in index['entities']:
                index['entities'][entity_text] = []
            index['entities'][entity_text].append({
                'doc_id': doc_id,
                'label': entity['label'],
                'confidence': entity['confidence']
            })
        
        # Index topics
        for topic in doc.topics:
            topic_name = topic['topic']
            if topic_name not in index['topics']:
                index['topics'][topic_name] = []
            index['topics'][topic_name].append({
                'doc_id': doc_id,
                'weight': topic['weight']
            })
    
    return index


def search_documents(index: Dict[str, Any], query: str, 
                    search_type: str = 'text') -> List[Dict[str, Any]]:
    """Search documents using the created index"""
    results = []
    query_lower = query.lower()
    
    if search_type == 'text':
        # Text search
        query_words = re.findall(r'\b\w+\b', query_lower)
        doc_scores = {}
        
        for word in query_words:
            if word in index['terms']:
                for doc_id in index['terms'][word]:
                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = 0
                    doc_scores[doc_id] += 1
        
        # Sort by relevance
        for doc_id, score in sorted(doc_scores.items(), key=lambda x: x[1], reverse=True):
            if doc_id in index['documents']:
                result = index['documents'][doc_id].copy()
                result['doc_id'] = doc_id
                result['relevance_score'] = score / len(query_words)
                results.append(result)
    
    elif search_type == 'entity':
        # Entity search
        if query_lower in index['entities']:
            for entity_match in index['entities'][query_lower]:
                doc_id = entity_match['doc_id']
                if doc_id in index['documents']:
                    result = index['documents'][doc_id].copy()
                    result['doc_id'] = doc_id
                    result['entity_label'] = entity_match['label']
                    result['confidence'] = entity_match['confidence']
                    results.append(result)
    
    elif search_type == 'topic':
        # Topic search
        if query_lower in index['topics']:
            for topic_match in index['topics'][query_lower]:
                doc_id = topic_match['doc_id']
                if doc_id in index['documents']:
                    result = index['documents'][doc_id].copy()
                    result['doc_id'] = doc_id
                    result['topic_weight'] = topic_match['weight']
                    results.append(result)
        
        # Sort by topic weight
        results.sort(key=lambda x: x.get('topic_weight', 0), reverse=True)
    
    return results


# Example usage and demo
if __name__ == "__main__":
    # Initialize analyzer
    analyzer = AdvancedDocumentAnalyzer()
    
    # Demo with a sample text file
    demo_text = """
    Advanced Document Analysis System
    
    This is a comprehensive document analysis system that provides:
    
    1. Text extraction from multiple formats
    2. Named entity recognition
    3. Topic modeling and analysis
    4. Sentiment analysis
    5. Document classification
    6. Structure analysis
    
    The system is designed to handle various document types including PDFs, 
    Word documents, and text files. It uses advanced NLP techniques to 
    extract meaningful insights from documents.
    
    Contact: support@example.com
    Phone: 555-123-4567
    
    This technology can be used in legal document review, medical record 
    analysis, financial document processing, and general content analysis.
    """
    
    # Create a temporary file for demo
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(demo_text)
        temp_file = f.name
    
    try:
        # Analyze the document
        result = analyzer.analyze_document(temp_file)
        
        print("Document Analysis Results:")
        print(f"Filename: {result.metadata.filename}")
        print(f"Word count: {result.word_count}")
        print(f"Entities found: {len(result.entities)}")
        print(f"Key phrases: {result.key_phrases[:5]}")
        print(f"Top topics: {[t['topic'] for t in result.topics[:5]]}")
        print(f"Sentiment score: {result.sentiment_score:.2f}")
        print(f"Readability score: {result.readability_score:.1f}")
        print(f"Document type: {result.classification['document_type']}")
        
        # Test search functionality
        documents = [result]
        index = create_searchable_index(documents)
        
        search_results = search_documents(index, "analysis system", "text")
        print(f"\nSearch results for 'analysis system': {len(search_results)} documents found")
        
    finally:
        # Clean up
        os.unlink(temp_file)
        
    print(f"\nProcessing statistics: {analyzer.get_analysis_statistics()}")