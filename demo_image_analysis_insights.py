#!/usr/bin/env python3
"""
Task 78: Image Analysis & Insights Demo
Demonstration script for the Image Analysis and Insights System
"""

import cv2
import numpy as np
import json
import time
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

# Import our system
from image_analysis_insights_system import ImageAnalysisInsightsSystem

def create_demo_images():
    """Create various demo images for testing"""
    demo_images = {}
    
    # 1. Colorful geometric image
    geometric = np.zeros((600, 800, 3), dtype=np.uint8)
    # Background gradient
    for i in range(600):
        geometric[i, :] = [int(i/600*255), 100, 200 - int(i/600*100)]
    
    # Add shapes
    cv2.rectangle(geometric, (100, 100), (300, 300), (255, 255, 0), -1)  # Yellow rectangle
    cv2.circle(geometric, (500, 200), 80, (255, 0, 255), -1)  # Magenta circle
    cv2.ellipse(geometric, (650, 400), (100, 60), 45, 0, 360, (0, 255, 255), -1)  # Cyan ellipse
    
    demo_images['geometric'] = geometric
    
    # 2. Nature-like scene
    nature = np.zeros((500, 700, 3), dtype=np.uint8)
    # Sky gradient (blue)
    for i in range(200):
        nature[i, :] = [int(255 - i/200*100), int(255 - i/200*50), 255]
    
    # Ground (green/brown)
    nature[200:, :] = [50, 150, 50]
    
    # Add "trees" (green circles)
    cv2.circle(nature, (150, 250), 80, (0, 200, 0), -1)
    cv2.circle(nature, (350, 200), 100, (0, 180, 0), -1)
    cv2.circle(nature, (550, 280), 90, (0, 190, 0), -1)
    
    # Add "sun" (yellow circle)
    cv2.circle(nature, (600, 80), 40, (0, 255, 255), -1)
    
    demo_images['nature'] = nature
    
    # 3. Portrait-like image
    portrait = np.ones((600, 400, 3), dtype=np.uint8) * 128
    # Add face-like oval
    cv2.ellipse(portrait, (200, 250), (80, 100), 0, 0, 360, (255, 220, 200), -1)
    # Add eyes
    cv2.circle(portrait, (180, 220), 8, (50, 50, 50), -1)
    cv2.circle(portrait, (220, 220), 8, (50, 50, 50), -1)
    # Add mouth
    cv2.ellipse(portrait, (200, 270), (20, 10), 0, 0, 180, (100, 50, 50), 2)
    
    demo_images['portrait'] = portrait
    
    # 4. High contrast black and white
    contrast = np.zeros((400, 600, 3), dtype=np.uint8)
    # Checkerboard pattern
    square_size = 50
    for i in range(0, 400, square_size):
        for j in range(0, 600, square_size):
            if (i//square_size + j//square_size) % 2 == 0:
                contrast[i:i+square_size, j:j+square_size] = 255
    
    demo_images['contrast'] = contrast
    
    # 5. Blurry image
    blurry = np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)
    # Add some structure then blur
    cv2.rectangle(blurry, (50, 50), (150, 150), (255, 0, 0), -1)
    cv2.circle(blurry, (250, 150), 60, (0, 255, 0), -1)
    blurry = cv2.GaussianBlur(blurry, (15, 15), 0)
    
    demo_images['blurry'] = blurry
    
    return demo_images

def analyze_and_display_results(system, image, image_name):
    """Analyze image and display comprehensive results"""
    print(f"\n{'='*60}")
    print(f"🔍 Analyzing: {image_name.upper()}")
    print(f"{'='*60}")
    
    # Perform analysis
    start_time = time.time()
    insights = system.analyze_image(image)
    analysis_time = time.time() - start_time
    
    print(f"⏱️  Analysis completed in {analysis_time:.2f} seconds")
    print(f"📊 Processing time (internal): {insights.processing_time:.2f} seconds")
    print(f"🕒 Timestamp: {insights.analysis_timestamp}")
    
    # Display image info
    print(f"\n📋 FILE INFORMATION:")
    for key, value in insights.file_info.items():
        if key != 'exif':  # Skip EXIF for demo
            print(f"   {key}: {value}")
    
    # Color Analysis
    print(f"\n🎨 COLOR ANALYSIS:")
    color = insights.color_analysis
    print(f"   Temperature: {color.color_temperature}")
    print(f"   Brightness: {color.brightness_level}")
    print(f"   Contrast: {color.contrast_level}")
    print(f"   Saturation: {color.saturation_level}")
    print(f"   Color Diversity: {color.color_diversity:.3f}")
    print(f"   Dominant Colors: {len(color.dominant_colors)} colors")
    
    # Show first few dominant colors
    for i, rgb in enumerate(color.dominant_colors[:3]):
        print(f"     Color {i+1}: RGB({rgb[0]}, {rgb[1]}, {rgb[2]})")
    
    # Composition Analysis
    print(f"\n📐 COMPOSITION ANALYSIS:")
    comp = insights.composition_analysis
    print(f"   Aspect Ratio: {comp.aspect_ratio:.2f}")
    print(f"   Orientation: {comp.orientation}")
    print(f"   Rule of Thirds: {comp.rule_of_thirds_alignment:.3f}")
    print(f"   Symmetry Score: {comp.symmetry_score:.3f}")
    print(f"   Balance Score: {comp.balance_score:.3f}")
    print(f"   Focal Points: {len(comp.focal_points)}")
    print(f"   Leading Lines: {'Yes' if comp.leading_lines_detected else 'No'}")
    print(f"   Depth of Field: {comp.depth_of_field_estimate}")
    
    # Content Analysis
    print(f"\n📸 CONTENT ANALYSIS:")
    content = insights.content_analysis
    print(f"   Scene Type: {content.scene_type}")
    print(f"   Scene Complexity: {content.scene_complexity}")
    print(f"   Faces Detected: {content.faces_detected}")
    print(f"   Text Regions: {len(content.text_regions)}")
    print(f"   Emotional Tone: {content.emotional_tone}")
    print(f"   Primary Subjects: {', '.join(content.primary_subjects[:3])}")
    
    # Quality Metrics
    print(f"\n🏆 QUALITY ASSESSMENT:")
    quality = insights.quality_metrics
    print(f"   Overall Quality: {quality.overall_quality}")
    print(f"   Technical Score: {quality.technical_score:.1f}/100")
    print(f"   Sharpness: {quality.sharpness_score:.1f}/100")
    print(f"   Exposure: {quality.exposure_quality}")
    print(f"   White Balance: {quality.white_balance}")
    print(f"   Noise Level: {quality.noise_level}")
    print(f"   Resolution: {quality.resolution_quality}")
    print(f"   Compression Artifacts: {'Yes' if quality.compression_artifacts else 'No'}")
    
    # Semantic Insights
    print(f"\n🧠 SEMANTIC INSIGHTS:")
    semantic = insights.semantic_insights
    print(f"   Commercial Potential: {semantic.commercial_potential}")
    print(f"   Emotional Impact: {semantic.emotional_impact}")
    print(f"   Scene Description: {semantic.scene_description[:100]}...")
    print(f"   Key Themes: {', '.join(semantic.key_themes[:5])}")
    print(f"   Content Categories: {', '.join(semantic.content_categories[:3])}")
    print(f"   Target Audience: {', '.join(semantic.target_audience[:3])}")
    
    # Confidence Scores
    print(f"\n📈 CONFIDENCE SCORES:")
    for category, score in insights.confidence_scores.items():
        print(f"   {category.title()}: {score:.3f}")
    
    return insights

def demonstrate_batch_analysis(system, demo_images):
    """Demonstrate batch analysis capabilities"""
    print(f"\n{'='*60}")
    print("🔄 BATCH ANALYSIS DEMONSTRATION")
    print(f"{'='*60}")
    
    # Prepare images for batch analysis
    images = list(demo_images.values())
    names = list(demo_images.keys())
    
    print(f"📦 Analyzing {len(images)} images in batch...")
    
    start_time = time.time()
    results = system.batch_analyze(images)
    batch_time = time.time() - start_time
    
    print(f"⏱️  Batch analysis completed in {batch_time:.2f} seconds")
    print(f"📊 Average time per image: {batch_time/len(images):.2f} seconds")
    
    # Display summary
    print(f"\n📋 BATCH ANALYSIS SUMMARY:")
    for i, (name, result) in enumerate(zip(names, results)):
        quality_score = result.quality_metrics.technical_score
        color_diversity = result.color_analysis.color_diversity
        print(f"   {name:12} | Quality: {quality_score:5.1f} | Colors: {color_diversity:.3f} | "
              f"Scene: {result.content_analysis.scene_type}")
    
    return results

def demonstrate_comparison(system, demo_images):
    """Demonstrate image comparison capabilities"""
    print(f"\n{'='*60}")
    print("🔀 IMAGE COMPARISON DEMONSTRATION")
    print(f"{'='*60}")
    
    # Compare geometric vs nature images
    image1 = demo_images['geometric']
    image2 = demo_images['nature']
    
    print("🆚 Comparing 'geometric' vs 'nature' images...")
    
    start_time = time.time()
    comparison = system.compare_images(image1, image2)
    compare_time = time.time() - start_time
    
    print(f"⏱️  Comparison completed in {compare_time:.2f} seconds")
    
    # Display comparison results
    print(f"\n📊 COMPARISON RESULTS:")
    
    if 'quality_score' in comparison['differences']:
        quality = comparison['differences']['quality_score']
        print(f"   Quality Comparison:")
        print(f"     Geometric: {quality['image_1']:.1f}")
        print(f"     Nature:    {quality['image_2']:.1f}")
        print(f"     Better:    {quality['better_image']}")
        print(f"     Difference: {quality['difference']:.1f}")
    
    if 'composition_score' in comparison['differences']:
        comp = comparison['differences']['composition_score']
        print(f"   Composition Comparison:")
        print(f"     Geometric: {comp['image_1']:.3f}")
        print(f"     Nature:    {comp['image_2']:.3f}")
        print(f"     Better:    {comp['better_image']}")
    
    # Display similarities
    if 'similarities' in comparison:
        similarities = comparison['similarities']
        print(f"   Similarities:")
        for key, value in similarities.items():
            print(f"     {key}: {value}")

def demonstrate_export_formats(system, insights, image_name):
    """Demonstrate different export formats"""
    print(f"\n{'='*60}")
    print("💾 EXPORT FORMATS DEMONSTRATION")
    print(f"{'='*60}")
    
    # JSON Export
    print("📄 Exporting to JSON...")
    json_export = system.export_analysis(insights, 'json')
    print(f"   JSON export size: {len(str(json_export))} characters")
    
    # Save JSON sample
    if isinstance(json_export, dict):
        with open(f'demo_export_{image_name}.json', 'w') as f:
            json.dump(json_export, f, indent=2, default=str)
        print(f"   ✅ Saved: demo_export_{image_name}.json")
    
    # CSV Export
    print("📊 Exporting to CSV...")
    csv_export = system.export_analysis(insights, 'csv')
    print(f"   CSV export size: {len(csv_export)} characters")
    
    # Save CSV sample
    with open(f'demo_export_{image_name}.csv', 'w') as f:
        f.write(csv_export)
    print(f"   ✅ Saved: demo_export_{image_name}.csv")
    
    # HTML Export
    print("🌐 Exporting to HTML...")
    html_export = system.export_analysis(insights, 'html')
    print(f"   HTML export size: {len(html_export)} characters")
    
    # Save HTML sample
    with open(f'demo_export_{image_name}.html', 'w') as f:
        f.write(html_export)
    print(f"   ✅ Saved: demo_export_{image_name}.html")

def create_analysis_visualization(results, names):
    """Create visualizations of analysis results"""
    print(f"\n{'='*60}")
    print("📈 CREATING ANALYSIS VISUALIZATIONS")
    print(f"{'='*60}")
    
    try:
        # Collect data for visualization
        quality_scores = [r.quality_metrics.technical_score for r in results]
        color_diversity = [r.color_analysis.color_diversity for r in results]
        processing_times = [r.processing_time for r in results]
        
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Image Analysis Results Visualization', fontsize=16)
        
        # Quality scores bar chart
        ax1.bar(names, quality_scores, color='skyblue')
        ax1.set_title('Quality Scores')
        ax1.set_ylabel('Score (0-100)')
        ax1.tick_params(axis='x', rotation=45)
        
        # Color diversity scatter plot
        ax2.scatter(names, color_diversity, color='orange', s=100)
        ax2.set_title('Color Diversity')
        ax2.set_ylabel('Diversity (0-1)')
        ax2.tick_params(axis='x', rotation=45)
        
        # Processing times
        ax3.bar(names, processing_times, color='lightgreen')
        ax3.set_title('Processing Times')
        ax3.set_ylabel('Time (seconds)')
        ax3.tick_params(axis='x', rotation=45)
        
        # Quality vs Diversity correlation
        ax4.scatter(quality_scores, color_diversity, s=100)
        for i, name in enumerate(names):
            ax4.annotate(name, (quality_scores[i], color_diversity[i]), 
                        xytext=(5, 5), textcoords='offset points')
        ax4.set_xlabel('Quality Score')
        ax4.set_ylabel('Color Diversity')
        ax4.set_title('Quality vs Diversity')
        
        plt.tight_layout()
        plt.savefig('image_analysis_results.png', dpi=300, bbox_inches='tight')
        print("   ✅ Saved: image_analysis_results.png")
        
        # Show the plot
        plt.show()
        
    except Exception as e:
        print(f"   ⚠️  Could not create visualizations: {e}")

def main():
    """Main demo function"""
    print("🚀 Starting Image Analysis & Insights System Demo")
    print("=" * 70)
    
    # Initialize system
    print("⚙️  Initializing Image Analysis & Insights System...")
    system = ImageAnalysisInsightsSystem(use_gpu=False)  # Use CPU for demo
    print("✅ System initialized successfully!")
    
    # Create demo images
    print("\n🖼️  Creating demo images...")
    demo_images = create_demo_images()
    print(f"✅ Created {len(demo_images)} demo images")
    
    # Save demo images for reference
    for name, image in demo_images.items():
        cv2.imwrite(f'demo_image_{name}.jpg', image)
        print(f"   💾 Saved: demo_image_{name}.jpg")
    
    # Analyze each image individually
    all_results = []
    for name, image in demo_images.items():
        insights = analyze_and_display_results(system, image, name)
        all_results.append(insights)
    
    # Demonstrate batch analysis
    batch_results = demonstrate_batch_analysis(system, demo_images)
    
    # Demonstrate comparison
    demonstrate_comparison(system, demo_images)
    
    # Demonstrate export formats (using first result)
    first_result = all_results[0]
    first_name = list(demo_images.keys())[0]
    demonstrate_export_formats(system, first_result, first_name)
    
    # Create visualizations
    create_analysis_visualization(all_results, list(demo_images.keys()))
    
    # Performance summary
    print(f"\n{'='*60}")
    print("🏁 DEMO SUMMARY")
    print(f"{'='*60}")
    
    avg_processing_time = np.mean([r.processing_time for r in all_results])
    avg_quality_score = np.mean([r.quality_metrics.technical_score for r in all_results])
    avg_confidence = np.mean([r.confidence_scores['overall'] for r in all_results])
    
    print(f"📊 Images Analyzed: {len(all_results)}")
    print(f"⏱️  Average Processing Time: {avg_processing_time:.2f} seconds")
    print(f"🏆 Average Quality Score: {avg_quality_score:.1f}/100")
    print(f"📈 Average Confidence: {avg_confidence:.3f}")
    
    print(f"\n🎉 Demo completed successfully!")
    print("📁 Generated files:")
    print("   • demo_image_*.jpg (sample images)")
    print("   • demo_export_*.* (export samples)")
    print("   • image_analysis_results.png (visualization)")
    
    print(f"\n💡 Next steps:")
    print("   • Try the Streamlit UI: python image_analysis_insights_ui.py")
    print("   • Test the API endpoints: see api/endpoints/image_analysis.py")
    print("   • Run comprehensive tests: python test_image_analysis_insights.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()