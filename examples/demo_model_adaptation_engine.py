#!/usr/bin/env python3
"""
Demo Script for Model Adaptation Engine
Interactive demonstration of model adaptation, parameter tuning, and learning capabilities
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import the modules to demonstrate
from model_adaptation_engine import (
    ModelAdaptationEngine, SpacyModelAdapter, TransformerModelAdapter,
    AdaptationType, AdaptationScope, AdaptationStatus, AdaptationRule,
    ModelParameters, AdaptationResult, create_model_adaptation_engine
)

from user_learning_profile import (
    UserLearningProfile, PersonalizationEngine, CorrectionPattern,
    ModelPreference, DomainExpertise, create_personalization_engine,
    create_user_profile_storage
)

from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, ContentType, create_feedback_storage
)

class ModelAdaptationEngineDemo:
    """Interactive demo for model adaptation engine"""
    
    def __init__(self):
        """Initialize demo with storage systems"""
        print("🚀 Initializing Model Adaptation Engine Demo...")
        
        # Create storage systems
        self.profile_storage = create_user_profile_storage("demo_profiles.db")
        self.feedback_storage = create_feedback_storage("demo_feedback.db")
        
        # Create personalization engine
        self.personalization_engine = create_personalization_engine(
            self.profile_storage, self.feedback_storage
        )
        
        # Create adaptation engine
        self.adaptation_engine = create_model_adaptation_engine(
            self.personalization_engine, self.feedback_storage
        )
        
        # Demo users with different profiles
        self.demo_users = [
            {
                'user_id': 'alice_researcher',
                'preferences': {
                    'model_preference_type': 'accuracy_optimized',
                    'domain_expertise': ['academic', 'technical'],
                    'learning_goals': ['accuracy_improvement', 'domain_adaptation']
                },
                'correction_patterns': [
                    ('capitalization', 'ai', 'AI', 8, 0.9),
                    ('capitalization', 'ml', 'ML', 6, 0.8),
                    ('word_replacement', 'machine learning', 'Machine Learning', 5, 0.7)
                ]
            },
            {
                'user_id': 'bob_developer',
                'preferences': {
                    'model_preference_type': 'speed_optimized',
                    'domain_expertise': ['technical', 'business'],
                    'learning_goals': ['speed_improvement', 'workflow_optimization']
                },
                'correction_patterns': [
                    ('capitalization', 'api', 'API', 10, 0.95),
                    ('punctuation', 'hello world', 'hello, world', 4, 0.6),
                    ('word_replacement', 'javascript', 'JavaScript', 7, 0.8)
                ]
            },
            {
                'user_id': 'carol_manager',
                'preferences': {
                    'model_preference_type': 'balanced',
                    'domain_expertise': ['business', 'general'],
                    'learning_goals': ['feature_exploration']
                },
                'correction_patterns': [
                    ('capitalization', 'roi', 'ROI', 3, 0.5),
                    ('word_replacement', 'kpi', 'KPI', 4, 0.6)
                ]
            }
        ]
        
        print("✅ Demo system initialized successfully!")
        print()
    
    def run_demo(self):
        """Run the complete demo"""
        print("=" * 60)
        print("🎯 MODEL ADAPTATION ENGINE DEMO")
        print("=" * 60)
        print()
        
        try:
            # Demo 1: Setup User Profiles
            self.demo_user_profile_setup()
            
            # Demo 2: Individual Model Adaptations
            self.demo_individual_adaptations()
            
            # Demo 3: Adapter Functionality
            self.demo_adapter_functionality()
            
            # Demo 4: Global Improvements
            self.demo_global_improvements()
            
            # Demo 5: Adaptation Analytics
            self.demo_adaptation_analytics()
            
            # Demo 6: Rollback and Management
            self.demo_rollback_management()
            
            print("🎉 Demo completed successfully!")
            
        except KeyboardInterrupt:
            print("\n⚠️ Demo interrupted by user")
        except Exception as e:
            print(f"❌ Demo error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def demo_user_profile_setup(self):
        """Demo user profile setup for adaptation"""
        print("👥 DEMO 1: User Profile Setup for Adaptation")
        print("-" * 50)
        
        for user_data in self.demo_users:
            user_id = user_data['user_id']
            print(f"Setting up profile for {user_id}...")
            
            # Create/get profile
            profile = self.personalization_engine.get_or_create_profile(user_id)
            
            # Set preferences
            success = self.personalization_engine.update_user_preferences(
                user_id, user_data['preferences']
            )
            
            if success:
                print(f"  ✅ Preferences updated")
                print(f"  🎯 Model preference: {user_data['preferences']['model_preference_type']}")
                print(f"  🏷️ Domain expertise: {user_data['preferences']['domain_expertise']}")
                print(f"  📈 Learning goals: {user_data['preferences']['learning_goals']}")
            
            # Add correction patterns
            profile = self.personalization_engine.get_or_create_profile(user_id)
            for pattern_data in user_data['correction_patterns']:
                pattern_type, original, corrected, frequency, confidence = pattern_data
                
                pattern = CorrectionPattern(
                    pattern_id=f"{user_id}_{pattern_type}_{original}",
                    pattern_type=pattern_type,
                    original_pattern=original,
                    corrected_pattern=corrected,
                    frequency=frequency,
                    confidence=confidence
                )
                profile.correction_patterns.append(pattern)
            
            # Save updated profile
            self.personalization_engine.profile_storage.store_profile(profile)
            print(f"  📝 Added {len(user_data['correction_patterns'])} correction patterns")
            print()
        
        self.wait_for_user()
    
    def demo_individual_adaptations(self):
        """Demo individual model adaptations"""
        print("🔧 DEMO 2: Individual Model Adaptations")
        print("-" * 50)
        
        adaptation_scenarios = [
            {'user_id': 'alice_researcher', 'model_id': 'spacy_lg', 'type': AdaptationType.PARAMETER_TUNING},
            {'user_id': 'bob_developer', 'model_id': 'spacy_sm', 'type': AdaptationType.RULE_ADJUSTMENT},
            {'user_id': 'carol_manager', 'model_id': 'spacy_md', 'type': AdaptationType.VOCABULARY_EXPANSION},
            {'user_id': 'alice_researcher', 'model_id': 'bert_base', 'type': AdaptationType.PARAMETER_TUNING},
        ]
        
        adaptation_ids = []
        
        for scenario in adaptation_scenarios:
            user_id = scenario['user_id']
            model_id = scenario['model_id']
            adaptation_type = scenario['type']
            
            print(f"🔄 Adapting {model_id} for {user_id} ({adaptation_type.value})...")
            
            # Queue adaptation
            adaptation_id = self.adaptation_engine.adapt_model_for_user(
                user_id, model_id, adaptation_type
            )
            adaptation_ids.append(adaptation_id)
            
            print(f"  ✅ Queued adaptation: {adaptation_id[:12]}...")
        
        print(f"\n⏳ Waiting for {len(adaptation_ids)} adaptations to process...")
        time.sleep(3)  # Wait for processing
        
        # Check results
        print("\n📊 Adaptation Results:")
        for i, adaptation_id in enumerate(adaptation_ids):
            scenario = adaptation_scenarios[i]
            user_id = scenario['user_id']
            model_id = scenario['model_id']
            
            # Get adapted parameters
            adapted_params = self.adaptation_engine.get_adapted_parameters(user_id, model_id)
            
            if adapted_params:
                print(f"\n{user_id} - {model_id}:")
                print(f"  📅 Last updated: {adapted_params.last_updated.strftime('%H:%M:%S')}")
                print(f"  ⚙️ Parameters: {len(adapted_params.parameters)} items")
                print(f"  🎯 Confidence thresholds: {len(adapted_params.confidence_thresholds)} items")
                print(f"  📚 Vocabulary additions: {len(adapted_params.vocabulary_additions)} words")
                print(f"  🔄 Pattern overrides: {len(adapted_params.pattern_overrides)} patterns")
                
                # Show some specific adaptations
                if adapted_params.vocabulary_additions:
                    print(f"  📝 Sample vocabulary: {adapted_params.vocabulary_additions[:5]}")
                
                if adapted_params.pattern_overrides:
                    sample_patterns = list(adapted_params.pattern_overrides.items())[:3]
                    print(f"  🔧 Sample patterns: {sample_patterns}")
            else:
                print(f"\n{user_id} - {model_id}: ❌ Adaptation failed or pending")
        
        print()
        self.wait_for_user()
    
    def demo_adapter_functionality(self):
        """Demo specific adapter functionality"""
        print("🔬 DEMO 3: Adapter Functionality Deep Dive")
        print("-" * 50)
        
        # Demo SpaCy Adapter
        print("🔍 SpaCy Model Adapter:")
        spacy_adapter = SpacyModelAdapter()
        
        # Get a user profile with patterns
        alice_profile = self.personalization_engine.get_or_create_profile('alice_researcher')
        
        print(f"  📋 Supported models: {spacy_adapter.supported_models}")
        print(f"  📊 Parameter ranges: {spacy_adapter.parameter_ranges}")
        
        # Demonstrate adaptation
        try:
            adapted_params = spacy_adapter.adapt_parameters('spacy_md', [], alice_profile)
            print(f"  ✅ Adaptation successful")
            print(f"  📚 Vocabulary additions: {len(adapted_params.vocabulary_additions)}")
            print(f"  🔧 Processing rules: {list(adapted_params.processing_rules.keys())}")
            
            # Show validation
            original_params = ModelParameters(model_id='spacy_md')
            is_valid = spacy_adapter.validate_adaptation(original_params, adapted_params)
            print(f"  ✅ Validation passed: {is_valid}")
            
        except Exception as e:
            print(f"  ❌ Adaptation failed: {e}")
        
        print()
        
        # Demo Transformer Adapter
        print("🤖 Transformer Model Adapter:")
        transformer_adapter = TransformerModelAdapter()
        
        print(f"  📋 Supported models: {transformer_adapter.supported_models}")
        print(f"  📊 Parameter ranges: {transformer_adapter.parameter_ranges}")
        
        # Create sample feedback for transformer adaptation
        sample_feedback = self._create_sample_feedback('alice_researcher', rating_value=3)
        
        try:
            adapted_params = transformer_adapter.adapt_parameters('bert_base', sample_feedback, alice_profile)
            print(f"  ✅ Adaptation successful")
            print(f"  ⚙️ Parameters: {adapted_params.parameters}")
            
            # Show validation
            original_params = ModelParameters(model_id='bert_base')
            is_valid = transformer_adapter.validate_adaptation(original_params, adapted_params)
            print(f"  ✅ Validation passed: {is_valid}")
            
        except Exception as e:
            print(f"  ❌ Adaptation failed: {e}")
        
        print()
        self.wait_for_user()
    
    def demo_global_improvements(self):
        """Demo global improvements across models"""
        print("🌍 DEMO 4: Global Improvements")
        print("-" * 50)
        
        # Define global improvements
        improvements = [
            {
                'type': 'threshold_modification',
                'models': ['spacy_sm', 'spacy_md', 'spacy_lg'],
                'threshold_changes': {
                    'transcription': 0.85,
                    'meeting_element': 0.80,
                    'action_item': 0.90
                },
                'description': 'Increase confidence thresholds for better quality'
            },
            {
                'type': 'vocabulary_expansion',
                'models': ['spacy_md', 'spacy_lg'],
                'vocabulary': ['AI', 'ML', 'NLP', 'API', 'SDK', 'DevOps', 'CI/CD'],
                'description': 'Add common technical vocabulary'
            },
            {
                'type': 'rule_adjustment',
                'models': ['bert_base', 'roberta_base'],
                'rule_changes': {
                    'enable_domain_adaptation': True,
                    'attention_boost': 1.1,
                    'context_window_expansion': True
                },
                'description': 'Enhance transformer model processing rules'
            }
        ]
        
        print("📋 Applying Global Improvements:")
        
        for i, improvement in enumerate(improvements, 1):
            print(f"\n{i}. {improvement['description']}")
            print(f"   Type: {improvement['type']}")
            print(f"   Target models: {improvement['models']}")
            
            # Apply improvement
            applied_adaptations = self.adaptation_engine.apply_global_improvements([improvement])
            
            print(f"   ✅ Applied {len(applied_adaptations)} adaptations")
            
            # Show results for first model
            if improvement['models']:
                first_model = improvement['models'][0]
                global_params = self.adaptation_engine.model_parameters.get(f'global_{first_model}')
                
                if global_params:
                    print(f"   📊 {first_model} global parameters updated:")
                    if improvement['type'] == 'threshold_modification':
                        print(f"      Thresholds: {global_params.confidence_thresholds}")
                    elif improvement['type'] == 'vocabulary_expansion':
                        print(f"      Vocabulary: {len(global_params.vocabulary_additions)} words")
                    elif improvement['type'] == 'rule_adjustment':
                        print(f"      Rules: {list(global_params.processing_rules.keys())}")
        
        print()
        self.wait_for_user()
    
    def demo_adaptation_analytics(self):
        """Demo adaptation analytics and insights"""
        print("📈 DEMO 5: Adaptation Analytics")
        print("-" * 50)
        
        # Get comprehensive statistics
        stats = self.adaptation_engine.get_adaptation_statistics()
        
        print("📊 Overall Statistics:")
        print(f"  Total adaptations: {stats['total_adaptations']}")
        print(f"  Success rate: {stats['success_rate']:.2%}")
        print(f"  Recent adaptations (7 days): {stats['recent_adaptations']}")
        print(f"  Queue size: {stats['queue_size']}")
        print(f"  Active models: {stats['active_models']}")
        
        if stats['status_distribution']:
            print(f"\n📋 Status Distribution:")
            for status, count in stats['status_distribution'].items():
                print(f"  {status}: {count}")
        
        if stats['type_distribution']:
            print(f"\n🔧 Adaptation Type Distribution:")
            for adaptation_type, count in stats['type_distribution'].items():
                print(f"  {adaptation_type}: {count}")
        
        if stats['scope_distribution']:
            print(f"\n🎯 Scope Distribution:")
            for scope, count in stats['scope_distribution'].items():
                print(f"  {scope}: {count}")
        
        # User-specific analytics
        print(f"\n👤 User-Specific Analytics:")
        for user_data in self.demo_users:
            user_id = user_data['user_id']
            user_adaptations = self.adaptation_engine.get_user_adaptations(user_id)
            
            print(f"\n{user_id}:")
            print(f"  Total adaptations: {len(user_adaptations)}")
            
            if user_adaptations:
                successful = len([a for a in user_adaptations if a.status == AdaptationStatus.COMPLETED])
                success_rate = successful / len(user_adaptations)
                print(f"  Success rate: {success_rate:.2%}")
                
                # Show recent adaptations
                recent_adaptations = [a for a in user_adaptations 
                                    if a.created_at >= datetime.now() - timedelta(minutes=10)]
                print(f"  Recent adaptations: {len(recent_adaptations)}")
                
                # Show adapted models
                adapted_models = set(a.target_model for a in user_adaptations 
                                   if a.status == AdaptationStatus.COMPLETED)
                print(f"  Adapted models: {list(adapted_models)}")
        
        print()
        self.wait_for_user()
    
    def demo_rollback_management(self):
        """Demo rollback and management features"""
        print("🔄 DEMO 6: Rollback and Management")
        print("-" * 50)
        
        # Find a completed adaptation to rollback
        all_adaptations = self.adaptation_engine.adaptation_results
        completed_adaptations = [a for a in all_adaptations 
                               if a.status == AdaptationStatus.COMPLETED]
        
        if completed_adaptations:
            # Try to rollback the first completed adaptation
            adaptation_to_rollback = completed_adaptations[0]
            
            print(f"🔄 Attempting to rollback adaptation:")
            print(f"  Adaptation ID: {adaptation_to_rollback.adaptation_id[:12]}...")
            print(f"  User: {adaptation_to_rollback.target_user}")
            print(f"  Model: {adaptation_to_rollback.target_model}")
            print(f"  Type: {adaptation_to_rollback.adaptation_type.value}")
            
            # Attempt rollback
            success = self.adaptation_engine.rollback_adaptation(adaptation_to_rollback.adaptation_id)
            
            if success:
                print(f"  ✅ Rollback successful")
                
                # Check status update
                updated_adaptation = None
                for a in self.adaptation_engine.adaptation_results:
                    if a.adaptation_id == adaptation_to_rollback.adaptation_id:
                        updated_adaptation = a
                        break
                
                if updated_adaptation:
                    print(f"  📊 Status updated to: {updated_adaptation.status.value}")
            else:
                print(f"  ❌ Rollback failed")
        else:
            print("ℹ️ No completed adaptations available for rollback demo")
        
        print()
        
        # Demo cleanup functionality
        print("🧹 Cleanup Management:")
        
        # Add some old test adaptations
        old_adaptation = AdaptationResult(
            adaptation_id="old_test_adaptation",
            adaptation_type=AdaptationType.PARAMETER_TUNING,
            scope=AdaptationScope.USER_SPECIFIC,
            target_model="test_model",
            created_at=datetime.now() - timedelta(days=100)
        )
        
        self.adaptation_engine.adaptation_results.append(old_adaptation)
        
        original_count = len(self.adaptation_engine.adaptation_results)
        print(f"  📊 Adaptations before cleanup: {original_count}")
        
        # Cleanup old adaptations
        cleaned_count = self.adaptation_engine.cleanup_old_adaptations(days=90)
        
        final_count = len(self.adaptation_engine.adaptation_results)
        print(f"  🧹 Cleaned up: {cleaned_count} old adaptations")
        print(f"  📊 Adaptations after cleanup: {final_count}")
        
        print()
        self.wait_for_user()
    
    def _create_sample_feedback(self, user_id: str, rating_value: int = 4) -> List[Feedback]:
        """Create sample feedback for testing"""
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id=f"sample_content_{user_id}",
            original_content="Sample transcription content for testing",
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
        
        return [feedback]
    
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
        
        # Stop adaptation engine
        self.adaptation_engine.stop()
        print("  ✅ Stopped adaptation engine")
        
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
    demo = ModelAdaptationEngineDemo()
    
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