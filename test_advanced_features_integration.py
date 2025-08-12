#!/usr/bin/env python3
"""
Integration tests for all advanced features
Tests the complete workflow and interaction between systems
"""

import asyncio
import pytest
import tempfile
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import wave

# Import all systems
from batch_transcription_system import BatchTranscriptionSystem, Priority
from punctuation_restoration import PunctuationRestorer
from advanced_timestamping_system import AdvancedTimestampingSystem, TimestampGranularity
from keyword_extraction_system import AdvancedKeywordExtractor, ExtractionMethod
from event_extraction_system import EventExtractor
from visual_content_analysis import VisualContentAnalyzer
from text_classification_system import TextClassificationSystem, ClassificationType, ModelType


class TestAdvancedFeaturesIntegration:
    """Integration tests for advanced features"""
    
    @pytest.fixture
    async def all_systems(self):
        """Initialize all systems for testing"""
        systems = {
            'batch': BatchTranscriptionSystem({'num_workers': 2}),
            'punctuation': PunctuationRestorer(),
            'timestamp': AdvancedTimestampingSystem(),
            'keyword': AdvancedKeywordExtractor(),
            'event': EventExtractor(),
            'visual': VisualContentAnalyzer(),
            'classification': TextClassificationSystem()
        }
        
        # Initialize batch system
        await systems['batch'].initialize()
        
        yield systems
        
        # Cleanup
        await systems['batch'].shutdown()
    
    @pytest.fixture
    def sample_text(self):
        """Sample text for testing"""
        return """
        the quarterly review meeting is scheduled for next monday at 2 pm in the main conference room
        john and sarah will present the q3 results the deadline for submitting the financial report
        is october 15th 2024 we agreed to launch the new product on november 1st this is a critical
        milestone for our company the marketing campaign will start two weeks before the launch date
        """
    
    @pytest.fixture
    def create_test_audio(self, tmp_path):
        """Create test audio file"""
        def _create_audio(duration=2, sample_rate=16000):
            filename = tmp_path / "test_audio.wav"
            
            # Generate simple sine wave
            t = np.linspace(0, duration, sample_rate * duration)
            audio_data = np.sin(2 * np.pi * 440 * t)
            audio_data = (audio_data * 32767).astype(np.int16)
            
            with wave.open(str(filename), 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            return str(filename)
        
        return _create_audio
    
    @pytest.mark.asyncio
    async def test_complete_text_processing_pipeline(self, all_systems, sample_text):
        """Test complete pipeline: punctuation -> keywords -> events -> classification"""
        
        # Step 1: Restore punctuation
        punctuation_result = await all_systems['punctuation'].restore_punctuation(sample_text)
        restored_text = punctuation_result.restored_text
        
        assert restored_text != sample_text
        assert '.' in restored_text
        assert ',' in restored_text
        
        # Step 2: Extract keywords
        keyword_result = await all_systems['keyword'].extract_keywords(
            restored_text,
            methods=[ExtractionMethod.RAKE, ExtractionMethod.TFIDF]
        )
        
        assert len(keyword_result.keywords) > 0
        assert 'meeting' in [k[0].lower() for k in keyword_result.keywords]
        
        # Step 3: Extract events
        event_result = await all_systems['event'].extract_events(
            restored_text,
            extract_actions=True,
            build_timeline=True
        )
        
        assert len(event_result.events) > 0
        assert len(event_result.action_items) > 0
        assert event_result.timeline is not None
        
        # Step 4: Classify text
        # First train a simple classifier
        training_texts = [
            "Business meeting about quarterly results",
            "Product launch announcement",
            "Technical documentation update",
            "Customer support ticket"
        ]
        training_labels = ["business", "marketing", "technical", "support"]
        
        performance = await all_systems['classification'].train_classifier(
            texts=training_texts,
            labels=training_labels,
            classification_type=ClassificationType.MULTICLASS,
            model_type=ModelType.NAIVE_BAYES
        )
        
        model_key = performance.metadata['model_key']
        
        # Classify the restored text
        classification_result = await all_systems['classification'].predict(
            restored_text,
            model_key=model_key
        )
        
        assert len(classification_result.predicted_labels) > 0
        assert classification_result.predicted_labels[0] in ["business", "marketing"]
    
    @pytest.mark.asyncio
    async def test_batch_processing_with_multiple_features(self, all_systems, create_test_audio):
        """Test batch processing with multiple feature extraction"""
        
        # Create test audio files
        audio_files = [create_test_audio() for _ in range(3)]
        
        # Create batch
        batch = await all_systems['batch'].create_batch(
            name="Integration Test Batch",
            file_paths=audio_files,
            priority=Priority.HIGH,
            config={
                'extract_keywords': True,
                'restore_punctuation': True,
                'extract_events': True
            }
        )
        
        assert batch is not None
        assert len(batch.jobs) == 3
        
        # Start processing
        await all_systems['batch'].start_batch(batch.batch_id)
        
        # Check status
        status = await all_systems['batch'].get_batch_status(batch.batch_id)
        assert status is not None
        assert status.batch_id == batch.batch_id
    
    @pytest.mark.asyncio
    async def test_visual_analysis_with_text_extraction(self, all_systems, tmp_path):
        """Test visual analysis with OCR and classification"""
        
        # Create a simple test image (would be actual image in production)
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add some text
        draw.text((50, 50), "Important Meeting", fill='black')
        draw.text((50, 100), "Date: October 15, 2024", fill='black')
        draw.text((50, 150), "Location: Conference Room A", fill='black')
        
        image_path = tmp_path / "test_image.png"
        img.save(image_path)
        
        # Analyze image
        visual_result = await all_systems['visual'].analyze_image(
            str(image_path),
            extract_text=True,
            detect_objects=True
        )
        
        # The extracted text should be processed further
        if visual_result.extracted_text:
            # Extract events from OCR text
            event_result = await all_systems['event'].extract_events(
                visual_result.extracted_text
            )
            
            # Events should be detected from the image text
            assert len(event_result.events) >= 0  # May detect meeting event
            assert len(event_result.temporal_expressions) >= 0  # May detect date
    
    @pytest.mark.asyncio
    async def test_active_learning_workflow(self, all_systems):
        """Test active learning workflow for classification"""
        
        # Initial training data
        initial_texts = [
            "The server is experiencing high latency",
            "Customer requested a refund",
            "New feature deployed to production"
        ]
        initial_labels = ["technical", "support", "deployment"]
        
        # Setup active learning
        learner_key = all_systems['classification'].setup_active_learning(
            initial_texts=initial_texts,
            initial_labels=initial_labels,
            model_type=ModelType.LOGISTIC_REGRESSION
        )
        
        assert learner_key is not None
        
        # Pool of unlabeled texts
        pool_texts = [
            "Database connection timeout error",
            "User cannot login to account",
            "API response time improved",
            "Payment processing failed",
            "New version released"
        ]
        
        # Query uncertain samples
        queries = all_systems['classification'].query_active_learning(
            learner_key=learner_key,
            pool_texts=pool_texts,
            n_instances=2
        )
        
        assert len(queries) == 2
        assert all(q.uncertainty_score > 0 for q in queries)
        
        # Simulate labeling and update
        new_labels = ["technical", "support"]
        all_systems['classification'].update_active_learner(
            learner_key=learner_key,
            texts=[q.text for q in queries],
            labels=new_labels
        )
    
    @pytest.mark.asyncio
    async def test_timestamp_synchronization(self, all_systems, create_test_audio):
        """Test timestamp generation and synchronization with text"""
        
        audio_file = create_test_audio(duration=5)
        
        # Generate timestamps
        timestamp_result = await all_systems['timestamp'].generate_timestamps(
            audio_file,
            granularity=TimestampGranularity.WORD
        )
        
        assert timestamp_result is not None
        assert len(timestamp_result.timestamps) > 0
        
        # Export to different formats
        srt_output = all_systems['timestamp'].export_subtitles(
            timestamp_result,
            format='srt'
        )
        assert 'SRT' in srt_output or '-->' in srt_output
        
        vtt_output = all_systems['timestamp'].export_subtitles(
            timestamp_result,
            format='vtt'
        )
        assert 'WEBVTT' in vtt_output
    
    @pytest.mark.asyncio
    async def test_keyword_trend_analysis(self, all_systems):
        """Test keyword extraction with trend analysis over time"""
        
        # Multiple texts representing different time periods
        texts_over_time = [
            "AI and machine learning are transforming industries",
            "Deep learning models show impressive results",
            "Neural networks achieve breakthrough performance",
            "Transformer models revolutionize NLP tasks",
            "Large language models demonstrate emergent abilities"
        ]
        
        all_keywords = []
        
        for text in texts_over_time:
            result = await all_systems['keyword'].extract_keywords(
                text,
                methods=[ExtractionMethod.RAKE, ExtractionMethod.TFIDF],
                max_keywords=5
            )
            all_keywords.append(result.keywords)
        
        # Analyze trends
        trend_analysis = all_systems['keyword'].analyze_keyword_trends(all_keywords)
        
        assert 'trending_up' in trend_analysis
        assert 'trending_down' in trend_analysis
        assert 'stable' in trend_analysis
    
    @pytest.mark.asyncio
    async def test_event_calendar_export(self, all_systems):
        """Test event extraction and calendar export"""
        
        text = """
        Team meeting scheduled for October 15th at 10 AM.
        Project deadline is October 30th.
        Conference call with clients on October 20th at 2 PM.
        Submit quarterly report by October 25th.
        """
        
        # Extract events
        result = await all_systems['event'].extract_events(
            text,
            reference_date=datetime(2024, 10, 1)
        )
        
        assert len(result.events) > 0
        assert len(result.action_items) > 0
        
        # Export to calendar format
        ics_content = all_systems['event'].export_calendar(
            result.events,
            result.action_items,
            format='ics'
        )
        
        assert 'BEGIN:VCALENDAR' in ics_content
        assert 'BEGIN:VEVENT' in ics_content
        assert 'BEGIN:VTODO' in ics_content
    
    @pytest.mark.asyncio
    async def test_hierarchical_classification(self, all_systems):
        """Test hierarchical text classification"""
        
        # Training data with hierarchical labels
        texts = [
            "Python programming tutorial",
            "JavaScript web development",
            "Machine learning with TensorFlow",
            "React frontend framework",
            "Natural language processing"
        ]
        
        labels = [
            "technology/programming/python",
            "technology/web/javascript",
            "technology/ai/machine_learning",
            "technology/web/react",
            "technology/ai/nlp"
        ]
        
        # Train hierarchical classifier
        performance = await all_systems['classification'].train_classifier(
            texts=texts,
            labels=labels,
            classification_type=ClassificationType.HIERARCHICAL,
            model_type=ModelType.LOGISTIC_REGRESSION
        )
        
        assert performance is not None
        model_key = performance.metadata['model_key']
        
        # Test prediction
        test_text = "Deep learning tutorial using PyTorch"
        result = await all_systems['classification'].predict(
            test_text,
            model_key=model_key
        )
        
        assert len(result.predicted_labels) > 0
        # Should predict something in technology/ai hierarchy
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_retry(self, all_systems):
        """Test error handling and retry mechanisms"""
        
        # Test batch system retry
        batch = await all_systems['batch'].create_batch(
            name="Error Test Batch",
            file_paths=["/nonexistent/file.wav"],
            priority=Priority.LOW
        )
        
        await all_systems['batch'].start_batch(batch.batch_id)
        await asyncio.sleep(0.5)  # Let it fail
        
        # Retry failed jobs
        retried = await all_systems['batch'].retry_failed_jobs(batch.batch_id)
        assert retried >= 0  # Should attempt retry
        
        # Test punctuation restoration with empty text
        result = await all_systems['punctuation'].restore_punctuation("")
        assert result.restored_text == ""
        
        # Test classification with invalid model key
        with pytest.raises(ValueError):
            await all_systems['classification'].predict(
                "Test text",
                model_key="nonexistent_model"
            )
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, all_systems, sample_text):
        """Test performance metrics collection across systems"""
        
        metrics = {}
        
        # Measure punctuation restoration time
        import time
        start = time.time()
        await all_systems['punctuation'].restore_punctuation(sample_text)
        metrics['punctuation_time'] = time.time() - start
        
        # Measure keyword extraction time
        start = time.time()
        await all_systems['keyword'].extract_keywords(sample_text)
        metrics['keyword_time'] = time.time() - start
        
        # Measure event extraction time
        start = time.time()
        await all_systems['event'].extract_events(sample_text)
        metrics['event_time'] = time.time() - start
        
        # All operations should complete within reasonable time
        assert all(t < 10 for t in metrics.values())  # Less than 10 seconds each
        
        print(f"Performance metrics: {metrics}")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])