#!/usr/bin/env python3
"""
Demo: Clinical Documentation and Reporting System
Comprehensive demonstration of automated clinical note generation, ICD-10/CPT coding, and quality assessment
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import clinical documentation system
try:
    from clinical_documentation_system import (
        ClinicalDocumentationSystem,
        ClinicalNoteType,
        ClinicalSpecialty,
        DocumentationQuality
    )
except ImportError:
    st.error("Clinical documentation system not found. Please ensure clinical_documentation_system.py is available.")
    st.stop()

def main():
    st.set_page_config(
        page_title="Clinical Documentation Demo",
        page_icon="📋",
        layout="wide"
    )
    
    st.title("📋 Clinical Documentation and Reporting System")
    st.markdown("---")
    st.markdown("**Advanced clinical documentation with automatic note generation, ICD-10/CPT coding, and quality assessment**")
    
    # Sidebar configuration
    st.sidebar.header("🔧 Configuration")
    
    note_type = st.sidebar.selectbox(
        "Clinical Note Type",
        options=[note_type.value for note_type in ClinicalNoteType],
        index=0,
        help="Select the type of clinical note to generate"
    )
    
    specialty = st.sidebar.selectbox(
        "Medical Specialty",
        options=[specialty.value for specialty in ClinicalSpecialty],
        index=0,
        help="Select the medical specialty for specialized documentation"
    )
    
    enable_coding = st.sidebar.checkbox(
        "Enable Medical Coding",
        value=True,
        help="Automatically suggest ICD-10 and CPT codes"
    )
    
    enable_quality_assessment = st.sidebar.checkbox(
        "Enable Quality Assessment",
        value=True,
        help="Assess documentation quality and completeness"
    )
    
    # Main demo tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Clinical Documentation",
        "💰 Medical Coding",
        "📊 Quality Assessment",
        "📈 Analytics Dashboard",
        "🏥 Specialty Templates"
    ])
    
    # Initialize clinical documentation system
    try:
        clinical_system = ClinicalDocumentationSystem()
    except Exception as e:
        st.error(f"Failed to initialize clinical documentation system: {e}")
        return
    
    with tab1:
        demo_clinical_documentation(clinical_system, note_type, specialty, enable_coding, enable_quality_assessment)
    
    with tab2:
        demo_medical_coding(clinical_system)
    
    with tab3:
        demo_quality_assessment(clinical_system)
    
    with tab4:
        demo_analytics_dashboard()
    
    with tab5:
        demo_specialty_templates(clinical_system)

def demo_clinical_documentation(clinical_system, note_type, specialty, enable_coding, enable_quality_assessment):
    """Demo clinical documentation generation"""
    st.subheader("📋 Automated Clinical Documentation")
    
    st.markdown("""
    **Features:**
    - Automatic clinical note generation from transcripts
    - Structured section extraction (SOAP, H&P, etc.)
    - Medical entity recognition and validation
    - ICD-10 diagnostic and CPT procedure code suggestions
    - Quality assessment and improvement recommendations
    """)
    
    # Sample clinical transcripts
    sample_transcripts = {
        "Cardiology Consultation": """
        Chief Complaint: 65-year-old male presents with chest pain and shortness of breath.
        
        History of Present Illness: Patient reports acute onset of substernal chest pain 
        that started 2 hours ago. Pain is 8/10 severity, radiating to left arm. 
        Associated with diaphoresis and nausea. Patient has history of hypertension 
        and diabetes mellitus.
        
        Physical Examination: 
        Vital signs: BP 160/95, HR 110, RR 22, Temp 98.6°F, O2 sat 94%
        General: Appears uncomfortable, diaphoretic
        Cardiovascular: Irregular rhythm, S3 gallop present
        Pulmonary: Bilateral rales at lung bases
        
        Assessment: 
        1. Acute myocardial infarction
        2. Congestive heart failure
        3. Hypertension
        4. Diabetes mellitus
        
        Plan: 
        1. Admit to CCU for monitoring
        2. Start aspirin 325mg daily
        3. Begin metoprolol 25mg BID
        4. Continue lisinopril 10mg daily
        5. Monitor blood glucose, continue metformin
        6. Cardiology consultation
        7. Follow-up echocardiogram
        """,
        
        "Emergency Department Note": """
        Chief Complaint: 45-year-old female presents with severe abdominal pain.
        
        History of Present Illness: Patient reports sudden onset of severe right upper 
        quadrant abdominal pain that started 4 hours ago after eating a fatty meal. 
        Pain is 9/10 severity, radiating to right shoulder. Associated with nausea 
        and vomiting. No fever reported.
        
        Physical Examination:
        Vital signs: BP 140/85, HR 95, RR 18, Temp 99.2°F
        General: Appears uncomfortable, holding right side
        Abdomen: Tender right upper quadrant, positive Murphy's sign
        
        Laboratory: WBC 12,000, Total bilirubin 2.5
        Imaging: Ultrasound shows gallbladder wall thickening and multiple stones
        
        Assessment: Acute cholecystitis
        
        Plan: 
        1. NPO status
        2. IV fluids and pain control
        3. Surgery consultation for cholecystectomy
        4. Antibiotics - ceftriaxone and metronidazole
        """,
        
        "Progress Note": """
        Subjective: Patient reports feeling much better today. Pain has decreased 
        from 8/10 to 3/10. Appetite is improving and no nausea or vomiting since yesterday.
        Ambulating without difficulty.
        
        Objective: 
        Vital signs: BP 125/75, HR 78, RR 16, Temp 98.8°F
        General: Alert and oriented x3, appears comfortable
        Abdomen: Soft, mild tenderness right upper quadrant, bowel sounds present
        Incisions: Clean, dry, and intact with no signs of infection
        
        Assessment: Post-operative day 2 status post laparoscopic cholecystectomy
        Patient recovering well with no complications
        
        Plan: 
        1. Continue current pain medications
        2. Advance diet as tolerated
        3. Physical therapy for ambulation
        4. Discharge planning for tomorrow if continues to improve
        """,
        
        "Discharge Summary": """
        Admission Diagnosis: Acute cholecystitis
        Discharge Diagnosis: Acute cholecystitis, status post laparoscopic cholecystectomy
        
        Hospital Course: 45-year-old female admitted with acute cholecystitis. 
        Underwent successful laparoscopic cholecystectomy on hospital day 1. 
        Post-operative course was uncomplicated. Patient tolerated regular diet 
        and ambulated independently.
        
        Discharge Medications:
        1. Acetaminophen 650mg every 6 hours as needed for pain
        2. Ibuprofen 400mg every 8 hours as needed for pain
        3. Omeprazole 20mg daily for 2 weeks
        
        Discharge Instructions:
        1. No heavy lifting >10 pounds for 2 weeks
        2. May shower, keep incisions dry
        3. Return to work in 1 week if desk job
        4. Follow low-fat diet for 4-6 weeks
        
        Follow-up: Surgery clinic in 2 weeks
        """
    }
    
    # Transcript selection
    selected_transcript = st.selectbox(
        "Select Sample Clinical Transcript:",
        options=list(sample_transcripts.keys()),
        help="Choose a sample clinical transcript to process"
    )
    
    # Text input area
    transcript_text = st.text_area(
        "Clinical Transcript:",
        value=sample_transcripts[selected_transcript],
        height=400,
        help="Enter or modify the clinical transcript text"
    )
    
    if st.button("📋 Generate Clinical Documentation", type="primary"):
        if transcript_text.strip():
            with st.spinner("Generating clinical documentation..."):
                try:
                    # Generate clinical note
                    clinical_note = asyncio.run(
                        clinical_system.generate_clinical_note(
                            transcript_text=transcript_text,
                            note_type=ClinicalNoteType(note_type),
                            specialty=ClinicalSpecialty(specialty),
                            patient_id="DEMO_PATIENT_001",
                            provider_id="DEMO_PROVIDER_001",
                            encounter_id="DEMO_ENCOUNTER_001"
                        )
                    )
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 📄 Generated Clinical Note")
                        
                        # Note summary
                        st.markdown("**Note Information:**")
                        st.markdown(f"• **Type**: {clinical_note.note_type.value.replace('_', ' ').title()}")
                        st.markdown(f"• **Specialty**: {clinical_note.specialty.value.replace('_', ' ').title()}")
                        st.markdown(f"• **Quality**: {clinical_note.overall_quality.value.replace('_', ' ').title()}")
                        st.markdown(f"• **Word Count**: {clinical_note.word_count}")
                        st.markdown(f"• **Time Saved**: {clinical_note.estimated_time_saved:.1f} minutes")
                        
                        # Clinical sections
                        st.markdown("**Clinical Sections:**")
                        for section_name, section in clinical_note.sections.items():
                            with st.expander(f"{section_name.replace('_', ' ').title()}"):
                                st.text_area(
                                    "Content",
                                    value=section.content,
                                    height=100,
                                    disabled=True,
                                    key=f"section_{section_name}"
                                )
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("Quality Score", f"{section.quality_score:.2f}")
                                with col_b:
                                    st.metric("Completeness", f"{section.completeness_score:.2f}")
                                
                                if section.recommendations:
                                    st.markdown("**Recommendations:**")
                                    for rec in section.recommendations:
                                        st.markdown(f"• {rec}")
                    
                    with col2:
                        st.markdown("### 🏥 Clinical Information")
                        
                        # Primary diagnosis
                        if clinical_note.primary_diagnosis:
                            st.markdown("**Primary Diagnosis:**")
                            st.success(clinical_note.primary_diagnosis)
                        
                        # Secondary diagnoses
                        if clinical_note.secondary_diagnoses:
                            st.markdown("**Secondary Diagnoses:**")
                            for diag in clinical_note.secondary_diagnoses:
                                st.markdown(f"• {diag}")
                        
                        # Procedures
                        if clinical_note.procedures:
                            st.markdown("**Procedures:**")
                            for proc in clinical_note.procedures:
                                st.markdown(f"• {proc}")
                        
                        # Medications
                        if clinical_note.medications:
                            st.markdown("**Medications:**")
                            for med in clinical_note.medications:
                                st.markdown(f"• {med}")
                        
                        # Billing codes
                        if enable_coding and clinical_note.billing_codes:
                            st.markdown("**Billing Codes:**")
                            
                            # Separate ICD-10 and CPT codes
                            icd10_codes = [c for c in clinical_note.billing_codes if c.code_type == "ICD-10"]
                            cpt_codes = [c for c in clinical_note.billing_codes if c.code_type == "CPT"]
                            
                            if icd10_codes:
                                st.markdown("*ICD-10 Diagnostic Codes:*")
                                for code in icd10_codes[:3]:  # Show top 3
                                    st.markdown(f"• **{code.code}**: {code.description}")
                                    st.caption(f"Confidence: {code.confidence:.2f}")
                            
                            if cpt_codes:
                                st.markdown("*CPT Procedure Codes:*")
                                for code in cpt_codes[:3]:  # Show top 3
                                    st.markdown(f"• **{code.code}**: {code.description}")
                                    st.caption(f"Confidence: {code.confidence:.2f}, Rate: ${code.reimbursement_rate or 0:.2f}")
                    
                    # Quality assessment
                    if enable_quality_assessment:
                        st.markdown("### 📊 Quality Assessment")
                        
                        # Generate comprehensive report
                        clinical_report = clinical_system.generate_clinical_report(clinical_note)
                        quality_assessment = clinical_report["quality_assessment"]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Completeness", f"{quality_assessment['completeness_score']:.2%}")
                        
                        with col2:
                            st.metric("Accuracy", f"{quality_assessment['accuracy_score']:.2%}")
                        
                        with col3:
                            st.metric("Specificity", f"{quality_assessment['specificity_score']:.2%}")
                        
                        with col4:
                            st.metric("Coding Accuracy", f"{quality_assessment['coding_accuracy']:.2%}")
                        
                        # Missing elements and suggestions
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if quality_assessment["missing_elements"]:
                                st.markdown("**Missing Elements:**")
                                for element in quality_assessment["missing_elements"]:
                                    st.warning(f"• {element}")
                        
                        with col2:
                            if quality_assessment["improvement_suggestions"]:
                                st.markdown("**Improvement Suggestions:**")
                                for suggestion in quality_assessment["improvement_suggestions"]:
                                    st.info(f"• {suggestion}")
                    
                    # Store results in session state for other tabs
                    st.session_state.clinical_note = clinical_note
                    st.session_state.clinical_report = clinical_report
                    
                except Exception as e:
                    st.error(f"Error generating clinical documentation: {e}")
        else:
            st.warning("Please enter a clinical transcript to process.")

def demo_medical_coding(clinical_system):
    """Demo medical coding features"""
    st.subheader("💰 Medical Coding and Billing")
    
    st.markdown("""
    **Medical Coding Features:**
    - ICD-10 diagnostic code suggestions
    - CPT procedure code recommendations
    - HCPCS code integration
    - Reimbursement rate estimates
    - Coding accuracy assessment
    """)
    
    # Medical coding lookup
    st.markdown("### 🔍 Medical Code Lookup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**ICD-10 Diagnostic Codes:**")
        
        # Sample ICD-10 codes
        icd10_samples = [
            {"Code": "I21.9", "Description": "Acute myocardial infarction, unspecified", "Category": "Cardiovascular"},
            {"Code": "I10", "Description": "Essential hypertension", "Category": "Cardiovascular"},
            {"Code": "E11.9", "Description": "Type 2 diabetes mellitus without complications", "Category": "Endocrine"},
            {"Code": "J44.1", "Description": "COPD with acute exacerbation", "Category": "Respiratory"},
            {"Code": "F32.9", "Description": "Major depressive disorder, single episode", "Category": "Psychiatric"}
        ]
        
        icd10_df = pd.DataFrame(icd10_samples)
        st.dataframe(icd10_df, use_container_width=True)
    
    with col2:
        st.markdown("**CPT Procedure Codes:**")
        
        # Sample CPT codes
        cpt_samples = [
            {"Code": "99213", "Description": "Office visit, established patient", "Rate": "$109.00"},
            {"Code": "99214", "Description": "Office visit, moderate complexity", "Rate": "$167.00"},
            {"Code": "93000", "Description": "Electrocardiogram", "Rate": "$25.00"},
            {"Code": "71020", "Description": "Chest X-ray", "Rate": "$42.00"},
            {"Code": "85025", "Description": "Complete blood count", "Rate": "$10.00"}
        ]
        
        cpt_df = pd.DataFrame(cpt_samples)
        st.dataframe(cpt_df, use_container_width=True)
    
    # Coding accuracy assessment
    if hasattr(st.session_state, 'clinical_note'):
        st.markdown("### 📊 Coding Analysis")
        
        clinical_note = st.session_state.clinical_note
        
        if clinical_note.billing_codes:
            # Create coding analysis
            coding_data = []
            total_reimbursement = 0
            
            for code in clinical_note.billing_codes:
                coding_data.append({
                    "Code": code.code,
                    "Type": code.code_type,
                    "Description": code.description,
                    "Confidence": f"{code.confidence:.2%}",
                    "Reimbursement": f"${code.reimbursement_rate or 0:.2f}"
                })
                total_reimbursement += code.reimbursement_rate or 0
            
            coding_df = pd.DataFrame(coding_data)
            st.dataframe(coding_df, use_container_width=True)
            
            # Reimbursement summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Codes", len(clinical_note.billing_codes))
            
            with col2:
                avg_confidence = sum(c.confidence for c in clinical_note.billing_codes) / len(clinical_note.billing_codes)
                st.metric("Avg Confidence", f"{avg_confidence:.2%}")
            
            with col3:
                st.metric("Est. Reimbursement", f"${total_reimbursement:.2f}")

def demo_quality_assessment(clinical_system):
    """Demo quality assessment features"""
    st.subheader("📊 Clinical Documentation Quality Assessment")
    
    st.markdown("""
    **Quality Assessment Features:**
    - Documentation completeness scoring
    - Medical accuracy validation
    - Specificity and detail analysis
    - Coding accuracy assessment
    - Improvement recommendations
    """)
    
    if hasattr(st.session_state, 'clinical_report'):
        clinical_report = st.session_state.clinical_report
        quality_assessment = clinical_report["quality_assessment"]
        
        # Quality metrics visualization
        st.markdown("### 📈 Quality Metrics")
        
        # Create radar chart for quality metrics
        categories = ['Completeness', 'Accuracy', 'Specificity', 'Coding Accuracy']
        values = [
            quality_assessment['completeness_score'],
            quality_assessment['accuracy_score'],
            quality_assessment['specificity_score'],
            quality_assessment['coding_accuracy']
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Quality Scores'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Clinical Documentation Quality Assessment"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed quality breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ✅ Quality Strengths")
            
            # Identify strengths (scores > 0.8)
            strengths = []
            if quality_assessment['completeness_score'] > 0.8:
                strengths.append("Comprehensive documentation")
            if quality_assessment['accuracy_score'] > 0.8:
                strengths.append("High medical accuracy")
            if quality_assessment['specificity_score'] > 0.8:
                strengths.append("Detailed and specific")
            if quality_assessment['coding_accuracy'] > 0.8:
                strengths.append("Accurate medical coding")
            
            if strengths:
                for strength in strengths:
                    st.success(f"• {strength}")
            else:
                st.info("Continue improving documentation quality")
        
        with col2:
            st.markdown("### ⚠️ Areas for Improvement")
            
            # Show improvement suggestions
            if quality_assessment["improvement_suggestions"]:
                for suggestion in quality_assessment["improvement_suggestions"]:
                    st.warning(f"• {suggestion}")
            else:
                st.success("• Documentation meets quality standards")
        
        # Missing elements
        if quality_assessment["missing_elements"]:
            st.markdown("### 📋 Missing Documentation Elements")
            
            missing_df = pd.DataFrame({
                "Missing Element": quality_assessment["missing_elements"],
                "Priority": ["High"] * len(quality_assessment["missing_elements"])
            })
            
            st.dataframe(missing_df, use_container_width=True)
    
    else:
        st.info("Generate a clinical note first to see quality assessment results.")

def demo_analytics_dashboard():
    """Demo analytics dashboard"""
    st.subheader("📈 Clinical Documentation Analytics")
    
    st.markdown("""
    **Analytics Features:**
    - Documentation efficiency metrics
    - Quality trends over time
    - Specialty-specific performance
    - Reimbursement optimization
    - Provider productivity analysis
    """)
    
    # Mock analytics data
    st.markdown("### 📊 Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Time Saved", "18.5 min", delta="2.3 min")
    
    with col2:
        st.metric("Documentation Quality", "87%", delta="5%")
    
    with col3:
        st.metric("Coding Accuracy", "92%", delta="3%")
    
    with col4:
        st.metric("Reimbursement Rate", "$156/note", delta="$12")
    
    # Quality trends
    st.markdown("### 📈 Quality Trends")
    
    # Generate mock trend data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    quality_scores = [0.75 + 0.15 * (i / len(dates)) + 0.05 * (i % 7) / 7 for i in range(len(dates))]
    
    trend_df = pd.DataFrame({
        'Date': dates,
        'Quality Score': quality_scores
    })
    
    fig = px.line(trend_df, x='Date', y='Quality Score', 
                  title='Documentation Quality Trend',
                  range_y=[0.7, 1.0])
    st.plotly_chart(fig, use_container_width=True)
    
    # Specialty performance
    st.markdown("### 🏥 Specialty Performance")
    
    specialty_data = {
        'Specialty': ['Cardiology', 'Emergency Medicine', 'Internal Medicine', 'Surgery', 'Neurology'],
        'Avg Quality': [0.89, 0.85, 0.87, 0.91, 0.83],
        'Time Saved (min)': [22, 15, 18, 25, 20],
        'Reimbursement': [180, 145, 160, 220, 175]
    }
    
    specialty_df = pd.DataFrame(specialty_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(specialty_df, x='Specialty', y='Avg Quality',
                     title='Quality by Specialty')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(specialty_df, x='Specialty', y='Time Saved (min)',
                     title='Time Savings by Specialty')
        st.plotly_chart(fig, use_container_width=True)

def demo_specialty_templates(clinical_system):
    """Demo specialty-specific templates"""
    st.subheader("🏥 Specialty-Specific Documentation Templates")
    
    st.markdown("""
    **Specialty Templates:**
    - Cardiology: Focus on cardiovascular assessment
    - Emergency Medicine: Rapid triage and disposition
    - Surgery: Operative reports and procedures
    - Internal Medicine: Comprehensive evaluations
    - Neurology: Neurological examinations
    """)
    
    # Template selection
    selected_specialty = st.selectbox(
        "Select Medical Specialty:",
        options=[specialty.value for specialty in ClinicalSpecialty],
        help="Choose a specialty to view its documentation template"
    )
    
    selected_note_type = st.selectbox(
        "Select Note Type:",
        options=[note_type.value for note_type in ClinicalNoteType],
        help="Choose the type of clinical note"
    )
    
    if st.button("📋 Generate Template"):
        try:
            # Generate template
            template = clinical_system.template_engine.generate_template(
                ClinicalNoteType(selected_note_type),
                ClinicalSpecialty(selected_specialty)
            )
            
            st.markdown("### 📄 Template Structure")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Required Sections:**")
                for section in template["sections"]:
                    st.markdown(f"• {section.replace('_', ' ').title()}")
                
                st.markdown("**Documentation Format:**")
                st.info(f"Format: {template['format'].title()}")
                st.info(f"Billing Level: {template['billing_level'].replace('_', ' ').title()}")
            
            with col2:
                st.markdown("**Specialty Requirements:**")
                if template.get("specialty_elements"):
                    for element in template["specialty_elements"]:
                        st.markdown(f"• {element.replace('_', ' ').title()}")
                
                st.markdown("**Common Procedures:**")
                if template.get("common_procedures"):
                    for procedure in template["common_procedures"][:5]:
                        st.markdown(f"• {procedure.replace('_', ' ').title()}")
                
                st.markdown("**Key Diagnoses:**")
                if template.get("key_diagnoses"):
                    for diagnosis in template["key_diagnoses"][:5]:
                        st.markdown(f"• {diagnosis.replace('_', ' ').title()}")
            
            # Required elements breakdown
            if template.get("required_elements"):
                st.markdown("### 📋 Required Elements by Section")
                
                for section, elements in template["required_elements"].items():
                    with st.expander(f"{section.replace('_', ' ').title()}"):
                        for element in elements:
                            st.markdown(f"• {element.replace('_', ' ').title()}")
            
        except Exception as e:
            st.error(f"Error generating template: {e}")

if __name__ == "__main__":
    main()