"""
WhisperX provider for enhanced speaker diarization with ML-based clustering
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
import asyncio
import numpy as np
from pathlib import Path
import tempfile
import os

from .base import BaseDiarizationProvider
from ..diarization_manager import DiarizationResult, SpeakerSegment

logger = logging.getLogger(__name__)


class WhisperXProvider(BaseDiarizationProvider):
    """Enhanced speaker diarization using WhisperX with ML-based clustering"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.model = None
        self.diarize_model = None
        self.align_model = None
        self.metadata = None
        
        # Configuration
        config = config or {}
        self.model_size = config.get('model_size', 'base')
        self.device = config.get('device', 'cpu')
        self.compute_type = config.get('compute_type', 'float32')
        self.batch_size = config.get('batch_size', 16)
        self.language = config.get('language', 'en')
        self.hf_token = config.get('huggingface_token')
        
        # Speaker embedding configuration
        self.embedding_model = config.get('embedding_model', 'speechbrain/spkrec-ecapa-voxceleb')
        self.clustering_method = config.get('clustering_method', 'spectral')
        self.min_speakers = config.get('min_speakers', 1)
        self.max_speakers = config.get('max_speakers', 10)
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize WhisperX models"""
        try:
            import whisperx
            import torch
            
            logger.info(f"Loading WhisperX model: {self.model_size}")
            
            # Load ASR model
            self.model = whisperx.load_model(
                self.model_size, 
                self.device, 
                compute_type=self.compute_type,
                language=self.language
            )
            
            # Load alignment model
            self.align_model, self.metadata = whisperx.load_align_model(
                language_code=self.language, 
                device=self.device
            )
            
            # Load diarization model
            self.diarize_model = whisperx.DiarizationPipeline(
                use_auth_token=self.hf_token,
                device=self.device
            )
            
            logger.info("WhisperX models loaded successfully")
            
        except ImportError:
            logger.warning("WhisperX not installed. Install with: pip install whisperx")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to initialize WhisperX models: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if WhisperX is available"""
        try:
            import whisperx
            import torch
            return self.model is not None
        except ImportError:
            return False
    
    async def diarize(self, 
                     audio_path: str,
                     min_segment_duration: float = 1.0,
                     max_speakers: Optional[int] = None) -> DiarizationResult:
        """Perform enhanced speaker diarization using WhisperX"""
        if not self.is_available():
            raise RuntimeError("WhisperX provider is not available")
        
        self.validate_audio_file(audio_path)
        
        # Get audio duration
        audio_duration = self.get_audio_duration(audio_path)
        
        # Run WhisperX pipeline in thread pool
        loop = asyncio.get_event_loop()
        diarization_data = await loop.run_in_executor(
            None,
            self._run_whisperx_pipeline,
            audio_path,
            min_segment_duration,
            max_speakers or self.max_speakers
        )
        
        # Convert to our format
        result = self._convert_whisperx_result(
            diarization_data, 
            audio_duration,
            min_segment_duration
        )
        
        # Add metadata
        result.metadata = {
            'provider': 'whisperx',
            'model_size': self.model_size,
            'device': self.device,
            'language': self.language,
            'embedding_model': self.embedding_model,
            'clustering_method': self.clustering_method,
            'min_segment_duration': min_segment_duration,
            'max_speakers': max_speakers
        }
        
        logger.info(f"WhisperX diarization completed: {len(result.speakers)} speakers, {len(result.segments)} segments")
        return result
    
    def _run_whisperx_pipeline(self, 
                              audio_path: str,
                              min_segment_duration: float,
                              max_speakers: int) -> Dict[str, Any]:
        """Run the complete WhisperX pipeline"""
        import whisperx
        
        logger.info(f"Running WhisperX pipeline on {audio_path}")
        
        # Load audio
        audio = whisperx.load_audio(audio_path)
        
        # Step 1: Transcribe with Whisper
        logger.info("Step 1: Transcribing audio...")
        result = self.model.transcribe(
            audio, 
            batch_size=self.batch_size,
            language=self.language
        )
        
        # Step 2: Align whisper output
        logger.info("Step 2: Aligning transcript...")
        result = whisperx.align(
            result["segments"], 
            self.align_model, 
            self.metadata, 
            audio, 
            self.device, 
            return_char_alignments=False
        )
        
        # Step 3: Assign speaker labels
        logger.info("Step 3: Performing speaker diarization...")
        diarize_segments = self.diarize_model(
            audio,
            min_speakers=self.min_speakers,
            max_speakers=max_speakers
        )
        
        # Step 4: Assign speakers to words
        logger.info("Step 4: Assigning speakers to segments...")
        result = whisperx.assign_word_speakers(diarize_segments, result)
        
        return {
            'segments': result.get('segments', []),
            'word_segments': result.get('word_segments', []),
            'diarize_segments': diarize_segments,
            'language': result.get('language', self.language)
        }
    
    def _convert_whisperx_result(self, 
                                data: Dict[str, Any],
                                audio_duration: float,
                                min_segment_duration: float) -> DiarizationResult:
        """Convert WhisperX output to our DiarizationResult format"""
        result = DiarizationResult(audio_duration=audio_duration)
        
        # Process segments with speaker information
        segments = data.get('segments', [])
        
        # Group consecutive segments by speaker
        current_speaker = None
        current_start = None
        current_end = None
        current_text_parts = []
        
        for segment in segments:
            speaker = segment.get('speaker')
            start_time = segment.get('start', 0.0)
            end_time = segment.get('end', start_time + 1.0)
            text = segment.get('text', '').strip()
            
            # Skip segments without speaker information
            if not speaker:
                continue
            
            # If this is a new speaker or there's a significant gap
            if (current_speaker != speaker or 
                (current_end and start_time - current_end > 2.0)):
                
                # Save previous segment if it exists and meets duration requirement
                if (current_speaker and current_start is not None and 
                    current_end and current_end - current_start >= min_segment_duration):
                    
                    segment_obj = SpeakerSegment(
                        speaker_id=current_speaker,
                        start_time=current_start,
                        end_time=current_end,
                        confidence=0.95,  # WhisperX provides high confidence
                        text=' '.join(current_text_parts).strip()
                    )
                    result.add_segment(segment_obj)
                
                # Start new segment
                current_speaker = speaker
                current_start = start_time
                current_end = end_time
                current_text_parts = [text] if text else []
            else:
                # Continue current segment
                current_end = end_time
                if text:
                    current_text_parts.append(text)
        
        # Don't forget the last segment
        if (current_speaker and current_start is not None and 
            current_end and current_end - current_start >= min_segment_duration):
            
            segment_obj = SpeakerSegment(
                speaker_id=current_speaker,
                start_time=current_start,
                end_time=current_end,
                confidence=0.95,
                text=' '.join(current_text_parts).strip()
            )
            result.add_segment(segment_obj)
        
        # If no segments were created from WhisperX output, create from diarize_segments
        if not result.segments:
            diarize_segments = data.get('diarize_segments')
            if diarize_segments:
                for turn, _, speaker in diarize_segments.itertracks(yield_label=True):
                    if turn.duration >= min_segment_duration:
                        segment_obj = SpeakerSegment(
                            speaker_id=f"SPEAKER_{speaker}",
                            start_time=turn.start,
                            end_time=turn.end,
                            confidence=0.90
                        )
                        result.add_segment(segment_obj)
        
        return result
    
    def extract_speaker_embeddings(self, 
                                 audio_path: str,
                                 segments: List[SpeakerSegment]) -> Dict[str, np.ndarray]:
        """Extract speaker embeddings for voice profiling"""
        try:
            import whisperx
            from speechbrain.pretrained import EncoderClassifier
            
            # Load speaker embedding model
            classifier = EncoderClassifier.from_hparams(
                source=self.embedding_model,
                savedir="tmp_speaker_model"
            )
            
            # Load audio
            audio = whisperx.load_audio(audio_path)
            sample_rate = 16000  # WhisperX uses 16kHz
            
            embeddings = {}
            
            for segment in segments:
                # Extract audio segment
                start_sample = int(segment.start_time * sample_rate)
                end_sample = int(segment.end_time * sample_rate)
                segment_audio = audio[start_sample:end_sample]
                
                # Skip very short segments
                if len(segment_audio) < sample_rate * 0.5:  # Less than 0.5 seconds
                    continue
                
                # Extract embedding
                embedding = classifier.encode_batch(
                    segment_audio.unsqueeze(0)
                ).squeeze().cpu().numpy()
                
                if segment.speaker_id not in embeddings:
                    embeddings[segment.speaker_id] = []
                embeddings[segment.speaker_id].append(embedding)
            
            # Average embeddings for each speaker
            averaged_embeddings = {}
            for speaker_id, speaker_embeddings in embeddings.items():
                if speaker_embeddings:
                    averaged_embeddings[speaker_id] = np.mean(speaker_embeddings, axis=0)
            
            return averaged_embeddings
            
        except Exception as e:
            logger.error(f"Failed to extract speaker embeddings: {e}")
            return {}
    
    def cluster_speakers(self, 
                        embeddings: Dict[str, np.ndarray],
                        n_clusters: Optional[int] = None) -> Dict[str, str]:
        """Cluster speakers based on embeddings"""
        try:
            from sklearn.cluster import SpectralClustering, AgglomerativeClustering
            from sklearn.metrics.pairwise import cosine_similarity
            
            if not embeddings or len(embeddings) < 2:
                return {k: k for k in embeddings.keys()}
            
            # Prepare data
            speaker_ids = list(embeddings.keys())
            embedding_matrix = np.array([embeddings[sid] for sid in speaker_ids])
            
            # Determine number of clusters
            if n_clusters is None:
                n_clusters = min(len(speaker_ids), self.max_speakers)
            
            # Perform clustering
            if self.clustering_method == 'spectral':
                # Use cosine similarity for spectral clustering
                similarity_matrix = cosine_similarity(embedding_matrix)
                clusterer = SpectralClustering(
                    n_clusters=n_clusters,
                    affinity='precomputed',
                    random_state=42
                )
                cluster_labels = clusterer.fit_predict(similarity_matrix)
            else:
                # Use agglomerative clustering
                clusterer = AgglomerativeClustering(
                    n_clusters=n_clusters,
                    linkage='ward'
                )
                cluster_labels = clusterer.fit_predict(embedding_matrix)
            
            # Create mapping
            speaker_mapping = {}
            for i, speaker_id in enumerate(speaker_ids):
                cluster_id = f"speaker_{cluster_labels[i] + 1}"
                speaker_mapping[speaker_id] = cluster_id
            
            return speaker_mapping
            
        except Exception as e:
            logger.error(f"Failed to cluster speakers: {e}")
            return {k: k for k in embeddings.keys()}
    
    def create_speaker_profiles(self, 
                              embeddings: Dict[str, np.ndarray],
                              segments: List[SpeakerSegment]) -> Dict[str, Dict[str, Any]]:
        """Create detailed speaker profiles"""
        profiles = {}
        
        for speaker_id in embeddings.keys():
            speaker_segments = [s for s in segments if s.speaker_id == speaker_id]
            
            if not speaker_segments:
                continue
            
            # Calculate statistics
            total_time = sum(s.duration for s in speaker_segments)
            avg_segment_duration = total_time / len(speaker_segments)
            avg_confidence = sum(s.confidence for s in speaker_segments) / len(speaker_segments)
            
            # Calculate speaking patterns
            gaps_between_segments = []
            for i in range(1, len(speaker_segments)):
                gap = speaker_segments[i].start_time - speaker_segments[i-1].end_time
                if gap > 0:
                    gaps_between_segments.append(gap)
            
            avg_gap = np.mean(gaps_between_segments) if gaps_between_segments else 0.0
            
            profiles[speaker_id] = {
                'embedding': embeddings[speaker_id].tolist(),
                'total_speaking_time': total_time,
                'segment_count': len(speaker_segments),
                'average_segment_duration': avg_segment_duration,
                'average_confidence': avg_confidence,
                'average_gap_between_segments': avg_gap,
                'speaking_pattern': self._analyze_speaking_pattern(speaker_segments),
                'voice_characteristics': self._analyze_voice_characteristics(embeddings[speaker_id])
            }
        
        return profiles
    
    def _analyze_speaking_pattern(self, segments: List[SpeakerSegment]) -> Dict[str, Any]:
        """Analyze speaking patterns for a speaker"""
        if not segments:
            return {}
        
        durations = [s.duration for s in segments]
        
        return {
            'min_segment_duration': min(durations),
            'max_segment_duration': max(durations),
            'median_segment_duration': np.median(durations),
            'std_segment_duration': np.std(durations),
            'speaking_style': 'continuous' if np.std(durations) < 2.0 else 'varied'
        }
    
    def _analyze_voice_characteristics(self, embedding: np.ndarray) -> Dict[str, Any]:
        """Analyze voice characteristics from embedding"""
        # This is a simplified analysis - in practice, you'd use more sophisticated methods
        embedding_stats = {
            'embedding_norm': float(np.linalg.norm(embedding)),
            'embedding_mean': float(np.mean(embedding)),
            'embedding_std': float(np.std(embedding)),
            'dominant_features': embedding.argsort()[-5:].tolist()  # Top 5 features
        }
        
        # Simple voice type classification based on embedding characteristics
        if embedding_stats['embedding_mean'] > 0.1:
            voice_type = 'expressive'
        elif embedding_stats['embedding_std'] > 0.5:
            voice_type = 'dynamic'
        else:
            voice_type = 'steady'
        
        embedding_stats['voice_type'] = voice_type
        
        return embedding_stats
    
    def get_requirements(self) -> Dict[str, str]:
        """Get provider requirements"""
        return {
            'name': 'WhisperX Enhanced Diarization',
            'description': 'State-of-the-art speaker diarization with ML-based clustering and voice profiling',
            'dependencies': [
                'whisperx>=3.1.0',
                'torch>=1.9',
                'torchaudio',
                'speechbrain>=0.5.0',
                'scikit-learn>=1.0',
                'pyannote.audio>=3.1.0'
            ],
            'features': [
                'High accuracy speaker identification',
                'ML-based speaker clustering',
                'Voice embedding extraction',
                'Speaker profiling and recognition',
                'Word-level speaker alignment',
                'GPU acceleration support'
            ],
            'limitations': [
                'Requires HuggingFace token for some models',
                'Large model size (~2GB)',
                'Higher computational requirements',
                'Slower processing than basic methods'
            ]
        }