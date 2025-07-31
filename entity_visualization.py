#!/usr/bin/env python3
"""
Enhanced Entity Visualization Module
Provides interactive entity highlighting, relationship mapping, and advanced visualization
"""

import streamlit as st
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
import json
import pandas as pd
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import re
import io
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EntityInstance:
    """Data class for individual entity instances"""
    text: str
    label: str
    start_pos: int
    end_pos: int
    confidence: float
    context: str = ""
    corrected_text: Optional[str] = None
    is_verified: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class EntityRelationship:
    """Data class for entity relationships"""
    entity1: str
    entity2: str
    relationship_type: str
    confidence: float
    context: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)

class EntityVisualizer:
    """Enhanced entity visualization with interactive features"""
    
    def __init__(self):
        self.entity_colors = {
            "PERSON": "#FF6B6B",
            "ORG": "#4ECDC4", 
            "DATE": "#45B7D1",
            "TIME": "#96CEB4",
            "GPE": "#FFEAA7",
            "MONEY": "#DDA0DD",
            "CARDINAL": "#98D8C8",
            "TOPIC": "#F7DC6F",
            "EVENT": "#FFB6C1",
            "PRODUCT": "#87CEEB",
            "TECHNOLOGY": "#DEB887",
            "EMOTION": "#F0E68C"
        }
        
        self.entity_icons = {
            "PERSON": "👤",
            "ORG": "🏢",
            "DATE": "📅",
            "TIME": "⏰",
            "GPE": "🌍",
            "MONEY": "💰",
            "CARDINAL": "🔢",
            "TOPIC": "🏷️",
            "EVENT": "📅",
            "PRODUCT": "📦",
            "TECHNOLOGY": "💻",
            "EMOTION": "😊"
        }
    
    def render_interactive_entity_highlighting(self, 
                                             transcript: str, 
                                             entities: Dict[str, List[str]],
                                             entity_positions: Optional[Dict] = None,
                                             show_confidence: bool = True) -> Dict[str, Any]:
        """
        Render interactive entity highlighting in transcript text
        
        Args:
            transcript: Full transcript text
            entities: Dictionary of entity types and their instances
            entity_positions: Optional position data for entities
            show_confidence: Whether to show confidence scores
            
        Returns:
            Dictionary with user interactions and selections
        """
        st.subheader("🎯 Interactive Entity Highlighting")
        
        if not entities or not transcript:
            st.info("No entities or transcript available for highlighting")
            return {}
        
        # Entity filtering controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Entity type filter
            available_types = list(entities.keys())
            selected_types = st.multiselect(
                "Filter Entity Types:",
                options=available_types,
                default=available_types,
                help="Select which entity types to highlight"
            )
        
        with col2:
            # Confidence threshold
            confidence_threshold = st.slider(
                "Confidence Threshold:",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="Minimum confidence score to display entities"
            )
        
        with col3:
            # Highlighting style
            highlight_style = st.selectbox(
                "Highlight Style:",
                options=["Background", "Underline", "Border", "Bold"],
                help="Choose how entities are highlighted"
            )
        
        # Search functionality
        search_term = st.text_input(
            "🔍 Search Entities:",
            placeholder="Search for specific entities...",
            help="Search for entities by name or type"
        )
        
        # Generate highlighted transcript
        highlighted_transcript = self._generate_highlighted_transcript(
            transcript, entities, selected_types, confidence_threshold, 
            highlight_style, search_term, entity_positions
        )
        
        # Display highlighted transcript
        st.markdown("### 📝 Highlighted Transcript")
        st.markdown(highlighted_transcript, unsafe_allow_html=True)
        
        # Entity interaction tracking
        interactions = {
            'selected_types': selected_types,
            'confidence_threshold': confidence_threshold,
            'highlight_style': highlight_style,
            'search_term': search_term,
            'clicked_entities': []
        }
        
        return interactions
    
    def render_entity_relationship_map(self, 
                                     entities: Dict[str, List[str]], 
                                     transcript: str) -> List[EntityRelationship]:
        """
        Render entity relationship mapping and visualization
        
        Args:
            entities: Dictionary of entity types and instances
            transcript: Full transcript text for context analysis
            
        Returns:
            List of discovered entity relationships
        """
        st.subheader("🔗 Entity Relationship Mapping")
        
        if not entities:
            st.info("No entities available for relationship analysis")
            return []
        
        # Generate relationships
        relationships = self._discover_entity_relationships(entities, transcript)
        
        if not relationships:
            st.info("No significant relationships found between entities")
            return []
        
        # Relationship visualization options
        col1, col2 = st.columns(2)
        
        with col1:
            viz_type = st.selectbox(
                "Visualization Type:",
                options=["Network Graph", "Matrix View", "Timeline"],
                help="Choose how to visualize entity relationships"
            )
        
        with col2:
            min_confidence = st.slider(
                "Minimum Relationship Confidence:",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Filter relationships by confidence score"
            )
        
        # Filter relationships by confidence
        filtered_relationships = [
            rel for rel in relationships 
            if rel.confidence >= min_confidence
        ]
        
        if viz_type == "Network Graph":
            self._render_network_graph(filtered_relationships)
        elif viz_type == "Matrix View":
            self._render_relationship_matrix(filtered_relationships)
        elif viz_type == "Timeline":
            self._render_relationship_timeline(filtered_relationships, entities)
        
        # Relationship details table
        if filtered_relationships:
            st.markdown("### 📊 Relationship Details")
            
            relationship_data = []
            for rel in filtered_relationships:
                relationship_data.append({
                    "Entity 1": rel.entity1,
                    "Relationship": rel.relationship_type,
                    "Entity 2": rel.entity2,
                    "Confidence": f"{rel.confidence:.2f}",
                    "Context": rel.context[:100] + "..." if len(rel.context) > 100 else rel.context
                })
            
            df = pd.DataFrame(relationship_data)
            st.dataframe(df, use_container_width=True)
        
        return filtered_relationships
    
    def render_entity_filtering_search(self, 
                                     entities: Dict[str, List[str]],
                                     entity_confidence: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Render advanced entity filtering and search functionality
        
        Args:
            entities: Dictionary of entity types and instances
            entity_confidence: Optional confidence scores for entities
            
        Returns:
            Dictionary with filtered entities and search results
        """
        st.subheader("🔍 Advanced Entity Search & Filtering")
        
        if not entities:
            st.info("No entities available for filtering")
            return {}
        
        # Search and filter controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Text search
            search_query = st.text_input(
                "Search Entities:",
                placeholder="Enter search term...",
                help="Search entity names and types"
            )
        
        with col2:
            # Entity type filter
            entity_types = list(entities.keys())
            selected_types = st.multiselect(
                "Entity Types:",
                options=entity_types,
                default=entity_types,
                help="Filter by entity types"
            )
        
        with col3:
            # Confidence filter
            if entity_confidence:
                min_confidence = st.slider(
                    "Min Confidence:",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1,
                    help="Minimum confidence score"
                )
            else:
                min_confidence = 0.0
        
        # Advanced filters
        with st.expander("🔧 Advanced Filters", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                # Length filter
                min_length = st.number_input(
                    "Minimum Entity Length:",
                    min_value=1,
                    max_value=50,
                    value=1,
                    help="Minimum number of characters"
                )
                
                # Frequency filter
                min_frequency = st.number_input(
                    "Minimum Frequency:",
                    min_value=1,
                    max_value=10,
                    value=1,
                    help="Minimum number of occurrences"
                )
            
            with col2:
                # Pattern matching
                regex_pattern = st.text_input(
                    "Regex Pattern:",
                    placeholder="e.g., .*Corp.*",
                    help="Filter entities using regex patterns"
                )
                
                # Case sensitivity
                case_sensitive = st.checkbox(
                    "Case Sensitive Search",
                    value=False,
                    help="Enable case-sensitive filtering"
                )
        
        # Apply filters
        filtered_entities = self._apply_entity_filters(
            entities, entity_confidence, search_query, selected_types,
            min_confidence, min_length, min_frequency, regex_pattern, case_sensitive
        )
        
        # Display filtered results
        self._display_filtered_entities(filtered_entities, entity_confidence)
        
        # Search statistics
        total_entities = sum(len(entity_list) for entity_list in entities.values())
        filtered_count = sum(len(entity_list) for entity_list in filtered_entities.values())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Entities", total_entities)
        with col2:
            st.metric("Filtered Results", filtered_count)
        with col3:
            filter_percentage = (filtered_count / total_entities * 100) if total_entities > 0 else 0
            st.metric("Filter Efficiency", f"{filter_percentage:.1f}%")
        
        return {
            'filtered_entities': filtered_entities,
            'search_query': search_query,
            'selected_types': selected_types,
            'filters_applied': {
                'min_confidence': min_confidence,
                'min_length': min_length,
                'min_frequency': min_frequency,
                'regex_pattern': regex_pattern,
                'case_sensitive': case_sensitive
            }
        }
    
    def render_exportable_reports(self, 
                                entities: Dict[str, List[str]],
                                entity_confidence: Optional[Dict] = None,
                                relationships: Optional[List[EntityRelationship]] = None,
                                transcript: str = "") -> Dict[str, str]:
        """
        Create exportable entity reports in multiple formats
        
        Args:
            entities: Dictionary of entity types and instances
            entity_confidence: Optional confidence scores
            relationships: Optional entity relationships
            transcript: Original transcript text
            
        Returns:
            Dictionary with report data in different formats
        """
        st.subheader("📥 Export Entity Reports")
        
        if not entities:
            st.info("No entities available for export")
            return {}
        
        # Export format selection
        col1, col2, col3 = st.columns(3)
        
        with col1:
            export_formats = st.multiselect(
                "Export Formats:",
                options=["JSON", "CSV", "PDF", "XML", "Excel"],
                default=["JSON", "CSV"],
                help="Select formats for export"
            )
        
        with col2:
            include_confidence = st.checkbox(
                "Include Confidence Scores",
                value=bool(entity_confidence),
                help="Include confidence scores in exports"
            )
        
        with col3:
            include_relationships = st.checkbox(
                "Include Relationships",
                value=bool(relationships),
                help="Include entity relationships in exports"
            )
        
        # Generate reports
        reports = {}
        
        if "JSON" in export_formats:
            reports["json"] = self._generate_json_report(
                entities, entity_confidence, relationships, transcript,
                include_confidence, include_relationships
            )
        
        if "CSV" in export_formats:
            reports["csv"] = self._generate_csv_report(
                entities, entity_confidence, include_confidence
            )
        
        if "PDF" in export_formats:
            reports["pdf"] = self._generate_pdf_report(
                entities, entity_confidence, relationships, transcript,
                include_confidence, include_relationships
            )
        
        if "XML" in export_formats:
            reports["xml"] = self._generate_xml_report(
                entities, entity_confidence, relationships,
                include_confidence, include_relationships
            )
        
        if "Excel" in export_formats:
            reports["excel"] = self._generate_excel_report(
                entities, entity_confidence, relationships,
                include_confidence, include_relationships
            )
        
        # Display download buttons
        if reports:
            st.markdown("### 📁 Download Reports")
            
            cols = st.columns(len(reports))
            for i, (format_name, report_data) in enumerate(reports.items()):
                with cols[i]:
                    if format_name == "json":
                        st.download_button(
                            "📄 Download JSON",
                            data=report_data,
                            file_name=f"entity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    elif format_name == "csv":
                        st.download_button(
                            "📊 Download CSV",
                            data=report_data,
                            file_name=f"entity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    elif format_name == "pdf":
                        st.download_button(
                            "📑 Download PDF",
                            data=report_data,
                            file_name=f"entity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                    elif format_name == "xml":
                        st.download_button(
                            "📋 Download XML",
                            data=report_data,
                            file_name=f"entity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
                            mime="application/xml"
                        )
                    elif format_name == "excel":
                        st.download_button(
                            "📈 Download Excel",
                            data=report_data,
                            file_name=f"entity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        
        return reports
    
    def render_confidence_scoring_correction(self, 
                                           entities: Dict[str, List[str]],
                                           entity_confidence: Optional[Dict] = None,
                                           transcript: str = "") -> Dict[str, Any]:
        """
        Render entity confidence scoring and manual correction interface
        
        Args:
            entities: Dictionary of entity types and instances
            entity_confidence: Optional confidence scores
            transcript: Original transcript for context
            
        Returns:
            Dictionary with corrections and confidence updates
        """
        st.subheader("✏️ Entity Confidence & Manual Correction")
        
        if not entities:
            st.info("No entities available for correction")
            return {}
        
        corrections = {
            'entity_corrections': {},
            'confidence_updates': {},
            'verified_entities': set(),
            'rejected_entities': set()
        }
        
        # Correction mode selection
        correction_mode = st.selectbox(
            "Correction Mode:",
            options=["Review All", "Low Confidence Only", "By Entity Type"],
            help="Choose which entities to review for corrections"
        )
        
        # Filter entities based on correction mode
        entities_to_review = self._filter_entities_for_correction(
            entities, entity_confidence, correction_mode
        )
        
        if not entities_to_review:
            st.info("No entities match the selected correction criteria")
            return corrections
        
        # Entity correction interface
        st.markdown("### 🔍 Entity Review & Correction")
        
        for entity_type, entity_list in entities_to_review.items():
            if not entity_list:
                continue
            
            with st.expander(f"{self.entity_icons.get(entity_type, '🏷️')} {entity_type} ({len(entity_list)} entities)", expanded=True):
                
                for i, entity in enumerate(entity_list):
                    # Get confidence score
                    confidence = 0.8  # Default
                    if entity_confidence and entity_type in entity_confidence:
                        confidence = entity_confidence[entity_type].get(entity, 0.8)
                    
                    # Entity correction row
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
                    
                    with col1:
                        # Editable entity text
                        corrected_text = st.text_input(
                            f"Entity {i+1}:",
                            value=entity,
                            key=f"correct_{entity_type}_{i}",
                            label_visibility="collapsed"
                        )
                        
                        if corrected_text != entity:
                            corrections['entity_corrections'][f"{entity_type}_{entity}"] = corrected_text
                    
                    with col2:
                        # Confidence adjustment
                        new_confidence = st.slider(
                            "Confidence:",
                            min_value=0.0,
                            max_value=1.0,
                            value=confidence,
                            step=0.1,
                            key=f"conf_{entity_type}_{i}",
                            label_visibility="collapsed"
                        )
                        
                        if abs(new_confidence - confidence) > 0.05:
                            corrections['confidence_updates'][f"{entity_type}_{entity}"] = new_confidence
                    
                    with col3:
                        # Verify button
                        if st.button("✅", key=f"verify_{entity_type}_{i}", help="Verify as correct"):
                            corrections['verified_entities'].add(f"{entity_type}_{entity}")
                            st.success("Verified!")
                    
                    with col4:
                        # Reject button
                        if st.button("❌", key=f"reject_{entity_type}_{i}", help="Mark as incorrect"):
                            corrections['rejected_entities'].add(f"{entity_type}_{entity}")
                            st.error("Rejected!")
                    
                    with col5:
                        # Context button
                        if st.button("📝", key=f"context_{entity_type}_{i}", help="Show context"):
                            context = self._find_entity_context(entity, transcript)
                            if context:
                                st.info(f"Context: ...{context}...")
        
        # Bulk operations
        st.markdown("### ⚡ Bulk Operations")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Verify All High Confidence", help="Verify entities with confidence > 0.8"):
                for entity_type, entity_list in entities.items():
                    for entity in entity_list:
                        if entity_confidence and entity_type in entity_confidence:
                            conf = entity_confidence[entity_type].get(entity, 0.8)
                            if conf > 0.8:
                                corrections['verified_entities'].add(f"{entity_type}_{entity}")
                st.success("High confidence entities verified!")
        
        with col2:
            if st.button("❌ Reject All Low Confidence", help="Reject entities with confidence < 0.5"):
                for entity_type, entity_list in entities.items():
                    for entity in entity_list:
                        if entity_confidence and entity_type in entity_confidence:
                            conf = entity_confidence[entity_type].get(entity, 0.8)
                            if conf < 0.5:
                                corrections['rejected_entities'].add(f"{entity_type}_{entity}")
                st.success("Low confidence entities rejected!")
        
        with col3:
            if st.button("🔄 Reset All Corrections", help="Clear all corrections"):
                corrections = {
                    'entity_corrections': {},
                    'confidence_updates': {},
                    'verified_entities': set(),
                    'rejected_entities': set()
                }
                st.success("Corrections reset!")
        
        # Correction summary
        if any(corrections.values()):
            st.markdown("### 📊 Correction Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Text Corrections", len(corrections['entity_corrections']))
            with col2:
                st.metric("Confidence Updates", len(corrections['confidence_updates']))
            with col3:
                st.metric("Verified Entities", len(corrections['verified_entities']))
            with col4:
                st.metric("Rejected Entities", len(corrections['rejected_entities']))
        
        return corrections 
   
    # Helper methods for EntityVisualizer
    
    def _generate_highlighted_transcript(self, 
                                       transcript: str, 
                                       entities: Dict[str, List[str]],
                                       selected_types: List[str],
                                       confidence_threshold: float,
                                       highlight_style: str,
                                       search_term: str,
                                       entity_positions: Optional[Dict] = None) -> str:
        """Generate HTML-highlighted transcript with entity markup"""
        
        highlighted_text = transcript
        
        # Create entity highlighting patterns
        for entity_type in selected_types:
            if entity_type not in entities:
                continue
            
            color = self.entity_colors.get(entity_type, "#cccccc")
            icon = self.entity_icons.get(entity_type, "🏷️")
            
            for entity in entities[entity_type]:
                # Skip if search term is specified and doesn't match
                if search_term and search_term.lower() not in entity.lower():
                    continue
                
                # Apply highlighting based on style
                if highlight_style == "Background":
                    replacement = f'<span style="background-color: {color}40; padding: 2px 4px; border-radius: 4px; margin: 1px;" title="{entity_type}: {entity}">{icon} {entity}</span>'
                elif highlight_style == "Underline":
                    replacement = f'<span style="text-decoration: underline; text-decoration-color: {color}; text-decoration-thickness: 2px;" title="{entity_type}: {entity}">{icon} {entity}</span>'
                elif highlight_style == "Border":
                    replacement = f'<span style="border: 2px solid {color}; padding: 1px 3px; border-radius: 3px; margin: 1px;" title="{entity_type}: {entity}">{icon} {entity}</span>'
                elif highlight_style == "Bold":
                    replacement = f'<span style="font-weight: bold; color: {color};" title="{entity_type}: {entity}">{icon} {entity}</span>'
                
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(entity) + r'\b'
                highlighted_text = re.sub(pattern, replacement, highlighted_text, flags=re.IGNORECASE)
        
        return highlighted_text
    
    def _discover_entity_relationships(self, 
                                     entities: Dict[str, List[str]], 
                                     transcript: str) -> List[EntityRelationship]:
        """Discover relationships between entities based on context"""
        
        relationships = []
        
        # Get all entities with their types
        all_entities = []
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                all_entities.append((entity, entity_type))
        
        # Find co-occurrences and relationships
        sentences = transcript.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue
            
            # Find entities in this sentence
            sentence_entities = []
            for entity, entity_type in all_entities:
                if entity.lower() in sentence.lower():
                    sentence_entities.append((entity, entity_type))
            
            # Create relationships between entities in the same sentence
            for i, (entity1, type1) in enumerate(sentence_entities):
                for entity2, type2 in sentence_entities[i+1:]:
                    if entity1 != entity2:
                        # Determine relationship type based on entity types
                        rel_type = self._determine_relationship_type(type1, type2, sentence)
                        confidence = self._calculate_relationship_confidence(entity1, entity2, sentence)
                        
                        relationship = EntityRelationship(
                            entity1=entity1,
                            entity2=entity2,
                            relationship_type=rel_type,
                            confidence=confidence,
                            context=sentence[:200]
                        )
                        relationships.append(relationship)
        
        # Remove duplicates and sort by confidence
        unique_relationships = {}
        for rel in relationships:
            key = f"{rel.entity1}_{rel.entity2}_{rel.relationship_type}"
            if key not in unique_relationships or rel.confidence > unique_relationships[key].confidence:
                unique_relationships[key] = rel
        
        return sorted(unique_relationships.values(), key=lambda x: x.confidence, reverse=True)
    
    def _determine_relationship_type(self, type1: str, type2: str, context: str) -> str:
        """Determine the type of relationship between two entities"""
        
        # Define relationship patterns
        relationship_patterns = {
            "works_at": ["works at", "employed by", "employee of", "job at"],
            "located_in": ["in", "at", "located in", "based in"],
            "associated_with": ["with", "and", "along with", "together with"],
            "mentioned_with": ["mentioned", "discussed", "talked about"],
            "temporal": ["during", "on", "at", "when", "while"],
            "financial": ["paid", "cost", "worth", "valued at", "price"]
        }
        
        context_lower = context.lower()
        
        # Check for specific relationship patterns
        for rel_type, patterns in relationship_patterns.items():
            if any(pattern in context_lower for pattern in patterns):
                return rel_type
        
        # Default relationships based on entity types
        if type1 == "PERSON" and type2 == "ORG":
            return "associated_with"
        elif type1 == "PERSON" and type2 == "GPE":
            return "located_in"
        elif type1 == "ORG" and type2 == "GPE":
            return "located_in"
        elif type1 in ["DATE", "TIME"] and type2 in ["PERSON", "ORG", "EVENT"]:
            return "temporal"
        elif type1 == "MONEY" and type2 in ["PERSON", "ORG", "PRODUCT"]:
            return "financial"
        else:
            return "co_mentioned"
    
    def _calculate_relationship_confidence(self, entity1: str, entity2: str, context: str) -> float:
        """Calculate confidence score for entity relationship"""
        
        base_confidence = 0.5
        
        # Increase confidence based on proximity
        entity1_pos = context.lower().find(entity1.lower())
        entity2_pos = context.lower().find(entity2.lower())
        
        if entity1_pos >= 0 and entity2_pos >= 0:
            distance = abs(entity1_pos - entity2_pos)
            proximity_bonus = max(0, 0.3 - (distance / 100))
            base_confidence += proximity_bonus
        
        # Increase confidence for specific relationship indicators
        relationship_indicators = [
            "works at", "employed by", "CEO of", "president of", "located in",
            "based in", "founded by", "owned by", "part of", "member of"
        ]
        
        for indicator in relationship_indicators:
            if indicator in context.lower():
                base_confidence += 0.2
                break
        
        return min(1.0, base_confidence)
    
    def _render_network_graph(self, relationships: List[EntityRelationship]):
        """Render network graph visualization of entity relationships"""
        
        if not relationships:
            st.info("No relationships to visualize")
            return
        
        # Create network data
        nodes = set()
        edges = []
        
        for rel in relationships:
            nodes.add(rel.entity1)
            nodes.add(rel.entity2)
            edges.append({
                'from': rel.entity1,
                'to': rel.entity2,
                'label': rel.relationship_type,
                'weight': rel.confidence
            })
        
        # Simple network visualization using HTML/CSS
        network_html = """
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; background: #f9f9f9; margin: 10px 0;">
            <h4>🕸️ Entity Network Graph</h4>
            <p>Network visualization showing relationships between entities:</p>
        """
        
        # Add nodes
        network_html += "<div style='margin: 10px 0;'><strong>Entities:</strong> "
        for node in sorted(nodes):
            network_html += f"<span style='background: #e3f2fd; padding: 4px 8px; margin: 2px; border-radius: 12px; font-size: 0.9em;'>{node}</span> "
        network_html += "</div>"
        
        # Add relationships
        network_html += "<div style='margin: 10px 0;'><strong>Relationships:</strong><ul>"
        for rel in relationships[:10]:  # Show top 10 relationships
            confidence_color = "#4caf50" if rel.confidence > 0.7 else "#ff9800" if rel.confidence > 0.5 else "#f44336"
            network_html += f"""
            <li style='margin: 5px 0;'>
                <strong>{rel.entity1}</strong> 
                <span style='color: {confidence_color}; font-weight: bold;'>→ {rel.relationship_type} →</span> 
                <strong>{rel.entity2}</strong> 
                <span style='color: #666; font-size: 0.8em;'>({rel.confidence:.2f})</span>
            </li>
            """
        network_html += "</ul></div></div>"
        
        st.markdown(network_html, unsafe_allow_html=True)
    
    def _render_relationship_matrix(self, relationships: List[EntityRelationship]):
        """Render matrix view of entity relationships"""
        
        if not relationships:
            st.info("No relationships to display in matrix")
            return
        
        # Create relationship matrix data
        entities = set()
        for rel in relationships:
            entities.add(rel.entity1)
            entities.add(rel.entity2)
        
        entities = sorted(list(entities))
        
        # Create matrix
        matrix_data = []
        for entity1 in entities:
            row = {"Entity": entity1}
            for entity2 in entities:
                if entity1 == entity2:
                    row[entity2] = "—"
                else:
                    # Find relationship
                    rel_found = None
                    for rel in relationships:
                        if (rel.entity1 == entity1 and rel.entity2 == entity2) or \
                           (rel.entity1 == entity2 and rel.entity2 == entity1):
                            rel_found = rel
                            break
                    
                    if rel_found:
                        row[entity2] = f"{rel_found.relationship_type} ({rel_found.confidence:.2f})"
                    else:
                        row[entity2] = ""
            
            matrix_data.append(row)
        
        if matrix_data:
            df = pd.DataFrame(matrix_data)
            st.dataframe(df, use_container_width=True)
    
    def _render_relationship_timeline(self, relationships: List[EntityRelationship], entities: Dict[str, List[str]]):
        """Render timeline view of entity relationships"""
        
        # Check if we have temporal entities
        temporal_entities = entities.get("DATE", []) + entities.get("TIME", [])
        
        if not temporal_entities:
            st.info("No temporal entities found for timeline visualization")
            return
        
        # Create timeline visualization
        timeline_html = """
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; background: #f9f9f9; margin: 10px 0;">
            <h4>📅 Entity Relationship Timeline</h4>
        """
        
        # Sort temporal entities (basic sorting)
        sorted_temporal = sorted(temporal_entities)
        
        for temp_entity in sorted_temporal:
            timeline_html += f"<div style='margin: 10px 0; padding: 10px; background: white; border-radius: 5px;'>"
            timeline_html += f"<strong>📅 {temp_entity}</strong><br>"
            
            # Find relationships involving this temporal entity
            related_entities = []
            for rel in relationships:
                if rel.entity1 == temp_entity:
                    related_entities.append(f"{rel.relationship_type} → {rel.entity2}")
                elif rel.entity2 == temp_entity:
                    related_entities.append(f"{rel.entity1} → {rel.relationship_type}")
            
            if related_entities:
                timeline_html += "<ul>"
                for related in related_entities[:5]:  # Show top 5
                    timeline_html += f"<li style='color: #666; font-size: 0.9em;'>{related}</li>"
                timeline_html += "</ul>"
            else:
                timeline_html += "<em style='color: #999;'>No relationships found</em>"
            
            timeline_html += "</div>"
        
        timeline_html += "</div>"
        
        st.markdown(timeline_html, unsafe_allow_html=True)
    
    def _apply_entity_filters(self, 
                            entities: Dict[str, List[str]], 
                            entity_confidence: Optional[Dict],
                            search_query: str,
                            selected_types: List[str],
                            min_confidence: float,
                            min_length: int,
                            min_frequency: int,
                            regex_pattern: str,
                            case_sensitive: bool) -> Dict[str, List[str]]:
        """Apply various filters to entities"""
        
        filtered_entities = {}
        
        # Count entity frequencies
        entity_counts = defaultdict(int)
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                entity_counts[entity] += 1
        
        for entity_type in selected_types:
            if entity_type not in entities:
                continue
            
            filtered_list = []
            
            for entity in entities[entity_type]:
                # Apply filters
                
                # Search query filter
                if search_query:
                    if case_sensitive:
                        if search_query not in entity:
                            continue
                    else:
                        if search_query.lower() not in entity.lower():
                            continue
                
                # Confidence filter
                if entity_confidence and entity_type in entity_confidence:
                    confidence = entity_confidence[entity_type].get(entity, 0.0)
                    if confidence < min_confidence:
                        continue
                
                # Length filter
                if len(entity) < min_length:
                    continue
                
                # Frequency filter
                if entity_counts[entity] < min_frequency:
                    continue
                
                # Regex pattern filter
                if regex_pattern:
                    try:
                        flags = 0 if case_sensitive else re.IGNORECASE
                        if not re.search(regex_pattern, entity, flags):
                            continue
                    except re.error:
                        # Invalid regex, skip this filter
                        pass
                
                filtered_list.append(entity)
            
            if filtered_list:
                filtered_entities[entity_type] = filtered_list
        
        return filtered_entities
    
    def _display_filtered_entities(self, filtered_entities: Dict[str, List[str]], entity_confidence: Optional[Dict]):
        """Display filtered entities with enhanced formatting"""
        
        if not filtered_entities:
            st.info("No entities match the current filters")
            return
        
        st.markdown("### 🎯 Filtered Results")
        
        for entity_type, entity_list in filtered_entities.items():
            color = self.entity_colors.get(entity_type, "#cccccc")
            icon = self.entity_icons.get(entity_type, "🏷️")
            
            with st.expander(f"{icon} {entity_type} ({len(entity_list)} entities)", expanded=True):
                
                # Create entity tags
                entity_html = '<div style="margin: 0.5rem 0; line-height: 2;">'
                
                for entity in entity_list:
                    confidence = None
                    if entity_confidence and entity_type in entity_confidence:
                        confidence = entity_confidence[entity_type].get(entity, None)
                    
                    confidence_text = f" ({confidence:.2f})" if confidence else ""
                    
                    entity_html += f"""
                    <span style="
                        background: linear-gradient(135deg, {color}20, {color}10);
                        border: 1px solid {color}40;
                        border-radius: 20px;
                        color: var(--text-primary-color);
                        display: inline-block;
                        font-size: 0.85rem;
                        font-weight: 500;
                        margin: 2px 4px;
                        padding: 6px 12px;
                        transition: all 0.3s ease;
                        cursor: pointer;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)';" 
                       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                        {entity}{confidence_text}
                    </span>
                    """
                
                entity_html += '</div>'
                st.markdown(entity_html, unsafe_allow_html=True)
    
    def _generate_json_report(self, 
                            entities: Dict[str, List[str]], 
                            entity_confidence: Optional[Dict],
                            relationships: Optional[List[EntityRelationship]],
                            transcript: str,
                            include_confidence: bool,
                            include_relationships: bool) -> str:
        """Generate JSON format report"""
        
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_entities": sum(len(entity_list) for entity_list in entities.values()),
                "entity_types": list(entities.keys()),
                "transcript_length": len(transcript)
            },
            "entities": {}
        }
        
        # Add entities
        for entity_type, entity_list in entities.items():
            report_data["entities"][entity_type] = []
            
            for entity in entity_list:
                entity_data = {"text": entity}
                
                if include_confidence and entity_confidence and entity_type in entity_confidence:
                    entity_data["confidence"] = entity_confidence[entity_type].get(entity, 0.0)
                
                report_data["entities"][entity_type].append(entity_data)
        
        # Add relationships
        if include_relationships and relationships:
            report_data["relationships"] = [rel.to_dict() for rel in relationships]
        
        # Add transcript
        if transcript:
            report_data["transcript"] = transcript
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _generate_csv_report(self, 
                           entities: Dict[str, List[str]], 
                           entity_confidence: Optional[Dict],
                           include_confidence: bool) -> str:
        """Generate CSV format report"""
        
        csv_data = []
        
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                row = {
                    "Entity_Type": entity_type,
                    "Entity_Text": entity
                }
                
                if include_confidence and entity_confidence and entity_type in entity_confidence:
                    row["Confidence"] = entity_confidence[entity_type].get(entity, 0.0)
                
                csv_data.append(row)
        
        if not csv_data:
            return "Entity_Type,Entity_Text\n"
        
        # Convert to CSV
        df = pd.DataFrame(csv_data)
        return df.to_csv(index=False)
    
    def _generate_pdf_report(self, 
                           entities: Dict[str, List[str]], 
                           entity_confidence: Optional[Dict],
                           relationships: Optional[List[EntityRelationship]],
                           transcript: str,
                           include_confidence: bool,
                           include_relationships: bool) -> bytes:
        """Generate PDF format report (placeholder - would need reportlab)"""
        
        # For now, return a simple text-based PDF content
        # In a real implementation, you would use reportlab or similar
        
        pdf_content = f"""
Entity Extraction Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY
=======
Total Entities: {sum(len(entity_list) for entity_list in entities.values())}
Entity Types: {len(entities)}

ENTITIES BY TYPE
================
"""
        
        for entity_type, entity_list in entities.items():
            pdf_content += f"\n{entity_type} ({len(entity_list)} entities):\n"
            for entity in entity_list:
                confidence_text = ""
                if include_confidence and entity_confidence and entity_type in entity_confidence:
                    confidence = entity_confidence[entity_type].get(entity, 0.0)
                    confidence_text = f" (confidence: {confidence:.2f})"
                
                pdf_content += f"  - {entity}{confidence_text}\n"
        
        if include_relationships and relationships:
            pdf_content += f"\nRELATIONSHIPS ({len(relationships)} found):\n"
            for rel in relationships:
                pdf_content += f"  - {rel.entity1} → {rel.relationship_type} → {rel.entity2} (confidence: {rel.confidence:.2f})\n"
        
        if transcript:
            pdf_content += f"\nORIGINAL TRANSCRIPT:\n{transcript}\n"
        
        return pdf_content.encode('utf-8')
    
    def _generate_xml_report(self, 
                           entities: Dict[str, List[str]], 
                           entity_confidence: Optional[Dict],
                           relationships: Optional[List[EntityRelationship]],
                           include_confidence: bool,
                           include_relationships: bool) -> str:
        """Generate XML format report"""
        
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += f'<entity_report generated_at="{datetime.now().isoformat()}">\n'
        
        # Add metadata
        xml_content += '  <metadata>\n'
        xml_content += f'    <total_entities>{sum(len(entity_list) for entity_list in entities.values())}</total_entities>\n'
        xml_content += f'    <entity_types>{len(entities)}</entity_types>\n'
        xml_content += '  </metadata>\n'
        
        # Add entities
        xml_content += '  <entities>\n'
        for entity_type, entity_list in entities.items():
            xml_content += f'    <entity_type name="{entity_type}" count="{len(entity_list)}">\n'
            
            for entity in entity_list:
                confidence_attr = ""
                if include_confidence and entity_confidence and entity_type in entity_confidence:
                    confidence = entity_confidence[entity_type].get(entity, 0.0)
                    confidence_attr = f' confidence="{confidence:.3f}"'
                
                xml_content += f'      <entity{confidence_attr}>{entity}</entity>\n'
            
            xml_content += '    </entity_type>\n'
        xml_content += '  </entities>\n'
        
        # Add relationships
        if include_relationships and relationships:
            xml_content += '  <relationships>\n'
            for rel in relationships:
                xml_content += f'    <relationship confidence="{rel.confidence:.3f}">\n'
                xml_content += f'      <entity1>{rel.entity1}</entity1>\n'
                xml_content += f'      <type>{rel.relationship_type}</type>\n'
                xml_content += f'      <entity2>{rel.entity2}</entity2>\n'
                xml_content += f'      <context>{rel.context}</context>\n'
                xml_content += '    </relationship>\n'
            xml_content += '  </relationships>\n'
        
        xml_content += '</entity_report>\n'
        
        return xml_content
    
    def _generate_excel_report(self, 
                             entities: Dict[str, List[str]], 
                             entity_confidence: Optional[Dict],
                             relationships: Optional[List[EntityRelationship]],
                             include_confidence: bool,
                             include_relationships: bool) -> bytes:
        """Generate Excel format report"""
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        try:
            import pandas as pd
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Entities sheet
                entity_data = []
                for entity_type, entity_list in entities.items():
                    for entity in entity_list:
                        row = {
                            "Entity_Type": entity_type,
                            "Entity_Text": entity
                        }
                        
                        if include_confidence and entity_confidence and entity_type in entity_confidence:
                            row["Confidence"] = entity_confidence[entity_type].get(entity, 0.0)
                        
                        entity_data.append(row)
                
                if entity_data:
                    entities_df = pd.DataFrame(entity_data)
                    entities_df.to_excel(writer, sheet_name='Entities', index=False)
                
                # Relationships sheet
                if include_relationships and relationships:
                    rel_data = [rel.to_dict() for rel in relationships]
                    if rel_data:
                        relationships_df = pd.DataFrame(rel_data)
                        relationships_df.to_excel(writer, sheet_name='Relationships', index=False)
                
                # Summary sheet
                summary_data = {
                    "Metric": ["Total Entities", "Entity Types", "Generated At"],
                    "Value": [
                        sum(len(entity_list) for entity_list in entities.values()),
                        len(entities),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            output.seek(0)
            return output.read()
            
        except ImportError:
            # Fallback to CSV if pandas/openpyxl not available
            return self._generate_csv_report(entities, entity_confidence, include_confidence).encode('utf-8')
    
    def _filter_entities_for_correction(self, 
                                      entities: Dict[str, List[str]], 
                                      entity_confidence: Optional[Dict],
                                      correction_mode: str) -> Dict[str, List[str]]:
        """Filter entities based on correction mode"""
        
        if correction_mode == "Review All":
            return entities
        
        elif correction_mode == "Low Confidence Only":
            if not entity_confidence:
                return {}
            
            filtered_entities = {}
            for entity_type, entity_list in entities.items():
                if entity_type not in entity_confidence:
                    continue
                
                low_conf_entities = []
                for entity in entity_list:
                    confidence = entity_confidence[entity_type].get(entity, 0.8)
                    if confidence < 0.7:  # Low confidence threshold
                        low_conf_entities.append(entity)
                
                if low_conf_entities:
                    filtered_entities[entity_type] = low_conf_entities
            
            return filtered_entities
        
        elif correction_mode == "By Entity Type":
            # This would be handled by the UI allowing selection of specific types
            return entities
        
        return entities
    
    def _find_entity_context(self, entity: str, transcript: str, context_window: int = 50) -> str:
        """Find context around an entity in the transcript"""
        
        entity_pos = transcript.lower().find(entity.lower())
        if entity_pos == -1:
            return ""
        
        start_pos = max(0, entity_pos - context_window)
        end_pos = min(len(transcript), entity_pos + len(entity) + context_window)
        
        context = transcript[start_pos:end_pos]
        
        # Add ellipsis if truncated
        if start_pos > 0:
            context = "..." + context
        if end_pos < len(transcript):
            context = context + "..."
        
        return context


def create_entity_visualizer() -> EntityVisualizer:
    """Factory function to create EntityVisualizer instance"""
    return EntityVisualizer()


def render_enhanced_entity_display(entities: Dict[str, List[str]], 
                                 entity_confidence: Optional[Dict] = None,
                                 transcript: str = "",
                                 show_all_features: bool = True) -> Dict[str, Any]:
    """
    Main function to render all enhanced entity visualization features
    
    Args:
        entities: Dictionary of entity types and instances
        entity_confidence: Optional confidence scores
        transcript: Original transcript text
        show_all_features: Whether to show all visualization features
        
    Returns:
        Dictionary with all user interactions and results
    """
    
    if not entities:
        st.info("No entities available for visualization")
        return {}
    
    visualizer = create_entity_visualizer()
    results = {}
    
    # Create tabs for different visualization features
    if show_all_features:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎯 Interactive Highlighting", 
            "🔗 Relationships", 
            "🔍 Search & Filter", 
            "📥 Export Reports", 
            "✏️ Manual Correction"
        ])
        
        with tab1:
            results['highlighting'] = visualizer.render_interactive_entity_highlighting(
                transcript, entities, show_confidence=bool(entity_confidence)
            )
        
        with tab2:
            results['relationships'] = visualizer.render_entity_relationship_map(
                entities, transcript
            )
        
        with tab3:
            results['filtering'] = visualizer.render_entity_filtering_search(
                entities, entity_confidence
            )
        
        with tab4:
            results['reports'] = visualizer.render_exportable_reports(
                entities, entity_confidence, results.get('relationships', []), transcript
            )
        
        with tab5:
            results['corrections'] = visualizer.render_confidence_scoring_correction(
                entities, entity_confidence, transcript
            )
    
    else:
        # Show simplified version with just highlighting and basic features
        results['highlighting'] = visualizer.render_interactive_entity_highlighting(
            transcript, entities, show_confidence=bool(entity_confidence)
        )
        
        with st.expander("🔍 Advanced Features", expanded=False):
            results['filtering'] = visualizer.render_entity_filtering_search(
                entities, entity_confidence
            )
    
    return results