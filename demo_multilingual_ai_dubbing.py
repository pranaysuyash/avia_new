"""
Demo script for Multilingual AI Dubbing System
Demonstrates voice cloning, lip-sync generation, and quality assessment
"""

import asyncio
import os
import tempfile
import logging
from pathlib import Path
import numpy as np
import json
from datetime import datetime

from multilingual_ai_dubbing_system import (
    MultilingualAIDubbingSystem,
    VoiceProfile,
    SpeakerMapping,
    LipSyncConfig,
    DubbingJob,
    create_default_config
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultilingualDubbingDemo:
    """Demo class showcasing the dubbing system capabilities"""
    
    def __init__(self):
        self.config = create_default_config()
        self.dubbing_system = None
        self.demo_data_dir = Path("demo_data")
        self.demo_data_dir.mkdir(exist_ok=True)
    
    async def initialize_system(self):
        """Initialize the dubbing system"""
        try:
            logger.info("Initializing Multilingual AI Dubbing System...")
            self.dubbing_system = MultilingualAIDubbingSystem(self.config)
            logger.info("✅ System initialized successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def demo_voice_cloning(self):
        """Demonstrate voice cloning capabilities"""
        logger.info("\n🎤 === Voice Cloning Demo ===")
        
        try:
            # Create sample voice profiles
            voice_profiles = []
            
            # Demo voice profile 1 - Male English
            logger.info("Creating male English voice profile...")
            male_profile = VoiceProfile(
                voice_id="demo_male_en",
                name="Demo Male English",
                language="en",
                gender="male",
                age_range="adult",
                voice_samples=["demo_male_sample.wav"],  # Would be actual files
                quality_score=0.92
            )
            voice_profiles.append(male_profile)
            
            # Demo voice profile 2 - Female Spanish
            logger.info("Creating female Spanish voice profile...")
            female_profile = VoiceProfile(
                voice_id="demo_female_es",
                name="Demo Female Spanish",
                language="es",
                gender="female",
                age_range="adult",
                voice_samples=["demo_female_sample.wav"],  # Would be actual files
                quality_score=0.88
            )
            voice_profiles.append(female_profile)
            
            # Store profiles
            for profile in voice_profiles:
                self.dubbing_system.voice_cloning_engine.voice_profiles[profile.voice_id] = profile
            
            logger.info(f"✅ Created {len(voice_profiles)} voice profiles")
            
            # Demonstrate voice cloning
            test_texts = [
                "Hello, this is a demonstration of voice cloning technology.",
                "The weather today is absolutely beautiful and perfect for a walk.",
                "Artificial intelligence is transforming how we create and consume media."
            ]
            
            for i, text in enumerate(test_texts):
                logger.info(f"Cloning voice for text {i+1}: '{text[:50]}...'")
                
                # Clone with male voice
                try:
                    male_audio = await self.dubbing_system.voice_cloning_engine.clone_voice(
                        text, male_profile
                    )
                    logger.info(f"  ✅ Male voice cloned: {male_audio}")
                except Exception as e:
                    logger.warning(f"  ⚠️ Male voice cloning failed: {e}")
                
                # Clone with female voice
                try:
                    female_audio = await self.dubbing_system.voice_cloning_engine.clone_voice(
                        text, female_profile
                    )
                    logger.info(f"  ✅ Female voice cloned: {female_audio}")
                except Exception as e:
                    logger.warning(f"  ⚠️ Female voice cloning failed: {e}")
            
            return voice_profiles
            
        except Exception as e:
            logger.error(f"❌ Voice cloning demo failed: {e}")
            return []
    
    async def demo_speaker_identification(self):
        """Demonstrate speaker identification and diarization"""
        logger.info("\n👥 === Speaker Identification Demo ===")
        
        try:
            # Simulate audio file with multiple speakers
            demo_audio_path = "demo_conversation.wav"
            
            logger.info(f"Analyzing speakers in: {demo_audio_path}")
            
            # Identify speakers
            speakers = await self.dubbing_system.multi_speaker_manager.identify_speakers(
                demo_audio_path
            )
            
            logger.info(f"✅ Identified {len(speakers)} speakers:")
            
            for speaker in speakers:
                logger.info(f"  Speaker {speaker['speaker_id']}:")
                logger.info(f"    - Total duration: {speaker['total_duration']:.1f}s")
                logger.info(f"    - Segments: {len(speaker['segments'])}")
                logger.info(f"    - Characteristics: {speaker['characteristics']}")
            
            return speakers
            
        except Exception as e:
            logger.error(f"❌ Speaker identification demo failed: {e}")
            return []
    
    async def demo_lip_sync_generation(self):
        """Demonstrate lip-sync generation with different models"""
        logger.info("\n💋 === Lip-Sync Generation Demo ===")
        
        try:
            # Demo video and audio files
            demo_video = "demo_video.mp4"
            demo_audio = "demo_dubbed_audio.wav"
            
            # Test different lip-sync models
            models = ["musetalk", "wav2lip", "float"]
            quality_levels = ["medium", "high"]
            
            results = {}
            
            for model in models:
                for quality in quality_levels:
                    config_name = f"{model}_{quality}"
                    logger.info(f"Testing {config_name}...")
                    
                    # Create lip-sync configuration
                    lip_sync_config = LipSyncConfig(
                        model_type=model,
                        quality_level=quality,
                        fps=30,
                        resolution=(1920, 1080),
                        face_enhancement=True,
                        temporal_consistency=True,
                        emotion_preservation=True
                    )
                    
                    try:
                        # Generate lip-sync
                        start_time = datetime.now()
                        
                        output_path = await self.dubbing_system.lip_sync_generator.generate_lip_sync(
                            demo_video, demo_audio, lip_sync_config
                        )
                        
                        processing_time = (datetime.now() - start_time).total_seconds()
                        
                        results[config_name] = {
                            "output_path": output_path,
                            "processing_time": processing_time,
                            "config": lip_sync_config,
                            "success": True
                        }
                        
                        logger.info(f"  ✅ {config_name}: {processing_time:.1f}s -> {output_path}")
                        
                    except Exception as e:
                        results[config_name] = {
                            "error": str(e),
                            "success": False
                        }
                        logger.warning(f"  ⚠️ {config_name} failed: {e}")
            
            # Summary
            successful_configs = [k for k, v in results.items() if v.get("success")]
            logger.info(f"✅ Successfully generated lip-sync with {len(successful_configs)} configurations")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Lip-sync generation demo failed: {e}")
            return {}
    
    async def demo_quality_assessment(self):
        """Demonstrate quality assessment and correction"""
        logger.info("\n📊 === Quality Assessment Demo ===")
        
        try:
            # Simulate quality assessment on generated content
            demo_original = "demo_original.mp4"
            demo_dubbed = "demo_dubbed.mp4"
            demo_audio = "demo_dubbed_audio.wav"
            
            logger.info("Assessing dubbing quality...")
            
            # Perform quality assessment
            quality_metrics = await self.dubbing_system.quality_assessment.assess_dubbing_quality(
                demo_original, demo_dubbed, demo_audio
            )
            
            logger.info("Quality Assessment Results:")
            logger.info(f"  📈 Lip-sync accuracy: {quality_metrics['lip_sync_accuracy']:.3f}")
            logger.info(f"  🎤 Voice quality: {quality_metrics['voice_quality']:.3f}")
            logger.info(f"  🎥 Visual quality: {quality_metrics['visual_quality']:.3f}")
            logger.info(f"  ⏱️ Temporal consistency: {quality_metrics['temporal_consistency']:.3f}")
            logger.info(f"  🏆 Overall score: {quality_metrics['overall_score']:.3f}")
            
            # Quality recommendations
            recommendations = []
            
            if quality_metrics['lip_sync_accuracy'] < 0.8:
                recommendations.append("Consider re-generating lip-sync with higher quality settings")
            
            if quality_metrics['voice_quality'] < 0.8:
                recommendations.append("Voice samples may need improvement or noise reduction")
            
            if quality_metrics['visual_quality'] < 0.8:
                recommendations.append("Apply video enhancement or use higher resolution")
            
            if quality_metrics['temporal_consistency'] < 0.8:
                recommendations.append("Enable temporal consistency in lip-sync configuration")
            
            if recommendations:
                logger.info("📋 Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    logger.info(f"  {i}. {rec}")
            else:
                logger.info("✅ Quality meets all standards!")
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"❌ Quality assessment demo failed: {e}")
            return {}
    
    async def demo_complete_dubbing_workflow(self):
        """Demonstrate complete end-to-end dubbing workflow"""
        logger.info("\n🎬 === Complete Dubbing Workflow Demo ===")
        
        try:
            # Create a complete dubbing job
            demo_video = "demo_input_video.mp4"
            
            logger.info("Creating dubbing job...")
            
            # Create dubbing job
            job = await self.dubbing_system.create_dubbing_job(
                video_path=demo_video,
                target_language="es",
                source_language="en"
            )
            
            logger.info(f"✅ Created job: {job.job_id}")
            
            # Process the job
            logger.info("Processing dubbing job...")
            
            result = await self.dubbing_system.process_dubbing_job(job)
            
            logger.info("🎉 Dubbing workflow completed!")
            logger.info(f"  📁 Output video: {result['output_video_path']}")
            logger.info(f"  🎵 Dubbed audio: {result['dubbed_audio_path']}")
            logger.info(f"  ⏱️ Processing time: {result['processing_time']:.1f}s")
            logger.info(f"  👥 Speakers found: {len(result['speakers'])}")
            logger.info(f"  🏆 Quality score: {result['quality_metrics']['overall_score']:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Complete workflow demo failed: {e}")
            return None
    
    async def demo_real_time_processing(self):
        """Demonstrate real-time dubbing capabilities"""
        logger.info("\n⚡ === Real-Time Processing Demo ===")
        
        if not self.config.get("enable_real_time", False):
            logger.info("⚠️ Real-time processing is disabled in configuration")
            return
        
        try:
            logger.info("Simulating real-time audio stream...")
            
            # Simulate audio stream chunks
            audio_chunks = [
                "Hello, this is the first chunk of audio.",
                "This is the second chunk, continuing the conversation.",
                "And this is the final chunk of our demonstration."
            ]
            
            target_language = "fr"
            
            for i, chunk in enumerate(audio_chunks):
                logger.info(f"Processing chunk {i+1}: '{chunk[:30]}...'")
                
                # Simulate real-time processing
                start_time = datetime.now()
                
                # In real implementation, this would process actual audio stream
                processed_chunk = await self.dubbing_system.process_real_time_dubbing(
                    chunk, target_language
                )
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"  ✅ Processed in {processing_time:.3f}s")
            
            logger.info("✅ Real-time processing demo completed")
            
        except Exception as e:
            logger.error(f"❌ Real-time processing demo failed: {e}")
    
    async def demo_multi_language_support(self):
        """Demonstrate multi-language dubbing capabilities"""
        logger.info("\n🌍 === Multi-Language Support Demo ===")
        
        try:
            # Test multiple language pairs
            language_pairs = [
                ("en", "es"),  # English to Spanish
                ("en", "fr"),  # English to French
                ("en", "de"),  # English to German
                ("es", "en"),  # Spanish to English
                ("fr", "ja"),  # French to Japanese
            ]
            
            demo_text = "This is a demonstration of multilingual dubbing capabilities."
            
            for source_lang, target_lang in language_pairs:
                logger.info(f"Testing {source_lang} → {target_lang}")
                
                try:
                    # Create a simple transcript
                    transcript = {
                        "segments": [{
                            "start": 0.0,
                            "end": 5.0,
                            "text": demo_text,
                            "speaker": "speaker_0"
                        }],
                        "language": source_lang
                    }
                    
                    # Translate
                    translated = await self.dubbing_system.translate_transcript(
                        transcript, target_lang
                    )
                    
                    logger.info(f"  ✅ Original: {transcript['segments'][0]['text'][:50]}...")
                    logger.info(f"  ✅ Translated: {translated['segments'][0]['text'][:50]}...")
                    
                except Exception as e:
                    logger.warning(f"  ⚠️ Translation failed: {e}")
            
            logger.info("✅ Multi-language support demo completed")
            
        except Exception as e:
            logger.error(f"❌ Multi-language demo failed: {e}")
    
    def generate_demo_report(self, results: dict):
        """Generate a comprehensive demo report"""
        logger.info("\n📋 === Demo Report ===")
        
        report = {
            "demo_timestamp": datetime.now().isoformat(),
            "system_config": self.config,
            "results": results,
            "summary": {
                "total_tests": len(results),
                "successful_tests": len([r for r in results.values() if r.get("success", False)]),
                "failed_tests": len([r for r in results.values() if not r.get("success", True)])
            }
        }
        
        # Save report
        report_path = self.demo_data_dir / f"demo_report_{int(datetime.now().timestamp())}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Demo report saved: {report_path}")
        
        # Print summary
        logger.info("Demo Summary:")
        logger.info(f"  ✅ Successful tests: {report['summary']['successful_tests']}")
        logger.info(f"  ❌ Failed tests: {report['summary']['failed_tests']}")
        logger.info(f"  📊 Success rate: {report['summary']['successful_tests']/report['summary']['total_tests']*100:.1f}%")
        
        return report
    
    async def run_complete_demo(self):
        """Run the complete demonstration"""
        logger.info("🚀 Starting Multilingual AI Dubbing System Demo")
        logger.info("=" * 60)
        
        results = {}
        
        # Initialize system
        if not await self.initialize_system():
            logger.error("❌ Cannot proceed without system initialization")
            return
        
        # Run all demos
        demos = [
            ("voice_cloning", self.demo_voice_cloning),
            ("speaker_identification", self.demo_speaker_identification),
            ("lip_sync_generation", self.demo_lip_sync_generation),
            ("quality_assessment", self.demo_quality_assessment),
            ("complete_workflow", self.demo_complete_dubbing_workflow),
            ("real_time_processing", self.demo_real_time_processing),
            ("multi_language_support", self.demo_multi_language_support),
        ]
        
        for demo_name, demo_func in demos:
            try:
                logger.info(f"\n🔄 Running {demo_name} demo...")
                result = await demo_func()
                results[demo_name] = {
                    "success": True,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"✅ {demo_name} demo completed successfully")
                
            except Exception as e:
                results[demo_name] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                logger.error(f"❌ {demo_name} demo failed: {e}")
        
        # Generate report
        report = self.generate_demo_report(results)
        
        # Cleanup
        self.dubbing_system.cleanup_temp_files()
        
        logger.info("\n🎉 Demo completed!")
        logger.info("=" * 60)
        
        return report

async def main():
    """Main demo entry point"""
    demo = MultilingualDubbingDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    asyncio.run(main())