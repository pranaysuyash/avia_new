#!/usr/bin/env python3
"""
Test data generator for creating comprehensive test datasets
Creates known audio samples, transcriptions, and entity extractions for testing
"""

import os
import json
import wave
import numpy as np
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Any

class TestDataGenerator:
    """Generate test data for comprehensive testing"""
    
    def __init__(self, output_dir: str = "test_data"):
        """Initialize test data generator"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "audio").mkdir(exist_ok=True)
        (self.output_dir / "transcripts").mkdir(exist_ok=True)
        (self.output_dir / "entities").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
    
    def generate_test_audio(self, filename: str, duration: float, 
                           frequency: float = 440, sample_rate: int = 16000) -> str:
        """Generate a test audio file with sine wave"""
        audio_path = self.output_dir / "audio" / f"{filename}.wav"
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(str(audio_path), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return str(audio_path)
    
    def create_test_dataset(self) -> Dict[str, Any]:
        """Create comprehensive test dataset with known transcriptions and entities"""
        
        test_cases = [
            {
                "id": "business_meeting",
                "duration": 30,
                "frequency": 440,
                "transcript": """
                Good morning everyone. This is John Smith, CEO of TechCorp Industries. 
                Today is January 15th, 2024, and we're here in our Seattle headquarters 
                for the quarterly board meeting. We'll be discussing our Q4 results 
                with Sarah Johnson from the finance team and Michael Chen from operations.
                
                Our revenue for this quarter reached $2.5 million, which represents 
                a 25% increase from last year. We've successfully expanded to 
                New York City and Los Angeles, hiring 150 new employees.
                
                The partnership with Microsoft Corporation and Google LLC has been 
                instrumental in our growth. We're planning to invest $500,000 in 
                new technology infrastructure by March 2024.
                """.strip(),
                "expected_entities": {
                    "persons": ["John Smith", "Sarah Johnson", "Michael Chen"],
                    "organizations": ["TechCorp Industries", "Microsoft Corporation", "Google LLC"],
                    "locations": ["Seattle", "New York City", "Los Angeles"],
                    "dates": ["January 15th, 2024", "Q4", "March 2024"],
                    "money": ["$2.5 million", "$500,000"],
                    "numbers": ["25%", "150"],
                    "key_topics": ["quarterly board meeting", "revenue", "expansion", "partnership", "technology infrastructure"]
                },
                "expected_summary": "CEO John Smith discusses Q4 results showing $2.5M revenue and 25% growth, expansion to new cities, partnerships with major tech companies, and future investment plans."
            },
            {
                "id": "technical_interview",
                "duration": 45,
                "frequency": 523,  # C5 note
                "transcript": """
                Welcome to TechTalk podcast. I'm Dr. Emily Rodriguez, and today 
                I'm speaking with Professor David Kim from Stanford University 
                about artificial intelligence and machine learning.
                
                Professor Kim, you've been researching AI for over 15 years at 
                Stanford's Computer Science Department. Can you tell us about 
                your latest work on neural networks?
                
                Certainly, Emily. Our team has developed a new architecture that 
                improves accuracy by 30% while reducing computational costs by 
                40%. We published these findings in Nature AI journal last month.
                
                The implications for healthcare are significant. We're collaborating 
                with UCSF Medical Center and Johns Hopkins Hospital to implement 
                these algorithms in diagnostic imaging. The FDA approval process 
                is expected to take 18 months.
                
                Our research is funded by a $3.2 million grant from the National 
                Science Foundation, with additional support from IBM Research 
                and NVIDIA Corporation.
                """.strip(),
                "expected_entities": {
                    "persons": ["Dr. Emily Rodriguez", "Professor David Kim"],
                    "organizations": ["Stanford University", "Stanford's Computer Science Department", 
                                    "Nature AI journal", "UCSF Medical Center", "Johns Hopkins Hospital", 
                                    "FDA", "National Science Foundation", "IBM Research", "NVIDIA Corporation"],
                    "locations": ["Stanford"],
                    "dates": ["15 years", "last month", "18 months"],
                    "money": ["$3.2 million"],
                    "numbers": ["30%", "40%"],
                    "key_topics": ["artificial intelligence", "machine learning", "neural networks", 
                                 "healthcare", "diagnostic imaging", "research funding"]
                },
                "expected_summary": "Dr. Rodriguez interviews Professor Kim about AI research at Stanford, discussing new neural network architecture with improved performance, healthcare applications, and research funding."
            },
            {
                "id": "customer_service",
                "duration": 20,
                "frequency": 330,  # E4 note
                "transcript": """
                Thank you for calling DataSoft Solutions customer support. 
                This is Jennifer Martinez. How can I help you today?
                
                Hi Jennifer, this is Robert Thompson from Acme Corporation. 
                I'm having issues with our software license that expires on 
                December 31st, 2024. Our account number is DS-12345.
                
                Let me look that up for you, Mr. Thompson. I see your account 
                here. You have a Premium Enterprise license for 500 users. 
                The annual fee is $15,000, and it's due for renewal.
                
                We'd like to upgrade to the Platinum package which supports 
                1,000 users. What would be the cost difference?
                
                The Platinum package is $25,000 annually, so the difference 
                would be $10,000. I can process that upgrade today and extend 
                your license through December 31st, 2025.
                
                Perfect. Please proceed with the upgrade. Our billing address 
                is 123 Business Park Drive, Austin, Texas 78701.
                """.strip(),
                "expected_entities": {
                    "persons": ["Jennifer Martinez", "Robert Thompson"],
                    "organizations": ["DataSoft Solutions", "Acme Corporation"],
                    "locations": ["Austin, Texas"],
                    "dates": ["December 31st, 2024", "December 31st, 2025"],
                    "money": ["$15,000", "$25,000", "$10,000"],
                    "numbers": ["DS-12345", "500", "1,000", "123 Business Park Drive", "78701"],
                    "key_topics": ["customer support", "software license", "renewal", "upgrade", "billing"]
                },
                "expected_summary": "Customer service call where Jennifer helps Robert from Acme Corporation upgrade their software license from Premium to Platinum package."
            },
            {
                "id": "medical_consultation",
                "duration": 35,
                "frequency": 392,  # G4 note
                "transcript": """
                Good afternoon, Mrs. Anderson. I'm Dr. Patricia Williams from 
                City General Hospital. Thank you for coming in today for your 
                follow-up appointment on February 20th, 2024.
                
                How have you been feeling since your surgery on January 8th? 
                Are you taking the prescribed medications - the 10mg Lisinopril 
                twice daily and 5mg Metformin once daily?
                
                Yes, doctor. I've been taking them as prescribed. My blood 
                pressure has been around 120/80, and my blood sugar levels 
                have improved significantly.
                
                Excellent. Your lab results from February 15th show your 
                cholesterol is down to 180 mg/dL, which is much better than 
                the 240 mg/dL we saw three months ago.
                
                I'd like to schedule your next appointment for May 20th, 2024. 
                Please continue with your current medications and maintain 
                the diet plan we discussed. The nutritionist, Ms. Sarah Chen, 
                will follow up with you next week.
                
                If you have any concerns, please call our office at 
                555-MEDICAL or visit our website at citygeneral.org.
                """.strip(),
                "expected_entities": {
                    "persons": ["Mrs. Anderson", "Dr. Patricia Williams", "Ms. Sarah Chen"],
                    "organizations": ["City General Hospital"],
                    "locations": ["City General Hospital"],
                    "dates": ["February 20th, 2024", "January 8th", "February 15th", "three months ago", "May 20th, 2024", "next week"],
                    "money": [],
                    "numbers": ["10mg", "5mg", "120/80", "180 mg/dL", "240 mg/dL", "555-MEDICAL"],
                    "key_topics": ["follow-up appointment", "surgery", "medications", "blood pressure", "blood sugar", "cholesterol", "diet plan"]
                },
                "expected_summary": "Dr. Williams conducts follow-up appointment with Mrs. Anderson, reviewing post-surgery progress, medication compliance, and improved lab results."
            },
            {
                "id": "educational_lecture",
                "duration": 60,
                "frequency": 261,  # C4 note
                "transcript": """
                Welcome to Introduction to Environmental Science, lecture 15. 
                I'm Professor Maria Gonzalez from UC Berkeley's Environmental 
                Science Department. Today is March 10th, 2024, and we're 
                discussing climate change impacts on biodiversity.
                
                As we've learned, global temperatures have risen by 1.1 degrees 
                Celsius since the Industrial Revolution. This warming has led 
                to significant changes in ecosystems worldwide.
                
                The Arctic ice cap has lost approximately 13% of its mass per 
                decade since 1979. This affects polar bear populations, which 
                have declined by 30% in the last 20 years according to the 
                World Wildlife Fund.
                
                In tropical regions, coral reefs are experiencing widespread 
                bleaching. The Great Barrier Reef in Australia has lost 50% 
                of its coral cover since 1995. The Australian Institute of 
                Marine Science published these findings in Science Magazine.
                
                Deforestation in the Amazon rainforest continues at an alarming 
                rate. Brazil reported losing 10,000 square kilometers of forest 
                in 2023, equivalent to an area larger than Lebanon.
                
                For next week's assignment, please read chapters 12-14 in your 
                textbook and prepare a 500-word essay on conservation strategies. 
                The deadline is March 17th, 2024.
                
                Office hours are Tuesdays and Thursdays from 2-4 PM in room 
                301 of the Life Sciences Building. My email is mgonzalez@berkeley.edu.
                """.strip(),
                "expected_entities": {
                    "persons": ["Professor Maria Gonzalez"],
                    "organizations": ["UC Berkeley", "Environmental Science Department", "World Wildlife Fund", 
                                    "Australian Institute of Marine Science", "Science Magazine"],
                    "locations": ["UC Berkeley", "Arctic", "Australia", "Great Barrier Reef", "Amazon rainforest", 
                                "Brazil", "Lebanon", "Life Sciences Building"],
                    "dates": ["March 10th, 2024", "Industrial Revolution", "1979", "20 years", "1995", 
                            "2023", "March 17th, 2024", "Tuesdays", "Thursdays"],
                    "money": [],
                    "numbers": ["15", "1.1 degrees Celsius", "13%", "30%", "50%", "10,000 square kilometers", 
                              "12-14", "500-word", "2-4 PM", "301"],
                    "key_topics": ["environmental science", "climate change", "biodiversity", "global warming", 
                                 "ecosystems", "polar bears", "coral reefs", "deforestation", "conservation"]
                },
                "expected_summary": "Professor Gonzalez lectures on climate change impacts including Arctic ice loss, polar bear decline, coral reef bleaching, and Amazon deforestation, with assignment details."
            }
        ]
        
        # Generate audio files and save metadata
        dataset = {
            "metadata": {
                "created_date": "2024-01-01",
                "version": "1.0",
                "description": "Comprehensive test dataset for audio transcription and entity extraction",
                "total_cases": len(test_cases)
            },
            "test_cases": []
        }
        
        for case in test_cases:
            # Generate audio file
            audio_path = self.generate_test_audio(
                case["id"], 
                case["duration"], 
                case["frequency"]
            )
            
            # Save transcript
            transcript_path = self.output_dir / "transcripts" / f"{case['id']}.txt"
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(case["transcript"])
            
            # Save expected entities
            entities_path = self.output_dir / "entities" / f"{case['id']}.json"
            with open(entities_path, 'w', encoding='utf-8') as f:
                json.dump(case["expected_entities"], f, indent=2, ensure_ascii=False)
            
            # Add to dataset
            dataset["test_cases"].append({
                "id": case["id"],
                "audio_file": str(audio_path),
                "transcript_file": str(transcript_path),
                "entities_file": str(entities_path),
                "duration": case["duration"],
                "frequency": case["frequency"],
                "word_count": len(case["transcript"].split()),
                "character_count": len(case["transcript"]),
                "expected_entity_count": sum(len(v) for v in case["expected_entities"].values()),
                "expected_summary": case["expected_summary"]
            })
        
        # Save dataset metadata
        dataset_path = self.output_dir / "metadata" / "dataset.json"
        with open(dataset_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        return dataset
    
    def create_edge_case_data(self) -> Dict[str, Any]:
        """Create edge case test data for robustness testing"""
        
        edge_cases = [
            {
                "id": "empty_audio",
                "duration": 0.1,
                "frequency": 0,  # Silence
                "transcript": "",
                "expected_entities": {},
                "expected_summary": "No content to analyze"
            },
            {
                "id": "very_short",
                "duration": 1,
                "frequency": 440,
                "transcript": "Hi.",
                "expected_entities": {},
                "expected_summary": "Very brief greeting"
            },
            {
                "id": "numbers_only",
                "duration": 10,
                "frequency": 440,
                "transcript": "123 456 789 2024 $1000 25% 3.14159",
                "expected_entities": {
                    "numbers": ["123", "456", "789", "2024", "25%", "3.14159"],
                    "money": ["$1000"]
                },
                "expected_summary": "Sequence of numbers and monetary values"
            },
            {
                "id": "special_characters",
                "duration": 15,
                "frequency": 440,
                "transcript": "Email: test@example.com, Website: https://example.org, Phone: +1-555-123-4567",
                "expected_entities": {
                    "numbers": ["+1-555-123-4567"]
                },
                "expected_summary": "Contact information with email, website, and phone number"
            },
            {
                "id": "multilingual_names",
                "duration": 20,
                "frequency": 440,
                "transcript": "José García from México, François Dubois from France, and 李明 from China attended the meeting.",
                "expected_entities": {
                    "persons": ["José García", "François Dubois", "李明"],
                    "locations": ["México", "France", "China"]
                },
                "expected_summary": "International meeting with participants from Mexico, France, and China"
            },
            {
                "id": "very_long_text",
                "duration": 120,
                "frequency": 440,
                "transcript": "This is a very long text that repeats the same information multiple times. " * 100,
                "expected_entities": {},
                "expected_summary": "Repetitive text with no specific entities or meaningful content"
            }
        ]
        
        # Generate edge case dataset
        edge_dataset = {
            "metadata": {
                "created_date": "2024-01-01",
                "version": "1.0",
                "description": "Edge case test dataset for robustness testing",
                "total_cases": len(edge_cases)
            },
            "edge_cases": []
        }
        
        for case in edge_cases:
            # Generate audio file (or silence for empty case)
            if case["frequency"] == 0:
                audio_path = self.generate_silence(case["id"], case["duration"])
            else:
                audio_path = self.generate_test_audio(
                    f"edge_{case['id']}", 
                    case["duration"], 
                    case["frequency"]
                )
            
            # Save transcript
            transcript_path = self.output_dir / "transcripts" / f"edge_{case['id']}.txt"
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(case["transcript"])
            
            # Save expected entities
            entities_path = self.output_dir / "entities" / f"edge_{case['id']}.json"
            with open(entities_path, 'w', encoding='utf-8') as f:
                json.dump(case["expected_entities"], f, indent=2, ensure_ascii=False)
            
            # Add to dataset
            edge_dataset["edge_cases"].append({
                "id": case["id"],
                "audio_file": str(audio_path),
                "transcript_file": str(transcript_path),
                "entities_file": str(entities_path),
                "duration": case["duration"],
                "word_count": len(case["transcript"].split()) if case["transcript"] else 0,
                "character_count": len(case["transcript"]),
                "expected_entity_count": sum(len(v) for v in case["expected_entities"].values()),
                "expected_summary": case["expected_summary"]
            })
        
        # Save edge case dataset metadata
        edge_dataset_path = self.output_dir / "metadata" / "edge_cases.json"
        with open(edge_dataset_path, 'w', encoding='utf-8') as f:
            json.dump(edge_dataset, f, indent=2, ensure_ascii=False)
        
        return edge_dataset
    
    def generate_silence(self, filename: str, duration: float, sample_rate: int = 16000) -> str:
        """Generate a silent audio file"""
        audio_path = self.output_dir / "audio" / f"{filename}.wav"
        
        # Generate silence (zeros)
        audio_data = np.zeros(int(sample_rate * duration), dtype=np.int16)
        
        # Write WAV file
        with wave.open(str(audio_path), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return str(audio_path)
    
    def create_performance_test_data(self) -> Dict[str, Any]:
        """Create test data specifically for performance testing"""
        
        performance_cases = [
            {"id": "perf_small", "duration": 5, "text_multiplier": 1},
            {"id": "perf_medium", "duration": 30, "text_multiplier": 5},
            {"id": "perf_large", "duration": 60, "text_multiplier": 15},
            {"id": "perf_xlarge", "duration": 120, "text_multiplier": 30}
        ]
        
        base_text = """
        This is a performance test transcript with various entities for testing. 
        John Smith from Microsoft Corporation in Seattle discussed quarterly results 
        on January 15th, 2024. The revenue reached $1.5 million with 20% growth.
        """
        
        performance_dataset = {
            "metadata": {
                "created_date": "2024-01-01",
                "version": "1.0",
                "description": "Performance test dataset with varying sizes",
                "total_cases": len(performance_cases)
            },
            "performance_cases": []
        }
        
        for case in performance_cases:
            # Generate scaled text
            scaled_text = (base_text.strip() + " ") * case["text_multiplier"]
            
            # Generate audio file
            audio_path = self.generate_test_audio(
                f"perf_{case['id']}", 
                case["duration"], 
                440  # Standard frequency
            )
            
            # Save transcript
            transcript_path = self.output_dir / "transcripts" / f"perf_{case['id']}.txt"
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(scaled_text)
            
            # Add to dataset
            performance_dataset["performance_cases"].append({
                "id": case["id"],
                "audio_file": str(audio_path),
                "transcript_file": str(transcript_path),
                "duration": case["duration"],
                "text_multiplier": case["text_multiplier"],
                "word_count": len(scaled_text.split()),
                "character_count": len(scaled_text)
            })
        
        # Save performance dataset metadata
        perf_dataset_path = self.output_dir / "metadata" / "performance_cases.json"
        with open(perf_dataset_path, 'w', encoding='utf-8') as f:
            json.dump(performance_dataset, f, indent=2, ensure_ascii=False)
        
        return performance_dataset
    
    def generate_all_test_data(self) -> Dict[str, Any]:
        """Generate all test datasets"""
        print("Generating comprehensive test datasets...")
        
        # Create main test dataset
        print("Creating main test dataset...")
        main_dataset = self.create_test_dataset()
        
        # Create edge case dataset
        print("Creating edge case dataset...")
        edge_dataset = self.create_edge_case_data()
        
        # Create performance test dataset
        print("Creating performance test dataset...")
        performance_dataset = self.create_performance_test_data()
        
        # Create combined metadata
        combined_metadata = {
            "metadata": {
                "created_date": "2024-01-01",
                "version": "1.0",
                "description": "Complete test dataset collection",
                "datasets": {
                    "main": main_dataset["metadata"],
                    "edge_cases": edge_dataset["metadata"],
                    "performance": performance_dataset["metadata"]
                }
            },
            "summary": {
                "total_audio_files": (
                    main_dataset["metadata"]["total_cases"] + 
                    edge_dataset["metadata"]["total_cases"] + 
                    performance_dataset["metadata"]["total_cases"]
                ),
                "total_transcripts": (
                    main_dataset["metadata"]["total_cases"] + 
                    edge_dataset["metadata"]["total_cases"] + 
                    performance_dataset["metadata"]["total_cases"]
                ),
                "total_entity_files": (
                    main_dataset["metadata"]["total_cases"] + 
                    edge_dataset["metadata"]["total_cases"]
                )
            }
        }
        
        # Save combined metadata
        combined_path = self.output_dir / "metadata" / "complete_dataset.json"
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump(combined_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Test data generation complete!")
        print(f"   Output directory: {self.output_dir}")
        print(f"   Total audio files: {combined_metadata['summary']['total_audio_files']}")
        print(f"   Total transcripts: {combined_metadata['summary']['total_transcripts']}")
        print(f"   Total entity files: {combined_metadata['summary']['total_entity_files']}")
        
        return combined_metadata


def main():
    """Generate all test data"""
    generator = TestDataGenerator()
    generator.generate_all_test_data()


if __name__ == "__main__":
    main()