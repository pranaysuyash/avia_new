#!/usr/bin/env python3
"""
Demo: HIPAA-Compliant Medical Transcription System
Comprehensive demonstration of medical transcription with HIPAA compliance
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go

# Import medical transcription system
try:
    from medical_transcription_system import (
        MedicalTranscriptionSystem,
        HIPAACompliance,
        MedicalEntityType,
        HIPAAViolation
    )
except ImportError:
    st.error("Medical transcription system not found. Please ensure medical_transcription_system.py is available.")
    st.stop()

def main():
    st.set_page_config(
        page_title="HIPAA Medical Transcription Demo",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 HIPAA-Compliant Medical Transcription System")
    st.markdown("---")
    st.markdown("**Enterprise-grade medical transcription with comprehensive HIPAA compliance**")
    
    # Sidebar configuration
    st.sidebar.header("🔧 Configuration")
    
    compliance_level = st.sidebar.selectbox(
        "HIPAA Compliance Level",
        options=[level.value for level in HIPAACompliance],
        index=1,
        help="Select the level of HIPAA compliance enforcement"
    )
    
    enable_phi_detection = st.sidebar.checkbox(
        "Enable PHI Detection",
        value=True,
        help="Automatically detect and flag Protected Health Information"
    )
    
    enable_medical_coding = st.sidebar.checkbox(
        "Enable Medical Coding",
        value=True,
        help="Automatically suggest ICD-10 and CPT codes"
    )
    
    enable_audit_logging = st.sidebar.checkbox(
        "Enable Audit Logging",
        value=True,
        help="Log all access and modifications for compliance"
    )
    
    # Main demo tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏥 Medical Transcription",
        "🔒 HIPAA Compliance",
        "📋 Clinical Documentation",
        "📊 Compliance Dashboard",
        "🔍 Medical Coding"
    ])
    
    # Initialize medical transcription system
    try:
        medical_system = MedicalTranscriptionSystem(
            compliance_level=HIPAACompliance(compliance_level)
        )
    except Exception as e:
        st.error(f"Failed to initialize medical transcription system: {e}")
        return
    
    with tab1:
        demo_medical_transcription(medical_system, enable_phi_detection, enable_medical_coding)
    
    with tab2:
        demo_hipaa_compliance(medical_system, enable_phi_detection)
    
    with tab3:
        demo_clinical_documentation(medical_system)
    
    with tab4:
        demo_compliance_dashboard(medical_system)
    
    with tab5:
        demo_medical_coding(medical_system)

def demo_medical_transcription(medical_system, enable_phi_detection, enable_medical_coding):
    """Demo medical transcription with HIPAA compliance"""
    st.subheader("🏥 Medical Transcription Processing")
    
    st.markdown("""
    **Features:**
    - Real-time PHI detection and de-identification
    - Medical terminology recognition and validation
    - Automatic ICD-10 and CPT code suggestions
    - Clinical section extraction and formatting
    - HIPAA-compliant audit logging
    """)
    
    # Sample medical transcripts
    sample_transcripts = {
        "Cardiology Consultation": """
        Patient: John Smith, DOB: 03/15/1975, MRN: 12345678
        
        Chief Complaint: Chest pain and shortness of breath
        
        History of Present Illness: 
        48-year-old male presents with acute onset chest pain that started 2 hours ago. 
        Pain is substernal, radiating to left arm. Associated with diaphoresis and nausea.
        Patient has history of hypertension and diabetes mellitus.
        
        Physical Examination:
        Vital Signs: BP 160/95, HR 110, RR 22, Temp 98.6°F
        Cardiovascular: Irregular rhythm, S3 gallop present
        Pulmonary: Bilateral rales at bases
        
        Assessment and Plan:
        1. Acute myocardial infarction - Start aspirin 325mg, metoprolol 25mg BID
        2. Hypertension - Continue lisinopril 10mg daily
        3. Diabetes mellitus - Monitor blood glucose, continue metformin
        
        Follow-up in cardiology clinic in 1 week.
        """,
        
        "Emergency Department Note": """
        Patient: Mary Johnson, DOB: 07/22/1982, Phone: 555-123-4567
        
        Chief Complaint: Severe abdominal pain
        
        HPI: 41-year-old female presents with sudden onset severe RUQ abdominal pain 
        radiating to right shoulder. Pain started 4 hours ago after eating fatty meal.
        Associated with nausea and vomiting. No fever.
        
        Physical Exam:
        Abdomen: Tender RUQ with positive Murphy's sign
        
        Labs: WBC 12,000, Total bilirubin 2.5
        
        Imaging: Ultrasound shows gallbladder wall thickening and stones
        
        Assessment: Acute cholecystitis
        Plan: NPO, IV fluids, pain control, surgery consult
        """,
        
        "Progress Note": """
        Patient: Robert Davis, MRN: 87654321, Room 302
        
        Subjective: Patient reports feeling better today. Pain decreased from 8/10 to 4/10.
        Appetite improving. No nausea or vomiting.
        
        Objective: 
        Vital Signs: BP 130/80, HR 85, RR 18, Temp 99.1°F
        General: Alert and oriented x3, appears comfortable
        Abdomen: Soft, mild tenderness RUQ, bowel sounds present
        
        Assessment: Post-operative day 2 status post laparoscopic cholecystectomy
        Recovering well, no complications
        
        Plan: 
        1. Continue current medications
        2. Advance diet as tolerated
        3. Ambulation with PT
        4. Discharge planning for tomorrow
        """
    }
    
    # Transcript selection
    selected_transcript = st.selectbox(
        "Select Sample Medical Transcript:",
        options=list(sample_transcripts.keys()),
        help="Choose a sample medical transcript to process"
    )
    
    # Text input area
    transcript_text = st.text_area(
        "Medical Transcript:",
        value=sample_transcripts[selected_transcript],
        height=300,
        help="Enter or modify the medical transcript text"
    )
    
    if st.button("🔍 Process Medical Transcript", type="primary"):
        if transcript_text.strip():
            with st.spinner("Processing medical transcript with HIPAA compliance..."):
                try:
                    # Process transcript
                    result = medical_system.process_transcript(
                        transcript_text,
                        enable_phi_detection=enable_phi_detection,
                        enable_medical_coding=enable_medical_coding
                    )
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 📄 Original Transcript")
                        st.text_area("Original", transcript_text, height=200, disabled=True)
                        
                        # PHI Detection Results
                        if enable_phi_detection and result.get('phi_violations'):
                            st.markdown("### 🚨 PHI Detected")
                            phi_violations = result['phi_violations']
                            
                            for violation in phi_violations[:5]:  # Show first 5
                                severity_color = {
                                    'high': '🔴',
                                    'medium': '🟡',
                                    'low': '🟢'
                                }.get(violation.severity, '⚪')
                                
                                st.markdown(f"{severity_color} **{violation.violation_type}**: {violation.text}")
                                st.caption(f"Recommendation: {violation.recommendation}")
                    
                    with col2:
                        st.markdown("### 🔒 De-identified Transcript")
                        if result.get('anonymized_text'):
                            st.text_area("De-identified", result['anonymized_text'], height=200, disabled=True)
                        
                        # Medical Entities
                        if result.get('medical_entities'):
                            st.markdown("### 🏥 Medical Entities Detected")
                            entities = result['medical_entities']
                            
                            entity_df = pd.DataFrame([
                                {
                                    'Entity': entity.text,
                                    'Type': entity.entity_type.value,
                                    'Confidence': f"{entity.confidence:.2f}",
                                    'Code': entity.medical_code or 'N/A'
                                }
                                for entity in entities[:10]  # Show first 10
                            ])
                            
                            st.dataframe(entity_df, use_container_width=True)
                    
                    # Medical Coding Results
                    if enable_medical_coding and result.get('medical_codes'):
                        st.markdown("### 📋 Medical Coding Suggestions")
                        
                        codes = result['medical_codes']
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if codes.get('icd10_codes'):
                                st.markdown("**ICD-10 Diagnostic Codes:**")
                                for code in codes['icd10_codes']:
                                    st.markdown(f"• **{code['code']}**: {code['description']}")
                        
                        with col2:
                            if codes.get('cpt_codes'):
                                st.markdown("**CPT Procedure Codes:**")
                                for code in codes['cpt_codes']:
                                    st.markdown(f"• **{code['code']}**: {code['description']}")
                    
                    # Compliance Status
                    st.markdown("### ✅ Compliance Status")
                    compliance_score = result.get('compliance_score', 0.0)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Compliance Score", f"{compliance_score:.1%}")
                    
                    with col2:
                        phi_count = len(result.get('phi_violations', []))
                        st.metric("PHI Violations", phi_count)
                    
                    with col3:
                        entity_count = len(result.get('medical_entities', []))
                        st.metric("Medical Entities", entity_count)
                    
                except Exception as e:
                    st.error(f"Error processing transcript: {e}")
        else:
            st.warning("Please enter a medical transcript to process.")

def demo_hipaa_compliance(medical_system, enable_phi_detection):
    """Demo HIPAA compliance features"""
    st.subheader("🔒 HIPAA Compliance Management")
    
    st.markdown("""
    **HIPAA Compliance Features:**
    - Protected Health Information (PHI) detection
    - Safe Harbor de-identification method
    - Audit logging and access controls
    - Breach notification procedures
    - Compliance monitoring and reporting
    """)
    
    # PHI Detection Demo
    st.markdown("### 🔍 PHI Detection Engine")
    
    sample_phi_text = st.text_area(
        "Sample Text with PHI:",
        value="""
        Patient John Doe, DOB 01/15/1980, SSN 123-45-6789, Phone 555-123-4567
        Address: 123 Main Street, Anytown, NY 12345
        Email: john.doe@email.com, MRN: MED123456
        Insurance: Blue Cross Policy #ABC123456789
        """,
        height=150
    )
    
    if st.button("🔍 Detect PHI"):
        if sample_phi_text.strip():
            with st.spinner("Analyzing text for PHI..."):
                try:
                    # Detect PHI
                    phi_violations = medical_system.compliance_checker.detect_phi(sample_phi_text)
                    
                    if phi_violations:
                        st.warning(f"⚠️ Found {len(phi_violations)} potential PHI violations:")
                        
                        # Create PHI violations table
                        phi_data = []
                        for violation in phi_violations:
                            phi_data.append({
                                'Type': violation.violation_type.replace('potential_', '').title(),
                                'Text': violation.text,
                                'Severity': violation.severity.title(),
                                'Recommendation': violation.recommendation
                            })
                        
                        phi_df = pd.DataFrame(phi_data)
                        st.dataframe(phi_df, use_container_width=True)
                        
                        # Show de-identified version
                        st.markdown("### 🔒 De-identified Version")
                        anonymized = medical_system.compliance_checker.anonymize_text(sample_phi_text)
                        st.text_area("De-identified Text", anonymized, height=150, disabled=True)
                        
                    else:
                        st.success("✅ No PHI detected in the text.")
                        
                except Exception as e:
                    st.error(f"Error detecting PHI: {e}")
    
    # Compliance Rules
    st.markdown("### 📋 HIPAA Compliance Rules")
    
    compliance_rules = [
        {
            'Rule': 'PHI Encryption',
            'Status': '✅ Compliant',
            'Description': 'All PHI encrypted at rest and in transit'
        },
        {
            'Rule': 'Access Logging',
            'Status': '✅ Compliant',
            'Description': 'All PHI access logged and auditable'
        },
        {
            'Rule': 'Minimum Necessary',
            'Status': '✅ Compliant',
            'Description': 'Only necessary PHI accessed'
        },
        {
            'Rule': 'Business Associate Agreements',
            'Status': '⚠️ Review Required',
            'Description': 'BAAs required for third parties'
        },
        {
            'Rule': 'Breach Notification',
            'Status': '✅ Compliant',
            'Description': 'Automated breach detection and notification'
        }
    ]
    
    rules_df = pd.DataFrame(compliance_rules)
    st.dataframe(rules_df, use_container_width=True)

def demo_clinical_documentation(medical_system):
    """Demo clinical documentation generation"""
    st.subheader("📋 Clinical Documentation Generation")
    
    st.markdown("""
    **Clinical Documentation Features:**
    - SOAP note generation
    - Clinical section extraction
    - Medical report templates
    - Structured data extraction
    """)
    
    # Report type selection
    report_types = ['consultation', 'progress_note', 'discharge_summary']
    selected_report_type = st.selectbox(
        "Report Type:",
        options=report_types,
        help="Select the type of clinical report to generate"
    )
    
    # Sample clinical text
    clinical_text = st.text_area(
        "Clinical Transcript:",
        value="""
        Chief Complaint: Patient presents with chest pain and shortness of breath.
        
        History of Present Illness: 65-year-old male with history of hypertension 
        and diabetes presents with acute onset chest pain that started 2 hours ago.
        Pain is substernal, 8/10 severity, radiating to left arm.
        
        Physical Examination: 
        Vital signs: BP 160/95, HR 110, RR 22, O2 sat 94%
        Cardiovascular: Irregular rhythm, S3 gallop
        Pulmonary: Bilateral rales
        
        Assessment: Acute myocardial infarction, congestive heart failure
        
        Plan: Admit to CCU, start aspirin, beta blocker, ACE inhibitor
        """,
        height=200
    )
    
    if st.button("📋 Generate Clinical Report"):
        if clinical_text.strip():
            with st.spinner("Generating clinical documentation..."):
                try:
                    # Extract medical entities
                    entities = medical_system.entity_extractor.extract_entities(clinical_text)
                    
                    # Generate report
                    report = medical_system.report_generator.generate_report(
                        clinical_text,
                        entities,
                        report_type=selected_report_type,
                        metadata={
                            'patient_id': 'PATIENT_001',
                            'provider_id': 'PROVIDER_001',
                            'transcript_id': 'TRANSCRIPT_001'
                        }
                    )
                    
                    # Display report sections
                    st.markdown("### 📄 Generated Clinical Report")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Report Information:**")
                        st.markdown(f"• **Type**: {report.report_type.title()}")
                        st.markdown(f"• **Generated**: {report.created_at.strftime('%Y-%m-%d %H:%M')}")
                        st.markdown(f"• **Status**: {report.compliance_status.title()}")
                        
                        st.markdown("**Clinical Sections:**")
                        for section_name, content in report.sections.items():
                            if content.strip():
                                st.markdown(f"**{section_name.replace('_', ' ').title()}:**")
                                st.markdown(content[:200] + "..." if len(content) > 200 else content)
                    
                    with col2:
                        # Medications
                        if report.medications:
                            st.markdown("**Medications:**")
                            for med in report.medications:
                                st.markdown(f"• {med['name']} (Confidence: {med['confidence']:.2f})")
                        
                        # Procedures
                        if report.procedures:
                            st.markdown("**Procedures:**")
                            for proc in report.procedures:
                                st.markdown(f"• {proc['name']} (Confidence: {proc['confidence']:.2f})")
                        
                        # Diagnoses
                        if report.diagnoses:
                            st.markdown("**Diagnoses:**")
                            for diag in report.diagnoses:
                                st.markdown(f"• {diag['name']} (Confidence: {diag['confidence']:.2f})")
                    
                except Exception as e:
                    st.error(f"Error generating clinical report: {e}")

def demo_compliance_dashboard(medical_system):
    """Demo compliance monitoring dashboard"""
    st.subheader("📊 Compliance Monitoring Dashboard")
    
    # Mock compliance data
    compliance_data = {
        'overall_score': 0.92,
        'phi_violations': 3,
        'audit_events': 1247,
        'encrypted_records': 5432,
        'access_violations': 1,
        'compliance_trends': [0.88, 0.90, 0.89, 0.91, 0.92, 0.94, 0.92]
    }
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Overall Compliance",
            f"{compliance_data['overall_score']:.1%}",
            delta="2.1%"
        )
    
    with col2:
        st.metric(
            "PHI Violations",
            compliance_data['phi_violations'],
            delta=-2,
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "Audit Events",
            f"{compliance_data['audit_events']:,}",
            delta="+156"
        )
    
    with col4:
        st.metric(
            "Encrypted Records",
            f"{compliance_data['encrypted_records']:,}",
            delta="+89"
        )
    
    # Compliance trend chart
    st.markdown("### 📈 Compliance Trend")
    
    trend_data = pd.DataFrame({
        'Week': range(1, 8),
        'Compliance Score': compliance_data['compliance_trends']
    })
    
    fig = px.line(
        trend_data,
        x='Week',
        y='Compliance Score',
        title='Weekly Compliance Score Trend',
        markers=True
    )
    fig.update_layout(yaxis_range=[0.8, 1.0])
    st.plotly_chart(fig, use_container_width=True)
    
    # Violation breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚨 Recent Violations")
        violations_data = [
            {'Type': 'Unencrypted PHI', 'Count': 2, 'Severity': 'High'},
            {'Type': 'Unauthorized Access', 'Count': 1, 'Severity': 'Critical'},
            {'Type': 'Missing Audit Log', 'Count': 3, 'Severity': 'Medium'},
            {'Type': 'Weak Password', 'Count': 5, 'Severity': 'Low'}
        ]
        violations_df = pd.DataFrame(violations_data)
        st.dataframe(violations_df, use_container_width=True)
    
    with col2:
        st.markdown("### 📋 Compliance Actions")
        actions_data = [
            {'Action': 'PHI Encryption Review', 'Status': 'In Progress', 'Due': '2024-01-15'},
            {'Action': 'Access Control Audit', 'Status': 'Completed', 'Due': '2024-01-10'},
            {'Action': 'Staff Training Update', 'Status': 'Scheduled', 'Due': '2024-01-20'},
            {'Action': 'Policy Review', 'Status': 'Pending', 'Due': '2024-01-25'}
        ]
        actions_df = pd.DataFrame(actions_data)
        st.dataframe(actions_df, use_container_width=True)

def demo_medical_coding(medical_system):
    """Demo medical coding features"""
    st.subheader("🔍 Medical Coding & Terminology")
    
    st.markdown("""
    **Medical Coding Features:**
    - ICD-10 diagnostic code suggestions
    - CPT procedure code integration
    - Medical terminology validation
    - Drug interaction checking
    - Medical abbreviation expansion
    """)
    
    # Medical term validation
    st.markdown("### 🏥 Medical Term Validation")
    
    medical_term = st.text_input(
        "Enter Medical Term:",
        value="hypertension",
        help="Enter a medical term to validate and get coding information"
    )
    
    if st.button("🔍 Validate Medical Term"):
        if medical_term.strip():
            try:
                validation_result = medical_system.terminology_validator.validate_medical_term(medical_term)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Validation Results:**")
                    st.markdown(f"• **Original**: {validation_result['original']}")
                    st.markdown(f"• **Normalized**: {validation_result['normalized']}")
                    st.markdown(f"• **Valid**: {'✅' if validation_result['is_valid'] else '❌'}")
                    st.markdown(f"• **Category**: {validation_result['category'] or 'Unknown'}")
                    st.markdown(f"• **Confidence**: {validation_result['confidence']:.2f}")
                
                with col2:
                    if validation_result['code']:
                        st.markdown("**Medical Codes:**")
                        st.markdown(f"• **Code**: {validation_result['code']}")
                    
                    if validation_result.get('additional_info'):
                        info = validation_result['additional_info']
                        st.markdown("**Additional Information:**")
                        if 'category' in info:
                            st.markdown(f"• **Drug Category**: {info['category']}")
                        if 'interactions' in info:
                            st.markdown(f"• **Interactions**: {', '.join(info['interactions'])}")
                
            except Exception as e:
                st.error(f"Error validating medical term: {e}")
    
    # Medical abbreviation expansion
    st.markdown("### 📝 Medical Abbreviation Expansion")
    
    abbreviation = st.text_input(
        "Enter Medical Abbreviation:",
        value="bp",
        help="Enter a medical abbreviation to expand"
    )
    
    context = st.text_input(
        "Context (optional):",
        value="patient has elevated bp",
        help="Provide context for context-dependent abbreviations"
    )
    
    if st.button("📝 Expand Abbreviation"):
        if abbreviation.strip():
            try:
                expansion = medical_system.terminology_validator.expand_abbreviation(
                    abbreviation, context if context.strip() else None
                )
                
                if expansion:
                    st.success(f"**{abbreviation.upper()}** expands to: **{expansion.expansion}**")
                    st.markdown(f"• **Category**: {expansion.category}")
                    st.markdown(f"• **Confidence**: {expansion.confidence:.2f}")
                    if expansion.context_dependent:
                        st.info("ℹ️ This abbreviation is context-dependent")
                else:
                    st.warning(f"No expansion found for abbreviation: {abbreviation}")
                    
            except Exception as e:
                st.error(f"Error expanding abbreviation: {e}")
    
    # Common medical codes reference
    st.markdown("### 📚 Common Medical Codes Reference")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Common ICD-10 Codes:**")
        icd10_codes = [
            {'Code': 'I10', 'Description': 'Essential hypertension'},
            {'Code': 'E11.9', 'Description': 'Type 2 diabetes mellitus'},
            {'Code': 'I21.9', 'Description': 'Acute myocardial infarction'},
            {'Code': 'J44.1', 'Description': 'COPD with exacerbation'},
            {'Code': 'R50.9', 'Description': 'Fever, unspecified'}
        ]
        icd10_df = pd.DataFrame(icd10_codes)
        st.dataframe(icd10_df, use_container_width=True)
    
    with col2:
        st.markdown("**Common CPT Codes:**")
        cpt_codes = [
            {'Code': '99213', 'Description': 'Office visit, established patient'},
            {'Code': '93000', 'Description': 'Electrocardiogram'},
            {'Code': '71020', 'Description': 'Chest X-ray'},
            {'Code': '85025', 'Description': 'Complete blood count'},
            {'Code': '82947', 'Description': 'Blood glucose test'}
        ]
        cpt_df = pd.DataFrame(cpt_codes)
        st.dataframe(cpt_df, use_container_width=True)

if __name__ == "__main__":
    main()