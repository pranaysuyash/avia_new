#!/usr/bin/env python3
"""
Advanced Text Classification System
Implements multi-label, hierarchical, zero-shot classification with active learning
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from enum import Enum
import numpy as np
from pathlib import Path
import json
import pickle

# Machine Learning
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    classification_report, confusion_matrix,
    roc_auc_score, hamming_loss, jaccard_score
)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.multioutput import MultiOutputClassifier

# Deep Learning
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    AutoModelForZeroShotClassification,
    pipeline, Trainer, TrainingArguments,
    BertForSequenceClassification, BertTokenizer,
    DistilBertForSequenceClassification, DistilBertTokenizer
)

# NLP
import spacy
from sentence_transformers import SentenceTransformer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Active Learning
from modAL.models import ActiveLearner
from modAL.uncertainty import uncertainty_sampling, entropy_sampling
from modAL.batch import uncertainty_batch_sampling

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import plotly.graph_objects as go
import plotly.express as px

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClassificationType(Enum):
    """Types of classification"""
    BINARY = "binary"
    MULTICLASS = "multiclass"
    MULTILABEL = "multilabel"
    HIERARCHICAL = "hierarchical"
    ZERO_SHOT = "zero_shot"


class ModelType(Enum):
    """Classification model types"""
    NAIVE_BAYES = "naive_bayes"
    LOGISTIC_REGRESSION = "logistic_regression"
    RANDOM_FOREST = "random_forest"
    SVM = "svm"
    GRADIENT_BOOSTING = "gradient_boosting"
    BERT = "bert"
    DISTILBERT = "distilbert"
    ROBERTA = "roberta"
    ENSEMBLE = "ensemble"


@dataclass
class ClassLabel:
    """Classification label"""
    label_id: str
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None  # For hierarchical classification
    confidence_threshold: float = 0.5
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HierarchyNode:
    """Node in label hierarchy"""
    label: ClassLabel
    children: List['HierarchyNode'] = field(default_factory=list)
    level: int = 0
    path: List[str] = field(default_factory=list)


@dataclass
class ClassificationResult:
    """Classification result for a text"""
    text_id: str
    text: str
    predictions: List[Tuple[str, float]]  # (label, confidence)
    predicted_labels: List[str]
    confidence_scores: Dict[str, float]
    model_type: ModelType
    classification_type: ClassificationType
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActiveLearningQuery:
    """Query for active learning"""
    text_id: str
    text: str
    uncertainty_score: float
    predicted_labels: List[str]
    confidence_scores: Dict[str, float]
    acquisition_method: str


@dataclass
class ModelPerformance:
    """Model performance metrics"""
    accuracy: float
    precision: Dict[str, float]
    recall: Dict[str, float]
    f1_score: Dict[str, float]
    confusion_matrix: Optional[np.ndarray] = None
    classification_report: Optional[str] = None
    roc_auc: Optional[float] = None
    hamming_loss: Optional[float] = None  # For multi-label
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextDataset(Dataset):
    """PyTorch dataset for text classification"""
    
    def __init__(self, texts: List[str], labels: List[Any], tokenizer, max_length: int = 512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


class HierarchicalClassifier:
    """Hierarchical text classifier"""
    
    def __init__(self, hierarchy: HierarchyNode):
        self.hierarchy = hierarchy
        self.classifiers = {}  # One classifier per internal node
        self.label_paths = self._build_label_paths()
    
    def _build_label_paths(self) -> Dict[str, List[str]]:
        """Build paths from root to each label"""
        paths = {}
        
        def traverse(node: HierarchyNode, path: List[str]):
            current_path = path + [node.label.label_id]
            paths[node.label.label_id] = current_path
            
            for child in node.children:
                traverse(child, current_path)
        
        traverse(self.hierarchy, [])
        return paths
    
    def train(self, texts: List[str], labels: List[str], model_type: ModelType = ModelType.LOGISTIC_REGRESSION):
        """Train hierarchical classifiers"""
        
        def train_node(node: HierarchyNode, node_texts: List[str], node_labels: List[str]):
            if not node.children:
                return
            
            # Get child labels for this node
            child_ids = [child.label.label_id for child in node.children]
            
            # Filter training data for this node
            relevant_indices = [
                i for i, label in enumerate(node_labels)
                if any(label.startswith(child_id) for child_id in child_ids)
            ]
            
            if not relevant_indices:
                return
            
            X = [node_texts[i] for i in relevant_indices]
            y = [node_labels[i].split('/')[node.level + 1] for i in relevant_indices]
            
            # Train classifier for this node
            if model_type == ModelType.LOGISTIC_REGRESSION:
                classifier = LogisticRegression(random_state=42)
            elif model_type == ModelType.RANDOM_FOREST:
                classifier = RandomForestClassifier(random_state=42)
            else:
                classifier = MultinomialNB()
            
            # Vectorize texts
            vectorizer = TfidfVectorizer(max_features=1000)
            X_vec = vectorizer.fit_transform(X)
            
            classifier.fit(X_vec, y)
            self.classifiers[node.label.label_id] = (classifier, vectorizer)
            
            # Recursively train child nodes
            for child in node.children:
                train_node(child, node_texts, node_labels)
        
        train_node(self.hierarchy, texts, labels)
    
    def predict(self, text: str) -> List[Tuple[str, float]]:
        """Predict using hierarchical classification"""
        predictions = []
        
        def predict_node(node: HierarchyNode, confidence: float = 1.0):
            if node.label.label_id in self.classifiers:
                classifier, vectorizer = self.classifiers[node.label.label_id]
                X_vec = vectorizer.transform([text])
                
                # Get prediction and probabilities
                pred = classifier.predict(X_vec)[0]
                proba = classifier.predict_proba(X_vec)[0]
                
                # Find the predicted child
                for i, child in enumerate(node.children):
                    if child.label.label_id == pred:
                        child_confidence = confidence * proba[i]
                        predictions.append((child.label.label_id, child_confidence))
                        predict_node(child, child_confidence)
                        break
        
        predict_node(self.hierarchy)
        return predictions


class TextClassificationSystem:
    """Advanced text classification system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize models
        self.models = {}
        self.vectorizers = {}
        self.label_encoders = {}
        
        # Initialize NLP tools
        self._initialize_nlp()
        
        # Active learning components
        self.active_learners = {}
        self.query_pool = []
        
        # Model performance tracking
        self.performance_history = []
        
    def _initialize_nlp(self):
        """Initialize NLP models and tools"""
        try:
            # SpaCy
            self.nlp = spacy.load("en_core_web_sm")
            
            # Sentence transformer for embeddings
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            
            # NLTK tools
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words('english'))
            
            # Transformers
            if self.config.get('use_transformers', False):
                self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
                
            logger.info("NLP tools initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize NLP tools: {e}")
    
    def preprocess_text(self, text: str, use_lemma: bool = True) -> str:
        """Preprocess text for classification"""
        
        # Convert to lowercase
        text = text.lower()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        tokens = [t for t in tokens if t not in self.stop_words]
        
        # Lemmatize if requested
        if use_lemma:
            tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
        
        return ' '.join(tokens)
    
    async def train_classifier(
        self,
        texts: List[str],
        labels: List[Union[str, List[str]]],
        classification_type: ClassificationType,
        model_type: ModelType = ModelType.LOGISTIC_REGRESSION,
        test_size: float = 0.2,
        cross_validate: bool = True
    ) -> ModelPerformance:
        """Train a text classifier"""
        
        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in texts]
        
        # Handle different classification types
        if classification_type == ClassificationType.MULTILABEL:
            return await self._train_multilabel(
                processed_texts, labels, model_type, test_size
            )
        elif classification_type == ClassificationType.HIERARCHICAL:
            return await self._train_hierarchical(
                processed_texts, labels, model_type
            )
        else:
            return await self._train_standard(
                processed_texts, labels, model_type, test_size, cross_validate
            )
    
    async def _train_standard(
        self,
        texts: List[str],
        labels: List[str],
        model_type: ModelType,
        test_size: float,
        cross_validate: bool
    ) -> ModelPerformance:
        """Train standard classifier (binary or multiclass)"""
        
        # Vectorize texts
        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        X = vectorizer.fit_transform(texts)
        
        # Encode labels
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Select and train model
        if model_type == ModelType.NAIVE_BAYES:
            model = MultinomialNB()
        elif model_type == ModelType.LOGISTIC_REGRESSION:
            model = LogisticRegression(max_iter=1000, random_state=42)
        elif model_type == ModelType.RANDOM_FOREST:
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        elif model_type == ModelType.SVM:
            model = LinearSVC(random_state=42)
        elif model_type == ModelType.GRADIENT_BOOSTING:
            model = GradientBoostingClassifier(random_state=42)
        else:
            model = LogisticRegression(random_state=42)
        
        # Cross-validation if requested
        if cross_validate:
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            logger.info(f"Cross-validation scores: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        # Train model
        model.fit(X_train, y_train)
        
        # Store model and preprocessors
        model_key = f"{model_type.value}_{len(self.models)}"
        self.models[model_key] = model
        self.vectorizers[model_key] = vectorizer
        self.label_encoders[model_key] = label_encoder
        
        # Evaluate
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted'
        )
        
        # Get per-class metrics
        class_names = label_encoder.classes_
        precision_dict, recall_dict, f1_dict, _ = precision_recall_fscore_support(
            y_test, y_pred, average=None
        )
        
        precision_by_class = {
            class_names[i]: precision_dict[i] 
            for i in range(len(class_names))
        }
        recall_by_class = {
            class_names[i]: recall_dict[i]
            for i in range(len(class_names))
        }
        f1_by_class = {
            class_names[i]: f1_dict[i]
            for i in range(len(class_names))
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Classification report
        report = classification_report(
            y_test, y_pred,
            target_names=class_names
        )
        
        return ModelPerformance(
            accuracy=accuracy,
            precision=precision_by_class,
            recall=recall_by_class,
            f1_score=f1_by_class,
            confusion_matrix=cm,
            classification_report=report,
            metadata={
                'model_type': model_type.value,
                'test_size': test_size,
                'num_classes': len(class_names),
                'model_key': model_key
            }
        )
    
    async def _train_multilabel(
        self,
        texts: List[str],
        labels: List[List[str]],
        model_type: ModelType,
        test_size: float
    ) -> ModelPerformance:
        """Train multi-label classifier"""
        
        # Vectorize texts
        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        X = vectorizer.fit_transform(texts)
        
        # Encode multi-labels
        mlb = MultiLabelBinarizer()
        y = mlb.fit_transform(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Select base model
        if model_type == ModelType.LOGISTIC_REGRESSION:
            base_model = LogisticRegression(max_iter=1000, random_state=42)
        elif model_type == ModelType.RANDOM_FOREST:
            base_model = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            base_model = LinearSVC(random_state=42)
        
        # Wrap in multi-label classifier
        model = MultiOutputClassifier(base_model)
        
        # Train
        model.fit(X_train, y_train)
        
        # Store model
        model_key = f"multilabel_{model_type.value}_{len(self.models)}"
        self.models[model_key] = model
        self.vectorizers[model_key] = vectorizer
        self.label_encoders[model_key] = mlb
        
        # Evaluate
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        hamming = hamming_loss(y_test, y_pred)
        
        # Per-label metrics
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='samples'
        )
        
        return ModelPerformance(
            accuracy=accuracy,
            precision={'overall': precision},
            recall={'overall': recall},
            f1_score={'overall': f1},
            hamming_loss=hamming,
            metadata={
                'model_type': model_type.value,
                'classification_type': 'multilabel',
                'num_labels': len(mlb.classes_),
                'model_key': model_key
            }
        )
    
    async def _train_hierarchical(
        self,
        texts: List[str],
        labels: List[str],
        model_type: ModelType
    ) -> ModelPerformance:
        """Train hierarchical classifier"""
        
        # Build hierarchy from labels (assuming "/" separated paths)
        hierarchy = self._build_hierarchy(labels)
        
        # Create hierarchical classifier
        h_classifier = HierarchicalClassifier(hierarchy)
        
        # Train
        h_classifier.train(texts, labels, model_type)
        
        # Store
        model_key = f"hierarchical_{model_type.value}_{len(self.models)}"
        self.models[model_key] = h_classifier
        
        # Note: Simplified evaluation for hierarchical
        return ModelPerformance(
            accuracy=0.0,  # Would need proper hierarchical evaluation
            precision={},
            recall={},
            f1_score={},
            metadata={
                'model_type': model_type.value,
                'classification_type': 'hierarchical',
                'model_key': model_key
            }
        )
    
    def _build_hierarchy(self, labels: List[str]) -> HierarchyNode:
        """Build hierarchy tree from label paths"""
        
        # Create root
        root = HierarchyNode(
            label=ClassLabel(label_id="root", name="Root"),
            level=0
        )
        
        # Build tree
        nodes = {"root": root}
        
        for label_path in set(labels):
            parts = label_path.split('/')
            parent = root
            
            for i, part in enumerate(parts):
                node_id = '/'.join(parts[:i+1])
                
                if node_id not in nodes:
                    new_node = HierarchyNode(
                        label=ClassLabel(label_id=node_id, name=part),
                        level=i+1,
                        path=parts[:i+1]
                    )
                    nodes[node_id] = new_node
                    parent.children.append(new_node)
                
                parent = nodes[node_id]
        
        return root
    
    async def predict(
        self,
        text: str,
        model_key: str,
        threshold: float = 0.5
    ) -> ClassificationResult:
        """Predict class for text"""
        
        import time
        start_time = time.time()
        
        if model_key not in self.models:
            raise ValueError(f"Model {model_key} not found")
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Get model and preprocessors
        model = self.models[model_key]
        vectorizer = self.vectorizers.get(model_key)
        label_encoder = self.label_encoders.get(model_key)
        
        # Handle hierarchical classifier
        if isinstance(model, HierarchicalClassifier):
            predictions = model.predict(processed_text)
            predicted_labels = [p[0] for p in predictions if p[1] >= threshold]
            confidence_scores = {p[0]: p[1] for p in predictions}
            
            return ClassificationResult(
                text_id=self._generate_id(),
                text=text,
                predictions=predictions,
                predicted_labels=predicted_labels,
                confidence_scores=confidence_scores,
                model_type=ModelType.ENSEMBLE,  # Placeholder
                classification_type=ClassificationType.HIERARCHICAL,
                processing_time=time.time() - start_time
            )
        
        # Vectorize text
        X = vectorizer.transform([processed_text])
        
        # Get predictions
        if hasattr(model, 'predict_proba'):
            probas = model.predict_proba(X)[0]
            predictions = []
            
            if isinstance(label_encoder, MultiLabelBinarizer):
                # Multi-label case
                for i, label in enumerate(label_encoder.classes_):
                    predictions.append((label, probas[i]))
                predicted_labels = [
                    label for label, conf in predictions if conf >= threshold
                ]
            else:
                # Standard case
                for i, label in enumerate(label_encoder.classes_):
                    predictions.append((label, probas[i]))
                predictions.sort(key=lambda x: x[1], reverse=True)
                predicted_labels = [predictions[0][0]]
        else:
            # No probability support
            pred = model.predict(X)[0]
            if isinstance(label_encoder, MultiLabelBinarizer):
                predicted_labels = label_encoder.inverse_transform([pred])[0]
            else:
                predicted_labels = [label_encoder.inverse_transform([pred])[0]]
            predictions = [(label, 1.0) for label in predicted_labels]
        
        confidence_scores = {label: conf for label, conf in predictions}
        
        return ClassificationResult(
            text_id=self._generate_id(),
            text=text,
            predictions=predictions,
            predicted_labels=predicted_labels,
            confidence_scores=confidence_scores,
            model_type=self._get_model_type(model_key),
            classification_type=self._get_classification_type(model_key),
            processing_time=time.time() - start_time
        )
    
    async def zero_shot_classify(
        self,
        text: str,
        candidate_labels: List[str],
        hypothesis_template: str = "This text is about {}."
    ) -> ClassificationResult:
        """Zero-shot classification using transformers"""
        
        import time
        start_time = time.time()
        
        # Use zero-shot classification pipeline
        classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
        result = classifier(
            text,
            candidate_labels,
            hypothesis_template=hypothesis_template
        )
        
        # Format results
        predictions = list(zip(result['labels'], result['scores']))
        predicted_labels = [
            label for label, score in predictions 
            if score >= self.config.get('zero_shot_threshold', 0.5)
        ]
        
        if not predicted_labels:
            predicted_labels = [predictions[0][0]]  # At least one label
        
        confidence_scores = {
            label: score for label, score in predictions
        }
        
        return ClassificationResult(
            text_id=self._generate_id(),
            text=text,
            predictions=predictions,
            predicted_labels=predicted_labels,
            confidence_scores=confidence_scores,
            model_type=ModelType.BERT,  # Using transformer
            classification_type=ClassificationType.ZERO_SHOT,
            processing_time=time.time() - start_time,
            metadata={'candidate_labels': candidate_labels}
        )
    
    def setup_active_learning(
        self,
        initial_texts: List[str],
        initial_labels: List[str],
        model_type: ModelType = ModelType.LOGISTIC_REGRESSION
    ):
        """Setup active learning pipeline"""
        
        # Preprocess
        processed_texts = [self.preprocess_text(text) for text in initial_texts]
        
        # Vectorize
        vectorizer = TfidfVectorizer(max_features=5000)
        X_initial = vectorizer.fit_transform(processed_texts)
        
        # Encode labels
        label_encoder = LabelEncoder()
        y_initial = label_encoder.fit_transform(initial_labels)
        
        # Create base estimator
        if model_type == ModelType.LOGISTIC_REGRESSION:
            estimator = LogisticRegression(random_state=42)
        else:
            estimator = RandomForestClassifier(random_state=42)
        
        # Create active learner
        learner = ActiveLearner(
            estimator=estimator,
            X_training=X_initial,
            y_training=y_initial,
            query_strategy=uncertainty_sampling
        )
        
        # Store
        learner_key = f"active_{model_type.value}_{len(self.active_learners)}"
        self.active_learners[learner_key] = {
            'learner': learner,
            'vectorizer': vectorizer,
            'label_encoder': label_encoder
        }
        
        logger.info(f"Active learner setup complete: {learner_key}")
        return learner_key
    
    def query_active_learning(
        self,
        learner_key: str,
        pool_texts: List[str],
        n_instances: int = 10
    ) -> List[ActiveLearningQuery]:
        """Query most informative samples for labeling"""
        
        if learner_key not in self.active_learners:
            raise ValueError(f"Active learner {learner_key} not found")
        
        learner_data = self.active_learners[learner_key]
        learner = learner_data['learner']
        vectorizer = learner_data['vectorizer']
        label_encoder = learner_data['label_encoder']
        
        # Preprocess pool
        processed_pool = [self.preprocess_text(text) for text in pool_texts]
        X_pool = vectorizer.transform(processed_pool)
        
        # Query
        query_idx, query_inst = learner.query(X_pool, n_instances=n_instances)
        
        # Create query objects
        queries = []
        for idx in query_idx:
            # Get predictions for this instance
            X_single = X_pool[idx]
            pred_proba = learner.predict_proba(X_single)[0]
            pred_label = learner.predict(X_single)[0]
            
            # Calculate uncertainty
            uncertainty = 1 - max(pred_proba)
            
            # Decode label
            predicted_label = label_encoder.inverse_transform([pred_label])[0]
            
            # Create confidence scores
            confidence_scores = {
                label_encoder.inverse_transform([i])[0]: prob
                for i, prob in enumerate(pred_proba)
            }
            
            queries.append(ActiveLearningQuery(
                text_id=self._generate_id(),
                text=pool_texts[idx],
                uncertainty_score=uncertainty,
                predicted_labels=[predicted_label],
                confidence_scores=confidence_scores,
                acquisition_method="uncertainty_sampling"
            ))
        
        return queries
    
    def update_active_learner(
        self,
        learner_key: str,
        texts: List[str],
        labels: List[str]
    ):
        """Update active learner with new labeled data"""
        
        if learner_key not in self.active_learners:
            raise ValueError(f"Active learner {learner_key} not found")
        
        learner_data = self.active_learners[learner_key]
        learner = learner_data['learner']
        vectorizer = learner_data['vectorizer']
        label_encoder = learner_data['label_encoder']
        
        # Preprocess and vectorize
        processed_texts = [self.preprocess_text(text) for text in texts]
        X_new = vectorizer.transform(processed_texts)
        
        # Encode labels
        y_new = label_encoder.transform(labels)
        
        # Teach learner
        learner.teach(X_new, y_new)
        
        logger.info(f"Active learner {learner_key} updated with {len(texts)} samples")
    
    def visualize_performance(
        self,
        performance: ModelPerformance,
        output_path: Optional[str] = None
    ) -> plt.Figure:
        """Visualize model performance"""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Confusion matrix
        if performance.confusion_matrix is not None:
            sns.heatmap(
                performance.confusion_matrix,
                annot=True,
                fmt='d',
                cmap='Blues',
                ax=axes[0, 0]
            )
            axes[0, 0].set_title('Confusion Matrix')
            axes[0, 0].set_xlabel('Predicted')
            axes[0, 0].set_ylabel('Actual')
        
        # F1 scores by class
        if performance.f1_score:
            classes = list(performance.f1_score.keys())
            scores = list(performance.f1_score.values())
            
            axes[0, 1].barh(classes, scores)
            axes[0, 1].set_xlabel('F1 Score')
            axes[0, 1].set_title('F1 Score by Class')
            axes[0, 1].set_xlim([0, 1])
        
        # Precision-Recall comparison
        if performance.precision and performance.recall:
            classes = list(performance.precision.keys())
            precision_scores = [performance.precision[c] for c in classes]
            recall_scores = [performance.recall[c] for c in classes]
            
            x = np.arange(len(classes))
            width = 0.35
            
            axes[1, 0].bar(x - width/2, precision_scores, width, label='Precision')
            axes[1, 0].bar(x + width/2, recall_scores, width, label='Recall')
            axes[1, 0].set_xlabel('Class')
            axes[1, 0].set_ylabel('Score')
            axes[1, 0].set_title('Precision vs Recall')
            axes[1, 0].set_xticks(x)
            axes[1, 0].set_xticklabels(classes, rotation=45)
            axes[1, 0].legend()
        
        # Overall metrics
        metrics_text = f"Overall Accuracy: {performance.accuracy:.3f}\n"
        if performance.hamming_loss is not None:
            metrics_text += f"Hamming Loss: {performance.hamming_loss:.3f}\n"
        if performance.roc_auc is not None:
            metrics_text += f"ROC-AUC: {performance.roc_auc:.3f}\n"
        
        axes[1, 1].text(0.5, 0.5, metrics_text, ha='center', va='center', fontsize=12)
        axes[1, 1].set_title('Overall Metrics')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
        
        return fig
    
    def export_model(self, model_key: str, output_path: str):
        """Export trained model"""
        
        if model_key not in self.models:
            raise ValueError(f"Model {model_key} not found")
        
        export_data = {
            'model': self.models[model_key],
            'vectorizer': self.vectorizers.get(model_key),
            'label_encoder': self.label_encoders.get(model_key),
            'config': self.config
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(export_data, f)
        
        logger.info(f"Model exported to {output_path}")
    
    def load_model(self, model_path: str, model_key: Optional[str] = None):
        """Load exported model"""
        
        with open(model_path, 'rb') as f:
            export_data = pickle.load(f)
        
        if model_key is None:
            model_key = f"loaded_{len(self.models)}"
        
        self.models[model_key] = export_data['model']
        self.vectorizers[model_key] = export_data.get('vectorizer')
        self.label_encoders[model_key] = export_data.get('label_encoder')
        
        logger.info(f"Model loaded: {model_key}")
        return model_key
    
    def _get_model_type(self, model_key: str) -> ModelType:
        """Get model type from key"""
        for mt in ModelType:
            if mt.value in model_key:
                return mt
        return ModelType.ENSEMBLE
    
    def _get_classification_type(self, model_key: str) -> ClassificationType:
        """Get classification type from key"""
        if 'multilabel' in model_key:
            return ClassificationType.MULTILABEL
        elif 'hierarchical' in model_key:
            return ClassificationType.HIERARCHICAL
        else:
            return ClassificationType.MULTICLASS
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())[:8]


# Example usage
async def main():
    """Example usage of text classification system"""
    
    # Initialize system
    classifier = TextClassificationSystem(
        config={'use_transformers': False}
    )
    
    # Sample data
    texts = [
        "The stock market rose today on positive earnings reports.",
        "Scientists discover new species in the Amazon rainforest.",
        "The new smartphone features an improved camera and battery life.",
        "Local team wins championship after dramatic overtime victory.",
        "Climate change impacts are accelerating globally.",
        "Tech company announces layoffs amid economic uncertainty.",
        "Medical breakthrough offers hope for cancer patients.",
        "Movie review: The latest blockbuster disappoints critics.",
        "Recipe: How to make the perfect chocolate cake.",
        "Travel guide: Top 10 destinations for 2024."
    ]
    
    labels = [
        "business", "science", "technology", "sports", "environment",
        "business", "health", "entertainment", "food", "travel"
    ]
    
    # Train classifier
    print("Training classifier...")
    performance = await classifier.train_classifier(
        texts=texts,
        labels=labels,
        classification_type=ClassificationType.MULTICLASS,
        model_type=ModelType.LOGISTIC_REGRESSION,
        test_size=0.3
    )
    
    print(f"\nModel Performance:")
    print(f"Accuracy: {performance.accuracy:.3f}")
    print(f"\nClassification Report:\n{performance.classification_report}")
    
    # Test prediction
    test_text = "The company reported record profits this quarter."
    model_key = performance.metadata['model_key']
    
    result = await classifier.predict(test_text, model_key)
    print(f"\nPrediction for: '{test_text}'")
    print(f"Predicted label: {result.predicted_labels[0]}")
    print(f"Confidence: {result.confidence_scores[result.predicted_labels[0]]:.3f}")
    
    # Zero-shot classification example
    print("\n--- Zero-shot Classification ---")
    zero_shot_text = "The hurricane caused significant damage to coastal areas."
    candidate_labels = ["weather", "disaster", "politics", "sports", "technology"]
    
    zero_shot_result = await classifier.zero_shot_classify(
        zero_shot_text,
        candidate_labels
    )
    
    print(f"Text: '{zero_shot_text}'")
    print(f"Predicted labels: {zero_shot_result.predicted_labels}")
    print("Scores:")
    for label, score in zero_shot_result.predictions[:3]:
        print(f"  {label}: {score:.3f}")
    
    # Multi-label classification example
    print("\n--- Multi-label Classification ---")
    multi_label_texts = [
        "This smartphone has great camera quality and long battery life.",
        "The movie features stunning visuals and an emotional storyline.",
        "The recipe is both healthy and delicious.",
        "The startup secured funding and plans international expansion."
    ]
    
    multi_labels = [
        ["technology", "review"],
        ["entertainment", "review"],
        ["food", "health"],
        ["business", "technology"]
    ]
    
    ml_performance = await classifier.train_classifier(
        texts=multi_label_texts,
        labels=multi_labels,
        classification_type=ClassificationType.MULTILABEL,
        model_type=ModelType.RANDOM_FOREST
    )
    
    print(f"Multi-label Accuracy: {ml_performance.accuracy:.3f}")
    print(f"Hamming Loss: {ml_performance.hamming_loss:.3f}")
    
    # Active learning setup
    print("\n--- Active Learning ---")
    learner_key = classifier.setup_active_learning(
        initial_texts=texts[:5],
        initial_labels=labels[:5],
        model_type=ModelType.LOGISTIC_REGRESSION
    )
    
    # Query uncertain samples
    pool_texts = texts[5:]
    queries = classifier.query_active_learning(
        learner_key,
        pool_texts,
        n_instances=3
    )
    
    print("Most uncertain samples for labeling:")
    for query in queries:
        print(f"  Text: '{query.text[:50]}...'")
        print(f"  Uncertainty: {query.uncertainty_score:.3f}")
        print(f"  Predicted: {query.predicted_labels[0]}")
    
    # Visualize performance
    fig = classifier.visualize_performance(
        performance,
        "classification_performance.png"
    )
    print("\nPerformance visualization saved")


if __name__ == "__main__":
    asyncio.run(main())