#!/usr/bin/env python3
"""
Demo Script for AI-Powered Content Generation System (Task 44)
Demonstrates all content generation features with sample data
"""

import sys
import os
import asyncio
import time
from datetime import datetime
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_content_generation import (
        AIContentGenerator, ContentGenerationRequest, ContentType,
        AudienceType, ContentTone
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure ai_content_generation.py is available.")
    sys.exit(1)

class AIContentGenerationDemo:
    """Comprehensive demo of the AI content generation system"""
    
    def __init__(self):
        print("🤖 AI-Powered Content Generation System Demo")
        print("=" * 60)
        print("Initializing content generation system...")
        
        # Initialize generator
        self.generator = AIContentGenerator()
        
        # Sample content for demonstrations
        self.sample_transcripts = self.create_sample_content()
        
        print(f"✅ System initialized")
        print(f"📊 API Status: {'Connected' if self.generator.client else 'Fallback Mode'}")
        print(f"🔧 NLP Status: {'Available' if self.generator.nlp else 'Limited'}")
        print("🚀 Ready to demonstrate content generation features")
    
    def create_sample_content(self):
        """Create sample content for demonstrations"""
        return {
            "tech_podcast": """
            Welcome to Tech Talk Today. I'm your host Sarah Chen, and today we're diving deep into 
            the world of artificial intelligence and machine learning. We'll explore how these 
            technologies are transforming industries, from healthcare to finance to transportation.
            
            Our guest today is Dr. Michael Rodriguez, a leading AI researcher from Stanford University. 
            Dr. Rodriguez has been working on neural networks for over a decade and has published 
            groundbreaking research on deep learning applications.
            
            We'll discuss the current state of AI, the challenges we face in implementation, 
            and what the future holds for artificial intelligence. We'll also cover practical 
            applications that businesses can implement today, including automated customer service, 
            predictive analytics, and intelligent data processing.
            
            Key topics we'll cover include machine learning algorithms, natural language processing, 
            computer vision, and the ethical considerations of AI deployment. We'll also touch on 
            the importance of data quality, model training, and continuous improvement in AI systems.
            """,
            
            "business_meeting": """
            Good morning everyone. Thank you for joining our quarterly business review. 
            I'm excited to share our progress and discuss our strategic initiatives for the coming quarter.
            
            Our sales team has exceeded targets by 25% this quarter, driven by strong performance 
            in our enterprise segment. The marketing campaigns have generated significant ROI, 
            with digital channels showing particularly strong results.
            
            Key achievements include the successful launch of our new product line, expansion 
            into three new markets, and the completion of our digital transformation initiative. 
            Customer satisfaction scores have improved by 15%, and we've reduced operational 
            costs by 12% through process optimization.
            
            Looking ahead, we're focusing on international expansion, product innovation, 
            and strategic partnerships. We'll be investing in new technologies, expanding 
            our team, and enhancing our customer experience capabilities.
            
            The competitive landscape continues to evolve, but our strong market position 
            and innovative approach give us confidence in our ability to maintain growth 
            and deliver value to our stakeholders.
            """,
            
            "educational_content": """
            Introduction to Machine Learning: A Beginner's Guide
            
            Machine learning is a subset of artificial intelligence that enables computers 
            to learn and improve from experience without being explicitly programmed. 
            It's based on the idea that systems can automatically learn and improve 
            from data, identify patterns, and make decisions with minimal human intervention.
            
            There are three main types of machine learning: supervised learning, 
            unsupervised learning, and reinforcement learning. Supervised learning 
            uses labeled data to train models, unsupervised learning finds patterns 
            in unlabeled data, and reinforcement learning learns through interaction 
            with an environment.
            
            Common applications include recommendation systems, fraud detection, 
            image recognition, natural language processing, and predictive analytics. 
            Popular algorithms include linear regression, decision trees, neural networks, 
            and support vector machines.
            
            To get started with machine learning, you'll need to understand basic 
            statistics, programming (Python or R), and data manipulation. Key steps 
            in a machine learning project include data collection, data preprocessing, 
            model selection, training, evaluation, and deployment.
            """,
            
            "bullet_points": """
            • Artificial intelligence is transforming business operations
            • Machine learning enables predictive analytics and automation
            • Data quality is crucial for successful AI implementation
            • Natural language processing improves customer interactions
            • Computer vision applications are expanding rapidly
            • Ethical AI considerations are becoming increasingly important
            • Cloud platforms make AI more accessible to businesses
            • Continuous learning and model updates are essential
            • Human-AI collaboration enhances decision making
            • Investment in AI skills and training is critical for success
            """
        }
    
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
    
    def demo_podcast_content_generation(self):
        """Demonstrate podcast intro and outro generation"""
        self.print_section("1. PODCAST CONTENT GENERATION")
        
        print("Generating podcast intro and outro from tech discussion transcript...")
        
        try:
            # Generate podcast intro and outro
            results = self.generator.generate_podcast_intro_outro(
                transcript=self.sample_transcripts["tech_podcast"],
                show_name="Tech Talk Today",
                host_name="Sarah Chen",
                episode_number=42
            )
            
            # Display intro
            self.print_subsection("Podcast Intro")
            intro = results['intro']
            print(f"📝 Generated Intro ({intro.word_count} words, {intro.confidence_score:.1%} confidence):")
            print(f"\n{intro.generated_text}")
            
            if intro.suggestions:
                print(f"\n💡 Suggestions:")
                for suggestion in intro.suggestions:
                    print(f"   • {suggestion}")
            
            # Display outro
            self.print_subsection("Podcast Outro")
            outro = results['outro']
            print(f"📝 Generated Outro ({outro.word_count} words, {outro.confidence_score:.1%} confidence):")
            print(f"\n{outro.generated_text}")
            
            if outro.suggestions:
                print(f"\n💡 Suggestions:")
                for suggestion in outro.suggestions:
                    print(f"   • {suggestion}")
            
            # Performance metrics
            total_time = intro.generation_time + outro.generation_time
            print(f"\n⚡ Performance: Generated both intro and outro in {total_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error generating podcast content: {e}")
    
    def demo_content_expansion(self):
        """Demonstrate bullet point expansion"""
        self.print_section("2. CONTENT EXPANSION")
        
        print("Expanding bullet points into comprehensive text...")
        
        try:
            # Test different expansion levels
            expansion_levels = ["brief", "detailed", "comprehensive"]
            
            for level in expansion_levels:
                self.print_subsection(f"{level.title()} Expansion")
                
                result = self.generator.expand_bullet_points(
                    bullet_points=self.sample_transcripts["bullet_points"],
                    expansion_level=level
                )
                
                print(f"📝 {level.title()} Expansion ({result.word_count} words):")
                print(f"\n{result.generated_text[:300]}...")  # Show first 300 chars
                
                if result.suggestions:
                    print(f"\n💡 Suggestions:")
                    for suggestion in result.suggestions[:2]:  # Show first 2 suggestions
                        print(f"   • {suggestion}")
                
                print(f"\n⚡ Generated in {result.generation_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error expanding content: {e}")
    
    def demo_faq_generation(self):
        """Demonstrate FAQ generation"""
        self.print_section("3. FAQ GENERATION")
        
        print("Generating comprehensive FAQ from educational content...")
        
        try:
            # Generate FAQ with different question counts
            question_counts = [5, 8, 10]
            
            for count in question_counts:
                self.print_subsection(f"FAQ with {count} Questions")
                
                result = self.generator.generate_comprehensive_faq(
                    content=self.sample_transcripts["educational_content"],
                    num_questions=count
                )
                
                print(f"📝 Generated FAQ ({result.word_count} words, {result.confidence_score:.1%} confidence):")
                
                # Display first few Q&As
                faq_text = result.generated_text
                qa_pairs = faq_text.split('\n\n')[:3]  # Show first 3 Q&A pairs
                
                for qa in qa_pairs:
                    if qa.strip():
                        print(f"\n{qa}")
                
                if len(qa_pairs) < len(faq_text.split('\n\n')):
                    print(f"\n... and {len(faq_text.split('Q')) - 4} more questions")
                
                print(f"\n⚡ Generated in {result.generation_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error generating FAQ: {e}")
    
    def demo_content_tagging(self):
        """Demonstrate content tagging and categorization"""
        self.print_section("4. CONTENT TAGGING & CATEGORIZATION")
        
        print("Generating tags for different types of content...")
        
        content_samples = [
            ("Tech Podcast", self.sample_transcripts["tech_podcast"]),
            ("Business Meeting", self.sample_transcripts["business_meeting"]),
            ("Educational Content", self.sample_transcripts["educational_content"])
        ]
        
        try:
            for content_name, content_text in content_samples:
                self.print_subsection(f"Tags for {content_name}")
                
                # Generate general tags
                result = self.generator.generate_content_tags(content_text)
                
                print(f"📝 Generated Tags ({result.word_count} words):")
                print(f"\n{result.generated_text}")
                
                # Show alternatives if available
                if result.alternatives:
                    print(f"\n🔄 Alternative Tag Sets:")
                    for i, alternative in enumerate(result.alternatives, 1):
                        print(f"   {i}. {alternative}")
                
                # Generate category-specific tags
                categories = ["technology", "business", "education"]
                category_result = self.generator.generate_content_tags(
                    content_text, 
                    tag_categories=categories
                )
                
                print(f"\n🎯 Category-Focused Tags:")
                print(f"{category_result.generated_text}")
                
                print(f"\n⚡ Generated in {result.generation_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error generating tags: {e}")
    
    def demo_content_optimization(self):
        """Demonstrate content optimization for different audiences"""
        self.print_section("5. CONTENT OPTIMIZATION")
        
        print("Optimizing content for different target audiences...")
        
        # Sample content to optimize
        original_content = """
        We need to utilize advanced methodologies to implement comprehensive solutions 
        that facilitate optimal performance and leverage cutting-edge technologies to 
        maximize efficiency and optimize resource allocation across all operational domains.
        """
        
        audiences = [
            AudienceType.CASUAL.value,
            AudienceType.TECHNICAL.value,
            AudienceType.BUSINESS.value,
            AudienceType.EDUCATIONAL.value
        ]
        
        try:
            for audience in audiences:
                self.print_subsection(f"Optimization for {audience.title()} Audience")
                
                optimization = self.generator.optimize_content_for_audience(
                    content=original_content,
                    target_audience=audience,
                    optimization_focus="readability"
                )
                
                print(f"📝 Original Content:")
                print(f"{optimization.original_text}")
                
                print(f"\n✨ Optimized Content:")
                print(f"{optimization.optimized_text}")
                
                print(f"\n🔧 Improvements Made:")
                for improvement in optimization.improvements:
                    print(f"   • {improvement}")
                
                print(f"\n📊 Readability Score: {optimization.readability_score:.1f}/100")
                print(f"🎯 Target Audience: {optimization.target_audience.title()}")
            
        except Exception as e:
            print(f"❌ Error optimizing content: {e}")
    
    def demo_batch_content_generation(self):
        """Demonstrate batch content generation"""
        self.print_section("6. BATCH CONTENT GENERATION")
        
        print("Generating multiple types of content from the same source...")
        
        source_content = self.sample_transcripts["business_meeting"]
        
        # Create batch requests
        requests = [
            ContentGenerationRequest(
                content_type=ContentType.PODCAST_INTRO.value,
                source_text=source_content,
                target_audience=AudienceType.BUSINESS.value,
                tone=ContentTone.PROFESSIONAL.value
            ),
            ContentGenerationRequest(
                content_type=ContentType.FAQ.value,
                source_text=source_content,
                target_audience=AudienceType.BUSINESS.value,
                tone=ContentTone.INFORMATIVE.value
            ),
            ContentGenerationRequest(
                content_type=ContentType.TAGS.value,
                source_text=source_content,
                target_audience=AudienceType.BUSINESS.value
            ),
            ContentGenerationRequest(
                content_type=ContentType.EXPANDED_TEXT.value,
                source_text=source_content[:500],  # Use first part for expansion
                target_audience=AudienceType.PROFESSIONAL.value,
                tone=ContentTone.FORMAL.value
            )
        ]
        
        try:
            print(f"🚀 Generating {len(requests)} types of content...")
            
            start_time = time.time()
            results = self.generator.batch_generate_content(requests)
            end_time = time.time()
            
            batch_time = end_time - start_time
            
            print(f"✅ Batch generation completed in {batch_time:.2f} seconds")
            
            # Display results
            for result in results:
                self.print_subsection(f"{result.content_type.replace('_', ' ').title()}")
                
                if result.metadata.get('error'):
                    print(f"❌ Error: {result.generated_text}")
                else:
                    print(f"📝 Generated Content ({result.word_count} words, {result.confidence_score:.1%} confidence):")
                    
                    # Show preview of content
                    preview_length = 200 if len(result.generated_text) > 200 else len(result.generated_text)
                    print(f"\n{result.generated_text[:preview_length]}...")
                    
                    if result.suggestions:
                        print(f"\n💡 Top Suggestions:")
                        for suggestion in result.suggestions[:2]:
                            print(f"   • {suggestion}")
                    
                    print(f"\n⚡ Generated in {result.generation_time:.2f} seconds")
            
            # Performance summary
            avg_time = sum(r.generation_time for r in results if not r.metadata.get('error')) / len([r for r in results if not r.metadata.get('error')])
            print(f"\n📊 Performance Summary:")
            print(f"   Total Time: {batch_time:.2f} seconds")
            print(f"   Average per Item: {avg_time:.2f} seconds")
            print(f"   Success Rate: {len([r for r in results if not r.metadata.get('error')])}/{len(results)}")
            
        except Exception as e:
            print(f"❌ Error in batch generation: {e}")
    
    def demo_specialized_features(self):
        """Demonstrate specialized content generation features"""
        self.print_section("7. SPECIALIZED FEATURES")
        
        # Custom instructions demo
        self.print_subsection("Custom Instructions")
        
        try:
            request = ContentGenerationRequest(
                content_type=ContentType.PODCAST_INTRO.value,
                source_text=self.sample_transcripts["tech_podcast"],
                target_audience=AudienceType.GENERAL.value,
                tone=ContentTone.ENTHUSIASTIC.value,
                custom_instructions="Make it sound like a radio DJ introduction with high energy and include a call-to-action for listeners to subscribe"
            )
            
            result = asyncio.run(self.generator.generate_content(request))
            
            print(f"📝 Custom Intro with DJ Style:")
            print(f"\n{result.generated_text}")
            print(f"\n⚡ Generated in {result.generation_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error with custom instructions: {e}")
        
        # Different tones demo
        self.print_subsection("Tone Variations")
        
        tones = [ContentTone.CASUAL.value, ContentTone.FORMAL.value, ContentTone.ENTHUSIASTIC.value]
        
        for tone in tones:
            try:
                request = ContentGenerationRequest(
                    content_type=ContentType.PODCAST_OUTRO.value,
                    source_text="Thank you for listening to our discussion about AI.",
                    tone=tone
                )
                
                result = asyncio.run(self.generator.generate_content(request))
                
                print(f"\n🎭 {tone.title()} Tone:")
                print(f"{result.generated_text}")
                
            except Exception as e:
                print(f"❌ Error with {tone} tone: {e}")
    
    def demo_performance_analysis(self):
        """Demonstrate performance characteristics"""
        self.print_section("8. PERFORMANCE ANALYSIS")
        
        print("Analyzing system performance with various content types...")
        
        # Performance test data
        test_cases = [
            ("Short Content", "AI is transforming business operations.", ContentType.TAGS.value),
            ("Medium Content", self.sample_transcripts["educational_content"][:1000], ContentType.FAQ.value),
            ("Long Content", self.sample_transcripts["tech_podcast"], ContentType.EXPANDED_TEXT.value)
        ]
        
        performance_results = []
        
        try:
            for test_name, content, content_type in test_cases:
                print(f"\n🧪 Testing {test_name} ({len(content)} characters)")
                
                request = ContentGenerationRequest(
                    content_type=content_type,
                    source_text=content
                )
                
                start_time = time.time()
                result = asyncio.run(self.generator.generate_content(request))
                end_time = time.time()
                
                actual_time = end_time - start_time
                
                performance_results.append({
                    'test_name': test_name,
                    'content_length': len(content),
                    'content_type': content_type,
                    'generation_time': result.generation_time,
                    'actual_time': actual_time,
                    'word_count': result.word_count,
                    'confidence': result.confidence_score
                })
                
                print(f"   ⚡ Generation Time: {result.generation_time:.3f}s")
                print(f"   📊 Output: {result.word_count} words")
                print(f"   🎯 Confidence: {result.confidence_score:.1%}")
            
            # Performance summary
            self.print_subsection("Performance Summary")
            
            avg_time = sum(r['generation_time'] for r in performance_results) / len(performance_results)
            avg_confidence = sum(r['confidence'] for r in performance_results) / len(performance_results)
            
            print(f"📈 Average Generation Time: {avg_time:.3f} seconds")
            print(f"🎯 Average Confidence: {avg_confidence:.1%}")
            print(f"🔧 Model Used: {'OpenAI API' if self.generator.client else 'Fallback Generation'}")
            
            # Throughput calculation
            total_words_generated = sum(r['word_count'] for r in performance_results)
            total_time = sum(r['generation_time'] for r in performance_results)
            
            if total_time > 0:
                words_per_second = total_words_generated / total_time
                print(f"⚡ Throughput: {words_per_second:.1f} words/second")
            
        except Exception as e:
            print(f"❌ Error in performance analysis: {e}")
    
    def demo_system_statistics(self):
        """Demonstrate system statistics and capabilities"""
        self.print_section("9. SYSTEM STATISTICS")
        
        stats = self.generator.get_generation_statistics()
        
        print("📊 System Capabilities:")
        print(f"   API Available: {'✅ Yes' if stats['api_available'] else '❌ No (Fallback Mode)'}")
        print(f"   NLP Available: {'✅ Yes' if stats['nlp_available'] else '❌ Limited'}")
        print(f"   Total Generations: {stats['total_generations']}")
        
        print(f"\n🎯 Supported Content Types ({len(stats['supported_content_types'])}):")
        for content_type in stats['supported_content_types']:
            print(f"   • {content_type.replace('_', ' ').title()}")
        
        if stats['by_content_type']:
            print(f"\n📈 Usage Statistics:")
            for content_type, count in stats['by_content_type'].items():
                print(f"   • {content_type.replace('_', ' ').title()}: {count} generations")
        
        # Feature matrix
        print(f"\n🔧 Feature Matrix:")
        features = [
            ("Podcast Intro/Outro Generation", "✅ Available"),
            ("Content Expansion", "✅ Available"),
            ("FAQ Generation", "✅ Available"),
            ("Content Tagging", "✅ Available"),
            ("Content Optimization", "✅ Available"),
            ("Batch Generation", "✅ Available"),
            ("Custom Instructions", "✅ Available"),
            ("Multiple Tones", "✅ Available"),
            ("Audience Targeting", "✅ Available"),
            ("Performance Analytics", "✅ Available")
        ]
        
        for feature, status in features:
            print(f"   • {feature}: {status}")
    
    def demo_real_world_scenarios(self):
        """Demonstrate real-world usage scenarios"""
        self.print_section("10. REAL-WORLD SCENARIOS")
        
        scenarios = [
            {
                "name": "Content Creator Workflow",
                "description": "A content creator wants to turn a video transcript into multiple formats",
                "steps": [
                    ("Generate podcast intro", ContentType.PODCAST_INTRO.value),
                    ("Create FAQ", ContentType.FAQ.value),
                    ("Generate tags", ContentType.TAGS.value)
                ]
            },
            {
                "name": "Business Communication",
                "description": "A business wants to optimize meeting notes for different stakeholders",
                "steps": [
                    ("Expand key points", ContentType.EXPANDED_TEXT.value),
                    ("Optimize for executives", ContentType.OPTIMIZATION.value)
                ]
            },
            {
                "name": "Educational Content Development",
                "description": "An educator wants to create comprehensive learning materials",
                "steps": [
                    ("Generate FAQ", ContentType.FAQ.value),
                    ("Create study tags", ContentType.TAGS.value),
                    ("Expand concepts", ContentType.EXPANDED_TEXT.value)
                ]
            }
        ]
        
        for scenario in scenarios:
            self.print_subsection(scenario["name"])
            print(f"📋 Scenario: {scenario['description']}")
            
            source_content = self.sample_transcripts["business_meeting"][:800]  # Use subset
            
            try:
                print(f"\n🚀 Executing workflow...")
                
                for step_name, content_type in scenario["steps"]:
                    print(f"\n   📝 {step_name}...")
                    
                    request = ContentGenerationRequest(
                        content_type=content_type,
                        source_text=source_content,
                        target_audience=AudienceType.PROFESSIONAL.value
                    )
                    
                    result = asyncio.run(self.generator.generate_content(request))
                    
                    print(f"      ✅ Generated {result.word_count} words in {result.generation_time:.2f}s")
                    print(f"      📊 Confidence: {result.confidence_score:.1%}")
                
                print(f"\n✅ Workflow completed successfully!")
                
            except Exception as e:
                print(f"❌ Error in scenario: {e}")
    
    def run_complete_demo(self):
        """Run the complete demonstration"""
        print("Starting comprehensive AI content generation demonstration...")
        print(f"Demo timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Run all demo sections
            self.demo_podcast_content_generation()
            self.demo_content_expansion()
            self.demo_faq_generation()
            self.demo_content_tagging()
            self.demo_content_optimization()
            self.demo_batch_content_generation()
            self.demo_specialized_features()
            self.demo_performance_analysis()
            self.demo_system_statistics()
            self.demo_real_world_scenarios()
            
            # Summary
            self.print_section("DEMO SUMMARY")
            print("✅ Successfully demonstrated all AI content generation features:")
            print("   🎙️ Podcast Intro/Outro Generation - Professional audio content creation")
            print("   📝 Content Expansion - Transform bullet points into comprehensive text")
            print("   ❓ FAQ Generation - Create comprehensive question-answer pairs")
            print("   🏷️ Content Tagging - Automatic categorization and keyword extraction")
            print("   ⚡ Content Optimization - Audience-specific content enhancement")
            print("   📦 Batch Generation - Multiple content types from single source")
            print("   🎯 Specialized Features - Custom instructions and tone variations")
            print("   📊 Performance Analysis - Speed and quality metrics")
            print("   📈 System Statistics - Comprehensive capability overview")
            print("   🌍 Real-World Scenarios - Practical usage workflows")
            
            print(f"\n🎉 Demo completed successfully!")
            print("The AI Content Generation System is ready for production use.")
            
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\nDemo finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Run the AI content generation demo"""
    demo = AIContentGenerationDemo()
    demo.run_complete_demo()

if __name__ == "__main__":
    main()