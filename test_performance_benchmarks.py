"""
Performance and benchmark tests for Whisper Advanced Integration
Tests processing speed, memory usage, and scalability
"""

import pytest
import asyncio
import time
import psutil
import threading
import tempfile
import os
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import components for testing
from whisper_advanced_processor import WhisperAdvancedProcessor, WhisperConfig, WhisperModel
from whisper_audio_preprocessor import AudioPreprocessor, AudioConfig, ProcessingMode

@pytest.fixture
def performance_config():
    """Configuration optimized for performance testing"""
    return WhisperConfig(
        model_size=WhisperModel.BASE,
        language="en",
        temperature=0.0,
        word_timestamps=False,  # Disable for faster processing
        enable_diarization=False
    )

@pytest.fixture
def fast_audio_config():
    """Audio configuration optimized for speed"""
    return AudioConfig(
        processing_mode=ProcessingMode.FAST,
        enable_noise_reduction=False,
        enable_enhancement=False,
        enable_normalization=True
    )

class PerformanceMonitor:
    """Monitor system performance during tests"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.cpu_usage = []
        self.memory_usage = []
        self.monitoring = False
        self.monitor_thread = None
    
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor)
        self.monitor_thread.start()
    
    def stop(self):
        """Stop monitoring"""
        self.end_time = time.time()
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor(self):
        """Monitor system resources"""
        while self.monitoring:
            try:
                self.cpu_usage.append(psutil.cpu_percent(interval=0.1))
                self.memory_usage.append(psutil.virtual_memory().percent)
            except:
                pass  # Ignore monitoring errors
            time.sleep(0.1)
    
    @property
    def duration(self):
        """Get total duration"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def avg_cpu_usage(self):
        """Get average CPU usage"""
        return sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
    
    @property
    def max_cpu_usage(self):
        """Get maximum CPU usage"""
        return max(self.cpu_usage) if self.cpu_usage else 0
    
    @property
    def avg_memory_usage(self):
        """Get average memory usage"""
        return sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
    
    @property
    def max_memory_usage(self):
        """Get maximum memory usage"""
        return max(self.memory_usage) if self.memory_usage else 0

@pytest.mark.performance
class TestProcessingSpeed:
    """Test processing speed benchmarks"""
    
    @patch('whisper.load_model')
    @patch('librosa.load')
    async def test_single_file_processing_speed(self, mock_load, mock_load_model, test_audio_samples, performance_config):
        """Test single file processing speed"""
        # Mock dependencies
        mock_audio_data = np.random.randn(16000 * 10)  # 10 seconds of audio
        mock_load.return_value = (mock_audio_data, 16000)
        
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'text': 'Performance test transcription result.',
            'language': 'en',
            'segments': []
        }
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        monitor = PerformanceMonitor()
        
        # Test different audio lengths
        test_cases = [
            ("short", 2.0),   # 2 seconds
            ("medium", 10.0), # 10 seconds
            ("long", 30.0)    # 30 seconds
        ]
        
        results = {}
        
        for case_name, duration in test_cases:
            # Create test audio
            audio_file = test_audio_samples.get(case_name)
            if not audio_file:
                continue
            
            monitor.start()
            start_time = time.time()
            
            result = await processor.transcribe(audio_file, performance_config)
            
            end_time = time.time()
            monitor.stop()
            
            processing_time = end_time - start_time
            results[case_name] = {
                'duration': duration,
                'processing_time': processing_time,
                'real_time_factor': processing_time / duration,
                'avg_cpu': monitor.avg_cpu_usage,
                'max_cpu': monitor.max_cpu_usage,
                'avg_memory': monitor.avg_memory_usage,
                'max_memory': monitor.max_memory_usage
            }
            
            # Performance assertions
            assert processing_time < duration * 2  # Should be faster than 2x real-time
            assert result is not None
            
            print(f"\n{case_name.upper()} AUDIO ({duration}s):")
            print(f"  Processing time: {processing_time:.2f}s")
            print(f"  Real-time factor: {processing_time/duration:.2f}x")
            print(f"  CPU usage: {monitor.avg_cpu_usage:.1f}% avg, {monitor.max_cpu_usage:.1f}% max")
            print(f"  Memory usage: {monitor.avg_memory_usage:.1f}% avg, {monitor.max_memory_usage:.1f}% max")
        
        # Overall performance check
        if results:
            avg_rtf = sum(r['real_time_factor'] for r in results.values()) / len(results)
            assert avg_rtf < 1.5  # Average should be better than 1.5x real-time
    
    @patch('whisper.load_model')
    @patch('librosa.load')
    async def test_batch_processing_speed(self, mock_load, mock_load_model, test_audio_samples, performance_config):
        """Test batch processing speed and efficiency"""
        # Mock dependencies
        mock_audio_data = np.random.randn(16000 * 5)  # 5 seconds of audio
        mock_load.return_value = (mock_audio_data, 16000)
        
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'text': 'Batch processing test.',
            'language': 'en',
            'segments': []
        }
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        
        # Test different batch sizes
        batch_sizes = [1, 3, 5]
        audio_files = [test_audio_samples.get('short', 'dummy.wav')] * 5
        
        for batch_size in batch_sizes:
            files_to_process = audio_files[:batch_size]
            
            monitor = PerformanceMonitor()
            monitor.start()
            start_time = time.time()
            
            # Process files concurrently
            tasks = []
            for audio_file in files_to_process:
                task = processor.transcribe(audio_file, performance_config)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            monitor.stop()
            
            total_time = end_time - start_time
            avg_time_per_file = total_time / batch_size
            
            print(f"\nBATCH SIZE {batch_size}:")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Avg time per file: {avg_time_per_file:.2f}s")
            print(f"  CPU usage: {monitor.avg_cpu_usage:.1f}% avg, {monitor.max_cpu_usage:.1f}% max")
            print(f"  Memory usage: {monitor.avg_memory_usage:.1f}% avg, {monitor.max_memory_usage:.1f}% max")
            
            # Verify all files processed successfully
            assert len(results) == batch_size
            for result in results:
                assert result is not None
    
    @patch('librosa.load')
    @patch('noisereduce.reduce_noise')
    def test_audio_preprocessing_speed(self, mock_noise_reduce, mock_load, test_audio_samples, fast_audio_config):
        """Test audio preprocessing speed"""
        # Mock dependencies
        mock_audio_data = np.random.randn(16000 * 10)  # 10 seconds
        mock_load.return_value = (mock_audio_data, 16000)
        mock_noise_reduce.return_value = mock_audio_data
        
        preprocessor = AudioPreprocessor()
        
        # Test different processing modes
        modes = [ProcessingMode.FAST, ProcessingMode.BALANCED, ProcessingMode.HIGH_QUALITY]
        
        for mode in modes:
            config = AudioConfig(processing_mode=mode)
            
            monitor = PerformanceMonitor()
            monitor.start()
            start_time = time.time()
            
            result = preprocessor.preprocess_audio(
                test_audio_samples.get('medium', 'dummy.wav'), 
                config
            )
            
            end_time = time.time()
            monitor.stop()
            
            processing_time = end_time - start_time
            
            print(f"\nPREPROCESSING MODE {mode.value}:")
            print(f"  Processing time: {processing_time:.2f}s")
            print(f"  CPU usage: {monitor.avg_cpu_usage:.1f}% avg")
            print(f"  Memory usage: {monitor.avg_memory_usage:.1f}% avg")
            
            # Performance assertions based on mode
            if mode == ProcessingMode.FAST:
                assert processing_time < 2.0  # Fast mode should be very quick
            elif mode == ProcessingMode.BALANCED:
                assert processing_time < 5.0  # Balanced mode should be reasonable
            # High quality mode may take longer
            
            assert result is not None
            assert result.processing_time > 0

@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage and resource management"""
    
    @patch('whisper.load_model')
    def test_model_memory_usage(self, mock_load_model):
        """Test memory usage during model loading and caching"""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        
        # Monitor memory before loading
        initial_memory = psutil.virtual_memory().used
        
        # Load different model sizes
        configs = [
            WhisperConfig(model_size=WhisperModel.TINY),
            WhisperConfig(model_size=WhisperModel.BASE),
            WhisperConfig(model_size=WhisperModel.SMALL)
        ]
        
        for config in configs:
            memory_before = psutil.virtual_memory().used
            
            # Load model
            processor._load_model(config)
            
            memory_after = psutil.virtual_memory().used
            memory_increase = memory_after - memory_before
            
            print(f"\nMODEL {config.model_size.value}:")
            print(f"  Memory increase: {memory_increase / 1024 / 1024:.1f} MB")
            
            # Memory should not increase excessively (mocked, so minimal increase expected)
            assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
        
        # Check model caching
        assert len(processor.model_cache) == len(configs)
        
        # Memory should not grow linearly with cached models (due to mocking)
        final_memory = psutil.virtual_memory().used
        total_increase = final_memory - initial_memory
        print(f"\nTOTAL MEMORY INCREASE: {total_increase / 1024 / 1024:.1f} MB")
    
    @patch('whisper.load_model')
    @patch('librosa.load')
    async def test_concurrent_processing_memory(self, mock_load, mock_load_model, test_audio_samples):
        """Test memory usage during concurrent processing"""
        # Mock dependencies
        mock_audio_data = np.random.randn(16000 * 5)
        mock_load.return_value = (mock_audio_data, 16000)
        
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'text': 'Concurrent processing test.',
            'language': 'en',
            'segments': []
        }
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        config = WhisperConfig(model_size=WhisperModel.BASE)
        
        initial_memory = psutil.virtual_memory().used
        
        # Run multiple concurrent transcriptions
        tasks = []
        for i in range(5):
            task = processor.transcribe(
                test_audio_samples.get('short', 'dummy.wav'), 
                config
            )
            tasks.append(task)
        
        # Monitor memory during processing
        peak_memory = initial_memory
        
        async def monitor_memory():
            nonlocal peak_memory
            while tasks:
                current_memory = psutil.virtual_memory().used
                peak_memory = max(peak_memory, current_memory)
                await asyncio.sleep(0.1)
        
        # Start monitoring and processing
        monitor_task = asyncio.create_task(monitor_memory())
        results = await asyncio.gather(*tasks)
        monitor_task.cancel()
        
        final_memory = psutil.virtual_memory().used
        memory_increase = peak_memory - initial_memory
        
        print(f"\nCONCURRENT PROCESSING:")
        print(f"  Peak memory increase: {memory_increase / 1024 / 1024:.1f} MB")
        print(f"  Final memory increase: {(final_memory - initial_memory) / 1024 / 1024:.1f} MB")
        
        # Verify all tasks completed
        assert len(results) == 5
        for result in results:
            assert result is not None
        
        # Memory increase should be reasonable
        assert memory_increase < 500 * 1024 * 1024  # Less than 500MB increase

@pytest.mark.performance
class TestScalability:
    """Test system scalability and load handling"""
    
    @patch('whisper.load_model')
    @patch('librosa.load')
    async def test_load_handling(self, mock_load, mock_load_model, test_audio_samples):
        """Test system behavior under load"""
        # Mock dependencies
        mock_audio_data = np.random.randn(16000 * 3)  # 3 seconds
        mock_load.return_value = (mock_audio_data, 16000)
        
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'text': 'Load test transcription.',
            'language': 'en',
            'segments': []
        }
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        config = WhisperConfig(model_size=WhisperModel.BASE)
        
        # Test increasing load levels
        load_levels = [5, 10, 20]
        
        for load_level in load_levels:
            print(f"\nTesting load level: {load_level} concurrent requests")
            
            monitor = PerformanceMonitor()
            monitor.start()
            start_time = time.time()
            
            # Create concurrent tasks
            tasks = []
            for i in range(load_level):
                task = processor.transcribe(
                    test_audio_samples.get('short', 'dummy.wav'),
                    config
                )
                tasks.append(task)
            
            # Process all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            monitor.stop()
            
            # Analyze results
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful
            total_time = end_time - start_time
            
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Successful: {successful}/{load_level}")
            print(f"  Failed: {failed}/{load_level}")
            print(f"  Avg CPU: {monitor.avg_cpu_usage:.1f}%")
            print(f"  Max CPU: {monitor.max_cpu_usage:.1f}%")
            print(f"  Avg Memory: {monitor.avg_memory_usage:.1f}%")
            print(f"  Max Memory: {monitor.max_memory_usage:.1f}%")
            
            # Performance assertions
            assert successful >= load_level * 0.9  # At least 90% success rate
            assert monitor.max_cpu_usage < 95  # CPU should not max out
            assert monitor.max_memory_usage < 90  # Memory should not max out
    
    @patch('whisper.load_model')
    @patch('librosa.load')
    def test_throughput_measurement(self, mock_load, mock_load_model, test_audio_samples):
        """Measure system throughput"""
        # Mock dependencies
        mock_audio_data = np.random.randn(16000 * 2)  # 2 seconds
        mock_load.return_value = (mock_audio_data, 16000)
        
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'text': 'Throughput test.',
            'language': 'en',
            'segments': []
        }
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        config = WhisperConfig(model_size=WhisperModel.BASE)
        
        # Measure throughput over time
        duration = 10  # seconds
        start_time = time.time()
        completed_tasks = 0
        
        async def process_continuously():
            nonlocal completed_tasks
            while time.time() - start_time < duration:
                try:
                    await processor.transcribe(
                        test_audio_samples.get('short', 'dummy.wav'),
                        config
                    )
                    completed_tasks += 1
                except:
                    pass  # Ignore errors for throughput test
        
        # Run throughput test
        import asyncio
        asyncio.run(process_continuously())
        
        actual_duration = time.time() - start_time
        throughput = completed_tasks / actual_duration
        
        print(f"\nTHROUGHPUT TEST:")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Completed tasks: {completed_tasks}")
        print(f"  Throughput: {throughput:.2f} tasks/second")
        
        # Throughput should be reasonable
        assert throughput > 0.1  # At least 0.1 tasks per second
        assert completed_tasks > 0

@pytest.mark.performance
class TestResourceOptimization:
    """Test resource optimization and efficiency"""
    
    @patch('whisper.load_model')
    def test_model_caching_efficiency(self, mock_load_model):
        """Test model caching reduces loading time"""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        config = WhisperConfig(model_size=WhisperModel.BASE)
        
        # First load (should call load_model)
        start_time = time.time()
        model1 = processor._load_model(config)
        first_load_time = time.time() - start_time
        
        # Second load (should use cache)
        start_time = time.time()
        model2 = processor._load_model(config)
        second_load_time = time.time() - start_time
        
        print(f"\nMODEL CACHING:")
        print(f"  First load time: {first_load_time:.4f}s")
        print(f"  Second load time: {second_load_time:.4f}s")
        print(f"  Cache hit speedup: {first_load_time/second_load_time:.1f}x")
        
        # Verify caching works
        assert model1 is model2  # Same object from cache
        assert second_load_time < first_load_time  # Faster from cache
        assert mock_load_model.call_count == 1  # Only called once
    
    @patch('librosa.load')
    def test_audio_processing_optimization(self, mock_load, test_audio_samples):
        """Test audio processing optimization"""
        mock_audio_data = np.random.randn(16000 * 5)
        mock_load.return_value = (mock_audio_data, 16000)
        
        preprocessor = AudioPreprocessor()
        
        # Test different optimization levels
        configs = [
            AudioConfig(processing_mode=ProcessingMode.FAST),
            AudioConfig(processing_mode=ProcessingMode.BALANCED),
            AudioConfig(processing_mode=ProcessingMode.HIGH_QUALITY)
        ]
        
        processing_times = {}
        
        for config in configs:
            start_time = time.time()
            
            result = preprocessor.preprocess_audio(
                test_audio_samples.get('medium', 'dummy.wav'),
                config
            )
            
            processing_time = time.time() - start_time
            processing_times[config.processing_mode] = processing_time
            
            assert result is not None
        
        # Verify optimization levels
        fast_time = processing_times[ProcessingMode.FAST]
        balanced_time = processing_times[ProcessingMode.BALANCED]
        hq_time = processing_times[ProcessingMode.HIGH_QUALITY]
        
        print(f"\nPROCESSING OPTIMIZATION:")
        print(f"  Fast mode: {fast_time:.3f}s")
        print(f"  Balanced mode: {balanced_time:.3f}s")
        print(f"  High quality mode: {hq_time:.3f}s")
        
        # Fast should be fastest, high quality should be slowest
        assert fast_time <= balanced_time <= hq_time

if __name__ == "__main__":
    # Run performance tests
    pytest.main([
        __file__,
        "-v",
        "-m", "performance",
        "--tb=short",
        "--durations=10"
    ])