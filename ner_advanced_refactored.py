#!/usr/bin/env python3
"""
Advanced Named Entity Recognition Module
Handles entity extraction using OpenAI API with enhanced processing
Refactored to use BaseNER class
"""

import os
import re
import logging
import json
from typing import Dict, List, Tuple, Optional
import openai
from dotenv import load_dotenv

from errors import NERError, handle_error, ErrorCode
from ner_base import BaseNER, EntityValidationConfig, normalize_entity_type

load_dotenv()
logger = logging.getLogger(__name__)


class AdvancedNER(BaseNER):
    """Advanced NER implementation using OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 model: str = "gpt-3.5-turbo",
                 validation_config: Optional[EntityValidationConfig] = None):
        """
        Initialize Advanced NER with OpenAI API
        
        Args:
            api_key: OpenAI API key (if None, reads from environment)
            model: OpenAI model to use
            validation_config: Configuration for entity validation
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        self.client = None
        
        # Set up validation config
        if validation_config is None:
            validation_config = EntityValidationConfig(
                min_length=2,
                max_length=200,  # Allow longer entities for AI extraction
                blacklist_patterns=[
                    r'^\d+$',  # Pure numbers
                    r'^[^\w\s]+$',  # Only special characters
                    r'^\s+$',  # Only whitespace
                ]
            )
        
        super().__init__(validation_config)
    
    def _initialize(self):
        """Initialize the OpenAI client"""
        if not self.api_key:
            raise NERError(
                message="OpenAI API key not found",
                error_code=ErrorCode.API_KEY_MISSING,
                user_message="OpenAI API key is required for advanced entity extraction.",
                ner_type="openai",
                suggestions=[
                    "Set your OpenAI API key in the .env file",
                    "Get an API key from https://platform.openai.com/",
                    "Use Basic NER mode instead"
                ]
            )
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info("Successfully initialized OpenAI client")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise NERError(
                message=f"Failed to initialize OpenAI client: {e}",
                error_code=ErrorCode.API_CONNECTION_ERROR,
                user_message="Failed to connect to OpenAI API.",
                ner_type="openai",
                suggestions=[
                    "Check your internet connection",
                    "Verify your API key is valid",
                    "Try again later"
                ]
            )
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities using OpenAI API
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary with entity types as keys and lists of unique entities as values
        """
        if not text or not text.strip():
            return {}
        
        try:
            if not self.client:
                self._initialize()
            
            # Check text length
            if len(text) > 50000:  # ~12k tokens
                logger.warning(f"Text too long ({len(text)} chars), truncating to 50000")
                text = text[:50000]
            
            # Create the prompt
            prompt = self._create_extraction_prompt(text)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise entity extraction assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse response
            content = response.choices[0].message.content
            entities = self._parse_response(content)
            
            # Normalize entity types
            normalized_entities = {}
            for entity_type, entity_list in entities.items():
                normalized_type = normalize_entity_type(entity_type)
                normalized_entities[normalized_type] = entity_list
            
            # Apply validation and filtering
            filtered_entities = self.filter_entities(normalized_entities)
            
            logger.info(f"Advanced NER extracted {sum(len(v) for v in filtered_entities.values())} entities")
            return filtered_entities
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise NERError(
                message=f"API rate limit exceeded: {e}",
                error_code=ErrorCode.API_RATE_LIMIT,
                user_message="Too many requests. Please wait a moment.",
                ner_type="openai",
                suggestions=[
                    "Wait a few seconds and try again",
                    "Use Basic NER mode for immediate results",
                    "Consider upgrading your OpenAI plan"
                ]
            )
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {e}")
            raise NERError(
                message=f"API authentication failed: {e}",
                error_code=ErrorCode.API_AUTH_ERROR,
                user_message="Invalid API key.",
                ner_type="openai",
                suggestions=[
                    "Check your OpenAI API key in settings",
                    "Generate a new API key from OpenAI dashboard",
                    "Use Basic NER mode instead"
                ]
            )
        except Exception as e:
            logger.error(f"Error during advanced entity extraction: {e}")
            app_error = handle_error(e, {
                "ner_type": "openai",
                "text_length": len(text) if text else 0,
                "operation": "advanced_entity_extraction"
            })
            raise app_error
    
    def extract_entities_with_summary(self, text: str) -> Tuple[Dict[str, List[str]], str]:
        """
        Extract entities and generate a summary
        
        Args:
            text: Input text to process
            
        Returns:
            Tuple of (entities dict, summary text)
        """
        entities = self.extract_entities(text)
        
        # Generate summary
        summary = self._generate_summary(text, entities)
        
        return entities, summary
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create the prompt for entity extraction"""
        return f"""Extract named entities from the following text and return them in a structured JSON format.

Categories to extract:
- PERSON: Names of people
- ORGANIZATION: Companies, agencies, institutions
- LOCATION: Cities, countries, addresses
- DATE: Dates and time expressions
- MONEY: Monetary values
- PRODUCT: Products or services
- EVENT: Named events
- EMAIL: Email addresses
- URL: Web addresses
- PHONE: Phone numbers

Return ONLY a JSON object with these categories as keys and arrays of unique entities as values.
Example: {{"PERSON": ["John Smith"], "ORGANIZATION": ["OpenAI"], "LOCATION": ["San Francisco"]}}

Text to analyze:
{text}

JSON Response:"""
    
    def _parse_response(self, response: str) -> Dict[str, List[str]]:
        """Parse the OpenAI response to extract entities"""
        try:
            # Try to parse as JSON
            entities = json.loads(response.strip())
            
            # Validate structure
            if not isinstance(entities, dict):
                raise ValueError("Response is not a dictionary")
            
            # Ensure all values are lists of strings
            result = {}
            for key, value in entities.items():
                if isinstance(value, list):
                    # Filter and clean entities
                    cleaned = []
                    for item in value:
                        if isinstance(item, str) and item.strip():
                            cleaned.append(item.strip())
                    if cleaned:
                        result[key] = cleaned
                elif isinstance(value, str) and value.strip():
                    result[key] = [value.strip()]
            
            return result
            
        except json.JSONDecodeError:
            # Fallback: try to extract entities from text response
            logger.warning("Failed to parse JSON response, using fallback extraction")
            return self._fallback_extraction(response)
    
    def _fallback_extraction(self, response: str) -> Dict[str, List[str]]:
        """Fallback method to extract entities from non-JSON response"""
        entities = {
            'person': [],
            'organization': [],
            'location': [],
            'date': [],
            'miscellaneous': []
        }
        
        # Simple pattern matching
        lines = response.split('\n')
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for category headers
            line_lower = line.lower()
            if 'person' in line_lower or 'people' in line_lower:
                current_category = 'person'
            elif 'organization' in line_lower or 'company' in line_lower:
                current_category = 'organization'
            elif 'location' in line_lower or 'place' in line_lower:
                current_category = 'location'
            elif 'date' in line_lower or 'time' in line_lower:
                current_category = 'date'
            elif current_category and line.startswith(('-', '•', '*', '·')):
                # Extract entity from bullet point
                entity = line.lstrip('-•*· ').strip()
                if entity and self.validate_entity(entity):
                    entities[current_category].append(entity)
        
        # Remove empty categories
        return {k: v for k, v in entities.items() if v}
    
    def _generate_summary(self, text: str, entities: Dict[str, List[str]]) -> str:
        """Generate a summary of the text focusing on key entities"""
        try:
            # Create a focused prompt
            entity_context = []
            for entity_type, entity_list in entities.items():
                if entity_list:
                    entity_context.append(f"{entity_type}: {', '.join(entity_list[:5])}")
            
            prompt = f"""Provide a brief 2-3 sentence summary of this text, focusing on the key entities mentioned:

Entities found:
{chr(10).join(entity_context)}

Text:
{text[:2000]}...

Summary:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise summarization assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"Failed to generate summary: {e}")
            return "Summary generation failed."


# Global instance for backward compatibility
_default_ner = None

def get_default_ner() -> AdvancedNER:
    """Get the default AdvancedNER instance"""
    global _default_ner
    if _default_ner is None:
        _default_ner = AdvancedNER()
    return _default_ner


# Legacy function for backward compatibility
def extract_entities_advanced(text: str) -> Tuple[Dict[str, List[str]], str]:
    """
    Extract entities using OpenAI API (legacy function)
    
    This is a legacy function maintained for backward compatibility.
    For new code, use AdvancedNER class directly.
    
    Args:
        text: Input text to process
        
    Returns:
        Tuple of (entities dict, summary text)
    """
    ner = get_default_ner()
    return ner.extract_entities_with_summary(text)


# Simpler version that returns just entities
def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract entities without summary (legacy function)"""
    ner = get_default_ner()
    return ner.extract_entities(text)