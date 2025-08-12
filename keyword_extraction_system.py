#!/usr/bin/env python3
"""
Advanced Keyword and Phrase Extraction System
Implements RAKE, TF-IDF, topic modeling with LDA, phrase clustering,
and semantic grouping for comprehensive keyword extraction
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from enum import Enum
import numpy as np
from collections import Counter, defaultdict
import pandas as pd

# NLP libraries
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag

# Machine Learning
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE

# Topic Modeling
import gensim
from gensim import corpora, models
from gensim.models import Word2Vec, FastText, LdaModel, CoherenceModel
from gensim.models.phrases import Phrases, Phraser

# Advanced NLP
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from sentence_transformers import SentenceTransformer

# RAKE algorithm
from rake_nltk import Rake

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
except:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtractionMethod(Enum):
    """Keyword extraction methods"""
    RAKE = "rake"
    TFIDF = "tfidf"
    TEXTRANK = "textrank"
    LDA = "lda"
    NMF = "nmf"
    BERT = "bert"
    YAKE = "yake"
    KEYBERT = "keybert"


class KeywordType(Enum):
    """Types of keywords"""
    SINGLE = "single"
    BIGRAM = "bigram"
    TRIGRAM = "trigram"
    PHRASE = "phrase"
    ENTITY = "entity"
    TOPIC = "topic"


@dataclass
class Keyword:
    """Individual keyword or phrase"""
    text: str
    score: float
    frequency: int
    type: KeywordType
    positions: List[int] = field(default_factory=list)
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Topic:
    """Topic from topic modeling"""
    topic_id: int
    words: List[Tuple[str, float]]  # (word, weight)
    coherence_score: float
    documents: List[int] = field(default_factory=list)
    label: Optional[str] = None
    description: Optional[str] = None


@dataclass
class PhraseCluster:
    """Cluster of related phrases"""
    cluster_id: int
    phrases: List[str]
    centroid: Optional[np.ndarray] = None
    coherence: float = 0.0
    theme: Optional[str] = None


@dataclass
class KeywordExtractionResult:
    """Complete keyword extraction result"""
    keywords: List[Keyword]
    topics: List[Topic]
    clusters: List[PhraseCluster]
    trends: Dict[str, List[float]]  # Keyword trends over time
    statistics: Dict[str, Any]
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedKeywordExtractor:
    """Main keyword extraction system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize NLP models
        self._initialize_models()
        
        # Initialize extractors
        self.extractors = {}
        self._initialize_extractors()
        
        # Stopwords
        self.stopwords = set(stopwords.words('english'))
        self.custom_stopwords = set(self.config.get('custom_stopwords', []))
        self.stopwords.update(self.custom_stopwords)
        
        # Lemmatizer and stemmer
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        
    def _initialize_models(self):
        """Initialize NLP models"""
        try:
            # SpaCy model
            self.nlp = spacy.load("en_core_web_sm")
            
            # Sentence transformer for embeddings
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # BERT for keyword extraction
            if self.config.get('use_bert', False):
                self.bert_tokenizer = AutoTokenizer.from_pretrained(
                    'bert-base-uncased'
                )
                self.bert_model = AutoModel.from_pretrained(
                    'bert-base-uncased'
                )
            
            logger.info("NLP models initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
    
    def _initialize_extractors(self):
        """Initialize keyword extractors"""
        
        # RAKE extractor
        self.extractors['rake'] = Rake(
            stopwords=list(self.stopwords),
            punctuations='!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~',
            language='english',
            max_length=3,
            include_repeated_phrases=False
        )
        
        # TF-IDF vectorizer
        self.extractors['tfidf'] = TfidfVectorizer(
            max_features=100,
            stop_words=list(self.stopwords),
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.8
        )
        
        # Count vectorizer for LDA
        self.extractors['count'] = CountVectorizer(
            max_features=100,
            stop_words=list(self.stopwords),
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
    
    async def extract_keywords(
        self,
        text: Union[str, List[str]],
        methods: List[ExtractionMethod] = None,
        max_keywords: int = 20,
        include_entities: bool = True,
        include_topics: bool = True,
        cluster_phrases: bool = True
    ) -> KeywordExtractionResult:
        """Extract keywords using multiple methods"""
        
        import time
        start_time = time.time()
        
        # Default methods
        if methods is None:
            methods = [
                ExtractionMethod.RAKE,
                ExtractionMethod.TFIDF,
                ExtractionMethod.LDA
            ]
        
        # Prepare text
        if isinstance(text, list):
            documents = text
            full_text = ' '.join(text)
        else:
            documents = [text]
            full_text = text
        
        # Extract keywords with different methods
        all_keywords = []
        
        for method in methods:
            keywords = await self._extract_with_method(
                full_text,
                method,
                max_keywords
            )
            all_keywords.extend(keywords)
        
        # Extract named entities
        if include_entities:
            entities = self._extract_entities(full_text)
            all_keywords.extend(entities)
        
        # Remove duplicates and merge scores
        keywords = self._merge_keywords(all_keywords)
        
        # Sort by score and limit
        keywords = sorted(keywords, key=lambda k: k.score, reverse=True)[:max_keywords]
        
        # Extract topics
        topics = []
        if include_topics and len(documents) > 1:
            topics = await self._extract_topics(documents)
        
        # Cluster phrases
        clusters = []
        if cluster_phrases and len(keywords) > 5:
            clusters = await self._cluster_phrases(keywords)
        
        # Analyze trends (if multiple documents)
        trends = {}
        if len(documents) > 1:
            trends = self._analyze_keyword_trends(documents, keywords)
        
        # Calculate statistics
        statistics = self._calculate_statistics(
            keywords,
            topics,
            clusters,
            full_text
        )
        
        processing_time = time.time() - start_time
        
        return KeywordExtractionResult(
            keywords=keywords,
            topics=topics,
            clusters=clusters,
            trends=trends,
            statistics=statistics,
            processing_time=processing_time,
            metadata={
                'methods_used': [m.value for m in methods],
                'document_count': len(documents),
                'total_words': len(full_text.split())
            }
        )
    
    async def _extract_with_method(
        self,
        text: str,
        method: ExtractionMethod,
        max_keywords: int
    ) -> List[Keyword]:
        """Extract keywords using specific method"""
        
        keywords = []
        
        if method == ExtractionMethod.RAKE:
            keywords = self._extract_rake(text, max_keywords)
            
        elif method == ExtractionMethod.TFIDF:
            keywords = self._extract_tfidf([text], max_keywords)
            
        elif method == ExtractionMethod.TEXTRANK:
            keywords = self._extract_textrank(text, max_keywords)
            
        elif method == ExtractionMethod.LDA:
            keywords = await self._extract_lda_keywords([text], max_keywords)
            
        elif method == ExtractionMethod.NMF:
            keywords = self._extract_nmf(text, max_keywords)
            
        elif method == ExtractionMethod.BERT:
            if hasattr(self, 'bert_model'):
                keywords = self._extract_bert(text, max_keywords)
        
        return keywords
    
    def _extract_rake(self, text: str, max_keywords: int) -> List[Keyword]:
        """Extract keywords using RAKE algorithm"""
        
        keywords = []
        
        try:
            rake = self.extractors['rake']
            rake.extract_keywords_from_text(text)
            
            # Get ranked phrases
            ranked_phrases = rake.get_ranked_phrases_with_scores()
            
            for score, phrase in ranked_phrases[:max_keywords]:
                # Determine keyword type
                word_count = len(phrase.split())
                if word_count == 1:
                    kw_type = KeywordType.SINGLE
                elif word_count == 2:
                    kw_type = KeywordType.BIGRAM
                elif word_count == 3:
                    kw_type = KeywordType.TRIGRAM
                else:
                    kw_type = KeywordType.PHRASE
                
                keywords.append(Keyword(
                    text=phrase,
                    score=score,
                    frequency=text.lower().count(phrase.lower()),
                    type=kw_type,
                    metadata={'method': 'RAKE'}
                ))
                
        except Exception as e:
            logger.error(f"RAKE extraction failed: {e}")
        
        return keywords
    
    def _extract_tfidf(self, documents: List[str], max_keywords: int) -> List[Keyword]:
        """Extract keywords using TF-IDF"""
        
        keywords = []
        
        try:
            vectorizer = self.extractors['tfidf']
            tfidf_matrix = vectorizer.fit_transform(documents)
            
            # Get feature names
            feature_names = vectorizer.get_feature_names_out()
            
            # Calculate average TF-IDF scores across documents
            avg_scores = tfidf_matrix.mean(axis=0).A1
            
            # Get top keywords
            top_indices = avg_scores.argsort()[-max_keywords:][::-1]
            
            for idx in top_indices:
                phrase = feature_names[idx]
                score = avg_scores[idx]
                
                # Determine type
                word_count = len(phrase.split())
                if word_count == 1:
                    kw_type = KeywordType.SINGLE
                elif word_count == 2:
                    kw_type = KeywordType.BIGRAM
                else:
                    kw_type = KeywordType.TRIGRAM
                
                keywords.append(Keyword(
                    text=phrase,
                    score=score,
                    frequency=sum(doc.lower().count(phrase.lower()) for doc in documents),
                    type=kw_type,
                    metadata={'method': 'TF-IDF'}
                ))
                
        except Exception as e:
            logger.error(f"TF-IDF extraction failed: {e}")
        
        return keywords
    
    def _extract_textrank(self, text: str, max_keywords: int) -> List[Keyword]:
        """Extract keywords using TextRank algorithm"""
        
        keywords = []
        
        try:
            # Use SpaCy for TextRank
            doc = self.nlp(text)
            
            # Build word graph
            word_graph = defaultdict(list)
            words = []
            
            for token in doc:
                if not token.is_stop and not token.is_punct and len(token.text) > 2:
                    words.append(token.text.lower())
            
            # Create co-occurrence graph
            window_size = 5
            for i, word in enumerate(words):
                for j in range(i + 1, min(i + window_size, len(words))):
                    word_graph[word].append(words[j])
                    word_graph[words[j]].append(word)
            
            # Calculate TextRank scores
            scores = self._calculate_textrank_scores(word_graph)
            
            # Get top keywords
            sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            for word, score in sorted_words[:max_keywords]:
                keywords.append(Keyword(
                    text=word,
                    score=score,
                    frequency=text.lower().count(word),
                    type=KeywordType.SINGLE,
                    metadata={'method': 'TextRank'}
                ))
                
        except Exception as e:
            logger.error(f"TextRank extraction failed: {e}")
        
        return keywords
    
    def _calculate_textrank_scores(
        self,
        graph: Dict[str, List[str]],
        damping: float = 0.85,
        iterations: int = 100
    ) -> Dict[str, float]:
        """Calculate TextRank scores for word graph"""
        
        # Initialize scores
        scores = {word: 1.0 for word in graph}
        
        # Iterate to convergence
        for _ in range(iterations):
            new_scores = {}
            
            for word in graph:
                rank = (1 - damping)
                
                for neighbor in graph[word]:
                    if neighbor in scores:
                        rank += damping * scores[neighbor] / len(graph[neighbor])
                
                new_scores[word] = rank
            
            scores = new_scores
        
        return scores
    
    async def _extract_lda_keywords(
        self,
        documents: List[str],
        max_keywords: int
    ) -> List[Keyword]:
        """Extract keywords using LDA topic modeling"""
        
        keywords = []
        
        try:
            # Vectorize documents
            vectorizer = self.extractors['count']
            doc_term_matrix = vectorizer.fit_transform(documents)
            
            # Fit LDA model
            n_topics = min(10, len(documents))
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=10
            )
            lda.fit(doc_term_matrix)
            
            # Get feature names
            feature_names = vectorizer.get_feature_names_out()
            
            # Extract top words from each topic
            topic_words = set()
            for topic_idx, topic in enumerate(lda.components_):
                top_indices = topic.argsort()[-10:][::-1]
                
                for idx in top_indices:
                    word = feature_names[idx]
                    score = topic[idx] / topic.sum()
                    topic_words.add((word, score))
            
            # Convert to keywords
            sorted_words = sorted(topic_words, key=lambda x: x[1], reverse=True)
            
            for word, score in sorted_words[:max_keywords]:
                keywords.append(Keyword(
                    text=word,
                    score=score,
                    frequency=sum(doc.lower().count(word) for doc in documents),
                    type=KeywordType.TOPIC,
                    metadata={'method': 'LDA'}
                ))
                
        except Exception as e:
            logger.error(f"LDA extraction failed: {e}")
        
        return keywords
    
    def _extract_nmf(self, text: str, max_keywords: int) -> List[Keyword]:
        """Extract keywords using Non-negative Matrix Factorization"""
        
        keywords = []
        
        try:
            # Prepare documents
            sentences = sent_tokenize(text)
            
            if len(sentences) > 1:
                # Vectorize
                vectorizer = TfidfVectorizer(
                    max_features=100,
                    stop_words=list(self.stopwords),
                    ngram_range=(1, 2)
                )
                tfidf_matrix = vectorizer.fit_transform(sentences)
                
                # Apply NMF
                nmf = NMF(n_components=min(5, len(sentences)), random_state=42)
                nmf.fit(tfidf_matrix)
                
                # Get feature names
                feature_names = vectorizer.get_feature_names_out()
                
                # Extract top words from components
                component_words = set()
                
                for component in nmf.components_:
                    top_indices = component.argsort()[-10:][::-1]
                    
                    for idx in top_indices:
                        word = feature_names[idx]
                        score = component[idx]
                        component_words.add((word, score))
                
                # Sort and convert to keywords
                sorted_words = sorted(component_words, key=lambda x: x[1], reverse=True)
                
                for word, score in sorted_words[:max_keywords]:
                    keywords.append(Keyword(
                        text=word,
                        score=score,
                        frequency=text.lower().count(word),
                        type=KeywordType.TOPIC,
                        metadata={'method': 'NMF'}
                    ))
                    
        except Exception as e:
            logger.error(f"NMF extraction failed: {e}")
        
        return keywords
    
    def _extract_bert(self, text: str, max_keywords: int) -> List[Keyword]:
        """Extract keywords using BERT embeddings"""
        
        keywords = []
        
        try:
            # Tokenize text
            doc = self.nlp(text)
            
            # Extract candidate keywords (nouns and noun phrases)
            candidates = []
            for chunk in doc.noun_chunks:
                candidates.append(chunk.text.lower())
            
            # Get BERT embeddings for candidates
            embeddings = []
            for candidate in candidates[:50]:  # Limit for performance
                inputs = self.bert_tokenizer(
                    candidate,
                    return_tensors="pt",
                    truncation=True,
                    padding=True,
                    max_length=512
                )
                
                with torch.no_grad():
                    outputs = self.bert_model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                    embeddings.append(embedding)
            
            # Get document embedding
            doc_inputs = self.bert_tokenizer(
                text[:512],
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            )
            
            with torch.no_grad():
                doc_outputs = self.bert_model(**doc_inputs)
                doc_embedding = doc_outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            
            # Calculate similarity scores
            scores = []
            for i, embedding in enumerate(embeddings):
                similarity = cosine_similarity(
                    embedding.reshape(1, -1),
                    doc_embedding.reshape(1, -1)
                )[0, 0]
                scores.append((candidates[i], similarity))
            
            # Sort and create keywords
            scores.sort(key=lambda x: x[1], reverse=True)
            
            for phrase, score in scores[:max_keywords]:
                keywords.append(Keyword(
                    text=phrase,
                    score=score,
                    frequency=text.lower().count(phrase),
                    type=KeywordType.PHRASE,
                    metadata={'method': 'BERT'}
                ))
                
        except Exception as e:
            logger.error(f"BERT extraction failed: {e}")
        
        return keywords
    
    def _extract_entities(self, text: str) -> List[Keyword]:
        """Extract named entities as keywords"""
        
        keywords = []
        
        try:
            doc = self.nlp(text)
            
            # Count entity frequencies
            entity_freq = Counter()
            
            for ent in doc.ents:
                if ent.label_ not in ['DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']:
                    entity_freq[ent.text] += 1
            
            # Convert to keywords
            for entity, freq in entity_freq.most_common():
                keywords.append(Keyword(
                    text=entity,
                    score=freq / len(doc.ents) if doc.ents else 0,
                    frequency=freq,
                    type=KeywordType.ENTITY,
                    metadata={'entity_type': 'NAMED_ENTITY'}
                ))
                
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
        
        return keywords
    
    def _merge_keywords(self, keywords: List[Keyword]) -> List[Keyword]:
        """Merge duplicate keywords and combine scores"""
        
        merged = {}
        
        for keyword in keywords:
            text_lower = keyword.text.lower()
            
            if text_lower in merged:
                # Merge scores (weighted average)
                existing = merged[text_lower]
                total_weight = existing.frequency + keyword.frequency
                
                if total_weight > 0:
                    existing.score = (
                        (existing.score * existing.frequency + 
                         keyword.score * keyword.frequency) / total_weight
                    )
                
                existing.frequency += keyword.frequency
                
                # Merge metadata
                if 'methods' not in existing.metadata:
                    existing.metadata['methods'] = []
                
                if 'method' in keyword.metadata:
                    existing.metadata['methods'].append(keyword.metadata['method'])
                    
            else:
                merged[text_lower] = keyword
        
        return list(merged.values())
    
    async def _extract_topics(
        self,
        documents: List[str],
        n_topics: int = 10
    ) -> List[Topic]:
        """Extract topics from documents using Gensim LDA"""
        
        topics = []
        
        try:
            # Preprocess documents
            processed_docs = []
            for doc in documents:
                # Tokenize and clean
                tokens = word_tokenize(doc.lower())
                tokens = [
                    self.lemmatizer.lemmatize(token)
                    for token in tokens
                    if token.isalnum() and token not in self.stopwords and len(token) > 2
                ]
                processed_docs.append(tokens)
            
            # Create dictionary and corpus
            dictionary = corpora.Dictionary(processed_docs)
            dictionary.filter_extremes(no_below=2, no_above=0.5)
            corpus = [dictionary.doc2bow(doc) for doc in processed_docs]
            
            # Train LDA model
            lda_model = LdaModel(
                corpus=corpus,
                id2word=dictionary,
                num_topics=n_topics,
                random_state=42,
                passes=10,
                alpha='auto',
                per_word_topics=True
            )
            
            # Calculate coherence
            coherence_model = CoherenceModel(
                model=lda_model,
                texts=processed_docs,
                dictionary=dictionary,
                coherence='c_v'
            )
            coherence_score = coherence_model.get_coherence()
            
            # Extract topics
            for topic_id in range(n_topics):
                # Get top words for topic
                word_weights = lda_model.show_topic(topic_id, topn=10)
                
                # Find documents with this topic
                doc_topics = []
                for doc_id, doc_corpus in enumerate(corpus):
                    doc_topic_dist = lda_model[doc_corpus]
                    for topic, prob in doc_topic_dist[0]:
                        if topic == topic_id and prob > 0.2:
                            doc_topics.append(doc_id)
                
                # Generate topic label (most representative words)
                label = ' '.join([word for word, _ in word_weights[:3]])
                
                topics.append(Topic(
                    topic_id=topic_id,
                    words=word_weights,
                    coherence_score=coherence_score,
                    documents=doc_topics,
                    label=label,
                    description=f"Topic characterized by: {label}"
                ))
                
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
        
        return topics
    
    async def _cluster_phrases(
        self,
        keywords: List[Keyword],
        n_clusters: Optional[int] = None
    ) -> List[PhraseCluster]:
        """Cluster related phrases using embeddings"""
        
        clusters = []
        
        try:
            # Get phrase embeddings
            phrases = [kw.text for kw in keywords]
            embeddings = self.sentence_model.encode(phrases)
            
            # Determine optimal number of clusters if not specified
            if n_clusters is None:
                n_clusters = min(5, max(2, len(phrases) // 5))
            
            # Perform clustering
            if len(phrases) >= n_clusters:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = kmeans.fit_predict(embeddings)
                
                # Group phrases by cluster
                cluster_groups = defaultdict(list)
                for i, label in enumerate(cluster_labels):
                    cluster_groups[label].append(phrases[i])
                
                # Create cluster objects
                for cluster_id, cluster_phrases in cluster_groups.items():
                    # Calculate cluster coherence
                    cluster_embeddings = [
                        embeddings[i] for i, label in enumerate(cluster_labels)
                        if label == cluster_id
                    ]
                    
                    if cluster_embeddings:
                        centroid = np.mean(cluster_embeddings, axis=0)
                        
                        # Calculate average pairwise similarity as coherence
                        similarities = []
                        for i in range(len(cluster_embeddings)):
                            for j in range(i + 1, len(cluster_embeddings)):
                                sim = cosine_similarity(
                                    cluster_embeddings[i].reshape(1, -1),
                                    cluster_embeddings[j].reshape(1, -1)
                                )[0, 0]
                                similarities.append(sim)
                        
                        coherence = np.mean(similarities) if similarities else 0
                        
                        # Determine theme (most representative phrase)
                        distances = [
                            cosine_similarity(
                                emb.reshape(1, -1),
                                centroid.reshape(1, -1)
                            )[0, 0]
                            for emb in cluster_embeddings
                        ]
                        theme_idx = np.argmax(distances)
                        theme = cluster_phrases[theme_idx]
                        
                        clusters.append(PhraseCluster(
                            cluster_id=int(cluster_id),
                            phrases=cluster_phrases,
                            centroid=centroid,
                            coherence=float(coherence),
                            theme=theme
                        ))
                        
        except Exception as e:
            logger.error(f"Phrase clustering failed: {e}")
        
        return clusters
    
    def _analyze_keyword_trends(
        self,
        documents: List[str],
        keywords: List[Keyword]
    ) -> Dict[str, List[float]]:
        """Analyze keyword trends across documents"""
        
        trends = {}
        
        for keyword in keywords:
            trend = []
            
            for doc in documents:
                # Calculate normalized frequency
                doc_words = len(doc.split())
                keyword_count = doc.lower().count(keyword.text.lower())
                normalized_freq = keyword_count / doc_words if doc_words > 0 else 0
                trend.append(normalized_freq)
            
            trends[keyword.text] = trend
        
        return trends
    
    def _calculate_statistics(
        self,
        keywords: List[Keyword],
        topics: List[Topic],
        clusters: List[PhraseCluster],
        text: str
    ) -> Dict[str, Any]:
        """Calculate extraction statistics"""
        
        # Basic statistics
        total_words = len(text.split())
        unique_words = len(set(text.lower().split()))
        
        # Keyword statistics
        keyword_coverage = sum(k.frequency for k in keywords) / total_words if total_words > 0 else 0
        
        # Type distribution
        type_dist = Counter(k.type.value for k in keywords)
        
        # Score distribution
        scores = [k.score for k in keywords]
        
        return {
            'total_words': total_words,
            'unique_words': unique_words,
            'keyword_count': len(keywords),
            'topic_count': len(topics),
            'cluster_count': len(clusters),
            'keyword_coverage': keyword_coverage,
            'type_distribution': dict(type_dist),
            'avg_keyword_score': np.mean(scores) if scores else 0,
            'max_keyword_score': max(scores) if scores else 0,
            'min_keyword_score': min(scores) if scores else 0,
            'avg_topic_coherence': np.mean([t.coherence_score for t in topics]) if topics else 0,
            'avg_cluster_coherence': np.mean([c.coherence for c in clusters]) if clusters else 0
        }
    
    def visualize_keywords(
        self,
        result: KeywordExtractionResult,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate visualizations for keyword extraction results"""
        
        visualizations = {}
        
        try:
            # Create figure with subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. Keyword scores bar chart
            ax1 = axes[0, 0]
            top_keywords = result.keywords[:15]
            texts = [k.text for k in top_keywords]
            scores = [k.score for k in top_keywords]
            
            ax1.barh(texts, scores)
            ax1.set_xlabel('Score')
            ax1.set_title('Top Keywords by Score')
            ax1.invert_yaxis()
            
            # 2. Word cloud
            ax2 = axes[0, 1]
            word_freq = {k.text: k.score for k in result.keywords}
            
            if word_freq:
                wordcloud = WordCloud(
                    width=400,
                    height=300,
                    background_color='white'
                ).generate_from_frequencies(word_freq)
                
                ax2.imshow(wordcloud, interpolation='bilinear')
                ax2.axis('off')
                ax2.set_title('Keyword Cloud')
            
            # 3. Topic distribution
            ax3 = axes[1, 0]
            if result.topics:
                topic_sizes = [len(t.documents) for t in result.topics]
                topic_labels = [t.label for t in result.topics]
                
                ax3.pie(topic_sizes, labels=topic_labels, autopct='%1.1f%%')
                ax3.set_title('Topic Distribution')
            else:
                ax3.text(0.5, 0.5, 'No topics extracted', ha='center', va='center')
                ax3.set_title('Topic Distribution')
            
            # 4. Cluster visualization
            ax4 = axes[1, 1]
            if result.clusters and len(result.clusters) > 1:
                # Use t-SNE for 2D visualization
                all_phrases = []
                cluster_labels = []
                
                for cluster in result.clusters:
                    all_phrases.extend(cluster.phrases)
                    cluster_labels.extend([cluster.cluster_id] * len(cluster.phrases))
                
                if len(all_phrases) > 2:
                    embeddings = self.sentence_model.encode(all_phrases)
                    
                    # Apply t-SNE
                    tsne = TSNE(n_components=2, random_state=42)
                    coords = tsne.fit_transform(embeddings)
                    
                    # Plot clusters
                    scatter = ax4.scatter(
                        coords[:, 0],
                        coords[:, 1],
                        c=cluster_labels,
                        cmap='viridis',
                        alpha=0.6
                    )
                    ax4.set_title('Phrase Clusters')
                    plt.colorbar(scatter, ax=ax4)
            else:
                ax4.text(0.5, 0.5, 'No clusters extracted', ha='center', va='center')
                ax4.set_title('Phrase Clusters')
            
            plt.tight_layout()
            
            # Save or show
            if output_path:
                plt.savefig(output_path, dpi=100, bbox_inches='tight')
                visualizations['saved_to'] = output_path
            
            plt.close()
            
            visualizations['figure'] = fig
            
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
        
        return visualizations
    
    def export_results(
        self,
        result: KeywordExtractionResult,
        format: str = "json"
    ) -> str:
        """Export extraction results in various formats"""
        
        if format == "json":
            import json
            
            data = {
                'keywords': [
                    {
                        'text': k.text,
                        'score': k.score,
                        'frequency': k.frequency,
                        'type': k.type.value
                    }
                    for k in result.keywords
                ],
                'topics': [
                    {
                        'id': t.topic_id,
                        'label': t.label,
                        'words': t.words,
                        'coherence': t.coherence_score,
                        'document_count': len(t.documents)
                    }
                    for t in result.topics
                ],
                'clusters': [
                    {
                        'id': c.cluster_id,
                        'theme': c.theme,
                        'phrases': c.phrases,
                        'coherence': c.coherence
                    }
                    for c in result.clusters
                ],
                'statistics': result.statistics,
                'metadata': result.metadata
            }
            
            return json.dumps(data, indent=2, default=str)
        
        elif format == "csv":
            # Export keywords as CSV
            df = pd.DataFrame([
                {
                    'keyword': k.text,
                    'score': k.score,
                    'frequency': k.frequency,
                    'type': k.type.value
                }
                for k in result.keywords
            ])
            
            return df.to_csv(index=False)
        
        else:
            raise ValueError(f"Unsupported format: {format}")


# Example usage
async def main():
    """Example usage of keyword extraction system"""
    
    # Initialize extractor
    extractor = AdvancedKeywordExtractor()
    
    # Sample documents
    documents = [
        """
        Artificial intelligence and machine learning are transforming industries.
        Deep learning models, particularly neural networks, have achieved remarkable
        success in computer vision, natural language processing, and speech recognition.
        Companies are investing heavily in AI research and development.
        """,
        """
        The future of technology lies in quantum computing and artificial intelligence.
        These emerging technologies will revolutionize how we process information
        and solve complex problems. Machine learning algorithms continue to improve.
        """,
        """
        Data science combines statistics, programming, and domain expertise.
        Big data analytics helps organizations make data-driven decisions.
        Python and R are popular programming languages for data analysis.
        Machine learning is a key component of modern data science.
        """
    ]
    
    # Extract keywords
    result = await extractor.extract_keywords(
        documents,
        methods=[
            ExtractionMethod.RAKE,
            ExtractionMethod.TFIDF,
            ExtractionMethod.LDA
        ],
        max_keywords=20,
        include_entities=True,
        include_topics=True,
        cluster_phrases=True
    )
    
    # Print results
    print(f"Extracted {len(result.keywords)} keywords:")
    for kw in result.keywords[:10]:
        print(f"  - {kw.text}: {kw.score:.3f} (type: {kw.type.value})")
    
    print(f"\nExtracted {len(result.topics)} topics:")
    for topic in result.topics[:5]:
        print(f"  Topic {topic.topic_id}: {topic.label}")
        print(f"    Top words: {[w for w, _ in topic.words[:5]]}")
    
    print(f"\nFound {len(result.clusters)} phrase clusters:")
    for cluster in result.clusters:
        print(f"  Cluster {cluster.cluster_id} (theme: {cluster.theme}):")
        print(f"    Phrases: {cluster.phrases[:3]}")
    
    print(f"\nStatistics:")
    for key, value in result.statistics.items():
        print(f"  {key}: {value}")
    
    # Generate visualizations
    extractor.visualize_keywords(result, "keyword_analysis.png")
    
    # Export results
    json_output = extractor.export_results(result, "json")
    print(f"\nExported results ({len(json_output)} characters)")


if __name__ == "__main__":
    asyncio.run(main())