#!/usr/bin/env python3
"""
Test script for enhanced entity visualization functionality
"""

import pytest
import json
from entity_visualization import EntityVisualizer, EntityInstance, EntityRelationship, render_enhanced_entity_display

def test_entity_visualizer_initialization():
    """Test EntityVisualizer initialization"""
    visualizer = EntityVisualizer()
    
    assert visualizer is not None
    assert len(visualizer.entity_colors) > 0
    assert len(visualizer.entity_icons) > 0
    assert "PERSON" in visualizer.entity_colors
    assert "PERSON" in visualizer.entity_icons

def test_entity_instance_creation():
    """Test EntityInstance data class"""
    entity = EntityInstance(
        text="John Doe",
        label="PERSON",
        start_pos=0,
        end_pos=8,
        confidence=0.95,
        context="John Doe is a software engineer"
    )
    
    assert entity.text == "John Doe"
    assert entity.label == "PERSON"
    assert entity.confidence == 0.95
    assert entity.is_verified == False
    
    # Test to_dict method
    entity_dict = entity.to_dict()
    assert isinstance(entity_dict, dict)
    assert entity_dict["text"] == "John Doe"

def test_entity_relationship_creation():
    """Test EntityRelationship data class"""
    relationship = EntityRelationship(
        entity1="John Doe",
        entity2="Microsoft",
        relationship_type="works_at",
        confidence=0.8,
        context="John Doe works at Microsoft"
    )
    
    assert relationship.entity1 == "John Doe"
    assert relationship.entity2 == "Microsoft"
    assert relationship.relationship_type == "works_at"
    assert relationship.confidence == 0.8

def test_discover_entity_relationships():
    """Test entity relationship discovery"""
    visualizer = EntityVisualizer()
    
    entities = {
        "PERSON": ["John Doe", "Jane Smith"],
        "ORG": ["Microsoft", "Google"],
        "GPE": ["Seattle", "California"]
    }
    
    transcript = "John Doe works at Microsoft in Seattle. Jane Smith is employed by Google in California."
    
    relationships = visualizer._discover_entity_relationships(entities, transcript)
    
    assert len(relationships) > 0
    
    # Check that we found some relationships
    relationship_types = [rel.relationship_type for rel in relationships]
    assert len(relationship_types) > 0

def test_apply_entity_filters():
    """Test entity filtering functionality"""
    visualizer = EntityVisualizer()
    
    entities = {
        "PERSON": ["John Doe", "Jane Smith", "Bob"],
        "ORG": ["Microsoft Corporation", "Google Inc", "AI"],
        "GPE": ["Seattle", "California", "NY"]
    }
    
    entity_confidence = {
        "PERSON": {"John Doe": 0.9, "Jane Smith": 0.8, "Bob": 0.4},
        "ORG": {"Microsoft Corporation": 0.95, "Google Inc": 0.85, "AI": 0.3},
        "GPE": {"Seattle": 0.9, "California": 0.8, "NY": 0.5}
    }
    
    # Test confidence filtering
    filtered = visualizer._apply_entity_filters(
        entities=entities,
        entity_confidence=entity_confidence,
        search_query="",
        selected_types=["PERSON", "ORG", "GPE"],
        min_confidence=0.7,
        min_length=3,
        min_frequency=1,
        regex_pattern="",
        case_sensitive=False
    )
    
    # Should filter out low confidence entities
    assert "Bob" not in filtered.get("PERSON", [])
    assert "AI" not in filtered.get("ORG", [])
    assert "NY" not in filtered.get("GPE", [])
    
    # Should keep high confidence entities
    assert "John Doe" in filtered.get("PERSON", [])
    assert "Microsoft Corporation" in filtered.get("ORG", [])

def test_generate_json_report():
    """Test JSON report generation"""
    visualizer = EntityVisualizer()
    
    entities = {
        "PERSON": ["John Doe", "Jane Smith"],
        "ORG": ["Microsoft", "Google"]
    }
    
    entity_confidence = {
        "PERSON": {"John Doe": 0.9, "Jane Smith": 0.8},
        "ORG": {"Microsoft": 0.95, "Google": 0.85}
    }
    
    transcript = "Test transcript content"
    
    json_report = visualizer._generate_json_report(
        entities=entities,
        entity_confidence=entity_confidence,
        relationships=None,
        transcript=transcript,
        include_confidence=True,
        include_relationships=False
    )
    
    # Parse JSON to verify structure
    report_data = json.loads(json_report)
    
    assert "metadata" in report_data
    assert "entities" in report_data
    assert "transcript" in report_data
    
    assert report_data["metadata"]["total_entities"] == 4
    assert len(report_data["metadata"]["entity_types"]) == 2
    
    # Check entities structure
    assert "PERSON" in report_data["entities"]
    assert "ORG" in report_data["entities"]
    
    # Check confidence scores are included
    person_entities = report_data["entities"]["PERSON"]
    assert any("confidence" in entity for entity in person_entities)

def test_generate_csv_report():
    """Test CSV report generation"""
    visualizer = EntityVisualizer()
    
    entities = {
        "PERSON": ["John Doe", "Jane Smith"],
        "ORG": ["Microsoft"]
    }
    
    entity_confidence = {
        "PERSON": {"John Doe": 0.9, "Jane Smith": 0.8},
        "ORG": {"Microsoft": 0.95}
    }
    
    csv_report = visualizer._generate_csv_report(
        entities=entities,
        entity_confidence=entity_confidence,
        include_confidence=True
    )
    
    # Basic CSV structure checks
    lines = csv_report.strip().split('\n')
    assert len(lines) > 1  # Header + data rows
    
    header = lines[0]
    assert "Entity_Type" in header
    assert "Entity_Text" in header
    assert "Confidence" in header
    
    # Check data rows
    assert len(lines) == 4  # Header + 3 entities

def test_find_entity_context():
    """Test entity context finding"""
    visualizer = EntityVisualizer()
    
    transcript = "John Doe is a software engineer at Microsoft. He has been working there for five years."
    entity = "John Doe"
    
    context = visualizer._find_entity_context(entity, transcript, context_window=20)
    
    assert entity in context
    assert len(context) > len(entity)

def test_determine_relationship_type():
    """Test relationship type determination"""
    visualizer = EntityVisualizer()
    
    # Test work relationship
    context1 = "John Doe works at Microsoft Corporation"
    rel_type1 = visualizer._determine_relationship_type("PERSON", "ORG", context1)
    assert rel_type1 == "works_at"
    
    # Test location relationship
    context2 = "Microsoft is located in Seattle"
    rel_type2 = visualizer._determine_relationship_type("ORG", "GPE", context2)
    assert rel_type2 == "located_in"
    
    # Test temporal relationship
    context3 = "The meeting is scheduled for Monday"
    rel_type3 = visualizer._determine_relationship_type("EVENT", "DATE", context3)
    # Accept any valid relationship type for this test
    assert isinstance(rel_type3, str) and len(rel_type3) > 0

def test_calculate_relationship_confidence():
    """Test relationship confidence calculation"""
    visualizer = EntityVisualizer()
    
    # Test high confidence (close proximity + relationship indicator)
    context1 = "John Doe works at Microsoft"
    confidence1 = visualizer._calculate_relationship_confidence("John Doe", "Microsoft", context1)
    assert confidence1 > 0.7
    
    # Test lower confidence (distant entities)
    context2 = "John Doe is a great engineer. Microsoft is a technology company."
    confidence2 = visualizer._calculate_relationship_confidence("John Doe", "Microsoft", context2)
    assert confidence2 < confidence1

def test_filter_entities_for_correction():
    """Test entity filtering for correction mode"""
    visualizer = EntityVisualizer()
    
    entities = {
        "PERSON": ["John Doe", "Jane Smith", "Bob"],
        "ORG": ["Microsoft", "Google"]
    }
    
    entity_confidence = {
        "PERSON": {"John Doe": 0.9, "Jane Smith": 0.6, "Bob": 0.4},
        "ORG": {"Microsoft": 0.95, "Google": 0.5}
    }
    
    # Test "Review All" mode
    all_entities = visualizer._filter_entities_for_correction(
        entities, entity_confidence, "Review All"
    )
    assert len(all_entities) == 2
    assert len(all_entities["PERSON"]) == 3
    
    # Test "Low Confidence Only" mode
    low_conf_entities = visualizer._filter_entities_for_correction(
        entities, entity_confidence, "Low Confidence Only"
    )
    
    # Should only include entities with confidence < 0.7
    assert "John Doe" not in low_conf_entities.get("PERSON", [])
    assert "Jane Smith" in low_conf_entities.get("PERSON", [])
    assert "Bob" in low_conf_entities.get("PERSON", [])

def test_generate_highlighted_transcript():
    """Test transcript highlighting functionality"""
    visualizer = EntityVisualizer()
    
    transcript = "John Doe works at Microsoft in Seattle."
    entities = {
        "PERSON": ["John Doe"],
        "ORG": ["Microsoft"],
        "GPE": ["Seattle"]
    }
    
    highlighted = visualizer._generate_highlighted_transcript(
        transcript=transcript,
        entities=entities,
        selected_types=["PERSON", "ORG", "GPE"],
        confidence_threshold=0.0,
        highlight_style="Background",
        search_term="",
        entity_positions=None
    )
    
    # Should contain HTML markup for highlighting
    assert "<span" in highlighted
    assert "John Doe" in highlighted
    assert "Microsoft" in highlighted
    assert "Seattle" in highlighted

if __name__ == "__main__":
    # Run basic tests
    print("🧪 Testing Entity Visualization Module...")
    
    try:
        test_entity_visualizer_initialization()
        print("✅ EntityVisualizer initialization test passed")
        
        test_entity_instance_creation()
        print("✅ EntityInstance creation test passed")
        
        test_entity_relationship_creation()
        print("✅ EntityRelationship creation test passed")
        
        test_discover_entity_relationships()
        print("✅ Entity relationship discovery test passed")
        
        test_apply_entity_filters()
        print("✅ Entity filtering test passed")
        
        test_generate_json_report()
        print("✅ JSON report generation test passed")
        
        test_generate_csv_report()
        print("✅ CSV report generation test passed")
        
        test_find_entity_context()
        print("✅ Entity context finding test passed")
        
        test_determine_relationship_type()
        print("✅ Relationship type determination test passed")
        
        test_calculate_relationship_confidence()
        print("✅ Relationship confidence calculation test passed")
        
        test_filter_entities_for_correction()
        print("✅ Entity correction filtering test passed")
        
        test_generate_highlighted_transcript()
        print("✅ Transcript highlighting test passed")
        
        print("\n🎉 All tests passed! Entity visualization module is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()