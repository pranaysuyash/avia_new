#!/usr/bin/env python3
"""
Intelligent Content-Based Search System
Implements visual scene description, semantic video search, and audio pattern recognition
"""

import os
import json
import sqlite3
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import cv2
import torch
import whisper
import librosa
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import imagehash
import soundfile as sf
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VisualScene:
    """Represents a visual scene with description and metadata"""
    scene_id: str
    file_path: str
    timestamp: float
    frame_number: int
    description: str
    objects: List[str]
    confidence: float
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AudioPattern:
    """Represents an audio pattern with features"""
    pattern_id: str
    file_path: str
    start_time: float
    end_time: float
    pattern_type: str  # 'music', 'applause', 'silence', 'noise', etc.
    confidence: float
    features: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SearchResult:
    """Represents a search result"""
    content_id: str
    content_type: str  # 'visual', 'audio', 'text'
    file_path: str
    timestamp: float
    relevance_score: float
    description: str
    preview: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class VisualSceneAnalyzer:
    """Analyzes video frames and generates scene descriptions"""
    
    def __init__(self, model_name: str = "Salesforce/blip-image-captioning-base"):
        """Initialize the visual scene analyzer"""
        try:
            # Load BLIP model for image captioning
            self.processor = BlipProcessor.from_pretrained(model_name)
            self.model = BlipForConditionalGeneration.from_pretrained(model_name)
            
            # Load object detection model (using OpenCV's DNN module)
            self.load_object_detection()
            
            logger.info(f"Visual scene analyzer initialized with {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize visual analyzer: {e}")
            # Fallback to basic mode
            self.processor = None
            self.model = None
    
    def load_object_detection(self):
        """Load object detection model"""
        try:
            # For demo, we'll use YOLO or similar
            # In production, use proper model loading
            self.object_detector = None  # Placeholder
        except Exception as e:
            logger.error(f"Failed to load object detection: {e}")
    
    def analyze_frame(self, frame: np.ndarray, frame_number: int, timestamp: float) -> VisualScene:
        """Analyze a single video frame"""
        try:
            # Convert frame to PIL Image
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            # Generate scene description
            description = self.generate_description(image)
            
            # Detect objects
            objects = self.detect_objects(frame)
            
            # Calculate confidence
            confidence = self.calculate_confidence(description, objects)
            
            # Generate scene ID
            scene_id = f"scene_{frame_number}_{int(timestamp*1000)}"
            
            return VisualScene(
                scene_id=scene_id,
                file_path="",  # Will be set by caller
                timestamp=timestamp,
                frame_number=frame_number,
                description=description,
                objects=objects,
                confidence=confidence,
                metadata={
                    "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
                    "analyzed_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze frame: {e}")
            return self._create_fallback_scene(frame_number, timestamp)
    
    def generate_description(self, image: Image) -> str:
        """Generate natural language description of the image"""
        try:
            if self.processor and self.model:
                # Generate caption using BLIP
                inputs = self.processor(image, return_tensors="pt")
                out = self.model.generate(**inputs, max_length=50)
                description = self.processor.decode(out[0], skip_special_tokens=True)
                return description
            else:
                return "Scene analysis unavailable"
        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            return "Error generating description"
    
    def detect_objects(self, frame: np.ndarray) -> List[str]:
        """Detect objects in the frame"""
        try:
            # Mock object detection for demo
            # In production, use YOLO, Detectron2, etc.
            mock_objects = ["person", "car", "building", "tree"]
            detected = np.random.choice(mock_objects, size=np.random.randint(1, 4), replace=False)
            return detected.tolist()
        except Exception as e:
            logger.error(f"Failed to detect objects: {e}")
            return []
    
    def calculate_confidence(self, description: str, objects: List[str]) -> float:
        """Calculate confidence score for the analysis"""
        base_confidence = 0.7
        if description and description != "Scene analysis unavailable":
            base_confidence += 0.2
        if objects:
            base_confidence += 0.1
        return min(base_confidence, 1.0)
    
    def _create_fallback_scene(self, frame_number: int, timestamp: float) -> VisualScene:
        """Create a fallback scene when analysis fails"""
        return VisualScene(
            scene_id=f"scene_{frame_number}_{int(timestamp*1000)}",
            file_path="",
            timestamp=timestamp,
            frame_number=frame_number,
            description="Scene analysis failed",
            objects=[],
            confidence=0.0
        )

class AudioPatternRecognizer:
    """Recognizes patterns in audio (music, applause, silence, etc.)"""
    
    def __init__(self):
        """Initialize the audio pattern recognizer"""
        self.sample_rate = 22050
        self.hop_length = 512
        self.patterns = {
            'music': {'energy_threshold': 0.5, 'spectral_rolloff': 0.7},
            'applause': {'zero_crossing_rate': 0.8, 'spectral_centroid': 0.6},
            'silence': {'energy_threshold': 0.1, 'zero_crossing_rate': 0.1},
            'speech': {'mfcc_variance': 0.5, 'pitch_presence': 0.6},
            'noise': {'spectral_flatness': 0.8, 'energy_variance': 0.7}
        }
        logger.info("Audio pattern recognizer initialized")
    
    def analyze_audio_segment(self, audio_data: np.ndarray, sr: int, 
                            start_time: float, end_time: float) -> List[AudioPattern]:
        """Analyze an audio segment for patterns"""
        patterns = []
        
        try:
            # Extract audio features
            features = self.extract_audio_features(audio_data, sr)
            
            # Classify the segment
            pattern_type, confidence = self.classify_audio_pattern(features)
            
            # Create pattern object
            pattern = AudioPattern(
                pattern_id=f"audio_{int(start_time*1000)}_{int(end_time*1000)}",
                file_path="",  # Will be set by caller
                start_time=start_time,
                end_time=end_time,
                pattern_type=pattern_type,
                confidence=confidence,
                features=features,
                metadata={
                    "duration": end_time - start_time,
                    "sample_rate": sr
                }
            )
            patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Failed to analyze audio segment: {e}")
        
        return patterns
    
    def extract_audio_features(self, audio_data: np.ndarray, sr: int) -> np.ndarray:
        """Extract audio features for pattern recognition"""
        try:
            # Extract various audio features
            mfcc = librosa.feature.mfcc(y=audio_data, sr=sr, n_mfcc=13)
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sr)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_data)
            energy = np.sum(audio_data ** 2) / len(audio_data)
            
            # Combine features
            features = np.concatenate([
                np.mean(mfcc, axis=1),
                [np.mean(spectral_centroid)],
                [np.mean(spectral_rolloff)],
                [np.mean(zero_crossing_rate)],
                [energy]
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to extract audio features: {e}")
            return np.zeros(17)  # Default feature vector
    
    def classify_audio_pattern(self, features: np.ndarray) -> Tuple[str, float]:
        """Classify audio pattern based on features"""
        try:
            # Simple rule-based classification for demo
            # In production, use trained ML model
            
            energy = features[-1]
            mfcc_variance = np.var(features[:13])
            
            if energy < 0.1:
                return 'silence', 0.9
            elif mfcc_variance > 0.5 and energy > 0.3:
                return 'speech', 0.8
            elif features[14] > 0.7:  # spectral rolloff
                return 'music', 0.75
            else:
                return 'noise', 0.6
                
        except Exception as e:
            logger.error(f"Failed to classify audio pattern: {e}")
            return 'unknown', 0.0

class SemanticVideoSearchEngine:
    """Semantic search engine for video content"""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize the semantic search engine"""
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = 384
        logger.info(f"Semantic search engine initialized with {embedding_model}")
    
    def create_embedding(self, text: str) -> np.ndarray:
        """Create embedding for text"""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            return np.zeros(self.embedding_dim)
    
    def create_visual_embedding(self, scene: VisualScene) -> np.ndarray:
        """Create embedding for visual scene"""
        # Combine description and objects
        text = f"{scene.description}. Objects: {', '.join(scene.objects)}"
        return self.create_embedding(text)
    
    def search_similar_scenes(self, query: str, scene_embeddings: List[Tuple[str, np.ndarray]], 
                            top_k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar scenes using semantic similarity"""
        try:
            query_embedding = self.create_embedding(query)
            
            # Calculate similarities
            similarities = []
            for scene_id, embedding in scene_embeddings:
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    embedding.reshape(1, -1)
                )[0][0]
                similarities.append((scene_id, similarity))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to search similar scenes: {e}")
            return []

class IntelligentContentSearchSystem:
    """Main system for intelligent content-based search"""
    
    def __init__(self, db_path: str = "intelligent_search.db"):
        """Initialize the search system"""
        self.db_path = db_path
        self.visual_analyzer = VisualSceneAnalyzer()
        self.audio_recognizer = AudioPatternRecognizer()
        self.search_engine = SemanticVideoSearchEngine()
        
        # Initialize database
        self._init_database()
        
        logger.info("Intelligent content search system initialized")
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visual_scenes (
                    scene_id TEXT PRIMARY KEY,
                    file_path TEXT,
                    timestamp REAL,
                    frame_number INTEGER,
                    description TEXT,
                    objects TEXT,
                    confidence REAL,
                    embedding BLOB,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    file_path TEXT,
                    start_time REAL,
                    end_time REAL,
                    pattern_type TEXT,
                    confidence REAL,
                    features BLOB,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    search_id TEXT PRIMARY KEY,
                    query TEXT,
                    query_type TEXT,
                    results_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scenes_file ON visual_scenes(file_path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scenes_timestamp ON visual_scenes(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_file ON audio_patterns(file_path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_type ON audio_patterns(pattern_type)')
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def process_video_file(self, video_path: str, sample_interval: float = 1.0) -> Dict[str, Any]:
        """Process a video file for intelligent search"""
        results = {
            'visual_scenes': [],
            'audio_patterns': [],
            'metadata': {}
        }
        
        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Extract audio
            audio_data, sr = self._extract_audio(video_path)
            
            # Process video frames
            frame_interval = int(fps * sample_interval)
            frame_count = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    timestamp = frame_count / fps
                    scene = self.visual_analyzer.analyze_frame(frame, frame_count, timestamp)
                    scene.file_path = video_path
                    
                    # Create embedding
                    scene.embedding = self.search_engine.create_visual_embedding(scene)
                    
                    # Save to database
                    self._save_visual_scene(scene)
                    results['visual_scenes'].append(scene)
                
                frame_count += 1
            
            cap.release()
            
            # Process audio patterns
            if audio_data is not None:
                audio_patterns = self._process_audio_patterns(audio_data, sr, video_path)
                results['audio_patterns'] = audio_patterns
            
            # Update metadata
            results['metadata'] = {
                'file_path': video_path,
                'duration': total_frames / fps,
                'fps': fps,
                'total_frames': total_frames,
                'scenes_analyzed': len(results['visual_scenes']),
                'audio_patterns_found': len(results['audio_patterns'])
            }
            
            logger.info(f"Processed video: {video_path}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to process video: {e}")
            return results
    
    def _extract_audio(self, video_path: str) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """Extract audio from video file"""
        try:
            # Use librosa to load audio
            audio_data, sr = librosa.load(video_path, sr=22050)
            return audio_data, sr
        except Exception as e:
            logger.error(f"Failed to extract audio: {e}")
            return None, None
    
    def _process_audio_patterns(self, audio_data: np.ndarray, sr: int, 
                              file_path: str, segment_duration: float = 5.0) -> List[AudioPattern]:
        """Process audio for pattern recognition"""
        patterns = []
        
        try:
            # Process audio in segments
            segment_samples = int(segment_duration * sr)
            total_samples = len(audio_data)
            
            for start_sample in range(0, total_samples, segment_samples):
                end_sample = min(start_sample + segment_samples, total_samples)
                segment = audio_data[start_sample:end_sample]
                
                start_time = start_sample / sr
                end_time = end_sample / sr
                
                # Analyze segment
                segment_patterns = self.audio_recognizer.analyze_audio_segment(
                    segment, sr, start_time, end_time
                )
                
                for pattern in segment_patterns:
                    pattern.file_path = file_path
                    self._save_audio_pattern(pattern)
                    patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Failed to process audio patterns: {e}")
        
        return patterns
    
    def search_visual_scenes(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search for visual scenes matching the query"""
        results = []
        
        try:
            # Get all scenes with embeddings
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT scene_id, file_path, timestamp, description, embedding
                FROM visual_scenes
                WHERE embedding IS NOT NULL
            ''')
            
            scenes = cursor.fetchall()
            conn.close()
            
            if not scenes:
                return results
            
            # Prepare embeddings
            scene_embeddings = []
            scene_data = {}
            
            for scene_id, file_path, timestamp, description, embedding_blob in scenes:
                embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                scene_embeddings.append((scene_id, embedding))
                scene_data[scene_id] = (file_path, timestamp, description)
            
            # Search similar scenes
            similar_scenes = self.search_engine.search_similar_scenes(query, scene_embeddings, top_k)
            
            # Create search results
            for scene_id, relevance_score in similar_scenes:
                file_path, timestamp, description = scene_data[scene_id]
                
                result = SearchResult(
                    content_id=scene_id,
                    content_type='visual',
                    file_path=file_path,
                    timestamp=timestamp,
                    relevance_score=relevance_score,
                    description=description,
                    metadata={'query': query}
                )
                results.append(result)
            
            # Log search
            self._log_search(query, 'visual', len(results))
            
        except Exception as e:
            logger.error(f"Failed to search visual scenes: {e}")
        
        return results
    
    def search_audio_patterns(self, pattern_type: str = None, 
                            file_path: str = None) -> List[SearchResult]:
        """Search for audio patterns"""
        results = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM audio_patterns WHERE 1=1"
            params = []
            
            if pattern_type:
                query += " AND pattern_type = ?"
                params.append(pattern_type)
            
            if file_path:
                query += " AND file_path = ?"
                params.append(file_path)
            
            query += " ORDER BY confidence DESC"
            
            cursor.execute(query, params)
            patterns = cursor.fetchall()
            conn.close()
            
            # Create search results
            for row in patterns:
                pattern_id, file_path, start_time, end_time, pattern_type, confidence, _, metadata, _ = row
                
                result = SearchResult(
                    content_id=pattern_id,
                    content_type='audio',
                    file_path=file_path,
                    timestamp=start_time,
                    relevance_score=confidence,
                    description=f"{pattern_type} pattern from {start_time:.1f}s to {end_time:.1f}s",
                    metadata=json.loads(metadata) if metadata else {}
                )
                results.append(result)
            
            # Log search
            search_query = f"pattern_type={pattern_type}" if pattern_type else "all_patterns"
            self._log_search(search_query, 'audio', len(results))
            
        except Exception as e:
            logger.error(f"Failed to search audio patterns: {e}")
        
        return results
    
    def get_video_timeline(self, file_path: str) -> Dict[str, Any]:
        """Get complete timeline of a video with all analyzed content"""
        timeline = {
            'file_path': file_path,
            'visual_events': [],
            'audio_events': [],
            'combined_timeline': []
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get visual scenes
            cursor.execute('''
                SELECT scene_id, timestamp, description, objects, confidence
                FROM visual_scenes
                WHERE file_path = ?
                ORDER BY timestamp
            ''', (file_path,))
            
            for row in cursor.fetchall():
                scene_id, timestamp, description, objects_str, confidence = row
                event = {
                    'type': 'visual',
                    'timestamp': timestamp,
                    'description': description,
                    'objects': json.loads(objects_str) if objects_str else [],
                    'confidence': confidence
                }
                timeline['visual_events'].append(event)
                timeline['combined_timeline'].append(event)
            
            # Get audio patterns
            cursor.execute('''
                SELECT pattern_id, start_time, end_time, pattern_type, confidence
                FROM audio_patterns
                WHERE file_path = ?
                ORDER BY start_time
            ''', (file_path,))
            
            for row in cursor.fetchall():
                pattern_id, start_time, end_time, pattern_type, confidence = row
                event = {
                    'type': 'audio',
                    'timestamp': start_time,
                    'end_time': end_time,
                    'pattern_type': pattern_type,
                    'confidence': confidence
                }
                timeline['audio_events'].append(event)
                timeline['combined_timeline'].append(event)
            
            conn.close()
            
            # Sort combined timeline
            timeline['combined_timeline'].sort(key=lambda x: x['timestamp'])
            
        except Exception as e:
            logger.error(f"Failed to get video timeline: {e}")
        
        return timeline
    
    def _save_visual_scene(self, scene: VisualScene):
        """Save visual scene to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            embedding_blob = scene.embedding.tobytes() if scene.embedding is not None else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO visual_scenes
                (scene_id, file_path, timestamp, frame_number, description, 
                 objects, confidence, embedding, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scene.scene_id,
                scene.file_path,
                scene.timestamp,
                scene.frame_number,
                scene.description,
                json.dumps(scene.objects),
                scene.confidence,
                embedding_blob,
                json.dumps(scene.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save visual scene: {e}")
    
    def _save_audio_pattern(self, pattern: AudioPattern):
        """Save audio pattern to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            features_blob = pattern.features.tobytes() if pattern.features is not None else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO audio_patterns
                (pattern_id, file_path, start_time, end_time, pattern_type,
                 confidence, features, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id,
                pattern.file_path,
                pattern.start_time,
                pattern.end_time,
                pattern.pattern_type,
                pattern.confidence,
                features_blob,
                json.dumps(pattern.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save audio pattern: {e}")
    
    def _log_search(self, query: str, query_type: str, results_count: int):
        """Log search query"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            search_id = f"search_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            
            cursor.execute('''
                INSERT INTO search_history
                (search_id, query, query_type, results_count)
                VALUES (?, ?, ?, ?)
            ''', (search_id, query, query_type, results_count))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log search: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        stats = {
            'total_scenes': 0,
            'total_patterns': 0,
            'total_searches': 0,
            'pattern_distribution': {},
            'files_processed': 0
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count scenes
            cursor.execute('SELECT COUNT(*) FROM visual_scenes')
            stats['total_scenes'] = cursor.fetchone()[0]
            
            # Count patterns
            cursor.execute('SELECT COUNT(*) FROM audio_patterns')
            stats['total_patterns'] = cursor.fetchone()[0]
            
            # Count searches
            cursor.execute('SELECT COUNT(*) FROM search_history')
            stats['total_searches'] = cursor.fetchone()[0]
            
            # Pattern distribution
            cursor.execute('''
                SELECT pattern_type, COUNT(*) 
                FROM audio_patterns 
                GROUP BY pattern_type
            ''')
            stats['pattern_distribution'] = dict(cursor.fetchall())
            
            # Files processed
            cursor.execute('SELECT COUNT(DISTINCT file_path) FROM visual_scenes')
            stats['files_processed'] = cursor.fetchone()[0]
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
        
        return stats

# Example usage
if __name__ == "__main__":
    # Initialize system
    search_system = IntelligentContentSearchSystem()
    
    # Process a video file
    # results = search_system.process_video_file("sample_video.mp4")
    # print(f"Processed {len(results['visual_scenes'])} scenes")
    
    # Search for visual scenes
    # search_results = search_system.search_visual_scenes("person getting out of car")
    # for result in search_results[:5]:
    #     print(f"Found: {result.description} at {result.timestamp}s (score: {result.relevance_score:.3f})")
    
    # Get statistics
    stats = search_system.get_statistics()
    print(f"System statistics: {stats}")