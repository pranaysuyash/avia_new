#!/usr/bin/env python3
"""
Test script for advanced content analysis functionality
Tests Task 39: Create advanced AI-powered content analysis
"""

import os
import sys
import logging
from typing import Dict, List, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_content_analysis import (
    advanced_content_analyzer, emotion_detector, speaking_pattern_analyzer,
    complexity_analyzer, bias_detector, plagiarism_detector
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_emotion_detection():
    """Test emotion detection functionality"""
    print("\n😊 Testing Emotion Detection...")
    
    test_texts = [
        "I am absolutely thrilled and excited about this amazing opportunity!",
        "I'm feeling quite disappointed and sad about the recent developments.",
        "This situation is making me really angry and frustrated.",
        "I'm worried and anxious about what might happen next.",
        "What a surprising and unexpected turn of events!"
    ]
    
    try:
        for i, text in enumerate(test_texts, 1):
            print(f"\nTest {i}: {text[:50]}...")
            
            result = emotion_detector.analyze_emotions(text)
            
            print(f"  Dominant emotion: {result.dominant_emotion}")
            print(f"  Confidence: {result.confidence:.2%}")
            print(f"  Emotional intensity: {result.emotional_intensity:.2f}")
            print(f"  Top emotions: {dict(list(result.emotion_scores.items())[:3])}")
        
        print("✅ Emotion detection test successful")
        return True
        
    except Exception as e:
        print(f"❌ Emotion detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_speaking_pattern_analysis():
    """Test speaking pattern analysis"""
    print("\n🎤 Testing Speaking Pattern Analysis...")
    
    test_cases = [
        {
            'text': "Well, um, I think that, you know, this is definitely a great opportunity. I'm absolutely certain that we can achieve our goals!",
            'duration': 10.0,
            'description': "Uncertain speech with confidence indicators"
        },
        {
            'text': "The quarterly results show SIGNIFICANT growth. Our revenue increased by 25%. This is EXCELLENT news for all stakeholders.",
            'duration': 8.0,
            'description': "Confident speech with emphasis"
        },
        {
            'text': "Today we discussed the project timeline. The development phase will take three months. Testing will require additional time. Deployment is scheduled for Q4.",
            'duration': 12.0,
            'description': "Steady, professional speech"
        }
    ]
    
    try:
        for i, case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {case['description']}")
            print(f"Text: {case['text'][:60]}...")
            
            result = speaking_pattern_analyzer.analyze_speaking_patterns(
                case['text'], case['duration']
            )
            
            print(f"  Average pace: {result.average_pace:.1f} WPM")
            print(f"  Pace variation: {result.pace_variation:.2f}")
            print(f"  Speaking rhythm: {result.speaking_rhythm}")
            print(f"  Emphasis points: {len(result.emphasis_points)}")
            print(f"  Confidence indicators: {len(result.confidence_indicators)}")
        
        print("✅ Speaking pattern analysis test successful")
        return True
        
    except Exception as e:
        print(f"❌ Speaking pattern analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_content_complexity_analysis():
    """Test content complexity analysis"""
    print("\n📚 Testing Content Complexity Analysis...")
    
    test_texts = [
        {
            'text': "The cat sat on the mat. It was a sunny day. The children played in the park.",
            'expected_complexity': 'simple'
        },
        {
            'text': "The implementation of machine learning algorithms requires careful consideration of various factors including data preprocessing, feature selection, and model validation techniques.",
            'expected_complexity': 'complex'
        },
        {
            'text': "Notwithstanding the aforementioned considerations, the paradigmatic framework necessitates a comprehensive methodology that encompasses multifaceted analytical approaches.",
            'expected_complexity': 'advanced'
        }
    ]
    
    try:
        for i, case in enumerate(test_texts, 1):
            print(f"\nTest {i}: Expected complexity - {case['expected_complexity']}")
            print(f"Text: {case['text'][:60]}...")
            
            result = complexity_analyzer.analyze_complexity(case['text'])
            
            print(f"  Readability score: {result.readability_score:.1f}")
            print(f"  Grade level: {result.grade_level:.1f}")
            print(f"  Complexity rating: {result.complexity_rating}")
            print(f"  Vocabulary diversity: {result.vocabulary_diversity:.2f}")
            print(f"  Recommendations: {len(result.recommendations)}")
        
        print("✅ Content complexity analysis test successful")
        return True
        
    except Exception as e:
        print(f"❌ Content complexity analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bias_detection():
    """Test bias detection functionality"""
    print("\n⚖️ Testing Bias Detection...")
    
    test_texts = [
        {
            'text': "The team of guys worked hard to complete the project. The chairman made the final decision.",
            'description': "Gender bias example"
        },
        {
            'text': "Young people these days don't understand hard work like older workers do.",
            'description': "Age bias example"
        },
        {
            'text': "The team members collaborated effectively to achieve their goals. Everyone contributed valuable insights.",
            'description': "Inclusive language example"
        },
        {
            'text': "The person with disabilities uses a wheelchair and has valuable expertise in accessibility design.",
            'description': "Person-first language example"
        }
    ]
    
    try:
        for i, case in enumerate(test_texts, 1):
            print(f"\nTest {i}: {case['description']}")
            print(f"Text: {case['text']}")
            
            result = bias_detector.analyze_bias(case['text'])
            
            print(f"  Bias score: {result.bias_score:.2f}")
            print(f"  Inclusive language score: {result.inclusive_language_score:.2f}")
            print(f"  Detected biases: {len(result.detected_biases)}")
            print(f"  Problematic phrases: {len(result.problematic_phrases)}")
            print(f"  Suggestions: {len(result.suggestions)}")
            
            if result.detected_biases:
                for bias in result.detected_biases:
                    print(f"    - {bias['category']} bias: {bias['pattern']} ({bias['severity']})")
        
        print("✅ Bias detection test successful")
        return True
        
    except Exception as e:
        print(f"❌ Bias detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plagiarism_detection():
    """Test plagiarism detection functionality"""
    print("\n🔍 Testing Plagiarism Detection...")
    
    # Create a simple reference database
    reference_database = [
        "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
        "Natural language processing is a branch of artificial intelligence that helps computers understand, interpret and manipulate human language.",
        "Deep learning uses neural networks with multiple layers to model and understand complex patterns in data."
    ]
    
    test_cases = [
        {
            'text': "Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
            'description': "High similarity to reference"
        },
        {
            'text': "Quantum computing represents a revolutionary approach to information processing using quantum mechanical phenomena.",
            'description': "Original content"
        },
        {
            'text': "AI and machine learning are transforming how we process information and make decisions in various industries.",
            'description': "Moderate similarity"
        }
    ]
    
    try:
        for i, case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {case['description']}")
            print(f"Text: {case['text'][:60]}...")
            
            result = plagiarism_detector.analyze_plagiarism(case['text'], reference_database)
            
            print(f"  Similarity score: {result.similarity_score:.2%}")
            print(f"  Originality score: {result.originality_score:.2%}")
            print(f"  Confidence: {result.confidence:.2%}")
            print(f"  Potential matches: {len(result.potential_matches)}")
            print(f"  Flagged segments: {len(result.flagged_segments)}")
            
            if result.potential_matches:
                top_match = result.potential_matches[0]
                print(f"    Top match similarity: {top_match['similarity']:.2%}")
        
        print("✅ Plagiarism detection test successful")
        return True
        
    except Exception as e:
        print(f"❌ Plagiarism detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_comprehensive_analysis():
    """Test comprehensive content analysis"""
    print("\n🧠 Testing Comprehensive Content Analysis...")
    
    test_text = """
    I'm absolutely thrilled to present our quarterly results today! The team has worked incredibly hard, 
    and I'm confident that our innovative approach to machine learning implementation has yielded 
    exceptional outcomes. While some stakeholders were initially concerned about the complexity of our 
    methodology, the results speak for themselves. Our revenue increased by 35%, and customer satisfaction 
    scores reached an all-time high. I believe this demonstrates the effectiveness of our strategic vision.
    """
    
    try:
        print("Running comprehensive analysis...")
        print(f"Text length: {len(test_text)} characters")
        
        result = advanced_content_analyzer.analyze_content(
            text=test_text,
            audio_duration=30.0,  # Assume 30 seconds
            timestamps=None,
            reference_database=None
        )
        
        if 'error' in result:
            print(f"❌ Analysis failed: {result['error']}")
            return False
        
        print("✅ Comprehensive analysis completed!")
        
        # Display key results
        if 'emotions' in result:
            emotions = result['emotions']
            print(f"  Dominant emotion: {emotions.dominant_emotion}")
            print(f"  Emotional intensity: {emotions.emotional_intensity:.2f}")
        
        if 'speaking_patterns' in result:
            patterns = result['speaking_patterns']
            print(f"  Speaking pace: {patterns.average_pace:.1f} WPM")
            print(f"  Speaking rhythm: {patterns.speaking_rhythm}")
        
        if 'complexity' in result:
            complexity = result['complexity']
            print(f"  Complexity rating: {complexity.complexity_rating}")
            print(f"  Readability score: {complexity.readability_score:.1f}")
        
        if 'bias' in result:
            bias = result['bias']
            print(f"  Bias score: {bias.bias_score:.2f}")
            print(f"  Inclusive language score: {bias.inclusive_language_score:.2f}")
        
        if 'plagiarism' in result:
            plagiarism = result['plagiarism']
            print(f"  Originality score: {plagiarism.originality_score:.2%}")
        
        if 'overall_score' in result:
            overall = result['overall_score']
            print(f"  Overall quality: {overall.get('overall_quality', 0):.2f}")
        
        print("✅ Comprehensive analysis test successful")
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_integration():
    """Test UI integration"""
    print("\n🎨 Testing UI Integration...")
    
    try:
        # Test UI component import
        from advanced_content_analysis_ui import advanced_content_analysis_ui
        print("✅ UI components imported successfully")
        
        # Test UI instance
        ui_instance = advanced_content_analysis_ui
        print(f"✅ UI instance created: {type(ui_instance)}")
        
        # Test analyzer integration
        analyzer = ui_instance.analyzer
        print(f"✅ Analyzer integration working: {type(analyzer)}")
        
        return True
        
    except Exception as e:
        print(f"❌ UI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all advanced content analysis tests"""
    print("🚀 Starting Advanced Content Analysis Tests (Task 39)")
    print("=" * 70)
    
    tests = [
        ("Emotion Detection", test_emotion_detection),
        ("Speaking Pattern Analysis", test_speaking_pattern_analysis),
        ("Content Complexity Analysis", test_content_complexity_analysis),
        ("Bias Detection", test_bias_detection),
        ("Plagiarism Detection", test_plagiarism_detection),
        ("Comprehensive Analysis", test_comprehensive_analysis),
        ("UI Integration", test_ui_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            if test_func():
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} test FAILED with error: {e}")
        
        print("-" * 70)
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All advanced content analysis tests passed!")
        print("\n🚀 Advanced content analysis is ready to use!")
        print("\nFeatures available:")
        print("• 😊 Emotion detection and mood tracking")
        print("• 🎤 Speaking pattern analysis (pace, pauses, emphasis)")
        print("• 📚 Content complexity and readability scoring")
        print("• ⚖️ Bias detection and inclusive language suggestions")
        print("• 🔍 Plagiarism detection and originality checking")
        print("\nTo use advanced content analysis:")
        print("1. Run: streamlit run app.py")
        print("2. Enable '🧠 Advanced Content Analysis' mode in sidebar")
        print("3. Analyze your content with AI-powered insights!")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Check the output above for details.")
    
    return passed == failed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)