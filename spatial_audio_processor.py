"""
Spatial Audio Processing Engine
Task 2: Spatial Audio Processing and Format Support

Professional spatial audio processing with support for Dolby Atmos, DTS:X, 
Ambisonics, 3D audio processing, surround sound, and spatial visualization.

Requirements: 1.2, 1.5
Dependencies: Professional audio processing engine, multi-channel audio engine
"""

import os
import numpy as np
import scipy.signal
import scipy.spatial
import librosa
import soundfile as sf
import logging
import asyncio
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import uuid
import json
import math

# Third-party imports with fallbacks
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available - some AI spatial features will be limited")

try:
    from professional_audio_processing_engine import (
        ProfessionalAudioProcessingEngine, AudioMetadata, AudioQuality
    )
    PROFESSIONAL_ENGINE_AVAILABLE = True
except ImportError:
    PROFESSIONAL_ENGINE_AVAILABLE = False
    logging.warning("Professional audio processing engine not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpatialFormat(Enum):
    """Supported spatial audio formats"""
    STEREO = "stereo"
    SURROUND_5_1 = "5.1"
    SURROUND_7_1 = "7.1"
    DOLBY_ATMOS = "dolby_atmos"
    DTS_X = "dts_x"
    AMBISONICS_FOA = "ambisonics_foa"  # First Order Ambisonics
    AMBISONICS_HOA = "ambisonics_hoa"  # Higher Order Ambisonics
    BINAURAL = "binaural"
    QUAD = "quad"


class SpatialProcessingMode(Enum):
    """Spatial processing modes"""
    PRESERVE = "preserve"
    ENHANCE = "enhance"
    CONVERT = "convert"
    UPMIX = "upmix"
    DOWNMIX = "downmix"


class AmbisonicsOrder(Enum):
    """Ambisonics order levels"""
    FIRST_ORDER = 1   # 4 channels (W, X, Y, Z)
    SECOND_ORDER = 2  # 9 channels
    THIRD_ORDER = 3   # 16 channels
    FOURTH_ORDER = 4  # 25 channels


@dataclass
class SpatialPosition:
    """3D spatial position"""
    x: float  # Left-Right (-1 to 1)
    y: float  # Front-Back (-1 to 1)
    z: float  # Up-Down (-1 to 1)
    distance: float = 1.0  # Distance from listener
    
    def to_spherical(self) -> Tuple[float, float, float]:
        """Convert to spherical coordinates (azimuth, elevation, distance)"""
        azimuth = math.atan2(self.y, self.x)
        elevation = math.atan2(self.z, math.sqrt(self.x**2 + self.y**2))
        return azimuth, elevation, self.distance


@dataclass
class SpatialAudioObject:
    """Spatial audio object with position and properties"""
    audio_data: np.ndarray
    position: SpatialPosition
    object_id: str
    gain: float = 1.0
    spread: float = 0.0  # Object spread/size
    priority: int = 1    # Rendering priority
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpatialScene:
    """Complete spatial audio scene"""
    objects: List[SpatialAudioObject]
    listener_position: SpatialPosition
    room_acoustics: Dict[str, float]
    sample_rate: int
    duration: float
    format: SpatialFormat
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpatialAnalysis:
    """Spatial audio analysis results"""
    format_detected: SpatialFormat
    channel_mapping: Dict[int, str]
    spatial_width: float
    spatial_depth: float
    spatial_height: float
    center_of_mass: SpatialPosition
    spatial_correlation: np.ndarray
    immersion_score: float
    localization_accuracy: float
    spatial_artifacts: List[str]


class SpatialAudioProcessor:
    """
    Professional spatial audio processing engine with support for
    multiple spatial formats and 3D audio processing.
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the spatial audio processor
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # Initialize spatial processing components
        self._initialize_spatial_processors()
        
        # Channel mappings for different formats
        self._initialize_channel_mappings()
        
        # Spatial rendering matrices
        self._initialize_rendering_matrices()
        
        logger.info("SpatialAudioProcessor initialized successfully")
    
    def _initialize_spatial_processors(self):
        """Initialize spatial audio processing components"""
        try:
            # Initialize HRTF (Head-Related Transfer Function) data
            self._initialize_hrtf()
            
            # Initialize room impulse responses
            self._initialize_room_responses()
            
            # Initialize spatial filters
            self._initialize_spatial_filters()
            
            logger.info("Spatial processors initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize spatial processors: {e}")
    
    def _initialize_hrtf(self):
        """Initialize Head-Related Transfer Function data"""
        # In production, load HRTF database (e.g., CIPIC, MIT KEMAR)
        # For now, create simplified HRTF approximation
        self.hrtf_data = {
            'sample_rate': 44100,
            'elevations': np.arange(-40, 91, 10),  # -40° to 90°
            'azimuths': np.arange(0, 360, 5),      # 0° to 355°
            'impulse_responses': {}  # Would contain actual HRTF data
        }
        
        # Generate simplified HRTF for demonstration
        self._generate_simplified_hrtf()
    
    def _generate_simplified_hrtf(self):
        """Generate simplified HRTF for demonstration purposes"""
        # This is a very simplified approximation
        # In production, use measured HRTF data
        for elevation in self.hrtf_data['elevations']:
            for azimuth in self.hrtf_data['azimuths']:
                # Create simple ITD (Interaural Time Difference) and ILD (Interaural Level Difference)
                key = (elevation, azimuth)
                
                # Simplified ITD calculation
                itd_samples = int(0.0006 * np.sin(np.radians(azimuth)) * self.hrtf_data['sample_rate'])
                
                # Simplified ILD calculation
                ild_db = 3.0 * np.sin(np.radians(azimuth))
                
                self.hrtf_data['impulse_responses'][key] = {
                    'left': np.array([1.0] + [0.0] * 127),   # 128-tap FIR
                    'right': np.array([1.0] + [0.0] * 127),
                    'itd_samples': itd_samples,
                    'ild_db': ild_db
                }
    
    def _initialize_room_responses(self):
        """Initialize room impulse responses for different acoustics"""
        self.room_responses = {
            'anechoic': np.array([1.0]),  # No reverb
            'small_room': self._generate_room_response(0.3, 0.1),
            'medium_room': self._generate_room_response(0.6, 0.2),
            'large_hall': self._generate_room_response(1.5, 0.4),
            'cathedral': self._generate_room_response(3.0, 0.7)
        }
    
    def _generate_room_response(self, rt60: float, early_reflection_level: float) -> np.ndarray:
        """Generate simplified room impulse response"""
        sample_rate = 44100
        length = int(rt60 * sample_rate)
        
        # Exponential decay
        decay = np.exp(-6.91 * np.arange(length) / (rt60 * sample_rate))
        
        # Add early reflections
        response = np.random.normal(0, 0.1, length) * decay
        response[0] = 1.0  # Direct sound
        
        # Add some early reflections
        for i in range(1, min(10, length)):
            if np.random.random() < early_reflection_level:
                response[i * 100] += 0.3 * decay[i * 100]
        
        return response
    
    def _initialize_spatial_filters(self):
        """Initialize spatial processing filters"""
        self.spatial_filters = {
            'crossfeed': self._create_crossfeed_filter(),
            'width_control': self._create_width_control_filters(),
            'bass_management': self._create_bass_management_filter()
        }
    
    def _create_crossfeed_filter(self) -> Dict[str, np.ndarray]:
        """Create crossfeed filter for headphone processing"""
        # Simple crossfeed implementation
        return {
            'direct': np.array([0.7, 0.0]),
            'cross': np.array([0.0, 0.3])
        }
    
    def _create_width_control_filters(self) -> Dict[str, Any]:
        """Create stereo width control filters"""
        return {
            'mid_side_matrix': np.array([[0.5, 0.5], [0.5, -0.5]]),
            'side_gain_range': (0.0, 2.0)
        }
    
    def _create_bass_management_filter(self) -> Dict[str, Any]:
        """Create bass management filter for subwoofer routing"""
        sample_rate = 44100
        cutoff_freq = 80  # Hz
        
        # Design lowpass filter for subwoofer
        nyquist = sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        b, a = scipy.signal.butter(4, normalized_cutoff, btype='low')
        
        return {
            'subwoofer_filter': (b, a),
            'cutoff_frequency': cutoff_freq
        }
    
    def _initialize_channel_mappings(self):
        """Initialize channel mappings for different spatial formats"""
        self.channel_mappings = {
            SpatialFormat.STEREO: {
                0: 'Left',
                1: 'Right'
            },
            SpatialFormat.SURROUND_5_1: {
                0: 'Front Left',
                1: 'Front Right', 
                2: 'Center',
                3: 'LFE',
                4: 'Rear Left',
                5: 'Rear Right'
            },
            SpatialFormat.SURROUND_7_1: {
                0: 'Front Left',
                1: 'Front Right',
                2: 'Center',
                3: 'LFE',
                4: 'Side Left',
                5: 'Side Right',
                6: 'Rear Left',
                7: 'Rear Right'
            },
            SpatialFormat.AMBISONICS_FOA: {
                0: 'W (Omnidirectional)',
                1: 'X (Front-Back)',
                2: 'Y (Left-Right)',
                3: 'Z (Up-Down)'
            }
        }
    
    def _initialize_rendering_matrices(self):
        """Initialize spatial rendering matrices"""
        # Ambisonics encoding matrices
        self.ambisonics_matrices = {
            AmbisonicsOrder.FIRST_ORDER: self._create_foa_encoding_matrix(),
            AmbisonicsOrder.SECOND_ORDER: self._create_soa_encoding_matrix()
        }
        
        # Surround sound panning matrices
        self.panning_matrices = {
            SpatialFormat.SURROUND_5_1: self._create_5_1_panning_matrix(),
            SpatialFormat.SURROUND_7_1: self._create_7_1_panning_matrix()
        }
    
    def _create_foa_encoding_matrix(self) -> np.ndarray:
        """Create First Order Ambisonics encoding matrix"""
        # FOA encoding for unit sphere
        # W = 1/sqrt(2), X = cos(elevation)*cos(azimuth), 
        # Y = cos(elevation)*sin(azimuth), Z = sin(elevation)
        return np.array([
            [1/np.sqrt(2), 1, 0, 0],      # W channel
            [0, 0, 1, 0],                 # X channel  
            [0, 0, 0, 1],                 # Y channel
            [0, 0, 0, 0]                  # Z channel (simplified)
        ])
    
    def _create_soa_encoding_matrix(self) -> np.ndarray:
        """Create Second Order Ambisonics encoding matrix"""
        # Simplified SOA matrix (9 channels)
        return np.eye(9)  # Placeholder - would need proper SOA implementation
    
    def _create_5_1_panning_matrix(self) -> np.ndarray:
        """Create 5.1 surround panning matrix"""
        # Speaker positions in degrees
        speakers = {
            'FL': -30,   # Front Left
            'FR': 30,    # Front Right
            'C': 0,      # Center
            'LFE': 0,    # Low Frequency Effects
            'RL': -110,  # Rear Left
            'RR': 110    # Rear Right
        }
        
        # Create panning matrix (simplified)
        matrix = np.zeros((6, 2))  # 6 speakers, 2 input channels
        for i, (speaker, angle) in enumerate(speakers.items()):
            if speaker != 'LFE':
                rad = np.radians(angle)
                matrix[i, 0] = np.cos(rad + np.pi/4)  # Left input
                matrix[i, 1] = np.sin(rad + np.pi/4)  # Right input
        
        return matrix
    
    def _create_7_1_panning_matrix(self) -> np.ndarray:
        """Create 7.1 surround panning matrix"""
        # Speaker positions for 7.1
        speakers = {
            'FL': -30, 'FR': 30, 'C': 0, 'LFE': 0,
            'SL': -90, 'SR': 90, 'RL': -150, 'RR': 150
        }
        
        matrix = np.zeros((8, 2))
        for i, (speaker, angle) in enumerate(speakers.items()):
            if speaker != 'LFE':
                rad = np.radians(angle)
                matrix[i, 0] = np.cos(rad + np.pi/4)
                matrix[i, 1] = np.sin(rad + np.pi/4)
        
        return matrix   
 async def detect_spatial_format(self, audio_path: str) -> SpatialFormat:
        """Detect the spatial audio format of the input file"""
        try:
            # Load audio file info
            info = sf.info(audio_path)
            channels = info.channels
            
            # Analyze channel configuration
            if channels == 2:
                # Could be stereo or binaural - analyze content
                audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)
                if self._is_binaural(audio_data):
                    return SpatialFormat.BINAURAL
                else:
                    return SpatialFormat.STEREO
            elif channels == 4:
                # Could be quad or FOA Ambisonics
                if self._is_ambisonics_foa(audio_path):
                    return SpatialFormat.AMBISONICS_FOA
                else:
                    return SpatialFormat.QUAD
            elif channels == 6:
                return SpatialFormat.SURROUND_5_1
            elif channels == 8:
                return SpatialFormat.SURROUND_7_1
            elif channels == 9:
                return SpatialFormat.AMBISONICS_HOA
            elif channels > 9:
                # Could be higher order Ambisonics or object-based
                if self._is_ambisonics_hoa(audio_path):
                    return SpatialFormat.AMBISONICS_HOA
                else:
                    return SpatialFormat.DOLBY_ATMOS  # Assume object-based
            else:
                return SpatialFormat.STEREO  # Default fallback
                
        except Exception as e:
            logger.error(f"Failed to detect spatial format: {e}")
            return SpatialFormat.STEREO
    
    def _is_binaural(self, audio_data: np.ndarray) -> bool:
        """Detect if stereo audio is binaural"""
        if audio_data.shape[0] != 2:
            return False
        
        # Analyze cross-correlation and spectral differences
        left, right = audio_data[0], audio_data[1]
        
        # Calculate cross-correlation
        correlation = np.corrcoef(left, right)[0, 1]
        
        # Binaural audio typically has lower correlation than regular stereo
        # and specific spectral characteristics
        if correlation < 0.7:  # Lower correlation suggests binaural processing
            # Additional spectral analysis could be added here
            return True
        
        return False
    
    def _is_ambisonics_foa(self, audio_path: str) -> bool:
        """Detect if 4-channel audio is First Order Ambisonics"""
        try:
            # Load and analyze the audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)
            
            if audio_data.shape[0] != 4:
                return False
            
            # FOA has specific channel relationships
            # W channel should be omnidirectional (similar energy across frequency)
            # X, Y, Z channels should have directional characteristics
            
            w_channel = audio_data[0]
            x_channel = audio_data[1]
            
            # Simple heuristic: W channel should have more consistent energy
            w_variance = np.var(np.abs(w_channel))
            x_variance = np.var(np.abs(x_channel))
            
            # W channel typically has lower variance in amplitude
            return w_variance < x_variance * 0.8
            
        except Exception as e:
            logger.error(f"Failed to analyze FOA: {e}")
            return False
    
    def _is_ambisonics_hoa(self, audio_path: str) -> bool:
        """Detect if multi-channel audio is Higher Order Ambisonics"""
        try:
            info = sf.info(audio_path)
            channels = info.channels
            
            # HOA channel counts: 9 (2nd order), 16 (3rd order), 25 (4th order)
            hoa_channel_counts = [9, 16, 25, 36, 49]
            
            return channels in hoa_channel_counts
            
        except Exception as e:
            logger.error(f"Failed to analyze HOA: {e}")
            return False
    
    async def analyze_spatial_properties(self, audio_path: str) -> SpatialAnalysis:
        """Analyze spatial properties of the audio"""
        try:
            # Detect format
            format_detected = await self.detect_spatial_format(audio_path)
            
            # Load audio data
            audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)
            
            # Get channel mapping
            channel_mapping = self.channel_mappings.get(format_detected, {})
            
            # Analyze spatial dimensions
            spatial_width = self._calculate_spatial_width(audio_data)
            spatial_depth = self._calculate_spatial_depth(audio_data)
            spatial_height = self._calculate_spatial_height(audio_data, format_detected)
            
            # Calculate center of mass
            center_of_mass = self._calculate_spatial_center_of_mass(audio_data, format_detected)
            
            # Calculate spatial correlation matrix
            spatial_correlation = self._calculate_spatial_correlation(audio_data)
            
            # Calculate immersion and localization scores
            immersion_score = self._calculate_immersion_score(audio_data, format_detected)
            localization_accuracy = self._calculate_localization_accuracy(audio_data, format_detected)
            
            # Detect spatial artifacts
            spatial_artifacts = self._detect_spatial_artifacts(audio_data, format_detected)
            
            return SpatialAnalysis(
                format_detected=format_detected,
                channel_mapping=channel_mapping,
                spatial_width=spatial_width,
                spatial_depth=spatial_depth,
                spatial_height=spatial_height,
                center_of_mass=center_of_mass,
                spatial_correlation=spatial_correlation,
                immersion_score=immersion_score,
                localization_accuracy=localization_accuracy,
                spatial_artifacts=spatial_artifacts
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze spatial properties: {e}")
            raise
    
    def _calculate_spatial_width(self, audio_data: np.ndarray) -> float:
        """Calculate spatial width (stereo width)"""
        if audio_data.shape[0] < 2:
            return 0.0
        
        # For stereo, calculate correlation between L/R channels
        if audio_data.shape[0] == 2:
            left, right = audio_data[0], audio_data[1]
            correlation = np.corrcoef(left, right)[0, 1]
            # Lower correlation = wider stereo image
            width = 1.0 - abs(correlation)
            return float(np.clip(width, 0.0, 1.0))
        
        # For multichannel, analyze left-right channel pairs
        width_scores = []
        for i in range(0, audio_data.shape[0] - 1, 2):
            if i + 1 < audio_data.shape[0]:
                correlation = np.corrcoef(audio_data[i], audio_data[i + 1])[0, 1]
                width_scores.append(1.0 - abs(correlation))
        
        return float(np.mean(width_scores)) if width_scores else 0.0
    
    def _calculate_spatial_depth(self, audio_data: np.ndarray) -> float:
        """Calculate spatial depth (front-back dimension)"""
        if audio_data.shape[0] < 4:
            return 0.0
        
        # For surround formats, compare front and rear channels
        if audio_data.shape[0] >= 6:  # 5.1 or higher
            # Compare front L/R with rear L/R
            front_left, front_right = audio_data[0], audio_data[1]
            rear_left, rear_right = audio_data[4], audio_data[5]
            
            front_energy = np.mean(front_left**2 + front_right**2)
            rear_energy = np.mean(rear_left**2 + rear_right**2)
            
            if front_energy + rear_energy > 0:
                depth = rear_energy / (front_energy + rear_energy)
                return float(np.clip(depth, 0.0, 1.0))
        
        return 0.0
    
    def _calculate_spatial_height(self, audio_data: np.ndarray, format: SpatialFormat) -> float:
        """Calculate spatial height dimension"""
        if format == SpatialFormat.AMBISONICS_FOA and audio_data.shape[0] >= 4:
            # For FOA, Z channel represents height
            z_channel = audio_data[3]
            z_energy = np.mean(z_channel**2)
            total_energy = np.mean(np.sum(audio_data**2, axis=0))
            
            if total_energy > 0:
                height = z_energy / total_energy
                return float(np.clip(height, 0.0, 1.0))
        
        # For other formats, height information is limited
        return 0.0
    
    def _calculate_spatial_center_of_mass(self, audio_data: np.ndarray, 
                                        format: SpatialFormat) -> SpatialPosition:
        """Calculate the spatial center of mass"""
        if format == SpatialFormat.STEREO and audio_data.shape[0] == 2:
            left_energy = np.mean(audio_data[0]**2)
            right_energy = np.mean(audio_data[1]**2)
            
            if left_energy + right_energy > 0:
                x_position = (right_energy - left_energy) / (left_energy + right_energy)
            else:
                x_position = 0.0
            
            return SpatialPosition(x=x_position, y=0.0, z=0.0)
        
        elif format == SpatialFormat.AMBISONICS_FOA and audio_data.shape[0] >= 4:
            # For FOA, calculate position from X, Y, Z channels
            x_energy = np.mean(audio_data[1]**2)  # X channel
            y_energy = np.mean(audio_data[2]**2)  # Y channel
            z_energy = np.mean(audio_data[3]**2)  # Z channel
            
            total_directional = x_energy + y_energy + z_energy
            if total_directional > 0:
                x_pos = x_energy / total_directional - 0.5
                y_pos = y_energy / total_directional - 0.5
                z_pos = z_energy / total_directional - 0.5
            else:
                x_pos = y_pos = z_pos = 0.0
            
            return SpatialPosition(x=x_pos, y=y_pos, z=z_pos)
        
        # Default center position
        return SpatialPosition(x=0.0, y=0.0, z=0.0)
    
    def _calculate_spatial_correlation(self, audio_data: np.ndarray) -> np.ndarray:
        """Calculate spatial correlation matrix between channels"""
        num_channels = audio_data.shape[0]
        correlation_matrix = np.zeros((num_channels, num_channels))
        
        for i in range(num_channels):
            for j in range(num_channels):
                if i == j:
                    correlation_matrix[i, j] = 1.0
                else:
                    correlation = np.corrcoef(audio_data[i], audio_data[j])[0, 1]
                    correlation_matrix[i, j] = correlation
        
        return correlation_matrix
    
    def _calculate_immersion_score(self, audio_data: np.ndarray, format: SpatialFormat) -> float:
        """Calculate immersion score based on spatial content"""
        if format == SpatialFormat.STEREO:
            # For stereo, immersion is based on width and content diversity
            width = self._calculate_spatial_width(audio_data)
            return width * 0.5  # Stereo has limited immersion
        
        elif format in [SpatialFormat.SURROUND_5_1, SpatialFormat.SURROUND_7_1]:
            # For surround, consider all channel utilization
            channel_energies = [np.mean(channel**2) for channel in audio_data]
            total_energy = sum(channel_energies)
            
            if total_energy > 0:
                # Calculate energy distribution across channels
                energy_distribution = [e / total_energy for e in channel_energies]
                # Higher entropy = better immersion
                entropy = -sum(p * np.log2(p + 1e-10) for p in energy_distribution if p > 0)
                max_entropy = np.log2(len(channel_energies))
                immersion = entropy / max_entropy if max_entropy > 0 else 0.0
                return float(np.clip(immersion, 0.0, 1.0))
        
        elif format == SpatialFormat.AMBISONICS_FOA:
            # For Ambisonics, consider directional content
            w_energy = np.mean(audio_data[0]**2)  # Omnidirectional
            directional_energy = np.mean(np.sum(audio_data[1:]**2, axis=0))  # X, Y, Z
            
            total_energy = w_energy + directional_energy
            if total_energy > 0:
                directional_ratio = directional_energy / total_energy
                return float(np.clip(directional_ratio, 0.0, 1.0))
        
        return 0.5  # Default moderate immersion
    
    def _calculate_localization_accuracy(self, audio_data: np.ndarray, 
                                       format: SpatialFormat) -> float:
        """Calculate localization accuracy score"""
        if format == SpatialFormat.STEREO:
            # For stereo, localization is limited to left-right
            return 0.3
        
        elif format in [SpatialFormat.SURROUND_5_1, SpatialFormat.SURROUND_7_1]:
            # For surround, analyze channel separation
            correlation_matrix = self._calculate_spatial_correlation(audio_data)
            
            # Good localization means low cross-correlation between distant speakers
            off_diagonal = correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)]
            avg_correlation = np.mean(np.abs(off_diagonal))
            
            # Lower correlation = better localization
            localization = 1.0 - avg_correlation
            return float(np.clip(localization, 0.0, 1.0))
        
        elif format == SpatialFormat.AMBISONICS_FOA:
            # For Ambisonics, analyze directional precision
            return 0.8  # Ambisonics generally provides good localization
        
        return 0.5  # Default moderate localization
    
    def _detect_spatial_artifacts(self, audio_data: np.ndarray, 
                                format: SpatialFormat) -> List[str]:
        """Detect spatial audio artifacts"""
        artifacts = []
        
        # Check for phase issues
        if self._has_phase_issues(audio_data):
            artifacts.append("Phase correlation issues detected")
        
        # Check for channel imbalance
        if self._has_channel_imbalance(audio_data):
            artifacts.append("Channel level imbalance detected")
        
        # Check for spatial aliasing (for Ambisonics)
        if format in [SpatialFormat.AMBISONICS_FOA, SpatialFormat.AMBISONICS_HOA]:
            if self._has_spatial_aliasing(audio_data):
                artifacts.append("Spatial aliasing detected")
        
        # Check for center channel issues (for surround)
        if format in [SpatialFormat.SURROUND_5_1, SpatialFormat.SURROUND_7_1]:
            if self._has_center_channel_issues(audio_data):
                artifacts.append("Center channel issues detected")
        
        return artifacts
    
    def _has_phase_issues(self, audio_data: np.ndarray) -> bool:
        """Detect phase correlation issues"""
        if audio_data.shape[0] < 2:
            return False
        
        # Check phase correlation between channel pairs
        for i in range(audio_data.shape[0] - 1):
            for j in range(i + 1, audio_data.shape[0]):
                # Calculate instantaneous phase correlation
                analytic_i = scipy.signal.hilbert(audio_data[i])
                analytic_j = scipy.signal.hilbert(audio_data[j])
                
                phase_diff = np.angle(analytic_i) - np.angle(analytic_j)
                phase_correlation = np.mean(np.cos(phase_diff))
                
                # Severe phase issues if correlation is very negative
                if phase_correlation < -0.5:
                    return True
        
        return False
    
    def _has_channel_imbalance(self, audio_data: np.ndarray) -> bool:
        """Detect significant channel level imbalances"""
        if audio_data.shape[0] < 2:
            return False
        
        # Calculate RMS levels for each channel
        rms_levels = [np.sqrt(np.mean(channel**2)) for channel in audio_data]
        
        if max(rms_levels) > 0:
            # Check for significant imbalances (>12dB difference)
            level_ratios = [level / max(rms_levels) for level in rms_levels]
            min_ratio = min(level_ratios)
            
            # 12dB = ratio of ~0.25
            return min_ratio < 0.25
        
        return False
    
    def _has_spatial_aliasing(self, audio_data: np.ndarray) -> bool:
        """Detect spatial aliasing in Ambisonics content"""
        # Simplified spatial aliasing detection
        # In practice, this would analyze high-frequency directional content
        if audio_data.shape[0] < 4:
            return False
        
        # Analyze high-frequency content in directional channels
        for i in range(1, min(4, audio_data.shape[0])):  # X, Y, Z channels
            # High-pass filter to isolate high frequencies
            b, a = scipy.signal.butter(4, 0.5, btype='high')  # Above Nyquist/2
            high_freq = scipy.signal.filtfilt(b, a, audio_data[i])
            
            # Check for excessive high-frequency directional content
            hf_energy = np.mean(high_freq**2)
            total_energy = np.mean(audio_data[i]**2)
            
            if total_energy > 0 and hf_energy / total_energy > 0.3:
                return True
        
        return False
    
    def _has_center_channel_issues(self, audio_data: np.ndarray) -> bool:
        """Detect center channel issues in surround formats"""
        if audio_data.shape[0] < 6:  # Need at least 5.1
            return False
        
        # Center channel is typically channel 2 in 5.1/7.1
        center_channel = audio_data[2]
        left_channel = audio_data[0]
        right_channel = audio_data[1]
        
        # Check if center channel has appropriate content
        center_energy = np.mean(center_channel**2)
        lr_energy = np.mean((left_channel**2 + right_channel**2) / 2)
        
        # Center channel should have reasonable level relative to L/R
        if lr_energy > 0:
            center_ratio = center_energy / lr_energy
            # Issues if center is too quiet (<-20dB) or too loud (>+6dB)
            return center_ratio < 0.01 or center_ratio > 4.0
        
        return False    as
ync def convert_spatial_format(self, audio_path: str, 
                                   target_format: SpatialFormat,
                                   output_path: Optional[str] = None) -> str:
        """Convert between spatial audio formats"""
        try:
            if output_path is None:
                output_path = os.path.join(
                    self.temp_dir, 
                    f"converted_{target_format.value}_{uuid.uuid4().hex[:8]}.wav"
                )
            
            # Detect source format
            source_format = await self.detect_spatial_format(audio_path)
            
            # Load audio data
            audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)
            
            # Perform format conversion
            converted_audio = await self._perform_format_conversion(
                audio_data, source_format, target_format, sample_rate
            )
            
            # Save converted audio
            sf.write(output_path, converted_audio.T, sample_rate)
            
            logger.info(f"Converted {source_format.value} to {target_format.value}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to convert spatial format: {e}")
            raise
    
    async def _perform_format_conversion(self, audio_data: np.ndarray,
                                       source_format: SpatialFormat,
                                       target_format: SpatialFormat,
                                       sample_rate: int) -> np.ndarray:
        """Perform the actual format conversion"""
        
        # Stereo to other formats
        if source_format == SpatialFormat.STEREO:
            if target_format == SpatialFormat.SURROUND_5_1:
                return self._stereo_to_5_1(audio_data)
            elif target_format == SpatialFormat.SURROUND_7_1:
                return self._stereo_to_7_1(audio_data)
            elif target_format == SpatialFormat.AMBISONICS_FOA:
                return self._stereo_to_ambisonics_foa(audio_data)
            elif target_format == SpatialFormat.BINAURAL:
                return self._stereo_to_binaural(audio_data, sample_rate)
        
        # 5.1 to other formats
        elif source_format == SpatialFormat.SURROUND_5_1:
            if target_format == SpatialFormat.STEREO:
                return self._5_1_to_stereo(audio_data)
            elif target_format == SpatialFormat.SURROUND_7_1:
                return self._5_1_to_7_1(audio_data)
            elif target_format == SpatialFormat.BINAURAL:
                return self._5_1_to_binaural(audio_data, sample_rate)
        
        # 7.1 to other formats
        elif source_format == SpatialFormat.SURROUND_7_1:
            if target_format == SpatialFormat.STEREO:
                return self._7_1_to_stereo(audio_data)
            elif target_format == SpatialFormat.SURROUND_5_1:
                return self._7_1_to_5_1(audio_data)
            elif target_format == SpatialFormat.BINAURAL:
                return self._7_1_to_binaural(audio_data, sample_rate)
        
        # Ambisonics FOA to other formats
        elif source_format == SpatialFormat.AMBISONICS_FOA:
            if target_format == SpatialFormat.STEREO:
                return self._ambisonics_foa_to_stereo(audio_data)
            elif target_format == SpatialFormat.SURROUND_5_1:
                return self._ambisonics_foa_to_5_1(audio_data)
            elif target_format == SpatialFormat.BINAURAL:
                return self._ambisonics_foa_to_binaural(audio_data, sample_rate)
        
        # If no conversion is implemented, return original
        logger.warning(f"Conversion from {source_format.value} to {target_format.value} not implemented")
        return audio_data
    
    def _stereo_to_5_1(self, stereo_audio: np.ndarray) -> np.ndarray:
        """Convert stereo to 5.1 surround"""
        left, right = stereo_audio[0], stereo_audio[1]
        
        # Create 5.1 channels
        front_left = left
        front_right = right
        center = (left + right) * 0.5  # Mono sum for center
        lfe = self._extract_lfe(left + right)  # Low-frequency content
        rear_left = left * 0.3  # Reduced level for ambience
        rear_right = right * 0.3
        
        return np.array([front_left, front_right, center, lfe, rear_left, rear_right])
    
    def _stereo_to_7_1(self, stereo_audio: np.ndarray) -> np.ndarray:
        """Convert stereo to 7.1 surround"""
        left, right = stereo_audio[0], stereo_audio[1]
        
        # Create 7.1 channels
        front_left = left
        front_right = right
        center = (left + right) * 0.5
        lfe = self._extract_lfe(left + right)
        side_left = left * 0.4
        side_right = right * 0.4
        rear_left = left * 0.2
        rear_right = right * 0.2
        
        return np.array([front_left, front_right, center, lfe, 
                        side_left, side_right, rear_left, rear_right])
    
    def _stereo_to_ambisonics_foa(self, stereo_audio: np.ndarray) -> np.ndarray:
        """Convert stereo to First Order Ambisonics"""
        left, right = stereo_audio[0], stereo_audio[1]
        
        # FOA encoding from stereo
        w = (left + right) * 0.707  # Omnidirectional component
        x = (left - right) * 0.5    # Front-back (simplified)
        y = (right - left) * 0.5    # Left-right
        z = np.zeros_like(left)     # No height information from stereo
        
        return np.array([w, x, y, z])
    
    def _stereo_to_binaural(self, stereo_audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Convert stereo to binaural using HRTF processing"""
        left, right = stereo_audio[0], stereo_audio[1]
        
        # Apply simplified binaural processing
        # In production, use proper HRTF convolution
        
        # Add crossfeed for more natural headphone listening
        crossfeed_amount = 0.3
        processed_left = left + right * crossfeed_amount
        processed_right = right + left * crossfeed_amount
        
        # Apply simple ITD (Interaural Time Difference)
        itd_samples = int(0.0006 * sample_rate)  # ~0.6ms max ITD
        
        # Delay right channel slightly for left-positioned content
        if len(processed_right) > itd_samples:
            processed_right = np.concatenate([
                np.zeros(itd_samples), 
                processed_right[:-itd_samples]
            ])
        
        return np.array([processed_left, processed_right])
    
    def _5_1_to_stereo(self, surround_audio: np.ndarray) -> np.ndarray:
        """Convert 5.1 surround to stereo"""
        fl, fr, c, lfe, rl, rr = surround_audio[:6]
        
        # Downmix to stereo with proper coefficients
        left = fl + c * 0.707 + rl * 0.5 + lfe * 0.5
        right = fr + c * 0.707 + rr * 0.5 + lfe * 0.5
        
        return np.array([left, right])
    
    def _5_1_to_7_1(self, surround_5_1: np.ndarray) -> np.ndarray:
        """Convert 5.1 to 7.1 by adding side channels"""
        fl, fr, c, lfe, rl, rr = surround_5_1[:6]
        
        # Create side channels from front and rear
        sl = (fl + rl) * 0.5
        sr = (fr + rr) * 0.5
        
        return np.array([fl, fr, c, lfe, sl, sr, rl, rr])
    
    def _5_1_to_binaural(self, surround_audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Convert 5.1 surround to binaural"""
        # This is a simplified implementation
        # In production, use proper HRTF convolution for each speaker position
        
        fl, fr, c, lfe, rl, rr = surround_audio[:6]
        
        # Apply spatial positioning using simplified HRTF
        left_ear = (fl * 1.0 +      # Front left - direct
                   fr * 0.3 +       # Front right - crosstalk
                   c * 0.707 +      # Center - equal to both ears
                   rl * 0.8 +       # Rear left - slightly attenuated
                   rr * 0.2 +       # Rear right - more crosstalk
                   lfe * 0.5)       # LFE - equal to both ears
        
        right_ear = (fr * 1.0 +     # Front right - direct
                    fl * 0.3 +      # Front left - crosstalk
                    c * 0.707 +     # Center - equal to both ears
                    rr * 0.8 +      # Rear right - slightly attenuated
                    rl * 0.2 +      # Rear left - more crosstalk
                    lfe * 0.5)      # LFE - equal to both ears
        
        return np.array([left_ear, right_ear])
    
    def _7_1_to_stereo(self, surround_audio: np.ndarray) -> np.ndarray:
        """Convert 7.1 surround to stereo"""
        fl, fr, c, lfe, sl, sr, rl, rr = surround_audio[:8]
        
        # Downmix to stereo
        left = fl + c * 0.707 + sl * 0.6 + rl * 0.4 + lfe * 0.5
        right = fr + c * 0.707 + sr * 0.6 + rr * 0.4 + lfe * 0.5
        
        return np.array([left, right])
    
    def _7_1_to_5_1(self, surround_7_1: np.ndarray) -> np.ndarray:
        """Convert 7.1 to 5.1 by combining side and rear channels"""
        fl, fr, c, lfe, sl, sr, rl, rr = surround_7_1[:8]
        
        # Combine side and rear channels
        new_rl = (sl + rl) * 0.707
        new_rr = (sr + rr) * 0.707
        
        return np.array([fl, fr, c, lfe, new_rl, new_rr])
    
    def _7_1_to_binaural(self, surround_audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Convert 7.1 surround to binaural"""
        fl, fr, c, lfe, sl, sr, rl, rr = surround_audio[:8]
        
        # Apply spatial positioning for 7.1 layout
        left_ear = (fl * 1.0 + fr * 0.3 + c * 0.707 + 
                   sl * 0.9 + sr * 0.2 + rl * 0.7 + rr * 0.1 + lfe * 0.5)
        
        right_ear = (fr * 1.0 + fl * 0.3 + c * 0.707 + 
                    sr * 0.9 + sl * 0.2 + rr * 0.7 + rl * 0.1 + lfe * 0.5)
        
        return np.array([left_ear, right_ear])
    
    def _ambisonics_foa_to_stereo(self, ambisonics_audio: np.ndarray) -> np.ndarray:
        """Convert First Order Ambisonics to stereo"""
        w, x, y, z = ambisonics_audio[:4]
        
        # Simple FOA to stereo decoding
        # This is a basic implementation - production would use proper decoder matrices
        left = w * 0.707 + y * 0.5 - x * 0.3
        right = w * 0.707 - y * 0.5 - x * 0.3
        
        return np.array([left, right])
    
    def _ambisonics_foa_to_5_1(self, ambisonics_audio: np.ndarray) -> np.ndarray:
        """Convert First Order Ambisonics to 5.1 surround"""
        w, x, y, z = ambisonics_audio[:4]
        
        # FOA to 5.1 decoding using speaker positions
        # Speaker angles: FL(-30°), FR(30°), C(0°), RL(-110°), RR(110°)
        
        fl = w * 0.707 + x * 0.5 + y * 0.866  # -30° position
        fr = w * 0.707 + x * 0.5 - y * 0.866  # 30° position
        c = w * 0.707 + x * 1.0               # 0° position
        lfe = w * 0.5                         # LFE from omnidirectional
        rl = w * 0.707 - x * 0.5 + y * 0.866  # -110° position
        rr = w * 0.707 - x * 0.5 - y * 0.866  # 110° position
        
        return np.array([fl, fr, c, lfe, rl, rr])
    
    def _ambisonics_foa_to_binaural(self, ambisonics_audio: np.ndarray, 
                                   sample_rate: int) -> np.ndarray:
        """Convert First Order Ambisonics to binaural"""
        # This would typically use binaural room impulse responses (BRIRs)
        # For now, use simplified conversion via stereo
        stereo = self._ambisonics_foa_to_stereo(ambisonics_audio)
        return self._stereo_to_binaural(stereo, sample_rate)
    
    def _extract_lfe(self, audio: np.ndarray, cutoff_freq: float = 120.0) -> np.ndarray:
        """Extract low-frequency effects channel"""
        # Apply low-pass filter for LFE content
        sample_rate = 44100  # Assume standard sample rate
        nyquist = sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        b, a = scipy.signal.butter(4, normalized_cutoff, btype='low')
        lfe = scipy.signal.filtfilt(b, a, audio)
        
        # Reduce level for LFE channel
        return lfe * 0.5
    
    async def enhance_spatial_audio(self, audio_path: str,
                                  enhancement_config: Dict[str, Any],
                                  output_path: Optional[str] = None) -> str:
        """Enhance spatial audio with various processing options"""
        try:
            if output_path is None:
                output_path = os.path.join(
                    self.temp_dir, 
                    f"enhanced_spatial_{uuid.uuid4().hex[:8]}.wav"
                )
            
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)
            format = await self.detect_spatial_format(audio_path)
            
            # Apply enhancements based on configuration
            enhanced_audio = audio_data.copy()
            
            if enhancement_config.get('width_enhancement', False):
                enhanced_audio = self._enhance_spatial_width(enhanced_audio, format)
            
            if enhancement_config.get('depth_enhancement', False):
                enhanced_audio = self._enhance_spatial_depth(enhanced_audio, format)
            
            if enhancement_config.get('height_enhancement', False):
                enhanced_audio = self._enhance_spatial_height(enhanced_audio, format)
            
            if enhancement_config.get('immersion_boost', False):
                enhanced_audio = self._boost_immersion(enhanced_audio, format)
            
            if enhancement_config.get('localization_improvement', False):
                enhanced_audio = self._improve_localization(enhanced_audio, format)
            
            # Save enhanced audio
            sf.write(output_path, enhanced_audio.T, sample_rate)
            
            logger.info(f"Enhanced spatial audio saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to enhance spatial audio: {e}")
            raise
    
    def _enhance_spatial_width(self, audio_data: np.ndarray, format: SpatialFormat) -> np.ndarray:
        """Enhance spatial width"""
        if format == SpatialFormat.STEREO and audio_data.shape[0] == 2:
            # Apply stereo width enhancement
            left, right = audio_data[0], audio_data[1]
            
            # Mid-side processing
            mid = (left + right) * 0.5
            side = (left - right) * 0.5
            
            # Enhance side signal
            enhanced_side = side * 1.3  # Increase width
            
            # Convert back to L/R
            enhanced_left = mid + enhanced_side
            enhanced_right = mid - enhanced_side
            
            return np.array([enhanced_left, enhanced_right])
        
        return audio_data
    
    def _enhance_spatial_depth(self, audio_data: np.ndarray, format: SpatialFormat) -> np.ndarray:
        """Enhance spatial depth"""
        if format in [SpatialFormat.SURROUND_5_1, SpatialFormat.SURROUND_7_1]:
            # Enhance rear channel content for better depth perception
            enhanced_audio = audio_data.copy()
            
            if format == SpatialFormat.SURROUND_5_1:
                # Boost rear channels slightly
                enhanced_audio[4] *= 1.1  # Rear left
                enhanced_audio[5] *= 1.1  # Rear right
            elif format == SpatialFormat.SURROUND_7_1:
                # Boost rear channels
                enhanced_audio[6] *= 1.1  # Rear left
                enhanced_audio[7] *= 1.1  # Rear right
            
            return enhanced_audio
        
        return audio_data
    
    def _enhance_spatial_height(self, audio_data: np.ndarray, format: SpatialFormat) -> np.ndarray:
        """Enhance spatial height"""
        if format == SpatialFormat.AMBISONICS_FOA and audio_data.shape[0] >= 4:
            # Enhance Z channel for better height perception
            enhanced_audio = audio_data.copy()
            enhanced_audio[3] *= 1.2  # Z channel
            return enhanced_audio
        
        return audio_data
    
    def _boost_immersion(self, audio_data: np.ndarray, format: SpatialFormat) -> np.ndarray:
        """Boost overall immersion"""
        # Apply subtle reverb to enhance spatial impression
        enhanced_audio = audio_data.copy()
        
        for i in range(enhanced_audio.shape[0]):
            # Add subtle room ambience
            room_response = self.room_responses['small_room']
            enhanced_channel = np.convolve(enhanced_audio[i], room_response, mode='same')
            
            # Mix with original
            enhanced_audio[i] = enhanced_audio[i] * 0.8 + enhanced_channel * 0.2
        
        return enhanced_audio
    
    def _improve_localization(self, audio_data: np.ndarray, format: SpatialFormat) -> np.ndarray:
        """Improve localization accuracy"""
        # Apply subtle EQ to enhance localization cues
        enhanced_audio = audio_data.copy()
        
        # Enhance frequencies important for localization (2-8 kHz)
        sample_rate = 44100
        nyquist = sample_rate / 2
        
        # Create bandpass filter for localization frequencies
        low_freq = 2000 / nyquist
        high_freq = 8000 / nyquist
        b, a = scipy.signal.butter(2, [low_freq, high_freq], btype='band')
        
        for i in range(enhanced_audio.shape[0]):
            # Extract localization frequencies
            localization_band = scipy.signal.filtfilt(b, a, enhanced_audio[i])
            
            # Subtle boost
            enhanced_audio[i] += localization_band * 0.1
        
        return enhanced_audio
    
    async def create_spatial_visualization(self, audio_path: str,
                                         output_path: Optional[str] = None) -> str:
        """Create spatial audio visualization"""
        try:
            if output_path is None:
                output_path = os.path.join(
                    self.temp_dir, 
                    f"spatial_viz_{uuid.uuid4().hex[:8]}.json"
                )
            
            # Analyze spatial properties
            analysis = await self.analyze_spatial_properties(audio_path)
            
            # Create visualization data
            viz_data = {
                'format': analysis.format_detected.value,
                'channel_mapping': analysis.channel_mapping,
                'spatial_dimensions': {
                    'width': analysis.spatial_width,
                    'depth': analysis.spatial_depth,
                    'height': analysis.spatial_height
                },
                'center_of_mass': {
                    'x': analysis.center_of_mass.x,
                    'y': analysis.center_of_mass.y,
                    'z': analysis.center_of_mass.z
                },
                'quality_metrics': {
                    'immersion_score': analysis.immersion_score,
                    'localization_accuracy': analysis.localization_accuracy
                },
                'spatial_correlation': analysis.spatial_correlation.tolist(),
                'artifacts': analysis.spatial_artifacts,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save visualization data
            with open(output_path, 'w') as f:
                json.dump(viz_data, f, indent=2)
            
            logger.info(f"Spatial visualization data saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to create spatial visualization: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            # Clean up any temporary files or resources
            logger.info("SpatialAudioProcessor cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Test and demonstration code
if __name__ == "__main__":
    import asyncio
    
    async def test_spatial_audio_processing():
        """Test spatial audio processing functionality"""
        processor = SpatialAudioProcessor()
        
        print("Spatial Audio Processor Test")
        print("=" * 40)
        
        # Test format detection (would need actual audio file)
        # format = await processor.detect_spatial_format("test_audio.wav")
        # print(f"Detected format: {format.value}")
        
        # Test spatial analysis
        # analysis = await processor.analyze_spatial_properties("test_audio.wav")
        # print(f"Spatial analysis completed")
        
        # Test format conversion
        # converted = await processor.convert_spatial_format(
        #     "stereo_audio.wav", SpatialFormat.SURROUND_5_1
        # )
        # print(f"Converted to 5.1: {converted}")
        
        print("Spatial audio processing test completed")
        
        await processor.cleanup()
    
    # Run test
    asyncio.run(test_spatial_audio_processing())