#!/usr/bin/env python3
"""
Demo script to test the basic NER functionality with real text
"""

import ner_basic

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
    
    print("Testing Basic NER Entity Extraction")
    print("=" * 50)
    print(f"Input text: {sample_text.strip()}")
    print("\n" + "=" * 50)
    
    # Extract entities
    print("Extracting entities...")
    entities = ner_basic.extract_entities(sample_text)
    
    print("\nExtracted Entities:")
    for entity_type, entity_list in entities.items():
        print(f"\n{entity_type}:")
        for entity in entity_list:
            print(f"  - {entity}")
    
    # Test confidence scoring
    print("\n" + "=" * 50)
    print("Testing confidence scoring...")
    confidence_scores = ner_basic.get_entity_confidence(sample_text)
    
    print("\nEntity Confidence Scores:")
    for entity_type, scores in confidence_scores.items():
        print(f"\n{entity_type}:")
        for entity, score in scores.items():
            print(f"  - {entity}: {score:.2f}")
    
    # Test filtering
    print("\n" + "=" * 50)
    print("Testing entity filtering...")
    filtered_entities = ner_basic.filter_entities_by_type(entities, ["PERSON", "ORG"])
    
    print("\nFiltered Entities (PERSON and ORG only):")
    for entity_type, entity_list in filtered_entities.items():
        print(f"\n{entity_type}:")
        for entity in entity_list:
            print(f"  - {entity}")

if __name__ == "__main__":
    main()