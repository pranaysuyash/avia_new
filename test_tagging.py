#!/usr/bin/env python3
"""
Test script to demonstrate AI-powered content tagging
"""

import streamlit as st
from tagging import (
    TagManager, Tag, TagCategory,
    render_tagging_view, render_tag_cloud,
    MockAIProvider
)
import time
from datetime import datetime


# Sample content for testing
SAMPLE_CONTENTS = {
    "Technology Article": """
    Artificial Intelligence and Machine Learning: Transforming the Future of Technology
    
    In recent years, artificial intelligence (AI) and machine learning (ML) have emerged as transformative technologies 
    that are reshaping industries across the globe. From healthcare to finance, transportation to entertainment, 
    AI-powered solutions are driving innovation and efficiency at an unprecedented scale.
    
    Python has become the dominant programming language for AI development, with frameworks like TensorFlow, PyTorch, 
    and scikit-learn leading the way. Companies like Google, Microsoft, and Amazon are investing billions in AI research,
    while startups are leveraging these technologies to solve complex problems.
    
    The impact of deep learning and neural networks has been particularly profound in computer vision and natural 
    language processing. Models like GPT-3 and BERT have demonstrated remarkable capabilities in understanding and 
    generating human-like text, while computer vision systems can now identify objects, faces, and even emotions 
    with high accuracy.
    
    As we look to the future, ethical considerations around AI bias, privacy, and job displacement must be addressed. 
    The development of explainable AI and responsible AI practices will be crucial for building trust and ensuring 
    these powerful technologies benefit humanity as a whole.
    
    Contact: ai-research@techcompany.com | Published: March 15, 2024 | www.ai-future.tech
    """,
    
    "Business Report": """
    Q4 2023 Financial Performance and Strategic Outlook
    
    Executive Summary:
    Our company achieved record-breaking revenue of $2.5 billion in Q4 2023, representing a 35% year-over-year growth. 
    This exceptional performance was driven by strong customer acquisition, successful product launches, and strategic 
    market expansion into Asia-Pacific regions.
    
    Key Highlights:
    - Revenue: $2.5B (+35% YoY)
    - Net Profit: $450M (+42% YoY)
    - Customer Base: 1.2M active users (+28% YoY)
    - Market Share: 23% in North America, 18% in Europe
    
    Strategic Initiatives:
    The board has approved a $300M investment in R&D for 2024, focusing on artificial intelligence integration and 
    cloud infrastructure optimization. Our partnership with Microsoft Azure will enable us to scale operations while 
    reducing costs by an estimated 20%.
    
    CEO John Smith stated, "This quarter's results demonstrate the strength of our business model and the dedication 
    of our 5,000+ employees worldwide. We remain optimistic about our growth trajectory and committed to delivering 
    value to our shareholders."
    
    Looking ahead, we project 25-30% revenue growth for FY2024, with expansion plans in Tokyo, Singapore, and Mumbai. 
    The upcoming product launch in June 2024 is expected to capture additional market share in the enterprise segment.
    
    For more information, contact: investor.relations@company.com
    """,
    
    "Scientific Paper Abstract": """
    Climate Change Impact on Coral Reef Ecosystems: A Comprehensive Study of the Great Barrier Reef
    
    Abstract:
    This study presents a comprehensive analysis of climate change impacts on coral reef ecosystems, with a specific 
    focus on the Great Barrier Reef, Australia. Using satellite imagery, underwater sensors, and machine learning 
    algorithms, we analyzed data from 2015-2023 to assess coral bleaching events, species diversity changes, and 
    ecosystem resilience.
    
    Our findings indicate a 43% increase in severe bleaching events compared to the previous decade, with water 
    temperature anomalies exceeding 2°C during summer months. The research identified critical threshold temperatures 
    of 29.5°C for widespread bleaching initiation. Species diversity decreased by 18% in affected areas, with 
    particular vulnerability observed in Acropora and Pocillopora genera.
    
    However, we also discovered encouraging signs of adaptation in certain coral populations, suggesting potential 
    for ecosystem recovery under appropriate conservation measures. The study recommends immediate implementation of 
    marine protected areas, reduction of local stressors, and global cooperation on carbon emission reduction.
    
    Keywords: climate change, coral bleaching, Great Barrier Reef, marine biodiversity, ecosystem resilience, 
    environmental conservation, ocean acidification
    
    Authors: Dr. Sarah Johnson (Marine Biology Institute), Prof. Michael Chen (University of Queensland), 
    Dr. Emma Williams (CSIRO Marine Research)
    
    Published: Environmental Science Journal, January 2024 | DOI: 10.1234/esj.2024.001
    """
}


def main():
    st.set_page_config(
        page_title="AI-Powered Content Tagging Demo",
        page_icon="🏷️",
        layout="wide"
    )
    
    st.title("🏷️ AI-Powered Content Tagging Demo")
    st.markdown("Demonstrating intelligent content analysis and automatic tag generation")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Live Demo", "Custom Content", "Tag Management", "API Example"
    ])
    
    with tab1:
        st.header("🔄 Live Tagging Demo")
        
        # Content selection
        selected_content = st.selectbox(
            "Select Sample Content",
            list(SAMPLE_CONTENTS.keys())
        )
        
        # Display content
        with st.expander("📄 View Content", expanded=True):
            st.text(SAMPLE_CONTENTS[selected_content])
        
        # Tagging interface
        st.markdown("---")
        tags = render_tagging_view(
            SAMPLE_CONTENTS[selected_content],
            editable=True
        )
        
        # Show generated tags summary
        if tags:
            st.markdown("---")
            st.success(f"Generated {len(tags)} tags across {len(set(t.category for t in tags))} categories")
    
    with tab2:
        st.header("✏️ Tag Custom Content")
        
        # Custom content input
        custom_content = st.text_area(
            "Enter your content to tag",
            height=300,
            placeholder="Paste or type your content here..."
        )
        
        if custom_content:
            # Tagging interface for custom content
            st.markdown("---")
            custom_tags = render_tagging_view(
                custom_content,
                editable=True
            )
    
    with tab3:
        st.header("🔧 Tag Management")
        
        # Manual tag creation
        st.subheader("Create Custom Tags")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Create individual tag
            st.markdown("#### Individual Tag")
            tag_text = st.text_input("Tag Text")
            tag_category = st.selectbox(
                "Category",
                [cat.value for cat in TagCategory]
            )
            tag_confidence = st.slider("Confidence", 0.0, 1.0, 0.8)
            
            if st.button("Create Tag"):
                if tag_text:
                    manager = TagManager()
                    new_tag = Tag(
                        id=manager._generate_tag_id(tag_text),
                        text=tag_text,
                        category=TagCategory(tag_category),
                        confidence=tag_confidence,
                        frequency=1,
                        source='manual',
                        metadata={'created_via': 'demo'},
                        created_at=datetime.now()
                    )
                    st.success(f"Created tag: {tag_text}")
                    
                    # Display the tag
                    render_tag_cloud([new_tag])
        
        with col2:
            # Bulk tag import
            st.markdown("#### Bulk Import")
            tag_list = st.text_area(
                "Tags (one per line)",
                height=150,
                placeholder="tag1\ntag2\ntag3"
            )
            bulk_category = st.selectbox(
                "Default Category",
                [cat.value for cat in TagCategory],
                key="bulk_category"
            )
            
            if st.button("Import Tags"):
                if tag_list:
                    tags = []
                    manager = TagManager()
                    
                    for line in tag_list.strip().split('\n'):
                        if line.strip():
                            tag = Tag(
                                id=manager._generate_tag_id(line.strip()),
                                text=line.strip(),
                                category=TagCategory(bulk_category),
                                confidence=0.7,
                                frequency=1,
                                source='import',
                                metadata={'imported': True},
                                created_at=datetime.now()
                            )
                            tags.append(tag)
                    
                    st.success(f"Imported {len(tags)} tags")
                    render_tag_cloud(tags)
        
        # Tag rules
        st.markdown("---")
        st.subheader("Custom Tagging Rules")
        
        with st.expander("Add Custom Rule"):
            rule_name = st.text_input("Rule Name")
            rule_tag = st.text_input("Tag to Apply")
            rule_category = st.selectbox(
                "Tag Category",
                [cat.value for cat in TagCategory],
                key="rule_category"
            )
            
            rule_type = st.radio("Rule Type", ["Keywords", "Pattern"])
            
            if rule_type == "Keywords":
                keywords = st.text_input(
                    "Keywords (comma-separated)",
                    placeholder="keyword1, keyword2, keyword3"
                )
            else:
                pattern = st.text_input(
                    "Regular Expression Pattern",
                    placeholder=r"\b(word1|word2)\b"
                )
            
            if st.button("Add Rule"):
                manager = TagManager()
                
                try:
                    if rule_type == "Keywords":
                        manager.add_custom_rule(
                            name=rule_name,
                            tag=rule_tag,
                            category=rule_category,
                            keywords=keywords.split(',')
                        )
                    else:
                        manager.add_custom_rule(
                            name=rule_name,
                            tag=rule_tag,
                            category=rule_category,
                            pattern=pattern
                        )
                    
                    st.success(f"Added rule: {rule_name}")
                except Exception as e:
                    st.error(f"Error adding rule: {e}")
    
    with tab4:
        st.header("🔌 API Example")
        
        st.markdown("""
        ### Using the Tag Manager API
        
        The Tag Manager can be used programmatically in your Python applications:
        
        ```python
        from tagging import TagManager, MockAIProvider
        
        # Initialize tag manager with AI provider
        provider = MockAIProvider()  # Or OpenAIProvider, LocalModelProvider
        manager = TagManager(ai_provider=provider)
        
        # Generate tags for content
        content = "Your text content here..."
        tags = manager.generate_tags(
            content,
            max_tags=20,
            min_confidence=0.5
        )
        
        # Access tag properties
        for tag in tags:
            print(f"{tag.text} ({tag.category.value}) - {tag.confidence:.0%}")
        
        # Export tags
        json_data = manager.export_tags(tags, format="json")
        csv_data = manager.export_tags(tags, format="csv")
        
        # Add custom rules
        manager.add_custom_rule(
            name="my_rule",
            tag="Custom Tag",
            category="topic",
            keywords=["trigger", "words"]
        )
        ```
        
        ### Available AI Providers
        
        1. **OpenAI Provider**: Uses GPT models for intelligent tagging
        2. **Local Model Provider**: Uses Hugging Face models for offline tagging
        3. **Mock Provider**: For testing without API dependencies
        
        ### Tag Categories
        
        - **Topic**: General subject matter
        - **Person**: Names and people
        - **Location**: Places and geographical entities
        - **Organization**: Companies and institutions
        - **Date**: Temporal references
        - **Concept**: Abstract ideas
        - **Technical**: Technical terms
        - **Sentiment**: Emotional tone
        - **Action**: Verbs and activities
        - **Product**: Products and services
        - **Event**: Events and occurrences
        - **Custom**: User-defined categories
        """)
        
        # Interactive API tester
        st.markdown("---")
        st.subheader("Try the API")
        
        test_content = st.text_area(
            "Test Content",
            value="Python is a great programming language for machine learning.",
            height=100
        )
        
        if st.button("Generate Tags (API)"):
            with st.spinner("Processing..."):
                # Simulate API call
                provider = MockAIProvider()
                manager = TagManager(ai_provider=provider)
                
                tags = manager.generate_tags(test_content, max_tags=10)
                
                # Show results
                st.json([tag.to_dict() for tag in tags])
    
    # Sidebar
    with st.sidebar:
        st.header("📚 About AI Tagging")
        
        st.markdown("""
        ### Features
        - 🤖 **AI-Powered**: Uses advanced NLP for intelligent tagging
        - 📊 **Multi-Category**: Supports 12+ tag categories
        - 🎯 **High Accuracy**: Confidence scoring for each tag
        - 🔍 **Pattern Detection**: Extracts dates, emails, URLs
        - 📏 **Custom Rules**: Define your own tagging logic
        - 🌐 **Multi-Provider**: OpenAI, local models, or mock
        - 📈 **Analytics**: Visualize tag distributions
        - 💾 **Export Options**: JSON, CSV, text formats
        
        ### Use Cases
        - Content categorization
        - Document indexing
        - SEO optimization
        - Knowledge management
        - Content discovery
        - Trend analysis
        - Compliance checking
        - Research organization
        
        ### Tag Sources
        - **AI**: Generated by AI models
        - **Pattern**: Extracted via regex
        - **Rule**: Applied via custom rules
        - **Manual**: Added by users
        - **Import**: Bulk imported
        - **Suggestion**: Related tag suggestions
        """)


if __name__ == "__main__":
    main()