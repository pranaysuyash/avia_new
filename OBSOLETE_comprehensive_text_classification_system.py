#!/usr/bin/env python3
"""
Comprehensive Text Classification System
Task 122: Multi-label classification for content types, domain-specific classification,
custom model training, confidence calibration, and active learning.
"""

import asyncio
import json
import logging
import pickle
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

# Optional imports with fallbacks
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    from transformers import (
        AutoModel, 
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
        pipeline
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline

# Medical schema integration - optional
try:
    from medical_schema_models import (
        MedicalEntity,
        MedicalSpecialty,
        ComplianceRecord,
        ProcessingSession,
        QualityMetrics
    )
    MEDICAL_SCHEMA_AVAILABLE = True
except ImportError:
    MEDICAL_SCHEMA_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextPreprocessor(BaseEstimator, TransformerMixin):
    """Advanced text preprocessing for classification."""
    
    def __init__(self, language='en', remove_stopwords=True, lemmatize=True):
        self.language = language
        self.remove_stopwords = remove_stopwords
        self.lemmatize = lemmatize
        self.nlp = None
        
    def fit(self, X, y=None):
        """Initialize spaCy model if available."""
        if SPACY_AVAILABLE and spacy:
            try:
                if self.language == 'en':
                    self.nlp = spacy.load('en_core_web_sm')
                elif self.language == 'es':
                    self.nlp = spacy.load('es_core_news_sm')
                elif self.language == 'fr':
                    self.nlp = spacy.load('fr_core_news_sm')
                elif self.language == 'de':
                    self.nlp = spacy.load('de_core_news_sm')
                else:
                    self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                logger.warning(f"Could not load spaCy model for {self.language}, using basic preprocessing")
                self.nlp = None
        else:
            logger.info("spaCy not available, using basic preprocessing")
            self.nlp = None
        
        return self
    
    def transform(self, X):
        """Transform text data with advanced preprocessing."""
        if isinstance(X, str):
            X = [X]
        
        processed_texts = []
        for text in X:
            processed = self._preprocess_text(text)
            processed_texts.append(processed)
        
        return processed_texts
    
    def _preprocess_text(self, text):
        """Preprocess individual text."""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.lower().strip()
        
        if self.nlp:
            doc = self.nlp(text)
            tokens = []
            
            for token in doc:
                # Skip punctuation, spaces, and stopwords if requested
                if token.is_punct or token.is_space:
                    continue
                if self.remove_stopwords and token.is_stop:
                    continue
                    
                # Use lemma if lemmatization is enabled
                if self.lemmatize and token.lemma_ != '-PRON-':
                    tokens.append(token.lemma_)
                else:
                    tokens.append(token.text)
            
            return ' '.join(tokens)
        else:
            # Basic preprocessing without spaCy
            import re
            text = re.sub(r'[^\w\s]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            return text


class ContentTypeClassifier:
    """Multi-label classifier for different content types."""
    
    def __init__(self):
        self.content_types = [
            'educational', 'promotional', 'entertainment', 'training',
            'news', 'interview', 'presentation', 'meeting', 'lecture',
            'podcast', 'webinar', 'discussion', 'announcement'
        ]
        self.model = None
        self.vectorizer = None
        self.preprocessor = None
        
    def build_model(self):
        """Build the content type classification pipeline."""
        self.preprocessor = TextPreprocessor()
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
        # Multi-label classifier
        base_classifier = LogisticRegression(
            random_state=42,
            max_iter=1000
        )
        self.model = OneVsRestClassifier(base_classifier)
        
        return self
    
    def train(self, texts: List[str], labels: List[List[str]]):
        """Train the content type classifier."""
        if not self.model:
            self.build_model()
        
        # Preprocess texts
        processed_texts = self.preprocessor.fit_transform(texts)
        
        # Vectorize
        X = self.vectorizer.fit_transform(processed_texts)
        
        # Convert multi-label format
        from sklearn.preprocessing import MultiLabelBinarizer
        self.mlb = MultiLabelBinarizer(classes=self.content_types)
        y = self.mlb.fit_transform(labels)
        
        # Train model
        self.model.fit(X, y)
        
        return self
    
    def predict(self, texts: List[str], threshold: float = 0.5) -> List[Dict[str, float]]:
        """Predict content types with confidence scores."""
        if not self.model:
            raise ValueError("Model not trained")
        
        # Preprocess and vectorize
        processed_texts = self.preprocessor.transform(texts)
        X = self.vectorizer.transform(processed_texts)
        
        # Get probabilities
        probabilities = self.model.predict_proba(X)
        
        results = []
        for i, probs in enumerate(probabilities):
            content_scores = {}
            for j, content_type in enumerate(self.content_types):
                if hasattr(probs, '__len__') and len(probs) > j:
                    content_scores[content_type] = float(probs[j])
                else:
                    content_scores[content_type] = 0.0
            
            # Filter by threshold
            filtered_scores = {
                k: v for k, v in content_scores.items() 
                if v >= threshold
            }
            
            results.append(filtered_scores if filtered_scores else content_scores)
        
        return results


class DomainSpecificClassifier:
    """Domain-specific classification for medical, legal, technical content."""
    
    def __init__(self):
        self.domains = {
            'medical': [
                'clinical', 'pharmaceutical', 'diagnostic', 'therapeutic',
                'surgical', 'medical_research', 'patient_care'
            ],
            'legal': [
                'contract', 'litigation', 'regulatory', 'intellectual_property',
                'corporate', 'criminal', 'civil'
            ],
            'technical': [
                'software', 'engineering', 'scientific', 'manufacturing',
                'research_development', 'technical_support'
            ],
            'business': [
                'finance', 'marketing', 'sales', 'operations',
                'strategy', 'human_resources', 'customer_service'
            ]
        }
        
        self.models = {}
        self.vectorizers = {}
        self.preprocessors = {}
        
    def build_domain_model(self, domain: str):
        """Build classifier for specific domain."""
        if domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}")
        
        self.preprocessors[domain] = TextPreprocessor()
        self.vectorizers[domain] = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        # Use calibrated classifier for confidence scores
        base_classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )
        self.models[domain] = CalibratedClassifierCV(
            base_classifier, 
            cv=3, 
            method='isotonic'
        )
        
        return self
    
    def train_domain(self, domain: str, texts: List[str], labels: List[str]):
        """Train classifier for specific domain."""
        if domain not in self.models:
            self.build_domain_model(domain)
        
        # Preprocess texts
        processed_texts = self.preprocessors[domain].fit_transform(texts)
        
        # Vectorize
        X = self.vectorizers[domain].fit_transform(processed_texts)
        
        # Train model
        self.models[domain].fit(X, labels)
        
        return self
    
    def predict_domain(self, domain: str, texts: List[str]) -> List[Dict[str, float]]:
        """Predict domain-specific classifications."""
        if domain not in self.models:
            raise ValueError(f"Model for domain {domain} not trained")
        
        # Preprocess and vectorize
        processed_texts = self.preprocessors[domain].transform(texts)
        X = self.vectorizers[domain].transform(processed_texts)
        
        # Get predictions and probabilities
        predictions = self.models[domain].predict(X)
        probabilities = self.models[domain].predict_proba(X)
        
        results = []
        classes = self.models[domain].classes_
        
        for i, (pred, probs) in enumerate(zip(predictions, probabilities)):
            class_scores = {}
            for j, class_name in enumerate(classes):
                class_scores[class_name] = float(probs[i][j])
            
            results.append({
                'predicted_class': pred,
                'confidence': float(max(probs[i])),
                'all_scores': class_scores
            })
        
        return results


class TransformerClassifier:
    """Transformer-based classification with Hugging Face models."""
    
    def __init__(self, model_name: str = 'distilbert-base-uncased'):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        
        if TORCH_AVAILABLE and torch:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = 'cpu'
            logger.warning("PyTorch not available, transformer features disabled")
        
    def initialize_model(self, num_labels: int):
        """Initialize transformer model and tokenizer."""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers library not available")
        
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=num_labels
        ).to(self.device)
        
        return self
    
    def train_transformer(self, texts: List[str], labels: List[int], 
                         validation_split: float = 0.2):
        """Train transformer model."""
        if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE:
            raise ImportError("Required libraries (transformers, torch) not available")
        
        if not self.model:
            num_labels = len(set(labels))
            self.initialize_model(num_labels)
        
        # Prepare data
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=validation_split, random_state=42
        )
        
        train_encodings = self.tokenizer(
            train_texts, truncation=True, padding=True, max_length=512
        )
        val_encodings = self.tokenizer(
            val_texts, truncation=True, padding=True, max_length=512
        )
        
        # Create dataset
        class ClassificationDataset(torch.utils.data.Dataset):
            def __init__(self, encodings, labels):
                self.encodings = encodings
                self.labels = labels
            
            def __getitem__(self, idx):
                item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
                item['labels'] = torch.tensor(self.labels[idx])
                return item
            
            def __len__(self):
                return len(self.labels)
        
        train_dataset = ClassificationDataset(train_encodings, train_labels)
        val_dataset = ClassificationDataset(val_encodings, val_labels)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir='./results',
            num_train_epochs=3,
            per_device_train_batch_size=16,
            per_device_eval_batch_size=64,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='./logs',
            evaluation_strategy='steps',
            eval_steps=500,
            save_strategy='steps',
            save_steps=1000,
            load_best_model_at_end=True,
        )
        
        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
        )
        
        # Train
        trainer.train()
        
        return self
    
    def predict_transformer(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Predict using transformer model."""
        if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE:
            raise ImportError("Required libraries (transformers, torch) not available")
        
        if not self.model:
            raise ValueError("Model not initialized")
        
        # Tokenize inputs
        encodings = self.tokenizer(
            texts, truncation=True, padding=True, max_length=512, return_tensors='pt'
        ).to(self.device)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(**encodings)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        results = []
        for i, pred in enumerate(predictions):
            probs = pred.cpu().numpy()
            predicted_class = int(np.argmax(probs))
            confidence = float(np.max(probs))
            
            results.append({
                'predicted_class': predicted_class,
                'confidence': confidence,
                'probabilities': probs.tolist()
            })
        
        return results


class ActiveLearningSystem:
    """Active learning for classification improvement."""
    
    def __init__(self, classifier):
        self.classifier = classifier
        self.uncertainty_samples = []
        self.labeled_pool = []
        self.unlabeled_pool = []
        
    def uncertainty_sampling(self, texts: List[str], n_samples: int = 10) -> List[int]:
        """Select most uncertain samples for labeling."""
        predictions = self.classifier.predict(texts)
        
        uncertainties = []
        for pred in predictions:
            if isinstance(pred, dict) and 'confidence' in pred:
                # Lower confidence = higher uncertainty
                uncertainty = 1.0 - pred['confidence']
            else:
                # For multi-label predictions, use entropy
                probs = list(pred.values()) if isinstance(pred, dict) else [0.5]
                entropy = -sum(p * np.log(p + 1e-10) for p in probs if p > 0)
                uncertainty = entropy
            
            uncertainties.append(uncertainty)
        
        # Get indices of most uncertain samples
        uncertain_indices = np.argsort(uncertainties)[-n_samples:]
        
        return uncertain_indices.tolist()
    
    def diversity_sampling(self, texts: List[str], n_samples: int = 10) -> List[int]:
        """Select diverse samples for labeling."""
        # Simple diversity sampling based on text length and vocabulary
        features = []
        for text in texts:
            words = text.split()
            features.append([
                len(text),  # Character length
                len(words),  # Word count
                len(set(words)),  # Unique words
                sum(len(word) for word in words) / max(len(words), 1)  # Avg word length
            ])
        
        features = np.array(features)
        
        # Use k-means clustering for diversity
        from sklearn.cluster import KMeans
        
        if n_samples >= len(texts):
            return list(range(len(texts)))
        
        kmeans = KMeans(n_clusters=n_samples, random_state=42)
        clusters = kmeans.fit_predict(features)
        
        # Select one sample from each cluster (closest to centroid)
        selected_indices = []
        for i in range(n_samples):
            cluster_indices = np.where(clusters == i)[0]
            if len(cluster_indices) > 0:
                centroid = kmeans.cluster_centers_[i]
                distances = [
                    np.linalg.norm(features[idx] - centroid) 
                    for idx in cluster_indices
                ]
                best_idx = cluster_indices[np.argmin(distances)]
                selected_indices.append(best_idx)
        
        return selected_indices
    
    def combined_sampling(self, texts: List[str], n_samples: int = 10) -> List[int]:
        """Combine uncertainty and diversity sampling."""
        n_uncertain = n_samples // 2
        n_diverse = n_samples - n_uncertain
        
        uncertain_indices = self.uncertainty_sampling(texts, n_uncertain)
        diverse_indices = self.diversity_sampling(texts, n_diverse)
        
        # Combine and remove duplicates
        combined_indices = list(set(uncertain_indices + diverse_indices))
        
        # If we need more samples, add random ones
        if len(combined_indices) < n_samples:
            remaining = n_samples - len(combined_indices)
            available_indices = set(range(len(texts))) - set(combined_indices)
            additional_indices = np.random.choice(
                list(available_indices), 
                min(remaining, len(available_indices)),
                replace=False
            )
            combined_indices.extend(additional_indices.tolist())
        
        return combined_indices[:n_samples]


class ComprehensiveTextClassificationSystem:
    """Main system integrating all classification capabilities."""
    
    def __init__(self, db_path: str = "text_classification.db"):
        self.db_path = db_path
        self.content_classifier = ContentTypeClassifier()
        self.domain_classifier = DomainSpecificClassifier()
        self.transformer_classifier = TransformerClassifier()
        self.active_learning = None
        self.medical_schema = {}
        
        self._initialize_database()
        self._initialize_medical_integration()
    
    def _initialize_database(self):
        """Initialize SQLite database for classification data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS classification_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text_hash TEXT NOT NULL,
                    text_content TEXT NOT NULL,
                    content_types TEXT,
                    domain_classification TEXT,
                    confidence_scores TEXT,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text_content TEXT NOT NULL,
                    labels TEXT,
                    domain TEXT,
                    source TEXT,
                    validated BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_type TEXT NOT NULL,
                    domain TEXT,
                    accuracy REAL,
                    precision_scores TEXT,
                    recall_scores TEXT,
                    f1_scores TEXT,
                    confusion_matrix TEXT,
                    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    def _initialize_medical_integration(self):
        """Initialize medical schema integration."""
        self.medical_schema = {
            'specialties': [
                'cardiology', 'neurology', 'oncology', 'pediatrics',
                'surgery', 'radiology', 'pathology', 'psychiatry'
            ],
            'document_types': [
                'clinical_note', 'discharge_summary', 'operative_report',
                'pathology_report', 'radiology_report', 'consultation'
            ],
            'urgency_levels': ['routine', 'urgent', 'stat', 'critical']
        }
    
    async def classify_text(self, text: str, include_domains: List[str] = None) -> Dict[str, Any]:
        """Comprehensive text classification."""
        if not text or not text.strip():
            return {'error': 'Empty text provided'}
        
        results = {
            'text_hash': hash(text),
            'timestamp': datetime.now().isoformat(),
            'classifications': {}
        }
        
        try:
            # Content type classification
            content_types = self.content_classifier.predict([text])
            results['classifications']['content_types'] = content_types[0] if content_types else {}
            
            # Domain-specific classifications
            if include_domains:
                results['classifications']['domains'] = {}
                for domain in include_domains:
                    if domain in self.domain_classifier.models:
                        domain_results = self.domain_classifier.predict_domain(domain, [text])
                        results['classifications']['domains'][domain] = domain_results[0] if domain_results else {}
            
            # Medical classification if medical content is detected
            content_scores = results['classifications']['content_types']
            if any(score > 0.3 for key, score in content_scores.items() 
                   if 'medical' in key.lower() or 'clinical' in key.lower()):
                results['classifications']['medical'] = await self._classify_medical_content(text)
            
            # Store results
            self._store_classification_results(text, results)
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            results['error'] = str(e)
        
        return results
    
    async def _classify_medical_content(self, text: str) -> Dict[str, Any]:
        """Medical-specific classification with HIPAA compliance."""
        medical_results = {
            'specialty': 'general',
            'document_type': 'clinical_note',
            'urgency': 'routine',
            'phi_detected': False,
            'compliance_score': 1.0
        }
        
        try:
            # Simple keyword-based medical classification
            text_lower = text.lower()
            
            # Specialty detection
            for specialty in self.medical_schema['specialties']:
                if specialty in text_lower:
                    medical_results['specialty'] = specialty
                    break
            
            # Document type detection
            for doc_type in self.medical_schema['document_types']:
                type_keywords = doc_type.replace('_', ' ')
                if type_keywords in text_lower:
                    medical_results['document_type'] = doc_type
                    break
            
            # Urgency detection
            urgent_keywords = ['urgent', 'stat', 'emergency', 'critical', 'immediate']
            if any(keyword in text_lower for keyword in urgent_keywords):
                if 'stat' in text_lower or 'critical' in text_lower:
                    medical_results['urgency'] = 'critical'
                elif 'emergency' in text_lower:
                    medical_results['urgency'] = 'stat'
                else:
                    medical_results['urgency'] = 'urgent'
            
            # Basic PHI detection
            phi_patterns = ['ssn', 'social security', 'date of birth', 'dob', 'phone number']
            medical_results['phi_detected'] = any(pattern in text_lower for pattern in phi_patterns)
            
            if medical_results['phi_detected']:
                medical_results['compliance_score'] = 0.5
            
        except Exception as e:
            logger.error(f"Medical classification error: {e}")
        
        return medical_results
    
    def _store_classification_results(self, text: str, results: Dict[str, Any]):
        """Store classification results in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO classification_results 
                    (text_hash, text_content, content_types, domain_classification, confidence_scores, model_version)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    str(results.get('text_hash', '')),
                    text[:1000],  # Truncate for storage
                    json.dumps(results['classifications'].get('content_types', {})),
                    json.dumps(results['classifications'].get('domains', {})),
                    json.dumps({k: v for k, v in results['classifications'].items() if 'confidence' in str(v)}),
                    'v1.0'
                ))
        except Exception as e:
            logger.error(f"Database storage error: {e}")
    
    def train_content_classifier(self, training_data: List[Tuple[str, List[str]]]):
        """Train the content type classifier."""
        texts, labels = zip(*training_data) if training_data else ([], [])
        
        try:
            self.content_classifier.train(list(texts), list(labels))
            logger.info("Content classifier trained successfully")
        except Exception as e:
            logger.error(f"Content classifier training error: {e}")
    
    def train_domain_classifier(self, domain: str, training_data: List[Tuple[str, str]]):
        """Train domain-specific classifier."""
        texts, labels = zip(*training_data) if training_data else ([], [])
        
        try:
            self.domain_classifier.train_domain(domain, list(texts), list(labels))
            logger.info(f"Domain classifier for {domain} trained successfully")
        except Exception as e:
            logger.error(f"Domain classifier training error for {domain}: {e}")
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification system statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total classifications
                cursor.execute("SELECT COUNT(*) FROM classification_results")
                total_classifications = cursor.fetchone()[0]
                
                # Classifications by date
                cursor.execute('''
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM classification_results
                    WHERE created_at >= datetime('now', '-30 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                ''')
                daily_stats = cursor.fetchall()
                
                # Most common content types
                cursor.execute('''
                    SELECT content_types, COUNT(*) as count
                    FROM classification_results
                    WHERE content_types IS NOT NULL AND content_types != '{}'
                    GROUP BY content_types
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                common_types = cursor.fetchall()
                
                return {
                    'total_classifications': total_classifications,
                    'daily_stats': daily_stats,
                    'common_content_types': common_types,
                    'models_trained': {
                        'content_classifier': self.content_classifier.model is not None,
                        'domain_classifiers': list(self.domain_classifier.models.keys()),
                        'transformer_model': self.transformer_classifier.model is not None
                    }
                }
        except Exception as e:
            logger.error(f"Stats retrieval error: {e}")
            return {'error': str(e)}
    
    async def batch_classify(self, texts: List[str], batch_size: int = 10) -> List[Dict[str, Any]]:
        """Classify multiple texts in batches."""
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = []
            
            for text in batch:
                result = await self.classify_text(text)
                batch_results.append(result)
            
            results.extend(batch_results)
            
            # Small delay to prevent overwhelming the system
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return results
    
    def export_training_data(self, domain: str = None) -> List[Dict[str, Any]]:
        """Export training data for analysis or transfer."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM training_data"
                params = ()
                
                if domain:
                    query += " WHERE domain = ?"
                    params = (domain,)
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Export error: {e}")
            return []
    
    def cleanup_old_data(self, days_old: int = 90):
        """Clean up old classification results."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    DELETE FROM classification_results
                    WHERE created_at < datetime('now', '-{} days')
                '''.format(days_old))
                
                deleted_count = conn.total_changes
                logger.info(f"Cleaned up {deleted_count} old classification results")
                
                return deleted_count
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return 0


# Example usage and testing
async def main():
    """Example usage of the comprehensive text classification system."""
    
    # Initialize system
    classifier_system = ComprehensiveTextClassificationSystem()
    
    # Example texts for classification
    test_texts = [
        "This is a clinical note documenting the patient's cardiology consultation regarding chest pain and arrhythmia.",
        "Welcome to our exciting new product launch webinar where we'll demonstrate cutting-edge features.",
        "Today's lecture covers advanced machine learning algorithms and their applications in natural language processing.",
        "The legal contract outlines the terms and conditions for intellectual property licensing agreements.",
        "This technical documentation explains the software architecture and implementation details for developers."
    ]
    
    print("🔍 Comprehensive Text Classification System Demo")
    print("=" * 60)
    
    # Classify each text
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 Text {i}: {text[:100]}...")
        
        result = await classifier_system.classify_text(text)
        
        if 'error' not in result:
            print(f"📊 Classifications:")
            
            # Content types
            content_types = result['classifications'].get('content_types', {})
            if content_types:
                print(f"  Content Types:")
                for content_type, score in content_types.items():
                    if score > 0.1:  # Only show significant scores
                        print(f"    - {content_type}: {score:.3f}")
            
            # Medical classification if present
            medical = result['classifications'].get('medical')
            if medical:
                print(f"  Medical Classification:")
                print(f"    - Specialty: {medical.get('specialty', 'N/A')}")
                print(f"    - Document Type: {medical.get('document_type', 'N/A')}")
                print(f"    - Urgency: {medical.get('urgency', 'N/A')}")
                print(f"    - PHI Detected: {medical.get('phi_detected', False)}")
                print(f"    - Compliance Score: {medical.get('compliance_score', 1.0):.2f}")
        else:
            print(f"❌ Error: {result['error']}")
    
    # Get system statistics
    print(f"\n📈 System Statistics:")
    stats = classifier_system.get_classification_stats()
    print(f"  Total Classifications: {stats.get('total_classifications', 0)}")
    print(f"  Models Trained: {stats.get('models_trained', {})}")
    
    print(f"\n✅ Classification system demo completed!")


if __name__ == "__main__":
    asyncio.run(main())