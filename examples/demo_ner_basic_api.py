#!/usr/bin/env python3
"""
Demo script to test the basic NER functionality using API
"""

from api_client import get_api_client
from api_wrappers import ner_basic

def main():
    # Test with sample text containing various entity types
    sample_text = """
    John Smith works at Microsoft Corporation in Seattle, Washington. 
    He met with Sarah Johnson on January 15, 2024 at 3:00 PM to discuss 
    the quarterly results. They also talked about the partnership with 
    Google and Apple Inc. The meeting was held in New York City.
    Barack Obama was mentioned as a former president, and they discussed
    the impact on companies like Amazon and Tesla.
    """
    
    print("Testing Basic NER Entity Extraction via API")
    print("=" * 50)
    
    # Check API connection
    api_client = get_api_client()
    try:
        health = api_client._make_request("GET", "/api/v1/health")
        print(f"✅ API Status: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ API Connection Error: {str(e)}")
        print("Make sure the API server is running\n")
        return
    
    print(f"\nInput text: {sample_text.strip()}")
    print("\n" + "=" * 50)
    
    # Extract entities using API wrapper
    print("Extracting entities via API...")
    try:
        entities = ner_basic.extract_entities(sample_text)
        
        print("\nExtracted Entities:")
        # Group entities by type
        entity_dict = {}
        for entity in entities:
            entity_type = entity.get('type', 'UNKNOWN')
            if entity_type not in entity_dict:
                entity_dict[entity_type] = []
            entity_dict[entity_type].append(entity)
        
        for entity_type, entity_list in entity_dict.items():
            print(f"\n{entity_type}:")
            for entity in entity_list:
                print(f"  - {entity['text']} (confidence: {entity.get('confidence', 1.0):.2f})")
    
    except Exception as e:
        print(f"Error extracting entities: {str(e)}")
        return
    
    # Test with specific entity types
    print("\n" + "=" * 50)
    print("Testing entity filtering (PERSON and ORG only)...")
    
    try:
        filtered_entities = ner_basic.extract_entities(
            sample_text, 
            entity_types=["PERSON", "ORG"]
        )
        
        print("\nFiltered Entities:")
        # Group filtered entities
        filtered_dict = {}
        for entity in filtered_entities:
            entity_type = entity.get('type', 'UNKNOWN')
            if entity_type not in filtered_dict:
                filtered_dict[entity_type] = []
            filtered_dict[entity_type].append(entity)
        
        for entity_type, entity_list in filtered_dict.items():
            print(f"\n{entity_type}:")
            for entity in entity_list:
                print(f"  - {entity['text']}")
    
    except Exception as e:
        print(f"Error with filtered extraction: {str(e)}")
    
    # Test direct API call
    print("\n" + "=" * 50)
    print("Testing direct API call...")
    
    try:
        response = api_client.extract_entities(sample_text)
        
        if response.get('success'):
            print(f"\n✅ Direct API call successful!")
            print(f"Total entities found: {len(response.get('entities', []))}")
            print(f"Processing time: {response.get('processing_time', 0):.3f}s")
            
            if response.get('metadata'):
                print(f"\nMetadata:")
                for key, value in response['metadata'].items():
                    print(f"  - {key}: {value}")
        else:
            print(f"❌ API call failed: {response.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"Error with direct API call: {str(e)}")
    
    # Test entity types endpoint
    print("\n" + "=" * 50)
    print("Getting supported entity types...")
    
    try:
        entity_types = ner_basic.get_entity_types()
        print(f"\nSupported entity types ({len(entity_types)} total):")
        for i, entity_type in enumerate(entity_types[:10]):  # Show first 10
            print(f"  {i+1}. {entity_type}")
        if len(entity_types) > 10:
            print(f"  ... and {len(entity_types) - 10} more")
    
    except Exception as e:
        print(f"Error getting entity types: {str(e)}")

if __name__ == "__main__":
    main()