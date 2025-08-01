# Structured Analysis UI Components
# Provides Streamlit interface for structured analysis with schema validation

import streamlit as st
import json
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from structured_analysis import (
    structured_analyzer, get_available_templates, analyze_with_schema,
    validate_analysis_result, export_analysis, AnalysisResult
)
from errors import handle_error, NERError, APIError

def display_structured_analysis_interface():
    """Display the main structured analysis interface"""
    st.markdown("### 🔍 Structured Analysis")
    st.markdown("*Advanced domain-specific analysis with JSON schema validation*")
    
    # Template selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get available templates
        templates = get_available_templates()
        template_options = {f"{t['name']} ({t['domain']})": t['name'] for t in templates}
        
        selected_display = st.selectbox(
            "Select Analysis Template",
            options=list(template_options.keys()),
            help="Choose a domain-specific analysis template"
        )
        
        selected_template = template_options[selected_display]
    
    with col2:
        # Domain filter
        domains = list(set(t['domain'] for t in templates))
        domain_filter = st.selectbox(
            "Filter by Domain",
            options=["All"] + domains,
            help="Filter templates by domain"
        )
    
    # Display template information
    template_info = next((t for t in templates if t['name'] == selected_template), None)
    if template_info:
        st.info(f"**{template_info['description']}**")
        
        # Show schema preview in expander
        with st.expander("📋 View Schema Structure"):
            template_obj = structured_analyzer.get_template(selected_template)
            if template_obj:
                st.json(template_obj.schema)
    
    return selected_template

def perform_structured_analysis(text: str, template_name: str) -> Optional[AnalysisResult]:
    """Perform structured analysis and display results"""
    if not text or not text.strip():
        st.warning("Please provide text for analysis.")
        return None
    
    try:
        with st.spinner(f"Performing {template_name} analysis..."):
            # Perform analysis
            result_dict = analyze_with_schema(text, template_name)
            result = AnalysisResult(**result_dict)
            
            # Display results
            display_analysis_results(result)
            
            return result
            
    except (NERError, APIError) as e:
        st.error(f"Analysis failed: {e.user_message}")
        if hasattr(e, 'suggestions') and e.suggestions:
            st.info("**Suggestions:**")
            for suggestion in e.suggestions:
                st.write(f"• {suggestion}")
        return None
    except Exception as e:
        error = handle_error(e, {"operation": "structured_analysis", "template": template_name})
        st.error(f"Unexpected error: {error.user_message}")
        return None

def display_analysis_results(result: AnalysisResult):
    """Display structured analysis results"""
    st.markdown("### 📊 Analysis Results")
    
    # Metadata
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Template", result.template_name)
    with col2:
        st.metric("Domain", result.domain.title())
    with col3:
        st.metric("Confidence", f"{result.confidence:.1%}")
    with col4:
        st.metric("Processing Time", f"{result.processing_time:.2f}s")
    
    # Validation status
    if result.validation_errors:
        st.warning("⚠️ Schema validation issues found:")
        for error in result.validation_errors:
            st.write(f"• {error}")
    else:
        st.success("✅ Data validates against schema")
    
    # Results display
    st.markdown("#### Extracted Data")
    
    # Display based on domain
    if result.domain == "medical":
        display_medical_results(result.data)
    elif result.domain == "legal":
        display_legal_results(result.data)
    elif result.domain == "business":
        display_business_results(result.data)
    elif result.domain == "educational":
        display_educational_results(result.data)
    else:
        # Generic display
        display_generic_results(result.data)
    
    # Export options
    display_export_options(result)

def display_medical_results(data: Dict[str, Any]):
    """Display medical analysis results"""
    # Summary
    if data.get("summary"):
        st.markdown("**Clinical Summary:**")
        st.write(data["summary"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Patient info
        if data.get("patient_info"):
            st.markdown("**Patient Information:**")
            patient = data["patient_info"]
            if patient.get("age"):
                st.write(f"• Age: {patient['age']}")
            if patient.get("gender"):
                st.write(f"• Gender: {patient['gender']}")
            if patient.get("medical_record_number"):
                st.write(f"• MRN: {patient['medical_record_number']}")
        
        # Symptoms
        if data.get("symptoms"):
            st.markdown("**Symptoms:**")
            for symptom in data["symptoms"]:
                st.write(f"• {symptom}")
        
        # Diagnoses
        if data.get("diagnoses"):
            st.markdown("**Diagnoses:**")
            for diagnosis in data["diagnoses"]:
                st.write(f"• {diagnosis}")
    
    with col2:
        # Medications
        if data.get("medications"):
            st.markdown("**Medications:**")
            for med in data["medications"]:
                med_text = med["name"]
                if med.get("dosage"):
                    med_text += f" - {med['dosage']}"
                if med.get("frequency"):
                    med_text += f" ({med['frequency']})"
                st.write(f"• {med_text}")
        
        # Healthcare providers
        if data.get("healthcare_providers"):
            st.markdown("**Healthcare Providers:**")
            for provider in data["healthcare_providers"]:
                st.write(f"• {provider}")
        
        # Follow-up
        if data.get("follow_up"):
            st.markdown("**Follow-up:**")
            for item in data["follow_up"]:
                st.write(f"• {item}")

def display_legal_results(data: Dict[str, Any]):
    """Display legal analysis results"""
    # Summary
    if data.get("summary"):
        st.markdown("**Legal Summary:**")
        st.write(data["summary"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Case info
        if data.get("case_info"):
            st.markdown("**Case Information:**")
            case = data["case_info"]
            if case.get("case_number"):
                st.write(f"• Case Number: {case['case_number']}")
            if case.get("case_type"):
                st.write(f"• Type: {case['case_type']}")
            if case.get("jurisdiction"):
                st.write(f"• Jurisdiction: {case['jurisdiction']}")
        
        # Parties
        if data.get("parties"):
            parties = data["parties"]
            if parties.get("plaintiffs"):
                st.markdown("**Plaintiffs:**")
                for plaintiff in parties["plaintiffs"]:
                    st.write(f"• {plaintiff}")
            
            if parties.get("defendants"):
                st.markdown("**Defendants:**")
                for defendant in parties["defendants"]:
                    st.write(f"• {defendant}")
        
        # Legal issues
        if data.get("legal_issues"):
            st.markdown("**Legal Issues:**")
            for issue in data["legal_issues"]:
                st.write(f"• {issue}")
    
    with col2:
        # Attorneys
        if data.get("parties", {}).get("attorneys"):
            st.markdown("**Attorneys:**")
            for attorney in data["parties"]["attorneys"]:
                attorney_text = attorney["name"]
                if attorney.get("representing"):
                    attorney_text += f" (representing {attorney['representing']})"
                if attorney.get("firm"):
                    attorney_text += f" - {attorney['firm']}"
                st.write(f"• {attorney_text}")
        
        # Statutes cited
        if data.get("statutes_cited"):
            st.markdown("**Statutes Cited:**")
            for statute in data["statutes_cited"]:
                st.write(f"• {statute}")
        
        # Decisions
        if data.get("decisions"):
            st.markdown("**Decisions:**")
            for decision in data["decisions"]:
                st.write(f"• {decision['decision']}")
                if decision.get("reasoning"):
                    st.write(f"  *Reasoning: {decision['reasoning']}*")

def display_business_results(data: Dict[str, Any]):
    """Display business meeting analysis results"""
    # Summary
    if data.get("summary"):
        st.markdown("**Executive Summary:**")
        st.write(data["summary"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Meeting info
        if data.get("meeting_info"):
            st.markdown("**Meeting Information:**")
            meeting = data["meeting_info"]
            if meeting.get("title"):
                st.write(f"• Title: {meeting['title']}")
            if meeting.get("date"):
                st.write(f"• Date: {meeting['date']}")
            if meeting.get("meeting_type"):
                st.write(f"• Type: {meeting['meeting_type']}")
        
        # Attendees
        if data.get("attendees"):
            st.markdown("**Attendees:**")
            for attendee in data["attendees"]:
                attendee_text = attendee["name"]
                if attendee.get("role"):
                    attendee_text += f" ({attendee['role']})"
                if attendee.get("department"):
                    attendee_text += f" - {attendee['department']}"
                st.write(f"• {attendee_text}")
        
        # Decisions
        if data.get("decisions"):
            st.markdown("**Decisions Made:**")
            for decision in data["decisions"]:
                st.write(f"• {decision['decision']}")
                if decision.get("responsible_party"):
                    st.write(f"  *Responsible: {decision['responsible_party']}*")
    
    with col2:
        # Action items
        if data.get("action_items"):
            st.markdown("**Action Items:**")
            for item in data["action_items"]:
                item_text = item["task"]
                if item.get("assignee"):
                    item_text += f" (Assigned to: {item['assignee']})"
                if item.get("deadline"):
                    item_text += f" - Due: {item['deadline']}"
                st.write(f"• {item_text}")
        
        # Projects
        if data.get("projects"):
            st.markdown("**Projects Discussed:**")
            for project in data["projects"]:
                project_text = project["name"]
                if project.get("status"):
                    project_text += f" - Status: {project['status']}"
                st.write(f"• {project_text}")
        
        # Next meeting
        if data.get("next_meeting"):
            st.markdown("**Next Meeting:**")
            next_meeting = data["next_meeting"]
            if next_meeting.get("date"):
                st.write(f"• Date: {next_meeting['date']}")
            if next_meeting.get("agenda"):
                st.write(f"• Agenda: {next_meeting['agenda']}")

def display_educational_results(data: Dict[str, Any]):
    """Display educational content analysis results"""
    # Summary
    if data.get("summary"):
        st.markdown("**Educational Summary:**")
        st.write(data["summary"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Course info
        if data.get("course_info"):
            st.markdown("**Course Information:**")
            course = data["course_info"]
            if course.get("subject"):
                st.write(f"• Subject: {course['subject']}")
            if course.get("level"):
                st.write(f"• Level: {course['level']}")
            if course.get("instructor"):
                st.write(f"• Instructor: {course['instructor']}")
        
        # Learning objectives
        if data.get("learning_objectives"):
            st.markdown("**Learning Objectives:**")
            for objective in data["learning_objectives"]:
                st.write(f"• {objective}")
        
        # Key concepts
        if data.get("key_concepts"):
            st.markdown("**Key Concepts:**")
            for concept in data["key_concepts"]:
                st.write(f"• **{concept['concept']}**")
                if concept.get("definition"):
                    st.write(f"  *{concept['definition']}*")
    
    with col2:
        # Assignments
        if data.get("assignments"):
            st.markdown("**Assignments:**")
            for assignment in data["assignments"]:
                assignment_text = assignment["assignment"]
                if assignment.get("due_date"):
                    assignment_text += f" - Due: {assignment['due_date']}"
                st.write(f"• {assignment_text}")
        
        # Questions asked
        if data.get("questions_asked"):
            st.markdown("**Questions & Answers:**")
            for qa in data["questions_asked"]:
                st.write(f"• **Q:** {qa['question']}")
                if qa.get("answer"):
                    st.write(f"  **A:** {qa['answer']}")
        
        # Resources
        if data.get("resources_mentioned"):
            st.markdown("**Resources Mentioned:**")
            for resource in data["resources_mentioned"]:
                resource_text = resource["resource"]
                if resource.get("type"):
                    resource_text += f" ({resource['type']})"
                st.write(f"• {resource_text}")

def display_generic_results(data: Dict[str, Any]):
    """Display generic structured results"""
    for key, value in data.items():
        if isinstance(value, dict):
            st.markdown(f"**{key.replace('_', ' ').title()}:**")
            for sub_key, sub_value in value.items():
                if sub_value:
                    st.write(f"• {sub_key.replace('_', ' ').title()}: {sub_value}")
        elif isinstance(value, list):
            if value:
                st.markdown(f"**{key.replace('_', ' ').title()}:**")
                for item in value:
                    if isinstance(item, dict):
                        # Display dict items
                        item_text = " - ".join(f"{k}: {v}" for k, v in item.items() if v)
                        st.write(f"• {item_text}")
                    else:
                        st.write(f"• {item}")
        else:
            if value:
                st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")

def display_export_options(result: AnalysisResult):
    """Display export options for analysis results"""
    st.markdown("#### 📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export as JSON"):
            json_data = export_analysis(result, "json")
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"{result.template_name}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export as CSV"):
            try:
                csv_data = export_analysis(result, "csv")
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"{result.template_name}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"CSV export failed: {str(e)}")
    
    with col3:
        if st.button("📋 Copy to Clipboard"):
            json_data = export_analysis(result, "json")
            st.code(json_data, language="json")
            st.info("JSON data displayed above - copy manually")

def display_custom_schema_creator():
    """Display interface for creating custom analysis schemas"""
    st.markdown("### 🛠️ Custom Schema Creator")
    st.markdown("*Create your own domain-specific analysis templates*")
    
    with st.form("custom_schema_form"):
        # Basic info
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Template Name", help="Unique identifier for the template")
            domain = st.text_input("Domain", help="Domain category (e.g., finance, healthcare)")
        
        with col2:
            description = st.text_area("Description", help="Brief description of what this template analyzes")
        
        # Schema definition
        st.markdown("#### Schema Definition")
        st.info("Define the JSON schema for your analysis output. Use JSON Schema format.")
        
        schema_text = st.text_area(
            "JSON Schema",
            height=300,
            value="""{
  "type": "object",
  "properties": {
    "summary": {
      "type": "string",
      "description": "Brief summary of the content"
    },
    "key_points": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Main points identified"
    }
  },
  "required": ["summary"]
}""",
            help="Define the structure of your analysis output"
        )
        
        # Prompt template
        st.markdown("#### Analysis Prompt")
        prompt_template = st.text_area(
            "Prompt Template",
            height=200,
            value="You are an expert analyst. Analyze the provided content and extract structured information according to the specified schema.",
            help="Instructions for the AI to perform the analysis"
        )
        
        # Submit button
        submitted = st.form_submit_button("Create Template")
        
        if submitted:
            if not all([name, domain, description, schema_text, prompt_template]):
                st.error("Please fill in all fields")
            else:
                try:
                    # Parse and validate schema
                    schema = json.loads(schema_text)
                    
                    # Create template
                    template = structured_analyzer.create_custom_template(
                        name=name,
                        description=description,
                        domain=domain,
                        schema=schema,
                        prompt_template=prompt_template
                    )
                    
                    st.success(f"✅ Custom template '{name}' created successfully!")
                    st.info("You can now use this template in the structured analysis interface.")
                    
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON schema: {str(e)}")
                except Exception as e:
                    st.error(f"Failed to create template: {str(e)}")

def display_schema_validation_tool():
    """Display tool for validating data against schemas"""
    st.markdown("### ✅ Schema Validation Tool")
    st.markdown("*Validate your data against analysis templates*")
    
    # Template selection
    templates = get_available_templates()
    template_options = {f"{t['name']} ({t['domain']})": t['name'] for t in templates}
    
    selected_display = st.selectbox(
        "Select Template for Validation",
        options=list(template_options.keys())
    )
    selected_template = template_options[selected_display]
    
    # Data input
    st.markdown("#### Data to Validate")
    data_text = st.text_area(
        "JSON Data",
        height=300,
        help="Paste your JSON data to validate against the selected template"
    )
    
    if st.button("Validate Data"):
        if not data_text.strip():
            st.warning("Please provide JSON data to validate")
        else:
            try:
                data = json.loads(data_text)
                errors = validate_analysis_result(data, selected_template)
                
                if not errors:
                    st.success("✅ Data is valid according to the schema!")
                else:
                    st.error("❌ Validation errors found:")
                    for error in errors:
                        st.write(f"• {error}")
                        
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON format: {str(e)}")
            except Exception as e:
                st.error(f"Validation failed: {str(e)}")