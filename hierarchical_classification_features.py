"""
Hierarchical Classification Features
Extracted from text_classification_system.py

This module provides hierarchical classification capabilities with multi-level label structures.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
from collections import defaultdict, deque

# Core ML libraries
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HierarchyLevel(Enum):
    """Hierarchy levels for classification"""
    ROOT = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEAF = 99

class PredictionStrategy(Enum):
    """Strategies for hierarchical prediction"""
    TOP_DOWN = "top_down"              # Predict from root to leaf
    BOTTOM_UP = "bottom_up"            # Predict leaves then aggregate up
    GLOBAL = "global"                  # Single classifier for all levels
    LOCAL = "local"                    # Separate classifier per node
    HYBRID = "hybrid"                  # Combination of strategies

class ConsistencyEnforcement(Enum):
    """Methods for enforcing hierarchical consistency"""
    NONE = "none"
    HARD = "hard"                      # Strict hierarchy enforcement
    SOFT = "soft"                      # Probability-based enforcement
    WEIGHTED = "weighted"              # Confidence-weighted enforcement

@dataclass
class HierarchicalLabel:
    """Represents a label in a hierarchical structure"""
    label_id: str
    name: str
    level: HierarchyLevel
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_path(self, hierarchy: 'LabelHierarchy') -> List[str]:
        """Get the path from root to this label"""
        path = []
        current = self
        
        while current:
            path.insert(0, current.label_id)
            if current.parent_id:
                current = hierarchy.get_label(current.parent_id)
            else:
                break
        
        return path
    
    def get_ancestors(self, hierarchy: 'LabelHierarchy') -> List['HierarchicalLabel']:
        """Get all ancestor labels"""
        ancestors = []
        current = self
        
        while current and current.parent_id:
            parent = hierarchy.get_label(current.parent_id)
            if parent:
                ancestors.insert(0, parent)
                current = parent
            else:
                break
        
        return ancestors
    
    def get_descendants(self, hierarchy: 'LabelHierarchy') -> List['HierarchicalLabel']:
        """Get all descendant labels"""
        descendants = []
        queue = deque([self])
        
        while queue:
            current = queue.popleft()
            for child_id in current.children_ids:
                child = hierarchy.get_label(child_id)
                if child:
                    descendants.append(child)
                    queue.append(child)
        
        return descendants
    
    def is_ancestor_of(self, other: 'HierarchicalLabel', hierarchy: 'LabelHierarchy') -> bool:
        """Check if this label is an ancestor of another"""
        other_ancestors = other.get_ancestors(hierarchy)
        return self in other_ancestors
    
    def is_leaf(self) -> bool:
        """Check if this is a leaf node"""
        return len(self.children_ids) == 0

@dataclass
class HierarchicalPrediction:
    """Represents a hierarchical classification prediction"""
    text: str
    predictions_by_level: Dict[HierarchyLevel, Dict[str, float]]
    final_path: List[str]
    final_label: str
    overall_confidence: float
    strategy_used: PredictionStrategy
    consistency_enforced: bool
    level_confidences: Dict[HierarchyLevel, float]
    explanation: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class LabelHierarchy:
    """Manages hierarchical label structure"""
    
    def __init__(self):
        self.labels: Dict[str, HierarchicalLabel] = {}
        self.root_labels: List[str] = []
        self.level_labels: Dict[HierarchyLevel, List[str]] = defaultdict(list)
        self.parent_child_map: Dict[str, List[str]] = defaultdict(list)
        
    def add_label(self, label: HierarchicalLabel):
        """Add a label to the hierarchy"""
        self.labels[label.label_id] = label
        
        # Update level mapping
        self.level_labels[label.level].append(label.label_id)
        
        # Update parent-child relationships
        if label.parent_id:
            self.parent_child_map[label.parent_id].append(label.label_id)
            # Update parent's children list
            if label.parent_id in self.labels:
                parent = self.labels[label.parent_id]
                if label.label_id not in parent.children_ids:
                    parent.children_ids.append(label.label_id)
        else:
            # Root label
            if label.label_id not in self.root_labels:
                self.root_labels.append(label.label_id)
        
        logger.debug(f"Added label {label.label_id} at level {label.level.value}")
    
    def get_label(self, label_id: str) -> Optional[HierarchicalLabel]:
        """Get a label by ID"""
        return self.labels.get(label_id)
    
    def get_children(self, label_id: str) -> List[HierarchicalLabel]:
        """Get all children of a label"""
        return [self.labels[child_id] for child_id in self.parent_child_map.get(label_id, [])]
    
    def get_leaves(self) -> List[HierarchicalLabel]:
        """Get all leaf labels"""
        return [label for label in self.labels.values() if label.is_leaf()]
    
    def get_labels_at_level(self, level: HierarchyLevel) -> List[HierarchicalLabel]:
        """Get all labels at a specific level"""
        return [self.labels[label_id] for label_id in self.level_labels.get(level, [])]
    
    def validate_hierarchy(self) -> List[str]:
        """Validate the hierarchy structure"""
        issues = []
        
        # Check for orphaned labels
        for label_id, label in self.labels.items():
            if label.parent_id and label.parent_id not in self.labels:
                issues.append(f"Label {label_id} has non-existent parent {label.parent_id}")
        
        # Check for circular references
        for label_id in self.labels:
            visited = set()
            current = label_id
            while current:
                if current in visited:
                    issues.append(f"Circular reference detected involving {current}")
                    break
                visited.add(current)
                current = self.labels[current].parent_id
        
        # Check for inconsistent levels
        for label_id, label in self.labels.items():
            if label.parent_id:
                parent = self.labels.get(label.parent_id)
                if parent and parent.level.value >= label.level.value:
                    issues.append(f"Label {label_id} level inconsistent with parent {label.parent_id}")
        
        return issues
    
    def print_hierarchy(self, indent: int = 0, label_id: Optional[str] = None):
        """Print the hierarchy structure"""
        if label_id is None:
            # Print all root labels
            for root_id in self.root_labels:
                self.print_hierarchy(indent, root_id)
        else:
            label = self.get_label(label_id)
            if label:
                print("  " * indent + f"{label.name} ({label.label_id}) - Level {label.level.value}")
                for child_id in label.children_ids:
                    self.print_hierarchy(indent + 1, child_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert hierarchy to dictionary"""
        return {
            "labels": {
                label_id: {
                    "name": label.name,
                    "level": label.level.value,
                    "parent_id": label.parent_id,
                    "children_ids": label.children_ids,
                    "description": label.description,
                    "keywords": label.keywords,
                    "examples": label.examples,
                    "weight": label.weight,
                    "metadata": label.metadata
                }
                for label_id, label in self.labels.items()
            },
            "root_labels": self.root_labels
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LabelHierarchy':
        """Create hierarchy from dictionary"""
        hierarchy = cls()
        
        # Create labels
        for label_id, label_data in data["labels"].items():
            label = HierarchicalLabel(
                label_id=label_id,
                name=label_data["name"],
                level=HierarchyLevel(label_data["level"]),
                parent_id=label_data.get("parent_id"),
                children_ids=label_data.get("children_ids", []),
                description=label_data.get("description"),
                keywords=label_data.get("keywords", []),
                examples=label_data.get("examples", []),
                weight=label_data.get("weight", 1.0),
                metadata=label_data.get("metadata", {})
            )
            hierarchy.add_label(label)
        
        return hierarchy

class HierarchicalClassifier:
    """Hierarchical text classifier"""
    
    def __init__(self, 
                 hierarchy: LabelHierarchy,
                 strategy: PredictionStrategy = PredictionStrategy.TOP_DOWN,
                 consistency: ConsistencyEnforcement = ConsistencyEnforcement.SOFT):
        self.hierarchy = hierarchy
        self.strategy = strategy
        self.consistency = consistency
        self.classifiers: Dict[str, Any] = {}  # Classifiers per level/node
        self.vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
        self.is_trained = False
        
        logger.info(f"✅ Hierarchical classifier initialized with {strategy.value} strategy")
    
    def train(self, texts: List[str], labels: List[str]):
        """Train the hierarchical classifier"""
        logger.info(f"Training hierarchical classifier with {len(texts)} samples")
        
        # Vectorize texts
        X = self.vectorizer.fit_transform(texts)
        
        if self.strategy == PredictionStrategy.TOP_DOWN:
            self._train_top_down(X, labels)
        elif self.strategy == PredictionStrategy.BOTTOM_UP:
            self._train_bottom_up(X, labels)
        elif self.strategy == PredictionStrategy.GLOBAL:
            self._train_global(X, labels)
        elif self.strategy == PredictionStrategy.LOCAL:
            self._train_local(X, labels)
        elif self.strategy == PredictionStrategy.HYBRID:
            self._train_hybrid(X, labels)
        
        self.is_trained = True
        logger.info("✅ Hierarchical classifier training completed")
    
    def _train_top_down(self, X, labels):
        """Train classifiers in top-down manner"""
        # Group labels by level
        label_levels = defaultdict(list)
        
        for label in labels:
            label_obj = self.hierarchy.get_label(label)
            if label_obj:
                # Add labels at each level in the path
                path = label_obj.get_path(self.hierarchy)
                for i, path_label in enumerate(path):
                    label_levels[i].append(path_label)
        
        # Train classifier for each level
        for level in sorted(label_levels.keys()):
            level_labels = label_levels[level]
            unique_labels = list(set(level_labels))
            
            if len(unique_labels) > 1:
                classifier = RandomForestClassifier(n_estimators=100, random_state=42)
                classifier.fit(X, level_labels)
                self.classifiers[f"level_{level}"] = classifier
                logger.debug(f"Trained level {level} classifier with {len(unique_labels)} classes")
    
    def _train_bottom_up(self, X, labels):
        """Train classifiers in bottom-up manner"""
        # Start with leaf classifiers
        leaf_labels = [label for label in labels if self.hierarchy.get_label(label).is_leaf()]
        
        if leaf_labels:
            classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            classifier.fit(X, leaf_labels)
            self.classifiers["leaf"] = classifier
        
        # Train aggregation classifiers for higher levels
        self._train_aggregation_classifiers(X, labels)
    
    def _train_global(self, X, labels):
        """Train single global classifier"""
        classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        classifier.fit(X, labels)
        self.classifiers["global"] = classifier
    
    def _train_local(self, X, labels):
        """Train local classifier for each non-leaf node"""
        # For each non-leaf node, train binary classifier to distinguish its children
        for label_id, label in self.hierarchy.labels.items():
            if not label.is_leaf():
                children_ids = label.children_ids
                if len(children_ids) > 1:
                    # Create training data for this node
                    node_X = []
                    node_y = []
                    
                    for i, text_label in enumerate(labels):
                        text_label_obj = self.hierarchy.get_label(text_label)
                        if text_label_obj:
                            # Check if this label is a descendant of current node
                            if text_label in children_ids or any(
                                self.hierarchy.get_label(child_id).is_ancestor_of(text_label_obj, self.hierarchy)
                                for child_id in children_ids
                            ):
                                node_X.append(i)
                                # Find which child this belongs to
                                for child_id in children_ids:
                                    child = self.hierarchy.get_label(child_id)
                                    if text_label == child_id or child.is_ancestor_of(text_label_obj, self.hierarchy):
                                        node_y.append(child_id)
                                        break
                    
                    if node_X and len(set(node_y)) > 1:
                        X_node = X[node_X]
                        classifier = RandomForestClassifier(n_estimators=50, random_state=42)
                        classifier.fit(X_node, node_y)
                        self.classifiers[label_id] = classifier
    
    def _train_hybrid(self, X, labels):
        """Train hybrid combination of strategies"""
        # Train both global and local classifiers
        self._train_global(X, labels)
        self._train_local(X, labels)
    
    def _train_aggregation_classifiers(self, X, labels):
        """Train classifiers for aggregating predictions upward"""
        # Implementation for bottom-up aggregation
        pass
    
    def predict(self, text: str) -> HierarchicalPrediction:
        """Predict hierarchical label for text"""
        if not self.is_trained:
            raise ValueError("Classifier not trained. Call train() first.")
        
        # Vectorize text
        X_text = self.vectorizer.transform([text])
        
        if self.strategy == PredictionStrategy.TOP_DOWN:
            return self._predict_top_down(text, X_text)
        elif self.strategy == PredictionStrategy.BOTTOM_UP:
            return self._predict_bottom_up(text, X_text)
        elif self.strategy == PredictionStrategy.GLOBAL:
            return self._predict_global(text, X_text)
        elif self.strategy == PredictionStrategy.LOCAL:
            return self._predict_local(text, X_text)
        elif self.strategy == PredictionStrategy.HYBRID:
            return self._predict_hybrid(text, X_text)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def _predict_top_down(self, text: str, X_text) -> HierarchicalPrediction:
        """Predict using top-down strategy"""
        predictions_by_level = {}
        path = []
        confidences = {}
        
        # Start from level 0 and work down
        level = 0
        current_candidates = self.hierarchy.root_labels
        
        while current_candidates and f"level_{level}" in self.classifiers:
            classifier = self.classifiers[f"level_{level}"]
            
            # Get probabilities for current level
            if hasattr(classifier, 'predict_proba'):
                probas = classifier.predict_proba(X_text)[0]
                classes = classifier.classes_
                
                # Create probability dictionary
                level_probs = {}
                for i, class_name in enumerate(classes):
                    if class_name in current_candidates:
                        level_probs[class_name] = probas[i]
                
                predictions_by_level[HierarchyLevel(level)] = level_probs
                
                # Select best candidate
                if level_probs:
                    best_label = max(level_probs, key=level_probs.get)
                    path.append(best_label)
                    confidences[HierarchyLevel(level)] = level_probs[best_label]
                    
                    # Get children for next level
                    label_obj = self.hierarchy.get_label(best_label)
                    if label_obj:
                        current_candidates = label_obj.children_ids
                    else:
                        break
                else:
                    break
            else:
                break
            
            level += 1
        
        # Calculate overall confidence
        overall_confidence = np.mean(list(confidences.values())) if confidences else 0.0
        
        # Apply consistency enforcement
        if self.consistency != ConsistencyEnforcement.NONE:
            path = self._enforce_consistency(path, predictions_by_level)
        
        final_label = path[-1] if path else "unknown"
        
        explanation = self._generate_explanation(predictions_by_level, path, "top-down")
        
        return HierarchicalPrediction(
            text=text,
            predictions_by_level=predictions_by_level,
            final_path=path,
            final_label=final_label,
            overall_confidence=overall_confidence,
            strategy_used=self.strategy,
            consistency_enforced=self.consistency != ConsistencyEnforcement.NONE,
            level_confidences=confidences,
            explanation=explanation
        )
    
    def _predict_bottom_up(self, text: str, X_text) -> HierarchicalPrediction:
        """Predict using bottom-up strategy"""
        predictions_by_level = {}
        
        # Start with leaf prediction
        if "leaf" in self.classifiers:
            classifier = self.classifiers["leaf"]
            if hasattr(classifier, 'predict_proba'):
                probas = classifier.predict_proba(X_text)[0]
                classes = classifier.classes_
                
                leaf_probs = {classes[i]: probas[i] for i in range(len(classes))}
                predictions_by_level[HierarchyLevel.LEAF] = leaf_probs
                
                # Get best leaf prediction
                best_leaf = max(leaf_probs, key=leaf_probs.get)
                leaf_obj = self.hierarchy.get_label(best_leaf)
                
                if leaf_obj:
                    # Build path from leaf to root
                    path = leaf_obj.get_path(self.hierarchy)
                    
                    # Aggregate probabilities upward
                    self._aggregate_probabilities_upward(predictions_by_level, leaf_probs)
                    
                    overall_confidence = leaf_probs[best_leaf]
                    explanation = self._generate_explanation(predictions_by_level, path, "bottom-up")
                    
                    return HierarchicalPrediction(
                        text=text,
                        predictions_by_level=predictions_by_level,
                        final_path=path,
                        final_label=best_leaf,
                        overall_confidence=overall_confidence,
                        strategy_used=self.strategy,
                        consistency_enforced=True,
                        level_confidences={HierarchyLevel.LEAF: overall_confidence},
                        explanation=explanation
                    )
        
        # Fallback to global prediction
        return self._predict_global(text, X_text)
    
    def _predict_global(self, text: str, X_text) -> HierarchicalPrediction:
        """Predict using global strategy"""
        if "global" in self.classifiers:
            classifier = self.classifiers["global"]
            prediction = classifier.predict(X_text)[0]
            
            if hasattr(classifier, 'predict_proba'):
                probas = classifier.predict_proba(X_text)[0]
                classes = classifier.classes_
                confidence = max(probas)
                
                all_probs = {classes[i]: probas[i] for i in range(len(classes))}
            else:
                confidence = 0.5
                all_probs = {prediction: confidence}
            
            # Get path for predicted label
            label_obj = self.hierarchy.get_label(prediction)
            if label_obj:
                path = label_obj.get_path(self.hierarchy)
            else:
                path = [prediction]
            
            # Organize predictions by level
            predictions_by_level = {HierarchyLevel.LEAF: all_probs}
            
            explanation = self._generate_explanation(predictions_by_level, path, "global")
            
            return HierarchicalPrediction(
                text=text,
                predictions_by_level=predictions_by_level,
                final_path=path,
                final_label=prediction,
                overall_confidence=confidence,
                strategy_used=self.strategy,
                consistency_enforced=True,
                level_confidences={HierarchyLevel.LEAF: confidence},
                explanation=explanation
            )
        
        raise ValueError("Global classifier not trained")
    
    def _predict_local(self, text: str, X_text) -> HierarchicalPrediction:
        """Predict using local strategy"""
        predictions_by_level = {}
        path = []
        confidences = {}
        
        # Start from root and traverse down using local classifiers
        current_nodes = self.hierarchy.root_labels
        level = 0
        
        while current_nodes:
            level_predictions = {}
            best_node = None
            best_confidence = 0.0
            
            # Try each current node's classifier
            for node_id in current_nodes:
                if node_id in self.classifiers:
                    classifier = self.classifiers[node_id]
                    if hasattr(classifier, 'predict_proba'):
                        probas = classifier.predict_proba(X_text)[0]
                        classes = classifier.classes_
                        
                        for i, class_name in enumerate(classes):
                            level_predictions[class_name] = probas[i]
                            if probas[i] > best_confidence:
                                best_confidence = probas[i]
                                best_node = class_name
            
            if best_node:
                predictions_by_level[HierarchyLevel(level)] = level_predictions
                path.append(best_node)
                confidences[HierarchyLevel(level)] = best_confidence
                
                # Move to children
                node_obj = self.hierarchy.get_label(best_node)
                if node_obj and node_obj.children_ids:
                    current_nodes = node_obj.children_ids
                else:
                    break
            else:
                break
            
            level += 1
        
        overall_confidence = np.mean(list(confidences.values())) if confidences else 0.0
        final_label = path[-1] if path else "unknown"
        
        explanation = self._generate_explanation(predictions_by_level, path, "local")
        
        return HierarchicalPrediction(
            text=text,
            predictions_by_level=predictions_by_level,
            final_path=path,
            final_label=final_label,
            overall_confidence=overall_confidence,
            strategy_used=self.strategy,
            consistency_enforced=True,
            level_confidences=confidences,
            explanation=explanation
        )
    
    def _predict_hybrid(self, text: str, X_text) -> HierarchicalPrediction:
        """Predict using hybrid strategy"""
        # Get predictions from both global and local strategies
        global_pred = self._predict_global(text, X_text)
        local_pred = self._predict_local(text, X_text)
        
        # Combine predictions (simple averaging for now)
        combined_confidence = (global_pred.overall_confidence + local_pred.overall_confidence) / 2
        
        # Choose path with higher confidence
        if global_pred.overall_confidence > local_pred.overall_confidence:
            final_prediction = global_pred
            final_prediction.overall_confidence = combined_confidence
            final_prediction.strategy_used = PredictionStrategy.HYBRID
            final_prediction.explanation = f"Hybrid: Global ({global_pred.overall_confidence:.2f}) > Local ({local_pred.overall_confidence:.2f})"
        else:
            final_prediction = local_pred
            final_prediction.overall_confidence = combined_confidence
            final_prediction.strategy_used = PredictionStrategy.HYBRID
            final_prediction.explanation = f"Hybrid: Local ({local_pred.overall_confidence:.2f}) > Global ({global_pred.overall_confidence:.2f})"
        
        return final_prediction
    
    def _enforce_consistency(self, path: List[str], predictions_by_level: Dict) -> List[str]:
        """Enforce hierarchical consistency"""
        if self.consistency == ConsistencyEnforcement.HARD:
            # Ensure each label is child of previous
            consistent_path = []
            for i, label_id in enumerate(path):
                if i == 0:
                    consistent_path.append(label_id)
                else:
                    parent_id = consistent_path[-1]
                    parent_obj = self.hierarchy.get_label(parent_id)
                    if parent_obj and label_id in parent_obj.children_ids:
                        consistent_path.append(label_id)
                    else:
                        # Find best child of parent
                        if parent_obj.children_ids:
                            consistent_path.append(parent_obj.children_ids[0])  # Default to first child
                        break
            return consistent_path
        
        return path
    
    def _aggregate_probabilities_upward(self, predictions_by_level: Dict, leaf_probs: Dict[str, float]):
        """Aggregate leaf probabilities to higher levels"""
        # Group probabilities by parent labels
        level_probs = defaultdict(lambda: defaultdict(float))
        
        for leaf_id, prob in leaf_probs.items():
            leaf_obj = self.hierarchy.get_label(leaf_id)
            if leaf_obj:
                ancestors = leaf_obj.get_ancestors(self.hierarchy)
                for i, ancestor in enumerate(ancestors):
                    level_probs[HierarchyLevel(i)][ancestor.label_id] += prob
        
        # Add aggregated probabilities to predictions
        for level, probs in level_probs.items():
            predictions_by_level[level] = dict(probs)
    
    def _generate_explanation(self, predictions_by_level: Dict, path: List[str], strategy: str) -> str:
        """Generate explanation for hierarchical prediction"""
        explanation_parts = [f"Strategy: {strategy}"]
        
        for level, probs in predictions_by_level.items():
            if probs:
                best_label = max(probs, key=probs.get)
                best_score = probs[best_label]
                explanation_parts.append(f"Level {level.value}: {best_label} ({best_score:.2f})")
        
        if path:
            explanation_parts.append(f"Final path: {' → '.join(path)}")
        
        return "; ".join(explanation_parts)
    
    def batch_predict(self, texts: List[str]) -> List[HierarchicalPrediction]:
        """Predict multiple texts"""
        return [self.predict(text) for text in texts]

def create_sample_hierarchy() -> LabelHierarchy:
    """Create a sample hierarchical label structure"""
    hierarchy = LabelHierarchy()
    
    # Level 0 (Root)
    hierarchy.add_label(HierarchicalLabel(
        label_id="technology",
        name="Technology",
        level=HierarchyLevel.ROOT,
        description="Technology-related content",
        keywords=["tech", "digital", "computer", "software", "hardware"]
    ))
    
    hierarchy.add_label(HierarchicalLabel(
        label_id="business",
        name="Business",
        level=HierarchyLevel.ROOT,
        description="Business-related content",
        keywords=["business", "company", "market", "finance", "revenue"]
    ))
    
    # Level 1
    hierarchy.add_label(HierarchicalLabel(
        label_id="software",
        name="Software",
        level=HierarchyLevel.LEVEL_1,
        parent_id="technology",
        description="Software development and applications",
        keywords=["programming", "app", "application", "code", "development"]
    ))
    
    hierarchy.add_label(HierarchicalLabel(
        label_id="hardware",
        name="Hardware",
        level=HierarchyLevel.LEVEL_1,
        parent_id="technology",
        description="Computer hardware and devices",
        keywords=["device", "processor", "memory", "storage", "chip"]
    ))
    
    hierarchy.add_label(HierarchicalLabel(
        label_id="finance",
        name="Finance",
        level=HierarchyLevel.LEVEL_1,
        parent_id="business",
        description="Financial topics and markets",
        keywords=["money", "investment", "stock", "banking", "financial"]
    ))
    
    hierarchy.add_label(HierarchicalLabel(
        label_id="marketing",
        name="Marketing",
        level=HierarchyLevel.LEVEL_1,
        parent_id="business",
        description="Marketing and advertising",
        keywords=["marketing", "advertising", "promotion", "brand", "campaign"]
    ))
    
    # Level 2
    hierarchy.add_label(HierarchicalLabel(
        label_id="mobile_apps",
        name="Mobile Apps",
        level=HierarchyLevel.LEVEL_2,
        parent_id="software",
        description="Mobile application development",
        keywords=["mobile", "app", "ios", "android", "smartphone"]
    ))
    
    hierarchy.add_label(HierarchicalLabel(
        label_id="web_development",
        name="Web Development",
        level=HierarchyLevel.LEVEL_2,
        parent_id="software",
        description="Web development and technologies",
        keywords=["web", "website", "html", "css", "javascript"]
    ))
    
    hierarchy.add_label(HierarchicalLabel(
        label_id="processors",
        name="Processors",
        level=HierarchyLevel.LEVEL_2,
        parent_id="hardware",
        description="CPU and processing units",
        keywords=["cpu", "processor", "intel", "amd", "chip"]
    ))
    
    return hierarchy

def integrate_with_production_classifier(production_system, 
                                       text: str,
                                       hierarchy: LabelHierarchy) -> Dict[str, Any]:
    """Integrate hierarchical features with production text classification system"""
    
    # Get standard classification
    standard_result = production_system.classify_text(text)
    
    # Initialize hierarchical classifier (in practice, this would be pre-trained)
    hierarchical_classifier = HierarchicalClassifier(
        hierarchy=hierarchy,
        strategy=PredictionStrategy.TOP_DOWN
    )
    
    # For demo purposes, create some mock training data
    # In practice, this would use real training data
    sample_texts = ["Sample text for training"] * 10
    sample_labels = ["mobile_apps"] * 10  # Mock labels
    
    try:
        hierarchical_classifier.train(sample_texts, sample_labels)
        hierarchical_prediction = hierarchical_classifier.predict(text)
        
        enhanced_result = {
            **standard_result,
            "hierarchical_analysis": {
                "final_label": hierarchical_prediction.final_label,
                "final_path": hierarchical_prediction.final_path,
                "overall_confidence": hierarchical_prediction.overall_confidence,
                "predictions_by_level": {
                    str(level.value): probs 
                    for level, probs in hierarchical_prediction.predictions_by_level.items()
                },
                "strategy_used": hierarchical_prediction.strategy_used.value,
                "consistency_enforced": hierarchical_prediction.consistency_enforced,
                "explanation": hierarchical_prediction.explanation
            },
            "is_hierarchical_enhanced": True
        }
        
    except Exception as e:
        logger.error(f"Hierarchical classification failed: {e}")
        enhanced_result = {
            **standard_result,
            "hierarchical_analysis": {
                "error": str(e),
                "fallback_used": True
            },
            "is_hierarchical_enhanced": False
        }
    
    return enhanced_result

def main():
    """Demo hierarchical classification features"""
    print("=== Hierarchical Classification Features Demo ===\n")
    
    # Create sample hierarchy
    hierarchy = create_sample_hierarchy()
    
    print("Hierarchy Structure:")
    hierarchy.print_hierarchy()
    print()
    
    # Validate hierarchy
    issues = hierarchy.validate_hierarchy()
    if issues:
        print("Hierarchy Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Hierarchy validation passed")
    print()
    
    # Sample texts and labels for training
    sample_texts = [
        "The new iPhone app features advanced machine learning capabilities",
        "Latest Intel processor offers 20% better performance than previous generation",
        "Stock market reached new highs following strong quarterly earnings reports",
        "Digital marketing campaigns show increased ROI with targeted advertising",
        "Web development frameworks continue to evolve with new JavaScript libraries",
        "Mobile app development requires understanding both iOS and Android platforms"
    ]
    
    sample_labels = [
        "mobile_apps", "processors", "finance", "marketing", "web_development", "mobile_apps"
    ]
    
    # Initialize and train classifier
    classifier = HierarchicalClassifier(
        hierarchy=hierarchy,
        strategy=PredictionStrategy.TOP_DOWN,
        consistency=ConsistencyEnforcement.SOFT
    )
    
    print("Training hierarchical classifier...")
    classifier.train(sample_texts, sample_labels)
    print("✅ Training completed\n")
    
    # Test predictions
    test_texts = [
        "Building responsive websites with modern CSS frameworks",
        "The latest smartphone processors deliver exceptional performance",
        "Investment portfolio management in volatile markets"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"Test {i}: {text}")
        prediction = classifier.predict(text)
        
        print(f"  Final prediction: {prediction.final_label}")
        print(f"  Confidence: {prediction.overall_confidence:.2f}")
        print(f"  Path: {' → '.join(prediction.final_path)}")
        print(f"  Strategy: {prediction.strategy_used.value}")
        print(f"  Explanation: {prediction.explanation}")
        print()

if __name__ == "__main__":
    main()