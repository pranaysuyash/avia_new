#!/usr/bin/env python3
"""
Demo script for Cross-Provider Entity Linking System.
Demonstrates entity linking across Wikipedia, Wikidata, DBpedia, and Hugging Face.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from cross_provider_entity_linking import (
    CrossProviderEntityLinker,
    create_entity_linker,
    link_entities_in_text
)


def demo_basic_entity_linking():
    """Demonstrate basic entity linking functionality."""
    print("🔗 Demo: Basic Entity Linking")
    print("=" * 50)
    
    # Sample text with various entity types
    sample_text = """
    Apple Inc. is an American multinational technology company headquartered in Cupertino, California.
    The company was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976.
    Tim Cook is the current CEO of Apple. The company is known for products like the iPhone,
    iPad, and MacBook. Apple's headquarters, Apple Park, opened in 2017 in California.
    """
    
    print("📝 Sample Text:")
    print(sample_text)
    print()
    
    # Create entity linker with multiple providers
    print("🔧 Initializing entity linker with multiple providers...")
    linker = create_entity_linker(["wikipedia", "wikidata"])
    
    # Process the text
    print("🔄 Processing text for entity linking...")
    results = linker.process_text(sample_text)
    
    # Display results
    print(f"\n📊 Results Summary:")
    print(f"  • Entities extracted: {len(results['entities'])}")
    print(f"  • Entities linked: {len(results['entity_links'])}")
    print(f"  • Relationships found: {len(results['relationships'])}")
    print(f"  • Providers used: {', '.join(results['processing_metadata']['providers_used'])}")
    
    print(f"\n🏷️ Extracted Entities:")
    for entity in results['entities']:
        print(f"  • {entity['text']} ({entity['label']}) - {entity['start']}:{entity['end']}")
    
    print(f"\n🔗 Entity Links:")
    for link in results['entity_links']:
        print(f"  • {link['mention']} → {link['entity_name']}")
        print(f"    Source: {link['source']}, Confidence: {link['confidence']:.2f}")
        if link['description']:
            print(f"    Description: {link['description'][:100]}...")
        print()
    
    print("✅ Basic entity linking demo completed!")
    return results


def demo_provider_comparison():
    """Demonstrate comparison between different providers."""
    print("\n🔍 Demo: Provider Comparison")
    print("=" * 50)
    
    # Text with entities that might be handled differently by providers
    comparison_text = """
    The Beatles were an English rock band formed in Liverpool in 1960.
    The group consisted of John Lennon, Paul McCartney, George Harrison, and Ringo Starr.
    They are regarded as the most influential band of all time and were integral to the
    development of 1960s counterculture and popular music's recognition as an art form.
    """
    
    print("📝 Comparison Text:")
    print(comparison_text)
    print()
    
    # Test different provider combinations
    provider_combinations = [
        ["wikipedia"],
        ["wikidata"],
        ["wikipedia", "wikidata"],
    ]
    
    results_by_provider = {}
    
    for providers in provider_combinations:
        provider_name = "+".join(providers)
        print(f"🔄 Testing with providers: {provider_name}")
        
        linker = create_entity_linker(providers)
        results = linker.process_text(comparison_text)
        results_by_provider[provider_name] = results
        
        print(f"  • Entities linked: {len(results['entity_links'])}")
        print(f"  • Average confidence: {sum(link['confidence'] for link in results['entity_links']) / max(len(results['entity_links']), 1):.2f}")
        print()
    
    # Compare results
    print("📊 Provider Comparison Summary:")
    print("-" * 30)
    
    for provider_name, results in results_by_provider.items():
        print(f"\n{provider_name}:")
        for link in results['entity_links']:
            print(f"  • {link['mention']} → {link['entity_name']} (conf: {link['confidence']:.2f})")
    
    print("\n✅ Provider comparison demo completed!")
    return results_by_provider


def demo_entity_disambiguation():
    """Demonstrate entity disambiguation across providers."""
    print("\n🎯 Demo: Entity Disambiguation")
    print("=" * 50)
    
    # Text with ambiguous entities
    ambiguous_text = """
    Jordan is a country in the Middle East. Michael Jordan was a famous basketball player.
    Jordan Peterson is a Canadian psychologist. The Jordan River flows through the region.
    Apple is a fruit, but Apple Inc. is a technology company founded by Steve Jobs.
    """
    
    print("📝 Ambiguous Text:")
    print(ambiguous_text)
    print()
    
    # Process with multiple providers for disambiguation
    print("🔄 Processing with multiple providers for disambiguation...")
    linker = create_entity_linker(["wikipedia", "wikidata"])
    results = linker.process_text(ambiguous_text)
    
    # Show how disambiguation works
    print("🎯 Disambiguation Results:")
    
    # Group by mention to show disambiguation
    mention_groups = {}
    for link in results['entity_links']:
        mention = link['mention']
        if mention not in mention_groups:
            mention_groups[mention] = []
        mention_groups[mention].append(link)
    
    for mention, links in mention_groups.items():
        print(f"\n📍 Mention: '{mention}'")
        if len(links) == 1:
            link = links[0]
            print(f"  ✅ Disambiguated to: {link['entity_name']}")
            print(f"     Source: {link['source']}, Confidence: {link['confidence']:.2f}")
            if link['description']:
                print(f"     Description: {link['description'][:80]}...")
        else:
            print(f"  ⚠️ Multiple candidates found:")
            for link in links:
                print(f"     • {link['entity_name']} ({link['source']}, conf: {link['confidence']:.2f})")
    
    # Show provider-specific results
    print(f"\n📊 Provider-Specific Results:")
    for provider, links in results['provider_results'].items():
        print(f"\n{provider.title()}:")
        for link in links:
            print(f"  • {link['mention']} → {link['entity_name']} (conf: {link['confidence']:.2f})")
    
    print("\n✅ Entity disambiguation demo completed!")
    return results


def demo_relationship_extraction():
    """Demonstrate relationship extraction between entities."""
    print("\n🕸️ Demo: Relationship Extraction")
    print("=" * 50)
    
    # Text with entities that have known relationships
    relationship_text = """
    Barack Obama was the 44th President of the United States. He was married to Michelle Obama.
    They have two daughters: Malia Obama and Sasha Obama. Obama was born in Honolulu, Hawaii,
    and later lived in Chicago, Illinois. He attended Harvard Law School and worked as a
    community organizer before entering politics.
    """
    
    print("📝 Relationship Text:")
    print(relationship_text)
    print()
    
    # Process for relationships
    print("🔄 Processing for entity relationships...")
    linker = create_entity_linker(["wikidata"])  # Wikidata has rich relationship data
    results = linker.process_text(relationship_text)
    
    print(f"🔗 Found {len(results['entity_links'])} linked entities")
    for link in results['entity_links']:
        print(f"  • {link['mention']} → {link['entity_name']} ({link['source']})")
    
    print(f"\n🕸️ Found {len(results['relationships'])} relationships:")
    
    # Group relationships by subject
    relationship_groups = {}
    for rel in results['relationships']:
        subject = rel['subject_entity']
        if subject not in relationship_groups:
            relationship_groups[subject] = []
        relationship_groups[subject].append(rel)
    
    for subject, rels in relationship_groups.items():
        print(f"\n📍 {subject}:")
        for rel in rels[:5]:  # Show first 5 relationships
            print(f"  • {rel['predicate']} → {rel['object_entity']}")
    
    # Show graph statistics
    print(f"\n📊 Entity Graph Statistics:")
    graph_stats = results['graph_stats']
    print(f"  • Nodes (entities): {graph_stats['nodes']}")
    print(f"  • Edges (relationships): {graph_stats['edges']}")
    print(f"  • Connected components: {graph_stats['connected_components']}")
    
    print("\n✅ Relationship extraction demo completed!")
    return results


def demo_quality_assessment():
    """Demonstrate quality assessment of entity linking results."""
    print("\n📊 Demo: Quality Assessment")
    print("=" * 50)
    
    # Create different quality scenarios
    scenarios = [
        {
            "name": "High Quality Text",
            "text": "Barack Obama was the President of the United States. He was born in Hawaii.",
            "expected_quality": "High"
        },
        {
            "name": "Medium Quality Text", 
            "text": "Some person named John worked at a company in New York.",
            "expected_quality": "Medium"
        },
        {
            "name": "Low Quality Text",
            "text": "He went there and did something with them.",
            "expected_quality": "Low"
        }
    ]
    
    linker = create_entity_linker(["wikipedia", "wikidata"])
    
    for scenario in scenarios:
        print(f"\n🔍 Scenario: {scenario['name']}")
        print(f"Text: {scenario['text']}")
        print(f"Expected Quality: {scenario['expected_quality']}")
        
        # Process text
        results = linker.process_text(scenario['text'])
        
        # Validate links
        from cross_provider_entity_linking import EntityLink
        entity_links = [
            EntityLink(**link_data) for link_data in results['entity_links']
        ]
        validation = linker.validate_links(entity_links)
        
        print(f"📊 Quality Metrics:")
        print(f"  • Total links: {validation['total_links']}")
        print(f"  • High confidence: {validation['high_confidence_links']}")
        print(f"  • Medium confidence: {validation['medium_confidence_links']}")
        print(f"  • Low confidence: {validation['low_confidence_links']}")
        print(f"  • Average confidence: {validation['average_confidence']:.2f}")
        print(f"  • Quality score: {validation['quality_score']:.2f}")
        
        # Quality assessment
        if validation['quality_score'] >= 0.8:
            quality_rating = "🟢 Excellent"
        elif validation['quality_score'] >= 0.6:
            quality_rating = "🟡 Good"
        elif validation['quality_score'] >= 0.4:
            quality_rating = "🟠 Fair"
        else:
            quality_rating = "🔴 Poor"
        
        print(f"  • Overall rating: {quality_rating}")
        
        # Provider distribution
        print(f"  • Provider distribution:")
        for provider, count in validation['provider_distribution'].items():
            print(f"    - {provider}: {count}")
    
    print("\n✅ Quality assessment demo completed!")


def demo_performance_benchmarking():
    """Demonstrate performance benchmarking across providers."""
    print("\n⚡ Demo: Performance Benchmarking")
    print("=" * 50)
    
    # Test texts of different lengths
    test_texts = [
        {
            "name": "Short Text",
            "text": "Apple Inc. was founded by Steve Jobs.",
            "expected_entities": 2
        },
        {
            "name": "Medium Text",
            "text": """
            Microsoft Corporation is an American multinational technology company.
            It was founded by Bill Gates and Paul Allen in 1975. The company is
            headquartered in Redmond, Washington. Satya Nadella is the current CEO.
            """,
            "expected_entities": 6
        },
        {
            "name": "Long Text",
            "text": """
            The United Nations is an international organization founded in 1945.
            It is headquartered in New York City. The UN has 193 member states.
            António Guterres is the current Secretary-General. The organization
            was established after World War II to promote international cooperation.
            The UN has six main organs: the General Assembly, the Security Council,
            the Economic and Social Council, the Trusteeship Council, the International
            Court of Justice, and the Secretariat. The UN plays a crucial role in
            maintaining international peace and security.
            """,
            "expected_entities": 10
        }
    ]
    
    providers_to_test = [
        ["wikipedia"],
        ["wikidata"],
        ["wikipedia", "wikidata"]
    ]
    
    print("🔄 Running performance benchmarks...")
    
    benchmark_results = {}
    
    for provider_combo in providers_to_test:
        provider_name = "+".join(provider_combo)
        print(f"\n📊 Testing {provider_name}:")
        
        benchmark_results[provider_name] = {}
        
        for test_case in test_texts:
            print(f"  🔍 {test_case['name']}...")
            
            # Measure performance
            import time
            start_time = time.time()
            
            linker = create_entity_linker(provider_combo)
            results = linker.process_text(test_case['text'])
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Store results
            benchmark_results[provider_name][test_case['name']] = {
                'processing_time': processing_time,
                'entities_found': len(results['entity_links']),
                'expected_entities': test_case['expected_entities'],
                'accuracy': len(results['entity_links']) / test_case['expected_entities'] if test_case['expected_entities'] > 0 else 0,
                'average_confidence': sum(link['confidence'] for link in results['entity_links']) / max(len(results['entity_links']), 1)
            }
            
            print(f"    ⏱️ Time: {processing_time:.2f}s")
            print(f"    🔗 Entities: {len(results['entity_links'])}/{test_case['expected_entities']}")
            print(f"    🎯 Avg Confidence: {benchmark_results[provider_name][test_case['name']]['average_confidence']:.2f}")
    
    # Summary comparison
    print(f"\n📊 Performance Summary:")
    print("-" * 60)
    print(f"{'Provider':<20} {'Avg Time':<12} {'Avg Entities':<12} {'Avg Confidence':<15}")
    print("-" * 60)
    
    for provider_name, results in benchmark_results.items():
        avg_time = sum(r['processing_time'] for r in results.values()) / len(results)
        avg_entities = sum(r['entities_found'] for r in results.values()) / len(results)
        avg_confidence = sum(r['average_confidence'] for r in results.values()) / len(results)
        
        print(f"{provider_name:<20} {avg_time:<12.2f} {avg_entities:<12.1f} {avg_confidence:<15.2f}")
    
    print("\n✅ Performance benchmarking demo completed!")
    return benchmark_results


def demo_real_world_scenarios():
    """Demonstrate real-world entity linking scenarios."""
    print("\n🌍 Demo: Real-World Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "News Article",
            "text": """
            Tesla CEO Elon Musk announced that the company will build a new Gigafactory
            in Berlin, Germany. The facility will produce Model Y vehicles for the
            European market. The announcement was made at the Tesla Design Studio in
            Hawthorne, California. Musk said the factory will create thousands of jobs
            in the region.
            """,
            "domain": "Business/Technology"
        },
        {
            "name": "Academic Paper",
            "text": """
            The research was conducted at Stanford University by Dr. Sarah Johnson
            and her team. The study, published in Nature, examined the effects of
            climate change on Arctic ice. The findings were presented at the
            International Climate Conference in Geneva, Switzerland.
            """,
            "domain": "Academic/Research"
        },
        {
            "name": "Historical Text",
            "text": """
            During World War II, Winston Churchill served as Prime Minister of
            the United Kingdom. The Battle of Britain took place in 1940, with
            the Royal Air Force defending against the German Luftwaffe. The war
            ended in 1945 with the surrender of Nazi Germany.
            """,
            "domain": "Historical"
        }
    ]
    
    linker = create_entity_linker(["wikipedia", "wikidata"])
    
    for scenario in scenarios:
        print(f"\n📰 Scenario: {scenario['name']} ({scenario['domain']})")
        print(f"Text: {scenario['text'][:100]}...")
        
        # Process the scenario
        results = linker.process_text(scenario['text'])
        
        print(f"\n🔍 Analysis Results:")
        print(f"  • Entities extracted: {len(results['entities'])}")
        print(f"  • Entities linked: {len(results['entity_links'])}")
        print(f"  • Relationships: {len(results['relationships'])}")
        
        # Show top entities
        print(f"\n🏷️ Top Linked Entities:")
        sorted_links = sorted(results['entity_links'], key=lambda x: x['confidence'], reverse=True)
        for link in sorted_links[:5]:
            print(f"  • {link['mention']} → {link['entity_name']}")
            print(f"    Confidence: {link['confidence']:.2f}, Source: {link['source']}")
            if link['description']:
                print(f"    Description: {link['description'][:80]}...")
        
        # Domain-specific insights
        entity_types = {}
        for entity in results['entities']:
            entity_type = entity['label']
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        print(f"\n📊 Entity Type Distribution:")
        for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {entity_type}: {count}")
    
    print("\n✅ Real-world scenarios demo completed!")


def save_demo_results(results: dict, filename: str = "entity_linking_demo_results.json"):
    """Save demo results to a JSON file."""
    print(f"\n💾 Saving demo results to {filename}...")
    
    # Convert datetime objects to strings for JSON serialization
    def serialize_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=serialize_datetime)
        print(f"✅ Results saved successfully!")
    except Exception as e:
        print(f"❌ Error saving results: {e}")


def main():
    """Run all demonstration scenarios."""
    print("🎉 Cross-Provider Entity Linking Demo")
    print("=" * 60)
    print("This demo showcases comprehensive entity linking capabilities")
    print("across multiple knowledge bases and providers:")
    print("• Wikipedia - General knowledge encyclopedia")
    print("• Wikidata - Structured knowledge base")
    print("• DBpedia - Structured Wikipedia data")
    print("• Hugging Face - ML-based entity linking")
    print("=" * 60)
    
    # Run all demos
    demo_results = {}
    
    try:
        demo_results['basic_linking'] = demo_basic_entity_linking()
        demo_results['provider_comparison'] = demo_provider_comparison()
        demo_results['disambiguation'] = demo_entity_disambiguation()
        demo_results['relationships'] = demo_relationship_extraction()
        demo_quality_assessment()
        demo_results['performance'] = demo_performance_benchmarking()
        demo_real_world_scenarios()
        
        # Save results
        save_demo_results(demo_results)
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("Note: Some providers may not be available in the demo environment")
    
    print("\n🎊 All demonstrations completed successfully!")
    print("\n📚 Next Steps:")
    print("1. Install required dependencies (spacy, transformers, etc.)")
    print("2. Download spaCy language models")
    print("3. Configure API access for external services")
    print("4. Integrate with your text processing pipeline")
    print("5. Customize confidence thresholds and disambiguation rules")
    
    print("\n💡 Pro Tips:")
    print("• Use multiple providers for better disambiguation")
    print("• Adjust confidence thresholds based on your use case")
    print("• Cache results for frequently processed entities")
    print("• Monitor provider performance and availability")
    print("• Consider domain-specific entity linking models")


if __name__ == "__main__":
    main()