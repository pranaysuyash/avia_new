#!/usr/bin/env python3
"""
Demo script for semantic search and similarity features
"""

import asyncio
import logging
import os
import sys
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from semantic_search.semantic_engine import SemanticSearchEngine
from semantic_search.transcript_embeddings import TranscriptEmbeddingManager
from semantic_search.providers import OpenAIEmbeddingProvider, SentenceTransformerProvider, MockEmbeddingProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticSearchDemo:
    """Demo class for semantic search features"""
    
    def __init__(self, use_mock_provider: bool = False):
        """Initialize demo with embedding provider"""
        try:
            if use_mock_provider:
                provider = MockEmbeddingProvider()
                logger.info("Using mock embedding provider for demo")
            else:
                # Try OpenAI first, fallback to SentenceTransformer
                try:
                    provider = OpenAIEmbeddingProvider()
                    logger.info("Using OpenAI embedding provider")
                except Exception as e:
                    logger.warning(f"OpenAI provider failed: {e}")
                    provider = SentenceTransformerProvider()
                    logger.info("Using SentenceTransformer provider")
            
            self.embedding_manager = TranscriptEmbeddingManager(
                embedding_provider=provider,
                db_path="demo_embeddings.db"
            )
            self.search_engine = SemanticSearchEngine(self.embedding_manager)
            
        except Exception as e:
            logger.error(f"Failed to initialize demo: {e}")
            raise
    
    def create_sample_transcripts(self) -> List[Dict[str, Any]]:
        """Create sample transcripts for demonstration"""
        return [
            {
                'id': 'meeting_001',
                'title': 'Weekly Team Meeting - Project Alpha',
                'content': '''
                Good morning everyone. Let's start with our weekly team meeting for Project Alpha.
                First, let's review our progress on the user authentication system. Sarah, can you give us an update?
                
                Sarah: Thanks, Mike. We've completed the login functionality and are now working on password reset features.
                The security audit revealed some vulnerabilities that we need to address before the next release.
                
                Mike: That's concerning. What kind of vulnerabilities are we talking about?
                
                Sarah: Mainly around session management and input validation. Nothing critical, but we should fix them.
                I estimate it will take about two weeks to implement all the security improvements.
                
                Mike: Okay, let's prioritize security. What about the mobile app development?
                
                John: The iOS version is almost ready for beta testing. We're still working on the Android version.
                The main challenge is ensuring consistent user experience across both platforms.
                
                Mike: Great work everyone. Let's schedule a security review meeting for next week.
                ''',
                'metadata': {
                    'type': 'meeting',
                    'participants': ['Mike', 'Sarah', 'John'],
                    'duration': 1800,
                    'date': '2024-01-15'
                }
            },
            {
                'id': 'interview_001',
                'title': 'Customer Interview - Product Feedback',
                'content': '''
                Interviewer: Thank you for taking the time to speak with us today. Can you tell us about your experience with our product?
                
                Customer: Overall, I'm quite satisfied with the product. The user interface is intuitive and easy to navigate.
                However, I've encountered some performance issues, especially when uploading large files.
                
                Interviewer: Can you describe these performance issues in more detail?
                
                Customer: When I try to upload files larger than 100MB, the system becomes very slow and sometimes times out.
                This is frustrating because I often need to upload video files for my work.
                
                Interviewer: I understand. Are there any other features you'd like to see improved?
                
                Customer: I'd love to see better collaboration features. Currently, it's difficult to share projects with team members.
                Also, the mobile app could use some improvements. It's missing several features that are available on the desktop version.
                
                Interviewer: Those are valuable insights. Is there anything you particularly like about the product?
                
                Customer: The automated transcription feature is fantastic. It saves me hours of work every week.
                The accuracy is impressive, even with technical terminology.
                ''',
                'metadata': {
                    'type': 'interview',
                    'customer_id': 'cust_001',
                    'duration': 1200,
                    'date': '2024-01-16'
                }
            },
            {
                'id': 'lecture_001',
                'title': 'Introduction to Machine Learning',
                'content': '''
                Welcome to today's lecture on machine learning fundamentals. Today we'll cover the basic concepts
                that form the foundation of artificial intelligence and data science.
                
                Machine learning is a subset of artificial intelligence that enables computers to learn and improve
                from experience without being explicitly programmed. There are three main types of machine learning:
                supervised learning, unsupervised learning, and reinforcement learning.
                
                Supervised learning uses labeled training data to learn a mapping function from input to output.
                Common examples include classification tasks like email spam detection and regression tasks like
                predicting house prices based on features like location, size, and age.
                
                Unsupervised learning finds hidden patterns in data without labeled examples. Clustering algorithms
                group similar data points together, while dimensionality reduction techniques help visualize
                high-dimensional data in lower dimensions.
                
                Reinforcement learning involves an agent learning to make decisions by interacting with an environment
                and receiving rewards or penalties. This approach has been successful in game playing, robotics,
                and autonomous vehicle control.
                
                The key to successful machine learning is having quality data, choosing appropriate algorithms,
                and properly evaluating model performance using techniques like cross-validation.
                ''',
                'metadata': {
                    'type': 'lecture',
                    'subject': 'machine_learning',
                    'instructor': 'Dr. Smith',
                    'duration': 3600,
                    'date': '2024-01-17'
                }
            },
            {
                'id': 'support_001',
                'title': 'Customer Support Call - Technical Issue',
                'content': '''
                Support Agent: Hello, this is Alex from technical support. How can I help you today?
                
                Customer: Hi Alex, I'm having trouble with the software crashing whenever I try to export my data.
                It worked fine last week, but now it crashes every time.
                
                Support Agent: I'm sorry to hear about that issue. Let me help you troubleshoot this problem.
                Can you tell me what operating system you're using and which version of our software?
                
                Customer: I'm using Windows 11 and I believe it's version 2.3.1 of your software.
                
                Support Agent: Thank you. Have you tried restarting the application or your computer since the issue started?
                
                Customer: Yes, I've tried both multiple times. The problem persists.
                
                Support Agent: Let's try clearing the application cache. Can you navigate to the settings menu
                and look for a "Clear Cache" option under the Advanced tab?
                
                Customer: Okay, I found it. Should I click it now?
                
                Support Agent: Yes, please go ahead and clear the cache, then try exporting your data again.
                
                Customer: Wow, that worked! The export completed successfully. Thank you so much for your help.
                
                Support Agent: You're welcome! The cache can sometimes become corrupted and cause these issues.
                Is there anything else I can help you with today?
                ''',
                'metadata': {
                    'type': 'support',
                    'issue_type': 'technical',
                    'resolution': 'cache_clear',
                    'duration': 900,
                    'date': '2024-01-18'
                }
            },
            {
                'id': 'brainstorm_001',
                'title': 'Product Brainstorming Session',
                'content': '''
                Team Lead: Alright everyone, let's brainstorm ideas for our next product feature.
                We want to focus on improving user engagement and retention.
                
                Designer: What if we added gamification elements? Users could earn points for completing certain actions
                and unlock achievements. This could make the experience more engaging and fun.
                
                Developer: That's interesting. We could implement a badge system and leaderboards.
                From a technical perspective, it would require a new database schema for tracking user activities.
                
                Product Manager: I like the gamification idea, but we should be careful not to make it feel forced.
                What about personalized recommendations based on user behavior and preferences?
                
                Designer: Personalization is definitely important. We could use machine learning to analyze user patterns
                and suggest relevant content or features they might be interested in.
                
                Developer: For recommendations, we'd need to implement analytics tracking and build a recommendation engine.
                It's doable, but it would be a significant development effort.
                
                Team Lead: Both ideas have merit. Let's think about which one would have the biggest impact on user retention.
                What does the data tell us about why users stop using our product?
                
                Product Manager: The main reasons are lack of relevant content and difficulty finding features they need.
                Personalized recommendations could address both of these issues.
                
                Team Lead: Great point. Let's prototype the recommendation system first and see how users respond.
                ''',
                'metadata': {
                    'type': 'brainstorming',
                    'participants': ['Team Lead', 'Designer', 'Developer', 'Product Manager'],
                    'duration': 2400,
                    'date': '2024-01-19'
                }
            }
        ]
    
    async def run_demo(self):
        """Run the complete semantic search demo"""
        print("🧠 Semantic Search & Similarity Demo")
        print("=" * 50)
        
        # Step 1: Index sample transcripts
        print("\n1. Indexing Sample Transcripts...")
        sample_transcripts = self.create_sample_transcripts()
        
        results = await self.search_engine.batch_index_transcripts(sample_transcripts)
        successful = sum(1 for success in results.values() if success)
        print(f"   ✅ Successfully indexed {successful}/{len(sample_transcripts)} transcripts")
        
        # Step 2: Demonstrate semantic search
        print("\n2. Semantic Search Demo...")
        search_queries = [
            "security vulnerabilities and authentication",
            "performance issues with file uploads",
            "machine learning algorithms and data science",
            "technical support and troubleshooting",
            "product features and user engagement"
        ]
        
        for query in search_queries:
            print(f"\n   🔍 Query: '{query}'")
            results = await self.search_engine.semantic_search(query, limit=3, min_similarity=0.3)
            
            for i, result in enumerate(results, 1):
                print(f"      {i}. {result.title} (Similarity: {result.similarity_score:.3f})")
                if result.matching_chunks:
                    snippet = result.matching_chunks[0]['text'][:100] + "..."
                    print(f"         Preview: {snippet}")
        
        # Step 3: Demonstrate similarity search
        print("\n3. Similarity Search Demo...")
        reference_transcript = "meeting_001"
        print(f"   🔗 Finding transcripts similar to: {reference_transcript}")
        
        similar_results = await self.search_engine.find_similar_transcripts(
            reference_transcript, limit=3, min_similarity=0.2
        )
        
        for i, result in enumerate(similar_results, 1):
            print(f"      {i}. {result.title} (Similarity: {result.similarity_score:.3f})")
        
        # Step 4: Demonstrate recommendations
        print("\n4. Content Recommendations Demo...")
        user_history = ["meeting_001", "interview_001"]
        print(f"   💡 Recommendations based on history: {user_history}")
        
        recommendations = await self.search_engine.get_recommendations(user_history, limit=3)
        
        for i, result in enumerate(recommendations, 1):
            print(f"      {i}. {result.title} (Score: {result.similarity_score:.3f})")
        
        # Step 5: Show search statistics
        print("\n5. Search Statistics...")
        stats = self.search_engine.get_search_stats()
        
        if stats.get('semantic_search_enabled'):
            embedding_stats = stats.get('embedding_stats', {})
            print(f"   📊 Total Transcripts: {embedding_stats.get('total_transcripts', 0)}")
            print(f"   📊 Total Chunks: {embedding_stats.get('total_chunks', 0)}")
            print(f"   📊 Avg Chunks/Transcript: {embedding_stats.get('avg_chunks_per_transcript', 0)}")
            print(f"   📊 Embedding Model: {embedding_stats.get('embedding_model', 'Unknown')}")
            print(f"   📊 Embedding Dimension: {embedding_stats.get('embedding_dimension', 0)}")
        
        # Step 6: Demonstrate within-transcript search
        print("\n6. Within-Transcript Search Demo...")
        transcript_id = "lecture_001"
        within_query = "supervised learning examples"
        print(f"   🎯 Searching within '{transcript_id}' for: '{within_query}'")
        
        within_results = await self.search_engine.search_within_transcript(
            transcript_id, within_query, limit=2
        )
        
        for i, result in enumerate(within_results, 1):
            print(f"      {i}. Chunk (Similarity: {result['similarity']:.3f})")
            snippet = result['text'][:150] + "..."
            print(f"         Content: {snippet}")
        
        print("\n✅ Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("• Semantic search using natural language queries")
        print("• Finding similar transcripts based on content")
        print("• Personalized content recommendations")
        print("• Within-transcript semantic search")
        print("• Batch indexing and search analytics")


async def main():
    """Main demo function"""
    print("Semantic Search Demo")
    print("Choose embedding provider:")
    print("1. OpenAI (requires API key)")
    print("2. SentenceTransformer (local, no API key needed)")
    print("3. Mock (for testing, generates random embeddings)")
    
    choice = input("Enter choice (1-3): ").strip()
    
    use_mock = False
    if choice == "3":
        use_mock = True
    elif choice == "2":
        # Force SentenceTransformer by removing OpenAI key temporarily
        original_key = os.environ.get('OPENAI_API_KEY')
        if original_key:
            del os.environ['OPENAI_API_KEY']
    
    try:
        demo = SemanticSearchDemo(use_mock_provider=use_mock)
        await demo.run_demo()
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("• Make sure you have the required dependencies installed")
        print("• For OpenAI provider, set OPENAI_API_KEY environment variable")
        print("• For SentenceTransformer, ensure you have sufficient disk space for model download")
        
    finally:
        # Restore OpenAI key if it was temporarily removed
        if choice == "2" and 'original_key' in locals() and original_key:
            os.environ['OPENAI_API_KEY'] = original_key


if __name__ == "__main__":
    asyncio.run(main())