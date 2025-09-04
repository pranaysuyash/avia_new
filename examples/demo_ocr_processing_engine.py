"""
Demo script for Enterprise OCR Processing Engine

This script demonstrates the comprehensive capabilities of the OCR processing engine
including multiple providers, routing policies, and advanced features.
"""

import os
import cv2
import numpy as np
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import matplotlib.pyplot as plt
from pathlib import Path

# Set Tesseract data path for macOS
os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata'

from ocr_processing_engine import (
    OCRProcessingService, OCRConfig, OCRProvider, PreprocessingMode,
    RoutingPolicy, TextDetectionMethod, TextDetectionService,
    create_ocr_config, get_available_ocr_providers
)


def create_test_images() -> Dict[str, np.ndarray]:
    """Create various test images for OCR demonstration"""
    test_images = {}
    
    # 1. Simple text document
    img1 = np.ones((300, 500, 3), dtype=np.uint8) * 255
    cv2.putText(img1, "ENTERPRISE OCR SYSTEM", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img1, "This is a test document with", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(img1, "multiple lines of text for", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(img1, "OCR processing demonstration.", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(img1, "Confidence: High", (50, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    test_images["document"] = img1
    
    # 2. Noisy image (challenging)
    img2 = np.ones((200, 400, 3), dtype=np.uint8) * 240
    cv2.putText(img2, "NOISY TEXT", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img2, "Hard to read", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    # Add noise
    noise = np.random.randint(0, 50, img2.shape, dtype=np.uint8)
    img2 = cv2.add(img2, noise)
    test_images["noisy"] = img2
    
    # 3. Multi-language text
    img3 = np.ones((250, 450, 3), dtype=np.uint8) * 255
    cv2.putText(img3, "English Text", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img3, "Texto en Espanol", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    cv2.putText(img3, "Texte en Francais", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    cv2.putText(img3, "Deutscher Text", (50, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    test_images["multilingual"] = img3
    
    # 4. Receipt-like image
    img4 = np.ones((350, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img4, "RECEIPT", (100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img4, "Item 1......$10.99", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img4, "Item 2......$15.50", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img4, "Item 3.......$8.25", (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img4, "Tax..........$2.75", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img4, "Total.......$37.49", (20, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.putText(img4, "Thank you!", (80, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    test_images["receipt"] = img4
    
    # 5. Low contrast image
    img5 = np.ones((200, 400, 3), dtype=np.uint8) * 200
    cv2.putText(img5, "Low Contrast Text", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2)
    cv2.putText(img5, "Difficult to detect", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (160, 160, 160), 1)
    test_images["low_contrast"] = img5
    
    return test_images


def demo_basic_ocr():
    """Demonstrate basic OCR functionality"""
    print("\n" + "="*60)
    print("DEMO: Basic OCR Functionality")
    print("="*60)
    
    # Check available providers
    available_providers = get_available_ocr_providers()
    print(f"Available OCR providers: {available_providers}")
    
    if not available_providers:
        print("❌ No OCR providers available! Please install Tesseract or EasyOCR.")
        return
    
    # Create test images
    test_images = create_test_images()
    
    # Basic configuration
    config = OCRConfig(
        providers=[OCRProvider.TESSERACT] if 'tesseract' in available_providers else [OCRProvider.EASYOCR],
        preprocessing_mode=PreprocessingMode.STANDARD,
        confidence_threshold=0.3,
        routing_policy=RoutingPolicy.BALANCED
    )
    
    service = OCRProcessingService(config)
    
    try:
        print(f"\n1. Processing test images with {config.providers[0].value}:")
        
        for image_name, image in test_images.items():
            print(f"\n   Processing '{image_name}' image:")
            
            start_time = time.time()
            result = service.process_image(image)
            end_time = time.time()
            
            print(f"     Provider: {result.provider}")
            print(f"     Processing time: {end_time - start_time:.3f}s")
            print(f"     Segments found: {len(result.segments)}")
            print(f"     Average confidence: {result.get_average_confidence():.3f}")
            print(f"     Extracted text: '{result.get_text()}'")
            
            if result.segments:
                print(f"     Text segments:")
                for i, segment in enumerate(result.segments[:3]):  # Show first 3
                    print(f"       {i+1}. '{segment.text}' (conf: {segment.confidence:.3f})")
    
    finally:
        service.cleanup()


def demo_provider_comparison():
    """Compare different OCR providers"""
    print("\n" + "="*60)
    print("DEMO: OCR Provider Comparison")
    print("="*60)
    
    available_providers = get_available_ocr_providers()
    
    if len(available_providers) < 2:
        print("⚠️  Need at least 2 providers for comparison. Available:", available_providers)
        if available_providers:
            print("Demonstrating with single provider...")
        else:
            return
    
    test_images = create_test_images()
    test_image = test_images["document"]  # Use document image for comparison
    
    # Test each available provider
    provider_results = {}
    
    for provider_name in available_providers:
        if provider_name == 'tesseract':
            provider = OCRProvider.TESSERACT
        elif provider_name == 'easyocr':
            provider = OCRProvider.EASYOCR
        else:
            continue
        
        print(f"\n   Testing {provider.value}:")
        
        config = OCRConfig(
            providers=[provider],
            preprocessing_mode=PreprocessingMode.STANDARD,
            confidence_threshold=0.3
        )
        
        service = OCRProcessingService(config)
        
        try:
            start_time = time.time()
            result = service.process_image(test_image)
            end_time = time.time()
            
            provider_results[provider.value] = {
                'processing_time': end_time - start_time,
                'segments_found': len(result.segments),
                'average_confidence': result.get_average_confidence(),
                'extracted_text': result.get_text(),
                'text_length': len(result.get_text())
            }
            
            print(f"     Processing time: {end_time - start_time:.3f}s")
            print(f"     Segments found: {len(result.segments)}")
            print(f"     Average confidence: {result.get_average_confidence():.3f}")
            print(f"     Text length: {len(result.get_text())} characters")
        
        except Exception as e:
            print(f"     ❌ Failed: {e}")
            provider_results[provider.value] = None
        
        finally:
            service.cleanup()
    
    # Comparison summary
    print(f"\n   Provider Comparison Summary:")
    print(f"   {'Provider':<12} {'Time (s)':<10} {'Segments':<10} {'Confidence':<12} {'Text Length':<12}")
    print(f"   {'-'*60}")
    
    for provider, results in provider_results.items():
        if results:
            print(f"   {provider:<12} {results['processing_time']:<10.3f} "
                  f"{results['segments_found']:<10} {results['average_confidence']:<12.3f} "
                  f"{results['text_length']:<12}")
        else:
            print(f"   {provider:<12} {'FAILED':<10}")


def demo_routing_policies():
    """Demonstrate different routing policies"""
    print("\n" + "="*60)
    print("DEMO: Routing Policy Comparison")
    print("="*60)
    
    available_providers = get_available_ocr_providers()
    
    if not available_providers:
        print("❌ No providers available for routing demo")
        return
    
    test_images = create_test_images()
    
    # Test different routing policies
    policies = [
        RoutingPolicy.ACCURACY_FIRST,
        RoutingPolicy.COST_OPTIMIZED,
        RoutingPolicy.LATENCY_OPTIMIZED,
        RoutingPolicy.BALANCED
    ]
    
    for policy in policies:
        print(f"\n   Testing {policy.value} routing:")
        
        config = OCRConfig(
            providers=[OCRProvider(p) for p in available_providers if p in ['tesseract', 'easyocr']],
            routing_policy=policy,
            preprocessing_mode=PreprocessingMode.STANDARD,
            confidence_threshold=0.3
        )
        
        service = OCRProcessingService(config)
        
        try:
            # Process a few images to build metrics
            for image_name, image in list(test_images.items())[:3]:
                result = service.process_image(image)
                print(f"     {image_name}: Used {result.provider}, "
                      f"confidence: {result.get_average_confidence():.3f}")
            
            # Show provider metrics
            metrics = service.get_provider_metrics()
            print(f"     Provider metrics after processing:")
            for provider, provider_metrics in metrics.items():
                print(f"       {provider}: {provider_metrics['total_requests']} requests, "
                      f"success rate: {provider_metrics['success_rate']:.1%}")
        
        finally:
            service.cleanup()


def demo_preprocessing_effects():
    """Demonstrate preprocessing effects on OCR accuracy"""
    print("\n" + "="*60)
    print("DEMO: Preprocessing Effects")
    print("="*60)
    
    available_providers = get_available_ocr_providers()
    
    if not available_providers:
        print("❌ No providers available")
        return
    
    # Use challenging images
    test_images = create_test_images()
    challenging_images = {
        'noisy': test_images['noisy'],
        'low_contrast': test_images['low_contrast']
    }
    
    preprocessing_modes = [
        PreprocessingMode.MINIMAL,
        PreprocessingMode.STANDARD,
        PreprocessingMode.AGGRESSIVE
    ]
    
    for image_name, image in challenging_images.items():
        print(f"\n   Testing preprocessing on '{image_name}' image:")
        
        for mode in preprocessing_modes:
            config = OCRConfig(
                providers=[OCRProvider(available_providers[0])],
                preprocessing_mode=mode,
                confidence_threshold=0.1  # Lower threshold for challenging images
            )
            
            service = OCRProcessingService(config)
            
            try:
                result = service.process_image(image)
                
                print(f"     {mode.value:>12}: {len(result.segments)} segments, "
                      f"avg confidence: {result.get_average_confidence():.3f}, "
                      f"text: '{result.get_text()}'")
                
                if result.preprocessing_applied:
                    print(f"                   Applied: {', '.join(result.preprocessing_applied)}")
            
            except Exception as e:
                print(f"     {mode.value:>12}: Failed - {e}")
            
            finally:
                service.cleanup()


def demo_text_detection():
    """Demonstrate text detection methods"""
    print("\n" + "="*60)
    print("DEMO: Text Detection Methods")
    print("="*60)
    
    test_images = create_test_images()
    detector = TextDetectionService()
    
    detection_methods = [
        TextDetectionMethod.MSER,
        TextDetectionMethod.CONTOUR
    ]
    
    for image_name, image in test_images.items():
        print(f"\n   Text detection on '{image_name}' image:")
        
        for method in detection_methods:
            try:
                regions = detector.detect_text_regions(image, method)
                
                print(f"     {method.value:>12}: {len(regions)} regions detected")
                
                if regions:
                    # Show first few regions
                    for i, region in enumerate(regions[:3]):
                        print(f"                   Region {i+1}: "
                              f"({region.x}, {region.y}) {region.width}x{region.height}, "
                              f"conf: {region.confidence:.3f}")
            
            except Exception as e:
                print(f"     {method.value:>12}: Failed - {e}")


def demo_batch_processing():
    """Demonstrate batch processing capabilities"""
    print("\n" + "="*60)
    print("DEMO: Batch Processing")
    print("="*60)
    
    available_providers = get_available_ocr_providers()
    
    if not available_providers:
        print("❌ No providers available")
        return
    
    test_images = create_test_images()
    image_list = list(test_images.values())
    
    config = OCRConfig(
        providers=[OCRProvider(available_providers[0])],
        preprocessing_mode=PreprocessingMode.STANDARD,
        confidence_threshold=0.3
    )
    
    service = OCRProcessingService(config)
    
    try:
        print(f"   Processing {len(image_list)} images in batch...")
        
        start_time = time.time()
        results = service.batch_process_images(image_list)
        end_time = time.time()
        
        print(f"   Batch processing completed in {end_time - start_time:.3f}s")
        print(f"   Average time per image: {(end_time - start_time) / len(image_list):.3f}s")
        
        # Summary statistics
        total_segments = sum(len(result.segments) for result in results)
        avg_confidence = sum(result.get_average_confidence() for result in results) / len(results)
        
        print(f"   Total segments extracted: {total_segments}")
        print(f"   Average confidence: {avg_confidence:.3f}")
        
        # Individual results
        print(f"\n   Individual results:")
        for i, result in enumerate(results):
            image_name = list(test_images.keys())[i]
            print(f"     {image_name:>12}: {len(result.segments)} segments, "
                  f"conf: {result.get_average_confidence():.3f}")
    
    finally:
        service.cleanup()


def demo_cost_estimation():
    """Demonstrate cost estimation features"""
    print("\n" + "="*60)
    print("DEMO: Cost Estimation")
    print("="*60)
    
    available_providers = get_available_ocr_providers()
    
    if not available_providers:
        print("❌ No providers available")
        return
    
    test_images = create_test_images()
    image_list = list(test_images.values())
    
    # Test different configurations
    configs = [
        ("Basic", OCRConfig(
            providers=[OCRProvider(available_providers[0])],
            preprocessing_mode=PreprocessingMode.MINIMAL,
            confidence_threshold=0.5
        )),
        ("Standard", OCRConfig(
            providers=[OCRProvider(available_providers[0])],
            preprocessing_mode=PreprocessingMode.STANDARD,
            confidence_threshold=0.3
        )),
        ("High Quality", OCRConfig(
            providers=[OCRProvider(available_providers[0])],
            preprocessing_mode=PreprocessingMode.AGGRESSIVE,
            confidence_threshold=0.7,
            enable_confidence_calibration=True
        ))
    ]
    
    print(f"   Cost estimation for {len(image_list)} images:")
    print(f"   {'Configuration':<15} {'Est. Cost':<12} {'Est. Time':<12} {'Policy':<15}")
    print(f"   {'-'*60}")
    
    for config_name, config in configs:
        service = OCRProcessingService(config)
        
        try:
            cost_estimate = service.estimate_processing_cost(image_list, config)
            
            print(f"   {config_name:<15} "
                  f"${cost_estimate['estimated_total_cost']:<11.4f} "
                  f"{cost_estimate['estimated_processing_time']:<11.2f}s "
                  f"{config.routing_policy.value:<15}")
        
        except Exception as e:
            print(f"   {config_name:<15} {'ERROR':<12} {str(e)[:20]:<12}")
        
        finally:
            service.cleanup()


def demo_quality_validation():
    """Demonstrate quality validation and metrics"""
    print("\n" + "="*60)
    print("DEMO: Quality Validation")
    print("="*60)
    
    available_providers = get_available_ocr_providers()
    
    if not available_providers:
        print("❌ No providers available")
        return
    
    test_images = create_test_images()
    
    # Expected text for validation
    expected_texts = {
        'document': 'ENTERPRISE OCR SYSTEM This is a test document with multiple lines of text for OCR processing demonstration. Confidence: High',
        'receipt': 'RECEIPT Item 1......$10.99 Item 2......$15.50 Item 3.......$8.25 Tax..........$2.75 Total.......$37.49 Thank you!',
        'multilingual': 'English Text Texto en Espanol Texte en Francais Deutscher Text'
    }
    
    config = OCRConfig(
        providers=[OCRProvider(available_providers[0])],
        preprocessing_mode=PreprocessingMode.STANDARD,
        confidence_threshold=0.3
    )
    
    service = OCRProcessingService(config)
    
    try:
        print(f"   Quality validation results:")
        print(f"   {'Image':<12} {'Accuracy':<10} {'Segments':<10} {'Confidence':<12} {'Valid':<8}")
        print(f"   {'-'*60}")
        
        for image_name in ['document', 'receipt', 'multilingual']:
            if image_name in test_images and image_name in expected_texts:
                image = test_images[image_name]
                expected = expected_texts[image_name]
                
                result = service.process_image(image)
                validation = service.validate_result(result, expected)
                
                accuracy = validation.get('accuracy', 0.0)
                is_valid = accuracy > 0.5 and validation['has_text']
                
                print(f"   {image_name:<12} {accuracy:<10.3f} "
                      f"{validation['segment_count']:<10} "
                      f"{validation['average_confidence']:<12.3f} "
                      f"{'✓' if is_valid else '✗':<8}")
    
    finally:
        service.cleanup()


def demo_error_handling():
    """Demonstrate error handling and edge cases"""
    print("\n" + "="*60)
    print("DEMO: Error Handling & Edge Cases")
    print("="*60)
    
    available_providers = get_available_ocr_providers()
    
    if not available_providers:
        print("❌ No providers available for error handling demo")
        return
    
    config = OCRConfig(
        providers=[OCRProvider(available_providers[0])],
        max_processing_time=5.0  # Short timeout for demo
    )
    
    service = OCRProcessingService(config)
    
    try:
        # Test 1: Empty image
        print("   1. Testing empty image:")
        try:
            empty_image = np.zeros((100, 100, 3), dtype=np.uint8)
            result = service.process_image(empty_image)
            print(f"      ✓ Handled gracefully: {len(result.segments)} segments found")
        except Exception as e:
            print(f"      ✓ Properly caught error: {type(e).__name__}")
        
        # Test 2: Invalid image
        print("   2. Testing invalid image:")
        try:
            invalid_image = np.array([])
            result = service.process_image(invalid_image)
            print(f"      ✗ Should have failed but didn't")
        except Exception as e:
            print(f"      ✓ Properly caught error: {type(e).__name__}")
        
        # Test 3: Very small image
        print("   3. Testing very small image:")
        try:
            tiny_image = np.ones((10, 10, 3), dtype=np.uint8) * 255
            result = service.process_image(tiny_image)
            print(f"      ✓ Handled gracefully: {len(result.segments)} segments found")
        except Exception as e:
            print(f"      ✓ Properly caught error: {type(e).__name__}")
        
        # Test 4: Image with no text
        print("   4. Testing image with no text:")
        try:
            no_text_image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
            result = service.process_image(no_text_image)
            print(f"      ✓ Handled gracefully: {len(result.segments)} segments found")
        except Exception as e:
            print(f"      ✓ Properly caught error: {type(e).__name__}")
    
    finally:
        service.cleanup()


def main():
    """Run all demonstrations"""
    print("Enterprise OCR Processing Engine - Comprehensive Demo")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_basic_ocr()
        demo_provider_comparison()
        demo_routing_policies()
        demo_preprocessing_effects()
        demo_text_detection()
        demo_batch_processing()
        demo_cost_estimation()
        demo_quality_validation()
        demo_error_handling()
        
        print("\n" + "="*60)
        print("✅ All demonstrations completed successfully!")
        print("="*60)
        
        print("\nKey Features Demonstrated:")
        print("• Multiple OCR provider support (Tesseract, EasyOCR)")
        print("• Intelligent provider routing policies")
        print("• Advanced image preprocessing pipeline")
        print("• Separate text detection and recognition")
        print("• Confidence calibration and text normalization")
        print("• Multi-language support and auto-detection")
        print("• Batch processing capabilities")
        print("• Cost estimation and resource planning")
        print("• Quality validation and accuracy metrics")
        print("• Comprehensive error handling")
        
        print("\nNext Steps:")
        print("• Run the Streamlit UI: streamlit run ocr_processing_engine_ui.py")
        print("• Integrate with frame extraction pipeline")
        print("• Add cloud provider implementations")
        print("• Implement EAST/CRAFT text detection models")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()