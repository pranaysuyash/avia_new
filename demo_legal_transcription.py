#!/usr/bin/env python3
"""
Demo: Legal Transcription and Analysis System
Comprehensive demonstration of legal transcription with case analysis, citation extraction, and compliance checking
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import legal transcription system
try:
    from legal_transcription_system import (
        LegalTranscriptionSystem,
        LegalDocument,
        ProceedingType,
        LegalSpecialty
    )
    from legal_transcription_core import LegalEntityType
except ImportError:
    st.error("Legal transcription system not found. Please ensure legal_transcription_system.py is available.")
    st.stop()

def main():
    st.set_page_config(
        page_title="Legal Transcription Demo",
        page_icon="⚖️",
        layout="wide"
    )
    
    st.title("⚖️ Legal Transcription and Analysis System")
    st.markdown("---")
    st.markdown("**Advanced legal transcription with case analysis, citation extraction, and compliance checking**")
    
    # Sidebar configuration
    st.sidebar.header("🔧 Configuration")
    
    proceeding_type = st.sidebar.selectbox(
        "Proceeding Type",
        options=[proc_type.value for proc_type in ProceedingType],
        index=0,
        help="Select the type of legal proceeding"
    )
    
    legal_specialty = st.sidebar.selectbox(
        "Legal Specialty",
        options=[specialty.value for specialty in LegalSpecialty],
        index=0,
        help="Select the area of legal practice"
    )
    
    enable_case_analysis = st.sidebar.checkbox(
        "Enable Case Analysis",
        value=True,
        help="Analyze legal arguments and precedents"
    )
    
    enable_compliance_check = st.sidebar.checkbox(
        "Enable Compliance Check",
        value=True,
        help="Check for privilege and ethical issues"
    )
    
    # Main demo tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚖️ Legal Transcription",
        "📚 Case Analysis",
        "🔍 Citation Extraction",
        "⚠️ Compliance Check",
        "📊 Analytics Dashboard"
    ])
    
    # Initialize legal transcription system
    try:
        legal_system = LegalTranscriptionSystem()
    except Exception as e:
        st.error(f"Failed to initialize legal transcription system: {e}")
        return
    
    with tab1:
        demo_legal_transcription(legal_system, proceeding_type, legal_specialty, 
                               enable_case_analysis, enable_compliance_check)
    
    with tab2:
        demo_case_analysis(legal_system)
    
    with tab3:
        demo_citation_extraction(legal_system)
    
    with tab4:
        demo_compliance_check(legal_system)
    
    with tab5:
        demo_analytics_dashboard()

def demo_legal_transcription(legal_system, proceeding_type, legal_specialty, 
                           enable_case_analysis, enable_compliance_check):
    """Demo legal transcription processing"""
    st.subheader("⚖️ Legal Transcription Processing")
    
    st.markdown("""
    **Features:**
    - Legal entity extraction (parties, attorneys, judges, witnesses)
    - Case law citation identification and analysis
    - Legal argument structure analysis
    - Compliance and privilege checking
    - Risk assessment and recommendations
    """)
    
    # Sample legal transcripts
    sample_transcripts = {
        "Contract Dispute Hearing": """
        Your Honor, this case involves a breach of contract claim between ABC Corporation 
        and XYZ Company. The contract was executed on January 15, 2023, with a clear 
        delivery deadline of February 15, 2023.
        
        Counsel for plaintiff: Your Honor, the evidence clearly shows that defendant 
        failed to deliver the goods by the contractual deadline. Under Hadley v. Baxendale, 
        347 U.S. 483 (1954), the damages must be reasonably foreseeable at the time of 
        contract formation. Here, plaintiff suffered $50,000 in consequential damages 
        that were clearly foreseeable.
        
        The Court: Counsel, what is your response to the foreseeability argument?
        
        Defense counsel: Your Honor, we object to the characterization of these damages 
        as foreseeable. The contract contained a force majeure clause, and the delay 
        was caused by circumstances beyond our client's control.
        
        The Court: I'll allow the testimony to continue. Please proceed with your examination.
        
        Plaintiff's counsel: Thank you, Your Honor. We seek damages of $100,000 plus 
        attorney fees under the contract's prevailing party clause.
        """,
        
        "Criminal Trial Excerpt": """
        The Court: The defendant is charged with burglary in the first degree under 
        Penal Code Section 459. How does the defendant plead?
        
        Defense Attorney: Not guilty, Your Honor.
        
        Prosecutor: Your Honor, the People will prove beyond a reasonable doubt that 
        on the night of March 15, 2023, the defendant unlawfully entered the victim's 
        residence with intent to commit theft.
        
        Defense Attorney: Objection, Your Honor. Hearsay.
        
        The Court: Overruled. The prosecutor may continue with the opening statement.
        
        Prosecutor: The evidence will show that the defendant's fingerprints were found 
        on the window frame, and stolen property was recovered from his vehicle. 
        Under People v. Smith, 123 Cal.App.4th 456 (2019), circumstantial evidence 
        is sufficient to prove intent.
        
        Defense Attorney: Your Honor, we maintain that the evidence is insufficient 
        and request that the charges be dismissed under Penal Code Section 995.
        """,
        
        "Deposition Transcript": """
        Attorney: Please state your name for the record.
        
        Witness: John Smith.
        
        Attorney: Mr. Smith, were you present at the accident scene on June 1, 2023?
        
        Witness: Yes, I was driving northbound on Main Street when I saw the collision.
        
        Attorney: Can you describe what you observed?
        
        Witness: The blue car ran the red light and struck the white car in the intersection.
        
        Opposing Counsel: Objection. Lack of foundation. How does the witness know 
        the light was red?
        
        Attorney: I'll rephrase. Mr. Smith, what did you observe about the traffic signal?
        
        Witness: I saw the light was red for the blue car's direction of travel.
        
        Attorney: How far were you from the intersection?
        
        Witness: Approximately 50 feet.
        
        Attorney: Did you have an unobstructed view?
        
        Witness: Yes, there were no other vehicles blocking my view.
        """,
        
        "Settlement Conference": """
        Mediator: We're here today to discuss settlement in the case of Johnson v. 
        Medical Center. Plaintiff is seeking $500,000 in damages for medical malpractice.
        
        Plaintiff's Attorney: Your Honor, our client suffered permanent injury due to 
        the defendant's negligence. The medical records clearly show a deviation from 
        the standard of care.
        
        Defense Attorney: We dispute the causation element. Our expert will testify 
        that the patient's condition was pre-existing and not caused by our client's treatment.
        
        Mediator: Let's discuss the damages calculation. What is the basis for the 
        $500,000 demand?
        
        Plaintiff's Attorney: $200,000 in medical expenses, $150,000 in lost wages, 
        and $150,000 for pain and suffering.
        
        Defense Attorney: We're prepared to offer $100,000 to resolve this matter, 
        without admission of liability.
        
        Mediator: That's a significant gap. Let's explore the strengths and weaknesses 
        of each side's case.
        """
    }
    
    # Transcript selection
    selected_transcript = st.selectbox(
        "Select Sample Legal Transcript:",
        options=list(sample_transcripts.keys()),
        help="Choose a sample legal transcript to process"
    )
    
    # Text input area
    transcript_text = st.text_area(
        "Legal Transcript:",
        value=sample_transcripts[selected_transcript],
        height=400,
        help="Enter or modify the legal transcript text"
    )
    
    # Case information inputs
    col1, col2 = st.columns(2)
    
    with col1:
        case_number = st.text_input("Case Number:", value="CV-2023-001234")
        court = st.text_input("Court:", value="Superior Court of California")
    
    with col2:
        parties_input = st.text_input("Parties (comma-separated):", value="ABC Corporation, XYZ Company")
        parties = [party.strip() for party in parties_input.split(",")]
    
    if st.button("⚖️ Process Legal Transcript", type="primary"):
        if transcript_text.strip():
            with st.spinner("Processing legal transcript..."):
                try:
                    # Process legal transcript
                    legal_document = asyncio.run(
                        legal_system.process_legal_transcript(
                            transcript_text=transcript_text,
                            document_type=ProceedingType(proceeding_type),
                            specialty=LegalSpecialty(legal_specialty),
                            case_number=case_number,
                            court=court,
                            parties=parties
                        )
                    )
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 📄 Document Summary")
                        st.markdown(f"**Document ID**: {legal_document.document_id}")
                        st.markdown(f"**Type**: {legal_document.document_type.value.replace('_', ' ').title()}")
                        st.markdown(f"**Specialty**: {legal_document.specialty.value.replace('_', ' ').title()}")
                        st.markdown(f"**Case Number**: {legal_document.case_number}")
                        st.markdown(f"**Court**: {legal_document.court}")
                        st.markdown(f"**Parties**: {', '.join(legal_document.parties)}")
                        st.markdown(f"**Word Count**: {legal_document.word_count}")
                        st.markdown(f"**Time Saved**: {legal_document.estimated_time_saved:.1f} minutes")
                        
                        # Entity Analysis
                        st.markdown("### 📊 Entity Analysis")
                        total_entities = sum(len(entities) for entities in legal_document.entities.values())
                        st.metric("Total Entities", total_entities)
                        
                        for category, entities in legal_document.entities.items():
                            if entities:
                                st.markdown(f"**{category.replace('_', ' ').title()}**: {len(entities)}")
                    
                    with col2:
                        st.markdown("### ⚖️ Legal Analysis")
                        
                        # Citations
                        st.markdown(f"**Citations Found**: {len(legal_document.citations)}")
                        if legal_document.citations:
                            st.markdown("**Key Citations:**")
                            for citation in legal_document.citations[:3]:
                                st.markdown(f"• {citation.citation_text}")
                                if citation.case_name:
                                    st.caption(f"Case: {citation.case_name}")
                        
                        # Arguments
                        st.markdown(f"**Arguments Identified**: {len(legal_document.arguments)}")
                        if legal_document.arguments:
                            st.markdown("**Argument Summary:**")
                            for i, arg in enumerate(legal_document.arguments[:2]):
                                st.markdown(f"**Argument {i+1}** ({arg.attorney}):")
                                st.markdown(f"• {arg.argument_summary[:100]}...")
                                st.caption(f"Strength: {arg.strength_assessment}")
                        
                        # Compliance Status
                        st.markdown("### ⚠️ Compliance Status")
                        status_color = "🟢" if legal_document.compliance_status == "compliant" else "🔴"
                        st.markdown(f"{status_color} **Status**: {legal_document.compliance_status.title()}")
                        
                        risk_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
                            legal_document.risk_assessment["overall_risk_level"], "⚪"
                        )
                        st.markdown(f"{risk_color} **Risk Level**: {legal_document.risk_assessment['overall_risk_level'].title()}")
                    
                    # Detailed Analysis
                    if enable_case_analysis or enable_compliance_check:
                        st.markdown("### 📋 Detailed Analysis")
                        
                        if enable_case_analysis and legal_document.arguments:
                            with st.expander("Legal Arguments Analysis"):
                                for i, arg in enumerate(legal_document.arguments):
                                    st.markdown(f"**Argument {i+1}**: {arg.attorney}")
                                    st.markdown(f"**Summary**: {arg.argument_summary}")
                                    st.markdown(f"**Legal Basis**: {', '.join(arg.legal_basis) if arg.legal_basis else 'None specified'}")
                                    st.markdown(f"**Factual Basis**: {', '.join(arg.factual_basis) if arg.factual_basis else 'None specified'}")
                                    st.markdown(f"**Strength**: {arg.strength_assessment}")
                                    if arg.precedents_cited:
                                        st.markdown("**Precedents Cited**:")
                                        for precedent in arg.precedents_cited:
                                            st.markdown(f"• {precedent.citation_text}")
                                    st.markdown("---")
                        
                        if enable_compliance_check:
                            with st.expander("Compliance and Risk Assessment"):
                                risk_assessment = legal_document.risk_assessment
                                
                                for risk_type, risks in risk_assessment.items():
                                    if risk_type != "overall_risk_level" and risks:
                                        st.markdown(f"**{risk_type.replace('_', ' ').title()}**:")
                                        if isinstance(risks, list):
                                            for risk in risks:
                                                st.markdown(f"• {risk}")
                                        else:
                                            st.markdown(f"• {risks}")
                    
                    # Store results in session state for other tabs
                    st.session_state.legal_document = legal_document
                    st.session_state.legal_report = legal_system.generate_legal_report(legal_document)
                    
                except Exception as e:
                    st.error(f"Error processing legal transcript: {e}")
        else:
            st.warning("Please enter a legal transcript to process.")

def demo_case_analysis(legal_system):
    """Demo case analysis features"""
    st.subheader("📚 Legal Case Analysis")
    
    st.markdown("""
    **Case Analysis Features:**
    - Legal argument identification and strength assessment
    - Precedent citation analysis
    - Case law database integration
    - Legal standard application
    - Argument structure evaluation
    """)
    
    if hasattr(st.session_state, 'legal_document'):
        legal_document = st.session_state.legal_document
        
        # Arguments Analysis
        st.markdown("### ⚖️ Legal Arguments")
        
        if legal_document.arguments:
            for i, argument in enumerate(legal_document.arguments):
                with st.expander(f"Argument {i+1}: {argument.attorney}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Argument Summary:**")
                        st.write(argument.argument_summary)
                        
                        st.markdown("**Legal Basis:**")
                        if argument.legal_basis:
                            for basis in argument.legal_basis:
                                st.markdown(f"• {basis}")
                        else:
                            st.markdown("• No legal basis specified")
                    
                    with col2:
                        st.markdown("**Factual Basis:**")
                        if argument.factual_basis:
                            for basis in argument.factual_basis:
                                st.markdown(f"• {basis}")
                        else:
                            st.markdown("• No factual basis specified")
                        
                        st.markdown("**Strength Assessment:**")
                        strength_color = {"strong": "🟢", "moderate": "🟡", "weak": "🔴"}.get(
                            argument.strength_assessment, "⚪"
                        )
                        st.markdown(f"{strength_color} {argument.strength_assessment.title()}")
                        
                        if argument.precedents_cited:
                            st.markdown("**Precedents Cited:**")
                            for precedent in argument.precedents_cited:
                                st.markdown(f"• {precedent.citation_text}")
                                if precedent.relevance:
                                    st.caption(f"Relevance: {precedent.relevance}")
        else:
            st.info("No legal arguments identified in the transcript.")
        
        # Case Law Database
        st.markdown("### 📚 Case Law Database")
        
        # Display relevant case law from the database
        case_analyzer = legal_system.case_analyzer
        case_law_data = []
        
        for case_name, case_info in case_analyzer.case_law_database.items():
            case_law_data.append({
                "Case Name": case_name,
                "Citation": case_info["citation"],
                "Court": case_info["court"],
                "Year": case_info["year"],
                "Area": case_info["area"].replace("_", " ").title(),
                "Significance": case_info["significance"].title(),
                "Holding": case_info["holding"][:100] + "..." if len(case_info["holding"]) > 100 else case_info["holding"]
            })
        
        case_law_df = pd.DataFrame(case_law_data)
        st.dataframe(case_law_df, use_container_width=True)
        
    else:
        st.info("Process a legal transcript first to see case analysis results.")

def demo_citation_extraction(legal_system):
    """Demo citation extraction features"""
    st.subheader("🔍 Legal Citation Extraction")
    
    st.markdown("""
    **Citation Extraction Features:**
    - Automatic case law citation identification
    - Statute and regulation citation parsing
    - Citation format validation
    - Relevance assessment
    - Holding and precedent analysis
    """)
    
    if hasattr(st.session_state, 'legal_document'):
        legal_document = st.session_state.legal_document
        
        if legal_document.citations:
            st.markdown(f"### 📖 Citations Found ({len(legal_document.citations)})")
            
            # Create citations dataframe
            citations_data = []
            for citation in legal_document.citations:
                citations_data.append({
                    "Citation": citation.citation_text,
                    "Case Name": citation.case_name or "N/A",
                    "Court": citation.court or "N/A",
                    "Year": citation.year or "N/A",
                    "Type": citation.citation_type.title(),
                    "Relevance": citation.relevance or "N/A",
                    "Holding": citation.holding[:100] + "..." if citation.holding and len(citation.holding) > 100 else citation.holding or "N/A"
                })
            
            citations_df = pd.DataFrame(citations_data)
            st.dataframe(citations_df, use_container_width=True)
            
            # Citation analysis
            st.markdown("### 📊 Citation Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                case_citations = [c for c in legal_document.citations if c.citation_type == "case"]
                st.metric("Case Citations", len(case_citations))
            
            with col2:
                statute_citations = [c for c in legal_document.citations if c.citation_type == "statute"]
                st.metric("Statute Citations", len(statute_citations))
            
            with col3:
                other_citations = [c for c in legal_document.citations if c.citation_type not in ["case", "statute"]]
                st.metric("Other Citations", len(other_citations))
            
            # Relevance distribution
            if any(c.relevance for c in legal_document.citations):
                relevance_data = {}
                for citation in legal_document.citations:
                    if citation.relevance:
                        relevance_data[citation.relevance] = relevance_data.get(citation.relevance, 0) + 1
                
                if relevance_data:
                    fig = px.pie(
                        values=list(relevance_data.values()),
                        names=list(relevance_data.keys()),
                        title="Citation Relevance Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No legal citations found in the transcript.")
    else:
        st.info("Process a legal transcript first to see citation extraction results.")

def demo_compliance_check(legal_system):
    """Demo compliance checking features"""
    st.subheader("⚠️ Legal Compliance Check")
    
    st.markdown("""
    **Compliance Features:**
    - Attorney-client privilege detection
    - Work product doctrine protection
    - Ethical guidelines compliance
    - Professional conduct rules
    - Risk assessment and recommendations
    """)
    
    if hasattr(st.session_state, 'legal_document'):
        legal_document = st.session_state.legal_document
        
        # Overall compliance status
        st.markdown("### 📋 Compliance Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_color = "🟢" if legal_document.compliance_status == "compliant" else "🔴"
            st.metric("Overall Status", f"{status_color} {legal_document.compliance_status.title()}")
        
        with col2:
            risk_level = legal_document.risk_assessment["overall_risk_level"]
            risk_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_level, "⚪")
            st.metric("Risk Level", f"{risk_color} {risk_level.title()}")
        
        with col3:
            total_risks = sum(
                len(risks) if isinstance(risks, list) else (1 if risks else 0)
                for key, risks in legal_document.risk_assessment.items()
                if key != "overall_risk_level"
            )
            st.metric("Total Risk Items", total_risks)
        
        # Risk breakdown
        st.markdown("### 🚨 Risk Assessment")
        
        risk_assessment = legal_document.risk_assessment
        
        for risk_type, risks in risk_assessment.items():
            if risk_type != "overall_risk_level" and risks:
                st.markdown(f"**{risk_type.replace('_', ' ').title()}:**")
                
                if isinstance(risks, list):
                    for risk in risks:
                        if isinstance(risk, dict):
                            severity = risk.get('severity', 'medium')
                            severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
                            st.markdown(f"{severity_color} {risk.get('description', risk)}")
                        else:
                            st.markdown(f"• {risk}")
                else:
                    st.markdown(f"• {risks}")
        
        # Compliance recommendations
        st.markdown("### 💡 Compliance Recommendations")
        
        # Mock compliance recommendations based on risk assessment
        recommendations = []
        
        if legal_document.risk_assessment.get("privilege_risks"):
            recommendations.append("Review transcript for attorney-client privilege issues")
            recommendations.append("Consider redacting privileged communications")
        
        if legal_document.risk_assessment.get("malpractice_risks"):
            recommendations.append("Conduct malpractice risk assessment")
            recommendations.append("Review professional liability insurance coverage")
        
        if legal_document.risk_assessment.get("procedural_risks"):
            recommendations.append("Verify compliance with court rules and procedures")
            recommendations.append("Calendar all mentioned deadlines and requirements")
        
        if not recommendations:
            recommendations.append("No specific compliance issues identified")
            recommendations.append("Continue following standard legal practices")
        
        for i, recommendation in enumerate(recommendations, 1):
            st.markdown(f"{i}. {recommendation}")
        
        # Compliance rules reference
        with st.expander("📚 Compliance Rules Reference"):
            compliance_checker = legal_system.compliance_checker
            
            st.markdown("**Professional Conduct Rules:**")
            for rule_id, rule_desc in compliance_checker.ethical_guidelines["model_rules"].items():
                st.markdown(f"• **{rule_id.upper()}**: {rule_desc}")
    
    else:
        st.info("Process a legal transcript first to see compliance check results.")

def demo_analytics_dashboard():
    """Demo analytics dashboard"""
    st.subheader("📊 Legal Analytics Dashboard")
    
    st.markdown("""
    **Analytics Features:**
    - Case processing metrics
    - Legal entity distribution
    - Citation analysis trends
    - Compliance monitoring
    - Time savings calculations
    """)
    
    # Mock analytics data
    st.markdown("### 📈 Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Cases Processed", "1,247", delta="156")
    
    with col2:
        st.metric("Avg Time Saved", "45.2 min", delta="3.1 min")
    
    with col3:
        st.metric("Citations Extracted", "3,891", delta="287")
    
    with col4:
        st.metric("Compliance Rate", "94.2%", delta="2.1%")
    
    # Case type distribution
    st.markdown("### ⚖️ Case Type Distribution")
    
    case_types = {
        'Civil Litigation': 387,
        'Contract Law': 234,
        'Criminal Law': 198,
        'Corporate Law': 156,
        'Family Law': 123,
        'Employment Law': 89,
        'Other': 60
    }
    
    fig = px.pie(
        values=list(case_types.values()),
        names=list(case_types.keys()),
        title="Cases by Legal Specialty"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Processing trends
    st.markdown("### 📈 Processing Trends")
    
    # Generate mock trend data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    cases_processed = [15 + 5 * (i % 7) + (i % 3) for i in range(len(dates))]
    
    trend_df = pd.DataFrame({
        'Date': dates,
        'Cases Processed': cases_processed
    })
    
    fig = px.line(trend_df, x='Date', y='Cases Processed', 
                  title='Daily Case Processing Volume')
    st.plotly_chart(fig, use_container_width=True)
    
    # Entity analysis
    st.markdown("### 🏷️ Entity Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        entity_types = {
            'Legal Roles': 1234,
            'Citations': 987,
            'Procedures': 756,
            'Documents': 543,
            'Monetary': 321,
            'Objections': 234
        }
        
        fig = px.bar(
            x=list(entity_types.keys()),
            y=list(entity_types.values()),
            title='Entity Types Extracted'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        compliance_status = {
            'Compliant': 1175,
            'Warnings': 58,
            'Violations': 14
        }
        
        fig = px.pie(
            values=list(compliance_status.values()),
            names=list(compliance_status.keys()),
            title='Compliance Status Distribution'
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()