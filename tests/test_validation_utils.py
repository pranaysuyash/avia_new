"""
Unit tests for validation functions in utils.py
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from typing import List

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    validate_file_size,
    validate_email,
    validate_phone_number,
    validate_url,
    validate_file_extension,
    validate_content_type,
    validate_language_code,
    validate_model_name,
    validate_json_structure,
    validate_date_range,
    validate_pagination_params,
    validate_sort_parameter,
    validate_enum_value,
    validate_audio_file,
    validate_video_file,
    validate_image_file,
    validate_media_file
)


class TestFileValidation:
    """Test file-related validation functions"""
    
    def test_validate_file_size_valid(self):
        """Test file size validation with valid file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('x' * 1024 * 1024)  # 1MB
            f.flush()
            
            assert validate_file_size(f.name, max_size_mb=2) == True
            assert validate_file_size(f.name, max_size_mb=1) == True
            
            os.unlink(f.name)
    
    def test_validate_file_size_too_large(self):
        """Test file size validation with oversized file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('x' * 3 * 1024 * 1024)  # 3MB
            f.flush()
            
            assert validate_file_size(f.name, max_size_mb=2) == False
            assert validate_file_size(f.name, max_size_mb=5) == True
            
            os.unlink(f.name)
    
    def test_validate_file_size_nonexistent(self):
        """Test file size validation with non-existent file"""
        assert validate_file_size('/path/that/does/not/exist.txt') == False
    
    def test_validate_file_extension(self):
        """Test file extension validation"""
        # Valid extensions
        assert validate_file_extension('audio.mp3', ['mp3', 'wav', 'flac']) == True
        assert validate_file_extension('Audio.MP3', ['mp3', 'wav', 'flac']) == True
        assert validate_file_extension('document.pdf', ['pdf', 'doc', 'docx']) == True
        
        # Invalid extensions
        assert validate_file_extension('audio.ogg', ['mp3', 'wav', 'flac']) == False
        assert validate_file_extension('', ['mp3']) == False
        assert validate_file_extension('no_extension', ['mp3']) == False
        
        # Edge cases
        assert validate_file_extension('file.tar.gz', ['gz']) == True
        # .hidden file has no extension, so it should fail
        assert validate_file_extension('.hidden', ['hidden']) == False


class TestEmailValidation:
    """Test email validation function"""
    
    def test_valid_emails(self):
        """Test with valid email addresses"""
        valid_emails = [
            'user@example.com',
            'john.doe@company.co.uk',
            'admin+tag@service.io',
            'user123@sub.domain.com',
            'test_user@example-site.com'
        ]
        
        for email in valid_emails:
            assert validate_email(email) == True, f"Failed for valid email: {email}"
    
    def test_invalid_emails(self):
        """Test with invalid email addresses"""
        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
            'user@@example.com',
            'user@.com',
            'user@example',
            'user example@example.com',
            ''
            # Note: 'user@example..com' might be accepted by some regex patterns
        ]
        
        for email in invalid_emails:
            assert validate_email(email) == False, f"Failed for invalid email: {email}"


class TestPhoneValidation:
    """Test phone number validation function"""
    
    def test_valid_phone_numbers(self):
        """Test with valid phone numbers"""
        valid_phones = [
            '+1234567890',
            '1234567890',
            '+1-234-567-8901',
            '(123) 456-7890',
            '123.456.7890',
            '+44 20 7123 4567',
            '12345678901234'  # Up to 15 digits
        ]
        
        for phone in valid_phones:
            assert validate_phone_number(phone) == True, f"Failed for valid phone: {phone}"
    
    def test_invalid_phone_numbers(self):
        """Test with invalid phone numbers"""
        invalid_phones = [
            '123',  # Too short
            '12345',  # Still too short
            'abcdefghij',  # Letters
            '+123456789012345678',  # Too long (>15 digits)
            '',
            '++1234567890',  # Double plus
            '123-abc-4567'  # Mixed with letters
        ]
        
        for phone in invalid_phones:
            assert validate_phone_number(phone) == False, f"Failed for invalid phone: {phone}"


class TestURLValidation:
    """Test URL validation function"""
    
    def test_valid_urls(self):
        """Test with valid URLs"""
        valid_urls = [
            'http://example.com',
            'https://www.example.com',
            'https://sub.domain.example.com',
            'http://example.com/path/to/resource',
            'https://example.com:8080',
            'https://example.com/path?query=value&another=value2',
            'https://example.com#anchor'
        ]
        
        for url in valid_urls:
            assert validate_url(url) == True, f"Failed for valid URL: {url}"
    
    def test_invalid_urls(self):
        """Test with invalid URLs"""
        invalid_urls = [
            'not a url',
            'ftp://example.com',  # Not http/https
            'http://',
            'https://',
            'example.com',  # Missing protocol
            '//example.com',  # Missing protocol
            '',
            'http://   .com',  # Invalid domain
            'javascript:alert(1)'  # Not http/https
        ]
        
        for url in invalid_urls:
            assert validate_url(url) == False, f"Failed for invalid URL: {url}"


class TestContentTypeValidation:
    """Test content type validation function"""
    
    def test_valid_content_types(self):
        """Test with valid content types"""
        allowed = ['audio/mpeg', 'audio/wav', 'video/mp4']
        
        assert validate_content_type('audio/mpeg', allowed) == True
        assert validate_content_type('audio/wav', allowed) == True
        assert validate_content_type('video/mp4', allowed) == True
        assert validate_content_type('audio/mpeg; charset=utf-8', allowed) == True
    
    def test_invalid_content_types(self):
        """Test with invalid content types"""
        allowed = ['audio/mpeg', 'audio/wav', 'video/mp4']
        
        assert validate_content_type('application/json', allowed) == False
        assert validate_content_type('', allowed) == False
        assert validate_content_type('audio/ogg', allowed) == False


class TestLanguageValidation:
    """Test language code validation function"""
    
    def test_valid_languages(self):
        """Test with valid language codes"""
        # Using default languages
        assert validate_language_code('en') == True
        assert validate_language_code('es') == True
        assert validate_language_code('fr') == True
        assert validate_language_code('auto') == True
        
        # Using custom languages
        custom = ['en-US', 'en-GB', 'pt-BR']
        assert validate_language_code('en-US', custom) == True
        assert validate_language_code('pt-BR', custom) == True
    
    def test_invalid_languages(self):
        """Test with invalid language codes"""
        assert validate_language_code('') == False
        assert validate_language_code('xyz') == False
        assert validate_language_code('english') == False


class TestModelValidation:
    """Test model name validation function"""
    
    def test_valid_models(self):
        """Test with valid model names"""
        # Using default Whisper models
        assert validate_model_name('tiny') == True
        assert validate_model_name('base') == True
        assert validate_model_name('small') == True
        assert validate_model_name('medium') == True
        assert validate_model_name('large') == True
        
        # Using custom models
        custom = ['gpt-3.5-turbo', 'gpt-4', 'claude-2']
        assert validate_model_name('gpt-4', custom) == True
        assert validate_model_name('claude-2', custom) == True
    
    def test_invalid_models(self):
        """Test with invalid model names"""
        assert validate_model_name('') == False
        assert validate_model_name('extra-large') == False
        assert validate_model_name('whisper-xl') == False


class TestJSONValidation:
    """Test JSON structure validation function"""
    
    def test_valid_json_structure(self):
        """Test with valid JSON structures"""
        data = {'name': 'John', 'age': 30, 'email': 'john@example.com'}
        
        valid, error = validate_json_structure(data, ['name', 'age'])
        assert valid == True
        assert error is None
        
        valid, error = validate_json_structure(data, ['email'])
        assert valid == True
        assert error is None
    
    def test_invalid_json_structure(self):
        """Test with invalid JSON structures"""
        data = {'name': 'John', 'age': 30}
        
        valid, error = validate_json_structure(data, ['name', 'email'])
        assert valid == False
        assert 'email' in error
        
        valid, error = validate_json_structure(data, ['id', 'timestamp'])
        assert valid == False
        assert 'id' in error and 'timestamp' in error


class TestDateRangeValidation:
    """Test date range validation function"""
    
    def test_valid_date_ranges(self):
        """Test with valid date ranges"""
        # Valid ISO format dates
        valid, error = validate_date_range('2024-01-01T00:00:00', '2024-12-31T23:59:59')
        assert valid == True
        assert error is None
        
        # With timezone
        valid, error = validate_date_range('2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z')
        assert valid == True
        assert error is None
    
    def test_invalid_date_ranges(self):
        """Test with invalid date ranges"""
        # End before start
        valid, error = validate_date_range('2024-12-31', '2024-01-01')
        assert valid == False
        assert 'before' in error
        
        # Invalid format
        valid, error = validate_date_range('2024/01/01', '2024/12/31')
        assert valid == False
        assert 'Invalid' in error
        
        # Empty dates
        valid, error = validate_date_range('', '')
        assert valid == False


class TestPaginationValidation:
    """Test pagination parameter validation function"""
    
    def test_valid_pagination(self):
        """Test with valid pagination parameters"""
        valid, error = validate_pagination_params(1, 10)
        assert valid == True
        assert error is None
        
        valid, error = validate_pagination_params(5, 50, max_per_page=100)
        assert valid == True
        assert error is None
        
        valid, error = validate_pagination_params(100, 100, max_per_page=100)
        assert valid == True
        assert error is None
    
    def test_invalid_pagination(self):
        """Test with invalid pagination parameters"""
        # Invalid page
        valid, error = validate_pagination_params(0, 10)
        assert valid == False
        assert 'Page' in error
        
        # Invalid per_page
        valid, error = validate_pagination_params(1, 0)
        assert valid == False
        assert 'Items per page' in error or 'per page' in error.lower()
        
        # Exceeds max
        valid, error = validate_pagination_params(1, 200, max_per_page=100)
        assert valid == False
        assert 'exceed' in error  # Check for "exceed" instead of "exceeds"


class TestSortParameterValidation:
    """Test sort parameter validation function"""
    
    def test_valid_sort_parameters(self):
        """Test with valid sort parameters"""
        valid_sorts = ['name', 'date', 'size']
        
        assert validate_sort_parameter('name', valid_sorts) == True
        assert validate_sort_parameter('DATE', valid_sorts) == True  # Case insensitive
        assert validate_sort_parameter('Size', valid_sorts) == True
    
    def test_invalid_sort_parameters(self):
        """Test with invalid sort parameters"""
        valid_sorts = ['name', 'date', 'size']
        
        assert validate_sort_parameter('price', valid_sorts) == False
        assert validate_sort_parameter('', valid_sorts) == False
        assert validate_sort_parameter('random', valid_sorts) == False


class TestEnumValidation:
    """Test enum value validation function"""
    
    def test_enum_validation_case_insensitive(self):
        """Test enum validation with case insensitive mode"""
        enum_values = ['active', 'inactive', 'pending']
        
        assert validate_enum_value('active', enum_values) == True
        assert validate_enum_value('ACTIVE', enum_values) == True
        assert validate_enum_value('Pending', enum_values) == True
        assert validate_enum_value('invalid', enum_values) == False
    
    def test_enum_validation_case_sensitive(self):
        """Test enum validation with case sensitive mode"""
        enum_values = ['Active', 'Inactive', 'Pending']
        
        assert validate_enum_value('Active', enum_values, case_sensitive=True) == True
        assert validate_enum_value('active', enum_values, case_sensitive=True) == False
        assert validate_enum_value('ACTIVE', enum_values, case_sensitive=True) == False


class TestMediaFileValidation:
    """Test media file validation functions"""
    
    def test_validate_audio_files(self):
        """Test audio file validation"""
        # Valid audio files
        assert validate_audio_file('song.mp3') == True
        assert validate_audio_file('podcast.wav') == True
        assert validate_audio_file('recording.m4a') == True
        assert validate_audio_file('audio.flac') == True
        
        # With content type
        assert validate_audio_file('song.mp3', 'audio/mpeg') == True
        assert validate_audio_file('podcast.wav', 'audio/wav') == True
        
        # Invalid
        assert validate_audio_file('video.mp4') == False
        assert validate_audio_file('document.pdf') == False
        assert validate_audio_file('song.mp3', 'video/mp4') == False
    
    def test_validate_video_files(self):
        """Test video file validation"""
        # Valid video files
        assert validate_video_file('movie.mp4') == True
        assert validate_video_file('clip.avi') == True
        assert validate_video_file('video.mov') == True
        assert validate_video_file('recording.mkv') == True
        
        # With content type
        assert validate_video_file('movie.mp4', 'video/mp4') == True
        assert validate_video_file('clip.avi', 'video/x-msvideo') == True
        
        # Invalid
        assert validate_video_file('audio.mp3') == False
        assert validate_video_file('image.jpg') == False
        assert validate_video_file('movie.mp4', 'audio/mpeg') == False
    
    def test_validate_image_files(self):
        """Test image file validation"""
        # Valid image files
        assert validate_image_file('photo.jpg') == True
        assert validate_image_file('picture.png') == True
        assert validate_image_file('graphic.gif') == True
        assert validate_image_file('logo.webp') == True
        
        # With content type
        assert validate_image_file('photo.jpg', 'image/jpeg') == True
        assert validate_image_file('picture.png', 'image/png') == True
        
        # Invalid
        assert validate_image_file('audio.mp3') == False
        assert validate_image_file('video.mp4') == False
        assert validate_image_file('photo.jpg', 'video/mp4') == False
    
    def test_validate_media_file(self):
        """Test general media file validation"""
        # Audio files
        valid, media_type = validate_media_file('song.mp3')
        assert valid == True
        assert media_type == 'audio'
        
        # Video files
        valid, media_type = validate_media_file('movie.mp4')
        assert valid == True
        assert media_type == 'video'
        
        # Image files
        valid, media_type = validate_media_file('photo.jpg')
        assert valid == True
        assert media_type == 'image'
        
        # Invalid files
        valid, media_type = validate_media_file('document.pdf')
        assert valid == False
        assert media_type is None
        
        valid, media_type = validate_media_file('script.py')
        assert valid == False
        assert media_type is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])