#!/usr/bin/env python3
"""
Demo script for AI-Powered Discussion Facilitator
Showcases intelligent discussion guidance and participation balancing
"""

import asyncio
import json
from datetime import datetime
from collaborative_discussion_facilitator import (
    CollaborativeDiscussionFacilitator,
    DiscussionContext,
    FacilitationMode,
    DiscussionAnalyzer,
    TopicSuggestionEngine
)

class MockCollaborativeEngine:
    """Mock collaborative engine for demonstration"""
    
    def __init__(self):
        self.session_data = {
            'segments': [
                {'user_id': 'alice', 'text': 'I think we should focus on user experience first', 'duration': 4.0, 'timestamp': 0.0},
                {'user_id': 'bob', 'text': 'What about the technical constraints we discussed?', 'duration': 3.5, 'timestamp': 4.0},
                {'user_id': 'alice', 'text': 'Good point, but I still believe users come first', 'duration': 3.0, 'timestamp': 7.5},
                {'user_id': 'charlie', 'text': 'Maybe we can find a balance between both?', 'duration': 2.5, 'timestamp': 10.5},
                {'user_id': 'bob', 'text': 'How would that work in practice though?', 'duration': 2.0, 'timestamp': 13.0},
                {'user_id': 'alice', 'text': 'We could prioritize features that are both user-friendly and technically feasible', 'duration': 5.0, 'timestamp': 15.0},
                {'user_id': 'david', 'text': 'I agree with Alice on this approach', 'duration': 2.0, 'timestamp': 20.0},
                {'user_id': 'bob', 'text': 'But what about the timeline? Can we deliver this quickly?', 'duration': 3.0, 'timestamp': 22.0},
                {'user_id': 'charlie', 'text': 'That\'s a valid concern. What\'s our deadline?', 'duration': 2.5, 'timestamp': 25.0},
                {'user_id': 'alice', 'text': 'We have 3 months, which should be enough if we plan carefully', 'duration': 4.0, 'timestamp': 27.5}
            ]
        }
        self.messages_sent = []
    
    def get_session_state(self, session_id):
        return self.session_data
    
    async def broadcast_message(self, session_id, message):
        self.messages_sent.append(message)
        print(f"🤖 AI Facilitator: {message['message']}")
        return True

async def demo_discussion_analysis():
    """Demonstrate discussion analysis capabilities"""
    print("📊 Discussion Analysis Demo")
    print("-" * 40)
    
    analyzer = DiscussionAnalyzer()
    mock_engine = MockCollaborativeEngine()
    
    # Analyze the mock discussion
    session_data = mock_engine.get_session_state("demo")
    participation_metrics = analyzer.analyze_participation(session_data)
    
    print(f"Participants analyzed: {len(participation_metrics)}")
    print()
    
    for metrics in participation_metrics:
        print(f"👤 {metrics.user_id}:")
        print(f"   Speaking time: {metrics.speaking_time:.1f}s")
        print(f"   Contributions: {metrics.contribution_count}")
        print(f"   Questions asked: {metrics.question_count}")
        print(f"   Engagement score: {metrics.engagement_score:.2f}")
        print(f"   Confidence level: {metrics.confidence_level:.2f}")
        print(f"   Topic relevance: {metrics.topic_relevance:.2f}")
        print()

async def demo_topic_suggestions():
    """Demonstrate topic suggestion engine"""
    print("💡 Topic Suggestion Demo")
    print("-" * 40)
    
    topic_engine = TopicSuggestionEngine()
    
    # Create different contexts
    contexts = [
        DiscussionContext(
            session_id="brainstorm_demo",
            participants=["alice", "bob", "charlie"],
            topic="New Product Features",
            mode=FacilitationMode.BRAINSTORMING,
            duration_minutes=45,
            objectives=["Generate innovative ideas", "Explore user needs"],
            current_phase="ideation",
            metadata={}
        ),
        DiscussionContext(
            session_id="decision_demo",
            participants=["alice", "bob", "charlie", "david"],
            topic="Budget Allocation",
            mode=FacilitationMode.DECISION_MAKING,
            duration_minutes=30,
            objectives=["Decide on Q4 budget", "Align on priorities"],
            current_phase="evaluation",
            metadata={}
        )
    ]
    
    for context in contexts:
        print(f"📋 Context: {context.topic} ({context.mode.value})")
        
        session_data = {'segments': []}
        discussion_state = {'energy_level': 0.6}
        
        suggestions = topic_engine.generate_topic_suggestions(context, session_data, discussion_state)
        
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"   {i}. {suggestion.topic} (relevance: {suggestion.relevance_score:.2f})")
            print(f"      → {suggestion.reasoning}")
            print(f"      → Sample question: {suggestion.suggested_questions[0]}")
            print()

async def demo_full_facilitation():
    """Demonstrate complete facilitation workflow"""
    print("🎯 Complete Facilitation Demo")
    print("-" * 40)
    
    # Setup
    mock_engine = MockCollaborativeEngine()
    facilitator = CollaborativeDiscussionFacilitator(mock_engine)
    
    # Create discussion context
    context = DiscussionContext(
        session_id="product_planning",
        participants=["alice", "bob", "charlie", "david"],
        topic="Q4 Product Roadmap Planning",
        mode=FacilitationMode.DECISION_MAKING,
        duration_minutes=60,
        objectives=[
            "Prioritize top 5 features for Q4",
            "Align on resource allocation",
            "Set realistic timelines"
        ],
        current_phase="planning",
        metadata={"department": "product", "urgency": "high"}
    )
    
    print(f"🚀 Starting facilitated session: {context.topic}")
    print(f"   Mode: {context.mode.value}")
    print(f"   Duration: {context.duration_minutes} minutes")
    print(f"   Participants: {', '.join(context.participants)}")
    print(f"   Objectives: {', '.join(context.objectives)}")
    print()
    
    # Start session
    success = await facilitator.start_facilitated_session("product_planning", context)
    if not success:
        print("❌ Failed to start session")
        return
    
    print("✅ Session started successfully!")
    print()
    
    # Simulate discussion progression
    print("📈 Processing discussion updates...")
    
    # Process initial discussion
    await facilitator.process_discussion_update("product_planning", mock_engine.session_data)
    
    # Wait for periodic analysis
    print("⏳ Waiting for AI analysis...")
    await asyncio.sleep(3)
    
    # Get session analytics
    analytics = facilitator.get_session_analytics("product_planning")
    if analytics:
        print("📊 Current Session Analytics:")
        print(f"   Duration: {analytics['duration']:.1f} minutes")
        print(f"   AI interventions: {analytics['facilitation_interventions']}")
        print(f"   Active suggestions: {analytics['active_suggestions']}")
        print()
    
    # Simulate more discussion with conflict
    print("⚡ Simulating discussion with disagreement...")
    conflict_data = {
        'segments': mock_engine.session_data['segments'] + [
            {'user_id': 'alice', 'text': 'I strongly disagree with that approach', 'duration': 3.0, 'timestamp': 31.5},
            {'user_id': 'bob', 'text': 'No, you are completely wrong about this', 'duration': 2.5, 'timestamp': 34.5},
            {'user_id': 'alice', 'text': 'That is not true at all', 'duration': 2.0, 'timestamp': 37.0},
            {'user_id': 'charlie', 'text': 'Maybe we should step back and reconsider', 'duration': 3.0, 'timestamp': 39.0}
        ]
    }
    
    await facilitator.process_discussion_update("product_planning", conflict_data)
    
    # Show facilitation messages sent
    print(f"📨 Facilitation messages sent: {len(mock_engine.messages_sent)}")
    for i, message in enumerate(mock_engine.messages_sent, 1):
        print(f"   {i}. {message['message']}")
    print()
    
    # End session
    print("🏁 Ending facilitated session...")
    summary = await facilitator.end_facilitated_session("product_planning")
    
    print("✅ Session completed!")
    print(f"📋 Final Summary:")
    print(f"   Total duration: {summary['duration_minutes']:.1f} minutes")
    print(f"   Total AI interventions: {summary['facilitation_interventions']}")
    print(f"   Session mode: {summary['context']['mode']}")

async def demo_participation_balancing():
    """Demonstrate participation balancing features"""
    print("⚖️ Participation Balancing Demo")
    print("-" * 40)
    
    analyzer = DiscussionAnalyzer()
    
    # Create imbalanced discussion data
    imbalanced_data = {
        'segments': [
            # Alice dominates the conversation
            {'user_id': 'alice', 'text': 'I think we should do this approach because...', 'duration': 8.0},
            {'user_id': 'alice', 'text': 'And another thing, we need to consider...', 'duration': 6.0},
            {'user_id': 'alice', 'text': 'Also, from my experience, I believe...', 'duration': 7.0},
            {'user_id': 'alice', 'text': 'Let me add one more point about...', 'duration': 5.0},
            
            # Bob contributes minimally
            {'user_id': 'bob', 'text': 'Okay', 'duration': 1.0},
            {'user_id': 'bob', 'text': 'I see', 'duration': 0.5},
            
            # Charlie is completely silent (no segments)
            
            # David asks one question
            {'user_id': 'david', 'text': 'What about the budget?', 'duration': 2.0}
        ]
    }
    
    print("📊 Analyzing imbalanced discussion...")
    participation_metrics = analyzer.analyze_participation(imbalanced_data)
    
    print("Participation Analysis:")
    for metrics in participation_metrics:
        status = "🔴 Dominant" if metrics.engagement_score > 0.7 else "🟡 Quiet" if metrics.engagement_score < 0.3 else "🟢 Balanced"
        print(f"   {status} {metrics.user_id}: {metrics.speaking_time:.1f}s, engagement: {metrics.engagement_score:.2f}")
    
    print()
    
    # Show how facilitator would respond
    from collaborative_discussion_facilitator import FacilitationEngine
    
    engine = FacilitationEngine()
    context = DiscussionContext(
        session_id="balance_demo",
        participants=["alice", "bob", "charlie", "david"],
        topic="Team Discussion",
        mode=FacilitationMode.BRAINSTORMING,
        duration_minutes=30,
        objectives=[],
        current_phase="discussion",
        metadata={}
    )
    
    suggestions = engine._generate_participation_suggestions(participation_metrics, context)
    
    print("🤖 AI Facilitation Suggestions:")
    for suggestion in suggestions:
        priority_icon = "🔥" if suggestion.priority == "high" else "⚠️" if suggestion.priority == "medium" else "💡"
        print(f"   {priority_icon} {suggestion.suggestion_type}: {suggestion.message}")
        print(f"      Rationale: {suggestion.rationale}")
        print()

async def main():
    """Run all demos"""
    print("🎭 AI-Powered Discussion Facilitator Demo Suite")
    print("=" * 60)
    print()
    
    # Run individual demos
    await demo_discussion_analysis()
    print("\n" + "="*60 + "\n")
    
    await demo_topic_suggestions()
    print("\n" + "="*60 + "\n")
    
    await demo_participation_balancing()
    print("\n" + "="*60 + "\n")
    
    await demo_full_facilitation()
    
    print("\n🎉 Demo completed! The AI Discussion Facilitator is ready to enhance your collaborative sessions.")

if __name__ == "__main__":
    asyncio.run(main())