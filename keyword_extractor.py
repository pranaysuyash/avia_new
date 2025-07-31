#!/usr/bin/env python3
"""
Keyword Extraction Module
Implements RAKE (Rapid Automatic Keyword Extraction) and other keyword extraction methods
"""

import re
import logging
from typing import List, Dict, Tuple, Set
from collections import Counter, defaultdict
import math

logger = logging.getLogger(__name__)

class RAKEKeywordExtractor:
    """RAKE (Rapid Automatic Keyword Extraction) implementation"""
    
    def __init__(self, stop_words: Set[str] = None, min_char_length: int = 1, 
                 max_words_length: int = 3, min_keyword_frequency: int = 1):
        self.stop_words = stop_words or self._get_default_stop_words()
        self.min_char_length = min_char_length
        self.max_words_length = max_words_length
        self.min_keyword_frequency = min_keyword_frequency
    
    def _get_default_stop_words(self) -> Set[str]:
        """Get default English stop words"""
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
            'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'will', 'with',
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
            'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
            'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
            'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
            'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
            'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
            'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren',
            'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn',
            'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn'
        }
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[Tuple[str, float]]:
        """
        Extract keywords using RAKE algorithm
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of (keyword, score) tuples sorted by score
        """
        try:
            # Step 1: Split text into candidate keywords
            candidate_keywords = self._generate_candidate_keywords(text)
            
            # Step 2: Calculate word scores
            word_scores = self._calculate_word_scores(candidate_keywords)
            
            # Step 3: Calculate keyword scores
            keyword_scores = self._calculate_keyword_scores(candidate_keywords, word_scores)
            
            # Step 4: Sort and return top keywords
            sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
            
            logger.info(f"Extracted {len(sorted_keywords)} keywords using RAKE")
            return sorted_keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"RAKE keyword extraction failed: {e}")
            return []
    
    def _generate_candidate_keywords(self, text: str) -> List[List[str]]:
        """Generate candidate keywords by splitting on stop words and punctuation"""
        # Clean and normalize text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Split into candidate keyword phrases
        candidate_keywords = []
        current_phrase = []
        
        for word in words:
            if (word in self.stop_words or 
                len(word) < self.min_char_length or 
                not word.isalpha()):
                
                if current_phrase and len(current_phrase) <= self.max_words_length:
                    candidate_keywords.append(current_phrase)
                current_phrase = []
            else:
                current_phrase.append(word)
        
        # Add final phrase if exists
        if current_phrase and len(current_phrase) <= self.max_words_length:
            candidate_keywords.append(current_phrase)
        
        return candidate_keywords
    
    def _calculate_word_scores(self, candidate_keywords: List[List[str]]) -> Dict[str, float]:
        """Calculate scores for individual words"""
        word_frequency = defaultdict(int)
        word_degree = defaultdict(int)
        
        # Count word frequencies and degrees
        for phrase in candidate_keywords:
            phrase_length = len(phrase)
            phrase_degree = phrase_length - 1
            
            for word in phrase:
                word_frequency[word] += 1
                word_degree[word] += phrase_degree
        
        # Calculate word scores (degree/frequency)
        word_scores = {}
        for word in word_frequency:
            word_scores[word] = word_degree[word] / word_frequency[word]
        
        return word_scores
    
    def _calculate_keyword_scores(self, candidate_keywords: List[List[str]], 
                                word_scores: Dict[str, float]) -> Dict[str, float]:
        """Calculate scores for keyword phrases"""
        keyword_scores = {}
        
        for phrase in candidate_keywords:
            if len(phrase) == 0:
                continue
                
            keyword = ' '.join(phrase)
            
            # Skip if below minimum frequency
            if keyword_scores.get(keyword, 0) < self.min_keyword_frequency - 1:
                # Calculate score as sum of word scores
                score = sum(word_scores.get(word, 0) for word in phrase)
                keyword_scores[keyword] = score
        
        return keyword_scores

class TFIDFKeywordExtractor:
    """TF-IDF based keyword extraction"""
    
    def __init__(self, stop_words: Set[str] = None):
        self.stop_words = stop_words or RAKEKeywordExtractor()._get_default_stop_words()
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[Tuple[str, float]]:
        """
        Extract keywords using TF-IDF approach
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of (keyword, score) tuples sorted by score
        """
        try:
            # Clean and tokenize text
            words = self._tokenize_text(text)
            
            # Calculate term frequencies
            tf_scores = self._calculate_tf(words)
            
            # For single document, use term frequency with length normalization
            # In a real TF-IDF implementation, you'd need a corpus for IDF calculation
            keyword_scores = {}
            
            for word, tf in tf_scores.items():
                if (word not in self.stop_words and 
                    len(word) > 2 and 
                    word.isalpha()):
                    # Simple scoring: TF * inverse word length (longer words get higher scores)
                    score = tf * (len(word) / 10.0)
                    keyword_scores[word] = score
            
            # Sort and return top keywords
            sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
            
            logger.info(f"Extracted {len(sorted_keywords)} keywords using TF-IDF approach")
            return sorted_keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"TF-IDF keyword extraction failed: {e}")
            return []
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Clean text and convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return text.split()
    
    def _calculate_tf(self, words: List[str]) -> Dict[str, float]:
        """Calculate term frequency scores"""
        word_count = len(words)
        word_frequency = Counter(words)
        
        tf_scores = {}
        for word, freq in word_frequency.items():
            tf_scores[word] = freq / word_count
        
        return tf_scores

class KeywordExtractor:
    """Main keyword extraction class combining multiple methods"""
    
    def __init__(self):
        self.rake_extractor = RAKEKeywordExtractor()
        self.tfidf_extractor = TFIDFKeywordExtractor()
    
    def extract_keywords(self, text: str, method: str = "rake", max_keywords: int = 20) -> List[Tuple[str, float]]:
        """
        Extract keywords using specified method
        
        Args:
            text: Input text
            method: Extraction method ("rake", "tfidf", "combined")
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of (keyword, score) tuples sorted by score
        """
        if not text or not text.strip():
            return []
        
        try:
            if method == "rake":
                return self.rake_extractor.extract_keywords(text, max_keywords)
            elif method == "tfidf":
                return self.tfidf_extractor.extract_keywords(text, max_keywords)
            elif method == "combined":
                return self._extract_combined_keywords(text, max_keywords)
            else:
                logger.warning(f"Unknown extraction method: {method}, using RAKE")
                return self.rake_extractor.extract_keywords(text, max_keywords)
                
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def _extract_combined_keywords(self, text: str, max_keywords: int = 20) -> List[Tuple[str, float]]:
        """Combine RAKE and TF-IDF results"""
        try:
            # Get keywords from both methods
            rake_keywords = dict(self.rake_extractor.extract_keywords(text, max_keywords * 2))
            tfidf_keywords = dict(self.tfidf_extractor.extract_keywords(text, max_keywords * 2))
            
            # Combine scores with weights
            combined_scores = {}
            all_keywords = set(rake_keywords.keys()) | set(tfidf_keywords.keys())
            
            for keyword in all_keywords:
                rake_score = rake_keywords.get(keyword, 0) * 0.7  # RAKE weight
                tfidf_score = tfidf_keywords.get(keyword, 0) * 0.3  # TF-IDF weight
                combined_scores[keyword] = rake_score + tfidf_score
            
            # Sort and return top keywords
            sorted_keywords = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
            
            logger.info(f"Extracted {len(sorted_keywords)} keywords using combined method")
            return sorted_keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"Combined keyword extraction failed: {e}")
            return self.rake_extractor.extract_keywords(text, max_keywords)
    
    def extract_keyphrases(self, text: str, min_phrase_length: int = 2, 
                          max_phrase_length: int = 4, max_keyphrases: int = 15) -> List[Tuple[str, float]]:
        """
        Extract key phrases (multi-word keywords)
        
        Args:
            text: Input text
            min_phrase_length: Minimum number of words in phrase
            max_phrase_length: Maximum number of words in phrase
            max_keyphrases: Maximum number of keyphrases to return
            
        Returns:
            List of (keyphrase, score) tuples sorted by score
        """
        try:
            # Use RAKE with adjusted parameters for phrases
            phrase_extractor = RAKEKeywordExtractor(
                min_char_length=1,
                max_words_length=max_phrase_length,
                min_keyword_frequency=1
            )
            
            all_keywords = phrase_extractor.extract_keywords(text, max_keyphrases * 2)
            
            # Filter for phrases with desired length
            keyphrases = [
                (keyword, score) for keyword, score in all_keywords
                if min_phrase_length <= len(keyword.split()) <= max_phrase_length
            ]
            
            logger.info(f"Extracted {len(keyphrases)} keyphrases")
            return keyphrases[:max_keyphrases]
            
        except Exception as e:
            logger.error(f"Keyphrase extraction failed: {e}")
            return []
    
    def get_keyword_context(self, text: str, keyword: str, context_window: int = 50) -> List[str]:
        """
        Get context sentences containing the keyword
        
        Args:
            text: Input text
            keyword: Keyword to find context for
            context_window: Number of characters around keyword
            
        Returns:
            List of context strings
        """
        try:
            contexts = []
            text_lower = text.lower()
            keyword_lower = keyword.lower()
            
            # Find all occurrences of the keyword
            start = 0
            while True:
                pos = text_lower.find(keyword_lower, start)
                if pos == -1:
                    break
                
                # Extract context around the keyword
                context_start = max(0, pos - context_window)
                context_end = min(len(text), pos + len(keyword) + context_window)
                
                context = text[context_start:context_end].strip()
                if context and context not in contexts:
                    contexts.append(context)
                
                start = pos + 1
            
            return contexts
            
        except Exception as e:
            logger.error(f"Failed to get keyword context: {e}")
            return []

# Global extractor instance
_keyword_extractor = None

def get_keyword_extractor() -> KeywordExtractor:
    """Get or create global keyword extractor instance"""
    global _keyword_extractor
    if _keyword_extractor is None:
        _keyword_extractor = KeywordExtractor()
    return _keyword_extractor

# Public API functions
def extract_keywords(text: str, method: str = "rake", max_keywords: int = 20) -> List[Tuple[str, float]]:
    """Extract keywords from text"""
    extractor = get_keyword_extractor()
    return extractor.extract_keywords(text, method, max_keywords)

def extract_keyphrases(text: str, max_keyphrases: int = 15) -> List[Tuple[str, float]]:
    """Extract key phrases from text"""
    extractor = get_keyword_extractor()
    return extractor.extract_keyphrases(text, max_keyphrases=max_keyphrases)

def get_keyword_context(text: str, keyword: str) -> List[str]:
    """Get context for a specific keyword"""
    extractor = get_keyword_extractor()
    return extractor.get_keyword_context(text, keyword)