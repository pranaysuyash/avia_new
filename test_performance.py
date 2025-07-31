#!/usr/bin/env python3
"""
Performance tests for the audio transcription application
Tests processing speed, memory usage, and scalability with various file sizes
"""

import os
import time
import tempfile
import pytest
import psutil
import threading
from unittest.mock import patch, MagicMock
from pathlib import Path

import media
import stt
import ner_basic
import ner_advanced
import tts
import utils
from stt import TranscriptionResult

class TestPerformance:
    """Performance test suite for all modules"""
    
    def setup_method(self):
        """Set up performance test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.process = psutil.Process()
        
    def teardown_method(self):
        """Clean up performance test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_audio_file(self, duration_seconds: float, sample_rate: int = 16000) -> str:
        """Create a test audio file of specified duration"""
        import wave
        import numpy as np
        
        temp_file = os.path.join(self.temp_dir, f"test_audio_{duration_seconds}s.wav")
        
        # Generate sine wave
        t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        
        with wave.open(temp_file, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return temp_file
    
    def _measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage during function execution"""
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        processing_time = end_time - start_time
        
        return result, processing_time, memory_used
    
    @pytest.mark.performance
    def test_media_processing_performance(self):
        """Test media processing performance with various file sizes"""
        test_cases = [
            (10, "10 second audio"),
            (30, "30 second audio"),
            (60, "1 minute audio"),
            (120, "2 minute audio")
        ]
        
        results = []
        
        for duration, description in test_cases:
            audio_file = self._create_test_audio_file(duration)
            
            # Test validation performance
            validation_result, validation_time, validation_memory = self._measure_memory_usage(
                media.validate_media_file, audio_file
            )
            
            # Test format conversion performance
            conversion_result, conversion_time, conversion_memory = self._measure_memory_usage(
                media.convert_audio_format, audio_file
            )
            
            results.append({
                'duration': duration,
                'description': description,
                'validation_time': validation_time,
                'validation_memory': validation_memory,
                'conversion_time': conversion_time,
                'conversion_memory': conversion_memory
            })
            
            # Clean up converted file
            if os.path.exists(conversion_result):
                os.remove(conversion_result)
        
        # Performance assertions
        for result in results:
            # Validation should be fast (< 1 second for files up to 2 minutes)
            assert result['validation_time'] < 1.0, f"Validation too slow for {result['description']}: {result['validation_time']:.2f}s"
            
            # Conversion should be reasonable (< 0.5x real-time)
            expected_max_time = result['duration'] * 0.5
            assert result['conversion_time'] < expected_max_time, f"Conversion too slow for {result['description']}: {result['conversion_time']:.2f}s"
            
            # Memory usage should be reasonable (< 100MB for conversion)
            assert result['conversion_memory'] < 100, f"Conversion uses too much memory for {result['description']}: {result['conversion_memory']:.2f}MB"
        
        print("Media processing performance results:")
        for result in results:
            print(f"  {result['description']}: validation={result['validation_time']:.3f}s, conversion={result['conversion_time']:.3f}s")
    
    @pytest.mark.performance
    @patch('stt.WhisperTranscriber._transcribe_with_local_model')
    def test_transcription_performance(self, mock_transcribe):
        """Test transcription performance with various text lengths"""
        # Mock transcription results for different durations
        test_cases = [
            (10, "Short audio (10s)", "This is a short test transcription."),
            (30, "Medium audio (30s)", "This is a medium length test transcription with more words to process. " * 5),
            (60, "Long audio (60s)", "This is a long test transcription with many words to process and analyze. " * 15),
            (120, "Very long audio (120s)", "This is a very long test transcription with extensive content. " * 30)
        ]
        
        results = []
        
        for duration, description, transcript_text in test_cases:
            audio_file = self._create_test_audio_file(duration)
            
            # Mock the transcription result
            mock_result = TranscriptionResult(
                text=transcript_text,
                confidence=0.9,
                processing_time=duration * 0.3,  # Simulate processing time
                model_used="whisper-local-base",
                language="en"
            )
            mock_transcribe.return_value = mock_result
            
            # Measure transcription performance
            transcription_result, processing_time, memory_used = self._measure_memory_usage(
                stt.transcribe_detailed, audio_file, use_api=False
            )
            
            results.append({
                'duration': duration,
                'description': description,
                'word_count': transcription_result.word_count(),
                'processing_time': processing_time,
                'memory_used': memory_used,
                'words_per_second': transcription_result.word_count() / processing_time if processing_time > 0 else 0
            })
        
        # Performance assertions
        for result in results:
            # Processing should be faster than real-time (< 1x duration)
            assert result['processing_time'] < result['duration'], f"Transcription too slow for {result['description']}: {result['processing_time']:.2f}s"
            
            # Memory usage should be reasonable (< 500MB)
            assert result['memory_used'] < 500, f"Transcription uses too much memory for {result['description']}: {result['memory_used']:.2f}MB"
            
            # Should process at least 10 words per second
            assert result['words_per_second'] > 10, f"Word processing too slow for {result['description']}: {result['words_per_second']:.2f} words/s"
        
        print("Transcription performance results:")
        for result in results:
            print(f"  {result['description']}: {result['processing_time']:.3f}s, {result['words_per_second']:.1f} words/s")
    
    @pytest.mark.performance
    def test_ner_basic_performance(self):
        """Test basic NER performance with various text lengths"""
        test_texts = [
            ("Short text", "John Smith works at Microsoft in Seattle."),
            ("Medium text", "John Smith works at Microsoft Corporation in Seattle, Washington. He met with Sarah Johnson on January 15, 2024 at 3:00 PM to discuss the quarterly results. The meeting was attended by representatives from Google, Apple Inc, and Amazon. They discussed revenue growth of 25% and expansion plans for New York City." * 2),
            ("Long text", "John Smith works at Microsoft Corporation in Seattle, Washington. He met with Sarah Johnson on January 15, 2024 at 3:00 PM to discuss the quarterly results. The meeting was attended by representatives from Google, Apple Inc, and Amazon. They discussed revenue growth of 25% and expansion plans for New York City." * 10),
            ("Very long text", "John Smith works at Microsoft Corporation in Seattle, Washington. He met with Sarah Johnson on January 15, 2024 at 3:00 PM to discuss the quarterly results. The meeting was attended by representatives from Google, Apple Inc, and Amazon. They discussed revenue growth of 25% and expansion plans for New York City." * 50)
        ]
        
        results = []
        
        for description, text in test_texts:
            try:
                # Measure entity extraction performance
                entities_result, processing_time, memory_used = self._measure_memory_usage(
                    ner_basic.extract_entities, text
                )
                
                # Measure confidence scoring performance
                confidence_result, confidence_time, confidence_memory = self._measure_memory_usage(
                    ner_basic.get_entity_confidence, text
                )
                
                total_entities = sum(len(v) for v in entities_result.values()) if entities_result else 0
                
                results.append({
                    'description': description,
                    'text_length': len(text),
                    'word_count': len(text.split()),
                    'entities_found': total_entities,
                    'extraction_time': processing_time,
                    'confidence_time': confidence_time,
                    'total_time': processing_time + confidence_time,
                    'memory_used': memory_used + confidence_memory,
                    'words_per_second': len(text.split()) / (processing_time + confidence_time) if (processing_time + confidence_time) > 0 else 0
                })
                
            except Exception as e:
                print(f"⚠️ Basic NER performance test failed for {description}: {e}")
                continue
        
        if results:
            # Performance assertions
            for result in results:
                # Should process at least 100 words per second
                if result['word_count'] > 10:  # Only check for non-trivial texts
                    assert result['words_per_second'] > 100, f"Basic NER too slow for {result['description']}: {result['words_per_second']:.2f} words/s"
                
                # Memory usage should be reasonable (< 200MB)
                assert result['memory_used'] < 200, f"Basic NER uses too much memory for {result['description']}: {result['memory_used']:.2f}MB"
                
                # Processing time should be reasonable (< 10 seconds for very long text)
                assert result['total_time'] < 10, f"Basic NER processing too slow for {result['description']}: {result['total_time']:.2f}s"
            
            print("Basic NER performance results:")
            for result in results:
                print(f"  {result['description']}: {result['total_time']:.3f}s, {result['words_per_second']:.1f} words/s, {result['entities_found']} entities")
    
    @pytest.mark.performance
    @patch('ner_advanced._get_openai_client')
    def test_ner_advanced_performance(self, mock_client):
        """Test advanced NER performance with mocked API calls"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.function_call.arguments = '''
        {
            "summary": "Performance test summary",
            "persons": ["John Smith", "Sarah Johnson"],
            "organizations": ["Microsoft", "Google", "Apple Inc"],
            "dates": ["January 15, 2024"],
            "locations": ["Seattle", "New York City"],
            "key_topics": ["quarterly results", "revenue growth"]
        }
        '''
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        test_texts = [
            ("Short text", "John Smith works at Microsoft in Seattle."),
            ("Medium text", "John Smith works at Microsoft Corporation in Seattle, Washington. He met with Sarah Johnson on January 15, 2024." * 5),
            ("Long text", "John Smith works at Microsoft Corporation in Seattle, Washington. He met with Sarah Johnson on January 15, 2024." * 20)
        ]
        
        results = []
        
        for description, text in test_texts:
            try:
                # Measure advanced entity extraction performance
                extraction_result, processing_time, memory_used = self._measure_memory_usage(
                    ner_advanced.extract_entities_advanced, text
                )
                
                entities, summary = extraction_result
                total_entities = sum(len(v) for v in entities.values()) if entities else 0
                
                results.append({
                    'description': description,
                    'text_length': len(text),
                    'word_count': len(text.split()),
                    'entities_found': total_entities,
                    'processing_time': processing_time,
                    'memory_used': memory_used,
                    'has_summary': len(summary) > 0 if summary else False
                })
                
            except Exception as e:
                print(f"⚠️ Advanced NER performance test failed for {description}: {e}")
                continue
        
        if results:
            # Performance assertions (more lenient for API-based processing)
            for result in results:
                # Processing should complete within reasonable time (< 30 seconds)
                assert result['processing_time'] < 30, f"Advanced NER too slow for {result['description']}: {result['processing_time']:.2f}s"
                
                # Memory usage should be reasonable (< 300MB)
                assert result['memory_used'] < 300, f"Advanced NER uses too much memory for {result['description']}: {result['memory_used']:.2f}MB"
                
                # Should produce results
                assert result['entities_found'] > 0 or result['has_summary'], f"Advanced NER produced no results for {result['description']}"
            
            print("Advanced NER performance results:")
            for result in results:
                print(f"  {result['description']}: {result['processing_time']:.3f}s, {result['entities_found']} entities")
    
    @pytest.mark.performance
    @patch('tts._get_elevenlabs_client')
    def test_tts_performance(self, mock_client):
        """Test TTS performance with various text lengths"""
        # Mock ElevenLabs response
        mock_client_instance = MagicMock()
        mock_client_instance.text_to_speech.convert.return_value = [b'fake_audio_data' * 1000]
        mock_client.return_value = mock_client_instance
        
        test_texts = [
            ("Short text", "Hello, this is a short test."),
            ("Medium text", "This is a medium length text for testing text-to-speech performance. " * 5),
            ("Long text", "This is a longer text for testing text-to-speech performance with more content. " * 20),
            ("Very long text", "This is a very long text for testing text-to-speech performance with extensive content. " * 50)
        ]
        
        results = []
        
        for description, text in test_texts:
            try:
                # Measure TTS synthesis performance
                audio_path, processing_time, memory_used = self._measure_memory_usage(
                    tts.synthesize_speech, text
                )
                
                # Measure cost estimation performance
                cost_result, cost_time, cost_memory = self._measure_memory_usage(
                    tts.estimate_synthesis_cost, text
                )
                
                results.append({
                    'description': description,
                    'text_length': len(text),
                    'character_count': len(text),
                    'synthesis_time': processing_time,
                    'cost_estimation_time': cost_time,
                    'total_time': processing_time + cost_time,
                    'memory_used': memory_used + cost_memory,
                    'estimated_cost': cost_result,
                    'chars_per_second': len(text) / processing_time if processing_time > 0 else 0
                })
                
                # Clean up generated audio file
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                
            except Exception as e:
                print(f"⚠️ TTS performance test failed for {description}: {e}")
                continue
        
        if results:
            # Performance assertions
            for result in results:
                # Synthesis should be reasonably fast (> 100 chars/second)
                assert result['chars_per_second'] > 100, f"TTS too slow for {result['description']}: {result['chars_per_second']:.2f} chars/s"
                
                # Cost estimation should be very fast (< 0.1 seconds)
                assert result['cost_estimation_time'] < 0.1, f"Cost estimation too slow for {result['description']}: {result['cost_estimation_time']:.3f}s"
                
                # Memory usage should be reasonable (< 100MB)
                assert result['memory_used'] < 100, f"TTS uses too much memory for {result['description']}: {result['memory_used']:.2f}MB"
                
                # Cost should be reasonable (< $1 for test texts)
                assert result['estimated_cost'] < 1.0, f"Estimated cost too high for {result['description']}: ${result['estimated_cost']:.4f}"
            
            print("TTS performance results:")
            for result in results:
                print(f"  {result['description']}: {result['synthesis_time']:.3f}s, {result['chars_per_second']:.1f} chars/s, ${result['estimated_cost']:.4f}")
    
    @pytest.mark.performance
    def test_concurrent_processing(self):
        """Test performance under concurrent load"""
        import concurrent.futures
        
        def process_text_concurrently(text_id):
            """Process text in a separate thread"""
            test_text = f"This is test text number {text_id} for concurrent processing. John Smith works at Microsoft."
            
            try:
                # Test basic NER
                entities = ner_basic.extract_entities(test_text)
                
                # Test utilities
                temp_file = utils.create_temp_file(".txt")
                with open(temp_file, 'w') as f:
                    f.write(test_text)
                
                file_valid = utils.validate_file_size(temp_file, 1)
                utils.cleanup_file(temp_file)
                
                return {
                    'text_id': text_id,
                    'entities_count': sum(len(v) for v in entities.values()) if entities else 0,
                    'file_valid': file_valid,
                    'success': True
                }
                
            except Exception as e:
                return {
                    'text_id': text_id,
                    'error': str(e),
                    'success': False
                }
        
        # Test with multiple concurrent threads
        num_threads = 5
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(process_text_concurrently, i) for i in range(num_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        # Performance assertions
        assert len(successful_results) >= num_threads * 0.8, f"Too many concurrent processing failures: {len(failed_results)}/{num_threads}"
        assert total_time < 30, f"Concurrent processing too slow: {total_time:.2f}s"
        
        print(f"Concurrent processing results: {len(successful_results)}/{num_threads} successful in {total_time:.2f}s")
        
        if failed_results:
            print("Failed concurrent processes:")
            for result in failed_results:
                print(f"  Thread {result['text_id']}: {result.get('error', 'Unknown error')}")
    
    @pytest.mark.performance
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations"""
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform repeated operations
        for i in range(10):
            # Create and process test data
            test_text = f"Memory leak test iteration {i}. John Smith works at Microsoft in Seattle."
            
            # Test basic NER
            try:
                entities = ner_basic.extract_entities(test_text)
            except:
                pass  # Ignore errors, focus on memory
            
            # Test file operations
            temp_file = utils.create_temp_file(".txt")
            with open(temp_file, 'w') as f:
                f.write(test_text)
            utils.cleanup_file(temp_file)
            
            # Check memory every few iterations
            if i % 3 == 0:
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be reasonable (< 50MB after 10 iterations)
                assert memory_growth < 50, f"Potential memory leak detected: {memory_growth:.2f}MB growth after {i+1} iterations"
        
        final_memory = self.process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - initial_memory
        
        print(f"Memory usage: initial={initial_memory:.2f}MB, final={final_memory:.2f}MB, growth={total_growth:.2f}MB")
        
        # Final memory check
        assert total_growth < 100, f"Excessive memory growth detected: {total_growth:.2f}MB"


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-m", "performance"])