#!/usr/bin/env python3
"""
Legal Transcription and Analysis System - Task 142
Main system integrating legal entity extraction, case analysis, and compliance checking
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from legal_transcription_core import (
    LegalEntity, LegalEntityType, LegalSpecialty, ProceedingType,
    LegalCitation, LegalArgument
)
from legal_schema_processor import LegalEntityExtractor, COMPREHENSIVE_LEGAL_SCHEMA

logger = logging.getLogger(__name__)

@dataclass
class LegalDocument:
    """Complete legal document analysis"""
    document_id: str
    document_type: ProceedingType
    specialty: LegalSpecialty
    case_number: str
    court: str
    parties: List[str]
    created_at: datetime
    entities: Dict[str, List[LegalEntity]]
    citations: List[LegalCitation]
    arguments: List[LegalArgument]
    compliance_status: str
    risk_assessment: Dict[str, Any]
    word_count: int
    estimated_time_saved: float

class LegalCaseAnalyzer:
    """Analyze legal cases and extract key information"""
    
    def __init__(self):
        self.case_law_database = self._load_case_law_database()
        self.legal_standards = self._load_legal_standards()
    
    def _load_case_law_database(self) -> Dict[str, Dict[str, Any]]:
        """Load case law database for reference"""
        return {
            # Constitutional Law
            "Brown v. Board of Education": {
                "citation": "347 U.S. 483 (1954)",
                "court": "Supreme Court",
                "year": "1954",
                "area": "constitutional_law",
                "holding": "Separate educational facilities are inherently unequal",
                "significance": "landmark",
                "keywords": ["equal protection", "education", "segregation"]
            },
            "Miranda v. Arizona": {
                "citation": "384 U.S. 436 (1966)",
                "court": "Supreme Court", 
                "year": "1966",
                "area": "criminal_law",
                "holding": "Suspects must be informed of rights before interrogation",
                "significance": "landmark",
                "keywords": ["miranda rights", "self-incrimination", "due process"]
            },
            
            # Contract Law
            "Hadley v. Baxendale": {
                "citation": "9 Ex. 341 (1854)",
                "court": "Court of Exchequer",
                "year": "1854", 
                "area": "contract_law",
                "holding": "Damages must be reasonably foreseeable at contract formation",
                "significance": "foundational",
                "keywords": ["consequential damages", "foreseeability", "breach"]
            },
            
            # Tort Law
            "Palsgraf v. Long Island Railroad": {
                "citation": "248 N.Y. 339 (1928)",
                "court": "New York Court of Appeals",
                "year": "1928",
                "area": "tort_law", 
                "holding": "Duty of care limited to foreseeable plaintiffs",
                "significance": "landmark",
                "keywords": ["negligence", "proximate cause", "duty", "foreseeability"]
            },
            
            # Corporate Law
            "Dodge v. Ford Motor Co.": {
                "citation": "204 Mich. 459 (1919)",
                "court": "Michigan Supreme Court",
                "year": "1919",
                "area": "corporate_law",
                "holding": "Directors must maximize shareholder value",
                "significance": "foundational",
                "keywords": ["fiduciary duty", "business judgment", "shareholder primacy"]
            }
        }
    
    def _load_legal_standards(self) -> Dict[str, Dict[str, Any]]:
        """Load legal standards and tests"""
        return {
            "burden_of_proof": {
                "beyond_reasonable_doubt": {
                    "standard": "criminal",
                    "description": "Highest standard of proof",
                    "percentage": "~99%",
                    "context": "criminal prosecution"
                },
                "clear_and_convincing": {
                    "standard": "intermediate",
                    "description": "Higher than preponderance",
                    "percentage": "~75%",
                    "context": "civil cases with heightened scrutiny"
                },
                "preponderance_of_evidence": {
                    "standard": "civil",
                    "description": "More likely than not",
                    "percentage": ">50%",
                    "context": "most civil cases"
                }
            },
            "constitutional_tests": {
                "strict_scrutiny": {
                    "elements": ["compelling government interest", "narrowly tailored"],
                    "application": "fundamental rights, suspect classifications",
                    "standard": "highest"
                },
                "intermediate_scrutiny": {
                    "elements": ["important government interest", "substantially related"],
                    "application": "quasi-suspect classifications",
                    "standard": "middle"
                },
                "rational_basis": {
                    "elements": ["legitimate government interest", "rationally related"],
                    "application": "economic regulations, general classifications",
                    "standard": "lowest"
                }
            }
        }
    
    def analyze_legal_arguments(self, transcript_text: str, entities: Dict[str, List[LegalEntity]]) -> List[LegalArgument]:
        """Analyze legal arguments in transcript"""
        arguments = []
        
        # Extract argument patterns
        argument_patterns = self._identify_argument_patterns(transcript_text)
        
        for i, pattern in enumerate(argument_patterns):
            argument = LegalArgument(
                argument_id=f"arg_{i+1}",
                attorney=pattern.get('speaker', 'Unknown'),
                argument_summary=pattern['summary'],
                legal_basis=pattern.get('legal_basis', []),
                factual_basis=pattern.get('factual_basis', []),
                precedents_cited=self._extract_precedents_from_pattern(pattern),
                counter_arguments=pattern.get('counter_arguments', []),
                strength_assessment=self._assess_argument_strength(pattern)
            )
            arguments.append(argument)
        
        return arguments
    
    def _identify_argument_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Identify legal argument patterns in text"""
        patterns = []
        
        # Simple pattern recognition for legal arguments
        # In practice, this would be more sophisticated
        argument_indicators = [
            "your honor", "the court should", "we argue that", "it is clear that",
            "the evidence shows", "the law requires", "precedent establishes"
        ]
        
        sentences = text.split('.')
        current_argument = None
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if sentence starts an argument
            if any(indicator in sentence.lower() for indicator in argument_indicators):
                if current_argument:
                    patterns.append(current_argument)
                
                current_argument = {
                    'summary': sentence,
                    'legal_basis': [],
                    'factual_basis': [],
                    'speaker': self._identify_speaker(sentence)
                }
            elif current_argument:
                # Add to current argument
                current_argument['summary'] += '. ' + sentence
                
                # Identify legal vs factual basis
                if any(word in sentence.lower() for word in ['statute', 'case', 'precedent', 'law']):
                    current_argument['legal_basis'].append(sentence)
                elif any(word in sentence.lower() for word in ['evidence', 'fact', 'testimony']):
                    current_argument['factual_basis'].append(sentence)
        
        if current_argument:
            patterns.append(current_argument)
        
        return patterns
    
    def _extract_precedents_from_pattern(self, pattern: Dict[str, Any]) -> List[LegalCitation]:
        """Extract legal precedents from argument pattern"""
        precedents = []
        text = pattern['summary']
        
        # Look for case names in the argument
        for case_name, case_info in self.case_law_database.items():
            if case_name.lower() in text.lower():
                citation = LegalCitation(
                    citation_text=case_info['citation'],
                    case_name=case_name,
                    court=case_info['court'],
                    year=case_info['year'],
                    citation_type="case",
                    relevance=self._assess_case_relevance(case_info, pattern),
                    holding=case_info['holding']
                )
                precedents.append(citation)
        
        return precedents
    
    def _assess_argument_strength(self, pattern: Dict[str, Any]) -> str:
        """Assess strength of legal argument"""
        score = 0
        
        # Check for legal basis
        if pattern.get('legal_basis'):
            score += len(pattern['legal_basis']) * 2
        
        # Check for factual basis
        if pattern.get('factual_basis'):
            score += len(pattern['factual_basis'])
        
        # Check for precedents
        precedents = self._extract_precedents_from_pattern(pattern)
        score += len(precedents) * 3
        
        # Assess based on score
        if score >= 10:
            return "strong"
        elif score >= 5:
            return "moderate"
        else:
            return "weak"
    
    def _identify_speaker(self, sentence: str) -> str:
        """Identify speaker from sentence context"""
        # Simple speaker identification
        if any(phrase in sentence.lower() for phrase in ['your honor', 'the court']):
            return 'attorney'
        elif any(phrase in sentence.lower() for phrase in ['counsel', 'attorney']):
            return 'judge'
        else:
            return 'unknown'
    
    def _assess_case_relevance(self, case_info: Dict[str, Any], pattern: Dict[str, Any]) -> str:
        """Assess relevance of cited case to current argument"""
        # Check keyword overlap
        pattern_text = pattern['summary'].lower()
        case_keywords = case_info.get('keywords', [])
        
        overlap = sum(1 for keyword in case_keywords if keyword in pattern_text)
        
        if overlap >= 2:
            return "highly_relevant"
        elif overlap >= 1:
            return "relevant"
        else:
            return "tangentially_relevant"

class LegalComplianceChecker:
    """Check legal compliance and ethical considerations"""
    
    def __init__(self):
        self.compliance_rules = self._load_compliance_rules()
        self.ethical_guidelines = self._load_ethical_guidelines()
    
    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load legal compliance rules"""
        return {
            "attorney_client_privilege": {
                "description": "Communications between attorney and client are privileged",
                "indicators": ["confidential", "privileged", "attorney-client"],
                "action": "redact_or_seal"
            },
            "work_product_doctrine": {
                "description": "Attorney work product is protected",
                "indicators": ["work product", "trial preparation", "strategy"],
                "action": "protect_from_disclosure"
            },
            "court_rules_compliance": {
                "description": "Must comply with local court rules",
                "indicators": ["filing deadline", "page limit", "format requirements"],
                "action": "verify_compliance"
            },
            "professional_conduct": {
                "description": "Must follow rules of professional conduct",
                "indicators": ["conflict of interest", "competence", "diligence"],
                "action": "ethics_review"
            }
        }
    
    def _load_ethical_guidelines(self) -> Dict[str, Any]:
        """Load ethical guidelines for legal practice"""
        return {
            "model_rules": {
                "rule_1_1": "Competence - lawyer must provide competent representation",
                "rule_1_3": "Diligence - lawyer must act with reasonable diligence",
                "rule_1_4": "Communication - lawyer must keep client informed",
                "rule_1_6": "Confidentiality - lawyer must maintain client confidentiality",
                "rule_1_7": "Conflicts - lawyer must avoid conflicts of interest"
            }
        }
    
    def check_compliance(self, transcript_text: str, entities: Dict[str, List[LegalEntity]]) -> Dict[str, Any]:
        """Check legal compliance of transcript"""
        compliance_results = {
            "overall_status": "compliant",
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check for privilege issues
        privilege_issues = self._check_privilege(transcript_text)
        if privilege_issues:
            compliance_results["violations"].extend(privilege_issues)
            compliance_results["overall_status"] = "non_compliant"
        
        # Check for ethical issues
        ethical_issues = self._check_ethics(transcript_text, entities)
        if ethical_issues:
            compliance_results["warnings"].extend(ethical_issues)
        
        # Check procedural compliance
        procedural_issues = self._check_procedural_compliance(transcript_text, entities)
        if procedural_issues:
            compliance_results["recommendations"].extend(procedural_issues)
        
        return compliance_results
    
    def _check_privilege(self, text: str) -> List[Dict[str, Any]]:
        """Check for privilege violations"""
        violations = []
        
        for rule_name, rule_info in self.compliance_rules.items():
            if rule_name in ["attorney_client_privilege", "work_product_doctrine"]:
                for indicator in rule_info["indicators"]:
                    if indicator in text.lower():
                        violations.append({
                            "type": rule_name,
                            "description": rule_info["description"],
                            "action_required": rule_info["action"],
                            "severity": "high"
                        })
        
        return violations
    
    def _check_ethics(self, text: str, entities: Dict[str, List[LegalEntity]]) -> List[Dict[str, Any]]:
        """Check for ethical issues"""
        warnings = []
        
        # Check for potential conflicts
        if "conflict" in text.lower():
            warnings.append({
                "type": "potential_conflict",
                "description": "Potential conflict of interest mentioned",
                "recommendation": "Review for actual conflicts"
            })
        
        # Check for competence issues
        if any(phrase in text.lower() for phrase in ["don't know", "unsure", "not familiar"]):
            warnings.append({
                "type": "competence_concern",
                "description": "Attorney expressed uncertainty about legal matter",
                "recommendation": "Ensure adequate preparation and competence"
            })
        
        return warnings
    
    def _check_procedural_compliance(self, text: str, entities: Dict[str, List[LegalEntity]]) -> List[Dict[str, Any]]:
        """Check procedural compliance"""
        recommendations = []
        
        # Check for deadline mentions
        if any(word in text.lower() for word in ["deadline", "due date", "filing"]):
            recommendations.append({
                "type": "deadline_tracking",
                "description": "Deadlines mentioned in transcript",
                "recommendation": "Ensure all deadlines are properly calendared"
            })
        
        # Check for discovery obligations
        if any(word in text.lower() for word in ["discovery", "document production", "interrogatory"]):
            recommendations.append({
                "type": "discovery_compliance",
                "description": "Discovery obligations discussed",
                "recommendation": "Verify compliance with discovery rules"
            })
        
        return recommendations

class LegalTranscriptionSystem:
    """Main legal transcription and analysis system"""
    
    def __init__(self):
        self.entity_extractor = LegalEntityExtractor()
        self.case_analyzer = LegalCaseAnalyzer()
        self.compliance_checker = LegalComplianceChecker()
    
    async def process_legal_transcript(
        self,
        transcript_text: str,
        document_type: ProceedingType,
        specialty: LegalSpecialty,
        case_number: str,
        court: str,
        parties: List[str]
    ) -> LegalDocument:
        """Process legal transcript with comprehensive analysis"""
        
        # Extract legal entities
        entities = self.entity_extractor.extract_legal_entities(transcript_text)
        
        # Extract citations
        citations = entities.get('citations', [])
        
        # Analyze legal arguments
        arguments = self.case_analyzer.analyze_legal_arguments(transcript_text, entities)
        
        # Check compliance
        compliance_results = self.compliance_checker.check_compliance(transcript_text, entities)
        
        # Assess risks
        risk_assessment = self._assess_legal_risks(transcript_text, entities, compliance_results)
        
        # Calculate time savings
        estimated_time_saved = self._calculate_time_savings(transcript_text, entities)
        
        # Create legal document
        legal_document = LegalDocument(
            document_id=str(uuid.uuid4()),
            document_type=document_type,
            specialty=specialty,
            case_number=case_number,
            court=court,
            parties=parties,
            created_at=datetime.now(),
            entities=entities,
            citations=citations,
            arguments=arguments,
            compliance_status=compliance_results["overall_status"],
            risk_assessment=risk_assessment,
            word_count=len(transcript_text.split()),
            estimated_time_saved=estimated_time_saved
        )
        
        return legal_document
    
    def _assess_legal_risks(self, text: str, entities: Dict[str, List[LegalEntity]], 
                          compliance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess legal risks in transcript"""
        risks = {
            "privilege_risks": [],
            "malpractice_risks": [],
            "procedural_risks": [],
            "ethical_risks": [],
            "overall_risk_level": "low"
        }
        
        # Assess privilege risks
        if compliance_results["violations"]:
            risks["privilege_risks"] = [v for v in compliance_results["violations"] 
                                     if "privilege" in v["type"]]
        
        # Assess malpractice risks
        if any(phrase in text.lower() for phrase in ["missed deadline", "failed to", "error"]):
            risks["malpractice_risks"].append("Potential malpractice indicators found")
        
        # Assess procedural risks
        procedural_entities = entities.get('procedures', [])
        if len(procedural_entities) > 10:  # High procedural complexity
            risks["procedural_risks"].append("High procedural complexity")
        
        # Determine overall risk level
        total_risks = (len(risks["privilege_risks"]) + 
                      len(risks["malpractice_risks"]) + 
                      len(risks["procedural_risks"]) + 
                      len(risks["ethical_risks"]))
        
        if total_risks >= 5:
            risks["overall_risk_level"] = "high"
        elif total_risks >= 2:
            risks["overall_risk_level"] = "medium"
        else:
            risks["overall_risk_level"] = "low"
        
        return risks
    
    def _calculate_time_savings(self, text: str, entities: Dict[str, List[LegalEntity]]) -> float:
        """Calculate estimated time savings from automated analysis"""
        base_time = len(text.split()) / 200 * 60  # Assume 200 words per minute reading
        
        # Add time for manual entity extraction
        entity_count = sum(len(entity_list) for entity_list in entities.values())
        manual_extraction_time = entity_count * 2  # 2 minutes per entity
        
        # Add time for legal research
        citations = entities.get('citations', [])
        research_time = len(citations) * 15  # 15 minutes per citation to research
        
        # Add time for compliance checking
        compliance_time = 30  # 30 minutes for manual compliance review
        
        total_manual_time = base_time + manual_extraction_time + research_time + compliance_time
        automated_time = base_time * 0.1  # 10% of reading time for review
        
        return max(0, total_manual_time - automated_time)
    
    def generate_legal_report(self, legal_document: LegalDocument) -> Dict[str, Any]:
        """Generate comprehensive legal analysis report"""
        report = {
            "document_summary": {
                "document_id": legal_document.document_id,
                "document_type": legal_document.document_type.value,
                "specialty": legal_document.specialty.value,
                "case_number": legal_document.case_number,
                "court": legal_document.court,
                "parties": legal_document.parties,
                "created_at": legal_document.created_at.isoformat(),
                "word_count": legal_document.word_count
            },
            
            "entity_analysis": {
                "total_entities": sum(len(entities) for entities in legal_document.entities.values()),
                "entity_breakdown": {
                    category: len(entities) 
                    for category, entities in legal_document.entities.items()
                },
                "key_entities": self._extract_key_entities(legal_document.entities)
            },
            
            "legal_analysis": {
                "citations_found": len(legal_document.citations),
                "arguments_identified": len(legal_document.arguments),
                "legal_precedents": [
                    {
                        "case_name": citation.case_name,
                        "citation": citation.citation_text,
                        "relevance": citation.relevance
                    }
                    for citation in legal_document.citations if citation.case_name
                ],
                "argument_strength": [
                    {
                        "attorney": arg.attorney,
                        "summary": arg.argument_summary[:100] + "...",
                        "strength": arg.strength_assessment
                    }
                    for arg in legal_document.arguments
                ]
            },
            
            "compliance_assessment": {
                "status": legal_document.compliance_status,
                "risk_level": legal_document.risk_assessment["overall_risk_level"],
                "key_risks": self._summarize_risks(legal_document.risk_assessment)
            },
            
            "efficiency_metrics": {
                "estimated_time_saved": legal_document.estimated_time_saved,
                "automation_percentage": 0.85,  # Estimated automation benefit
                "manual_review_time": legal_document.estimated_time_saved * 0.15
            }
        }
        
        return report
    
    def _extract_key_entities(self, entities: Dict[str, List[LegalEntity]]) -> List[Dict[str, Any]]:
        """Extract most important entities"""
        key_entities = []
        
        for category, entity_list in entities.items():
            # Sort by confidence and take top entities
            sorted_entities = sorted(entity_list, key=lambda x: x.confidence, reverse=True)
            for entity in sorted_entities[:3]:  # Top 3 per category
                key_entities.append({
                    "text": entity.text,
                    "type": entity.entity_type.value,
                    "category": category,
                    "confidence": entity.confidence,
                    "significance": entity.legal_significance
                })
        
        return key_entities[:10]  # Top 10 overall
    
    def _summarize_risks(self, risk_assessment: Dict[str, Any]) -> List[str]:
        """Summarize key risks"""
        risks = []
        
        for risk_type, risk_list in risk_assessment.items():
            if risk_type != "overall_risk_level" and risk_list:
                risks.extend(risk_list[:2])  # Top 2 risks per category
        
        return risks[:5]  # Top 5 overall risks

# Usage example
async def main():
    """Main function for testing legal transcription system"""
    print("⚖️ Legal Transcription and Analysis System")
    print("=" * 50)
    
    # Initialize system
    legal_system = LegalTranscriptionSystem()
    
    # Sample legal transcript
    sample_transcript = """
    Your Honor, this case involves a breach of contract claim. The plaintiff, 
    ABC Corporation, entered into a contract with defendant XYZ Company on 
    January 15, 2023. The contract clearly states that delivery must be made 
    within 30 days.
    
    The evidence shows that defendant failed to deliver the goods by the 
    February 15 deadline. Under Hadley v. Baxendale, the damages must be 
    reasonably foreseeable. Here, the plaintiff suffered $50,000 in 
    consequential damages.
    
    Objection, Your Honor. Hearsay.
    Overruled. Please continue, counsel.
    
    The defendant's breach was material and substantial. We seek damages 
    of $100,000 plus attorney fees under the contract's prevailing party clause.
    """
    
    print("\n⚖️ Processing Legal Transcript...")
    
    # Process legal transcript
    legal_document = await legal_system.process_legal_transcript(
        transcript_text=sample_transcript,
        document_type=ProceedingType.HEARING,
        specialty=LegalSpecialty.CONTRACT_LAW,
        case_number="CV-2023-001234",
        court="Superior Court of California",
        parties=["ABC Corporation", "XYZ Company"]
    )
    
    print(f"✅ Legal document processed: {legal_document.document_id}")
    print(f"   Document type: {legal_document.document_type.value}")
    print(f"   Specialty: {legal_document.specialty.value}")
    print(f"   Compliance status: {legal_document.compliance_status}")
    print(f"   Risk level: {legal_document.risk_assessment['overall_risk_level']}")
    print(f"   Time saved: {legal_document.estimated_time_saved:.1f} minutes")
    
    # Display entity analysis
    print(f"\n📊 Entity Analysis:")
    total_entities = sum(len(entities) for entities in legal_document.entities.values())
    print(f"   Total entities: {total_entities}")
    
    for category, entities in legal_document.entities.items():
        if entities:
            print(f"   • {category}: {len(entities)} entities")
    
    # Display legal analysis
    print(f"\n⚖️ Legal Analysis:")
    print(f"   Citations found: {len(legal_document.citations)}")
    print(f"   Arguments identified: {len(legal_document.arguments)}")
    
    if legal_document.citations:
        print("   Key citations:")
        for citation in legal_document.citations[:3]:
            print(f"     • {citation.citation_text}")
    
    # Generate comprehensive report
    print(f"\n📋 Generating Legal Report...")
    legal_report = legal_system.generate_legal_report(legal_document)
    
    print(f"   Entity breakdown: {legal_report['entity_analysis']['entity_breakdown']}")
    print(f"   Compliance status: {legal_report['compliance_assessment']['status']}")
    print(f"   Automation benefit: {legal_report['efficiency_metrics']['automation_percentage']:.0%}")
    
    print(f"\n✅ Legal transcription system demonstration complete!")

if __name__ == "__main__":
    asyncio.run(main())