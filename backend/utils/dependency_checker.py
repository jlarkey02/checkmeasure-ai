import logging
import importlib
import subprocess
import sys
from typing import Dict, List, Tuple
import traceback

logger = logging.getLogger(__name__)

class DependencyChecker:
    """Check and verify all system dependencies"""
    
    def __init__(self):
        self.required_packages = [
            ('cv2', 'opencv-python', 'Computer Vision'),
            ('pytesseract', 'pytesseract', 'Tesseract OCR'),
            ('easyocr', 'easyocr', 'EasyOCR'),
            ('PIL', 'Pillow', 'Image Processing'),
            ('skimage', 'scikit-image', 'Image Processing'),
            ('scipy', 'scipy', 'Scientific Computing'),
            ('sklearn', 'scikit-learn', 'Machine Learning'),
            ('matplotlib', 'matplotlib', 'Plotting'),
            ('numpy', 'numpy', 'Numerical Computing'),
            ('fitz', 'PyMuPDF', 'PDF Processing')
        ]
        
        self.system_dependencies = [
            ('tesseract', 'Tesseract OCR Engine'),
        ]
    
    def check_all_dependencies(self) -> Dict:
        """Check all dependencies and return detailed status"""
        result = {
            'all_dependencies_ok': True,
            'python_packages': {},
            'system_dependencies': {},
            'errors': [],
            'warnings': [],
            'installation_commands': []
        }
        
        # Check Python packages
        for module_name, package_name, description in self.required_packages:
            status = self._check_python_package(module_name, package_name, description)
            result['python_packages'][package_name] = status
            
            if not status['available']:
                result['all_dependencies_ok'] = False
                result['errors'].append(f"Missing package: {package_name} ({description})")
                result['installation_commands'].append(f"pip install {package_name}")
        
        # Check system dependencies
        for command, description in self.system_dependencies:
            status = self._check_system_command(command, description)
            result['system_dependencies'][command] = status
            
            if not status['available']:
                result['all_dependencies_ok'] = False
                result['errors'].append(f"Missing system dependency: {command} ({description})")
                if command == 'tesseract':
                    result['installation_commands'].append("brew install tesseract  # On macOS")
                    result['installation_commands'].append("apt-get install tesseract-ocr  # On Ubuntu")
        
        # Test critical functionality
        functionality_tests = self._test_critical_functionality()
        result['functionality_tests'] = functionality_tests
        
        for test_name, test_result in functionality_tests.items():
            if not test_result['success']:
                result['warnings'].append(f"Functionality test failed: {test_name} - {test_result['error']}")
        
        return result
    
    def _check_python_package(self, module_name: str, package_name: str, description: str) -> Dict:
        """Check if a Python package is available and working"""
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'Unknown')
            
            return {
                'available': True,
                'version': version,
                'description': description,
                'error': None
            }
        except ImportError as e:
            return {
                'available': False,
                'version': None,
                'description': description,
                'error': str(e)
            }
        except Exception as e:
            return {
                'available': False,
                'version': None,
                'description': description,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def _check_system_command(self, command: str, description: str) -> Dict:
        """Check if a system command is available"""
        try:
            result = subprocess.run([command, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_output = result.stdout.strip() or result.stderr.strip()
                return {
                    'available': True,
                    'version': version_output.split('\n')[0] if version_output else 'Unknown',
                    'description': description,
                    'error': None
                }
            else:
                return {
                    'available': False,
                    'version': None,
                    'description': description,
                    'error': f"Command failed with code {result.returncode}"
                }
        except subprocess.TimeoutExpired:
            return {
                'available': False,
                'version': None,
                'description': description,
                'error': "Command timeout"
            }
        except FileNotFoundError:
            return {
                'available': False,
                'version': None,
                'description': description,
                'error': "Command not found"
            }
        except Exception as e:
            return {
                'available': False,
                'version': None,
                'description': description,
                'error': str(e)
            }
    
    def _test_critical_functionality(self) -> Dict:
        """Test critical functionality to ensure everything works"""
        tests = {}
        
        # Test OpenCV
        tests['opencv_basic'] = self._test_opencv()
        
        # Test Tesseract
        tests['tesseract_basic'] = self._test_tesseract()
        
        # Test EasyOCR
        tests['easyocr_basic'] = self._test_easyocr()
        
        # Test PIL/Image processing
        tests['image_processing'] = self._test_image_processing()
        
        # Test PDF processing
        tests['pdf_processing'] = self._test_pdf_processing()
        
        return tests
    
    def _test_opencv(self) -> Dict:
        """Test OpenCV functionality"""
        try:
            import cv2
            import numpy as np
            
            # Create a simple test image
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            test_image[25:75, 25:75] = [255, 255, 255]
            
            # Test basic operations
            gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            return {
                'success': True,
                'error': None,
                'details': f"OpenCV {cv2.__version__} working correctly"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': traceback.format_exc()
            }
    
    def _test_tesseract(self) -> Dict:
        """Test Tesseract OCR functionality"""
        try:
            import pytesseract
            from PIL import Image
            import numpy as np
            
            # Create a simple test image with text
            test_image = Image.new('RGB', (200, 50), color='white')
            
            # Try to run OCR on the test image
            text = pytesseract.image_to_string(test_image, config='--psm 6')
            
            return {
                'success': True,
                'error': None,
                'details': "Tesseract OCR working correctly"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': traceback.format_exc()
            }
    
    def _test_easyocr(self) -> Dict:
        """Test EasyOCR functionality"""
        try:
            import easyocr
            import numpy as np
            
            # Create a simple test image
            test_image = np.ones((50, 200, 3), dtype=np.uint8) * 255
            
            # Initialize reader (this might download models on first run)
            reader = easyocr.Reader(['en'])
            
            # Test reading (should not crash even on empty image)
            results = reader.readtext(test_image)
            
            return {
                'success': True,
                'error': None,
                'details': "EasyOCR working correctly"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': traceback.format_exc()
            }
    
    def _test_image_processing(self) -> Dict:
        """Test image processing functionality"""
        try:
            from PIL import Image, ImageEnhance
            import numpy as np
            
            # Create test image
            test_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            test_image = Image.fromarray(test_array)
            
            # Test enhancements
            enhancer = ImageEnhance.Contrast(test_image)
            enhanced = enhancer.enhance(1.5)
            
            return {
                'success': True,
                'error': None,
                'details': "Image processing working correctly"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': traceback.format_exc()
            }
    
    def _test_pdf_processing(self) -> Dict:
        """Test PDF processing functionality"""
        try:
            import fitz  # PyMuPDF
            
            # Create a simple test PDF in memory
            doc = fitz.open()  # Create empty document
            page = doc.new_page()  # Add a page
            page.insert_text((72, 72), "Test text")  # Add some text
            
            # Get text back
            text = page.get_text()
            
            doc.close()
            
            return {
                'success': True,
                'error': None,
                'details': "PDF processing working correctly"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': traceback.format_exc()
            }
    
    def get_installation_instructions(self) -> Dict:
        """Get detailed installation instructions"""
        return {
            'pip_packages': [
                "pip install opencv-python",
                "pip install pytesseract",
                "pip install easyocr",
                "pip install Pillow",
                "pip install scikit-image",
                "pip install scipy",
                "pip install scikit-learn",
                "pip install matplotlib"
            ],
            'system_dependencies': {
                'macOS': [
                    "brew install tesseract",
                    "brew install tesseract-lang  # For additional languages"
                ],
                'Ubuntu/Debian': [
                    "sudo apt-get update",
                    "sudo apt-get install tesseract-ocr",
                    "sudo apt-get install tesseract-ocr-eng  # For English"
                ],
                'Windows': [
                    "Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki",
                    "Add Tesseract to PATH environment variable"
                ]
            },
            'troubleshooting': [
                "If EasyOCR fails to initialize, it may need to download models (requires internet)",
                "If Tesseract is not found, ensure it's installed and in PATH",
                "On macOS, use 'which tesseract' to verify installation",
                "Some dependencies may require system restarts after installation"
            ]
        }