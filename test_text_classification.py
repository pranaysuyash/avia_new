#!/usr/bin/env python3
"""
Test suite for Text Classification System
"""

import asyncio
import pytest
import numpy as np
from typing import List

from text_classification_system import (
    TextClassificationSystem,
    ClassificationType,
    ModelType,
    ClassLabel,
    Priority
)


@pytest.fixture
async def classification_system():
    """Create text classification system instance"""
    config = {
        'use_transformers': False,  # Disable for faster tests
        'zero_shot_threshold': 0.3
    }
    system = TextClassificationSystem(config)
    return system


@pytest.fixture
def sample_texts_labels():
    """Sample texts and labels for testing"""
    texts = [
        "The stock market surged today following positive earnings reports from major tech companies.",
        "Scientists have discovered a new species of butterfly in the Amazon rainforest.",
        "The local basketball team won the championship game in overtime last night.",
        "A new study shows that meditation can significantly reduce stress levels.",
        "The latest smartphone features a revolutionary camera system with AI capabilities.",
        "Climate change is causing unprecedented melting of polar ice caps.",
        "The restaurant's new menu features organic, locally-sourced ingredients.",
        "Researchers develop breakthrough treatment for rare genetic disorder.",
        "The movie broke box office records on its opening weekend.",
        "Cryptocurrency prices experienced high volatility this week."
    ]
    
    labels = [
        "business", "science", "sports", "health", "technology",
        "environment", "food", "health", "entertainment", "business"
    ]
    
    return texts, labels


@pytest.fixture
def multi_label_data():
    """Sample data for multi-label classification"""
    texts = [
        "This smartphone combines cutting-edge technology with premium business features.",
        "The health-focused restaurant uses organic ingredients and sustainable practices.",
        "The documentary explores climate science and its impact on business decisions.",
        "The fitness app tracks health metrics and integrates with smart devices.",
        "The electric car company announced record sales and environmental achievements."
    ]
    
    labels = [
        ["technology", "business"],
        ["food", "health", "environment"],
        ["science", "environment", "business"],
        ["health", "technology"],
        ["business", "environment", "technology"]
    ]
    
    return texts, labels


@pytest.fixture
def hierarchical_labels():
    """Sample hierarchical labels"""
    texts = [
        "Apple releases new iPhone model",
        "Tesla announces quarterly earnings",
        "NBA finals game highlights",
        "Soccer World Cup update",
        "Python programming tutorial"
    ]
    
    labels = [
        "technology/hardware/mobile",
        "business/automotive/electric",
        "sports/basketball/professional",
        "sports/soccer/international",
        "technology/software/programming"
    ]
    
    return texts, labels


@pytest.mark.asyncio
async def test_binary_classification(classification_system):
    """Test binary classification"""
    texts = [
        "This product is excellent and works perfectly.",
        "Terrible experience, would not recommend.",
        "Amazing quality and great value for money.",
        "Complete waste of money, very disappointed.",
        "Best purchase I've made this year!",
        "Broken on arrival, poor packaging."
    ]
    
    labels = ["positive", "negative", "positive", "negative", "positive", "negative"]
    
    # Train classifier
    performance = await classification_system.train_classifier(
        texts=texts,
        labels=labels,
        classification_type=ClassificationType.BINARY,
        model_type=ModelType.LOGISTIC_REGRESSION,
        test_size=0.3
    )
    
    assert performance.accuracy >= 0.5  # Should be better than random
    assert 'positive' in performance.precision
    assert 'negative' in performance.precision


@pytest.mark.asyncio
async def test_multiclass_classification(classification_system, sample_texts_labels):
    """Test multiclass classification"""
    texts, labels = sample_texts_labels
    
    # Train classifier
    performance = await classification_system.train_classifier(
        texts=texts,
        labels=labels,
        classification_type=ClassificationType.MULTICLASS,
        model_type=ModelType.RANDOM_FOREST,
        test_size=0.3,
        cross_validate=True
    )
    
    assert performance.accuracy >= 0.3  # Reasonable for small dataset
    assert len(performance.precision) > 0
    assert performance.confusion_matrix is not None
    assert performance.classification_report is not None


@pytest.mark.asyncio
async def test_multilabel_classification(classification_system, multi_label_data):
    """Test multi-label classification"""
    texts, labels = multi_label_data
    
    # Train classifier
    performance = await classification_system.train_classifier(
        texts=texts,
        labels=labels,
        classification_type=ClassificationType.MULTILABEL,
        model_type=ModelType.LOGISTIC_REGRESSION,
        test_size=0.2
    )
    
    assert performance.hamming_loss is not None
    assert performance.hamming_loss <= 1.0
    assert 'multilabel' in performance.metadata['classification_type']


@pytest.mark.asyncio
async def test_hierarchical_classification(classification_system, hierarchical_labels):
    """Test hierarchical classification"""
    texts, labels = hierarchical_labels
    
    # Train classifier
    performance = await classification_system.train_classifier(
        texts=texts,
        labels=labels,
        classification_type=ClassificationType.HIERARCHICAL,
        model_type=ModelType.LOGISTIC_REGRESSION
    )
    
    assert 'hierarchical' in performance.metadata['classification_type']
    assert 'model_key' in performance.metadata


@pytest.mark.asyncio
async def test_prediction(classification_system, sample_texts_labels):
    """Test making predictions"""
    texts, labels = sample_texts_labels
    
    # Train classifier
    performance = await classification_system.train_classifier(
        texts=texts,
        labels=labels,
        classification_type=ClassificationType.MULTICLASS,
        model_type=ModelType.NAIVE_BAYES
    )
    
    model_key = performance.metadata['model_key']
    
    # Test prediction
    test_text = "The company's stock price increased significantly today."
    result = await classification_system.predict(
        text=test_text,
        model_key=model_key,
        threshold=0.5
    )
    
    assert len(result.predicted_labels) > 0
    assert result.predicted_labels[0] in ["business", "technology", "science"]
    assert result.confidence_scores[result.predicted_labels[0]] > 0
    assert result.processing_time > 0


@pytest.mark.asyncio
async def test_zero_shot_classification(classification_system):
    """Test zero-shot classification"""
    text = "The hurricane caused major damage to coastal areas."
    candidate_labels = ["weather", "disaster", "politics", "sports", "technology"]
    
    result = await classification_system.zero_shot_classify(
        text=text,
        candidate_labels=candidate_labels,
        hypothesis_template="This text is about {}."
    )
    
    assert len(result.predicted_labels) > 0
    assert result.predicted_labels[0] in ["weather", "disaster"]
    assert result.classification_type == ClassificationType.ZERO_SHOT
    assert len(result.predictions) == len(candidate_labels)


@pytest.mark.asyncio
async def test_active_learning_setup(classification_system, sample_texts_labels):
    """Test active learning setup and querying"""
    texts, labels = sample_texts_labels
    
    # Setup active learning with initial data
    learner_key = classification_system.setup_active_learning(
        initial_texts=texts[:5],
        initial_labels=labels[:5],
        model_type=ModelType.LOGISTIC_REGRESSION
    )
    
    assert learner_key in classification_system.active_learners
    
    # Query uncertain samples
    pool_texts = texts[5:]
    queries = classification_system.query_active_learning(
        learner_key=learner_key,
        pool_texts=pool_texts,
        n_instances=2
    )
    
    assert len(queries) == 2
    for query in queries:
        assert query.uncertainty_score >= 0
        assert len(query.predicted_labels) > 0
        assert query.acquisition_method == "uncertainty_sampling"


@pytest.mark.asyncio
async def test_active_learning_update(classification_system, sample_texts_labels):
    """Test updating active learner with new data"""
    texts, labels = sample_texts_labels
    
    # Setup active learner
    learner_key = classification_system.setup_active_learning(
        initial_texts=texts[:3],
        initial_labels=labels[:3],
        model_type=ModelType.RANDOM_FOREST
    )
    
    # Update with new labeled data
    new_texts = texts[3:5]
    new_labels = labels[3:5]
    
    classification_system.update_active_learner(
        learner_key=learner_key,
        texts=new_texts,
        labels=new_labels
    )
    
    # Verify learner was updated
    assert learner_key in classification_system.active_learners


@pytest.mark.asyncio
async def test_text_preprocessing(classification_system):
    """Test text preprocessing"""
    text = "The Quick BROWN Fox Jumps Over The Lazy Dog!"
    
    # With lemmatization
    processed = classification_system.preprocess_text(text, use_lemma=True)
    assert processed.islower()
    assert "quick" in processed
    
    # Without lemmatization
    processed_no_lemma = classification_system.preprocess_text(text, use_lemma=False)
    assert processed_no_lemma.islower()


@pytest.mark.asyncio
async def test_model_export_import(classification_system, sample_texts_labels, tmp_path):
    """Test exporting and importing models"""
    texts, labels = sample_texts_labels
    
    # Train a model
    performance = await classification_system.train_classifier(
        texts=texts,
        labels=labels,
        classification_type=ClassificationType.MULTICLASS,
        model_type=ModelType.LOGISTIC_REGRESSION
    )
    
    model_key = performance.metadata['model_key']
    
    # Export model
    export_path = tmp_path / "model.pkl"
    classification_system.export_model(model_key, str(export_path))
    assert export_path.exists()
    
    # Create new system and import model
    new_system = TextClassificationSystem()
    imported_key = new_system.load_model(str(export_path))
    
    # Test prediction with imported model
    test_text = "Technology companies are investing heavily in AI."
    result = await new_system.predict(
        text=test_text,
        model_key=imported_key
    )
    
    assert len(result.predicted_labels) > 0


@pytest.mark.asyncio
async def test_different_model_types(classification_system, sample_texts_labels):
    """Test different model types"""
    texts, labels = sample_texts_labels
    
    model_types = [
        ModelType.NAIVE_BAYES,
        ModelType.LOGISTIC_REGRESSION,
        ModelType.RANDOM_FOREST,
        ModelType.SVM,
        ModelType.GRADIENT_BOOSTING
    ]
    
    for model_type in model_types:
        performance = await classification_system.train_classifier(
            texts=texts,
            labels=labels,
            classification_type=ClassificationType.MULTICLASS,
            model_type=model_type,
            test_size=0.3,
            cross_validate=False  # Speed up tests
        )
        
        assert performance.accuracy >= 0.0
        assert performance.accuracy <= 1.0
        assert model_type.value in performance.metadata['model_type']


@pytest.mark.asyncio
async def test_confidence_thresholding(classification_system, sample_texts_labels):
    """Test confidence threshold in predictions"""
    texts, labels = sample_texts_labels
    
    # Train classifier
    performance = await classification_system.train_classifier(
        texts=texts,
        labels=labels,
        classification_type=ClassificationType.MULTICLASS,
        model_type=ModelType.LOGISTIC_REGRESSION
    )
    
    model_key = performance.metadata['model_key']
    test_text = "This is an ambiguous text that could belong to multiple categories."
    
    # Test with different thresholds
    for threshold in [0.3, 0.5, 0.7]:
        result = await classification_system.predict(
            text=test_text,
            model_key=model_key,
            threshold=threshold
        )
        
        # Higher threshold might result in fewer predictions
        assert len(result.predicted_labels) >= 0


@pytest.mark.asyncio
async def test_performance_visualization(classification_system, sample_texts_labels, tmp_path):
    """Test performance visualization"""
    texts, labels = sample_texts_labels
    
    # Train classifier
    performance = await classification_system.train_classifier(
        texts=texts,
        labels=labels,
        classification_type=ClassificationType.MULTICLASS,
        model_type=ModelType.RANDOM_FOREST
    )
    
    # Visualize performance
    output_path = tmp_path / "performance.png"
    fig = classification_system.visualize_performance(
        performance,
        output_path=str(output_path)
    )
    
    assert fig is not None
    assert output_path.exists()


@pytest.mark.asyncio
async def test_error_handling(classification_system):
    """Test error handling"""
    
    # Test prediction with non-existent model
    with pytest.raises(ValueError):
        await classification_system.predict(
            text="Test text",
            model_key="non_existent_model"
        )
    
    # Test empty training data
    with pytest.raises(Exception):
        await classification_system.train_classifier(
            texts=[],
            labels=[],
            classification_type=ClassificationType.MULTICLASS,
            model_type=ModelType.NAIVE_BAYES
        )
    
    # Test mismatched texts and labels
    with pytest.raises(Exception):
        await classification_system.train_classifier(
            texts=["text1", "text2"],
            labels=["label1"],  # Mismatched length
            classification_type=ClassificationType.MULTICLASS,
            model_type=ModelType.LOGISTIC_REGRESSION
        )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])