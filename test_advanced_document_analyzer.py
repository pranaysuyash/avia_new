#!/usr/bin/env python3
"""
Test suite for Advanced Document Analysis System
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Import the system under test
from advanced_document_analyzer import (
    AdvancedDocumentAnalyzer,
    DocumentClassifier,
    DocumentInsightExtractor,
    FormFieldExtractor,
    TableExtractor,
    AdvancedDocumentResult,
    DocumentClassification,
    DocumentInsights,
    FormField,
    TableData,
    create_searchable_index,
    search_documents
)

class TestDocumentClassifier(unittest.TestCase):
    """Test document classification functionality"""
    
    def setUp(self):
        self.classifier = DocumentClassifier()
    
    def test_classify_invoice(self):
        """Test invoice classification"""
        invoice_text = """
        INVOICE
        Invoice Number: INV-001
        Date: 2024-01-15
        Amount Due: $1,250.00
        Tax: $125.00
        Total: $1,375.00
        """
        
        result = self.classifier.classify_document(invoice_text, "invoice_001.pdf")
        
        self.assertEqual(result.document_type, "invoice")
        self.assertGreater(result.confidence, 0.0)
        self.assertIsInstance(result.categories, list)
        self.assertGreater(len(result.categories), 0)
    
    def test_classify_contract(self):
        """Test contract classification"""
        contract_text = """
        SERVICE AGREEMENT
        This agreement is between Party A and Party B.
        Terms and conditions apply.
        Both parties agree to the following terms.
        Signature required.
        """
        
        result = self.classifier.classify_document(contract_text, "contract.pdf")
        
        self.assertEqual(result.document_type, "contract")
        self.assertGreater(result.confidence, 0.0)
    
    def test_classify_unknown(self):
        """Test unknown document classification"""
        random_text = "This is just some random text without specific keywords."
        
        result = self.classifier.classify_document(random_text, "random.txt")
        
        self.assertIsInstance(result.document_type, str)
        self.assertIsInstance(result.confidence, float)

class TestDocumentInsightExtractor(unittest.TestCase):
    """Test document insight extraction"""
    
    def setUp(self):
        self.extractor = DocumentInsightExtractor()
    
    def test_extract_insights_basic(self):
        """Test basic insight extraction"""
        text = """
        John Smith works at Microsoft Corporation.
        He can be reached at john.smith@microsoft.com.
        The meeting is scheduled for January 15, 2024.
        This is a positive development for the company.
        """
        
        insights = self.extractor.extract_insights(text)
        
        self.assertIsInstance(insights.key_entities, list)
        self.assertIsInstance(insights.topics, list)
        self.assertIsInstance(insights.sentiment, dict)
        self.assertIsInstance(insights.readability_score, float)
        self.assertIsInstance(insights.language_detected, str)
        self.assertIsInstance(insights.document_structure, dict)
        self.assertIsInstance(insights.compliance_flags, list)
    
    def test_extract_entities_regex(self):
        """Test regex-based entity extraction"""
        text = """
        Contact: john.doe@example.com
        Phone: (555) 123-4567
        SSN: 123-45-6789
        Website: https://example.com
        """
        
        entities = self.extractor._extract_regex_entities(text)
        
        # Should find email, phone, SSN, and URL
        entity_types = [e["label"] for e in entities]
        self.assertIn("EMAIL", entity_types)
        self.assertIn("PHONE", entity_types)
        self.assertIn("SSN", entity_types)
        self.assertIn("URL", entity_types)
    
    def test_readability_calculation(self):
        """Test readability score calculation"""
        simple_text = "This is a simple sentence. It is easy to read."
        complex_text = "The implementation of sophisticated algorithms necessitates comprehensive understanding of computational complexity theory."
        
        simple_score = self.extractor._calculate_readability(simple_text)
        complex_score = self.extractor._calculate_readability(complex_text)
        
        # Simple text should have higher readability score
        self.assertGreater(simple_score, complex_score)
        self.assertGreaterEqual(simple_score, 0)
        self.assertLessEqual(simple_score, 100)
    
    def test_compliance_flags(self):
        """Test compliance flag detection"""
        sensitive_text = """
        CONFIDENTIAL DOCUMENT
        SSN: 123-45-6789
        Credit Card: 4532-1234-5678-9012
        Email: user@example.com
        This document is classified and proprietary.
        """
        
        flags = self.extractor._check_compliance(sensitive_text)
        
        self.assertGreater(len(flags), 0)
        flag_types = [f["type"] for f in flags]
        self.assertIn("PII_DETECTED", flag_types)
        self.assertIn("SENSITIVE_CONTENT", flag_types)

class TestFormFieldExtractor(unittest.TestCase):
    """Test form field extraction"""
    
    def setUp(self):
        self.extractor = FormFieldExtractor()
    
    def test_extract_form_fields(self):
        """Test form field extraction"""
        form_text = """
        Name: John Smith
        Email: john.smith@example.com
        Phone: (555) 123-4567
        Address: 123 Main St, Anytown, USA
        Date: January 15, 2024
        Amount: $1,500.00
        """
        
        # Mock OCR result
        mock_ocr = Mock()
        
        fields = self.extractor.extract_fields(form_text, mock_ocr)
        
        self.assertGreater(len(fields), 0)
        
        field_names = [f.field_name for f in fields]
        self.assertIn("name", field_names)
        self.assertIn("email", field_names)
        self.assertIn("phone", field_names)
        
        # Check field values
        name_field = next((f for f in fields if f.field_name == "name"), None)
        self.assertIsNotNone(name_field)
        self.assertEqual(name_field.field_value, "John Smith")

class TestTableExtractor(unittest.TestCase):
    """Test table extraction"""
    
    def setUp(self):
        self.extractor = TableExtractor()
    
    def test_is_table_row(self):
        """Test table row detection"""
        table_row = "Product    Price    Quantity    Total"
        non_table_row = "This is just a regular sentence."
        
        self.assertTrue(self.extractor._is_table_row(table_row))
        self.assertFalse(self.extractor._is_table_row(non_table_row))
    
    def test_extract_simple_table(self):
        """Test simple table extraction"""
        table_text = """
        Product    Price    Quantity    Total
        Apple      $1.00    5           $5.00
        Orange     $0.75    3           $2.25
        Banana     $0.50    8           $4.00
        """
        
        # Mock OCR result
        mock_ocr = Mock()
        
        tables = self.extractor.extract_tables(table_text, mock_ocr)
        
        self.assertGreater(len(tables), 0)
        
        table = tables[0]
        self.assertEqual(len(table.headers), 4)
        self.assertGreater(len(table.rows), 0)
        self.assertIn("Product", table.headers)
        self.assertIn("Price", table.headers)

class TestAdvancedDocumentAnalyzer(unittest.TestCase):
    """Test the main document analyzer"""
    
    def setUp(self):
        self.analyzer = AdvancedDocumentAnalyzer()
    
    @patch('advanced_document_analyzer.OCRManager')
    def test_analyze_document_mock(self, mock_ocr_manager):
        """Test document analysis with mocked OCR"""
        # Mock OCR result
        mock_ocr_result = Mock()
        mock_ocr_result.text = "This is a test invoice. Amount: $100.00"
        mock_ocr_manager.return_value.process_file.return_value = mock_ocr_result
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_path = temp_file.name
        
        try:
            result = self.analyzer.analyze_document(temp_path)
            
            self.assertIsInstance(result, AdvancedDocumentResult)
            self.assertIsInstance(result.classification, DocumentClassification)
            self.assertIsInstance(result.insights, DocumentInsights)
            self.assertIsInstance(result.form_fields, list)
            self.assertIsInstance(result.tables, list)
            self.assertGreater(result.processing_time, 0)
            
        finally:
            os.unlink(temp_path)
    
    def test_export_results(self):
        """Test results export"""
        # Create mock result
        mock_result = Mock(spec=AdvancedDocumentResult)
        mock_result.filename = "test.pdf"
        mock_result.processing_time = 1.5
        
        # Mock asdict to return a simple dict
        with patch('advanced_document_analyzer.asdict') as mock_asdict:
            mock_asdict.return_value = {"filename": "test.pdf", "processing_time": 1.5}
            
            exported = self.analyzer.export_results([mock_result], "json")
            
            self.assertIsInstance(exported, str)
            # Should be valid JSON
            parsed = json.loads(exported)
            self.assertIsInstance(parsed, list)
    
    def test_get_analysis_summary(self):
        """Test analysis summary generation"""
        # Create mock results
        mock_results = []
        for i in range(3):
            mock_result = Mock(spec=AdvancedDocumentResult)
            mock_result.classification.document_type = "invoice" if i < 2 else "contract"
            mock_result.insights.language_detected = "en"
            mock_result.insights.compliance_flags = []
            mock_result.insights.readability_score = 75.0
            mock_result.processing_time = 1.0 + i
            mock_result.form_fields = [Mock()] if i == 0 else []
            mock_result.tables = [Mock()] if i < 2 else []
            mock_results.append(mock_result)
        
        summary = self.analyzer.get_analysis_summary(mock_results)
        
        self.assertEqual(summary["total_documents"], 3)
        self.assertIn("document_types", summary)
        self.assertIn("languages", summary)
        self.assertIn("average_processing_time", summary)
        self.assertEqual(summary["documents_with_forms"], 1)
        self.assertEqual(summary["documents_with_tables"], 2)

class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_create_searchable_index(self):
        """Test searchable index creation"""
        # Create mock results
        mock_results = []
        for i, doc_type in enumerate(["invoice", "contract"]):
            mock_result = Mock(spec=AdvancedDocumentResult)
            mock_result.filename = f"doc_{i}.pdf"
            mock_result.classification.document_type = doc_type
            mock_result.insights.key_entities = [
                {"text": "John Smith", "label": "PERSON"},
                {"text": "Microsoft", "label": "ORG"}
            ]
            mock_result.insights.topics = [
                {"topic": "business", "score": 0.8}
            ]
            mock_results.append(mock_result)
        
        index = create_searchable_index(mock_results)
        
        self.assertIn("invoice", index)
        self.assertIn("contract", index)
        self.assertIn("john smith", index)
        self.assertIn("microsoft", index)
        self.assertIn("business", index)
    
    def test_search_documents(self):
        """Test document search"""
        index = {
            "invoice": ["doc1.pdf", "doc2.pdf"],
            "contract": ["doc3.pdf"],
            "john smith": ["doc1.pdf", "doc3.pdf"],
            "microsoft": ["doc1.pdf", "doc2.pdf"]
        }
        
        # Test exact match
        results = search_documents(index, "invoice")
        self.assertEqual(set(results), {"doc1.pdf", "doc2.pdf"})
        
        # Test partial match
        results = search_documents(index, "john")
        self.assertEqual(set(results), {"doc1.pdf", "doc3.pdf"})
        
        # Test case insensitive
        results = search_documents(index, "MICROSOFT")
        self.assertEqual(set(results), {"doc1.pdf", "doc2.pdf"})

def run_tests():
    """Run all tests"""
    print("🧪 Running Advanced Document Analyzer Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestDocumentClassifier,
        TestDocumentInsightExtractor,
        TestFormFieldExtractor,
        TestTableExtractor,
        TestAdvancedDocumentAnalyzer,
        TestUtilityFunctions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🎯 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            error_lines = traceback.split('\n')
            error_msg = error_lines[-2] if len(error_lines) >= 2 else str(traceback)
            print(f"   - {test}: {error_msg}")
    
    if not result.failures and not result.errors:
        print("✅ All tests passed successfully!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)