"""
AI Model Management & Fine-tuning System
Comprehensive model lifecycle management with versioning, A/B testing, and fine-tuning
"""

import asyncio
import json
import uuid
import hashlib
import pickle
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import transformers
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    EvalPrediction
)
import whisper
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import pandas as pd
import redis.asyncio as redis
import mlflow
import optuna
from optuna.integration import PyTorchLightningPruningCallback
import logging
import boto3
from collections import defaultdict
import wandb
import onnx
import onnxruntime as ort

logger = logging.getLogger(__name__)

class ModelType(str, Enum):
    """Model types"""
    WHISPER = "whisper"
    BERT = "bert"
    GPT = "gpt"
    T5 = "t5"
    CUSTOM = "custom"
    ENSEMBLE = "ensemble"

class ModelStatus(str, Enum):
    """Model status"""
    TRAINING = "training"
    VALIDATING = "validating"
    READY = "ready"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ARCHIVED = "archived"

class DeploymentStrategy(str, Enum):
    """Deployment strategies"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    SHADOW = "shadow"
    AB_TEST = "ab_test"

@dataclass
class ModelMetadata:
    """Model metadata"""
    id: str
    name: str
    type: ModelType
    version: str
    status: ModelStatus
    created_at: datetime
    updated_at: datetime
    created_by: str
    description: str
    base_model: Optional[str] = None
    training_config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)
    deployment_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'version': self.version,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'description': self.description,
            'base_model': self.base_model,
            'training_config': self.training_config,
            'metrics': self.metrics,
            'parameters': self.parameters,
            'tags': self.tags,
            'artifacts': self.artifacts,
            'deployment_info': self.deployment_info
        }

@dataclass
class TrainingJob:
    """Training job information"""
    id: str
    model_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    epochs_completed: int = 0
    total_epochs: int = 0
    current_loss: float = 0.0
    best_metric: float = 0.0
    logs: List[str] = field(default_factory=list)
    checkpoints: List[str] = field(default_factory=list)
    
    def add_log(self, message: str):
        """Add log entry"""
        timestamp = datetime.utcnow().isoformat()
        self.logs.append(f"[{timestamp}] {message}")

@dataclass
class ABTestConfig:
    """A/B test configuration"""
    id: str
    name: str
    model_a_id: str
    model_b_id: str
    traffic_split: float  # Percentage for model A (0-100)
    metrics_to_track: List[str]
    success_criteria: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    results: Dict[str, Any] = field(default_factory=dict)

class CustomDataset(Dataset):
    """Custom dataset for fine-tuning"""
    
    def __init__(self, data: List[Dict], tokenizer, max_length: int = 512):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # Tokenize input
        encoding = self.tokenizer(
            item['text'],
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(item.get('label', 0), dtype=torch.long)
        }

class ModelRegistry:
    """Central model registry"""
    
    def __init__(self, storage_path: str = "./models", s3_bucket: Optional[str] = None):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if s3_bucket else None
        self.models: Dict[str, ModelMetadata] = {}
        self.active_models: Dict[str, str] = {}  # deployment -> model_id
        
    async def register_model(
        self,
        model: Any,
        metadata: ModelMetadata,
        artifacts: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new model"""
        # Save model locally
        model_path = self.storage_path / metadata.id
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Save model based on type
        if metadata.type == ModelType.WHISPER:
            # Whisper models are already saved
            pass
        elif metadata.type in [ModelType.BERT, ModelType.GPT, ModelType.T5]:
            # Save transformer model
            model.save_pretrained(str(model_path))
            if artifacts and 'tokenizer' in artifacts:
                artifacts['tokenizer'].save_pretrained(str(model_path))
        else:
            # Save custom model
            torch.save(model.state_dict(), model_path / "model.pt")
            
        # Save metadata
        with open(model_path / "metadata.json", 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
            
        # Upload to S3 if configured
        if self.s3_client and self.s3_bucket:
            await self._upload_to_s3(metadata.id, model_path)
            
        self.models[metadata.id] = metadata
        
        logger.info(f"Registered model: {metadata.id}")
        return metadata.id
        
    async def load_model(self, model_id: str) -> Tuple[Any, ModelMetadata]:
        """Load a model from registry"""
        if model_id not in self.models:
            # Try to load from disk
            model_path = self.storage_path / model_id
            if not model_path.exists():
                # Try to download from S3
                if self.s3_client and self.s3_bucket:
                    await self._download_from_s3(model_id, model_path)
                else:
                    raise ValueError(f"Model {model_id} not found")
                    
            # Load metadata
            with open(model_path / "metadata.json", 'r') as f:
                metadata_dict = json.load(f)
                metadata = ModelMetadata(**metadata_dict)
                self.models[model_id] = metadata
        else:
            metadata = self.models[model_id]
            model_path = self.storage_path / model_id
            
        # Load model based on type
        if metadata.type == ModelType.WHISPER:
            model = whisper.load_model(metadata.parameters.get('size', 'base'))
        elif metadata.type == ModelType.BERT:
            model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
        else:
            # Load custom model
            model = torch.load(model_path / "model.pt")
            
        return model, metadata
        
    async def _upload_to_s3(self, model_id: str, model_path: Path):
        """Upload model to S3"""
        for file_path in model_path.rglob('*'):
            if file_path.is_file():
                s3_key = f"models/{model_id}/{file_path.relative_to(model_path)}"
                self.s3_client.upload_file(str(file_path), self.s3_bucket, s3_key)
                
    async def _download_from_s3(self, model_id: str, model_path: Path):
        """Download model from S3"""
        model_path.mkdir(parents=True, exist_ok=True)
        
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=f"models/{model_id}/")
        
        for page in pages:
            for obj in page.get('Contents', []):
                s3_key = obj['Key']
                local_path = model_path / s3_key.replace(f"models/{model_id}/", "")
                local_path.parent.mkdir(parents=True, exist_ok=True)
                self.s3_client.download_file(self.s3_bucket, s3_key, str(local_path))

class ModelTrainer:
    """Handles model training and fine-tuning"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.training_jobs: Dict[str, TrainingJob] = {}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    async def fine_tune_transformer(
        self,
        base_model_name: str,
        train_data: List[Dict],
        val_data: List[Dict],
        model_name: str,
        user_id: str,
        config: Optional[Dict] = None
    ) -> str:
        """Fine-tune a transformer model"""
        job_id = str(uuid.uuid4())
        model_id = str(uuid.uuid4())
        
        # Create training job
        job = TrainingJob(
            id=job_id,
            model_id=model_id,
            status="initializing",
            started_at=datetime.utcnow()
        )
        self.training_jobs[job_id] = job
        
        try:
            # Load base model and tokenizer
            tokenizer = AutoTokenizer.from_pretrained(base_model_name)
            model = AutoModelForSequenceClassification.from_pretrained(
                base_model_name,
                num_labels=config.get('num_labels', 2)
            )
            model.to(self.device)
            
            # Create datasets
            train_dataset = CustomDataset(train_data, tokenizer)
            val_dataset = CustomDataset(val_data, tokenizer)
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=f"./models/{model_id}/checkpoints",
                num_train_epochs=config.get('epochs', 3),
                per_device_train_batch_size=config.get('batch_size', 16),
                per_device_eval_batch_size=config.get('batch_size', 16),
                warmup_steps=config.get('warmup_steps', 500),
                weight_decay=config.get('weight_decay', 0.01),
                logging_dir=f"./models/{model_id}/logs",
                evaluation_strategy="epoch",
                save_strategy="epoch",
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
            )
            
            # Create trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                compute_metrics=self._compute_metrics,
                callbacks=[self._create_callback(job)]
            )
            
            # Start training
            job.status = "training"
            job.total_epochs = training_args.num_train_epochs
            
            trainer.train()
            
            # Evaluate
            job.status = "validating"
            eval_results = trainer.evaluate()
            
            # Create model metadata
            metadata = ModelMetadata(
                id=model_id,
                name=model_name,
                type=ModelType.BERT,
                version="1.0.0",
                status=ModelStatus.READY,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by=user_id,
                description=f"Fine-tuned from {base_model_name}",
                base_model=base_model_name,
                training_config=config or {},
                metrics=eval_results,
                parameters={'num_labels': config.get('num_labels', 2)}
            )
            
            # Register model
            await self.registry.register_model(
                model,
                metadata,
                {'tokenizer': tokenizer}
            )
            
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.best_metric = eval_results.get('eval_loss', 0)
            
            logger.info(f"Fine-tuning completed: {model_id}")
            return model_id
            
        except Exception as e:
            job.status = "failed"
            job.add_log(f"Error: {str(e)}")
            logger.error(f"Fine-tuning failed: {e}")
            raise
            
    def _compute_metrics(self, eval_pred: EvalPrediction) -> Dict:
        """Compute metrics for evaluation"""
        predictions = np.argmax(eval_pred.predictions, axis=1)
        precision, recall, f1, _ = precision_recall_fscore_support(
            eval_pred.label_ids,
            predictions,
            average='weighted'
        )
        accuracy = accuracy_score(eval_pred.label_ids, predictions)
        
        return {
            'accuracy': accuracy,
            'f1': f1,
            'precision': precision,
            'recall': recall
        }
        
    def _create_callback(self, job: TrainingJob):
        """Create training callback"""
        class JobCallback(transformers.TrainerCallback):
            def on_epoch_end(self, args, state, control, **kwargs):
                job.epochs_completed = state.epoch
                job.current_loss = state.log_history[-1].get('loss', 0)
                job.add_log(f"Epoch {state.epoch} completed, loss: {job.current_loss:.4f}")
                
        return JobCallback()
        
    async def hyperparameter_optimization(
        self,
        base_model_name: str,
        train_data: List[Dict],
        val_data: List[Dict],
        n_trials: int = 20
    ) -> Dict:
        """Perform hyperparameter optimization using Optuna"""
        
        def objective(trial):
            # Suggest hyperparameters
            learning_rate = trial.suggest_float('learning_rate', 1e-5, 1e-3, log=True)
            batch_size = trial.suggest_categorical('batch_size', [8, 16, 32])
            num_epochs = trial.suggest_int('num_epochs', 2, 5)
            warmup_steps = trial.suggest_int('warmup_steps', 0, 1000, step=100)
            weight_decay = trial.suggest_float('weight_decay', 0.0, 0.1)
            
            # Train model with suggested hyperparameters
            config = {
                'learning_rate': learning_rate,
                'batch_size': batch_size,
                'epochs': num_epochs,
                'warmup_steps': warmup_steps,
                'weight_decay': weight_decay
            }
            
            # This would actually train the model
            # For demonstration, return a random score
            return np.random.random()
            
        # Create study
        study = optuna.create_study(
            direction='maximize',
            pruner=optuna.pruners.MedianPruner()
        )
        
        # Optimize
        study.optimize(objective, n_trials=n_trials)
        
        # Get best parameters
        best_params = study.best_params
        best_value = study.best_value
        
        logger.info(f"Best hyperparameters: {best_params}")
        logger.info(f"Best value: {best_value}")
        
        return {
            'best_params': best_params,
            'best_value': best_value,
            'n_trials': n_trials
        }

class ModelDeployer:
    """Handles model deployment and serving"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.deployments: Dict[str, Dict[str, Any]] = {}
        self.ab_tests: Dict[str, ABTestConfig] = {}
        
    async def deploy_model(
        self,
        model_id: str,
        deployment_name: str,
        strategy: DeploymentStrategy = DeploymentStrategy.BLUE_GREEN,
        config: Optional[Dict] = None
    ) -> str:
        """Deploy a model"""
        deployment_id = str(uuid.uuid4())
        
        # Load model
        model, metadata = await self.registry.load_model(model_id)
        
        if strategy == DeploymentStrategy.BLUE_GREEN:
            await self._deploy_blue_green(deployment_id, model_id, deployment_name)
        elif strategy == DeploymentStrategy.CANARY:
            await self._deploy_canary(deployment_id, model_id, deployment_name, config)
        elif strategy == DeploymentStrategy.AB_TEST:
            await self._deploy_ab_test(deployment_id, model_id, deployment_name, config)
        else:
            # Simple deployment
            self.deployments[deployment_id] = {
                'model_id': model_id,
                'name': deployment_name,
                'strategy': strategy.value,
                'status': 'active',
                'created_at': datetime.utcnow().isoformat()
            }
            
        # Update model status
        metadata.status = ModelStatus.DEPLOYED
        metadata.deployment_info = {
            'deployment_id': deployment_id,
            'deployment_name': deployment_name,
            'strategy': strategy.value
        }
        
        logger.info(f"Deployed model {model_id} as {deployment_name}")
        return deployment_id
        
    async def _deploy_blue_green(
        self,
        deployment_id: str,
        model_id: str,
        deployment_name: str
    ):
        """Blue-green deployment"""
        # Check if there's an existing deployment
        existing = next(
            (d for d in self.deployments.values() if d['name'] == deployment_name),
            None
        )
        
        if existing:
            # This is green deployment
            self.deployments[deployment_id] = {
                'model_id': model_id,
                'name': deployment_name,
                'strategy': 'blue_green',
                'status': 'green',
                'previous_model_id': existing['model_id'],
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Switch traffic
            await self._switch_traffic(deployment_name, model_id)
            
            # Mark old deployment as blue
            existing['status'] = 'blue'
        else:
            # First deployment
            self.deployments[deployment_id] = {
                'model_id': model_id,
                'name': deployment_name,
                'strategy': 'blue_green',
                'status': 'active',
                'created_at': datetime.utcnow().isoformat()
            }
            
    async def _deploy_canary(
        self,
        deployment_id: str,
        model_id: str,
        deployment_name: str,
        config: Dict
    ):
        """Canary deployment"""
        initial_traffic = config.get('initial_traffic', 10)
        increment = config.get('increment', 10)
        interval = config.get('interval_minutes', 30)
        
        self.deployments[deployment_id] = {
            'model_id': model_id,
            'name': deployment_name,
            'strategy': 'canary',
            'status': 'canary',
            'traffic_percentage': initial_traffic,
            'increment': increment,
            'interval': interval,
            'next_increase': datetime.utcnow() + timedelta(minutes=interval),
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Start canary rollout
        asyncio.create_task(self._canary_rollout(deployment_id))
        
    async def _canary_rollout(self, deployment_id: str):
        """Gradually increase canary traffic"""
        while deployment_id in self.deployments:
            deployment = self.deployments[deployment_id]
            
            if deployment['status'] != 'canary':
                break
                
            if datetime.utcnow() >= datetime.fromisoformat(deployment['next_increase']):
                # Increase traffic
                deployment['traffic_percentage'] = min(
                    100,
                    deployment['traffic_percentage'] + deployment['increment']
                )
                
                if deployment['traffic_percentage'] >= 100:
                    deployment['status'] = 'active'
                    logger.info(f"Canary deployment {deployment_id} completed")
                    break
                    
                deployment['next_increase'] = (
                    datetime.utcnow() + timedelta(minutes=deployment['interval'])
                ).isoformat()
                
                logger.info(f"Canary traffic increased to {deployment['traffic_percentage']}%")
                
            await asyncio.sleep(60)  # Check every minute
            
    async def _deploy_ab_test(
        self,
        deployment_id: str,
        model_id: str,
        deployment_name: str,
        config: Dict
    ):
        """A/B test deployment"""
        test_id = str(uuid.uuid4())
        
        # Get existing model
        existing_model_id = config.get('existing_model_id')
        if not existing_model_id:
            raise ValueError("Existing model ID required for A/B test")
            
        ab_test = ABTestConfig(
            id=test_id,
            name=deployment_name,
            model_a_id=existing_model_id,
            model_b_id=model_id,
            traffic_split=config.get('traffic_split', 50),
            metrics_to_track=config.get('metrics', ['accuracy', 'latency']),
            success_criteria=config.get('success_criteria', {}),
            start_time=datetime.utcnow()
        )
        
        self.ab_tests[test_id] = ab_test
        
        self.deployments[deployment_id] = {
            'model_id': model_id,
            'name': deployment_name,
            'strategy': 'ab_test',
            'status': 'testing',
            'ab_test_id': test_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
    async def _switch_traffic(self, deployment_name: str, model_id: str):
        """Switch traffic to new model"""
        # This would update load balancer or service mesh
        logger.info(f"Switching traffic for {deployment_name} to {model_id}")
        
    async def route_request(
        self,
        deployment_name: str,
        request_id: str
    ) -> str:
        """Route request to appropriate model based on deployment strategy"""
        # Find active deployment
        deployment = next(
            (d for d in self.deployments.values() if d['name'] == deployment_name),
            None
        )
        
        if not deployment:
            raise ValueError(f"Deployment {deployment_name} not found")
            
        if deployment['strategy'] == 'canary':
            # Route based on traffic percentage
            if np.random.random() * 100 < deployment['traffic_percentage']:
                return deployment['model_id']
            else:
                # Route to previous model
                return deployment.get('previous_model_id', deployment['model_id'])
                
        elif deployment['strategy'] == 'ab_test':
            # Route based on A/B test configuration
            ab_test = self.ab_tests.get(deployment['ab_test_id'])
            if ab_test:
                if np.random.random() * 100 < ab_test.traffic_split:
                    return ab_test.model_a_id
                else:
                    return ab_test.model_b_id
                    
        return deployment['model_id']
        
    async def record_prediction(
        self,
        deployment_name: str,
        model_id: str,
        request_id: str,
        prediction: Any,
        latency: float,
        actual: Optional[Any] = None
    ):
        """Record prediction for monitoring and A/B testing"""
        # Find deployment
        deployment = next(
            (d for d in self.deployments.values() if d['name'] == deployment_name),
            None
        )
        
        if deployment and deployment['strategy'] == 'ab_test':
            ab_test = self.ab_tests.get(deployment['ab_test_id'])
            
            if ab_test:
                # Update A/B test results
                model_key = 'model_a' if model_id == ab_test.model_a_id else 'model_b'
                
                if model_key not in ab_test.results:
                    ab_test.results[model_key] = {
                        'predictions': 0,
                        'total_latency': 0,
                        'correct': 0
                    }
                    
                ab_test.results[model_key]['predictions'] += 1
                ab_test.results[model_key]['total_latency'] += latency
                
                if actual is not None and prediction == actual:
                    ab_test.results[model_key]['correct'] += 1

class ModelOptimizer:
    """Handles model optimization and compression"""
    
    @staticmethod
    async def quantize_model(model: nn.Module, calibration_data: DataLoader) -> nn.Module:
        """Quantize model for inference optimization"""
        # Dynamic quantization
        quantized_model = torch.quantization.quantize_dynamic(
            model,
            {nn.Linear},
            dtype=torch.qint8
        )
        
        return quantized_model
        
    @staticmethod
    async def prune_model(model: nn.Module, sparsity: float = 0.5) -> nn.Module:
        """Prune model weights"""
        import torch.nn.utils.prune as prune
        
        for module in model.modules():
            if isinstance(module, nn.Linear):
                prune.l1_unstructured(module, name='weight', amount=sparsity)
                prune.remove(module, 'weight')
                
        return model
        
    @staticmethod
    async def convert_to_onnx(
        model: nn.Module,
        sample_input: torch.Tensor,
        output_path: str
    ):
        """Convert model to ONNX format"""
        model.eval()
        
        torch.onnx.export(
            model,
            sample_input,
            output_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
        )
        
        # Verify ONNX model
        onnx_model = onnx.load(output_path)
        onnx.checker.check_model(onnx_model)
        
        logger.info(f"Model converted to ONNX: {output_path}")
        
    @staticmethod
    async def optimize_for_edge(model: nn.Module) -> nn.Module:
        """Optimize model for edge deployment"""
        # Apply various optimizations
        model = await ModelOptimizer.quantize_model(model, None)
        model = await ModelOptimizer.prune_model(model, sparsity=0.3)
        
        # Fuse operations
        torch.quantization.fuse_modules(model, [['conv', 'bn', 'relu']], inplace=True)
        
        return model

class EnsembleModel:
    """Ensemble of multiple models"""
    
    def __init__(self, models: List[Tuple[Any, float]], voting: str = 'weighted'):
        """
        Initialize ensemble
        models: List of (model, weight) tuples
        voting: 'weighted' or 'majority'
        """
        self.models = models
        self.voting = voting
        
    async def predict(self, input_data: Any) -> Any:
        """Make ensemble prediction"""
        predictions = []
        weights = []
        
        for model, weight in self.models:
            pred = await self._get_prediction(model, input_data)
            predictions.append(pred)
            weights.append(weight)
            
        if self.voting == 'weighted':
            # Weighted average
            return np.average(predictions, weights=weights)
        else:
            # Majority voting
            from collections import Counter
            votes = Counter(predictions)
            return votes.most_common(1)[0][0]
            
    async def _get_prediction(self, model: Any, input_data: Any) -> Any:
        """Get prediction from single model"""
        if hasattr(model, 'predict'):
            return model.predict(input_data)
        elif hasattr(model, 'forward'):
            with torch.no_grad():
                return model(input_data)
        else:
            return model(input_data)

# MLOps integration
class MLOpsIntegration:
    """Integration with MLOps tools"""
    
    @staticmethod
    def setup_mlflow(experiment_name: str):
        """Setup MLflow tracking"""
        mlflow.set_experiment(experiment_name)
        mlflow.start_run()
        
    @staticmethod
    def log_metrics(metrics: Dict[str, float]):
        """Log metrics to MLflow"""
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
            
    @staticmethod
    def log_model(model: Any, artifact_path: str):
        """Log model to MLflow"""
        mlflow.pytorch.log_model(model, artifact_path)
        
    @staticmethod
    def setup_wandb(project: str, config: Dict):
        """Setup Weights & Biases tracking"""
        wandb.init(project=project, config=config)
        
    @staticmethod
    def log_to_wandb(metrics: Dict):
        """Log to Weights & Biases"""
        wandb.log(metrics)

# Usage example
async def demo_model_management():
    """Demonstrate model management system"""
    
    # Initialize components
    registry = ModelRegistry()
    trainer = ModelTrainer(registry)
    deployer = ModelDeployer(registry)
    
    # Create model metadata
    metadata = ModelMetadata(
        id=str(uuid.uuid4()),
        name="sentiment-classifier-v1",
        type=ModelType.BERT,
        version="1.0.0",
        status=ModelStatus.READY,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by="user123",
        description="Sentiment classification model",
        base_model="bert-base-uncased",
        metrics={'accuracy': 0.92, 'f1': 0.89}
    )
    
    # Register model (would normally have actual model)
    model_id = await registry.register_model(None, metadata)
    print(f"Registered model: {model_id}")
    
    # Deploy model
    deployment_id = await deployer.deploy_model(
        model_id,
        "sentiment-api",
        DeploymentStrategy.CANARY,
        {'initial_traffic': 10, 'increment': 20}
    )
    print(f"Deployed model: {deployment_id}")
    
    # Route request
    routed_model = await deployer.route_request("sentiment-api", "req_123")
    print(f"Routed to model: {routed_model}")

if __name__ == "__main__":
    asyncio.run(demo_model_management())