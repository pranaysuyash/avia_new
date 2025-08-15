#!/usr/bin/env python3
"""
Legal Transcription Core System - Task 142
Core components for legal transcription and analysis
"""

import os
import re
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class LegalEntityType(Enum):
    """Legal entity types for comprehensive analysis"""
    # Parties and People
    PARTY = "party"
    ATTORNEY = "attorney"
    JUDGE = "judge"
    WITNESS = "witness"
    EXPERT = "expert"
    JURY = "jury"
    
    # Legal Documents and References
    CASE_LAW = "case_law"
    STATUTE = "statute"
    REGULATION = "regulation"
    CONTRACT = "contract"
    EXHIBIT = "exhibit"
    MOTION = "motion"
    
    # Legal Concepts
    LEGAL_STANDARD = "legal_standard"
    CAUSE_OF_ACTION = "cause_of_action"
    DEFENSE = "defense"
    REMEDY = "remedy"
    JURISDICTION = "jurisdiction"
    VENUE = "venue"
    
    # Procedural Elements
    OBJECTION = "objection"
    RULING = "ruling"
    ORDER = "order"
    DEADLINE = "deadline"
    HEARING = "hearing"
    
    # Financial and Damages
    DAMAGES = "damages"
    COSTS = "costs"
    FEES = "fees"
    SETTLEMENT = "settlement"
    
    # Evidence and Facts
    EVIDENCE = "evidence"
    FACT = "fact"
    TESTIMONY = "testimony"
    OPINION = "opinion"
    
    # Compliance and Ethics
    PRIVILEGE = "privilege"
    CONFIDENTIALITY = "confidentiality"
    ETHICS = "ethics"
    CONFLICT = "conflict"

class LegalSpecialty(Enum):
    """Legal practice areas"""
    CIVIL_LITIGATION = "civil_litigation"
    CRIMINAL_LAW = "criminal_law"
    CORPORATE_LAW = "corporate_law"
    CONTRACT_LAW = "contract_law"
    TORT_LAW = "tort_law"
    FAMILY_LAW = "family_law"
    EMPLOYMENT_LAW = "employment_law"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    REAL_ESTATE = "real_estate"
    BANKRUPTCY = "bankruptcy"
    TAX_LAW = "tax_law"
    IMMIGRATION = "immigration"
    ENVIRONMENTAL_LAW = "environmental_law"
    SECURITIES_LAW = "securities_law"
    ADMINISTRATIVE_LAW = "administrative_law"
    CONSTITUTIONAL_LAW = "constitutional_law"

class ProceedingType(Enum):
    """Types of legal proceedings"""
    DEPOSITION = "deposition"
    TRIAL = "trial"
    HEARING = "hearing"
    MEDIATION = "mediation"
    ARBITRATION = "arbitration"
    SETTLEMENT_CONFERENCE = "settlement_conference"
    CASE_MANAGEMENT = "case_management"
    MOTION_HEARING = "motion_hearing"
    JURY_SELECTION = "jury_selection"
    CLOSING_ARGUMENTS = "closing_arguments"

@dataclass
class LegalEntity:
    """Legal entity with comprehensive metadata"""
    text: str
    entity_type: LegalEntityType
    confidence: float
    start_pos: int
    end_pos: int
    normalized_form: str
    legal_citation: Optional[str] = None
    context: Optional[str] = None
    relevance: Optional[str] = None
    timestamp: Optional[str] = None
    speaker: Optional[str] = None
    legal_significance: Optional[str] = None
    follow_up_needed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LegalCitation:
    """Structured legal citation"""
    citation_text: str
    case_name: Optional[str] = None
    court: Optional[str] = None
    year: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    jurisdiction: Optional[str] = None
    citation_type: str = "case"  # "case", "statute", "regulation", "secondary"
    relevance: Optional[str] = None
    holding: Optional[str] = None

@dataclass
class LegalArgument:
    """Structured legal argument"""
    argument_id: str
    attorney: str
    argument_summary: str
    legal_basis: List[str]
    factual_basis: List[str]
    precedents_cited: List[LegalCitation]
    counter_arguments: List[str]
    strength_assessment: Optional[str] = None