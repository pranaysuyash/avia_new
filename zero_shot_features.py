"""
Zero-Shot Classification Features
Extracted from text_classification_system.py

This module provides zero-shot classification capabilities using pre-trained models.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

# Core ML libraries
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Transformers with fallback
try:
    from transformers import (
        AutoTokenizer, AutoModelForSequenceClassification,
        AutoModelForZeroShotClassification, pipeline
    )
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
    print("✅ Transformers available - Full zero-shot capabilities enabled")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not available - Using similarity-based fallback")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZeroShotMethod(Enum):
    """Zero-shot classification methods"""
    TRANSFORMER_NLI = "transformer_nli"
    SENTENCE_SIMILARITY = "sentence_similarity"
    KEYWORD_MATCHING = "keyword_matching"
    HYBRID = "hybrid"

class ConfidenceThreshold(Enum):
    """Confidence thresholds for zero-shot predictions"""
    VERY_HIGH = 0.9
    HIGH = 0.75
    MEDIUM = 0.6
    LOW = 0.4
    VERY_LOW = 0.2

@dataclass
class ZeroShotLabel:
    """Represents a zero-shot classification label"""
    label: str
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    parent_label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ZeroShotPrediction:
    """Represents a zero-shot classification prediction"""
    text: str
    predicted_label: str
    confidence: float
    all_scores: Dict[str, float]
    method_used: ZeroShotMethod
    threshold_met: ConfidenceThreshold
    explanation: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ZeroShotSession:
    """Zero-shot classification session"""
    session_id: str
    method: ZeroShotMethod
    labels: List[ZeroShotLabel]
    predictions_made: int = 0
    high_confidence_predictions: int = 0
    low_confidence_predictions: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    performance_stats: Dict[str, float] = field(default_factory=dict)

class TransformerZeroShotClassifier:
    """Zero-shot classification using transformer models"""
    
    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        self.model_name = model_name
        self.classifier = None
        self.init_model()
    
    def init_model(self):
        """Initialize the zero-shot classification model"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available - zero-shot classification disabled")
            return
        
        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model=self.model_name,
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info(f"✅ Zero-shot classifier initialized: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize zero-shot classifier: {e}")
            self.classifier = None
    
    def classify(self, text: str, candidate_labels: List[str]) -> Dict[str, float]:
        """Classify text against candidate labels"""
        if not self.classifier:
            return {}
        
        try:
            result = self.classifier(text, candidate_labels)
            
            # Convert to dictionary format
            scores = {}
            for label, score in zip(result['labels'], result['scores']):
                scores[label] = float(score)
            
            return scores
            
        except Exception as e:
            logger.error(f"Zero-shot classification failed: {e}")
            return {}

class SentenceSimilarityClassifier:
    """Zero-shot classification using sentence similarity"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.init_model()
    
    def init_model(self):
        """Initialize sentence transformer model"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available - using TF-IDF similarity")
            self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✅ Sentence transformer initialized: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize sentence transformer: {e}")
            self.model = None
            self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    
    def classify(self, text: str, label_descriptions: Dict[str, str]) -> Dict[str, float]:
        """Classify text using similarity to label descriptions"""
        if self.model:
            return self._classify_with_transformers(text, label_descriptions)
        else:
            return self._classify_with_tfidf(text, label_descriptions)
    
    def _classify_with_transformers(self, text: str, label_descriptions: Dict[str, str]) -> Dict[str, float]:
        """Classify using sentence transformers"""
        try:
            # Encode text and label descriptions
            text_embedding = self.model.encode([text])
            label_embeddings = self.model.encode(list(label_descriptions.values()))
            
            # Calculate similarities
            similarities = cosine_similarity(text_embedding, label_embeddings)[0]
            
            # Normalize to probabilities
            exp_similarities = np.exp(similarities)
            probabilities = exp_similarities / np.sum(exp_similarities)
            
            # Create scores dictionary
            scores = {}
            for i, (label, _) in enumerate(label_descriptions.items()):
                scores[label] = float(probabilities[i])
            
            return scores
            
        except Exception as e:
            logger.error(f"Sentence similarity classification failed: {e}")
            return {}
    
    def _classify_with_tfidf(self, text: str, label_descriptions: Dict[str, str]) -> Dict[str, float]:
        """Classify using TF-IDF similarity"""
        try:
            # Combine text with label descriptions
            all_texts = [text] + list(label_descriptions.values())
            
            # Vectorize
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            # Calculate similarities
            text_vector = tfidf_matrix[0]
            label_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(text_vector, label_vectors)[0]
            
            # Normalize to probabilities
            exp_similarities = np.exp(similarities)
            probabilities = exp_similarities / np.sum(exp_similarities)
            
            # Create scores dictionary
            scores = {}
            for i, (label, _) in enumerate(label_descriptions.items()):
                scores[label] = float(probabilities[i])
            
            return scores
            
        except Exception as e:
            logger.error(f"TF-IDF similarity classification failed: {e}")
            return {}

class KeywordMatchingClassifier:
    """Zero-shot classification using keyword matching"""
    
    def __init__(self):
        pass
    
    def classify(self, text: str, label_keywords: Dict[str, List[str]]) -> Dict[str, float]:
        """Classify text using keyword matching"""
        text_lower = text.lower()
        scores = {}
        
        for label, keywords in label_keywords.items():
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            
            # Calculate score based on matches and keyword coverage
            if keywords:
                score = matches / len(keywords)
            else:
                score = 0.0
            
            scores[label] = score
        
        # Normalize scores to sum to 1
        total_score = sum(scores.values())
        if total_score > 0:
            scores = {label: score / total_score for label, score in scores.items()}
        else:
            # If no matches, assign equal probability
            num_labels = len(label_keywords)
            scores = {label: 1.0 / num_labels for label in label_keywords.keys()}
        
        return scores

class ZeroShotClassificationPipeline:
    """Main zero-shot classification pipeline"""
    
    def __init__(self, 
                 method: ZeroShotMethod = ZeroShotMethod.HYBRID,
                 confidence_threshold: float = 0.5):
        self.method = method
        self.confidence_threshold = confidence_threshold
        self.transformer_classifier = TransformerZeroShotClassifier()
        self.similarity_classifier = SentenceSimilarityClassifier()
        self.keyword_classifier = KeywordMatchingClassifier()
        self.session = None
        
        logger.info(f"✅ Zero-shot pipeline initialized with {method.value}")
    
    def start_session(self, 
                     labels: List[ZeroShotLabel],
                     session_id: Optional[str] = None) -> ZeroShotSession:
        """Start a new zero-shot classification session"""
        if not session_id:
            session_id = f"zs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.session = ZeroShotSession(
            session_id=session_id,
            method=self.method,
            labels=labels
        )
        
        logger.info(f"Started zero-shot session {session_id} with {len(labels)} labels")
        return self.session
    
    def classify_text(self, text: str) -> ZeroShotPrediction:
        """Classify text using zero-shot learning"""
        if not self.session:
            raise ValueError("No session started. Call start_session() first.")
        
        # Prepare label information
        label_names = [label.label for label in self.session.labels]
        label_descriptions = {
            label.label: label.description or label.label 
            for label in self.session.labels
        }
        label_keywords = {
            label.label: label.keywords 
            for label in self.session.labels
        }
        
        # Get predictions from different methods
        all_scores = {}
        
        if self.method in [ZeroShotMethod.TRANSFORMER_NLI, ZeroShotMethod.HYBRID]:
            transformer_scores = self.transformer_classifier.classify(text, label_names)
            if transformer_scores:
                all_scores['transformer'] = transformer_scores
        
        if self.method in [ZeroShotMethod.SENTENCE_SIMILARITY, ZeroShotMethod.HYBRID]:
            similarity_scores = self.similarity_classifier.classify(text, label_descriptions)
            if similarity_scores:
                all_scores['similarity'] = similarity_scores
        
        if self.method in [ZeroShotMethod.KEYWORD_MATCHING, ZeroShotMethod.HYBRID]:
            keyword_scores = self.keyword_classifier.classify(text, label_keywords)
            if keyword_scores:
                all_scores['keyword'] = keyword_scores
        
        # Combine scores based on method
        if self.method == ZeroShotMethod.HYBRID and len(all_scores) > 1:
            final_scores = self._combine_scores(all_scores)
            method_used = ZeroShotMethod.HYBRID
        elif 'transformer' in all_scores:
            final_scores = all_scores['transformer']
            method_used = ZeroShotMethod.TRANSFORMER_NLI
        elif 'similarity' in all_scores:
            final_scores = all_scores['similarity']
            method_used = ZeroShotMethod.SENTENCE_SIMILARITY
        elif 'keyword' in all_scores:
            final_scores = all_scores['keyword']
            method_used = ZeroShotMethod.KEYWORD_MATCHING
        else:
            # Fallback to uniform distribution
            final_scores = {label: 1.0 / len(label_names) for label in label_names}
            method_used = ZeroShotMethod.KEYWORD_MATCHING
        
        # Get best prediction
        predicted_label = max(final_scores, key=final_scores.get)
        confidence = final_scores[predicted_label]
        
        # Determine confidence threshold
        threshold_met = self._get_confidence_threshold(confidence)
        
        # Generate explanation
        explanation = self._generate_explanation(text, predicted_label, confidence, all_scores)
        
        prediction = ZeroShotPrediction(
            text=text,
            predicted_label=predicted_label,
            confidence=confidence,
            all_scores=final_scores,
            method_used=method_used,
            threshold_met=threshold_met,
            explanation=explanation,
            metadata={
                "method_scores": all_scores,
                "session_id": self.session.session_id
            }
        )
        
        # Update session stats
        self.session.predictions_made += 1
        if confidence >= self.confidence_threshold:
            self.session.high_confidence_predictions += 1
        else:
            self.session.low_confidence_predictions += 1
        
        logger.info(f"Classified text: '{text[:50]}...' -> {predicted_label} ({confidence:.3f})")
        return prediction
    
    def _combine_scores(self, all_scores: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Combine scores from multiple methods"""
        # Weighted combination (can be tuned)
        weights = {
            'transformer': 0.5,
            'similarity': 0.3,
            'keyword': 0.2
        }
        
        combined_scores = {}
        
        # Get all labels
        all_labels = set()
        for scores in all_scores.values():
            all_labels.update(scores.keys())
        
        # Combine weighted scores
        for label in all_labels:
            combined_score = 0.0
            total_weight = 0.0
            
            for method, scores in all_scores.items():
                if label in scores:
                    weight = weights.get(method, 0.1)
                    combined_score += scores[label] * weight
                    total_weight += weight
            
            if total_weight > 0:
                combined_scores[label] = combined_score / total_weight
            else:
                combined_scores[label] = 0.0
        
        return combined_scores
    
    def _get_confidence_threshold(self, confidence: float) -> ConfidenceThreshold:
        """Determine confidence threshold level"""
        if confidence >= ConfidenceThreshold.VERY_HIGH.value:
            return ConfidenceThreshold.VERY_HIGH
        elif confidence >= ConfidenceThreshold.HIGH.value:
            return ConfidenceThreshold.HIGH
        elif confidence >= ConfidenceThreshold.MEDIUM.value:
            return ConfidenceThreshold.MEDIUM
        elif confidence >= ConfidenceThreshold.LOW.value:
            return ConfidenceThreshold.LOW
        else:
            return ConfidenceThreshold.VERY_LOW
    
    def _generate_explanation(self, 
                            text: str, 
                            predicted_label: str, 
                            confidence: float,
                            all_scores: Dict[str, Dict[str, float]]) -> str:
        """Generate explanation for the prediction"""
        explanation_parts = []
        
        explanation_parts.append(f"Predicted '{predicted_label}' with {confidence:.1%} confidence.")
        
        if 'transformer' in all_scores:
            transformer_score = all_scores['transformer'].get(predicted_label, 0.0)
            explanation_parts.append(f"Transformer model: {transformer_score:.1%}")
        
        if 'similarity' in all_scores:
            similarity_score = all_scores['similarity'].get(predicted_label, 0.0)
            explanation_parts.append(f"Semantic similarity: {similarity_score:.1%}")
        
        if 'keyword' in all_scores:
            keyword_score = all_scores['keyword'].get(predicted_label, 0.0)
            explanation_parts.append(f"Keyword matching: {keyword_score:.1%}")
        
        return ". ".join(explanation_parts)
    
    def batch_classify(self, texts: List[str]) -> List[ZeroShotPrediction]:
        """Classify multiple texts"""
        predictions = []
        
        for text in texts:
            prediction = self.classify_text(text)
            predictions.append(prediction)
        
        logger.info(f"Batch classified {len(texts)} texts")
        return predictions
    
    def finalize_session(self) -> Dict[str, Any]:
        """Finalize the zero-shot session"""
        if not self.session:
            raise ValueError("No session to finalize.")
        
        self.session.end_time = datetime.now()
        
        # Calculate performance statistics
        total_time = (self.session.end_time - self.session.start_time).total_seconds()
        high_confidence_rate = (
            self.session.high_confidence_predictions / self.session.predictions_made 
            if self.session.predictions_made > 0 else 0.0
        )
        
        self.session.performance_stats = {
            "total_time": total_time,
            "predictions_per_second": self.session.predictions_made / total_time if total_time > 0 else 0.0,
            "high_confidence_rate": high_confidence_rate,
            "low_confidence_rate": 1.0 - high_confidence_rate
        }
        
        session_summary = {
            "session_id": self.session.session_id,
            "method": self.session.method.value,
            "labels_count": len(self.session.labels),
            "predictions_made": self.session.predictions_made,
            "high_confidence_predictions": self.session.high_confidence_predictions,
            "low_confidence_predictions": self.session.low_confidence_predictions,
            "performance_stats": self.session.performance_stats
        }
        
        logger.info(f"Zero-shot session completed. High confidence rate: {high_confidence_rate:.1%}")
        return session_summary

def integrate_with_production_classifier(production_system, 
                                       text: str,
                                       custom_labels: List[str]) -> Dict[str, Any]:
    """Integrate zero-shot features with production text classification system"""
    
    # Get standard classification
    standard_result = production_system.classify_text(text)
    
    # Prepare zero-shot labels
    zero_shot_labels = [
        ZeroShotLabel(
            label=label,
            description=f"Text that belongs to the {label} category",
            keywords=[]  # Could be populated from domain knowledge
        )
        for label in custom_labels
    ]
    
    # Initialize zero-shot pipeline
    zs_pipeline = ZeroShotClassificationPipeline(method=ZeroShotMethod.HYBRID)
    session = zs_pipeline.start_session(zero_shot_labels)
    
    # Get zero-shot prediction
    zs_prediction = zs_pipeline.classify_text(text)
    
    # Combine results
    enhanced_result = {
        **standard_result,
        "zero_shot_analysis": {
            "predicted_label": zs_prediction.predicted_label,
            "confidence": zs_prediction.confidence,
            "all_scores": zs_prediction.all_scores,
            "method_used": zs_prediction.method_used.value,
            "threshold_met": zs_prediction.threshold_met.value,
            "explanation": zs_prediction.explanation
        },
        "is_zero_shot_enhanced": True,
        "custom_labels_available": custom_labels
    }
    
    return enhanced_result

def main():
    """Demo zero-shot classification features"""
    print("=== Zero-Shot Classification Features Demo ===\n")
    
    # Define custom labels
    labels = [
        ZeroShotLabel(
            label="technology",
            description="Content related to technology, software, hardware, or digital innovations",
            keywords=["software", "hardware", "AI", "machine learning", "computer", "digital", "tech"]
        ),
        ZeroShotLabel(
            label="business",
            description="Content related to business, finance, management, or corporate activities",
            keywords=["revenue", "profit", "management", "strategy", "market", "sales", "business"]
        ),
        ZeroShotLabel(
            label="health",
            description="Content related to health, medicine, wellness, or medical topics",
            keywords=["health", "medical", "doctor", "medicine", "wellness", "fitness", "treatment"]
        ),
        ZeroShotLabel(
            label="education",
            description="Content related to education, learning, teaching, or academic topics",
            keywords=["education", "learning", "teaching", "school", "university", "academic", "study"]
        )
    ]
    
    # Sample texts
    sample_texts = [
        "The new AI model achieved state-of-the-art performance on natural language processing tasks.",
        "The company reported a 15% increase in quarterly revenue driven by strong sales performance.",
        "Regular exercise and a balanced diet are essential for maintaining good cardiovascular health.",
        "The university launched a new online learning platform to enhance student engagement.",
        "Machine learning algorithms are transforming how we analyze big data in various industries."
    ]
    
    # Initialize pipeline
    pipeline = ZeroShotClassificationPipeline(method=ZeroShotMethod.HYBRID)
    session = pipeline.start_session(labels)
    
    print(f"Session ID: {session.session_id}")
    print(f"Labels: {[label.label for label in labels]}")
    print()
    
    # Classify texts
    for i, text in enumerate(sample_texts, 1):
        print(f"Text {i}: {text}")
        prediction = pipeline.classify_text(text)
        
        print(f"  Predicted: {prediction.predicted_label} ({prediction.confidence:.1%})")
        print(f"  Method: {prediction.method_used.value}")
        print(f"  Confidence level: {prediction.threshold_met.value}")
        print(f"  All scores: {', '.join([f'{k}: {v:.2f}' for k, v in prediction.all_scores.items()])}")
        print(f"  Explanation: {prediction.explanation}")
        print()
    
    # Finalize session
    summary = pipeline.finalize_session()
    print("=== Session Summary ===")
    print(f"Total predictions: {summary['predictions_made']}")
    print(f"High confidence: {summary['high_confidence_predictions']}")
    print(f"High confidence rate: {summary['performance_stats']['high_confidence_rate']:.1%}")

if __name__ == "__main__":
    main()