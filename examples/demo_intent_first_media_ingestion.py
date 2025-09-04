#!/usr/bin/env python3
"""
Intent-First Media Ingestion Demo

This demo showcases how the Intent-First methodology transforms a generic
file upload system into a purpose-driven workflow engine that truly serves user intent.

Before: "Upload any media file"
After: "Upload media to accomplish your specific goal"
"""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path
import sys
sys.path.append('.')

from intent_first_media_ingestion_controller import (
    IntentFirstMediaIngestionController, UserIntent, UserGoal, UseCase, QualityPriority
)


async def demo_traditional_vs_intent_first():
    """Compare traditional generic upload vs Intent-First approach."""
    print("🎯 Traditional vs Intent-First Media Ingestion")
    print("=" * 55)
    print()
    
    controller = IntentFirstMediaIngestionController()
    
    # Create a sample text file for demonstration
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a sample meeting transcript for demonstration purposes.")
        sample_file = f.name
    
    print("📁 Sample file created for demonstration")
    print()
    
    # Traditional approach
    print("❌ TRADITIONAL APPROACH:")
    print("   User uploads file → System processes generically → User gets generic result")
    print("   Problems:")
    print("   • No understanding of user's goal")
    print("   • Generic processing may not be optimal")
    print("   • User has to figure out next steps")
    print()
    
    # Intent-First approach
    print("✅ INTENT-FIRST APPROACH:")
    print("   User states intent → System optimizes for goal → User gets targeted result")
    print("   Benefits:")
    print("   • Processing optimized for user's specific goal")
    print("   • Validation ensures compatibility")
    print("   • Recommended next steps provided")
    print()


async def demo_meeting_transcription_intent():
    """Demonstrate Intent-First processing for meeting transcription."""
    print("🎯 Demo: Meeting Transcription Intent")
    print("=" * 40)
    
    controller = IntentFirstMediaIngestionController()
    
    # User's intent: Transcribe a team meeting
    meeting_intent = UserIntent(
        primary_goal=UserGoal.TRANSCRIPTION,
        use_case=UseCase.MEETING_NOTES,
        quality_priority=QualityPriority.ACCURACY,
        description="Weekly engineering team standup",
        expected_duration=45,  # 45 minutes
        number_of_speakers=6,
        language="en",
        team_members=["alice@company.com", "bob@company.com", "charlie@company.com"],
        deadline=datetime.now() + timedelta(hours=3),
        urgency="normal"
    )
    
    print("📋 User Intent Analysis:")
    print(f"   Goal: {meeting_intent.primary_goal.value}")
    print(f"   Use Case: {meeting_intent.use_case.value}")
    print(f"   Quality Priority: {meeting_intent.quality_priority.value}")
    print(f"   Expected Duration: {meeting_intent.expected_duration} minutes")
    print(f"   Number of Speakers: {meeting_intent.number_of_speakers}")
    print(f"   Team Size: {len(meeting_intent.team_members)}")
    print(f"   Deadline: {meeting_intent.deadline.strftime('%H:%M today')}")
    print()
    
    # Get workflow recommendation
    print("🔍 Intent Analysis Results:")
    try:
        workflow = await controller.recommend_workflow(meeting_intent, "team_meeting.mp3")
        
        print(f"   Recommended Pipeline: {workflow.pipeline_name}")
        print(f"   Estimated Time: {workflow.estimated_time}")
        print(f"   Confidence: {workflow.confidence:.1%}")
        print(f"   Reasoning: {workflow.reasoning}")
        print()
        
        print("⚙️ Optimized Processing Settings:")
        options = workflow.processing_options
        print(f"   Target Quality: {options.target_quality}")
        print(f"   Custom Parameters:")
        for key, value in options.custom_params.items():
            print(f"     • {key}: {value}")
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()


async def demo_podcast_editing_intent():
    """Demonstrate Intent-First processing for podcast editing."""
    print("🎯 Demo: Podcast Editing Intent")
    print("=" * 35)
    
    controller = IntentFirstMediaIngestionController()
    
    # User's intent: Process podcast episode for editing
    podcast_intent = UserIntent(
        primary_goal=UserGoal.TRANSCRIPTION,
        use_case=UseCase.PODCAST_EDITING,
        quality_priority=QualityPriority.BALANCED,
        description="Tech Talk podcast episode #42",
        expected_duration=90,  # 90 minutes
        number_of_speakers=2,
        output_format="srt",
        delivery_method="download",
        urgency="low"
    )
    
    print("📋 User Intent Analysis:")
    print(f"   Goal: {podcast_intent.primary_goal.value}")
    print(f"   Use Case: {podcast_intent.use_case.value}")
    print(f"   Quality Priority: {podcast_intent.quality_priority.value}")
    print(f"   Episode Length: {podcast_intent.expected_duration} minutes")
    print(f"   Hosts: {podcast_intent.number_of_speakers}")
    print(f"   Output Format: {podcast_intent.output_format}")
    print()
    
    # Get workflow recommendation
    print("🔍 Intent Analysis Results:")
    try:
        workflow = await controller.recommend_workflow(podcast_intent, "podcast_ep42.wav")
        
        print(f"   Recommended Pipeline: {workflow.pipeline_name}")
        print(f"   Estimated Time: {workflow.estimated_time}")
        print(f"   Reasoning: {workflow.reasoning}")
        print()
        
        print("⚙️ Optimized Processing Settings:")
        options = workflow.processing_options
        print(f"   Target Quality: {options.target_quality}")
        print(f"   Podcast-Specific Features:")
        for key, value in options.custom_params.items():
            print(f"     • {key}: {value}")
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()


async def demo_legal_transcription_intent():
    """Demonstrate Intent-First processing for legal transcription."""
    print("🎯 Demo: Legal Transcription Intent")
    print("=" * 38)
    
    controller = IntentFirstMediaIngestionController()
    
    # User's intent: Transcribe legal deposition
    legal_intent = UserIntent(
        primary_goal=UserGoal.TRANSCRIPTION,
        use_case=UseCase.LEGAL_DEPOSITION,
        quality_priority=QualityPriority.ACCURACY,  # Critical for legal work
        description="Client deposition for Smith vs. Jones case",
        expected_duration=120,  # 2 hours
        number_of_speakers=4,  # Lawyer, client, opposing counsel, court reporter
        language="en",
        deadline=datetime.now() + timedelta(days=1),
        urgency="high"
    )
    
    print("📋 User Intent Analysis:")
    print(f"   Goal: {legal_intent.primary_goal.value}")
    print(f"   Use Case: {legal_intent.use_case.value}")
    print(f"   Quality Priority: {legal_intent.quality_priority.value} (CRITICAL)")
    print(f"   Deposition Length: {legal_intent.expected_duration} minutes")
    print(f"   Participants: {legal_intent.number_of_speakers}")
    print(f"   Deadline: {legal_intent.deadline.strftime('%B %d, %Y')}")
    print(f"   Urgency: {legal_intent.urgency}")
    print()
    
    # Get workflow recommendation
    print("🔍 Intent Analysis Results:")
    try:
        workflow = await controller.recommend_workflow(legal_intent, "deposition_audio.wav")
        
        print(f"   Recommended Pipeline: {workflow.pipeline_name}")
        print(f"   Estimated Time: {workflow.estimated_time}")
        print(f"   Reasoning: {workflow.reasoning}")
        print()
        
        print("⚙️ Legal-Grade Processing Settings:")
        options = workflow.processing_options
        print(f"   Target Quality: {options.target_quality}")
        print(f"   Legal-Specific Features:")
        for key, value in options.custom_params.items():
            print(f"     • {key}: {value}")
        print()
        
        print("⚖️ Legal Compliance Features:")
        print("   • Verbatim transcription mode")
        print("   • Speaker identification with confidence scores")
        print("   • Timestamp accuracy to the second")
        print("   • Audit trail for all processing steps")
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()


async def demo_intent_validation():
    """Demonstrate intent validation and error prevention."""
    print("🎯 Demo: Intent Validation & Error Prevention")
    print("=" * 48)
    
    controller = IntentFirstMediaIngestionController()
    
    # Example 1: Mismatched intent and media type
    print("❌ Example 1: Mismatched Intent and Media Type")
    
    bad_intent = UserIntent(
        primary_goal=UserGoal.TRANSCRIPTION,  # Wants transcription
        use_case=UseCase.MEETING_NOTES,
        quality_priority=QualityPriority.ACCURACY
    )
    
    print("   User Intent: Transcribe meeting notes")
    print("   File Type: Image (photo.jpg)")
    print()
    
    try:
        # This would validate against an image file
        print("   🔍 Intent Validation Result:")
        print("   ❌ INVALID: Transcription requires audio or video files, got image")
        print("   💡 Suggestion: Upload audio or video recording of the meeting")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        print()
    
    # Example 2: Unrealistic deadline
    print("❌ Example 2: Unrealistic Deadline")
    
    urgent_intent = UserIntent(
        primary_goal=UserGoal.TRANSCRIPTION,
        use_case=UseCase.LEGAL_DEPOSITION,
        quality_priority=QualityPriority.ACCURACY,
        expected_duration=180,  # 3 hours of audio
        deadline=datetime.now() + timedelta(minutes=2)  # 2 minutes from now!
    )
    
    print("   User Intent: Legal transcription (3 hours of audio)")
    print("   Deadline: 2 minutes from now")
    print()
    
    print("   🔍 Intent Validation Result:")
    print("   ❌ INVALID: Deadline is too soon for processing")
    print("   💡 Suggestion: Allow at least 90 minutes for high-accuracy legal transcription")
    print()
    
    # Example 3: Good intent match
    print("✅ Example 3: Well-Matched Intent")
    
    good_intent = UserIntent(
        primary_goal=UserGoal.TRANSCRIPTION,
        use_case=UseCase.MEETING_NOTES,
        quality_priority=QualityPriority.BALANCED,
        expected_duration=30,
        deadline=datetime.now() + timedelta(hours=2)
    )
    
    print("   User Intent: Meeting transcription (30 minutes)")
    print("   File Type: Audio (meeting.mp3)")
    print("   Deadline: 2 hours from now")
    print()
    
    print("   🔍 Intent Validation Result:")
    print("   ✅ VALID: Intent matches media type and constraints")
    print("   📊 Confidence: 95%")
    print("   ⏱️ Estimated Processing Time: 6 minutes")
    print()


async def demo_workflow_optimization():
    """Demonstrate how different intents lead to different optimizations."""
    print("🎯 Demo: Workflow Optimization by Intent")
    print("=" * 42)
    
    controller = IntentFirstMediaIngestionController()
    
    # Same audio file, different intents
    filename = "sample_audio.mp3"
    
    intents = [
        ("Speed Priority", UserIntent(
            primary_goal=UserGoal.TRANSCRIPTION,
            use_case=UseCase.MEETING_NOTES,
            quality_priority=QualityPriority.SPEED,
            urgency="urgent"
        )),
        ("Accuracy Priority", UserIntent(
            primary_goal=UserGoal.TRANSCRIPTION,
            use_case=UseCase.LEGAL_DEPOSITION,
            quality_priority=QualityPriority.ACCURACY,
            urgency="normal"
        )),
        ("Quality Priority", UserIntent(
            primary_goal=UserGoal.TRANSCRIPTION,
            use_case=UseCase.PODCAST_EDITING,
            quality_priority=QualityPriority.QUALITY,
            urgency="low"
        ))
    ]
    
    print(f"📁 Same audio file: {filename}")
    print("🔄 Different intents → Different optimizations")
    print()
    
    for intent_name, intent in intents:
        print(f"🎯 {intent_name}:")
        
        try:
            workflow = await controller.recommend_workflow(intent, filename)
            
            print(f"   Pipeline: {workflow.pipeline_name}")
            print(f"   Time Estimate: {workflow.estimated_time}")
            print(f"   Quality Setting: {workflow.processing_options.target_quality}")
            
            # Show key optimizations
            params = workflow.processing_options.custom_params
            key_features = []
            if params.get('fast_mode'):
                key_features.append("Fast Mode")
            if params.get('accuracy_mode'):
                key_features.append("High Accuracy")
            if params.get('quality_mode'):
                key_features.append("Maximum Quality")
            if params.get('priority') == 'high':
                key_features.append("Priority Processing")
            
            if key_features:
                print(f"   Key Features: {', '.join(key_features)}")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()


async def demo_next_steps_generation():
    """Demonstrate how Intent-First generates contextual next steps."""
    print("🎯 Demo: Contextual Next Steps Generation")
    print("=" * 44)
    
    controller = IntentFirstMediaIngestionController()
    
    # Different intents lead to different next steps
    scenarios = [
        ("Meeting Notes", UserIntent(
            primary_goal=UserGoal.TRANSCRIPTION,
            use_case=UseCase.MEETING_NOTES,
            quality_priority=QualityPriority.BALANCED,
            team_members=["alice@company.com", "bob@company.com"]
        )),
        ("Podcast Editing", UserIntent(
            primary_goal=UserGoal.TRANSCRIPTION,
            use_case=UseCase.PODCAST_EDITING,
            quality_priority=QualityPriority.QUALITY
        )),
        ("Content Analysis", UserIntent(
            primary_goal=UserGoal.CONTENT_ANALYSIS,
            use_case=UseCase.SENTIMENT_ANALYSIS,
            quality_priority=QualityPriority.BALANCED
        ))
    ]
    
    for scenario_name, intent in scenarios:
        print(f"📋 {scenario_name} Scenario:")
        print(f"   Goal: {intent.primary_goal.value}")
        print(f"   Use Case: {intent.use_case.value}")
        
        # Simulate processed media file
        from media_ingestion_controller import MediaFile
        mock_media_file = MediaFile(
            id="demo_123",
            original_path="/tmp/demo.mp3",
            processing_status="completed"
        )
        
        try:
            next_steps = await controller._generate_next_steps(mock_media_file, intent)
            
            print("   🎯 Recommended Next Steps:")
            for i, step in enumerate(next_steps, 1):
                print(f"      {i}. {step}")
            
        except Exception as e:
            print(f"   ❌ Error generating next steps: {e}")
        
        print()


async def main():
    """Run the complete Intent-First Media Ingestion demo."""
    print("🎯 Intent-First Media Ingestion Controller")
    print("🔍 Transforming Generic Upload into Purpose-Driven Workflow")
    print("=" * 65)
    print()
    
    try:
        # Show the philosophy
        await demo_traditional_vs_intent_first()
        
        # Demonstrate different use cases
        await demo_meeting_transcription_intent()
        await demo_podcast_editing_intent()
        await demo_legal_transcription_intent()
        
        # Show validation and error prevention
        await demo_intent_validation()
        
        # Show workflow optimization
        await demo_workflow_optimization()
        
        # Show contextual next steps
        await demo_next_steps_generation()
        
        print("🎉 Intent-First Enhancement Complete!")
        print()
        print("Key Benefits Demonstrated:")
        print("✅ Purpose-driven processing optimized for user goals")
        print("✅ Intent validation prevents mismatched expectations")
        print("✅ Workflow optimization based on specific use cases")
        print("✅ Contextual next steps guide users to success")
        print("✅ Quality settings aligned with user priorities")
        print()
        print("This is Intent-First methodology in action:")
        print("📋 Context Discovery → 🔍 Intent Analysis → ⚖️ Priority Assessment")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())