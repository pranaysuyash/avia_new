"""
Advanced Visualization Features
Extracted from text_classification_system.py

This module provides advanced visualization capabilities for text analysis and classification results.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
import base64
from io import BytesIO

# Visualization libraries with fallbacks
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.figure import Figure
    from matplotlib.colors import LinearSegmentedColormap
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Matplotlib/Seaborn not available - Basic visualizations disabled")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.figure_factory as ff
    PLOTLY_AVAILABLE = True
    print("✅ Plotly available - Interactive visualizations enabled")
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️ Plotly not available - Interactive visualizations disabled")

try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
    print("✅ WordCloud available - Word cloud visualizations enabled")
except ImportError:
    WORDCLOUD_AVAILABLE = False
    print("⚠️ WordCloud not available - Word cloud visualizations disabled")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualizationType(Enum):
    """Types of visualizations"""
    CONFUSION_MATRIX = "confusion_matrix"
    CLASSIFICATION_REPORT = "classification_report"
    CONFIDENCE_DISTRIBUTION = "confidence_distribution"
    WORD_CLOUD = "word_cloud"
    FEATURE_IMPORTANCE = "feature_importance"
    PREDICTION_TIMELINE = "prediction_timeline"
    LABEL_DISTRIBUTION = "label_distribution"
    CONFIDENCE_HEATMAP = "confidence_heatmap"
    DECISION_BOUNDARY = "decision_boundary"
    LEARNING_CURVE = "learning_curve"
    ROC_CURVE = "roc_curve"
    PRECISION_RECALL = "precision_recall"

class ChartTheme(Enum):
    """Chart themes"""
    DEFAULT = "default"
    DARK = "dark"
    MINIMAL = "minimal"
    COLORFUL = "colorful"
    PROFESSIONAL = "professional"

@dataclass
class VisualizationConfig:
    """Configuration for visualization generation"""
    theme: ChartTheme = ChartTheme.DEFAULT
    width: int = 800
    height: int = 600
    dpi: int = 100
    save_format: str = "png"
    interactive: bool = True
    show_grid: bool = True
    show_legend: bool = True
    color_palette: Optional[List[str]] = None
    font_size: int = 12
    title_size: int = 16

@dataclass
class VisualizationResult:
    """Result of a visualization generation"""
    viz_type: VisualizationType
    title: str
    description: str
    figure_data: Optional[str] = None  # Base64 encoded image or HTML
    interactive_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

class ConfusionMatrixVisualizer:
    """Generates confusion matrix visualizations"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
    
    def create_static_confusion_matrix(self, 
                                     y_true: List[str], 
                                     y_pred: List[str],
                                     labels: Optional[List[str]] = None) -> VisualizationResult:
        """Create static confusion matrix using matplotlib/seaborn"""
        if not MATPLOTLIB_AVAILABLE:
            return VisualizationResult(
                viz_type=VisualizationType.CONFUSION_MATRIX,
                title="Confusion Matrix",
                description="Matplotlib not available",
                metadata={"error": "matplotlib_not_available"}
            )
        
        from sklearn.metrics import confusion_matrix
        
        # Calculate confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        
        # Create figure
        plt.style.use('seaborn-v0_8' if hasattr(plt.style, 'seaborn-v0_8') else 'default')
        fig, ax = plt.subplots(figsize=(self.config.width/100, self.config.height/100), dpi=self.config.dpi)
        
        # Create heatmap
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=labels or np.unique(y_true),
                   yticklabels=labels or np.unique(y_true),
                   ax=ax)
        
        ax.set_title('Confusion Matrix', fontsize=self.config.title_size)
        ax.set_xlabel('Predicted Label', fontsize=self.config.font_size)
        ax.set_ylabel('True Label', fontsize=self.config.font_size)
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format=self.config.save_format, bbox_inches='tight', dpi=self.config.dpi)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return VisualizationResult(
            viz_type=VisualizationType.CONFUSION_MATRIX,
            title="Confusion Matrix",
            description="Static confusion matrix showing prediction accuracy",
            figure_data=image_base64,
            metadata={"format": self.config.save_format, "labels": labels or list(np.unique(y_true))}
        )
    
    def create_interactive_confusion_matrix(self, 
                                          y_true: List[str], 
                                          y_pred: List[str],
                                          labels: Optional[List[str]] = None) -> VisualizationResult:
        """Create interactive confusion matrix using plotly"""
        if not PLOTLY_AVAILABLE:
            return self.create_static_confusion_matrix(y_true, y_pred, labels)
        
        from sklearn.metrics import confusion_matrix
        
        # Calculate confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        unique_labels = labels or list(np.unique(y_true))
        
        # Create interactive heatmap
        fig = go.Figure(data=go.Heatmap(
            z=cm,
            x=unique_labels,
            y=unique_labels,
            colorscale='Blues',
            text=cm,
            texttemplate="%{text}",
            textfont={"size": self.config.font_size},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Interactive Confusion Matrix",
            xaxis_title="Predicted Label",
            yaxis_title="True Label",
            width=self.config.width,
            height=self.config.height,
            font=dict(size=self.config.font_size)
        )
        
        # Convert to HTML
        html_str = fig.to_html(include_plotlyjs=True)
        
        return VisualizationResult(
            viz_type=VisualizationType.CONFUSION_MATRIX,
            title="Interactive Confusion Matrix",
            description="Interactive confusion matrix with hover details",
            figure_data=html_str,
            interactive_data={"plotly_json": fig.to_json()},
            metadata={"format": "html", "labels": unique_labels}
        )

class WordCloudVisualizer:
    """Generates word cloud visualizations"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
    
    def create_word_cloud(self, 
                         texts: List[str], 
                         title: str = "Word Cloud",
                         max_words: int = 100) -> VisualizationResult:
        """Create word cloud visualization"""
        if not WORDCLOUD_AVAILABLE:
            return VisualizationResult(
                viz_type=VisualizationType.WORD_CLOUD,
                title=title,
                description="WordCloud library not available",
                metadata={"error": "wordcloud_not_available"}
            )
        
        # Combine all texts
        combined_text = " ".join(texts)
        
        # Generate word cloud
        wordcloud = WordCloud(
            width=self.config.width,
            height=self.config.height,
            max_words=max_words,
            background_color='white' if self.config.theme != ChartTheme.DARK else 'black',
            colormap='viridis' if self.config.color_palette is None else None,
            relative_scaling=0.5,
            random_state=42
        ).generate(combined_text)
        
        if MATPLOTLIB_AVAILABLE:
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(self.config.width/100, self.config.height/100), dpi=self.config.dpi)
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title(title, fontsize=self.config.title_size)
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format=self.config.save_format, bbox_inches='tight', dpi=self.config.dpi)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            
            return VisualizationResult(
                viz_type=VisualizationType.WORD_CLOUD,
                title=title,
                description=f"Word cloud generated from {len(texts)} texts",
                figure_data=image_base64,
                metadata={
                    "format": self.config.save_format,
                    "max_words": max_words,
                    "total_texts": len(texts)
                }
            )
        else:
            return VisualizationResult(
                viz_type=VisualizationType.WORD_CLOUD,
                title=title,
                description="Word cloud generated but matplotlib not available for display",
                metadata={"error": "matplotlib_not_available"}
            )

class DistributionVisualizer:
    """Generates distribution visualizations"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
    
    def create_confidence_distribution(self, 
                                     confidences: List[float],
                                     labels: Optional[List[str]] = None) -> VisualizationResult:
        """Create confidence score distribution"""
        if PLOTLY_AVAILABLE and self.config.interactive:
            return self._create_interactive_confidence_distribution(confidences, labels)
        elif MATPLOTLIB_AVAILABLE:
            return self._create_static_confidence_distribution(confidences, labels)
        else:
            return VisualizationResult(
                viz_type=VisualizationType.CONFIDENCE_DISTRIBUTION,
                title="Confidence Distribution",
                description="No visualization libraries available",
                metadata={"error": "no_viz_libraries"}
            )
    
    def _create_interactive_confidence_distribution(self, 
                                                  confidences: List[float],
                                                  labels: Optional[List[str]] = None) -> VisualizationResult:
        """Create interactive confidence distribution with plotly"""
        fig = go.Figure()
        
        # Add histogram
        fig.add_trace(go.Histogram(
            x=confidences,
            nbinsx=20,
            name="Confidence Distribution",
            marker_color='skyblue',
            opacity=0.7
        ))
        
        # Add mean line
        mean_confidence = np.mean(confidences)
        fig.add_vline(x=mean_confidence, line_dash="dash", line_color="red",
                     annotation_text=f"Mean: {mean_confidence:.2f}")
        
        fig.update_layout(
            title="Confidence Score Distribution",
            xaxis_title="Confidence Score",
            yaxis_title="Frequency",
            width=self.config.width,
            height=self.config.height,
            showlegend=self.config.show_legend
        )
        
        html_str = fig.to_html(include_plotlyjs=True)
        
        return VisualizationResult(
            viz_type=VisualizationType.CONFIDENCE_DISTRIBUTION,
            title="Interactive Confidence Distribution",
            description=f"Distribution of {len(confidences)} confidence scores",
            figure_data=html_str,
            interactive_data={"plotly_json": fig.to_json()},
            metadata={
                "mean": mean_confidence,
                "std": np.std(confidences),
                "min": np.min(confidences),
                "max": np.max(confidences)
            }
        )
    
    def _create_static_confidence_distribution(self, 
                                             confidences: List[float],
                                             labels: Optional[List[str]] = None) -> VisualizationResult:
        """Create static confidence distribution with matplotlib"""
        fig, ax = plt.subplots(figsize=(self.config.width/100, self.config.height/100), dpi=self.config.dpi)
        
        # Create histogram
        n, bins, patches = ax.hist(confidences, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        
        # Add mean line
        mean_confidence = np.mean(confidences)
        ax.axvline(mean_confidence, color='red', linestyle='--', linewidth=2, 
                  label=f'Mean: {mean_confidence:.2f}')
        
        ax.set_title('Confidence Score Distribution', fontsize=self.config.title_size)
        ax.set_xlabel('Confidence Score', fontsize=self.config.font_size)
        ax.set_ylabel('Frequency', fontsize=self.config.font_size)
        
        if self.config.show_legend:
            ax.legend()
        
        if self.config.show_grid:
            ax.grid(True, alpha=0.3)
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format=self.config.save_format, bbox_inches='tight', dpi=self.config.dpi)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return VisualizationResult(
            viz_type=VisualizationType.CONFIDENCE_DISTRIBUTION,
            title="Confidence Distribution",
            description=f"Distribution of {len(confidences)} confidence scores",
            figure_data=image_base64,
            metadata={
                "format": self.config.save_format,
                "mean": mean_confidence,
                "std": np.std(confidences),
                "sample_size": len(confidences)
            }
        )
    
    def create_label_distribution(self, labels: List[str]) -> VisualizationResult:
        """Create label distribution visualization"""
        # Count label frequencies
        from collections import Counter
        label_counts = Counter(labels)
        
        if PLOTLY_AVAILABLE and self.config.interactive:
            # Create interactive bar chart
            fig = go.Figure(data=[
                go.Bar(x=list(label_counts.keys()), y=list(label_counts.values()),
                      marker_color='lightblue')
            ])
            
            fig.update_layout(
                title="Label Distribution",
                xaxis_title="Labels",
                yaxis_title="Count",
                width=self.config.width,
                height=self.config.height
            )
            
            html_str = fig.to_html(include_plotlyjs=True)
            
            return VisualizationResult(
                viz_type=VisualizationType.LABEL_DISTRIBUTION,
                title="Interactive Label Distribution",
                description=f"Distribution of {len(set(labels))} unique labels",
                figure_data=html_str,
                interactive_data={"plotly_json": fig.to_json()},
                metadata={"label_counts": dict(label_counts)}
            )
        
        elif MATPLOTLIB_AVAILABLE:
            # Create static bar chart
            fig, ax = plt.subplots(figsize=(self.config.width/100, self.config.height/100), dpi=self.config.dpi)
            
            bars = ax.bar(label_counts.keys(), label_counts.values(), color='lightblue', alpha=0.7)
            
            ax.set_title('Label Distribution', fontsize=self.config.title_size)
            ax.set_xlabel('Labels', fontsize=self.config.font_size)
            ax.set_ylabel('Count', fontsize=self.config.font_size)
            
            # Rotate x-axis labels if many labels
            if len(label_counts) > 5:
                plt.xticks(rotation=45, ha='right')
            
            if self.config.show_grid:
                ax.grid(True, alpha=0.3)
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format=self.config.save_format, bbox_inches='tight', dpi=self.config.dpi)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            
            return VisualizationResult(
                viz_type=VisualizationType.LABEL_DISTRIBUTION,
                title="Label Distribution",
                description=f"Distribution of {len(set(labels))} unique labels",
                figure_data=image_base64,
                metadata={
                    "format": self.config.save_format,
                    "label_counts": dict(label_counts)
                }
            )
        
        else:
            return VisualizationResult(
                viz_type=VisualizationType.LABEL_DISTRIBUTION,
                title="Label Distribution",
                description="No visualization libraries available",
                metadata={"error": "no_viz_libraries", "label_counts": dict(label_counts)}
            )

class TimelineVisualizer:
    """Generates timeline visualizations"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
    
    def create_prediction_timeline(self, 
                                 timestamps: List[datetime],
                                 predictions: List[str],
                                 confidences: List[float]) -> VisualizationResult:
        """Create prediction timeline visualization"""
        if not PLOTLY_AVAILABLE:
            return VisualizationResult(
                viz_type=VisualizationType.PREDICTION_TIMELINE,
                title="Prediction Timeline",
                description="Plotly not available for timeline visualization",
                metadata={"error": "plotly_not_available"}
            )
        
        # Create timeline scatter plot
        fig = go.Figure()
        
        # Add scatter plot with predictions
        unique_predictions = list(set(predictions))
        colors = px.colors.qualitative.Set1[:len(unique_predictions)]
        
        for i, pred in enumerate(unique_predictions):
            pred_mask = [p == pred for p in predictions]
            pred_timestamps = [t for t, mask in zip(timestamps, pred_mask) if mask]
            pred_confidences = [c for c, mask in zip(confidences, pred_mask) if mask]
            
            fig.add_trace(go.Scatter(
                x=pred_timestamps,
                y=pred_confidences,
                mode='markers+lines',
                name=pred,
                marker=dict(
                    size=8,
                    color=colors[i % len(colors)],
                    opacity=0.7
                ),
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title="Prediction Timeline",
            xaxis_title="Time",
            yaxis_title="Confidence Score",
            width=self.config.width,
            height=self.config.height,
            showlegend=self.config.show_legend
        )
        
        html_str = fig.to_html(include_plotlyjs=True)
        
        return VisualizationResult(
            viz_type=VisualizationType.PREDICTION_TIMELINE,
            title="Prediction Timeline",
            description=f"Timeline of {len(predictions)} predictions over time",
            figure_data=html_str,
            interactive_data={"plotly_json": fig.to_json()},
            metadata={
                "unique_predictions": unique_predictions,
                "time_range": {
                    "start": min(timestamps).isoformat(),
                    "end": max(timestamps).isoformat()
                }
            }
        )

class VisualizationManager:
    """Main manager for all visualization functions"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self.confusion_matrix_viz = ConfusionMatrixVisualizer(self.config)
        self.wordcloud_viz = WordCloudVisualizer(self.config)
        self.distribution_viz = DistributionVisualizer(self.config)
        self.timeline_viz = TimelineVisualizer(self.config)
        
        logger.info("✅ Visualization manager initialized")
    
    def create_visualization(self, 
                           viz_type: VisualizationType,
                           data: Dict[str, Any]) -> VisualizationResult:
        """Create visualization based on type and data"""
        
        if viz_type == VisualizationType.CONFUSION_MATRIX:
            if self.config.interactive:
                return self.confusion_matrix_viz.create_interactive_confusion_matrix(
                    data["y_true"], data["y_pred"], data.get("labels")
                )
            else:
                return self.confusion_matrix_viz.create_static_confusion_matrix(
                    data["y_true"], data["y_pred"], data.get("labels")
                )
        
        elif viz_type == VisualizationType.WORD_CLOUD:
            return self.wordcloud_viz.create_word_cloud(
                data["texts"], data.get("title", "Word Cloud"), data.get("max_words", 100)
            )
        
        elif viz_type == VisualizationType.CONFIDENCE_DISTRIBUTION:
            return self.distribution_viz.create_confidence_distribution(
                data["confidences"], data.get("labels")
            )
        
        elif viz_type == VisualizationType.LABEL_DISTRIBUTION:
            return self.distribution_viz.create_label_distribution(data["labels"])
        
        elif viz_type == VisualizationType.PREDICTION_TIMELINE:
            return self.timeline_viz.create_prediction_timeline(
                data["timestamps"], data["predictions"], data["confidences"]
            )
        
        else:
            return VisualizationResult(
                viz_type=viz_type,
                title="Unsupported Visualization",
                description=f"Visualization type {viz_type.value} not implemented",
                metadata={"error": "unsupported_type"}
            )
    
    def create_classification_dashboard(self, 
                                     classification_results: Dict[str, Any]) -> List[VisualizationResult]:
        """Create a comprehensive dashboard of classification visualizations"""
        visualizations = []
        
        # Extract data from classification results
        y_true = classification_results.get("y_true", [])
        y_pred = classification_results.get("y_pred", [])
        confidences = classification_results.get("confidences", [])
        texts = classification_results.get("texts", [])
        timestamps = classification_results.get("timestamps", [])
        
        # Create confusion matrix
        if y_true and y_pred:
            confusion_viz = self.create_visualization(
                VisualizationType.CONFUSION_MATRIX,
                {"y_true": y_true, "y_pred": y_pred}
            )
            visualizations.append(confusion_viz)
        
        # Create confidence distribution
        if confidences:
            confidence_viz = self.create_visualization(
                VisualizationType.CONFIDENCE_DISTRIBUTION,
                {"confidences": confidences}
            )
            visualizations.append(confidence_viz)
        
        # Create label distribution
        if y_true:
            label_viz = self.create_visualization(
                VisualizationType.LABEL_DISTRIBUTION,
                {"labels": y_true}
            )
            visualizations.append(label_viz)
        
        # Create word cloud
        if texts:
            wordcloud_viz = self.create_visualization(
                VisualizationType.WORD_CLOUD,
                {"texts": texts, "title": "Classification Texts Word Cloud"}
            )
            visualizations.append(wordcloud_viz)
        
        # Create timeline
        if timestamps and y_pred and confidences:
            timeline_viz = self.create_visualization(
                VisualizationType.PREDICTION_TIMELINE,
                {"timestamps": timestamps, "predictions": y_pred, "confidences": confidences}
            )
            visualizations.append(timeline_viz)
        
        logger.info(f"Created classification dashboard with {len(visualizations)} visualizations")
        return visualizations
    
    def export_visualization(self, visualization: VisualizationResult, filepath: str):
        """Export visualization to file"""
        if visualization.figure_data:
            if visualization.metadata.get("format") == "html":
                # Save HTML file
                with open(filepath, 'w') as f:
                    f.write(visualization.figure_data)
            else:
                # Save image file
                image_data = base64.b64decode(visualization.figure_data)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
            
            logger.info(f"Visualization exported to {filepath}")
        else:
            logger.warning("No figure data to export")

def integrate_with_production_classifier(production_system, 
                                       classification_results: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate visualization features with production text classification system"""
    
    # Initialize visualization manager
    viz_manager = VisualizationManager(VisualizationConfig(
        interactive=True,
        theme=ChartTheme.PROFESSIONAL
    ))
    
    # Create visualizations
    try:
        visualizations = viz_manager.create_classification_dashboard(classification_results)
        
        viz_data = []
        for viz in visualizations:
            viz_data.append({
                "type": viz.viz_type.value,
                "title": viz.title,
                "description": viz.description,
                "has_figure": viz.figure_data is not None,
                "is_interactive": viz.interactive_data is not None,
                "metadata": viz.metadata
            })
        
        enhanced_result = {
            **classification_results,
            "visualizations": viz_data,
            "visualization_count": len(visualizations),
            "interactive_available": PLOTLY_AVAILABLE,
            "static_available": MATPLOTLIB_AVAILABLE,
            "wordcloud_available": WORDCLOUD_AVAILABLE
        }
        
    except Exception as e:
        logger.error(f"Visualization integration failed: {e}")
        enhanced_result = {
            **classification_results,
            "visualizations": [],
            "visualization_error": str(e)
        }
    
    return enhanced_result

def main():
    """Demo visualization features"""
    print("=== Advanced Visualization Features Demo ===\n")
    
    # Check available libraries
    print("Library Availability:")
    print(f"  Matplotlib: {'✅' if MATPLOTLIB_AVAILABLE else '❌'}")
    print(f"  Plotly: {'✅' if PLOTLY_AVAILABLE else '❌'}")
    print(f"  WordCloud: {'✅' if WORDCLOUD_AVAILABLE else '❌'}")
    print()
    
    # Create sample data
    np.random.seed(42)
    sample_size = 100
    
    # Generate sample classification results
    labels = ['positive', 'negative', 'neutral']
    y_true = np.random.choice(labels, sample_size)
    y_pred = y_true.copy()
    # Add some errors
    error_indices = np.random.choice(sample_size, size=20, replace=False)
    y_pred[error_indices] = np.random.choice(labels, size=20)
    
    confidences = np.random.beta(2, 1, sample_size)  # Skewed towards higher confidence
    
    texts = [
        "This product is amazing, I love it!",
        "Terrible quality, waste of money.",
        "It's okay, nothing special.",
        "Great customer service and fast delivery.",
        "Poor packaging, item arrived damaged.",
    ] * 20
    
    timestamps = [datetime.now() for _ in range(sample_size)]
    
    classification_results = {
        "y_true": y_true.tolist(),
        "y_pred": y_pred.tolist(),
        "confidences": confidences.tolist(),
        "texts": texts,
        "timestamps": timestamps
    }
    
    # Initialize visualization manager
    config = VisualizationConfig(
        interactive=True,
        theme=ChartTheme.PROFESSIONAL,
        width=800,
        height=600
    )
    
    viz_manager = VisualizationManager(config)
    
    # Create dashboard
    print("Creating classification dashboard...")
    visualizations = viz_manager.create_classification_dashboard(classification_results)
    
    print(f"✅ Created {len(visualizations)} visualizations:")
    for viz in visualizations:
        print(f"  - {viz.title}: {viz.description}")
        if viz.metadata.get("error"):
            print(f"    ⚠️ Error: {viz.metadata['error']}")
        else:
            print(f"    ✅ Generated successfully")
    
    print()
    print("=== Visualization Dashboard Summary ===")
    print(f"Total visualizations: {len(visualizations)}")
    print(f"Interactive visualizations: {sum(1 for v in visualizations if v.interactive_data)}")
    print(f"Static visualizations: {sum(1 for v in visualizations if v.figure_data and not v.interactive_data)}")

if __name__ == "__main__":
    main()