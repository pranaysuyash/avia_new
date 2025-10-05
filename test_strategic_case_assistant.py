#!/usr/bin/env python3
"""
Test Suite for Strategic Case Assistant
Validates Intent-First transformation from legal transcription to strategic case analysis
"""

import pytest
import asyncio
from datetime import datetime
from strategic_case_assistant import (
    StrategicCaseAssistant,
    CaseStrategyType,
    ArgumentStrength,
    LegalUrgency,
    CasePhase,
    LegalJurisdiction
)

class TestStrategicCaseAssistant:
    """Test Strategic Case Assistant functionality"""
    
    def setup_method(self):
        self.assistant = StrategicCaseAssistant()
    
    @pytest.mark.asyncio
    async def test_case_strategy_analysis(self):
        """Test comprehensive case strategy analysis"""
        legal_content = """
        Plaintiff alleges constitutional violations under 42 USC 1983.
        Defendants argue qualified immunity and procedural defenses.
        Case involves due process and equal protection claims.
        Discovery reveals strong documentary evidence.
        """
        
        case_context = {
            'case_type': 'civil_rights',
            'case_value': 500000,
            'client_goals': ['monetary_damages', 'injunctive_relief']
        }
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='civil_rights',
            jurisdiction='federal',
            case_phase='discovery',
            case_value=500000,
            client_goals=['monetary_damages']
        )
        
        # Validate structure
        assert 'case_summary' in result
        assert 'primary_strategy' in result
        assert 'win_probability' in result
        assert 'overall_strength' in result
        assert 'key_recommendations' in result
        assert 'strategic_arguments' in result
        assert 'relevant_precedents' in result
        assert 'risk_assessment' in result
        
        # Validate content quality
        assert result['primary_strategy'] in [s.value for s in CaseStrategyType]
        assert '%' in result['win_probability']
        assert len(result['key_recommendations']) > 0
        assert len(result['strategic_arguments']) > 0
    
    @pytest.mark.asyncio
    async def test_constitutional_strategy(self):
        """Test constitutional law strategy analysis"""
        legal_content = """
        First Amendment free speech violation alleged.
        Government restriction on political expression.
        Strict scrutiny standard applies.
        Strong precedent support from Supreme Court.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='constitutional',
            jurisdiction='federal',
            case_phase='motion_practice'
        )
        
        # Should identify constitutional strategy
        assert 'constitutional' in result['primary_strategy'].lower() or \
               any('constitutional' in arg['type'] for arg in result['strategic_arguments'])
        
        # Should have high confidence for strong constitutional claims
        assert len(result['strategic_arguments']) > 0
    
    @pytest.mark.asyncio
    async def test_precedent_analysis(self):
        """Test legal precedent identification and analysis"""
        legal_content = """
        Contract breach claim with liquidated damages clause.
        Similar cases in jurisdiction favor enforcement.
        Clear contractual language and mutual assent.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='contract',
            jurisdiction='state',
            case_phase='discovery'
        )
        
        # Should identify relevant precedents
        assert 'relevant_precedents' in result
        assert isinstance(result['relevant_precedents'], list)
        
        # Precedents should have required fields
        if len(result['relevant_precedents']) > 0:
            precedent = result['relevant_precedents'][0]
            assert 'case_name' in precedent
            assert 'relevance' in precedent
            assert 'key_holding' in precedent
    
    @pytest.mark.asyncio
    async def test_risk_assessment(self):
        """Test litigation risk assessment"""
        legal_content = """
        Complex multi-party litigation with procedural challenges.
        Adverse precedent in jurisdiction.
        Evidentiary issues with key documents.
        High litigation costs expected.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='commercial',
            jurisdiction='federal',
            case_phase='discovery'
        )
        
        # Should identify risks
        assert 'risk_assessment' in result
        assert isinstance(result['risk_assessment'], list)
        
        # Risks should have required fields
        if len(result['risk_assessment']) > 0:
            risk = result['risk_assessment'][0]
            assert 'risk_type' in risk
            assert 'probability' in risk
            assert 'impact' in risk
            assert 'mitigation' in risk
    
    @pytest.mark.asyncio
    async def test_settlement_analysis(self):
        """Test settlement potential analysis"""
        legal_content = """
        Moderate strength case with settlement discussions ongoing.
        Both parties motivated to avoid trial costs.
        Reasonable settlement range identified.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='personal_injury',
            jurisdiction='state',
            case_phase='discovery',
            case_value=250000
        )
        
        # Should include settlement analysis
        assert 'settlement_analysis' in result
        settlement = result['settlement_analysis']
        
        # Settlement analysis should have key components
        assert isinstance(settlement, dict)
        # May have settlement_probability, estimated_range, etc.
    
    @pytest.mark.asyncio
    async def test_procedural_recommendations(self):
        """Test procedural strategy recommendations"""
        legal_content = """
        Motion to dismiss pending on procedural grounds.
        Discovery disputes requiring court intervention.
        Deadline approaching for expert disclosures.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='commercial',
            jurisdiction='federal',
            case_phase='motion_practice'
        )
        
        # Should provide procedural recommendations
        assert 'procedural_recommendations' in result
        assert isinstance(result['procedural_recommendations'], list)
    
    @pytest.mark.asyncio
    async def test_evidence_strategy(self):
        """Test evidence strategy development"""
        legal_content = """
        Strong documentary evidence supporting claims.
        Expert testimony needed on technical issues.
        Witness credibility will be key factor.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='product_liability',
            jurisdiction='federal',
            case_phase='trial_prep'
        )
        
        # Should include evidence strategy
        assert 'evidence_strategy' in result
        assert isinstance(result['evidence_strategy'], list)
    
    @pytest.mark.asyncio
    async def test_timeline_analysis(self):
        """Test case timeline and milestone analysis"""
        legal_content = """
        Case in early discovery phase.
        Trial date set for 12 months out.
        Multiple motions anticipated.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='employment',
            jurisdiction='federal',
            case_phase='discovery'
        )
        
        # Should include timeline analysis
        assert 'timeline_analysis' in result
        assert isinstance(result['timeline_analysis'], dict)
    
    @pytest.mark.asyncio
    async def test_cost_benefit_analysis(self):
        """Test litigation cost-benefit analysis"""
        legal_content = """
        High-value case with significant litigation costs.
        Strong merits but lengthy trial expected.
        Settlement may be cost-effective option.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='commercial',
            jurisdiction='federal',
            case_phase='discovery',
            case_value=1000000
        )
        
        # Should include cost-benefit analysis
        assert 'cost_benefit' in result
        assert isinstance(result['cost_benefit'], dict)
    
    @pytest.mark.asyncio
    async def test_transformation_validation(self):
        """Validate Intent-First transformation: Legal Transcription → Strategic Case Assistant"""
        legal_content = """
        Plaintiff alleges breach of contract and fraud.
        Strong documentary evidence and witness testimony.
        Defendant has procedural defenses but weak on merits.
        Case value estimated at $750,000.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='contract',
            jurisdiction='state',
            case_phase='discovery',
            case_value=750000
        )
        
        # BEFORE: Would just extract legal entities and citations
        # AFTER: Provides strategic case analysis with actionable recommendations
        
        # Validates transformation characteristics
        assert 'win_probability' in result
        assert 'key_recommendations' in result
        assert len(result['key_recommendations']) > 0
        assert 'strategic_arguments' in result
        assert len(result['strategic_arguments']) > 0
        
        # Each argument should have strategic analysis
        for arg in result['strategic_arguments']:
            assert 'type' in arg
            assert 'strength' in arg
            assert 'success_probability' in arg
            assert 'emphasis' in arg
        
        # Should provide actionable insights
        assert 'procedural_recommendations' in result
        assert 'evidence_strategy' in result
        assert 'risk_assessment' in result

class TestArgumentAnalysis:
    """Test argument strength and strategy analysis"""
    
    def setup_method(self):
        self.assistant = StrategicCaseAssistant()
    
    @pytest.mark.asyncio
    async def test_strong_argument_identification(self):
        """Test identification of strong legal arguments"""
        legal_content = """
        Clear statutory violation with strong precedent support.
        Undisputed facts favor plaintiff's position.
        Defendant's defenses lack legal merit.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='statutory',
            jurisdiction='federal',
            case_phase='motion_practice'
        )
        
        # Should identify strong arguments
        if result['strategic_arguments']:
            # At least one argument should be strong or moderate
            strengths = [arg['strength'] for arg in result['strategic_arguments']]
            assert any(s in ['strong', 'moderate'] for s in strengths)
    
    @pytest.mark.asyncio
    async def test_weak_argument_identification(self):
        """Test identification of weak legal arguments"""
        legal_content = """
        Novel legal theory with limited precedent support.
        Factual disputes undermine key claims.
        Adverse precedent in controlling jurisdiction.
        """
        
        result = await self.assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='tort',
            jurisdiction='state',
            case_phase='discovery'
        )
        
        # Should identify challenges and provide realistic assessment
        assert 'risk_assessment' in result
        # Win probability should reflect challenges
        if 'win_probability' in result:
            # Should be present even if not high
            assert '%' in result['win_probability']

class TestJurisdictionHandling:
    """Test handling of different jurisdictions"""
    
    def setup_method(self):
        self.assistant = StrategicCaseAssistant()
    
    @pytest.mark.asyncio
    async def test_federal_jurisdiction(self):
        """Test federal jurisdiction case analysis"""
        result = await self.assistant.get_strategic_case_analysis(
            legal_content="Federal question jurisdiction case",
            case_type='federal',
            jurisdiction='federal',
            case_phase='discovery'
        )
        
        assert result is not None
        assert 'case_summary' in result
    
    @pytest.mark.asyncio
    async def test_state_jurisdiction(self):
        """Test state jurisdiction case analysis"""
        result = await self.assistant.get_strategic_case_analysis(
            legal_content="State law claims",
            case_type='state',
            jurisdiction='state',
            case_phase='discovery'
        )
        
        assert result is not None
        assert 'case_summary' in result

class TestCasePhases:
    """Test analysis across different case phases"""
    
    def setup_method(self):
        self.assistant = StrategicCaseAssistant()
    
    @pytest.mark.asyncio
    async def test_discovery_phase(self):
        """Test analysis during discovery phase"""
        result = await self.assistant.get_strategic_case_analysis(
            legal_content="Discovery phase case",
            case_type='commercial',
            jurisdiction='federal',
            case_phase='discovery'
        )
        
        assert result is not None
        # Discovery phase should focus on evidence gathering
        assert 'evidence_strategy' in result
    
    @pytest.mark.asyncio
    async def test_trial_phase(self):
        """Test analysis during trial phase"""
        result = await self.assistant.get_strategic_case_analysis(
            legal_content="Trial preparation",
            case_type='commercial',
            jurisdiction='federal',
            case_phase='trial'
        )
        
        assert result is not None
        # Trial phase should focus on presentation strategy
        assert 'evidence_strategy' in result
    
    @pytest.mark.asyncio
    async def test_appeal_phase(self):
        """Test analysis during appeal phase"""
        result = await self.assistant.get_strategic_case_analysis(
            legal_content="Appellate issues",
            case_type='commercial',
            jurisdiction='federal',
            case_phase='appeal'
        )
        
        assert result is not None
        assert 'case_summary' in result

# Integration tests
class TestIntegration:
    """Integration tests for complete workflow"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_case_analysis(self):
        """Test complete end-to-end case analysis workflow"""
        assistant = StrategicCaseAssistant()
        
        legal_content = """
        Complex commercial litigation involving breach of contract,
        fraud, and tortious interference claims. Plaintiff seeks
        $2M in damages plus punitive damages. Strong documentary
        evidence but some witness credibility issues. Defendant
        has raised statute of limitations and failure to mitigate
        defenses. Case is in discovery phase with trial set for
        8 months out. Settlement discussions have been unsuccessful.
        Jurisdiction is federal district court.
        """
        
        result = await assistant.get_strategic_case_analysis(
            legal_content=legal_content,
            case_type='commercial',
            jurisdiction='federal',
            case_phase='discovery',
            case_value=2000000,
            client_goals=['monetary_damages', 'business_reputation']
        )
        
        # Validate comprehensive output
        assert all(key in result for key in [
            'case_summary',
            'primary_strategy',
            'win_probability',
            'overall_strength',
            'key_recommendations',
            'strategic_arguments',
            'relevant_precedents',
            'risk_assessment',
            'settlement_analysis',
            'procedural_recommendations',
            'evidence_strategy',
            'timeline_analysis',
            'cost_benefit'
        ])
        
        # Validate quality of analysis
        assert len(result['key_recommendations']) >= 1
        assert len(result['strategic_arguments']) >= 1
        assert result['overall_strength'] in ['strong', 'moderate', 'weak', 'unlikely']
        
        print("\n✅ End-to-end case analysis completed successfully")
        print(f"Primary Strategy: {result['primary_strategy']}")
        print(f"Win Probability: {result['win_probability']}")
        print(f"Overall Strength: {result['overall_strength']}")
        print(f"Key Recommendations: {len(result['key_recommendations'])}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
