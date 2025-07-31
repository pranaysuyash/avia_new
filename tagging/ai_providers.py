"""
AI providers for content tagging
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import openai
import streamlit as st
from transformers import pipeline

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def generate_tags(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate tags from prompt"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get model name"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI-based tag generation"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if self.api_key:
            openai.api_key = self.api_key
    
    def generate_tags(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate tags using OpenAI"""
        if not self.is_available():
            logger.warning("OpenAI API key not configured")
            return []
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content tagging expert. Generate relevant tags in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                tags = json.loads(json_str)
                return tags
            else:
                # Try to parse as single object
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    tag = json.loads(json_str)
                    return [tag]
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating tags with OpenAI: {e}")
            return []
    
    @property
    def model_name(self) -> str:
        return self.model
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class LocalModelProvider(AIProvider):
    """Local model-based tag generation using Hugging Face"""
    
    def __init__(self, model_name: str = "dslim/bert-base-NER"):
        self.model_name_str = model_name
        self.ner_pipeline = None
        self.zero_shot_pipeline = None
        self._load_models()
    
    def _load_models(self):
        """Load local models"""
        try:
            # Load NER model for entity extraction
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model_name_str,
                aggregation_strategy="simple"
            )
            
            # Load zero-shot classification for categorization
            self.zero_shot_pipeline = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            
        except Exception as e:
            logger.error(f"Error loading local models: {e}")
    
    def generate_tags(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate tags using local models"""
        if not self.is_available():
            return []
        
        try:
            # Extract content from prompt (remove instructions)
            content_start = prompt.find("Text to analyze:")
            if content_start > 0:
                content = prompt[content_start + len("Text to analyze:"):].strip()
            else:
                content = prompt
            
            tags = []
            
            # Extract named entities
            if self.ner_pipeline:
                entities = self.ner_pipeline(content)
                
                for entity in entities:
                    # Map entity types to categories
                    category_map = {
                        'PER': 'person',
                        'LOC': 'location',
                        'ORG': 'organization',
                        'MISC': 'concept'
                    }
                    
                    category = category_map.get(entity['entity_group'], 'topic')
                    
                    tags.append({
                        'text': entity['word'].strip(),
                        'category': category,
                        'confidence': entity['score']
                    })
            
            # Add topic classification
            if self.zero_shot_pipeline and len(content) > 50:
                # Define candidate labels
                candidate_labels = [
                    'technology', 'business', 'science', 'health',
                    'education', 'politics', 'entertainment', 'sports'
                ]
                
                # Classify content
                result = self.zero_shot_pipeline(
                    content[:500],  # Limit length
                    candidate_labels=candidate_labels,
                    multi_label=True
                )
                
                # Add top classifications as tags
                for label, score in zip(result['labels'][:3], result['scores'][:3]):
                    if score > 0.3:
                        tags.append({
                            'text': label,
                            'category': 'topic',
                            'confidence': score
                        })
            
            # Extract keywords using simple frequency analysis
            words = content.lower().split()
            word_freq = {}
            
            for word in words:
                if len(word) > 4 and word.isalpha():
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Add frequent words as tags
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            for word, freq in sorted_words[:5]:
                if freq > 1:
                    tags.append({
                        'text': word,
                        'category': 'concept',
                        'confidence': min(0.8, freq / 10)
                    })
            
            return tags
            
        except Exception as e:
            logger.error(f"Error generating tags with local model: {e}")
            return []
    
    @property
    def model_name(self) -> str:
        return self.model_name_str
    
    def is_available(self) -> bool:
        return self.ner_pipeline is not None


class MockAIProvider(AIProvider):
    """Mock AI provider for testing"""
    
    def generate_tags(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate mock tags"""
        # Extract some words from prompt as mock tags
        words = prompt.split()
        
        mock_tags = [
            {'text': 'artificial intelligence', 'category': 'concept', 'confidence': 0.9},
            {'text': 'machine learning', 'category': 'technical', 'confidence': 0.85},
            {'text': 'data science', 'category': 'topic', 'confidence': 0.8},
            {'text': 'python', 'category': 'technical', 'confidence': 0.75},
            {'text': 'innovation', 'category': 'concept', 'confidence': 0.7}
        ]
        
        # Add some random words from prompt
        content_words = [w for w in words if len(w) > 5 and w.isalpha()][:3]
        for word in content_words:
            mock_tags.append({
                'text': word.lower(),
                'category': 'topic',
                'confidence': 0.6
            })
        
        return mock_tags
    
    @property
    def model_name(self) -> str:
        return "mock-model"
    
    def is_available(self) -> bool:
        return True


def get_available_providers() -> Dict[str, AIProvider]:
    """Get all available AI providers"""
    providers = {}
    
    # Check OpenAI
    openai_key = os.getenv("OPENAI_API_KEY") or st.session_state.get('openai_api_key')
    if openai_key:
        providers['OpenAI'] = OpenAIProvider(api_key=openai_key)
    
    # Check local models
    try:
        local_provider = LocalModelProvider()
        if local_provider.is_available():
            providers['Local Model'] = local_provider
    except:
        pass
    
    # Always include mock provider for testing
    providers['Mock (Testing)'] = MockAIProvider()
    
    return providers


def select_ai_provider() -> Optional[AIProvider]:
    """UI component to select AI provider"""
    providers = get_available_providers()
    
    if not providers:
        st.warning("No AI providers available. Please configure OpenAI API key or install local models.")
        return None
    
    provider_names = list(providers.keys())
    
    selected_name = st.selectbox(
        "Select AI Provider",
        provider_names,
        help="Choose the AI provider for tag generation"
    )
    
    provider = providers[selected_name]
    
    # Show provider info
    st.info(f"Using {provider.model_name} for tag generation")
    
    # OpenAI API key input if needed
    if selected_name == "OpenAI" and not provider.is_available():
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key"
        )
        if api_key:
            st.session_state.openai_api_key = api_key
            provider = OpenAIProvider(api_key=api_key)
    
    return provider if provider.is_available() else None