"""
Streamlit Interactive Learning Interface
Bridge to the sophisticated transcription correction system
Provides guided learning for transcription improvement
"""

import streamlit as st
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from streamlit_unified_components import UnifiedComponents

class StreamlitLearningInterface:
    """Interactive learning interface for Streamlit"""
    
    def __init__(self):
        self.unified = UnifiedComponents()
        if 'learning_session' not in st.session_state:
            st.session_state.learning_session = {
                'corrections_applied': 0,
                'corrections_skipped': 0,
                'accuracy': 0.0,
                'start_time': datetime.now(),
                'suggestions': [],
                'current_suggestion_index': 0
            }
    
    def render_learning_dashboard(self, transcript_id: str, transcript_text: str):
        """Render the main learning interface"""
        
        # Header
        self.unified.accessibility.add_skip_link("learning-content")
        
        st.markdown("# 🧠 Interactive Learning Interface")
        st.markdown("*Improve your transcription accuracy with AI-powered suggestions*")
        
        # Load or analyze transcript
        if st.button("🔍 Analyze Transcript for Learning", type="primary"):
            with st.spinner("Analyzing transcript for correction opportunities..."):
                suggestions = self._get_correction_suggestions(transcript_text)
                st.session_state.learning_session['suggestions'] = suggestions
                st.session_state.learning_session['current_suggestion_index'] = 0
                st.rerun()
        
        # Main content
        st.markdown('<div id="learning-content">', unsafe_allow_html=True)
        
        # Display learning progress
        self._render_progress_header()
        
        # Three-column layout
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            self._render_transcript_panel(transcript_text)
        
        with col2:
            self._render_current_suggestion()
        
        with col3:
            self._render_session_stats()
        
        # Bottom learning insights
        self._render_learning_insights()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_progress_header(self):
        """Render progress indicators"""
        session = st.session_state.learning_session
        suggestions = session.get('suggestions', [])
        
        if not suggestions:
            st.info("👋 Click 'Analyze Transcript' to start your learning session!")
            return
        
        # Progress metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📈 Session Progress",
                value=f"{session['current_suggestion_index'] + 1}/{len(suggestions)}",
                delta=f"{((session['current_suggestion_index'] + 1) / len(suggestions) * 100):.1f}%"
            )
        
        with col2:
            st.metric(
                label="✅ Applied",
                value=session['corrections_applied'],
                delta=f"+{session['corrections_applied']}"
            )
        
        with col3:
            st.metric(
                label="⏭️ Skipped",
                value=session['corrections_skipped'],
                delta=f"+{session['corrections_skipped']}"
            )
        
        with col4:
            accuracy = session['accuracy'] * 100 if session['accuracy'] else 0
            st.metric(
                label="🎯 Accuracy",
                value=f"{accuracy:.1f}%",
                delta=f"{accuracy - 75:.1f}%" if accuracy > 0 else None
            )
        
        # Progress bar
        if suggestions:
            progress = (session['current_suggestion_index'] + 1) / len(suggestions)
            st.progress(progress)
    
    def _render_transcript_panel(self, transcript_text: str):
        """Render transcript with highlighting"""
        st.markdown("### 📝 Transcript")
        
        session = st.session_state.learning_session
        suggestions = session.get('suggestions', [])
        current_index = session.get('current_suggestion_index', 0)
        
        if suggestions and current_index < len(suggestions):
            current_suggestion = suggestions[current_index]
            
            # Highlight current suggestion in transcript
            start_pos = current_suggestion.get('position', {}).get('start', 0)
            end_pos = current_suggestion.get('position', {}).get('end', 0)
            
            highlighted_text = (
                transcript_text[:start_pos] +
                f"**<mark style='background-color: yellow; padding: 2px; border-radius: 3px;'>" +
                f"{transcript_text[start_pos:end_pos]}</mark>**" +
                transcript_text[end_pos:]
            )
            
            st.markdown(
                highlighted_text,
                unsafe_allow_html=True
            )
        else:
            st.text_area(
                "Transcript Content",
                value=transcript_text,
                height=300,
                disabled=True,
                label_visibility="collapsed"
            )
    
    def _render_current_suggestion(self):
        """Render current correction suggestion"""
        st.markdown("### 💡 Current Suggestion")
        
        session = st.session_state.learning_session
        suggestions = session.get('suggestions', [])
        current_index = session.get('current_suggestion_index', 0)
        
        if not suggestions:
            st.info("No suggestions to review yet.")
            return
        
        if current_index >= len(suggestions):
            st.success("🎉 All suggestions reviewed!")
            self._render_session_complete()
            return
        
        suggestion = suggestions[current_index]
        
        # Suggestion details
        correction_type = suggestion.get('type', 'unknown').replace('_', ' ').title()
        confidence = suggestion.get('confidence', 0) * 100
        
        # Type indicator with emoji
        type_emoji = {
            'spelling': '📝',
            'grammar': '📚',
            'punctuation': '🎯',
            'capitalization': '🔤',
            'word_boundary': '✂️'
        }.get(suggestion.get('type'), '✏️')
        
        st.markdown(f"**{type_emoji} {correction_type}**")
        
        # Confidence indicator
        confidence_color = "green" if confidence >= 80 else "orange" if confidence >= 60 else "red"
        st.markdown(f"<span style='color: {confidence_color}'>**Confidence: {confidence:.1f}%**</span>", 
                   unsafe_allow_html=True)
        
        # Original vs Suggested
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Original:**")
            st.code(suggestion.get('original', ''), language=None)
        
        with col2:
            st.markdown("**Suggested:**")
            st.code(suggestion.get('suggested', ''), language=None)
        
        # Explanation
        if suggestion.get('explanation'):
            st.markdown("**💭 Explanation:**")
            st.info(suggestion['explanation'])
        
        # Learning points
        if suggestion.get('learningPoints'):
            st.markdown("**💡 Learning Points:**")
            for point in suggestion['learningPoints']:
                st.markdown(f"• {point}")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("❌ Skip", key=f"skip_{current_index}"):
                self._handle_suggestion_action(suggestion, False)
        
        with col2:
            if st.button("✅ Apply", key=f"apply_{current_index}", type="primary"):
                self._handle_suggestion_action(suggestion, True)
    
    def _render_session_stats(self):
        """Render session statistics"""
        st.markdown("### 📊 Session Stats")
        
        session = st.session_state.learning_session
        
        # Time spent
        elapsed = datetime.now() - session['start_time']
        minutes = int(elapsed.total_seconds() / 60)
        
        st.metric("⏱️ Time", f"{minutes}m")
        
        # Create a simple chart of progress
        if session['corrections_applied'] + session['corrections_skipped'] > 0:
            fig = go.Figure(data=[
                go.Bar(
                    x=['Applied', 'Skipped'],
                    y=[session['corrections_applied'], session['corrections_skipped']],
                    marker_color=['green', 'orange']
                )
            ])
            fig.update_layout(
                title="Actions Taken",
                height=200,
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Learning mode selector
        st.markdown("**🎯 Learning Mode**")
        mode = st.selectbox(
            "Mode",
            ["Guided", "Challenge", "Review"],
            key="learning_mode",
            label_visibility="collapsed"
        )
        
        # Quick actions
        st.markdown("**⚡ Quick Actions**")
        
        if st.button("🔄 Re-analyze", help="Get fresh suggestions"):
            st.session_state.learning_session['suggestions'] = []
            st.rerun()
        
        if st.button("📚 Learning Guide", help="Open help guide"):
            st.info("💡 **Tip**: Focus on understanding why corrections are suggested rather than just applying them!")
    
    def _render_learning_insights(self):
        """Render learning insights and recommendations"""
        st.markdown("---")
        st.markdown("### 🎓 Learning Insights")
        
        session = st.session_state.learning_session
        suggestions = session.get('suggestions', [])
        
        if not suggestions:
            return
        
        # Analyze common error types
        error_types = {}
        for suggestion in suggestions:
            error_type = suggestion.get('type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        if error_types:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📈 Error Type Distribution**")
                fig = px.pie(
                    values=list(error_types.values()),
                    names=list(error_types.keys()),
                    title="Common Error Types"
                )
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**💡 Personalized Recommendations**")
                
                # Find most common error type
                most_common = max(error_types.items(), key=lambda x: x[1])
                
                recommendations = {
                    'spelling': "💡 **Focus on**: Double-check unfamiliar words and proper nouns",
                    'grammar': "💡 **Focus on**: Review subject-verb agreement and sentence structure",
                    'punctuation': "💡 **Focus on**: Practice comma placement and end punctuation",
                    'capitalization': "💡 **Focus on**: Remember proper noun and sentence start capitalization",
                    'word_boundary': "💡 **Focus on**: Listen carefully to word breaks and compound words"
                }
                
                if most_common[0] in recommendations:
                    st.info(recommendations[most_common[0]])
                
                # Achievement badges
                accuracy = session.get('accuracy', 0)
                if accuracy > 0.8:
                    st.success("🏆 **Achievement Unlocked**: High Accuracy!")
                elif accuracy > 0.6:
                    st.info("🥉 **Achievement Unlocked**: Good Progress!")
    
    def _render_session_complete(self):
        """Render session completion screen"""
        session = st.session_state.learning_session
        
        st.balloons()
        st.success("🎉 **Session Complete!**")
        
        final_accuracy = session.get('accuracy', 0) * 100
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Final Accuracy", f"{final_accuracy:.1f}%")
        
        with col2:
            st.metric("Corrections Applied", session['corrections_applied'])
        
        with col3:
            elapsed = datetime.now() - session['start_time']
            minutes = int(elapsed.total_seconds() / 60)
            st.metric("Time Spent", f"{minutes}m")
        
        # Achievements
        if final_accuracy >= 90:
            st.success("🏆 **Excellent Work!** - 90%+ accuracy achieved")
        elif final_accuracy >= 75:
            st.info("🥈 **Great Job!** - 75%+ accuracy achieved")
        elif final_accuracy >= 50:
            st.warning("🥉 **Good Effort!** - Keep practicing to improve")
        
        # Reset button
        if st.button("🔄 Start New Session"):
            st.session_state.learning_session = {
                'corrections_applied': 0,
                'corrections_skipped': 0,
                'accuracy': 0.0,
                'start_time': datetime.now(),
                'suggestions': [],
                'current_suggestion_index': 0
            }
            st.rerun()
    
    def _handle_suggestion_action(self, suggestion: Dict, accepted: bool):
        """Handle user action on suggestion"""
        session = st.session_state.learning_session
        
        if accepted:
            session['corrections_applied'] += 1
            # In real implementation, would apply correction to transcript
        else:
            session['corrections_skipped'] += 1
        
        # Calculate accuracy
        total_actions = session['corrections_applied'] + session['corrections_skipped']
        if total_actions > 0:
            session['accuracy'] = session['corrections_applied'] / total_actions
        
        # Move to next suggestion
        session['current_suggestion_index'] += 1
        
        # Record interaction (in real implementation, would send to backend)
        self._record_learning_interaction(suggestion, accepted)
        
        # Rerun to update display
        st.rerun()
    
    def _get_correction_suggestions(self, transcript: str) -> List[Dict]:
        """Get correction suggestions from the backend (mock for now)"""
        
        # In real implementation, would call the correction engine API
        # For demo purposes, return mock suggestions
        
        mock_suggestions = [
            {
                'id': 'suggestion_1',
                'type': 'spelling',
                'original': 'recieve',
                'suggested': 'receive',
                'confidence': 0.95,
                'position': {'start': 10, 'end': 17},
                'explanation': 'Common spelling error: "i before e except after c"',
                'learningPoints': [
                    'Remember: "receive" follows the "i before e except after c" rule',
                    'Other similar words: perceive, conceive, deceive'
                ]
            },
            {
                'id': 'suggestion_2', 
                'type': 'grammar',
                'original': 'The data is',
                'suggested': 'The data are',
                'confidence': 0.75,
                'position': {'start': 50, 'end': 61},
                'explanation': 'Data is plural, so use "are" instead of "is"',
                'learningPoints': [
                    'Data is the plural form of datum',
                    'Use "are" with plural subjects'
                ]
            },
            {
                'id': 'suggestion_3',
                'type': 'punctuation', 
                'original': 'However the results',
                'suggested': 'However, the results',
                'confidence': 0.88,
                'position': {'start': 80, 'end': 97},
                'explanation': 'Introductory words like "however" need a comma',
                'learningPoints': [
                    'Use commas after introductory words',
                    'Other examples: Therefore, Moreover, Nevertheless'
                ]
            }
        ]
        
        return mock_suggestions
    
    def _record_learning_interaction(self, suggestion: Dict, accepted: bool):
        """Record learning interaction (mock for now)"""
        # In real implementation, would send to backend API
        interaction_data = {
            'suggestion_id': suggestion.get('id'),
            'accepted': accepted,
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.get('session_id', 'demo_session')
        }
        
        # For now, just log to session state for demo
        if 'interaction_log' not in st.session_state:
            st.session_state.interaction_log = []
        
        st.session_state.interaction_log.append(interaction_data)


def demo_learning_interface():
    """Demo the interactive learning interface"""
    
    # Initialize the interface
    learning = StreamlitLearningInterface()
    
    # Sample transcript for demo
    sample_transcript = """
    The machine learning model was trained on a large dataset of transcribed audio files. 
    However the results showed that we need to recieve more training data to improve accuracy. 
    The data is promising but we need more samples to validate our approach.
    """
    
    # Render the interface
    learning.render_learning_dashboard(
        transcript_id="demo_transcript_123",
        transcript_text=sample_transcript
    )
    
    # Show interaction log in sidebar for demo
    with st.sidebar:
        if st.session_state.get('interaction_log'):
            st.markdown("### 📊 Interaction Log")
            for i, interaction in enumerate(st.session_state.interaction_log[-5:]):
                action = "✅ Applied" if interaction['accepted'] else "❌ Skipped"
                st.markdown(f"**{i+1}.** {action}")


if __name__ == "__main__":
    demo_learning_interface()