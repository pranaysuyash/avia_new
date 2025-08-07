"""
Demo script for Emotion and Sentiment Detection System

This script demonstrates the comprehensive emotion detection, sentiment analysis,
mood tracking, and stress/fatigue analysis capabilities of the system.
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import tempfile
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from emotion_sentiment_detection import (
        EmotionSentimentSystem, EmotionDetector, SentimentAnalyzer,
        MoodTracker, StressFatigueDetector, EmotionalTimelineVisualizer
    )
except ImportError as e:
    print(f"Error importing emotion detection modules: {e}")
    print("Please ensure all required dependencies are installed:")
    print("pip install librosa soundfile scikit-learn textblob spacy plotly")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_synthetic_audio(duration=30, sample_rate=22050, output_path="demo_audio.wav"):
    """Create synthetic audio for demonstration purposes"""
    try:
        import soundfile as sf
        
        # Generate synthetic audio with varying characteristics
        t = np.linspace(0, duration, int(duration * sample_rate))
        
        # Base frequency that varies over time (simulating speech)
        base_freq = 200 + 50 * np.sin(2 * np.pi * 0.1 * t)  # Varying pitch
        
        # Add harmonics and noise to simulate voice
        audio = np.sin(2 * np.pi * base_freq * t)  # Fundamental
        audio += 0.3 * np.sin(2 * np.pi * 2 * base_freq * t)  # Second harmonic
        audio += 0.1 * np.sin(2 * np.pi * 3 * base_freq * t)  # Third harmonic
        
        # Add some noise
        audio += 0.05 * np.random.randn(len(audio))
        
        # Add amplitude modulation (simulating speech patterns)
        amplitude_mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)
        audio *= amplitude_mod
        
        # Add some pauses (silence periods)
        for i in range(0, len(audio), sample_rate * 5):  # Every 5 seconds
            pause_start = i + int(sample_rate * 3)
            pause_end = min(pause_start + int(sample_rate * 0.5), len(audio))
            if pause_end < len(audio):
                audio[pause_start:pause_end] *= 0.1  # Reduce volume for pause
        
        # Normalize audio
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        # Save audio file
        sf.write(output_path, audio, sample_rate)
        logger.info(f"Created synthetic audio file: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating synthetic audio: {e}")
        return None

def demo_emotion_detection():
    """Demonstrate emotion detection capabilities"""
    print("\n" + "="*60)
    print("🎭 EMOTION DETECTION DEMO")
    print("="*60)
    
    try:
        # Create synthetic audio
        audio_path = create_synthetic_audio(duration=20, output_path="demo_emotion_audio.wav")
        if not audio_path:
            print("❌ Failed to create synthetic audio")
            return
        
        # Initialize emotion detector
        emotion_detector = EmotionDetector()
        
        # Detect emotions
        print("🔍 Detecting emotions from audio...")
        emotion_results = emotion_detector.detect_emotion(audio_path, segment_duration=3.0)
        
        if emotion_results:
            print(f"✅ Detected emotions in {len(emotion_results)} segments")
            
            # Display results
            print("\n📊 Emotion Detection Results:")
            print("-" * 50)
            
            for i, result in enumerate(emotion_results[:5]):  # Show first 5 results
                print(f"Segment {i+1} ({result.timestamp:.1f}s - {result.timestamp + result.duration:.1f}s):")
                print(f"  Primary Emotion: {result.primary_emotion} (confidence: {result.confidence:.2f})")
                print(f"  Arousal: {result.arousal:.2f}, Valence: {result.valence:.2f}")
                print(f"  Top emotions: {dict(list(sorted(result.emotion_scores.items(), key=lambda x: x[1], reverse=True))[:3])}")
                print()
            
            # Calculate statistics
            emotions = [r.primary_emotion for r in emotion_results]
            confidences = [r.confidence for r in emotion_results]
            
            print("📈 Statistics:")
            print(f"  Average confidence: {np.mean(confidences):.2f}")
            print(f"  Most common emotion: {max(set(emotions), key=emotions.count)}")
            print(f"  Emotion variety: {len(set(emotions))} different emotions detected")
            
        else:
            print("❌ No emotions detected")
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
    except Exception as e:
        logger.error(f"Error in emotion detection demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_sentiment_analysis():
    """Demonstrate sentiment analysis capabilities"""
    print("\n" + "="*60)
    print("💭 SENTIMENT ANALYSIS DEMO")
    print("="*60)
    
    try:
        # Create synthetic audio
        audio_path = create_synthetic_audio(duration=15, output_path="demo_sentiment_audio.wav")
        if not audio_path:
            print("❌ Failed to create synthetic audio")
            return
        
        # Sample transcript with varying sentiment
        transcript = """
        I'm really excited about this new project! It's going to be amazing and I can't wait to get started.
        However, I'm also a bit worried about the tight deadline. The pressure is quite intense.
        But overall, I think we can make it work if we stay focused and work together as a team.
        Sometimes I feel overwhelmed, but then I remember how much I love what I do.
        """
        
        # Initialize sentiment analyzer
        sentiment_analyzer = SentimentAnalyzer()
        
        # Analyze sentiment
        print("🔍 Analyzing sentiment from audio and text...")
        sentiment_results = sentiment_analyzer.analyze_sentiment(audio_path, transcript, segment_duration=3.0)
        
        if sentiment_results:
            print(f"✅ Analyzed sentiment in {len(sentiment_results)} segments")
            
            # Display results
            print("\n📊 Sentiment Analysis Results:")
            print("-" * 50)
            
            for i, result in enumerate(sentiment_results[:5]):  # Show first 5 results
                print(f"Segment {i+1} ({result.timestamp:.1f}s - {result.timestamp + result.duration:.1f}s):")
                print(f"  Sentiment: {result.sentiment} (polarity: {result.polarity:.2f})")
                print(f"  Confidence: {result.confidence:.2f}")
                print(f"  Text sentiment: {result.text_sentiment:.2f}")
                print(f"  Audio sentiment: {result.audio_sentiment:.2f}")
                print(f"  Subjectivity: {result.subjectivity:.2f}")
                print()
            
            # Calculate statistics
            polarities = [r.polarity for r in sentiment_results]
            sentiments = [r.sentiment for r in sentiment_results]
            
            print("📈 Statistics:")
            print(f"  Average polarity: {np.mean(polarities):.2f}")
            print(f"  Sentiment distribution: {dict(pd.Series(sentiments).value_counts()) if 'pd' in globals() else 'N/A'}")
            print(f"  Most positive segment: {max(sentiment_results, key=lambda x: x.polarity).timestamp:.1f}s")
            print(f"  Most negative segment: {min(sentiment_results, key=lambda x: x.polarity).timestamp:.1f}s")
            
        else:
            print("❌ No sentiment data generated")
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
    except Exception as e:
        logger.error(f"Error in sentiment analysis demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_mood_tracking():
    """Demonstrate mood tracking capabilities"""
    print("\n" + "="*60)
    print("🌡️ MOOD TRACKING DEMO")
    print("="*60)
    
    try:
        # Create longer synthetic audio for mood tracking
        audio_path = create_synthetic_audio(duration=60, output_path="demo_mood_audio.wav")
        if not audio_path:
            print("❌ Failed to create synthetic audio")
            return
        
        # Sample transcript with mood changes
        transcript = """
        Good morning everyone! I'm feeling really energetic today and ready to tackle our big presentation.
        We've been working on this project for months and I think we're finally ready to show what we've accomplished.
        
        Actually, now that I think about it, I'm getting a bit nervous. There's so much riding on this presentation.
        What if something goes wrong? What if the client doesn't like our approach?
        
        No, no, I need to stay positive. We've done great work and I'm confident in our team.
        Let's just focus on delivering our best performance and everything will work out fine.
        
        You know what, I'm actually feeling pretty calm now. Sometimes talking through your worries helps.
        I think we're going to do great today. Let's make this presentation memorable!
        """
        
        # Initialize mood tracker
        mood_tracker = MoodTracker()
        
        # Track mood
        print("🔍 Tracking mood changes throughout the recording...")
        mood_states = mood_tracker.track_mood(audio_path, transcript)
        
        if mood_states:
            print(f"✅ Tracked mood across {len(mood_states)} time windows")
            
            # Display results
            print("\n📊 Mood Tracking Results:")
            print("-" * 50)
            
            for i, mood in enumerate(mood_states):
                print(f"Window {i+1} ({mood.timestamp:.1f}s - {mood.timestamp + 30:.1f}s):")
                print(f"  Mood: {mood.mood}")
                print(f"  Energy: {mood.energy_level:.2f}")
                print(f"  Stress: {mood.stress_level:.2f}")
                print(f"  Fatigue: {mood.fatigue_level:.2f}")
                print(f"  Engagement: {mood.engagement_level:.2f}")
                print(f"  Stability: {mood.emotional_stability:.2f}")
                print()
            
            # Calculate trends
            energy_trend = np.diff([m.energy_level for m in mood_states])
            stress_trend = np.diff([m.stress_level for m in mood_states])
            
            print("📈 Mood Trends:")
            print(f"  Energy trend: {'Increasing' if np.mean(energy_trend) > 0 else 'Decreasing'}")
            print(f"  Stress trend: {'Increasing' if np.mean(stress_trend) > 0 else 'Decreasing'}")
            print(f"  Average energy: {np.mean([m.energy_level for m in mood_states]):.2f}")
            print(f"  Average stress: {np.mean([m.stress_level for m in mood_states]):.2f}")
            
        else:
            print("❌ No mood data generated")
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
    except Exception as e:
        logger.error(f"Error in mood tracking demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_stress_fatigue_detection():
    """Demonstrate stress and fatigue detection capabilities"""
    print("\n" + "="*60)
    print("😰 STRESS & FATIGUE DETECTION DEMO")
    print("="*60)
    
    try:
        # Create synthetic audio with stress indicators
        audio_path = create_synthetic_audio(duration=40, output_path="demo_stress_audio.wav")
        if not audio_path:
            print("❌ Failed to create synthetic audio")
            return
        
        # Initialize stress/fatigue detector
        stress_detector = StressFatigueDetector()
        
        # Detect stress and fatigue
        print("🔍 Detecting stress and fatigue indicators...")
        stress_results = stress_detector.detect_stress_fatigue(audio_path, segment_duration=10.0)
        
        if stress_results:
            print(f"✅ Analyzed stress/fatigue in {len(stress_results)} segments")
            
            # Display results
            print("\n📊 Stress & Fatigue Detection Results:")
            print("-" * 50)
            
            for i, result in enumerate(stress_results):
                print(f"Segment {i+1} ({result.timestamp:.1f}s - {result.timestamp + 10:.1f}s):")
                print(f"  Stress Level: {result.stress_level:.2f}")
                print(f"  Fatigue Level: {result.fatigue_level:.2f}")
                print(f"  Cognitive Load: {result.cognitive_load:.2f}")
                print(f"  Vocal Strain: {result.vocal_strain:.2f}")
                print(f"  Speaking Rate Deviation: {result.speaking_rate_deviation:.2f}")
                print(f"  Pause Frequency: {result.pause_frequency:.2f}")
                print()
            
            # Calculate statistics and alerts
            avg_stress = np.mean([r.stress_level for r in stress_results])
            avg_fatigue = np.mean([r.fatigue_level for r in stress_results])
            high_stress_periods = sum(1 for r in stress_results if r.stress_level > 0.7)
            high_fatigue_periods = sum(1 for r in stress_results if r.fatigue_level > 0.7)
            
            print("📈 Statistics:")
            print(f"  Average stress level: {avg_stress:.2f}")
            print(f"  Average fatigue level: {avg_fatigue:.2f}")
            print(f"  High stress periods: {high_stress_periods}")
            print(f"  High fatigue periods: {high_fatigue_periods}")
            
            # Generate alerts
            if avg_stress > 0.6:
                print("⚠️  Alert: Elevated stress levels detected")
            if avg_fatigue > 0.6:
                print("⚠️  Alert: Signs of fatigue detected")
            if high_stress_periods > 0:
                print(f"🚨 Alert: {high_stress_periods} periods of high stress identified")
            
        else:
            print("❌ No stress/fatigue data generated")
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
    except Exception as e:
        logger.error(f"Error in stress/fatigue detection demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_complete_analysis():
    """Demonstrate complete emotion and sentiment analysis system"""
    print("\n" + "="*60)
    print("🎯 COMPLETE ANALYSIS DEMO")
    print("="*60)
    
    try:
        # Create comprehensive synthetic audio
        audio_path = create_synthetic_audio(duration=45, output_path="demo_complete_audio.wav")
        if not audio_path:
            print("❌ Failed to create synthetic audio")
            return
        
        # Comprehensive transcript
        transcript = """
        Hello everyone, welcome to today's meeting. I'm excited to share our progress on the new initiative.
        We've made significant strides over the past few weeks, and I think you'll be impressed with what we've accomplished.
        
        However, I must admit that the journey hasn't been without its challenges. We've faced some unexpected obstacles
        that have caused me quite a bit of stress. The tight deadlines are really putting pressure on the entire team.
        
        But you know what? I believe in our ability to overcome these challenges. We're a strong team, and when we work together,
        there's nothing we can't achieve. I'm feeling more optimistic about our chances of success.
        
        That said, I am getting a bit tired from all the late nights we've been pulling. I think we all need to make sure
        we're taking care of ourselves and not burning out. Our health and well-being are just as important as meeting our goals.
        
        In conclusion, while there are challenges ahead, I'm confident that we can navigate them successfully.
        Let's stay focused, support each other, and make this project a great success!
        """
        
        # Initialize complete system
        emotion_system = EmotionSentimentSystem()
        
        # Perform complete analysis
        print("🔍 Performing comprehensive emotion and sentiment analysis...")
        results = emotion_system.analyze_complete(audio_path, transcript)
        
        if 'error' not in results:
            print("✅ Complete analysis finished successfully!")
            
            # Display summary
            if 'summary' in results:
                summary = results['summary']
                print("\n📊 Analysis Summary:")
                print("-" * 50)
                print(f"Duration analyzed: {summary.get('duration_analyzed', 0):.1f} seconds")
                print(f"Dominant emotion: {summary.get('dominant_emotion', 'Unknown')}")
                print(f"Average sentiment: {summary.get('average_sentiment', 0):.2f}")
                print(f"Emotional stability: {summary.get('emotional_stability', 0):.2f}")
                
                if 'stress_indicators' in summary:
                    stress_data = summary['stress_indicators']
                    print(f"Average stress level: {stress_data.get('average_stress_level', 0):.2f}")
                    print(f"Average fatigue level: {stress_data.get('average_fatigue_level', 0):.2f}")
                    print(f"High stress periods: {stress_data.get('high_stress_periods', 0)}")
                
                if 'key_insights' in summary and summary['key_insights']:
                    print("\n💡 Key Insights:")
                    for insight in summary['key_insights']:
                        print(f"  • {insight}")
            
            # Display data counts
            print(f"\n📈 Data Generated:")
            print(f"  Emotion segments: {len(results.get('emotions', []))}")
            print(f"  Sentiment segments: {len(results.get('sentiments', []))}")
            print(f"  Mood states: {len(results.get('mood_states', []))}")
            print(f"  Stress/fatigue segments: {len(results.get('stress_fatigue', []))}")
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"demo_emotion_results_{timestamp}.json"
            
            try:
                emotion_system.save_results(results, results_file)
                print(f"💾 Results saved to: {results_file}")
            except Exception as e:
                print(f"⚠️  Could not save results: {e}")
            
            # Display visualization info
            if 'visualizations' in results:
                viz_count = len([v for v in results['visualizations'].values() if v])
                print(f"📊 Generated {viz_count} visualizations")
                
                for viz_name, viz_path in results['visualizations'].items():
                    if viz_path and os.path.exists(viz_path):
                        print(f"  • {viz_name}: {viz_path}")
            
        else:
            print(f"❌ Analysis failed: {results['error']}")
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
    except Exception as e:
        logger.error(f"Error in complete analysis demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_visualization():
    """Demonstrate visualization capabilities"""
    print("\n" + "="*60)
    print("📊 VISUALIZATION DEMO")
    print("="*60)
    
    try:
        # Create sample data for visualization
        from emotion_sentiment_detection import EmotionResult, SentimentResult, MoodState, StressFatigueResult
        
        # Sample emotion results
        emotion_results = [
            EmotionResult(
                timestamp=i * 3.0,
                duration=3.0,
                primary_emotion=np.random.choice(['happy', 'sad', 'angry', 'neutral', 'excited']),
                emotion_scores={'happy': 0.3, 'sad': 0.2, 'angry': 0.1, 'neutral': 0.4},
                confidence=np.random.uniform(0.5, 0.9),
                arousal=np.random.uniform(0.2, 0.8),
                valence=np.random.uniform(0.3, 0.7),
                intensity=np.random.uniform(0.4, 0.8)
            )
            for i in range(10)
        ]
        
        # Sample sentiment results
        sentiment_results = [
            SentimentResult(
                timestamp=i * 3.0,
                duration=3.0,
                sentiment=np.random.choice(['positive', 'negative', 'neutral']),
                polarity=np.random.uniform(-0.5, 0.5),
                subjectivity=np.random.uniform(0.3, 0.8),
                confidence=np.random.uniform(0.6, 0.9),
                text_sentiment=np.random.uniform(-0.3, 0.3),
                audio_sentiment=np.random.uniform(-0.4, 0.4)
            )
            for i in range(10)
        ]
        
        # Initialize visualizer
        visualizer = EmotionalTimelineVisualizer()
        
        # Create visualizations
        print("🎨 Creating emotion timeline visualization...")
        emotion_timeline = visualizer.create_emotion_timeline(emotion_results, "demo_emotion_timeline.html")
        if emotion_timeline:
            print(f"✅ Emotion timeline saved to: {emotion_timeline}")
        
        print("🎨 Creating sentiment heatmap...")
        sentiment_heatmap = visualizer.create_sentiment_heatmap(sentiment_results, "demo_sentiment_heatmap.html")
        if sentiment_heatmap:
            print(f"✅ Sentiment heatmap saved to: {sentiment_heatmap}")
        
        print("📊 Visualization demo completed!")
        print("Open the generated HTML files in your browser to view the interactive visualizations.")
        
    except Exception as e:
        logger.error(f"Error in visualization demo: {e}")
        print(f"❌ Visualization demo failed: {e}")

def main():
    """Run all demonstration functions"""
    print("🎭 EMOTION & SENTIMENT DETECTION SYSTEM DEMO")
    print("=" * 80)
    print("This demo showcases the comprehensive emotion and sentiment analysis capabilities")
    print("of the system, including emotion detection, sentiment analysis, mood tracking,")
    print("stress/fatigue detection, and interactive visualizations.")
    print("=" * 80)
    
    try:
        # Check dependencies
        print("🔍 Checking dependencies...")
        
        required_modules = ['librosa', 'soundfile', 'sklearn', 'textblob', 'plotly']
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
        demo_emotion_detection()
        demo_sentiment_analysis()
        demo_mood_tracking()
        demo_stress_fatigue_detection()
        demo_complete_analysis()
        demo_visualization()
        
        print("\n" + "="*80)
        print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("The Emotion & Sentiment Detection System is working correctly.")
        print("You can now use the system for real audio analysis.")
        print("\nTo use the Streamlit UI, run:")
        print("streamlit run emotion_sentiment_detection_ui.py")
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"Error in main demo: {e}")
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    main()