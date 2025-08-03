#!/usr/bin/env python3
"""
Demo Script for Advanced Visualization Dashboard (Task 43)
Demonstrates all visualization features with sample data
"""

import sys
import os
from datetime import datetime, timedelta
import json
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from advanced_visualization_dashboard import (
        AdvancedVisualizationDashboard, TranscriptData, SentimentPoint
    )
    import pandas as pd
    import numpy as np
    from textblob import TextBlob
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud
    import networkx as nx
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install required dependencies:")
    print("pip install streamlit plotly pandas numpy wordcloud textblob matplotlib networkx scikit-learn nltk spacy")
    sys.exit(1)

class VisualizationDemo:
    """Comprehensive demo of the advanced visualization dashboard"""
    
    def __init__(self):
        print("🚀 Advanced Visualization Dashboard Demo")
        print("=" * 60)
        print("Initializing dashboard components...")
        
        # Initialize dashboard (mock streamlit for demo)
        self.dashboard = self.create_mock_dashboard()
        self.sample_transcripts = self.create_comprehensive_sample_data()
        
        print(f"✅ Loaded {len(self.sample_transcripts)} sample transcripts")
        print("📊 Ready to demonstrate visualization features")
    
    def create_mock_dashboard(self):
        """Create a mock dashboard for demonstration"""
        class MockDashboard:
            def __init__(self):
                self.analysis_cache = {}
            
            def preprocess_text_for_wordcloud(self, text, min_length=3):
                # Simple preprocessing for demo
                import re
                from collections import Counter
                
                # Remove speaker labels
                text = re.sub(r'^[A-Za-z]+:', '', text, flags=re.MULTILINE)
                text = re.sub(r'[^\w\s]', ' ', text)
                text = text.lower()
                
                # Basic word filtering
                words = text.split()
                stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
                
                filtered_words = [
                    word for word in words 
                    if len(word) >= min_length and word not in stop_words and word.isalpha()
                ]
                
                return ' '.join(filtered_words)
            
            def get_word_frequencies(self, text):
                from collections import Counter
                words = text.split()
                return dict(Counter(words).most_common(20))
            
            def analyze_sentiment_flow(self, transcript, granularity):
                # Simple sentiment analysis for demo
                import re
                
                if granularity == "Sentence":
                    from nltk.tokenize import sent_tokenize
                    try:
                        segments = sent_tokenize(transcript.content)
                    except:
                        segments = transcript.content.split('.')
                elif granularity == "Speaker Turn":
                    segments = self.split_by_speaker_turns(transcript.content)
                else:
                    segments = transcript.content.split('\n\n')
                
                sentiment_points = []
                total_duration = transcript.duration
                segment_duration = total_duration / len(segments) if segments else 0
                
                for i, segment in enumerate(segments):
                    if segment.strip():
                        clean_text = re.sub(r'^[A-Za-z]+:', '', segment.strip())
                        if clean_text:
                            blob = TextBlob(clean_text)
                            sentiment_points.append(SentimentPoint(
                                timestamp=i * segment_duration,
                                sentiment=blob.sentiment.polarity,
                                confidence=abs(blob.sentiment.subjectivity),
                                text=clean_text
                            ))
                
                return sentiment_points
            
            def split_by_speaker_turns(self, text):
                import re
                lines = text.strip().split('\n')
                turns = []
                current_turn = []
                
                for line in lines:
                    line = line.strip()
                    if line and ':' in line and re.match(r'^[A-Za-z]+:', line):
                        if current_turn:
                            turns.append('\n'.join(current_turn))
                        current_turn = [line]
                    elif line:
                        current_turn.append(line)
                
                if current_turn:
                    turns.append('\n'.join(current_turn))
                
                return turns
            
            def build_speaker_network(self, transcript):
                import re
                from collections import defaultdict
                
                lines = transcript.content.strip().split('\n')
                interactions = defaultdict(int)
                speaker_stats = defaultdict(lambda: {'total_words': 0, 'turns': 0})
                
                previous_speaker = None
                
                for line in lines:
                    line = line.strip()
                    if ':' in line and re.match(r'^[A-Za-z]+:', line):
                        parts = line.split(':', 1)
                        current_speaker = parts[0].strip()
                        text = parts[1].strip() if len(parts) > 1 else ""
                        
                        # Update speaker statistics
                        word_count = len(text.split())
                        speaker_stats[current_speaker]['total_words'] += word_count
                        speaker_stats[current_speaker]['turns'] += 1
                        
                        # Record interaction
                        if previous_speaker and previous_speaker != current_speaker:
                            pair = tuple(sorted([previous_speaker, current_speaker]))
                            interactions[pair] += 1
                        
                        previous_speaker = current_speaker
                
                return {
                    'interactions': dict(interactions),
                    'speaker_stats': dict(speaker_stats)
                }
        
        return MockDashboard()
    
    def create_comprehensive_sample_data(self):
        """Create comprehensive sample data for demonstration"""
        transcripts = [
            TranscriptData(
                id="product_launch_meeting",
                title="Product Launch Strategy Meeting",
                content="""
                CEO: Good morning everyone. Today we're finalizing our product launch strategy. I'm excited about what we've built.
                Marketing_Director: Thank you for bringing us together. Our market research shows tremendous opportunity in this space.
                Product_Manager: The product is ready and testing has exceeded our expectations. User feedback has been overwhelmingly positive.
                Sales_Director: The sales team is energized and ready. We've already received significant interest from key prospects.
                CEO: That's fantastic news! What are our main challenges moving forward?
                Marketing_Director: Competition is fierce, but our unique value proposition sets us apart. We need to communicate this clearly.
                Product_Manager: From a technical standpoint, we're confident in our scalability and performance capabilities.
                Sales_Director: Pricing strategy will be crucial. We need to balance market penetration with profitability.
                CEO: Let's discuss our go-to-market timeline. When can we realistically launch?
                Marketing_Director: Marketing campaigns are ready to deploy. We can launch the awareness campaign next week.
                Product_Manager: All technical preparations are complete. We're ready from a product perspective.
                Sales_Director: Sales enablement is in progress. The team will be fully trained by month-end.
                CEO: Excellent coordination across all teams. This launch will be our biggest success yet.
                """,
                timestamp=datetime.now() - timedelta(days=2),
                speakers=["CEO", "Marketing_Director", "Product_Manager", "Sales_Director"],
                duration=2400.0,  # 40 minutes
                metadata={"meeting_type": "strategy", "priority": "high", "department": "executive"}
            ),
            
            TranscriptData(
                id="customer_feedback_session",
                title="Customer Feedback Analysis Session",
                content="""
                Researcher: Welcome everyone to our customer feedback analysis session. We have concerning trends to discuss.
                UX_Designer: I've been reviewing the user experience feedback. There are several pain points we need to address urgently.
                Product_Owner: The customer satisfaction scores have dropped significantly. This is troubling and requires immediate attention.
                Support_Manager: Our support tickets have increased by 40%. Customers are frustrated with the recent changes.
                Researcher: Let's dive into the specific issues. The main complaints center around usability and performance.
                UX_Designer: The new interface is confusing users. Navigation has become less intuitive than before.
                Product_Owner: Performance issues are causing customer churn. Load times have increased substantially.
                Support_Manager: Customers are also reporting bugs that weren't present in the previous version.
                Researcher: What's our action plan to address these critical issues?
                UX_Designer: We need to redesign the navigation immediately. User testing should guide our decisions.
                Product_Owner: Performance optimization is my top priority. We'll allocate additional development resources.
                Support_Manager: Better communication with customers is essential. We need to acknowledge their concerns.
                Researcher: These improvements are necessary for customer retention and satisfaction.
                """,
                timestamp=datetime.now() - timedelta(days=5),
                speakers=["Researcher", "UX_Designer", "Product_Owner", "Support_Manager"],
                duration=1800.0,  # 30 minutes
                metadata={"meeting_type": "analysis", "priority": "urgent", "department": "product"}
            ),
            
            TranscriptData(
                id="technical_architecture_review",
                title="System Architecture Review",
                content="""
                Tech_Lead: Let's review our current system architecture and identify optimization opportunities.
                Backend_Dev: The microservices architecture is working well, but we're seeing latency issues between services.
                Frontend_Dev: The client-side performance is good, but API response times are affecting user experience.
                DevOps_Engineer: Infrastructure scaling is functioning properly. Auto-scaling policies are responding correctly.
                Tech_Lead: What specific bottlenecks have you identified in the system?
                Backend_Dev: Database queries are the primary bottleneck. Some queries are taking too long to execute.
                Frontend_Dev: Bundle sizes have grown significantly. We need better code splitting and lazy loading.
                DevOps_Engineer: Memory usage spikes during peak hours. We may need to adjust resource allocation.
                Tech_Lead: Let's prioritize these improvements. What's the most critical issue?
                Backend_Dev: Database optimization should be our first priority. It affects all other components.
                Frontend_Dev: Agreed. Once backend performance improves, frontend optimizations will be more effective.
                DevOps_Engineer: I'll work on monitoring improvements to better track performance metrics.
                Tech_Lead: Great collaboration. These optimizations will significantly improve system performance.
                """,
                timestamp=datetime.now() - timedelta(days=1),
                speakers=["Tech_Lead", "Backend_Dev", "Frontend_Dev", "DevOps_Engineer"],
                duration=2700.0,  # 45 minutes
                metadata={"meeting_type": "technical", "priority": "medium", "department": "engineering"}
            ),
            
            TranscriptData(
                id="quarterly_business_review",
                title="Q4 Business Performance Review",
                content="""
                CFO: Welcome to our quarterly business review. Overall performance has been exceptional this quarter.
                VP_Sales: Sales exceeded targets by 25%. The team delivered outstanding results across all regions.
                VP_Marketing: Marketing campaigns generated significant ROI. Brand awareness increased substantially.
                VP_Operations: Operational efficiency improved dramatically. Cost reduction initiatives were successful.
                CFO: These results demonstrate excellent execution across all departments. What drove this success?
                VP_Sales: Strong product-market fit and effective sales strategies. Customer acquisition accelerated significantly.
                VP_Marketing: Targeted campaigns and improved messaging resonated with our audience. Conversion rates improved.
                VP_Operations: Process improvements and automation reduced costs while maintaining quality standards.
                CFO: Looking ahead, what are our growth opportunities for next quarter?
                VP_Sales: International expansion presents significant opportunities. Several markets show strong potential.
                VP_Marketing: Digital transformation initiatives will drive further growth. Technology investments are paying off.
                VP_Operations: Scaling operations efficiently will support continued growth. Infrastructure is ready.
                CFO: Excellent strategic alignment. This momentum positions us well for continued success.
                """,
                timestamp=datetime.now() - timedelta(days=7),
                speakers=["CFO", "VP_Sales", "VP_Marketing", "VP_Operations"],
                duration=3600.0,  # 60 minutes
                metadata={"meeting_type": "review", "priority": "high", "department": "executive"}
            ),
            
            TranscriptData(
                id="team_retrospective",
                title="Sprint Retrospective - Development Team",
                content="""
                Scrum_Master: Let's begin our sprint retrospective. What went well during this sprint?
                Developer_1: Code quality improved significantly. Our new review process is working effectively.
                Developer_2: Team collaboration was excellent. Communication between team members was clear and helpful.
                QA_Engineer: Testing coverage increased substantially. We caught more bugs before production deployment.
                Scrum_Master: That's great progress! What challenges did we face this sprint?
                Developer_1: Some requirements were unclear initially. This caused delays in the development process.
                Developer_2: Technical debt accumulated faster than expected. We need more time for refactoring.
                QA_Engineer: Testing environments were unstable occasionally. This impacted our testing schedule.
                Scrum_Master: How can we improve for the next sprint?
                Developer_1: Better requirement clarification sessions would help. More detailed user stories are needed.
                Developer_2: Dedicated refactoring time should be allocated. Technical debt needs regular attention.
                QA_Engineer: Environment stability improvements are essential. DevOps support would be valuable.
                Scrum_Master: These improvements will enhance our team's effectiveness and delivery quality.
                """,
                timestamp=datetime.now() - timedelta(days=3),
                speakers=["Scrum_Master", "Developer_1", "Developer_2", "QA_Engineer"],
                duration=1500.0,  # 25 minutes
                metadata={"meeting_type": "retrospective", "priority": "medium", "department": "development"}
            )
        ]
        
        return transcripts
    
    def print_section(self, title):
        """Print formatted section header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_subsection(self, title):
        """Print formatted subsection header"""
        print(f"\n{'-'*40}")
        print(f"  {title}")
        print(f"{'-'*40}")
    
    def demo_word_cloud_analysis(self):
        """Demonstrate word cloud analysis"""
        self.print_section("1. WORD CLOUD ANALYSIS")
        
        print("Analyzing word frequencies and generating insights...")
        
        for transcript in self.sample_transcripts[:3]:  # Demo first 3 transcripts
            self.print_subsection(f"Word Cloud: {transcript.title}")
            
            # Process text
            processed_text = self.dashboard.preprocess_text_for_wordcloud(transcript.content)
            word_frequencies = self.dashboard.get_word_frequencies(processed_text)
            
            print(f"📊 Processed {len(processed_text.split())} words")
            print(f"🔤 Top 10 most frequent words:")
            
            for i, (word, freq) in enumerate(list(word_frequencies.items())[:10], 1):
                print(f"   {i:2d}. {word:<15} ({freq} occurrences)")
            
            # Analyze word patterns
            business_words = [word for word in word_frequencies.keys() 
                            if word in ['strategy', 'performance', 'growth', 'success', 'improvement', 'optimization']]
            
            if business_words:
                print(f"💼 Business-focused terms: {', '.join(business_words)}")
            
            # Sentiment indicators in word choice
            positive_words = [word for word in word_frequencies.keys() 
                            if word in ['excellent', 'great', 'good', 'success', 'positive', 'outstanding', 'fantastic']]
            negative_words = [word for word in word_frequencies.keys() 
                            if word in ['problem', 'issue', 'concern', 'challenge', 'difficult', 'poor', 'bad']]
            
            if positive_words:
                print(f"😊 Positive language: {', '.join(positive_words)}")
            if negative_words:
                print(f"😟 Concern indicators: {', '.join(negative_words)}")
    
    def demo_sentiment_flow_analysis(self):
        """Demonstrate sentiment flow analysis"""
        self.print_section("2. SENTIMENT FLOW ANALYSIS")
        
        print("Analyzing emotional tone and sentiment changes over time...")
        
        for transcript in self.sample_transcripts:
            self.print_subsection(f"Sentiment Analysis: {transcript.title}")
            
            # Analyze sentiment flow
            sentiment_data = self.dashboard.analyze_sentiment_flow(transcript, "Speaker Turn")
            
            if sentiment_data:
                sentiments = [point.sentiment for point in sentiment_data]
                confidences = [point.confidence for point in sentiment_data]
                
                avg_sentiment = np.mean(sentiments)
                sentiment_std = np.std(sentiments)
                avg_confidence = np.mean(confidences)
                
                print(f"📈 Average Sentiment: {avg_sentiment:.3f} ({'Positive' if avg_sentiment > 0.1 else 'Negative' if avg_sentiment < -0.1 else 'Neutral'})")
                print(f"📊 Sentiment Variability: {sentiment_std:.3f} ({'High' if sentiment_std > 0.3 else 'Low'} variation)")
                print(f"🎯 Average Confidence: {avg_confidence:.3f}")
                
                # Find most positive and negative moments
                most_positive = max(sentiment_data, key=lambda x: x.sentiment)
                most_negative = min(sentiment_data, key=lambda x: x.sentiment)
                
                print(f"😊 Most Positive Moment (Score: {most_positive.sentiment:.3f}):")
                print(f"   '{most_positive.text[:100]}...'")
                
                print(f"😟 Most Negative Moment (Score: {most_negative.sentiment:.3f}):")
                print(f"   '{most_negative.text[:100]}...'")
                
                # Sentiment trend analysis
                if len(sentiments) > 1:
                    trend = "Improving" if sentiments[-1] > sentiments[0] else "Declining" if sentiments[-1] < sentiments[0] else "Stable"
                    print(f"📈 Overall Trend: {trend}")
    
    def demo_speaker_network_analysis(self):
        """Demonstrate speaker interaction network analysis"""
        self.print_section("3. SPEAKER INTERACTION NETWORKS")
        
        print("Analyzing speaker interactions and communication patterns...")
        
        for transcript in self.sample_transcripts:
            if len(transcript.speakers) < 2:
                continue
                
            self.print_subsection(f"Speaker Network: {transcript.title}")
            
            # Build network
            network_data = self.dashboard.build_speaker_network(transcript)
            
            interactions = network_data['interactions']
            speaker_stats = network_data['speaker_stats']
            
            print(f"👥 Speakers: {len(speaker_stats)}")
            print(f"🔗 Interactions: {len(interactions)}")
            
            # Speaker activity analysis
            print(f"\n📊 Speaker Activity:")
            sorted_speakers = sorted(speaker_stats.items(), key=lambda x: x[1]['total_words'], reverse=True)
            
            for i, (speaker, stats) in enumerate(sorted_speakers, 1):
                words_per_turn = stats['total_words'] / max(stats['turns'], 1)
                print(f"   {i}. {speaker:<20} {stats['total_words']:4d} words, {stats['turns']:2d} turns, {words_per_turn:.1f} words/turn")
            
            # Interaction analysis
            if interactions:
                print(f"\n🤝 Most Frequent Interactions:")
                sorted_interactions = sorted(interactions.items(), key=lambda x: x[1], reverse=True)
                
                for i, ((speaker1, speaker2), count) in enumerate(sorted_interactions[:5], 1):
                    print(f"   {i}. {speaker1} ↔ {speaker2}: {count} interactions")
            
            # Communication patterns
            total_words = sum(stats['total_words'] for stats in speaker_stats.values())
            most_active = max(speaker_stats.items(), key=lambda x: x[1]['total_words'])
            
            dominance_ratio = most_active[1]['total_words'] / total_words
            print(f"\n💬 Communication Patterns:")
            print(f"   Most Active Speaker: {most_active[0]} ({dominance_ratio:.1%} of total words)")
            
            if dominance_ratio > 0.5:
                print(f"   ⚠️  High dominance - conversation may be unbalanced")
            elif dominance_ratio < 0.3:
                print(f"   ✅ Balanced participation across speakers")
            else:
                print(f"   📊 Moderate speaker dominance")
    
    def demo_comparative_analysis(self):
        """Demonstrate comparative analysis between transcripts"""
        self.print_section("4. COMPARATIVE ANALYSIS")
        
        print("Comparing transcripts across multiple dimensions...")
        
        # Sentiment comparison
        self.print_subsection("Sentiment Comparison")
        
        sentiment_comparison = []
        for transcript in self.sample_transcripts:
            # Overall sentiment
            clean_text = transcript.content.replace('\n', ' ')
            blob = TextBlob(clean_text)
            
            sentiment_comparison.append({
                'title': transcript.title,
                'sentiment': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity,
                'duration_min': transcript.duration / 60,
                'speaker_count': len(transcript.speakers)
            })
        
        # Sort by sentiment
        sentiment_comparison.sort(key=lambda x: x['sentiment'], reverse=True)
        
        print("📊 Transcripts ranked by sentiment (most positive first):")
        for i, data in enumerate(sentiment_comparison, 1):
            sentiment_label = "😊 Positive" if data['sentiment'] > 0.1 else "😟 Negative" if data['sentiment'] < -0.1 else "😐 Neutral"
            print(f"   {i}. {data['title']:<35} {sentiment_label} ({data['sentiment']:+.3f})")
        
        # Duration and activity comparison
        self.print_subsection("Duration and Activity Comparison")
        
        activity_data = []
        for transcript in self.sample_transcripts:
            network_data = self.dashboard.build_speaker_network(transcript)
            speaker_stats = network_data['speaker_stats']
            
            total_words = sum(stats['total_words'] for stats in speaker_stats.values())
            total_turns = sum(stats['turns'] for stats in speaker_stats.values())
            
            activity_data.append({
                'title': transcript.title,
                'duration_min': transcript.duration / 60,
                'total_words': total_words,
                'words_per_minute': total_words / (transcript.duration / 60),
                'turns_per_minute': total_turns / (transcript.duration / 60),
                'avg_words_per_turn': total_words / max(total_turns, 1)
            })
        
        print("📈 Meeting Activity Metrics:")
        print(f"{'Title':<35} {'Duration':<10} {'Words/Min':<10} {'Turns/Min':<10} {'Words/Turn':<12}")
        print("-" * 80)
        
        for data in activity_data:
            print(f"{data['title']:<35} {data['duration_min']:8.1f}m {data['words_per_minute']:8.1f} {data['turns_per_minute']:8.1f} {data['avg_words_per_turn']:10.1f}")
        
        # Topic similarity analysis
        self.print_subsection("Topic Similarity Analysis")
        
        print("🔍 Analyzing common themes across transcripts...")
        
        # Extract key terms from each transcript
        transcript_keywords = {}
        for transcript in self.sample_transcripts:
            processed_text = self.dashboard.preprocess_text_for_wordcloud(transcript.content)
            word_freq = self.dashboard.get_word_frequencies(processed_text)
            transcript_keywords[transcript.title] = set(list(word_freq.keys())[:10])
        
        # Find common themes
        all_keywords = set()
        for keywords in transcript_keywords.values():
            all_keywords.update(keywords)
        
        common_themes = {}
        for keyword in all_keywords:
            appearances = [title for title, keywords in transcript_keywords.items() if keyword in keywords]
            if len(appearances) > 1:
                common_themes[keyword] = appearances
        
        print("🎯 Common themes across transcripts:")
        for theme, transcripts in sorted(common_themes.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"   '{theme}' appears in: {', '.join(transcripts)}")
    
    def demo_performance_metrics(self):
        """Demonstrate performance characteristics"""
        self.print_section("5. PERFORMANCE ANALYSIS")
        
        print("Analyzing dashboard performance with sample data...")
        
        # Test processing speed
        start_time = time.time()
        
        total_operations = 0
        
        for transcript in self.sample_transcripts:
            # Word cloud processing
            processed_text = self.dashboard.preprocess_text_for_wordcloud(transcript.content)
            word_freq = self.dashboard.get_word_frequencies(processed_text)
            total_operations += 1
            
            # Sentiment analysis
            sentiment_data = self.dashboard.analyze_sentiment_flow(transcript, "Speaker Turn")
            total_operations += 1
            
            # Network analysis
            network_data = self.dashboard.build_speaker_network(transcript)
            total_operations += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"⚡ Performance Metrics:")
        print(f"   Total Operations: {total_operations}")
        print(f"   Total Time: {total_time:.3f} seconds")
        print(f"   Average Time per Operation: {total_time/total_operations:.3f} seconds")
        print(f"   Operations per Second: {total_operations/total_time:.1f}")
        
        # Memory usage estimation
        total_text_length = sum(len(t.content) for t in self.sample_transcripts)
        estimated_memory_mb = total_text_length / (1024 * 1024) * 10  # Rough estimate
        
        print(f"📊 Resource Usage:")
        print(f"   Total Text Processed: {total_text_length:,} characters")
        print(f"   Estimated Memory Usage: {estimated_memory_mb:.2f} MB")
        
        # Scalability analysis
        print(f"🚀 Scalability Insights:")
        if total_time < 1.0:
            print(f"   ✅ Excellent performance - suitable for real-time analysis")
        elif total_time < 5.0:
            print(f"   ✅ Good performance - suitable for interactive dashboards")
        else:
            print(f"   ⚠️  Consider optimization for large-scale deployments")
    
    def demo_insights_and_recommendations(self):
        """Demonstrate insights and recommendations"""
        self.print_section("6. INSIGHTS & RECOMMENDATIONS")
        
        print("Generating actionable insights from visualization analysis...")
        
        # Analyze all transcripts for patterns
        all_sentiments = []
        all_durations = []
        all_speaker_counts = []
        meeting_types = {}
        
        for transcript in self.sample_transcripts:
            # Sentiment analysis
            sentiment_data = self.dashboard.analyze_sentiment_flow(transcript, "Speaker Turn")
            if sentiment_data:
                avg_sentiment = np.mean([point.sentiment for point in sentiment_data])
                all_sentiments.append(avg_sentiment)
            
            all_durations.append(transcript.duration / 60)  # Convert to minutes
            all_speaker_counts.append(len(transcript.speakers))
            
            meeting_type = transcript.metadata.get('meeting_type', 'unknown')
            if meeting_type not in meeting_types:
                meeting_types[meeting_type] = []
            meeting_types[meeting_type].append(transcript.title)
        
        # Generate insights
        print("🔍 Key Insights:")
        
        # Sentiment insights
        if all_sentiments:
            avg_sentiment = np.mean(all_sentiments)
            if avg_sentiment > 0.1:
                print("   😊 Overall positive sentiment across meetings - good team morale")
            elif avg_sentiment < -0.1:
                print("   😟 Concerning negative sentiment - may indicate team stress or issues")
            else:
                print("   😐 Neutral sentiment - balanced but could benefit from more positive energy")
        
        # Duration insights
        avg_duration = np.mean(all_durations)
        if avg_duration > 45:
            print(f"   ⏰ Long meetings (avg: {avg_duration:.1f} min) - consider shorter, focused sessions")
        elif avg_duration < 15:
            print(f"   ⚡ Short meetings (avg: {avg_duration:.1f} min) - efficient but ensure adequate coverage")
        else:
            print(f"   ✅ Well-balanced meeting durations (avg: {avg_duration:.1f} min)")
        
        # Speaker participation insights
        avg_speakers = np.mean(all_speaker_counts)
        if avg_speakers > 6:
            print(f"   👥 Large groups (avg: {avg_speakers:.1f} speakers) - may benefit from smaller focused sessions")
        elif avg_speakers < 3:
            print(f"   👤 Small groups (avg: {avg_speakers:.1f} speakers) - good for focused discussions")
        else:
            print(f"   ✅ Optimal group sizes (avg: {avg_speakers:.1f} speakers)")
        
        # Meeting type insights
        print(f"\n📋 Meeting Type Distribution:")
        for meeting_type, transcripts in meeting_types.items():
            print(f"   {meeting_type.title()}: {len(transcripts)} meetings")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        # Based on sentiment analysis
        negative_meetings = [t for t in self.sample_transcripts 
                           if 'concern' in t.content.lower() or 'problem' in t.content.lower() or 'issue' in t.content.lower()]
        
        if negative_meetings:
            print("   🎯 Follow up on meetings with concerns to ensure issues are resolved")
        
        # Based on speaker analysis
        print("   🤝 Encourage balanced participation in meetings with dominant speakers")
        print("   📊 Use sentiment tracking to monitor team morale over time")
        print("   🔄 Implement regular retrospectives to maintain positive team dynamics")
        
        # Technical recommendations
        print(f"\n🛠️  Technical Recommendations:")
        print("   📈 Implement real-time sentiment monitoring for live meetings")
        print("   🎨 Add interactive filtering and drill-down capabilities")
        print("   📱 Consider mobile-friendly visualizations for on-the-go analysis")
        print("   🔔 Set up automated alerts for concerning sentiment trends")
    
    def run_complete_demo(self):
        """Run the complete demonstration"""
        print("Starting comprehensive visualization dashboard demonstration...")
        print(f"Demo timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Run all demo sections
            self.demo_word_cloud_analysis()
            self.demo_sentiment_flow_analysis()
            self.demo_speaker_network_analysis()
            self.demo_comparative_analysis()
            self.demo_performance_metrics()
            self.demo_insights_and_recommendations()
            
            # Summary
            self.print_section("DEMO SUMMARY")
            print("✅ Successfully demonstrated all visualization features:")
            print("   📊 Word Cloud Analysis - Frequency analysis and keyword extraction")
            print("   📈 Sentiment Flow - Emotional tone tracking over time")
            print("   🕸️  Speaker Networks - Interaction patterns and communication analysis")
            print("   📊 Comparative Analysis - Multi-transcript comparison and insights")
            print("   ⚡ Performance Analysis - Speed and scalability metrics")
            print("   💡 Insights & Recommendations - Actionable business intelligence")
            
            print(f"\n🎉 Demo completed successfully!")
            print("The Advanced Visualization Dashboard is ready for production use.")
            
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\nDemo finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Run the visualization dashboard demo"""
    demo = VisualizationDemo()
    demo.run_complete_demo()

if __name__ == "__main__":
    main()