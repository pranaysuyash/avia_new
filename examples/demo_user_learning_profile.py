#!/usr/bin/env python3
"""
Demo Script for User Learning Profile System
Interactive demonstration of user profile management, personalization, and learning capabilities
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import the modules to demonstrate
from user_learning_profile import (
    UserLearningProfile, UserProfileStorage, PersonalizationEngine,
    ModelPreference, DomainExpertise, LearningGoal, CorrectionPattern,
    QualityThreshold, FeedbackHistory, create_user_profile_storage,
    create_personalization_engine
)

from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, ContentType, create_feedback_storage
)

class UserLearningProfileDemo:
    """Interactive demo for user learning profile system"""
    
    def __init__(self):
        """Initialize demo with storage systems"""
        print("🚀 Initializing User Learning Profile System Demo...")
        
        # Create storage systems
        self.profile_storage = create_user_profile_storage("demo_profiles.db")
        self.feedback_storage = create_feedback_storage("demo_feedback.db")
        
        # Create personalization engine
        self.engine = create_personalization_engine(self.profile_storage, self.feedback_storage)
        
        # Demo users
        self.demo_users = [
            "alice_researcher",
            "bob_developer", 
            "carol_manager",
            "david_student"
        ]
        
        print("✅ Demo system initialized successfully!")
        print()
    
    def run_demo(self):
        """Run the complete demo"""
        print("=" * 60)
        print("🎯 USER LEARNING PROFILE SYSTEM DEMO")
        print("=" * 60)
        print()
        
        try:
            # Demo 1: Profile Creation and Basic Operations
            self.demo_profile_creation()
            
            # Demo 2: User Preferences and Personalization
            self.demo_user_preferences()
            
            # Demo 3: Feedback Integration and Learning
            self.demo_feedback_learning()
            
            # Demo 4: Model Recommendations
            self.demo_model_recommendations()
            
            # Demo 5: Pattern Analysis and Insights
            self.demo_pattern_analysis()
            
            # Demo 6: Advanced Personalization Features
            self.demo_advanced_features()
            
            print("🎉 Demo completed successfully!")
            
        except KeyboardInterrupt:
            print("\n⚠️ Demo interrupted by user")
        except Exception as e:
            print(f"❌ Demo error: {e}")
            import traceback
            traceback.print_exc()
    
    def demo_profile_creation(self):
        """Demo profile creation and basic operations"""
        print("📝 DEMO 1: Profile Creation and Basic Operations")
        print("-" * 50)
        
        # Create profiles for demo users
        for user_id in self.demo_users:
            print(f"Creating profile for {user_id}...")
            profile = self.engine.get_or_create_profile(user_id)
            
            print(f"  ✅ Profile ID: {profile.profile_id[:12]}...")
            print(f"  📅 Created: {profile.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"  🎯 Default preference: {profile.model_preference_type.value}")
            print(f"  🏷️ Domain expertise: {[d.value for d in profile.domain_expertise]}")
            print()
        
        # Demonstrate profile retrieval
        print("🔍 Retrieving existing profile...")
        existing_profile = self.engine.get_or_create_profile(self.demo_users[0])
        print(f"  Retrieved profile for {existing_profile.user_id}")
        print(f"  Same profile ID: {existing_profile.profile_id[:12]}...")
        print()
        
        self.wait_for_user()
    
    def demo_user_preferences(self):
        """Demo user preferences and customization"""
        print("⚙️ DEMO 2: User Preferences and Personalization")
        print("-" * 50)
        
        # Set different preferences for each user
        user_preferences = {
            "alice_researcher": {
                'model_preference_type': 'accuracy_optimized',
                'domain_expertise': ['academic', 'technical'],
                'learning_goals': ['accuracy_improvement', 'domain_adaptation'],
                'preferred_models': ['bert_large', 'roberta_large'],
                'auto_apply_corrections': True,
                'feedback_frequency_preference': 'high'
            },
            "bob_developer": {
                'model_preference_type': 'speed_optimized',
                'domain_expertise': ['technical', 'business'],
                'learning_goals': ['speed_improvement', 'workflow_optimization'],
                'preferred_models': ['spacy_sm', 'distilbert'],
                'auto_apply_corrections': False,
                'feedback_frequency_preference': 'moderate'
            },
            "carol_manager": {
                'model_preference_type': 'balanced',
                'domain_expertise': ['business', 'general'],
                'learning_goals': ['feature_exploration'],
                'preferred_models': ['spacy_md', 'bert_base'],
                'auto_apply_corrections': True,
                'feedback_frequency_preference': 'low'
            },
            "david_student": {
                'model_preference_type': 'balanced',
                'domain_expertise': ['general', 'academic'],
                'learning_goals': ['accuracy_improvement', 'feature_exploration'],
                'auto_apply_corrections': True,
                'feedback_frequency_preference': 'moderate'
            }
        }
        
        for user_id, preferences in user_preferences.items():
            print(f"Setting preferences for {user_id}...")
            success = self.engine.update_user_preferences(user_id, preferences)
            
            if success:
                print(f"  ✅ Preferences updated successfully")
                print(f"  🎯 Model preference: {preferences['model_preference_type']}")
                print(f"  🏷️ Domain expertise: {preferences['domain_expertise']}")
                print(f"  📈 Learning goals: {preferences['learning_goals']}")
                print()
            else:
                print(f"  ❌ Failed to update preferences")
        
        # Show personalized settings
        print("🔍 Retrieving personalized settings...")
        for user_id in self.demo_users[:2]:  # Show first 2 users
            settings = self.engine.get_personalized_settings(user_id)
            print(f"\n{user_id} personalized settings:")
            print(f"  Auto-apply corrections: {settings['auto_apply_corrections']}")
            print(f"  Feedback frequency: {settings['feedback_frequency']}")
            print(f"  Domain expertise: {settings['domain_expertise']}")
            print(f"  Learning goals: {settings['learning_goals']}")
        
        print()
        self.wait_for_user()
    
    def demo_feedback_learning(self):
        """Demo feedback integration and learning"""
        print("🧠 DEMO 3: Feedback Integration and Learning")
        print("-" * 50)
        
        # Simulate feedback for different users
        feedback_scenarios = [
            {
                'user_id': 'alice_researcher',
                'feedbacks': [
                    # High-quality ratings
                    {'type': 'rating', 'rating_type': RatingType.STARS, 'value': 5, 'confidence': 0.95},
                    {'type': 'rating', 'rating_type': RatingType.STARS, 'value': 4, 'confidence': 0.88},
                    # Technical corrections
                    {'type': 'correction', 'original': 'machine learning', 'corrected': 'Machine Learning', 'correction_type': 'capitalization'},
                    {'type': 'correction', 'original': 'ai model', 'corrected': 'AI model', 'correction_type': 'capitalization'},
                ]
            },
            {
                'user_id': 'bob_developer',
                'feedbacks': [
                    # Mixed ratings (speed preference)
                    {'type': 'rating', 'rating_type': RatingType.THUMBS, 'value': True, 'confidence': 0.75},
                    {'type': 'rating', 'rating_type': RatingType.STARS, 'value': 3, 'confidence': 0.70},
                    # Code-related corrections
                    {'type': 'correction', 'original': 'javascript', 'corrected': 'JavaScript', 'correction_type': 'capitalization'},
                    {'type': 'correction', 'original': 'api endpoint', 'corrected': 'API endpoint', 'correction_type': 'capitalization'},
                ]
            }
        ]
        
        for scenario in feedback_scenarios:
            user_id = scenario['user_id']
            print(f"Processing feedback for {user_id}...")
            
            for i, feedback_data in enumerate(scenario['feedbacks']):
                # Create context
                context = FeedbackContext(
                    content_type=ContentType.TRANSCRIPTION,
                    content_id=f"{user_id}_content_{i}",
                    original_content=f"Sample content for {user_id}",
                    confidence_score=feedback_data.get('confidence', 0.8),
                    processing_method="demo_method",
                    model_version="demo_v1.0"
                )
                
                # Create feedback based on type
                if feedback_data['type'] == 'rating':
                    rating = Rating(
                        rating_id=f"{user_id}_rating_{i}",
                        rating_type=feedback_data['rating_type'],
                        value=feedback_data['value'],
                        max_value=5 if feedback_data['rating_type'] == RatingType.STARS else None
                    )
                    
                    feedback = Feedback(
                        feedback_id=f"{user_id}_feedback_{i}",
                        user_id=user_id,
                        feedback_type=FeedbackType.RATING,
                        context=context,
                        timestamp=datetime.now(),
                        rating=rating
                    )
                
                elif feedback_data['type'] == 'correction':
                    correction = Correction(
                        correction_id=f"{user_id}_correction_{i}",
                        original_text=feedback_data['original'],
                        corrected_text=feedback_data['corrected'],
                        correction_type=feedback_data['correction_type']
                    )
                    
                    feedback = Feedback(
                        feedback_id=f"{user_id}_feedback_{i}",
                        user_id=user_id,
                        feedback_type=FeedbackType.CORRECTION,
                        context=context,
                        timestamp=datetime.now(),
                        correction=correction
                    )
                
                # Update profile from feedback
                success = self.engine.update_profile_from_feedback(user_id, feedback)
                if success:
                    print(f"  ✅ Processed {feedback_data['type']} feedback")
                else:
                    print(f"  ❌ Failed to process {feedback_data['type']} feedback")
            
            print()
        
        # Show updated profiles
        print("📊 Updated Profile Statistics:")
        for user_id in [s['user_id'] for s in feedback_scenarios]:
            profile = self.engine.get_or_create_profile(user_id)
            history = profile.feedback_history
            
            print(f"\n{user_id}:")
            print(f"  Total feedback: {history.total_feedback_count}")
            print(f"  Average rating: {history.average_rating:.2f}")
            print(f"  Corrections: {history.correction_count}")
            print(f"  Correction patterns: {len(profile.correction_patterns)}")
        
        print()
        self.wait_for_user()
    
    def demo_model_recommendations(self):
        """Demo model recommendation system"""
        print("🤖 DEMO 4: Model Recommendations")
        print("-" * 50)
        
        content_scenarios = [
            {'type': ContentType.TRANSCRIPTION, 'complexity': 0.3, 'description': 'Simple conversation'},
            {'type': ContentType.TRANSCRIPTION, 'complexity': 0.8, 'description': 'Technical presentation'},
            {'type': ContentType.MOM_DOCUMENT, 'complexity': 0.6, 'description': 'Meeting minutes'},
            {'type': ContentType.ACTION_ITEM, 'complexity': 0.7, 'description': 'Action item extraction'}
        ]
        
        for user_id in self.demo_users[:2]:  # Show first 2 users
            print(f"🔍 Model recommendations for {user_id}:")
            
            for scenario in content_scenarios:
                recommendations = self.engine.recommend_model_selection(
                    user_id, 
                    scenario['type'], 
                    scenario['complexity']
                )
                
                print(f"\n  📋 {scenario['description']} (complexity: {scenario['complexity']:.1f})")
                print(f"     Content type: {scenario['type'].value}")
                print(f"     Priority: {recommendations['priority']}")
                print(f"     Recommended models: {recommendations['recommended_models'][:3]}")
                print(f"     Quality threshold: {recommendations['quality_threshold']:.2f}")
                print(f"     Reasoning: {recommendations['reasoning']}")
            
            print()
        
        self.wait_for_user()
    
    def demo_pattern_analysis(self):
        """Demo pattern analysis and insights"""
        print("📈 DEMO 5: Pattern Analysis and Insights")
        print("-" * 50)
        
        for user_id in self.demo_users[:2]:  # Analyze first 2 users
            print(f"🔍 Analyzing patterns for {user_id}...")
            
            analysis = self.engine.analyze_user_patterns(user_id)
            
            print(f"\n📊 Analysis Results:")
            print(f"  Profile age: {analysis['profile_age_days']} days")
            
            # Pattern analysis
            pattern_analysis = analysis['pattern_analysis']
            print(f"\n  🔧 Correction Patterns:")
            print(f"    Total patterns: {pattern_analysis['total_patterns']}")
            if pattern_analysis['total_patterns'] > 0:
                print(f"    Pattern types: {pattern_analysis['pattern_types']}")
                print(f"    Average confidence: {pattern_analysis['average_confidence']:.2f}")
                
                if pattern_analysis['most_frequent']:
                    print(f"    Most frequent corrections:")
                    for pattern in pattern_analysis['most_frequent'][:3]:
                        print(f"      '{pattern['original']}' → '{pattern['corrected']}' ({pattern['frequency']}x)")
                
                if pattern_analysis['insights']:
                    print(f"    💡 Insights:")
                    for insight in pattern_analysis['insights']:
                        print(f"      • {insight}")
            
            # Feedback analysis
            feedback_analysis = analysis['feedback_analysis']
            print(f"\n  📝 Feedback Analysis:")
            print(f"    Total feedback: {feedback_analysis['total_feedback']}")
            print(f"    Average rating: {feedback_analysis['average_rating']:.2f}")
            print(f"    Correction ratio: {feedback_analysis['correction_ratio']:.2f}")
            print(f"    Engagement level: {feedback_analysis['engagement_level']}")
            
            # Recommendations
            if analysis['recommendations']:
                print(f"\n  💡 Recommendations:")
                for rec in analysis['recommendations']:
                    print(f"    • {rec}")
            
            # Learning progress
            progress = analysis['learning_progress']
            print(f"\n  📈 Learning Progress:")
            print(f"    Days active: {progress['days_active']}")
            print(f"    Feedback per day: {progress['feedback_per_day']:.2f}")
            print(f"    Pattern learning rate: {progress['pattern_learning_rate']:.2f}")
            print(f"    Improvement trend: {progress['improvement_trend']}")
            print(f"    Expertise development: {progress['expertise_development']}")
            
            print("\n" + "-" * 40)
        
        self.wait_for_user()
    
    def demo_advanced_features(self):
        """Demo advanced personalization features"""
        print("🚀 DEMO 6: Advanced Personalization Features")
        print("-" * 50)
        
        # Demo 6.1: Profile Statistics
        print("📊 Profile Storage Statistics:")
        stats = self.profile_storage.get_profile_statistics()
        print(f"  Total profiles: {stats.get('total_profiles', 0)}")
        print(f"  Active this week: {stats.get('active_week', 0)}")
        print(f"  Active this month: {stats.get('active_month', 0)}")
        if stats.get('oldest_profile'):
            print(f"  Oldest profile: {stats['oldest_profile']}")
        if stats.get('most_recent_update'):
            print(f"  Most recent update: {stats['most_recent_update']}")
        print()
        
        # Demo 6.2: Profile Listing
        print("📋 Profile Listing:")
        profiles = self.profile_storage.list_profiles(limit=5)
        for profile_info in profiles:
            print(f"  User: {profile_info['user_id']}")
            print(f"    Profile ID: {profile_info['profile_id'][:12]}...")
            print(f"    Created: {profile_info['created_at']}")
            print(f"    Updated: {profile_info['last_updated']}")
            print()
        
        # Demo 6.3: Quality Threshold Adaptation
        print("🎯 Quality Threshold Adaptation:")
        user_id = self.demo_users[0]
        profile = self.engine.get_or_create_profile(user_id)
        
        print(f"Quality thresholds for {user_id}:")
        for threshold in profile.quality_thresholds:
            print(f"  {threshold.content_type.value}:")
            print(f"    Minimum confidence: {threshold.minimum_confidence:.2f}")
            print(f"    Preferred confidence: {threshold.preferred_confidence:.2f}")
            print(f"    Acceptable error rate: {threshold.acceptable_error_rate:.2f}")
        print()
        
        # Demo 6.4: Correction Pattern Evolution
        print("🔄 Correction Pattern Evolution:")
        if profile.correction_patterns:
            print(f"Correction patterns for {user_id}:")
            for pattern in profile.correction_patterns[:3]:
                print(f"  Pattern: {pattern.pattern_type}")
                print(f"    '{pattern.original_pattern}' → '{pattern.corrected_pattern}'")
                print(f"    Frequency: {pattern.frequency}, Confidence: {pattern.confidence:.2f}")
                print(f"    Last seen: {pattern.last_seen.strftime('%Y-%m-%d %H:%M')}")
                print()
        else:
            print(f"  No correction patterns yet for {user_id}")
        
        # Demo 6.5: Personalization Summary
        print("🎨 Personalization Summary:")
        for user_id in self.demo_users:
            settings = self.engine.get_personalized_settings(user_id)
            print(f"\n{user_id}:")
            print(f"  Domain expertise: {', '.join(settings['domain_expertise'])}")
            print(f"  Learning goals: {', '.join(settings['learning_goals'])}")
            print(f"  Total feedback: {settings['total_feedback']}")
            print(f"  Average rating: {settings['average_rating']:.2f}")
            print(f"  Correction patterns: {settings['correction_patterns_count']}")
        
        print()
        self.wait_for_user()
    
    def wait_for_user(self):
        """Wait for user input to continue"""
        try:
            input("Press Enter to continue to the next demo section...")
            print()
        except KeyboardInterrupt:
            raise
    
    def cleanup(self):
        """Clean up demo files"""
        demo_files = ["demo_profiles.db", "demo_feedback.db"]
        
        print("🧹 Cleaning up demo files...")
        for file in demo_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"  ✅ Removed {file}")
            except Exception as e:
                print(f"  ⚠️ Could not remove {file}: {e}")

def main():
    """Main demo function"""
    demo = UserLearningProfileDemo()
    
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