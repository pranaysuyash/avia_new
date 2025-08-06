#!/usr/bin/env python3
"""
Test script for Image Preprocessing System (Task 82)
"""

import os
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from image_preprocessing_system import ImagePreprocessor, PreprocessingConfig

def create_test_image_with_noise():
    """Create a test image with various issues to test preprocessing"""
    # Create base image
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    img.fill(255)  # White background
    
    # Add text
    cv2.putText(img, "SAMPLE DOCUMENT", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
    cv2.putText(img, "Financial Report Q4 2024", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, "Revenue: $2.5M", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
    cv2.putText(img, "Growth: +25%", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
    
    # Add noise
    noise = np.random.randint(0, 50, img.shape, dtype=np.uint8)
    img = cv2.add(img, noise)
    
    # Reduce contrast
    img = cv2.convertScaleAbs(img, alpha=0.7, beta=30)
    
    # Add slight blur
    img = cv2.GaussianBlur(img, (3, 3), 0)
    
    # Add slight rotation (skew)
    rows, cols = img.shape[:2]
    M = cv2.getRotationMatrix2D((cols/2, rows/2), 2, 1)
    img = cv2.warpAffine(img, M, (cols, rows), borderValue=(255, 255, 255))
    
    return img

def test_basic_preprocessing():
    """Test basic preprocessing functionality"""
    print("Testing Basic Image Preprocessing...")
    
    try:
        # Create test image
        test_image = create_test_image_with_noise()
        print("✓ Created test image with noise and distortions")
        
        # Initialize preprocessor
        config = PreprocessingConfig(
            enable_denoising=True,
            auto_contrast=True,
            enable_sharpening=True,
            auto_deskew=True
        )
        preprocessor = ImagePreprocessor(config)
        print("✓ Initialized image preprocessor")
        
        # Process image
        result = preprocessor.preprocess_image(test_image, config)
        print(f"✓ Processed image in {result.processing_time:.2f}s")
        
        # Check operations
        print(f"✓ Applied operations: {result.operations_applied}")
        print(f"✓ Original shape: {result.metadata['original_shape']}")
        print(f"✓ Processed shape: {result.metadata['processed_shape']}")
        
        # Check quality metrics
        print("Quality Improvements:")
        for metric, value in result.quality_metrics.items():
            print(f"  - {metric}: {value:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_configurations():
    """Test different preprocessing configurations"""
    print("\nTesting Different Configurations...")
    
    try:
        test_image = create_test_image_with_noise()
        
        # Test different configs
        configs = [
            ("Minimal", PreprocessingConfig(
                enable_denoising=True,
                auto_contrast=False,
                enable_sharpening=False
            )),
            ("OCR Optimized", PreprocessingConfig(
                enable_denoising=True,
                auto_contrast=True,
                enable_sharpening=True,
                auto_threshold=True,
                upscale_factor=2.0
            )),
            ("High Quality", PreprocessingConfig(
                enable_denoising=True,
                denoise_method="nlm",
                auto_contrast=True,
                enable_sharpening=True,
                sharpen_method="unsharp_mask",
                auto_deskew=True,
                perspective_correction=True,
                upscale_factor=1.5
            ))
        ]
        
        preprocessor = ImagePreprocessor()
        
        for name, config in configs:
            print(f"\n  Testing {name} configuration:")
            result = preprocessor.preprocess_image(test_image, config)
            print(f"    - Processing time: {result.processing_time:.2f}s")
            print(f"    - Operations: {len(result.operations_applied)}")
            print(f"    - Quality improvements: {len([v for v in result.quality_metrics.values() if v > 0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_quality_assessment():
    """Test quality assessment functionality"""
    print("\nTesting Quality Assessment...")
    
    try:
        # Create images with different quality levels
        test_images = []
        
        # High quality image
        high_quality = np.zeros((300, 400, 3), dtype=np.uint8)
        high_quality.fill(255)
        cv2.putText(high_quality, "HIGH QUALITY TEXT", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        test_images.append(("High Quality", high_quality))
        
        # Low quality image (blurry, noisy)
        low_quality = high_quality.copy()
        noise = np.random.randint(0, 100, low_quality.shape, dtype=np.uint8)
        low_quality = cv2.add(low_quality, noise)
        low_quality = cv2.GaussianBlur(low_quality, (5, 5), 0)
        low_quality = cv2.convertScaleAbs(low_quality, alpha=0.5, beta=50)
        test_images.append(("Low Quality", low_quality))
        
        preprocessor = ImagePreprocessor()
        
        for name, image in test_images:
            print(f"\n  Assessing {name}:")
            quality = preprocessor._assess_image_quality(image)
            print(f"    - Sharpness: {quality['sharpness']:.2f}")
            print(f"    - Contrast: {quality['contrast']:.2f}")
            print(f"    - Brightness: {quality['brightness']:.2f}")
            print(f"    - Noise Level: {quality['noise_level']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_file_operations():
    """Test file loading and saving operations"""
    print("\nTesting File Operations...")
    
    try:
        # Create and save test image
        test_image = create_test_image_with_noise()
        temp_input = tempfile.mktemp(suffix='.png')
        cv2.imwrite(temp_input, test_image)
        print("✓ Created temporary test image file")
        
        # Process from file
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess_image(temp_input)
        print("✓ Processed image from file path")
        
        # Save comparison
        temp_output = tempfile.mktemp(suffix='.png')
        result.save_comparison(temp_output)
        print("✓ Saved before/after comparison")
        
        # Clean up
        os.unlink(temp_input)
        os.unlink(temp_output)
        print("✓ Cleaned up temporary files")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run all image preprocessing tests"""
    print("Image Preprocessing System Tests (Task 82)")
    print("=" * 60)
    
    tests = [
        test_basic_preprocessing,
        test_different_configurations,
        test_quality_assessment,
        test_file_operations
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Tests completed: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("✅ All image preprocessing tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    main()