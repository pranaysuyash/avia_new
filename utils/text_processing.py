"""
Text Processing Utilities
Handles text normalization, cleaning, and enhancement
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import unicodedata
from collections import Counter

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
import spacy
from textblob import TextBlob
from lingua import Language, LanguageDetectorBuilder
import contractions
import emoji

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)


class TextProcessor:
    """Text processing and enhancement utilities"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize NLP tools
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("SpaCy model not found. Some features may be limited.")
            self.nlp = None
        
        # Initialize language detector
        languages = [Language.ENGLISH, Language.SPANISH, Language.FRENCH, 
                    Language.GERMAN, Language.ITALIAN, Language.PORTUGUESE]
        self.language_detector = LanguageDetectorBuilder.from_languages(*languages).build()
        
        # Initialize text processing tools
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
    
    def clean_text(
        self,
        text: str,
        remove_urls: bool = True,
        remove_emails: bool = True,
        remove_numbers: bool = False,
        remove_punctuation: bool = False,
        expand_contractions: bool = True,
        convert_emojis: bool = True,
        lowercase: bool = False
    ) -> str:
        """Clean and normalize text"""
        
        # Expand contractions
        if expand_contractions:
            text = contractions.fix(text)
        
        # Convert emojis to text
        if convert_emojis:
            text = emoji.demojize(text)
        
        # Remove URLs
        if remove_urls:
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
            text = re.sub(r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove emails
        if remove_emails:
            text = re.sub(r'\S+@\S+', '', text)
        
        # Remove numbers
        if remove_numbers:
            text = re.sub(r'\d+', '', text)
        
        # Remove punctuation
        if remove_punctuation:
            text = re.sub(r'[^\w\s]', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Convert to lowercase
        if lowercase:
            text = text.lower()
        
        # Remove unicode characters
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        
        return text.strip()
    
    def segment_sentences(self, text: str) -> List[str]:
        """Segment text into sentences"""
        return sent_tokenize(text)
    
    def tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words"""
        return word_tokenize(text)
    
    def remove_stopwords(self, text: str, language: str = 'english') -> str:
        """Remove stopwords from text"""
        
        if language != 'english':
            try:
                stop_words = set(stopwords.words(language))
            except:
                logger.warning(f"Stopwords for {language} not available")
                stop_words = self.stop_words
        else:
            stop_words = self.stop_words
        
        words = word_tokenize(text.lower())
        filtered_words = [word for word in words if word not in stop_words]
        
        return ' '.join(filtered_words)
    
    def lemmatize_text(self, text: str) -> str:
        """Lemmatize text"""
        words = word_tokenize(text)
        lemmatized = [self.lemmatizer.lemmatize(word) for word in words]
        return ' '.join(lemmatized)
    
    def stem_text(self, text: str) -> str:
        """Stem text"""
        words = word_tokenize(text)
        stemmed = [self.stemmer.stem(word) for word in words]
        return ' '.join(stemmed)
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        
        if not self.nlp:
            return {}
        
        doc = self.nlp(text)
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        
        return entities
    
    def extract_keywords(
        self,
        text: str,
        num_keywords: int = 10,
        method: str = 'frequency'
    ) -> List[Tuple[str, float]]:
        """Extract keywords from text"""
        
        # Clean and tokenize
        cleaned_text = self.remove_stopwords(text.lower())
        words = word_tokenize(cleaned_text)
        
        if method == 'frequency':
            # Simple frequency-based extraction
            word_freq = Counter(words)
            return word_freq.most_common(num_keywords)
        
        elif method == 'tfidf':
            # TF-IDF based (simplified single document)
            word_freq = Counter(words)
            total_words = len(words)
            
            tfidf_scores = []
            for word, freq in word_freq.items():
                tf = freq / total_words
                # Simple IDF approximation
                idf = 1.0  # Would need document corpus for real IDF
                tfidf_scores.append((word, tf * idf))
            
            return sorted(tfidf_scores, key=lambda x: x[1], reverse=True)[:num_keywords]
        
        else:
            return []
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """Get various text statistics"""
        
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        
        # Basic statistics
        stats = {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'average_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'average_sentence_length': len(words) / len(sentences) if sentences else 0,
            'unique_words': len(set(words)),
            'lexical_diversity': len(set(words)) / len(words) if words else 0
        }
        
        # Readability scores
        if len(sentences) > 0 and len(words) > 0:
            # Flesch Reading Ease approximation
            syllable_count = sum(self._count_syllables(word) for word in words)
            stats['flesch_reading_ease'] = (
                206.835 - 1.015 * (len(words) / len(sentences)) 
                - 84.6 * (syllable_count / len(words))
            )
        
        return stats
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)"""
        word = word.lower()
        vowels = "aeiou"
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e'):
            syllable_count -= 1
        
        # Ensure at least one syllable
        if syllable_count == 0:
            syllable_count = 1
        
        return syllable_count
    
    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        
        try:
            language = self.language_detector.detect_language_of(text)
            if language:
                return language.iso_code_639_1.lower()
        except:
            pass
        
        # Fallback to TextBlob
        try:
            blob = TextBlob(text)
            return blob.detect_language()
        except:
            pass
        
        return 'en'  # Default to English
    
    def correct_spelling(self, text: str) -> str:
        """Correct spelling errors in text"""
        
        try:
            blob = TextBlob(text)
            return str(blob.correct())
        except:
            logger.warning("Spelling correction failed")
            return text
    
    def extract_phrases(
        self,
        text: str,
        min_freq: int = 2,
        max_phrase_length: int = 4
    ) -> List[Tuple[str, int]]:
        """Extract common phrases from text"""
        
        if not self.nlp:
            return []
        
        doc = self.nlp(text.lower())
        
        # Extract noun phrases
        phrases = []
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= max_phrase_length:
                phrases.append(chunk.text)
        
        # Count phrase frequency
        phrase_freq = Counter(phrases)
        
        # Filter by minimum frequency
        return [(phrase, count) for phrase, count in phrase_freq.items() if count >= min_freq]
    
    def summarize_text(
        self,
        text: str,
        num_sentences: int = 3,
        method: str = 'frequency'
    ) -> str:
        """Simple text summarization"""
        
        sentences = sent_tokenize(text)
        
        if len(sentences) <= num_sentences:
            return text
        
        if method == 'frequency':
            # Frequency-based summarization
            words = word_tokenize(text.lower())
            word_freq = Counter(words)
            
            # Score sentences
            sentence_scores = {}
            for sentence in sentences:
                words_in_sentence = word_tokenize(sentence.lower())
                score = sum(word_freq[word] for word in words_in_sentence if word in word_freq)
                sentence_scores[sentence] = score / len(words_in_sentence) if words_in_sentence else 0
            
            # Select top sentences
            top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
            
            # Return in original order
            summary_sentences = [sent for sent in sentences if sent in dict(top_sentences)]
            return ' '.join(summary_sentences)
        
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text"""
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)
        
        return text.strip()
    
    def extract_numbers(self, text: str) -> List[Dict[str, Any]]:
        """Extract numbers and numerical expressions from text"""
        
        numbers = []
        
        # Extract integers
        integers = re.findall(r'\b\d+\b', text)
        for num in integers:
            numbers.append({'value': int(num), 'type': 'integer', 'text': num})
        
        # Extract decimals
        decimals = re.findall(r'\b\d+\.\d+\b', text)
        for num in decimals:
            numbers.append({'value': float(num), 'type': 'decimal', 'text': num})
        
        # Extract percentages
        percentages = re.findall(r'\b\d+(?:\.\d+)?%', text)
        for pct in percentages:
            value = float(pct.rstrip('%'))
            numbers.append({'value': value, 'type': 'percentage', 'text': pct})
        
        # Extract currency
        currency_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?'
        currencies = re.findall(currency_pattern, text)
        for curr in currencies:
            value = float(curr.replace('$', '').replace(',', ''))
            numbers.append({'value': value, 'type': 'currency', 'text': curr})
        
        return numbers
    
    def split_into_chunks(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks"""
        
        words = word_tokenize(text)
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunks.append(' '.join(chunk_words))
        
        return chunks