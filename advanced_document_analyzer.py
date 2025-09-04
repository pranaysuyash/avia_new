#!/usr/bin/env python3
"""
Advanced Document Analysis System
Enhanced document processing with AI-powered analysis, classification, and insights
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import numpy as np
from collections import Counter
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import cv2
from PIL import Image
import fitz  # PyMuPDF

# Import our existing OCR system
from image_ocr_processor import OCRManager, OCRResult, DocumentResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentClassification:
    """Document classification result"""
    document_type: str
    confidence: float
    categories: List[Dict[str, float]]
    metadata: Dict[str, Any]

@dataclass
class DocumentInsights:
    """Advanced document insights"""
    key_entities: List[Dict[str, Any]]
    topics: List[Dict[str, float]]
    sentiment: Dict[str, float]
    readability_score: float
    language_detected: str
    document_structure: Dict[str, Any]
    compliance_flags: List[Dict[str, Any]]

@dataclass
class FormField:
    """Extracted form field"""
    field_name: str
    field_value: str
    field_type: str
    confidence: float
    bbox: List[int]

@dataclass
class TableData:
    """Extracted table data"""
    table_id: int
    headers: List[str]
    rows: List[List[str]]
    bbox: List[int]
    confidence: float

@dataclass
class AdvancedDocumentResult:
    """Complete advanced document analysis result"""
    filename: str
    ocr_result: Union[OCRResult, DocumentResult]
    classification: DocumentClassification
    insights: DocumentInsights
    form_fields: List[FormField]
    tables: List[TableData]
    processing_time: float
    metadata: Dict[str, Any]

class DocumentClassifier:
    """AI-powered document classification system"""
    
    def __init__(self):
        self.document_types = {
            'invoice': ['invoice', 'bill', 'payment', 'amount due', 'total', 'tax'],
            'contract': ['agreement', 'contract', 'terms', 'conditions', 'party', 'signature'],
            'receipt': ['receipt', 'purchase', 'transaction', 'paid', 'change'],
            'legal': ['court', 'legal', 'law', 'attorney', 'plaintiff', 'defendant'],
            'medical': ['patient', 'doctor', 'medical', 'diagnosis', 'treatment', 'prescription'],
            'financial': ['bank', 'account', 'balance', 'statement', 'transaction', 'credit'],
            'academic': ['university', 'student', 'grade', 'course', 'transcript', 'degree'],
            'government': ['government', 'official', 'department', 'license', 'permit', 'certificate'],
            'business': ['company', 'business', 'corporate', 'meeting', 'report', 'proposal'],
            'personal': ['personal', 'private', 'individual', 'family', 'home']
        }
        
        # Try to load a pre-trained classification model
        try:
            self.classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True
            )
            self.model_available = True
        except Exception as e:
            logger.warning(f"Could not load classification model: {e}")
            self.model_available = False
    
    def classify_document(self, text: str, filename: str = "") -> DocumentClassification:
        """Classify document type based on content"""
        try:
            # Rule-based classification
            text_lower = text.lower()
            filename_lower = filename.lower()
            
            scores = {}
            for doc_type, keywords in self.document_types.items():
                score = 0
                for keyword in keywords:
                    # Count occurrences in text
                    score += text_lower.count(keyword) * 2
                    # Bonus for filename match
                    if keyword in filename_lower:
                        score += 5
                
                # Normalize by text length
                if len(text) > 0:
                    scores[doc_type] = score / (len(text) / 1000)
                else:
                    scores[doc_type] = 0
            
            # Find best match
            if scores:
                best_type = max(scores, key=scores.get)
                confidence = min(scores[best_type] / 10, 1.0)  # Normalize to 0-1
            else:
                best_type = "unknown"
                confidence = 0.0
            
            # Create categories list
            categories = [{"type": k, "score": v} for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
            
            return DocumentClassification(
                document_type=best_type,
                confidence=confidence,
                categories=categories[:5],  # Top 5 categories
                metadata={
                    "method": "rule_based",
                    "total_keywords_found": sum(scores.values()),
                    "text_length": len(text)
                }
            )
            
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            return DocumentClassification(
                document_type="unknown",
                confidence=0.0,
                categories=[],
                metadata={"error": str(e)}
            )

class DocumentInsightExtractor:
    """Extract advanced insights from documents"""
    
    def __init__(self):
        # Load spaCy model for NER
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.spacy_available = True
        except Exception as e:
            logger.warning(f"spaCy model not available: {e}")
            self.spacy_available = False
        
        # Try to load sentiment analysis
        try:
            self.sentiment_analyzer = pipeline("sentiment-analysis")
            self.sentiment_available = True
        except Exception as e:
            logger.warning(f"Sentiment analysis not available: {e}")
            self.sentiment_available = False
    
    def extract_insights(self, text: str) -> DocumentInsights:
        """Extract comprehensive insights from document text"""
        try:
            # Extract entities
            entities = self._extract_entities(text)
            
            # Extract topics
            topics = self._extract_topics(text)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(text)
            
            # Calculate readability
            readability = self._calculate_readability(text)
            
            # Detect language
            language = self._detect_language(text)
            
            # Analyze document structure
            structure = self._analyze_structure(text)
            
            # Check compliance flags
            compliance_flags = self._check_compliance(text)
            
            return DocumentInsights(
                key_entities=entities,
                topics=topics,
                sentiment=sentiment,
                readability_score=readability,
                language_detected=language,
                document_structure=structure,
                compliance_flags=compliance_flags
            )
            
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return DocumentInsights(
                key_entities=[],
                topics=[],
                sentiment={"compound": 0.0, "positive": 0.0, "negative": 0.0, "neutral": 1.0},
                readability_score=0.0,
                language_detected="unknown",
                document_structure={},
                compliance_flags=[]
            )
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        entities = []
        
        if self.spacy_available and text.strip():
            try:
                doc = self.nlp(text[:1000000])  # Limit text length for processing
                
                for ent in doc.ents:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "description": spacy.explain(ent.label_),
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "confidence": 0.8  # spaCy doesn't provide confidence scores
                    })
            except Exception as e:
                logger.warning(f"Entity extraction failed: {e}")
        
        # Add regex-based entity extraction for common patterns
        regex_entities = self._extract_regex_entities(text)
        entities.extend(regex_entities)
        
        return entities
    
    def _extract_regex_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using regex patterns"""
        entities = []
        
        patterns = {
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "PHONE": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
            "DATE": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            "CURRENCY": r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
            "URL": r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "text": match.group(),
                    "label": entity_type,
                    "description": f"Regex-detected {entity_type.lower()}",
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.9
                })
        
        return entities
    
    def _extract_topics(self, text: str) -> List[Dict[str, float]]:
        """Extract main topics from text"""
        topics = []
        
        # Simple keyword-based topic extraction
        topic_keywords = {
            "finance": ["money", "payment", "cost", "price", "budget", "financial", "bank", "credit"],
            "legal": ["law", "legal", "court", "contract", "agreement", "terms", "liability"],
            "medical": ["health", "medical", "doctor", "patient", "treatment", "diagnosis", "medicine"],
            "business": ["business", "company", "corporate", "meeting", "project", "strategy", "market"],
            "technology": ["software", "computer", "digital", "online", "internet", "system", "data"],
            "education": ["education", "school", "student", "learning", "course", "academic", "university"],
            "government": ["government", "public", "official", "policy", "regulation", "department", "agency"]
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            score = sum(text_lower.count(keyword) for keyword in keywords)
            if score > 0:
                # Normalize by text length
                normalized_score = min(score / (len(text) / 1000), 1.0)
                topics.append({"topic": topic, "score": normalized_score})
        
        # Sort by score
        topics.sort(key=lambda x: x["score"], reverse=True)
        return topics[:5]  # Top 5 topics
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze document sentiment"""
        if self.sentiment_available and text.strip():
            try:
                # Truncate text for processing
                sample_text = text[:512]  # Most models have token limits
                result = self.sentiment_analyzer(sample_text)[0]
                
                return {
                    "label": result["label"].lower(),
                    "score": result["score"],
                    "compound": result["score"] if result["label"] == "POSITIVE" else -result["score"]
                }
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
        
        return {"label": "neutral", 
"score": 0.5, "compound": 0.0}
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (Flesch Reading Ease)"""
        if not text.strip():
            return 0.0
        
        try:
            # Simple readability calculation
            sentences = len(re.split(r'[.!?]+', text))
            words = len(text.split())
            syllables = sum(self._count_syllables(word) for word in text.split())
            
            if sentences == 0 or words == 0:
                return 0.0
            
            # Flesch Reading Ease formula
            score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
            return max(0, min(100, score))  # Clamp between 0-100
            
        except Exception:
            return 50.0  # Default middle score
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simple approximation)"""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Handle silent e
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _detect_language(self, text: str) -> str:
        """Detect document language"""
        # Simple language detection based on common words
        language_indicators = {
            'en': ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with'],
            'es': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no'],
            'fr': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir'],
            'de': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich'],
            'it': ['il', 'di', 'che', 'e', 'la', 'per', 'in', 'un', 'è', 'con']
        }
        
        text_lower = text.lower()
        scores = {}
        
        for lang, indicators in language_indicators.items():
            score = sum(text_lower.count(word) for word in indicators)
            scores[lang] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'en'  # Default to English
    
    def _analyze_structure(self, text: str) -> Dict[str, Any]:
        """Analyze document structure"""
        lines = text.split('\n')
        
        return {
            "total_lines": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "average_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0,
            "has_headers": any(line.isupper() for line in lines[:10]),  # Check first 10 lines
            "has_bullet_points": any(line.strip().startswith(('•', '-', '*', '1.', '2.')) for line in lines),
            "paragraph_count": len([line for line in lines if len(line.strip()) > 50]),
            "word_count": len(text.split()),
            "character_count": len(text)
        }
    
    def _check_compliance(self, text: str) -> List[Dict[str, Any]]:
        """Check for compliance-related content"""
        flags = []
        text_lower = text.lower()
        
        # PII detection patterns
        pii_patterns = {
            "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
            "Credit Card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        for pii_type, pattern in pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                flags.append({
                    "type": "PII_DETECTED",
                    "category": pii_type,
                    "count": len(matches),
                    "severity": "HIGH",
                    "description": f"Detected {len(matches)} instances of {pii_type}"
                })
        
        # Sensitive content keywords
        sensitive_keywords = [
            "confidential", "classified", "restricted", "proprietary", 
            "internal use only", "do not distribute", "trade secret"
        ]
        
        for keyword in sensitive_keywords:
            if keyword in text_lower:
                flags.append({
                    "type": "SENSITIVE_CONTENT",
                    "category": "CONFIDENTIAL",
                    "keyword": keyword,
                    "severity": "MEDIUM",
                    "description": f"Document contains sensitive keyword: {keyword}"
                })
        
        return flags

class FormFieldExtractor:
    """Extract form fields from documents"""
    
    def __init__(self):
        self.field_patterns = {
            "name": [r"name\s*:?\s*([^\n]+)", r"full\s+name\s*:?\s*([^\n]+)"],
            "email": [r"email\s*:?\s*([^\n]+)", r"e-mail\s*:?\s*([^\n]+)"],
            "phone": [r"phone\s*:?\s*([^\n]+)", r"telephone\s*:?\s*([^\n]+)"],
            "address": [r"address\s*:?\s*([^\n]+)", r"street\s*:?\s*([^\n]+)"],
            "date": [r"date\s*:?\s*([^\n]+)", r"dated\s*:?\s*([^\n]+)"],
            "amount": [r"amount\s*:?\s*([^\n]+)", r"total\s*:?\s*([^\n]+)"],
            "signature": [r"signature\s*:?\s*([^\n]+)", r"signed\s*:?\s*([^\n]+)"]
        }
    
    def extract_fields(self, text: str, ocr_result: Union[OCRResult, DocumentResult]) -> List[FormField]:
        """Extract form fields from text"""
        fields = []
        
        for field_type, patterns in self.field_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    field_value = match.group(1).strip()
                    if field_value and len(field_value) > 1:
                        fields.append(FormField(
                            field_name=field_type,
                            field_value=field_value,
                            field_type="text",
                            confidence=0.8,
                            bbox=[0, 0, 0, 0]  # Would need OCR bounding box data
                        ))
        
        return fields

class TableExtractor:
    """Extract table data from documents"""
    
    def extract_tables(self, text: str, ocr_result: Union[OCRResult, DocumentResult]) -> List[TableData]:
        """Extract table data from text"""
        tables = []
        
        # Simple table detection based on consistent spacing/alignment
        lines = text.split('\n')
        potential_tables = []
        current_table = []
        
        for line in lines:
            # Check if line looks like a table row (has multiple columns separated by spaces/tabs)
            if self._is_table_row(line):
                current_table.append(line)
            else:
                if len(current_table) >= 3:  # Minimum 3 rows for a table
                    potential_tables.append(current_table)
                current_table = []
        
        # Process potential tables
        for i, table_lines in enumerate(potential_tables):
            headers, rows = self._parse_table_lines(table_lines)
            if headers and rows:
                tables.append(TableData(
                    table_id=i,
                    headers=headers,
                    rows=rows,
                    bbox=[0, 0, 0, 0],  # Would need OCR bounding box data
                    confidence=0.7
                ))
        
        return tables
    
    def _is_table_row(self, line: str) -> bool:
        """Check if a line looks like a table row"""
        # Simple heuristic: line has multiple words separated by significant whitespace
        parts = line.split()
        if len(parts) < 2:
            return False
        
        # Check for consistent spacing patterns
        spaces = re.findall(r'\s{2,}', line)
        return len(spaces) >= 1  # At least one multi-space separator
    
    def _parse_table_lines(self, lines: List[str]) -> Tuple[List[str], List[List[str]]]:
        """Parse table lines into headers and rows"""
        if not lines:
            return [], []
        
        # Assume first line is headers
        headers = lines[0].split()
        rows = []
        
        for line in lines[1:]:
            row = line.split()
            if row:  # Skip empty rows
                rows.append(row)
        
        return headers, rows

class AdvancedDocumentAnalyzer:
    """Main advanced document analysis system"""
    
    def __init__(self):
        self.ocr_manager = OCRManager()
        self.classifier = DocumentClassifier()
        self.insight_extractor = DocumentInsightExtractor()
        self.form_extractor = FormFieldExtractor()
        self.table_extractor = TableExtractor()
    
    def analyze_document(self, file_path: str, language: str = 'en', 
                        extract_forms: bool = True, 
                        extract_tables: bool = True) -> AdvancedDocumentResult:
        """Perform comprehensive document analysis"""
        start_time = datetime.now()
        
        try:
            # Step 1: OCR processing
            ocr_result = self.ocr_manager.process_file(file_path, language)
            
            # Get text for analysis
            if isinstance(ocr_result, DocumentResult):
                text = ocr_result.combined_text
            else:
                text = ocr_result.text
            
            # Step 2: Document classification
            classification = self.classifier.classify_document(text, Path(file_path).name)
            
            # Step 3: Extract insights
            insights = self.insight_extractor.extract_insights(text)
            
            # Step 4: Extract form fields
            form_fields = []
            if extract_forms:
                form_fields = self.form_extractor.extract_fields(text, ocr_result)
            
            # Step 5: Extract tables
            tables = []
            if extract_tables:
                tables = self.table_extractor.extract_tables(text, ocr_result)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AdvancedDocumentResult(
                filename=Path(file_path).name,
                ocr_result=ocr_result,
                classification=classification,
                insights=insights,
                form_fields=form_fields,
                tables=tables,
                processing_time=processing_time,
                metadata={
                    "file_size": Path(file_path).stat().st_size,
                    "file_extension": Path(file_path).suffix,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "language": language,
                    "extract_forms": extract_forms,
                    "extract_tables": extract_tables
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing document {file_path}: {e}")
            raise
    
    def analyze_batch(self, file_paths: List[str], **kwargs) -> List[AdvancedDocumentResult]:
        """Analyze multiple documents in batch"""
        results = []
        
        for file_path in file_paths:
            try:
                result = self.analyze_document(file_path, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                continue
        
        return results
    
    def export_results(self, results: List[AdvancedDocumentResult], 
                      output_format: str = "json") -> str:
        """Export analysis results"""
        if output_format.lower() == "json":
            return json.dumps([asdict(result) for result in results], 
                            indent=2, default=str)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def get_analysis_summary(self, results: List[AdvancedDocumentResult]) -> Dict[str, Any]:
        """Get summary statistics from analysis results"""
        if not results:
            return {}
        
        # Document type distribution
        doc_types = [r.classification.document_type for r in results]
        type_counts = Counter(doc_types)
        
        # Language distribution
        languages = [r.insights.language_detected for r in results]
        lang_counts = Counter(languages)
        
        # Average processing time
        avg_processing_time = sum(r.processing_time for r in results) / len(results)
        
        # Compliance flags summary
        total_flags = sum(len(r.insights.compliance_flags) for r in results)
        
        return {
            "total_documents": len(results),
            "document_types": dict(type_counts),
            "languages": dict(lang_counts),
            "average_processing_time": avg_processing_time,
            "total_compliance_flags": total_flags,
            "documents_with_forms": sum(1 for r in results if r.form_fields),
            "documents_with_tables": sum(1 for r in results if r.tables),
            "average_readability": sum(r.insights.readability_score for r in results) / len(results)
        }

# Utility functions
def create_searchable_index(results: List[AdvancedDocumentResult]) -> Dict[str, List[str]]:
    """Create searchable index from analysis results"""
    index = {}
    
    for result in results:
        filename = result.filename
        
        # Index by document type
        doc_type = result.classification.document_type
        if doc_type not in index:
            index[doc_type] = []
        index[doc_type].append(filename)
        
        # Index by entities
        for entity in result.insights.key_entities:
            entity_text = entity["text"].lower()
            if entity_text not in index:
                index[entity_text] = []
            index[entity_text].append(filename)
        
        # Index by topics
        for topic in result.insights.topics:
            topic_name = topic["topic"]
            if topic_name not in index:
                index[topic_name] = []
            index[topic_name].append(filename)
    
    return index

def search_documents(index: Dict[str, List[str]], query: str) -> List[str]:
    """Search documents using the index"""
    query_lower = query.lower()
    results = set()
    
    for key, filenames in index.items():
        if query_lower in key.lower():
            results.update(filenames)
    
    return list(results)

# Export main classes
__all__ = [
    'AdvancedDocumentAnalyzer',
    'DocumentClassifier',
    'DocumentInsightExtractor',
    'FormFieldExtractor',
    'TableExtractor',
    'AdvancedDocumentResult',
    'DocumentClassification',
    'DocumentInsights',
    'FormField',
    'TableData',
    'create_searchable_index',
    'search_documents'
]