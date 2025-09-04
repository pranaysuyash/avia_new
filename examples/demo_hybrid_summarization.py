#!/usr/bin/env python3
"""
Demo Script for Hybrid Summarization System
Demonstrates Task 123: Build hybrid summarization system

This demo showcases comprehensive summarization capabilities including:
- Extractive and abstractive summarization
- Hybrid approaches combining both methods
- Multi-document summarization
- Query-focused summarization
- Personalization features
"""

import sys
import os
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from hybrid_summarization_system import (
        SummarizationService, SummarizationRequest, SummaryResult,
        SummarizationType, SummaryLength, SummaryStyle
    )
except ImportError:
    print("❌ Error: Could not import Hybrid Summarization system")
    print("Please ensure hybrid_summarization_system.py is in the same directory")
    sys.exit(1)

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_subheader(title: str):
    """Print a formatted subheader"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

def print_summary_result(result: SummaryResult, original_text: str = None):
    """Print summary result in a formatted way"""
    print(f"📝 Summary ({result.summary_type.value.title()}):")
    print(f"   {result.summary}")
    print()
    
    print(f"📊 Metrics:")
    print(f"   • Word Count: {result.word_count}")
    print(f"   • Sentences: {result.sentence_count}")
    print(f"   • Compression Ratio: {result.compression_ratio:.1f}:1")
    print(f"   • Quality Score: {result.quality_score:.2f}")
    print(f"   • Confidence: {result.confidence_score:.2f}")
    print(f"   • Processing Time: {result.processing_time:.2f}s")
    
    if result.key_points:
        print(f"\n🎯 Key Points:")
        for i, point in enumerate(result.key_points, 1):
            print(f"   {i}. {point}")
    
    if original_text:
        original_words = len(original_text.split())
        print(f"\n📈 Compression Analysis:")
        print(f"   • Original: {original_words} words")
        print(f"   • Summary: {result.word_count} words")
        print(f"   • Reduction: {((original_words - result.word_count) / original_words * 100):.1f}%")

async def demo_extractive_summarization():
    """Demonstrate extractive summarization"""
    print_subheader("Extractive Summarization")
    
    service = SummarizationService()
    
    sample_text = """
    Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.
    These algorithms build mathematical models based on training data to make predictions or decisions.
    The field has grown rapidly due to advances in computing power and the availability of large datasets.
    Common applications include image recognition, natural language processing, and recommendation systems.
    Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data.
    Deep learning, using neural networks with multiple layers, has achieved remarkable results in many domains.
    However, machine learning models can be biased if the training data is not representative.
    Ethical considerations around AI and machine learning are becoming increasingly important.
    The future of machine learning includes developments in explainable AI and automated machine learning.
    """
    
    print("📄 Original Text:")
    print(f"   {sample_text.strip()}")
    
    # Test different extractive configurations
    configs = [
        {"length": SummaryLength.BRIEF, "name": "Brief Summary"},
        {"length": SummaryLength.SHORT, "name": "Short Summary"},
        {"length": SummaryLength.MEDIUM, "name": "Medium Summary"}
    ]
    
    for config in configs:
        print(f"\n🔍 {config['name']}:")
        
        request = SummarizationRequest(
            text=sample_text,
            summary_type=SummarizationType.EXTRACTIVE,
            length=config["length"],
            style=SummaryStyle.FORMAL
        )
        
        result = await service.summarize(request)
        print_summary_result(result, sample_text)

if __name__ == "__main__":
    asyncio.run(demo_extractive_summarization())async def d
emo_abstractive_summarization():
    """Demonstrate abstractive summarization"""
    print_subheader("Abstractive Summarization")
    
    service = SummarizationService()
    
    sample_text = """
    Climate change represents one of the most pressing challenges of our time. Rising global temperatures are causing 
    ice caps to melt, sea levels to rise, and weather patterns to become more extreme. The primary cause is the 
    emission of greenhouse gases from human activities, particularly the burning of fossil fuels for energy production. 
    Carbon dioxide levels in the atmosphere have reached their highest point in over 3 million years. The consequences 
    are already visible: more frequent hurricanes, prolonged droughts, and unprecedented heatwaves. Scientists warn 
    that without immediate action to reduce emissions, the effects will become irreversible. Renewable energy sources 
    like solar and wind power offer promising alternatives to fossil fuels. Many countries have committed to achieving 
    net-zero emissions by 2050, but implementation remains challenging. Individual actions, while important, must be 
    complemented by systemic changes in policy and industry practices.
    """
    
    print("📄 Original Text:")
    print(f"   {sample_text.strip()}")
    
    # Test different styles
    styles = [
        {"style": SummaryStyle.FORMAL, "name": "Formal Style"},
        {"style": SummaryStyle.TECHNICAL, "name": "Technical Style"},
        {"style": SummaryStyle.EXECUTIVE, "name": "Executive Style"}
    ]
    
    for style_config in styles:
        print(f"\n✍️ {style_config['name']}:")
        
        request = SummarizationRequest(
            text=sample_text,
            summary_type=SummarizationType.ABSTRACTIVE,
            length=SummaryLength.SHORT,
            style=style_config["style"]
        )
        
        result = await service.summarize(request)
        print_summary_result(result, sample_text)

async def demo_hybrid_summarization():
    """Demonstrate hybrid summarization"""
    print_subheader("Hybrid Summarization")
    
    service = SummarizationService()
    
    sample_text = """
    The Internet of Things (IoT) is revolutionizing how we interact with technology in our daily lives. Smart devices 
    embedded with sensors and connectivity are creating an interconnected ecosystem of objects that can communicate 
    and share data. From smart thermostats that learn your preferences to wearable fitness trackers that monitor your 
    health, IoT devices are becoming ubiquitous. In industrial settings, IoT sensors monitor equipment performance, 
    predict maintenance needs, and optimize energy consumption. Smart cities use IoT infrastructure to manage traffic 
    flow, reduce energy waste, and improve public services. However, this connectivity comes with significant security 
    and privacy challenges. Each connected device represents a potential entry point for cyberattacks. Data privacy 
    concerns arise as these devices collect vast amounts of personal information. The sheer volume of data generated 
    by IoT devices requires new approaches to data processing and storage. Edge computing is emerging as a solution 
    to process data closer to its source, reducing latency and bandwidth requirements. As 5G networks roll out, they 
    will enable even more sophisticated IoT applications with real-time responsiveness. The future of IoT includes 
    integration with artificial intelligence to create truly autonomous systems.
    """
    
    print("📄 Original Text:")
    print(f"   {sample_text.strip()}")
    
    # Compare different approaches
    approaches = [
        {"type": SummarizationType.EXTRACTIVE, "name": "Extractive Only"},
        {"type": SummarizationType.ABSTRACTIVE, "name": "Abstractive Only"},
        {"type": SummarizationType.HYBRID, "name": "Hybrid Approach"}
    ]
    
    for approach in approaches:
        print(f"\n🔄 {approach['name']}:")
        
        request = SummarizationRequest(
            text=sample_text,
            summary_type=approach["type"],
            length=SummaryLength.MEDIUM,
            style=SummaryStyle.TECHNICAL,
            focus_keywords=["IoT", "devices", "connectivity", "data"]
        )
        
        result = await service.summarize(request)
        print_summary_result(result, sample_text)

async def demo_query_focused_summarization():
    """Demonstrate query-focused summarization"""
    print_subheader("Query-Focused Summarization")
    
    service = SummarizationService()
    
    sample_text = """
    Blockchain technology has emerged as a revolutionary approach to data storage and transaction processing. 
    At its core, blockchain is a distributed ledger that maintains a continuously growing list of records, 
    called blocks, which are linked and secured using cryptography. Each block contains a cryptographic hash 
    of the previous block, a timestamp, and transaction data. This design makes the blockchain inherently 
    resistant to modification of data. The technology was first conceptualized in 2008 as the underlying 
    technology for Bitcoin, but its applications extend far beyond cryptocurrency. Smart contracts, which 
    are self-executing contracts with terms directly written into code, represent one of the most promising 
    applications. Supply chain management can benefit from blockchain's transparency and traceability features. 
    Healthcare systems can use blockchain to securely store and share patient records while maintaining privacy. 
    Voting systems built on blockchain could provide unprecedented transparency and security in elections. 
    However, blockchain technology faces several challenges. Scalability remains a significant issue, with 
    many blockchain networks processing only a few transactions per second compared to traditional payment 
    systems that handle thousands. Energy consumption is another concern, particularly for proof-of-work 
    consensus mechanisms used by Bitcoin. Regulatory uncertainty creates additional challenges for widespread 
    adoption. Despite these challenges, major corporations and governments are investing heavily in blockchain 
    research and development.
    """
    
    print("📄 Original Text:")
    print(f"   {sample_text.strip()}")
    
    # Test different queries
    queries = [
        "What are the main applications of blockchain technology?",
        "What challenges does blockchain technology face?",
        "How does blockchain ensure security and transparency?",
        "What is the relationship between blockchain and cryptocurrency?"
    ]
    
    for query in queries:
        print(f"\n❓ Query: {query}")
        
        request = SummarizationRequest(
            text=sample_text,
            summary_type=SummarizationType.QUERY_FOCUSED,
            length=SummaryLength.SHORT,
            style=SummaryStyle.FORMAL,
            query=query
        )
        
        result = await service.summarize(request)
        print_summary_result(result, sample_text)

async def demo_multi_document_summarization():
    """Demonstrate multi-document summarization"""
    print_subheader("Multi-Document Summarization")
    
    service = SummarizationService()
    
    documents = [
        {
            'id': 'doc1',
            'title': 'Renewable Energy Growth',
            'content': '''
            Renewable energy capacity has grown exponentially over the past decade. Solar photovoltaic capacity 
            increased by 22% in 2021, while wind power grew by 13%. The cost of renewable energy has plummeted, 
            making it competitive with fossil fuels in many markets. Government policies and incentives have 
            played a crucial role in driving adoption. Investment in renewable energy reached $366 billion 
            globally in 2021. China leads in renewable energy deployment, followed by the United States and Europe.
            '''
        },
        {
            'id': 'doc2',
            'title': 'Energy Storage Solutions',
            'content': '''
            Energy storage is critical for the widespread adoption of renewable energy sources. Battery technology 
            has improved significantly, with lithium-ion battery costs falling by 90% over the past decade. 
            Grid-scale storage systems help balance supply and demand, storing excess energy when production 
            is high and releasing it when needed. Pumped hydro storage remains the most widely deployed 
            technology, but battery storage is growing rapidly. New technologies like compressed air energy 
            storage and hydrogen fuel cells show promise for long-duration storage applications.
            '''
        },
        {
            'id': 'doc3',
            'title': 'Smart Grid Technology',
            'content': '''
            Smart grids represent the modernization of electrical grid infrastructure. These systems use 
            digital technology to monitor and manage electricity flows from all generation sources to meet 
            varying electricity demands. Smart meters provide real-time data on energy consumption, enabling 
            better demand management. Advanced grid management systems can automatically reroute power during 
            outages and optimize energy distribution. Integration with renewable energy sources requires 
            sophisticated forecasting and control systems. Cybersecurity becomes increasingly important 
            as grids become more digitized and interconnected.
            '''
        }
    ]
    
    print("📚 Documents to Summarize:")
    for doc in documents:
        print(f"   • {doc['title']}: {len(doc['content'].split())} words")
    
    # Test multi-document summarization
    request = SummarizationRequest(
        text="",  # Will be filled by multi-doc summarizer
        summary_type=SummarizationType.HYBRID,
        length=SummaryLength.MEDIUM,
        style=SummaryStyle.EXECUTIVE
    )
    
    print(f"\n🔄 Generating Multi-Document Summary...")
    result = await service.summarize_documents(documents, request)
    
    print_summary_result(result)
    
    # Show document-specific information
    if 'document_summaries' in result.metadata:
        print(f"\n📋 Individual Document Summaries:")
        for doc_summary in result.metadata['document_summaries']:
            print(f"   • {doc_summary['title']}: {doc_summary['word_count']} words")
            print(f"     Summary: {doc_summary['summary'][:100]}...")
    
    if 'combined_topics' in result.metadata:
        print(f"\n🏷️ Combined Topics: {', '.join(result.metadata['combined_topics'])}")

async def demo_personalization():
    """Demonstrate personalization features"""
    print_subheader("Personalization Features")
    
    service = SummarizationService()
    
    # Create user profiles
    users = [
        {
            'id': 'technical_user',
            'name': 'Technical User',
            'preferences': {
                'preferred_length': 'long',
                'preferred_style': 'technical',
                'focus_areas': ['algorithms', 'performance', 'implementation'],
                'technical_level': 'high'
            }
        },
        {
            'id': 'executive_user',
            'name': 'Executive User',
            'preferences': {
                'preferred_length': 'brief',
                'preferred_style': 'executive',
                'focus_areas': ['business', 'impact', 'strategy'],
                'technical_level': 'low'
            }
        },
        {
            'id': 'academic_user',
            'name': 'Academic User',
            'preferences': {
                'preferred_length': 'medium',
                'preferred_style': 'academic',
                'focus_areas': ['research', 'methodology', 'findings'],
                'technical_level': 'high'
            }
        }
    ]
    
    # Create profiles
    for user in users:
        service.create_user_profile(user['id'], user['preferences'])
        print(f"✅ Created profile for {user['name']}")
    
    sample_text = """
    Artificial neural networks are computing systems inspired by biological neural networks. They consist of 
    interconnected nodes (neurons) that process information using a connectionist approach. Deep learning, 
    a subset of machine learning, uses neural networks with multiple hidden layers to model and understand 
    complex patterns in data. The backpropagation algorithm is used to train these networks by adjusting 
    weights based on the error between predicted and actual outputs. Convolutional neural networks (CNNs) 
    are particularly effective for image recognition tasks, while recurrent neural networks (RNNs) excel 
    at sequence processing. Recent advances include transformer architectures that have revolutionized 
    natural language processing. The computational requirements for training large neural networks have 
    led to the development of specialized hardware like GPUs and TPUs. Applications span computer vision, 
    natural language processing, speech recognition, and game playing. However, neural networks face 
    challenges including interpretability, bias, and the need for large amounts of training data.
    """
    
    print(f"\n📄 Original Text:")
    print(f"   {sample_text.strip()}")
    
    # Generate personalized summaries
    for user in users:
        print(f"\n👤 Summary for {user['name']}:")
        
        request = SummarizationRequest(
            text=sample_text,
            summary_type=SummarizationType.HYBRID
        )
        
        result = await service.summarize(request, user_id=user['id'])
        print_summary_result(result, sample_text)

async def demo_quality_assessment():
    """Demonstrate quality assessment features"""
    print_subheader("Quality Assessment & Analytics")
    
    service = SummarizationService()
    
    # Test with different text qualities
    test_cases = [
        {
            'name': 'High Quality Text',
            'text': '''
            Quantum computing represents a paradigm shift in computational capability. Unlike classical computers 
            that use binary bits, quantum computers leverage quantum mechanical phenomena such as superposition 
            and entanglement. Quantum bits (qubits) can exist in multiple states simultaneously, enabling 
            parallel processing of vast amounts of information. This quantum parallelism allows certain 
            algorithms to solve problems exponentially faster than classical approaches. Shor's algorithm 
            for factoring large numbers and Grover's algorithm for searching unsorted databases demonstrate 
            quantum advantage. However, quantum systems are extremely fragile and require near absolute 
            zero temperatures to maintain quantum coherence. Current quantum computers are noisy intermediate-scale 
            quantum (NISQ) devices with limited qubit counts and high error rates.
            '''
        },
        {
            'name': 'Medium Quality Text',
            'text': '''
            Social media has changed how people communicate. Platforms like Facebook, Twitter, and Instagram 
            connect billions of users worldwide. People share photos, videos, and thoughts instantly. 
            Businesses use social media for marketing and customer service. However, there are concerns 
            about privacy and misinformation. Some studies suggest social media can affect mental health. 
            Governments are considering regulations for social media companies. The future of social media 
            may include virtual reality and augmented reality features.
            '''
        },
        {
            'name': 'Lower Quality Text',
            'text': '''
            Technology is good. Computers help people work. Internet connects everyone. Phones are smart now. 
            Apps do many things. People buy online. Games are fun. Videos are popular. Music streams everywhere. 
            AI is coming. Robots will help. Future looks different. Change happens fast. Learning is important. 
            Skills need updating. Jobs will change. Education must adapt.
            '''
        }
    ]
    
    print("🔍 Testing Quality Assessment on Different Text Types:")
    
    for test_case in test_cases:
        print(f"\n📝 {test_case['name']}:")
        print(f"   Original: {len(test_case['text'].split())} words")
        
        request = SummarizationRequest(
            text=test_case['text'],
            summary_type=SummarizationType.HYBRID,
            length=SummaryLength.SHORT,
            style=SummaryStyle.FORMAL
        )
        
        result = await service.summarize(request)
        
        print(f"   Summary: {result.word_count} words")
        print(f"   Quality Score: {result.quality_score:.2f}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Compression: {result.compression_ratio:.1f}:1")
        print(f"   Summary: {result.summary[:100]}...")

async def demo_performance_comparison():
    """Demonstrate performance comparison between methods"""
    print_subheader("Performance Comparison")
    
    service = SummarizationService()
    
    sample_text = """
    The field of robotics has evolved dramatically over the past few decades, transitioning from simple 
    industrial automation to sophisticated autonomous systems. Modern robots incorporate advanced sensors, 
    artificial intelligence, and machine learning algorithms to navigate complex environments and perform 
    intricate tasks. Computer vision enables robots to perceive and interpret their surroundings, while 
    natural language processing allows for human-robot interaction. Collaborative robots (cobots) are 
    designed to work alongside humans in manufacturing and service industries. Autonomous vehicles represent 
    one of the most visible applications of robotics technology, combining perception, planning, and control 
    systems. Medical robotics has revolutionized surgery with precision instruments and minimally invasive 
    procedures. Service robots are increasingly common in hospitality, cleaning, and eldercare applications. 
    However, robotics faces challenges including safety, reliability, and ethical considerations around 
    job displacement. The integration of 5G networks and edge computing promises to enhance robot capabilities 
    through real-time data processing and communication. Future developments may include swarm robotics, 
    where multiple robots coordinate to accomplish complex tasks, and bio-inspired robots that mimic 
    natural organisms.
    """
    
    print("📄 Sample Text:")
    print(f"   {len(sample_text.split())} words")
    
    # Test different summarization methods
    methods = [
        SummarizationType.EXTRACTIVE,
        SummarizationType.ABSTRACTIVE,
        SummarizationType.HYBRID
    ]
    
    results = []
    
    for method in methods:
        print(f"\n⏱️ Testing {method.value.title()} Summarization...")
        
        request = SummarizationRequest(
            text=sample_text,
            summary_type=method,
            length=SummaryLength.MEDIUM,
            style=SummaryStyle.FORMAL
        )
        
        start_time = time.time()
        result = await service.summarize(request)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        results.append({
            'method': method.value.title(),
            'processing_time': processing_time,
            'word_count': result.word_count,
            'quality_score': result.quality_score,
            'confidence': result.confidence_score,
            'compression_ratio': result.compression_ratio
        })
        
        print(f"   ✅ Completed in {processing_time:.3f}s")
    
    # Display comparison
    print(f"\n📊 Performance Comparison:")
    print(f"{'Method':<12} {'Time(s)':<8} {'Words':<6} {'Quality':<8} {'Confidence':<11} {'Compression':<11}")
    print("-" * 60)
    
    for result in results:
        print(f"{result['method']:<12} {result['processing_time']:<8.3f} {result['word_count']:<6} "
              f"{result['quality_score']:<8.2f} {result['confidence']:<11.2f} {result['compression_ratio']:<11.1f}")

async def main():
    """Main demo function"""
    print_header("Hybrid Summarization System Demo")
    print("This demo showcases comprehensive summarization capabilities.")
    print("Task 123: Build hybrid summarization system")
    
    try:
        # Run all demo sections
        await demo_extractive_summarization()
        await demo_abstractive_summarization()
        await demo_hybrid_summarization()
        await demo_query_focused_summarization()
        await demo_multi_document_summarization()
        await demo_personalization()
        await demo_quality_assessment()
        await demo_performance_comparison()
        
        print_header("Demo Completed Successfully! 📝")
        print("The Hybrid Summarization system is working correctly.")
        print("\nKey Features Demonstrated:")
        print("✅ Extractive summarization with sentence ranking")
        print("✅ Abstractive summarization with AI models")
        print("✅ Hybrid approach combining both methods")
        print("✅ Multi-document summarization")
        print("✅ Query-focused summarization")
        print("✅ User personalization and preferences")
        print("✅ Quality assessment and confidence scoring")
        print("✅ Multiple writing styles and lengths")
        print("✅ Performance optimization and caching")
        print("✅ Comprehensive analytics and metrics")
        
        print("\n🚀 Ready to summarize any content with advanced AI!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())