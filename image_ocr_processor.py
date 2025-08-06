"""
Image and Document OCR Processing System
Comprehensive OCR solution for extracting text from images and documents
"""

import os
import io
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import easyocr
import fitz  # PyMuPDF for PDF processing
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging
from pathlib import Path
import tempfile
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """OCR processing result"""
    text: str
    confidence: float
    language: str
    processing_time: float
    word_count: int
    line_count: int
    bounding_boxes: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
@dataclass
class DocumentPage:
    """Individual document page result"""
    page_number: int
    text: str
    confidence: float
    image_path: Optional[str] = None
    tables: List[Dict[str, Any]] = None
    
@dataclass
class DocumentResult:
    """Complete document processing result"""
    filename: str
    total_pages: int
    pages: List[DocumentPage]
    combined_text: str
    processing_time: float
    metadata: Dict[str, Any]

class ImagePreprocessor:
    """Advanced image preprocessing for better OCR accuracy"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp']
    
    def preprocess_image(self, image: Union[str, np.ndarray, Image.Image], 
                        enhance_contrast: bool = True,
                        denoise: bool = True,
                        deskew: bool = True,
                        resize_factor: float = 2.0) -> np.ndarray:
        """
        Comprehensive image preprocessing for optimal OCR
        """
        try:
            # Load image
            if isinstance(image, str):
                img = cv2.imread(image)
                if img is None:
                    raise ValueError(f"Could not load image from {image}")
            elif isinstance(image, Image.Image):
                img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            else:
                img = image.copy()
            
            # Convert to grayscale
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img.copy()
            
            # Resize image for better OCR (larger images often work better)
            if resize_factor != 1.0:
                height, width = gray.shape
                new_height, new_width = int(height * resize_factor), int(width * resize_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Denoise
            if denoise:
                gray = cv2.fastNlMeansDenoising(gray)
            
            # Enhance contrast
            if enhance_contrast:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)
            
            # Deskew image
            if deskew:
                gray = self._deskew_image(gray)
            
            # Apply morphological operations to clean up text
            kernel = np.ones((1,1), np.uint8)
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # Threshold the image
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            return gray
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Detect and correct skew in the image"""
        try:
            # Find all white pixels
            coords = np.column_stack(np.where(image > 0))
            
            # Find minimum area rectangle
            if len(coords) > 0:
                angle = cv2.minAreaRect(coords)[-1]
                
                # Correct angle
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                
                # Rotate image to deskew
                if abs(angle) > 0.5:  # Only rotate if angle is significant
                    (h, w) = image.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    image = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, 
                                         borderMode=cv2.BORDER_REPLICATE)
            
            return image
            
        except Exception as e:
            logger.warning(f"Could not deskew image: {str(e)}")
            return image
    
    def detect_tables(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect table structures in the image"""
        try:
            # Find horizontal and vertical lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            # Detect horizontal lines
            horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Detect vertical lines
            vertical_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combine lines to find table structure
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Find contours (potential table cells)
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            tables = []
            for i, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                if w > 100 and h > 50:  # Filter small contours
                    tables.append({
                        'table_id': i,
                        'bbox': [x, y, x + w, y + h],
                        'width': w,
                        'height': h,
                        'area': w * h
                    })
            
            return tables
            
        except Exception as e:
            logger.warning(f"Could not detect tables: {str(e)}")
            return []

class OCREngine:
    """Multi-engine OCR processor with fallback support"""
    
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.tesseract_available = self._check_tesseract()
        self.easyocr_reader = None
        self._initialize_easyocr()
        
        # Language mappings
        self.language_codes = {
            'en': 'eng',  # Tesseract format
            'es': 'spa',
            'fr': 'fra',
            'de': 'deu',
            'it': 'ita',
            'pt': 'por',
            'ru': 'rus',
            'zh': 'chi_sim',
            'ja': 'jpn',
            'ko': 'kor',
            'ar': 'ara',
            'hi': 'hin'
        }
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            logger.warning("Tesseract not available")
            return False
    
    def _initialize_easyocr(self):
        """Initialize EasyOCR reader"""
        try:
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize EasyOCR: {str(e)}")
    
    def detect_language(self, image: np.ndarray) -> str:
        """Detect the primary language in the image"""
        try:
            if self.tesseract_available:
                # Use Tesseract's built-in language detection
                osd = pytesseract.image_to_osd(image)
                # Parse OSD output to extract language info
                # For now, default to English
                return 'en'
            else:
                return 'en'  # Default fallback
                
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return 'en'
    
    def extract_text_tesseract(self, image: np.ndarray, language: str = 'en') -> OCRResult:
        """Extract text using Tesseract OCR"""
        start_time = datetime.now()
        
        try:
            if not self.tesseract_available:
                raise Exception("Tesseract not available")
            
            # Get language code for Tesseract
            lang_code = self.language_codes.get(language, 'eng')
            
            # Configure Tesseract
            config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,!?;:()[]{}"\'-'
            
            # Extract text
            text = pytesseract.image_to_string(image, lang=lang_code, config=config)
            
            # Get detailed data with bounding boxes
            data = pytesseract.image_to_data(image, lang=lang_code, output_type=pytesseract.Output.DICT)
            
            # Calculate confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract bounding boxes
            bounding_boxes = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:
                    bounding_boxes.append({
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]),
                        'bbox': [data['left'][i], data['top'][i], 
                                data['left'][i] + data['width'][i], 
                                data['top'][i] + data['height'][i]]
                    })
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence / 100.0,
                language=language,
                processing_time=processing_time,
                word_count=len(text.split()),
                line_count=len(text.split('\n')),
                bounding_boxes=bounding_boxes,
                metadata={'engine': 'tesseract', 'config': config}
            )
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {str(e)}")
            raise
    
    def extract_text_easyocr(self, image: np.ndarray, language: str = 'en') -> OCRResult:
        """Extract text using EasyOCR"""
        start_time = datetime.now()
        
        try:
            if self.easyocr_reader is None:
                raise Exception("EasyOCR not available")
            
            # Extract text
            results = self.easyocr_reader.readtext(image)
            
            # Combine text and calculate confidence
            text_parts = []
            confidences = []
            bounding_boxes = []
            
            for (bbox, text, confidence) in results:
                text_parts.append(text)
                confidences.append(confidence)
                
                # Convert bbox format
                x1, y1 = bbox[0]
                x2, y2 = bbox[2]
                bounding_boxes.append({
                    'text': text,
                    'confidence': confidence,
                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                })
            
            combined_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return OCRResult(
                text=combined_text,
                confidence=avg_confidence,
                language=language,
                processing_time=processing_time,
                word_count=len(combined_text.split()),
                line_count=len(combined_text.split('\n')),
                bounding_boxes=bounding_boxes,
                metadata={'engine': 'easyocr'}
            )
            
        except Exception as e:
            logger.error(f"EasyOCR failed: {str(e)}")
            raise
    
    def extract_text_hybrid(self, image: np.ndarray, language: str = 'en') -> OCRResult:
        """Use hybrid approach combining multiple OCR engines"""
        results = []
        
        # Try Tesseract
        if self.tesseract_available:
            try:
                tesseract_result = self.extract_text_tesseract(image, language)
                results.append(('tesseract', tesseract_result))
            except Exception as e:
                logger.warning(f"Tesseract failed: {str(e)}")
        
        # Try EasyOCR
        if self.easyocr_reader is not None:
            try:
                easyocr_result = self.extract_text_easyocr(image, language)
                results.append(('easyocr', easyocr_result))
            except Exception as e:
                logger.warning(f"EasyOCR failed: {str(e)}")
        
        if not results:
            raise Exception("No OCR engines available")
        
        # Select best result based on confidence and text length
        best_result = max(results, key=lambda x: (x[1].confidence, len(x[1].text)))
        
        # Add metadata about hybrid processing
        best_result[1].metadata['hybrid_processing'] = True
        best_result[1].metadata['engines_tried'] = [r[0] for r in results]
        
        return best_result[1]

class DocumentProcessor:
    """Process various document formats including PDFs"""
    
    def __init__(self):
        self.ocr_engine = OCREngine()
        self.supported_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']
    
    def process_pdf(self, pdf_path: str, extract_images: bool = True) -> DocumentResult:
        """Process PDF document with OCR"""
        start_time = datetime.now()
        
        try:
            doc = fitz.open(pdf_path)
            pages = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Try to extract text directly first
                text = page.get_text()
                
                if len(text.strip()) < 50:  # If little text found, use OCR
                    # Convert page to image
                    mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    
                    # Convert to OpenCV format
                    nparr = np.frombuffer(img_data, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    # Preprocess and OCR
                    processed_image = self.ocr_engine.preprocessor.preprocess_image(image)
                    ocr_result = self.ocr_engine.extract_text_hybrid(processed_image)
                    
                    text = ocr_result.text
                    confidence = ocr_result.confidence
                else:
                    confidence = 1.0  # High confidence for direct text extraction
                
                # Detect tables if needed
                tables = []
                if extract_images:
                    # Convert page to image for table detection
                    mat = fitz.Matrix(1, 1)
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    nparr = np.frombuffer(img_data, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
                    tables = self.ocr_engine.preprocessor.detect_tables(image)
                
                pages.append(DocumentPage(
                    page_number=page_num + 1,
                    text=text,
                    confidence=confidence,
                    tables=tables
                ))
            
            doc.close()
            
            # Combine all text
            combined_text = '\n\n'.join([page.text for page in pages])
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return DocumentResult(
                filename=Path(pdf_path).name,
                total_pages=len(pages),
                pages=pages,
                combined_text=combined_text,
                processing_time=processing_time,
                metadata={
                    'format': 'pdf',
                    'extract_images': extract_images,
                    'total_characters': len(combined_text)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
    
    def process_image(self, image_path: str, language: str = 'en') -> OCRResult:
        """Process single image file"""
        try:
            # Load and preprocess image
            processed_image = self.ocr_engine.preprocessor.preprocess_image(image_path)
            
            # Detect language if not specified
            if language == 'auto':
                language = self.ocr_engine.detect_language(processed_image)
            
            # Extract text
            result = self.ocr_engine.extract_text_hybrid(processed_image, language)
            
            # Add image metadata
            result.metadata.update({
                'source_file': Path(image_path).name,
                'image_format': Path(image_path).suffix.lower()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise
    
    def process_batch(self, file_paths: List[str], language: str = 'en') -> List[Union[OCRResult, DocumentResult]]:
        """Process multiple files in batch"""
        results = []
        
        for file_path in file_paths:
            try:
                file_ext = Path(file_path).suffix.lower()
                
                if file_ext == '.pdf':
                    result = self.process_pdf(file_path)
                elif file_ext in self.supported_formats:
                    result = self.process_image(file_path, language)
                else:
                    logger.warning(f"Unsupported format: {file_ext}")
                    continue
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                continue
        
        return results

class OCRManager:
    """High-level OCR management system"""
    
    def __init__(self, temp_dir: str = None):
        self.document_processor = DocumentProcessor()
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "ocr_temp"
        self.temp_dir.mkdir(exist_ok=True)
    
    def process_file(self, file_path: str, language: str = 'en', 
                    extract_tables: bool = True) -> Union[OCRResult, DocumentResult]:
        """Process a single file (image or PDF)"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.pdf':
                return self.document_processor.process_pdf(file_path, extract_tables)
            else:
                return self.document_processor.process_image(file_path, language)
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise
    
    def process_base64_image(self, base64_data: str, language: str = 'en') -> OCRResult:
        """Process image from base64 data"""
        try:
            # Decode base64 data
            image_data = base64.b64decode(base64_data)
            
            # Create temporary file
            temp_file = self.temp_dir / f"temp_image_{datetime.now().timestamp()}.png"
            temp_file.write_bytes(image_data)
            
            # Process image
            result = self.document_processor.process_image(str(temp_file), language)
            
            # Clean up
            temp_file.unlink()
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing base64 image: {str(e)}")
            raise
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return [
            {'code': 'en', 'name': 'English'},
            {'code': 'es', 'name': 'Spanish'},
            {'code': 'fr', 'name': 'French'},
            {'code': 'de', 'name': 'German'},
            {'code': 'it', 'name': 'Italian'},
            {'code': 'pt', 'name': 'Portuguese'},
            {'code': 'ru', 'name': 'Russian'},
            {'code': 'zh', 'name': 'Chinese (Simplified)'},
            {'code': 'ja', 'name': 'Japanese'},
            {'code': 'ko', 'name': 'Korean'},
            {'code': 'ar', 'name': 'Arabic'},
            {'code': 'hi', 'name': 'Hindi'},
            {'code': 'auto', 'name': 'Auto-detect'}
        ]
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'tesseract_available': self.document_processor.ocr_engine.tesseract_available,
            'easyocr_available': self.document_processor.ocr_engine.easyocr_reader is not None,
            'supported_formats': self.document_processor.supported_formats,
            'supported_languages': len(self.get_supported_languages()),
            'temp_directory': str(self.temp_dir)
        }
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            for file in self.temp_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up temp files: {str(e)}")

# Utility functions
def validate_image_file(file_path: str) -> bool:
    """Validate if file is a supported image format"""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False

def estimate_processing_time(file_path: str) -> float:
    """Estimate processing time based on file size and type"""
    try:
        file_size = Path(file_path).stat().st_size / (1024 * 1024)  # MB
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            # Estimate based on file size (rough approximation)
            return file_size * 2.0  # 2 seconds per MB for PDF
        else:
            # Image processing is generally faster
            return file_size * 0.5  # 0.5 seconds per MB for images
            
    except Exception:
        return 10.0  # Default estimate

# Export main classes
__all__ = [
    'OCRManager',
    'DocumentProcessor', 
    'OCREngine',
    'ImagePreprocessor',
    'OCRResult',
    'DocumentResult',
    'DocumentPage',
    'validate_image_file',
    'estimate_processing_time'
]