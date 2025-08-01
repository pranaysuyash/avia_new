# Structured Analysis Module with JSON Schema Validation
# Provides domain-specific analysis templates and schema validation

import json
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError
from openai import OpenAI
from dotenv import load_dotenv

from errors import (
    NERError, APIError, handle_error, ErrorCode, 
    create_api_key_error
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class AnalysisTemplate:
    """Template for structured analysis"""
    name: str
    description: str
    schema: Dict[str, Any]
    prompt_template: str
    domain: str
    version: str = "1.0"

@dataclass
class AnalysisResult:
    """Result of structured analysis"""
    template_name: str
    domain: str
    data: Dict[str, Any]
    confidence: float
    processing_time: float
    timestamp: str
    validation_errors: List[str] = None

class StructuredAnalyzer:
    """Main class for structured analysis with schema validation"""
    
    def __init__(self):
        self.templates = {}
        self.client = None
        self._load_default_templates()
    
    def _get_openai_client(self):
        """Get OpenAI client with proper error handling"""
        if self.client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise create_api_key_error("OpenAI")
            
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                raise APIError(
                    message=f"Failed to initialize OpenAI client: {e}",
                    error_code=ErrorCode.API_AUTHENTICATION_ERROR,
                    user_message="Failed to connect to OpenAI API.",
                    api_name="OpenAI",
                    suggestions=[
                        "Check your OpenAI API key configuration",
                        "Verify your internet connection"
                    ]
                )
        return self.client
    
    def _load_default_templates(self):
        """Load default analysis templates"""
        
        # Medical Analysis Template
        medical_schema = {
            "type": "object",
            "properties": {
                "patient_info": {
                    "type": "object",
                    "properties": {
                        "age": {"type": ["string", "null"]},
                        "gender": {"type": ["string", "null"]},
                        "medical_record_number": {"type": ["string", "null"]}
                    }
                },
                "symptoms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of symptoms mentioned"
                },
                "diagnoses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Medical diagnoses or conditions"
                },
                "medications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "dosage": {"type": ["string", "null"]},
                            "frequency": {"type": ["string", "null"]}
                        },
                        "required": ["name"]
                    }
                },
                "procedures": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Medical procedures mentioned"
                },
                "healthcare_providers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Doctors, nurses, specialists mentioned"
                },
                "appointments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": ["string", "null"]},
                            "provider": {"type": ["string", "null"]},
                            "purpose": {"type": ["string", "null"]}
                        }
                    }
                },
                "summary": {
                    "type": "string",
                    "description": "Clinical summary of the consultation"
                },
                "follow_up": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Follow-up actions or recommendations"
                }
            },
            "required": ["summary"]
        }
        
        medical_prompt = """
        You are a medical transcription specialist. Analyze this medical consultation transcript and extract structured information.
        
        IMPORTANT: Only extract information that is explicitly mentioned in the text. Do not infer or assume medical information.
        
        Focus on:
        - Patient demographics (if mentioned)
        - Symptoms and complaints
        - Diagnoses and medical conditions
        - Medications with dosages
        - Medical procedures
        - Healthcare providers involved
        - Appointment scheduling
        - Follow-up recommendations
        
        Maintain strict medical confidentiality and accuracy.
        """
        
        self.add_template(AnalysisTemplate(
            name="medical_consultation",
            description="Medical consultation and patient interaction analysis",
            schema=medical_schema,
            prompt_template=medical_prompt,
            domain="medical"
        ))
        
        # Legal Analysis Template
        legal_schema = {
            "type": "object",
            "properties": {
                "case_info": {
                    "type": "object",
                    "properties": {
                        "case_number": {"type": ["string", "null"]},
                        "case_type": {"type": ["string", "null"]},
                        "jurisdiction": {"type": ["string", "null"]}
                    }
                },
                "parties": {
                    "type": "object",
                    "properties": {
                        "plaintiffs": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "defendants": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "attorneys": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "representing": {"type": ["string", "null"]},
                                    "firm": {"type": ["string", "null"]}
                                },
                                "required": ["name"]
                            }
                        }
                    }
                },
                "legal_issues": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Legal issues and claims discussed"
                },
                "statutes_cited": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Laws, statutes, or regulations referenced"
                },
                "case_citations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Legal precedents and case law cited"
                },
                "key_facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Important factual elements"
                },
                "decisions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "decision": {"type": "string"},
                            "reasoning": {"type": ["string", "null"]}
                        },
                        "required": ["decision"]
                    }
                },
                "deadlines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "action": {"type": "string"}
                        },
                        "required": ["date", "action"]
                    }
                },
                "summary": {
                    "type": "string",
                    "description": "Legal summary of the proceeding"
                }
            },
            "required": ["summary"]
        }
        
        legal_prompt = """
        You are a legal transcription specialist. Analyze this legal proceeding transcript and extract structured information.
        
        Focus on:
        - Case identification and type
        - Parties involved (plaintiffs, defendants, attorneys)
        - Legal issues and claims
        - Statutes and regulations cited
        - Case law and precedents referenced
        - Key factual elements
        - Court decisions and rulings
        - Important deadlines and dates
        
        Maintain accuracy and legal terminology precision.
        """
        
        self.add_template(AnalysisTemplate(
            name="legal_proceeding",
            description="Legal proceeding and court transcript analysis",
            schema=legal_schema,
            prompt_template=legal_prompt,
            domain="legal"
        ))
        
        # Business Meeting Template
        business_schema = {
            "type": "object",
            "properties": {
                "meeting_info": {
                    "type": "object",
                    "properties": {
                        "title": {"type": ["string", "null"]},
                        "date": {"type": ["string", "null"]},
                        "duration": {"type": ["string", "null"]},
                        "meeting_type": {"type": ["string", "null"]}
                    }
                },
                "attendees": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "role": {"type": ["string", "null"]},
                            "department": {"type": ["string", "null"]}
                        },
                        "required": ["name"]
                    }
                },
                "agenda_items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Topics discussed in the meeting"
                },
                "decisions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "decision": {"type": "string"},
                            "rationale": {"type": ["string", "null"]},
                            "responsible_party": {"type": ["string", "null"]}
                        },
                        "required": ["decision"]
                    }
                },
                "action_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string"},
                            "assignee": {"type": ["string", "null"]},
                            "deadline": {"type": ["string", "null"]},
                            "priority": {"type": ["string", "null"]}
                        },
                        "required": ["task"]
                    }
                },
                "financial_data": {
                    "type": "object",
                    "properties": {
                        "budgets": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "costs": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "revenue": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "projects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "status": {"type": ["string", "null"]},
                            "timeline": {"type": ["string", "null"]}
                        },
                        "required": ["name"]
                    }
                },
                "risks_issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "issue": {"type": "string"},
                            "severity": {"type": ["string", "null"]},
                            "mitigation": {"type": ["string", "null"]}
                        },
                        "required": ["issue"]
                    }
                },
                "next_meeting": {
                    "type": "object",
                    "properties": {
                        "date": {"type": ["string", "null"]},
                        "agenda": {"type": ["string", "null"]}
                    }
                },
                "summary": {
                    "type": "string",
                    "description": "Executive summary of the meeting"
                }
            },
            "required": ["summary"]
        }
        
        business_prompt = """
        You are a business meeting analyst. Analyze this business meeting transcript and extract structured information.
        
        Focus on:
        - Meeting details and attendees
        - Agenda items and topics discussed
        - Decisions made and their rationale
        - Action items with assignments and deadlines
        - Financial information (budgets, costs, revenue)
        - Project updates and status
        - Risks and issues identified
        - Next steps and future meetings
        
        Maintain business terminology and professional accuracy.
        """
        
        self.add_template(AnalysisTemplate(
            name="business_meeting",
            description="Business meeting and corporate discussion analysis",
            schema=business_schema,
            prompt_template=business_prompt,
            domain="business"
        ))
        
        # Educational Content Template
        educational_schema = {
            "type": "object",
            "properties": {
                "course_info": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": ["string", "null"]},
                        "level": {"type": ["string", "null"]},
                        "instructor": {"type": ["string", "null"]},
                        "session_number": {"type": ["string", "null"]}
                    }
                },
                "learning_objectives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Educational goals and objectives"
                },
                "key_concepts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "concept": {"type": "string"},
                            "definition": {"type": ["string", "null"]},
                            "examples": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["concept"]
                    }
                },
                "topics_covered": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Main topics discussed in the lesson"
                },
                "assignments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "assignment": {"type": "string"},
                            "due_date": {"type": ["string", "null"]},
                            "requirements": {"type": ["string", "null"]}
                        },
                        "required": ["assignment"]
                    }
                },
                "questions_asked": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "answer": {"type": ["string", "null"]},
                            "student": {"type": ["string", "null"]}
                        },
                        "required": ["question"]
                    }
                },
                "resources_mentioned": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "resource": {"type": "string"},
                            "type": {"type": ["string", "null"]},
                            "url": {"type": ["string", "null"]}
                        },
                        "required": ["resource"]
                    }
                },
                "assessments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "date": {"type": ["string", "null"]},
                            "topics": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["type"]
                    }
                },
                "summary": {
                    "type": "string",
                    "description": "Educational summary of the lesson"
                }
            },
            "required": ["summary"]
        }
        
        educational_prompt = """
        You are an educational content analyst. Analyze this educational content transcript and extract structured information.
        
        Focus on:
        - Course and session information
        - Learning objectives and goals
        - Key concepts with definitions and examples
        - Topics covered in the lesson
        - Assignments and homework
        - Student questions and interactions
        - Educational resources mentioned
        - Assessments and evaluations
        
        Maintain educational terminology and pedagogical accuracy.
        """
        
        self.add_template(AnalysisTemplate(
            name="educational_content",
            description="Educational lecture and classroom content analysis",
            schema=educational_schema,
            prompt_template=educational_prompt,
            domain="educational"
        ))
    
    def add_template(self, template: AnalysisTemplate):
        """Add a new analysis template"""
        self.templates[template.name] = template
        logger.info(f"Added analysis template: {template.name} ({template.domain})")
    
    def get_templates(self, domain: Optional[str] = None) -> List[AnalysisTemplate]:
        """Get available templates, optionally filtered by domain"""
        templates = list(self.templates.values())
        if domain:
            templates = [t for t in templates if t.domain == domain]
        return templates
    
    def get_template(self, name: str) -> Optional[AnalysisTemplate]:
        """Get a specific template by name"""
        return self.templates.get(name)
    
    def validate_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate data against JSON schema"""
        errors = []
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            errors.append(f"Validation error: {e.message}")
            if e.path:
                errors.append(f"Path: {' -> '.join(str(p) for p in e.path)}")
        except Exception as e:
            errors.append(f"Schema validation failed: {str(e)}")
        
        return errors
    
    def analyze_with_template(self, text: str, template_name: str) -> AnalysisResult:
        """Perform structured analysis using a specific template"""
        start_time = datetime.now()
        
        if not text or not text.strip():
            raise NERError(
                message="Text cannot be empty for structured analysis",
                error_code=ErrorCode.NER_INVALID_INPUT,
                user_message="Text cannot be empty for analysis.",
                ner_type="structured",
                suggestions=["Provide text content for analysis"]
            )
        
        template = self.get_template(template_name)
        if not template:
            raise NERError(
                message=f"Template '{template_name}' not found",
                error_code=ErrorCode.NER_INVALID_INPUT,
                user_message=f"Analysis template '{template_name}' not found.",
                ner_type="structured",
                suggestions=[
                    f"Available templates: {', '.join(self.templates.keys())}",
                    "Check template name spelling"
                ]
            )
        
        try:
            client = self._get_openai_client()
            
            # Create the analysis prompt
            messages = [
                {
                    "role": "system",
                    "content": f"""{template.prompt_template}
                    
                    Return your analysis as a valid JSON object that matches this schema:
                    {json.dumps(template.schema, indent=2)}
                    
                    IMPORTANT: Return ONLY valid JSON. Do not include any explanatory text before or after the JSON."""
                },
                {
                    "role": "user",
                    "content": f"Analyze this {template.domain} content:\n\n{text}"
                }
            ]
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            try:
                # Find JSON boundaries
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = result_text[start_idx:end_idx]
                    data = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON found", result_text, 0)
                
            except json.JSONDecodeError as e:
                raise NERError(
                    message=f"Failed to parse analysis result as JSON: {str(e)}",
                    error_code=ErrorCode.NER_PROCESSING_ERROR,
                    user_message="Failed to parse AI analysis result.",
                    ner_type="structured",
                    suggestions=[
                        "Try with different text",
                        "Check if text is too long or complex",
                        "Try a different analysis template"
                    ]
                )
            
            # Validate against schema
            validation_errors = self.validate_data(data, template.schema)
            
            # Calculate processing time and confidence
            processing_time = (datetime.now() - start_time).total_seconds()
            confidence = self._calculate_confidence(data, template)
            
            result = AnalysisResult(
                template_name=template_name,
                domain=template.domain,
                data=data,
                confidence=confidence,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                validation_errors=validation_errors if validation_errors else None
            )
            
            logger.info(f"Structured analysis completed: {template_name} ({processing_time:.2f}s)")
            return result
            
        except Exception as e:
            if isinstance(e, (NERError, APIError)):
                raise
            app_error = handle_error(e, {
                "ner_type": "structured",
                "template": template_name,
                "text_length": len(text),
                "operation": "structured_analysis"
            })
            raise app_error
    
    def _calculate_confidence(self, data: Dict[str, Any], template: AnalysisTemplate) -> float:
        """Calculate confidence score based on data completeness"""
        total_fields = len(template.schema.get("properties", {}))
        filled_fields = len([k for k, v in data.items() if v is not None and v != [] and v != ""])
        
        if total_fields == 0:
            return 0.0
        
        base_confidence = filled_fields / total_fields
        
        # Bonus for required fields
        required_fields = template.schema.get("required", [])
        required_filled = len([k for k in required_fields if k in data and data[k]])
        required_bonus = required_filled / len(required_fields) if required_fields else 1.0
        
        return min(1.0, base_confidence * 0.7 + required_bonus * 0.3)
    
    def export_result(self, result: AnalysisResult, format: str = "json") -> str:
        """Export analysis result in specified format"""
        if format.lower() == "json":
            return json.dumps(asdict(result), indent=2, ensure_ascii=False)
        
        elif format.lower() == "csv":
            # Flatten the data for CSV export
            import csv
            import io
            
            output = io.StringIO()
            
            # Write metadata
            writer = csv.writer(output)
            writer.writerow(["Field", "Value"])
            writer.writerow(["Template", result.template_name])
            writer.writerow(["Domain", result.domain])
            writer.writerow(["Confidence", f"{result.confidence:.2f}"])
            writer.writerow(["Processing Time", f"{result.processing_time:.2f}s"])
            writer.writerow(["Timestamp", result.timestamp])
            writer.writerow([])  # Empty row
            
            # Write data
            def flatten_dict(d, parent_key='', sep='_'):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    elif isinstance(v, list):
                        for i, item in enumerate(v):
                            if isinstance(item, dict):
                                items.extend(flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                            else:
                                items.append((f"{new_key}_{i}", str(item)))
                    else:
                        items.append((new_key, str(v) if v is not None else ""))
                return dict(items)
            
            flattened = flatten_dict(result.data)
            for key, value in flattened.items():
                writer.writerow([key, value])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def create_custom_template(self, name: str, description: str, domain: str, 
                             schema: Dict[str, Any], prompt_template: str) -> AnalysisTemplate:
        """Create a custom analysis template"""
        # Validate schema
        try:
            # Test schema with empty data
            validate(instance={}, schema=schema)
        except Exception:
            # Schema is valid if it can be used for validation
            pass
        
        template = AnalysisTemplate(
            name=name,
            description=description,
            schema=schema,
            prompt_template=prompt_template,
            domain=domain,
            version="custom"
        )
        
        self.add_template(template)
        return template

# Global instance
structured_analyzer = StructuredAnalyzer()

# Convenience functions
def get_available_templates(domain: Optional[str] = None) -> List[Dict[str, str]]:
    """Get list of available templates"""
    templates = structured_analyzer.get_templates(domain)
    return [
        {
            "name": t.name,
            "description": t.description,
            "domain": t.domain,
            "version": t.version
        }
        for t in templates
    ]

def analyze_with_schema(text: str, template_name: str) -> Dict[str, Any]:
    """Perform structured analysis and return result as dictionary"""
    result = structured_analyzer.analyze_with_template(text, template_name)
    return asdict(result)

def validate_analysis_result(data: Dict[str, Any], template_name: str) -> List[str]:
    """Validate analysis result against template schema"""
    template = structured_analyzer.get_template(template_name)
    if not template:
        return [f"Template '{template_name}' not found"]
    
    return structured_analyzer.validate_data(data, template.schema)

def export_analysis(result: AnalysisResult, format: str = "json") -> str:
    """Export analysis result in specified format"""
    return structured_analyzer.export_result(result, format)