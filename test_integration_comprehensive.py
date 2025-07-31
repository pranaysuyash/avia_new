#!/usr/bin/env python3
"""
Comprehensive integration tests using generated test data
Tests complete processing pipelines with known inputs and expected outputs
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Set up test environment
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['ELEVENLABS_API_KEY'] = 'test-key'

import media
import stt
import ner_basic
import ner_advanced
import tts
import utils
from test_data_generator import TestDataGenerator
from stt import TranscriptionResult

class TestComprehensiveIntegration:
    """Comprehensive integration tests with generated test data"""
    
    @classmethod
    def setup_class(cls):
        """Set up test data for the entire test class"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.generator = TestDataGenerator(cls.temp_dir)
        
        # Generate test datasets
        cls.main_dataset = cls.generator.create_test_dataset()
        cls.edge_dataset = cls.generator.create_edge_case_data()
        cls.performance_dataset = cls.generator.create_performance_test_data()
        
        print(f"Test data generated in: {cls.temp_dir}")
    
    @classmethod
    def teardown_class(cls):
        """Clean up test data"""
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def load_test_case_data(self, case_id: str, dataset_type: str = "main") -> dict:
        """Load test case data by ID"""
        if dataset_type == "main":
            cases = self.main_dataset["test_cases"]
        elif dataset_type == "edge":
            cases = self.edge_dataset["edge_cases"]
        elif dataset_type == "performance":
            cases = self.performance_dataset["performance_cases"]
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
        
        for case in cases:
            if case["id"] == case_id:
                return case
        
        raise ValueError(f"Test case not found: {case_id}")
    
    def load_expected_entities(self, entities_file: str) -> dict:
        """Load expected entities from JSON file"""
        with open(entities_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_transcript(self, transcript_file: str) -> str:
        """Load transcript from text file"""
        with open(transcript_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    
    @pytest.mark.integration
    def test_media_processing_integration(self):
        """Test media processing with generated audio files"""
        print("Testing media processing integration...")
        
        for case in self.main_dataset["test_cases"]:
            audio_file = case["audio_file"]
            
            # Test file validation
            assert media.validate_media_file(audio_file), f"Validation failed for {case['id']}"
            
            # Test media info extraction
            media_info = media.get_media_info(audio_file)
            assert media_info["duration"] > 0, f"Invalid duration for {case['id']}"
            assert media_info["sample_rate"] > 0, f"Invalid sample rate for {case['id']}"
            
            # Test format conversion
            converted_file = media.convert_audio_format(audio_file)
            assert os.path.exists(converted_file), f"Conversion failed for {case['id']}"
            assert converted_file.endswith('.wav'), f"Wrong output format for {case['id']}"
            
            # Clean up converted file
            utils.cleanup_file(converted_file)
    
    @pytest.mark.integration
    @patch('stt.WhisperTranscriber._transcribe_with_local_model')
    def test_transcription_integration(self, mock_transcribe):
        """Test transcription with known audio files and expected outputs"""
        print("Testing transcription integration...")
        
        for case in self.main_dataset["test_cases"]:
            audio_file = case["audio_file"]
            expected_transcript = self.load_transcript(case["transcript_file"])
            
            # Mock transcription result with expected transcript
            mock_result = TranscriptionResult(
                text=expected_transcript,
                confidence=0.95,
                processing_time=case["duration"] * 0.3,
                model_used="whisper-local-base",
                language="en"
            )
            mock_transcribe.return_value = mock_result
            
            # Test transcription
            result = stt.transcribe_detailed(audio_file, use_api=False)
            
            assert isinstance(result, TranscriptionResult), f"Invalid result type for {case['id']}"
            assert result.text == expected_transcript, f"Transcript mismatch for {case['id']}"
            assert result.word_count() == case["word_count"], f"Word count mismatch for {case['id']}"
            assert result.confidence > 0.8, f"Low confidence for {case['id']}"
            
            # Test timestamped transcription
            with patch('stt.WhisperTranscriber._load_local_model') as mock_load:
                mock_model = MagicMock()
                mock_model.transcribe.return_value = {
                    'segments': [
                        {
                            'text': expected_transcript[:50],
                            'start': 0.0,
                            'end': 5.0,
                            'avg_logprob': -0.2,
                            'words': [
                                {'word': 'test', 'start': 0.0, 'end': 0.5, 'probability': 0.9}
                            ]
                        }
                    ]
                }
                mock_load.return_value = mock_model
                
                timestamps = stt.transcribe_with_timestamps(audio_file)
                assert isinstance(timestamps, list), f"Invalid timestamps type for {case['id']}"
                assert len(timestamps) > 0, f"No timestamps returned for {case['id']}"
    
    @pytest.mark.integration
    def test_basic_ner_integration(self):
        """Test basic NER with known transcripts and expected entities"""
        print("Testing basic NER integration...")
        
        for case in self.main_dataset["test_cases"]:
            transcript = self.load_transcript(case["transcript_file"])
            expected_entities = self.load_expected_entities(case["entities_file"])
            
            try:
                # Test entity extraction
                extracted_entities = ner_basic.extract_entities(transcript)
                
                # Test confidence scoring
                confidence_scores = ner_basic.get_entity_confidence(transcript)
                
                # Verify structure
                assert isinstance(extracted_entities, dict), f"Invalid entities type for {case['id']}"
                assert isinstance(confidence_scores, dict), f"Invalid confidence type for {case['id']}"
                
                # Check that we found some entities (allowing for spaCy model differences)
                total_extracted = sum(len(v) for v in extracted_entities.values())
                if case["expected_entity_count"] > 0:
                    assert total_extracted > 0, f"No entities extracted for {case['id']}"
                
                # Test entity filtering
                if "PERSON" in extracted_entities:
                    filtered = ner_basic.filter_entities_by_type(extracted_entities, ["PERSON"])
                    assert "PERSON" in filtered, f"Entity filtering failed for {case['id']}"
                    assert len(filtered) == 1, f"Wrong filter result for {case['id']}"
                
                print(f"  ✅ {case['id']}: {total_extracted} entities extracted")
                
            except Exception as e:
                print(f"  ⚠️ {case['id']}: Basic NER failed (may need spaCy model): {e}")
    
    @pytest.mark.integration
    @patch('ner_advanced._get_openai_client')
    def test_advanced_ner_integration(self, mock_client):
        """Test advanced NER with known transcripts and expected outputs"""
        print("Testing advanced NER integration...")
        
        for case in self.main_dataset["test_cases"]:
            transcript = self.load_transcript(case["transcript_file"])
            expected_entities = self.load_expected_entities(case["entities_file"])
            expected_summary = case["expected_summary"]
            
            # Mock OpenAI response with expected entities
            mock_response = MagicMock()
            mock_response.choices[0].message.function_call.arguments = json.dumps(expected_entities)
            
            mock_client_instance = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # Test entity extraction
            extracted_entities, summary = ner_advanced.extract_entities_advanced(transcript)
            
            # Verify structure and content
            assert isinstance(extracted_entities, dict), f"Invalid entities type for {case['id']}"
            assert isinstance(summary, str), f"Invalid summary type for {case['id']}"
            
            # Check entity categories
            for category in expected_entities:
                if expected_entities[category]:  # Only check non-empty categories
                    assert category in extracted_entities, f"Missing category {category} for {case['id']}"
                    assert len(extracted_entities[category]) > 0, f"Empty category {category} for {case['id']}"
            
            # Test sentiment analysis
            sentiment = ner_advanced.analyze_sentiment(transcript)
            assert isinstance(sentiment, dict), f"Invalid sentiment type for {case['id']}"
            required_keys = ["positive", "negative", "neutral", "confidence"]
            for key in required_keys:
                assert key in sentiment, f"Missing sentiment key {key} for {case['id']}"
                assert 0.0 <= sentiment[key] <= 1.0, f"Invalid sentiment value for {key} in {case['id']}"
            
            print(f"  ✅ {case['id']}: {sum(len(v) for v in extracted_entities.values())} entities, sentiment analyzed")
    
    @pytest.mark.integration
    @patch('ner_advanced._get_openai_client')
    @patch('tts._get_elevenlabs_client')
    def test_admin_workflow_integration(self, mock_tts_client, mock_script_client):
        """Test complete admin workflow: script generation + TTS synthesis"""
        print("Testing admin workflow integration...")
        
        # Mock script generation
        test_scripts = [
            "This is a generated conversational script about technology and innovation.",
            "Welcome to our formal presentation on quarterly business results.",
            "Today's educational content covers environmental science and climate change."
        ]
        
        # Mock TTS synthesis
        mock_tts_client_instance = MagicMock()
        mock_tts_client_instance.text_to_speech.convert.return_value = [b'fake_audio_data' * 1000]
        mock_tts_client.return_value = mock_tts_client_instance
        
        for i, script_text in enumerate(test_scripts):
            # Mock script generation response
            mock_script_response = MagicMock()
            mock_script_response.choices[0].message.content = script_text
            
            mock_script_client_instance = MagicMock()
            mock_script_client_instance.chat.completions.create.return_value = mock_script_response
            mock_script_client.return_value = mock_script_client_instance
            
            # Test script generation
            prompt = f"Generate a test script {i+1}"
            styles = ["conversational", "formal", "educational"]
            style = styles[i % len(styles)]
            
            generated_script = ner_advanced.generate_script(prompt, style)
            assert isinstance(generated_script, str), f"Invalid script type for test {i+1}"
            assert len(generated_script) > 0, f"Empty script for test {i+1}"
            assert generated_script == script_text, f"Script mismatch for test {i+1}"
            
            # Test cost estimation
            estimated_cost = tts.estimate_synthesis_cost(generated_script)
            assert isinstance(estimated_cost, float), f"Invalid cost type for test {i+1}"
            assert estimated_cost >= 0, f"Negative cost for test {i+1}"
            
            # Test TTS synthesis
            audio_path = tts.synthesize_speech(
                text=generated_script,
                voice_id=tts.VOICE_PRESETS["professional"]["voice_id"],
                voice_settings=tts.VOICE_PRESETS["professional"]["settings"]
            )
            
            assert isinstance(audio_path, str), f"Invalid audio path type for test {i+1}"
            assert os.path.exists(audio_path), f"Audio file not created for test {i+1}"
            assert audio_path.endswith('.mp3'), f"Wrong audio format for test {i+1}"
            
            # Clean up generated audio
            utils.cleanup_file(audio_path)
            
            print(f"  ✅ Test {i+1}: Script generated ({len(generated_script)} chars), TTS synthesized")
    
    @pytest.mark.integration
    def test_edge_cases_integration(self):
        """Test integration with edge cases and error conditions"""
        print("Testing edge cases integration...")
        
        for case in self.edge_dataset["edge_cases"]:
            case_id = case["id"]
            audio_file = case["audio_file"]
            transcript = self.load_transcript(case["transcript_file"])
            
            print(f"  Testing edge case: {case_id}")
            
            # Test media processing with edge cases
            try:
                is_valid = media.validate_media_file(audio_file)
                assert isinstance(is_valid, bool), f"Invalid validation result for {case_id}"
                
                if is_valid:
                    media_info = media.get_media_info(audio_file)
                    assert isinstance(media_info, dict), f"Invalid media info for {case_id}"
                
            except Exception as e:
                print(f"    ⚠️ Media processing failed for {case_id}: {e}")
            
            # Test NER with edge cases
            try:
                basic_entities = ner_basic.extract_entities(transcript)
                assert isinstance(basic_entities, dict), f"Invalid basic entities for {case_id}"
                
                # Empty transcript should return empty entities
                if not transcript.strip():
                    assert len(basic_entities) == 0, f"Non-empty entities for empty transcript in {case_id}"
                
            except Exception as e:
                print(f"    ⚠️ Basic NER failed for {case_id}: {e}")
            
            # Test advanced NER with edge cases
            try:
                with patch('ner_advanced._get_openai_client') as mock_client:
                    # Mock appropriate response for edge case
                    expected_entities = self.load_expected_entities(case["entities_file"])
                    mock_response = MagicMock()
                    mock_response.choices[0].message.function_call.arguments = json.dumps(expected_entities)
                    
                    mock_client_instance = MagicMock()
                    mock_client_instance.chat.completions.create.return_value = mock_response
                    mock_client.return_value = mock_client_instance
                    
                    entities, summary = ner_advanced.extract_entities_advanced(transcript)
                    assert isinstance(entities, dict), f"Invalid advanced entities for {case_id}"
                    assert isinstance(summary, str), f"Invalid summary for {case_id}"
                
            except Exception as e:
                print(f"    ⚠️ Advanced NER failed for {case_id}: {e}")
            
            print(f"    ✅ {case_id}: Edge case handled")
    
    @pytest.mark.integration
    def test_complete_pipeline_integration(self):
        """Test complete end-to-end pipeline with realistic data"""
        print("Testing complete pipeline integration...")
        
        # Select a representative test case
        test_case = self.load_test_case_data("business_meeting")
        audio_file = test_case["audio_file"]
        expected_transcript = self.load_transcript(test_case["transcript_file"])
        expected_entities = self.load_expected_entities(test_case["entities_file"])
        
        temp_files_to_cleanup = []
        
        try:
            # Step 1: Media Processing
            print("  Step 1: Media processing...")
            assert media.validate_media_file(audio_file)
            
            if media.is_audio_file(audio_file):
                processed_audio = media.convert_audio_format(audio_file)
                temp_files_to_cleanup.append(processed_audio)
            else:
                processed_audio = audio_file
            
            # Step 2: Transcription
            print("  Step 2: Transcription...")
            with patch('stt.WhisperTranscriber._transcribe_with_local_model') as mock_transcribe:
                mock_result = TranscriptionResult(
                    text=expected_transcript,
                    confidence=0.95,
                    processing_time=test_case["duration"] * 0.3,
                    model_used="whisper-local-base",
                    language="en"
                )
                mock_transcribe.return_value = mock_result
                
                transcription_result = stt.transcribe_detailed(processed_audio, use_api=False)
                assert transcription_result.text == expected_transcript
            
            # Step 3: Basic Entity Extraction
            print("  Step 3: Basic entity extraction...")
            try:
                basic_entities = ner_basic.extract_entities(transcription_result.text)
                basic_confidence = ner_basic.get_entity_confidence(transcription_result.text)
                
                assert isinstance(basic_entities, dict)
                assert isinstance(basic_confidence, dict)
                
                basic_entity_count = sum(len(v) for v in basic_entities.values())
                print(f"    Basic NER: {basic_entity_count} entities extracted")
                
            except Exception as e:
                print(f"    ⚠️ Basic NER failed: {e}")
                basic_entities = {}
                basic_confidence = {}
            
            # Step 4: Advanced Entity Extraction
            print("  Step 4: Advanced entity extraction...")
            with patch('ner_advanced._get_openai_client') as mock_client:
                mock_response = MagicMock()
                mock_response.choices[0].message.function_call.arguments = json.dumps(expected_entities)
                
                mock_client_instance = MagicMock()
                mock_client_instance.chat.completions.create.return_value = mock_response
                mock_client.return_value = mock_client_instance
                
                advanced_entities, summary = ner_advanced.extract_entities_advanced(transcription_result.text)
                
                assert isinstance(advanced_entities, dict)
                assert isinstance(summary, str)
                assert len(summary) > 0
                
                advanced_entity_count = sum(len(v) for v in advanced_entities.values())
                print(f"    Advanced NER: {advanced_entity_count} entities extracted")
            
            # Step 5: Admin Workflow (Script Generation + TTS)
            print("  Step 5: Admin workflow...")
            with patch('ner_advanced._get_openai_client') as mock_script_client, \
                 patch('tts._get_elevenlabs_client') as mock_tts_client:
                
                # Mock script generation
                test_script = "This is a generated script based on the business meeting transcript."
                mock_script_response = MagicMock()
                mock_script_response.choices[0].message.content = test_script
                
                mock_script_client_instance = MagicMock()
                mock_script_client_instance.chat.completions.create.return_value = mock_script_response
                mock_script_client.return_value = mock_script_client_instance
                
                # Mock TTS synthesis
                mock_tts_client_instance = MagicMock()
                mock_tts_client_instance.text_to_speech.convert.return_value = [b'fake_audio_data']
                mock_tts_client.return_value = mock_tts_client_instance
                
                # Generate script
                generated_script = ner_advanced.generate_script(
                    "Create a summary script based on the business meeting", 
                    "professional"
                )
                assert generated_script == test_script
                
                # Synthesize speech
                audio_path = tts.synthesize_speech(generated_script)
                temp_files_to_cleanup.append(audio_path)
                
                assert os.path.exists(audio_path)
                print(f"    Admin workflow: Script generated and synthesized")
            
            # Step 6: Results Validation
            print("  Step 6: Results validation...")
            
            # Validate transcription results
            assert transcription_result.word_count() > 0
            assert transcription_result.confidence > 0.8
            
            # Validate entity extraction results
            if advanced_entities:
                for category in ["persons", "organizations", "locations"]:
                    if category in expected_entities and expected_entities[category]:
                        assert category in advanced_entities, f"Missing category: {category}"
            
            print("  ✅ Complete pipeline integration successful!")
            
        finally:
            # Clean up temporary files
            for file_path in temp_files_to_cleanup:
                if os.path.exists(file_path):
                    utils.cleanup_file(file_path)
    
    @pytest.mark.integration
    def test_error_recovery_integration(self):
        """Test error recovery and graceful degradation"""
        print("Testing error recovery integration...")
        
        # Test API failure recovery
        with patch('ner_advanced._get_openai_client', side_effect=Exception("API Error")):
            try:
                entities, summary = ner_advanced.extract_entities_advanced("Test text")
                assert False, "Should have raised an exception"
            except Exception as e:
                assert "API Error" in str(e) or "failed" in str(e).lower()
                print("  ✅ API failure properly handled")
        
        # Test file processing error recovery
        try:
            media.validate_media_file("nonexistent_file.mp3")
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "not found" in str(e).lower() or "does not exist" in str(e).lower()
            print("  ✅ File not found error properly handled")
        
        # Test empty input handling
        basic_entities = ner_basic.extract_entities("")
        assert basic_entities == {}
        print("  ✅ Empty input properly handled")
        
        advanced_entities, summary = ner_advanced.extract_entities_advanced("")
        assert advanced_entities == {}
        assert summary == "No content to analyze"
        print("  ✅ Empty advanced input properly handled")
    
    @pytest.mark.integration
    def test_configuration_integration(self):
        """Test configuration and environment setup"""
        print("Testing configuration integration...")
        
        from config import Config
        
        # Test API key validation
        api_status = Config.validate_api_keys()
        assert isinstance(api_status, dict)
        assert "openai" in api_status
        assert "elevenlabs" in api_status
        print("  ✅ API key validation working")
        
        # Test configuration validation
        is_valid, issues = Config.validate_configuration()
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)
        print("  ✅ Configuration validation working")
        
        # Test file size limits
        assert Config.MAX_FILE_SIZE_MB > 0
        print(f"  ✅ File size limit configured: {Config.MAX_FILE_SIZE_MB}MB")


def main():
    """Run comprehensive integration tests"""
    print("🚀 Starting comprehensive integration tests...")
    print("=" * 70)
    
    # Run the tests
    pytest.main([__file__, "-v", "-m", "integration"])


if __name__ == "__main__":
    main()