#!/usr/bin/env python3
"""
Clinical Intelligence Assistant UI - Streamlit Interface
User interface for the Intent-First Clinical Intelligence Assistant
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any

# Import the clinical intelligence assistant
try:
    from clinical_intelligence_assistant import ClinicalIntelligenceAssistant
    CLINICAL_INTELLIGENCE_AVAILABLE = True
except ImportError:
    CLINICAL_INTELLIGENCE_AVAILABLE = False
    st.error("Clinical Intelligence Assistant not available")

def main():
    st.set_page_config(
        page_title="Clinical Intelligence Assistant",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 Clinical Intelligence Assistant")
    st.markdown("**Intent-First Transformation**: From Documentation to Decision Support")
    
    if not CLINICAL_INTELLIGENCE_AVAILABLE:
        st.error("Clinical Intelligence Assistant is not available. Please check the installation.")
        return
    
    # Sidebar for patient information
    with st.sidebar:
        st.header("Patient Information")
        
        patient_age = st.number_input("Age", min_value=0, max_value=120, value=45)
        patient_gender = st.selectbox("Gender", ["male", "female", "other"])
        
        st.subheader("Medical History")
        medical_history = st.multiselect(
            "Select conditions",
            ["hypertension", "diabetes", "heart_disease", "asthma", "copd", 
             "depression", "anxiety", "arthritis", "cancer_history"]
        )
        
        st.subheader("Current Medications")
        medications_text = st.text_area(
            "Enter medications (one per line)",
            placeholder="lisinopril\nmetformin\naspirin"
        )
        current_medications = [med.strip() for med in medications_text.split('\n') if med.strip()]
        
        specialty = st.selectbox(
            "Clinical Specialty",
            ["internal_medicine", "cardiology", "pulmonology", "neurology", 
             "emergency_medicine", "family_medicine"]
        )
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Clinical Transcription")
        
        # Sample transcriptions for demo
        sample_transcriptions = {
            "Chest Pain": """Patient presents with chest pain that started 2 hours ago. 
Pain is substernal, 7/10 intensity, radiating to left arm.
Associated with shortness of breath and diaphoresis.
Patient appears anxious and diaphoretic.
Vital signs: BP 150/90, HR 95, RR 20, O2 sat 96%.""",
            
            "Diabetes Follow-up": """Patient returns for diabetes follow-up. 
Reports good adherence to metformin. 
Blood sugars have been running 120-140 fasting.
No polyuria, polydipsia, or polyphagia.
Feet examination shows no ulcers or neuropathy.
A1C from last month was 7.2%.""",
            
            "Hypertension Check": """Patient here for blood pressure check.
Home readings have been elevated 150-160/90-95.
Currently on lisinopril 10mg daily.
No headaches, vision changes, or chest pain.
Denies medication side effects.
Physical exam shows BP 158/92."""
        }
        
        selected_sample = st.selectbox("Choose sample or enter custom:", 
                                     ["Custom"] + list(sample_transcriptions.keys()))
        
        if selected_sample != "Custom":
            default_text = sample_transcriptions[selected_sample]
        else:
            default_text = ""
        
        transcription = st.text_area(
            "Enter clinical transcription:",
            value=default_text,
            height=200,
            placeholder="Enter the clinical encounter transcription here..."
        )
        
        analyze_button = st.button("🧠 Analyze Clinical Intelligence", type="primary")
    
    with col2:
        st.header("Clinical Decision Support")
        
        if analyze_button and transcription:
            with st.spinner("Analyzing clinical intelligence..."):
                try:
                    # Initialize the assistant
                    assistant = ClinicalIntelligenceAssistant()
                    
                    # Run the analysis
                    result = asyncio.run(assistant.get_clinical_intelligence(
                        transcription=transcription,
                        patient_age=patient_age,
                        patient_gender=patient_gender,
                        medical_history=medical_history,
                        current_medications=current_medications,
                        specialty=specialty
                    ))
                    
                    # Display results
                    display_clinical_intelligence_results(result)
                    
                except Exception as e:
                    st.error(f"Error analyzing clinical intelligence: {str(e)}")
        
        elif not transcription and analyze_button:
            st.warning("Please enter a clinical transcription to analyze.")

def display_clinical_intelligence_results(result: Dict[str, Any]):
    """Display the clinical intelligence analysis results"""
    
    # Patient Summary
    st.subheader("👤 Patient Summary")
    st.info(result['patient_summary'])
    
    # Quality Score
    quality_score = result.get('quality_score', 0)
    st.metric("📊 Clinical Quality Score", f"{quality_score:.1%}")
    
    # Key Clinical Insights
    st.subheader("🧠 Key Clinical Insights")
    insights = result.get('key_insights', [])
    
    if insights:
        for i, insight in enumerate(insights):
            with st.expander(f"💡 {insight['title']} ({insight['confidence']} confidence)"):
                st.write(f"**Description:** {insight['description']}")
                st.write(f"**Urgency:** {insight['urgency'].title()}")
                
                if insight.get('actions'):
                    st.write("**Recommended Actions:**")
                    for action in insight['actions']:
                        st.write(f"• {action}")
                
                if insight.get('questions'):
                    st.write("**Follow-up Questions:**")
                    for question in insight['questions']:
                        st.write(f"• {question}")
    else:
        st.info("No specific clinical insights identified.")
    
    # Diagnostic Suggestions
    st.subheader("🔬 Diagnostic Suggestions")
    diagnostics = result.get('diagnostic_suggestions', [])
    
    if diagnostics:
        for diag in diagnostics:
            with st.expander(f"🎯 {diag['condition']} ({diag['probability']} probability)"):
                if diag.get('supporting_symptoms'):
                    st.write("**Supporting Symptoms:**")
                    st.write(", ".join(diag['supporting_symptoms']))
                
                if diag.get('recommended_tests'):
                    st.write("**Recommended Tests:**")
                    for test in diag['recommended_tests']:
                        st.write(f"• {test}")
                
                if diag.get('red_flags'):
                    st.write("**⚠️ Red Flags:**")
                    for flag in diag['red_flags']:
                        st.write(f"• {flag}")
    else:
        st.info("No specific diagnostic suggestions available.")
    
    # Treatment Recommendations
    st.subheader("💊 Treatment Recommendations")
    treatments = result.get('treatment_recommendations', [])
    
    if treatments:
        for treat in treatments:
            with st.expander(f"💉 {treat['treatment']} for {treat['indication']}"):
                if treat.get('dosage'):
                    st.write(f"**Dosage:** {treat['dosage']}")
                
                if treat.get('monitoring'):
                    st.write("**Monitoring Requirements:**")
                    for monitor in treat['monitoring']:
                        st.write(f"• {monitor}")
                
                if treat.get('contraindications'):
                    st.write("**⚠️ Contraindications:**")
                    for contra in treat['contraindications']:
                        st.write(f"• {contra}")
    else:
        st.info("No specific treatment recommendations available.")
    
    # Risk Assessment
    st.subheader("⚠️ Risk Assessment")
    risks = result.get('risk_assessment', {})
    
    if risks:
        risk_cols = st.columns(len(risks))
        for i, (risk_type, score) in enumerate(risks.items()):
            with risk_cols[i]:
                risk_name = risk_type.replace('_', ' ').title()
                color = "red" if score > 0.7 else "orange" if score > 0.4 else "green"
                st.metric(
                    f"{risk_name} Risk",
                    f"{score:.1%}",
                    delta=None
                )
    
    # Care Gaps
    st.subheader("🔍 Care Gaps Identified")
    care_gaps = result.get('care_gaps', [])
    
    if care_gaps:
        for gap in care_gaps:
            st.warning(f"📋 {gap}")
    else:
        st.success("✅ No significant care gaps identified")
    
    # Preventive Opportunities
    st.subheader("🛡️ Preventive Care Opportunities")
    preventive = result.get('preventive_opportunities', [])
    
    if preventive:
        for opportunity in preventive:
            st.info(f"💡 {opportunity}")
    else:
        st.info("No specific preventive opportunities identified at this time.")
    
    # Transformation Comparison
    st.subheader("🔄 Intent-First Transformation Impact")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔍 BEFORE (Traditional Documentation):**")
        st.markdown("""
        - HIPAA-compliant transcription
        - Medical entity extraction
        - ICD-10 code assignment
        - Clinical note generation
        """)
    
    with col2:
        st.markdown("**✨ AFTER (Clinical Intelligence):**")
        st.markdown("""
        - Clinical decision support
        - Diagnostic suggestions
        - Treatment recommendations
        - Risk stratification
        - Care gap identification
        - Preventive care opportunities
        """)
    
    # Export functionality
    st.subheader("📤 Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Copy to Clipboard"):
            # Format results for clipboard
            clipboard_text = format_results_for_clipboard(result)
            st.code(clipboard_text, language="text")
    
    with col2:
        if st.button("💾 Download JSON"):
            # Prepare JSON download
            json_str = json.dumps(result, indent=2, default=str)
            st.download_button(
                label="Download Clinical Intelligence Report",
                data=json_str,
                file_name=f"clinical_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

def format_results_for_clipboard(result: Dict[str, Any]) -> str:
    """Format results for clipboard copying"""
    
    text = f"""CLINICAL INTELLIGENCE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PATIENT SUMMARY:
{result.get('patient_summary', 'N/A')}

QUALITY SCORE: {result.get('quality_score', 0):.1%}

KEY INSIGHTS:"""
    
    for insight in result.get('key_insights', []):
        text += f"\n• {insight['title']} ({insight['confidence']} confidence)"
        text += f"\n  {insight['description']}"
    
    text += "\n\nDIAGNOSTIC SUGGESTIONS:"
    for diag in result.get('diagnostic_suggestions', []):
        text += f"\n• {diag['condition']} ({diag['probability']} probability)"
    
    text += "\n\nTREATMENT RECOMMENDATIONS:"
    for treat in result.get('treatment_recommendations', []):
        text += f"\n• {treat['treatment']} for {treat['indication']}"
    
    text += "\n\nRISK ASSESSMENT:"
    for risk_type, score in result.get('risk_assessment', {}).items():
        text += f"\n• {risk_type.replace('_', ' ').title()}: {score:.1%}"
    
    return text

if __name__ == "__main__":
    main()