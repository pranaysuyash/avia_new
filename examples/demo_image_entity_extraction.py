#!/usr/bin/env python3
"""
Demo script for Image Entity Extraction System
Demonstrates the capabilities of the image-based entity extraction and analysis system
"""

import sys
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import json
from typing import Dict, List, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from image_entity_extraction_system import (
    ImageEntityExtractionSystem, ImageAnalysisResult, VisualEntity,
    EntityType, ImageQuality
)

class ImageEntityExtractionDemo:
    """Demo class for image entity extraction system"""
    
    def __init__(self):
        print("🚀 Initializing Image Entity Extraction System...")
        self.system = ImageEntityExtractionSystem()
        print("✅ System initialized successfully!")
    
    def create_sample_images(self) -> Dict[str, np.ndarray]:
        """Create various sample images for testing"""
        samples = {}
        
        # 1. Business Card Sample
        print("📄 Creating business card sample...")
        business_card = self.create_business_card()
        samples['business_card'] = business_card
        
        # 2. Document Sample
        print("📋 Creating document sample...")
        document = self.create_document_sample()
        samples['document'] = document
        
        # 3. Mixed Content Sample
        print("🖼️ Creating mixed content sample...")
        mixed_content = self.create_mixed_content()
        samples['mixed_content'] = mixed_content
        
        # 4. Chart Sample
        print("📊 Creating chart sample...")
        chart = self.create_chart_sample()
        samples['chart'] = chart
        
        return samples
    
    def create_business_card(self) -> np.ndarray:
        """Create a business card sample"""
        # Create white background
        image = np.ones((400, 700, 3), dtype=np.uint8) * 255
        
        # Add company logo area (rectangle)
        cv2.rectangle(image, (50, 50), (150, 120), (100, 150, 200), -1)
        cv2.putText(image, "LOGO", (80, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Add text content
        cv2.putText(image, "Dr. Sarah Johnson", (200, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        cv2.putText(image, "Chief Technology Officer", (200, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 50, 50), 1)
        cv2.putText(image, "TechCorp Industries", (200, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 100, 200), 2)
        
        # Contact information
        cv2.putText(image, "Email: sarah.johnson@techcorp.com", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Phone: +1 (555) 987-6543", (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Address: 123 Innovation Drive, Tech City, TC 12345", (50, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Website: www.techcorp.com", (50, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Add a simple QR code placeholder
        cv2.rectangle(image, (550, 250), (650, 350), (0, 0, 0), 2)
        cv2.putText(image, "QR", (580, 310), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        return image
    
    def create_document_sample(self) -> np.ndarray:
        """Create a document sample with various entities"""
        # Create white background
        image = np.ones((800, 600, 3), dtype=np.uint8) * 255
        
        # Header
        cv2.putText(image, "CONFIDENTIAL REPORT", (150, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (200, 0, 0), 2)
        cv2.putText(image, "Date: March 15, 2024", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
        cv2.putText(image, "Prepared by: Global Analytics Inc.", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
        
        # Content sections
        y_pos = 200
        lines = [
            "EXECUTIVE SUMMARY",
            "",
            "This report analyzes the performance of Microsoft Corporation",
            "and Apple Inc. during Q1 2024. Key findings include:",
            "",
            "• Revenue growth of $2.5 billion for Microsoft",
            "• Apple's market share increased by 15% in January 2024",
            "• Both companies showed strong performance in New York",
            "  and California markets",
            "",
            "FINANCIAL HIGHLIGHTS",
            "",
            "Total revenue: $125,000,000",
            "Net profit: $45,000,000",
            "Operating expenses: $80,000,000",
            "",
            "Contact: John Smith, Senior Analyst",
            "Email: j.smith@globalanalytics.com",
            "Phone: +1 (555) 123-4567"
        ]
        
        for line in lines:
            if line.startswith("•"):
                cv2.putText(image, line, (70, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            elif line.isupper() and line:
                cv2.putText(image, line, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 0), 2)
            elif line:
                cv2.putText(image, line, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            y_pos += 30
        
        # Add signature area
        cv2.rectangle(image, (400, 650), (550, 720), (0, 0, 0), 1)
        cv2.putText(image, "Signature", (420, 690), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        
        return image
    
    def create_mixed_content(self) -> np.ndarray:
        """Create mixed content with various visual elements"""
        # Create gradient background
        image = np.ones((600, 800, 3), dtype=np.uint8) * 240
        
        # Add some geometric shapes (potential logos)
        cv2.circle(image, (150, 150), 50, (255, 100, 100), -1)
        cv2.rectangle(image, (250, 100), (350, 200), (100, 255, 100), -1)
        cv2.ellipse(image, (500, 150), (60, 40), 0, 0, 360, (100, 100, 255), -1)
        
        # Add text content
        cv2.putText(image, "PRODUCT CATALOG 2024", (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Product information
        products = [
            ("Smartphone Pro Max - $999", 280),
            ("Laptop Ultra Thin - $1,299", 320),
            ("Tablet HD Display - $599", 360),
            ("Smartwatch Series X - $399", 400)
        ]
        
        for product, y in products:
            cv2.putText(image, product, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        
        # Add barcode-like pattern
        for i in range(20):
            x = 600 + i * 8
            if i % 3 == 0:
                cv2.line(image, (x, 450), (x, 500), (0, 0, 0), 2)
            else:
                cv2.line(image, (x, 450), (x, 500), (0, 0, 0), 1)
        
        # Add company info
        cv2.putText(image, "TechMart Solutions", (50, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 200), 2)
        cv2.putText(image, "Visit us at: San Francisco, CA", (50, 530), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Call: 1-800-TECHMART", (50, 560), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        return image
    
    def create_chart_sample(self) -> np.ndarray:
        """Create a chart/graph sample"""
        # Create white background
        image = np.ones((500, 700, 3), dtype=np.uint8) * 255
        
        # Title
        cv2.putText(image, "QUARTERLY SALES REPORT", (150, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
        cv2.putText(image, "Q1 2024 Performance", (220, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 1)
        
        # Draw axes
        cv2.line(image, (100, 400), (600, 400), (0, 0, 0), 2)  # X-axis
        cv2.line(image, (100, 400), (100, 150), (0, 0, 0), 2)  # Y-axis
        
        # Add axis labels
        cv2.putText(image, "Months", (350, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Sales ($M)", (20, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Add grid lines
        for i in range(1, 6):
            y = 400 - i * 50
            cv2.line(image, (100, y), (600, y), (200, 200, 200), 1)
            cv2.putText(image, str(i * 10), (70, y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Add month labels
        months = ["Jan", "Feb", "Mar"]
        for i, month in enumerate(months):
            x = 200 + i * 150
            cv2.putText(image, month, (x - 15, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Draw bar chart
        bar_heights = [120, 180, 150]  # Heights in pixels
        bar_width = 60
        
        for i, height in enumerate(bar_heights):
            x = 175 + i * 150
            y = 400 - height
            cv2.rectangle(image, (x, y), (x + bar_width, 400), (100, 150, 255), -1)
            cv2.rectangle(image, (x, y), (x + bar_width, 400), (0, 0, 0), 2)
            
            # Add value labels
            value = height // 6  # Convert to millions
            cv2.putText(image, f"${value}M", (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Add legend
        cv2.rectangle(image, (450, 180), (470, 200), (100, 150, 255), -1)
        cv2.putText(image, "Revenue", (480, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        return image
    
    def analyze_sample(self, name: str, image: np.ndarray) -> ImageAnalysisResult:
        """Analyze a sample image"""
        print(f"\n🔍 Analyzing {name}...")
        
        try:
            result = self.system.analyze_image(image_data=image)
            print(f"✅ Analysis completed for {name}")
            return result
        except Exception as e:
            print(f"❌ Error analyzing {name}: {e}")
            return None
    
    def print_analysis_summary(self, name: str, result: ImageAnalysisResult):
        """Print a summary of analysis results"""
        if not result:
            print(f"❌ No results for {name}")
            return
        
        print(f"\n📊 Analysis Summary for {name}:")
        print(f"   Overall Confidence: {result.confidence:.1%}")
        print(f"   Image Quality: {result.quality_assessment.overall_quality.value.title()}")
        print(f"   Entities Found: {len(result.visual_entities)}")
        print(f"   Faces Detected: {result.visual_content.faces_detected}")
        print(f"   Objects Detected: {len(result.visual_content.objects_detected)}")
        
        # Show entity types
        if result.visual_entities:
            entity_types = {}
            for entity in result.visual_entities:
                entity_type = entity.entity_type.value
                if entity_type not in entity_types:
                    entity_types[entity_type] = 0
                entity_types[entity_type] += 1
            
            print(f"   Entity Types: {dict(entity_types)}")
        
        # Show top entities
        if result.visual_entities:
            print("   Top Entities:")
            for i, entity in enumerate(result.visual_entities[:5], 1):
                text_preview = entity.text[:30] + "..." if len(entity.text) > 30 else entity.text
                print(f"     {i}. {entity.entity_type.value}: '{text_preview}' ({entity.confidence:.1%})")
        
        # Show quality metrics
        quality = result.quality_assessment
        print(f"   Quality Metrics:")
        print(f"     Sharpness: {quality.sharpness_score:.1f}")
        print(f"     Brightness: {quality.brightness_score:.1f}")
        print(f"     Contrast: {quality.contrast_score:.1f}")
        
        # Show recommendations
        if quality.recommendations:
            print(f"   Recommendations:")
            for i, rec in enumerate(quality.recommendations[:3], 1):
                print(f"     {i}. {rec}")
    
    def save_results(self, results: Dict[str, ImageAnalysisResult]):
        """Save analysis results to files"""
        print("\n💾 Saving results...")
        
        # Create results directory
        os.makedirs("demo_results", exist_ok=True)
        
        for name, result in results.items():
            if result:
                # Convert result to dictionary
                result_dict = {
                    'sample_name': name,
                    'confidence': result.confidence,
                    'extracted_text': result.extracted_text,
                    'image_quality': result.quality_assessment.overall_quality.value,
                    'entities_count': len(result.visual_entities),
                    'faces_detected': result.visual_content.faces_detected,
                    'objects_detected': len(result.visual_content.objects_detected),
                    'visual_entities': [
                        {
                            'type': entity.entity_type.value,
                            'text': entity.text,
                            'confidence': entity.confidence,
                            'source': entity.metadata.get('source', 'unknown')
                        }
                        for entity in result.visual_entities
                    ],
                    'content_description': result.visual_content.description,
                    'dominant_colors': result.visual_content.dominant_colors,
                    'quality_recommendations': result.quality_assessment.recommendations
                }
                
                # Save to JSON file
                filename = f"demo_results/{name}_analysis.json"
                with open(filename, 'w') as f:
                    json.dump(result_dict, f, indent=2, default=str)
                
                print(f"   ✅ Saved {filename}")
    
    def save_sample_images(self, samples: Dict[str, np.ndarray]):
        """Save sample images"""
        print("\n🖼️ Saving sample images...")
        
        os.makedirs("demo_results", exist_ok=True)
        
        for name, image in samples.items():
            filename = f"demo_results/{name}_sample.png"
            cv2.imwrite(filename, image)
            print(f"   ✅ Saved {filename}")
    
    def run_comprehensive_demo(self):
        """Run comprehensive demo of the system"""
        print("🎯 Starting Comprehensive Image Entity Extraction Demo")
        print("=" * 60)
        
        # Create sample images
        print("\n📸 Creating sample images...")
        samples = self.create_sample_images()
        
        # Save sample images
        self.save_sample_images(samples)
        
        # Analyze each sample
        results = {}
        for name, image in samples.items():
            result = self.analyze_sample(name, image)
            results[name] = result
            if result:
                self.print_analysis_summary(name, result)
        
        # Save results
        self.save_results(results)
        
        # Print overall summary
        print("\n🎉 Demo Completed Successfully!")
        print("=" * 60)
        
        successful_analyses = sum(1 for r in results.values() if r is not None)
        print(f"✅ Successfully analyzed {successful_analyses}/{len(samples)} samples")
        print(f"📁 Results saved to 'demo_results/' directory")
        print(f"🖼️ Sample images saved for reference")
        
        # Print system capabilities summary
        print("\n🚀 System Capabilities Demonstrated:")
        print("   • Image metadata extraction")
        print("   • Image quality assessment")
        print("   • Visual entity detection")
        print("   • Text extraction (OCR simulation)")
        print("   • Object detection")
        print("   • Content analysis and description")
        print("   • Color analysis")
        print("   • Chart and graph detection")
        print("   • Logo and signature detection")
        print("   • QR code and barcode detection")
        
        return results

def main():
    """Main function"""
    try:
        demo = ImageEntityExtractionDemo()
        results = demo.run_comprehensive_demo()
        
        print("\n🎯 Demo completed successfully!")
        print("Check the 'demo_results/' directory for output files.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()