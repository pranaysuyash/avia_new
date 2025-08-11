#!/usr/bin/env python3
"""
Test Suite for AI Model Management System
Tests for Task 65: AI model versioning and A/B testing

This module provides comprehensive tests for:
- Model registry and version management
- A/B testing framework functionality
- Performance monitoring and drift detection
- Cost optimization algorithms
"""

import unittest
import tempfile
import os
import sqlite3
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import uuid

# Import the modules to test
try:
    from ai_model_management import (
        ModelRegistry, ABTestingFramework, ModelPerformanceMonitor,
        CostOptimizer, ModelManagementService, ModelStatus, ExperimentStatus,
        ModelMetadata, ModelPerformanceMetrics, ABTestExperiment, ExperimentResult
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure ai_model_management.py is in the same directory")
    exit(1)

class TestModelRegistry(unittest.TestCase):
    """Test cases for ModelRegistry class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.registry = ModelRegistry(self.temp_db.name)
        
        # Create sample model metadata
        self.sample_metadata = ModelMetadata(
            model_id=str(uuid.uuid4()),
            name="test-model",
            version="1.0.0",
            description="Test model for unit testing",
            model_type="transcription",
            framework="openai",
            created_at=datetime.now(),
            created_by="test_user",
            status=ModelStatus.DEVELOPMENT,
            tags=["test", "sample"],
            parameters={"temperature": 0.1, "max_tokens": 1000}
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_db.name)
    
    def test_register_model(self):
        """Test model registration"""
        model_id = self.registry.register_model(self.sample_metadata)
        self.assertEqual(model_id, self.sample_metadata.model_id)
        
        # Verify model was stored
        retrieved_model = self.registry.get_model(model_id)
        self.assertIsNotNone(retrieved_model)
        self.assertEqual(retrieved_model.name, self.sample_metadata.name)
        self.assertEqual(retrieved_model.version, self.sample_metadata.version)
    
    def test_register_duplicate_model(self):
        """Test that duplicate model registration fails"""
        self.registry.register_model(self.sample_metadata)
        
        # Try to register the same model again
        duplicate_metadata = ModelMetadata(
            model_id=str(uuid.uuid4()),  # Different ID
            name=self.sample_metadata.name,  # Same name
            version=self.sample_metadata.version,  # Same version
            description="Duplicate model",
            model_type="transcription",
            framework="openai",
            created_at=datetime.now(),
            created_by="test_user",
            status=ModelStatus.DEVELOPMENT,
            tags=[],
            parameters={}
        )
        
        with self.assertRaises(ValueError):
            self.registry.register_model(duplicate_metadata)
    
    def test_get_nonexistent_model(self):
        """Test getting a model that doesn't exist"""
        result = self.registry.get_model("nonexistent-id")
        self.assertIsNone(result)
    
    def test_list_models(self):
        """Test listing models with filters"""
        # Register multiple models
        models = []
        for i in range(3):
            metadata = ModelMetadata(
                model_id=str(uuid.uuid4()),
                name=f"test-model-{i}",
                version="1.0.0",
                description=f"Test model {i}",
                model_type="transcription" if i % 2 == 0 else "analysis",
                framework="openai",
                created_at=datetime.now(),
                created_by="test_user",
                status=ModelStatus.DEVELOPMENT,
                tags=["test"],
                parameters={}
            )
            models.append(metadata)
            self.registry.register_model(metadata)
        
        # Test listing all models
        all_models = self.registry.list_models()
        self.assertEqual(len(all_models), 3)
        
        # Test filtering by model type
        transcription_models = self.registry.list_models(model_type="transcription")
        self.assertEqual(len(transcription_models), 2)
        
        analysis_models = self.registry.list_models(model_type="analysis")
        self.assertEqual(len(analysis_models), 1)
    
    def test_update_model_status(self):
        """Test updating model status"""
        model_id = self.registry.register_model(self.sample_metadata)
        
        # Update status
        self.registry.update_model_status(model_id, ModelStatus.PRODUCTION)
        
        # Verify status was updated
        updated_model = self.registry.get_model(model_id)
        self.assertEqual(updated_model.status, ModelStatus.PRODUCTION)
    
    def test_record_and_get_metrics(self):
        """Test recording and retrieving performance metrics"""
        model_id = self.registry.register_model(self.sample_metadata)
        
        # Record some metrics
        metrics = [
            ModelPerformanceMetrics(
                model_id=model_id,
                timestamp=datetime.now() - timedelta(hours=i),
                accuracy=0.85 + (i * 0.01),
                latency_ms=100 + (i * 10),
                cost_per_request=0.001 + (i * 0.0001)
            )
            for i in range(5)
        ]
        
        for metric in metrics:
            self.registry.record_metrics(metric)
        
        # Retrieve metrics
        retrieved_metrics = self.registry.get_model_metrics(model_id)
        self.assertEqual(len(retrieved_metrics), 5)
        
        # Test date filtering
        start_date = datetime.now() - timedelta(hours=2)
        filtered_metrics = self.registry.get_model_metrics(
            model_id, start_date=start_date
        )
        self.assertLessEqual(len(filtered_metrics), 3)

class TestABTestingFramework(unittest.TestCase):
    """Test cases for ABTestingFramework class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary databases
        self.temp_registry_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_registry_db.close()
        self.temp_experiments_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_experiments_db.close()
        
        self.registry = ModelRegistry(self.temp_registry_db.name)
        self.ab_testing = ABTestingFramework(self.registry, self.temp_experiments_db.name)
        
        # Create sample models for testing
        self.control_model_id = str(uuid.uuid4())
        self.treatment_model_id = str(uuid.uuid4())
        
        control_metadata = ModelMetadata(
            model_id=self.control_model_id,
            name="control-model",
            version="1.0.0",
            description="Control model",
            model_type="transcription",
            framework="openai",
            created_at=datetime.now(),
            created_by="test_user",
            status=ModelStatus.PRODUCTION,
            tags=["control"],
            parameters={}
        )
        
        treatment_metadata = ModelMetadata(
            model_id=self.treatment_model_id,
            name="treatment-model",
            version="1.1.0",
            description="Treatment model",
            model_type="transcription",
            framework="openai",
            created_at=datetime.now(),
            created_by="test_user",
            status=ModelStatus.PRODUCTION,
            tags=["treatment"],
            parameters={}
        )
        
        self.registry.register_model(control_metadata)
        self.registry.register_model(treatment_metadata)
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_registry_db.name)
        os.unlink(self.temp_experiments_db.name)
    
    def test_create_experiment(self):
        """Test creating an A/B test experiment"""
        experiment = ABTestExperiment(
            experiment_id=str(uuid.uuid4()),
            name="Test Experiment",
            description="Testing A/B framework",
            control_model_id=self.control_model_id,
            treatment_model_id=self.treatment_model_id,
            traffic_split=0.5,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            status=ExperimentStatus.DRAFT,
            success_metrics=["accuracy", "latency_ms"],
            minimum_sample_size=1000,
            confidence_level=0.95,
            created_by="test_user",
            tags=["test"],
            metadata={}
        )
        
        experiment_id = self.ab_testing.create_experiment(experiment)
        self.assertEqual(experiment_id, experiment.experiment_id)
    
    def test_create_experiment_invalid_models(self):
        """Test creating experiment with invalid model IDs"""
        experiment = ABTestExperiment(
            experiment_id=str(uuid.uuid4()),
            name="Invalid Experiment",
            description="Testing with invalid models",
            control_model_id="invalid-id",
            treatment_model_id=self.treatment_model_id,
            traffic_split=0.5,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            status=ExperimentStatus.DRAFT,
            success_metrics=["accuracy"],
            minimum_sample_size=1000,
            confidence_level=0.95,
            created_by="test_user",
            tags=[],
            metadata={}
        )
        
        with self.assertRaises(ValueError):
            self.ab_testing.create_experiment(experiment)
    
    def test_assign_variant(self):
        """Test user variant assignment"""
        # Create and start experiment
        experiment = ABTestExperiment(
            experiment_id=str(uuid.uuid4()),
            name="Assignment Test",
            description="Testing variant assignment",
            control_model_id=self.control_model_id,
            treatment_model_id=self.treatment_model_id,
            traffic_split=0.5,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            status=ExperimentStatus.RUNNING,
            success_metrics=["accuracy"],
            minimum_sample_size=100,
            confidence_level=0.95,
            created_by="test_user",
            tags=[],
            metadata={}
        )
        
        experiment_id = self.ab_testing.create_experiment(experiment)
        
        # Test consistent assignment
        user_id = "test_user_123"
        variant1 = self.ab_testing.assign_variant(experiment_id, user_id)
        variant2 = self.ab_testing.assign_variant(experiment_id, user_id)
        
        self.assertEqual(variant1, variant2)  # Should be consistent
        self.assertIn(variant1, ["control", "treatment"])
    
    def test_record_experiment_data(self):
        """Test recording experiment data"""
        # Create and start experiment
        experiment = ABTestExperiment(
            experiment_id=str(uuid.uuid4()),
            name="Data Recording Test",
            description="Testing data recording",
            control_model_id=self.control_model_id,
            treatment_model_id=self.treatment_model_id,
            traffic_split=0.5,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            status=ExperimentStatus.RUNNING,
            success_metrics=["accuracy", "latency_ms"],
            minimum_sample_size=100,
            confidence_level=0.95,
            created_by="test_user",
            tags=[],
            metadata={}
        )
        
        experiment_id = self.ab_testing.create_experiment(experiment)
        
        # Record some data points
        test_data = [
            ("control", "user1", {"accuracy": 0.85, "latency_ms": 120}),
            ("treatment", "user2", {"accuracy": 0.87, "latency_ms": 110}),
            ("control", "user3", {"accuracy": 0.84, "latency_ms": 125}),
            ("treatment", "user4", {"accuracy": 0.88, "latency_ms": 105})
        ]
        
        for variant, user_id, metrics in test_data:
            self.ab_testing.record_experiment_data(experiment_id, variant, user_id, metrics)
        
        # Verify data was recorded (would need to check database directly)
        # This is a basic test that the method doesn't raise exceptions
        self.assertTrue(True)
    
    def test_analyze_experiment(self):
        """Test experiment analysis"""
        # Create experiment
        experiment = ABTestExperiment(
            experiment_id=str(uuid.uuid4()),
            name="Analysis Test",
            description="Testing experiment analysis",
            control_model_id=self.control_model_id,
            treatment_model_id=self.treatment_model_id,
            traffic_split=0.5,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            status=ExperimentStatus.RUNNING,
            success_metrics=["accuracy", "latency_ms"],
            minimum_sample_size=10,  # Low for testing
            confidence_level=0.95,
            created_by="test_user",
            tags=[],
            metadata={}
        )
        
        experiment_id = self.ab_testing.create_experiment(experiment)
        
        # Add sample data
        import random
        for i in range(20):
            variant = "control" if i % 2 == 0 else "treatment"
            user_id = f"user_{i}"
            
            # Treatment performs slightly better
            base_accuracy = 0.85 if variant == "control" else 0.87
            base_latency = 120 if variant == "control" else 110
            
            metrics = {
                "accuracy": base_accuracy + random.uniform(-0.02, 0.02),
                "latency_ms": base_latency + random.uniform(-10, 10)
            }
            
            self.ab_testing.record_experiment_data(experiment_id, variant, user_id, metrics)
        
        # Analyze experiment
        results = self.ab_testing.analyze_experiment(experiment_id)
        
        self.assertIsInstance(results, ExperimentResult)
        self.assertEqual(results.experiment_id, experiment_id)
        self.assertIn("accuracy", results.control_metrics)
        self.assertIn("accuracy", results.treatment_metrics)
        self.assertIsNotNone(results.recommendation)

class TestModelPerformanceMonitor(unittest.TestCase):
    """Test cases for ModelPerformanceMonitor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.registry = ModelRegistry(self.temp_db.name)
        self.monitor = ModelPerformanceMonitor(self.registry)
        
        # Create sample model
        self.model_id = str(uuid.uuid4())
        metadata = ModelMetadata(
            model_id=self.model_id,
            name="test-model",
            version="1.0.0",
            description="Test model",
            model_type="transcription",
            framework="openai",
            created_at=datetime.now(),
            created_by="test_user",
            status=ModelStatus.PRODUCTION,
            tags=["test"],
            parameters={}
        )
        self.registry.register_model(metadata)
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_db.name)
    
    def test_check_model_health_insufficient_data(self):
        """Test health check with insufficient data"""
        health = self.monitor.check_model_health(self.model_id)
        self.assertEqual(health['status'], 'insufficient_data')
    
    def test_check_model_health_with_data(self):
        """Test health check with sufficient data"""
        # Add baseline metrics (7+ days ago)
        baseline_start = datetime.now() - timedelta(days=10)
        for i in range(10):
            metrics = ModelPerformanceMetrics(
                model_id=self.model_id,
                timestamp=baseline_start + timedelta(hours=i),
                accuracy=0.85,
                latency_ms=100,
                error_rate=0.01,
                cost_per_request=0.001
            )
            self.registry.record_metrics(metrics)
        
        # Add current metrics (last 24 hours)
        current_start = datetime.now() - timedelta(hours=12)
        for i in range(5):
            metrics = ModelPerformanceMetrics(
                model_id=self.model_id,
                timestamp=current_start + timedelta(hours=i),
                accuracy=0.84,  # Slight drop
                latency_ms=105,  # Slight increase
                error_rate=0.01,
                cost_per_request=0.001
            )
            self.registry.record_metrics(metrics)
        
        health = self.monitor.check_model_health(self.model_id)
        self.assertIn(health['status'], ['healthy', 'degraded', 'unhealthy'])
        self.assertIn('baseline_metrics', health)
        self.assertIn('current_metrics', health)
    
    def test_check_model_health_with_alerts(self):
        """Test health check that should trigger alerts"""
        # Add baseline metrics
        baseline_start = datetime.now() - timedelta(days=10)
        for i in range(10):
            metrics = ModelPerformanceMetrics(
                model_id=self.model_id,
                timestamp=baseline_start + timedelta(hours=i),
                accuracy=0.90,
                latency_ms=100,
                error_rate=0.01,
                cost_per_request=0.001
            )
            self.registry.record_metrics(metrics)
        
        # Add current metrics with significant degradation
        current_start = datetime.now() - timedelta(hours=12)
        for i in range(5):
            metrics = ModelPerformanceMetrics(
                model_id=self.model_id,
                timestamp=current_start + timedelta(hours=i),
                accuracy=0.80,  # Significant drop (>5%)
                latency_ms=250,  # Significant increase (>2x)
                error_rate=0.15,  # Significant increase
                cost_per_request=0.002  # Significant increase
            )
            self.registry.record_metrics(metrics)
        
        health = self.monitor.check_model_health(self.model_id)
        self.assertGreater(len(health['alerts']), 0)
        self.assertIn(health['status'], ['degraded', 'unhealthy'])

class TestCostOptimizer(unittest.TestCase):
    """Test cases for CostOptimizer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.registry = ModelRegistry(self.temp_db.name)
        self.optimizer = CostOptimizer(self.registry)
        
        # Create sample models with different performance characteristics
        self.models = []
        model_configs = [
            {"name": "fast-model", "accuracy": 0.80, "latency": 50, "cost": 0.0005},
            {"name": "balanced-model", "accuracy": 0.85, "latency": 100, "cost": 0.001},
            {"name": "accurate-model", "accuracy": 0.90, "latency": 200, "cost": 0.002}
        ]
        
        for i, config in enumerate(model_configs):
            model_id = str(uuid.uuid4())
            metadata = ModelMetadata(
                model_id=model_id,
                name=config["name"],
                version="1.0.0",
                description=f"Test model {i}",
                model_type="transcription",
                framework="openai",
                created_at=datetime.now(),
                created_by="test_user",
                status=ModelStatus.PRODUCTION,
                tags=["test"],
                parameters={}
            )
            self.registry.register_model(metadata)
            self.models.append((model_id, config))
            
            # Add performance metrics
            for j in range(10):
                metrics = ModelPerformanceMetrics(
                    model_id=model_id,
                    timestamp=datetime.now() - timedelta(hours=j),
                    accuracy=config["accuracy"] + (j * 0.001),  # Slight variation
                    latency_ms=config["latency"] + (j * 2),
                    cost_per_request=config["cost"] + (j * 0.00001)
                )
                self.registry.record_metrics(metrics)
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_db.name)
    
    def test_recommend_model_high_accuracy_requirement(self):
        """Test model recommendation with high accuracy requirement"""
        requirements = {
            'min_accuracy': 0.88,
            'max_latency_ms': 300,
            'max_cost_per_request': 0.003
        }
        
        recommended_id = self.optimizer.recommend_model("transcription", requirements)
        
        # Should recommend the accurate model
        self.assertIsNotNone(recommended_id)
        
        # Verify it's the accurate model
        accurate_model_id = next(
            model_id for model_id, config in self.models 
            if config["name"] == "accurate-model"
        )
        self.assertEqual(recommended_id, accurate_model_id)
    
    def test_recommend_model_low_latency_requirement(self):
        """Test model recommendation with low latency requirement"""
        requirements = {
            'min_accuracy': 0.75,
            'max_latency_ms': 80,
            'max_cost_per_request': 0.001
        }
        
        recommended_id = self.optimizer.recommend_model("transcription", requirements)
        
        # Should recommend the fast model
        self.assertIsNotNone(recommended_id)
        
        fast_model_id = next(
            model_id for model_id, config in self.models 
            if config["name"] == "fast-model"
        )
        self.assertEqual(recommended_id, fast_model_id)
    
    def test_recommend_model_no_match(self):
        """Test model recommendation with impossible requirements"""
        requirements = {
            'min_accuracy': 0.95,  # Higher than any model
            'max_latency_ms': 10,   # Lower than any model
            'max_cost_per_request': 0.0001  # Lower than any model
        }
        
        recommended_id = self.optimizer.recommend_model("transcription", requirements)
        self.assertIsNone(recommended_id)

class TestModelManagementService(unittest.TestCase):
    """Test cases for ModelManagementService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.service = ModelManagementService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_db.name)
        # Clean up experiments database
        experiments_db = self.temp_db.name.replace('.db', '_experiments.db')
        if os.path.exists(experiments_db):
            os.unlink(experiments_db)
    
    def test_create_model_version(self):
        """Test creating a new model version"""
        model_id = self.service.create_model_version(
            name="test-model",
            version="1.0.0",
            description="Test model",
            model_type="transcription",
            framework="openai",
            created_by="test_user",
            parameters={"temperature": 0.1},
            tags=["test"]
        )
        
        self.assertIsNotNone(model_id)
        
        # Verify model was created
        model = self.service.registry.get_model(model_id)
        self.assertIsNotNone(model)
        self.assertEqual(model.name, "test-model")
        self.assertEqual(model.version, "1.0.0")
    
    def test_deploy_model(self):
        """Test model deployment"""
        # Create model
        model_id = self.service.create_model_version(
            name="deploy-test",
            version="1.0.0",
            description="Deployment test",
            model_type="transcription",
            framework="openai",
            created_by="test_user",
            parameters={}
        )
        
        # Deploy to production
        result = self.service.deploy_model(model_id, "production")
        self.assertTrue(result)
        
        # Verify status was updated
        model = self.service.registry.get_model(model_id)
        self.assertEqual(model.status, ModelStatus.PRODUCTION)
    
    def test_rollback_model(self):
        """Test model rollback"""
        # Create two models
        current_id = self.service.create_model_version(
            name="current-model", version="2.0.0", description="Current",
            model_type="transcription", framework="openai", created_by="test_user",
            parameters={}
        )
        
        target_id = self.service.create_model_version(
            name="target-model", version="1.0.0", description="Target",
            model_type="transcription", framework="openai", created_by="test_user",
            parameters={}
        )
        
        # Deploy both
        self.service.deploy_model(current_id, "production")
        self.service.deploy_model(target_id, "production")
        
        # Rollback
        result = self.service.rollback_model(current_id, target_id)
        self.assertTrue(result)
        
        # Verify statuses
        current_model = self.service.registry.get_model(current_id)
        target_model = self.service.registry.get_model(target_id)
        
        self.assertEqual(current_model.status, ModelStatus.DEPRECATED)
        self.assertEqual(target_model.status, ModelStatus.PRODUCTION)
    
    def test_start_ab_test(self):
        """Test starting an A/B test"""
        # Create two models
        control_id = self.service.create_model_version(
            name="control", version="1.0.0", description="Control",
            model_type="transcription", framework="openai", created_by="test_user",
            parameters={}
        )
        
        treatment_id = self.service.create_model_version(
            name="treatment", version="1.1.0", description="Treatment",
            model_type="transcription", framework="openai", created_by="test_user",
            parameters={}
        )
        
        # Deploy both
        self.service.deploy_model(control_id, "production")
        self.service.deploy_model(treatment_id, "production")
        
        # Start A/B test
        experiment_id = self.service.start_ab_test(
            name="Test Experiment",
            description="Testing A/B functionality",
            control_model_id=control_id,
            treatment_model_id=treatment_id,
            traffic_split=0.5,
            success_metrics=["accuracy", "latency_ms"],
            duration_days=7,
            created_by="test_user"
        )
        
        self.assertIsNotNone(experiment_id)
        
        # Verify experiment was created
        self.assertIn(experiment_id, self.service.ab_testing.active_experiments)
    
    def test_get_system_health(self):
        """Test system health check"""
        # Create a production model
        model_id = self.service.create_model_version(
            name="health-test", version="1.0.0", description="Health test",
            model_type="transcription", framework="openai", created_by="test_user",
            parameters={}
        )
        self.service.deploy_model(model_id, "production")
        
        # Get system health
        health = self.service.get_system_health()
        
        self.assertIn('overall_status', health)
        self.assertIn('production_models', health)
        self.assertIn('model_health', health)
        self.assertIn('active_experiments', health)
        self.assertIn('alerts', health)
        
        self.assertGreaterEqual(health['production_models'], 1)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.service = ModelManagementService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_db.name)
        experiments_db = self.temp_db.name.replace('.db', '_experiments.db')
        if os.path.exists(experiments_db):
            os.unlink(experiments_db)
    
    def test_complete_model_lifecycle(self):
        """Test complete model lifecycle from creation to retirement"""
        # 1. Create model
        model_id = self.service.create_model_version(
            name="lifecycle-test",
            version="1.0.0",
            description="Complete lifecycle test",
            model_type="transcription",
            framework="openai",
            created_by="test_user",
            parameters={"temperature": 0.1}
        )
        
        # 2. Deploy to staging
        self.service.deploy_model(model_id, "staging")
        model = self.service.registry.get_model(model_id)
        self.assertEqual(model.status, ModelStatus.STAGING)
        
        # 3. Add performance metrics
        for i in range(10):
            metrics = ModelPerformanceMetrics(
                model_id=model_id,
                timestamp=datetime.now() - timedelta(hours=i),
                accuracy=0.85 + (i * 0.001),
                latency_ms=100 + (i * 2),
                cost_per_request=0.001
            )
            self.service.registry.record_metrics(metrics)
        
        # 4. Deploy to production
        self.service.deploy_model(model_id, "production")
        model = self.service.registry.get_model(model_id)
        self.assertEqual(model.status, ModelStatus.PRODUCTION)
        
        # 5. Check health
        health = self.service.monitor.check_model_health(model_id)
        self.assertIn(health['status'], ['healthy', 'degraded', 'unhealthy', 'insufficient_data'])
        
        # 6. Create new version
        new_model_id = self.service.create_model_version(
            name="lifecycle-test",
            version="2.0.0",
            description="New version",
            model_type="transcription",
            framework="openai",
            created_by="test_user",
            parameters={"temperature": 0.05},
            parent_model_id=model_id
        )
        
        # 7. Deploy new version
        self.service.deploy_model(new_model_id, "production")
        
        # 8. Rollback if needed
        self.service.rollback_model(new_model_id, model_id)
        
        # Verify final states
        old_model = self.service.registry.get_model(model_id)
        new_model = self.service.registry.get_model(new_model_id)
        
        self.assertEqual(old_model.status, ModelStatus.PRODUCTION)
        self.assertEqual(new_model.status, ModelStatus.DEPRECATED)
    
    def test_ab_test_workflow(self):
        """Test complete A/B testing workflow"""
        # Create two models
        control_id = self.service.create_model_version(
            name="ab-control", version="1.0.0", description="Control model",
            model_type="transcription", framework="openai", created_by="test_user",
            parameters={}
        )
        
        treatment_id = self.service.create_model_version(
            name="ab-treatment", version="1.1.0", description="Treatment model",
            model_type="transcription", framework="openai", created_by="test_user",
            parameters={}
        )
        
        # Deploy both
        self.service.deploy_model(control_id, "production")
        self.service.deploy_model(treatment_id, "production")
        
        # Start experiment
        experiment_id = self.service.start_ab_test(
            name="AB Workflow Test",
            description="Testing complete workflow",
            control_model_id=control_id,
            treatment_model_id=treatment_id,
            traffic_split=0.5,
            success_metrics=["accuracy", "latency_ms"],
            duration_days=1,
            created_by="test_user",
            minimum_sample_size=20
        )
        
        # Simulate user interactions
        import random
        for i in range(50):
            user_id = f"user_{i}"
            variant = self.service.ab_testing.assign_variant(experiment_id, user_id)
            
            # Simulate metrics (treatment performs slightly better)
            base_accuracy = 0.85 if variant == "control" else 0.87
            base_latency = 120 if variant == "control" else 110
            
            metrics = {
                "accuracy": base_accuracy + random.uniform(-0.02, 0.02),
                "latency_ms": base_latency + random.uniform(-10, 10)
            }
            
            self.service.ab_testing.record_experiment_data(
                experiment_id, variant, user_id, metrics
            )
        
        # Analyze results
        results = self.service.ab_testing.analyze_experiment(experiment_id)
        
        self.assertIsInstance(results, ExperimentResult)
        self.assertIn("accuracy", results.control_metrics)
        self.assertIn("accuracy", results.treatment_metrics)
        self.assertIsNotNone(results.recommendation)
        
        # Stop experiment
        self.service.ab_testing.stop_experiment(experiment_id)
        self.assertNotIn(experiment_id, self.service.ab_testing.active_experiments)

def run_performance_tests():
    """Run performance tests"""
    print("\n" + "="*50)
    print("PERFORMANCE TESTS")
    print("="*50)
    
    import time
    
    # Test model registry performance
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        registry = ModelRegistry(temp_db.name)
        
        # Test bulk model registration
        start_time = time.time()
        model_ids = []
        
        for i in range(100):
            metadata = ModelMetadata(
                model_id=str(uuid.uuid4()),
                name=f"perf-test-{i}",
                version="1.0.0",
                description=f"Performance test model {i}",
                model_type="transcription",
                framework="openai",
                created_at=datetime.now(),
                created_by="perf_test",
                status=ModelStatus.DEVELOPMENT,
                tags=["performance", "test"],
                parameters={}
            )
            model_id = registry.register_model(metadata)
            model_ids.append(model_id)
        
        registration_time = time.time() - start_time
        print(f"Registered 100 models in {registration_time:.3f}s")
        print(f"Average time per model: {registration_time/100:.4f}s")
        
        # Test bulk metrics recording
        start_time = time.time()
        
        for model_id in model_ids[:10]:  # Test with first 10 models
            for i in range(50):  # 50 metrics per model
                metrics = ModelPerformanceMetrics(
                    model_id=model_id,
                    timestamp=datetime.now() - timedelta(hours=i),
                    accuracy=0.85 + (i * 0.001),
                    latency_ms=100 + (i * 2),
                    cost_per_request=0.001
                )
                registry.record_metrics(metrics)
        
        metrics_time = time.time() - start_time
        print(f"Recorded 500 metrics in {metrics_time:.3f}s")
        print(f"Average time per metric: {metrics_time/500:.4f}s")
        
        # Test query performance
        start_time = time.time()
        
        for _ in range(100):
            models = registry.list_models(limit=50)
        
        query_time = time.time() - start_time
        print(f"Executed 100 list queries in {query_time:.3f}s")
        print(f"Average time per query: {query_time/100:.4f}s")
        
    finally:
        os.unlink(temp_db.name)

def run_example_scenarios():
    """Run example scenarios"""
    print("\n" + "="*50)
    print("EXAMPLE SCENARIOS")
    print("="*50)
    
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        service = ModelManagementService(temp_db.name)
        
        print("Scenario 1: Model Development Lifecycle")
        print("-" * 40)
        
        # Create initial model
        model_id = service.create_model_version(
            name="whisper-transcription",
            version="1.0.0",
            description="Initial Whisper model for transcription",
            model_type="transcription",
            framework="openai",
            created_by="ml_engineer",
            parameters={"model_size": "base", "language": "en"}
        )
        print(f"✅ Created model: {model_id[:8]}...")
        
        # Deploy to staging
        service.deploy_model(model_id, "staging")
        print("✅ Deployed to staging")
        
        # Add performance metrics
        for i in range(20):
            metrics = ModelPerformanceMetrics(
                model_id=model_id,
                timestamp=datetime.now() - timedelta(hours=i),
                accuracy=0.85 + random.uniform(-0.02, 0.02),
                latency_ms=100 + random.uniform(-10, 10),
                cost_per_request=0.001 + random.uniform(-0.0002, 0.0002)
            )
            service.registry.record_metrics(metrics)
        print("✅ Added performance metrics")
        
        # Check health
        health = service.monitor.check_model_health(model_id)
        print(f"✅ Model health: {health['status']}")
        
        # Deploy to production
        service.deploy_model(model_id, "production")
        print("✅ Deployed to production")
        
        print("\nScenario 2: A/B Testing")
        print("-" * 40)
        
        # Create improved model
        improved_id = service.create_model_version(
            name="whisper-transcription",
            version="1.1.0",
            description="Improved Whisper model",
            model_type="transcription",
            framework="openai",
            created_by="ml_engineer",
            parameters={"model_size": "large", "language": "en"},
            parent_model_id=model_id
        )
        service.deploy_model(improved_id, "production")
        print(f"✅ Created improved model: {improved_id[:8]}...")
        
        # Start A/B test
        experiment_id = service.start_ab_test(
            name="Base vs Large Model Comparison",
            description="Compare base and large Whisper models",
            control_model_id=model_id,
            treatment_model_id=improved_id,
            traffic_split=0.5,
            success_metrics=["accuracy", "latency_ms"],
            duration_days=7,
            created_by="ml_engineer"
        )
        print(f"✅ Started A/B test: {experiment_id[:8]}...")
        
        # Simulate user interactions
        import random
        for i in range(100):
            user_id = f"user_{i}"
            variant = service.ab_testing.assign_variant(experiment_id, user_id)
            
            # Large model performs better but is slower
            if variant == "control":
                accuracy = 0.85 + random.uniform(-0.02, 0.02)
                latency = 100 + random.uniform(-10, 10)
            else:
                accuracy = 0.88 + random.uniform(-0.02, 0.02)  # Better accuracy
                latency = 150 + random.uniform(-15, 15)        # Higher latency
            
            metrics = {"accuracy": accuracy, "latency_ms": latency}
            service.ab_testing.record_experiment_data(experiment_id, variant, user_id, metrics)
        
        print("✅ Simulated 100 user interactions")
        
        # Analyze results
        results = service.ab_testing.analyze_experiment(experiment_id)
        print(f"✅ Analysis complete: {results.recommendation}")
        
        print("\nScenario 3: Cost Optimization")
        print("-" * 40)
        
        # Get model recommendation
        requirements = {
            'min_accuracy': 0.80,
            'max_latency_ms': 200,
            'max_cost_per_request': 0.002
        }
        
        recommendation = service.get_model_recommendation("transcription", requirements)
        if recommendation:
            print(f"✅ Recommended model: {recommendation['model_name']} v{recommendation['model_version']}")
            print(f"   Reason: {recommendation['recommendation_reason']}")
        else:
            print("❌ No model meets the requirements")
        
        print("\nScenario 4: System Health Monitoring")
        print("-" * 40)
        
        health = service.get_system_health()
        print(f"✅ System status: {health['overall_status']}")
        print(f"✅ Production models: {health['production_models']}")
        print(f"✅ Active experiments: {health['active_experiments']}")
        print(f"✅ Active alerts: {len(health['alerts'])}")
        
    finally:
        os.unlink(temp_db.name)
        experiments_db = temp_db.name.replace('.db', '_experiments.db')
        if os.path.exists(experiments_db):
            os.unlink(experiments_db)

if __name__ == '__main__':
    # Run unit tests
    print("Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance tests
    run_performance_tests()
    
    # Run example scenarios
    run_example_scenarios()
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED")
    print("="*50)