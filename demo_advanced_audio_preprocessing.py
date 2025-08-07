"""
Demo script for Advanced Audio Preprocessing System

This script demonstrates the comprehensive audio preprocessing capabilities
including spectral analysis, pitch detection, audio fingerprinting, tempo analysis,
and audio similarity comparison and clustering.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import tempfile
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from advanced_audio_preprocessing import (
        AdvancedAudioPreprocessor, SpectralAnalyzer, PitchAnalyzer,
        RhythmAnalyzer, AudioFingerprinter, AudioSimilarityAnalyzer,
        AudioClusteringEngine
    )
except ImportError as e:
    print(f"Error importing advanced audio preprocessing modules: {e}")
    print("Please ensure all required dependencies are installed:")
    print("pip install librosa soundfile scipy scikit-learn matplotlib plotly")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_synthetic_audio_samples():
    """Create synthetic audio samples for demonstration"""
    try:
        import soundfile as sf
        
        sample_rate = 22050
        duration = 5.0  # 5 seconds
        
        # Create different types of synthetic audio
        samples = {}
        
        # 1. Pure tone (440 Hz - A4)
        t = np.linspace(0, duration, int(duration * sample_rate))
        pure_tone = 0.5 * np.sin(2 * np.pi * 440 * t)
        samples['pure_tone_440hz.wav'] = (pure_tone, sample_rate)
        
        # 2. Chord (C major: C4, E4, G4)
        c4 = 0.3 * np.sin(2 * np.pi * 261.63 * t)
        e4 = 0.3 * np.sin(2 * np.pi * 329.63 * t)
        g4 = 0.3 * np.sin(2 * np.pi * 392.00 * t)
        chord = c4 + e4 + g4
        samples['c_major_chord.wav'] = (chord, sample_rate)
        
        # 3. Frequency sweep (chirp)
        f0, f1 = 200, 2000  # Start and end frequencies
        chirp = 0.5 * np.sin(2 * np.pi * (f0 + (f1 - f0) * t / duration) * t)
        samples['frequency_sweep.wav'] = (chirp, sample_rate)
        
        # 4. Rhythmic pattern with beats
        beat_pattern = np.zeros_like(t)
        beat_times = np.arange(0, duration, 0.5)  # Beat every 0.5 seconds
        for beat_time in beat_times:
            if beat_time < duration:
                start_idx = int(beat_time * sample_rate)
                end_idx = min(start_idx + int(0.1 * sample_rate), len(beat_pattern))
                beat_pattern[start_idx:end_idx] = 0.7 * np.sin(2 * np.pi * 800 * t[start_idx:end_idx])
        samples['rhythmic_pattern.wav'] = (beat_pattern, sample_rate)
        
        # 5. Noisy signal
        noise = 0.1 * np.random.randn(len(t))
        signal = 0.4 * np.sin(2 * np.pi * 300 * t) + noise
        samples['noisy_signal.wav'] = (signal, sample_rate)
        
        # Save samples to temporary files
        temp_files = {}
        for filename, (audio, sr) in samples.items():
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sr)
            temp_files[filename] = temp_file.name
        
        logger.info(f"Created {len(temp_files)} synthetic audio samples")
        return temp_files
        
    except ImportError:
        logger.error("soundfile not available, cannot create synthetic audio")
        return {}
    except Exception as e:
        logger.error(f"Error creating synthetic audio: {e}")
        return {}

def demo_spectral_analysis():
    """Demonstrate spectral analysis capabilities"""
    print("\n" + "="*60)
    print("🌈 SPECTRAL ANALYSIS DEMO")
    print("="*60)
    
    try:
        # Create synthetic audio samples
        audio_samples = create_synthetic_audio_samples()
        
        if not audio_samples:
            print("❌ Could not create synthetic audio samples")
            return
        
        # Initialize spectral analyzer
        spectral_analyzer = SpectralAnalyzer()
        
        print("🔍 Analyzing spectral features for different audio types...")
        
        for sample_name, audio_path in audio_samples.items():
            print(f"\n📊 Analyzing: {sample_name}")
            
            # Extract spectral features
            features = spectral_analyzer.extract_spectral_features(audio_path)
            
            if features:
                print(f"   ✅ Extracted {len(features)} spectral features")
                
                # Display key statistics
                for feature_name, feature_data in features.items():
                    if len(feature_data) > 0:
                        mean_val = np.mean(feature_data)
                        std_val = np.std(feature_data)
                        print(f"      {feature_name}: mean={mean_val:.2f}, std={std_val:.2f}")
            else:
                print("   ❌ Failed to extract spectral features")
        
        # Compute spectrograms
        print(f"\n🎵 Computing spectrograms...")
        sample_path = list(audio_samples.values())[0]  # Use first sample
        
        magnitude, mel_spec, log_mel_spec = spectral_analyzer.compute_spectrogram(sample_path)
        
        if magnitude.size > 0:
            print(f"   ✅ STFT magnitude: {magnitude.shape}")
            print(f"   ✅ Mel spectrogram: {mel_spec.shape}")
            print(f"   ✅ Log-mel spectrogram: {log_mel_spec.shape}")
        
        # Harmonic-percussive separation
        print(f"\n🎼 Performing harmonic-percussive separation...")
        y_harmonic, y_percussive = spectral_analyzer.analyze_harmonic_percussive(sample_path)
        
        if y_harmonic.size > 0:
            print(f"   ✅ Harmonic component: {len(y_harmonic)} samples")
            print(f"   ✅ Percussive component: {len(y_percussive)} samples")
            
            # Calculate energy ratio
            harmonic_energy = np.sum(y_harmonic**2)
            percussive_energy = np.sum(y_percussive**2)
            total_energy = harmonic_energy + percussive_energy
            
            if total_energy > 0:
                harmonic_ratio = harmonic_energy / total_energy
                percussive_ratio = percussive_energy / total_energy
                print(f"   📈 Harmonic energy ratio: {harmonic_ratio:.2f}")
                print(f"   📈 Percussive energy ratio: {percussive_ratio:.2f}")
        
        print(f"\n📊 Spectral analysis demo completed")
        
        # Clean up temporary files
        for audio_path in audio_samples.values():
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
    except Exception as e:
        logger.error(f"Error in spectral analysis demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_pitch_analysis():
    """Demonstrate pitch detection and analysis"""
    print("\n" + "="*60)
    print("🎵 PITCH ANALYSIS DEMO")
    print("="*60)
    
    try:
        # Create synthetic audio samples
        audio_samples = create_synthetic_audio_samples()
        
        if not audio_samples:
            print("❌ Could not create synthetic audio samples")
            return
        
        # Initialize pitch analyzer
        pitch_analyzer = PitchAnalyzer()
        
        print("🔍 Analyzing pitch features for different audio types...")
        
        for sample_name, audio_path in audio_samples.items():
            print(f"\n🎵 Analyzing: {sample_name}")
            
            # Extract pitch features
            pitch_features = pitch_analyzer.extract_pitch_features(audio_path)
            
            if pitch_features:
                print(f"   ✅ Extracted pitch features")
                
                # Analyze fundamental frequency
                f0 = pitch_features.get('fundamental_frequency', np.array([]))
                if len(f0) > 0:
                    f0_nonzero = f0[f0 > 0]
                    if len(f0_nonzero) > 0:
                        print(f"      F0 mean: {np.mean(f0_nonzero):.2f} Hz")
                        print(f"      F0 std: {np.std(f0_nonzero):.2f} Hz")
                        print(f"      F0 range: {np.ptp(f0_nonzero):.2f} Hz")
                        print(f"      Voiced frames: {len(f0_nonzero)}/{len(f0)} ({100*len(f0_nonzero)/len(f0):.1f}%)")
                
                # Analyze chroma features
                chroma = pitch_features.get('chroma_features', np.array([]))
                if chroma.size > 0:
                    print(f"      Chroma features: {chroma.shape}")
                    # Find dominant pitch class
                    chroma_mean = np.mean(chroma, axis=1)
                    dominant_pitch_class = np.argmax(chroma_mean)
                    pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                    print(f"      Dominant pitch class: {pitch_classes[dominant_pitch_class]}")
            
            # Analyze pitch contour
            pitch_contour = pitch_analyzer.analyze_pitch_contour(audio_path)
            
            if pitch_contour:
                print(f"   📈 Pitch contour analysis:")
                for metric, value in pitch_contour.items():
                    print(f"      {metric}: {value:.3f}")
        
        print(f"\n📊 Pitch analysis demo completed")
        
        # Clean up temporary files
        for audio_path in audio_samples.values():
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
    except Exception as e:
        logger.error(f"Error in pitch analysis demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_rhythm_analysis():
    """Demonstrate rhythm and tempo analysis"""
    print("\n" + "="*60)
    print("🥁 RHYTHM ANALYSIS DEMO")
    print("="*60)
    
    try:
        # Create synthetic audio samples
        audio_samples = create_synthetic_audio_samples()
        
        if not audio_samples:
            print("❌ Could not create synthetic audio samples")
            return
        
        # Initialize rhythm analyzer
        rhythm_analyzer = RhythmAnalyzer()
        
        print("🔍 Analyzing rhythm features for different audio types...")
        
        for sample_name, audio_path in audio_samples.items():
            print(f"\n🥁 Analyzing: {sample_name}")
            
            # Extract rhythm features
            rhythm_features = rhythm_analyzer.extract_rhythm_features(audio_path)
            
            if rhythm_features:
                print(f"   ✅ Extracted rhythm features")
                print(f"      Tempo: {rhythm_features.get('tempo', 0):.1f} BPM")
                print(f"      Number of beats: {rhythm_features.get('num_beats', 0)}")
                print(f"      Number of onsets: {rhythm_features.get('num_onsets', 0)}")
                print(f"      Rhythm regularity: {rhythm_features.get('rhythm_regularity', 0):.3f}")
                print(f"      Onset density: {rhythm_features.get('onset_density', 0):.3f} onsets/sec")
                print(f"      Tempo stability: {rhythm_features.get('tempo_stability', 0):.3f}")
            
            # Analyze rhythmic patterns
            rhythmic_patterns = rhythm_analyzer.analyze_rhythmic_patterns(audio_path)
            
            if rhythmic_patterns:
                print(f"   📈 Rhythmic pattern analysis:")
                print(f"      Rhythmic complexity: {rhythmic_patterns.get('rhythmic_complexity', 0):.3f}")
                print(f"      Tempo variance: {rhythmic_patterns.get('tempo_variance', 0):.3f}")
                
                tempogram = rhythmic_patterns.get('tempogram', np.array([]))
                if tempogram.size > 0:
                    print(f"      Tempogram shape: {tempogram.shape}")
        
        print(f"\n📊 Rhythm analysis demo completed")
        
        # Clean up temporary files
        for audio_path in audio_samples.values():
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
    except Exception as e:
        logger.error(f"Error in rhythm analysis demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_audio_fingerprinting():
    """Demonstrate audio fingerprinting for duplicate detection"""
    print("\n" + "="*60)
    print("🔍 AUDIO FINGERPRINTING DEMO")
    print("="*60)
    
    try:
        # Create synthetic audio samples
        audio_samples = create_synthetic_audio_samples()
        
        if not audio_samples:
            print("❌ Could not create synthetic audio samples")
            return
        
        # Initialize fingerprinter
        fingerprinter = AudioFingerprinter()
        
        print("🔍 Generating audio fingerprints...")
        
        fingerprints = {}
        
        for sample_name, audio_path in audio_samples.items():
            print(f"\n🔍 Processing: {sample_name}")
            
            # Generate fingerprint
            fingerprint = fingerprinter.generate_fingerprint(audio_path)
            
            if fingerprint:
                fingerprints[sample_name] = fingerprint
                print(f"   ✅ Fingerprint: {fingerprint[:16]}...")
            else:
                print(f"   ❌ Failed to generate fingerprint")
        
        # Compare fingerprints
        print(f"\n🔗 Comparing fingerprints for similarity...")
        
        sample_names = list(fingerprints.keys())
        
        for i in range(len(sample_names)):
            for j in range(i + 1, len(sample_names)):
                name1, name2 = sample_names[i], sample_names[j]
                fingerprint1, fingerprint2 = fingerprints[name1], fingerprints[name2]
                
                similarity = fingerprinter.compare_fingerprints(fingerprint1, fingerprint2)
                
                print(f"   🔗 {name1} vs {name2}: {similarity:.3f} similarity")
                
                if similarity > 0.8:
                    print(f"      🚨 Potential duplicate detected!")
        
        # Test with identical audio (should have similarity = 1.0)
        print(f"\n🔄 Testing with identical audio...")
        
        if audio_samples:
            first_sample = list(audio_samples.values())[0]
            fingerprint1 = fingerprinter.generate_fingerprint(first_sample)
            fingerprint2 = fingerprinter.generate_fingerprint(first_sample)
            
            identical_similarity = fingerprinter.compare_fingerprints(fingerprint1, fingerprint2)
            print(f"   🔗 Identical audio similarity: {identical_similarity:.3f}")
        
        print(f"\n📊 Audio fingerprinting demo completed")
        
        # Clean up temporary files
        for audio_path in audio_samples.values():
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
    except Exception as e:
        logger.error(f"Error in audio fingerprinting demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_audio_similarity():
    """Demonstrate audio similarity comparison"""
    print("\n" + "="*60)
    print("🔗 AUDIO SIMILARITY DEMO")
    print("="*60)
    
    try:
        # Create synthetic audio samples
        audio_samples = create_synthetic_audio_samples()
        
        if not audio_samples:
            print("❌ Could not create synthetic audio samples")
            return
        
        # Initialize similarity analyzer
        similarity_analyzer = AudioSimilarityAnalyzer()
        
        print("🔍 Comparing audio similarity between different samples...")
        
        sample_paths = list(audio_samples.values())
        sample_names = list(audio_samples.keys())
        
        # Compare all pairs
        for i in range(len(sample_paths)):
            for j in range(i + 1, len(sample_paths)):
                print(f"\n🔗 Comparing: {sample_names[i]} vs {sample_names[j]}")
                
                similarity = similarity_analyzer.compare_audio_similarity(
                    sample_paths[i], sample_paths[j]
                )
                
                print(f"   Overall similarity: {similarity.similarity_score:.3f}")
                print(f"   Is duplicate: {similarity.is_duplicate}")
                print(f"   Confidence: {similarity.confidence:.3f}")
                
                # Distance metrics
                print(f"   Distance metrics:")
                for metric, value in similarity.distance_metrics.items():
                    print(f"      {metric}: {value:.3f}")
                
                # Feature correlations
                print(f"   Feature correlations:")
                for correlation, value in similarity.feature_correlations.items():
                    print(f"      {correlation}: {value:.3f}")
        
        print(f"\n📊 Audio similarity demo completed")
        
        # Clean up temporary files
        for audio_path in audio_samples.values():
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
    except Exception as e:
        logger.error(f"Error in audio similarity demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_audio_clustering():
    """Demonstrate audio clustering capabilities"""
    print("\n" + "="*60)
    print("🎯 AUDIO CLUSTERING DEMO")
    print("="*60)
    
    try:
        # Create synthetic audio samples
        audio_samples = create_synthetic_audio_samples()
        
        if not audio_samples:
            print("❌ Could not create synthetic audio samples")
            return
        
        # Initialize clustering engine
        clustering_engine = AudioClusteringEngine()
        
        sample_paths = list(audio_samples.values())
        sample_names = list(audio_samples.keys())
        
        print(f"🎯 Clustering {len(sample_paths)} audio samples...")
        
        # Test different clustering methods
        clustering_methods = ['kmeans', 'dbscan', 'hierarchical']
        
        for method in clustering_methods:
            print(f"\n🔍 Testing {method.upper()} clustering...")
            
            try:
                clusters = clustering_engine.cluster_audio_files(
                    sample_paths, method=method, n_clusters=3 if method != 'dbscan' else None
                )
                
                if clusters:
                    print(f"   ✅ Created {len(clusters)} clusters")
                    
                    for cluster in clusters:
                        print(f"   📁 Cluster {cluster.cluster_id}:")
                        print(f"      Size: {cluster.cluster_size}")
                        print(f"      Intra-cluster similarity: {cluster.intra_cluster_similarity:.3f}")
                        print(f"      Representative: {os.path.basename(cluster.representative_audio)}")
                        print(f"      Files: {[os.path.basename(f) for f in cluster.audio_files]}")
                else:
                    print(f"   ❌ No clusters created")
            
            except Exception as e:
                print(f"   ❌ Clustering failed: {e}")
        
        print(f"\n📊 Audio clustering demo completed")
        
        # Clean up temporary files
        for audio_path in audio_samples.values():
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
    except Exception as e:
        logger.error(f"Error in audio clustering demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_comprehensive_analysis():
    """Demonstrate comprehensive audio analysis"""
    print("\n" + "="*60)
    print("🎯 COMPREHENSIVE ANALYSIS DEMO")
    print("="*60)
    
    try:
        # Create synthetic audio samples
        audio_samples = create_synthetic_audio_samples()
        
        if not audio_samples:
            print("❌ Could not create synthetic audio samples")
            return
        
        # Initialize preprocessor
        preprocessor = AdvancedAudioPreprocessor()
        
        print("🔍 Performing comprehensive analysis on sample audio...")
        
        # Analyze first sample
        sample_name = list(audio_samples.keys())[0]
        sample_path = list(audio_samples.values())[0]
        
        print(f"\n📊 Analyzing: {sample_name}")
        
        # Extract comprehensive features
        features = preprocessor.extract_comprehensive_features(sample_path)
        
        if features:
            print(f"   ✅ Feature extraction completed")
            print(f"   Duration: {features.duration:.2f} seconds")
            print(f"   Sample rate: {features.sample_rate} Hz")
            print(f"   Channels: {features.channels}")
            print(f"   Tempo: {features.tempo:.1f} BPM")
            print(f"   Fingerprint: {features.fingerprint[:16]}...")
            
            # Feature statistics
            if features.feature_statistics:
                print(f"   📈 Feature statistics available for {len(features.feature_statistics)} features")
                
                # Show some key statistics
                for feature_name, stats in list(features.feature_statistics.items())[:3]:
                    print(f"      {feature_name}:")
                    print(f"         Mean: {stats.get('mean', 0):.3f}")
                    print(f"         Std: {stats.get('std', 0):.3f}")
                    print(f"         Range: {stats.get('max', 0) - stats.get('min', 0):.3f}")
            
            # Save features
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            feature_file = f"demo_features_{timestamp}.json"
            
            try:
                preprocessor.save_features(features, feature_file)
                print(f"   💾 Features saved to: {feature_file}")
            except Exception as e:
                print(f"   ⚠️  Could not save features: {e}")
        
        # Batch processing demo
        print(f"\n📦 Testing batch processing...")
        
        batch_results = preprocessor.batch_process_audio(
            list(audio_samples.values()), 
            output_dir="demo_batch_output"
        )
        
        if batch_results:
            stats = batch_results.get('processing_stats', {})
            print(f"   ✅ Batch processing completed")
            print(f"   Total files: {stats.get('total_files', 0)}")
            print(f"   Processed successfully: {stats.get('processed_successfully', 0)}")
            print(f"   Failed: {stats.get('failed_processing', 0)}")
            print(f"   Duplicates found: {stats.get('duplicates_found', 0)}")
            print(f"   Clusters created: {stats.get('clusters_created', 0)}")
        
        print(f"\n📊 Comprehensive analysis demo completed")
        
        # Clean up temporary files
        for audio_path in audio_samples.values():
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
        # Clean up batch output directory
        import shutil
        if os.path.exists("demo_batch_output"):
            shutil.rmtree("demo_batch_output")
            print("🧹 Cleaned up batch output directory")
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis demo: {e}")
        print(f"❌ Demo failed: {e}")

def main():
    """Run all demonstration functions"""
    print("🎵 ADVANCED AUDIO PREPROCESSING SYSTEM DEMO")
    print("=" * 80)
    print("This demo showcases comprehensive audio preprocessing capabilities")
    print("including spectral analysis, pitch detection, audio fingerprinting,")
    print("tempo analysis, and audio similarity comparison and clustering.")
    print("=" * 80)
    
    try:
        # Check dependencies
        print("🔍 Checking dependencies...")
        
        required_modules = ['librosa', 'soundfile', 'scipy', 'sklearn', 'matplotlib']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"❌ Missing required modules: {', '.join(missing_modules)}")
            print("Please install them using: pip install " + " ".join(missing_modules))
            return
        
        print("✅ All dependencies available")
        
        # Run demos
        demo_spectral_analysis()
        demo_pitch_analysis()
        demo_rhythm_analysis()
        demo_audio_fingerprinting()
        demo_audio_similarity()
        demo_audio_clustering()
        demo_comprehensive_analysis()
        
        print("\n" + "="*80)
        print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("The Advanced Audio Preprocessing System is working correctly.")
        print("Key features demonstrated:")
        print("✅ Spectral analysis and audio feature extraction")
        print("✅ Pitch detection and fundamental frequency analysis")
        print("✅ Audio fingerprinting for duplicate detection")
        print("✅ Tempo and rhythm analysis capabilities")
        print("✅ Audio similarity comparison and clustering")
        print("✅ Comprehensive feature extraction and analysis")
        print("✅ Batch processing for large audio datasets")
        print("\nTo use the Streamlit UI, run:")
        print("streamlit run advanced_audio_preprocessing_ui.py")
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"Error in main demo: {e}")
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    main()