#!/usr/bin/env python3
"""
AI Model Management System
Implements Task 65: AI model versioning and A/B testing

This module provides comprehensive model lifecycle management including:
- Model version control and registry
- A/B testing framework for model comparison
- Performance monitoring and drift detection
- Automated rollback capabilities
- Cost optimization through intelligent model selection
"""

import os
import json
import uuid
import hashlib
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import numpy as np
from pathlib import Path
import time
import statistics
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    """Model deployment status"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class ExperimentStatus(Enum):
    """A/B test experiment status"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ModelMetadata:
    """Model metadata and configuration"""
    model_id: str
    name: str
    version: str
    description: str
    model_type: str  # whisper, gpt, custom, etc.
    framework: str   # openai, huggingface, custom
    created_at: datetime
    created_by: str
    status: ModelStatus
    tags: List[str]
    parameters: Dict[str, Any]
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    parent_model_id: Optional[str] = None
    training_data_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelMetadata':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['status'] = ModelStatus(data['status'])
        return cls(**data)

@dataclass
class ModelPerformanceMetrics:
    """Model performance tracking"""
    model_id: str
    timestamp: datetime
    accuracy: Optional[float] = None
    latency_ms: Optional[float] = None
    throughput_rps: Optional[float] = None
    error_rate: Optional[float] = None
    cost_per_request: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    user_satisfaction: Optional[float] = None
    custom_metrics: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelPerformanceMetrics':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class ABTestExperiment:
    """A/B testing experiment configuration"""
    experiment_id: str
    name: str
    description: str
    control_model_id: str
    treatment_model_id: str
    traffic_split: float  # 0.0 to 1.0, percentage for treatment
    start_date: datetime
    end_date: Optional[datetime]
    status: ExperimentStatus
    success_metrics: List[str]
    minimum_sample_size: int
    confidence_level: float
    created_by: str
    tags: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['start_date'] = self.start_date.isoformat()
        data['end_date'] = self.end_date.isoformat() if self.end_date else None
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ABTestExperiment':
        """Create from dictionary"""
        data['start_date'] = datetime.fromisoformat(data['start_date'])
        data['end_date'] = datetime.fromisoformat(data['end_date']) if data['end_date'] else None
        data['status'] = ExperimentStatus(data['status'])
        return cls(**data)

@dataclass
class ExperimentResult:
    """A/B test experiment results"""
    experiment_id: str
    control_metrics: Dict[str, float]
    treatment_metrics: Dict[str, float]
    statistical_significance: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    sample_sizes: Dict[str, int]
    recommendation: str
    p_values: Dict[str, float]
    effect_sizes: Dict[str, float]
    generated_at: datetime

class ModelRegistry:
    """Central registry for model versions and metadata"""
    
    def __init__(self, registry_path: str = "model_registry.db"):
        self.registry_path = registry_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the model registry database"""
        with sqlite3.connect(self.registry_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    model_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    description TEXT,
                    model_type TEXT NOT NULL,
                    framework TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tags TEXT,
                    parameters TEXT,
                    file_path TEXT,
                    file_hash TEXT,
                    file_size INTEGER,
                    parent_model_id TEXT,
                    training_data_hash TEXT,
                    UNIQUE(name, version)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    accuracy REAL,
                    latency_ms REAL,
                    throughput_rps REAL,
                    error_rate REAL,
                    cost_per_request REAL,
                    memory_usage_mb REAL,
                    cpu_usage_percent REAL,
                    user_satisfaction REAL,
                    custom_metrics TEXT,
                    FOREIGN KEY (model_id) REFERENCES models (model_id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_metrics_timestamp 
                ON model_metrics (model_id, timestamp)
            """)
    
    def register_model(self, metadata: ModelMetadata) -> str:
        """Register a new model version"""
        with self.lock:
            with sqlite3.connect(self.registry_path) as conn:
                try:
                    conn.execute("""
                        INSERT INTO models (
                            model_id, name, version, description, model_type, framework,
                            created_at, created_by, status, tags, parameters, file_path,
                            file_hash, file_size, parent_model_id, training_data_hash
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metadata.model_id, metadata.name, metadata.version,
                        metadata.description, metadata.model_type, metadata.framework,
                        metadata.created_at.isoformat(), metadata.created_by,
                        metadata.status.value, json.dumps(metadata.tags),
                        json.dumps(metadata.parameters), metadata.file_path,
                        metadata.file_hash, metadata.file_size,
                        metadata.parent_model_id, metadata.training_data_hash
                    ))
                    logger.info(f"Registered model {metadata.name} v{metadata.version}")
                    return metadata.model_id
                except sqlite3.IntegrityError as e:
                    raise ValueError(f"Model {metadata.name} v{metadata.version} already exists")
    
    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID"""
        with sqlite3.connect(self.registry_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM models WHERE model_id = ?", (model_id,)
            )
            row = cursor.fetchone()
            
            if row:
                data = dict(row)
                data['tags'] = json.loads(data['tags'])
                data['parameters'] = json.loads(data['parameters'])
                return ModelMetadata.from_dict(data)
            return None
    
    def list_models(self, 
                   model_type: Optional[str] = None,
                   status: Optional[ModelStatus] = None,
                   limit: int = 100) -> List[ModelMetadata]:
        """List models with optional filtering"""
        query = "SELECT * FROM models WHERE 1=1"
        params = []
        
        if model_type:
            query += " AND model_type = ?"
            params.append(model_type)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.registry_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            models = []
            for row in cursor.fetchall():
                data = dict(row)
                data['tags'] = json.loads(data['tags'])
                data['parameters'] = json.loads(data['parameters'])
                models.append(ModelMetadata.from_dict(data))
            
            return models
    
    def update_model_status(self, model_id: str, status: ModelStatus):
        """Update model deployment status"""
        with self.lock:
            with sqlite3.connect(self.registry_path) as conn:
                conn.execute(
                    "UPDATE models SET status = ? WHERE model_id = ?",
                    (status.value, model_id)
                )
                logger.info(f"Updated model {model_id} status to {status.value}")
    
    def record_metrics(self, metrics: ModelPerformanceMetrics):
        """Record performance metrics for a model"""
        with sqlite3.connect(self.registry_path) as conn:
            conn.execute("""
                INSERT INTO model_metrics (
                    model_id, timestamp, accuracy, latency_ms, throughput_rps,
                    error_rate, cost_per_request, memory_usage_mb, cpu_usage_percent,
                    user_satisfaction, custom_metrics
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.model_id, metrics.timestamp.isoformat(),
                metrics.accuracy, metrics.latency_ms, metrics.throughput_rps,
                metrics.error_rate, metrics.cost_per_request, metrics.memory_usage_mb,
                metrics.cpu_usage_percent, metrics.user_satisfaction,
                json.dumps(metrics.custom_metrics) if metrics.custom_metrics else None
            ))
    
    def get_model_metrics(self, 
                         model_id: str,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 1000) -> List[ModelPerformanceMetrics]:
        """Get performance metrics for a model"""
        query = "SELECT * FROM model_metrics WHERE model_id = ?"
        params = [model_id]
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.registry_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            metrics = []
            for row in cursor.fetchall():
                data = dict(row)
                if data['custom_metrics']:
                    data['custom_metrics'] = json.loads(data['custom_metrics'])
                metrics.append(ModelPerformanceMetrics.from_dict(data))
            
            return metrics

class ABTestingFramework:
    """A/B testing framework for model comparison"""
    
    def __init__(self, registry: ModelRegistry, experiments_path: str = "experiments.db"):
        self.registry = registry
        self.experiments_path = experiments_path
        self.active_experiments: Dict[str, ABTestExperiment] = {}
        self.experiment_data: Dict[str, Dict] = defaultdict(lambda: {
            'control': defaultdict(list),
            'treatment': defaultdict(list)
        })
        self.lock = threading.Lock()
        self._init_database()
        self._load_active_experiments()
    
    def _init_database(self):
        """Initialize experiments database"""
        with sqlite3.connect(self.experiments_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    control_model_id TEXT NOT NULL,
                    treatment_model_id TEXT NOT NULL,
                    traffic_split REAL NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    status TEXT NOT NULL,
                    success_metrics TEXT NOT NULL,
                    minimum_sample_size INTEGER NOT NULL,
                    confidence_level REAL NOT NULL,
                    created_by TEXT NOT NULL,
                    tags TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiment_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    variant TEXT NOT NULL,
                    user_id TEXT,
                    timestamp TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
                )
            """)
    
    def _load_active_experiments(self):
        """Load active experiments from database"""
        with sqlite3.connect(self.experiments_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM experiments WHERE status = ?",
                (ExperimentStatus.RUNNING.value,)
            )
            
            for row in cursor.fetchall():
                data = dict(row)
                data['tags'] = json.loads(data['tags'])
                data['success_metrics'] = json.loads(data['success_metrics'])
                data['metadata'] = json.loads(data['metadata'])
                experiment = ABTestExperiment.from_dict(data)
                self.active_experiments[experiment.experiment_id] = experiment
    
    def create_experiment(self, experiment: ABTestExperiment) -> str:
        """Create a new A/B test experiment"""
        # Validate models exist
        control_model = self.registry.get_model(experiment.control_model_id)
        treatment_model = self.registry.get_model(experiment.treatment_model_id)
        
        if not control_model:
            raise ValueError(f"Control model {experiment.control_model_id} not found")
        if not treatment_model:
            raise ValueError(f"Treatment model {experiment.treatment_model_id} not found")
        
        with self.lock:
            with sqlite3.connect(self.experiments_path) as conn:
                conn.execute("""
                    INSERT INTO experiments (
                        experiment_id, name, description, control_model_id, treatment_model_id,
                        traffic_split, start_date, end_date, status, success_metrics,
                        minimum_sample_size, confidence_level, created_by, tags, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    experiment.experiment_id, experiment.name, experiment.description,
                    experiment.control_model_id, experiment.treatment_model_id,
                    experiment.traffic_split, experiment.start_date.isoformat(),
                    experiment.end_date.isoformat() if experiment.end_date else None,
                    experiment.status.value, json.dumps(experiment.success_metrics),
                    experiment.minimum_sample_size, experiment.confidence_level,
                    experiment.created_by, json.dumps(experiment.tags),
                    json.dumps(experiment.metadata)
                ))
                
                if experiment.status == ExperimentStatus.RUNNING:
                    self.active_experiments[experiment.experiment_id] = experiment
                
                logger.info(f"Created experiment {experiment.name}")
                return experiment.experiment_id
    
    def start_experiment(self, experiment_id: str):
        """Start an A/B test experiment"""
        with self.lock:
            with sqlite3.connect(self.experiments_path) as conn:
                conn.execute(
                    "UPDATE experiments SET status = ? WHERE experiment_id = ?",
                    (ExperimentStatus.RUNNING.value, experiment_id)
                )
                
                # Load experiment
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM experiments WHERE experiment_id = ?",
                    (experiment_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    data = dict(row)
                    data['tags'] = json.loads(data['tags'])
                    data['success_metrics'] = json.loads(data['success_metrics'])
                    data['metadata'] = json.loads(data['metadata'])
                    experiment = ABTestExperiment.from_dict(data)
                    self.active_experiments[experiment_id] = experiment
                    logger.info(f"Started experiment {experiment.name}")
    
    def stop_experiment(self, experiment_id: str):
        """Stop an A/B test experiment"""
        with self.lock:
            with sqlite3.connect(self.experiments_path) as conn:
                conn.execute(
                    "UPDATE experiments SET status = ?, end_date = ? WHERE experiment_id = ?",
                    (ExperimentStatus.COMPLETED.value, datetime.now().isoformat(), experiment_id)
                )
                
                if experiment_id in self.active_experiments:
                    del self.active_experiments[experiment_id]
                    logger.info(f"Stopped experiment {experiment_id}")
    
    def assign_variant(self, experiment_id: str, user_id: str) -> str:
        """Assign user to control or treatment variant"""
        if experiment_id not in self.active_experiments:
            return "control"  # Default to control if experiment not active
        
        experiment = self.active_experiments[experiment_id]
        
        # Use consistent hashing for user assignment
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        assignment_value = (hash_value % 10000) / 10000.0
        
        return "treatment" if assignment_value < experiment.traffic_split else "control"
    
    def record_experiment_data(self, 
                             experiment_id: str,
                             variant: str,
                             user_id: str,
                             metrics: Dict[str, float]):
        """Record data point for experiment"""
        if experiment_id not in self.active_experiments:
            return
        
        with sqlite3.connect(self.experiments_path) as conn:
            conn.execute("""
                INSERT INTO experiment_data (
                    experiment_id, variant, user_id, timestamp, metrics
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                experiment_id, variant, user_id,
                datetime.now().isoformat(), json.dumps(metrics)
            ))
        
        # Store in memory for real-time analysis
        for metric_name, value in metrics.items():
            self.experiment_data[experiment_id][variant][metric_name].append(value)
    
    def analyze_experiment(self, experiment_id: str) -> ExperimentResult:
        """Analyze experiment results with statistical significance"""
        experiment = self.active_experiments.get(experiment_id)
        if not experiment:
            # Load from database if not active
            with sqlite3.connect(self.experiments_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM experiments WHERE experiment_id = ?",
                    (experiment_id,)
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Experiment {experiment_id} not found")
                
                data = dict(row)
                data['tags'] = json.loads(data['tags'])
                data['success_metrics'] = json.loads(data['success_metrics'])
                data['metadata'] = json.loads(data['metadata'])
                experiment = ABTestExperiment.from_dict(data)
        
        # Load experiment data from database
        control_data = defaultdict(list)
        treatment_data = defaultdict(list)
        
        with sqlite3.connect(self.experiments_path) as conn:
            cursor = conn.execute("""
                SELECT variant, metrics FROM experiment_data 
                WHERE experiment_id = ?
            """, (experiment_id,))
            
            for variant, metrics_json in cursor.fetchall():
                metrics = json.loads(metrics_json)
                target_data = control_data if variant == "control" else treatment_data
                
                for metric_name, value in metrics.items():
                    target_data[metric_name].append(value)
        
        # Calculate statistics
        control_metrics = {}
        treatment_metrics = {}
        statistical_significance = {}
        confidence_intervals = {}
        sample_sizes = {}
        p_values = {}
        effect_sizes = {}
        
        for metric in experiment.success_metrics:
            if metric in control_data and metric in treatment_data:
                control_values = control_data[metric]
                treatment_values = treatment_data[metric]
                
                if len(control_values) > 0 and len(treatment_values) > 0:
                    control_metrics[metric] = statistics.mean(control_values)
                    treatment_metrics[metric] = statistics.mean(treatment_values)
                    sample_sizes[metric] = len(control_values) + len(treatment_values)
                    
                    # Simple t-test approximation
                    if len(control_values) > 1 and len(treatment_values) > 1:
                        control_std = statistics.stdev(control_values)
                        treatment_std = statistics.stdev(treatment_values)
                        
                        # Effect size (Cohen's d)
                        pooled_std = ((control_std ** 2 + treatment_std ** 2) / 2) ** 0.5
                        if pooled_std > 0:
                            effect_sizes[metric] = (treatment_metrics[metric] - control_metrics[metric]) / pooled_std
                        else:
                            effect_sizes[metric] = 0.0
                        
                        # Simplified p-value calculation (would use proper t-test in production)
                        diff = abs(treatment_metrics[metric] - control_metrics[metric])
                        se = (control_std ** 2 / len(control_values) + treatment_std ** 2 / len(treatment_values)) ** 0.5
                        if se > 0:
                            t_stat = diff / se
                            # Rough p-value approximation
                            p_values[metric] = max(0.001, min(0.999, 2 * (1 - min(0.999, t_stat / 3))))
                        else:
                            p_values[metric] = 1.0
                        
                        # Confidence interval (95%)
                        margin_error = 1.96 * se
                        diff_mean = treatment_metrics[metric] - control_metrics[metric]
                        confidence_intervals[metric] = (
                            diff_mean - margin_error,
                            diff_mean + margin_error
                        )
                        
                        statistical_significance[metric] = p_values[metric] < 0.05
        
        # Generate recommendation
        significant_improvements = sum(1 for metric in experiment.success_metrics 
                                     if statistical_significance.get(metric, False) 
                                     and treatment_metrics.get(metric, 0) > control_metrics.get(metric, 0))
        
        total_metrics = len(experiment.success_metrics)
        min_sample_reached = all(sample_sizes.get(metric, 0) >= experiment.minimum_sample_size 
                               for metric in experiment.success_metrics)
        
        if not min_sample_reached:
            recommendation = "Continue experiment - minimum sample size not reached"
        elif significant_improvements >= total_metrics * 0.6:
            recommendation = "Deploy treatment model - significant improvement detected"
        elif significant_improvements == 0:
            recommendation = "Keep control model - no significant improvement"
        else:
            recommendation = "Mixed results - consider additional analysis"
        
        return ExperimentResult(
            experiment_id=experiment_id,
            control_metrics=control_metrics,
            treatment_metrics=treatment_metrics,
            statistical_significance=statistical_significance,
            confidence_intervals=confidence_intervals,
            sample_sizes=sample_sizes,
            recommendation=recommendation,
            p_values=p_values,
            effect_sizes=effect_sizes,
            generated_at=datetime.now()
        )

class ModelPerformanceMonitor:
    """Monitor model performance and detect drift"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.alert_thresholds = {
            'accuracy_drop': 0.05,      # 5% accuracy drop
            'latency_increase': 2.0,    # 2x latency increase
            'error_rate_increase': 0.1, # 10% error rate increase
            'cost_increase': 1.5        # 1.5x cost increase
        }
        self.baseline_window_days = 7
        self.monitoring_window_hours = 24
    
    def check_model_health(self, model_id: str) -> Dict[str, Any]:
        """Check model health and detect performance drift"""
        now = datetime.now()
        baseline_start = now - timedelta(days=self.baseline_window_days + 1)
        baseline_end = now - timedelta(days=1)
        current_start = now - timedelta(hours=self.monitoring_window_hours)
        
        # Get baseline metrics
        baseline_metrics = self.registry.get_model_metrics(
            model_id, baseline_start, baseline_end
        )
        
        # Get current metrics
        current_metrics = self.registry.get_model_metrics(
            model_id, current_start, now
        )
        
        if not baseline_metrics or not current_metrics:
            return {
                'status': 'insufficient_data',
                'message': 'Not enough data for health check',
                'alerts': []
            }
        
        # Calculate baseline averages
        baseline_avg = self._calculate_average_metrics(baseline_metrics)
        current_avg = self._calculate_average_metrics(current_metrics)
        
        alerts = []
        
        # Check for performance degradation
        if (baseline_avg.get('accuracy') and current_avg.get('accuracy') and
            baseline_avg['accuracy'] - current_avg['accuracy'] > self.alert_thresholds['accuracy_drop']):
            alerts.append({
                'type': 'accuracy_drop',
                'severity': 'high',
                'message': f"Accuracy dropped from {baseline_avg['accuracy']:.3f} to {current_avg['accuracy']:.3f}",
                'baseline': baseline_avg['accuracy'],
                'current': current_avg['accuracy']
            })
        
        if (baseline_avg.get('latency_ms') and current_avg.get('latency_ms') and
            current_avg['latency_ms'] / baseline_avg['latency_ms'] > self.alert_thresholds['latency_increase']):
            alerts.append({
                'type': 'latency_increase',
                'severity': 'medium',
                'message': f"Latency increased from {baseline_avg['latency_ms']:.1f}ms to {current_avg['latency_ms']:.1f}ms",
                'baseline': baseline_avg['latency_ms'],
                'current': current_avg['latency_ms']
            })
        
        if (baseline_avg.get('error_rate') and current_avg.get('error_rate') and
            current_avg['error_rate'] - baseline_avg['error_rate'] > self.alert_thresholds['error_rate_increase']):
            alerts.append({
                'type': 'error_rate_increase',
                'severity': 'high',
                'message': f"Error rate increased from {baseline_avg['error_rate']:.3f} to {current_avg['error_rate']:.3f}",
                'baseline': baseline_avg['error_rate'],
                'current': current_avg['error_rate']
            })
        
        if (baseline_avg.get('cost_per_request') and current_avg.get('cost_per_request') and
            current_avg['cost_per_request'] / baseline_avg['cost_per_request'] > self.alert_thresholds['cost_increase']):
            alerts.append({
                'type': 'cost_increase',
                'severity': 'medium',
                'message': f"Cost increased from ${baseline_avg['cost_per_request']:.4f} to ${current_avg['cost_per_request']:.4f}",
                'baseline': baseline_avg['cost_per_request'],
                'current': current_avg['cost_per_request']
            })
        
        # Determine overall status
        if any(alert['severity'] == 'high' for alert in alerts):
            status = 'unhealthy'
        elif any(alert['severity'] == 'medium' for alert in alerts):
            status = 'degraded'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'alerts': alerts,
            'baseline_metrics': baseline_avg,
            'current_metrics': current_avg,
            'sample_sizes': {
                'baseline': len(baseline_metrics),
                'current': len(current_metrics)
            }
        }
    
    def _calculate_average_metrics(self, metrics: List[ModelPerformanceMetrics]) -> Dict[str, float]:
        """Calculate average metrics from a list"""
        if not metrics:
            return {}
        
        totals = defaultdict(list)
        for metric in metrics:
            if metric.accuracy is not None:
                totals['accuracy'].append(metric.accuracy)
            if metric.latency_ms is not None:
                totals['latency_ms'].append(metric.latency_ms)
            if metric.throughput_rps is not None:
                totals['throughput_rps'].append(metric.throughput_rps)
            if metric.error_rate is not None:
                totals['error_rate'].append(metric.error_rate)
            if metric.cost_per_request is not None:
                totals['cost_per_request'].append(metric.cost_per_request)
            if metric.memory_usage_mb is not None:
                totals['memory_usage_mb'].append(metric.memory_usage_mb)
            if metric.cpu_usage_percent is not None:
                totals['cpu_usage_percent'].append(metric.cpu_usage_percent)
            if metric.user_satisfaction is not None:
                totals['user_satisfaction'].append(metric.user_satisfaction)
        
        averages = {}
        for key, values in totals.items():
            if values:
                averages[key] = statistics.mean(values)
        
        return averages

class CostOptimizer:
    """Optimize model selection based on cost and performance"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.cost_weights = {
            'accuracy': 0.4,
            'latency': 0.3,
            'cost': 0.3
        }
    
    def recommend_model(self, 
                       model_type: str,
                       requirements: Dict[str, float]) -> Optional[str]:
        """Recommend best model based on requirements and cost"""
        models = self.registry.list_models(
            model_type=model_type,
            status=ModelStatus.PRODUCTION
        )
        
        if not models:
            return None
        
        best_model = None
        best_score = -1
        
        for model in models:
            # Get recent performance metrics
            recent_metrics = self.registry.get_model_metrics(
                model.model_id,
                start_date=datetime.now() - timedelta(days=7),
                limit=100
            )
            
            if not recent_metrics:
                continue
            
            avg_metrics = self._calculate_average_metrics(recent_metrics)
            score = self._calculate_model_score(avg_metrics, requirements)
            
            if score > best_score:
                best_score = score
                best_model = model.model_id
        
        return best_model
    
    def _calculate_model_score(self, 
                              metrics: Dict[str, float],
                              requirements: Dict[str, float]) -> float:
        """Calculate model score based on requirements"""
        score = 0.0
        
        # Accuracy score (higher is better)
        if 'accuracy' in metrics and 'min_accuracy' in requirements:
            if metrics['accuracy'] >= requirements['min_accuracy']:
                score += self.cost_weights['accuracy'] * (metrics['accuracy'] / requirements['min_accuracy'])
        
        # Latency score (lower is better)
        if 'latency_ms' in metrics and 'max_latency_ms' in requirements:
            if metrics['latency_ms'] <= requirements['max_latency_ms']:
                score += self.cost_weights['latency'] * (requirements['max_latency_ms'] / metrics['latency_ms'])
        
        # Cost score (lower is better)
        if 'cost_per_request' in metrics and 'max_cost_per_request' in requirements:
            if metrics['cost_per_request'] <= requirements['max_cost_per_request']:
                score += self.cost_weights['cost'] * (requirements['max_cost_per_request'] / metrics['cost_per_request'])
        
        return score
    
    def _calculate_average_metrics(self, metrics: List[ModelPerformanceMetrics]) -> Dict[str, float]:
        """Calculate average metrics from a list"""
        if not metrics:
            return {}
        
        totals = defaultdict(list)
        for metric in metrics:
            if metric.accuracy is not None:
                totals['accuracy'].append(metric.accuracy)
            if metric.latency_ms is not None:
                totals['latency_ms'].append(metric.latency_ms)
            if metric.cost_per_request is not None:
                totals['cost_per_request'].append(metric.cost_per_request)
        
        averages = {}
        for key, values in totals.items():
            if values:
                averages[key] = statistics.mean(values)
        
        return averages

class ModelManagementService:
    """Main service for AI model management"""
    
    def __init__(self, registry_path: str = "model_registry.db"):
        self.registry = ModelRegistry(registry_path)
        self.ab_testing = ABTestingFramework(self.registry)
        self.monitor = ModelPerformanceMonitor(self.registry)
        self.optimizer = CostOptimizer(self.registry)
    
    def create_model_version(self,
                           name: str,
                           version: str,
                           description: str,
                           model_type: str,
                           framework: str,
                           created_by: str,
                           parameters: Dict[str, Any],
                           file_path: Optional[str] = None,
                           tags: Optional[List[str]] = None,
                           parent_model_id: Optional[str] = None) -> str:
        """Create a new model version"""
        model_id = str(uuid.uuid4())
        
        # Calculate file hash if file provided
        file_hash = None
        file_size = None
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
                file_size = os.path.getsize(file_path)
        
        metadata = ModelMetadata(
            model_id=model_id,
            name=name,
            version=version,
            description=description,
            model_type=model_type,
            framework=framework,
            created_at=datetime.now(),
            created_by=created_by,
            status=ModelStatus.DEVELOPMENT,
            tags=tags or [],
            parameters=parameters,
            file_path=file_path,
            file_hash=file_hash,
            file_size=file_size,
            parent_model_id=parent_model_id
        )
        
        return self.registry.register_model(metadata)
    
    def deploy_model(self, model_id: str, environment: str = "production") -> bool:
        """Deploy model to specified environment"""
        model = self.registry.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        # Update status based on environment
        status_map = {
            "development": ModelStatus.DEVELOPMENT,
            "testing": ModelStatus.TESTING,
            "staging": ModelStatus.STAGING,
            "production": ModelStatus.PRODUCTION
        }
        
        if environment not in status_map:
            raise ValueError(f"Invalid environment: {environment}")
        
        self.registry.update_model_status(model_id, status_map[environment])
        logger.info(f"Deployed model {model.name} v{model.version} to {environment}")
        return True
    
    def rollback_model(self, current_model_id: str, target_model_id: str) -> bool:
        """Rollback from current model to target model"""
        current_model = self.registry.get_model(current_model_id)
        target_model = self.registry.get_model(target_model_id)
        
        if not current_model or not target_model:
            raise ValueError("One or both models not found")
        
        # Update statuses
        self.registry.update_model_status(current_model_id, ModelStatus.DEPRECATED)
        self.registry.update_model_status(target_model_id, ModelStatus.PRODUCTION)
        
        logger.info(f"Rolled back from {current_model.name} v{current_model.version} "
                   f"to {target_model.name} v{target_model.version}")
        return True
    
    def start_ab_test(self,
                     name: str,
                     description: str,
                     control_model_id: str,
                     treatment_model_id: str,
                     traffic_split: float,
                     success_metrics: List[str],
                     duration_days: int,
                     created_by: str,
                     minimum_sample_size: int = 1000,
                     confidence_level: float = 0.95) -> str:
        """Start an A/B test between two models"""
        experiment_id = str(uuid.uuid4())
        
        experiment = ABTestExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            control_model_id=control_model_id,
            treatment_model_id=treatment_model_id,
            traffic_split=traffic_split,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=duration_days),
            status=ExperimentStatus.RUNNING,
            success_metrics=success_metrics,
            minimum_sample_size=minimum_sample_size,
            confidence_level=confidence_level,
            created_by=created_by,
            tags=[],
            metadata={}
        )
        
        return self.ab_testing.create_experiment(experiment)
    
    def get_model_recommendation(self,
                               model_type: str,
                               requirements: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Get model recommendation based on requirements"""
        recommended_model_id = self.optimizer.recommend_model(model_type, requirements)
        
        if not recommended_model_id:
            return None
        
        model = self.registry.get_model(recommended_model_id)
        recent_metrics = self.registry.get_model_metrics(
            recommended_model_id,
            start_date=datetime.now() - timedelta(days=7),
            limit=100
        )
        
        avg_metrics = {}
        if recent_metrics:
            totals = defaultdict(list)
            for metric in recent_metrics:
                if metric.accuracy is not None:
                    totals['accuracy'].append(metric.accuracy)
                if metric.latency_ms is not None:
                    totals['latency_ms'].append(metric.latency_ms)
                if metric.cost_per_request is not None:
                    totals['cost_per_request'].append(metric.cost_per_request)
            
            for key, values in totals.items():
                if values:
                    avg_metrics[key] = statistics.mean(values)
        
        return {
            'model_id': recommended_model_id,
            'model_name': model.name,
            'model_version': model.version,
            'recent_performance': avg_metrics,
            'recommendation_reason': 'Best cost-performance ratio for requirements'
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        production_models = self.registry.list_models(status=ModelStatus.PRODUCTION)
        
        health_status = {
            'overall_status': 'healthy',
            'production_models': len(production_models),
            'model_health': {},
            'active_experiments': len(self.ab_testing.active_experiments),
            'alerts': []
        }
        
        unhealthy_count = 0
        degraded_count = 0
        
        for model in production_models:
            health = self.monitor.check_model_health(model.model_id)
            health_status['model_health'][model.model_id] = {
                'name': model.name,
                'version': model.version,
                'status': health['status'],
                'alert_count': len(health.get('alerts', []))
            }
            
            if health['status'] == 'unhealthy':
                unhealthy_count += 1
            elif health['status'] == 'degraded':
                degraded_count += 1
            
            # Add high-severity alerts to system alerts
            for alert in health.get('alerts', []):
                if alert['severity'] == 'high':
                    health_status['alerts'].append({
                        'model_id': model.model_id,
                        'model_name': model.name,
                        'alert': alert
                    })
        
        # Determine overall status
        if unhealthy_count > 0:
            health_status['overall_status'] = 'unhealthy'
        elif degraded_count > 0:
            health_status['overall_status'] = 'degraded'
        
        return health_status

# Example usage and testing functions
def create_sample_models(service: ModelManagementService):
    """Create sample models for testing"""
    models = [
        {
            'name': 'whisper-transcription',
            'version': '1.0.0',
            'description': 'OpenAI Whisper base model for transcription',
            'model_type': 'transcription',
            'framework': 'openai',
            'parameters': {'model_size': 'base', 'language': 'en'}
        },
        {
            'name': 'whisper-transcription',
            'version': '1.1.0',
            'description': 'OpenAI Whisper large model for transcription',
            'model_type': 'transcription',
            'framework': 'openai',
            'parameters': {'model_size': 'large', 'language': 'en'}
        },
        {
            'name': 'gpt-analysis',
            'version': '1.0.0',
            'description': 'GPT-4 for content analysis',
            'model_type': 'analysis',
            'framework': 'openai',
            'parameters': {'model': 'gpt-4', 'temperature': 0.1}
        }
    ]
    
    model_ids = []
    for model_config in models:
        model_id = service.create_model_version(
            created_by='system',
            tags=['sample', 'test'],
            **model_config
        )
        model_ids.append(model_id)
        
        # Deploy to production
        service.deploy_model(model_id, 'production')
        
        # Add some sample metrics
        for i in range(10):
            metrics = ModelPerformanceMetrics(
                model_id=model_id,
                timestamp=datetime.now() - timedelta(hours=i),
                accuracy=0.85 + (i * 0.01),
                latency_ms=100 + (i * 10),
                cost_per_request=0.001 + (i * 0.0001),
                error_rate=0.01 - (i * 0.001)
            )
            service.registry.record_metrics(metrics)
    
    return model_ids

if __name__ == "__main__":
    # Example usage
    service = ModelManagementService()
    
    # Create sample models
    model_ids = create_sample_models(service)
    
    # Start an A/B test
    if len(model_ids) >= 2:
        experiment_id = service.start_ab_test(
            name="Whisper Model Comparison",
            description="Compare base vs large Whisper models",
            control_model_id=model_ids[0],
            treatment_model_id=model_ids[1],
            traffic_split=0.5,
            success_metrics=['accuracy', 'latency_ms'],
            duration_days=7,
            created_by='admin'
        )
        print(f"Started A/B test: {experiment_id}")
    
    # Get model recommendation
    recommendation = service.get_model_recommendation(
        model_type='transcription',
        requirements={
            'min_accuracy': 0.8,
            'max_latency_ms': 200,
            'max_cost_per_request': 0.002
        }
    )
    print(f"Model recommendation: {recommendation}")
    
    # Check system health
    health = service.get_system_health()
    print(f"System health: {health['overall_status']}")
    print(f"Production models: {health['production_models']}")
    print(f"Active experiments: {health['active_experiments']}")