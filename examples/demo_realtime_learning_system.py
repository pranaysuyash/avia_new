#!/usr/bin/env python3
"""
Demo Script for Real-Time Learning System
Interactive demonstration of real-time learning, adjustment, and effectiveness monitoring
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import the modules to demonstrate
from realtime_learning_system import (
    RealTimeLearningSystem, LearningTrigger, LearningMode, AdjustmentType,
    LearningEvent, RealTimeAdjustment, create_realtime_learning_system
)

from model_adaptation_engine import (
    ModelAdaptationEngine, create_model_adaptation_engine
)

from user_learning_profile import (
    PersonalizationEngine, CorrectionPattern, ModelPreference, DomainExpertise,
    create_personalization_engine, create_user_profile_storage
)

from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, ContentType, create_feedback_storage
)

class RealTimeLearningDemo:
    """Interactive demo for real-time learning system"""
    
    def __init__(self):
        """Initialize demo with storage systems"""
        print("🚀 Initializing Real-Time Learning System Demo...")
        
        # Create storage systems
        self.profile_storage = create_user_profile_storage("demo_profiles.db")
        self.feedback_storage = create_feedback_storage("demo_feedback.db")
        
        # Create engines
        self.personalization_engine = create_personalization_engine(
            self.profile_storage, self.feedback_storage
        )
        self.adaptation_engine = create_model_adaptation_engine(
            self.personalization_engine, self.feedback_storage
        )
        
        # Create real-time learning system
        self.learning_system = create_realtime_learning_system(
            self.personalization_engine, self.adaptation_engine, LearningMode.BALANCED
        )
        
        # Demo users with different learning scenarios
        self.demo_scenarios = [
            {
                'user_id': 'alice_researcher',
                'model_id': 'spacy_lg',
                'scenario': 'low_quality_feedback',
                'description': 'User consistently gives low ratings, triggering threshold adjustments'
            },
            {
                'user_id': 'bob_developer',
                'model_id': 'bert_base',
                'scenario': 'pattern_corrections',
                'description': 'User makes consistent correction patterns, triggering pattern learning'
            },
            {
                'user_id': 'carol_manager',
                'model_id': 'spacy_md',
                'scenario': 'vocabulary_expansion',
                'description': 'User corrections lead to vocabulary expansion'
            }
        ]
        
        # Register callback for real-time monitoring
        self.learning_system.register_adjustment_callback(self._on_adjustment_made)
        
        print("✅ Demo system initialized successfully!")
        print()
    
    def run_demo(self):
        """Run the complete demo"""
        print("=" * 60)
        print("🎯 REAL-TIME LEARNING SYSTEM DEMO")
        print("=" * 60)
        print()
        
        try:
            # Demo 1: System Overview
            self.demo_system_overview()
            
            # Demo 2: Real-Time Feedback Processing
            self.demo_realtime_feedback_processing()
            
            # Demo 3: Learning Mode Comparison
            self.demo_learning_modes()
            
            # Demo 4: Pattern Recognition and Learning
            self.demo_pattern_learning()
            
            # Demo 5: Effectiveness Monitoring
            self.demo_effectiveness_monitoring()
            
            # Demo 6: Advanced Features
            self.demo_advanced_features()
            
            print("🎉 Demo completed successfully!")
            
        except KeyboardInterrupt:
            print("\n⚠️ Demo interrupted by user")
        except Exception as e:
            print(f"❌ Demo error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def demo_system_overview(self):
        """Demo system overview and capabilities"""
        print("📋 DEMO 1: System Overview and Capabilities")
        print("-" * 50)
        
        print("🔧 Real-Time Learning Components:")
        print(f"  Learning Mode: {self.learning_system.learning_mode.value}")
        print(f"  Available Learners: {list(self.learning_system.learners.keys())}")
        print(f"  Queue Size: {len(self.learning_system.event_queue)}")
        print(f"  Processing Interval: {self.learning_system.config['processing_interval']}s")
        
        print("\n📊 Initial Statistics:")
        stats = self.learning_system.get_learning_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n🎯 Demo Scenarios:")
        for i, scenario in enumerate(self.demo_scenarios, 1):
            print(f"  {i}. {scenario['user_id']} ({scenario['model_id']})")
            print(f"     {scenario['description']}")
        
        print()
        self.wait_for_user()
    
    def demo_realtime_feedback_processing(self):
        """Demo real-time feedback processing"""
        print("⚡ DEMO 2: Real-Time Feedback Processing")
        print("-" * 50)
        
        print("Processing feedback in real-time and observing adjustments...")
        print()
        
        # Scenario 1: Low quality feedback triggering threshold adjustments
        print("📉 Scenario 1: Low Quality Feedback (Alice)")
        alice_feedbacks = self._create_low_quality_feedback_sequence('alice_researcher', 'spacy_lg')
        
        for i, feedback in enumerate(alice_feedbacks, 1):
            print(f"  Processing feedback {i}/5 (rating: {feedback.rating.value}/5)...")
            event_ids = self.learning_system.process_feedback(feedback)
            print(f"    Created events: {len(event_ids)}")
            time.sleep(0.5)  # Brief pause to show real-time nature
        
        print("  ⏳ Waiting for real-time processing...")
        time.sleep(2)
        
        # Check results
        alice_adjustments = self.learning_system.get_user_adjustments('alice_researcher')
        print(f"  ✅ Generated {len(alice_adjustments)} real-time adjustments")
        
        if alice_adjustments:
            latest = alice_adjustments[0]
            print(f"    Latest: {latest.adjustment_type.value} - "
                  f"{latest.parameter_name} {latest.old_value} → {latest.new_value}")
        
        print()
        
        # Scenario 2: Pattern corrections triggering pattern learning
        print("🔄 Scenario 2: Pattern Corrections (Bob)")
        bob_feedbacks = self._create_pattern_correction_sequence('bob_developer', 'bert_base')
        
        for i, feedback in enumerate(bob_feedbacks, 1):
            correction = feedback.correction
            print(f"  Processing correction {i}/4: '{correction.original_text}' → '{correction.corrected_text}'")
            event_ids = self.learning_system.process_feedback(feedback)
            time.sleep(0.3)
        
        print("  ⏳ Waiting for pattern recognition...")
        time.sleep(2)
        
        bob_adjustments = self.learning_system.get_user_adjustments('bob_developer')
        print(f"  ✅ Generated {len(bob_adjustments)} pattern-based adjustments")
        
        print()
        self.wait_for_user()
    
    def demo_learning_modes(self):
        """Demo different learning modes"""
        print("🎛️ DEMO 3: Learning Mode Comparison")
        print("-" * 50)
        
        modes_to_test = [LearningMode.CONSERVATIVE, LearningMode.AGGRESSIVE, LearningMode.BALANCED]
        
        for mode in modes_to_test:
            print(f"\n🔧 Testing {mode.value.upper()} mode:")
            
            # Set learning mode
            self.learning_system.set_learning_mode(mode)
            
            # Create test feedback
            feedback = self._create_sample_feedback('mode_test_user', 'test_model', rating_value=2)
            
            print(f"  Processing low-quality feedback...")
            event_ids = self.learning_system.process_feedback(feedback)
            
            # Wait for processing
            time.sleep(1)
            
            # Check adjustments
            adjustments = self.learning_system.get_user_adjustments('mode_test_user')
            recent_adjustments = [adj for adj in adjustments 
                                if adj.timestamp > datetime.now() - timedelta(seconds=30)]
            
            print(f"  Adjustments made: {len(recent_adjustments)}")
            
            if recent_adjustments:
                adj = recent_adjustments[0]
                print(f"    Type: {adj.adjustment_type.value}")
                print(f"    Confidence: {adj.confidence:.2f}")
                print(f"    Change: {adj.old_value} → {adj.new_value}")
        
        # Reset to balanced mode
        self.learning_system.set_learning_mode(LearningMode.BALANCED)
        print(f"\n🔄 Reset to BALANCED mode")
        
        print()
        self.wait_for_user()
    
    def demo_pattern_learning(self):
        """Demo pattern recognition and learning"""
        print("🧠 DEMO 4: Pattern Recognition and Learning")
        print("-" * 50)
        
        print("Demonstrating how the system learns from correction patterns...")
        
        # Create a series of similar corrections to establish a pattern
        patterns_to_learn = [
            ('ai', 'AI', 'capitalization'),
            ('ml', 'ML', 'capitalization'),
            ('nlp', 'NLP', 'capitalization'),
            ('api', 'API', 'capitalization'),
            ('ai', 'AI', 'capitalization'),  # Repeat to establish pattern
            ('ml', 'ML', 'capitalization'),  # Repeat to establish pattern
        ]
        
        print("\n📝 Teaching correction patterns:")
        for i, (original, corrected, correction_type) in enumerate(patterns_to_learn, 1):
            print(f"  {i}. '{original}' → '{corrected}' ({correction_type})")
            
            feedback = self._create_correction_feedback(
                'pattern_learner_user', 'spacy_md', original, corrected, correction_type
            )
            
            event_ids = self.learning_system.process_feedback(feedback)
            time.sleep(0.2)
        
        print("\n⏳ Waiting for pattern recognition...")
        time.sleep(3)
        
        # Check learned patterns
        user_adjustments = self.learning_system.get_user_adjustments('pattern_learner_user')
        pattern_adjustments = [adj for adj in user_adjustments 
                             if adj.adjustment_type == AdjustmentType.PATTERN_ADD]
        
        print(f"\n🎯 Pattern Learning Results:")
        print(f"  Total adjustments: {len(user_adjustments)}")
        print(f"  Pattern adjustments: {len(pattern_adjustments)}")
        
        if pattern_adjustments:
            print(f"  Learned patterns:")
            for adj in pattern_adjustments[-3:]:  # Show last 3
                print(f"    '{adj.old_value}' → '{adj.new_value}' (confidence: {adj.confidence:.2f})")
        
        # Test vocabulary learning
        print(f"\n📚 Vocabulary Learning:")
        vocab_adjustments = [adj for adj in user_adjustments 
                           if adj.adjustment_type == AdjustmentType.VOCABULARY_UPDATE]
        print(f"  Vocabulary additions: {len(vocab_adjustments)}")
        
        if vocab_adjustments:
            vocab_words = [adj.new_value for adj in vocab_adjustments[-5:]]
            print(f"  Recent additions: {vocab_words}")
        
        print()
        self.wait_for_user()
    
    def demo_effectiveness_monitoring(self):
        """Demo effectiveness monitoring and adjustment reversion"""
        print("📈 DEMO 5: Effectiveness Monitoring")
        print("-" * 50)
        
        print("Demonstrating how the system monitors adjustment effectiveness...")
        
        # Create some adjustments and simulate effectiveness monitoring
        print("\n🔧 Creating test adjustments...")
        
        # Force some learning updates to create adjustments
        for i in range(3):
            user_id = f"effectiveness_user_{i}"
            event_id = self.learning_system.force_learning_update(user_id, "test_model")
            print(f"  Forced learning update {i+1}: {event_id[:12]}...")
        
        time.sleep(2)
        
        # Get current statistics
        print(f"\n📊 Current Learning Statistics:")
        stats = self.learning_system.get_learning_statistics()
        
        key_stats = ['total_adjustments', 'success_rate', 'revert_rate', 'average_effectiveness']
        for key in key_stats:
            if key in stats:
                value = stats[key]
                if isinstance(value, float):
                    print(f"  {key}: {value:.2%}" if 'rate' in key else f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")
        
        # Show adjustment types
        if 'adjustment_types' in stats and stats['adjustment_types']:
            print(f"\n🔧 Adjustment Types:")
            for adj_type, count in stats['adjustment_types'].items():
                print(f"  {adj_type}: {count}")
        
        # Demonstrate cleanup
        print(f"\n🧹 Cleanup Demonstration:")
        original_count = len(self.learning_system.adjustment_history)
        print(f"  Adjustments before cleanup: {original_count}")
        
        # Add some old adjustments for cleanup demo
        from realtime_learning_system import RealTimeAdjustment, AdjustmentType
        old_adjustment = RealTimeAdjustment(
            adjustment_id="old_demo_adjustment",
            user_id="demo_user",
            model_id="demo_model",
            adjustment_type=AdjustmentType.THRESHOLD_ADJUST,
            parameter_name="test_param",
            old_value=0.8,
            new_value=0.85,
            confidence=0.9,
            trigger_event="demo_event",
            timestamp=datetime.now() - timedelta(days=40)
        )
        self.learning_system.adjustment_history.append(old_adjustment)
        
        cleaned_count = self.learning_system.cleanup_old_adjustments(days=30)
        final_count = len(self.learning_system.adjustment_history)
        
        print(f"  Cleaned up: {cleaned_count} old adjustments")
        print(f"  Adjustments after cleanup: {final_count}")
        
        print()
        self.wait_for_user()
    
    def demo_advanced_features(self):
        """Demo advanced features"""
        print("🚀 DEMO 6: Advanced Features")
        print("-" * 50)
        
        # Demo 6.1: Callback System
        print("📞 Callback System:")
        print("  Real-time adjustment notifications are enabled")
        print("  (Callbacks are triggered when adjustments are made)")
        
        # Create feedback to trigger callback
        callback_feedback = self._create_sample_feedback('callback_user', 'callback_model', rating_value=1)
        print(f"\n  Triggering callback with low-quality feedback...")
        self.learning_system.process_feedback(callback_feedback)
        time.sleep(1)
        print(f"  ✅ Callback demonstration complete")
        
        # Demo 6.2: Learning Control
        print(f"\n⏸️ Learning Control:")
        print(f"  Current learning mode: {self.learning_system.learning_mode.value}")
        
        # Demonstrate pause/resume (simulated)
        self.learning_system.pause_learning('demo_user')
        print(f"  ⏸️ Paused learning for demo_user")
        
        self.learning_system.resume_learning('demo_user')
        print(f"  ▶️ Resumed learning for demo_user")
        
        # Demo 6.3: Configuration
        print(f"\n⚙️ System Configuration:")
        config_items = [
            'max_queue_size', 'processing_interval', 'max_adjustments_per_minute'
        ]
        for item in config_items:
            if item in self.learning_system.config:
                print(f"  {item}: {self.learning_system.config[item]}")
        
        # Demo 6.4: User-Specific Statistics
        print(f"\n👤 User-Specific Statistics:")
        test_users = ['alice_researcher', 'bob_developer', 'carol_manager']
        
        for user_id in test_users:
            user_stats = self.learning_system.get_learning_statistics(user_id)
            if user_stats.get('total_adjustments', 0) > 0:
                print(f"  {user_id}:")
                print(f"    Total adjustments: {user_stats['total_adjustments']}")
                print(f"    Success rate: {user_stats.get('success_rate', 0):.2%}")
        
        print()
        self.wait_for_user()
    
    def _create_low_quality_feedback_sequence(self, user_id: str, model_id: str) -> List[Feedback]:
        """Create sequence of low quality feedback"""
        feedbacks = []
        
        for i in range(5):
            context = FeedbackContext(
                content_type=ContentType.TRANSCRIPTION,
                content_id=f"low_quality_content_{i}",
                original_content=f"Sample transcription {i}",
                confidence_score=0.8 - i * 0.05  # Decreasing confidence
            )
            
            rating = Rating(
                rating_id=f"low_rating_{i}",
                rating_type=RatingType.STARS,
                value=2 - (i % 2),  # Alternating between 1 and 2 stars
                max_value=5
            )
            
            feedback = Feedback(
                feedback_id=f"low_feedback_{i}",
                user_id=user_id,
                feedback_type=FeedbackType.RATING,
                context=context,
                timestamp=datetime.now(),
                rating=rating
            )
            
            feedbacks.append(feedback)
        
        return feedbacks
    
    def _create_pattern_correction_sequence(self, user_id: str, model_id: str) -> List[Feedback]:
        """Create sequence of pattern corrections"""
        corrections = [
            ('javascript', 'JavaScript', 'capitalization'),
            ('api', 'API', 'capitalization'),
            ('json', 'JSON', 'capitalization'),
            ('javascript', 'JavaScript', 'capitalization')  # Repeat to establish pattern
        ]
        
        feedbacks = []
        
        for i, (original, corrected, correction_type) in enumerate(corrections):
            feedbacks.append(self._create_correction_feedback(
                user_id, model_id, original, corrected, correction_type, i
            ))
        
        return feedbacks
    
    def _create_correction_feedback(self, user_id: str, model_id: str, 
                                  original: str, corrected: str, correction_type: str, 
                                  index: int = 0) -> Feedback:
        """Create correction feedback"""
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id=f"correction_content_{index}",
            original_content=f"Sample content with {original}",
            confidence_score=0.8
        )
        
        correction = Correction(
            correction_id=f"correction_{index}",
            original_text=original,
            corrected_text=corrected,
            correction_type=correction_type
        )
        
        feedback = Feedback(
            feedback_id=f"correction_feedback_{index}",
            user_id=user_id,
            feedback_type=FeedbackType.CORRECTION,
            context=context,
            timestamp=datetime.now(),
            correction=correction
        )
        
        return feedback
    
    def _create_sample_feedback(self, user_id: str, model_id: str, rating_value: int = 3) -> Feedback:
        """Create sample feedback"""
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id=f"sample_content_{user_id}",
            original_content="Sample transcription content",
            confidence_score=0.8
        )
        
        rating = Rating(
            rating_id=f"sample_rating_{user_id}",
            rating_type=RatingType.STARS,
            value=rating_value,
            max_value=5
        )
        
        feedback = Feedback(
            feedback_id=f"sample_feedback_{user_id}",
            user_id=user_id,
            feedback_type=FeedbackType.RATING,
            context=context,
            timestamp=datetime.now(),
            rating=rating
        )
        
        return feedback
    
    def _on_adjustment_made(self, adjustment: RealTimeAdjustment):
        """Callback for when adjustments are made"""
        print(f"    🔔 Real-time adjustment: {adjustment.adjustment_type.value} "
              f"for {adjustment.user_id} ({adjustment.parameter_name})")
    
    def wait_for_user(self):
        """Wait for user input to continue"""
        try:
            input("Press Enter to continue to the next demo section...")
            print()
        except KeyboardInterrupt:
            raise
    
    def cleanup(self):
        """Clean up demo resources"""
        print("\n🧹 Cleaning up demo resources...")
        
        # Stop systems
        self.learning_system.stop()
        self.adaptation_engine.stop()
        print("  ✅ Stopped learning and adaptation systems")
        
        # Clean up demo files
        demo_files = ["demo_profiles.db", "demo_feedback.db"]
        
        for file in demo_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"  ✅ Removed {file}")
            except Exception as e:
                print(f"  ⚠️ Could not remove {file}: {e}")

def main():
    """Main demo function"""
    demo = RealTimeLearningDemo()
    
    try:
        demo.run_demo()
    finally:
        # Ask user if they want to keep demo files
        try:
            keep_files = input("\nKeep demo database files? (y/N): ").lower().strip()
            if keep_files != 'y':
                demo.cleanup()
            else:
                print("Demo files kept: demo_profiles.db, demo_feedback.db")
        except KeyboardInterrupt:
            demo.cleanup()

if __name__ == "__main__":
    main()