#!/usr/bin/env python3
"""
Minimal test version of MediaIngestionController to isolate issues
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class MediaFormat:
    """Media format information"""
    file_type: str
    mime_type: str
    extension: str
    is_supported: bool = True

class MediaIngestionController:
    """
    Minimal version of MediaIngestionController for testing
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the controller"""
        self.temp_dir = temp_dir or "/tmp"
        logger.info("MediaIngestionController initialized")
    
    def test_method(self):
        """Test method to verify functionality"""
        return "MediaIngestionController is working!"

# Test the class
if __name__ == "__main__":
    print("Testing minimal MediaIngestionController...")
    controller = MediaIngestionController()
    print(controller.test_method())
    print("✅ Minimal controller works!")