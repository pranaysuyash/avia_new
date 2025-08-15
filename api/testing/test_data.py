"""
Test Data
Comprehensive test data for API testing
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class TestDataTypes(Enum):
    """Types of test data available"""
    MEDICAL_TRANSCRIPTS = "medical_transcripts"
    STANDARD_TRANSCRIPTS = "standard_transcripts" 
    USER_DATA = "user_data"
    API_KEYS = "api_keys"
    PHI_DATA = "phi_data"
    COMPLIANCE_DATA = "compliance_data"
    AUDIO_FILES = "audio_files"
    GRAPHQL_QUERIES = "graphql_queries"
    ERROR_SCENARIOS = "error_scenarios"


def get_test_data(data_type: TestDataTypes) -> Dict[str, Any]:
    """Get test data by type"""
    
    if data_type == TestDataTypes.MEDICAL_TRANSCRIPTS:
        return get_medical_transcripts_test_data()
    elif data_type == TestDataTypes.STANDARD_TRANSCRIPTS:
        return get_standard_transcripts_test_data()
    elif data_type == TestDataTypes.USER_DATA:
        return get_user_test_data()
    elif data_type == TestDataTypes.API_KEYS:
        return get_api_keys_test_data()
    elif data_type == TestDataTypes.PHI_DATA:
        return get_phi_test_data()
    elif data_type == TestDataTypes.COMPLIANCE_DATA:
        return get_compliance_test_data()
    elif data_type == TestDataTypes.AUDIO_FILES:
        return get_audio_files_test_data()
    elif data_type == TestDataTypes.GRAPHQL_QUERIES:
        return get_graphql_test_data()
    elif data_type == TestDataTypes.ERROR_SCENARIOS:
        return get_error_scenarios_test_data()
    else:
        return {}


def get_medical_transcripts_test_data() -> Dict[str, Any]:
    """Medical transcripts test data"""
    return {
        "cardiology_consultation": {
            "title": "Cardiology Follow-up Consultation",
            "patient_id": "PAT001",
            "provider_id": "DOC001", 
            "encounter_type": "follow_up",
            "compliance_level": "standard",
            "transcript": """
            Patient presents for cardiology follow-up. 68-year-old male with history of 
            coronary artery disease, status post CABG in 2019. Currently on dual antiplatelet 
            therapy with aspirin 81 mg and clopidogrel 75 mg daily. Also taking metoprolol 
            50 mg twice daily and atorvastatin 40 mg daily.
            
            Patient reports no chest pain, shortness of breath, or palpitations since last visit.
            Exercise tolerance has improved. Walking 2 miles daily without symptoms.
            
            Physical examination reveals blood pressure 125/78 mmHg, heart rate 62 bpm regular.
            Heart sounds are normal, no murmurs. Lungs clear bilaterally. No edema.
            
            EKG shows normal sinus rhythm, no acute changes.
            Recent labs show LDL 85 mg/dL, well-controlled.
            
            Assessment: Stable coronary artery disease, well-controlled on current regimen.
            Plan: Continue current medications. Return in 6 months or sooner if symptoms develop.
            """,
            "expected_entities": ["coronary artery disease", "CABG", "aspirin", "clopidogrel", "metoprolol"],
            "expected_medications": [
                {"name": "aspirin", "dosage": "81 mg", "frequency": "daily"},
                {"name": "clopidogrel", "dosage": "75 mg", "frequency": "daily"},
                {"name": "metoprolol", "dosage": "50 mg", "frequency": "twice daily"}
            ],
            "expected_procedures": ["EKG", "physical examination"],
            "expected_diagnoses": ["coronary artery disease"],
            "expected_vital_signs": [
                {"type": "blood_pressure", "value": "125/78", "unit": "mmHg"},
                {"type": "heart_rate", "value": "62", "unit": "bpm"}
            ]
        },
        
        "diabetes_management": {
            "title": "Diabetes Management Visit",
            "patient_id": "PAT002",
            "provider_id": "DOC002",
            "encounter_type": "routine",
            "compliance_level": "standard",
            "transcript": """
            45-year-old female with type 2 diabetes mellitus for 8 years, here for routine 
            diabetes management. Currently on metformin 1000 mg twice daily and glipizide 
            10 mg daily. Home glucose monitoring shows fasting values 110-140 mg/dL.
            
            Patient reports good medication compliance. Following diabetic diet most of the time
            but admits to occasional lapses during holidays. Exercise consists of walking 
            30 minutes 3-4 times per week.
            
            Physical exam: BMI 32.1, blood pressure 138/85 mmHg. Diabetic foot exam normal,
            no neuropathy detected. Fundoscopic exam shows no diabetic retinopathy.
            
            Recent A1c is 7.2%, improved from 8.1% six months ago.
            Microalbumin/creatinine ratio is normal at 15 mg/g.
            
            Assessment: Type 2 diabetes with good control, improving trend.
            Plan: Continue current medications. Referral to nutrition counseling.
            Recheck A1c in 3 months. Annual ophthalmology exam scheduled.
            """,
            "expected_entities": ["type 2 diabetes mellitus", "metformin", "glipizide", "A1c"],
            "expected_medications": [
                {"name": "metformin", "dosage": "1000 mg", "frequency": "twice daily"},
                {"name": "glipizide", "dosage": "10 mg", "frequency": "daily"}
            ],
            "expected_test_results": [
                {"test_name": "A1c", "value": "7.2%", "interpretation": "improved"},
                {"test_name": "microalbumin/creatinine ratio", "value": "15 mg/g", "interpretation": "normal"}
            ]
        },
        
        "mental_health_assessment": {
            "title": "Mental Health Assessment",
            "patient_id": "PAT003", 
            "provider_id": "PSY001",
            "encounter_type": "assessment",
            "compliance_level": "standard",
            "transcript": """
            32-year-old male presents for initial psychiatric evaluation with complaints of
            depression and anxiety for the past 6 months. Symptoms began after job loss.
            Reports low mood, decreased interest in activities, poor sleep, and difficulty
            concentrating. Also experiencing worry, restlessness, and panic episodes.
            
            Patient appears somewhat anxious but cooperative. Speech is soft and slow.
            Mood is depressed, affect is constricted. No suicidal or homicidal ideation.
            Cognitive function appears intact.
            
            PHQ-9 score: 14 (moderate depression)
            GAD-7 score: 12 (moderate anxiety)
            
            Social history: Recently unemployed, lives alone, limited social support.
            Family history positive for depression in mother.
            
            Assessment: Major depressive episode, moderate severity with anxiety symptoms.
            Plan: Start sertraline 50 mg daily. Refer to therapy. Follow up in 2 weeks.
            Discussed side effects and importance of compliance.
            """,
            "expected_entities": ["depression", "anxiety", "sertraline", "PHQ-9", "GAD-7"],
            "expected_emotional_state": [
                {"emotion": "depression", "intensity": 7, "context": "moderate severity"},
                {"emotion": "anxiety", "intensity": 6, "context": "moderate symptoms"}
            ],
            "expected_social_determinants": [
                {"category": "employment", "factor": "unemployed", "impact_level": "high"},
                {"category": "social_support", "factor": "limited", "impact_level": "medium"}
            ]
        }
    }


def get_standard_transcripts_test_data() -> Dict[str, Any]:
    """Standard (non-medical) transcripts test data"""
    return {
        "business_meeting": {
            "title": "Q3 Planning Meeting",
            "transcript": """
            Good morning everyone, let's start our Q3 planning session. First item on the 
            agenda is reviewing our Q2 performance metrics. Sarah, can you walk us through 
            the numbers?
            
            Thanks John. So our revenue for Q2 came in at $2.3 million, which is 15% above 
            our target. The marketing campaigns really paid off, especially the digital 
            initiatives. Customer acquisition cost decreased by 20%.
            
            That's excellent news. What about the product development timeline? Are we still 
            on track for the August release?
            
            We're looking good for August. The development team has completed 85% of the 
            features. QA testing is starting next week. We might even finish ahead of schedule.
            
            Perfect. Let's discuss budget allocation for Q3...
            """,
            "language": "en",
            "expected_speakers": 3,
            "expected_topics": ["Q3 planning", "revenue", "marketing", "product development"]
        },
        
        "podcast_interview": {
            "title": "Tech Industry Podcast Interview", 
            "transcript": """
            Welcome to TechTalk, I'm your host Mike Chen. Today we're joined by Dr. Lisa Rodriguez,
            CTO of InnovateAI. Lisa, thanks for joining us.
            
            Thanks for having me, Mike. Great to be here.
            
            Let's dive right in. Your company has been making waves in the AI space. Can you
            tell us about your latest breakthrough in natural language processing?
            
            Absolutely. We've developed a new transformer architecture that reduces training
            time by 40% while maintaining accuracy. It's particularly effective for 
            multilingual applications.
            
            That sounds impressive. How does this compare to existing solutions like GPT-4?
            
            Our approach focuses on efficiency rather than raw parameter count. We're seeing
            comparable performance with significantly lower computational requirements...
            """,
            "language": "en",
            "expected_speakers": 2,
            "expected_topics": ["AI", "natural language processing", "transformers", "GPT-4"]
        }
    }


def get_user_test_data() -> Dict[str, Any]:
    """User test data"""
    return {
        "test_users": {
            "basic_user": {
                "id": 1001,
                "email": "basic.user@testmed.com",
                "first_name": "Basic",
                "last_name": "User", 
                "role": "user",
                "tier": "free",
                "is_active": True,
                "created_at": "2024-01-15T10:00:00Z"
            },
            "medical_professional": {
                "id": 1002,
                "email": "dr.smith@hospital.com",
                "first_name": "Dr. Jane",
                "last_name": "Smith",
                "role": "medical_professional",
                "tier": "professional", 
                "license_number": "MD123456",
                "specialty": "Internal Medicine",
                "is_active": True,
                "created_at": "2024-01-10T14:30:00Z"
            },
            "healthcare_admin": {
                "id": 1003,
                "email": "admin@healthsystem.com",
                "first_name": "Healthcare",
                "last_name": "Administrator",
                "role": "healthcare_admin",
                "tier": "enterprise",
                "organization": "Metro Health System",
                "is_active": True,
                "created_at": "2024-01-05T09:00:00Z"
            },
            "system_admin": {
                "id": 1004,
                "email": "sysadmin@platform.com", 
                "first_name": "System",
                "last_name": "Administrator",
                "role": "system_admin",
                "tier": "enterprise",
                "permissions": ["all"],
                "is_active": True,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }
    }


def get_api_keys_test_data() -> Dict[str, Any]:
    """API keys test data"""
    return {
        "api_keys": {
            "basic_api_key": {
                "name": "Basic User API Key",
                "permissions": ["read_own_data", "write_own_data"],
                "rate_limit_tier": "basic",
                "expires_in_days": 90
            },
            "medical_api_key": {
                "name": "Medical Professional API Key",
                "permissions": [
                    "read_own_data", "write_own_data", "process_medical_transcription",
                    "access_phi_data", "export_phi_data"
                ],
                "rate_limit_tier": "professional",
                "expires_in_days": 365
            },
            "enterprise_api_key": {
                "name": "Enterprise Integration Key",
                "permissions": [
                    "read_own_data", "write_own_data", "process_medical_transcription",
                    "access_phi_data", "cross_patient_analytics", "manage_providers"
                ],
                "rate_limit_tier": "enterprise",
                "expires_in_days": None  # No expiration
            }
        }
    }


def get_phi_test_data() -> Dict[str, Any]:
    """PHI (Protected Health Information) test data"""
    return {
        "phi_examples": {
            "names": [
                "John Doe", "Jane Smith", "Michael Johnson", "Dr. Robert Wilson",
                "Sarah Davis", "Patient Mary Brown"
            ],
            "dates": [
                "01/15/1980", "12/25/1975", "July 4th, 1990", "March 3, 1985",
                "DOB: 06/10/1970", "born 11/22/1988"
            ],
            "phone_numbers": [
                "(555) 123-4567", "555-987-6543", "1-800-555-0199",
                "phone: 555.111.2222", "tel: (555) 999-8888"
            ],
            "addresses": [
                "123 Main Street, Anytown, ST 12345",
                "456 Oak Avenue, Suite 200, Somewhere, CA 90210",
                "789 Pine Road, Unit 3B, Nowhere, NY 10001"
            ],
            "ssn": [
                "123-45-6789", "987-65-4321", "SSN: 555-44-3333"
            ],
            "mrn": [
                "MRN: 1234567", "Medical Record Number: 9876543",
                "Patient ID: ABC123456"
            ]
        },
        
        "phi_test_transcripts": {
            "high_phi_content": """
            Patient John Doe, DOB 01/15/1980, MRN 1234567, presents for follow-up.
            Phone number on file: (555) 123-4567.
            Address: 123 Main St, Anytown, ST 12345.
            SSN: 123-45-6789.
            Insurance ID: ABC123456789.
            Next of kin: Jane Doe, phone (555) 987-6543.
            """,
            
            "moderate_phi_content": """
            65-year-old male patient presents with chest pain. Lives in downtown area.
            Contact number ends in 4567. Has been seeing Dr. Smith for 3 years.
            Previous hospitalization was in January 2023.
            """,
            
            "low_phi_content": """
            Elderly male patient presents with cardiovascular concerns.
            Lives in urban area. Has established relationship with cardiology.
            Previous treatment was effective.
            """,
            
            "no_phi_content": """
            Patient presents with symptoms consistent with viral upper respiratory infection.
            Physical examination reveals mild throat erythema and clear lung sounds.
            Recommended supportive care and return if symptoms worsen.
            """
        }
    }


def get_compliance_test_data() -> Dict[str, Any]:
    """HIPAA compliance test data"""
    return {
        "compliance_levels": {
            "strict": {
                "description": "No PHI allowed - all personal information removed",
                "phi_detection": True,
                "phi_removal": True, 
                "anonymization": True,
                "audit_logging": True,
                "allowed_entities": [
                    "symptom", "diagnosis", "procedure", "medication",
                    "vital_sign", "test_result"
                ],
                "blocked_entities": [
                    "name", "phone", "address", "ssn", "mrn", "date_of_birth"
                ]
            },
            "standard": {
                "description": "PHI anonymized using secure tokens",
                "phi_detection": True,
                "phi_removal": False,
                "anonymization": True,
                "audit_logging": True,
                "allowed_entities": [
                    "symptom", "diagnosis", "procedure", "medication",
                    "vital_sign", "test_result", "provider"
                ],
                "anonymized_entities": [
                    "name", "phone", "address", "ssn", "mrn", "date_of_birth"
                ]
            },
            "research": {
                "description": "Limited PHI allowed for research with consent",
                "phi_detection": True,
                "phi_removal": False,
                "anonymization": False,
                "audit_logging": True,
                "allowed_entities": "all",
                "special_handling": [
                    "consent_required", "irb_approval", "data_use_agreement"
                ]
            }
        },
        
        "audit_events": {
            "access_events": [
                "phi_data_accessed", "medical_transcript_viewed", 
                "patient_data_exported", "analytics_report_generated"
            ],
            "modification_events": [
                "transcript_edited", "phi_data_anonymized",
                "compliance_level_changed", "user_permissions_modified"
            ],
            "security_events": [
                "unauthorized_access_attempt", "phi_violation_detected",
                "data_breach_suspected", "compliance_violation_flagged"
            ]
        }
    }


def get_audio_files_test_data() -> Dict[str, Any]:
    """Audio files test data"""
    return {
        "audio_formats": {
            "wav": {
                "mime_type": "audio/wav",
                "extension": ".wav",
                "supported": True,
                "sample_file_size": 5242880  # 5MB
            },
            "mp3": {
                "mime_type": "audio/mpeg",
                "extension": ".mp3", 
                "supported": True,
                "sample_file_size": 3145728  # 3MB
            },
            "mp4": {
                "mime_type": "audio/mp4",
                "extension": ".mp4",
                "supported": True,
                "sample_file_size": 4194304  # 4MB
            },
            "ogg": {
                "mime_type": "audio/ogg",
                "extension": ".ogg",
                "supported": True,
                "sample_file_size": 2097152  # 2MB
            },
            "webm": {
                "mime_type": "audio/webm",
                "extension": ".webm",
                "supported": True,
                "sample_file_size": 3670016  # 3.5MB
            }
        },
        
        "test_scenarios": {
            "short_audio": {
                "duration": 30,  # seconds
                "description": "Short medical consultation snippet"
            },
            "medium_audio": {
                "duration": 300,  # 5 minutes
                "description": "Standard consultation length"
            },
            "long_audio": {
                "duration": 1800,  # 30 minutes  
                "description": "Extended consultation or procedure"
            },
            "very_long_audio": {
                "duration": 3600,  # 1 hour
                "description": "Long procedure or conference"
            }
        }
    }


def get_graphql_test_data() -> Dict[str, Any]:
    """GraphQL test queries and mutations"""
    return {
        "queries": {
            "introspection": """
                query IntrospectionQuery {
                    __schema {
                        queryType { name }
                        mutationType { name }
                        subscriptionType { name }
                        types {
                            name
                            kind
                        }
                    }
                }
            """,
            
            "current_user": """
                query GetCurrentUser {
                    currentUser {
                        id
                        email
                        role
                        createdAt
                        updatedAt
                    }
                }
            """,
            
            "medical_transcripts_with_filters": """
                query GetFilteredMedicalTranscripts(
                    $limit: Int = 20,
                    $offset: Int = 0,
                    $complianceLevel: HIPAAComplianceLevel,
                    $patientIds: [String],
                    $providerIds: [String]
                ) {
                    medicalTranscripts(
                        limit: $limit,
                        offset: $offset,
                        complianceLevel: $complianceLevel,
                        patientIds: $patientIds,
                        providerIds: $providerIds
                    ) {
                        id
                        title
                        content
                        patientId
                        providerId
                        encounterType
                        complianceLevel
                        entities {
                            text
                            entityType
                            confidence
                            medicalCode
                        }
                        medications {
                            name
                            dosage
                            frequency
                            medicalCode
                        }
                        comprehensiveAnalysis {
                            patientEngagementScore
                            careQualityIndicators {
                                indicator
                                status
                                score
                                benchmark
                            }
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
        },
        
        "mutations": {
            "create_medical_transcription": """
                mutation CreateMedicalTranscription($input: MedicalTranscriptionInput!) {
                    startMedicalTranscription(transcriptionInput: $input) {
                        id
                        userId
                        status
                        progress
                        fileUrl
                        language
                        complianceLevel
                        enableComprehensiveAnalysis
                        enablePhiDetection
                        createdAt
                        updatedAt
                    }
                }
            """,
            
            "update_medical_transcript": """
                mutation UpdateMedicalTranscript(
                    $transcriptId: String!,
                    $content: String,
                    $title: String,
                    $patientId: String,
                    $providerId: String
                ) {
                    updateMedicalTranscript(
                        transcriptId: $transcriptId,
                        content: $content,
                        title: $title,
                        patientId: $patientId,
                        providerId: $providerId
                    ) {
                        id
                        title
                        content
                        patientId
                        providerId
                        updatedAt
                    }
                }
            """
        },
        
        "subscriptions": {
            "medical_transcription_status": """
                subscription MedicalTranscriptionUpdates($userId: Int!) {
                    medicalTranscriptionStatus(userId: $userId) {
                        id
                        userId
                        status
                        progress
                        fileUrl
                        complianceLevel
                        updatedAt
                        errorMessage
                    }
                }
            """,
            
            "hipaa_alerts": """
                subscription HIPAAAlerts($severityThreshold: String = "medium") {
                    hipaaComplianceAlerts(severityThreshold: $severityThreshold)
                }
            """
        }
    }


def get_error_scenarios_test_data() -> Dict[str, Any]:
    """Error scenarios test data"""
    return {
        "authentication_errors": {
            "missing_token": {
                "request": {"headers": {}},
                "expected_status": 401,
                "expected_error": "Authentication required"
            },
            "invalid_token": {
                "request": {"headers": {"Authorization": "Bearer invalid_token"}},
                "expected_status": 401,
                "expected_error": "Invalid token"
            },
            "expired_token": {
                "request": {"headers": {"Authorization": "Bearer expired_token_here"}},
                "expected_status": 401,
                "expected_error": "Token has expired"
            }
        },
        
        "authorization_errors": {
            "insufficient_permissions": {
                "endpoint": "/api/v2.1/medical/analytics",
                "user_role": "basic_user",
                "expected_status": 403,
                "expected_error": "Insufficient permissions"
            },
            "wrong_role": {
                "endpoint": "/api/v2.1/medical/transcriptions",
                "user_role": "basic_user", 
                "expected_status": 403,
                "expected_error": "Medical professional role required"
            }
        },
        
        "validation_errors": {
            "invalid_file_format": {
                "file_extension": ".txt",
                "expected_status": 400,
                "expected_error": "Invalid file format"
            },
            "missing_required_fields": {
                "request_data": {"title": "Test"},  # Missing required fields
                "expected_status": 400,
                "expected_error": "Missing required field"
            },
            "invalid_compliance_level": {
                "compliance_level": "invalid_level",
                "expected_status": 400,
                "expected_error": "Invalid compliance level"
            }
        },
        
        "rate_limit_errors": {
            "too_many_requests": {
                "requests_per_minute": 100,
                "expected_status": 429,
                "expected_error": "Rate limit exceeded"
            },
            "medical_api_limit": {
                "medical_requests_per_hour": 300,
                "expected_status": 429,
                "expected_error": "Medical transcription rate limit exceeded"
            }
        }
    }