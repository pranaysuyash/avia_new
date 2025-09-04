#!/usr/bin/env python3
"""
Demo script for Advanced NER functionality using API
Tests the GPT-powered entity extraction via API endpoints
"""

import os
from dotenv import load_dotenv
from api_client import get_api_client
from api_wrappers import ner_advanced

# Load environment variables
load_dotenv()

def demo_entity_extraction():
    """Demo advanced entity extraction via API"""
    print("=== Advanced Entity Extraction Demo (API) ===")
    
    sample_text = """
    Yesterday, CEO Sarah Johnson announced that TechCorp has secured a $50 million 
    investment from Goldman Sachs. The funding will be used to expand operations 
    in San Francisco and hire 200 new engineers by Q2 2024. The company, founded 
    in 2019, has grown from 10 to 500 employees and now serves over 10,000 customers 
    worldwide. "This investment validates our AI-first approach," said Johnson during 
    the press conference at the company's headquarters.
    """
    
    try:
        # Use advanced NER with options
        result = ner_advanced.extract_entities_advanced(
            sample_text,
            options={
                'group_by_type': True,
                'include_confidence': True,
                'extract_relationships': True
            }
        )
        
        print(f"Total entities found: {len(result.get('entities', []))}\n")
        
        # Display grouped entities
        if 'grouped' in result:
            for category, items in result['grouped'].items():
                if items:
                    print(f"{category}:")
                    for item in items:
                        confidence = f" ({item.get('confidence', 1.0):.2f})" if 'confidence' in item else ""
                        print(f"  - {item['text']}{confidence}")
                    print()
        
        # Show summary if available
        if 'summary' in result:
            print(f"Summary: {result['summary']['total']} entities across {result['summary']['types']} types")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nTip: Make sure the API server is running and configured properly.")

def demo_direct_api_calls():
    """Demo direct API calls for advanced features"""
    print("\n=== Direct API Calls Demo ===")
    
    api_client = get_api_client()
    
    test_texts = [
        "Apple Inc. released the iPhone 15 with new features designed by Tim Cook's team.",
        "The meeting between President Biden and Prime Minister Trudeau will be held in Washington D.C.",
        "Microsoft Azure and Amazon AWS compete in the cloud computing market worth $500 billion."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nText {i}: {text[:60]}...")
        
        try:
            # Direct API call with advanced options
            response = api_client.extract_entities(
                text,
                entity_types=["PERSON", "ORG", "PRODUCT", "MONEY"]
            )
            
            if response.get('success'):
                entities = response.get('entities', [])
                print(f"Found {len(entities)} entities:")
                for entity in entities[:5]:  # Show first 5
                    print(f"  - {entity['text']} ({entity['type']})")
                    
                # Show processing metadata
                if response.get('processing_time'):
                    print(f"Processing time: {response['processing_time']:.3f}s")
            else:
                print(f"API Error: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Request failed: {e}")

def demo_batch_processing():
    """Demo batch entity extraction"""
    print("\n=== Batch Processing Demo ===")
    
    api_client = get_api_client()
    
    batch_texts = [
        "Google announced a new AI model at their Mountain View headquarters.",
        "Tesla's stock price rose to $250 after Elon Musk's announcement.",
        "Amazon Prime Day sales exceeded $12 billion this year.",
        "Meta launched new VR headsets priced at $499.",
        "Netflix added 5 million subscribers in Q3 2024."
    ]
    
    print(f"Processing {len(batch_texts)} texts in batch mode...")
    
    try:
        # This would be a batch endpoint in the API
        # For now, demonstrate the concept
        results = []
        for text in batch_texts:
            result = ner_advanced.extract_entities_advanced(
                text,
                options={'group_by_type': False}
            )
            results.append({
                'text': text[:50] + '...',
                'entity_count': len(result.get('entities', []))
            })
        
        print("\nBatch Results:")
        for result in results:
            print(f"  - {result['text']}: {result['entity_count']} entities")
            
    except Exception as e:
        print(f"Batch processing error: {e}")

def demo_entity_analysis():
    """Demo entity distribution analysis"""
    print("\n=== Entity Analysis Demo ===")
    
    api_client = get_api_client()
    
    analysis_text = """
    In 2024, major tech companies like Apple, Google, Microsoft, and Amazon 
    continued to dominate the market. CEOs Tim Cook, Sundar Pichai, Satya Nadella, 
    and Andy Jassy led their companies through significant transformations. 
    Cities like San Francisco, Seattle, New York, and Austin became tech hubs. 
    Investment amounts reached $100 million, $250 million, and even $1 billion 
    for various startups. The industry employed over 5 million people globally.
    """
    
    try:
        # Use the analyze endpoint
        response = api_client._make_request(
            "POST",
            "/api/v1/ner/analyze",
            json={"text": analysis_text}
        )
        
        if response:
            print(f"Total entities: {response.get('total_entities', 0)}")
            print(f"Unique entities: {response.get('unique_entities', 0)}")
            print(f"Entity density: {response.get('entity_density', 0):.2f} per word")
            
            print("\nEntity Distribution:")
            distribution = response.get('distribution', {})
            for entity_type, stats in distribution.items():
                print(f"  {entity_type}: {stats['count']} ({stats['percentage']:.1f}%)")
                if stats.get('examples'):
                    print(f"    Examples: {', '.join(stats['examples'][:3])}")
                    
    except Exception as e:
        print(f"Analysis error: {e}")

def main():
    """Run all API demos"""
    print("Advanced NER API Demo")
    print("=" * 50)
    
    # Check API connection
    api_client = get_api_client()
    try:
        health = api_client._make_request("GET", "/api/v1/health")
        print(f"✅ API Status: {health.get('status', 'unknown')}\n")
    except Exception as e:
        print(f"❌ API Connection Error: {str(e)}")
        print("Make sure the API server is running at the configured URL")
        print("\nTo start the API server:")
        print("  uvicorn api.app:app --reload")
        return
    
    try:
        demo_entity_extraction()
        print("\n" + "="*50)
        
        demo_direct_api_calls()
        print("\n" + "="*50)
        
        demo_batch_processing()
        print("\n" + "="*50)
        
        demo_entity_analysis()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("This might be due to API rate limits or network issues.")

if __name__ == "__main__":
    main()