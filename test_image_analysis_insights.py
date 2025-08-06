#!/usr/bin/env python3
"""
Task 78: Image Analysis and Insights Testing Suite
Comprehensive tests for the Image Analysis and Insights System
"""

import pytest
import numpy as np
import cv2
import tempfile
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import our system
from image_analysis_insights_system import (
    ImageAnalysisInsightsSystem,
    ComprehensiveImageInsights,
    ColorAnalysis,
    CompositionAnalysis,
    ContentAnalysis,
    QualityMetrics,
    SemanticInsights
)

class TestImageAnalysisInsightsSystem:
    """Test suite for Image Analysis and Insights System"""
    
    @pytest.fixture
    def system(self):
        """Create system instance for testing"""
        return ImageAnalysisInsightsSystem(use_gpu=False)
    
    @pytest.fixture
    def sample_image(self):
        """Generate sample test image"""
        # Create a simple test image
        image = np.zeros((400, 600, 3), dtype=np.uint8)
        
        # Add some content
        cv2.rectangle(image, (50, 50), (200, 150), (255, 0, 0), -1)  # Blue rectangle
        cv2.circle(image, (400, 200), 80, (0, 255, 0), -1)  # Green circle
        cv2.line(image, (0, 300), (600, 350), (0, 0, 255), 5)  # Red line
        
        # Add some noise for texture
        noise = np.random.randint(0, 50, image.shape, dtype=np.uint8)
        image = cv2.add(image, noise)
        
        return image
    
    @pytest.fixture
    def complex_image(self):
        """Generate more complex test image"""
        image = np.zeros((800, 1200, 3), dtype=np.uint8)
        
        # Gradient background
        for i in range(800):
            image[i, :] = [int(i/800*255), 100, 200 - int(i/800*100)]
        
        # Add geometric shapes
        cv2.rectangle(image, (100, 100), (300, 300), (255, 255, 0), -1)
        cv2.circle(image, (600, 400), 120, (255, 0, 255), -1)
        cv2.ellipse(image, (900, 200), (150, 80), 45, 0, 360, (0, 255, 255), -1)
        
        # Add some text-like regions
        cv2.rectangle(image, (200, 500), (800, 600), (255, 255, 255), -1)
        cv2.rectangle(image, (220, 520), (780, 580), (0, 0, 0), -1)
        
        return image

    def test_system_initialization(self, system):
        """Test system initialization"""
        assert isinstance(system, ImageAnalysisInsightsSystem)
        assert hasattr(system, 'use_gpu')
        assert hasattr(system, 'models_loaded')
    
    def test_basic_image_analysis(self, system, sample_image):
        """Test basic image analysis functionality"""
        insights = system.analyze_image(sample_image)
        
        assert isinstance(insights, ComprehensiveImageInsights)
        assert insights.processing_time > 0
        assert insights.analysis_timestamp is not None
        
        # Check all analysis components exist
        assert isinstance(insights.color_analysis, ColorAnalysis)
        assert isinstance(insights.composition_analysis, CompositionAnalysis)
        assert isinstance(insights.content_analysis, ContentAnalysis)
        assert isinstance(insights.quality_metrics, QualityMetrics)
        assert isinstance(insights.semantic_insights, SemanticInsights)
    
    def test_color_analysis(self, system, sample_image):
        """Test color analysis functionality"""
        insights = system.analyze_image(sample_image)
        color_analysis = insights.color_analysis
        
        # Check dominant colors
        assert len(color_analysis.dominant_colors) > 0
        assert len(color_analysis.dominant_colors) <= 10
        
        # Check color properties
        assert color_analysis.color_temperature in ['warm', 'cool', 'neutral']
        assert color_analysis.brightness_level in ['very_dark', 'dark', 'medium', 'bright', 'very_bright']
        assert color_analysis.contrast_level in ['very_low', 'low', 'medium', 'high', 'very_high']
        assert color_analysis.saturation_level in ['very_low', 'low', 'medium', 'high', 'very_high']
        
        # Check diversity score
        assert 0 <= color_analysis.color_diversity <= 1
    
    def test_composition_analysis(self, system, sample_image):
        """Test composition analysis functionality"""
        insights = system.analyze_image(sample_image)
        composition = insights.composition_analysis
        
        # Check aspect ratio
        assert composition.aspect_ratio > 0
        
        # Check orientation
        assert composition.orientation in ['landscape', 'portrait', 'square']
        
        # Check scores
        assert 0 <= composition.rule_of_thirds_alignment <= 1
        assert 0 <= composition.symmetry_score <= 1
        assert 0 <= composition.balance_score <= 1
        
        # Check focal points
        assert isinstance(composition.focal_points, list)
        
        # Check depth of field estimate
        assert composition.depth_of_field_estimate in ['shallow', 'medium', 'deep']
    
    def test_content_analysis(self, system, sample_image):
        """Test content analysis functionality"""
        insights = system.analyze_image(sample_image)
        content = insights.content_analysis
        
        # Check scene type
        assert content.scene_type is not None
        
        # Check complexity
        assert content.scene_complexity in ['simple', 'moderate', 'complex', 'very_complex']
        
        # Check face detection
        assert isinstance(content.faces_detected, int)
        assert content.faces_detected >= 0
        
        # Check subjects and objects
        assert isinstance(content.primary_subjects, list)
        assert isinstance(content.object_count, dict)
        
        # Check emotional tone
        assert content.emotional_tone in ['positive', 'negative', 'neutral', 'mixed']
        
        # Check text regions
        assert isinstance(content.text_regions, list)
    
    def test_quality_metrics(self, system, sample_image):
        """Test quality assessment functionality"""
        insights = system.analyze_image(sample_image)
        quality = insights.quality_metrics
        
        # Check sharpness score
        assert 0 <= quality.sharpness_score <= 100
        
        # Check quality levels
        assert quality.exposure_quality in ['underexposed', 'optimal', 'overexposed']
        assert quality.white_balance in ['poor', 'fair', 'good']
        assert quality.noise_level in ['very_low', 'low', 'medium', 'high', 'very_high']
        assert quality.resolution_quality in ['low', 'medium', 'high']
        assert quality.overall_quality in ['poor', 'fair', 'good', 'excellent']
        
        # Check technical score
        assert 0 <= quality.technical_score <= 100
        
        # Check compression artifacts
        assert isinstance(quality.compression_artifacts, bool)
    
    def test_semantic_insights(self, system, sample_image):
        """Test semantic analysis functionality"""
        insights = system.analyze_image(sample_image)
        semantic = insights.semantic_insights
        
        # Check scene description
        assert semantic.scene_description is not None
        assert len(semantic.scene_description) > 0
        
        # Check themes and categories
        assert isinstance(semantic.key_themes, list)
        assert isinstance(semantic.content_categories, list)
        
        # Check commercial potential
        assert semantic.commercial_potential in ['low', 'medium', 'high', 'very_high']
        
        # Check emotional impact
        assert semantic.emotional_impact is not None
        
        # Check target audience
        assert isinstance(semantic.target_audience, list)
        
        # Check stock photo tags
        assert isinstance(semantic.similar_stock_tags, list)
        
        # Check accessibility description
        assert semantic.accessibility_description is not None
    
    def test_confidence_scores(self, system, sample_image):
        """Test confidence scoring"""
        insights = system.analyze_image(sample_image)
        confidence = insights.confidence_scores
        
        # Check that all required confidence scores exist
        required_scores = ['color', 'composition', 'content', 'quality', 'semantic', 'overall']
        for score_type in required_scores:
            assert score_type in confidence
            assert 0 <= confidence[score_type] <= 1
    
    def test_batch_analysis(self, system, sample_image, complex_image):
        """Test batch analysis functionality"""
        images = [sample_image, complex_image]
        results = system.batch_analyze(images)
        
        assert len(results) == 2
        for result in results:
            assert isinstance(result, ComprehensiveImageInsights)
    
    def test_comparative_analysis(self, system, sample_image, complex_image):
        """Test comparative analysis functionality"""
        comparison = system.compare_images(sample_image, complex_image)
        
        assert 'image_1' in comparison
        assert 'image_2' in comparison
        assert 'differences' in comparison
        assert 'similarities' in comparison
        
        # Check quality comparison
        if 'quality_score' in comparison['differences']:
            quality_diff = comparison['differences']['quality_score']
            assert 'difference' in quality_diff
            assert 'better_image' in quality_diff
    
    def test_analysis_options(self, system, sample_image):
        """Test different analysis options"""
        # Test with specific sections
        options = {
            'include_sections': ['color', 'quality'],
            'detailed_analysis': False
        }
        
        insights = system.analyze_image(sample_image, options)
        assert isinstance(insights, ComprehensiveImageInsights)
    
    def test_export_functionality(self, system, sample_image):
        """Test export functionality"""
        insights = system.analyze_image(sample_image)
        
        # Test JSON export
        json_export = system.export_analysis(insights, 'json')
        assert isinstance(json_export, (str, dict))
        
        # Test CSV export
        csv_export = system.export_analysis(insights, 'csv')
        assert isinstance(csv_export, str)
        
        # Test HTML export
        html_export = system.export_analysis(insights, 'html')
        assert isinstance(html_export, str)
        assert '<html>' in html_export.lower()
    
    def test_file_info_extraction(self, system, sample_image):
        """Test file information extraction"""
        insights = system.analyze_image(sample_image)
        file_info = insights.file_info
        
        assert 'width' in file_info
        assert 'height' in file_info
        assert 'channels' in file_info
        assert 'file_size_estimate' in file_info
        assert 'estimated_format' in file_info
    
    def test_error_handling(self, system):
        """Test error handling with invalid inputs"""
        # Test with None image
        with pytest.raises((ValueError, AttributeError)):
            system.analyze_image(None)
        
        # Test with empty image
        empty_image = np.array([])
        with pytest.raises((ValueError, IndexError)):
            system.analyze_image(empty_image)
        
        # Test with invalid image shape
        invalid_image = np.zeros((10, 10))  # Missing color channels
        try:
            insights = system.analyze_image(invalid_image)
            # Should handle gracefully or raise appropriate error
        except (ValueError, cv2.error):
            pass  # Expected behavior
    
    def test_performance_benchmarks(self, system, sample_image):
        """Test performance benchmarks"""
        start_time = time.time()
        insights = system.analyze_image(sample_image)
        processing_time = time.time() - start_time
        
        # Basic performance check - should complete within reasonable time
        assert processing_time < 30  # 30 seconds max for basic analysis
        assert insights.processing_time <= processing_time + 1  # Allow small margin
    
    def test_reproducibility(self, system, sample_image):
        """Test analysis reproducibility"""
        insights1 = system.analyze_image(sample_image)
        insights2 = system.analyze_image(sample_image)
        
        # Color analysis should be consistent
        assert len(insights1.color_analysis.dominant_colors) == len(insights2.color_analysis.dominant_colors)
        
        # Quality scores should be identical
        assert insights1.quality_metrics.technical_score == insights2.quality_metrics.technical_score
        
        # Composition metrics should be consistent
        assert insights1.composition_analysis.aspect_ratio == insights2.composition_analysis.aspect_ratio
    
    def test_memory_usage(self, system):
        """Test memory usage with multiple analyses"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform multiple analyses
        for i in range(5):
            test_image = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
            insights = system.analyze_image(test_image)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 500MB)
        assert memory_increase < 500 * 1024 * 1024
    
    def test_edge_cases(self, system):
        """Test edge cases"""
        # Very small image
        tiny_image = np.ones((10, 10, 3), dtype=np.uint8) * 128
        insights = system.analyze_image(tiny_image)
        assert isinstance(insights, ComprehensiveImageInsights)
        
        # Very large image (if memory allows)
        try:
            large_image = np.ones((2000, 3000, 3), dtype=np.uint8) * 128
            insights = system.analyze_image(large_image)
            assert isinstance(insights, ComprehensiveImageInsights)
        except MemoryError:
            pass  # Skip if insufficient memory
        
        # Single color image
        mono_image = np.ones((400, 600, 3), dtype=np.uint8) * 128
        insights = system.analyze_image(mono_image)
        assert insights.color_analysis.color_diversity < 0.1  # Should have low diversity
        
        # High contrast image
        contrast_image = np.zeros((400, 600, 3), dtype=np.uint8)
        contrast_image[:200, :] = 255
        insights = system.analyze_image(contrast_image)
        assert insights.color_analysis.contrast_level in ['high', 'very_high']

@pytest.mark.integration
class TestImageAnalysisIntegration:
    """Integration tests with real image files"""
    
    def test_with_real_images(self):
        """Test with actual image files if available"""
        system = ImageAnalysisInsightsSystem(use_gpu=False)
        
        # Create test image files
        test_images = []
        
        # Generate and save test images
        for i in range(3):
            image = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
            # Add some structure
            cv2.rectangle(image, (50*i, 50*i), (200+50*i, 200+50*i), (255, 128, 0), -1)
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                cv2.imwrite(tmp.name, image)
                test_images.append(tmp.name)
        
        try:
            for image_path in test_images:
                # Load and analyze
                image = cv2.imread(image_path)
                insights = system.analyze_image(image)
                
                # Verify analysis completed
                assert isinstance(insights, ComprehensiveImageInsights)
                assert insights.processing_time > 0
                
                # Test file info matches
                assert insights.file_info['width'] == image.shape[1]
                assert insights.file_info['height'] == image.shape[0]
        
        finally:
            # Cleanup
            for image_path in test_images:
                try:
                    os.unlink(image_path)
                except OSError:
                    pass

def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🔍 Starting Image Analysis & Insights System Tests...")
    
    # Run pytest
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])
    
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return exit_code == 0

if __name__ == "__main__":
    # Run comprehensive tests
    success = run_comprehensive_test()
    
    if success:
        print("\n🎉 Task 78 - Image Analysis & Insights System: All Tests Passed!")
        print("📊 System is ready for production use.")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        exit(1)