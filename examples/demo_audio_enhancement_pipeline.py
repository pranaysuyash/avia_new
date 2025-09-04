"""
Demo script for Audio Enhancement Pipeline
Task 117: Build comprehensive audio enhancement pipeline

This demo showcases the capabilities of the audio enhancement pipeline
with various audio scenarios and enhancement options.
"""

import os
import sys
import numpy as np
import librosa
import soundfile as sf
import tempfile
import shutil
from pathlib import Path
import json
import time
import matplotlib.pyplot as plt
from typing import List, Dict, Any

from audio_enhancement_pipeline import AudioEnhancementPipeline, EnhancementResult

class AudioEnhancementDemo:
    """Demo class for showcasing audio enhancement capabilities"""
    
    def __init__(self):
        """Initialize the demo"""
        self.demo_dir = tempfile.mkdtemp(prefix="audio_enhancement_demo_")
        self.pipeline = AudioEnhancementPipeline(temp_dir=self.demo_dir)
        self.sample_rate = 16000
        
        print("🎵 Audio Enhancement Pipeline Demo")
        print("=" * 50)
        print(f"Demo directory: {self.demo_dir}")
        print()
    
    def __del__(self):
        """Cleanup demo directory"""
        if hasattr(self, 'demo_dir') and os.path.exists(self.demo_dir):
            shutil.rmtree(self.demo_dir, ignore_errors=True)
    
    def create_demo_audio_files(self) -> Dict[str, str]:
        """Create various demo audio files with different characteristics"""
        print("📁 Creating demo audio files...")
        
        demo_files = {}
        duration = 3.0  # 3 seconds
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # 1. Clean speech-like audio
        print("  • Creating clean speech audio...")
        clean_audio = self._generate_speech_like_audio(t)
        clean_file = os.path.join(self.demo_dir, "01_clean_speech.wav")
        sf.write(clean_file, clean_audio, self.sample_rate)
        demo_files["clean"] = clean_file
        
        # 2. Noisy audio (speech + background noise)
        print("  • Creating noisy audio...")
        noise = np.random.normal(0, 0.08, samples)
        noisy_audio = clean_audio + noise
        noisy_file = os.path.join(self.demo_dir, "02_noisy_speech.wav")
        sf.write(noisy_file, noisy_audio, self.sample_rate)
        demo_files["noisy"] = noisy_file
        
        # 3. Clipped/distorted audio
        print("  • Creating clipped audio...")
        clipped_audio = np.clip(clean_audio * 2.5, -0.95, 0.95)
        clipped_file = os.path.join(self.demo_dir, "03_clipped_speech.wav")
        sf.write(clipped_file, clipped_audio, self.sample_rate)
        demo_files["clipped"] = clipped_file
        
        # 4. Very quiet audio
        print("  • Creating quiet audio...")
        quiet_audio = clean_audio * 0.05
        quiet_file = os.path.join(self.demo_dir, "04_quiet_speech.wav")
        sf.write(quiet_file, quiet_audio, self.sample_rate)
        demo_files["quiet"] = quiet_file
        
        # 5. Audio with dropouts/corrupted segments
        print("  • Creating audio with dropouts...")
        dropout_audio = clean_audio.copy()
        # Add some dropouts
        dropout_locations = [int(0.5 * self.sample_rate), int(1.5 * self.sample_rate), int(2.2 * self.sample_rate)]
        for loc in dropout_locations:
            if loc + 800 < len(dropout_audio):
                dropout_audio[loc:loc+800] *= 0.01  # Severe volume drop
        dropout_file = os.path.join(self.demo_dir, "05_dropout_speech.wav")
        sf.write(dropout_file, dropout_audio, self.sample_rate)
        demo_files["dropout"] = dropout_file
        
        # 6. Low-quality compressed audio simulation
        print("  • Creating low-quality audio...")
        # Simulate compression artifacts by reducing bit depth and adding quantization noise
        quantized_audio = np.round(clean_audio * 32) / 32  # Simulate 5-bit quantization
        quantization_noise = np.random.uniform(-1/64, 1/64, samples)
        lowqual_audio = quantized_audio + quantization_noise
        lowqual_file = os.path.join(self.demo_dir, "06_lowquality_speech.wav")
        sf.write(lowqual_file, lowqual_audio, self.sample_rate)
        demo_files["lowquality"] = lowqual_file
        
        print(f"  ✅ Created {len(demo_files)} demo audio files")
        print()
        
        return demo_files
    
    def _generate_speech_like_audio(self, t: np.ndarray) -> np.ndarray:
        """Generate realistic speech-like audio signal"""
        # Simulate formant frequencies for speech
        formants = [
            (700, 0.3),   # F1 - vowel height
            (1220, 0.25), # F2 - vowel frontness
            (2600, 0.2),  # F3 - lip rounding
            (3400, 0.15), # F4 - consonant clarity
        ]
        
        speech_signal = np.zeros_like(t)
        
        # Add formant frequencies with some modulation
        for freq, amplitude in formants:
            # Add slight frequency modulation to make it more natural
            freq_mod = freq * (1 + 0.05 * np.sin(2 * np.pi * 3 * t))
            speech_signal += amplitude * np.sin(2 * np.pi * freq_mod * t)
        
        # Add amplitude envelope to simulate speech patterns
        # Create speech-like envelope with pauses
        envelope = np.ones_like(t)
        
        # Add some pauses
        pause_times = [0.8, 1.6, 2.4]  # Pause locations
        for pause_time in pause_times:
            pause_start = int(pause_time * self.sample_rate)
            pause_end = int((pause_time + 0.1) * self.sample_rate)
            if pause_end < len(envelope):
                envelope[pause_start:pause_end] *= 0.1
        
        # Add natural amplitude variations
        amplitude_variation = 0.7 + 0.3 * np.sin(2 * np.pi * 2.5 * t)
        envelope *= amplitude_variation
        
        return speech_signal * envelope * 0.3  # Scale to reasonable level
    
    def demonstrate_enhancement_pipeline(self, demo_files: Dict[str, str]) -> Dict[str, EnhancementResult]:
        """Demonstrate the enhancement pipeline on all demo files"""
        print("🔧 Demonstrating Audio Enhancement Pipeline")
        print("=" * 50)
        
        results = {}
        
        for audio_type, file_path in demo_files.items():
            print(f"\n📊 Processing: {audio_type.upper()} audio")
            print(f"   Input file: {os.path.basename(file_path)}")
            
            # Enhance the audio
            start_time = time.time()
            result = self.pipeline.enhance_audio(file_path)
            processing_time = time.time() - start_time
            
            results[audio_type] = result
            
            # Display results
            print(f"   ✅ Enhanced in {processing_time:.2f}s")
            print(f"   📈 Quality improvement: {result.improvement_score:+.1f} points")
            print(f"   🎯 Original quality: {result.original_metrics.quality_score:.1f}/100")
            print(f"   ⭐ Enhanced quality: {result.enhanced_metrics.quality_score:.1f}/100")
            print(f"   🛠️  Enhancements applied: {', '.join(result.enhancement_applied)}")
            
            # Show specific improvements
            self._show_detailed_improvements(result)
        
        return results
    
    def _show_detailed_improvements(self, result: EnhancementResult):
        """Show detailed improvements for a single enhancement result"""
        orig = result.original_metrics
        enh = result.enhanced_metrics
        
        improvements = []
        
        # SNR improvement
        snr_improvement = enh.snr_db - orig.snr_db
        if abs(snr_improvement) > 1:
            improvements.append(f"SNR: {snr_improvement:+.1f} dB")
        
        # THD improvement
        thd_improvement = orig.thd_percent - enh.thd_percent
        if abs(thd_improvement) > 0.5:
            improvements.append(f"THD: {thd_improvement:+.1f}%")
        
        # Dynamic range improvement
        dr_improvement = enh.dynamic_range_db - orig.dynamic_range_db
        if abs(dr_improvement) > 1:
            improvements.append(f"Dynamic Range: {dr_improvement:+.1f} dB")
        
        # Loudness improvement
        loudness_improvement = enh.loudness_lufs - orig.loudness_lufs
        if abs(loudness_improvement) > 2:
            improvements.append(f"Loudness: {loudness_improvement:+.1f} LUFS")
        
        if improvements:
            print(f"   📊 Key improvements: {', '.join(improvements)}")
    
    def demonstrate_custom_enhancement_options(self, demo_files: Dict[str, str]):
        """Demonstrate custom enhancement options"""
        print("\n🎛️  Demonstrating Custom Enhancement Options")
        print("=" * 50)
        
        # Use the noisy audio for this demonstration
        test_file = demo_files["noisy"]
        
        # Test different enhancement combinations
        enhancement_configs = [
            {
                "name": "Noise Reduction Only",
                "options": {
                    "noise_reduction": True,
                    "audio_repair": False,
                    "spectral_enhancement": False,
                    "dynamic_processing": False,
                    "normalization": False
                }
            },
            {
                "name": "Full Enhancement",
                "options": {
                    "noise_reduction": True,
                    "audio_repair": True,
                    "spectral_enhancement": True,
                    "dynamic_processing": True,
                    "normalization": True
                }
            },
            {
                "name": "Minimal Processing",
                "options": {
                    "noise_reduction": False,
                    "audio_repair": True,
                    "spectral_enhancement": False,
                    "dynamic_processing": False,
                    "normalization": True
                }
            }
        ]
        
        for config in enhancement_configs:
            print(f"\n🔧 Testing: {config['name']}")
            
            output_file = os.path.join(self.demo_dir, f"custom_{config['name'].lower().replace(' ', '_')}.wav")
            result = self.pipeline.enhance_audio(test_file, output_file, config["options"])
            
            print(f"   📊 Quality score: {result.enhanced_metrics.quality_score:.1f}/100")
            print(f"   📈 Improvement: {result.improvement_score:+.1f} points")
            print(f"   ⏱️  Processing time: {result.processing_time:.2f}s")
            print(f"   🛠️  Applied: {', '.join(result.enhancement_applied)}")
    
    def demonstrate_format_recommendations(self, demo_files: Dict[str, str]):
        """Demonstrate format optimization recommendations"""
        print("\n📋 Format Optimization Recommendations")
        print("=" * 50)
        
        for audio_type, file_path in demo_files.items():
            print(f"\n📁 {audio_type.upper()} audio:")
            
            recommendations = self.pipeline.get_format_recommendations(file_path)
            
            print(f"   Current format: {recommendations['current_format']}")
            print(f"   File size: {recommendations['file_size_mb']:.2f} MB")
            print(f"   Duration: {recommendations['duration_seconds']:.1f}s")
            print(f"   Quality score: {recommendations['quality_score']:.1f}/100")
            
            print("   💡 Recommendations:")
            for rec in recommendations['recommendations']:
                print(f"      • {rec['format']} - {rec['reason']}")
                print(f"        Size reduction: {rec['expected_size_reduction']}")
                print(f"        Quality impact: {rec['quality_impact']}")
    
    def create_comparison_report(self, results: Dict[str, EnhancementResult]) -> str:
        """Create a detailed comparison report"""
        print("\n📊 Creating Detailed Comparison Report")
        print("=" * 50)
        
        report_file = os.path.join(self.demo_dir, "enhancement_report.json")
        
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pipeline_version": "1.0.0",
            "total_files_processed": len(results),
            "results": {}
        }
        
        for audio_type, result in results.items():
            report_data["results"][audio_type] = {
                "original_metrics": {
                    "quality_score": result.original_metrics.quality_score,
                    "snr_db": result.original_metrics.snr_db,
                    "thd_percent": result.original_metrics.thd_percent,
                    "dynamic_range_db": result.original_metrics.dynamic_range_db,
                    "loudness_lufs": result.original_metrics.loudness_lufs,
                    "recommendations": result.original_metrics.recommendations
                },
                "enhanced_metrics": {
                    "quality_score": result.enhanced_metrics.quality_score,
                    "snr_db": result.enhanced_metrics.snr_db,
                    "thd_percent": result.enhanced_metrics.thd_percent,
                    "dynamic_range_db": result.enhanced_metrics.dynamic_range_db,
                    "loudness_lufs": result.enhanced_metrics.loudness_lufs,
                    "recommendations": result.enhanced_metrics.recommendations
                },
                "processing_info": {
                    "processing_time": result.processing_time,
                    "improvement_score": result.improvement_score,
                    "enhancement_applied": result.enhancement_applied
                }
            }
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Report saved to: {report_file}")
        
        # Display summary statistics
        self._display_summary_statistics(results)
        
        return report_file
    
    def _display_summary_statistics(self, results: Dict[str, EnhancementResult]):
        """Display summary statistics for all processed files"""
        print("\n📈 Summary Statistics:")
        
        # Calculate averages
        total_improvement = sum(r.improvement_score for r in results.values())
        avg_improvement = total_improvement / len(results)
        
        total_processing_time = sum(r.processing_time for r in results.values())
        avg_processing_time = total_processing_time / len(results)
        
        original_scores = [r.original_metrics.quality_score for r in results.values()]
        enhanced_scores = [r.enhanced_metrics.quality_score for r in results.values()]
        
        avg_original_score = sum(original_scores) / len(original_scores)
        avg_enhanced_score = sum(enhanced_scores) / len(enhanced_scores)
        
        print(f"   📊 Average quality improvement: {avg_improvement:+.1f} points")
        print(f"   ⏱️  Average processing time: {avg_processing_time:.2f}s")
        print(f"   📈 Average original quality: {avg_original_score:.1f}/100")
        print(f"   ⭐ Average enhanced quality: {avg_enhanced_score:.1f}/100")
        
        # Find best and worst improvements
        best_improvement = max(results.items(), key=lambda x: x[1].improvement_score)
        worst_improvement = min(results.items(), key=lambda x: x[1].improvement_score)
        
        print(f"   🏆 Best improvement: {best_improvement[0]} ({best_improvement[1].improvement_score:+.1f} points)")
        print(f"   🔍 Least improvement: {worst_improvement[0]} ({worst_improvement[1].improvement_score:+.1f} points)")
    
    def demonstrate_real_world_scenarios(self):
        """Demonstrate enhancement on real-world-like scenarios"""
        print("\n🌍 Real-World Scenario Demonstrations")
        print("=" * 50)
        
        scenarios = [
            {
                "name": "Podcast Recording",
                "description": "Simulated podcast with background noise and volume variations",
                "generator": self._create_podcast_scenario
            },
            {
                "name": "Phone Call Quality",
                "description": "Simulated phone call with compression and limited bandwidth",
                "generator": self._create_phone_call_scenario
            },
            {
                "name": "Conference Room Recording",
                "description": "Simulated meeting recording with echo and multiple speakers",
                "generator": self._create_conference_room_scenario
            }
        ]
        
        for scenario in scenarios:
            print(f"\n🎭 Scenario: {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            
            # Generate scenario audio
            audio_file = scenario["generator"]()
            
            # Enhance the audio
            result = self.pipeline.enhance_audio(audio_file)
            
            print(f"   📊 Original quality: {result.original_metrics.quality_score:.1f}/100")
            print(f"   ⭐ Enhanced quality: {result.enhanced_metrics.quality_score:.1f}/100")
            print(f"   📈 Improvement: {result.improvement_score:+.1f} points")
            print(f"   ⏱️  Processing time: {result.processing_time:.2f}s")
    
    def _create_podcast_scenario(self) -> str:
        """Create a podcast-like audio scenario"""
        duration = 5.0
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Base speech signal
        speech = self._generate_speech_like_audio(t)
        
        # Add background noise (air conditioning, room tone)
        background_noise = np.random.normal(0, 0.03, samples)
        
        # Add occasional mouth sounds/pops
        pop_times = [1.2, 2.8, 4.1]
        for pop_time in pop_times:
            pop_idx = int(pop_time * self.sample_rate)
            if pop_idx < samples - 100:
                speech[pop_idx:pop_idx+50] += np.random.uniform(-0.2, 0.2, 50)
        
        # Add volume variations (moving closer/farther from mic)
        volume_envelope = 0.8 + 0.4 * np.sin(2 * np.pi * 0.3 * t)
        
        podcast_audio = (speech * volume_envelope) + background_noise
        
        file_path = os.path.join(self.demo_dir, "scenario_podcast.wav")
        sf.write(file_path, podcast_audio, self.sample_rate)
        
        return file_path
    
    def _create_phone_call_scenario(self) -> str:
        """Create a phone call quality audio scenario"""
        duration = 4.0
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Base speech signal
        speech = self._generate_speech_like_audio(t)
        
        # Apply phone-like filtering (300Hz - 3400Hz bandpass)
        from scipy import signal
        nyquist = self.sample_rate / 2
        low = 300 / nyquist
        high = 3400 / nyquist
        b, a = signal.butter(4, [low, high], btype='band')
        filtered_speech = signal.filtfilt(b, a, speech)
        
        # Add compression artifacts
        compressed_speech = np.sign(filtered_speech) * (np.abs(filtered_speech) ** 0.7)
        
        # Add digital noise
        digital_noise = np.random.uniform(-0.02, 0.02, samples)
        
        phone_audio = compressed_speech + digital_noise
        
        file_path = os.path.join(self.demo_dir, "scenario_phone_call.wav")
        sf.write(file_path, phone_audio, self.sample_rate)
        
        return file_path
    
    def _create_conference_room_scenario(self) -> str:
        """Create a conference room recording scenario"""
        duration = 6.0
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Primary speaker
        primary_speech = self._generate_speech_like_audio(t) * 0.8
        
        # Add echo/reverb
        echo_delay = int(0.15 * self.sample_rate)  # 150ms echo
        echo_audio = np.zeros_like(primary_speech)
        if echo_delay < len(primary_speech):
            echo_audio[echo_delay:] = primary_speech[:-echo_delay] * 0.3
        
        # Add distant background conversation
        background_speech = self._generate_speech_like_audio(t * 0.7) * 0.1
        
        # Add HVAC noise
        hvac_noise = np.random.normal(0, 0.02, samples)
        
        # Occasional chair squeaks or paper rustling
        noise_times = [1.5, 3.2, 4.8]
        for noise_time in noise_times:
            noise_idx = int(noise_time * self.sample_rate)
            if noise_idx < samples - 1000:
                rustling = np.random.exponential(0.05, 1000) * np.random.choice([-1, 1], 1000)
                primary_speech[noise_idx:noise_idx+1000] += rustling
        
        conference_audio = primary_speech + echo_audio + background_speech + hvac_noise
        
        file_path = os.path.join(self.demo_dir, "scenario_conference_room.wav")
        sf.write(file_path, conference_audio, self.sample_rate)
        
        return file_path
    
    def run_complete_demo(self):
        """Run the complete demonstration"""
        try:
            print("🚀 Starting Complete Audio Enhancement Demo")
            print("=" * 60)
            
            # Step 1: Create demo files
            demo_files = self.create_demo_audio_files()
            
            # Step 2: Demonstrate basic enhancement
            results = self.demonstrate_enhancement_pipeline(demo_files)
            
            # Step 3: Demonstrate custom options
            self.demonstrate_custom_enhancement_options(demo_files)
            
            # Step 4: Show format recommendations
            self.demonstrate_format_recommendations(demo_files)
            
            # Step 5: Create comparison report
            report_file = self.create_comparison_report(results)
            
            # Step 6: Real-world scenarios
            self.demonstrate_real_world_scenarios()
            
            print("\n🎉 Demo Complete!")
            print("=" * 60)
            print(f"📁 All demo files and results saved in: {self.demo_dir}")
            print(f"📊 Detailed report available at: {report_file}")
            print("\n💡 Key Takeaways:")
            print("   • The pipeline successfully enhances various types of audio issues")
            print("   • Custom enhancement options allow fine-tuned control")
            print("   • Format recommendations help optimize file size vs quality")
            print("   • Real-world scenarios show practical applications")
            print("\n🔧 Next Steps:")
            print("   • Integrate with your transcription pipeline")
            print("   • Customize enhancement parameters for your use case")
            print("   • Consider batch processing for multiple files")
            
        except Exception as e:
            print(f"❌ Demo failed with error: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    """Main demo function"""
    print("🎵 Audio Enhancement Pipeline Demo")
    print("This demo showcases the comprehensive audio enhancement capabilities")
    print("including noise reduction, audio repair, spectral enhancement, and more.")
    print()
    
    # Check if we should run a quick demo or full demo
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        print("🏃 Running quick demo...")
        demo = AudioEnhancementDemo()
        
        # Just create and enhance one file
        demo_files = {"noisy": list(demo.create_demo_audio_files().values())[1]}
        results = demo.demonstrate_enhancement_pipeline(demo_files)
        demo.create_comparison_report(results)
        
    else:
        print("🎭 Running complete demo...")
        demo = AudioEnhancementDemo()
        demo.run_complete_demo()

if __name__ == "__main__":
    main()