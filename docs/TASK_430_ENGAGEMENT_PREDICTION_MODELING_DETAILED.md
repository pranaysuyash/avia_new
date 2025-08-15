# Task 430: Build Engagement Prediction Modeling - Detailed Implementation Plan

## Overview
Forecast audience engagement before content publication with engagement scoring algorithms and predictive models for different content types.

## User Value
- Helps users predict how engaging their content will be before publishing
- Provides engagement optimization recommendations
- Enables data-driven content creation decisions
- Reduces trial-and-error in content creation

## Technical Requirements

### Backend Implementation
1. **Engagement Scoring Algorithms**
   - Text complexity analysis
   - Sentiment analysis scoring
   - Keyword relevance and density analysis
   - Structure and formatting evaluation
   - Call-to-action detection and scoring

2. **Predictive Models**
   - Historical engagement data analysis
   - Machine learning model for engagement prediction
   - Content type-specific models (articles, videos, podcasts, social posts)
   - Real-time prediction API endpoints

3. **Data Integration**
   - Connect with existing analytics system
   - Import historical engagement data
   - Real-time engagement tracking
   - Cross-platform engagement aggregation

### Frontend Implementation
1. **Engagement Prediction Dashboard**
   - Interactive prediction interface
   - Content scoring visualization
   - Recommendation display
   - Historical comparison charts

2. **Real-time Feedback**
   - Live engagement scoring during content creation
   - Instant optimization suggestions
   - Content improvement indicators
   - Engagement trend visualization

## Implementation Phases

### Phase 1: Core Algorithm Development (Days 1-2)
**Objective**: Build foundational engagement scoring algorithms

#### Day 1: Text Analysis Engine
```python
# engagement_scoring.py
import nltk
from textblob import TextBlob
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression
import numpy as np

class EngagementScoringEngine:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.vectorizer = TfidfVectorizer(max_features=1000)
        
    def calculate_text_complexity(self, text):
        """Calculate readability and complexity scores"""
        blob = TextBlob(text)
        
        # Sentence complexity
        avg_sentence_length = np.mean([len(sentence.words) for sentence in blob.sentences])
        
        # Word complexity
        avg_word_length = np.mean([len(word) for word in blob.words])
        
        # Vocabulary complexity
        unique_words = len(set(blob.words))
        total_words = len(blob.words)
        vocabulary_richness = unique_words / total_words if total_words > 0 else 0
        
        # Complexity score (0-1, lower is simpler)
        complexity_score = (
            min(avg_sentence_length / 50, 1) * 0.4 +
            min(avg_word_length / 10, 1) * 0.3 +
            (1 - vocabulary_richness) * 0.3
        )
        
        return {
            'sentence_complexity': avg_sentence_length,
            'word_complexity': avg_word_length,
            'vocabulary_richness': vocabulary_richness,
            'complexity_score': complexity_score
        }
    
    def analyze_sentiment_engagement(self, text):
        """Analyze sentiment for engagement potential"""
        blob = TextBlob(text)
        sentiment = blob.sentiment
        
        # Engagement-friendly sentiment (moderate polarity tends to engage more)
        # Too neutral or too extreme can reduce engagement
        polarity_score = abs(sentiment.polarity)  # Moderate polarity engages more
        engagement_sentiment = 1 - abs(polarity_score - 0.5) * 2  # Peak at 0.5 polarity
        
        return {
            'polarity': sentiment.polarity,
            'subjectivity': sentiment.subjectivity,
            'engagement_sentiment_score': max(0, engagement_sentiment)
        }
    
    def analyze_keyword_relevance(self, text, keywords=None):
        """Analyze keyword relevance and density"""
        if not keywords:
            # Extract important keywords using TF-IDF
            blob = TextBlob(text)
            keywords = [word for word in blob.words if len(word) > 4][:10]
        
        # Calculate keyword density
        text_lower = text.lower()
        keyword_density_scores = []
        
        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            density = count / len(text_lower.split()) if text_lower.split() else 0
            # Optimal density is around 2-3%
            optimal_density = 1 - abs(density - 0.025) * 40  # Peak at 2.5%
            keyword_density_scores.append(max(0, min(1, optimal_density)))
        
        avg_keyword_score = np.mean(keyword_density_scores) if keyword_density_scores else 0
        
        return {
            'keywords': keywords,
            'keyword_density_scores': keyword_density_scores,
            'avg_keyword_relevance': avg_keyword_score
        }
    
    def evaluate_structure_formatting(self, text):
        """Evaluate content structure and formatting"""
        lines = text.split('\n')
        
        # Paragraph length analysis
        paragraph_lengths = [len(line.split()) for line in lines if line.strip()]
        avg_paragraph_length = np.mean(paragraph_lengths) if paragraph_lengths else 0
        
        # Structure variety (mix of short/long paragraphs engages more)
        length_variance = np.var(paragraph_lengths) if len(paragraph_lengths) > 1 else 0
        structure_score = min(length_variance / 100, 1)  # Normalize variance
        
        # Formatting elements
        has_headings = '#' in text
        has_lists = ('-' in text or '*' in text) and ('\n' in text)
        has_bold = '**' in text or '__' in text
        has_italics = '*' in text or '_' in text
        
        formatting_score = (
            (0.25 if has_headings else 0) +
            (0.25 if has_lists else 0) +
            (0.25 if has_bold else 0) +
            (0.25 if has_italics else 0)
        )
        
        return {
            'avg_paragraph_length': avg_paragraph_length,
            'structure_variety': length_variance,
            'has_headings': has_headings,
            'has_lists': has_lists,
            'has_bold': has_bold,
            'has_italics': has_italics,
            'structure_score': structure_score,
            'formatting_score': formatting_score
        }
    
    def detect_call_to_actions(self, text):
        """Detect and score call-to-action elements"""
        cta_patterns = [
            r'\b(click|subscribe|follow|share|download|register|sign up|learn more|get started|try now|buy now)\b',
            r'\b(don\'t miss|limited time|act now|exclusive|special offer)\b',
            r'\b(hurry|soon|today|now)\b'
        ]
        
        import re
        cta_matches = []
        for pattern in cta_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            cta_matches.extend(matches)
        
        # Score based on CTA count and variety
        cta_count = len(cta_matches)
        cta_variety = len(set(cta_matches))
        
        # Optimal range is 2-5 CTAs
        cta_score = 1 - abs(min(cta_count, 5) / 5 - 0.6) * 1.67  # Peak at 3 CTAs
        
        return {
            'cta_count': cta_count,
            'cta_variety': cta_variety,
            'cta_score': max(0, cta_score)
        }
    
    def generate_engagement_score(self, text, content_type='article'):
        """Generate overall engagement score"""
        # Get individual scores
        complexity = self.calculate_text_complexity(text)
        sentiment = self.analyze_sentiment_engagement(text)
        keywords = self.analyze_keyword_relevance(text)
        structure = self.evaluate_structure_formatting(text)
        ctas = self.detect_call_to_actions(text)
        
        # Weighted combination based on content type
        if content_type == 'social':
            # Social content benefits more from CTAs and sentiment
            weights = {
                'complexity': 0.15,
                'sentiment': 0.25,
                'keywords': 0.20,
                'structure': 0.15,
                'ctas': 0.25
            }
        elif content_type == 'video':
            # Video content benefits more from structure and sentiment
            weights = {
                'complexity': 0.20,
                'sentiment': 0.25,
                'keywords': 0.15,
                'structure': 0.20,
                'ctas': 0.20
            }
        else:  # Article/default
            # Articles benefit from balanced approach
            weights = {
                'complexity': 0.20,
                'sentiment': 0.20,
                'keywords': 0.20,
                'structure': 0.20,
                'ctas': 0.20
            }
        
        # Calculate weighted engagement score
        engagement_score = (
            (1 - complexity['complexity_score']) * weights['complexity'] +
            sentiment['engagement_sentiment_score'] * weights['sentiment'] +
            keywords['avg_keyword_relevance'] * weights['keywords'] +
            structure['structure_score'] * weights['structure'] +
            ctas['cta_score'] * weights['ctas']
        )
        
        return {
            'overall_score': engagement_score,
            'breakdown': {
                'complexity': {
                    'score': 1 - complexity['complexity_score'],
                    'details': complexity
                },
                'sentiment': {
                    'score': sentiment['engagement_sentiment_score'],
                    'details': sentiment
                },
                'keywords': {
                    'score': keywords['avg_keyword_relevance'],
                    'details': keywords
                },
                'structure': {
                    'score': structure['structure_score'],
                    'details': structure
                },
                'ctas': {
                    'score': ctas['cta_score'],
                    'details': ctas
                }
            },
            'content_type': content_type,
            'recommendations': self._generate_recommendations(
                complexity, sentiment, keywords, structure, ctas, content_type
            )
        }
    
    def _generate_recommendations(self, complexity, sentiment, keywords, structure, ctas, content_type):
        """Generate optimization recommendations"""
        recommendations = []
        
        # Complexity recommendations
        if complexity['complexity_score'] > 0.7:
            recommendations.append("Simplify language - use shorter sentences and simpler words")
        elif complexity['complexity_score'] < 0.3:
            recommendations.append("Add some complexity - vary sentence lengths and vocabulary")
        
        # Sentiment recommendations
        if sentiment['engagement_sentiment_score'] < 0.5:
            recommendations.append("Adjust sentiment - aim for moderate positivity/negativity")
        
        # Structure recommendations
        if structure['structure_score'] < 0.3:
            recommendations.append("Improve structure - add headings, lists, and formatting variety")
        elif structure['structure_score'] > 0.8:
            recommendations.append("Vary paragraph lengths for better engagement")
        
        # CTA recommendations
        if ctas['cta_score'] < 0.5:
            recommendations.append("Add clear call-to-actions to drive engagement")
        elif ctas['cta_score'] > 0.8 and ctas['cta_count'] > 5:
            recommendations.append("Reduce call-to-action frequency to avoid overwhelming readers")
        
        # Content type specific recommendations
        if content_type == 'social':
            if ctas['cta_score'] < 0.6:
                recommendations.append("Social posts need stronger CTAs for engagement")
        elif content_type == 'video':
            if structure['structure_score'] < 0.4:
                recommendations.append("Video descriptions benefit from clear structure and formatting")
        
        return recommendations

# Example usage
if __name__ == "__main__":
    engine = EngagementScoringEngine()
    
    sample_text = """
    # How to Master Content Marketing in 2025
    
    Content marketing continues to evolve, and staying ahead requires mastering new strategies. 
    In this comprehensive guide, we'll explore the cutting-edge techniques that will drive 
    exceptional results for your business.
    
    ## Why Content Marketing Matters
    
    Modern consumers are increasingly skeptical of traditional advertising. They crave authentic, 
    valuable content that educates and entertains. This shift presents enormous opportunities 
    for brands willing to invest in quality content creation.
    
    ### Key Benefits Include:
    - Increased brand awareness and trust
    - Higher conversion rates and sales
    - Improved SEO and organic traffic
    - Stronger customer relationships
    
    ## Emerging Trends for 2025
    
    The landscape is changing rapidly. Here are the trends reshaping content marketing:
    
    1. **AI-Powered Personalization**: Leveraging artificial intelligence to deliver hyper-targeted content
    2. **Interactive Content**: Quizzes, polls, and calculators that boost engagement
    3. **Video-First Approach**: Prioritizing video content across all channels
    4. **Community Building**: Creating engaged communities around your brand
    
    Don't miss out on these opportunities! Subscribe to our newsletter for weekly marketing insights 
    and get early access to our premium content marketing toolkit. Ready to transform your strategy? 
    [Get Started Today](https://example.com/start) and see results within 30 days.
    """
    
    result = engine.generate_engagement_score(sample_text, 'article')
    print(f"Engagement Score: {result['overall_score']:.2f}")
    print("\nBreakdown:")
    for category, data in result['breakdown'].items():
        print(f"  {category.title()}: {data['score']:.2f}")
    
    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  • {rec}")
```

#### Day 2: Predictive Modeling Engine
```python
# predictive_engagement_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PredictiveEngagementModel:
    def __init__(self):
        self.model = None
        self.engagement_scoring_engine = EngagementScoringEngine()
        self.is_trained = False
        
    def prepare_training_data(self, historical_data):
        """Prepare training data from historical engagement records"""
        # Convert to DataFrame if it's a list
        if isinstance(historical_data, list):
            df = pd.DataFrame(historical_data)
        else:
            df = historical_data.copy()
        
        # Extract features using engagement scoring engine
        features_list = []
        for _, row in df.iterrows():
            text = row.get('content', '') or row.get('transcript', '') or ''
            content_type = row.get('content_type', 'article')
            
            # Get engagement features
            engagement_features = self.engagement_scoring_engine.generate_engagement_score(
                text, content_type
            )
            
            # Flatten features
            features = {
                'complexity_score': engagement_features['breakdown']['complexity']['score'],
                'sentiment_score': engagement_features['breakdown']['sentiment']['score'],
                'keywords_score': engagement_features['breakdown']['keywords']['score'],
                'structure_score': engagement_features['breakdown']['structure']['score'],
                'ctas_score': engagement_features['breakdown']['ctas']['score'],
                'content_length': len(text),
                'content_type': content_type,
                'hour_of_day': row.get('hour_of_day', 12),
                'day_of_week': row.get('day_of_week', 1),
                'season': row.get('season', 'spring')
            }
            
            # Add target variable (actual engagement)
            features['actual_engagement'] = row.get('engagement_score', 0)
            
            features_list.append(features)
        
        return pd.DataFrame(features_list)
    
    def train_model(self, training_data, test_size=0.2):
        """Train the predictive engagement model"""
        try:
            # Prepare features
            df = self.prepare_training_data(training_data)
            
            # Encode categorical variables
            df_encoded = pd.get_dummies(df, columns=['content_type', 'season'])
            
            # Separate features and target
            X = df_encoded.drop('actual_engagement', axis=1)
            y = df_encoded['actual_engagement']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Train model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            self.is_trained = True
            
            logger.info(f"Model trained successfully - MSE: {mse:.4f}, R²: {r2:.4f}")
            
            return {
                'mse': mse,
                'r2_score': r2,
                'feature_importance': dict(zip(X.columns, self.model.feature_importances_))
            }
            
        except Exception as e:
            logger.error(f"Error training predictive model: {e}")
            raise
    
    def predict_engagement(self, content, content_type='article', context=None):
        """Predict engagement for new content"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        try:
            # Get engagement features
            engagement_features = self.engagement_scoring_engine.generate_engagement_score(
                content, content_type
            )
            
            # Prepare features for prediction
            features = {
                'complexity_score': engagement_features['breakdown']['complexity']['score'],
                'sentiment_score': engagement_features['breakdown']['sentiment']['score'],
                'keywords_score': engagement_features['breakdown']['keywords']['score'],
                'structure_score': engagement_features['breakdown']['structure']['score'],
                'ctas_score': engagement_features['breakdown']['ctas']['score'],
                'content_length': len(content),
                'content_type': content_type,
                'hour_of_day': context.get('hour_of_day', 12) if context else 12,
                'day_of_week': context.get('day_of_week', 1) if context else 1,
                'season': context.get('season', 'spring') if context else 'spring'
            }
            
            # Convert to DataFrame and encode
            df = pd.DataFrame([features])
            df_encoded = pd.get_dummies(df, columns=['content_type', 'season'])
            
            # Ensure all columns from training are present
            # (This would need to be adapted based on actual training data)
            
            # Make prediction
            predicted_engagement = self.model.predict(df_encoded)[0]
            
            # Get confidence interval (using model's uncertainty estimation)
            # For Random Forest, we can use the standard deviation of trees
            tree_predictions = [tree.predict(df_encoded)[0] for tree in self.model.estimators_]
            confidence_interval = np.std(tree_predictions) * 1.96  # 95% confidence
            
            return {
                'predicted_engagement': predicted_engagement,
                'confidence_interval': confidence_interval,
                'lower_bound': max(0, predicted_engagement - confidence_interval),
                'upper_bound': min(1, predicted_engagement + confidence_interval),
                'engagement_features': engagement_features
            }
            
        except Exception as e:
            logger.error(f"Error predicting engagement: {e}")
            raise
    
    def save_model(self, filepath):
        """Save trained model to file"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        try:
            joblib.dump({
                'model': self.model,
                'is_trained': self.is_trained
            }, filepath)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
    
    def load_model(self, filepath):
        """Load trained model from file"""
        try:
            data = joblib.load(filepath)
            self.model = data['model']
            self.is_trained = data['is_trained']
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

# API Endpoint Implementation
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

class EngagementPredictionRequest(BaseModel):
    content: str
    content_type: str = "article"
    context: Optional[Dict[str, Any]] = None

class EngagementPredictionResponse(BaseModel):
    predicted_engagement: float
    confidence_interval: float
    lower_bound: float
    upper_bound: float
    engagement_features: Dict[str, Any]
    recommendations: list

router = APIRouter(prefix="/api/engagement-prediction", tags=["engagement-prediction"])

# Global model instance
engagement_model = PredictiveEngagementModel()

@router.post("/predict", response_model=EngagementPredictionResponse)
async def predict_engagement(request: EngagementPredictionRequest):
    """Predict engagement for content"""
    try:
        result = engagement_model.predict_engagement(
            request.content,
            request.content_type,
            request.context
        )
        
        return EngagementPredictionResponse(
            predicted_engagement=result['predicted_engagement'],
            confidence_interval=result['confidence_interval'],
            lower_bound=result['lower_bound'],
            upper_bound=result['upper_bound'],
            engagement_features=result['engagement_features'],
            recommendations=result['engagement_features']['recommendations']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting engagement: {str(e)}")

@router.post("/train")
async def train_model(training_data: list):
    """Train the engagement prediction model"""
    try:
        result = engagement_model.train_model(training_data)
        return {
            "status": "success",
            "metrics": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training model: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Sample training data
    sample_training_data = [
        {
            'content': 'Sample article content with good engagement',
            'content_type': 'article',
            'hour_of_day': 10,
            'day_of_week': 2,
            'season': 'spring',
            'engagement_score': 0.85
        },
        {
            'content': 'Poorly written content with low engagement',
            'content_type': 'article',
            'hour_of_day': 15,
            'day_of_week': 6,
            'season': 'winter',
            'engagement_score': 0.32
        }
    ]
    
    # Initialize and train model
    model = PredictiveEngagementModel()
    training_result = model.train_model(sample_training_data)
    print(f"Training completed - MSE: {training_result['mse']:.4f}")
    
    # Test prediction
    test_content = "This is a test article to predict engagement."
    prediction = model.predict_engagement(test_content, 'article')
    print(f"Predicted engagement: {prediction['predicted_engagement']:.2f}")
```

### Phase 2: API Integration (Days 3-4)
**Objective**: Create API endpoints and integrate with existing systems

#### Day 3: API Endpoints and Integration
```python
# api/endpoints/engagement_prediction.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from ..services.engagement_prediction_service import EngagementPredictionService
from ..deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/engagement-prediction", tags=["engagement-prediction"])

class EngagementPredictionRequest(BaseModel):
    content: str
    content_type: str = "article"
    context: Optional[Dict[str, Any]] = None

class EngagementPredictionResponse(BaseModel):
    predicted_engagement: float
    confidence_interval: float
    lower_bound: float
    upper_bound: float
    engagement_features: Dict[str, Any]
    recommendations: List[str]
    created_at: datetime = datetime.now()

class BatchEngagementPredictionRequest(BaseModel):
    contents: List[EngagementPredictionRequest]

class BatchEngagementPredictionResponse(BaseModel):
    predictions: List[EngagementPredictionResponse]
    average_engagement: float
    best_content_index: int
    created_at: datetime = datetime.now()

@router.post("/predict", response_model=EngagementPredictionResponse)
async def predict_engagement(
    request: EngagementPredictionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Predict engagement for a single piece of content"""
    try:
        service = EngagementPredictionService()
        result = service.predict_engagement(
            request.content,
            request.content_type,
            request.context
        )
        
        return EngagementPredictionResponse(
            predicted_engagement=result['predicted_engagement'],
            confidence_interval=result['confidence_interval'],
            lower_bound=result['lower_bound'],
            upper_bound=result['upper_bound'],
            engagement_features=result['engagement_features'],
            recommendations=result['engagement_features']['recommendations']
        )
        
    except Exception as e:
        logger.error(f"Error predicting engagement: {e}")
        raise HTTPException(status_code=500, detail=f"Error predicting engagement: {str(e)}")

@router.post("/predict/batch", response_model=BatchEngagementPredictionResponse)
async def predict_batch_engagement(
    request: BatchEngagementPredictionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Predict engagement for multiple pieces of content"""
    try:
        service = EngagementPredictionService()
        predictions = []
        
        for content_request in request.contents:
            result = service.predict_engagement(
                content_request.content,
                content_request.content_type,
                content_request.context
            )
            
            prediction = EngagementPredictionResponse(
                predicted_engagement=result['predicted_engagement'],
                confidence_interval=result['confidence_interval'],
                lower_bound=result['lower_bound'],
                upper_bound=result['upper_bound'],
                engagement_features=result['engagement_features'],
                recommendations=result['engagement_features']['recommendations']
            )
            predictions.append(prediction)
        
        # Calculate batch statistics
        engagement_scores = [p.predicted_engagement for p in predictions]
        average_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
        best_content_index = engagement_scores.index(max(engagement_scores)) if engagement_scores else 0
        
        return BatchEngagementPredictionResponse(
            predictions=predictions,
            average_engagement=average_engagement,
            best_content_index=best_content_index
        )
        
    except Exception as e:
        logger.error(f"Error predicting batch engagement: {e}")
        raise HTTPException(status_code=500, detail=f"Error predicting batch engagement: {str(e)}")

@router.get("/models/status")
async def get_model_status(current_user: dict = Depends(get_current_user)):
    """Get the status of the engagement prediction model"""
    try:
        service = EngagementPredictionService()
        status = service.get_model_status()
        return status
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting model status: {str(e)}")

@router.post("/models/train")
async def train_model(training_data: List[Dict], current_user: dict = Depends(get_current_user)):
    """Train the engagement prediction model with new data"""
    if not current_user.get('is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = EngagementPredictionService()
        result = service.train_model(training_data)
        return {
            "status": "success",
            "message": "Model trained successfully",
            "metrics": result
        }
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=f"Error training model: {str(e)}")

# services/engagement_prediction_service.py
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, Any, List

from ..ml.engagement_prediction_model import PredictiveEngagementModel
from ..database import get_db
from ..models import EngagementPrediction

logger = logging.getLogger(__name__)

class EngagementPredictionService:
    def __init__(self):
        self.model = PredictiveEngagementModel()
        
    def predict_engagement(self, content: str, content_type: str = "article", context: Dict = None) -> Dict[str, Any]:
        """Predict engagement for content"""
        try:
            # Get current model status
            model_status = self.get_model_status()
            
            if not model_status.get('is_trained', False):
                # Use rule-based prediction if model not trained
                logger.warning("Model not trained, using rule-based prediction")
                return self._rule_based_prediction(content, content_type, context)
            
            # Use ML model for prediction
            result = self.model.predict_engagement(content, content_type, context)
            
            # Save prediction to database
            self._save_prediction(content, content_type, context, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in engagement prediction: {e}")
            # Fallback to rule-based prediction
            return self._rule_based_prediction(content, content_type, context)
    
    def _rule_based_prediction(self, content: str, content_type: str, context: Dict = None) -> Dict[str, Any]:
        """Fallback rule-based engagement prediction"""
        # Use the engagement scoring engine directly
        from ..utils.engagement_scoring import EngagementScoringEngine
        engine = EngagementScoringEngine()
        result = engine.generate_engagement_score(content, content_type)
        
        return {
            'predicted_engagement': result['overall_score'],
            'confidence_interval': 0.1,
            'lower_bound': max(0, result['overall_score'] - 0.1),
            'upper_bound': min(1, result['overall_score'] + 0.1),
            'engagement_features': result
        }
    
    def train_model(self, training_data: List[Dict]) -> Dict[str, Any]:
        """Train the engagement prediction model"""
        try:
            result = self.model.train_model(training_data)
            
            # Save model
            self.model.save_model('models/engagement_prediction_model.pkl')
            
            # Update model status in database
            self._update_model_status(True, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error training engagement model: {e}")
            self._update_model_status(False, {'error': str(e)})
            raise
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get the current status of the engagement prediction model"""
        try:
            # Check if model file exists
            import os
            model_exists = os.path.exists('models/engagement_prediction_model.pkl')
            
            # Get training status from database
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT is_trained, last_trained, training_metrics, created_at
                FROM model_status 
                WHERE model_name = 'engagement_prediction'
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            
            if row:
                return {
                    'is_trained': bool(row[0]),
                    'last_trained': row[1],
                    'training_metrics': row[2],
                    'model_exists': model_exists,
                    'created_at': row[3]
                }
            else:
                return {
                    'is_trained': False,
                    'model_exists': model_exists,
                    'last_trained': None,
                    'training_metrics': None,
                    'created_at': None
                }
                
        except Exception as e:
            logger.error(f"Error getting model status: {e}")
            return {
                'is_trained': False,
                'model_exists': False,
                'error': str(e)
            }
    
    def _save_prediction(self, content: str, content_type: str, context: Dict, result: Dict):
        """Save prediction to database"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                INSERT INTO engagement_predictions 
                (content_preview, content_type, context, predicted_engagement, 
                 confidence_interval, lower_bound, upper_bound, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                content[:100] + '...' if len(content) > 100 else content,
                content_type,
                str(context) if context else None,
                result['predicted_engagement'],
                result['confidence_interval'],
                result['lower_bound'],
                result['upper_bound'],
                datetime.now().isoformat()
            ))
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
    
    def _update_model_status(self, is_trained: bool, metrics: Dict):
        """Update model status in database"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                INSERT INTO model_status 
                (model_name, is_trained, last_trained, training_metrics, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                'engagement_prediction',
                is_trained,
                datetime.now().isoformat(),
                str(metrics),
                datetime.now().isoformat()
            ))
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating model status: {e}")

# ml/engagement_prediction_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import logging
from datetime import datetime
from typing import Dict, Any, List

from ..utils.engagement_scoring import EngagementScoringEngine

logger = logging.getLogger(__name__)

class PredictiveEngagementModel:
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.engagement_scoring_engine = EngagementScoringEngine()
        self.is_trained = False
        self.feature_columns = None
        
    def prepare_training_data(self, historical_data: List[Dict]) -> pd.DataFrame:
        """Prepare training data from historical engagement records"""
        features_list = []
        
        for record in historical_data:
            content = record.get('content', '') or record.get('transcript', '') or ''
            content_type = record.get('content_type', 'article')
            
            # Get engagement features
            engagement_features = self.engagement_scoring_engine.generate_engagement_score(
                content, content_type
            )
            
            # Flatten features
            features = {
                'complexity_score': engagement_features['breakdown']['complexity']['score'],
                'sentiment_score': engagement_features['breakdown']['sentiment']['score'],
                'keywords_score': engagement_features['breakdown']['keywords']['score'],
                'structure_score': engagement_features['breakdown']['structure']['score'],
                'ctas_score': engagement_features['breakdown']['ctas']['score'],
                'content_length': len(content),
                'content_type_article': 1 if content_type == 'article' else 0,
                'content_type_social': 1 if content_type == 'social' else 0,
                'content_type_video': 1 if content_type == 'video' else 0,
                'hour_of_day': record.get('hour_of_day', 12),
                'day_of_week': record.get('day_of_week', 1),
                'season_spring': 1 if record.get('season') == 'spring' else 0,
                'season_summer': 1 if record.get('season') == 'summer' else 0,
                'season_fall': 1 if record.get('season') == 'fall' else 0,
                'season_winter': 1 if record.get('season') == 'winter' else 0
            }
            
            # Add target variable (actual engagement)
            features['actual_engagement'] = record.get('engagement_score', 0)
            
            features_list.append(features)
        
        return pd.DataFrame(features_list)
    
    def train_model(self, training_data: List[Dict]) -> Dict[str, Any]:
        """Train the predictive engagement model"""
        try:
            # Prepare features
            df = self.prepare_training_data(training_data)
            
            # Store feature columns for prediction
            self.feature_columns = [col for col in df.columns if col != 'actual_engagement']
            
            # Separate features and target
            X = df[self.feature_columns]
            y = df['actual_engagement']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            self.is_trained = True
            
            logger.info(f"Model trained successfully - MSE: {mse:.4f}, R²: {r2:.4f}")
            
            return {
                'mse': mse,
                'r2_score': r2,
                'feature_importance': dict(zip(self.feature_columns, self.model.feature_importances_))
            }
            
        except Exception as e:
            logger.error(f"Error training predictive model: {e}")
            raise
    
    def predict_engagement(self, content: str, content_type: str = "article", context: Dict = None) -> Dict[str, Any]:
        """Predict engagement for new content"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        try:
            # Get engagement features
            engagement_features = self.engagement_scoring_engine.generate_engagement_score(
                content, content_type
            )
            
            # Prepare features for prediction
            features = {
                'complexity_score': engagement_features['breakdown']['complexity']['score'],
                'sentiment_score': engagement_features['breakdown']['sentiment']['score'],
                'keywords_score': engagement_features['breakdown']['keywords']['score'],
                'structure_score': engagement_features['breakdown']['structure']['score'],
                'ctas_score': engagement_features['breakdown']['ctas']['score'],
                'content_length': len(content),
                'content_type_article': 1 if content_type == 'article' else 0,
                'content_type_social': 1 if content_type == 'social' else 0,
                'content_type_video': 1 if content_type == 'video' else 0,
                'hour_of_day': context.get('hour_of_day', 12) if context else 12,
                'day_of_week': context.get('day_of_week', 1) if context else 1,
                'season_spring': 1 if context and context.get('season') == 'spring' else 0,
                'season_summer': 1 if context and context.get('season') == 'summer' else 0,
                'season_fall': 1 if context and context.get('season') == 'fall' else 0,
                'season_winter': 1 if context and context.get('season') == 'winter' else 0
            }
            
            # Convert to DataFrame
            df = pd.DataFrame([features])
            
            # Ensure all columns from training are present
            if self.feature_columns:
                for col in self.feature_columns:
                    if col not in df.columns:
                        df[col] = 0
            
            # Select only the columns used in training
            df_filtered = df[self.feature_columns] if self.feature_columns else df
            
            # Make prediction
            predicted_engagement = self.model.predict(df_filtered)[0]
            
            # Get confidence interval (using model's uncertainty estimation)
            # For Random Forest, we can use the standard deviation of trees
            if hasattr(self.model, 'estimators_'):
                tree_predictions = [tree.predict(df_filtered)[0] for tree in self.model.estimators_]
                confidence_interval = np.std(tree_predictions) * 1.96  # 95% confidence
            else:
                confidence_interval = 0.1  # Default confidence
            
            return {
                'predicted_engagement': max(0, min(1, predicted_engagement)),  # Clamp to 0-1
                'confidence_interval': confidence_interval,
                'lower_bound': max(0, predicted_engagement - confidence_interval),
                'upper_bound': min(1, predicted_engagement + confidence_interval),
                'engagement_features': engagement_features
            }
            
        except Exception as e:
            logger.error(f"Error predicting engagement: {e}")
            raise
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        try:
            joblib.dump({
                'model': self.model,
                'is_trained': self.is_trained,
                'feature_columns': self.feature_columns
            }, filepath)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        try:
            data = joblib.load(filepath)
            self.model = data['model']
            self.is_trained = data['is_trained']
            self.feature_columns = data.get('feature_columns', None)
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
```