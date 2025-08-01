#!/usr/bin/env python3
"""
Demo script for structured analysis with JSON schema validation
Showcases domain-specific analysis templates and validation features
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from structured_analysis import (
    structured_analyzer, get_available_templates, analyze_with_schema,
    validate_analysis_result, export_analysis, AnalysisResult
)

def demo_available_templates():
    """Demo: Show available analysis templates"""
    print("🔍 Available Analysis Templates")
    print("=" * 50)
    
    templates = get_available_templates()
    
    for template in templates:
        print(f"📋 {template['name']}")
        print(f"   Domain: {template['domain']}")
        print(f"   Description: {template['description']}")
        print(f"   Version: {template['version']}")
        print()

def demo_medical_analysis():
    """Demo: Medical consultation analysis"""
    print("🏥 Medical Consultation Analysis Demo")
    print("=" * 50)
    
    medical_text = """
    Patient Sarah Johnson, 34-year-old female, presented to the clinic today with complaints of persistent headaches and fatigue over the past two weeks. 
    
    Dr. Martinez conducted a thorough examination. Patient reports headaches occurring daily, typically in the afternoon, rated 6-7/10 on pain scale. 
    Associated symptoms include mild nausea and sensitivity to light. No fever or neck stiffness reported.
    
    Physical examination revealed normal vital signs: BP 120/80, HR 72, temp 98.6°F. Neurological examination was within normal limits.
    
    Assessment: Likely tension-type headaches, possibly related to work stress and poor sleep hygiene.
    
    Treatment plan:
    - Prescribed Ibuprofen 400mg every 6 hours as needed for pain
    - Recommended stress management techniques and regular sleep schedule
    - Follow-up appointment scheduled in 2 weeks
    - Advised to return immediately if symptoms worsen or new symptoms develop
    
    Patient education provided regarding headache triggers and lifestyle modifications.
    """
    
    print("📝 Sample Medical Text:")
    print(medical_text[:200] + "..." if len(medical_text) > 200 else medical_text)
    print()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ OpenAI API key not configured. Skipping analysis.")
        return
    
    try:
        print("🔄 Performing medical analysis...")
        result_dict = analyze_with_schema(medical_text, "medical_consultation")
        result = AnalysisResult(**result_dict)
        
        print("✅ Analysis completed!")
        print(f"📊 Confidence: {result.confidence:.1%}")
        print(f"⏱️ Processing time: {result.processing_time:.2f}s")
        print()
        
        # Display key findings
        data = result.data
        
        if data.get("summary"):
            print("📋 Clinical Summary:")
            print(f"   {data['summary']}")
            print()
        
        if data.get("symptoms"):
            print("🤒 Symptoms Identified:")
            for symptom in data["symptoms"]:
                print(f"   • {symptom}")
            print()
        
        if data.get("medications"):
            print("💊 Medications Prescribed:")
            for med in data["medications"]:
                med_info = med["name"]
                if med.get("dosage"):
                    med_info += f" - {med['dosage']}"
                if med.get("frequency"):
                    med_info += f" ({med['frequency']})"
                print(f"   • {med_info}")
            print()
        
        if data.get("healthcare_providers"):
            print("👨‍⚕️ Healthcare Providers:")
            for provider in data["healthcare_providers"]:
                print(f"   • {provider}")
            print()
        
        # Validation check
        validation_errors = validate_analysis_result(data, "medical_consultation")
        if validation_errors:
            print("⚠️ Validation Issues:")
            for error in validation_errors:
                print(f"   • {error}")
        else:
            print("✅ Data validates against medical schema")
        
        print()
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")

def demo_business_analysis():
    """Demo: Business meeting analysis"""
    print("💼 Business Meeting Analysis Demo")
    print("=" * 50)
    
    business_text = """
    Q4 Planning Meeting - December 5, 2024
    
    Attendees:
    - Jennifer Smith, VP Marketing
    - Robert Chen, Director of Sales  
    - Lisa Rodriguez, Product Manager
    - Michael Johnson, Finance Director
    
    Meeting called to order at 2:00 PM by Jennifer Smith.
    
    Agenda Item 1: Q4 Budget Review
    Michael presented the Q4 budget status. Current spending is at 85% of allocated budget with one month remaining. 
    Revenue projections show we're on track to exceed targets by 12%.
    
    Decision: Approved additional $25,000 for holiday marketing campaign.
    
    Agenda Item 2: Product Launch Timeline
    Lisa provided update on new product launch scheduled for January 2025. Development is 90% complete, 
    beta testing shows positive user feedback with 4.2/5 average rating.
    
    Action Items:
    - Robert to finalize sales training materials by December 15th
    - Lisa to coordinate with PR team for launch announcement
    - Jennifer to approve final marketing creative by December 20th
    
    Agenda Item 3: Team Expansion
    Discussed hiring needs for Q1 2025. Sales team needs 2 additional representatives, 
    Marketing needs 1 content specialist.
    
    Decision: Approved hiring budget of $180,000 for new positions.
    
    Next meeting scheduled for December 19th to review launch preparations.
    
    Meeting adjourned at 3:30 PM.
    """
    
    print("📝 Sample Business Text:")
    print(business_text[:200] + "..." if len(business_text) > 200 else business_text)
    print()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ OpenAI API key not configured. Skipping analysis.")
        return
    
    try:
        print("🔄 Performing business analysis...")
        result_dict = analyze_with_schema(business_text, "business_meeting")
        result = AnalysisResult(**result_dict)
        
        print("✅ Analysis completed!")
        print(f"📊 Confidence: {result.confidence:.1%}")
        print(f"⏱️ Processing time: {result.processing_time:.2f}s")
        print()
        
        # Display key findings
        data = result.data
        
        if data.get("summary"):
            print("📋 Executive Summary:")
            print(f"   {data['summary']}")
            print()
        
        if data.get("attendees"):
            print("👥 Meeting Attendees:")
            for attendee in data["attendees"]:
                attendee_info = attendee["name"]
                if attendee.get("role"):
                    attendee_info += f" ({attendee['role']})"
                print(f"   • {attendee_info}")
            print()
        
        if data.get("decisions"):
            print("✅ Decisions Made:")
            for decision in data["decisions"]:
                print(f"   • {decision['decision']}")
                if decision.get("rationale"):
                    print(f"     Rationale: {decision['rationale']}")
            print()
        
        if data.get("action_items"):
            print("📋 Action Items:")
            for item in data["action_items"]:
                item_info = item["task"]
                if item.get("assignee"):
                    item_info += f" (Assigned to: {item['assignee']})"
                if item.get("deadline"):
                    item_info += f" - Due: {item['deadline']}"
                print(f"   • {item_info}")
            print()
        
        # Export demo
        print("📤 Export Demo:")
        json_export = export_analysis(result, "json")
        print("   JSON export created (first 200 chars):")
        print(f"   {json_export[:200]}...")
        print()
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")

def demo_custom_template():
    """Demo: Creating and using custom template"""
    print("🛠️ Custom Template Demo")
    print("=" * 50)
    
    # Create a custom template for interview analysis
    custom_schema = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Summary of the interview"
            },
            "candidate_info": {
                "type": "object",
                "properties": {
                    "name": {"type": ["string", "null"]},
                    "position": {"type": ["string", "null"]},
                    "experience": {"type": ["string", "null"]}
                }
            },
            "questions_asked": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answer_summary": {"type": ["string", "null"]}
                    },
                    "required": ["question"]
                }
            },
            "skills_mentioned": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Technical and soft skills mentioned"
            },
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Candidate strengths identified"
            },
            "concerns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Areas of concern or improvement"
            },
            "recommendation": {
                "type": "string",
                "description": "Hiring recommendation"
            }
        },
        "required": ["summary"]
    }
    
    custom_prompt = """
    You are an HR specialist analyzing job interview transcripts. Extract structured information about the candidate, questions asked, skills discussed, and provide a hiring assessment.
    
    Focus on:
    - Candidate background and experience
    - Questions asked and quality of responses
    - Technical and soft skills mentioned
    - Candidate strengths and potential concerns
    - Overall hiring recommendation
    
    Maintain professional HR standards and objectivity.
    """
    
    print("📋 Creating custom interview analysis template...")
    
    try:
        template = structured_analyzer.create_custom_template(
            name="job_interview",
            description="Job interview analysis and candidate assessment",
            domain="hr",
            schema=custom_schema,
            prompt_template=custom_prompt
        )
        
        print(f"✅ Custom template '{template.name}' created successfully!")
        print(f"   Domain: {template.domain}")
        print(f"   Version: {template.version}")
        print()
        
        # Demo with sample interview text
        interview_text = """
        Interview with Alex Thompson for Senior Software Engineer position.
        
        Interviewer: Tell me about your background in software development.
        Alex: I have 8 years of experience in full-stack development, primarily working with Python, JavaScript, and React. 
        I've led several projects at my current company, including a microservices migration that improved system performance by 40%.
        
        Interviewer: How do you handle debugging complex issues?
        Alex: I start with systematic logging and use debugging tools like pdb for Python. I also believe in writing comprehensive tests 
        to catch issues early. Recently, I solved a race condition bug that was affecting our payment system.
        
        Interviewer: What's your experience with team leadership?
        Alex: I've mentored 3 junior developers and led a team of 5 engineers on our latest project. I focus on code reviews, 
        knowledge sharing, and creating a collaborative environment.
        
        Interviewer: Any questions for us?
        Alex: I'm interested in the company's approach to technical debt and how you balance feature development with maintenance.
        
        Overall impression: Strong technical background, good communication skills, shows leadership potential.
        """
        
        if os.getenv('OPENAI_API_KEY'):
            print("🔄 Testing custom template with sample interview...")
            result_dict = analyze_with_schema(interview_text, "job_interview")
            result = AnalysisResult(**result_dict)
            
            print("✅ Custom analysis completed!")
            print(f"📊 Confidence: {result.confidence:.1%}")
            print()
            
            data = result.data
            if data.get("summary"):
                print("📋 Interview Summary:")
                print(f"   {data['summary']}")
                print()
            
            if data.get("skills_mentioned"):
                print("🛠️ Skills Mentioned:")
                for skill in data["skills_mentioned"]:
                    print(f"   • {skill}")
                print()
            
            if data.get("recommendation"):
                print("💼 Hiring Recommendation:")
                print(f"   {data['recommendation']}")
                print()
        else:
            print("⚠️ OpenAI API key not configured. Skipping custom analysis test.")
        
    except Exception as e:
        print(f"❌ Custom template creation failed: {str(e)}")

def demo_schema_validation():
    """Demo: Schema validation functionality"""
    print("✅ Schema Validation Demo")
    print("=" * 50)
    
    # Test with valid data
    print("Testing with valid medical data...")
    valid_data = {
        "summary": "Patient consultation for routine checkup",
        "symptoms": ["mild headache"],
        "medications": [
            {
                "name": "Aspirin",
                "dosage": "325mg",
                "frequency": "as needed"
            }
        ],
        "healthcare_providers": ["Dr. Smith"]
    }
    
    errors = validate_analysis_result(valid_data, "medical_consultation")
    if not errors:
        print("✅ Valid data passed validation")
    else:
        print("❌ Unexpected validation errors:")
        for error in errors:
            print(f"   • {error}")
    print()
    
    # Test with invalid data
    print("Testing with invalid medical data...")
    invalid_data = {
        # Missing required "summary" field
        "symptoms": "should be array, not string",  # Wrong type
        "medications": [
            {
                # Missing required "name" field
                "dosage": "100mg"
            }
        ]
    }
    
    errors = validate_analysis_result(invalid_data, "medical_consultation")
    if errors:
        print("✅ Invalid data correctly rejected:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("❌ Invalid data unexpectedly passed validation")
    print()

def main():
    """Run all demos"""
    print("🚀 Structured Analysis Demo")
    print("=" * 60)
    print()
    
    # Check API key status
    if os.getenv('OPENAI_API_KEY'):
        print("✅ OpenAI API key configured - full demos available")
    else:
        print("⚠️ OpenAI API key not configured - limited demos available")
        print("   Set OPENAI_API_KEY environment variable for full functionality")
    print()
    
    # Run demos
    demo_available_templates()
    print()
    
    demo_medical_analysis()
    print()
    
    demo_business_analysis()
    print()
    
    demo_custom_template()
    print()
    
    demo_schema_validation()
    print()
    
    print("🎉 Demo completed!")
    print()
    print("💡 Next steps:")
    print("   • Try the structured analysis in the main app (Advanced mode)")
    print("   • Create your own custom templates")
    print("   • Integrate with your domain-specific workflows")

if __name__ == "__main__":
    main()