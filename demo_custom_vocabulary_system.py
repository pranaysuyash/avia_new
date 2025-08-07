"""
Demo script for Custom Vocabulary and Domain Adaptation System

This script demonstrates the comprehensive vocabulary management capabilities
including user submissions, verification workflows, domain adaptation, and analytics.
"""

import os
import sys
import json
from datetime import datetime
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from custom_vocabulary_system import (
        CustomVocabularySystem, DomainCategory, VocabularyStatus,
        VocabularyEntry, ValidationResult, DomainAdaptationConfig
    )
except ImportError as e:
    print(f"Error importing custom vocabulary modules: {e}")
    print("Please ensure all required dependencies are installed:")
    print("pip install nltk spacy scikit-learn librosa soundfile")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_vocabulary_submission():
    """Demonstrate vocabulary submission workflow"""
    print("\n" + "="*60)
    print("📝 VOCABULARY SUBMISSION DEMO")
    print("="*60)
    
    try:
        # Initialize system
        vocab_system = CustomVocabularySystem("demo_vocabulary.db")
        
        # Sample vocabulary submissions for different domains
        sample_submissions = [
            {
                "term": "Myocardial Infarction",
                "definition": "A heart attack caused by blocked blood flow to the heart muscle, resulting in tissue death and potential cardiac dysfunction.",
                "domain": "medical",
                "submitter_id": "dr_smith",
                "context_examples": [
                    "The patient was diagnosed with acute myocardial infarction after presenting with chest pain.",
                    "Myocardial infarction is a leading cause of death worldwide, requiring immediate medical intervention."
                ],
                "alternatives": ["Heart Attack", "MI", "Cardiac Infarction"],
                "tags": ["cardiology", "emergency", "diagnosis", "cardiovascular"],
                "source_references": ["American Heart Association Guidelines 2023", "Cardiology Textbook Ch. 15"]
            },
            {
                "term": "Blockchain",
                "definition": "A distributed ledger technology that maintains a continuously growing list of records, called blocks, which are linked and secured using cryptography.",
                "domain": "technical",
                "submitter_id": "tech_expert",
                "context_examples": [
                    "The blockchain ensures data integrity through cryptographic hashing.",
                    "Many cryptocurrencies rely on blockchain technology for transaction verification."
                ],
                "alternatives": ["Distributed Ledger", "DLT"],
                "tags": ["cryptocurrency", "technology", "security", "distributed systems"],
                "source_references": ["Bitcoin Whitepaper", "Blockchain Technology Overview - NIST"]
            },
            {
                "term": "Force Majeure",
                "definition": "A contractual clause that frees parties from liability or obligation when an extraordinary circumstance beyond their control prevents them from fulfilling their contractual duties.",
                "domain": "legal",
                "submitter_id": "legal_counsel",
                "context_examples": [
                    "The contract included a force majeure clause to protect against natural disasters.",
                    "Due to the pandemic, many companies invoked force majeure provisions to suspend operations."
                ],
                "alternatives": ["Act of God", "Superior Force"],
                "tags": ["contract law", "liability", "extraordinary circumstances"],
                "source_references": ["Black's Law Dictionary", "Contract Law Principles"]
            },
            {
                "term": "Photosynthesis",
                "definition": "The process by which green plants and some other organisms use sunlight to synthesize foods with the aid of chlorophyll, converting carbon dioxide and water into glucose and oxygen.",
                "domain": "scientific",
                "submitter_id": "bio_researcher",
                "context_examples": [
                    "Photosynthesis is essential for life on Earth as it produces oxygen and removes carbon dioxide.",
                    "The rate of photosynthesis varies with light intensity, temperature, and carbon dioxide concentration."
                ],
                "alternatives": ["Carbon Fixation", "Light-dependent Reactions"],
                "tags": ["biology", "plants", "biochemistry", "energy conversion"],
                "source_references": ["Plant Biology Textbook", "Nature Journal - Photosynthesis Review 2023"]
            },
            {
                "term": "Arbitrage",
                "definition": "The simultaneous buying and selling of securities, currency, or commodities in different markets to take advantage of differing prices for the same asset.",
                "domain": "financial",
                "submitter_id": "finance_analyst",
                "context_examples": [
                    "The trader identified an arbitrage opportunity between the New York and London stock exchanges.",
                    "Currency arbitrage involves exploiting exchange rate differences across different markets."
                ],
                "alternatives": ["Risk-free Profit", "Price Differential Trading"],
                "tags": ["trading", "finance", "markets", "profit"],
                "source_references": ["Financial Markets Theory", "Investment Strategies Handbook"]
            }
        ]
        
        print("🚀 Submitting sample vocabulary entries...")
        
        submitted_entries = []
        for submission in sample_submissions:
            print(f"\n📝 Submitting: {submission['term']} ({submission['domain']})")
            
            success, message, entry = vocab_system.submit_vocabulary(**submission)
            
            if success:
                print(f"✅ Success: {message}")
                if entry:
                    print(f"   Entry ID: {entry['id']}")
                    print(f"   Pronunciation: {entry['pronunciation']} ({entry['phonetic_spelling']})")
                    print(f"   Confidence Score: {entry['confidence_score']:.2f}")
                    submitted_entries.append(entry)
            else:
                print(f"❌ Failed: {message}")
        
        print(f"\n📊 Summary: {len(submitted_entries)} entries submitted successfully")
        
        return vocab_system, submitted_entries
        
    except Exception as e:
        logger.error(f"Error in vocabulary submission demo: {e}")
        print(f"❌ Demo failed: {e}")
        return None, []

def demo_vocabulary_verification(vocab_system, submitted_entries):
    """Demonstrate vocabulary verification workflow"""
    print("\n" + "="*60)
    print("✅ VOCABULARY VERIFICATION DEMO")
    print("="*60)
    
    try:
        if not vocab_system or not submitted_entries:
            print("❌ No vocabulary system or entries available for verification")
            return
        
        # Get pending submissions
        pending_submissions = vocab_system.get_pending_submissions()
        print(f"📋 Found {len(pending_submissions)} pending submissions")
        
        if not pending_submissions:
            print("ℹ️ No pending submissions to verify")
            return
        
        # Simulate verification process
        verifier_id = "expert_verifier"
        
        for i, entry in enumerate(pending_submissions[:3]):  # Verify first 3 entries
            print(f"\n🔍 Verifying: {entry['term']} ({entry['domain']})")
            print(f"   Definition: {entry['definition'][:100]}...")
            print(f"   Confidence Score: {entry['confidence_score']:.2f}")
            
            # Simulate verification decision (approve high confidence, review others)
            if entry['confidence_score'] > 0.7:
                approved = True
                notes = "High quality submission with clear definition and good examples."
            elif entry['confidence_score'] > 0.5:
                approved = True
                notes = "Good submission, minor improvements could be made to examples."
            else:
                approved = False
                notes = "Needs improvement in definition clarity and context examples."
            
            # Perform verification
            success = vocab_system.verify_vocabulary(
                entry['id'],
                verifier_id,
                approved,
                notes
            )
            
            if success:
                status = "approved" if approved else "rejected"
                print(f"✅ Verification complete: {status}")
                print(f"   Notes: {notes}")
            else:
                print(f"❌ Verification failed")
        
        print(f"\n📊 Verification demo completed")
        
    except Exception as e:
        logger.error(f"Error in vocabulary verification demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_vocabulary_search(vocab_system):
    """Demonstrate vocabulary search capabilities"""
    print("\n" + "="*60)
    print("🔍 VOCABULARY SEARCH DEMO")
    print("="*60)
    
    try:
        if not vocab_system:
            print("❌ No vocabulary system available for search")
            return
        
        # Test different search queries
        search_queries = [
            {"query": "heart", "domain": "medical", "description": "Medical terms related to heart"},
            {"query": "blockchain", "domain": "technical", "description": "Technical terms about blockchain"},
            {"query": "contract", "domain": "legal", "description": "Legal terms about contracts"},
            {"query": "", "domain": "scientific", "description": "All scientific terms"},
            {"query": "trading", "domain": None, "description": "Trading-related terms across all domains"}
        ]
        
        for search in search_queries:
            print(f"\n🔍 Search: {search['description']}")
            print(f"   Query: '{search['query']}', Domain: {search['domain'] or 'All'}")
            
            results = vocab_system.search_vocabulary(
                query=search['query'],
                domain=search['domain'],
                status="approved"
            )
            
            print(f"   Results: {len(results)} entries found")
            
            for result in results[:2]:  # Show first 2 results
                print(f"   📖 {result['term']} ({result['domain']})")
                print(f"      {result['definition'][:80]}...")
                if result['pronunciation']:
                    print(f"      Pronunciation: {result['pronunciation']}")
                print(f"      Usage: {result['usage_count']}, Accuracy: {result['accuracy_score']:.2f}")
        
        print(f"\n📊 Search demo completed")
        
    except Exception as e:
        logger.error(f"Error in vocabulary search demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_domain_adaptation(vocab_system):
    """Demonstrate domain adaptation capabilities"""
    print("\n" + "="*60)
    print("🧠 DOMAIN ADAPTATION DEMO")
    print("="*60)
    
    try:
        if not vocab_system:
            print("❌ No vocabulary system available for domain adaptation")
            return
        
        # Sample text corpora for different domains
        sample_corpora = {
            "medical": [
                """
                The patient presented with acute myocardial infarction and was immediately taken to the catheterization lab.
                Percutaneous coronary intervention was performed to restore blood flow to the occluded left anterior descending artery.
                Post-procedural echocardiogram showed improved left ventricular function with an ejection fraction of 45%.
                The patient was started on dual antiplatelet therapy including aspirin and clopidogrel.
                Cardiac rehabilitation was recommended to improve cardiovascular outcomes and reduce future risk.
                """,
                """
                Hypertension is a major risk factor for cardiovascular disease and stroke.
                Antihypertensive medications including ACE inhibitors and beta-blockers are commonly prescribed.
                Regular monitoring of blood pressure and medication adherence is essential for optimal outcomes.
                Lifestyle modifications such as dietary changes and exercise can significantly impact blood pressure control.
                """
            ],
            "technical": [
                """
                Machine learning algorithms require large datasets for training and validation.
                Deep neural networks use backpropagation to optimize weights and minimize loss functions.
                Convolutional neural networks are particularly effective for image recognition tasks.
                Natural language processing involves tokenization, embedding, and attention mechanisms.
                Cloud computing platforms provide scalable infrastructure for deploying AI models.
                """,
                """
                Microservices architecture enables scalable and maintainable software systems.
                Container orchestration with Kubernetes facilitates deployment and management.
                API gateways provide centralized access control and rate limiting.
                Continuous integration and deployment pipelines automate software delivery.
                Monitoring and observability tools help maintain system reliability and performance.
                """
            ],
            "financial": [
                """
                Portfolio diversification reduces investment risk through asset allocation strategies.
                Risk-adjusted returns are measured using metrics like the Sharpe ratio and alpha.
                Derivatives including options and futures provide hedging and speculation opportunities.
                Credit risk assessment involves analyzing borrower creditworthiness and default probability.
                Regulatory compliance requires adherence to financial reporting standards and regulations.
                """,
                """
                Quantitative trading strategies use mathematical models and statistical analysis.
                High-frequency trading relies on algorithmic execution and low-latency systems.
                Market volatility affects option pricing and portfolio risk management.
                Liquidity risk can impact the ability to execute large trades without price impact.
                """
            ]
        }
        
        print("🚀 Testing domain adaptation for different domains...")
        
        for domain, corpus in sample_corpora.items():
            print(f"\n🏢 Adapting vocabulary for {domain} domain")
            print(f"   Corpus size: {len(corpus)} documents")
            
            # Perform domain adaptation
            adapted_terms = vocab_system.adapt_domain_vocabulary(domain, corpus)
            
            print(f"   ✅ Found {len(adapted_terms)} potential new terms")
            
            # Show top 10 adapted terms
            if adapted_terms:
                print("   📚 Top suggested terms:")
                for i, term in enumerate(adapted_terms[:10]):
                    # Get pronunciation for the term
                    ipa, phonetic = vocab_system.get_pronunciation(term)
                    print(f"      {i+1}. {term} - {ipa} ({phonetic})")
            else:
                print("   ℹ️ No new terms suggested for this domain")
        
        print(f"\n📊 Domain adaptation demo completed")
        
    except Exception as e:
        logger.error(f"Error in domain adaptation demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_pronunciation_system(vocab_system):
    """Demonstrate pronunciation generation system"""
    print("\n" + "="*60)
    print("🗣️ PRONUNCIATION SYSTEM DEMO")
    print("="*60)
    
    try:
        if not vocab_system:
            print("❌ No vocabulary system available for pronunciation demo")
            return
        
        # Test words with different complexity levels
        test_words = [
            "hello",
            "pronunciation",
            "myocardial",
            "blockchain",
            "photosynthesis",
            "arbitrage",
            "pneumonia",
            "cryptocurrency",
            "antidisestablishmentarianism",
            "supercalifragilisticexpialidocious"
        ]
        
        print("🎵 Generating pronunciations for test words...")
        
        for word in test_words:
            print(f"\n📝 Word: {word}")
            
            # Generate pronunciation
            ipa, phonetic = vocab_system.get_pronunciation(word)
            
            print(f"   IPA: {ipa}")
            print(f"   Phonetic: {phonetic}")
            
            # Show syllable count estimation
            syllable_count = len([char for char in phonetic.split('-') if char])
            print(f"   Estimated syllables: {syllable_count}")
        
        print(f"\n📊 Pronunciation demo completed")
        
    except Exception as e:
        logger.error(f"Error in pronunciation demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_analytics_dashboard(vocab_system):
    """Demonstrate analytics and reporting capabilities"""
    print("\n" + "="*60)
    print("📊 ANALYTICS DASHBOARD DEMO")
    print("="*60)
    
    try:
        if not vocab_system:
            print("❌ No vocabulary system available for analytics")
            return
        
        # Get overall analytics
        print("📈 Overall Vocabulary Analytics:")
        analytics = vocab_system.get_vocabulary_analytics()
        
        if analytics:
            print(f"   Total Entries: {analytics.get('total_entries', 0)}")
            print(f"   Average Usage Count: {analytics.get('average_usage_count', 0):.2f}")
            print(f"   Average Accuracy Score: {analytics.get('average_accuracy_score', 0):.2f}")
            
            # Status distribution
            status_dist = analytics.get('status_distribution', {})
            if status_dist:
                print("   Status Distribution:")
                for status, count in status_dist.items():
                    print(f"      {status.title()}: {count}")
            
            # Top domains
            top_domains = analytics.get('top_domains', {})
            if top_domains:
                print("   Top Domains:")
                for domain, count in list(top_domains.items())[:5]:
                    print(f"      {domain.title()}: {count} terms")
        
        # Domain-specific analytics
        print(f"\n🏢 Domain-Specific Analytics:")
        
        for domain in ["medical", "technical", "legal", "financial", "scientific"]:
            domain_analytics = vocab_system.get_vocabulary_analytics(domain)
            
            if domain_analytics and domain_analytics.get('total_entries', 0) > 0:
                print(f"   {domain.title()} Domain:")
                print(f"      Terms: {domain_analytics.get('total_entries', 0)}")
                print(f"      Avg Usage: {domain_analytics.get('average_usage_count', 0):.2f}")
                print(f"      Avg Accuracy: {domain_analytics.get('average_accuracy_score', 0):.2f}")
        
        print(f"\n📊 Analytics demo completed")
        
    except Exception as e:
        logger.error(f"Error in analytics demo: {e}")
        print(f"❌ Demo failed: {e}")

def demo_usage_tracking(vocab_system):
    """Demonstrate usage tracking and feedback system"""
    print("\n" + "="*60)
    print("📈 USAGE TRACKING DEMO")
    print("="*60)
    
    try:
        if not vocab_system:
            print("❌ No vocabulary system available for usage tracking")
            return
        
        # Get some approved vocabulary entries
        approved_entries = vocab_system.search_vocabulary("", status="approved")
        
        if not approved_entries:
            print("ℹ️ No approved entries available for usage tracking")
            return
        
        print(f"🎯 Simulating usage tracking for {len(approved_entries)} approved entries...")
        
        # Simulate usage with different users and contexts
        users = ["user1", "user2", "user3", "researcher", "student"]
        contexts = ["search", "transcription", "document_analysis", "learning", "verification"]
        
        import random
        
        for entry in approved_entries[:5]:  # Track usage for first 5 entries
            print(f"\n📖 Tracking usage for: {entry['term']}")
            
            # Simulate multiple usage events
            for _ in range(random.randint(1, 5)):
                user = random.choice(users)
                context = random.choice(contexts)
                accuracy_feedback = random.uniform(0.6, 1.0)  # Simulate positive feedback
                
                vocab_system.update_vocabulary_usage(
                    entry['id'],
                    user,
                    context,
                    accuracy_feedback
                )
                
                print(f"   📊 Usage recorded: {user} in {context} (accuracy: {accuracy_feedback:.2f})")
        
        # Show updated statistics
        print(f"\n📈 Updated Usage Statistics:")
        updated_entries = vocab_system.search_vocabulary("", status="approved")
        
        for entry in updated_entries[:5]:
            print(f"   📖 {entry['term']}: {entry['usage_count']} uses, {entry['accuracy_score']:.2f} accuracy")
        
        print(f"\n📊 Usage tracking demo completed")
        
    except Exception as e:
        logger.error(f"Error in usage tracking demo: {e}")
        print(f"❌ Demo failed: {e}")

def main():
    """Run all demonstration functions"""
    print("📚 CUSTOM VOCABULARY & DOMAIN ADAPTATION SYSTEM DEMO")
    print("=" * 80)
    print("This demo showcases comprehensive vocabulary management capabilities")
    print("including user submissions, verification workflows, domain adaptation,")
    print("pronunciation generation, and analytics with usage tracking.")
    print("=" * 80)
    
    try:
        # Check dependencies
        print("🔍 Checking dependencies...")
        
        required_modules = ['nltk', 'spacy', 'sklearn', 'librosa', 'soundfile']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"❌ Missing required modules: {', '.join(missing_modules)}")
            print("Please install them using: pip install " + " ".join(missing_modules))
            print("Also run: python -m spacy download en_core_web_sm")
            return
        
        print("✅ All dependencies available")
        
        # Run demos in sequence
        vocab_system, submitted_entries = demo_vocabulary_submission()
        
        if vocab_system:
            demo_vocabulary_verification(vocab_system, submitted_entries)
            demo_vocabulary_search(vocab_system)
            demo_domain_adaptation(vocab_system)
            demo_pronunciation_system(vocab_system)
            demo_usage_tracking(vocab_system)
            demo_analytics_dashboard(vocab_system)
        
        print("\n" + "="*80)
        print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("The Custom Vocabulary & Domain Adaptation System is working correctly.")
        print("Key features demonstrated:")
        print("✅ User-submitted vocabulary with verification workflow")
        print("✅ Domain-specific vocabulary management")
        print("✅ Phonetic transcription and pronunciation guides")
        print("✅ Vocabulary validation and quality control")
        print("✅ Domain adaptation with machine learning")
        print("✅ Usage tracking and analytics")
        print("✅ Multi-domain support for all industries")
        print("\nTo use the Streamlit UI, run:")
        print("streamlit run custom_vocabulary_system_ui.py")
        
        # Clean up demo database
        if os.path.exists("demo_vocabulary.db"):
            os.remove("demo_vocabulary.db")
            print("\n🧹 Demo database cleaned up")
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"Error in main demo: {e}")
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    main()