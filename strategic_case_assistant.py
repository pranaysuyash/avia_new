#!/usr/bin/env python3
"""
Strategic Case Assistant - Intent-First Transformation
Phase 2 System #3: Legal Transcription → Strategic Case Analysis

TRANSFORMATION:
Before: "Legal entities extracted - 12 case citations identified"
After: "Based on case precedents, this argument has 78% success probability - 
       recommend emphasizing constitutional grounds"

This system transforms legal transcription from technical entity extraction into
strategic case analysis that predicts litigation outcomes and provides actionable
legal strategy recommendations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Enums for case analysis
class CaseStrategyType(Enum):
    """Types of legal case strategies"""
    AGGRESSIVE_LITIGATION = "aggressive_litigation"
    SETTLEMENT_FOCUSED = "settlement_focused"
    DEFENSIVE_POSTURE = "defensive_posture"
    PRECEDENT_BUILDING = "precedent_building"
    PROCEDURAL_CHALLENGE = "procedural_challenge"
    CONSTITUTIONAL_ARGUMENT = "constitutional_argument"
    STATUTORY_INTERPRETATION = "statutory_interpretation"
    FACTUAL_DEVELOPMENT = "factual_development"

class ArgumentStrength(Enum):
    """Strength assessment for legal arguments"""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    UNLIKELY = "unlikely"

class LegalUrgency(Enum):
    """Urgency levels for legal actions"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CasePhase(Enum):
    """Phases of litigation"""
    PLEADING = "pleading"
    DISCOVERY = "discovery"
    MOTION_PRACTICE = "motion_practice"
    TRIAL_PREP = "trial_prep"
    TRIAL = "trial"
    APPEAL = "appeal"
    POST_JUDGMENT = "post_judgment"

class LegalJurisdiction(Enum):
    """Legal jurisdictions"""
    FEDERAL = "federal"
    STATE = "state"
    APPELLATE = "appellate"
    SUPREME_COURT = "supreme_court"

@dataclass
class StrategicArgument:
    """Strategic legal argument with success prediction"""
    argument_type: str
    strength: ArgumentStrength
    success_probability: str
    supporting_precedents: List[str]
    counter_arguments: List[str]
    emphasis_points: List[str]
    estimated_impact: str

@dataclass
class LegalPrecedent:
    """Legal precedent with relevance analysis"""
    case_name: str
    citation: str
    relevance: str
    key_holding: str
    supporting_factors: List[str]
    distinguishing_factors: List[str]
    jurisdiction: str
    year: str

@dataclass
class LitigationRisk:
    """Litigation risk assessment"""
    risk_type: str
    probability: str
    impact: str
    mitigation_strategies: List[str]
    urgency: LegalUrgency

class StrategicCaseAssistant:
    """
    Strategic Case Assistant - Transforms legal transcription into strategic case analysis
    
    Intent-First Transformation:
    - FROM: Technical entity extraction and document coding
    - TO: Strategic litigation support with outcome prediction
    """
    
    def __init__(self):
        self.precedent_database = self._initialize_precedent_database()
        self.strategy_patterns = self._initialize_strategy_patterns()
        self.risk_factors = self._initialize_risk_factors()
    
    def _initialize_precedent_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive precedent database"""
        return {
            "constitutional_law": {
                "Brown v. Board of Education": {
                    "citation": "347 U.S. 483 (1954)",
                    "holding": "Separate educational facilities are inherently unequal",
                    "significance": "landmark",
                    "keywords": ["equal protection", "education", "segregation"],
                    "success_factors": ["clear constitutional violation", "compelling evidence", "social impact"]
                },
                "Miranda v. Arizona": {
                    "citation": "384 U.S. 436 (1966)",
                    "holding": "Suspects must be informed of rights before interrogation",
                    "significance": "landmark",
                    "keywords": ["miranda rights", "self-incrimination", "due process"],
                    "success_factors": ["procedural safeguards", "constitutional rights", "law enforcement"]
                }
            },
            "contract_law": {
                "Hadley v. Baxendale": {
                    "citation": "9 Ex. 341 (1854)",
                    "holding": "Damages must be reasonably foreseeable at contract formation",
                    "significance": "foundational",
                    "keywords": ["consequential damages", "foreseeability", "breach"],
                    "success_factors": ["clear contract terms", "foreseeable damages", "causation"]
                }
            },
            "tort_law": {
                "Palsgraf v. Long Island Railroad": {
                    "citation": "248 N.Y. 339 (1928)",
                    "holding": "Duty of care limited to foreseeable plaintiffs",
                    "significance": "landmark",
                    "keywords": ["negligence", "proximate cause", "duty", "foreseeability"],
                    "success_factors": ["foreseeable harm", "duty relationship", "causation"]
                }
            }
        }
    
    def _initialize_strategy_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize case strategy patterns"""
        return {
            "strong_precedent": {
                "strategy": CaseStrategyType.PRECEDENT_BUILDING,
                "success_rate": 0.75,
                "indicators": ["landmark case", "controlling precedent", "circuit split"]
            },
            "constitutional_claim": {
                "strategy": CaseStrategyType.CONSTITUTIONAL_ARGUMENT,
                "success_rate": 0.65,
                "indicators": ["fundamental rights", "strict scrutiny", "constitutional violation"]
            },
            "procedural_defense": {
                "strategy": CaseStrategyType.PROCEDURAL_CHALLENGE,
                "success_rate": 0.55,
                "indicators": ["statute of limitations", "jurisdiction", "standing"]
            },
            "settlement_indicators": {
                "strategy": CaseStrategyType.SETTLEMENT_FOCUSED,
                "success_rate": 0.70,
                "indicators": ["cost concerns", "business relationship", "uncertain outcome"]
            }
        }
    
    def _initialize_risk_factors(self) -> Dict[str, Dict[str, Any]]:
        """Initialize litigation risk factors"""
        return {
            "adverse_precedent": {
                "impact": "high",
                "mitigation": ["distinguish facts", "argue policy change", "seek en banc review"]
            },
            "weak_evidence": {
                "impact": "high",
                "mitigation": ["additional discovery", "expert testimony", "circumstantial evidence"]
            },
            "procedural_defects": {
                "impact": "medium",
                "mitigation": ["motion to amend", "cure defects", "procedural workarounds"]
            },
            "cost_concerns": {
                "impact": "medium",
                "mitigation": ["fee shifting provisions", "cost-benefit analysis", "settlement"]
            }
        }
    
    async def get_strategic_case_analysis(
        self,
        legal_content: str,
        case_type: str,
        jurisdiction: str,
        case_phase: str,
        case_value: Optional[int] = None,
        client_goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive strategic case analysis
        
        TRANSFORMATION EXAMPLE:
        Before: "12 legal entities extracted, 5 citations found"
        After: "Constitutional argument has 78% success probability - recommend 
                emphasizing due process grounds with supporting precedent from 
                Miranda v. Arizona"
        """
        
        # Analyze case strategy
        primary_strategy = self._determine_primary_strategy(legal_content, case_type)
        
        # Calculate win probability
        win_probability = self._calculate_win_probability(
            legal_content, case_type, jurisdiction, case_phase
        )
        
        # Identify strategic arguments
        strategic_arguments = self._identify_strategic_arguments(
            legal_content, case_type, jurisdiction
        )
        
        # Find relevant precedents
        relevant_precedents = self._find_relevant_precedents(
            legal_content, case_type, jurisdiction
        )
        
        # Assess litigation risks
        risk_assessment = self._assess_litigation_risks(
            legal_content, case_type, case_phase
        )
        
        # Generate settlement analysis
        settlement_analysis = self._analyze_settlement_potential(
            legal_content, case_value, win_probability
        )
        
        # Develop procedural recommendations
        procedural_recommendations = self._generate_procedural_recommendations(
            legal_content, case_phase, jurisdiction
        )
        
        # Create evidence strategy
        evidence_strategy = self._develop_evidence_strategy(
            legal_content, case_type, case_phase
        )
        
        # Timeline analysis
        timeline_analysis = self._analyze_case_timeline(
            case_phase, jurisdiction
        )
        
        # Cost-benefit analysis
        cost_benefit = self._perform_cost_benefit_analysis(
            case_value, win_probability, case_phase
        )
        
        # Generate key recommendations
        key_recommendations = self._generate_key_recommendations(
            strategic_arguments, risk_assessment, settlement_analysis, case_phase
        )
        
        # Determine overall case strength
        overall_strength = self._assess_overall_strength(
            win_probability, strategic_arguments, risk_assessment
        )
        
        return {
            "case_summary": self._generate_case_summary(legal_content, case_type),
            "primary_strategy": primary_strategy.value,
            "win_probability": win_probability,
            "overall_strength": overall_strength,
            "key_recommendations": key_recommendations,
            "strategic_arguments": strategic_arguments,
            "relevant_precedents": relevant_precedents,
            "risk_assessment": risk_assessment,
            "settlement_analysis": settlement_analysis,
            "procedural_recommendations": procedural_recommendations,
            "evidence_strategy": evidence_strategy,
            "timeline_analysis": timeline_analysis,
            "cost_benefit": cost_benefit
        }
    
    def _determine_primary_strategy(self, legal_content: str, case_type: str) -> CaseStrategyType:
        """Determine primary litigation strategy"""
        content_lower = legal_content.lower()
        
        # Check for constitutional claims
        if any(term in content_lower for term in ["constitutional", "due process", "equal protection", "first amendment"]):
            return CaseStrategyType.CONSTITUTIONAL_ARGUMENT
        
        # Check for settlement indicators
        if any(term in content_lower for term in ["settlement", "negotiate", "mediation", "cost"]):
            return CaseStrategyType.SETTLEMENT_FOCUSED
        
        # Check for procedural challenges
        if any(term in content_lower for term in ["statute of limitations", "jurisdiction", "standing", "motion to dismiss"]):
            return CaseStrategyType.PROCEDURAL_CHALLENGE
        
        # Check for precedent-based strategy
        if any(term in content_lower for term in ["precedent", "landmark", "circuit", "supreme court"]):
            return CaseStrategyType.PRECEDENT_BUILDING
        
        # Default based on case type
        if case_type in ["commercial", "contract"]:
            return CaseStrategyType.SETTLEMENT_FOCUSED
        elif case_type in ["civil_rights", "constitutional"]:
            return CaseStrategyType.CONSTITUTIONAL_ARGUMENT
        else:
            return CaseStrategyType.FACTUAL_DEVELOPMENT
    
    def _calculate_win_probability(
        self, legal_content: str, case_type: str, jurisdiction: str, case_phase: str
    ) -> str:
        """Calculate win probability based on case factors"""
        base_probability = 0.50  # Start at 50%
        
        content_lower = legal_content.lower()
        
        # Positive factors
        if "strong evidence" in content_lower or "documentary evidence" in content_lower:
            base_probability += 0.15
        if "precedent" in content_lower and "support" in content_lower:
            base_probability += 0.12
        if "expert testimony" in content_lower:
            base_probability += 0.08
        if "clear violation" in content_lower or "material breach" in content_lower:
            base_probability += 0.10
        
        # Negative factors
        if "adverse precedent" in content_lower or "unfavorable" in content_lower:
            base_probability -= 0.15
        if "weak evidence" in content_lower or "credibility issues" in content_lower:
            base_probability -= 0.12
        if "procedural defects" in content_lower or "statute of limitations" in content_lower:
            base_probability -= 0.10
        if "novel theory" in content_lower or "untested" in content_lower:
            base_probability -= 0.08
        
        # Cap between 10% and 90%
        base_probability = max(0.10, min(0.90, base_probability))
        
        return f"{base_probability:.0%}"
    
    def _identify_strategic_arguments(
        self, legal_content: str, case_type: str, jurisdiction: str
    ) -> List[Dict[str, Any]]:
        """Identify strategic legal arguments with success prediction"""
        arguments = []
        content_lower = legal_content.lower()
        
        # Constitutional arguments
        if any(term in content_lower for term in ["constitutional", "due process", "equal protection"]):
            arguments.append({
                "type": "constitutional_claim",
                "strength": "strong" if "clear violation" in content_lower else "moderate",
                "success_probability": "75%" if "precedent support" in content_lower else "60%",
                "supporting_precedents": ["Miranda v. Arizona", "Brown v. Board of Education"],
                "counter_arguments": ["Qualified immunity", "Rational basis review"],
                "emphasis": ["Fundamental rights violation", "Strict scrutiny standard"],
                "estimated_impact": "high"
            })
        
        # Contract arguments
        if any(term in content_lower for term in ["breach", "contract", "agreement"]):
            arguments.append({
                "type": "breach_of_contract",
                "strength": "strong" if "clear terms" in content_lower else "moderate",
                "success_probability": "70%" if "documentary evidence" in content_lower else "55%",
                "supporting_precedents": ["Hadley v. Baxendale"],
                "counter_arguments": ["Impossibility", "Failure to mitigate"],
                "emphasis": ["Clear contractual language", "Material breach"],
                "estimated_impact": "medium"
            })
        
        # Negligence arguments
        if any(term in content_lower for term in ["negligence", "duty", "breach of duty"]):
            arguments.append({
                "type": "negligence_claim",
                "strength": "moderate",
                "success_probability": "65%",
                "supporting_precedents": ["Palsgraf v. Long Island Railroad"],
                "counter_arguments": ["Contributory negligence", "Assumption of risk"],
                "emphasis": ["Duty of care", "Proximate cause"],
                "estimated_impact": "medium"
            })
        
        # Statutory claims
        if any(term in content_lower for term in ["statute", "statutory", "violation"]):
            arguments.append({
                "type": "statutory_violation",
                "strength": "strong" if "clear violation" in content_lower else "moderate",
                "success_probability": "72%",
                "supporting_precedents": [],
                "counter_arguments": ["Statutory interpretation", "Legislative intent"],
                "emphasis": ["Plain language", "Legislative history"],
                "estimated_impact": "high"
            })
        
        # If no specific arguments identified, add general argument
        if not arguments:
            arguments.append({
                "type": "general_claim",
                "strength": "moderate",
                "success_probability": "50%",
                "supporting_precedents": [],
                "counter_arguments": [],
                "emphasis": ["Factual development needed"],
                "estimated_impact": "medium"
            })
        
        return arguments
    
    def _find_relevant_precedents(
        self, legal_content: str, case_type: str, jurisdiction: str
    ) -> List[Dict[str, Any]]:
        """Find relevant legal precedents with relevance scoring"""
        precedents = []
        content_lower = legal_content.lower()
        
        # Search precedent database
        for category, cases in self.precedent_database.items():
            for case_name, case_info in cases.items():
                # Check keyword relevance
                relevance_score = sum(
                    1 for keyword in case_info["keywords"]
                    if keyword in content_lower
                )
                
                if relevance_score > 0:
                    precedents.append({
                        "case_name": case_name,
                        "citation": case_info["citation"],
                        "relevance": "high" if relevance_score >= 2 else "moderate",
                        "key_holding": case_info["holding"],
                        "supporting_factors": case_info.get("success_factors", []),
                        "distinguishing_factors": [],
                        "jurisdiction": "federal" if "U.S." in case_info["citation"] else "state",
                        "year": case_info["citation"].split("(")[-1].strip(")")
                    })
        
        # Sort by relevance
        precedents.sort(key=lambda x: 1 if x["relevance"] == "high" else 2)
        
        return precedents[:5]  # Return top 5 most relevant
    
    def _assess_litigation_risks(
        self, legal_content: str, case_type: str, case_phase: str
    ) -> List[Dict[str, Any]]:
        """Assess litigation risks with mitigation strategies"""
        risks = []
        content_lower = legal_content.lower()
        
        # Check for adverse precedent risk
        if "adverse precedent" in content_lower or "unfavorable" in content_lower:
            risks.append({
                "risk_type": "Adverse Precedent",
                "probability": "high",
                "impact": "significant",
                "mitigation": [
                    "Distinguish factual circumstances",
                    "Argue for policy change",
                    "Seek en banc review if appellate"
                ],
                "urgency": LegalUrgency.HIGH.value
            })
        
        # Check for evidentiary risks
        if "weak evidence" in content_lower or "credibility" in content_lower:
            risks.append({
                "risk_type": "Evidentiary Challenges",
                "probability": "medium",
                "impact": "moderate",
                "mitigation": [
                    "Conduct additional discovery",
                    "Retain expert witnesses",
                    "Develop circumstantial evidence"
                ],
                "urgency": LegalUrgency.MEDIUM.value
            })
        
        # Check for procedural risks
        if any(term in content_lower for term in ["deadline", "statute of limitations", "procedural"]):
            risks.append({
                "risk_type": "Procedural Compliance",
                "probability": "medium",
                "impact": "high",
                "mitigation": [
                    "Calendar all deadlines",
                    "File protective motions",
                    "Seek extensions if needed"
                ],
                "urgency": LegalUrgency.HIGH.value
            })
        
        # Check for cost risks
        if "complex" in content_lower or "extensive discovery" in content_lower:
            risks.append({
                "risk_type": "Litigation Costs",
                "probability": "high",
                "impact": "moderate",
                "mitigation": [
                    "Evaluate settlement options",
                    "Consider fee-shifting provisions",
                    "Implement cost controls"
                ],
                "urgency": LegalUrgency.MEDIUM.value
            })
        
        return risks
    
    def _analyze_settlement_potential(
        self, legal_content: str, case_value: Optional[int], win_probability: str
    ) -> Dict[str, Any]:
        """Analyze settlement potential and recommend strategy"""
        content_lower = legal_content.lower()
        
        # Extract probability percentage
        prob_value = float(win_probability.strip('%')) / 100
        
        # Calculate settlement probability
        settlement_indicators = sum([
            "settlement" in content_lower,
            "negotiate" in content_lower,
            "mediation" in content_lower,
            "cost" in content_lower and "high" in content_lower,
            prob_value < 0.60  # Lower win probability increases settlement likelihood
        ])
        
        settlement_probability = min(0.90, 0.30 + (settlement_indicators * 0.15))
        
        analysis = {
            "settlement_probability": settlement_probability,
            "recommendation": "Pursue settlement" if settlement_probability > 0.60 else "Continue litigation"
        }
        
        # Add settlement range if case value provided
        if case_value:
            expected_value = case_value * prob_value
            analysis["estimated_range"] = {
                "low": int(expected_value * 0.60),
                "high": int(expected_value * 0.90),
                "expected": int(expected_value * 0.75)
            }
        
        return analysis
    
    def _generate_procedural_recommendations(
        self, legal_content: str, case_phase: str, jurisdiction: str
    ) -> List[str]:
        """Generate procedural strategy recommendations"""
        recommendations = []
        content_lower = legal_content.lower()
        
        if case_phase == "discovery":
            recommendations.extend([
                "Conduct comprehensive document discovery",
                "Schedule key witness depositions",
                "Retain necessary expert witnesses"
            ])
            
            if "complex" in content_lower:
                recommendations.append("Consider phased discovery approach")
        
        elif case_phase == "motion_practice":
            recommendations.extend([
                "File dispositive motions if appropriate",
                "Respond to opposing motions strategically",
                "Preserve issues for appeal"
            ])
        
        elif case_phase == "trial_prep":
            recommendations.extend([
                "Prepare comprehensive trial brief",
                "Develop witness examination outlines",
                "Create demonstrative exhibits"
            ])
        
        elif case_phase == "appeal":
            recommendations.extend([
                "Identify preserved appellate issues",
                "Research circuit precedent thoroughly",
                "Prepare for oral argument"
            ])
        
        return recommendations
    
    def _develop_evidence_strategy(
        self, legal_content: str, case_type: str, case_phase: str
    ) -> List[str]:
        """Develop evidence gathering and presentation strategy"""
        strategy = []
        content_lower = legal_content.lower()
        
        # Documentary evidence
        if "document" in content_lower or "contract" in content_lower:
            strategy.append("Prioritize documentary evidence collection and authentication")
        
        # Expert testimony
        if "expert" in content_lower or "technical" in content_lower:
            strategy.append("Retain qualified expert witnesses for technical issues")
        
        # Witness testimony
        if "witness" in content_lower or "testimony" in content_lower:
            strategy.append("Prepare key witnesses thoroughly for deposition and trial")
        
        # Physical evidence
        if "physical" in content_lower or "demonstrative" in content_lower:
            strategy.append("Develop demonstrative exhibits for jury presentation")
        
        # Default strategies
        if not strategy:
            strategy.extend([
                "Gather all available documentary evidence",
                "Identify and interview key witnesses",
                "Consider need for expert testimony"
            ])
        
        return strategy
    
    def _analyze_case_timeline(self, case_phase: str, jurisdiction: str) -> Dict[str, Any]:
        """Analyze case timeline and key milestones"""
        timeline = {
            "current_phase": case_phase,
            "estimated_duration": "Unknown"
        }
        
        if case_phase == "discovery":
            timeline["estimated_duration"] = "6-12 months"
            timeline["key_milestones"] = [
                "Complete document production",
                "Conduct depositions",
                "Retain experts"
            ]
        elif case_phase == "motion_practice":
            timeline["estimated_duration"] = "3-6 months"
            timeline["key_milestones"] = [
                "File dispositive motions",
                "Briefing schedule",
                "Oral argument"
            ]
        elif case_phase == "trial_prep":
            timeline["estimated_duration"] = "2-4 months"
            timeline["key_milestones"] = [
                "Finalize witness list",
                "Prepare exhibits",
                "Conduct mock trial"
            ]
        
        return timeline
    
    def _perform_cost_benefit_analysis(
        self, case_value: Optional[int], win_probability: str, case_phase: str
    ) -> Dict[str, Any]:
        """Perform litigation cost-benefit analysis"""
        analysis = {
            "recommendation": "Continue litigation"
        }
        
        if case_value:
            prob_value = float(win_probability.strip('%')) / 100
            expected_value = case_value * prob_value
            
            # Estimate litigation costs based on phase
            cost_estimates = {
                "discovery": case_value * 0.15,
                "motion_practice": case_value * 0.10,
                "trial_prep": case_value * 0.20,
                "trial": case_value * 0.25
            }
            
            estimated_cost = cost_estimates.get(case_phase, case_value * 0.15)
            
            analysis["expected_value"] = int(expected_value)
            analysis["estimated_cost"] = int(estimated_cost)
            analysis["net_benefit"] = int(expected_value - estimated_cost)
            
            if expected_value < estimated_cost:
                analysis["recommendation"] = "Consider settlement - costs exceed expected value"
        
        return analysis
    
    def _generate_key_recommendations(
        self,
        strategic_arguments: List[Dict[str, Any]],
        risk_assessment: List[Dict[str, Any]],
        settlement_analysis: Dict[str, Any],
        case_phase: str
    ) -> List[str]:
        """Generate key strategic recommendations"""
        recommendations = []
        
        # Argument-based recommendations
        if strategic_arguments:
            strongest_arg = max(strategic_arguments, key=lambda x: x.get("success_probability", "0%"))
            recommendations.append(
                f"Emphasize {strongest_arg['type'].replace('_', ' ')} argument - "
                f"{strongest_arg['success_probability']} success probability"
            )
        
        # Risk-based recommendations
        if risk_assessment:
            high_risks = [r for r in risk_assessment if r.get("probability") == "high"]
            if high_risks:
                recommendations.append(
                    f"Address {high_risks[0]['risk_type']} risk immediately - "
                    f"implement mitigation strategies"
                )
        
        # Settlement recommendations
        if settlement_analysis.get("settlement_probability", 0) > 0.60:
            recommendations.append(
                "Strong settlement potential - initiate negotiations with realistic expectations"
            )
        
        # Phase-specific recommendations
        if case_phase == "discovery":
            recommendations.append("Focus on comprehensive fact development during discovery")
        elif case_phase == "trial_prep":
            recommendations.append("Prioritize trial preparation and witness readiness")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _assess_overall_strength(
        self,
        win_probability: str,
        strategic_arguments: List[Dict[str, Any]],
        risk_assessment: List[Dict[str, Any]]
    ) -> str:
        """Assess overall case strength"""
        prob_value = float(win_probability.strip('%')) / 100
        
        # Count strong arguments
        strong_args = sum(1 for arg in strategic_arguments if arg.get("strength") == "strong")
        
        # Count high risks
        high_risks = sum(1 for risk in risk_assessment if risk.get("probability") == "high")
        
        # Calculate overall strength
        if prob_value >= 0.70 and strong_args >= 2 and high_risks == 0:
            return "strong"
        elif prob_value >= 0.55 and strong_args >= 1:
            return "moderate"
        elif prob_value >= 0.40:
            return "weak"
        else:
            return "unlikely"
    
    def _generate_case_summary(self, legal_content: str, case_type: str) -> str:
        """Generate concise case summary"""
        content_lower = legal_content.lower()
        
        # Extract key elements
        claims = []
        if "breach" in content_lower:
            claims.append("breach of contract")
        if "negligence" in content_lower:
            claims.append("negligence")
        if "constitutional" in content_lower:
            claims.append("constitutional violation")
        if "fraud" in content_lower:
            claims.append("fraud")
        
        if claims:
            return f"{case_type.title()} case involving {', '.join(claims)}"
        else:
            return f"{case_type.title()} litigation matter"

# Usage example
async def main():
    """Demo strategic case assistant"""
    print("⚖️  Strategic Case Assistant - Intent-First Transformation")
    print("=" * 70)
    
    assistant = StrategicCaseAssistant()
    
    # Sample legal content
    legal_content = """
    Plaintiff alleges constitutional violations under 42 USC 1983.
    Defendants argue qualified immunity and procedural defenses.
    Case involves due process and equal protection claims.
    Discovery reveals strong documentary evidence supporting plaintiff's claims.
    Similar cases in this jurisdiction have had mixed results.
    Expert testimony available on constitutional standards.
    """
    
    print("\n📋 Analyzing case strategy...")
    
    result = await assistant.get_strategic_case_analysis(
        legal_content=legal_content,
        case_type="civil_rights",
        jurisdiction="federal",
        case_phase="discovery",
        case_value=500000,
        client_goals=["monetary_damages", "injunctive_relief"]
    )
    
    print(f"\n✅ Strategic Analysis Complete")
    print(f"\nPrimary Strategy: {result['primary_strategy'].replace('_', ' ').title()}")
    print(f"Win Probability: {result['win_probability']}")
    print(f"Overall Strength: {result['overall_strength'].title()}")
    
    print(f"\n🎯 Key Recommendations:")
    for i, rec in enumerate(result['key_recommendations'], 1):
        print(f"  {i}. {rec}")
    
    print(f"\n📚 Relevant Precedents: {len(result['relevant_precedents'])} identified")
    print(f"⚠️  Risks Identified: {len(result['risk_assessment'])}")
    
    print("\n" + "=" * 70)
    print("✅ Transformation: Legal Transcription → Strategic Case Assistant")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
