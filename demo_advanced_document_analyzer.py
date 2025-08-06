#!/usr/bin/env python3
"""
Demo script for Advanced Document Analysis System
Demonstrates document classification, insight extraction, and advanced analysis
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import List

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_document_analyzer import (
    AdvancedDocumentAnalyzer,
    create_searchable_index,
    search_documents
)

class AdvancedDocumentAnalyzerDemo:
    """Demo class for advanced document analysis system"""
    
    def __init__(self):
        print("🚀 Initializing Advanced Document Analysis System...")
        self.analyzer = AdvancedDocumentAnalyzer()
        print("✅ System initialized successfully!")
    
    def create_sample_documents(self) -> List[str]:
        """Create sample documents for demonstration"""
        print("\\n📄 Creating sample documents...")
        
        sample_docs = {
            "invoice_sample.txt": """
            INVOICE
            
            Invoice Number: INV-2024-001
            Date: January 15, 2024
            Due Date: February 15, 2024
            
            Bill To:
            John Smith
            123 Main Street
            Anytown, NY 12345
            Email: john.smith@email.com
            Phone: (555) 123-4567
            
            From:
            ABC Corporation
            456 Business Ave
            Corporate City, CA 90210
            
            Description          Quantity    Unit Price    Total
            Web Development      40 hours    $75.00        $3,000.00
            Consulting           10 hours    $100.00       $1,000.00
            
            Subtotal:                                      $4,000.00
            Tax (8.5%):                                    $340.00
            Total Amount Due:                              $4,340.00
            
            Payment Terms: Net 30 days
            """,
            
            "contract_sample.txt": """
            SERVICE AGREEMENT
            
            This Service Agreement ("Agreement") is entered into on January 1, 2024,
            between ABC Corporation ("Company") and XYZ Services ("Contractor").
            
            TERMS AND CONDITIONS:
            
            1. Services: Contractor agrees to provide web development services
               as specified in Exhibit A.
            
            2. Payment: Company agrees to pay $5,000 per month for services.
            
            3. Term: This agreement shall commence on January 1, 2024 and
               continue for a period of 12 months.
            
            4. Confidentiality: Both parties agree to maintain confidentiality
               of proprietary information.
            
            5. Termination: Either party may terminate this agreement with
               30 days written notice.
            
            IN WITNESS WHEREOF, the parties have executed this Agreement.
            
            Company Signature: ___________________ Date: ___________
            
            Contractor Signature: ________________ Date: ___________
            """,
            
            "medical_report.txt": """
            MEDICAL CONSULTATION REPORT
            
            Patient: Jane Doe
            DOB: March 15, 1985
            Patient ID: P-12345
            Date of Visit: January 20, 2024
            
            Chief Complaint:
            Patient presents with persistent headaches and fatigue.
            
            History of Present Illness:
            The patient reports experiencing daily headaches for the past 3 weeks.
            Associated symptoms include fatigue, difficulty concentrating,
            and occasional nausea.
            
            Physical Examination:
            - Blood Pressure: 120/80 mmHg
            - Heart Rate: 72 bpm
            - Temperature: 98.6°F
            - Neurological exam: Normal
            
            Assessment and Plan:
            1. Tension headaches - likely stress-related
            2. Recommend stress management techniques
            3. Prescribe ibuprofen 400mg as needed
            4. Follow-up in 2 weeks
            
            Dr. Sarah Johnson, MD
            Internal Medicine
            License #: MD-54321
            """,
            
            "financial_statement.txt": """
            BANK STATEMENT
            
            Account Holder: John Smith
            Account Number: ****-****-****-1234
            Statement Period: December 1-31, 2023
            
            Beginning Balance:                     $5,250.00
            
            DEPOSITS:
            12/05/2023  Direct Deposit - Salary    $3,500.00
            12/15/2023  Check Deposit              $1,200.00
            12/28/2023  Transfer from Savings      $500.00
            
            WITHDRAWALS:
            12/03/2023  ATM Withdrawal             -$100.00
            12/10/2023  Online Payment - Rent      -$1,800.00
            12/15/2023  Debit Purchase - Groceries -$150.00
            12/20/2023  Check #1001 - Utilities    -$250.00
            12/25/2023  Online Transfer            -$300.00
            
            Ending Balance:                        $7,850.00
            
            For questions, contact: 1-800-BANK-123
            Online Banking: www.bank.com
            """
        }
        
        # Create temporary files
        temp_files = []
        temp_dir = Path(tempfile.gettempdir()) / "doc_analyzer_demo"
        temp_dir.mkdir(exist_ok=True)
        
        for filename, content in sample_docs.items():
            file_path = temp_dir / filename
            file_path.write_text(content.strip())
            temp_files.append(str(file_path))
            print(f"   Created: {filename}")
        
        print(f"✅ Created {len(temp_files)} sample documents")
        return temp_files
    
    def demonstrate_document_classification(self, file_paths: List[str]):
        """Demonstrate document classification"""
        print("\\n🏷️ Demonstrating Document Classification...")
        
        for file_path in file_paths:
            filename = Path(file_path).name
            print(f"\\n   Analyzing: {filename}")
            
            try:
                result = self.analyzer.analyze_document(file_path)
                classification = result.classification
                
                print(f"     Document Type: {classification.document_type}")
                print(f"     Confidence: {classification.confidence:.2f}")
                print(f"     Top Categories:")
                
                for i, category in enumerate(classification.categories[:3]):
                    print(f"       {i+1}. {category['type']}: {category['score']:.2f}")
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
    
    def demonstrate_insight_extraction(self, file_paths: List[str]):
        """Demonstrate insight extraction"""
        print("\\n🔍 Demonstrating Insight Extraction...")
        
        for file_path in file_paths[:2]:  # Analyze first 2 documents for brevity
            filename = Path(file_path).name
            print(f"\\n   Analyzing insights for: {filename}")
            
            try:
                result = self.analyzer.analyze_document(file_path)
                insights = result.insights
                
                print(f"     Language: {insights.language_detected}")
                print(f"     Readability Score: {insights.readability_score:.1f}")
                print(f"     Sentiment: {insights.sentiment.get('label', 'neutral')}")
                
                print(f"     Key Entities ({len(insights.key_entities)}):")
                for entity in insights.key_entities[:5]:  # Show top 5
                    print(f"       • {entity['text']} ({entity['label']})")
                
                print(f"     Topics ({len(insights.topics)}):")
                for topic in insights.topics[:3]:  # Show top 3
                    print(f"       • {topic['topic']}: {topic['score']:.2f}")
                
                if insights.compliance_flags:
                    print(f"     ⚠️ Compliance Flags ({len(insights.compliance_flags)}):")
                    for flag in insights.compliance_flags:
                        print(f"       • {flag['type']}: {flag['description']}")
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
    
    def demonstrate_form_extraction(self, file_paths: List[str]):
        """Demonstrate form field extraction"""
        print("\\n📝 Demonstrating Form Field Extraction...")
        
        for file_path in file_paths:
            filename = Path(file_path).name
            
            try:
                result = self.analyzer.analyze_document(file_path, extract_forms=True)
                
                if result.form_fields:
                    print(f"\\n   Form fields found in {filename}:")
                    for field in result.form_fields:
                        print(f"     • {field.field_name}: {field.field_value}")
                else:
                    print(f"\\n   No form fields detected in {filename}")
                
            except Exception as e:
                print(f"\\n   ❌ Error analyzing {filename}: {e}")
    
    def demonstrate_table_extraction(self, file_paths: List[str]):
        """Demonstrate table extraction"""
        print("\\n📊 Demonstrating Table Extraction...")
        
        for file_path in file_paths:
            filename = Path(file_path).name
            
            try:
                result = self.analyzer.analyze_document(file_path, extract_tables=True)
                
                if result.tables:
                    print(f"\\n   Tables found in {filename}:")
                    for i, table in enumerate(result.tables):
                        print(f"     Table {i+1}:")
                        print(f"       Headers: {', '.join(table.headers)}")
                        print(f"       Rows: {len(table.rows)}")
                        if table.rows:
                            print(f"       Sample row: {table.rows[0]}")
                else:
                    print(f"\\n   No tables detected in {filename}")
                
            except Exception as e:
                print(f"\\n   ❌ Error analyzing {filename}: {e}")
    
    def demonstrate_batch_analysis(self, file_paths: List[str]):
        """Demonstrate batch document analysis"""
        print("\\n📦 Demonstrating Batch Analysis...")
        
        try:
            print("   Processing all documents in batch...")
            results = self.analyzer.analyze_batch(file_paths)
            
            print(f"   ✅ Successfully processed {len(results)} documents")
            
            # Generate summary
            summary = self.analyzer.get_analysis_summary(results)
            
            print("\\n   📊 Analysis Summary:")
            print(f"     Total Documents: {summary['total_documents']}")
            print(f"     Average Processing Time: {summary['average_processing_time']:.2f}s")
            print(f"     Average Readability: {summary['average_readability']:.1f}")
            
            print("\\n     Document Types:")
            for doc_type, count in summary['document_types'].items():
                print(f"       • {doc_type}: {count}")
            
            print("\\n     Languages:")
            for lang, count in summary['languages'].items():
                print(f"       • {lang}: {count}")
            
            if summary['total_compliance_flags'] > 0:
                print(f"\\n     ⚠️ Total Compliance Flags: {summary['total_compliance_flags']}")
            
            return results
            
        except Exception as e:
            print(f"   ❌ Batch analysis failed: {e}")
            return []
    
    def demonstrate_search_functionality(self, results):
        """Demonstrate search functionality"""
        print("\\n🔎 Demonstrating Search Functionality...")
        
        if not results:
            print("   No results available for search demonstration")
            return
        
        try:
            # Create searchable index
            print("   Creating searchable index...")
            index = create_searchable_index(results)
            
            print(f"   ✅ Index created with {len(index)} searchable terms")
            
            # Demonstrate searches
            search_queries = ["invoice", "john", "medical", "bank", "contract"]
            
            print("\\n   Search Results:")
            for query in search_queries:
                results_found = search_documents(index, query)
                if results_found:
                    print(f"     '{query}': {', '.join(results_found)}")
                else:
                    print(f"     '{query}': No results found")
            
        except Exception as e:
            print(f"   ❌ Search demonstration failed: {e}")
    
    def demonstrate_export_functionality(self, results):
        """Demonstrate export functionality"""
        print("\\n📤 Demonstrating Export Functionality...")
        
        if not results:
            print("   No results available for export demonstration")
            return
        
        try:
            # Export to JSON
            print("   Exporting results to JSON...")
            json_export = self.analyzer.export_results(results, "json")
            
            # Save to file
            export_file = Path(tempfile.gettempdir()) / "document_analysis_results.json"
            export_file.write_text(json_export)
            
            print(f"   ✅ Results exported to: {export_file}")
            print(f"   Export size: {len(json_export)} characters")
            
            # Show sample of exported data
            import json
            parsed_data = json.loads(json_export)
            print(f"   Sample export structure:")
            if parsed_data:
                sample = parsed_data[0]
                print(f"     Keys: {', '.join(sample.keys())}")
            
        except Exception as e:
            print(f"   ❌ Export demonstration failed: {e}")
    
    def cleanup_demo_files(self, file_paths: List[str]):
        """Clean up demo files"""
        print("\\n🧹 Cleaning up demo files...")
        
        for file_path in file_paths:
            try:
                Path(file_path).unlink()
            except Exception as e:
                print(f"   Warning: Could not delete {file_path}: {e}")
        
        # Try to remove demo directory
        try:
            demo_dir = Path(tempfile.gettempdir()) / "doc_analyzer_demo"
            if demo_dir.exists():
                demo_dir.rmdir()
        except Exception:
            pass  # Directory might not be empty
        
        print("   ✅ Cleanup completed")
    
    def run_comprehensive_demo(self):
        """Run comprehensive demo of the document analysis system"""
        print("🎯 Advanced Document Analysis System - Comprehensive Demo")
        print("=" * 70)
        
        try:
            # Create sample documents
            file_paths = self.create_sample_documents()
            
            # Demonstrate core features
            self.demonstrate_document_classification(file_paths)
            self.demonstrate_insight_extraction(file_paths)
            self.demonstrate_form_extraction(file_paths)
            self.demonstrate_table_extraction(file_paths)
            
            # Demonstrate batch processing
            results = self.demonstrate_batch_analysis(file_paths)
            
            # Demonstrate search and export
            self.demonstrate_search_functionality(results)
            self.demonstrate_export_functionality(results)
            
            print("\\n🎉 Demo Completed Successfully!")
            print("=" * 70)
            
            print("\\n🚀 System Capabilities Demonstrated:")
            print("   ✅ Document classification (invoice, contract, medical, financial)")
            print("   ✅ Entity extraction (names, emails, phones, dates, amounts)")
            print("   ✅ Insight analysis (sentiment, readability, topics, language)")
            print("   ✅ Form field extraction (structured data from forms)")
            print("   ✅ Table extraction (tabular data detection and parsing)")
            print("   ✅ Compliance checking (PII detection, sensitive content)")
            print("   ✅ Batch processing (multiple documents simultaneously)")
            print("   ✅ Search functionality (indexed search across documents)")
            print("   ✅ Export capabilities (JSON format with full metadata)")
            
            print("\\n💡 Use Cases Supported:")
            print("   • Legal document analysis and classification")
            print("   • Medical record processing and compliance checking")
            print("   • Financial document analysis and data extraction")
            print("   • Invoice processing and form field extraction")
            print("   • Contract analysis and key term identification")
            print("   • Bulk document processing and organization")
            print("   • Searchable document archives and knowledge bases")
            
            # Cleanup
            self.cleanup_demo_files(file_paths)
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main function"""
    try:
        demo = AdvancedDocumentAnalyzerDemo()
        demo.run_comprehensive_demo()
        
    except Exception as e:
        print(f"❌ Demo initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()