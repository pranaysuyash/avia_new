"""
Demo script for Market Opportunity Identification System

This script demonstrates the capabilities of the market opportunity identification system
including trend analysis, opportunity scoring, and market intelligence generation.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

from market_opportunity_identification import (
    MarketOpportunityIdentificationSystem,
    create_sample_content_data
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_comprehensive_sample_data() -> List[Dict[str, Any]]:
    """Create comprehensive sample content data for demonstration"""
    sample_data = [
        {
            'id': 'content_001',
            'type': 'video',
            'transcript': '''
            This comprehensive guide explores the latest trends in artificial intelligence and machine learning.
            We discuss how AI is transforming business operations, from automated customer service to 
            predictive analytics. The video covers practical implementation strategies for small and 
            medium businesses looking to adopt AI technologies. Key topics include natural language 
            processing, computer vision, and robotic process automation.
            ''',
            'metadata': {
                'duration': 1200,
                'language': 'en',
                'category': 'Technology',
                'tags': ['AI', 'Machine Learning', 'Business Automation']
            },
            'engagement': {
                'views': 15000,
                'likes': 1200,
                'comments': 89,
                'shares': 156,
                'watch_time_avg': 780
            },
            'created_at': datetime.now() - timedelta(days=3)
        },
        {
            'id': 'content_002',
            'type': 'audio',
            'transcript': '''
            In this podcast episode, we interview leading experts about the future of remote work
            and digital collaboration tools. The discussion covers emerging trends in virtual reality
            meetings, asynchronous communication platforms, and productivity tracking software.
            We also explore the challenges of maintaining company culture in distributed teams
            and strategies for effective remote team management.
            ''',
            'metadata': {
                'duration': 2400,
                'language': 'en',
                'category': 'Business',
                'tags': ['Remote Work', 'Digital Collaboration', 'Team Management']
            },
            'engagement': {
                'views': 8500,
                'likes': 650,
                'comments': 45,
                'shares': 78,
                'watch_time_avg': 1800
            },
            'created_at': datetime.now() - timedelta(days=7)
        },
        {
            'id': 'content_003',
            'type': 'video',
            'transcript': '''
            This educational content focuses on sustainable technology and green computing practices.
            We examine how companies are reducing their carbon footprint through efficient data centers,
            renewable energy adoption, and sustainable software development practices. The video
            includes case studies from major tech companies and practical tips for developers
            to write more energy-efficient code.
            ''',
            'metadata': {
                'duration': 900,
                'language': 'en',
                'category': 'Environment',
                'tags': ['Sustainability', 'Green Technology', 'Environmental Impact']
            },
            'engagement': {
                'views': 5200,
                'likes': 420,
                'comments': 32,
                'shares': 89,
                'watch_time_avg': 650
            },
            'created_at': datetime.now() - timedelta(days=12)
        },
        {
            'id': 'content_004',
            'type': 'audio',
            'transcript': '''
            This healthcare technology podcast explores telemedicine innovations and digital health solutions.
            We discuss wearable devices, health monitoring apps, and AI-powered diagnostic tools.
            The episode covers regulatory challenges, patient privacy concerns, and the future
            of personalized medicine. Expert guests share insights on emerging trends in
            mental health apps and remote patient monitoring systems.
            ''',
            'metadata': {
                'duration': 1800,
                'language': 'en',
                'category': 'Healthcare',
                'tags': ['Telemedicine', 'Digital Health', 'Medical Technology']
            },
            'engagement': {
                'views': 6800,
                'likes': 540,
                'comments': 67,
                'shares': 123,
                'watch_time_avg': 1200
            },
            'created_at': datetime.now() - timedelta(days=15)
        },
        {
            'id': 'content_005',
            'type': 'video',
            'transcript': '''
            This financial technology overview covers cryptocurrency trends, blockchain applications,
            and digital banking innovations. We explore decentralized finance (DeFi) platforms,
            central bank digital currencies (CBDCs), and the impact of fintech on traditional banking.
            The content includes analysis of regulatory developments and investment opportunities
            in the fintech sector.
            ''',
            'metadata': {
                'duration': 1500,
                'language': 'en',
                'category': 'Finance',
                'tags': ['Fintech', 'Cryptocurrency', 'Digital Banking']
            },
            'engagement': {
                'views': 12000,
                'likes': 980,
                'comments': 156,
                'shares': 234,
                'watch_time_avg': 1100
            },
            'created_at': datetime.now() - timedelta(days=20)
        },
        {
            'id': 'content_006',
            'type': 'audio',
            'transcript': '''
            This educational podcast focuses on cybersecurity best practices for small businesses.
            We cover common security threats, password management, employee training programs,
            and incident response planning. The episode includes practical advice on choosing
            security software, implementing multi-factor authentication, and creating
            security-aware company culture.
            ''',
            'metadata': {
                'duration': 2100,
                'language': 'en',
                'category': 'Security',
                'tags': ['Cybersecurity', 'Small Business', 'Security Training']
            },
            'engagement': {
                'views': 4500,
                'likes': 380,
                'comments': 28,
                'shares': 67,
                'watch_time_avg': 1600
            },
            'created_at': datetime.now() - timedelta(days=25)
        },
        {
            'id': 'content_007',
            'type': 'video',
            'transcript': '''
            This content marketing strategy guide explores social media trends and influencer marketing.
            We analyze successful campaigns across different platforms, discuss content creation tools,
            and examine audience engagement strategies. The video covers emerging platforms,
            video marketing trends, and the role of user-generated content in brand building.
            ''',
            'metadata': {
                'duration': 1350,
                'language': 'en',
                'category': 'Marketing',
                'tags': ['Content Marketing', 'Social Media', 'Influencer Marketing']
            },
            'engagement': {
                'views': 9200,
                'likes': 750,
                'comments': 94,
                'shares': 187,
                'watch_time_avg': 950
            },
            'created_at': datetime.now() - timedelta(days=30)
        },
        {
            'id': 'content_008',
            'type': 'audio',
            'transcript': '''
            This e-learning and educational technology podcast examines online learning platforms,
            virtual classrooms, and adaptive learning systems. We discuss the impact of AI
            in education, personalized learning paths, and the future of skill development.
            The episode includes insights on microlearning, gamification, and assessment technologies.
            ''',
            'metadata': {
                'duration': 1950,
                'language': 'en',
                'category': 'Education',
                'tags': ['E-learning', 'Educational Technology', 'Online Learning']
            },
            'engagement': {
                'views': 7100,
                'likes': 590,
                'comments': 73,
                'shares': 145,
                'watch_time_avg': 1400
            },
            'created_at': datetime.now() - timedelta(days=35)
        }
    ]
    
    return sample_data

async def demonstrate_opportunity_identification():
    """Demonstrate the complete opportunity identification process"""
    print("🎯 Market Opportunity Identification System Demo")
    print("=" * 60)
    
    try:
        # Initialize the system
        print("\n1. Initializing Market Opportunity Identification System...")
        system = MarketOpportunityIdentificationSystem()
        
        # Create comprehensive sample data
        print("\n2. Creating comprehensive sample content data...")
        content_data = create_comprehensive_sample_data()
        print(f"   Created {len(content_data)} content items for analysis")
        
        # Display sample content overview
        print("\n3. Sample Content Overview:")
        categories = {}
        total_engagement = 0
        
        for item in content_data:
            category = item['metadata']['category']
            categories[category] = categories.get(category, 0) + 1
            total_engagement += item['engagement']['views']
        
        print(f"   • Total Content Items: {len(content_data)}")
        print(f"   • Categories: {', '.join(categories.keys())}")
        print(f"   • Total Views: {total_engagement:,}")
        print(f"   • Date Range: {min(item['created_at'] for item in content_data).strftime('%Y-%m-%d')} to {max(item['created_at'] for item in content_data).strftime('%Y-%m-%d')}")
        
        # Run opportunity identification
        print("\n4. Running Market Opportunity Analysis...")
        print("   This may take a moment as we analyze trends and identify opportunities...")
        
        results = await system.identify_opportunities(content_data, time_period_days=40)
        
        if not results['success']:
            print(f"   ❌ Analysis failed: {results['message']}")
            return
        
        print(f"   ✅ Analysis completed successfully!")
        print(f"   📊 {results['message']}")
        
        # Display analysis metadata
        metadata = results.get('analysis_metadata', {})
        print(f"\n5. Analysis Summary:")
        print(f"   • Content Items Analyzed: {metadata.get('content_items_analyzed', 0)}")
        print(f"   • Trends Identified: {metadata.get('trends_identified', 0)}")
        print(f"   • Opportunities Found: {metadata.get('opportunities_found', 0)}")
        print(f"   • Analysis Date: {metadata.get('analysis_date', 'N/A')[:19]}")
        
        # Display top opportunities
        opportunities = results.get('opportunities', [])
        if opportunities:
            print(f"\n6. Top Market Opportunities:")
            print("-" * 40)
            
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"\n   {i}. {opp['title']}")
                print(f"      📊 Score: {opp['opportunity_score']:.2f}/10")
                print(f"      🏷️  Category: {opp['category']}")
                print(f"      ⭐ Priority: {opp['priority_level']}")
                print(f"      💰 Market Size: ${opp['market_size_estimate']:,.0f}")
                print(f"      🏁 Competition: {opp['competition_level']}")
                print(f"      📈 Trend: {opp['trend_direction']}")
                print(f"      📝 Description: {opp['description']}")
                
                # Show top keywords and recommendations
                keywords = opp.get('keywords', [])[:3]
                if keywords:
                    print(f"      🔑 Keywords: {', '.join(keywords)}")
                
                recommendations = opp.get('recommended_actions', [])[:2]
                if recommendations:
                    print(f"      💡 Top Recommendations:")
                    for rec in recommendations:
                        print(f"         • {rec}")
        
        # Display trend analysis
        trends = results.get('trends', [])
        if trends:
            print(f"\n7. Market Trends Analysis:")
            print("-" * 40)
            
            for i, trend in enumerate(trends[:5], 1):
                print(f"\n   {i}. {trend['trend_name']}")
                print(f"      💪 Strength: {trend['trend_strength']:.2f}/10")
                print(f"      📈 Growth Rate: {trend['growth_rate']:.1f}%")
                print(f"      🎯 Market Impact: {trend['market_impact']}")
                print(f"      🎲 Confidence: {trend['confidence_level']:.2f}")
                
                related_keywords = trend.get('related_keywords', [])[:3]
                if related_keywords:
                    print(f"      🔗 Related: {', '.join(related_keywords)}")
        
        # Display executive summary
        summary = results.get('summary', {})
        if summary:
            print(f"\n8. Executive Summary:")
            print("-" * 40)
            
            exec_summary = summary.get('executive_summary', {})
            print(f"   • Total Market Size: ${exec_summary.get('estimated_total_market_size', 0):,.0f}")
            print(f"   • High Priority Opportunities: {exec_summary.get('high_priority_opportunities', 0)}")
            print(f"   • High Growth Trends: {exec_summary.get('high_growth_trends', 0)}")
            
            # Key insights
            key_insights = summary.get('key_insights', [])
            if key_insights:
                print(f"\n   Key Insights:")
                for insight in key_insights[:3]:
                    print(f"   • {insight}")
            
            # Market outlook
            market_outlook = summary.get('market_outlook', {})
            if market_outlook:
                print(f"\n   Market Outlook:")
                print(f"   • Overall: {market_outlook.get('outlook', 'N/A')}")
                print(f"   • Confidence: {market_outlook.get('confidence', 'N/A')}")
                print(f"   • Summary: {market_outlook.get('summary', 'N/A')}")
        
        # Get dashboard data
        print(f"\n9. Market Intelligence Dashboard:")
        print("-" * 40)
        
        dashboard_data = system.get_market_intelligence_dashboard()
        
        opp_summary = dashboard_data.get('opportunity_summary', {})
        trend_summary = dashboard_data.get('trend_summary', {})
        
        print(f"   Opportunity Metrics:")
        print(f"   • Total Opportunities: {opp_summary.get('total_opportunities', 0)}")
        print(f"   • High Priority Count: {opp_summary.get('high_priority_count', 0)}")
        print(f"   • Average Score: {opp_summary.get('average_opportunity_score', 0):.2f}")
        
        print(f"\n   Trend Metrics:")
        print(f"   • Total Trends: {trend_summary.get('total_trends', 0)}")
        print(f"   • High Impact Trends: {trend_summary.get('high_impact_trends', 0)}")
        print(f"   • Average Strength: {trend_summary.get('average_trend_strength', 0):.2f}")
        
        # Category distribution
        category_dist = opp_summary.get('category_distribution', {})
        if category_dist:
            print(f"\n   Category Distribution:")
            for category, count in sorted(category_dist.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {category}: {count} opportunities")
        
        # Demonstrate specific opportunity report
        if opportunities:
            print(f"\n10. Detailed Opportunity Report Example:")
            print("-" * 40)
            
            sample_opp_id = opportunities[0]['id']
            detailed_report = system.get_opportunity_report(sample_opp_id)
            
            if detailed_report:
                print(f"   Opportunity ID: {detailed_report['id']}")
                print(f"   Title: {detailed_report['title']}")
                print(f"   Category: {detailed_report['category']}")
                print(f"   Score: {detailed_report['opportunity_score']:.2f}")
                print(f"   Created: {detailed_report['created_at'][:19]}")
                
                target_audience = detailed_report.get('target_audience', [])
                if target_audience:
                    print(f"   Target Audience: {', '.join(target_audience)}")
                
                content_gaps = detailed_report.get('content_gaps', [])
                if content_gaps:
                    print(f"   Content Gaps:")
                    for gap in content_gaps[:3]:
                        print(f"   • {gap}")
        
        print(f"\n✅ Demo completed successfully!")
        print(f"📊 The system identified {len(opportunities)} opportunities and {len(trends)} trends")
        print(f"💡 Use the Streamlit UI (market_opportunity_identification_ui.py) for interactive analysis")
        
        return results
        
    except Exception as e:
        print(f"❌ Demo failed with error: {str(e)}")
        logger.error(f"Demo error: {str(e)}")
        return None

def demonstrate_content_analysis():
    """Demonstrate content analysis capabilities"""
    print(f"\n🔍 Content Analysis Demonstration")
    print("=" * 50)
    
    try:
        # Create sample data
        content_data = create_comprehensive_sample_data()
        
        # Analyze content characteristics
        print(f"\n1. Content Portfolio Analysis:")
        
        # Category analysis
        categories = {}
        total_duration = 0
        total_engagement = 0
        
        for item in content_data:
            category = item['metadata']['category']
            categories[category] = categories.get(category, 0) + 1
            total_duration += item['metadata']['duration']
            total_engagement += item['engagement']['views']
        
        print(f"   • Content Categories: {len(categories)}")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {category}: {count} items")
        
        print(f"   • Total Duration: {total_duration/60:.1f} minutes")
        print(f"   • Total Engagement: {total_engagement:,} views")
        print(f"   • Average Duration: {total_duration/len(content_data)/60:.1f} minutes per item")
        
        # Engagement analysis
        print(f"\n2. Engagement Analysis:")
        
        engagement_data = []
        for item in content_data:
            engagement = item['engagement']
            engagement_data.append({
                'id': item['id'],
                'category': item['metadata']['category'],
                'views': engagement['views'],
                'likes': engagement['likes'],
                'engagement_rate': engagement['likes'] / engagement['views'] * 100,
                'watch_time_ratio': engagement['watch_time_avg'] / item['metadata']['duration'] * 100
            })
        
        df = pd.DataFrame(engagement_data)
        
        print(f"   • Average Views: {df['views'].mean():.0f}")
        print(f"   • Average Likes: {df['likes'].mean():.0f}")
        print(f"   • Average Engagement Rate: {df['engagement_rate'].mean():.2f}%")
        print(f"   • Average Watch Time Ratio: {df['watch_time_ratio'].mean():.1f}%")
        
        # Top performing content
        top_content = df.nlargest(3, 'views')
        print(f"\n   Top Performing Content:")
        for _, row in top_content.iterrows():
            print(f"   • {row['id']}: {row['views']:,} views ({row['category']})")
        
        # Content gaps analysis
        print(f"\n3. Content Gap Analysis:")
        
        # Analyze content distribution by category and identify gaps
        category_performance = df.groupby('category').agg({
            'views': 'mean',
            'engagement_rate': 'mean',
            'watch_time_ratio': 'mean'
        }).round(2)
        
        print(f"   Category Performance:")
        for category, metrics in category_performance.iterrows():
            print(f"   • {category}:")
            print(f"     - Avg Views: {metrics['views']:,.0f}")
            print(f"     - Engagement Rate: {metrics['engagement_rate']:.2f}%")
            print(f"     - Watch Time: {metrics['watch_time_ratio']:.1f}%")
        
        # Identify underrepresented categories
        category_counts = df['category'].value_counts()
        underrepresented = category_counts[category_counts == 1].index.tolist()
        
        if underrepresented:
            print(f"\n   Underrepresented Categories (Opportunities):")
            for category in underrepresented:
                print(f"   • {category}: Only 1 content item")
        
        print(f"\n✅ Content analysis completed!")
        
    except Exception as e:
        print(f"❌ Content analysis failed: {str(e)}")
        logger.error(f"Content analysis error: {str(e)}")

def demonstrate_trend_prediction():
    """Demonstrate trend prediction capabilities"""
    print(f"\n📈 Trend Prediction Demonstration")
    print("=" * 50)
    
    try:
        # Simulate trend data over time
        trend_data = [
            {'date': '2024-01-01', 'ai_mentions': 45, 'sustainability_mentions': 12, 'remote_work_mentions': 28},
            {'date': '2024-01-15', 'ai_mentions': 52, 'sustainability_mentions': 18, 'remote_work_mentions': 31},
            {'date': '2024-02-01', 'ai_mentions': 68, 'sustainability_mentions': 25, 'remote_work_mentions': 29},
            {'date': '2024-02-15', 'ai_mentions': 78, 'sustainability_mentions': 32, 'remote_work_mentions': 27},
            {'date': '2024-03-01', 'ai_mentions': 89, 'sustainability_mentions': 41, 'remote_work_mentions': 25},
        ]
        
        df = pd.DataFrame(trend_data)
        df['date'] = pd.to_datetime(df['date'])
        
        print(f"\n1. Trend Growth Analysis:")
        
        # Calculate growth rates
        for column in ['ai_mentions', 'sustainability_mentions', 'remote_work_mentions']:
            initial_value = df[column].iloc[0]
            final_value = df[column].iloc[-1]
            growth_rate = ((final_value - initial_value) / initial_value) * 100
            
            trend_name = column.replace('_mentions', '').replace('_', ' ').title()
            print(f"   • {trend_name}: {growth_rate:.1f}% growth")
            print(f"     - Initial: {initial_value} mentions")
            print(f"     - Current: {final_value} mentions")
            
            # Predict next period
            avg_growth = growth_rate / len(df)
            predicted_next = final_value * (1 + avg_growth/100)
            print(f"     - Predicted Next: {predicted_next:.0f} mentions")
        
        print(f"\n2. Trend Momentum Analysis:")
        
        # Calculate momentum (acceleration)
        for column in ['ai_mentions', 'sustainability_mentions', 'remote_work_mentions']:
            values = df[column].values
            momentum = values[-1] - values[-2] - (values[-2] - values[-3])
            
            trend_name = column.replace('_mentions', '').replace('_', ' ').title()
            momentum_status = "Accelerating" if momentum > 0 else "Decelerating" if momentum < 0 else "Stable"
            print(f"   • {trend_name}: {momentum_status} (momentum: {momentum:+.0f})")
        
        print(f"\n3. Market Opportunity Predictions:")
        
        # Identify emerging opportunities based on trends
        opportunities = [
            {
                'trend': 'AI Integration',
                'confidence': 0.92,
                'time_to_peak': '3-6 months',
                'market_potential': 'Very High',
                'recommended_action': 'Immediate investment in AI content creation'
            },
            {
                'trend': 'Sustainability Focus',
                'confidence': 0.78,
                'time_to_peak': '6-12 months',
                'market_potential': 'High',
                'recommended_action': 'Develop green technology content series'
            },
            {
                'trend': 'Remote Work Evolution',
                'confidence': 0.65,
                'time_to_peak': '12+ months',
                'market_potential': 'Medium',
                'recommended_action': 'Monitor and adapt existing remote work content'
            }
        ]
        
        for opp in opportunities:
            print(f"\n   • {opp['trend']}:")
            print(f"     - Confidence: {opp['confidence']:.0%}")
            print(f"     - Time to Peak: {opp['time_to_peak']}")
            print(f"     - Market Potential: {opp['market_potential']}")
            print(f"     - Recommendation: {opp['recommended_action']}")
        
        print(f"\n✅ Trend prediction analysis completed!")
        
    except Exception as e:
        print(f"❌ Trend prediction failed: {str(e)}")
        logger.error(f"Trend prediction error: {str(e)}")

async def main():
    """Main demo function"""
    print("🚀 Market Opportunity Identification System - Comprehensive Demo")
    print("=" * 80)
    
    try:
        # Run main opportunity identification demo
        results = await demonstrate_opportunity_identification()
        
        # Run additional demonstrations
        demonstrate_content_analysis()
        demonstrate_trend_prediction()
        
        print(f"\n🎉 All demonstrations completed successfully!")
        print(f"\n📋 Next Steps:")
        print(f"   1. Run the Streamlit UI: streamlit run market_opportunity_identification_ui.py")
        print(f"   2. Upload your own content data for analysis")
        print(f"   3. Explore the interactive dashboard and opportunity reports")
        print(f"   4. Use the insights to guide your content strategy")
        
        return results
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        logger.error(f"Main demo error: {str(e)}")
        return None

if __name__ == "__main__":
    # Run the comprehensive demo
    asyncio.run(main())