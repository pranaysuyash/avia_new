#!/usr/bin/env python3
"""
Legal Schema Processor - Comprehensive Legal Document Analysis
"""

import re
import spacy
from spacy.matcher import PhraseMatcher, Matcher
from spacy.tokens import Doc, Span
from typing import Dict, List, Any, Optional
from legal_transcription_core import LegalEntity, LegalEntityType, LegalCitation

# Comprehensive Legal Schema Definition
COMPREHENSIVE_LEGAL_SCHEMA = {
    "metadata": {
        "case_number": "",
        "court_name": "",
        "jurisdiction": "",
        "case_type": "",  # "civil", "criminal", "family", "bankruptcy"
        "hearing_type": "",  # "deposition", "trial", "hearing", "mediation"
        "proceeding_date": "",
        "recording_quality": "",
        "court_reporter": "",
        "technology_used": "",
        "location": "",
        "duration": ""
    },
    
    "participants": [
        {
            "name": "",
            "role": "",  # "judge", "attorney", "plaintiff", "defendant", "witness"
            "representation": "",
            "bar_number": "",
            "firm_affiliation": "",
            "specialization": ""
        }
    ],
    
    "case_information": {
        "case_title": "",
        "docket_number": "",
        "filing_date": "",
        "case_status": "",
        "legal_issues": [""],
        "claims_and_defenses": [""],
        "relief_sought": "",
        "damages_claimed": ""
    },
    
    "legal_content": {
        "evidence_presented": [],
        "testimony": [],
        "legal_arguments": [],
        "objections": [],
        "motions": []
    },
    
    "judicial_actions": {
        "rulings_made": [""],
        "orders_issued": [""],
        "sanctions_imposed": [""],
        "procedural_decisions": [""]
    },
    
    "legal_analysis": {
        "applicable_laws": [""],
        "legal_precedents": [""],
        "constitutional_issues": [""],
        "procedural_compliance": ""
    },
    
    "outcomes": {
        "verdict": "",
        "judgment": "",
        "damages_awarded": "",
        "sentences_imposed": "",
        "future_proceedings": ""
    },
    
    "compliance": {
        "confidentiality_requirements": "",
        "privilege_claims": [""],
        "redaction_needed": [""],
        "public_record_status": ""
    }
}

class LegalEntityExtractor:
    """Extract legal entities from transcripts"""
    
    def __init__(self):
        self.setup_nlp_model()
        self.setup_legal_matchers()
        self.setup_citation_patterns()
    
    def setup_nlp_model(self):
        """Setup NLP model with legal components"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise Exception("spaCy model not found. Please install: python -m spacy download en_core_web_sm")
    
    def setup_legal_matchers(self):
        """Setup matchers for legal entities"""
        # Legal roles matcher
        self.roles_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        legal_roles = [
            "judge", "justice", "magistrate", "attorney", "lawyer", "counsel",
            "plaintiff", "defendant", "witness", "expert witness", "jury",
            "court reporter", "bailiff", "clerk"
        ]
        role_patterns = [self.nlp.make_doc(role) for role in legal_roles]
        self.roles_matcher.add("LEGAL_ROLES", role_patterns)
        
        # Legal procedures matcher
        self.procedures_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        procedures = [
            "deposition", "trial", "hearing", "mediation", "arbitration",
            "settlement conference", "motion hearing", "jury selection",
            "opening statement", "closing argument", "cross examination",
            "direct examination", "redirect", "objection", "sustained", "overruled"
        ]
        procedure_patterns = [self.nlp.make_doc(proc) for proc in procedures]
        self.procedures_matcher.add("LEGAL_PROCEDURES", procedure_patterns)
        
        # Legal documents matcher
        self.documents_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        documents = [
            "complaint", "answer", "motion", "brief", "memorandum", "order",
            "judgment", "verdict", "exhibit", "contract", "agreement",
            "statute", "regulation", "rule", "precedent", "case law"
        ]
        document_patterns = [self.nlp.make_doc(doc) for doc in documents]
        self.documents_matcher.add("LEGAL_DOCUMENTS", document_patterns)
        
        # Legal concepts matcher
        self.concepts_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        concepts = [
            "jurisdiction", "venue", "standing", "burden of proof", "standard of review",
            "due process", "equal protection", "probable cause", "reasonable doubt",
            "preponderance of evidence", "negligence", "breach of contract",
            "damages", "injunction", "remedy", "liability", "causation"
        ]
        concept_patterns = [self.nlp.make_doc(concept) for concept in concepts]
        self.concepts_matcher.add("LEGAL_CONCEPTS", concept_patterns)
    
    def setup_citation_patterns(self):
        """Setup patterns for legal citations"""
        self.citation_patterns = {
            # Case citations: Volume Reporter Page (Year)
            'case_citation': re.compile(
                r'(\d+)\s+([A-Z][a-z]*\.?\s*\d*[a-z]*\.?)\s+(\d+)(?:\s*\((\d{4})\))?',
                re.IGNORECASE
            ),
            # Statute citations: Title U.S.C. § Section
            'statute_citation': re.compile(
                r'(\d+)\s+U\.?S\.?C\.?\s*§\s*(\d+(?:\.\d+)*)',
                re.IGNORECASE
            ),
            # Federal Rules citations
            'rule_citation': re.compile(
                r'(?:Fed\.?\s*R\.?\s*(?:Civ\.?\s*P\.?|Crim\.?\s*P\.?|Evid\.?))\s*(\d+(?:\.\d+)*)',
                re.IGNORECASE
            ),
            # Constitutional citations
            'constitutional_citation': re.compile(
                r'U\.?S\.?\s*Const\.?\s*(?:art\.?\s*([IVX]+)|amend\.?\s*([IVX]+))',
                re.IGNORECASE
            )
        }
    
    def extract_legal_entities(self, transcript_text: str) -> Dict[str, List[LegalEntity]]:
        """Extract all legal entities from transcript"""
        doc = self.nlp(transcript_text)
        entities = {}
        
        # Extract legal roles
        entities['legal_roles'] = self._extract_legal_roles(doc)
        
        # Extract legal procedures
        entities['procedures'] = self._extract_procedures(doc)
        
        # Extract legal documents
        entities['documents'] = self._extract_documents(doc)
        
        # Extract legal concepts
        entities['concepts'] = self._extract_concepts(doc)
        
        # Extract citations
        entities['citations'] = self._extract_citations(transcript_text)
        
        # Extract objections
        entities['objections'] = self._extract_objections(doc, transcript_text)
        
        # Extract monetary amounts (damages, fees, etc.)
        entities['monetary'] = self._extract_monetary_amounts(doc, transcript_text)
        
        return entities
    
    def _extract_legal_roles(self, doc: Doc) -> List[LegalEntity]:
        """Extract legal roles and participants"""
        role_entities = []
        matches = self.roles_matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            entity = LegalEntity(
                text=span.text,
                entity_type=self._map_role_to_entity_type(span.text),
                confidence=0.9,
                start_pos=span.start_char,
                end_pos=span.end_char,
                normalized_form=span.text.lower(),
                context=self._get_context(doc, span),
                metadata={
                    'role_type': span.text.lower(),
                    'participant_category': self._categorize_participant(span.text)
                }
            )
            role_entities.append(entity)
        
        return role_entities
    
    def _extract_procedures(self, doc: Doc) -> List[LegalEntity]:
        """Extract legal procedures and proceedings"""
        procedure_entities = []
        matches = self.procedures_matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            entity = LegalEntity(
                text=span.text,
                entity_type=LegalEntityType.HEARING,
                confidence=0.85,
                start_pos=span.start_char,
                end_pos=span.end_char,
                normalized_form=span.text.lower(),
                context=self._get_context(doc, span),
                metadata={
                    'procedure_type': span.text.lower(),
                    'procedural_stage': self._determine_procedural_stage(span.text)
                }
            )
            procedure_entities.append(entity)
        
        return procedure_entities
    
    def _extract_documents(self, doc: Doc) -> List[LegalEntity]:
        """Extract legal documents and filings"""
        document_entities = []
        matches = self.documents_matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            entity_type = self._map_document_to_entity_type(span.text)
            
            entity = LegalEntity(
                text=span.text,
                entity_type=entity_type,
                confidence=0.8,
                start_pos=span.start_char,
                end_pos=span.end_char,
                normalized_form=span.text.lower(),
                context=self._get_context(doc, span),
                metadata={
                    'document_type': span.text.lower(),
                    'document_category': self._categorize_document(span.text)
                }
            )
            document_entities.append(entity)
        
        return document_entities
    
    def _extract_concepts(self, doc: Doc) -> List[LegalEntity]:
        """Extract legal concepts and standards"""
        concept_entities = []
        matches = self.concepts_matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            entity = LegalEntity(
                text=span.text,
                entity_type=LegalEntityType.LEGAL_STANDARD,
                confidence=0.75,
                start_pos=span.start_char,
                end_pos=span.end_char,
                normalized_form=span.text.lower(),
                context=self._get_context(doc, span),
                metadata={
                    'concept_type': span.text.lower(),
                    'legal_domain': self._determine_legal_domain(span.text)
                }
            )
            concept_entities.append(entity)
        
        return concept_entities
    
    def _extract_citations(self, text: str) -> List[LegalCitation]:
        """Extract legal citations from text"""
        citations = []
        
        for citation_type, pattern in self.citation_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                citation = self._parse_citation(match, citation_type)
                if citation:
                    citations.append(citation)
        
        return citations
    
    def _extract_objections(self, doc: Doc, text: str) -> List[LegalEntity]:
        """Extract objections and rulings"""
        objection_entities = []
        
        # Pattern for objections
        objection_pattern = re.compile(
            r'(objection|I object).*?(sustained|overruled|withdrawn)',
            re.IGNORECASE | re.DOTALL
        )
        
        matches = objection_pattern.finditer(text)
        for match in matches:
            entity = LegalEntity(
                text=match.group(0),
                entity_type=LegalEntityType.OBJECTION,
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end(),
                normalized_form=match.group(0).lower(),
                context=self._get_text_context(text, match.start(), match.end()),
                metadata={
                    'objection_type': self._classify_objection(match.group(0)),
                    'ruling': self._extract_ruling(match.group(0))
                }
            )
            objection_entities.append(entity)
        
        return objection_entities
    
    def _extract_monetary_amounts(self, doc: Doc, text: str) -> List[LegalEntity]:
        """Extract monetary amounts (damages, fees, costs)"""
        monetary_entities = []
        
        # Pattern for monetary amounts
        money_pattern = re.compile(
            r'\$[\d,]+(?:\.\d{2})?|\b\d+\s*(?:dollars?|million|billion)\b',
            re.IGNORECASE
        )
        
        matches = money_pattern.finditer(text)
        for match in matches:
            amount_type = self._classify_monetary_amount(text, match.start(), match.end())
            
            entity = LegalEntity(
                text=match.group(0),
                entity_type=self._map_amount_to_entity_type(amount_type),
                confidence=0.85,
                start_pos=match.start(),
                end_pos=match.end(),
                normalized_form=match.group(0).lower(),
                context=self._get_text_context(text, match.start(), match.end()),
                metadata={
                    'amount': self._normalize_amount(match.group(0)),
                    'amount_type': amount_type,
                    'currency': 'USD'
                }
            )
            monetary_entities.append(entity)
        
        return monetary_entities
    
    # Helper methods
    def _get_context(self, doc: Doc, span: Span, window: int = 5) -> str:
        """Get context around entity"""
        start = max(0, span.start - window)
        end = min(len(doc), span.end + window)
        return doc[start:end].text
    
    def _get_text_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get text context around position"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]
    
    def _map_role_to_entity_type(self, role_text: str) -> LegalEntityType:
        """Map role text to entity type"""
        role_lower = role_text.lower()
        if 'judge' in role_lower or 'justice' in role_lower:
            return LegalEntityType.JUDGE
        elif 'attorney' in role_lower or 'lawyer' in role_lower or 'counsel' in role_lower:
            return LegalEntityType.ATTORNEY
        elif 'witness' in role_lower:
            return LegalEntityType.WITNESS
        elif 'expert' in role_lower:
            return LegalEntityType.EXPERT
        elif 'jury' in role_lower:
            return LegalEntityType.JURY
        else:
            return LegalEntityType.PARTY
    
    def _map_document_to_entity_type(self, doc_text: str) -> LegalEntityType:
        """Map document text to entity type"""
        doc_lower = doc_text.lower()
        if any(word in doc_lower for word in ['statute', 'code', 'usc']):
            return LegalEntityType.STATUTE
        elif any(word in doc_lower for word in ['regulation', 'rule', 'cfr']):
            return LegalEntityType.REGULATION
        elif any(word in doc_lower for word in ['contract', 'agreement']):
            return LegalEntityType.CONTRACT
        elif 'exhibit' in doc_lower:
            return LegalEntityType.EXHIBIT
        elif 'motion' in doc_lower:
            return LegalEntityType.MOTION
        else:
            return LegalEntityType.CASE_LAW
    
    def _parse_citation(self, match, citation_type: str) -> Optional[LegalCitation]:
        """Parse citation match into structured citation"""
        if citation_type == 'case_citation':
            groups = match.groups()
            return LegalCitation(
                citation_text=match.group(0),
                volume=groups[0],
                reporter=groups[1],
                page=groups[2],
                year=groups[3] if len(groups) > 3 and groups[3] else None,
                citation_type="case"
            )
        elif citation_type == 'statute_citation':
            groups = match.groups()
            return LegalCitation(
                citation_text=match.group(0),
                volume=groups[0],
                page=groups[1],
                citation_type="statute"
            )
        # Add more citation types as needed
        
        return None
    
    def _categorize_participant(self, role: str) -> str:
        """Categorize participant by role"""
        role_lower = role.lower()
        if any(word in role_lower for word in ['judge', 'justice', 'magistrate']):
            return 'judicial'
        elif any(word in role_lower for word in ['attorney', 'lawyer', 'counsel']):
            return 'legal_counsel'
        elif any(word in role_lower for word in ['plaintiff', 'defendant']):
            return 'party'
        elif 'witness' in role_lower:
            return 'witness'
        else:
            return 'other'
    
    def _determine_procedural_stage(self, procedure: str) -> str:
        """Determine procedural stage"""
        procedure_lower = procedure.lower()
        if any(word in procedure_lower for word in ['opening', 'complaint', 'answer']):
            return 'pleading'
        elif any(word in procedure_lower for word in ['discovery', 'deposition', 'interrogatory']):
            return 'discovery'
        elif any(word in procedure_lower for word in ['motion', 'summary judgment']):
            return 'motion_practice'
        elif any(word in procedure_lower for word in ['trial', 'hearing', 'testimony']):
            return 'trial'
        else:
            return 'other'
    
    def _categorize_document(self, document: str) -> str:
        """Categorize legal document"""
        doc_lower = document.lower()
        if any(word in doc_lower for word in ['pleading', 'complaint', 'answer']):
            return 'pleading'
        elif any(word in doc_lower for word in ['motion', 'brief', 'memorandum']):
            return 'motion'
        elif any(word in doc_lower for word in ['order', 'judgment', 'ruling']):
            return 'court_order'
        elif any(word in doc_lower for word in ['contract', 'agreement']):
            return 'contract'
        elif 'exhibit' in doc_lower:
            return 'evidence'
        else:
            return 'other'
    
    def _determine_legal_domain(self, concept: str) -> str:
        """Determine legal domain for concept"""
        concept_lower = concept.lower()
        if any(word in concept_lower for word in ['constitutional', 'due process', 'equal protection']):
            return 'constitutional'
        elif any(word in concept_lower for word in ['contract', 'breach', 'agreement']):
            return 'contract'
        elif any(word in concept_lower for word in ['negligence', 'tort', 'liability']):
            return 'tort'
        elif any(word in concept_lower for word in ['criminal', 'probable cause', 'reasonable doubt']):
            return 'criminal'
        else:
            return 'general'
    
    def _classify_objection(self, objection_text: str) -> str:
        """Classify type of objection"""
        text_lower = objection_text.lower()
        if 'hearsay' in text_lower:
            return 'hearsay'
        elif 'relevance' in text_lower or 'relevant' in text_lower:
            return 'relevance'
        elif 'foundation' in text_lower:
            return 'foundation'
        elif 'leading' in text_lower:
            return 'leading'
        elif 'speculation' in text_lower:
            return 'speculation'
        else:
            return 'other'
    
    def _extract_ruling(self, objection_text: str) -> str:
        """Extract ruling on objection"""
        text_lower = objection_text.lower()
        if 'sustained' in text_lower:
            return 'sustained'
        elif 'overruled' in text_lower:
            return 'overruled'
        elif 'withdrawn' in text_lower:
            return 'withdrawn'
        else:
            return 'unknown'
    
    def _classify_monetary_amount(self, text: str, start: int, end: int) -> str:
        """Classify type of monetary amount"""
        context = text[max(0, start-50):min(len(text), end+50)].lower()
        
        if any(word in context for word in ['damages', 'award', 'compensation']):
            return 'damages'
        elif any(word in context for word in ['fees', 'attorney', 'legal']):
            return 'fees'
        elif any(word in context for word in ['costs', 'court costs']):
            return 'costs'
        elif any(word in context for word in ['settlement', 'settle']):
            return 'settlement'
        elif any(word in context for word in ['fine', 'penalty']):
            return 'penalty'
        else:
            return 'other'
    
    def _map_amount_to_entity_type(self, amount_type: str) -> LegalEntityType:
        """Map amount type to entity type"""
        if amount_type == 'damages':
            return LegalEntityType.DAMAGES
        elif amount_type == 'fees':
            return LegalEntityType.FEES
        elif amount_type == 'costs':
            return LegalEntityType.COSTS
        elif amount_type == 'settlement':
            return LegalEntityType.SETTLEMENT
        else:
            return LegalEntityType.DAMAGES  # Default
    
    def _normalize_amount(self, amount_text: str) -> str:
        """Normalize monetary amount"""
        # Remove $ and commas, convert to float
        cleaned = re.sub(r'[$,]', '', amount_text)
        
        # Handle million/billion
        if 'million' in amount_text.lower():
            try:
                num = float(re.search(r'[\d.]+', cleaned).group())
                return str(int(num * 1000000))
            except:
                return cleaned
        elif 'billion' in amount_text.lower():
            try:
                num = float(re.search(r'[\d.]+', cleaned).group())
                return str(int(num * 1000000000))
            except:
                return cleaned
        
        return cleaned