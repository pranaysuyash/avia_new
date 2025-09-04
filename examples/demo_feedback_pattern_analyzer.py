#!/usr/bin/env python3
"""
Demo script for Feedback Pattern Analysis and Recognition System
Showcases comprehensive pattern detection, user preference analysis, and trend analysis
"""

import sys
import os
import tempfile
import time
import json
from datetime import datetime, timedelta

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feedback_pattern_analyzer import (
    PatternAnalyzer, create_pattern_analyzer, PatternType, TrendDirection
)

from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, ContentType,
    generate_feedback_id, generate_rating_id, generate_correction_id
)

def print_separator(title="", char="=", width=80):
    """Print a formatted separator"""
    if title:
        title_line = f" {title} "
        padding = (width - len(title_line)) // 2
        print(char * padding + title_line + char * padding)
    else:
        print(char * width)

def print_progress(current, total, task_name="Processing", width=50):
    """Print a progress bar"""
    progress = current / total
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percentage = progress * 100
    print(f"\r{task_name}: |{bar}| {percentage:.1f}% ({current}/{total})", end='', flush=True)
    if current == total:
        print()  # New line when complete

def create_realistic_feedback_dataset():
    """Create a realistic feedback dataset with patterns"""
    print("📊 Creating realistic feedback dataset with detectable patterns...")
    
    feedback_data = []
    base_time = datetime.now() - timedelta(days=45)
    
    # Define user personas with distinct behaviors
    user_personas = {
        "alice_expert": {
            "rating_style": "harsh",  # Consistently low ratings
            "correction_focus": "grammar",
            "activity_level": "high",
            "detail_level": "detailed"
        },
        "bob_casual": {
            "rating_style": "lenient",  # Consistently high ratings
            "correction_focus": "spelling",
            "activity_level": "medium",
            "detail_level": "minimal"
        },
        "charlie_balanced": {
            "rating_style": "moderate",
            "correction_focus": "punctuation",
            "activity_level": "high",
            "detail_level": "detailed"
        },
        "diana_newcomer": {
            "rating_style": "improving",  # Ratings improve over time
            "correction_focus": "capitalization",
            "activity_level": "low",
            "detail_level": "moderate"
        },
        "eve_inconsistent": {
            "rating_style": "volatile",  # Inconsistent ratings
            "correction_focus": "mixed",
            "activity_level": "medium",
            "detail_level": "minimal"
        }
    }
    
    # Create diverse content contexts
    content_contexts = [
        FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="weekly_standup_001",
            original_content="Weekly team standup meeting transcript",
            confidence_score=0.92,
            processing_method="whisper_v3"
        ),
        FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="client_call_002",
            original_content="Client presentation and Q&A session",
            confidence_score=0.87,
            processing_method="whisper_v3"
        ),
        FeedbackContext(
            content_type=ContentType.MEETING_ELEMENT,
            content_id="agenda_planning_003",
            original_content="Quarterly planning agenda items",
            confidence_score=0.89,
            processing_method="nlp_extraction"
        ),
        FeedbackContext(
            content_type=ContentType.ACTION_ITEM,
            content_id="followup_tasks_004",
            original_content="Action items from leadership meeting",
            confidence_score=0.94,
            processing_method="action_extraction"
        ),
        FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="training_session_005",
            original_content="Employee training session recording",
            confidence_score=0.85,
            processing_method="whisper_v3"
        )
    ]
    
    print(f"  👥 Creating feedback for {len(user_personas)} user personas")
    print(f"  📄 Using {len(content_contexts)} different content contexts")
    
    total_feedback = 0
    
    # Generate feedback over time with patterns
    for day in range(40):  # 40 days of feedback
        day_time = base_time + timedelta(days=day)
        
        for user_id, persona in user_personas.items():
            # Skip some days based on activity level
            if persona["activity_level"] == "low" and day % 3 != 0:
                continue
            elif persona["activity_level"] == "medium" and day % 2 != 0:
                continue
            
            # Each user interacts with 1-3 content items per active day
            content_count = 3 if persona["activity_level"] == "high" else (2 if persona["activity_level"] == "medium" else 1)
            
            for content_idx in range(content_count):
                context = content_contexts[content_idx % len(content_contexts)]
                
                # Create rating feedback based on persona
                rating_value = _get_rating_for_persona(persona, day)
                
                rating = Rating(
                    rating_id=generate_rating_id(),
                    rating_type=RatingType.STARS,
                    value=rating_value,
                    max_value=5,
                    comment=f"Feedback from {user_id}" if persona["detail_level"] != "minimal" else None
                )
                
                rating_feedback = Feedback(
                    feedback_id=generate_feedback_id(),
                    user_id=user_id,
                    feedback_type=FeedbackType.RATING,
                    context=context,
                    timestamp=day_time + timedelta(hours=content_idx*2, minutes=hash(user_id) % 60),
                    rating=rating,
                    tags=["demo", "realistic", persona["rating_style"]]
                )
                feedback_data.append(rating_feedback)
                total_feedback += 1
                
                # Create correction feedback (not every interaction)
                if day % 2 == 0 and content_idx == 0:  # Every other day, first content only
                    correction_type = _get_correction_type_for_persona(persona)
                    
                    correction = Correction(
                        correction_id=generate_correction_id(),
                        original_text=f"example text {day}",
                        corrected_text=f"Example Text {day}",
                        correction_type=correction_type,
                        explanation=f"Corrected by {user_id}: {correction_type} fix" if persona["detail_level"] == "detailed" else None
                    )
                    
                    correction_feedback = Feedback(
                        feedback_id=generate_feedback_id(),
                        user_id=user_id,
                        feedback_type=FeedbackType.CORRECTION,
                        context=context,
                        timestamp=day_time + timedelta(hours=content_idx*2+1, minutes=hash(user_id) % 60),
                        correction=correction,
                        tags=["demo", "realistic", correction_type]
                    )
                    feedback_data.append(correction_feedback)
                    total_feedback += 1
                
                # Occasionally add suggestions
                if day % 5 == 0 and user_id in ["alice_expert", "charlie_balanced"]:
                    suggestion_feedback = Feedback(
                        feedback_id=generate_feedback_id(),
                        user_id=user_id,
                        feedback_type=FeedbackType.SUGGESTION,
                        context=context,
                        timestamp=day_time + timedelta(hours=content_idx*2+0.5, minutes=hash(user_id) % 60),
                        suggestion_text=f"Suggestion from {user_id}: Consider improving {context.content_type.value} processing",
                        tags=["demo", "realistic", "suggestion"]
                    )
                    feedback_data.append(suggestion_feedback)
                    total_feedback += 1
    
    print(f"  ✅ Generated {total_feedback} feedback items with realistic patterns")
    return feedback_data

def _get_rating_for_persona(persona, day):
    """Get rating value based on user persona and day"""
    if persona["rating_style"] == "harsh":
        return 2 + (day % 2)  # Consistently low: 2-3
    elif persona["rating_style"] == "lenient":
        return 4 + (day % 2)  # Consistently high: 4-5
    elif persona["rating_style"] == "moderate":
        return 3 + (day % 3)  # Moderate: 3-5
    elif persona["rating_style"] == "improving":
        return min(5, 2 + (day // 10))  # Improves over time: 2->5
    else:  # volatile
        return 1 + (day % 5)  # Highly variable: 1-5

def _get_correction_type_for_persona(persona):
    """Get correction type based on user persona"""
    focus = persona["correction_focus"]
    if focus == "mixed":
        types = ["grammar", "spelling", "punctuation", "capitalization"]
        return types[hash(str(persona)) % len(types)]
    return focus

def demo_pattern_detection(analyzer, feedback_count):
    """Demo pattern detection capabilities"""
    print_separator("PATTERN DETECTION DEMO", "-")
    
    print("🔍 Running comprehensive pattern analysis...")
    results = analyzer.analyze_all_patterns(time_window_days=50)
    
    patterns = results['patterns']
    print(f"  📊 Detected {len(patterns)} patterns from {feedback_count} feedback items")
    
    # Group patterns by type
    pattern_types = {}
    for pattern in patterns:
        ptype = pattern['pattern_type']
        if ptype not in pattern_types:
            pattern_types[ptype] = []
        pattern_types[ptype].append(pattern)
    
    print(f"\n  📋 Pattern Types Detected:")
    for ptype, type_patterns in pattern_types.items():
        print(f"    • {ptype.replace('_', ' ').title()}: {len(type_patterns)} patterns")
    
    # Show high-confidence patterns
    high_conf_patterns = [p for p in patterns if p['confidence'] >= 0.8]
    print(f"\n  🎯 High-Confidence Patterns ({len(high_conf_patterns)}):")
    
    for i, pattern in enumerate(high_conf_patterns[:5]):  # Show top 5
        print(f"    {i+1}. {pattern['description']}")
        print(f"       Confidence: {pattern['confidence']:.2f}, Frequency: {pattern['frequency']}")
        print(f"       Affects {len(pattern['affected_users'])} users, {len(pattern['affected_content'])} content items")
    
    # Show user behavior patterns specifically
    user_patterns = [p for p in patterns if p['pattern_type'] == 'user_behavior']
    if user_patterns:
        print(f"\n  👤 User Behavior Patterns ({len(user_patterns)}):")
        for pattern in user_patterns[:3]:
            print(f"    • {pattern['description']} (confidence: {pattern['confidence']:.2f})")
    
    return results

def demo_user_preferences(results):
    """Demo user preference analysis"""
    print_separator("USER PREFERENCE ANALYSIS DEMO", "-")
    
    user_preferences = results['user_preferences']
    print(f"🧑‍💼 Analyzed preferences for {len(user_preferences)} users")
    
    # Analyze preference types across all users
    all_preference_types = set()
    preference_type_counts = {}
    
    for user_id, preferences in user_preferences.items():
        print(f"\n  👤 {user_id} ({len(preferences)} preferences):")
        
        for pref in preferences:
            pref_type = pref['preference_type']
            all_preference_types.add(pref_type)
            preference_type_counts[pref_type] = preference_type_counts.get(pref_type, 0) + 1
            
            print(f"    • {pref_type.replace('_', ' ').title()}: {pref['preference_value']}")
            print(f"      Confidence: {pref['confidence']:.2f}, Evidence: {pref['evidence_count']} items")
    
    print(f"\n  📊 Preference Type Distribution:")
    for pref_type, count in sorted(preference_type_counts.items()):
        print(f"    • {pref_type.replace('_', ' ').title()}: {count} users")

def demo_trend_analysis(results):
    """Demo trend analysis capabilities"""
    print_separator("TREND ANALYSIS DEMO", "-")
    
    trends = results['trends']
    print(f"📈 Detected {len(trends)} trends in feedback data")
    
    if not trends:
        print("  ℹ️  No significant trends detected in current dataset")
        print("     (This is normal for smaller datasets or stable patterns)")
        return
    
    # Group trends by metric
    trend_metrics = {}
    for trend in trends:
        metric = trend['metric_name']
        if metric not in trend_metrics:
            trend_metrics[metric] = []
        trend_metrics[metric].append(trend)
    
    print(f"\n  📊 Trend Metrics:")
    for metric, metric_trends in trend_metrics.items():
        print(f"    • {metric.replace('_', ' ').title()}: {len(metric_trends)} trends")
    
    # Show significant trends
    significant_trends = [t for t in trends if t['confidence'] >= 0.6]
    if significant_trends:
        print(f"\n  🎯 Significant Trends ({len(significant_trends)}):")
        
        for i, trend in enumerate(significant_trends):
            direction_icon = {
                'increasing': '📈',
                'decreasing': '📉',
                'stable': '➡️',
                'volatile': '📊'
            }.get(trend['direction'], '📊')
            
            print(f"    {i+1}. {direction_icon} {trend['metric_name'].replace('_', ' ').title()}")
            print(f"       Direction: {trend['direction'].title()}")
            print(f"       Confidence: {trend['confidence']:.2f}")
            print(f"       Magnitude: {trend['magnitude']:.3f}")
            print(f"       Data Points: {len(trend['data_points'])}")

def demo_analysis_summary(results):
    """Demo analysis summary and insights"""
    print_separator("ANALYSIS SUMMARY & INSIGHTS", "-")
    
    summary = results['summary']
    
    print("📋 Analysis Summary:")
    print(f"  • Total Feedback Analyzed: {summary['total_feedback']}")
    print(f"  • Unique Users: {summary['unique_users']}")
    print(f"  • Unique Content Items: {summary['unique_content']}")
    print(f"  • Analysis Time Window: {summary['time_window_days']} days")
    
    print(f"\n  📊 Feedback Distribution:")
    for feedback_type, count in summary['feedback_type_distribution'].items():
        percentage = (count / summary['total_feedback']) * 100
        print(f"    • {feedback_type.title()}: {count} ({percentage:.1f}%)")
    
    print(f"\n  🔍 Pattern Detection Results:")
    print(f"    • Total Patterns: {summary['patterns_detected']}")
    print(f"    • High-Confidence Patterns: {summary['high_confidence_patterns']}")
    print(f"    • User Preferences Analyzed: {summary['user_preferences_analyzed']}")
    print(f"    • Total Preferences: {summary['total_preferences']}")
    
    if summary.get('trend_direction_distribution'):
        print(f"\n  📈 Trend Analysis:")
        for direction, count in summary['trend_direction_distribution'].items():
            direction_icon = {
                'increasing': '📈',
                'decreasing': '📉',
                'stable': '➡️',
                'volatile': '📊'
            }.get(direction, '📊')
            print(f"    • {direction_icon} {direction.title()}: {count} trends")
    
    # Generate insights
    print(f"\n  💡 Key Insights:")
    
    # User engagement insight
    avg_feedback_per_user = summary['total_feedback'] / summary['unique_users']
    if avg_feedback_per_user > 10:
        print(f"    • High user engagement: {avg_feedback_per_user:.1f} feedback items per user")
    elif avg_feedback_per_user > 5:
        print(f"    • Moderate user engagement: {avg_feedback_per_user:.1f} feedback items per user")
    else:
        print(f"    • Low user engagement: {avg_feedback_per_user:.1f} feedback items per user")
    
    # Pattern detection insight
    pattern_rate = summary['patterns_detected'] / summary['total_feedback'] * 100
    if pattern_rate > 10:
        print(f"    • Rich pattern environment: {pattern_rate:.1f}% pattern detection rate")
    elif pattern_rate > 5:
        print(f"    • Moderate patterns detected: {pattern_rate:.1f}% pattern detection rate")
    else:
        print(f"    • Few patterns detected: {pattern_rate:.1f}% pattern detection rate")
    
    # Quality insight
    high_conf_rate = summary['high_confidence_patterns'] / max(1, summary['patterns_detected']) * 100
    if high_conf_rate > 50:
        print(f"    • High-quality patterns: {high_conf_rate:.1f}% high-confidence detection rate")
    else:
        print(f"    • Mixed pattern quality: {high_conf_rate:.1f}% high-confidence detection rate")

def demo_export_results(results):
    """Demo exporting analysis results"""
    print_separator("RESULTS EXPORT DEMO", "-")
    
    print("💾 Exporting analysis results...")
    
    # Create export filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_filename = f"pattern_analysis_results_{timestamp}.json"
    
    # Convert results to JSON-serializable format
    def convert_to_serializable(obj):
        """Recursively convert objects to JSON-serializable format"""
        if hasattr(obj, 'value'):  # Handle enums
            return obj.value
        elif hasattr(obj, 'isoformat'):  # Handle datetime
            return obj.isoformat()
        elif isinstance(obj, set):  # Handle sets
            return list(obj)
        elif isinstance(obj, dict):
            # Convert dictionary keys and values
            return {
                (k.value if hasattr(k, 'value') else str(k)): convert_to_serializable(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, (list, tuple)):
            return [convert_to_serializable(item) for item in obj]
        else:
            return obj
    
    # Convert results to serializable format
    serializable_results = convert_to_serializable(results)
    
    with open(export_filename, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"  ✅ Results exported to: {export_filename}")
    
    # Create summary report
    summary_filename = f"pattern_analysis_summary_{timestamp}.txt"
    with open(summary_filename, 'w') as f:
        f.write("FEEDBACK PATTERN ANALYSIS SUMMARY REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        summary = results['summary']
        f.write(f"Analysis Date: {summary['analysis_date']}\n")
        f.write(f"Time Window: {summary['time_window_days']} days\n")
        f.write(f"Total Feedback: {summary['total_feedback']}\n")
        f.write(f"Unique Users: {summary['unique_users']}\n")
        f.write(f"Patterns Detected: {summary['patterns_detected']}\n")
        f.write(f"High-Confidence Patterns: {summary['high_confidence_patterns']}\n")
        f.write(f"User Preferences: {summary['total_preferences']}\n")
        
        f.write("\nTOP PATTERNS:\n")
        f.write("-" * 20 + "\n")
        
        high_conf_patterns = [p for p in results['patterns'] if p['confidence'] >= 0.8]
        for i, pattern in enumerate(high_conf_patterns[:10]):
            f.write(f"{i+1}. {pattern['description']}\n")
            f.write(f"   Confidence: {pattern['confidence']:.2f}\n")
            f.write(f"   Frequency: {pattern['frequency']}\n\n")
    
    print(f"  ✅ Summary report saved to: {summary_filename}")
    
    return export_filename, summary_filename

def main():
    """Run comprehensive pattern analysis demo"""
    print_separator("FEEDBACK PATTERN ANALYSIS SYSTEM DEMO", "=")
    print("🧠 Advanced pattern detection, user preference analysis, and trend analysis")
    print("📊 Showcasing comprehensive feedback intelligence capabilities")
    print()
    
    start_time = time.time()
    
    # Create temporary storage
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        print("🔧 Setting up analysis environment...")
        storage = FeedbackStorage(temp_db.name)
        analyzer = create_pattern_analyzer(storage)
        
        # Create realistic dataset
        feedback_data = create_realistic_feedback_dataset()
        
        print(f"\n💾 Storing {len(feedback_data)} feedback items...")
        stored_count = 0
        for i, feedback in enumerate(feedback_data):
            if storage.store_feedback(feedback):
                stored_count += 1
            
            if (i + 1) % 50 == 0:  # Progress update every 50 items
                print_progress(i + 1, len(feedback_data), "Storing feedback")
        
        print_progress(len(feedback_data), len(feedback_data), "Storing feedback")
        print(f"  ✅ Successfully stored {stored_count} feedback items")
        
        # Run comprehensive analysis
        print(f"\n🧠 Running comprehensive pattern analysis...")
        results = demo_pattern_detection(analyzer, stored_count)
        
        # Demo user preferences
        demo_user_preferences(results)
        
        # Demo trend analysis
        demo_trend_analysis(results)
        
        # Demo analysis summary
        demo_analysis_summary(results)
        
        # Export results
        export_files = demo_export_results(results)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print_separator("DEMO COMPLETED SUCCESSFULLY", "=")
        print("✅ Pattern analysis demo completed successfully!")
        print(f"⏱️  Total execution time: {duration:.2f} seconds")
        print("🚀 The Feedback Pattern Analysis System is ready for production use!")
        
        print("\n🎯 Demo Highlights:")
        print(f"  • Analyzed {stored_count} feedback items from 5 user personas")
        print(f"  • Detected {len(results['patterns'])} patterns with confidence scoring")
        print(f"  • Analyzed preferences for {len(results['user_preferences'])} users")
        print(f"  • Identified {len(results['trends'])} trends in feedback data")
        print(f"  • Generated comprehensive analysis reports")
        
        print("\n📁 Generated Files:")
        print(f"  • Analysis results: {export_files[0]}")
        print(f"  • Summary report: {export_files[1]}")
        
        print("\n🔍 Key Capabilities Demonstrated:")
        print("  • Correction pattern detection with user behavior analysis")
        print("  • Rating pattern detection with harsh/lenient user identification")
        print("  • User preference analysis with confidence scoring")
        print("  • Temporal trend analysis with statistical significance")
        print("  • Comprehensive reporting and export functionality")
        print("  • Real-time progress tracking and visual feedback")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            os.unlink(temp_db.name)
            print("\n🧹 Demo database cleaned up")
        except:
            pass

if __name__ == "__main__":
    main()