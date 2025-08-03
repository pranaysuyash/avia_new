#!/usr/bin/env python3
"""
AI-Powered Content Generation and Enhancement System (Task 44)
Comprehensive content generation including podcast intros, content expansion, FAQ generation, and optimization
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import time
from collections import defaultdict, Counter

# Import AI/ML libraries
try:
    import openai
    from openai import OpenAI
    import tiktoken
    from textblob import TextBlob
    import spacy
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.tag import pos_tag
    from nltk.chunk import ne_chunk
except ImportError as e:
    print(f"Warning: Some AI libraries not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Types of content that can be generated"""
    PODCAST_INTRO = "podcast_intro"
    PODCAST_OUTRO = "podcast_outro"
    EXPANDED_TEXT = "expanded_text"
    FAQ = "faq"
    SUMMARY = "summary"
    TAGS = "tags"
    OPTIMIZATION = "optimization"
    SOCIAL_MEDIA = "social_media"
    BLOG_POST = "blog_post"
    NEWSLETTER = "newsletter"

class AudienceType(Enum):
    """Target audience types for content optimization"""
    GENERAL = "general"
    TECHNICAL = "technical"
    BUSINESS = "business"
    ACADEMIC = "academic"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    EDUCATIONAL = "educational"
    MARKETING = "marketing"

class ContentTone(Enum):
    """Tone options for generated content"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    ENTHUSIASTIC = "enthusiastic"
    INFORMATIVE = "informative"
    CONVERSATIONAL = "conversational"
    AUTHORITATIVE = "authoritative"

@dataclass
class ContentGenerationRequest:
    """Request structure for content generation"""
    content_type: str
    source_text: str
    target_audience: str = AudienceType.GENERAL.value
    tone: str = ContentTone.PROFESSIONAL.value
    length: str = "medium"  # short, medium, long
    language: str = "en"
    custom_instructions: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class GeneratedContent:
    """Structure for generated content response"""
    content_type: str
    generated_text: str
    confidence_score: float
    word_count: int
    generation_time: float
    metadata: Dict[str, Any]
    suggestions: List[str] = None
    alternatives: List[str] = None

@dataclass
class ContentOptimization:
    """Structure for content optimization suggestions"""
    original_text: str
    optimized_text: str
    improvements: List[str]
    readability_score: float
    target_audience: str
    optimization_type: str

class AIContentGenerator:
    """Main AI-powered content generation system"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not provided. Some features will be limited.")
        
        # Initialize NLP components
        self.setup_nlp()
        
        # Content templates and prompts
        self.templates = self.load_content_templates()
        
        # Generation statistics
        self.generation_stats = defaultdict(int)
    
    def setup_nlp(self):
        """Setup NLP components"""
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('maxent_ne_chunker', quiet=True)
            nltk.download('words', quiet=True)
            
            # Load spaCy model
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found. Some features will be limited.")
                self.nlp = None
            
            # Initialize tokenizer for token counting
            try:
                self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
            except:
                self.tokenizer = None
                
        except Exception as e:
            logger.error(f"Error setting up NLP components: {e}")
    
    def load_content_templates(self) -> Dict[str, Dict[str, str]]:
        """Load content generation templates and prompts"""
        return {
            ContentType.PODCAST_INTRO.value: {
                "system_prompt": "You are an expert podcast producer creating engaging introductions.",
                "user_prompt": """Create a compelling podcast intro based on this transcript content: {content}

Requirements:
- Target audience: {audience}
- Tone: {tone}
- Length: {length}
- Include a hook to grab attention
- Mention key topics that will be covered
- Keep it engaging and professional

Generate only the intro text, no additional commentary.""",
                "max_tokens": 300
            },
            
            ContentType.PODCAST_OUTRO.value: {
                "system_prompt": "You are an expert podcast producer creating memorable conclusions.",
                "user_prompt": """Create an engaging podcast outro based on this transcript content: {content}

Requirements:
- Target audience: {audience}
- Tone: {tone}
- Length: {length}
- Summarize key takeaways
- Include a call-to-action
- Thank the audience
- Encourage engagement (subscribe, share, etc.)

Generate only the outro text, no additional commentary.""",
                "max_tokens": 300
            },
            
            ContentType.EXPANDED_TEXT.value: {
                "system_prompt": "You are an expert content writer who expands bullet points into comprehensive text.",
                "user_prompt": """Expand these bullet points into well-structured, comprehensive text: {content}

Requirements:
- Target audience: {audience}
- Tone: {tone}
- Length: {length}
- Maintain the original meaning and key points
- Add context, examples, and explanations
- Use proper paragraph structure
- Make it flow naturally

Generate the expanded text only.""",
                "max_tokens": 800
            },
            
            ContentType.FAQ.value: {
                "system_prompt": "You are an expert at creating comprehensive FAQ sections from content.",
                "user_prompt": """Generate a comprehensive FAQ based on this content: {content}

Requirements:
- Target audience: {audience}
- Tone: {tone}
- Create 5-10 relevant questions and detailed answers
- Cover the main topics and potential user concerns
- Make answers informative and helpful
- Use clear, accessible language

Format as Q: [Question] A: [Answer] for each item.""",
                "max_tokens": 1000
            },
            
            ContentType.TAGS.value: {
                "system_prompt": "You are an expert content categorization specialist.",
                "user_prompt": """Generate relevant tags and categories for this content: {content}

Requirements:
- Create 10-15 relevant tags
- Include both specific and general tags
- Consider SEO keywords
- Think about searchability
- Include topic categories

Return as a comma-separated list of tags.""",
                "max_tokens": 200
            },
            
            ContentType.OPTIMIZATION.value: {
                "system_prompt": "You are a content optimization expert who improves text for specific audiences.",
                "user_prompt": """Optimize this content for the target audience: {content}

Target audience: {audience}
Desired tone: {tone}
Optimization focus: {length}

Provide:
1. Optimized version of the text
2. List of specific improvements made
3. Explanation of changes for the target audience

Format as:
OPTIMIZED TEXT:
[optimized content]

IMPROVEMENTS:
- [improvement 1]
- [improvement 2]
etc.""",
                "max_tokens": 1200
            }
        }
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text for API usage estimation"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough estimation: ~4 characters per token
            return len(text) // 4
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str = "gpt-3.5-turbo") -> float:
        """Estimate API cost for generation"""
        # Pricing as of 2024 (may need updates)
        pricing = {
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},  # per 1K tokens
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03}
        }
        
        if model in pricing:
            input_cost = (prompt_tokens / 1000) * pricing[model]["input"]
            output_cost = (completion_tokens / 1000) * pricing[model]["output"]
            return input_cost + output_cost
        
        return 0.0
    
    async def generate_content(self, request: ContentGenerationRequest) -> GeneratedContent:
        """Generate content based on request"""
        start_time = time.time()
        
        try:
            # Get template for content type
            template = self.templates.get(request.content_type)
            if not template:
                raise ValueError(f"Unsupported content type: {request.content_type}")
            
            # Prepare prompt
            user_prompt = template["user_prompt"].format(
                content=request.source_text[:4000],  # Limit input length
                audience=request.target_audience,
                tone=request.tone,
                length=request.length
            )
            
            if request.custom_instructions:
                user_prompt += f"\n\nAdditional instructions: {request.custom_instructions}"
            
            # Generate content using OpenAI
            if self.client:
                generated_text = await self._generate_with_openai(
                    system_prompt=template["system_prompt"],
                    user_prompt=user_prompt,
                    max_tokens=template.get("max_tokens", 500)
                )
                confidence_score = 0.9  # High confidence for OpenAI
            else:
                # Fallback to rule-based generation
                generated_text = self._generate_fallback(request)
                confidence_score = 0.6  # Lower confidence for fallback
            
            generation_time = time.time() - start_time
            
            # Post-process generated content
            generated_text = self._post_process_content(generated_text, request.content_type)
            
            # Generate suggestions and alternatives
            suggestions = self._generate_suggestions(request, generated_text)
            alternatives = self._generate_alternatives(request, generated_text) if request.content_type in [ContentType.TAGS.value, ContentType.SUMMARY.value] else []
            
            # Update statistics
            self.generation_stats[request.content_type] += 1
            
            return GeneratedContent(
                content_type=request.content_type,
                generated_text=generated_text,
                confidence_score=confidence_score,
                word_count=len(generated_text.split()),
                generation_time=generation_time,
                metadata={
                    "target_audience": request.target_audience,
                    "tone": request.tone,
                    "length": request.length,
                    "language": request.language,
                    "source_length": len(request.source_text.split()),
                    "model_used": "openai" if self.client else "fallback"
                },
                suggestions=suggestions,
                alternatives=alternatives
            )
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise
    
    async def _generate_with_openai(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Generate content using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _generate_fallback(self, request: ContentGenerationRequest) -> str:
        """Fallback content generation without OpenAI"""
        content_type = request.content_type
        source_text = request.source_text
        
        if content_type == ContentType.PODCAST_INTRO.value:
            return self._generate_podcast_intro_fallback(source_text, request.target_audience)
        elif content_type == ContentType.PODCAST_OUTRO.value:
            return self._generate_podcast_outro_fallback(source_text, request.target_audience)
        elif content_type == ContentType.EXPANDED_TEXT.value:
            return self._generate_expanded_text_fallback(source_text)
        elif content_type == ContentType.FAQ.value:
            return self._generate_faq_fallback(source_text)
        elif content_type == ContentType.TAGS.value:
            return self._generate_tags_fallback(source_text)
        elif content_type == ContentType.OPTIMIZATION.value:
            return self._generate_optimization_fallback(source_text, request.target_audience)
        else:
            return f"Generated content for {content_type} (fallback mode)"
    
    def _generate_podcast_intro_fallback(self, source_text: str, audience: str) -> str:
        """Generate podcast intro using rule-based approach"""
        # Extract key topics
        key_topics = self._extract_key_topics(source_text)[:3]
        
        intro_templates = [
            f"Welcome to today's episode! We're diving deep into {', '.join(key_topics)} and exploring what this means for {audience} audiences.",
            f"Hello and welcome! Today we're discussing {', '.join(key_topics)} - topics that are crucial for anyone interested in this field.",
            f"Thanks for joining us! In this episode, we'll explore {', '.join(key_topics)} and share insights that matter to you."
        ]
        
        return intro_templates[0]  # Use first template
    
    def _generate_podcast_outro_fallback(self, source_text: str, audience: str) -> str:
        """Generate podcast outro using rule-based approach"""
        key_takeaways = self._extract_key_takeaways(source_text)[:2]
        
        outro = f"That wraps up today's discussion on {', '.join(key_takeaways)}. "
        outro += "Thanks for listening! If you found this valuable, please subscribe and share with others who might benefit. "
        outro += "We'll be back next time with more insights. Until then, keep learning and growing!"
        
        return outro
    
    def _generate_expanded_text_fallback(self, source_text: str) -> str:
        """Generate expanded text using rule-based approach"""
        sentences = sent_tokenize(source_text)
        expanded_sentences = []
        
        for sentence in sentences:
            # Add context and explanation
            expanded = sentence
            if len(sentence.split()) < 10:  # Short sentences get expanded
                expanded += " This is particularly important because it affects how we understand and approach the topic."
            expanded_sentences.append(expanded)
        
        return " ".join(expanded_sentences)
    
    def _generate_faq_fallback(self, source_text: str) -> str:
        """Generate FAQ using rule-based approach"""
        key_topics = self._extract_key_topics(source_text)
        
        faq_items = []
        for i, topic in enumerate(key_topics[:5], 1):
            question = f"Q{i}: What should I know about {topic}?"
            answer = f"A{i}: {topic} is an important aspect covered in our discussion. It involves key considerations that can impact your understanding and approach to the subject."
            faq_items.append(f"{question}\n{answer}")
        
        return "\n\n".join(faq_items)
    
    def _generate_tags_fallback(self, source_text: str) -> str:
        """Generate tags using rule-based approach"""
        # Extract keywords using TF-IDF
        try:
            vectorizer = TfidfVectorizer(max_features=20, stop_words='english', ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform([source_text])
            feature_names = vectorizer.get_feature_names_out()
            
            # Get top features
            scores = tfidf_matrix.toarray()[0]
            top_indices = scores.argsort()[-15:][::-1]
            tags = [feature_names[i] for i in top_indices if scores[i] > 0]
            
            return ", ".join(tags)
        except:
            # Simple word frequency fallback
            words = word_tokenize(source_text.lower())
            stop_words = set(stopwords.words('english'))
            filtered_words = [w for w in words if w.isalpha() and w not in stop_words and len(w) > 3]
            
            word_freq = Counter(filtered_words)
            top_words = [word for word, count in word_freq.most_common(10)]
            
            return ", ".join(top_words)
    
    def _generate_optimization_fallback(self, source_text: str, audience: str) -> str:
        """Generate content optimization using rule-based approach"""
        optimized = source_text
        improvements = []
        
        # Simple optimizations based on audience
        if audience == AudienceType.TECHNICAL.value:
            # Add more technical detail
            optimized = re.sub(r'\b(system|process|method)\b', r'technical \1', optimized)
            improvements.append("Added technical terminology for technical audience")
        elif audience == AudienceType.CASUAL.value:
            # Simplify language
            optimized = re.sub(r'\b(utilize|implement|facilitate)\b', lambda m: {'utilize': 'use', 'implement': 'set up', 'facilitate': 'help'}[m.group()], optimized)
            improvements.append("Simplified language for casual audience")
        
        result = f"OPTIMIZED TEXT:\n{optimized}\n\nIMPROVEMENTS:\n"
        result += "\n".join(f"- {imp}" for imp in improvements)
        
        return result
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from text"""
        if self.nlp:
            doc = self.nlp(text)
            # Extract noun phrases and named entities
            topics = []
            
            # Named entities
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'EVENT', 'WORK_OF_ART']:
                    topics.append(ent.text.lower())
            
            # Noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3:  # Keep it concise
                    topics.append(chunk.text.lower())
            
            # Remove duplicates and return top topics
            unique_topics = list(dict.fromkeys(topics))
            return unique_topics[:10]
        else:
            # Simple keyword extraction
            words = word_tokenize(text.lower())
            stop_words = set(stopwords.words('english'))
            
            # Get nouns using POS tagging
            pos_tags = pos_tag(words)
            nouns = [word for word, pos in pos_tags if pos.startswith('NN') and word not in stop_words and len(word) > 3]
            
            # Return most frequent nouns
            noun_freq = Counter(nouns)
            return [word for word, count in noun_freq.most_common(10)]
    
    def _extract_key_takeaways(self, text: str) -> List[str]:
        """Extract key takeaways from text"""
        sentences = sent_tokenize(text)
        
        # Look for sentences with conclusion indicators
        takeaway_indicators = ['important', 'key', 'crucial', 'essential', 'main', 'primary', 'significant']
        
        takeaways = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in takeaway_indicators):
                # Extract the main concept
                words = sentence.split()
                if len(words) > 5:
                    takeaways.append(' '.join(words[:8]) + '...')
        
        return takeaways[:5] if takeaways else ['key insights', 'important concepts']
    
    def _post_process_content(self, content: str, content_type: str) -> str:
        """Post-process generated content"""
        # Clean up common issues
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Fix multiple newlines
        content = re.sub(r'\s+', ' ', content)  # Fix multiple spaces
        content = content.strip()
        
        # Content-type specific processing
        if content_type == ContentType.TAGS.value:
            # Ensure tags are properly formatted
            tags = [tag.strip() for tag in content.split(',')]
            tags = [tag for tag in tags if tag and len(tag) > 1]
            content = ', '.join(tags[:15])  # Limit to 15 tags
        
        elif content_type in [ContentType.PODCAST_INTRO.value, ContentType.PODCAST_OUTRO.value]:
            # Ensure proper sentence structure
            if not content.endswith(('.', '!', '?')):
                content += '.'
        
        return content
    
    def _generate_suggestions(self, request: ContentGenerationRequest, generated_content: str) -> List[str]:
        """Generate improvement suggestions for the content"""
        suggestions = []
        
        # Length-based suggestions
        word_count = len(generated_content.split())
        if request.length == "short" and word_count > 100:
            suggestions.append("Consider shortening the content for better impact")
        elif request.length == "long" and word_count < 200:
            suggestions.append("Consider expanding with more details and examples")
        
        # Audience-specific suggestions
        if request.target_audience == AudienceType.TECHNICAL.value:
            if not any(word in generated_content.lower() for word in ['system', 'process', 'implementation', 'technical']):
                suggestions.append("Add more technical terminology for your technical audience")
        
        elif request.target_audience == AudienceType.CASUAL.value:
            complex_words = ['utilize', 'implement', 'facilitate', 'optimize', 'leverage']
            if any(word in generated_content.lower() for word in complex_words):
                suggestions.append("Consider using simpler language for casual audience")
        
        # Content type specific suggestions
        if request.content_type == ContentType.PODCAST_INTRO.value:
            if 'welcome' not in generated_content.lower():
                suggestions.append("Consider adding a welcoming greeting")
        
        elif request.content_type == ContentType.FAQ.value:
            if generated_content.count('Q:') < 3:
                suggestions.append("Consider adding more questions for comprehensive coverage")
        
        return suggestions
    
    def _generate_alternatives(self, request: ContentGenerationRequest, generated_content: str) -> List[str]:
        """Generate alternative versions of the content"""
        alternatives = []
        
        if request.content_type == ContentType.TAGS.value:
            # Generate alternative tag sets
            source_words = word_tokenize(request.source_text.lower())
            stop_words = set(stopwords.words('english'))
            
            # Alternative 1: More specific tags
            specific_words = [w for w in source_words if len(w) > 6 and w.isalpha() and w not in stop_words]
            if specific_words:
                alternatives.append(', '.join(Counter(specific_words).most_common(10)))
            
            # Alternative 2: More general tags
            general_words = [w for w in source_words if 3 <= len(w) <= 6 and w.isalpha() and w not in stop_words]
            if general_words:
                alternatives.append(', '.join(Counter(general_words).most_common(10)))
        
        return alternatives[:2]  # Limit to 2 alternatives
    
    def optimize_content_for_audience(self, content: str, target_audience: str, optimization_focus: str = "readability") -> ContentOptimization:
        """Optimize existing content for a specific audience"""
        try:
            # Create optimization request
            request = ContentGenerationRequest(
                content_type=ContentType.OPTIMIZATION.value,
                source_text=content,
                target_audience=target_audience,
                length=optimization_focus
            )
            
            # Generate optimized content
            result = asyncio.run(self.generate_content(request))
            
            # Parse the optimization result
            optimized_text = result.generated_text
            improvements = []
            
            if "OPTIMIZED TEXT:" in optimized_text:
                parts = optimized_text.split("IMPROVEMENTS:")
                optimized_text = parts[0].replace("OPTIMIZED TEXT:", "").strip()
                
                if len(parts) > 1:
                    improvement_text = parts[1].strip()
                    improvements = [imp.strip("- ").strip() for imp in improvement_text.split("\n") if imp.strip()]
            
            # Calculate readability score (simple metric)
            readability_score = self._calculate_readability_score(optimized_text)
            
            return ContentOptimization(
                original_text=content,
                optimized_text=optimized_text,
                improvements=improvements,
                readability_score=readability_score,
                target_audience=target_audience,
                optimization_type=optimization_focus
            )
            
        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            raise
    
    def _calculate_readability_score(self, text: str) -> float:
        """Calculate a simple readability score"""
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        
        if not sentences or not words:
            return 0.0
        
        # Simple metrics
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words if word.isalpha()) / len([w for w in words if w.isalpha()])
        
        # Simple readability score (lower is more readable)
        score = (avg_sentence_length * 0.5) + (avg_word_length * 2)
        
        # Normalize to 0-100 scale (100 = most readable)
        normalized_score = max(0, min(100, 100 - (score - 10) * 5))
        
        return normalized_score
    
    def generate_podcast_intro_outro(self, transcript: str, show_name: str = "", host_name: str = "", 
                                   episode_number: Optional[int] = None) -> Dict[str, GeneratedContent]:
        """Generate both intro and outro for a podcast episode"""
        results = {}
        
        # Enhanced context for podcast generation
        context = f"Show: {show_name}\nHost: {host_name}\n"
        if episode_number:
            context += f"Episode: {episode_number}\n"
        context += f"Content: {transcript[:2000]}"
        
        # Generate intro
        intro_request = ContentGenerationRequest(
            content_type=ContentType.PODCAST_INTRO.value,
            source_text=context,
            target_audience=AudienceType.GENERAL.value,
            tone=ContentTone.ENTHUSIASTIC.value,
            length="medium"
        )
        
        # Generate outro
        outro_request = ContentGenerationRequest(
            content_type=ContentType.PODCAST_OUTRO.value,
            source_text=context,
            target_audience=AudienceType.GENERAL.value,
            tone=ContentTone.FRIENDLY.value,
            length="medium"
        )
        
        try:
            results['intro'] = asyncio.run(self.generate_content(intro_request))
            results['outro'] = asyncio.run(self.generate_content(outro_request))
        except Exception as e:
            logger.error(f"Error generating podcast intro/outro: {e}")
            raise
        
        return results
    
    def generate_comprehensive_faq(self, content: str, num_questions: int = 8) -> GeneratedContent:
        """Generate a comprehensive FAQ with specified number of questions"""
        request = ContentGenerationRequest(
            content_type=ContentType.FAQ.value,
            source_text=content,
            target_audience=AudienceType.GENERAL.value,
            tone=ContentTone.INFORMATIVE.value,
            length="long",
            custom_instructions=f"Generate exactly {num_questions} questions and detailed answers"
        )
        
        return asyncio.run(self.generate_content(request))
    
    def expand_bullet_points(self, bullet_points: str, expansion_level: str = "detailed") -> GeneratedContent:
        """Expand bullet points into comprehensive text"""
        length_mapping = {
            "brief": "short",
            "detailed": "medium", 
            "comprehensive": "long"
        }
        
        request = ContentGenerationRequest(
            content_type=ContentType.EXPANDED_TEXT.value,
            source_text=bullet_points,
            target_audience=AudienceType.PROFESSIONAL.value,
            tone=ContentTone.INFORMATIVE.value,
            length=length_mapping.get(expansion_level, "medium")
        )
        
        return asyncio.run(self.generate_content(request))
    
    def generate_content_tags(self, content: str, tag_categories: List[str] = None) -> GeneratedContent:
        """Generate comprehensive tags for content"""
        custom_instructions = ""
        if tag_categories:
            custom_instructions = f"Focus on these categories: {', '.join(tag_categories)}"
        
        request = ContentGenerationRequest(
            content_type=ContentType.TAGS.value,
            source_text=content,
            target_audience=AudienceType.GENERAL.value,
            tone=ContentTone.PROFESSIONAL.value,
            length="medium",
            custom_instructions=custom_instructions
        )
        
        return asyncio.run(self.generate_content(request))
    
    def batch_generate_content(self, requests: List[ContentGenerationRequest]) -> List[GeneratedContent]:
        """Generate multiple pieces of content in batch"""
        results = []
        
        for request in requests:
            try:
                result = asyncio.run(self.generate_content(request))
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch generation for {request.content_type}: {e}")
                # Create error result
                error_result = GeneratedContent(
                    content_type=request.content_type,
                    generated_text=f"Error generating {request.content_type}: {str(e)}",
                    confidence_score=0.0,
                    word_count=0,
                    generation_time=0.0,
                    metadata={"error": True, "error_message": str(e)}
                )
                results.append(error_result)
        
        return results
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get statistics about content generation usage"""
        return {
            "total_generations": sum(self.generation_stats.values()),
            "by_content_type": dict(self.generation_stats),
            "api_available": self.client is not None,
            "nlp_available": self.nlp is not None,
            "supported_content_types": list(self.templates.keys())
        }

class ContentGenerationUI:
    """Streamlit UI for content generation system"""
    
    def __init__(self):
        self.generator = AIContentGenerator()
    
    def render_header(self):
        """Render the main header"""
        st.title("🤖 AI-Powered Content Generation")
        st.markdown("Transform your transcripts into engaging content with AI assistance")
        
        # API status
        if self.generator.client:
            st.success("✅ OpenAI API connected - Full AI features available")
        else:
            st.warning("⚠️ OpenAI API not configured - Using fallback generation")
    
    def render_content_generator(self):
        """Render the main content generation interface"""
        st.header("📝 Content Generator")
        
        # Input section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            source_text = st.text_area(
                "Source Content",
                height=200,
                placeholder="Paste your transcript or content here...",
                help="Enter the source content you want to transform"
            )
        
        with col2:
            content_type = st.selectbox(
                "Content Type",
                options=[
                    ContentType.PODCAST_INTRO.value,
                    ContentType.PODCAST_OUTRO.value,
                    ContentType.EXPANDED_TEXT.value,
                    ContentType.FAQ.value,
                    ContentType.TAGS.value,
                    ContentType.OPTIMIZATION.value
                ],
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            target_audience = st.selectbox(
                "Target Audience",
                options=[e.value for e in AudienceType],
                format_func=lambda x: x.title()
            )
            
            tone = st.selectbox(
                "Tone",
                options=[e.value for e in ContentTone],
                format_func=lambda x: x.title()
            )
            
            length = st.selectbox(
                "Length",
                options=["short", "medium", "long"],
                index=1
            )
        
        # Custom instructions
        custom_instructions = st.text_input(
            "Custom Instructions (Optional)",
            placeholder="Any specific requirements or preferences..."
        )
        
        # Generate button
        if st.button("🚀 Generate Content", type="primary", disabled=not source_text):
            if source_text:
                with st.spinner("Generating content..."):
                    try:
                        request = ContentGenerationRequest(
                            content_type=content_type,
                            source_text=source_text,
                            target_audience=target_audience,
                            tone=tone,
                            length=length,
                            custom_instructions=custom_instructions if custom_instructions else None
                        )
                        
                        result = asyncio.run(self.generator.generate_content(request))
                        
                        # Display results
                        st.success("✅ Content generated successfully!")
                        
                        # Main result
                        st.subheader("Generated Content")
                        st.write(result.generated_text)
                        
                        # Metadata
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Word Count", result.word_count)
                        
                        with col2:
                            st.metric("Confidence", f"{result.confidence_score:.1%}")
                        
                        with col3:
                            st.metric("Generation Time", f"{result.generation_time:.2f}s")
                        
                        with col4:
                            model_used = result.metadata.get('model_used', 'unknown')
                            st.metric("Model", model_used.title())
                        
                        # Suggestions
                        if result.suggestions:
                            st.subheader("💡 Suggestions")
                            for suggestion in result.suggestions:
                                st.write(f"• {suggestion}")
                        
                        # Alternatives
                        if result.alternatives:
                            st.subheader("🔄 Alternatives")
                            for i, alternative in enumerate(result.alternatives, 1):
                                with st.expander(f"Alternative {i}"):
                                    st.write(alternative)
                        
                        # Copy to clipboard button
                        st.code(result.generated_text, language=None)
                        
                    except Exception as e:
                        st.error(f"❌ Error generating content: {e}")
    
    def render_podcast_generator(self):
        """Render podcast-specific content generator"""
        st.header("🎙️ Podcast Content Generator")
        
        # Podcast details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_name = st.text_input("Show Name", placeholder="My Awesome Podcast")
        
        with col2:
            host_name = st.text_input("Host Name", placeholder="John Doe")
        
        with col3:
            episode_number = st.number_input("Episode Number", min_value=1, value=1)
        
        # Transcript input
        transcript = st.text_area(
            "Episode Transcript",
            height=300,
            placeholder="Paste your episode transcript here..."
        )
        
        if st.button("🎙️ Generate Intro & Outro", disabled=not transcript):
            if transcript:
                with st.spinner("Generating podcast intro and outro..."):
                    try:
                        results = self.generator.generate_podcast_intro_outro(
                            transcript=transcript,
                            show_name=show_name,
                            host_name=host_name,
                            episode_number=episode_number if episode_number > 0 else None
                        )
                        
                        # Display intro
                        st.subheader("🎵 Podcast Intro")
                        st.write(results['intro'].generated_text)
                        st.code(results['intro'].generated_text, language=None)
                        
                        # Display outro
                        st.subheader("🎵 Podcast Outro")
                        st.write(results['outro'].generated_text)
                        st.code(results['outro'].generated_text, language=None)
                        
                        # Statistics
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Intro Word Count", results['intro'].word_count)
                            st.metric("Intro Confidence", f"{results['intro'].confidence_score:.1%}")
                        
                        with col2:
                            st.metric("Outro Word Count", results['outro'].word_count)
                            st.metric("Outro Confidence", f"{results['outro'].confidence_score:.1%}")
                        
                    except Exception as e:
                        st.error(f"❌ Error generating podcast content: {e}")
    
    def render_content_optimizer(self):
        """Render content optimization interface"""
        st.header("⚡ Content Optimizer")
        
        # Input content
        original_content = st.text_area(
            "Content to Optimize",
            height=200,
            placeholder="Enter the content you want to optimize..."
        )
        
        # Optimization settings
        col1, col2 = st.columns(2)
        
        with col1:
            target_audience = st.selectbox(
                "Target Audience",
                options=[e.value for e in AudienceType],
                format_func=lambda x: x.title(),
                key="optimizer_audience"
            )
        
        with col2:
            optimization_focus = st.selectbox(
                "Optimization Focus",
                options=["readability", "engagement", "clarity", "professionalism"],
                help="What aspect should be optimized?"
            )
        
        if st.button("⚡ Optimize Content", disabled=not original_content):
            if original_content:
                with st.spinner("Optimizing content..."):
                    try:
                        optimization = self.generator.optimize_content_for_audience(
                            content=original_content,
                            target_audience=target_audience,
                            optimization_focus=optimization_focus
                        )
                        
                        # Display results
                        st.success("✅ Content optimized successfully!")
                        
                        # Before/After comparison
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📝 Original Content")
                            st.write(optimization.original_text)
                        
                        with col2:
                            st.subheader("✨ Optimized Content")
                            st.write(optimization.optimized_text)
                        
                        # Improvements
                        st.subheader("🔧 Improvements Made")
                        for improvement in optimization.improvements:
                            st.write(f"• {improvement}")
                        
                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Readability Score", f"{optimization.readability_score:.1f}/100")
                        
                        with col2:
                            st.metric("Target Audience", optimization.target_audience.title())
                        
                        with col3:
                            st.metric("Optimization Type", optimization.optimization_type.title())
                        
                        # Copy optimized content
                        st.code(optimization.optimized_text, language=None)
                        
                    except Exception as e:
                        st.error(f"❌ Error optimizing content: {e}")
    
    def render_batch_generator(self):
        """Render batch content generation interface"""
        st.header("📦 Batch Content Generator")
        
        st.write("Generate multiple types of content from the same source material.")
        
        # Source content
        source_content = st.text_area(
            "Source Content",
            height=200,
            placeholder="Enter your source content here..."
        )
        
        # Content types to generate
        st.subheader("Select Content Types to Generate")
        
        content_types = []
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.checkbox("Podcast Intro"):
                content_types.append(ContentType.PODCAST_INTRO.value)
            if st.checkbox("Podcast Outro"):
                content_types.append(ContentType.PODCAST_OUTRO.value)
        
        with col2:
            if st.checkbox("FAQ"):
                content_types.append(ContentType.FAQ.value)
            if st.checkbox("Tags"):
                content_types.append(ContentType.TAGS.value)
        
        with col3:
            if st.checkbox("Expanded Text"):
                content_types.append(ContentType.EXPANDED_TEXT.value)
            if st.checkbox("Content Optimization"):
                content_types.append(ContentType.OPTIMIZATION.value)
        
        # Common settings
        col1, col2 = st.columns(2)
        
        with col1:
            batch_audience = st.selectbox(
                "Target Audience",
                options=[e.value for e in AudienceType],
                format_func=lambda x: x.title(),
                key="batch_audience"
            )
        
        with col2:
            batch_tone = st.selectbox(
                "Tone",
                options=[e.value for e in ContentTone],
                format_func=lambda x: x.title(),
                key="batch_tone"
            )
        
        if st.button("🚀 Generate All Selected Content", disabled=not source_content or not content_types):
            if source_content and content_types:
                with st.spinner(f"Generating {len(content_types)} types of content..."):
                    try:
                        # Create requests
                        requests = []
                        for content_type in content_types:
                            request = ContentGenerationRequest(
                                content_type=content_type,
                                source_text=source_content,
                                target_audience=batch_audience,
                                tone=batch_tone,
                                length="medium"
                            )
                            requests.append(request)
                        
                        # Generate all content
                        results = self.generator.batch_generate_content(requests)
                        
                        # Display results
                        st.success(f"✅ Generated {len(results)} pieces of content!")
                        
                        for result in results:
                            st.subheader(f"📄 {result.content_type.replace('_', ' ').title()}")
                            
                            if result.metadata.get('error'):
                                st.error(result.generated_text)
                            else:
                                st.write(result.generated_text)
                                
                                # Metrics
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Words", result.word_count)
                                
                                with col2:
                                    st.metric("Confidence", f"{result.confidence_score:.1%}")
                                
                                with col3:
                                    st.metric("Time", f"{result.generation_time:.2f}s")
                                
                                # Copy button
                                with st.expander("Copy Content"):
                                    st.code(result.generated_text, language=None)
                            
                            st.markdown("---")
                        
                    except Exception as e:
                        st.error(f"❌ Error in batch generation: {e}")
    
    def render_statistics(self):
        """Render generation statistics"""
        st.header("📊 Generation Statistics")
        
        stats = self.generator.get_generation_statistics()
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Generations", stats['total_generations'])
        
        with col2:
            st.metric("API Status", "Connected" if stats['api_available'] else "Offline")
        
        with col3:
            st.metric("NLP Status", "Available" if stats['nlp_available'] else "Limited")
        
        with col4:
            st.metric("Content Types", len(stats['supported_content_types']))
        
        # Usage by content type
        if stats['by_content_type']:
            st.subheader("Usage by Content Type")
            
            usage_data = []
            for content_type, count in stats['by_content_type'].items():
                usage_data.append({
                    'Content Type': content_type.replace('_', ' ').title(),
                    'Generations': count
                })
            
            df = pd.DataFrame(usage_data)
            st.bar_chart(df.set_index('Content Type'))
        
        # Supported content types
        st.subheader("Supported Content Types")
        for content_type in stats['supported_content_types']:
            st.write(f"• {content_type.replace('_', ' ').title()}")
    
    def run(self):
        """Run the Streamlit application"""
        st.set_page_config(
            page_title="AI Content Generation",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Render header
        self.render_header()
        
        # Sidebar navigation
        st.sidebar.title("🤖 Content Generation")
        
        page = st.sidebar.selectbox(
            "Select Tool",
            [
                "Content Generator",
                "Podcast Generator", 
                "Content Optimizer",
                "Batch Generator",
                "Statistics"
            ]
        )
        
        # Render selected page
        if page == "Content Generator":
            self.render_content_generator()
        elif page == "Podcast Generator":
            self.render_podcast_generator()
        elif page == "Content Optimizer":
            self.render_content_optimizer()
        elif page == "Batch Generator":
            self.render_batch_generator()
        elif page == "Statistics":
            self.render_statistics()
        
        # Footer
        st.markdown("---")
        st.markdown("**AI-Powered Content Generation System** - Transform your content with AI")

def main():
    """Main function to run the UI"""
    ui = ContentGenerationUI()
    ui.run()

if __name__ == "__main__":
    main()