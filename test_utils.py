#!/usr/bin/env python3
"""
Unit tests for utilities module
Tests shared utilities for file management and logging
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import utils

class TestUtilities:
    """Test cases for utility functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_temp_file(self):
        """Test temporary file creation"""
        temp_file = utils.create_temp_file(".txt")
        
        assert isinstance(temp_file, str)
        assert temp_file.endswith(".txt")
        assert os.path.exists(temp_file)
        
        # Clean up
        os.remove(temp_file)
    
    def test_create_temp_file_custom_suffix(self):
        """Test temporary file creation with custom suffix"""
        temp_file = utils.create_temp_file(".json")
        
        assert temp_file.endswith(".json")
        assert os.path.exists(temp_file)
        
        # Clean up
        os.remove(temp_file)
    
    def test_cleanup_temp_files(self):
        """Test cleanup of multiple temporary files"""
        # Create test files
        test_files = []
        for i in range(3):
            temp_file = os.path.join(self.temp_dir, f"test_file_{i}.txt")
            with open(temp_file, 'w') as f:
                f.write(f"Test content {i}")
            test_files.append(temp_file)
        
        # Verify files exist
        for file_path in test_files:
            assert os.path.exists(file_path)
        
        # Clean up files
        utils.cleanup_temp_files(test_files)
        
        # Verify files are removed
        for file_path in test_files:
            assert not os.path.exists(file_path)
    
    def test_cleanup_temp_files_nonexistent(self):
        """Test cleanup with non-existent files (should not raise error)"""
        nonexistent_files = [
            os.path.join(self.temp_dir, "nonexistent1.txt"),
            os.path.join(self.temp_dir, "nonexistent2.txt")
        ]
        
        # Should not raise an exception
        utils.cleanup_temp_files(nonexistent_files)
    
    def test_validate_file_size_valid(self):
        """Test file size validation with valid file"""
        test_file = os.path.join(self.temp_dir, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("Small test content")
        
        # Should be valid for 1MB limit
        assert utils.validate_file_size(test_file, 1) is True
    
    def test_validate_file_size_too_large(self):
        """Test file size validation with oversized file"""
        test_file = os.path.join(self.temp_dir, "large_file.txt")
        with open(test_file, 'w') as f:
            # Write 1KB of data
            f.write("x" * 1024)
        
        # Should be invalid for very small limit
        assert utils.validate_file_size(test_file, 0.0001) is False
    
    def test_validate_file_size_nonexistent(self):
        """Test file size validation with non-existent file"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.txt")
        
        # Should return False for non-existent file
        assert utils.validate_file_size(nonexistent_file) is False
    
    def test_ensure_temp_directory(self):
        """Test temporary directory creation"""
        temp_dir = utils.ensure_temp_directory()
        
        assert isinstance(temp_dir, str)
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)
    
    def test_ensure_temp_directory_custom_env(self):
        """Test temporary directory creation with custom environment variable"""
        custom_temp_dir = os.path.join(self.temp_dir, "custom_temp")
        
        with patch.dict(os.environ, {'TEMP_DIR': custom_temp_dir}):
            temp_dir = utils.ensure_temp_directory()
            
            assert temp_dir == custom_temp_dir
            assert os.path.exists(custom_temp_dir)
    
    @patch('os.makedirs')
    def test_ensure_temp_directory_creation_error(self, mock_makedirs):
        """Test temporary directory creation with permission error"""
        mock_makedirs.side_effect = PermissionError("Permission denied")
        
        with pytest.raises(PermissionError):
            utils.ensure_temp_directory()
    
    def test_cleanup_file(self):
        """Test single file cleanup"""
        test_file = os.path.join(self.temp_dir, "test_cleanup.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Verify file exists
        assert os.path.exists(test_file)
        
        # Clean up file
        utils.cleanup_file(test_file)
        
        # Verify file is removed
        assert not os.path.exists(test_file)
    
    def test_cleanup_file_nonexistent(self):
        """Test cleanup of non-existent file (should not raise error)"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.txt")
        
        # Should not raise an exception
        utils.cleanup_file(nonexistent_file)
    
    def test_setup_logging_default(self):
        """Test logging setup with default level"""
        import logging
        
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        utils.setup_logging()
        
        # Check that logging is configured
        logger = logging.getLogger("test_logger")
        assert logger.getEffectiveLevel() == logging.INFO
    
    def test_setup_logging_custom_level(self):
        """Test logging setup with custom level"""
        import logging
        
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        utils.setup_logging("DEBUG")
        
        # Check that logging level is set correctly
        logger = logging.getLogger("test_logger")
        assert logger.getEffectiveLevel() == logging.DEBUG
    
    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid level"""
        import logging
        
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Should fall back to INFO level for invalid input
        utils.setup_logging("INVALID_LEVEL")
        
        logger = logging.getLogger("test_logger")
        assert logger.getEffectiveLevel() == logging.INFO
    
    @patch('utils.logging.basicConfig')
    def test_setup_logging_configuration_error(self, mock_basic_config):
        """Test logging setup with configuration error"""
        mock_basic_config.side_effect = Exception("Configuration error")
        
        # Should not raise exception, should fall back to basic config
        utils.setup_logging()
        
        # Should have attempted configuration twice (original + fallback)
        assert mock_basic_config.call_count >= 1


class TestUtilitiesIntegration:
    """Integration tests for utilities module"""
    
    def setup_method(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up integration test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_lifecycle_integration(self):
        """Test complete file lifecycle: create, validate, cleanup"""
        # Create temporary file
        temp_file = utils.create_temp_file(".txt")
        
        # Write some content
        with open(temp_file, 'w') as f:
            f.write("Integration test content")
        
        # Validate file size
        assert utils.validate_file_size(temp_file, 1) is True
        
        # Clean up file
        utils.cleanup_file(temp_file)
        
        # Verify file is gone
        assert not os.path.exists(temp_file)
    
    def test_temp_directory_workflow(self):
        """Test temporary directory workflow"""
        # Ensure temp directory exists
        temp_dir = utils.ensure_temp_directory()
        
        # Create a file in the temp directory
        test_file = os.path.join(temp_dir, "workflow_test.txt")
        with open(test_file, 'w') as f:
            f.write("Workflow test")
        
        # Validate the file
        assert utils.validate_file_size(test_file, 1) is True
        
        # Clean up the file
        utils.cleanup_file(test_file)
        
        # Verify cleanup
        assert not os.path.exists(test_file)
    
    def test_batch_file_operations(self):
        """Test batch file operations"""
        # Create multiple temporary files
        temp_files = []
        for i in range(5):
            temp_file = utils.create_temp_file(f".test_{i}")
            with open(temp_file, 'w') as f:
                f.write(f"Batch test content {i}")
            temp_files.append(temp_file)
        
        # Validate all files
        for temp_file in temp_files:
            assert utils.validate_file_size(temp_file, 1) is True
        
        # Batch cleanup
        utils.cleanup_temp_files(temp_files)
        
        # Verify all files are cleaned up
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])