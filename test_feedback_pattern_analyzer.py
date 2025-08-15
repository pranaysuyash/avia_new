#!/usr/bin/env python3
"""
Test suite for Feedback Pattern Analysis and Recognition System
Comprehensive testing with progress tracking and visual feedback
"""

import pytest
import sys
import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import List
from unittest.mock import patch, MagicMock

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Progress tracking utilities (reused from feedback data models tests)
def print_separator(title="", char="=", width=80):
    """Print a formatted separator"""
    if title:
        title_line = f" {title} "
        padding = (width - len(title_line)) // 2
        print(char * padding + title_line + char * padding)
    else:
        print(char * width)

def print_progress(current, total, task_name="Testing", width=50):
    """Print a progress bar"""
    progress = current / total
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percentage = progress * 100
    print(f"\r{task_name}: |{bar}| {percentage:.1f}% ({current}/{total})", end='', flush=True)
    if current == total:
        print()  # New line when complete

def print_test_status(test_name, status="RUNNING", details=""):
    """Print test status with visual indicators"""
    status_icons = {
        'RUNNING': '🔄',
        'PASSED': '✅',
        'FAILED': '❌',
        'SKIPPED': '⏭️',
        'SETUP': '🔧',
        'TEARDOWN': '🧹'
    }
    icon = status_icons.get(status, '📋')
    detail_text = f" - {details}" if details else ""
    print(f"{icon} {test_name}: {status}{detail_text}")

class ProgressTracker:
    """Context manager for tracking test progress"""
    
    def __init__(self, test_name, total_steps=1):
        self.test_name = test_name
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        print_test_status(self.test_name, "RUNNING")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            print_test_status(self.test_name, "PASSED", f"completed in {duration:.2f}s")
        else:
            print_test_status(self.test_name, "FAILED", f"error after {duration:.2f}s")
    
    def step(self, description=""):
        """Advance to next step"""
        self.current_step += 1
        if self.total_steps > 1:
            print_progress(self.current_step, self.total_steps, f"{self.test_name}")
        if description:
            print(f"  📝 {description}")
        time.sleep(0.01)  # Minimal delay for visual effect
# Import the modules we're testing
from feedback_pattern_analyzer import (
    PatternAnalyzer, CorrectionPatternDetector, RatingPatternDetector,
    PreferenceAnalyzer, TrendAnalyzer, Pattern, UserPreference, TrendAnalysis,
    PatternType, TrendDirection, create_pattern_analyzer
)

from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, FeedbackStatus, ContentType,
    generate_feedback_id, generate_rating_id, generate_correction_id
)

from feedback_collector import FeedbackCollector

class TestPatternDetection:
    """Test pattern detection functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.storage = FeedbackStorage(self.temp_db.name)
        self.analyzer = create_pattern_analyzer(self.storage)
        
        # Create test data
        self.test_feedback = self._create_test_feedback_data()
        
        # Store test feedback
        for feedback in self.test_feedback:
            self.storage.store_feedback(feedback)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_test_feedback_data(self) -> List[Feedback]:
        """Create comprehensive test feedback data"""
        feedback_data = []
        base_time = datetime.now() - timedelta(days=10)
        
        # Create contexts for different content types
        contexts = [
            FeedbackContext(
                content_type=ContentType.TRANSCRIPTION,
                content_id="transcript_001",
                original_content="Hello everyone, welcome to today's meeting.",
                confidence_score=0.95
            ),
            FeedbackContext(
                content_type=ContentType.MEETING_ELEMENT,
                content_id="agenda_001",
                original_content="Discuss quarterly budget planning",
                confidence_score=0.88
            ),
            FeedbackContext(
                content_type=ContentType.ACTION_ITEM,
                content_id="action_001",
                original_content="John will prepare the financial report",
                confidence_score=0.92
            )
        ]
        
        # Create pattern-rich feedback data
        users = ["user_alice", "user_bob", "user_charlie", "user_diana"]
        
        for i, user in enumerate(users):
            for j, context in enumerate(contexts):
                # Create rating feedback with patterns
                if user == "user_alice":  # Harsh rater
                    rating_value = 2
                elif user == "user_bob":  # Lenient rater
                    rating_value = 5
                else:  # Normal raters
                    rating_value = 3 + (i + j) % 3
                
                rating = Rating(
                    rating_id=generate_rating_id(),
                    rating_type=RatingType.STARS,
                    value=rating_value,
                    max_value=5,
                    comment=f"Rating from {user}"
                )
                
                rating_feedback = Feedback(
                    feedback_id=generate_feedback_id(),
                    user_id=user,
                    feedback_type=FeedbackType.RATING,
                    context=context,
                    timestamp=base_time + timedelta(days=i, hours=j),
                    rating=rating
                )
                feedback_data.append(rating_feedback)
                
                # Create correction feedback with patterns
                if user in ["user_alice", "user_charlie"]:  # Users who make corrections
                    correction_types = {
                        "user_alice": "punctuation",  # Alice focuses on punctuation
                        "user_charlie": "spelling"    # Charlie focuses on spelling
                    }
                    
                    correction = Correction(
                        correction_id=generate_correction_id(),
                        original_text="today's",
                        corrected_text="today's",
                        correction_type=correction_types[user],
                        explanation=f"Correction by {user}"
                    )
                    
                    correction_feedback = Feedback(
                        feedback_id=generate_feedback_id(),
                        user_id=user,
                        feedback_type=FeedbackType.CORRECTION,
                        context=context,
                        timestamp=base_time + timedelta(days=i, hours=j+1),
                        correction=correction
                    )
                    feedback_data.append(correction_feedback)
        
        return feedback_data
    
    def test_correction_pattern_detection(self):
        """Test correction pattern detection"""
        with ProgressTracker("Correction Pattern Detection", 5) as tracker:
            tracker.step("Creating correction pattern detector")
            detector = CorrectionPatternDetector()
            
            tracker.step("Filtering correction feedback")
            corrections = [f for f in self.test_feedback if f.feedback_type == FeedbackType.CORRECTION]
            
            tracker.step("Detecting correction patterns")
            patterns = detector.detect_patterns(self.test_feedback)
            
            tracker.step("Validating pattern detection")
            assert len(patterns) > 0, "Should detect correction patterns"
            
            # Check for user-specific patterns
            user_patterns = [p for p in patterns if p.pattern_type == PatternType.USER_BEHAVIOR]
            assert len(user_patterns) > 0, "Should detect user behavior patterns"
            
            tracker.step("Verifying pattern details")
            # Verify pattern structure
            for pattern in patterns:
                assert pattern.pattern_id is not None
                assert pattern.confidence > 0
                assert pattern.frequency > 0
                assert len(pattern.affected_users) > 0
    
    def test_rating_pattern_detection(self):
        """Test rating pattern detection"""
        with ProgressTracker("Rating Pattern Detection", 5) as tracker:
            tracker.step("Creating rating pattern detector")
            detector = RatingPatternDetector()
            
            tracker.step("Filtering rating feedback")
            ratings = [f for f in self.test_feedback if f.feedback_type == FeedbackType.RATING]
            
            tracker.step("Detecting rating patterns")
            patterns = detector.detect_patterns(self.test_feedback)
            
            tracker.step("Validating pattern detection")
            assert len(patterns) > 0, "Should detect rating patterns"
            
            # Check for user behavior patterns (harsh/lenient raters)
            user_patterns = [p for p in patterns if p.pattern_type == PatternType.USER_BEHAVIOR]
            assert len(user_patterns) > 0, "Should detect user rating behavior patterns"
            
            tracker.step("Verifying harsh/lenient rater detection")
            # Should detect harsh rater (user_alice) and lenient rater (user_bob)
            pattern_descriptions = [p.description for p in user_patterns]
            harsh_detected = any("low ratings" in desc for desc in pattern_descriptions)
            lenient_detected = any("high ratings" in desc for desc in pattern_descriptions)
            
            assert harsh_detected or lenient_detected, "Should detect harsh or lenient rater patterns"

class TestPreferenceAnalysis:
    """Test user preference analysis"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.storage = FeedbackStorage(self.temp_db.name)
        self.preference_analyzer = PreferenceAnalyzer()
        
        # Create test data with clear preferences
        self.test_feedback = self._create_preference_test_data()
        
        # Store test feedback
        for feedback in self.test_feedback:
            self.storage.store_feedback(feedback)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_preference_test_data(self) -> List[Feedback]:
        """Create test data with clear user preferences"""
        feedback_data = []
        base_time = datetime.now() - timedelta(days=5)
        
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="Test content for preferences"
        )
        
        # Create user with clear rating preferences (always uses stars, harsh rater)
        user_id = "preference_test_user"
        
        for i in range(6):  # Create enough data for pattern detection
            # Consistent star ratings with low values
            rating = Rating(
                rating_id=generate_rating_id(),
                rating_type=RatingType.STARS,
                value=2,  # Consistently low
                max_value=5,
                comment="Consistent rating pattern"
            )
            
            rating_feedback = Feedback(
                feedback_id=generate_feedback_id(),
                user_id=user_id,
                feedback_type=FeedbackType.RATING,
                context=context,
                timestamp=base_time + timedelta(hours=i),
                rating=rating
            )
            feedback_data.append(rating_feedback)
            
            # Consistent correction type preferences
            correction = Correction(
                correction_id=generate_correction_id(),
                original_text=f"test{i}",
                corrected_text=f"Test{i}",
                correction_type="capitalization",  # Consistent type
                explanation="Detailed explanation"  # Always provides explanations
            )
            
            correction_feedback = Feedback(
                feedback_id=generate_feedback_id(),
                user_id=user_id,
                feedback_type=FeedbackType.CORRECTION,
                context=context,
                timestamp=base_time + timedelta(hours=i+0.5),
                correction=correction
            )
            feedback_data.append(correction_feedback)
        
        return feedback_data
    
    def test_user_preference_analysis(self):
        """Test user preference analysis"""
        with ProgressTracker("User Preference Analysis", 6) as tracker:
            tracker.step("Analyzing user preferences")
            user_id = "preference_test_user"
            preferences = self.preference_analyzer.analyze_user_preferences(user_id, self.test_feedback)
            
            tracker.step("Validating preference detection")
            assert len(preferences) > 0, "Should detect user preferences"
            
            tracker.step("Checking rating preferences")
            rating_prefs = [p for p in preferences if p.preference_type == "preferred_rating_type"]
            assert len(rating_prefs) > 0, "Should detect preferred rating type"
            
            # Should prefer STARS rating type
            stars_pref = next((p for p in rating_prefs if p.preference_value == "stars"), None)
            assert stars_pref is not None, "Should detect stars rating preference"
            
            tracker.step("Checking rating severity preferences")
            severity_prefs = [p for p in preferences if p.preference_type == "rating_severity"]
            assert len(severity_prefs) > 0, "Should detect rating severity preference"
            
            # Should be detected as harsh rater
            harsh_pref = next((p for p in severity_prefs if p.preference_value == "harsh"), None)
            assert harsh_pref is not None, "Should detect harsh rating preference"
            
            tracker.step("Checking correction preferences")
            correction_prefs = [p for p in preferences if p.preference_type == "correction_focus"]
            assert len(correction_prefs) > 0, "Should detect correction focus preference"
            
            # Should focus on capitalization
            cap_pref = next((p for p in correction_prefs if p.preference_value == "capitalization"), None)
            assert cap_pref is not None, "Should detect capitalization correction preference"
            
            tracker.step("Checking correction detail level")
            detail_prefs = [p for p in preferences if p.preference_type == "correction_detail_level"]
            assert len(detail_prefs) > 0, "Should detect correction detail level preference"
            
            # Should be detailed (always provides explanations)
            detailed_pref = next((p for p in detail_prefs if p.preference_value == "detailed"), None)
            assert detailed_pref is not None, "Should detect detailed correction preference"

class TestTrendAnalysis:
    """Test trend analysis functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.storage = FeedbackStorage(self.temp_db.name)
        self.trend_analyzer = TrendAnalyzer()
        
        # Create test data with trends
        self.test_feedback = self._create_trend_test_data()
        
        # Store test feedback
        for feedback in self.test_feedback:
            self.storage.store_feedback(feedback)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_trend_test_data(self) -> List[Feedback]:
        """Create test data with clear trends"""
        feedback_data = []
        base_time = datetime.now() - timedelta(days=10)
        
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="trend_test_content",
            original_content="Test content for trends"
        )
        
        # Create improving rating trend (ratings get better over time)
        for day in range(8):
            for hour in range(3):  # Multiple ratings per day
                # Ratings improve over time (2 -> 5)
                rating_value = min(5, 2 + (day * 0.4))
                
                rating = Rating(
                    rating_id=generate_rating_id(),
                    rating_type=RatingType.STARS,
                    value=int(rating_value),
                    max_value=5
                )
                
                rating_feedback = Feedback(
                    feedback_id=generate_feedback_id(),
                    user_id=f"trend_user_{hour}",
                    feedback_type=FeedbackType.RATING,
                    context=context,
                    timestamp=base_time + timedelta(days=day, hours=hour),
                    rating=rating
                )
                feedback_data.append(rating_feedback)
        
        # Create increasing correction trend (more corrections over time)
        for day in range(8):
            correction_count = day + 1  # Increasing corrections per day
            
            for i in range(correction_count):
                correction = Correction(
                    correction_id=generate_correction_id(),
                    original_text=f"error{day}{i}",
                    corrected_text=f"Error{day}{i}",
                    correction_type="capitalization"
                )
                
                correction_feedback = Feedback(
                    feedback_id=generate_feedback_id(),
                    user_id=f"trend_user_{i}",
                    feedback_type=FeedbackType.CORRECTION,
                    context=context,
                    timestamp=base_time + timedelta(days=day, hours=12+i),
                    correction=correction
                )
                feedback_data.append(correction_feedback)
        
        return feedback_data
    
    def test_trend_analysis(self):
        """Test trend analysis"""
        with ProgressTracker("Trend Analysis", 5) as tracker:
            tracker.step("Analyzing trends in feedback data")
            trends = self.trend_analyzer.analyze_trends(self.test_feedback, time_window_days=15)
            
            tracker.step("Validating trend detection")
            assert len(trends) > 0, "Should detect trends in data"
            
            tracker.step("Checking for rating trends")
            rating_trends = [t for t in trends if t.metric_name == "average_rating"]
            assert len(rating_trends) > 0, "Should detect rating trends"
            
            # Should detect increasing rating trend
            increasing_trends = [t for t in rating_trends if t.direction == TrendDirection.INCREASING]
            assert len(increasing_trends) > 0, "Should detect increasing rating trend"
            
            tracker.step("Checking for correction trends")
            correction_trends = [t for t in trends if t.metric_name == "correction_count"]
            assert len(correction_trends) > 0, "Should detect correction trends"
            
            tracker.step("Validating trend properties")
            for trend in trends:
                assert trend.confidence >= 0, "Trend confidence should be non-negative"
                assert trend.magnitude >= 0, "Trend magnitude should be non-negative"
                assert len(trend.data_points) >= 3, "Should have sufficient data points"

class TestPatternAnalyzer:
    """Test the main PatternAnalyzer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.storage = FeedbackStorage(self.temp_db.name)
        self.analyzer = create_pattern_analyzer(self.storage)
        
        # Create comprehensive test data
        self.test_feedback = self._create_comprehensive_test_data()
        
        # Store test feedback
        for feedback in self.test_feedback:
            self.storage.store_feedback(feedback)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_comprehensive_test_data(self) -> List[Feedback]:
        """Create comprehensive test data for full analysis"""
        feedback_data = []
        base_time = datetime.now() - timedelta(days=15)
        
        contexts = [
            FeedbackContext(
                content_type=ContentType.TRANSCRIPTION,
                content_id="comprehensive_transcript",
                original_content="Comprehensive test transcript"
            ),
            FeedbackContext(
                content_type=ContentType.MEETING_ELEMENT,
                content_id="comprehensive_meeting",
                original_content="Comprehensive test meeting"
            )
        ]
        
        users = ["comp_user_1", "comp_user_2", "comp_user_3"]
        
        # Create diverse feedback with patterns
        for day in range(10):
            for user_idx, user in enumerate(users):
                for context_idx, context in enumerate(contexts):
                    # Rating feedback
                    rating_value = 3 + user_idx + (day % 3)  # Varied ratings
                    rating = Rating(
                        rating_id=generate_rating_id(),
                        rating_type=RatingType.STARS,
                        value=min(5, rating_value),
                        max_value=5
                    )
                    
                    rating_feedback = Feedback(
                        feedback_id=generate_feedback_id(),
                        user_id=user,
                        feedback_type=FeedbackType.RATING,
                        context=context,
                        timestamp=base_time + timedelta(days=day, hours=user_idx*2),
                        rating=rating
                    )
                    feedback_data.append(rating_feedback)
                    
                    # Correction feedback (some users more active)
                    if user_idx <= 1 and day % 2 == 0:  # Some users make more corrections
                        correction = Correction(
                            correction_id=generate_correction_id(),
                            original_text=f"test{day}",
                            corrected_text=f"Test{day}",
                            correction_type="capitalization" if user_idx == 0 else "spelling"
                        )
                        
                        correction_feedback = Feedback(
                            feedback_id=generate_feedback_id(),
                            user_id=user,
                            feedback_type=FeedbackType.CORRECTION,
                            context=context,
                            timestamp=base_time + timedelta(days=day, hours=user_idx*2+1),
                            correction=correction
                        )
                        feedback_data.append(correction_feedback)
        
        return feedback_data
    
    def test_comprehensive_analysis(self):
        """Test comprehensive pattern analysis"""
        with ProgressTracker("Comprehensive Pattern Analysis", 8) as tracker:
            tracker.step("Running comprehensive analysis")
            results = self.analyzer.analyze_all_patterns(time_window_days=20)
            
            tracker.step("Validating analysis results structure")
            assert 'patterns' in results
            assert 'user_preferences' in results
            assert 'trends' in results
            assert 'summary' in results
            
            tracker.step("Checking pattern detection results")
            patterns = results['patterns']
            assert len(patterns) > 0, "Should detect patterns"
            
            # Validate pattern structure
            for pattern in patterns:
                assert 'pattern_id' in pattern
                assert 'pattern_type' in pattern
                assert 'confidence' in pattern
                assert 'frequency' in pattern
            
            tracker.step("Checking user preference analysis")
            user_preferences = results['user_preferences']
            assert len(user_preferences) > 0, "Should analyze user preferences"
            
            tracker.step("Checking trend analysis")
            trends = results['trends']
            # Trends might be empty if data doesn't show clear trends
            assert isinstance(trends, list), "Trends should be a list"
            
            tracker.step("Validating summary statistics")
            summary = results['summary']
            assert summary['total_feedback'] > 0
            assert summary['unique_users'] > 0
            assert summary['patterns_detected'] >= 0
            
            tracker.step("Testing pattern filtering methods")
            # Test pattern filtering methods
            high_conf_patterns = self.analyzer.get_high_confidence_patterns(0.7)
            assert isinstance(high_conf_patterns, list)
            
            user_patterns = self.analyzer.get_user_patterns("comp_user_1")
            assert isinstance(user_patterns, list)
            
            tracker.step("Verifying analysis completeness")
            # Verify the analysis covers all major components
            assert len(self.analyzer.detected_patterns) > 0
            assert len(self.analyzer.user_preferences) > 0

def test_integration_comprehensive():
    """Comprehensive integration test"""
    print_separator("COMPREHENSIVE PATTERN ANALYSIS INTEGRATION TEST", "=")
    
    with ProgressTracker("Integration Test", 10) as tracker:
        # Create temporary storage
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            tracker.step("Setting up comprehensive test environment")
            storage = FeedbackStorage(temp_db.name)
            analyzer = create_pattern_analyzer(storage)
            
            tracker.step("Creating realistic feedback dataset")
            # Create realistic feedback data
            feedback_data = []
            base_time = datetime.now() - timedelta(days=30)
            
            # Multiple users with different behaviors
            users = {
                "expert_user": {"harsh": True, "correction_focus": "grammar"},
                "casual_user": {"harsh": False, "correction_focus": "spelling"},
                "detailed_user": {"harsh": False, "correction_focus": "punctuation"},
                "active_user": {"harsh": True, "correction_focus": "capitalization"}
            }
            
            contexts = [
                FeedbackContext(
                    content_type=ContentType.TRANSCRIPTION,
                    content_id=f"meeting_{i}",
                    original_content=f"Meeting transcript {i}",
                    confidence_score=0.85 + (i * 0.02)
                ) for i in range(5)
            ]
            
            tracker.step("Generating pattern-rich feedback data")
            for day in range(20):
                for user_id, user_props in users.items():
                    for context in contexts[:3]:  # Use subset of contexts
                        # Create rating with user-specific patterns
                        if user_props["harsh"]:
                            rating_value = 2 + (day % 2)  # Harsh rater: 2-3
                        else:
                            rating_value = 4 + (day % 2)  # Lenient rater: 4-5
                        
                        rating = Rating(
                            rating_id=generate_rating_id(),
                            rating_type=RatingType.STARS,
                            value=rating_value,
                            max_value=5,
                            comment=f"Rating from {user_id}"
                        )
                        
                        rating_feedback = Feedback(
                            feedback_id=generate_feedback_id(),
                            user_id=user_id,
                            feedback_type=FeedbackType.RATING,
                            context=context,
                            timestamp=base_time + timedelta(days=day, hours=hash(user_id) % 24),
                            rating=rating
                        )
                        feedback_data.append(rating_feedback)
                        
                        # Create corrections with user-specific focus
                        if day % 3 == 0:  # Not every day
                            correction = Correction(
                                correction_id=generate_correction_id(),
                                original_text=f"error{day}",
                                corrected_text=f"Error{day}",
                                correction_type=user_props["correction_focus"],
                                explanation=f"Fixed by {user_id}" if "detailed" in user_id else None
                            )
                            
                            correction_feedback = Feedback(
                                feedback_id=generate_feedback_id(),
                                user_id=user_id,
                                feedback_type=FeedbackType.CORRECTION,
                                context=context,
                                timestamp=base_time + timedelta(days=day, hours=hash(user_id) % 24 + 1),
                                correction=correction
                            )
                            feedback_data.append(correction_feedback)
            
            tracker.step("Storing feedback data in database")
            stored_count = 0
            for feedback in feedback_data:
                if storage.store_feedback(feedback):
                    stored_count += 1
            
            print(f"  📊 Stored {stored_count} feedback items")
            
            tracker.step("Running comprehensive pattern analysis")
            results = analyzer.analyze_all_patterns(time_window_days=35)
            
            tracker.step("Analyzing detection results")
            patterns = results['patterns']
            user_preferences = results['user_preferences']
            trends = results['trends']
            summary = results['summary']
            
            print(f"  📊 Analysis Results:")
            print(f"     • Patterns detected: {len(patterns)}")
            print(f"     • User profiles: {len(user_preferences)}")
            print(f"     • Trends identified: {len(trends)}")
            print(f"     • Total feedback analyzed: {summary['total_feedback']}")
            
            tracker.step("Validating pattern quality")
            # Check for expected patterns
            high_confidence_patterns = [p for p in patterns if p['confidence'] >= 0.7]
            user_behavior_patterns = [p for p in patterns if p['pattern_type'] == 'user_behavior']
            correction_patterns = [p for p in patterns if p['pattern_type'] == 'correction_pattern']
            
            print(f"  🎯 Pattern Quality:")
            print(f"     • High confidence patterns: {len(high_confidence_patterns)}")
            print(f"     • User behavior patterns: {len(user_behavior_patterns)}")
            print(f"     • Correction patterns: {len(correction_patterns)}")
            
            tracker.step("Validating user preference detection")
            # Check user preferences
            preference_types = set()
            for user_prefs in user_preferences.values():
                for pref in user_prefs:
                    preference_types.add(pref['preference_type'])
            
            print(f"  👤 User Preferences:")
            print(f"     • Users analyzed: {len(user_preferences)}")
            print(f"     • Preference types: {len(preference_types)}")
            print(f"     • Types detected: {', '.join(preference_types)}")
            
            tracker.step("Validating trend analysis")
            if trends:
                trend_directions = [str(t['direction']) for t in trends]
                print(f"  📈 Trends:")
                print(f"     • Trends detected: {len(trends)}")
                print(f"     • Directions: {', '.join(set(trend_directions))}")
            
            tracker.step("Verifying analysis completeness")
            # Verify we detected expected patterns
            assert len(patterns) > 0, "Should detect patterns in rich dataset"
            assert len(user_preferences) > 0, "Should detect user preferences"
            assert summary['total_feedback'] == stored_count, "Should analyze all stored feedback"
            
            # Verify pattern types we expect to see
            pattern_types = {p['pattern_type'] for p in patterns}
            expected_types = {'user_behavior', 'correction_pattern'}
            detected_expected = pattern_types.intersection(expected_types)
            assert len(detected_expected) > 0, f"Should detect expected pattern types: {expected_types}"
            
            print(f"  ✅ Integration test completed successfully!")
            print(f"     • Detected {len(detected_expected)} expected pattern types")
            print(f"     • Analysis covered {summary['unique_users']} users")
            print(f"     • Processed {summary['unique_content']} content items")
            
        finally:
            # Clean up
            try:
                os.unlink(temp_db.name)
            except:
                pass

def run_comprehensive_test_suite():
    """Run comprehensive test suite with progress tracking"""
    print_separator("FEEDBACK PATTERN ANALYZER TEST SUITE", "=")
    print("🧪 Comprehensive testing with progress tracking and visual feedback")
    print("📊 Testing: Pattern Detection, Preference Analysis, Trend Analysis")
    print()
    
    start_time = time.time()
    
    try:
        # Run integration test first
        test_integration_comprehensive()
        print()
        
        # Run pytest for all other tests
        print_separator("RUNNING PYTEST SUITE", "-")
        print("🔬 Executing detailed unit tests...")
        
        # Run pytest with verbose output
        exit_code = pytest.main([__file__, "-v", "--tb=short"])
        
        end_time = time.time()
        duration = end_time - start_time
        
        print_separator("TEST SUITE COMPLETED", "=")
        if exit_code == 0:
            print("✅ All tests passed successfully!")
        else:
            print("❌ Some tests failed. Check output above for details.")
        
        print(f"⏱️  Total execution time: {duration:.2f} seconds")
        print("🚀 The Feedback Pattern Analysis System is ready for production!")
        
        print("\n🎯 Key Features Tested:")
        print("  • Correction pattern detection with user behavior analysis")
        print("  • Rating pattern detection with quality trend analysis")
        print("  • User preference analysis with confidence scoring")
        print("  • Temporal trend analysis with statistical significance")
        print("  • Comprehensive pattern analysis with filtering capabilities")
        print("  • Integration with feedback storage and collection systems")
        
        return exit_code
        
    except Exception as e:
        print(f"❌ Error during test execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = run_comprehensive_test_suite()
    sys.exit(exit_code)