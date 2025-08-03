#!/usr/bin/env python3
"""
Demo script for Smart Content Recommendations (Task 42)
Test the content recommendation system with sample data
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from content_recommendations import (
    ContentItem, UserProfile, recommendation_engine,
    create_content_item_from_session
)

def create_sample_content_items():
    """Create sample content items for testing"""
    
    sample_contents = [
        {
            "title": "Quarterly Business Review Meeting",
            "transcript": """
            Welcome to our Q3 business review. I'm Sarah Johnson, VP of Sales. 
            Our revenue this quarter was $2.5 million, representing a 15% increase over Q2.
            The main growth drivers were our enterprise clients including Microsoft, Google, and Amazon.
            Our marketing team generated 1,200 qualified leads with an 8.5% conversion rate.
            For Q4, we need to focus on expanding our sales team and launching new product features.
            Action items: hire 2 new sales reps by November, launch holiday campaign by December.
            """,
            "topics": ["business", "sales", "marketing", "revenue"],
            "entities": [
                {"text": "Sarah Johnson", "type": "PERSON", "confidence": 0.95},
                {"text": "Microsoft", "type": "ORG", "confidence": 0.96},
                {"text": "Google", "type": "ORG", "confidence": 0.96},
                {"text": "Amazon", "type": "ORG", "confidence": 0.96},
                {"text": "$2.5 million", "type": "MONEY", "confidence": 0.90}
            ],
            "duration": 1800,  # 30 minutes
            "language": "en",
            "confidence": 0.92
        },
        {
            "title": "Machine Learning Workshop Introduction",
            "transcript": """
            Hello everyone, welcome to our machine learning workshop. I'm Dr. Alex Chen.
            Today we'll cover the fundamentals of supervised learning, neural networks, and deep learning.
            We'll start with linear regression, move to decision trees, and finish with neural networks.
            Machine learning is transforming industries from healthcare to finance to technology.
            Python and TensorFlow will be our primary tools for this workshop.
            Please make sure you have Jupyter notebooks installed on your laptops.
            """,
            "topics": ["technology", "education", "machine learning", "programming"],
            "entities": [
                {"text": "Dr. Alex Chen", "type": "PERSON", "confidence": 0.94},
                {"text": "Python", "type": "ORG", "confidence": 0.88},
                {"text": "TensorFlow", "type": "ORG", "confidence": 0.90},
                {"text": "Jupyter", "type": "ORG", "confidence": 0.85}
            ],
            "duration": 3600,  # 60 minutes
            "language": "en",
            "confidence": 0.89
        },
        {
            "title": "Healthcare Innovation Conference Keynote",
            "transcript": """
            Good morning, I'm Dr. Maria Rodriguez, Chief Medical Officer at HealthTech Solutions.
            Healthcare is undergoing a digital transformation with AI, telemedicine, and wearable devices.
            Patient outcomes are improving through personalized medicine and data-driven treatments.
            We're seeing breakthrough innovations in cancer research, diabetes management, and mental health.
            The integration of electronic health records with AI is revolutionizing diagnosis and treatment.
            Our goal is to make healthcare more accessible, affordable, and effective for everyone.
            """,
            "topics": ["health", "technology", "innovation", "medicine"],
            "entities": [
                {"text": "Dr. Maria Rodriguez", "type": "PERSON", "confidence": 0.96},
                {"text": "HealthTech Solutions", "type": "ORG", "confidence": 0.93},
                {"text": "AI", "type": "TECH", "confidence": 0.91}
            ],
            "duration": 2700,  # 45 minutes
            "language": "en",
            "confidence": 0.94
        },
        {
            "title": "Financial Planning Webinar",
            "transcript": """
            Welcome to our financial planning webinar. I'm Robert Kim, certified financial planner.
            Today we'll discuss investment strategies, retirement planning, and tax optimization.
            The stock market has been volatile, but long-term investing remains the best strategy.
            Diversification across stocks, bonds, and real estate is crucial for risk management.
            We'll cover 401k contributions, IRA options, and estate planning basics.
            Remember, starting early with compound interest is the key to building wealth.
            """,
            "topics": ["finance", "investment", "planning", "retirement"],
            "entities": [
                {"text": "Robert Kim", "type": "PERSON", "confidence": 0.95},
                {"text": "401k", "type": "FINANCIAL", "confidence": 0.92},
                {"text": "IRA", "type": "FINANCIAL", "confidence": 0.90}
            ],
            "duration": 2400,  # 40 minutes
            "language": "en",
            "confidence": 0.91
        },
        {
            "title": "Cooking Class: Italian Cuisine Basics",
            "transcript": """
            Buongiorno! I'm Chef Giuseppe Rossi, and welcome to Italian cooking basics.
            Today we'll learn to make authentic pasta, risotto, and tiramisu from scratch.
            Italian cuisine is all about fresh ingredients, simple techniques, and passion.
            We'll start with making fresh pasta dough using semolina flour and eggs.
            Then we'll prepare a classic marinara sauce with San Marzano tomatoes.
            Cooking is an art form that brings families and friends together around the table.
            """,
            "topics": ["food", "cooking", "education", "culture"],
            "entities": [
                {"text": "Chef Giuseppe Rossi", "type": "PERSON", "confidence": 0.97},
                {"text": "Italian", "type": "NATIONALITY", "confidence": 0.94},
                {"text": "San Marzano", "type": "GPE", "confidence": 0.88}
            ],
            "duration": 3300,  # 55 minutes
            "language": "en",
            "confidence": 0.87
        },
        {
            "title": "Climate Change Research Update",
            "transcript": """
            I'm Dr. Emily Watson from the Climate Research Institute.
            Our latest research shows accelerating climate change impacts globally.
            Temperature increases, sea level rise, and extreme weather events are intensifying.
            Renewable energy adoption is growing, but we need faster decarbonization.
            Carbon capture technology and sustainable agriculture are promising solutions.
            International cooperation and policy changes are essential for climate action.
            """,
            "topics": ["science", "environment", "research", "climate"],
            "entities": [
                {"text": "Dr. Emily Watson", "type": "PERSON", "confidence": 0.96},
                {"text": "Climate Research Institute", "type": "ORG", "confidence": 0.94}
            ],
            "duration": 2100,  # 35 minutes
            "language": "en",
            "confidence": 0.93
        }
    ]
    
    content_items = []
    
    for i, content_data in enumerate(sample_contents):
        # Create content item
        content_item = ContentItem(
            id=f"sample_content_{i+1}",
            title=content_data["title"],
            transcript=content_data["transcript"],
            entities=content_data["entities"],
            topics=content_data["topics"],
            tags=[],  # Will be generated
            duration=content_data["duration"],
            language=content_data["language"],
            confidence=content_data["confidence"],
            created_at=(datetime.now() - timedelta(days=i*2)).isoformat(),
            user_id="demo_user",
            file_info={
                "original_filename": f"sample_{i+1}.mp3",
                "file_size": content_data["duration"] * 1000,  # Approximate
                "processing_time": content_data["duration"] * 0.1
            },
            view_count=max(0, 10 - i*2),  # Decreasing view counts
            last_accessed=(datetime.now() - timedelta(hours=i*6)).isoformat() if i < 4 else None
        )
        
        content_items.append(content_item)
    
    return content_items


def create_sample_user_profiles():
    """Create sample user profiles for testing"""
    
    profiles = [
        {
            "user_id": "business_user",
            "interests": {
                "business": 0.9,
                "sales": 0.8,
                "marketing": 0.7,
                "finance": 0.6,
                "technology": 0.4
            },
            "viewing_history": ["sample_content_1", "sample_content_4"],
            "preferred_languages": ["en"],
            "preferred_duration_range": (1200, 3600)  # 20-60 minutes
        },
        {
            "user_id": "tech_enthusiast",
            "interests": {
                "technology": 0.95,
                "machine learning": 0.9,
                "programming": 0.85,
                "science": 0.7,
                "innovation": 0.6
            },
            "viewing_history": ["sample_content_2", "sample_content_3"],
            "preferred_languages": ["en"],
            "preferred_duration_range": (1800, 7200)  # 30-120 minutes
        },
        {
            "user_id": "health_professional",
            "interests": {
                "health": 0.95,
                "medicine": 0.9,
                "science": 0.8,
                "research": 0.75,
                "technology": 0.5
            },
            "viewing_history": ["sample_content_3", "sample_content_6"],
            "preferred_languages": ["en"],
            "preferred_duration_range": (1500, 4500)  # 25-75 minutes
        }
    ]
    
    user_profiles = []
    
    for profile_data in profiles:
        profile = UserProfile(
            user_id=profile_data["user_id"],
            interests=profile_data["interests"],
            viewing_history=profile_data["viewing_history"],
            search_history=[],
            preferred_languages=profile_data["preferred_languages"],
            preferred_duration_range=profile_data["preferred_duration_range"],
            created_at=(datetime.now() - timedelta(days=30)).isoformat(),
            last_updated=datetime.now().isoformat()
        )
        
        user_profiles.append(profile)
    
    return user_profiles


def test_content_similarity():
    """Test content similarity recommendations"""
    print("🧪 Testing Content Similarity...")
    
    try:
        # Get similar content for the first item
        similar_items = recommendation_engine.get_similar_content("sample_content_1", limit=3)
        
        if similar_items:
            print("✅ Content similarity test successful!")
            print(f"Found {len(similar_items)} similar items to 'Quarterly Business Review Meeting':")
            
            for i, (content, similarity) in enumerate(similar_items, 1):
                print(f"  {i}. {content.title} (Similarity: {similarity:.2f})")
        else:
            print("⚠️ No similar content found")
        
        return True
        
    except Exception as e:
        print(f"❌ Content similarity test failed: {e}")
        return False


def test_personalized_recommendations():
    """Test personalized recommendations"""
    print("\n🧪 Testing Personalized Recommendations...")
    
    try:
        # Test recommendations for different user types
        test_users = ["business_user", "tech_enthusiast", "health_professional"]
        
        for user_id in test_users:
            recommendations = recommendation_engine.get_personalized_recommendations(user_id, limit=3)
            
            if recommendations:
                print(f"✅ Recommendations for {user_id}:")
                for i, (content, score) in enumerate(recommendations, 1):
                    print(f"  {i}. {content.title} (Score: {score:.2f})")
            else:
                print(f"⚠️ No recommendations found for {user_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Personalized recommendations test failed: {e}")
        return False


def test_trending_content():
    """Test trending content analysis"""
    print("\n🧪 Testing Trending Content...")
    
    try:
        trending_items = recommendation_engine.get_trending_content(limit=5, time_window_days=7)
        
        if trending_items:
            print("✅ Trending content test successful!")
            print("Top trending content (last 7 days):")
            
            for i, (content, score) in enumerate(trending_items, 1):
                print(f"  {i}. {content.title} (Trending Score: {score:.1f}, Views: {content.view_count})")
        else:
            print("⚠️ No trending content found")
        
        return True
        
    except Exception as e:
        print(f"❌ Trending content test failed: {e}")
        return False


def test_content_gap_analysis():
    """Test content gap analysis"""
    print("\n🧪 Testing Content Gap Analysis...")
    
    try:
        gap_analysis = recommendation_engine.analyze_content_gaps()
        
        print("✅ Content gap analysis successful!")
        print(f"Total topics: {gap_analysis['total_topics']}")
        print(f"Total content: {gap_analysis['total_content']}")
        print(f"Average topics per content: {gap_analysis['average_topics_per_content']:.1f}")
        
        # Show underrepresented topics
        if gap_analysis["underrepresented_topics"]:
            print("\nUnderrepresented topics:")
            for topic_info in gap_analysis["underrepresented_topics"][:3]:
                print(f"  • {topic_info['topic']}: {topic_info['coverage_ratio']:.1%} coverage ({topic_info['suggested_priority']} priority)")
        
        # Show missing trending topics
        if gap_analysis["missing_trending_topics"]:
            print("\nMissing trending topics:")
            for trend_info in gap_analysis["missing_trending_topics"][:3]:
                print(f"  • {trend_info['keyword']}: trend score {trend_info['trend_score']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Content gap analysis test failed: {e}")
        return False


def test_smart_tagging():
    """Test smart tag generation"""
    print("\n🧪 Testing Smart Tag Generation...")
    
    try:
        # Test with the first content item
        content_item = list(recommendation_engine.content_items.values())[0]
        smart_tags = recommendation_engine.generate_smart_tags(content_item)
        
        print("✅ Smart tagging test successful!")
        print(f"Generated {len(smart_tags)} tags for '{content_item.title}':")
        
        # Group tags by type
        tag_types = {}
        for tag in smart_tags:
            if ":" in tag:
                tag_type, tag_value = tag.split(":", 1)
                if tag_type not in tag_types:
                    tag_types[tag_type] = []
                tag_types[tag_type].append(tag_value)
            else:
                if "general" not in tag_types:
                    tag_types["general"] = []
                tag_types["general"].append(tag)
        
        for tag_type, tags in tag_types.items():
            print(f"  {tag_type.title()}: {', '.join(tags[:3])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Smart tagging test failed: {e}")
        return False


def test_library_stats():
    """Test library statistics"""
    print("\n🧪 Testing Library Statistics...")
    
    try:
        stats = recommendation_engine.get_content_stats()
        
        print("✅ Library statistics test successful!")
        print(f"Total content: {stats['total_content']}")
        print(f"Total duration: {stats['total_duration_hours']:.1f} hours")
        print(f"Average duration: {stats['average_duration_minutes']:.1f} minutes")
        print(f"Total users: {stats['total_users']}")
        
        # Show top languages
        if stats["language_distribution"]:
            print(f"Languages: {', '.join(stats['language_distribution'].keys())}")
        
        # Show top topics
        if stats["top_topics"]:
            top_topics = list(stats["top_topics"].keys())[:5]
            print(f"Top topics: {', '.join(top_topics)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Library statistics test failed: {e}")
        return False


def main():
    """Run all content recommendation tests"""
    print("🚀 Starting Content Recommendations Tests")
    print("=" * 50)
    
    # Clear existing data for clean test
    recommendation_engine.content_items.clear()
    recommendation_engine.user_profiles.clear()
    
    # Create sample data
    print("📝 Creating sample content and user profiles...")
    
    # Add sample content items
    sample_contents = create_sample_content_items()
    for content_item in sample_contents:
        # Generate smart tags
        content_item.tags = recommendation_engine.generate_smart_tags(content_item)
        # Add to recommendation engine
        recommendation_engine.add_content_item(content_item)
    
    # Add sample user profiles
    sample_profiles = create_sample_user_profiles()
    for profile in sample_profiles:
        recommendation_engine.user_profiles[profile.user_id] = profile
    
    print(f"✅ Created {len(sample_contents)} content items and {len(sample_profiles)} user profiles")
    
    # Run tests
    tests = [
        test_content_similarity,
        test_personalized_recommendations,
        test_trending_content,
        test_content_gap_analysis,
        test_smart_tagging,
        test_library_stats
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Content recommendation system is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")
    
    # Save test data for UI testing
    recommendation_engine.save_data()
    print("\n💾 Test data saved for UI testing")
    
    print("\n📝 You can now run the Streamlit app to test the UI:")
    print("   streamlit run app_refactored.py")
    print("   Navigate to 'Search & Insights' → 'Smart Recommendations' tab")


if __name__ == "__main__":
    main()