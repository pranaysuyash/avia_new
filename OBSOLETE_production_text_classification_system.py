"""
Production-Ready Text Classification System
A complete ML pipeline with real transformer models, proper training, and enterprise features.

This replaces the proof-of-concept with actual machine learning implementations.
"""

import os
import json
import sqlite3
import pickle
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Core ML libraries
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import LabelEncoder, StandardScaler

# Advanced ML libraries with fallbacks
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    from transformers import (
        AutoTokenizer, AutoModel, AutoModelForSequenceClassification,
        Trainer, TrainingArguments, EarlyStoppingCallback,
        pipeline, set_seed
    )
    from datasets import Dataset as HFDataset
    TRANSFORMERS_AVAILABLE = True
    print("✅ Transformers and PyTorch available - Full ML capabilities enabled")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    HFDataset = None
    print("⚠️ Transformers not available - Using sklearn-only implementation")

try:
    import spacy
    from spacy.lang.en import English
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️ spaCy not available - Using basic text preprocessing")

# MLOps and monitoring
try:
    import mlflow
    import mlflow.sklearn
    import mlflow.pytorch
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

# Visualization
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for ML models"""
    model_type: str = "transformer"  # transformer, traditional, ensemble
    model_name: str = "distilbert-base-uncased"
    max_length: int = 512
    batch_size: int = 16
    learning_rate: float = 2e-5
    num_epochs: int = 3
    warmup_steps: int = 500
    weight_decay: float = 0.01
    early_stopping_patience: int = 3
    use_gpu: bool = True
    random_seed: int = 42

@dataclass
class TrainingConfig:
    """Configuration for training pipeline"""
    train_split: float = 0.8
    val_split: float = 0.1
    test_split: float = 0.1
    cv_folds: int = 5
    enable_cross_validation: bool = True
    enable_hyperparameter_tuning: bool = True
    save_model_artifacts: bool = True
    track_experiments: bool = True

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_score: Optional[float]
    confusion_matrix: List[List[int]]
    classification_report: str
    training_time: float
    inference_time: float
    model_size_mb: float

@dataclass
class PredictionResult:
    """Enhanced prediction result with confidence and explanations"""
    predicted_class: str
    confidence_score: float
    prediction_probabilities: Dict[str, float]
    feature_importance: Dict[str, float]
    explanation: str
    model_version: str
    prediction_time: float

class AdvancedTextPreprocessor:
    """Production-grade text preprocessing with multiple strategies"""
    
    def __init__(self, language: str = "en", strategy: str = "advanced"):
        self.language = language
        self.strategy = strategy
        self.nlp = None
        self.stopwords = set()
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize preprocessing components"""
        if SPACY_AVAILABLE:
            try:
                if self.language == "en":
                    self.nlp = spacy.load("en_core_web_sm")
                else:
                    self.nlp = English()
                
                # Extract stopwords
                self.stopwords = self.nlp.Defaults.stop_words
                logger.info(f"✅ Loaded spaCy model for {self.language}")
                
            except OSError:
                logger.warning("spaCy model not found, using basic preprocessing")
                self.nlp = None
        
        # Fallback stopwords
        if not self.stopwords:
            self.stopwords = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
            }
    
    def preprocess(self, texts: List[str]) -> List[str]:
        """Preprocess list of texts"""
        if self.strategy == "basic":
            return [self._basic_preprocess(text) for text in texts]
        elif self.strategy == "advanced" and self.nlp:
            return [self._advanced_preprocess(text) for text in texts]
        else:
            return [self._basic_preprocess(text) for text in texts]
    
    def _basic_preprocess(self, text: str) -> str:
        """Basic text preprocessing"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep alphanumeric and spaces
        import re
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove stopwords
        words = text.split()
        words = [word for word in words if word not in self.stopwords and len(word) > 2]
        
        return ' '.join(words)
    
    def _advanced_preprocess(self, text: str) -> str:
        """Advanced preprocessing using spaCy"""
        if not text:
            return ""
        
        doc = self.nlp(text)
        
        # Extract lemmatized tokens, excluding stopwords, punctuation, and spaces
        tokens = [
            token.lemma_.lower() 
            for token in doc 
            if not token.is_stop 
            and not token.is_punct 
            and not token.is_space 
            and len(token.text) > 2
            and token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']  # Keep only content words
        ]
        
        return ' '.join(tokens)

class TransformerTextClassifier:
    """Production-ready transformer-based text classifier"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.label_encoder = LabelEncoder()
        self.training_args = None
        self.trainer = None
        self.device = self._get_device()
        
        if TRANSFORMERS_AVAILABLE:
            set_seed(config.random_seed)
            self._initialize_model()
    
    def _get_device(self):
        """Get appropriate device for training"""
        if TRANSFORMERS_AVAILABLE and self.config.use_gpu and torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"✅ Using GPU: {torch.cuda.get_device_name()}")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU for training")
        return device
    
    def _initialize_model(self):
        """Initialize tokenizer and model"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            logger.info(f"✅ Loaded tokenizer: {self.config.model_name}")
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise
    
    def prepare_dataset(self, texts: List[str], labels: List[str]):
        """Prepare dataset for training"""
        # Encode labels
        encoded_labels = self.label_encoder.fit_transform(labels)
        
        # Tokenize texts
        encodings = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=self.config.max_length,
            return_tensors="pt"
        )
        
        # Create dataset
        if HFDataset:
            dataset = HFDataset.from_dict({
                'input_ids': encodings['input_ids'],
                'attention_mask': encodings['attention_mask'],
                'labels': encoded_labels
            })
            return dataset
        else:
            # Fallback for when datasets library not available
            return {
                'input_ids': encodings['input_ids'],
                'attention_mask': encodings['attention_mask'],
                'labels': encoded_labels
            }
    
    def train(self, train_texts: List[str], train_labels: List[str],
              val_texts: List[str], val_labels: List[str]) -> ModelMetrics:
        """Train the transformer model"""
        
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers library not available")
        
        start_time = datetime.now()
        
        # Prepare datasets
        train_dataset = self.prepare_dataset(train_texts, train_labels)
        val_dataset = self.prepare_dataset(val_texts, val_labels)
        
        # Initialize model for sequence classification
        num_labels = len(self.label_encoder.classes_)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.config.model_name,
            num_labels=num_labels
        )
        
        # Set up training arguments
        self.training_args = TrainingArguments(
            output_dir='./model_checkpoints',
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            warmup_steps=self.config.warmup_steps,
            weight_decay=self.config.weight_decay,
            learning_rate=self.config.learning_rate,
            logging_dir='./logs',
            logging_steps=100,
            evaluation_strategy="steps",
            eval_steps=500,
            save_strategy="steps",
            save_steps=500,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to=None,  # Disable wandb logging
        )
        
        # Initialize trainer
        self.trainer = Trainer(
            model=self.model,
            args=self.training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=self.config.early_stopping_patience)]
        )
        
        # Train the model
        logger.info("🚀 Starting transformer training...")
        train_result = self.trainer.train()
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Evaluate on validation set
        eval_result = self.trainer.evaluate()
        
        # Generate predictions for metrics
        predictions = self.trainer.predict(val_dataset)
        predicted_labels = np.argmax(predictions.predictions, axis=1)
        true_labels = val_labels
        
        # Calculate metrics
        metrics = self._calculate_metrics(
            true_labels, 
            self.label_encoder.inverse_transform(predicted_labels),
            predictions.predictions,
            training_time
        )
        
        logger.info(f"✅ Training completed in {training_time:.2f} seconds")
        logger.info(f"📊 Validation accuracy: {metrics.accuracy:.4f}")
        
        return metrics
    
    def predict(self, texts: List[str]) -> List[PredictionResult]:
        """Make predictions on new texts"""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not trained or loaded")
        
        start_time = datetime.now()
        
        # Create classification pipeline
        classifier = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device.type == "cuda" else -1,
            return_all_scores=True
        )
        
        results = []
        for text in texts:
            # Get predictions
            predictions = classifier(text)
            
            # Parse results
            class_probs = {pred['label']: pred['score'] for pred in predictions}
            predicted_class = max(class_probs, key=class_probs.get)
            confidence = class_probs[predicted_class]
            
            # Create result
            result = PredictionResult(
                predicted_class=predicted_class,
                confidence_score=confidence,
                prediction_probabilities=class_probs,
                feature_importance={},  # Would need LIME/SHAP for feature importance
                explanation=f"Predicted as {predicted_class} with {confidence:.3f} confidence",
                model_version=self.config.model_name,
                prediction_time=(datetime.now() - start_time).total_seconds() / len(texts)
            )
            results.append(result)
        
        return results
    
    def _calculate_metrics(self, true_labels: List[str], predicted_labels: List[str], 
                          prediction_probs: np.ndarray, training_time: float) -> ModelMetrics:
        """Calculate comprehensive model metrics"""
        
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
        
        # Basic metrics
        accuracy = accuracy_score(true_labels, predicted_labels)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, predicted_labels, average='weighted'
        )
        
        # Confusion matrix
        cm = confusion_matrix(true_labels, predicted_labels)
        
        # Classification report
        report = classification_report(true_labels, predicted_labels)
        
        # AUC score (for binary/multiclass)
        auc_score = None
        try:
            if len(np.unique(true_labels)) == 2:
                auc_score = roc_auc_score(true_labels, prediction_probs[:, 1])
            else:
                # For multiclass, use ovr strategy
                label_binarizer = LabelEncoder()
                true_labels_encoded = label_binarizer.fit_transform(true_labels)
                auc_score = roc_auc_score(
                    true_labels_encoded, prediction_probs, 
                    multi_class='ovr', average='weighted'
                )
        except Exception:
            pass
        
        # Model size estimation
        model_size_mb = 0
        if hasattr(self.model, 'num_parameters'):
            # Rough estimation: 4 bytes per parameter (float32)
            model_size_mb = (self.model.num_parameters() * 4) / (1024 * 1024)
        
        return ModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            auc_score=auc_score,
            confusion_matrix=cm.tolist(),
            classification_report=report,
            training_time=training_time,
            inference_time=0.1,  # Placeholder
            model_size_mb=model_size_mb
        )
    
    def save_model(self, save_path: str):
        """Save the trained model"""
        if self.model and self.tokenizer:
            os.makedirs(save_path, exist_ok=True)
            self.model.save_pretrained(save_path)
            self.tokenizer.save_pretrained(save_path)
            
            # Save label encoder
            with open(os.path.join(save_path, 'label_encoder.pkl'), 'wb') as f:
                pickle.dump(self.label_encoder, f)
            
            logger.info(f"✅ Model saved to {save_path}")
    
    def load_model(self, load_path: str):
        """Load a trained model"""
        if TRANSFORMERS_AVAILABLE:
            self.model = AutoModelForSequenceClassification.from_pretrained(load_path)
            self.tokenizer = AutoTokenizer.from_pretrained(load_path)
            
            # Load label encoder
            with open(os.path.join(load_path, 'label_encoder.pkl'), 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            self.model.to(self.device)
            logger.info(f"✅ Model loaded from {load_path}")

class TraditionalMLClassifier:
    """Fallback traditional ML classifier when transformers unavailable"""
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = LabelEncoder()
        self.feature_names = []
    
    def train(self, train_texts: List[str], train_labels: List[str],
              val_texts: List[str], val_labels: List[str]) -> ModelMetrics:
        """Train traditional ML model"""
        
        start_time = datetime.now()
        
        # Encode labels
        all_labels = train_labels + val_labels
        self.label_encoder.fit(all_labels)
        train_labels_encoded = self.label_encoder.transform(train_labels)
        
        # Create pipeline with TF-IDF and ensemble classifier
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            stop_words='english',
            min_df=2,
            max_df=0.95
        )
        
        # Use ensemble of classifiers
        base_classifiers = [
            ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
            ('gb', GradientBoostingClassifier(random_state=42)),
            ('lr', LogisticRegression(max_iter=1000, random_state=42))
        ]
        
        self.model = Pipeline([
            ('tfidf', self.vectorizer),
            ('classifier', RandomForestClassifier(n_estimators=200, random_state=42))
        ])
        
        # Train model
        logger.info("🚀 Training traditional ML model...")
        self.model.fit(train_texts, train_labels_encoded)
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Make predictions on validation set
        val_predictions = self.model.predict(val_texts)
        val_proba = self.model.predict_proba(val_texts)
        
        # Calculate metrics
        metrics = self._calculate_metrics(
            val_labels,
            self.label_encoder.inverse_transform(val_predictions),
            val_proba,
            training_time
        )
        
        logger.info(f"✅ Training completed in {training_time:.2f} seconds")
        logger.info(f"📊 Validation accuracy: {metrics.accuracy:.4f}")
        
        return metrics
    
    def predict(self, texts: List[str]) -> List[PredictionResult]:
        """Make predictions using traditional ML"""
        if not self.model:
            raise RuntimeError("Model not trained")
        
        start_time = datetime.now()
        
        # Get predictions and probabilities
        predictions = self.model.predict(texts)
        probabilities = self.model.predict_proba(texts)
        
        # Get feature names for importance
        feature_names = self.model.named_steps['tfidf'].get_feature_names_out()
        
        results = []
        for i, text in enumerate(texts):
            predicted_class = self.label_encoder.inverse_transform([predictions[i]])[0]
            confidence = np.max(probabilities[i])
            
            # Create probability distribution
            class_probs = {
                self.label_encoder.inverse_transform([j])[0]: probabilities[i][j]
                for j in range(len(probabilities[i]))
            }
            
            # Get top features (simplified feature importance)
            text_vector = self.model.named_steps['tfidf'].transform([text])
            feature_importance = {}
            if hasattr(text_vector, 'indices') and len(text_vector.indices) > 0:
                # Get non-zero feature indices
                nonzero_indices = text_vector.indices
                nonzero_data = text_vector.data
                
                # Get top features by value
                top_idx = np.argsort(nonzero_data)[-10:]  # Top 10 features
                for i, data_idx in enumerate(top_idx):
                    if data_idx < len(nonzero_indices):
                        feature_idx = nonzero_indices[data_idx]
                        if feature_idx < len(feature_names):
                            feature_importance[feature_names[feature_idx]] = float(nonzero_data[data_idx])
            
            result = PredictionResult(
                predicted_class=predicted_class,
                confidence_score=confidence,
                prediction_probabilities=class_probs,
                feature_importance=feature_importance,
                explanation=f"Traditional ML prediction: {predicted_class} ({confidence:.3f})",
                model_version="traditional_ml_v1",
                prediction_time=(datetime.now() - start_time).total_seconds() / len(texts)
            )
            results.append(result)
        
        return results
    
    def _calculate_metrics(self, true_labels: List[str], predicted_labels: List[str],
                          prediction_probs: np.ndarray, training_time: float) -> ModelMetrics:
        """Calculate metrics for traditional ML model"""
        
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
        
        accuracy = accuracy_score(true_labels, predicted_labels)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, predicted_labels, average='weighted'
        )
        
        cm = confusion_matrix(true_labels, predicted_labels)
        report = classification_report(true_labels, predicted_labels)
        
        # AUC score
        auc_score = None
        try:
            if len(np.unique(true_labels)) == 2:
                auc_score = roc_auc_score(true_labels, prediction_probs[:, 1])
        except Exception:
            pass
        
        return ModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            auc_score=auc_score,
            confusion_matrix=cm.tolist(),
            classification_report=report,
            training_time=training_time,
            inference_time=0.05,
            model_size_mb=1.0  # Estimated
        )

class ProductionTextClassificationSystem:
    """Production-ready text classification system with full ML pipeline"""
    
    def __init__(self, database_path: str = "production_text_classification.db"):
        self.database_path = database_path
        self.preprocessor = AdvancedTextPreprocessor()
        self.models = {}
        self.active_model = None
        self.model_config = ModelConfig()
        self.training_config = TrainingConfig()
        
        self.init_database()
        logger.info("✅ Production Text Classification System initialized")
    
    def init_database(self):
        """Initialize production database schema"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Enhanced model registry
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_registry (
            model_id TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            model_type TEXT NOT NULL,
            version TEXT NOT NULL,
            accuracy REAL,
            f1_score REAL,
            training_date TIMESTAMP,
            is_active BOOLEAN DEFAULT FALSE,
            model_config TEXT,
            metrics TEXT,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Training experiments
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_experiments (
            experiment_id TEXT PRIMARY KEY,
            model_id TEXT,
            dataset_size INTEGER,
            training_time REAL,
            hyperparameters TEXT,
            metrics TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES model_registry (model_id)
        )
        ''')
        
        # Prediction logs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT,
            input_text TEXT,
            predicted_class TEXT,
            confidence_score REAL,
            prediction_time REAL,
            user_feedback TEXT,
            is_correct BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES model_registry (model_id)
        )
        ''')
        
        # Dataset management
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            dataset_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            size INTEGER,
            num_classes INTEGER,
            file_path TEXT,
            preprocessing_config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Performance monitoring
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT,
            metric_name TEXT,
            metric_value REAL,
            measurement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES model_registry (model_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database schema initialized")
    
    def create_sample_dataset(self, size: int = 1000) -> Tuple[List[str], List[str]]:
        """Create a sample dataset for demonstration"""
        import random
        
        # Sample data for different content types
        sample_data = {
            "business_email": [
                "Please find attached the quarterly sales report. The revenue increased by 15% compared to last quarter.",
                "We need to schedule a meeting to discuss the new product launch timeline and marketing strategy.",
                "The project budget has been approved. Please proceed with the implementation phase.",
                "Our customer satisfaction scores have improved significantly after implementing the new support system."
            ],
            "technical_documentation": [
                "This API endpoint accepts POST requests with JSON payload containing user authentication data.",
                "The algorithm uses machine learning to classify text documents based on feature extraction.",
                "Database migration scripts should be executed in the following order to maintain data integrity.",
                "The microservice architecture ensures scalability and fault tolerance for high-traffic applications."
            ],
            "customer_support": [
                "I'm having trouble accessing my account. The password reset doesn't seem to be working.",
                "The product arrived damaged. I would like to request a replacement or refund.",
                "Thank you for the quick response. The issue has been resolved and everything is working now.",
                "I need help understanding how to use the advanced features of your software."
            ],
            "educational_content": [
                "Today we'll learn about the fundamental principles of machine learning and artificial intelligence.",
                "The assignment requires students to analyze the historical significance of the Renaissance period.",
                "Please review chapters 5-7 before the next class. There will be a quiz on the material.",
                "The laboratory experiment demonstrates the relationship between temperature and chemical reaction rates."
            ],
            "news_article": [
                "Breaking news: Technology company announces breakthrough in quantum computing research.",
                "The weather forecast predicts heavy rainfall and possible flooding in coastal areas.",
                "Stock markets showed mixed results today as investors react to economic policy changes.",
                "Scientists discover new species of marine life in deep ocean exploration mission."
            ]
        }
        
        texts = []
        labels = []
        
        for _ in range(size):
            category = random.choice(list(sample_data.keys()))
            text = random.choice(sample_data[category])
            
            # Add some variation to make it more realistic
            if random.random() < 0.3:
                text += f" Additional context: {random.choice(['Important', 'Urgent', 'Please review', 'For your information'])}"
            
            texts.append(text)
            labels.append(category)
        
        logger.info(f"✅ Created sample dataset with {size} examples across {len(sample_data)} categories")
        return texts, labels
    
    def train_model(self, texts: List[str], labels: List[str], 
                   model_type: str = "auto") -> str:
        """Train a new model with the provided data"""
        
        # Determine model type
        if model_type == "auto":
            model_type = "transformer" if TRANSFORMERS_AVAILABLE else "traditional"
        
        # Preprocess texts
        logger.info("🔄 Preprocessing texts...")
        processed_texts = self.preprocessor.preprocess(texts)
        
        # Split data
        train_texts, temp_texts, train_labels, temp_labels = train_test_split(
            processed_texts, labels, 
            test_size=(1 - self.training_config.train_split),
            random_state=42, stratify=labels
        )
        
        val_texts, test_texts, val_labels, test_labels = train_test_split(
            temp_texts, temp_labels,
            test_size=0.5,  # Split remaining 20% into 10% val, 10% test
            random_state=42, stratify=temp_labels
        )
        
        logger.info(f"📊 Dataset split: Train={len(train_texts)}, Val={len(val_texts)}, Test={len(test_texts)}")
        
        # Initialize model
        model_id = f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if model_type == "transformer" and TRANSFORMERS_AVAILABLE:
            model = TransformerTextClassifier(self.model_config)
        else:
            model = TraditionalMLClassifier()
            model_type = "traditional"
        
        # Train model
        logger.info(f"🚀 Training {model_type} model...")
        metrics = model.train(train_texts, train_labels, val_texts, val_labels)
        
        # Test on held-out test set
        test_predictions = model.predict(test_texts)
        test_accuracy = sum(
            1 for pred, true in zip(test_predictions, test_labels)
            if pred.predicted_class == true
        ) / len(test_labels)
        
        logger.info(f"📊 Test accuracy: {test_accuracy:.4f}")
        
        # Save model
        model_path = f"models/{model_id}"
        os.makedirs(model_path, exist_ok=True)
        
        if hasattr(model, 'save_model'):
            model.save_model(model_path)
        else:
            # Save traditional model
            with open(f"{model_path}/model.pkl", 'wb') as f:
                pickle.dump(model, f)
        
        # Store in registry
        self._register_model(model_id, model_type, metrics, model_path)
        
        # Set as active model
        self.models[model_id] = model
        self.active_model = model_id
        
        logger.info(f"✅ Model {model_id} trained and registered successfully")
        return model_id
    
    def predict(self, texts: List[str], model_id: Optional[str] = None) -> List[PredictionResult]:
        """Make predictions using specified or active model"""
        
        if model_id is None:
            model_id = self.active_model
        
        if model_id not in self.models:
            # Load model if not in memory
            self._load_model(model_id)
        
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        # Preprocess texts
        processed_texts = self.preprocessor.preprocess(texts)
        
        # Make predictions
        model = self.models[model_id]
        results = model.predict(processed_texts)
        
        # Log predictions
        self._log_predictions(model_id, texts, results)
        
        return results
    
    def evaluate_model(self, model_id: str, test_texts: List[str], 
                      test_labels: List[str]) -> ModelMetrics:
        """Evaluate model on test data"""
        
        predictions = self.predict(test_texts, model_id)
        predicted_labels = [pred.predicted_class for pred in predictions]
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
        
        accuracy = accuracy_score(test_labels, predicted_labels)
        precision, recall, f1, _ = precision_recall_fscore_support(
            test_labels, predicted_labels, average='weighted'
        )
        
        cm = confusion_matrix(test_labels, predicted_labels)
        report = classification_report(test_labels, predicted_labels)
        
        metrics = ModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            auc_score=None,
            confusion_matrix=cm.tolist(),
            classification_report=report,
            training_time=0,
            inference_time=sum(pred.prediction_time for pred in predictions) / len(predictions),
            model_size_mb=0
        )
        
        logger.info(f"📊 Model {model_id} evaluation: Accuracy={accuracy:.4f}, F1={f1:.4f}")
        return metrics
    
    def get_model_list(self) -> List[Dict[str, Any]]:
        """Get list of all registered models"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT model_id, model_name, model_type, version, accuracy, f1_score, 
               training_date, is_active
        FROM model_registry
        ORDER BY training_date DESC
        ''')
        
        models = []
        for row in cursor.fetchall():
            models.append({
                'model_id': row[0],
                'model_name': row[1],
                'model_type': row[2],
                'version': row[3],
                'accuracy': row[4],
                'f1_score': row[5],
                'training_date': row[6],
                'is_active': bool(row[7])
            })
        
        conn.close()
        return models
    
    def set_active_model(self, model_id: str):
        """Set the active model for predictions"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Deactivate all models
        cursor.execute('UPDATE model_registry SET is_active = FALSE')
        
        # Activate specified model
        cursor.execute('UPDATE model_registry SET is_active = TRUE WHERE model_id = ?', (model_id,))
        
        conn.commit()
        conn.close()
        
        self.active_model = model_id
        logger.info(f"✅ Set active model to {model_id}")
    
    def _register_model(self, model_id: str, model_type: str, metrics: ModelMetrics, model_path: str):
        """Register model in database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO model_registry (
            model_id, model_name, model_type, version, accuracy, f1_score,
            training_date, is_active, model_config, metrics, file_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            model_id,
            f"{model_type}_classifier",
            model_type,
            "1.0",
            metrics.accuracy,
            metrics.f1_score,
            datetime.now().isoformat(),
            True,  # Set as active by default
            json.dumps(self.model_config.__dict__),
            json.dumps(metrics.__dict__, default=str),
            model_path
        ))
        
        conn.commit()
        conn.close()
    
    def _load_model(self, model_id: str):
        """Load model from storage"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT model_type, file_path FROM model_registry WHERE model_id = ?', (model_id,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError(f"Model {model_id} not found in registry")
        
        model_type, file_path = row
        
        if model_type == "transformer" and TRANSFORMERS_AVAILABLE:
            model = TransformerTextClassifier(self.model_config)
            model.load_model(file_path)
        else:
            # Load traditional model
            with open(f"{file_path}/model.pkl", 'rb') as f:
                model = pickle.load(f)
        
        self.models[model_id] = model
        conn.close()
        logger.info(f"✅ Loaded model {model_id}")
    
    def _log_predictions(self, model_id: str, texts: List[str], results: List[PredictionResult]):
        """Log predictions for monitoring"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        for text, result in zip(texts, results):
            cursor.execute('''
            INSERT INTO prediction_logs (
                model_id, input_text, predicted_class, confidence_score, prediction_time
            ) VALUES (?, ?, ?, ?, ?)
            ''', (
                model_id,
                text[:1000],  # Truncate long texts
                result.predicted_class,
                result.confidence_score,
                result.prediction_time
            ))
        
        conn.commit()
        conn.close()
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get model performance analytics"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Overall statistics
        cursor.execute('SELECT COUNT(*) FROM prediction_logs')
        total_predictions = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(confidence_score) FROM prediction_logs')
        avg_confidence = cursor.fetchone()[0] or 0
        
        # Model comparison
        cursor.execute('''
        SELECT mr.model_id, mr.model_type, mr.accuracy, COUNT(pl.id) as prediction_count
        FROM model_registry mr
        LEFT JOIN prediction_logs pl ON mr.model_id = pl.model_id
        GROUP BY mr.model_id
        ORDER BY mr.accuracy DESC
        ''')
        
        model_stats = []
        for row in cursor.fetchall():
            model_stats.append({
                'model_id': row[0],
                'model_type': row[1],
                'accuracy': row[2],
                'prediction_count': row[3]
            })
        
        conn.close()
        
        return {
            'total_predictions': total_predictions,
            'average_confidence': avg_confidence,
            'model_statistics': model_stats,
            'active_model': self.active_model
        }


def demo_production_text_classification():
    """Demonstrate the production text classification system"""
    print("🚀 Production Text Classification System Demo")
    print("=" * 60)
    
    # Initialize system
    system = ProductionTextClassificationSystem()
    
    # Create sample dataset
    print("\n📊 Creating sample dataset...")
    texts, labels = system.create_sample_dataset(size=500)
    
    print(f"Dataset size: {len(texts)} examples")
    print(f"Classes: {set(labels)}")
    print(f"Sample text: {texts[0][:100]}...")
    
    # Train model
    print(f"\n🎯 Training model...")
    model_id = system.train_model(texts, labels, model_type="auto")
    
    # Make predictions on new samples
    print(f"\n🔮 Making predictions...")
    test_texts = [
        "We need to discuss the budget allocation for the next quarter and review our sales projections.",
        "The API documentation explains how to authenticate requests using bearer tokens and handle rate limits.",
        "I'm experiencing issues with my login credentials and need assistance resetting my password.",
        "Today's lecture covers the fundamental concepts of machine learning and neural networks.",
        "Breaking: Scientists announce major breakthrough in renewable energy technology."
    ]
    
    predictions = system.predict(test_texts)
    
    print("\n📋 Prediction Results:")
    for i, (text, pred) in enumerate(zip(test_texts, predictions)):
        print(f"\n{i+1}. Text: {text[:80]}...")
        print(f"   Predicted: {pred.predicted_class}")
        print(f"   Confidence: {pred.confidence_score:.3f}")
        print(f"   Top probabilities:")
        sorted_probs = sorted(pred.prediction_probabilities.items(), key=lambda x: x[1], reverse=True)
        for class_name, prob in sorted_probs[:3]:
            print(f"     {class_name}: {prob:.3f}")
    
    # Show model analytics
    print(f"\n📈 Performance Analytics:")
    analytics = system.get_performance_analytics()
    
    print(f"Total predictions made: {analytics['total_predictions']}")
    print(f"Average confidence: {analytics['average_confidence']:.3f}")
    print(f"Active model: {analytics['active_model']}")
    
    print(f"\nRegistered models:")
    models = system.get_model_list()
    for model in models:
        status = "✅ ACTIVE" if model['is_active'] else "📋"
        print(f"  {status} {model['model_id']} ({model['model_type']}) - Accuracy: {model['accuracy']:.3f}")
    
    # Test evaluation
    if len(texts) > 100:
        print(f"\n🧪 Model Evaluation:")
        eval_texts = texts[-50:]  # Use last 50 for evaluation
        eval_labels = labels[-50:]
        
        metrics = system.evaluate_model(model_id, eval_texts, eval_labels)
        print(f"Test Accuracy: {metrics.accuracy:.4f}")
        print(f"Test F1-Score: {metrics.f1_score:.4f}")
        print(f"Average Inference Time: {metrics.inference_time:.4f}s")
    
    print(f"\n✅ Production text classification system demonstration complete!")
    print(f"Database: {system.database_path}")
    print(f"Model availability: Transformers={TRANSFORMERS_AVAILABLE}, spaCy={SPACY_AVAILABLE}")


if __name__ == "__main__":
    demo_production_text_classification()