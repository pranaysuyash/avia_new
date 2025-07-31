"""
AI-powered tag management system
"""

import json
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import re
import hashlib
from collections import Counter
import os

logger = logging.getLogger(__name__)


class TagCategory(Enum):
    """Categories for tags"""
    TOPIC = "topic"
    PERSON = "person"
    LOCATION = "location"
    ORGANIZATION = "organization"
    DATE = "date"
    CONCEPT = "concept"
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    ACTION = "action"
    PRODUCT = "product"
    EVENT = "event"
    CUSTOM = "custom"


@dataclass
class Tag:
    """Represents a content tag"""
    id: str
    text: str
    category: TagCategory
    confidence: float
    frequency: int
    source: str  # 'ai', 'manual', 'rule'
    metadata: Dict[str, Any]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'text': self.text,
            'category': self.category.value,
            'confidence': self.confidence,
            'frequency': self.frequency,
            'source': self.source,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


class TagManager:
    """Manages AI-powered content tagging"""
    
    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider
        self.tag_cache = {}
        self.custom_rules = []
        self.taxonomies = self._load_taxonomies()
        self.stopwords = self._load_stopwords()
    
    def generate_tags(
        self,
        content: str,
        max_tags: int = 20,
        min_confidence: float = 0.5,
        categories: Optional[List[TagCategory]] = None,
        use_cache: bool = True
    ) -> List[Tag]:
        """
        Generate tags for content using AI and rules
        
        Args:
            content: Text content to tag
            max_tags: Maximum number of tags to generate
            min_confidence: Minimum confidence threshold
            categories: Specific categories to focus on
            use_cache: Whether to use cached results
            
        Returns:
            List of tags
        """
        # Check cache
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if use_cache and content_hash in self.tag_cache:
            return self.tag_cache[content_hash]
        
        tags = []
        
        # AI-based tagging
        if self.ai_provider:
            ai_tags = self._generate_ai_tags(content, categories)
            tags.extend(ai_tags)
        
        # Rule-based tagging
        rule_tags = self._generate_rule_tags(content)
        tags.extend(rule_tags)
        
        # Pattern-based extraction
        pattern_tags = self._extract_pattern_tags(content)
        tags.extend(pattern_tags)
        
        # Deduplicate and rank
        tags = self._deduplicate_and_rank(tags, content)
        
        # Filter by confidence
        tags = [tag for tag in tags if tag.confidence >= min_confidence]
        
        # Limit to max_tags
        tags = tags[:max_tags]
        
        # Cache results
        if use_cache:
            self.tag_cache[content_hash] = tags
        
        return tags
    
    def _generate_ai_tags(
        self,
        content: str,
        categories: Optional[List[TagCategory]] = None
    ) -> List[Tag]:
        """Generate tags using AI provider"""
        if not self.ai_provider:
            return []
        
        try:
            # Prepare prompt
            prompt = self._create_tagging_prompt(content, categories)
            
            # Get AI response
            response = self.ai_provider.generate_tags(prompt)
            
            # Parse response into tags
            tags = []
            for tag_data in response:
                tag = Tag(
                    id=self._generate_tag_id(tag_data['text']),
                    text=tag_data['text'],
                    category=TagCategory(tag_data.get('category', 'topic')),
                    confidence=tag_data.get('confidence', 0.8),
                    frequency=1,
                    source='ai',
                    metadata={'model': self.ai_provider.model_name},
                    created_at=datetime.now()
                )
                tags.append(tag)
            
            return tags
            
        except Exception as e:
            logger.error(f"Error generating AI tags: {e}")
            return []
    
    def _generate_rule_tags(self, content: str) -> List[Tag]:
        """Generate tags using custom rules"""
        tags = []
        content_lower = content.lower()
        
        for rule in self.custom_rules:
            if self._match_rule(rule, content_lower):
                tag = Tag(
                    id=self._generate_tag_id(rule['tag']),
                    text=rule['tag'],
                    category=TagCategory(rule.get('category', 'topic')),
                    confidence=rule.get('confidence', 0.9),
                    frequency=1,
                    source='rule',
                    metadata={'rule_name': rule.get('name', 'custom')},
                    created_at=datetime.now()
                )
                tags.append(tag)
        
        return tags
    
    def _extract_pattern_tags(self, content: str) -> List[Tag]:
        """Extract tags using pattern matching"""
        tags = []
        
        # Extract dates
        date_pattern = r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|' \
                      r'January|February|March|April|May|June|July|August|September|October|November|December' \
                      r'\s+\d{1,2},?\s+\d{4})\b'
        dates = re.findall(date_pattern, content, re.IGNORECASE)
        for date in dates:
            tags.append(Tag(
                id=self._generate_tag_id(date),
                text=date,
                category=TagCategory.DATE,
                confidence=0.95,
                frequency=1,
                source='pattern',
                metadata={'pattern': 'date'},
                created_at=datetime.now()
            ))
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        for email in emails:
            tags.append(Tag(
                id=self._generate_tag_id(email),
                text=email,
                category=TagCategory.TECHNICAL,
                confidence=0.95,
                frequency=1,
                source='pattern',
                metadata={'pattern': 'email'},
                created_at=datetime.now()
            ))
        
        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, content)
        for url in urls:
            domain = re.search(r'://([^/]+)', url)
            if domain:
                tags.append(Tag(
                    id=self._generate_tag_id(domain.group(1)),
                    text=domain.group(1),
                    category=TagCategory.TECHNICAL,
                    confidence=0.9,
                    frequency=1,
                    source='pattern',
                    metadata={'pattern': 'url', 'full_url': url},
                    created_at=datetime.now()
                ))
        
        # Extract hashtags
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, content)
        for hashtag in hashtags:
            tags.append(Tag(
                id=self._generate_tag_id(hashtag),
                text=hashtag,
                category=TagCategory.TOPIC,
                confidence=0.85,
                frequency=1,
                source='pattern',
                metadata={'pattern': 'hashtag'},
                created_at=datetime.now()
            ))
        
        # Extract quoted phrases
        quote_pattern = r'"([^"]+)"'
        quotes = re.findall(quote_pattern, content)
        for quote in quotes[:5]:  # Limit to 5 quotes
            if len(quote.split()) <= 4:  # Only short quotes
                tags.append(Tag(
                    id=self._generate_tag_id(quote),
                    text=quote,
                    category=TagCategory.CONCEPT,
                    confidence=0.7,
                    frequency=1,
                    source='pattern',
                    metadata={'pattern': 'quote'},
                    created_at=datetime.now()
                ))
        
        return tags
    
    def _deduplicate_and_rank(self, tags: List[Tag], content: str) -> List[Tag]:
        """Deduplicate and rank tags"""
        # Group by normalized text
        tag_groups = {}
        for tag in tags:
            normalized = self._normalize_text(tag.text)
            if normalized not in tag_groups:
                tag_groups[normalized] = []
            tag_groups[normalized].append(tag)
        
        # Merge and rank
        ranked_tags = []
        for normalized, group in tag_groups.items():
            # Merge tags in group
            merged_tag = self._merge_tags(group)
            
            # Calculate frequency in content
            frequency = len(re.findall(r'\b' + re.escape(merged_tag.text) + r'\b', 
                                     content, re.IGNORECASE))
            merged_tag.frequency = frequency
            
            # Adjust confidence based on frequency
            if frequency > 1:
                merged_tag.confidence = min(1.0, merged_tag.confidence * 1.1)
            
            ranked_tags.append(merged_tag)
        
        # Sort by confidence and frequency
        ranked_tags.sort(key=lambda t: (t.confidence, t.frequency), reverse=True)
        
        return ranked_tags
    
    def _merge_tags(self, tags: List[Tag]) -> Tag:
        """Merge multiple tags into one"""
        if len(tags) == 1:
            return tags[0]
        
        # Use the most confident source
        best_tag = max(tags, key=lambda t: t.confidence)
        
        # Merge metadata
        merged_metadata = {}
        for tag in tags:
            merged_metadata.update(tag.metadata)
        merged_metadata['merged_from'] = len(tags)
        
        # Average confidence
        avg_confidence = sum(t.confidence for t in tags) / len(tags)
        
        return Tag(
            id=best_tag.id,
            text=best_tag.text,
            category=best_tag.category,
            confidence=avg_confidence,
            frequency=best_tag.frequency,
            source='merged',
            metadata=merged_metadata,
            created_at=best_tag.created_at
        )
    
    def _create_tagging_prompt(
        self,
        content: str,
        categories: Optional[List[TagCategory]] = None
    ) -> str:
        """Create prompt for AI tagging"""
        category_list = categories or list(TagCategory)
        category_str = ", ".join([cat.value for cat in category_list])
        
        prompt = f"""Analyze the following text and generate relevant tags.

Categories to consider: {category_str}

For each tag, provide:
- text: the tag text
- category: one of the categories listed above
- confidence: a score between 0 and 1

Focus on:
1. Key topics and themes
2. Important entities (people, places, organizations)
3. Technical terms and concepts
4. Actionable items
5. Sentiment and tone

Text to analyze:
{content[:2000]}  # Limit content length

Generate up to 15 tags in JSON format."""
        
        return prompt
    
    def _generate_tag_id(self, text: str) -> str:
        """Generate unique ID for tag"""
        normalized = self._normalize_text(text)
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def _match_rule(self, rule: Dict[str, Any], content: str) -> bool:
        """Check if rule matches content"""
        if 'pattern' in rule:
            return bool(re.search(rule['pattern'], content, re.IGNORECASE))
        elif 'keywords' in rule:
            return any(keyword.lower() in content for keyword in rule['keywords'])
        return False
    
    def _load_taxonomies(self) -> Dict[str, List[str]]:
        """Load predefined taxonomies"""
        return {
            'programming_languages': [
                'python', 'javascript', 'java', 'c++', 'ruby', 'go', 'rust',
                'typescript', 'swift', 'kotlin', 'scala', 'r', 'matlab'
            ],
            'ai_ml_terms': [
                'machine learning', 'deep learning', 'neural network', 'ai',
                'artificial intelligence', 'nlp', 'computer vision', 'reinforcement learning',
                'supervised learning', 'unsupervised learning', 'transformer', 'llm'
            ],
            'business_terms': [
                'revenue', 'profit', 'growth', 'strategy', 'market', 'customer',
                'sales', 'marketing', 'investment', 'roi', 'kpi', 'stakeholder'
            ],
            'sentiments': [
                'positive', 'negative', 'neutral', 'optimistic', 'pessimistic',
                'excited', 'concerned', 'confident', 'uncertain'
            ]
        }
    
    def _load_stopwords(self) -> Set[str]:
        """Load stopwords to filter out"""
        return {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are',
            'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
            'it', 'we', 'they', 'them', 'their', 'what', 'which', 'who',
            'when', 'where', 'why', 'how', 'all', 'each', 'every', 'some',
            'any', 'few', 'more', 'most', 'other', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
            'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
            'then', 'once'
        }
    
    def add_custom_rule(
        self,
        name: str,
        tag: str,
        category: str,
        pattern: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        confidence: float = 0.9
    ):
        """Add custom tagging rule"""
        rule = {
            'name': name,
            'tag': tag,
            'category': category,
            'confidence': confidence
        }
        
        if pattern:
            rule['pattern'] = pattern
        elif keywords:
            rule['keywords'] = keywords
        else:
            raise ValueError("Either pattern or keywords must be provided")
        
        self.custom_rules.append(rule)
    
    def suggest_related_tags(
        self,
        tags: List[Tag],
        content: str,
        max_suggestions: int = 10
    ) -> List[Tag]:
        """Suggest related tags based on existing tags"""
        suggestions = []
        
        # Extract concepts related to existing tags
        for tag in tags:
            # Look for related terms in taxonomies
            for taxonomy_name, terms in self.taxonomies.items():
                if tag.text.lower() in terms:
                    # Suggest other terms from same taxonomy
                    for term in terms:
                        if term != tag.text.lower() and term in content.lower():
                            suggestions.append(Tag(
                                id=self._generate_tag_id(term),
                                text=term,
                                category=tag.category,
                                confidence=0.7,
                                frequency=1,
                                source='suggestion',
                                metadata={'based_on': tag.text, 'taxonomy': taxonomy_name},
                                created_at=datetime.now()
                            ))
        
        # Deduplicate and limit
        seen = set()
        unique_suggestions = []
        for tag in suggestions:
            if tag.text not in seen:
                seen.add(tag.text)
                unique_suggestions.append(tag)
        
        return unique_suggestions[:max_suggestions]
    
    def export_tags(self, tags: List[Tag], format: str = "json") -> str:
        """Export tags in various formats"""
        if format == "json":
            return json.dumps([tag.to_dict() for tag in tags], indent=2)
        
        elif format == "csv":
            lines = ["text,category,confidence,frequency,source"]
            for tag in tags:
                lines.append(f"{tag.text},{tag.category.value},{tag.confidence:.2f},"
                           f"{tag.frequency},{tag.source}")
            return '\n'.join(lines)
        
        elif format == "text":
            lines = []
            for category in TagCategory:
                category_tags = [t for t in tags if t.category == category]
                if category_tags:
                    lines.append(f"\n{category.value.upper()}:")
                    for tag in category_tags:
                        lines.append(f"  - {tag.text} ({tag.confidence:.0%})")
            return '\n'.join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def save_tag_profile(self, tags: List[Tag], filepath: str):
        """Save tag profile for later use"""
        profile = {
            'tags': [tag.to_dict() for tag in tags],
            'created_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        with open(filepath, 'w') as f:
            json.dump(profile, f, indent=2)
    
    def load_tag_profile(self, filepath: str) -> List[Tag]:
        """Load tag profile from file"""
        with open(filepath, 'r') as f:
            profile = json.load(f)
        
        tags = []
        for tag_data in profile['tags']:
            tag = Tag(
                id=tag_data['id'],
                text=tag_data['text'],
                category=TagCategory(tag_data['category']),
                confidence=tag_data['confidence'],
                frequency=tag_data['frequency'],
                source=tag_data['source'],
                metadata=tag_data['metadata'],
                created_at=datetime.fromisoformat(tag_data['created_at'])
            )
            tags.append(tag)
        
        return tags