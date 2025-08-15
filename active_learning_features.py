"""
Active Learning Features
Extracted from text_classification_system.py

This module provides active learning capabilities for iterative model improvement.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
import pickle
from pathlib import Path

# Core ML libraries
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer

# Active Learning libraries with fallback
try:
    from modAL.models import ActiveLearner
    from modAL.uncertainty import uncertainty_sampling, entropy_sampling, margin_sampling
    from modAL.batch import uncertainty_batch_sampling, ranked_batch
    from modAL.disagreement import vote_entropy_sampling, consensus_entropy_sampling
    MODAL_AVAILABLE = True
    print("✅ modAL available - Full active learning capabilities enabled")
except ImportError:
    MODAL_AVAILABLE = False
    print("⚠️ modAL not available - Using basic uncertainty sampling")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActiveLearningStrategy(Enum):
    """Active learning strategies"""
    UNCERTAINTY_SAMPLING = "uncertainty_sampling"
    ENTROPY_SAMPLING = "entropy_sampling"
    MARGIN_SAMPLING = "margin_sampling"
    BATCH_UNCERTAINTY = "batch_uncertainty"
    RANKED_BATCH = "ranked_batch"
    VOTE_ENTROPY = "vote_entropy"
    CONSENSUS_ENTROPY = "consensus_entropy"
    RANDOM_SAMPLING = "random_sampling"

class LabelingStatus(Enum):
    """Status of data labeling"""
    UNLABELED = "unlabeled"
    PENDING_REVIEW = "pending_review"
    LABELED = "labeled"
    DISPUTED = "disputed"
    VERIFIED = "verified"
    REJECTED = "rejected"

@dataclass
class ActiveLearningQuery:
    """Represents an active learning query"""
    query_id: str
    text: str
    uncertainty_score: float
    strategy_used: ActiveLearningStrategy
    predicted_label: Optional[str] = None
    predicted_confidence: float = 0.0
    actual_label: Optional[str] = None
    labeling_status: LabelingStatus = LabelingStatus.UNLABELED
    created_at: datetime = field(default_factory=datetime.now)
    labeled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActiveLearningSession:
    """Active learning session tracking"""
    session_id: str
    strategy: ActiveLearningStrategy
    initial_data_size: int
    queries_made: int = 0
    labels_acquired: int = 0
    model_iterations: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    performance_history: List[Dict[str, float]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelPerformance:
    """Model performance metrics"""
    iteration: int
    training_size: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    uncertainty_reduction: float
    confidence_improvement: float
    timestamp: datetime = field(default_factory=datetime.now)

class UncertaintySampler:
    """Basic uncertainty sampling implementation when modAL is not available"""
    
    def __init__(self, strategy: str = "entropy"):
        self.strategy = strategy
    
    def query(self, classifier, X_pool: np.ndarray, n_instances: int = 1) -> np.ndarray:
        """Query instances using uncertainty sampling"""
        if hasattr(classifier, 'predict_proba'):
            probabilities = classifier.predict_proba(X_pool)
            
            if self.strategy == "entropy":
                # Entropy-based uncertainty
                entropy = -np.sum(probabilities * np.log(probabilities + 1e-10), axis=1)
                query_indices = np.argsort(entropy)[-n_instances:]
            elif self.strategy == "margin":
                # Margin-based uncertainty
                sorted_probs = np.sort(probabilities, axis=1)
                margins = sorted_probs[:, -1] - sorted_probs[:, -2]
                query_indices = np.argsort(margins)[:n_instances]
            else:  # least confident
                # Least confident sampling
                confidences = np.max(probabilities, axis=1)
                query_indices = np.argsort(confidences)[:n_instances]
        else:
            # Random sampling if no probability estimates
            query_indices = np.random.choice(len(X_pool), n_instances, replace=False)
        
        return query_indices

class ActiveLearningPipeline:
    """Active learning pipeline for text classification"""
    
    def __init__(self, 
                 strategy: ActiveLearningStrategy = ActiveLearningStrategy.UNCERTAINTY_SAMPLING,
                 batch_size: int = 10,
                 max_iterations: int = 20):
        self.strategy = strategy
        self.batch_size = batch_size
        self.max_iterations = max_iterations
        self.vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.learner = None
        self.session = None
        self.queries_history = []
        self.performance_history = []
        
        # Initialize active learner
        self._initialize_learner()
        
        logger.info(f"✅ Active learning pipeline initialized with {strategy.value}")
    
    def _initialize_learner(self):
        """Initialize the active learner"""
        if MODAL_AVAILABLE:
            # Use modAL for advanced active learning
            if self.strategy == ActiveLearningStrategy.UNCERTAINTY_SAMPLING:
                query_strategy = uncertainty_sampling
            elif self.strategy == ActiveLearningStrategy.ENTROPY_SAMPLING:
                query_strategy = entropy_sampling
            elif self.strategy == ActiveLearningStrategy.MARGIN_SAMPLING:
                query_strategy = margin_sampling
            elif self.strategy == ActiveLearningStrategy.BATCH_UNCERTAINTY:
                query_strategy = uncertainty_batch_sampling
            elif self.strategy == ActiveLearningStrategy.RANKED_BATCH:
                query_strategy = ranked_batch
            elif self.strategy == ActiveLearningStrategy.VOTE_ENTROPY:
                query_strategy = vote_entropy_sampling
            elif self.strategy == ActiveLearningStrategy.CONSENSUS_ENTROPY:
                query_strategy = consensus_entropy_sampling
            else:
                query_strategy = uncertainty_sampling
            
            self.learner = ActiveLearner(
                estimator=self.classifier,
                query_strategy=query_strategy
            )
        else:
            # Use basic uncertainty sampler
            self.uncertainty_sampler = UncertaintySampler(
                strategy="entropy" if "entropy" in self.strategy.value else "margin"
            )
            logger.warning("Using basic uncertainty sampling - install modAL for advanced features")
    
    def start_session(self, 
                     initial_texts: List[str], 
                     initial_labels: List[str],
                     session_id: Optional[str] = None) -> ActiveLearningSession:
        """Start a new active learning session"""
        if not session_id:
            session_id = f"al_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.session = ActiveLearningSession(
            session_id=session_id,
            strategy=self.strategy,
            initial_data_size=len(initial_texts)
        )
        
        # Vectorize initial data
        X_initial = self.vectorizer.fit_transform(initial_texts)
        y_initial = np.array(initial_labels)
        
        # Train initial model
        if MODAL_AVAILABLE and self.learner:
            self.learner.fit(X_initial, y_initial)
        else:
            self.classifier.fit(X_initial, y_initial)
        
        # Record initial performance
        initial_performance = self._evaluate_model(X_initial, y_initial)
        self.performance_history.append(initial_performance)
        self.session.performance_history.append(initial_performance.__dict__)
        
        logger.info(f"Started active learning session {session_id} with {len(initial_texts)} initial samples")
        return self.session
    
    def query_instances(self, 
                       pool_texts: List[str], 
                       n_instances: Optional[int] = None) -> List[ActiveLearningQuery]:
        """Query the most informative instances from the pool"""
        if not n_instances:
            n_instances = self.batch_size
        
        if not self.session:
            raise ValueError("No active learning session started. Call start_session() first.")
        
        # Vectorize pool data
        X_pool = self.vectorizer.transform(pool_texts)
        
        # Query instances
        if MODAL_AVAILABLE and self.learner:
            query_indices, query_instances = self.learner.query(X_pool, n_instances=n_instances)
        else:
            query_indices = self.uncertainty_sampler.query(self.classifier, X_pool, n_instances)
            query_instances = X_pool[query_indices]
        
        # Create query objects
        queries = []
        for i, idx in enumerate(query_indices):
            # Calculate uncertainty score
            if hasattr(self.classifier, 'predict_proba'):
                proba = self.classifier.predict_proba(query_instances[i:i+1])[0]
                uncertainty_score = 1.0 - np.max(proba)
                predicted_label = self.classifier.classes_[np.argmax(proba)]
                predicted_confidence = np.max(proba)
            else:
                uncertainty_score = 0.5  # Default uncertainty
                predicted_label = self.classifier.predict(query_instances[i:i+1])[0]
                predicted_confidence = 0.5
            
            query = ActiveLearningQuery(
                query_id=f"{self.session.session_id}_q{self.session.queries_made + i + 1}",
                text=pool_texts[idx],
                uncertainty_score=uncertainty_score,
                strategy_used=self.strategy,
                predicted_label=predicted_label,
                predicted_confidence=predicted_confidence,
                metadata={"pool_index": int(idx)}
            )
            queries.append(query)
        
        self.queries_history.extend(queries)
        self.session.queries_made += len(queries)
        
        logger.info(f"Queried {len(queries)} instances with average uncertainty {np.mean([q.uncertainty_score for q in queries]):.3f}")
        return queries
    
    def update_model(self, 
                     query_texts: List[str], 
                     query_labels: List[str],
                     validation_texts: Optional[List[str]] = None,
                     validation_labels: Optional[List[str]] = None) -> ModelPerformance:
        """Update the model with new labels"""
        if not self.session:
            raise ValueError("No active learning session started.")
        
        # Vectorize new data
        X_new = self.vectorizer.transform(query_texts)
        y_new = np.array(query_labels)
        
        # Update model
        if MODAL_AVAILABLE and self.learner:
            self.learner.teach(X_new, y_new)
        else:
            # For basic implementation, retrain on all data
            # This is less efficient but works without modAL
            all_texts = self._get_all_training_texts() + query_texts
            all_labels = self._get_all_training_labels() + query_labels
            X_all = self.vectorizer.fit_transform(all_texts)
            y_all = np.array(all_labels)
            self.classifier.fit(X_all, y_all)
        
        # Update query status
        for i, query in enumerate(self.queries_history[-len(query_texts):]):
            query.actual_label = query_labels[i]
            query.labeling_status = LabelingStatus.LABELED
            query.labeled_at = datetime.now()
        
        # Evaluate performance
        if validation_texts and validation_labels:
            X_val = self.vectorizer.transform(validation_texts)
            y_val = np.array(validation_labels)
            performance = self._evaluate_model(X_val, y_val)
        else:
            # Use training data for performance (not ideal but works)
            performance = self._evaluate_model(X_new, y_new)
        
        self.performance_history.append(performance)
        self.session.performance_history.append(performance.__dict__)
        self.session.labels_acquired += len(query_labels)
        self.session.model_iterations += 1
        
        logger.info(f"Model updated with {len(query_labels)} new labels. Accuracy: {performance.accuracy:.3f}")
        return performance
    
    def _evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> ModelPerformance:
        """Evaluate model performance"""
        if MODAL_AVAILABLE and self.learner:
            predictions = self.learner.predict(X_test)
            if hasattr(self.learner, 'predict_proba'):
                probabilities = self.learner.predict_proba(X_test)
                confidences = np.max(probabilities, axis=1)
            else:
                confidences = np.full(len(predictions), 0.5)
        else:
            predictions = self.classifier.predict(X_test)
            if hasattr(self.classifier, 'predict_proba'):
                probabilities = self.classifier.predict_proba(X_test)
                confidences = np.max(probabilities, axis=1)
            else:
                confidences = np.full(len(predictions), 0.5)
        
        accuracy = accuracy_score(y_test, predictions)
        
        # Calculate additional metrics
        report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
        macro_avg = report.get('macro avg', {})
        
        # Calculate uncertainty and confidence improvements
        uncertainty_reduction = 0.0
        confidence_improvement = 0.0
        
        if len(self.performance_history) > 0:
            prev_performance = self.performance_history[-1]
            uncertainty_reduction = prev_performance.accuracy - accuracy if accuracy < prev_performance.accuracy else 0.0
            confidence_improvement = accuracy - prev_performance.accuracy if accuracy > prev_performance.accuracy else 0.0
        
        performance = ModelPerformance(
            iteration=len(self.performance_history),
            training_size=self.session.initial_data_size + self.session.labels_acquired if self.session else len(y_test),
            accuracy=accuracy,
            precision=macro_avg.get('precision', 0.0),
            recall=macro_avg.get('recall', 0.0),
            f1_score=macro_avg.get('f1-score', 0.0),
            uncertainty_reduction=uncertainty_reduction,
            confidence_improvement=confidence_improvement
        )
        
        return performance
    
    def should_continue(self) -> bool:
        """Determine if active learning should continue"""
        if not self.session:
            return False
        
        # Check maximum iterations
        if self.session.model_iterations >= self.max_iterations:
            return False
        
        # Check performance improvement
        if len(self.performance_history) >= 3:
            recent_improvements = [
                p.confidence_improvement for p in self.performance_history[-3:]
            ]
            if all(imp < 0.01 for imp in recent_improvements):  # Less than 1% improvement
                logger.info("Stopping: Performance improvement below threshold")
                return False
        
        # Check uncertainty reduction
        if len(self.queries_history) >= self.batch_size:
            recent_uncertainties = [
                q.uncertainty_score for q in self.queries_history[-self.batch_size:]
            ]
            if np.mean(recent_uncertainties) < 0.1:  # Very low uncertainty
                logger.info("Stopping: Uncertainty below threshold")
                return False
        
        return True
    
    def finalize_session(self) -> Dict[str, Any]:
        """Finalize the active learning session"""
        if not self.session:
            raise ValueError("No active learning session to finalize.")
        
        self.session.end_time = datetime.now()
        
        # Calculate session statistics
        total_time = (self.session.end_time - self.session.start_time).total_seconds()
        final_accuracy = self.performance_history[-1].accuracy if self.performance_history else 0.0
        initial_accuracy = self.performance_history[0].accuracy if self.performance_history else 0.0
        improvement = final_accuracy - initial_accuracy
        
        avg_uncertainty = np.mean([q.uncertainty_score for q in self.queries_history]) if self.queries_history else 0.0
        
        session_summary = {
            "session_id": self.session.session_id,
            "strategy": self.session.strategy.value,
            "total_time": total_time,
            "initial_data_size": self.session.initial_data_size,
            "queries_made": self.session.queries_made,
            "labels_acquired": self.session.labels_acquired,
            "model_iterations": self.session.model_iterations,
            "initial_accuracy": initial_accuracy,
            "final_accuracy": final_accuracy,
            "accuracy_improvement": improvement,
            "average_uncertainty": avg_uncertainty,
            "performance_history": [p.__dict__ for p in self.performance_history]
        }
        
        logger.info(f"Active learning session completed. Improvement: {improvement:.3f}")
        return session_summary
    
    def _get_all_training_texts(self) -> List[str]:
        """Get all training texts (needed for basic implementation)"""
        # This would need to be tracked in a real implementation
        return []
    
    def _get_all_training_labels(self) -> List[str]:
        """Get all training labels (needed for basic implementation)"""
        # This would need to be tracked in a real implementation
        return []
    
    def save_session(self, filepath: str):
        """Save the active learning session"""
        session_data = {
            "session": self.session.__dict__ if self.session else None,
            "queries_history": [q.__dict__ for q in self.queries_history],
            "performance_history": [p.__dict__ for p in self.performance_history],
            "strategy": self.strategy.value,
            "batch_size": self.batch_size,
            "max_iterations": self.max_iterations
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
        
        logger.info(f"Session saved to {filepath}")
    
    def load_session(self, filepath: str):
        """Load an active learning session"""
        with open(filepath, 'r') as f:
            session_data = json.load(f)
        
        # Reconstruct session objects
        if session_data["session"]:
            session_dict = session_data["session"]
            self.session = ActiveLearningSession(
                session_id=session_dict["session_id"],
                strategy=ActiveLearningStrategy(session_dict["strategy"]),
                initial_data_size=session_dict["initial_data_size"],
                queries_made=session_dict["queries_made"],
                labels_acquired=session_dict["labels_acquired"],
                model_iterations=session_dict["model_iterations"]
            )
        
        logger.info(f"Session loaded from {filepath}")

def integrate_with_production_classifier(production_system, 
                                       unlabeled_texts: List[str],
                                       strategy: ActiveLearningStrategy = ActiveLearningStrategy.UNCERTAINTY_SAMPLING) -> Dict[str, Any]:
    """Integrate active learning with production text classification system"""
    
    # Initialize active learning pipeline
    al_pipeline = ActiveLearningPipeline(strategy=strategy, batch_size=5)
    
    # Get some initial predictions from production system
    initial_predictions = []
    high_confidence_texts = []
    high_confidence_labels = []
    
    for text in unlabeled_texts[:20]:  # Use first 20 for initial training
        result = production_system.classify_text(text)
        initial_predictions.append(result)
        
        if result.get("confidence", 0) > 0.8:  # High confidence predictions as initial labels
            high_confidence_texts.append(text)
            high_confidence_labels.append(result.get("predicted_class", "unknown"))
    
    if len(high_confidence_texts) >= 5:
        # Start active learning session
        session = al_pipeline.start_session(high_confidence_texts, high_confidence_labels)
        
        # Query most uncertain instances
        remaining_texts = [t for t in unlabeled_texts if t not in high_confidence_texts]
        queries = al_pipeline.query_instances(remaining_texts, n_instances=5)
        
        return {
            "session_id": session.session_id,
            "initial_training_size": len(high_confidence_texts),
            "queries_for_labeling": [
                {
                    "query_id": q.query_id,
                    "text": q.text,
                    "uncertainty_score": q.uncertainty_score,
                    "predicted_label": q.predicted_label,
                    "predicted_confidence": q.predicted_confidence
                }
                for q in queries
            ],
            "strategy_used": strategy.value,
            "next_steps": [
                "Label the queried instances",
                "Call update_model() with new labels",
                "Continue querying until performance plateaus"
            ]
        }
    else:
        return {
            "error": "Insufficient high-confidence predictions for initial training",
            "high_confidence_count": len(high_confidence_texts),
            "required_minimum": 5
        }

def main():
    """Demo active learning features"""
    print("=== Active Learning Features Demo ===\n")
    
    # Create sample data
    sample_texts = [
        "This product is amazing, I love it!",
        "Terrible quality, waste of money.",
        "Good value for the price, recommended.",
        "Not what I expected, very disappointed.",
        "Excellent customer service and fast delivery.",
        "Poor packaging, item arrived damaged.",
        "Great features and easy to use.",
        "Overpriced for what you get.",
        "Perfect for my needs, very satisfied.",
        "Would not buy again, poor quality."
    ]
    
    sample_labels = ["positive", "negative", "positive", "negative", "positive", 
                    "negative", "positive", "negative", "positive", "negative"]
    
    # Split into initial training and pool
    initial_texts = sample_texts[:4]
    initial_labels = sample_labels[:4]
    pool_texts = sample_texts[4:]
    pool_labels = sample_labels[4:]  # In real scenario, these would be unknown
    
    # Initialize active learning
    al_pipeline = ActiveLearningPipeline(
        strategy=ActiveLearningStrategy.UNCERTAINTY_SAMPLING,
        batch_size=2,
        max_iterations=3
    )
    
    # Start session
    print("Starting active learning session...")
    session = al_pipeline.start_session(initial_texts, initial_labels)
    print(f"Session ID: {session.session_id}")
    print(f"Initial training size: {session.initial_data_size}")
    
    # Active learning loop
    iteration = 0
    while al_pipeline.should_continue() and iteration < 3:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        
        # Query instances
        queries = al_pipeline.query_instances(pool_texts, n_instances=2)
        print(f"Queried {len(queries)} instances:")
        
        for query in queries:
            print(f"  - '{query.text[:50]}...' (uncertainty: {query.uncertainty_score:.3f})")
        
        # Simulate labeling (in real scenario, human would label these)
        query_texts = [q.text for q in queries]
        query_labels = []
        for text in query_texts:
            # Find the true label (simulation)
            if text in sample_texts:
                idx = sample_texts.index(text)
                query_labels.append(sample_labels[idx])
            else:
                query_labels.append("unknown")
        
        # Update model
        performance = al_pipeline.update_model(query_texts, query_labels)
        print(f"Model performance - Accuracy: {performance.accuracy:.3f}, Improvement: {performance.confidence_improvement:.3f}")
        
        # Remove queried texts from pool
        pool_texts = [t for t in pool_texts if t not in query_texts]
        
        if not pool_texts:
            break
    
    # Finalize session
    summary = al_pipeline.finalize_session()
    print("\n=== Session Summary ===")
    print(f"Total improvement: {summary['accuracy_improvement']:.3f}")
    print(f"Labels acquired: {summary['labels_acquired']}")
    print(f"Final accuracy: {summary['final_accuracy']:.3f}")

if __name__ == "__main__":
    main()