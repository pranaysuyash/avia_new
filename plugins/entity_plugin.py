"""
Entity extraction plugin system
"""

import logging
import re
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Pattern
from enum import Enum

from .plugin_manager import Plugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of entity extraction rules"""
    REGEX = "regex"
    KEYWORD = "keyword"
    PATTERN = "pattern"
    FUNCTION = "function"


@dataclass
class CustomEntityRule:
    """Custom entity extraction rule"""
    id: str
    name: str
    entity_type: str
    rule_type: RuleType
    pattern: str
    keywords: List[str] = None
    confidence: float = 0.8
    case_sensitive: bool = False
    enabled: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ExtractedEntity:
    """Extracted entity result"""
    text: str
    entity_type: str
    start_pos: int
    end_pos: int
    confidence: float
    rule_id: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EntityExtractionPlugin(Plugin):
    """Base class for entity extraction plugins"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.rules: List[CustomEntityRule] = []
        self.compiled_patterns: Dict[str, Pattern] = {}
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            # Load rules from config
            rules_config = self.config.get('rules', [])
            for rule_config in rules_config:
                rule = CustomEntityRule(**rule_config)
                self.add_rule(rule)
            
            logger.info(f"Initialized entity extraction plugin with {len(self.rules)} rules")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing entity extraction plugin: {e}")
            return False
    
    async def execute(self, text: str, **kwargs) -> List[ExtractedEntity]:
        """Execute entity extraction on text"""
        entities = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                rule_entities = self._apply_rule(text, rule)
                entities.extend(rule_entities)
                
            except Exception as e:
                logger.error(f"Error applying rule {rule.id}: {e}")
        
        # Remove duplicates and sort by position
        entities = self._deduplicate_entities(entities)
        entities.sort(key=lambda e: e.start_pos)
        
        return entities
    
    async def cleanup(self):
        """Clean up plugin resources"""
        self.rules.clear()
        self.compiled_patterns.clear()
    
    def add_rule(self, rule: CustomEntityRule) -> bool:
        """Add a custom entity extraction rule"""
        try:
            # Validate rule
            if not self._validate_rule(rule):
                return False
            
            # Compile regex patterns
            if rule.rule_type == RuleType.REGEX:
                flags = 0 if rule.case_sensitive else re.IGNORECASE
                self.compiled_patterns[rule.id] = re.compile(rule.pattern, flags)
            
            self.rules.append(rule)
            logger.info(f"Added entity extraction rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding rule {rule.name}: {e}")
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a custom entity extraction rule"""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                del self.rules[i]
                if rule_id in self.compiled_patterns:
                    del self.compiled_patterns[rule_id]
                logger.info(f"Removed entity extraction rule: {rule_id}")
                return True
        
        return False
    
    def get_rule(self, rule_id: str) -> Optional[CustomEntityRule]:
        """Get a rule by ID"""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def list_rules(self, enabled_only: bool = False) -> List[CustomEntityRule]:
        """List all rules"""
        if enabled_only:
            return [rule for rule in self.rules if rule.enabled]
        return self.rules.copy()
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule"""
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule"""
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = False
            return True
        return False
    
    def _apply_rule(self, text: str, rule: CustomEntityRule) -> List[ExtractedEntity]:
        """Apply a single rule to text"""
        entities = []
        
        if rule.rule_type == RuleType.REGEX:
            entities = self._apply_regex_rule(text, rule)
        elif rule.rule_type == RuleType.KEYWORD:
            entities = self._apply_keyword_rule(text, rule)
        elif rule.rule_type == RuleType.PATTERN:
            entities = self._apply_pattern_rule(text, rule)
        elif rule.rule_type == RuleType.FUNCTION:
            entities = self._apply_function_rule(text, rule)
        
        return entities
    
    def _apply_regex_rule(self, text: str, rule: CustomEntityRule) -> List[ExtractedEntity]:
        """Apply regex rule"""
        entities = []
        pattern = self.compiled_patterns.get(rule.id)
        
        if pattern:
            for match in pattern.finditer(text):
                entity = ExtractedEntity(
                    text=match.group(),
                    entity_type=rule.entity_type,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=rule.confidence,
                    rule_id=rule.id,
                    metadata={'rule_type': 'regex', 'pattern': rule.pattern}
                )
                entities.append(entity)
        
        return entities
    
    def _apply_keyword_rule(self, text: str, rule: CustomEntityRule) -> List[ExtractedEntity]:
        """Apply keyword rule"""
        entities = []
        search_text = text if rule.case_sensitive else text.lower()
        
        for keyword in rule.keywords:
            search_keyword = keyword if rule.case_sensitive else keyword.lower()
            start = 0
            
            while True:
                pos = search_text.find(search_keyword, start)
                if pos == -1:
                    break
                
                # Check word boundaries
                if self._is_word_boundary(text, pos, pos + len(keyword)):
                    entity = ExtractedEntity(
                        text=text[pos:pos + len(keyword)],
                        entity_type=rule.entity_type,
                        start_pos=pos,
                        end_pos=pos + len(keyword),
                        confidence=rule.confidence,
                        rule_id=rule.id,
                        metadata={'rule_type': 'keyword', 'keyword': keyword}
                    )
                    entities.append(entity)
                
                start = pos + 1
        
        return entities
    
    def _apply_pattern_rule(self, text: str, rule: CustomEntityRule) -> List[ExtractedEntity]:
        """Apply pattern rule (simplified regex)"""
        # Convert simple patterns to regex
        pattern = rule.pattern
        pattern = pattern.replace('*', '.*')
        pattern = pattern.replace('?', '.')
        
        flags = 0 if rule.case_sensitive else re.IGNORECASE
        compiled_pattern = re.compile(pattern, flags)
        
        entities = []
        for match in compiled_pattern.finditer(text):
            entity = ExtractedEntity(
                text=match.group(),
                entity_type=rule.entity_type,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=rule.confidence,
                rule_id=rule.id,
                metadata={'rule_type': 'pattern', 'pattern': rule.pattern}
            )
            entities.append(entity)
        
        return entities
    
    def _apply_function_rule(self, text: str, rule: CustomEntityRule) -> List[ExtractedEntity]:
        """Apply function-based rule"""
        # This would be implemented by subclasses for custom logic
        return []
    
    def _validate_rule(self, rule: CustomEntityRule) -> bool:
        """Validate a rule"""
        if not rule.name or not rule.entity_type:
            return False
        
        if rule.rule_type == RuleType.REGEX:
            try:
                re.compile(rule.pattern)
            except re.error:
                return False
        elif rule.rule_type == RuleType.KEYWORD:
            if not rule.keywords:
                return False
        
        return True
    
    def _is_word_boundary(self, text: str, start: int, end: int) -> bool:
        """Check if positions are at word boundaries"""
        if start > 0 and text[start - 1].isalnum():
            return False
        if end < len(text) and text[end].isalnum():
            return False
        return True
    
    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate entities"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity.start_pos, entity.end_pos, entity.entity_type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities


class DefaultEntityExtractionPlugin(EntityExtractionPlugin):
    """Default entity extraction plugin with common rules"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Default Entity Extraction",
            version="1.0.0",
            description="Default entity extraction plugin with common patterns",
            author="Transcription App",
            plugin_type=PluginType.ENTITY_EXTRACTION,
            config_schema={
                "type": "object",
                "properties": {
                    "rules": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "entity_type": {"type": "string"},
                                "rule_type": {"type": "string"},
                                "pattern": {"type": "string"},
                                "keywords": {"type": "array", "items": {"type": "string"}},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                "case_sensitive": {"type": "boolean"},
                                "enabled": {"type": "boolean"}
                            },
                            "required": ["id", "name", "entity_type", "rule_type"]
                        }
                    }
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize with default rules"""
        # Add default rules if none configured
        if not self.config.get('rules'):
            self._add_default_rules()
        
        return await super().initialize()
    
    def _add_default_rules(self):
        """Add default entity extraction rules"""
        default_rules = [
            # Email addresses
            CustomEntityRule(
                id="email_rule",
                name="Email Addresses",
                entity_type="EMAIL",
                rule_type=RuleType.REGEX,
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                confidence=0.95
            ),
            
            # Phone numbers
            CustomEntityRule(
                id="phone_rule",
                name="Phone Numbers",
                entity_type="PHONE",
                rule_type=RuleType.REGEX,
                pattern=r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                confidence=0.9
            ),
            
            # URLs
            CustomEntityRule(
                id="url_rule",
                name="URLs",
                entity_type="URL",
                rule_type=RuleType.REGEX,
                pattern=r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
                confidence=0.95
            ),
            
            # Credit card numbers (masked)
            CustomEntityRule(
                id="credit_card_rule",
                name="Credit Card Numbers",
                entity_type="CREDIT_CARD",
                rule_type=RuleType.REGEX,
                pattern=r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                confidence=0.8
            ),
            
            # Social Security Numbers (masked)
            CustomEntityRule(
                id="ssn_rule",
                name="Social Security Numbers",
                entity_type="SSN",
                rule_type=RuleType.REGEX,
                pattern=r'\b\d{3}-\d{2}-\d{4}\b',
                confidence=0.9
            ),
            
            # IP Addresses
            CustomEntityRule(
                id="ip_rule",
                name="IP Addresses",
                entity_type="IP_ADDRESS",
                rule_type=RuleType.REGEX,
                pattern=r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                confidence=0.85
            ),
            
            # Technical terms
            CustomEntityRule(
                id="tech_terms_rule",
                name="Technical Terms",
                entity_type="TECHNOLOGY",
                rule_type=RuleType.KEYWORD,
                keywords=[
                    "API", "REST", "GraphQL", "JSON", "XML", "HTTP", "HTTPS",
                    "database", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL",
                    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "cloud",
                    "machine learning", "AI", "artificial intelligence", "neural network",
                    "blockchain", "cryptocurrency", "Bitcoin", "Ethereum"
                ],
                confidence=0.7,
                case_sensitive=False
            )
        ]
        
        # Add rules to config
        self.config['rules'] = [
            {
                'id': rule.id,
                'name': rule.name,
                'entity_type': rule.entity_type,
                'rule_type': rule.rule_type.value,
                'pattern': rule.pattern,
                'keywords': rule.keywords,
                'confidence': rule.confidence,
                'case_sensitive': rule.case_sensitive,
                'enabled': rule.enabled
            }
            for rule in default_rules
        ]


class MedicalEntityExtractionPlugin(EntityExtractionPlugin):
    """Medical entity extraction plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Medical Entity Extraction",
            version="1.0.0",
            description="Entity extraction plugin for medical terminology",
            author="Transcription App",
            plugin_type=PluginType.ENTITY_EXTRACTION,
            dependencies=["medical_terms_db"]  # Hypothetical dependency
        )
    
    async def initialize(self) -> bool:
        """Initialize with medical rules"""
        medical_rules = [
            CustomEntityRule(
                id="medication_rule",
                name="Medications",
                entity_type="MEDICATION",
                rule_type=RuleType.KEYWORD,
                keywords=[
                    "aspirin", "ibuprofen", "acetaminophen", "lisinopril",
                    "metformin", "amlodipine", "simvastatin", "omeprazole"
                ],
                confidence=0.8,
                case_sensitive=False
            ),
            
            CustomEntityRule(
                id="condition_rule",
                name="Medical Conditions",
                entity_type="CONDITION",
                rule_type=RuleType.KEYWORD,
                keywords=[
                    "diabetes", "hypertension", "asthma", "pneumonia",
                    "bronchitis", "arthritis", "migraine", "depression"
                ],
                confidence=0.8,
                case_sensitive=False
            )
        ]
        
        for rule in medical_rules:
            self.add_rule(rule)
        
        return True


class LegalEntityExtractionPlugin(EntityExtractionPlugin):
    """Legal entity extraction plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Legal Entity Extraction",
            version="1.0.0",
            description="Entity extraction plugin for legal terminology",
            author="Transcription App",
            plugin_type=PluginType.ENTITY_EXTRACTION
        )
    
    async def initialize(self) -> bool:
        """Initialize with legal rules"""
        legal_rules = [
            CustomEntityRule(
                id="case_number_rule",
                name="Case Numbers",
                entity_type="CASE_NUMBER",
                rule_type=RuleType.REGEX,
                pattern=r'\b\d{2}-\w{2}-\d{4,6}\b',
                confidence=0.9
            ),
            
            CustomEntityRule(
                id="legal_terms_rule",
                name="Legal Terms",
                entity_type="LEGAL_TERM",
                rule_type=RuleType.KEYWORD,
                keywords=[
                    "plaintiff", "defendant", "contract", "agreement",
                    "liability", "damages", "settlement", "injunction",
                    "subpoena", "deposition", "testimony", "evidence"
                ],
                confidence=0.7,
                case_sensitive=False
            )
        ]
        
        for rule in legal_rules:
            self.add_rule(rule)
        
        return True