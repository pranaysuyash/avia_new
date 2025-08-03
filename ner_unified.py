#!/usr/bin/env python3
"""
Unified Named Entity Recognition Module
Combines Basic and Advanced NER with automatic fallback
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

from ner_base import BaseNER, EntityValidationConfig, combine_ner_results
from ner_basic_refactored import BasicNER
from ner_advanced_refactored import AdvancedNER
from errors import NERError, ErrorCode

logger = logging.getLogger(__name__)


class NERMode(Enum):
    """NER processing modes"""
    BASIC = "basic"
    ADVANCED = "advanced"
    HYBRID = "hybrid"  # Use both and combine results
    AUTO = "auto"  # Automatically choose based on availability


class UnifiedNER:
    """Unified NER that can use multiple extraction methods"""
    
    def __init__(self, 
                 mode: NERMode = NERMode.AUTO,
                 basic_model: str = "en_core_web_sm",
                 advanced_model: str = "gpt-3.5-turbo",
                 api_key: Optional[str] = None,
                 validation_config: Optional[EntityValidationConfig] = None):
        """
        Initialize Unified NER
        
        Args:
            mode: NER processing mode
            basic_model: spaCy model name for basic NER
            advanced_model: OpenAI model name for advanced NER
            api_key: OpenAI API key (optional, can read from env)
            validation_config: Shared validation configuration
        """
        self.mode = mode
        self.validation_config = validation_config
        
        # Initialize NER implementations
        self.basic_ner = None
        self.advanced_ner = None
        
        # Try to initialize based on mode
        if mode in [NERMode.BASIC, NERMode.HYBRID, NERMode.AUTO]:
            try:
                self.basic_ner = BasicNER(basic_model, validation_config)
                logger.info("Basic NER initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Basic NER: {e}")
                if mode == NERMode.BASIC:
                    raise
        
        if mode in [NERMode.ADVANCED, NERMode.HYBRID, NERMode.AUTO]:
            try:
                self.advanced_ner = AdvancedNER(api_key, advanced_model, validation_config)
                logger.info("Advanced NER initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Advanced NER: {e}")
                if mode == NERMode.ADVANCED:
                    raise
        
        # Validate we have at least one working NER
        if not self.basic_ner and not self.advanced_ner:
            raise NERError(
                message="No NER implementation available",
                error_code=ErrorCode.NER_NOT_AVAILABLE,
                user_message="Entity extraction is not available.",
                suggestions=[
                    "Install spaCy model: python -m spacy download en_core_web_sm",
                    "Configure OpenAI API key in settings",
                    "Check error logs for more details"
                ]
            )
    
    def extract_entities(self, text: str, 
                        fallback: bool = True) -> Dict[str, List[str]]:
        """
        Extract entities using configured mode
        
        Args:
            text: Text to process
            fallback: Whether to fallback to other methods on failure
            
        Returns:
            Dictionary of entity types to entity lists
        """
        if not text or not text.strip():
            return {}
        
        # Determine which method to use
        if self.mode == NERMode.BASIC:
            return self._extract_basic(text, fallback)
        elif self.mode == NERMode.ADVANCED:
            return self._extract_advanced(text, fallback)
        elif self.mode == NERMode.HYBRID:
            return self._extract_hybrid(text)
        else:  # AUTO mode
            return self._extract_auto(text)
    
    def extract_entities_with_summary(self, text: str) -> Tuple[Dict[str, List[str]], str]:
        """
        Extract entities and generate summary (if available)
        
        Args:
            text: Text to process
            
        Returns:
            Tuple of (entities dict, summary text)
        """
        entities = self.extract_entities(text)
        
        # Try to get summary from advanced NER
        summary = "Summary not available."
        if self.advanced_ner:
            try:
                _, summary = self.advanced_ner.extract_entities_with_summary(text)
            except Exception as e:
                logger.warning(f"Failed to generate summary: {e}")
        
        return entities, summary
    
    def _extract_basic(self, text: str, fallback: bool) -> Dict[str, List[str]]:
        """Extract using basic NER with optional fallback"""
        try:
            if not self.basic_ner:
                raise NERError(
                    message="Basic NER not available",
                    error_code=ErrorCode.NER_NOT_AVAILABLE,
                    user_message="Basic entity extraction is not available."
                )
            return self.basic_ner.extract_entities(text)
        except Exception as e:
            logger.error(f"Basic NER failed: {e}")
            if fallback and self.advanced_ner:
                logger.info("Falling back to Advanced NER")
                return self._extract_advanced(text, fallback=False)
            raise
    
    def _extract_advanced(self, text: str, fallback: bool) -> Dict[str, List[str]]:
        """Extract using advanced NER with optional fallback"""
        try:
            if not self.advanced_ner:
                raise NERError(
                    message="Advanced NER not available",
                    error_code=ErrorCode.NER_NOT_AVAILABLE,
                    user_message="Advanced entity extraction is not available."
                )
            return self.advanced_ner.extract_entities(text)
        except Exception as e:
            logger.error(f"Advanced NER failed: {e}")
            if fallback and self.basic_ner:
                logger.info("Falling back to Basic NER")
                return self._extract_basic(text, fallback=False)
            raise
    
    def _extract_hybrid(self, text: str) -> Dict[str, List[str]]:
        """Extract using both methods and combine results"""
        basic_entities = {}
        advanced_entities = {}
        
        # Try basic extraction
        if self.basic_ner:
            try:
                basic_entities = self.basic_ner.extract_entities(text)
            except Exception as e:
                logger.warning(f"Basic NER failed in hybrid mode: {e}")
        
        # Try advanced extraction
        if self.advanced_ner:
            try:
                advanced_entities = self.advanced_ner.extract_entities(text)
            except Exception as e:
                logger.warning(f"Advanced NER failed in hybrid mode: {e}")
        
        # Combine results
        if basic_entities and advanced_entities:
            return combine_ner_results(basic_entities, advanced_entities)
        elif basic_entities:
            return basic_entities
        elif advanced_entities:
            return advanced_entities
        else:
            return {}
    
    def _extract_auto(self, text: str) -> Dict[str, List[str]]:
        """Automatically choose best method based on text and availability"""
        # For short texts, prefer basic NER (faster)
        if len(text) < 1000 and self.basic_ner:
            try:
                return self.basic_ner.extract_entities(text)
            except Exception as e:
                logger.warning(f"Basic NER failed in auto mode: {e}")
        
        # For longer texts or if basic failed, try advanced
        if self.advanced_ner:
            try:
                return self.advanced_ner.extract_entities(text)
            except Exception as e:
                logger.warning(f"Advanced NER failed in auto mode: {e}")
        
        # Fallback to basic if available
        if self.basic_ner:
            return self.basic_ner.extract_entities(text)
        
        return {}
    
    def get_available_modes(self) -> List[NERMode]:
        """Get list of available NER modes"""
        modes = []
        if self.basic_ner:
            modes.append(NERMode.BASIC)
        if self.advanced_ner:
            modes.append(NERMode.ADVANCED)
        if self.basic_ner and self.advanced_ner:
            modes.append(NERMode.HYBRID)
        modes.append(NERMode.AUTO)
        return modes
    
    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about available NER methods"""
        return {
            'mode': self.mode.value,
            'basic_available': self.basic_ner is not None,
            'advanced_available': self.advanced_ner is not None,
            'basic_model': self.basic_ner.model_name if self.basic_ner else None,
            'advanced_model': self.advanced_ner.model if self.advanced_ner else None,
            'available_modes': [mode.value for mode in self.get_available_modes()]
        }


# Convenience function for quick entity extraction
def extract_entities(text: str, 
                    mode: str = "auto",
                    api_key: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Quick entity extraction with specified mode
    
    Args:
        text: Text to process
        mode: One of "basic", "advanced", "hybrid", or "auto"
        api_key: Optional OpenAI API key
        
    Returns:
        Dictionary of entity types to entity lists
    """
    try:
        ner_mode = NERMode(mode)
    except ValueError:
        ner_mode = NERMode.AUTO
    
    unified_ner = UnifiedNER(mode=ner_mode, api_key=api_key)
    return unified_ner.extract_entities(text)


# Example usage
if __name__ == "__main__":
    # Example text
    sample_text = """
    Apple Inc. CEO Tim Cook announced the new iPhone 15 at the Steve Jobs Theater 
    in Cupertino, California on September 12, 2023. The event was attended by 
    tech journalists from The Verge, TechCrunch, and Wired. The new phone starts 
    at $799 and will be available on September 22nd.
    """
    
    # Test different modes
    for mode in ["basic", "advanced", "hybrid", "auto"]:
        print(f"\n{mode.upper()} Mode:")
        try:
            entities = extract_entities(sample_text, mode=mode)
            for entity_type, entity_list in entities.items():
                print(f"  {entity_type}: {', '.join(entity_list)}")
        except Exception as e:
            print(f"  Error: {e}")