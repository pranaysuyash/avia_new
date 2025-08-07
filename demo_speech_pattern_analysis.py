"""
Demo Script for Speech Pattern Analysis System

This script demonstrates the comprehensive speech pattern analysis capabilities including:
- Speech rate analysis and speaking pattern detection
- Pause detection and silence analysis
- Filler word detection and removal
- Speaking confidence and hesitation analysis
- Speech coaching suggestions based on patterns

Requirements: 3.1, 5.1
"""

import sys
import os
from pathlib import Path
import numpy as np
from datetime import datetime
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from speech_pattern_analysis import (
    SpeechPatternAnalysisSystem,
    SpeechSegment,
    create_sample_segments,
    format_analysis_report
)

def create_demo_audio_features(duration: float = 15.0) -> dict:
    """Create mock audio features for demo purposes"""
    sample_rate = 16000
    samples = int(duration * sample_rate)
    
    # Generate synthetic audio features
    audio = np.random.normal(0, 0.1, samples)  # Mock audio signal
    
    # Add some speech-like patterns
    speech_regions = [(1, 3), (4, 7), (8, 10), (11, 14)]  # Speaking regions
    for start, end in speech_regions:
        start_idx = int(start * sample_rate)
        end_idx = int(end * sample_rate)
        if end_idx <= len(audio):
            # Add higher energy in speech regions
            audio[start_idx:end_idx] *= 3
    
    # Create mock features
    n_frames = int(samples / 512) + 1  # Assuming hop_length=512
    
    features = {
        'audio': audio,
        'sample_rate': sample_rate,
        'duration': duration,
        'mfcc': np.random.randn(13, n_frames),
        'spectral_centroid': np.random.uniform(1000, 3000, n_frames),
        'spectral_rolloff': np.random.uniform(2000, 6000, n_frames),
        'zero_crossing_rate': np.random.uniform(0.01, 0.1, n_frames),
        'rms_energy': np.random.uniform(0.001, 0.1, n_frames),
        'volume_envelope': np.abs(audio),
        'pitch': np.random.uniform(80, 300, n_frames),
        'tempo': 120.0,
        'beats': np.arange(0, duration, 0.5)  # Beat times
    }
    
    # Make silent regions have low energy
    for i in range(n_frames):
        time = i * 512 / sample_rate
        is_speech = any(start <= time <= end for start, end in speech_regions)
        if not is_speech:
            features['rms_energy'][i] *= 0.1  # Much lower energy in non-speech
    
    return features

def demo_professional_speaker():
    """Demo analysis for a professional speaker"""
    print("\n" + "="*60)
    print("DEMO: Professional Speaker Analysis")
    print("="*60)
    
    # Professional speaker text with good pacing
    text = """
    Good morning everyone. Today I want to discuss the importance of effective communication 
    in business environments. Clear communication builds trust and drives results. 
    When we speak with confidence and clarity, we inspire others to take action. 
    Thank you for your attention.
    """
    
    segments = create_sample_segments(text.strip(), 12.0)
    
    print(f"Created {len(segments)} speech segments")
    for i, seg in enumerate(segments[:3]):  # Show first 3
        print(f"  Segment {i+1}: {seg.start_time:.1f}s-{seg.end_time:.1f}s: '{seg.text[:50]}...'")
    
    return segments, "professional_speaker_demo.wav"

def demo_nervous_speaker():
    """Demo analysis for a nervous speaker with fillers"""
    print("\n" + "="*60)
    print("DEMO: Nervous Speaker Analysis")
    print("="*60)
    
    # Nervous speaker text with many fillers
    text = """
    Um, hello everyone. I, uh, I want to talk about, like, communication today. 
    You know, it's really important and, er, I think we should focus on it. 
    So, um, when we communicate effectively, we can, uh, achieve better results. 
    I mean, that's what I believe anyway.
    """
    
    segments = create_sample_segments(text.strip(), 15.0)
    
    print(f"Created {len(segments)} speech segments")
    for i, seg in enumerate(segments[:3]):  # Show first 3
        print(f"  Segment {i+1}: {seg.start_time:.1f}s-{seg.end_time:.1f}s: '{seg.text[:50]}...'")
    
    return segments, "nervous_speaker_demo.wav"

def demo_fast_speaker():
    """Demo analysis for a fast speaker"""
    print("\n" + "="*60)
    print("DEMO: Fast Speaker Analysis")
    print("="*60)
    
    # Fast speaker text - lots of content in short time
    text = """
    Hello everyone today I want to talk about communication it's really important 
    and we need to focus on effective strategies for business success because 
    when we communicate well we achieve better results and build stronger relationships 
    with our colleagues and clients which leads to improved performance overall.
    """
    
    segments = create_sample_segments(text.strip(), 8.0)  # Short duration = fast pace
    
    print(f"Created {len(segments)} speech segments")
    for i, seg in enumerate(segments[:3]):  # Show first 3
        print(f"  Segment {i+1}: {seg.start_time:.1f}s-{seg.end_time:.1f}s: '{seg.text[:50]}...'")
    
    return segments, "fast_speaker_demo.wav"

def run_analysis_demo(segments, audio_path, speaker_type):
    """Run analysis demo for given segments"""
    print(f"\nRunning analysis for {speaker_type}...")
    
    # Create mock system that doesn't require actual audio files
    class MockSpeechPatternAnalysisSystem(SpeechPatternAnalysisSystem):
        def __init__(self):
            # Initialize without database for demo
            self.feature_extractor = None
            self.speech_rate_analyzer = SpeechPatternAnalysisSystem().speech_rate_analyzer
            self.pause_detector = SpeechPatternAnalysisSystem().pause_detector
            self.filler_detector = SpeechPatternAnalysisSystem().filler_detector
            self.confidence_analyzer = SpeechPatternAnalysisSystem().confidence_analyzer
            self.speech_coach = SpeechPatternAnalysisSystem().speech_coach
        
        def analyze_speech_patterns(self, audio_path, segments):
            # Create mock audio features
            total_duration = max(seg.end_time for seg in segments) if segments else 15.0
            audio_features = create_demo_audio_features(total_duration)
            
            # Perform individual analyses
            speech_rate = self.speech_rate_analyzer.analyze_speech_rate(segments, audio_features)
            pause_analysis = self.pause_detector.detect_pauses(audio_features, segments)
            filler_analysis = self.filler_detector.detect_filler_words(segments)
            confidence_analysis = self.confidence_analyzer.analyze_confidence(
                segments, audio_features, filler_analysis, pause_analysis
            )
            
            # Create comprehensive analysis
            from speech_pattern_analysis import ComprehensiveSpeechAnalysis, SpeechCoachingSuggestions
            
            comprehensive_analysis = ComprehensiveSpeechAnalysis(
                speech_rate=speech_rate,
                pause_analysis=pause_analysis,
                filler_analysis=filler_analysis,
                confidence_analysis=confidence_analysis,
                coaching_suggestions=SpeechCoachingSuggestions([], [], [], [], "Unknown", []),
                analysis_timestamp=datetime.now(),
                audio_duration=audio_features.get('duration', 0)
            )
            
            # Generate coaching suggestions
            comprehensive_analysis.coaching_suggestions = self.speech_coach.generate_suggestions(
                comprehensive_analysis
            )
            
            return comprehensive_analysis
    
    try:
        # Create mock system
        system = MockSpeechPatternAnalysisSystem()
        
        # Run analysis
        analysis = system.analyze_speech_patterns(audio_path, segments)
        
        print("✅ Analysis completed successfully!")
        
        # Display key results
        print(f"\n📊 Key Metrics:")
        print(f"  Words per minute: {analysis.speech_rate.words_per_minute:.1f}")
        print(f"  Filler percentage: {analysis.filler_analysis.filler_percentage:.1f}%")
        print(f"  Confidence score: {analysis.confidence_analysis.overall_confidence_score:.2f}")
        print(f"  Pause frequency: {analysis.pause_analysis.pause_frequency:.1f} per minute")
        print(f"  Overall rating: {analysis.coaching_suggestions.overall_rating}")
        
        # Show top filler words
        if analysis.filler_analysis.filler_words:
            print(f"\n🗣️ Top Filler Words:")
            sorted_fillers = sorted(analysis.filler_analysis.filler_words.items(), 
                                  key=lambda x: x[1], reverse=True)
            for word, count in sorted_fillers[:3]:
                print(f"  '{word}': {count} times")
        
        # Show priority areas
        if analysis.coaching_suggestions.priority_areas:
            print(f"\n🎯 Priority Areas:")
            for area in analysis.coaching_suggestions.priority_areas:
                print(f"  • {area}")
        
        # Show sample coaching suggestions
        all_suggestions = (
            analysis.coaching_suggestions.pace_suggestions +
            analysis.coaching_suggestions.pause_suggestions +
            analysis.coaching_suggestions.filler_reduction_tips +
            analysis.coaching_suggestions.confidence_building_tips
        )
        
        if all_suggestions:
            print(f"\n💡 Sample Coaching Suggestions:")
            for suggestion in all_suggestions[:3]:  # Show first 3
                print(f"  • {suggestion}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

def demo_batch_analysis():
    """Demo batch analysis of multiple speakers"""
    print("\n" + "="*60)
    print("DEMO: Batch Analysis")
    print("="*60)
    
    # Create multiple speaker demos
    speakers = [
        ("Professional", *demo_professional_speaker()),
        ("Nervous", *demo_nervous_speaker()),
        ("Fast", *demo_fast_speaker())
    ]
    
    results = []
    
    for speaker_type, segments, audio_path in speakers:
        print(f"\nAnalyzing {speaker_type} speaker...")
        analysis = run_analysis_demo(segments, audio_path, speaker_type)
        if analysis:
            results.append((speaker_type, analysis))
    
    # Compare results
    if results:
        print("\n" + "="*60)
        print("BATCH ANALYSIS COMPARISON")
        print("="*60)
        
        print(f"{'Speaker Type':<15} {'WPM':<8} {'Fillers%':<10} {'Confidence':<12} {'Rating':<15}")
        print("-" * 60)
        
        for speaker_type, analysis in results:
            wpm = analysis.speech_rate.words_per_minute
            filler_pct = analysis.filler_analysis.filler_percentage
            confidence = analysis.confidence_analysis.overall_confidence_score
            rating = analysis.coaching_suggestions.overall_rating
            
            print(f"{speaker_type:<15} {wpm:<8.1f} {filler_pct:<10.1f} {confidence:<12.2f} {rating:<15}")
    
    return results

def demo_export_functionality():
    """Demo export and reporting functionality"""
    print("\n" + "="*60)
    print("DEMO: Export Functionality")
    print("="*60)
    
    # Run a quick analysis
    segments, audio_path = demo_professional_speaker()
    analysis = run_analysis_demo(segments, audio_path, "Professional")
    
    if analysis:
        # Generate formatted report
        print("\n📄 Generating formatted report...")
        report = format_analysis_report(analysis)
        
        # Save to file
        report_filename = f"speech_analysis_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ Report saved to: {report_filename}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}")
        
        # Generate JSON export
        json_filename = f"speech_analysis_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            analysis_dict = analysis.to_dict()
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_dict, f, indent=2, default=str)
            print(f"✅ JSON data saved to: {json_filename}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")
        
        # Show sample of report
        print(f"\n📋 Sample Report Content:")
        print("-" * 40)
        print(report[:500] + "..." if len(report) > 500 else report)

def main():
    """Main demo function"""
    print("🎤 Speech Pattern Analysis System Demo")
    print("=" * 60)
    print("This demo showcases comprehensive speech pattern analysis capabilities:")
    print("• Speech rate analysis and tempo detection")
    print("• Pause detection and timing analysis") 
    print("• Filler word detection and hesitation analysis")
    print("• Speaking confidence assessment")
    print("• Personalized coaching suggestions")
    print("=" * 60)
    
    try:
        # Demo individual speaker types
        print("\n🎯 Individual Speaker Analysis Demos:")
        
        # Professional speaker
        segments, audio_path = demo_professional_speaker()
        professional_analysis = run_analysis_demo(segments, audio_path, "Professional")
        
        # Nervous speaker
        segments, audio_path = demo_nervous_speaker()
        nervous_analysis = run_analysis_demo(segments, audio_path, "Nervous")
        
        # Fast speaker
        segments, audio_path = demo_fast_speaker()
        fast_analysis = run_analysis_demo(segments, audio_path, "Fast")
        
        # Batch analysis demo
        batch_results = demo_batch_analysis()
        
        # Export functionality demo
        demo_export_functionality()
        
        print("\n" + "="*60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n🚀 Next Steps:")
        print("• Run 'streamlit run speech_pattern_analysis_ui.py' for the web interface")
        print("• Upload your own audio files for real analysis")
        print("• Explore the coaching suggestions and improvement tips")
        print("• Export detailed reports for progress tracking")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()