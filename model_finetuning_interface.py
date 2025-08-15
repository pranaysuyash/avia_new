"""
Model Fine-tuning Interface
User-friendly interface for custom model training with data management
"""

import asyncio
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, random_split
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import plotly.graph_objects as go
import plotly.express as px
import redis.asyncio as redis
import boto3
import tempfile
import zipfile
import yaml
import logging
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class DatasetType(str, Enum):
    """Dataset types"""
    TEXT_CLASSIFICATION = "text_classification"
    TOKEN_CLASSIFICATION = "token_classification"
    QUESTION_ANSWERING = "question_answering"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_GENERATION = "text_generation"
    TRANSLATION = "translation"

class DataFormat(str, Enum):
    """Data formats"""
    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"
    TSV = "tsv"
    PARQUET = "parquet"
    AUDIO = "audio"
    TEXT = "text"

class TrainingStatus(str, Enum):
    """Training status"""
    PENDING = "pending"
    PREPARING = "preparing"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DatasetInfo:
    """Dataset information"""
    id: str
    name: str
    type: DatasetType
    format: DataFormat
    size: int
    num_samples: int
    num_classes: Optional[int]
    label_distribution: Dict[str, int]
    created_at: datetime
    created_by: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_split: float = 0.2
    test_split: float = 0.1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'format': self.format.value,
            'size': self.size,
            'num_samples': self.num_samples,
            'num_classes': self.num_classes,
            'label_distribution': self.label_distribution,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'description': self.description,
            'metadata': self.metadata,
            'validation_split': self.validation_split,
            'test_split': self.test_split
        }

@dataclass
class TrainingConfig:
    """Training configuration"""
    model_type: str
    base_model: str
    dataset_id: str
    hyperparameters: Dict[str, Any]
    augmentation: Dict[str, Any]
    early_stopping: bool = True
    patience: int = 3
    max_epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 2e-5
    warmup_steps: int = 500
    gradient_accumulation_steps: int = 1
    fp16: bool = False
    evaluation_strategy: str = "epoch"
    save_strategy: str = "epoch"
    logging_steps: int = 100
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class TrainingRun:
    """Training run information"""
    id: str
    name: str
    config: TrainingConfig
    status: TrainingStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    current_epoch: int = 0
    total_epochs: int = 0
    current_step: int = 0
    total_steps: int = 0
    metrics: Dict[str, List[float]] = field(default_factory=dict)
    best_metrics: Dict[str, float] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)
    
    def add_metric(self, name: str, value: float):
        """Add metric value"""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)
        
        # Update best metric
        if name not in self.best_metrics or value > self.best_metrics[name]:
            self.best_metrics[name] = value

class DatasetManager:
    """Manages datasets for fine-tuning"""
    
    def __init__(self, storage_path: str = "./datasets", s3_bucket: Optional[str] = None):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if s3_bucket else None
        self.datasets: Dict[str, DatasetInfo] = {}
        
    async def upload_dataset(
        self,
        file_path: str,
        name: str,
        dataset_type: DatasetType,
        user_id: str,
        description: str = ""
    ) -> str:
        """Upload and process dataset"""
        dataset_id = str(uuid.uuid4())
        dataset_path = self.storage_path / dataset_id
        dataset_path.mkdir(parents=True, exist_ok=True)
        
        # Detect format
        file_ext = Path(file_path).suffix.lower()
        format_map = {
            '.csv': DataFormat.CSV,
            '.json': DataFormat.JSON,
            '.jsonl': DataFormat.JSONL,
            '.tsv': DataFormat.TSV,
            '.parquet': DataFormat.PARQUET,
            '.txt': DataFormat.TEXT,
            '.wav': DataFormat.AUDIO,
            '.mp3': DataFormat.AUDIO
        }
        data_format = format_map.get(file_ext, DataFormat.TEXT)
        
        # Load and analyze dataset
        if data_format in [DataFormat.CSV, DataFormat.TSV]:
            df = pd.read_csv(file_path, sep=',' if data_format == DataFormat.CSV else '\t')
            num_samples = len(df)
            
            # Analyze labels if present
            label_col = self._detect_label_column(df)
            if label_col:
                label_distribution = df[label_col].value_counts().to_dict()
                num_classes = len(label_distribution)
            else:
                label_distribution = {}
                num_classes = None
                
        elif data_format == DataFormat.JSON:
            with open(file_path, 'r') as f:
                data = json.load(f)
            num_samples = len(data) if isinstance(data, list) else 1
            label_distribution = {}
            num_classes = None
            
        elif data_format == DataFormat.JSONL:
            data = []
            with open(file_path, 'r') as f:
                for line in f:
                    data.append(json.loads(line))
            num_samples = len(data)
            label_distribution = {}
            num_classes = None
            
        else:
            num_samples = 1
            label_distribution = {}
            num_classes = None
            
        # Copy file to dataset directory
        import shutil
        dest_path = dataset_path / Path(file_path).name
        shutil.copy2(file_path, dest_path)
        
        # Get file size
        file_size = os.path.getsize(dest_path)
        
        # Create dataset info
        dataset_info = DatasetInfo(
            id=dataset_id,
            name=name,
            type=dataset_type,
            format=data_format,
            size=file_size,
            num_samples=num_samples,
            num_classes=num_classes,
            label_distribution=label_distribution,
            created_at=datetime.utcnow(),
            created_by=user_id,
            description=description
        )
        
        # Save metadata
        with open(dataset_path / "metadata.json", 'w') as f:
            json.dump(dataset_info.to_dict(), f, indent=2)
            
        # Upload to S3 if configured
        if self.s3_client and self.s3_bucket:
            await self._upload_to_s3(dataset_id, dataset_path)
            
        self.datasets[dataset_id] = dataset_info
        
        logger.info(f"Uploaded dataset: {dataset_id}")
        return dataset_id
        
    def _detect_label_column(self, df: pd.DataFrame) -> Optional[str]:
        """Detect label column in dataframe"""
        common_names = ['label', 'labels', 'target', 'class', 'category', 'sentiment']
        
        for col in df.columns:
            if col.lower() in common_names:
                return col
                
        return None
        
    async def _upload_to_s3(self, dataset_id: str, dataset_path: Path):
        """Upload dataset to S3"""
        for file_path in dataset_path.rglob('*'):
            if file_path.is_file():
                s3_key = f"datasets/{dataset_id}/{file_path.relative_to(dataset_path)}"
                self.s3_client.upload_file(str(file_path), self.s3_bucket, s3_key)
                
    async def load_dataset(self, dataset_id: str) -> Tuple[Any, DatasetInfo]:
        """Load dataset"""
        if dataset_id not in self.datasets:
            # Try to load from disk
            dataset_path = self.storage_path / dataset_id
            if dataset_path.exists():
                with open(dataset_path / "metadata.json", 'r') as f:
                    info_dict = json.load(f)
                    self.datasets[dataset_id] = DatasetInfo(**info_dict)
            else:
                raise ValueError(f"Dataset {dataset_id} not found")
                
        dataset_info = self.datasets[dataset_id]
        dataset_path = self.storage_path / dataset_id
        
        # Load data based on format
        data_files = list(dataset_path.glob(f"*.{dataset_info.format.value}"))
        if not data_files:
            data_files = list(dataset_path.glob("*"))
            
        if data_files:
            data_file = data_files[0]
            
            if dataset_info.format == DataFormat.CSV:
                data = pd.read_csv(data_file)
            elif dataset_info.format == DataFormat.JSON:
                with open(data_file, 'r') as f:
                    data = json.load(f)
            elif dataset_info.format == DataFormat.JSONL:
                data = []
                with open(data_file, 'r') as f:
                    for line in f:
                        data.append(json.loads(line))
            else:
                data = data_file
                
            return data, dataset_info
            
        raise ValueError(f"No data files found for dataset {dataset_id}")
        
    async def prepare_splits(
        self,
        dataset_id: str,
        validation_split: float = 0.2,
        test_split: float = 0.1,
        stratify: bool = True,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """Prepare train/validation/test splits"""
        data, dataset_info = await self.load_dataset(dataset_id)
        
        if isinstance(data, pd.DataFrame):
            # Detect features and labels
            label_col = self._detect_label_column(data)
            
            if label_col:
                X = data.drop(columns=[label_col])
                y = data[label_col]
                
                # First split: train+val vs test
                X_temp, X_test, y_temp, y_test = train_test_split(
                    X, y,
                    test_size=test_split,
                    stratify=y if stratify else None,
                    random_state=random_state
                )
                
                # Second split: train vs val
                val_size = validation_split / (1 - test_split)
                X_train, X_val, y_train, y_val = train_test_split(
                    X_temp, y_temp,
                    test_size=val_size,
                    stratify=y_temp if stratify else None,
                    random_state=random_state
                )
                
                return {
                    'train': {'X': X_train, 'y': y_train},
                    'validation': {'X': X_val, 'y': y_val},
                    'test': {'X': X_test, 'y': y_test}
                }
            else:
                # No labels, just split data
                train_size = int(len(data) * (1 - validation_split - test_split))
                val_size = int(len(data) * validation_split)
                
                train_data = data[:train_size]
                val_data = data[train_size:train_size + val_size]
                test_data = data[train_size + val_size:]
                
                return {
                    'train': train_data,
                    'validation': val_data,
                    'test': test_data
                }
        else:
            # Handle other data types
            return {'train': data, 'validation': None, 'test': None}

class DataAugmentation:
    """Data augmentation techniques"""
    
    @staticmethod
    def text_augmentation(text: str, techniques: List[str]) -> List[str]:
        """Apply text augmentation techniques"""
        augmented = [text]
        
        if 'synonym_replacement' in techniques:
            # Replace words with synonyms
            # This would use NLTK or similar
            pass
            
        if 'random_insertion' in techniques:
            # Randomly insert words
            pass
            
        if 'random_swap' in techniques:
            # Randomly swap words
            words = text.split()
            if len(words) > 1:
                import random
                idx1, idx2 = random.sample(range(len(words)), 2)
                words[idx1], words[idx2] = words[idx2], words[idx1]
                augmented.append(' '.join(words))
                
        if 'random_deletion' in techniques:
            # Randomly delete words
            words = text.split()
            if len(words) > 1:
                import random
                idx = random.randint(0, len(words) - 1)
                words.pop(idx)
                augmented.append(' '.join(words))
                
        return augmented
        
    @staticmethod
    def audio_augmentation(audio: np.ndarray, sample_rate: int, techniques: List[str]) -> List[np.ndarray]:
        """Apply audio augmentation techniques"""
        augmented = [audio]
        
        if 'noise_injection' in techniques:
            # Add random noise
            noise = np.random.normal(0, 0.005, audio.shape)
            augmented.append(audio + noise)
            
        if 'time_stretch' in techniques:
            # Change speed without changing pitch
            pass
            
        if 'pitch_shift' in techniques:
            # Change pitch without changing speed
            pass
            
        if 'volume_change' in techniques:
            # Random volume changes
            factor = np.random.uniform(0.8, 1.2)
            augmented.append(audio * factor)
            
        return augmented

class TrainingInterface:
    """Streamlit interface for model fine-tuning"""
    
    def __init__(self, dataset_manager: DatasetManager):
        self.dataset_manager = dataset_manager
        self.training_runs: Dict[str, TrainingRun] = {}
        
    def render(self):
        """Render Streamlit interface"""
        st.set_page_config(
            page_title="Model Fine-tuning Interface",
            page_icon="🤖",
            layout="wide"
        )
        
        st.title("🤖 Model Fine-tuning Interface")
        st.markdown("Train custom models with your data")
        
        # Sidebar
        with st.sidebar:
            st.header("Navigation")
            page = st.radio(
                "Select Page",
                ["Dataset Management", "Model Training", "Training History", "Model Evaluation"]
            )
            
        if page == "Dataset Management":
            self.render_dataset_management()
        elif page == "Model Training":
            self.render_model_training()
        elif page == "Training History":
            self.render_training_history()
        else:
            self.render_model_evaluation()
            
    def render_dataset_management(self):
        """Render dataset management page"""
        st.header("📊 Dataset Management")
        
        tabs = st.tabs(["Upload Dataset", "View Datasets", "Data Analysis"])
        
        with tabs[0]:
            st.subheader("Upload New Dataset")
            
            col1, col2 = st.columns(2)
            
            with col1:
                uploaded_file = st.file_uploader(
                    "Choose a file",
                    type=['csv', 'json', 'jsonl', 'tsv', 'txt', 'parquet']
                )
                
                dataset_name = st.text_input("Dataset Name")
                dataset_type = st.selectbox(
                    "Dataset Type",
                    [t.value for t in DatasetType]
                )
                
            with col2:
                description = st.text_area("Description")
                validation_split = st.slider("Validation Split", 0.0, 0.5, 0.2)
                test_split = st.slider("Test Split", 0.0, 0.3, 0.1)
                
            if st.button("Upload Dataset", type="primary"):
                if uploaded_file and dataset_name:
                    with st.spinner("Uploading and processing dataset..."):
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                            tmp_file.write(uploaded_file.getbuffer())
                            tmp_path = tmp_file.name
                            
                        # Upload dataset
                        dataset_id = asyncio.run(
                            self.dataset_manager.upload_dataset(
                                tmp_path,
                                dataset_name,
                                DatasetType(dataset_type),
                                "current_user",
                                description
                            )
                        )
                        
                        st.success(f"Dataset uploaded successfully! ID: {dataset_id}")
                        
                        # Clean up
                        os.unlink(tmp_path)
                        
        with tabs[1]:
            st.subheader("Existing Datasets")
            
            if self.dataset_manager.datasets:
                datasets_df = pd.DataFrame([
                    {
                        'Name': d.name,
                        'Type': d.type.value,
                        'Format': d.format.value,
                        'Samples': d.num_samples,
                        'Classes': d.num_classes or 'N/A',
                        'Size': f"{d.size / 1024 / 1024:.2f} MB",
                        'Created': d.created_at.strftime('%Y-%m-%d')
                    }
                    for d in self.dataset_manager.datasets.values()
                ])
                
                st.dataframe(datasets_df, use_container_width=True)
                
                # Dataset details
                selected_dataset = st.selectbox(
                    "Select dataset for details",
                    list(self.dataset_manager.datasets.keys()),
                    format_func=lambda x: self.dataset_manager.datasets[x].name
                )
                
                if selected_dataset:
                    dataset = self.dataset_manager.datasets[selected_dataset]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Samples", dataset.num_samples)
                    with col2:
                        st.metric("Classes", dataset.num_classes or "N/A")
                    with col3:
                        st.metric("Size", f"{dataset.size / 1024 / 1024:.2f} MB")
                        
                    if dataset.label_distribution:
                        st.subheader("Label Distribution")
                        fig = px.bar(
                            x=list(dataset.label_distribution.keys()),
                            y=list(dataset.label_distribution.values()),
                            labels={'x': 'Label', 'y': 'Count'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No datasets uploaded yet")
                
        with tabs[2]:
            st.subheader("Data Analysis")
            
            if self.dataset_manager.datasets:
                dataset_id = st.selectbox(
                    "Select dataset to analyze",
                    list(self.dataset_manager.datasets.keys()),
                    format_func=lambda x: self.dataset_manager.datasets[x].name,
                    key="analysis_dataset"
                )
                
                if st.button("Analyze Dataset"):
                    with st.spinner("Analyzing dataset..."):
                        data, info = asyncio.run(
                            self.dataset_manager.load_dataset(dataset_id)
                        )
                        
                        if isinstance(data, pd.DataFrame):
                            st.subheader("Dataset Preview")
                            st.dataframe(data.head(100), use_container_width=True)
                            
                            st.subheader("Statistical Summary")
                            st.dataframe(data.describe(), use_container_width=True)
                            
                            st.subheader("Missing Values")
                            missing = data.isnull().sum()
                            if missing.any():
                                st.bar_chart(missing[missing > 0])
                            else:
                                st.success("No missing values found")
                                
    def render_model_training(self):
        """Render model training page"""
        st.header("🎯 Model Training")
        
        if not self.dataset_manager.datasets:
            st.warning("Please upload a dataset first")
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Training Configuration")
            
            training_name = st.text_input("Training Run Name")
            
            dataset_id = st.selectbox(
                "Select Dataset",
                list(self.dataset_manager.datasets.keys()),
                format_func=lambda x: self.dataset_manager.datasets[x].name
            )
            
            model_type = st.selectbox(
                "Model Type",
                ["BERT", "GPT-2", "T5", "Whisper", "Custom"]
            )
            
            if model_type in ["BERT", "GPT-2", "T5"]:
                base_model = st.selectbox(
                    "Base Model",
                    {
                        "BERT": ["bert-base-uncased", "bert-large-uncased", "distilbert-base-uncased"],
                        "GPT-2": ["gpt2", "gpt2-medium", "gpt2-large"],
                        "T5": ["t5-small", "t5-base", "t5-large"]
                    }.get(model_type, [])
                )
            else:
                base_model = st.text_input("Base Model Path/Name")
                
        with col2:
            st.subheader("Hyperparameters")
            
            epochs = st.number_input("Epochs", 1, 100, 10)
            batch_size = st.select_slider("Batch Size", [8, 16, 32, 64, 128], value=32)
            learning_rate = st.number_input(
                "Learning Rate",
                min_value=1e-6,
                max_value=1e-2,
                value=2e-5,
                format="%.2e"
            )
            
            warmup_steps = st.number_input("Warmup Steps", 0, 1000, 500)
            
            early_stopping = st.checkbox("Enable Early Stopping", value=True)
            if early_stopping:
                patience = st.number_input("Patience", 1, 10, 3)
            else:
                patience = 3
                
            fp16 = st.checkbox("Use Mixed Precision (FP16)", value=False)
            
        st.subheader("Data Augmentation")
        
        augmentation_enabled = st.checkbox("Enable Data Augmentation")
        
        if augmentation_enabled:
            dataset_type = self.dataset_manager.datasets[dataset_id].type
            
            if dataset_type == DatasetType.TEXT_CLASSIFICATION:
                augmentation_techniques = st.multiselect(
                    "Augmentation Techniques",
                    ["synonym_replacement", "random_insertion", "random_swap", "random_deletion"]
                )
            elif dataset_type == DatasetType.SPEECH_TO_TEXT:
                augmentation_techniques = st.multiselect(
                    "Augmentation Techniques",
                    ["noise_injection", "time_stretch", "pitch_shift", "volume_change"]
                )
            else:
                augmentation_techniques = []
        else:
            augmentation_techniques = []
            
        if st.button("Start Training", type="primary"):
            if training_name:
                # Create training configuration
                config = TrainingConfig(
                    model_type=model_type,
                    base_model=base_model,
                    dataset_id=dataset_id,
                    hyperparameters={
                        'epochs': epochs,
                        'batch_size': batch_size,
                        'learning_rate': learning_rate,
                        'warmup_steps': warmup_steps,
                        'early_stopping': early_stopping,
                        'patience': patience,
                        'fp16': fp16
                    },
                    augmentation={
                        'enabled': augmentation_enabled,
                        'techniques': augmentation_techniques
                    },
                    max_epochs=epochs,
                    batch_size=batch_size,
                    learning_rate=learning_rate,
                    warmup_steps=warmup_steps,
                    early_stopping=early_stopping,
                    patience=patience,
                    fp16=fp16
                )
                
                # Create training run
                run_id = str(uuid.uuid4())
                training_run = TrainingRun(
                    id=run_id,
                    name=training_name,
                    config=config,
                    status=TrainingStatus.PENDING,
                    started_at=None,
                    completed_at=None
                )
                
                self.training_runs[run_id] = training_run
                
                st.success(f"Training run created: {run_id}")
                st.info("Training will start in the background. Check the Training History page for progress.")
                
                # Start training (would be async in production)
                # asyncio.create_task(self.start_training(run_id))
                
    def render_training_history(self):
        """Render training history page"""
        st.header("📈 Training History")
        
        if not self.training_runs:
            st.info("No training runs yet")
            return
            
        # Training runs table
        runs_data = []
        for run in self.training_runs.values():
            runs_data.append({
                'Name': run.name,
                'Status': run.status.value,
                'Model': run.config.model_type,
                'Dataset': self.dataset_manager.datasets.get(run.config.dataset_id, {}).name if run.config.dataset_id in self.dataset_manager.datasets else 'Unknown',
                'Epochs': f"{run.current_epoch}/{run.total_epochs}",
                'Started': run.started_at.strftime('%Y-%m-%d %H:%M') if run.started_at else 'Not started',
                'ID': run.id
            })
            
        runs_df = pd.DataFrame(runs_data)
        
        selected_run_idx = st.dataframe(
            runs_df,
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun"
        )
        
        if selected_run_idx and selected_run_idx.selection.rows:
            selected_run_id = runs_df.iloc[selected_run_idx.selection.rows[0]]['ID']
            selected_run = self.training_runs[selected_run_id]
            
            st.subheader(f"Training Run: {selected_run.name}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Status", selected_run.status.value)
            with col2:
                st.metric("Current Epoch", f"{selected_run.current_epoch}/{selected_run.total_epochs}")
            with col3:
                st.metric("Current Step", selected_run.current_step)
            with col4:
                if selected_run.best_metrics:
                    best_metric = max(selected_run.best_metrics.values())
                    st.metric("Best Metric", f"{best_metric:.4f}")
                    
            # Training metrics chart
            if selected_run.metrics:
                st.subheader("Training Metrics")
                
                metrics_to_plot = st.multiselect(
                    "Select metrics to plot",
                    list(selected_run.metrics.keys()),
                    default=list(selected_run.metrics.keys())[:3]
                )
                
                if metrics_to_plot:
                    fig = go.Figure()
                    
                    for metric_name in metrics_to_plot:
                        if metric_name in selected_run.metrics:
                            fig.add_trace(go.Scatter(
                                x=list(range(len(selected_run.metrics[metric_name]))),
                                y=selected_run.metrics[metric_name],
                                mode='lines+markers',
                                name=metric_name
                            ))
                            
                    fig.update_layout(
                        xaxis_title="Step",
                        yaxis_title="Value",
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
            # Training logs
            if selected_run.logs:
                with st.expander("Training Logs"):
                    for log in selected_run.logs[-20:]:  # Show last 20 logs
                        st.text(log)
                        
            # Control buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if selected_run.status == TrainingStatus.TRAINING:
                    if st.button("Pause Training", type="secondary"):
                        st.info("Training paused")
                elif selected_run.status in [TrainingStatus.PENDING, TrainingStatus.PREPARING]:
                    if st.button("Cancel Training", type="secondary"):
                        selected_run.status = TrainingStatus.CANCELLED
                        st.info("Training cancelled")
                        
            with col2:
                if selected_run.status == TrainingStatus.COMPLETED:
                    if st.button("Download Model", type="primary"):
                        st.info("Model download started")
                        
            with col3:
                if selected_run.status == TrainingStatus.COMPLETED:
                    if st.button("Deploy Model", type="primary"):
                        st.info("Opening deployment interface...")
                        
    def render_model_evaluation(self):
        """Render model evaluation page"""
        st.header("🔍 Model Evaluation")
        
        completed_runs = [
            run for run in self.training_runs.values()
            if run.status == TrainingStatus.COMPLETED
        ]
        
        if not completed_runs:
            st.info("No completed training runs to evaluate")
            return
            
        selected_run = st.selectbox(
            "Select Model to Evaluate",
            completed_runs,
            format_func=lambda x: x.name
        )
        
        if selected_run:
            st.subheader(f"Evaluating: {selected_run.name}")
            
            # Evaluation metrics
            if selected_run.best_metrics:
                cols = st.columns(len(selected_run.best_metrics))
                for i, (metric_name, value) in enumerate(selected_run.best_metrics.items()):
                    with cols[i]:
                        st.metric(metric_name.capitalize(), f"{value:.4f}")
                        
            # Test on custom input
            st.subheader("Test Model")
            
            dataset_type = self.dataset_manager.datasets.get(
                selected_run.config.dataset_id, {}
            ).type if selected_run.config.dataset_id in self.dataset_manager.datasets else None
            
            if dataset_type == DatasetType.TEXT_CLASSIFICATION:
                test_input = st.text_area("Enter text to classify")
                
                if st.button("Predict"):
                    with st.spinner("Making prediction..."):
                        # This would actually run the model
                        st.success("Prediction: Positive (confidence: 0.92)")
                        
            elif dataset_type == DatasetType.SPEECH_TO_TEXT:
                uploaded_audio = st.file_uploader("Upload audio file", type=['wav', 'mp3'])
                
                if uploaded_audio and st.button("Transcribe"):
                    with st.spinner("Transcribing..."):
                        st.success("Transcription: This is a sample transcription")
                        
            # Confusion matrix / other visualizations
            st.subheader("Model Performance Visualizations")
            
            # Mock confusion matrix
            cm_data = np.random.randint(0, 100, (3, 3))
            fig = px.imshow(
                cm_data,
                labels=dict(x="Predicted", y="Actual", color="Count"),
                x=['Class A', 'Class B', 'Class C'],
                y=['Class A', 'Class B', 'Class C'],
                color_continuous_scale='Blues'
            )
            fig.update_xaxis(side="top")
            st.plotly_chart(fig, use_container_width=True)

# Usage
def main():
    """Main function to run the interface"""
    dataset_manager = DatasetManager()
    interface = TrainingInterface(dataset_manager)
    interface.render()

if __name__ == "__main__":
    main()