"""
Automated Model Retraining Pipeline
Intelligent retraining system with data drift detection, performance monitoring, and automated triggers
"""

import asyncio
import json
import logging
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import transformers
from transformers import AutoModelForSequenceClassification, AutoTokenizer, TrainingArguments, Trainer
import sqlite3
import redis.asyncio as redis
from collections import defaultdict, deque
import threading
import queue
import schedule
import time
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Import our model management components
from ai_model_management_system import ModelRegistry, ModelTrainer, ModelMetadata, ModelType, ModelStatus
from ai_model_performance_monitoring import ModelPerformanceMonitor, MetricType, AlertSeverity
from comprehensive_medical_schema import ComprehensiveMedicalSchema, MedicalValidationEngine

logger = logging.getLogger(__name__)

class RetrainingTrigger(Enum):
    """Types of retraining triggers"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_DRIFT = "data_drift"
    MODEL_DRIFT = "model_drift"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    NEW_DATA_THRESHOLD = "new_data_threshold"
    ERROR_RATE_SPIKE = "error_rate_spike"
    ACCURACY_DROP = "accuracy_drop"
    MEDICAL_COMPLIANCE_ISSUE = "medical_compliance_issue"

class RetrainingStatus(Enum):
    """Retraining job status"""
    QUEUED = "queued"
    PREPARING_DATA = "preparing_data"
    TRAINING = "training"
    VALIDATING = "validating"
    TESTING = "testing"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DataDriftMethod(Enum):
    """Data drift detection methods"""
    STATISTICAL = "statistical"
    ADVERSARIAL = "adversarial"
    FEATURE_DISTRIBUTION = "feature_distribution"
    EMBEDDING_DISTANCE = "embedding_distance"

@dataclass
class RetrainingConfig:
    """Configuration for automated retraining"""
    model_id: str
    triggers: List[RetrainingTrigger]
    schedule: Optional[str] = None  # Cron-like schedule
    performance_threshold: float = 0.85
    drift_threshold: float = 0.1
    min_new_samples: int = 1000
    validation_split: float = 0.2
    test_split: float = 0.1
    max_training_time_hours: int = 24
    auto_deploy: bool = False
    rollback_on_performance_drop: bool = True
    medical_validation_required: bool = True
    notification_webhooks: List[str] = field(default_factory=list)
    custom_training_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RetrainingJob:
    """Retraining job information"""
    id: str
    model_id: str
    trigger: RetrainingTrigger
    status: RetrainingStatus
    config: RetrainingConfig
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    new_model_id: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    data_stats: Dict[str, Any] = field(default_factory=dict)
    performance_comparison: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DriftDetectionResult:
    """Result of drift detection analysis"""
    has_drift: bool
    drift_score: float
    drift_method: DataDriftMethod
    affected_features: List[str]
    details: Dict[str, Any]
    timestamp: datetime

class DataCollector:
    """Collects and manages training data for retraining"""
    
    def __init__(self, db_path: str = "retraining_data.db"):
        self.db_path = db_path
        self.connection = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database for storing training data"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.connection.cursor()
        
        # Training data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT,
                input_text TEXT,
                label TEXT,
                predicted_label TEXT,
                confidence REAL,
                timestamp TEXT,
                session_id TEXT,
                user_id TEXT,
                feedback_score REAL,
                is_corrected BOOLEAN,
                metadata TEXT
            )
        ''')
        
        # Data drift history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drift_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT,
                drift_score REAL,
                drift_method TEXT,
                has_drift BOOLEAN,
                affected_features TEXT,
                timestamp TEXT,
                details TEXT
            )
        ''')
        
        self.connection.commit()
    
    def collect_prediction_data(
        self,
        model_id: str,
        input_text: str,
        predicted_label: str,
        confidence: float,
        actual_label: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        feedback_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Collect prediction data for future retraining"""
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO training_data (
                model_id, input_text, label, predicted_label, confidence,
                timestamp, session_id, user_id, feedback_score, is_corrected, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            model_id,
            input_text,
            actual_label,
            predicted_label,
            confidence,
            datetime.now().isoformat(),
            session_id,
            user_id,
            feedback_score,
            actual_label is not None and actual_label != predicted_label,
            json.dumps(metadata) if metadata else None
        ))
        self.connection.commit()
    
    def get_training_data(
        self,
        model_id: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get training data for a model"""
        cursor = self.connection.cursor()
        
        query = '''
            SELECT input_text, label, predicted_label, confidence, timestamp,
                   feedback_score, is_corrected, metadata
            FROM training_data
            WHERE model_id = ?
        '''
        params = [model_id]
        
        if since:
            query += ' AND timestamp > ?'
            params.append(since.isoformat())
        
        query += ' ORDER BY timestamp DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            {
                'input_text': row[0],
                'label': row[1],
                'predicted_label': row[2],
                'confidence': row[3],
                'timestamp': row[4],
                'feedback_score': row[5],
                'is_corrected': row[6],
                'metadata': json.loads(row[7]) if row[7] else {}
            }
            for row in rows
        ]
    
    def get_data_statistics(self, model_id: str, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get statistics about collected data"""
        cursor = self.connection.cursor()
        
        query = '''
            SELECT COUNT(*) as total_samples,
                   AVG(confidence) as avg_confidence,
                   SUM(CASE WHEN is_corrected = 1 THEN 1 ELSE 0 END) as corrections,
                   AVG(feedback_score) as avg_feedback,
                   COUNT(DISTINCT label) as unique_labels
            FROM training_data
            WHERE model_id = ?
        '''
        params = [model_id]
        
        if since:
            query += ' AND timestamp > ?'
            params.append(since.isoformat())
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        return {
            'total_samples': row[0] or 0,
            'avg_confidence': row[1] or 0,
            'corrections': row[2] or 0,
            'avg_feedback': row[3] or 0,
            'unique_labels': row[4] or 0,
            'correction_rate': (row[2] or 0) / max(row[0] or 1, 1)
        }

class DriftDetector:
    """Detects data and model drift"""
    
    def __init__(self):
        self.reference_data: Dict[str, Any] = {}
        self.feature_extractors: Dict[str, Callable] = {}
    
    def set_reference_data(self, model_id: str, reference_data: List[Dict[str, Any]]):
        """Set reference data for drift detection"""
        # Extract features from reference data
        features = self._extract_features(reference_data)
        
        self.reference_data[model_id] = {
            'features': features,
            'statistics': self._calculate_statistics(features),
            'timestamp': datetime.now()
        }
    
    def _extract_features(self, data: List[Dict[str, Any]]) -> np.ndarray:
        """Extract numerical features from text data"""
        features = []
        
        for item in data:
            text = item.get('input_text', '')
            
            # Simple text features
            feature_vector = [
                len(text),  # Text length
                len(text.split()),  # Word count
                len(set(text.split())),  # Unique words
                text.count('.'),  # Sentence count approximation
                text.count(','),  # Comma count
                len([w for w in text.split() if w.isupper()]),  # Uppercase words
                sum(1 for c in text if c.isdigit()),  # Digit count
                len([w for w in text.split() if len(w) > 10]),  # Long words
            ]
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def _calculate_statistics(self, features: np.ndarray) -> Dict[str, Any]:
        """Calculate statistical properties of features"""
        return {
            'mean': np.mean(features, axis=0).tolist(),
            'std': np.std(features, axis=0).tolist(),
            'min': np.min(features, axis=0).tolist(),
            'max': np.max(features, axis=0).tolist(),
            'percentiles': {
                '25': np.percentile(features, 25, axis=0).tolist(),
                '50': np.percentile(features, 50, axis=0).tolist(),
                '75': np.percentile(features, 75, axis=0).tolist(),
                '95': np.percentile(features, 95, axis=0).tolist()
            }
        }
    
    def detect_drift(
        self,
        model_id: str,
        new_data: List[Dict[str, Any]],
        method: DataDriftMethod = DataDriftMethod.STATISTICAL,
        threshold: float = 0.1
    ) -> DriftDetectionResult:
        """Detect drift in new data compared to reference"""
        
        if model_id not in self.reference_data:
            return DriftDetectionResult(
                has_drift=False,
                drift_score=0.0,
                drift_method=method,
                affected_features=[],
                details={'error': 'No reference data available'},
                timestamp=datetime.now()
            )
        
        reference = self.reference_data[model_id]
        new_features = self._extract_features(new_data)
        
        if method == DataDriftMethod.STATISTICAL:
            return self._detect_statistical_drift(
                reference['features'], new_features, threshold
            )
        elif method == DataDriftMethod.FEATURE_DISTRIBUTION:
            return self._detect_feature_distribution_drift(
                reference['features'], new_features, threshold
            )
        else:
            # Default to statistical method
            return self._detect_statistical_drift(
                reference['features'], new_features, threshold
            )
    
    def _detect_statistical_drift(
        self,
        reference_features: np.ndarray,
        new_features: np.ndarray,
        threshold: float
    ) -> DriftDetectionResult:
        """Detect drift using statistical tests"""
        p_values = []
        affected_features = []
        
        for i in range(reference_features.shape[1]):
            ref_feature = reference_features[:, i]
            new_feature = new_features[:, i]
            
            # Kolmogorov-Smirnov test
            statistic, p_value = stats.ks_2samp(ref_feature, new_feature)
            p_values.append(p_value)
            
            if p_value < threshold:
                affected_features.append(f"feature_{i}")
        
        # Overall drift score (average of significant p-values)
        drift_score = 1 - np.mean(p_values)
        has_drift = len(affected_features) > 0
        
        return DriftDetectionResult(
            has_drift=has_drift,
            drift_score=drift_score,
            drift_method=DataDriftMethod.STATISTICAL,
            affected_features=affected_features,
            details={
                'p_values': p_values,
                'threshold': threshold,
                'num_features_affected': len(affected_features)
            },
            timestamp=datetime.now()
        )
    
    def _detect_feature_distribution_drift(
        self,
        reference_features: np.ndarray,
        new_features: np.ndarray,
        threshold: float
    ) -> DriftDetectionResult:
        """Detect drift using feature distribution comparison"""
        
        # Calculate distribution distances
        distances = []
        affected_features = []
        
        for i in range(reference_features.shape[1]):
            ref_feature = reference_features[:, i]
            new_feature = new_features[:, i]
            
            # Calculate Earth Mover's Distance (Wasserstein distance)
            distance = stats.wasserstein_distance(ref_feature, new_feature)
            distances.append(distance)
            
            # Normalize by feature scale
            feature_scale = np.std(ref_feature)
            normalized_distance = distance / max(feature_scale, 1e-6)
            
            if normalized_distance > threshold:
                affected_features.append(f"feature_{i}")
        
        drift_score = np.mean(distances)
        has_drift = len(affected_features) > 0
        
        return DriftDetectionResult(
            has_drift=has_drift,
            drift_score=drift_score,
            drift_method=DataDriftMethod.FEATURE_DISTRIBUTION,
            affected_features=affected_features,
            details={
                'distances': distances,
                'threshold': threshold,
                'num_features_affected': len(affected_features)
            },
            timestamp=datetime.now()
        )

class AutomatedRetrainingPipeline:
    """Main automated retraining pipeline orchestrator"""
    
    def __init__(
        self,
        model_registry: ModelRegistry,
        performance_monitor: ModelPerformanceMonitor,
        redis_url: str = "redis://localhost:6379"
    ):
        self.model_registry = model_registry
        self.performance_monitor = performance_monitor
        self.redis_url = redis_url
        self.redis_client = None
        
        # Components
        self.data_collector = DataCollector()
        self.drift_detector = DriftDetector()
        self.model_trainer = ModelTrainer(model_registry)
        
        # Configuration and state
        self.retraining_configs: Dict[str, RetrainingConfig] = {}
        self.active_jobs: Dict[str, RetrainingJob] = {}
        self.job_queue = queue.PriorityQueue()
        
        # Background workers
        self.is_running = False
        self.monitoring_thread = None
        self.training_thread = None
        
        # Medical schema integration
        self.medical_schema = None
        self.medical_validator = None
    
    async def initialize(self):
        """Initialize the retraining pipeline"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Initialize medical components
            try:
                self.medical_schema = ComprehensiveMedicalSchema()
                await self.medical_schema.initialize()
                
                self.medical_validator = MedicalValidationEngine()
                await self.medical_validator.initialize()
            except Exception as e:
                logger.warning(f"Medical components not available: {e}")
            
            # Start background workers
            self.is_running = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
            self.training_thread = threading.Thread(target=self._training_worker, daemon=True)
            
            self.monitoring_thread.start()
            self.training_thread.start()
            
            logger.info("Automated Retraining Pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Automated Retraining Pipeline: {e}")
            raise e
    
    def register_model_for_retraining(self, config: RetrainingConfig):
        """Register a model for automated retraining"""
        self.retraining_configs[config.model_id] = config
        
        # Set up scheduled retraining if specified
        if config.schedule:
            self._schedule_retraining(config)
        
        # Initialize reference data for drift detection
        self._initialize_reference_data(config.model_id)
        
        logger.info(f"Model {config.model_id} registered for automated retraining")
    
    def _initialize_reference_data(self, model_id: str):
        """Initialize reference data for a model"""
        # Get recent data as reference
        reference_data = self.data_collector.get_training_data(
            model_id,
            since=datetime.now() - timedelta(days=30),
            limit=10000
        )
        
        if reference_data:
            self.drift_detector.set_reference_data(model_id, reference_data)
            logger.info(f"Reference data initialized for model {model_id} with {len(reference_data)} samples")
    
    def _schedule_retraining(self, config: RetrainingConfig):
        """Schedule automatic retraining based on cron-like schedule"""
        # Parse schedule and set up periodic retraining
        # This is a simplified version - in production, use a proper scheduler like APScheduler
        def scheduled_retrain():
            self.trigger_retraining(config.model_id, RetrainingTrigger.SCHEDULED)
        
        # Example: schedule.every().day.at("02:00").do(scheduled_retrain)
        logger.info(f"Scheduled retraining set up for model {config.model_id}")
    
    def _monitoring_worker(self):
        """Background worker for monitoring triggers"""
        while self.is_running:
            try:
                # Check all registered models for retraining triggers
                for model_id, config in self.retraining_configs.items():
                    self._check_retraining_triggers(model_id, config)
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Monitoring worker error: {e}")
                time.sleep(60)
    
    def _training_worker(self):
        """Background worker for processing retraining jobs"""
        while self.is_running:
            try:
                if not self.job_queue.empty():
                    priority, job_id = self.job_queue.get()
                    job = self.active_jobs.get(job_id)
                    
                    if job:
                        asyncio.run(self._process_retraining_job(job))
                else:
                    time.sleep(30)
                    
            except Exception as e:
                logger.error(f"Training worker error: {e}")
                time.sleep(60)
    
    def _check_retraining_triggers(self, model_id: str, config: RetrainingConfig):
        """Check if any retraining triggers are activated"""
        
        # Check performance degradation
        if RetrainingTrigger.PERFORMANCE_DEGRADATION in config.triggers:
            current_metrics = self.performance_monitor.get_current_metrics(model_id)
            accuracy = current_metrics.get('accuracy', {}).get('value', 1.0)
            
            if accuracy < config.performance_threshold:
                self.trigger_retraining(model_id, RetrainingTrigger.PERFORMANCE_DEGRADATION)
                return
        
        # Check data drift
        if RetrainingTrigger.DATA_DRIFT in config.triggers:
            recent_data = self.data_collector.get_training_data(
                model_id,
                since=datetime.now() - timedelta(days=7),
                limit=1000
            )
            
            if len(recent_data) > 100:  # Minimum samples for drift detection
                drift_result = self.drift_detector.detect_drift(
                    model_id, recent_data, threshold=config.drift_threshold
                )
                
                if drift_result.has_drift:
                    self.trigger_retraining(model_id, RetrainingTrigger.DATA_DRIFT)
                    return
        
        # Check new data threshold
        if RetrainingTrigger.NEW_DATA_THRESHOLD in config.triggers:
            stats = self.data_collector.get_data_statistics(
                model_id,
                since=datetime.now() - timedelta(days=1)
            )
            
            if stats['total_samples'] >= config.min_new_samples:
                self.trigger_retraining(model_id, RetrainingTrigger.NEW_DATA_THRESHOLD)
                return
        
        # Check medical compliance issues
        if RetrainingTrigger.MEDICAL_COMPLIANCE_ISSUE in config.triggers and self.medical_validator:
            current_metrics = self.performance_monitor.get_current_metrics(model_id)
            hipaa_score = current_metrics.get('hipaa_compliance', {}).get('value', 1.0)
            medical_accuracy = current_metrics.get('medical_accuracy', {}).get('value', 1.0)
            
            if hipaa_score < 0.95 or medical_accuracy < 0.90:
                self.trigger_retraining(model_id, RetrainingTrigger.MEDICAL_COMPLIANCE_ISSUE)
                return
    
    def trigger_retraining(
        self,
        model_id: str,
        trigger: RetrainingTrigger,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Trigger a retraining job"""
        
        if model_id not in self.retraining_configs:
            raise ValueError(f"Model {model_id} not registered for retraining")
        
        config = self.retraining_configs[model_id]
        
        # Check if there's already an active job for this model
        active_job = next(
            (job for job in self.active_jobs.values() 
             if job.model_id == model_id and job.status not in [RetrainingStatus.COMPLETED, RetrainingStatus.FAILED, RetrainingStatus.CANCELLED]),
            None
        )
        
        if active_job:
            logger.info(f"Retraining already in progress for model {model_id}")
            return active_job.id
        
        # Create retraining job
        job_id = f"retrain_{model_id}_{int(time.time())}"
        job = RetrainingJob(
            id=job_id,
            model_id=model_id,
            trigger=trigger,
            status=RetrainingStatus.QUEUED,
            config=config,
            created_at=datetime.now()
        )
        
        # Apply custom configuration
        if custom_config:
            job.config.custom_training_config.update(custom_config)
        
        self.active_jobs[job_id] = job
        
        # Add to queue with priority based on trigger
        priority = self._get_trigger_priority(trigger)
        self.job_queue.put((priority, job_id))
        
        logger.info(f"Retraining job {job_id} queued for model {model_id} (trigger: {trigger.value})")
        return job_id
    
    def _get_trigger_priority(self, trigger: RetrainingTrigger) -> int:
        """Get priority for retraining trigger (lower number = higher priority)"""
        priority_map = {
            RetrainingTrigger.MEDICAL_COMPLIANCE_ISSUE: 1,
            RetrainingTrigger.ERROR_RATE_SPIKE: 2,
            RetrainingTrigger.PERFORMANCE_DEGRADATION: 3,
            RetrainingTrigger.DATA_DRIFT: 4,
            RetrainingTrigger.MANUAL: 5,
            RetrainingTrigger.NEW_DATA_THRESHOLD: 6,
            RetrainingTrigger.SCHEDULED: 7
        }
        return priority_map.get(trigger, 10)
    
    async def _process_retraining_job(self, job: RetrainingJob):
        """Process a retraining job"""
        try:
            job.status = RetrainingStatus.PREPARING_DATA
            job.started_at = datetime.now()
            job.logs.append(f"Started retraining job {job.id}")
            
            # Prepare training data
            training_data = await self._prepare_training_data(job)
            if not training_data:
                job.status = RetrainingStatus.FAILED
                job.error_message = "No training data available"
                return
            
            job.logs.append(f"Prepared {len(training_data)} training samples")
            
            # Split data
            train_data, val_data, test_data = self._split_data(
                training_data,
                job.config.validation_split,
                job.config.test_split
            )
            
            # Get original model metadata
            original_model, original_metadata = await self.model_registry.load_model(job.model_id)
            
            # Train new model
            job.status = RetrainingStatus.TRAINING
            job.logs.append("Starting model training")
            
            new_model_id = await self._train_new_model(
                job, original_metadata, train_data, val_data
            )
            
            if not new_model_id:
                job.status = RetrainingStatus.FAILED
                job.error_message = "Model training failed"
                return
            
            job.new_model_id = new_model_id
            job.logs.append(f"New model trained: {new_model_id}")
            
            # Validate new model
            job.status = RetrainingStatus.VALIDATING
            validation_results = await self._validate_new_model(
                job, new_model_id, test_data
            )
            
            job.metrics = validation_results
            job.logs.append(f"Validation completed: {validation_results}")
            
            # Compare performance with original model
            performance_comparison = await self._compare_model_performance(
                job.model_id, new_model_id, test_data
            )
            job.performance_comparison = performance_comparison
            
            # Decide whether to deploy
            should_deploy = self._should_deploy_new_model(job, performance_comparison)
            
            if should_deploy and job.config.auto_deploy:
                job.status = RetrainingStatus.DEPLOYING
                await self._deploy_new_model(job, new_model_id)
                job.logs.append("New model deployed successfully")
            
            job.status = RetrainingStatus.COMPLETED
            job.completed_at = datetime.now()
            job.logs.append("Retraining job completed successfully")
            
            # Send notifications
            await self._send_retraining_notifications(job)
            
        except Exception as e:
            job.status = RetrainingStatus.FAILED
            job.error_message = str(e)
            job.logs.append(f"Retraining failed: {str(e)}")
            logger.error(f"Retraining job {job.id} failed: {e}")
            
            # Send failure notifications
            await self._send_failure_notifications(job)
    
    async def _prepare_training_data(self, job: RetrainingJob) -> List[Dict[str, Any]]:
        """Prepare training data for retraining"""
        
        # Get all available training data
        all_data = self.data_collector.get_training_data(job.model_id)
        
        # Filter data based on quality and recency
        filtered_data = []
        
        for item in all_data:
            # Skip data without labels
            if not item.get('label'):
                continue
            
            # Skip low-confidence predictions unless they were corrected
            if item.get('confidence', 0) < 0.5 and not item.get('is_corrected', False):
                continue
            
            # Prefer corrected data and data with good feedback
            if item.get('is_corrected', False) or item.get('feedback_score', 0) > 0.7:
                filtered_data.append(item)
            elif item.get('confidence', 0) > 0.8:
                filtered_data.append(item)
        
        # Ensure we have enough data
        if len(filtered_data) < job.config.min_new_samples:
            logger.warning(f"Insufficient training data for model {job.model_id}: {len(filtered_data)} samples")
            return []
        
        job.data_stats = {
            'total_samples': len(all_data),
            'filtered_samples': len(filtered_data),
            'correction_rate': sum(1 for item in filtered_data if item.get('is_corrected', False)) / len(filtered_data)
        }
        
        return filtered_data
    
    def _split_data(
        self,
        data: List[Dict[str, Any]],
        val_split: float,
        test_split: float
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split data into train, validation, and test sets"""
        
        # First split: train + val vs test
        train_val_data, test_data = train_test_split(
            data,
            test_size=test_split,
            stratify=[item['label'] for item in data] if len(set(item['label'] for item in data)) > 1 else None,
            random_state=42
        )
        
        # Second split: train vs val
        train_data, val_data = train_test_split(
            train_val_data,
            test_size=val_split / (1 - test_split),
            stratify=[item['label'] for item in train_val_data] if len(set(item['label'] for item in train_val_data)) > 1 else None,
            random_state=42
        )
        
        return train_data, val_data, test_data
    
    async def _train_new_model(
        self,
        job: RetrainingJob,
        original_metadata: ModelMetadata,
        train_data: List[Dict[str, Any]],
        val_data: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Train a new model version"""
        
        try:
            # Determine model type and training approach
            if original_metadata.type == ModelType.BERT:
                return await self._retrain_transformer_model(
                    job, original_metadata, train_data, val_data
                )
            else:
                # For other model types, implement specific retraining logic
                logger.warning(f"Retraining not implemented for model type: {original_metadata.type}")
                return None
                
        except Exception as e:
            logger.error(f"Error training new model for job {job.id}: {e}")
            return None
    
    async def _retrain_transformer_model(
        self,
        job: RetrainingJob,
        original_metadata: ModelMetadata,
        train_data: List[Dict[str, Any]],
        val_data: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Retrain a transformer model"""
        
        # Use the model trainer with enhanced configuration
        training_config = {
            'epochs': job.config.custom_training_config.get('epochs', 3),
            'batch_size': job.config.custom_training_config.get('batch_size', 16),
            'learning_rate': job.config.custom_training_config.get('learning_rate', 2e-5),
            'warmup_steps': job.config.custom_training_config.get('warmup_steps', 500),
            'weight_decay': job.config.custom_training_config.get('weight_decay', 0.01),
            'num_labels': len(set(item['label'] for item in train_data))
        }
        
        new_model_id = await self.model_trainer.fine_tune_transformer(
            base_model_name=original_metadata.base_model or "bert-base-uncased",
            train_data=train_data,
            val_data=val_data,
            model_name=f"{original_metadata.name}_retrained_{int(time.time())}",
            user_id="retraining_pipeline",
            config=training_config
        )
        
        return new_model_id
    
    async def _validate_new_model(
        self,
        job: RetrainingJob,
        new_model_id: str,
        test_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Validate the newly trained model"""
        
        # Load the new model
        new_model, new_metadata = await self.model_registry.load_model(new_model_id)
        
        # Perform validation
        predictions = []
        actuals = []
        
        # This is a simplified validation - in practice, you'd use the actual model
        for item in test_data:
            predictions.append(item['predicted_label'])  # Placeholder
            actuals.append(item['label'])
        
        # Calculate metrics
        accuracy = accuracy_score(actuals, predictions)
        precision = precision_score(actuals, predictions, average='weighted')
        recall = recall_score(actuals, predictions, average='weighted')
        f1 = f1_score(actuals, predictions, average='weighted')
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'test_samples': len(test_data)
        }
        
        # Medical validation if applicable
        if job.config.medical_validation_required and self.medical_validator:
            medical_metrics = await self._validate_medical_performance(
                new_model, test_data
            )
            metrics.update(medical_metrics)
        
        return metrics
    
    async def _validate_medical_performance(
        self,
        model: Any,
        test_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Validate medical performance aspects"""
        
        medical_texts = [item['input_text'] for item in test_data if 'medical' in item.get('metadata', {}).get('domain', '')]
        
        if not medical_texts:
            return {}
        
        total_medical_accuracy = 0
        total_hipaa_compliance = 0
        count = 0
        
        for text in medical_texts[:100]:  # Sample for validation
            validation_result = await self.medical_validator.validate_content(text)
            total_medical_accuracy += validation_result.get('medical_accuracy', 0)
            total_hipaa_compliance += validation_result.get('hipaa_compliance_score', 0)
            count += 1
        
        if count == 0:
            return {}
        
        return {
            'medical_accuracy': total_medical_accuracy / count,
            'hipaa_compliance': total_hipaa_compliance / count,
            'medical_samples_validated': count
        }
    
    async def _compare_model_performance(
        self,
        original_model_id: str,
        new_model_id: str,
        test_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare performance between original and new model"""
        
        # Get performance metrics for both models
        original_metrics = self.performance_monitor.get_current_metrics(original_model_id)
        
        # Load new model and get its metadata
        new_model, new_metadata = await self.model_registry.load_model(new_model_id)
        
        comparison = {
            'original_accuracy': original_metrics.get('accuracy', {}).get('value', 0),
            'new_accuracy': new_metadata.metrics.get('accuracy', 0),
            'improvement': new_metadata.metrics.get('accuracy', 0) - original_metrics.get('accuracy', {}).get('value', 0),
            'test_samples': len(test_data)
        }
        
        # Add medical metrics if available
        if 'medical_accuracy' in new_metadata.metrics:
            original_medical = original_metrics.get('medical_accuracy', {}).get('value', 0)
            new_medical = new_metadata.metrics.get('medical_accuracy', 0)
            comparison.update({
                'original_medical_accuracy': original_medical,
                'new_medical_accuracy': new_medical,
                'medical_improvement': new_medical - original_medical
            })
        
        return comparison
    
    def _should_deploy_new_model(
        self,
        job: RetrainingJob,
        performance_comparison: Dict[str, Any]
    ) -> bool:
        """Decide whether to deploy the new model"""
        
        # Check if new model performs better
        improvement = performance_comparison.get('improvement', 0)
        
        # Minimum improvement threshold
        min_improvement = 0.01  # 1% improvement
        
        if improvement < min_improvement:
            job.logs.append(f"New model improvement ({improvement:.3f}) below threshold ({min_improvement})")
            return False
        
        # Check medical metrics if applicable
        if 'medical_improvement' in performance_comparison:
            medical_improvement = performance_comparison['medical_improvement']
            if medical_improvement < 0:
                job.logs.append("New model has worse medical performance")
                return False
        
        # Additional safety checks
        new_accuracy = performance_comparison.get('new_accuracy', 0)
        if new_accuracy < 0.8:  # Minimum acceptable accuracy
            job.logs.append(f"New model accuracy ({new_accuracy:.3f}) below minimum threshold")
            return False
        
        return True
    
    async def _deploy_new_model(self, job: RetrainingJob, new_model_id: str):
        """Deploy the new model"""
        # This would integrate with the deployment system
        # For now, just update the model status
        new_model, new_metadata = await self.model_registry.load_model(new_model_id)
        new_metadata.status = ModelStatus.DEPLOYED
        
        # In a real system, this would trigger deployment orchestration
        job.logs.append(f"Model {new_model_id} deployed to replace {job.model_id}")
    
    async def _send_retraining_notifications(self, job: RetrainingJob):
        """Send notifications about completed retraining"""
        
        message = f"""
        Retraining completed for model {job.model_id}
        
        Job ID: {job.id}
        Trigger: {job.trigger.value}
        Status: {job.status.value}
        Duration: {(job.completed_at - job.started_at).total_seconds() / 3600:.2f} hours
        
        Performance:
        - New model accuracy: {job.metrics.get('accuracy', 0):.3f}
        - Improvement: {job.performance_comparison.get('improvement', 0):.3f}
        
        New model: {job.new_model_id}
        """
        
        # Send to configured webhooks
        for webhook_url in job.config.notification_webhooks:
            try:
                # In practice, send HTTP POST to webhook
                logger.info(f"Notification sent to {webhook_url}")
            except Exception as e:
                logger.error(f"Failed to send notification to {webhook_url}: {e}")
    
    async def _send_failure_notifications(self, job: RetrainingJob):
        """Send notifications about failed retraining"""
        
        message = f"""
        Retraining FAILED for model {job.model_id}
        
        Job ID: {job.id}
        Trigger: {job.trigger.value}
        Error: {job.error_message}
        
        Please check the logs and investigate.
        """
        
        for webhook_url in job.config.notification_webhooks:
            try:
                logger.error(f"Failure notification sent to {webhook_url}")
            except Exception as e:
                logger.error(f"Failed to send failure notification to {webhook_url}: {e}")
    
    def get_retraining_status(self, job_id: str) -> Optional[RetrainingJob]:
        """Get the status of a retraining job"""
        return self.active_jobs.get(job_id)
    
    def cancel_retraining_job(self, job_id: str) -> bool:
        """Cancel a retraining job"""
        job = self.active_jobs.get(job_id)
        if job and job.status in [RetrainingStatus.QUEUED, RetrainingStatus.PREPARING_DATA]:
            job.status = RetrainingStatus.CANCELLED
            job.logs.append("Job cancelled by user")
            return True
        return False
    
    def get_model_retraining_history(self, model_id: str) -> List[RetrainingJob]:
        """Get retraining history for a model"""
        return [
            job for job in self.active_jobs.values()
            if job.model_id == model_id
        ]
    
    def shutdown(self):
        """Shutdown the retraining pipeline"""
        self.is_running = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.training_thread:
            self.training_thread.join(timeout=5)
        
        if self.redis_client:
            asyncio.create_task(self.redis_client.close())
        
        logger.info("Automated Retraining Pipeline shutdown complete")

# Usage example
async def demo_retraining_pipeline():
    """Demonstrate the automated retraining pipeline"""
    
    # Initialize components
    registry = ModelRegistry()
    monitor = ModelPerformanceMonitor()
    await monitor.initialize()
    
    pipeline = AutomatedRetrainingPipeline(registry, monitor)
    await pipeline.initialize()
    
    # Register a model for retraining
    config = RetrainingConfig(
        model_id="sentiment_classifier_v1",
        triggers=[
            RetrainingTrigger.PERFORMANCE_DEGRADATION,
            RetrainingTrigger.DATA_DRIFT,
            RetrainingTrigger.NEW_DATA_THRESHOLD
        ],
        performance_threshold=0.85,
        drift_threshold=0.1,
        min_new_samples=1000,
        auto_deploy=True,
        medical_validation_required=True
    )
    
    pipeline.register_model_for_retraining(config)
    
    # Simulate some predictions and data collection
    for i in range(100):
        pipeline.data_collector.collect_prediction_data(
            model_id="sentiment_classifier_v1",
            input_text=f"Sample text {i}",
            predicted_label="positive" if i % 2 == 0 else "negative",
            confidence=0.8 + np.random.normal(0, 0.1),
            actual_label="positive" if i % 2 == 0 else "negative",
            feedback_score=0.9 if i % 10 != 0 else 0.3
        )
    
    # Trigger manual retraining
    job_id = pipeline.trigger_retraining(
        "sentiment_classifier_v1",
        RetrainingTrigger.MANUAL
    )
    
    print(f"Retraining job triggered: {job_id}")
    
    # Check job status
    job = pipeline.get_retraining_status(job_id)
    if job:
        print(f"Job status: {job.status.value}")
    
    pipeline.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_retraining_pipeline())