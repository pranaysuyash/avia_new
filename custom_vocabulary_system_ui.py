"""
Streamlit UI for Custom Vocabulary and Domain Adaptation System

This module provides a comprehensive user interface for managing custom vocabulary,
including user submissions, verification workflows, domain adaptation, and analytics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import logging

# Import the main vocabulary system
try:
    from custom_vocabulary_system import (
        CustomVocabularySystem, DomainCategory, VocabularyStatus,
        VocabularyEntry, ValidationResult
    )
except ImportError:
    st.error("Could not import custom_vocabulary_system module. Please ensure it's available.")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_session_state():
    """Initialize session state variables"""
    if 'vocab_system' not in st.session_state:
        st.session_state.vocab_system = CustomVocabularySystem()
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = "demo_user"
    
    if 'user_role' not in st.session_state:
        st.session_state.user_role = "contributor"  # contributor, verifier, admin
    
    if 'selected_domain' not in st.session_state:
        st.session_state.selected_domain = "general"

def display_vocabulary_submission():
    """Display vocabulary submission form"""
    st.header("📝 Submit New Vocabulary")
    
    with st.form("vocabulary_submission"):
        col1, col2 = st.columns(2)
        
        with col1:
            term = st.text_input(
                "Term *",
                help="The vocabulary term or phrase"
            )
            
            domain = st.selectbox(
                "Domain *",
                options=[domain.value for domain in DomainCategory],
                help="Select the domain category for this term"
            )
            
            pronunciation = st.text_input(
                "Pronunciation (Optional)",
                help="IPA or phonetic pronunciation guide"
            )
        
        with col2:
            alternatives = st.text_area(
                "Alternative Terms",
                help="Enter alternative terms, one per line"
            )
            
            tags = st.text_input(
                "Tags",
                help="Comma-separated tags for categorization"
            )
            
            source_refs = st.text_area(
                "Source References",
                help="References or sources for this term, one per line"
            )
        
        definition = st.text_area(
            "Definition *",
            height=100,
            help="Clear and comprehensive definition of the term"
        )
        
        context_examples = st.text_area(
            "Context Examples *",
            height=100,
            help="Usage examples showing the term in context, one per line"
        )
        
        submitted = st.form_submit_button("🚀 Submit Vocabulary", type="primary")
        
        if submitted:
            if not term or not definition or not context_examples:
                st.error("Please fill in all required fields (marked with *)")
            else:
                # Process form data
                alternatives_list = [alt.strip() for alt in alternatives.split('\n') if alt.strip()]
                tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                source_refs_list = [ref.strip() for ref in source_refs.split('\n') if ref.strip()]
                examples_list = [ex.strip() for ex in context_examples.split('\n') if ex.strip()]
                
                # Submit vocabulary
                success, message, entry = st.session_state.vocab_system.submit_vocabulary(
                    term=term,
                    definition=definition,
                    domain=domain,
                    submitter_id=st.session_state.current_user,
                    context_examples=examples_list,
                    pronunciation=pronunciation if pronunciation else None,
                    alternatives=alternatives_list,
                    tags=tags_list,
                    source_references=source_refs_list
                )
                
                if success:
                    st.success(f"✅ {message}")
                    if entry:
                        st.info(f"Entry ID: {entry['id']}")
                        if entry['pronunciation']:
                            st.info(f"Generated pronunciation: {entry['pronunciation']} ({entry['phonetic_spelling']})")
                else:
                    st.error(f"❌ {message}")

def display_vocabulary_search():
    """Display vocabulary search interface"""
    st.header("🔍 Search Vocabulary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("Search Terms", placeholder="Enter search query...")
    
    with col2:
        search_domain = st.selectbox(
            "Filter by Domain",
            options=["all"] + [domain.value for domain in DomainCategory]
        )
    
    with col3:
        search_status = st.selectbox(
            "Filter by Status",
            options=["approved", "pending", "rejected", "all"]
        )
    
    if st.button("🔍 Search", type="primary") or search_query:
        # Perform search
        domain_filter = None if search_domain == "all" else search_domain
        status_filter = None if search_status == "all" else search_status
        
        results = st.session_state.vocab_system.search_vocabulary(
            query=search_query or "",
            domain=domain_filter,
            status=status_filter
        )
        
        if results:
            st.success(f"Found {len(results)} vocabulary entries")
            
            # Display results
            for entry in results:
                with st.expander(f"📖 {entry['term']} ({entry['domain']})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Definition:** {entry['definition']}")
                        
                        if entry['pronunciation']:
                            st.write(f"**Pronunciation:** {entry['pronunciation']} ({entry['phonetic_spelling']})")
                        
                        if entry['alternatives']:
                            st.write(f"**Alternatives:** {', '.join(entry['alternatives'])}")
                        
                        if entry['context_examples']:
                            st.write("**Examples:**")
                            for example in entry['context_examples']:
                                st.write(f"• {example}")
                        
                        if entry['tags']:
                            st.write(f"**Tags:** {', '.join(entry['tags'])}")
                    
                    with col2:
                        st.metric("Status", entry['status'].title())
                        st.metric("Usage Count", entry['usage_count'])
                        st.metric("Accuracy", f"{entry['accuracy_score']:.2f}")
                        st.metric("Confidence", f"{entry['confidence_score']:.2f}")
                        
                        # Usage feedback
                        if entry['status'] == 'approved':
                            feedback = st.slider(
                                "Rate Accuracy",
                                0.0, 1.0, 0.5,
                                key=f"feedback_{entry['id']}"
                            )
                            
                            if st.button("Submit Feedback", key=f"submit_{entry['id']}"):
                                st.session_state.vocab_system.update_vocabulary_usage(
                                    entry['id'],
                                    st.session_state.current_user,
                                    "search_interface",
                                    feedback
                                )
                                st.success("Feedback submitted!")
        else:
            st.info("No vocabulary entries found matching your search criteria.")

def display_verification_interface():
    """Display vocabulary verification interface for verifiers"""
    if st.session_state.user_role not in ["verifier", "admin"]:
        st.warning("⚠️ You need verifier or admin privileges to access this section.")
        return
    
    st.header("✅ Vocabulary Verification")
    
    # Get pending submissions
    pending_submissions = st.session_state.vocab_system.get_pending_submissions()
    
    if not pending_submissions:
        st.info("🎉 No pending vocabulary submissions to verify!")
        return
    
    st.success(f"📋 {len(pending_submissions)} submissions pending verification")
    
    for entry in pending_submissions:
        with st.expander(f"🔍 Verify: {entry['term']} ({entry['domain']})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Term:** {entry['term']}")
                st.write(f"**Domain:** {entry['domain']}")
                st.write(f"**Definition:** {entry['definition']}")
                
                if entry['pronunciation']:
                    st.write(f"**Pronunciation:** {entry['pronunciation']} ({entry['phonetic_spelling']})")
                
                if entry['alternatives']:
                    st.write(f"**Alternatives:** {', '.join(entry['alternatives'])}")
                
                if entry['context_examples']:
                    st.write("**Context Examples:**")
                    for example in entry['context_examples']:
                        st.write(f"• {example}")
                
                if entry['tags']:
                    st.write(f"**Tags:** {', '.join(entry['tags'])}")
                
                if entry['source_references']:
                    st.write("**Source References:**")
                    for ref in entry['source_references']:
                        st.write(f"• {ref}")
            
            with col2:
                st.write(f"**Submitted by:** {entry['submitter_id']}")
                st.write(f"**Submitted:** {entry['created_at']}")
                st.metric("Confidence Score", f"{entry['confidence_score']:.2f}")
                
                # Verification form
                with st.form(f"verify_{entry['id']}"):
                    verification_decision = st.radio(
                        "Verification Decision",
                        options=["Approve", "Reject"],
                        key=f"decision_{entry['id']}"
                    )
                    
                    verification_notes = st.text_area(
                        "Verification Notes",
                        placeholder="Optional notes about the verification decision...",
                        key=f"notes_{entry['id']}"
                    )
                    
                    if st.form_submit_button("Submit Verification"):
                        approved = verification_decision == "Approve"
                        
                        success = st.session_state.vocab_system.verify_vocabulary(
                            entry['id'],
                            st.session_state.current_user,
                            approved,
                            verification_notes
                        )
                        
                        if success:
                            status = "approved" if approved else "rejected"
                            st.success(f"✅ Vocabulary {status} successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Error processing verification")

def display_domain_management():
    """Display domain-specific vocabulary management"""
    st.header("🏢 Domain Management")
    
    # Domain selection
    selected_domain = st.selectbox(
        "Select Domain",
        options=[domain.value for domain in DomainCategory],
        index=[domain.value for domain in DomainCategory].index(st.session_state.selected_domain)
    )
    
    st.session_state.selected_domain = selected_domain
    
    # Domain vocabulary overview
    domain_vocab = st.session_state.vocab_system.get_domain_vocabulary(selected_domain)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Terms", len(domain_vocab))
    
    with col2:
        avg_usage = sum(entry['usage_count'] for entry in domain_vocab) / len(domain_vocab) if domain_vocab else 0
        st.metric("Avg Usage", f"{avg_usage:.1f}")
    
    with col3:
        avg_accuracy = sum(entry['accuracy_score'] for entry in domain_vocab) / len(domain_vocab) if domain_vocab else 0
        st.metric("Avg Accuracy", f"{avg_accuracy:.2f}")
    
    with col4:
        high_usage_terms = sum(1 for entry in domain_vocab if entry['usage_count'] > 10)
        st.metric("High Usage Terms", high_usage_terms)
    
    # Domain adaptation
    st.subheader("🧠 Domain Adaptation")
    
    with st.expander("Adapt Vocabulary from Text Corpus"):
        st.write("Upload or paste text content to automatically extract domain-specific vocabulary.")
        
        adaptation_method = st.radio(
            "Input Method",
            options=["Text Input", "File Upload"]
        )
        
        text_corpus = []
        
        if adaptation_method == "Text Input":
            corpus_text = st.text_area(
                "Text Corpus",
                height=200,
                placeholder="Paste domain-specific text content here..."
            )
            if corpus_text:
                text_corpus = [corpus_text]
        
        else:
            uploaded_files = st.file_uploader(
                "Upload Text Files",
                type=['txt', 'md'],
                accept_multiple_files=True
            )
            
            if uploaded_files:
                for file in uploaded_files:
                    content = file.read().decode('utf-8')
                    text_corpus.append(content)
        
        if st.button("🚀 Adapt Vocabulary") and text_corpus:
            with st.spinner("Analyzing text corpus and extracting domain terms..."):
                adapted_terms = st.session_state.vocab_system.adapt_domain_vocabulary(
                    selected_domain, text_corpus
                )
            
            if adapted_terms:
                st.success(f"✅ Found {len(adapted_terms)} potential new terms for {selected_domain}")
                
                # Display suggested terms
                st.subheader("Suggested Terms")
                for i, term in enumerate(adapted_terms[:20]):  # Show top 20
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{term}**")
                        # Get pronunciation
                        ipa, phonetic = st.session_state.vocab_system.get_pronunciation(term)
                        st.caption(f"Pronunciation: {ipa} ({phonetic})")
                    
                    with col2:
                        if st.button("Add Term", key=f"add_term_{i}"):
                            st.info(f"Please use the submission form to add '{term}' with proper definition and examples.")
            else:
                st.info("No new terms found for adaptation.")
    
    # Domain vocabulary list
    if domain_vocab:
        st.subheader(f"📚 {selected_domain.title()} Vocabulary")
        
        # Create DataFrame for display
        vocab_df = pd.DataFrame([
            {
                'Term': entry['term'],
                'Definition': entry['definition'][:100] + "..." if len(entry['definition']) > 100 else entry['definition'],
                'Usage Count': entry['usage_count'],
                'Accuracy': f"{entry['accuracy_score']:.2f}",
                'Status': entry['status'].title()
            }
            for entry in domain_vocab
        ])
        
        st.dataframe(vocab_df, use_container_width=True)

def display_analytics_dashboard():
    """Display vocabulary analytics dashboard"""
    st.header("📊 Vocabulary Analytics")
    
    # Get analytics data
    analytics = st.session_state.vocab_system.get_vocabulary_analytics()
    
    if not analytics:
        st.error("Unable to load analytics data")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Entries", analytics.get('total_entries', 0))
    
    with col2:
        approved_count = analytics.get('status_distribution', {}).get('approved', 0)
        st.metric("Approved", approved_count)
    
    with col3:
        pending_count = analytics.get('status_distribution', {}).get('pending', 0)
        st.metric("Pending", pending_count)
    
    with col4:
        avg_usage = analytics.get('average_usage_count', 0)
        st.metric("Avg Usage", f"{avg_usage:.1f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Status distribution pie chart
        if analytics.get('status_distribution'):
            status_data = analytics['status_distribution']
            fig_status = px.pie(
                values=list(status_data.values()),
                names=list(status_data.keys()),
                title="Vocabulary Status Distribution"
            )
            st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Top domains bar chart
        if analytics.get('top_domains'):
            domain_data = analytics['top_domains']
            fig_domains = px.bar(
                x=list(domain_data.keys()),
                y=list(domain_data.values()),
                title="Vocabulary by Domain",
                labels={'x': 'Domain', 'y': 'Count'}
            )
            fig_domains.update_xaxes(tickangle=45)
            st.plotly_chart(fig_domains, use_container_width=True)
    
    # Domain-specific analytics
    st.subheader("🏢 Domain-Specific Analytics")
    
    selected_domain_analytics = st.selectbox(
        "Select Domain for Detailed Analytics",
        options=["all"] + [domain.value for domain in DomainCategory]
    )
    
    if selected_domain_analytics != "all":
        domain_analytics = st.session_state.vocab_system.get_vocabulary_analytics(selected_domain_analytics)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(f"{selected_domain_analytics.title()} Terms", domain_analytics.get('total_entries', 0))
        
        with col2:
            domain_avg_usage = domain_analytics.get('average_usage_count', 0)
            st.metric("Domain Avg Usage", f"{domain_avg_usage:.1f}")
        
        with col3:
            domain_avg_accuracy = domain_analytics.get('average_accuracy_score', 0)
            st.metric("Domain Avg Accuracy", f"{domain_avg_accuracy:.2f}")

def display_pronunciation_guide():
    """Display pronunciation guide and tools"""
    st.header("🗣️ Pronunciation Guide")
    
    st.write("""
    This tool helps generate phonetic transcriptions and pronunciation guides for vocabulary terms.
    """)
    
    # Pronunciation generator
    col1, col2 = st.columns(2)
    
    with col1:
        term_for_pronunciation = st.text_input(
            "Enter Term",
            placeholder="Type a word or phrase..."
        )
        
        if st.button("🎵 Generate Pronunciation") and term_for_pronunciation:
            ipa, phonetic = st.session_state.vocab_system.get_pronunciation(term_for_pronunciation)
            
            st.success("✅ Pronunciation Generated")
            st.write(f"**IPA:** {ipa}")
            st.write(f"**Phonetic Spelling:** {phonetic}")
    
    with col2:
        st.subheader("📚 Pronunciation Guide")
        st.write("""
        **IPA (International Phonetic Alphabet)** symbols used:
        
        **Vowels:**
        - /i/ - "ee" as in "see"
        - /ɪ/ - "i" as in "sit"
        - /ɛ/ - "e" as in "bed"
        - /æ/ - "a" as in "cat"
        - /ɑ/ - "a" as in "father"
        - /ɔ/ - "o" as in "law"
        - /ʊ/ - "u" as in "put"
        - /u/ - "oo" as in "boot"
        - /ʌ/ - "u" as in "but"
        - /ə/ - "a" as in "about"
        
        **Consonants:**
        - /θ/ - "th" as in "think"
        - /ð/ - "th" as in "this"
        - /ʃ/ - "sh" as in "ship"
        - /ʒ/ - "s" as in "measure"
        - /tʃ/ - "ch" as in "chair"
        - /dʒ/ - "j" as in "judge"
        - /ŋ/ - "ng" as in "sing"
        """)

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Custom Vocabulary System",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Custom Vocabulary & Domain Adaptation System")
    st.markdown("Comprehensive vocabulary management with user submissions, verification, and domain adaptation")
    
    # Initialize session state
    init_session_state()
    
    # Sidebar for navigation and user settings
    with st.sidebar:
        st.header("🎛️ Navigation")
        
        # User settings
        st.subheader("👤 User Settings")
        st.session_state.current_user = st.text_input("User ID", value=st.session_state.current_user)
        st.session_state.user_role = st.selectbox(
            "Role",
            options=["contributor", "verifier", "admin"],
            index=["contributor", "verifier", "admin"].index(st.session_state.user_role)
        )
        
        st.divider()
        
        # Navigation menu
        page = st.selectbox(
            "Select Page",
            options=[
                "🔍 Search Vocabulary",
                "📝 Submit Vocabulary",
                "✅ Verify Submissions",
                "🏢 Domain Management",
                "📊 Analytics Dashboard",
                "🗣️ Pronunciation Guide"
            ]
        )
        
        st.divider()
        
        # Quick stats
        st.subheader("📈 Quick Stats")
        try:
            analytics = st.session_state.vocab_system.get_vocabulary_analytics()
            st.metric("Total Vocabulary", analytics.get('total_entries', 0))
            st.metric("Pending Review", analytics.get('status_distribution', {}).get('pending', 0))
            st.metric("Approved Terms", analytics.get('status_distribution', {}).get('approved', 0))
        except Exception as e:
            st.error(f"Error loading stats: {e}")
    
    # Main content area
    if page == "🔍 Search Vocabulary":
        display_vocabulary_search()
    
    elif page == "📝 Submit Vocabulary":
        display_vocabulary_submission()
    
    elif page == "✅ Verify Submissions":
        display_verification_interface()
    
    elif page == "🏢 Domain Management":
        display_domain_management()
    
    elif page == "📊 Analytics Dashboard":
        display_analytics_dashboard()
    
    elif page == "🗣️ Pronunciation Guide":
        display_pronunciation_guide()
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Custom Vocabulary & Domain Adaptation System | 
        Supporting all domains and industries with verified, validated vocabulary</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()