"""
Test Suite for Transcription Correction System
Tests all correction engines, learning system, and UI components
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import json
import sqlite3
import tempfile
import os
from pathlib import Path

# Import system components
from transcription_correction_engine import (
    TranscriptionCorrectionSystem,
    CorrectionType,
    CorrectionResult,
    UserCorrection,
    SpellingCorrector,
    GrammarCorrector,
    PunctuationCorrector,
    ContextualCorrector,
    TechnicalTermCorrector,
    HomophoneDetector,
    CorrectionLearningSystem
)


class TestSpellingCorrector:
    """Test spelling correction functionality"""
    
    @pytest.fixture
    def corrector(self):
        return SpellingCorrector()
        
    @pytest.mark.asyncio
    async def test_basic_spelling_correction(self, corrector):
        """Test basic spelling error detection and correction"""
        text = "I recieved the packge yesterday"
        corrections = await corrector.correct(text)
        
        assert len(corrections) == 2
        assert any(c.original == "recieved" and c.corrected == "received" for c in corrections)
        assert any(c.original == "packge" and c.corrected == "package" for c in corrections)
        
    @pytest.mark.asyncio
    async def test_context_aware_spelling(self, corrector):
        """Test context-aware spelling corrections"""
        text = "The principle of the school is very strict"
        corrections = await corrector.correct(text)
        
        # Should detect "principle" should be "principal" in this context
        assert any(c.original == "principle" for c in corrections)
        
    @pytest.mark.asyncio
    async def test_technical_terms_preserved(self, corrector):
        """Test that technical terms are not incorrectly corrected"""
        await corrector.add_to_dictionary(["API", "JSON", "OAuth"])
        text = "The API returns JSON data after OAuth authentication"
        corrections = await corrector.correct(text)
        
        # Technical terms should not be flagged as errors
        assert not any(c.original in ["API", "JSON", "OAuth"] for c in corrections)
        
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, corrector):
        """Test confidence scoring for corrections"""
        text = "This is definately wrong"
        corrections = await corrector.correct(text)
        
        assert len(corrections) == 1
        assert corrections[0].original == "definately"
        assert corrections[0].corrected == "definitely"
        assert corrections[0].confidence > 0.8  # High confidence for common error


class TestGrammarCorrector:
    """Test grammar correction functionality"""
    
    @pytest.fixture
    def corrector(self):
        return GrammarCorrector()
        
    @pytest.mark.asyncio
    async def test_subject_verb_agreement(self, corrector):
        """Test subject-verb agreement corrections"""
        text = "The team are working on the project"
        corrections = await corrector.correct(text)
        
        assert len(corrections) > 0
        assert any("are" in c.original and "is" in c.corrected for c in corrections)
        
    @pytest.mark.asyncio
    async def test_article_corrections(self, corrector):
        """Test article usage corrections"""
        text = "I saw a elephant at the zoo"
        corrections = await corrector.correct(text)
        
        assert len(corrections) == 1
        assert corrections[0].original == "a elephant"
        assert corrections[0].corrected == "an elephant"
        
    @pytest.mark.asyncio
    async def test_tense_consistency(self, corrector):
        """Test tense consistency corrections"""
        text = "Yesterday I go to the store and buy milk"
        corrections = await corrector.correct(text)
        
        assert len(corrections) >= 2
        assert any("go" in c.original and "went" in c.corrected for c in corrections)
        assert any("buy" in c.original and "bought" in c.corrected for c in corrections)


class TestPunctuationCorrector:
    """Test punctuation correction functionality"""
    
    @pytest.fixture
    def corrector(self):
        return PunctuationCorrector()
        
    @pytest.mark.asyncio
    async def test_sentence_ending_punctuation(self, corrector):
        """Test addition of sentence-ending punctuation"""
        text = "This is a sentence without punctuation"
        corrections = await corrector.correct(text)
        
        assert len(corrections) == 1
        assert corrections[0].correction_type == CorrectionType.PUNCTUATION
        assert corrections[0].corrected.endswith(".")
        
    @pytest.mark.asyncio
    async def test_comma_insertion(self, corrector):
        """Test comma insertion in lists"""
        text = "I bought apples oranges and bananas"
        corrections = await corrector.correct(text)
        
        assert len(corrections) > 0
        assert any("," in c.corrected for c in corrections)
        
    @pytest.mark.asyncio
    async def test_quotation_marks(self, corrector):
        """Test quotation mark corrections"""
        text = 'He said "hello and walked away'
        corrections = await corrector.correct(text)
        
        assert len(corrections) > 0
        # Should close the quotation
        
    @pytest.mark.asyncio
    async def test_apostrophe_corrections(self, corrector):
        """Test apostrophe usage in contractions and possessives"""
        text = "Its the dogs bone and theyre happy"
        corrections = await corrector.correct(text)
        
        assert any("Its" in c.original and "It's" in c.corrected for c in corrections)
        assert any("dogs" in c.original and "dog's" in c.corrected for c in corrections)
        assert any("theyre" in c.original and "they're" in c.corrected for c in corrections)


class TestContextualCorrector:
    """Test contextual correction functionality"""
    
    @pytest.fixture
    def corrector(self):
        return ContextualCorrector()
        
    @pytest.mark.asyncio
    async def test_word_choice_corrections(self, corrector):
        """Test contextual word choice corrections"""
        text = "The whether is nice today"
        corrections = await corrector.correct(text, context="casual conversation")
        
        assert len(corrections) == 1
        assert corrections[0].original == "whether"
        assert corrections[0].corrected == "weather"
        
    @pytest.mark.asyncio
    async def test_domain_specific_corrections(self, corrector):
        """Test domain-specific contextual corrections"""
        text = "The patient has a temperature"
        corrections_medical = await corrector.correct(text, context="medical")
        
        text = "The metal has a temperature"
        corrections_technical = await corrector.correct(text, context="technical")
        
        # Different contexts might suggest different corrections
        assert corrections_medical != corrections_technical
        
    @pytest.mark.asyncio
    async def test_collocation_corrections(self, corrector):
        """Test collocation and phrase corrections"""
        text = "I made a mistake on purpose by accident"
        corrections = await corrector.correct(text)
        
        # Should detect the contradiction
        assert len(corrections) > 0


class TestHomophoneDetector:
    """Test homophone detection and correction"""
    
    @pytest.fixture
    def detector(self):
        return HomophoneDetector()
        
    @pytest.mark.asyncio
    async def test_common_homophones(self, detector):
        """Test detection of common homophones"""
        text = "Their going to there house over they're"
        corrections = await detector.detect(text)
        
        assert len(corrections) >= 2
        assert any("Their" in c.original and "They're" in c.corrected for c in corrections)
        assert any("they're" in c.original and "there" in c.corrected for c in corrections)
        
    @pytest.mark.asyncio
    async def test_context_based_homophone_detection(self, detector):
        """Test context-based homophone correction"""
        text = "I need to bye some bread"
        corrections = await detector.detect(text)
        
        assert len(corrections) == 1
        assert corrections[0].original == "bye"
        assert corrections[0].corrected == "buy"
        
    @pytest.mark.asyncio
    async def test_multiple_homophones(self, detector):
        """Test handling of multiple homophones"""
        text = "Eye can sea the see from hear"
        corrections = await detector.detect(text)
        
        assert len(corrections) >= 3
        assert any("Eye" in c.original and "I" in c.corrected for c in corrections)
        assert any("sea" in c.original and "see" in c.corrected for c in corrections)
        assert any("hear" in c.original and "here" in c.corrected for c in corrections)


class TestCorrectionLearningSystem:
    """Test the learning system functionality"""
    
    @pytest.fixture
    def learning_system(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        system = CorrectionLearningSystem(db_path)
        yield system
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
            
    @pytest.mark.asyncio
    async def test_learn_from_correction(self, learning_system):
        """Test learning from user corrections"""
        correction = UserCorrection(
            original_text="recieve",
            corrected_text="receive",
            correction_type=CorrectionType.SPELLING,
            context="email",
            accepted=True
        )
        
        await learning_system.learn_from_correction(correction)
        
        # Check if pattern was stored
        patterns = await learning_system.get_correction_patterns()
        assert len(patterns) > 0
        assert patterns[0]['original'] == "recieve"
        assert patterns[0]['corrected'] == "receive"
        
    @pytest.mark.asyncio
    async def test_pattern_frequency_tracking(self, learning_system):
        """Test that pattern frequency is tracked correctly"""
        correction = UserCorrection(
            original_text="teh",
            corrected_text="the",
            correction_type=CorrectionType.SPELLING,
            accepted=True
        )
        
        # Learn the same correction multiple times
        for _ in range(3):
            await learning_system.learn_from_correction(correction)
            
        patterns = await learning_system.get_correction_patterns()
        pattern = next(p for p in patterns if p['original'] == "teh")
        assert pattern['frequency'] == 3
        
    @pytest.mark.asyncio
    async def test_rejection_tracking(self, learning_system):
        """Test tracking of rejected corrections"""
        correction = UserCorrection(
            original_text="colour",
            corrected_text="color",
            correction_type=CorrectionType.SPELLING,
            accepted=False
        )
        
        await learning_system.learn_from_correction(correction)
        
        # Check if rejection was tracked
        should_apply = await learning_system.should_apply_correction("colour", "color")
        assert not should_apply
        
    @pytest.mark.asyncio
    async def test_custom_dictionary_management(self, learning_system):
        """Test custom dictionary functionality"""
        terms = ["COVID-19", "mRNA", "blockchain"]
        
        for term in terms:
            await learning_system.add_to_custom_dictionary(term)
            
        # Check if terms are in dictionary
        for term in terms:
            is_valid = await learning_system.is_in_custom_dictionary(term)
            assert is_valid


class TestTranscriptionCorrectionSystem:
    """Test the main correction system"""
    
    @pytest.fixture
    def correction_system(self):
        return TranscriptionCorrectionSystem()
        
    @pytest.mark.asyncio
    async def test_full_correction_pipeline(self, correction_system):
        """Test the complete correction pipeline"""
        text = "I recieved you're email yesterday. Their was alot of infomation"
        
        result = await correction_system.correct_transcription(
            text=text,
            correction_types=[
                CorrectionType.SPELLING,
                CorrectionType.GRAMMAR,
                CorrectionType.HOMOPHONES
            ]
        )
        
        assert 'corrected_text' in result
        assert 'corrections' in result
        assert 'metrics' in result
        
        assert len(result['corrections']) > 0
        assert result['corrected_text'] != text
        
    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, correction_system):
        """Test that confidence threshold filters corrections"""
        text = "This text has some errors"
        
        # High threshold
        result_high = await correction_system.correct_transcription(
            text=text,
            confidence_threshold=0.9
        )
        
        # Low threshold
        result_low = await correction_system.correct_transcription(
            text=text,
            confidence_threshold=0.1
        )
        
        # Low threshold should have more or equal corrections
        assert len(result_low['corrections']) >= len(result_high['corrections'])
        
    @pytest.mark.asyncio
    async def test_context_aware_correction(self, correction_system):
        """Test context-aware corrections"""
        medical_text = "The patient presented with severe headache"
        
        result = await correction_system.correct_transcription(
            text=medical_text,
            context="medical"
        )
        
        # Medical context should preserve medical terminology
        assert "patient" in result['corrected_text']
        
    @pytest.mark.asyncio
    async def test_batch_correction(self, correction_system):
        """Test batch correction functionality"""
        texts = [
            "First text with erors",
            "Second text with mistakes",
            "Third text with problems"
        ]
        
        results = await correction_system.batch_correct(texts)
        
        assert len(results) == 3
        for result in results:
            assert 'corrected_text' in result
            assert 'corrections' in result
            
    @pytest.mark.asyncio
    async def test_learning_integration(self, correction_system):
        """Test integration with learning system"""
        # Make a correction
        text = "I recieve emails daily"
        result = await correction_system.correct_transcription(text)
        
        # Learn from user feedback
        if result['corrections']:
            correction = result['corrections'][0]
            user_correction = UserCorrection(
                original_text=correction.original,
                corrected_text=correction.corrected,
                correction_type=correction.correction_type,
                accepted=True
            )
            
            await correction_system.learn_from_correction(user_correction)
            
            # The system should remember this correction
            patterns = await correction_system.learning_system.get_correction_patterns()
            assert any(p['original'] == correction.original for p in patterns)
            
    @pytest.mark.asyncio
    async def test_custom_terms_handling(self, correction_system):
        """Test handling of custom technical terms"""
        # Add custom terms
        await correction_system.add_custom_terms([
            "Kubernetes",
            "PostgreSQL",
            "WebSocket"
        ])
        
        text = "We use Kubernetes for orchestration and PostgreSQL for data"
        result = await correction_system.correct_transcription(text)
        
        # Custom terms should not be corrected
        assert not any(
            c.original in ["Kubernetes", "PostgreSQL", "WebSocket"]
            for c in result['corrections']
        )
        
    @pytest.mark.asyncio
    async def test_performance_metrics(self, correction_system):
        """Test that performance metrics are collected"""
        text = "This is a test text with some errors"
        
        result = await correction_system.correct_transcription(text)
        
        assert 'metrics' in result
        assert 'processing_time' in result['metrics']
        assert 'total_corrections' in result['metrics']
        assert 'confidence_avg' in result['metrics']
        assert result['metrics']['processing_time'] > 0


class TestCorrectionUI:
    """Test UI components and interactions"""
    
    @pytest.fixture
    def mock_streamlit(self):
        with patch('correction_ui.st') as mock_st:
            yield mock_st
            
    def test_ui_initialization(self, mock_streamlit):
        """Test UI initialization"""
        from correction_ui import CorrectionUI
        
        ui = CorrectionUI()
        assert ui.correction_system is not None
        
    def test_session_state_initialization(self, mock_streamlit):
        """Test session state initialization"""
        from correction_ui import CorrectionUI
        
        mock_streamlit.session_state = {}
        ui = CorrectionUI()
        
        assert 'current_text' in mock_streamlit.session_state
        assert 'original_text' in mock_streamlit.session_state
        assert 'corrections' in mock_streamlit.session_state
        
    @pytest.mark.asyncio
    async def test_process_corrections_ui(self, mock_streamlit):
        """Test correction processing in UI"""
        from correction_ui import CorrectionUI
        
        mock_streamlit.session_state = {}
        ui = CorrectionUI()
        
        test_text = "Test text with erors"
        await ui.process_corrections(test_text, None)
        
        assert mock_streamlit.session_state.corrections is not None


class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_correction_flow(self):
        """Test complete end-to-end correction flow"""
        system = TranscriptionCorrectionSystem()
        
        # Input text with various error types
        input_text = """
        I recieved you're email about the meeting. Their was alot of good points.
        The principle reason for the delay is the whether conditions.
        We need to adress this issue imediately.
        """
        
        # Process corrections
        result = await system.correct_transcription(
            text=input_text,
            correction_types=[
                CorrectionType.SPELLING,
                CorrectionType.GRAMMAR,
                CorrectionType.PUNCTUATION,
                CorrectionType.HOMOPHONES
            ],
            confidence_threshold=0.5
        )
        
        # Verify corrections were made
        assert result['corrected_text'] != input_text
        assert len(result['corrections']) > 5  # Should catch multiple errors
        
        # Check specific corrections
        corrections_dict = {c.original: c.corrected for c in result['corrections']}
        
        assert "recieved" in corrections_dict
        assert corrections_dict.get("recieved") == "received"
        
        assert "you're" in corrections_dict or "your" in result['corrected_text']
        assert "Their" in corrections_dict or "There" in result['corrected_text']
        
        # Learn from corrections
        for correction in result['corrections'][:3]:
            user_correction = UserCorrection(
                original_text=correction.original,
                corrected_text=correction.corrected,
                correction_type=correction.correction_type,
                accepted=True
            )
            await system.learn_from_correction(user_correction)
            
        # Verify learning worked
        patterns = await system.learning_system.get_correction_patterns()
        assert len(patterns) >= 3
        
    @pytest.mark.asyncio
    async def test_real_world_transcription(self):
        """Test with real-world transcription scenarios"""
        system = TranscriptionCorrectionSystem()
        
        # Simulate real transcription with common ASR errors
        transcription = """
        okay so today were going to talk about the new product launch
        um the marketing team has prepared there presentation
        and uh we need to finalize the bugdet by friday
        i think we should focus on the online chanels first
        lets make sure we address all the stake holders concerns
        """
        
        result = await system.correct_transcription(
            text=transcription,
            correction_types=[
                CorrectionType.SPELLING,
                CorrectionType.GRAMMAR,
                CorrectionType.PUNCTUATION,
                CorrectionType.CONTEXTUAL
            ],
            context="business meeting"
        )
        
        corrected = result['corrected_text']
        
        # Check key corrections
        assert "we're" in corrected or "we are" in corrected  # were -> we're
        assert "their" in corrected  # there -> their
        assert "budget" in corrected  # bugdet -> budget
        assert "channels" in corrected  # chanels -> channels
        assert "stakeholders" in corrected or "stake holders" not in corrected
        
        # Should add punctuation
        assert corrected.count('.') > transcription.count('.')
        
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test system performance with large texts"""
        system = TranscriptionCorrectionSystem()
        
        # Generate a large text
        base_text = "This is a sample sentence with some erors. "
        large_text = base_text * 100  # ~5000 characters
        
        import time
        start_time = time.time()
        
        result = await system.correct_transcription(
            text=large_text,
            correction_types=[CorrectionType.SPELLING]
        )
        
        processing_time = time.time() - start_time
        
        # Should process in reasonable time
        assert processing_time < 10  # Less than 10 seconds for large text
        assert len(result['corrections']) > 0
        assert 'processing_time' in result['metrics']


# Performance benchmarks
@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarks for the correction system"""
    
    @pytest.fixture
    def system(self):
        return TranscriptionCorrectionSystem()
        
    @pytest.mark.asyncio
    async def test_correction_speed(self, system, benchmark):
        """Benchmark correction speed"""
        text = "This is a sample text with some errors for testing"
        
        async def correct():
            return await system.correct_transcription(text)
            
        result = benchmark(lambda: asyncio.run(correct()))
        assert result is not None
        
    @pytest.mark.asyncio
    async def test_learning_speed(self, system, benchmark):
        """Benchmark learning system speed"""
        correction = UserCorrection(
            original_text="test",
            corrected_text="test",
            correction_type=CorrectionType.SPELLING,
            accepted=True
        )
        
        async def learn():
            return await system.learn_from_correction(correction)
            
        benchmark(lambda: asyncio.run(learn()))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])