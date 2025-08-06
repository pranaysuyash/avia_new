"""
Knowledge Base and Help Center System

Self-service knowledge base with articles, FAQs, and intelligent search
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator
import asyncio
from collections import defaultdict
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ArticleType(str, Enum):
    """Knowledge base article types"""
    GUIDE = "guide"
    TUTORIAL = "tutorial"
    FAQ = "faq"
    TROUBLESHOOTING = "troubleshooting"
    REFERENCE = "reference"
    VIDEO = "video"
    RELEASE_NOTES = "release_notes"
    API_DOCS = "api_docs"

class ArticleStatus(str, Enum):
    """Article publication status"""
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    OUTDATED = "outdated"

class ContentDifficulty(str, Enum):
    """Content difficulty level"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class SearchResult(BaseModel):
    """Search result model"""
    article_id: str
    title: str
    excerpt: str
    relevance_score: float
    article_type: ArticleType
    url: str
    highlights: List[str] = []

class ArticleSection(BaseModel):
    """Article section/chapter"""
    section_id: str
    title: str
    content: str
    order: int
    
    # Media
    images: List[str] = []
    videos: List[str] = []
    code_samples: List[Dict[str, str]] = []
    
    # Navigation
    subsections: List['ArticleSection'] = []

class RelatedResource(BaseModel):
    """Related article or resource"""
    resource_id: str
    resource_type: str  # article, video, external
    title: str
    url: str
    relevance: float = 0.8

class KnowledgeArticle(BaseModel):
    """Knowledge base article"""
    article_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Content
    title: str
    slug: str
    summary: str
    content: str
    sections: List[ArticleSection] = []
    
    # Metadata
    article_type: ArticleType
    status: ArticleStatus = ArticleStatus.DRAFT
    difficulty: ContentDifficulty = ContentDifficulty.BEGINNER
    
    # Organization
    category: str
    subcategory: Optional[str]
    tags: List[str] = []
    
    # Author and review
    author_id: str
    author_name: str
    reviewers: List[str] = []
    last_reviewed: Optional[datetime]
    
    # SEO
    meta_description: str
    keywords: List[str] = []
    
    # Engagement
    view_count: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    avg_time_on_page: float = 0
    
    # Related content
    related_articles: List[str] = []
    prerequisites: List[str] = []
    
    # Versioning
    version: str = "1.0"
    changelog: List[Dict[str, Any]] = []

class FAQ(BaseModel):
    """Frequently Asked Question"""
    faq_id: str
    question: str
    answer: str
    category: str
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Engagement
    view_count: int = 0
    helpful_count: int = 0
    
    # Related
    related_articles: List[str] = []
    related_faqs: List[str] = []

class VideoTutorial(BaseModel):
    """Video tutorial resource"""
    video_id: str
    title: str
    description: str
    duration_seconds: int
    
    # Video details
    video_url: str
    thumbnail_url: str
    transcript: Optional[str]
    
    # Metadata
    category: str
    tags: List[str] = []
    difficulty: ContentDifficulty
    
    # Chapters
    chapters: List[Dict[str, Any]] = []  # timestamp, title, description
    
    # Engagement
    view_count: int = 0
    completion_rate: float = 0

class SearchQuery(BaseModel):
    """Search query with context"""
    query_id: str
    query_text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Context
    user_id: Optional[str]
    session_id: str
    source: str  # search_box, chatbot, api
    
    # Results
    results_returned: int = 0
    results_clicked: List[str] = []
    
    # Feedback
    was_helpful: Optional[bool]
    selected_result: Optional[str]

class KnowledgeBase:
    """Main knowledge base system"""
    
    def __init__(self):
        self.articles: Dict[str, KnowledgeArticle] = {}
        self.faqs: Dict[str, FAQ] = {}
        self.videos: Dict[str, VideoTutorial] = {}
        self.search_queries: Dict[str, SearchQuery] = {}
        
        # Indexes
        self.articles_by_category: Dict[str, Set[str]] = defaultdict(set)
        self.articles_by_tag: Dict[str, Set[str]] = defaultdict(set)
        self.articles_by_type: Dict[ArticleType, Set[str]] = defaultdict(set)
        
        # Search engine
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 3)
        )
        self.search_index_built = False
        self.document_vectors = None
        self.indexed_articles: List[str] = []
        
        # Popular content cache
        self.popular_articles_cache: List[str] = []
        self.trending_searches_cache: List[str] = []
        
        # Initialize sample content
        self._init_sample_content()
    
    def _init_sample_content(self):
        """Initialize with sample content"""
        # Getting started guide
        getting_started = KnowledgeArticle(
            article_id="article_getting_started",
            title="Getting Started with Transcription Platform",
            slug="getting-started",
            summary="Learn how to set up and use the transcription platform",
            content="Welcome to the Transcription Platform! This guide will help you get started...",
            article_type=ArticleType.GUIDE,
            status=ArticleStatus.PUBLISHED,
            category="Getting Started",
            author_id="system",
            author_name="Documentation Team",
            meta_description="Complete guide to getting started with our transcription platform",
            keywords=["getting started", "setup", "quickstart", "tutorial"]
        )
        self.articles[getting_started.article_id] = getting_started
        
        # FAQ samples
        faq1 = FAQ(
            faq_id="faq_file_formats",
            question="What audio/video file formats are supported?",
            answer="We support MP3, WAV, MP4, AVI, MOV, and many other common formats up to 2GB in size.",
            category="Technical"
        )
        self.faqs[faq1.faq_id] = faq1
    
    def create_article(
        self,
        title: str,
        content: str,
        article_type: ArticleType,
        category: str,
        author_id: str,
        author_name: str,
        summary: Optional[str] = None,
        tags: List[str] = None
    ) -> KnowledgeArticle:
        """Create new knowledge base article"""
        # Generate slug
        slug = self._generate_slug(title)
        
        # Auto-generate summary if not provided
        if not summary:
            summary = self._generate_summary(content)
        
        # Create article
        article = KnowledgeArticle(
            article_id=f"article_{datetime.utcnow().timestamp()}",
            title=title,
            slug=slug,
            summary=summary,
            content=content,
            article_type=article_type,
            category=category,
            author_id=author_id,
            author_name=author_name,
            meta_description=summary[:160],
            keywords=self._extract_keywords(content),
            tags=tags or []
        )
        
        # Store article
        self.articles[article.article_id] = article
        
        # Update indexes
        self.articles_by_category[category].add(article.article_id)
        self.articles_by_type[article_type].add(article.article_id)
        for tag in article.tags:
            self.articles_by_tag[tag].add(article.article_id)
        
        # Mark search index for rebuild
        self.search_index_built = False
        
        return article
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title"""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """Generate summary from content"""
        # Simple approach: take first paragraph
        paragraphs = content.split('\n\n')
        if paragraphs:
            summary = paragraphs[0]
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            return summary
        return content[:max_length]
    
    def _extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from content"""
        # In production, use NLP for better keyword extraction
        words = re.findall(r'\b[a-z]+\b', content.lower())
        word_freq = defaultdict(int)
        
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] += 1
        
        # Get top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in keywords[:max_keywords]]
    
    def update_article(
        self,
        article_id: str,
        updates: Dict[str, Any],
        reviewer_id: Optional[str] = None
    ) -> bool:
        """Update existing article"""
        article = self.articles.get(article_id)
        if not article:
            return False
        
        # Track changes
        changelog_entry = {
            "version": article.version,
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": updates.get("author_id", article.author_id),
            "changes": list(updates.keys())
        }
        
        # Update fields
        for field, value in updates.items():
            if hasattr(article, field):
                setattr(article, field, value)
        
        # Update metadata
        article.updated_at = datetime.utcnow()
        if reviewer_id:
            article.reviewers.append(reviewer_id)
            article.last_reviewed = datetime.utcnow()
        
        # Increment version
        version_parts = article.version.split('.')
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        article.version = '.'.join(version_parts)
        
        # Add to changelog
        article.changelog.append(changelog_entry)
        
        # Mark search index for rebuild
        self.search_index_built = False
        
        return True
    
    def build_search_index(self):
        """Build or rebuild search index"""
        if not self.articles:
            return
        
        # Prepare documents
        documents = []
        self.indexed_articles = []
        
        for article_id, article in self.articles.items():
            if article.status == ArticleStatus.PUBLISHED:
                # Combine searchable content
                searchable_text = f"{article.title} {article.summary} {article.content} {' '.join(article.tags)} {' '.join(article.keywords)}"
                documents.append(searchable_text)
                self.indexed_articles.append(article_id)
        
        if documents:
            # Build TF-IDF vectors
            self.document_vectors = self.vectorizer.fit_transform(documents)
            self.search_index_built = True
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[SearchResult]:
        """Search knowledge base"""
        # Record query
        search_query = SearchQuery(
            query_id=f"query_{datetime.utcnow().timestamp()}",
            query_text=query,
            user_id=user_id,
            session_id=session_id or "anonymous",
            source="search_box"
        )
        self.search_queries[search_query.query_id] = search_query
        
        # Build index if needed
        if not self.search_index_built:
            self.build_search_index()
        
        if not self.indexed_articles:
            return []
        
        # Vectorize query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Get top results
        top_indices = similarities.argsort()[-limit*2:][::-1]  # Get extra for filtering
        
        results = []
        for idx in top_indices:
            if idx < len(self.indexed_articles):
                article_id = self.indexed_articles[idx]
                article = self.articles[article_id]
                
                # Apply filters
                if filters:
                    if filters.get("category") and article.category != filters["category"]:
                        continue
                    if filters.get("type") and article.article_type != filters["type"]:
                        continue
                    if filters.get("difficulty") and article.difficulty != filters["difficulty"]:
                        continue
                
                # Create search result
                result = SearchResult(
                    article_id=article_id,
                    title=article.title,
                    excerpt=article.summary,
                    relevance_score=float(similarities[idx]),
                    article_type=article.article_type,
                    url=f"/help/{article.category.lower()}/{article.slug}",
                    highlights=self._generate_highlights(article.content, query)
                )
                results.append(result)
                
                if len(results) >= limit:
                    break
        
        # Update query with results
        search_query.results_returned = len(results)
        
        # Also search FAQs
        faq_results = self._search_faqs(query, limit=5)
        
        # Combine and sort by relevance
        all_results = results + faq_results
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return all_results[:limit]
    
    def _generate_highlights(self, content: str, query: str, context_words: int = 10) -> List[str]:
        """Generate highlighted snippets from content"""
        highlights = []
        query_words = query.lower().split()
        sentences = content.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in query_words):
                # Extract context around matched words
                words = sentence.split()
                for i, word in enumerate(words):
                    if any(qw in word.lower() for qw in query_words):
                        start = max(0, i - context_words)
                        end = min(len(words), i + context_words + 1)
                        highlight = ' '.join(words[start:end])
                        if start > 0:
                            highlight = '...' + highlight
                        if end < len(words):
                            highlight = highlight + '...'
                        highlights.append(highlight)
                        break
                
                if len(highlights) >= 3:
                    break
        
        return highlights
    
    def _search_faqs(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Search FAQs"""
        results = []
        query_lower = query.lower()
        
        for faq in self.faqs.values():
            # Simple keyword matching for FAQs
            score = 0
            if query_lower in faq.question.lower():
                score += 0.8
            if query_lower in faq.answer.lower():
                score += 0.5
            
            # Check individual words
            for word in query_lower.split():
                if word in faq.question.lower():
                    score += 0.3
                if word in faq.answer.lower():
                    score += 0.2
            
            if score > 0:
                result = SearchResult(
                    article_id=faq.faq_id,
                    title=faq.question,
                    excerpt=faq.answer[:200] + "..." if len(faq.answer) > 200 else faq.answer,
                    relevance_score=score,
                    article_type=ArticleType.FAQ,
                    url=f"/help/faq#{faq.faq_id}"
                )
                results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]
    
    def get_popular_articles(self, limit: int = 10) -> List[KnowledgeArticle]:
        """Get most popular articles"""
        published_articles = [
            article for article in self.articles.values()
            if article.status == ArticleStatus.PUBLISHED
        ]
        
        # Sort by views and helpfulness
        published_articles.sort(
            key=lambda a: (a.view_count * 0.7 + a.helpful_count * 0.3),
            reverse=True
        )
        
        return published_articles[:limit]
    
    def get_recent_articles(self, limit: int = 10) -> List[KnowledgeArticle]:
        """Get recently updated articles"""
        published_articles = [
            article for article in self.articles.values()
            if article.status == ArticleStatus.PUBLISHED
        ]
        
        # Sort by update date
        published_articles.sort(
            key=lambda a: a.updated_at,
            reverse=True
        )
        
        return published_articles[:limit]
    
    def get_related_articles(self, article_id: str, limit: int = 5) -> List[KnowledgeArticle]:
        """Get articles related to given article"""
        article = self.articles.get(article_id)
        if not article:
            return []
        
        related = []
        
        # First, get explicitly related articles
        for related_id in article.related_articles:
            if related_id in self.articles:
                related.append(self.articles[related_id])
        
        # Then, find articles with similar tags
        for tag in article.tags:
            for other_id in self.articles_by_tag[tag]:
                if other_id != article_id and other_id not in article.related_articles:
                    related.append(self.articles[other_id])
        
        # Finally, find articles in same category
        for other_id in self.articles_by_category[article.category]:
            if other_id != article_id and self.articles[other_id] not in related:
                related.append(self.articles[other_id])
        
        # Remove duplicates and limit
        seen = set()
        unique_related = []
        for art in related:
            if art.article_id not in seen:
                seen.add(art.article_id)
                unique_related.append(art)
        
        return unique_related[:limit]
    
    def record_article_view(self, article_id: str, session_id: str, time_on_page: float):
        """Record article view analytics"""
        article = self.articles.get(article_id)
        if article:
            article.view_count += 1
            # Update average time on page
            total_time = article.avg_time_on_page * (article.view_count - 1) + time_on_page
            article.avg_time_on_page = total_time / article.view_count
    
    def record_article_feedback(self, article_id: str, helpful: bool, user_id: Optional[str] = None):
        """Record article helpfulness feedback"""
        article = self.articles.get(article_id)
        if article:
            if helpful:
                article.helpful_count += 1
            else:
                article.not_helpful_count += 1
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query"""
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Search in article titles
        for article in self.articles.values():
            if partial_lower in article.title.lower():
                suggestions.append(article.title)
        
        # Search in FAQ questions
        for faq in self.faqs.values():
            if partial_lower in faq.question.lower():
                suggestions.append(faq.question)
        
        # Search in recent queries
        recent_queries = sorted(
            self.search_queries.values(),
            key=lambda q: q.timestamp,
            reverse=True
        )[:100]
        
        for query in recent_queries:
            if partial_lower in query.query_text.lower() and query.was_helpful:
                suggestions.append(query.query_text)
        
        # Remove duplicates and return top suggestions
        seen = set()
        unique_suggestions = []
        for sugg in suggestions:
            if sugg.lower() not in seen:
                seen.add(sugg.lower())
                unique_suggestions.append(sugg)
        
        return unique_suggestions[:limit]
    
    def generate_help_metrics(self) -> Dict[str, Any]:
        """Generate knowledge base metrics"""
        metrics = {
            "total_articles": len(self.articles),
            "published_articles": len([a for a in self.articles.values() if a.status == ArticleStatus.PUBLISHED]),
            "total_faqs": len(self.faqs),
            "total_videos": len(self.videos),
            "total_searches": len(self.search_queries),
            "articles_by_type": defaultdict(int),
            "articles_by_category": defaultdict(int),
            "search_success_rate": 0,
            "avg_helpfulness_score": 0,
            "popular_search_terms": []
        }
        
        # Articles by type
        for article in self.articles.values():
            metrics["articles_by_type"][article.article_type.value] += 1
            metrics["articles_by_category"][article.category] += 1
        
        # Search success rate
        successful_searches = len([
            q for q in self.search_queries.values()
            if q.results_clicked or q.was_helpful
        ])
        if self.search_queries:
            metrics["search_success_rate"] = (successful_searches / len(self.search_queries)) * 100
        
        # Average helpfulness
        total_feedback = sum(
            a.helpful_count + a.not_helpful_count
            for a in self.articles.values()
        )
        total_helpful = sum(a.helpful_count for a in self.articles.values())
        
        if total_feedback > 0:
            metrics["avg_helpfulness_score"] = (total_helpful / total_feedback) * 100
        
        # Popular search terms
        term_frequency = defaultdict(int)
        for query in self.search_queries.values():
            for term in query.query_text.lower().split():
                if len(term) > 3:  # Skip short words
                    term_frequency[term] += 1
        
        popular_terms = sorted(term_frequency.items(), key=lambda x: x[1], reverse=True)
        metrics["popular_search_terms"] = [term for term, _ in popular_terms[:10]]
        
        return dict(metrics)

# Example usage
if __name__ == "__main__":
    # Initialize knowledge base
    kb = KnowledgeBase()
    
    # Create articles
    api_guide = kb.create_article(
        title="API Authentication Guide",
        content="""
        # API Authentication Guide
        
        This guide explains how to authenticate with our API using OAuth 2.0.
        
        ## Getting Started
        
        First, you need to register your application to get client credentials...
        
        ## Authentication Flow
        
        1. Request authorization code
        2. Exchange code for access token
        3. Use token in API requests
        
        ## Code Examples
        
        Here's how to authenticate using Python...
        """,
        article_type=ArticleType.GUIDE,
        category="API Documentation",
        author_id="tech_writer_01",
        author_name="Tech Writer",
        tags=["api", "authentication", "oauth", "security"]
    )
    
    print(f"Created article: {api_guide.title}")
    
    # Search knowledge base
    results = kb.search("api authentication", limit=5)
    
    print("\nSearch Results:")
    for result in results:
        print(f"- {result.title} (Score: {result.relevance_score:.2f})")
        if result.highlights:
            print(f"  Highlight: {result.highlights[0]}")
    
    # Get popular articles
    popular = kb.get_popular_articles(5)
    print(f"\nPopular Articles: {len(popular)}")
    
    # Record feedback
    kb.record_article_feedback(api_guide.article_id, helpful=True)
    
    # Get metrics
    metrics = kb.generate_help_metrics()
    print(f"\nKnowledge Base Metrics:")
    print(f"Total articles: {metrics['total_articles']}")
    print(f"Published articles: {metrics['published_articles']}")
    print(f"Search success rate: {metrics['search_success_rate']:.1f}%")