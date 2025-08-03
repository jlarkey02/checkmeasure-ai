import logging
import traceback
import sys
from datetime import datetime
from typing import Dict, Optional, Any
import json

class ErrorLogger:
    """Enhanced error logging and tracking system"""
    
    def __init__(self):
        self.setup_logging()
        self.error_history = []
    
    def setup_logging(self):
        """Configure comprehensive logging"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # Detailed logger for our modules
        pdf_logger = logging.getLogger('pdf_processing')
        pdf_logger.setLevel(logging.DEBUG)
    
    def log_error(self, error: Exception, context: str, additional_info: Optional[Dict] = None) -> str:
        """Log an error with full context and return error ID"""
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        error_details = {
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'additional_info': additional_info or {}
        }
        
        # Store in history
        self.error_history.append(error_details)
        
        # Keep only last 100 errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        # Log to console
        logger = logging.getLogger(context)
        logger.error(f"Error {error_id}: {str(error)}")
        logger.debug(f"Full traceback for {error_id}:\n{traceback.format_exc()}")
        
        return error_id
    
    def log_warning(self, message: str, context: str, additional_info: Optional[Dict] = None) -> str:
        """Log a warning with context"""
        warning_id = f"WARN_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        warning_details = {
            'warning_id': warning_id,
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'message': message,
            'additional_info': additional_info or {}
        }
        
        # Store in history
        self.error_history.append(warning_details)
        
        # Log to console
        logger = logging.getLogger(context)
        logger.warning(f"Warning {warning_id}: {message}")
        
        return warning_id
    
    def log_info(self, message: str, context: str, additional_info: Optional[Dict] = None):
        """Log information with context"""
        logger = logging.getLogger(context)
        logger.info(f"{context}: {message}")
        
        if additional_info:
            logger.debug(f"Additional info: {json.dumps(additional_info, indent=2)}")
    
    def get_error_details(self, error_id: str) -> Optional[Dict]:
        """Get detailed error information by ID"""
        for error in self.error_history:
            if error.get('error_id') == error_id or error.get('warning_id') == error_id:
                return error
        return None
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors"""
        return self.error_history[-limit:] if self.error_history else []
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
    
    def get_error_summary(self) -> Dict:
        """Get summary of recent errors"""
        if not self.error_history:
            return {
                'total_errors': 0,
                'recent_errors': [],
                'error_types': {},
                'contexts': {}
            }
        
        error_types = {}
        contexts = {}
        
        for item in self.error_history:
            # Count error types
            error_type = item.get('error_type', 'warning')
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Count contexts
            context = item.get('context', 'unknown')
            contexts[context] = contexts.get(context, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': self.error_history[-5:],
            'error_types': error_types,
            'contexts': contexts
        }

# Global error logger instance
error_logger = ErrorLogger()

def log_error(error: Exception, context: str, additional_info: Optional[Dict] = None) -> str:
    """Global function to log errors"""
    return error_logger.log_error(error, context, additional_info)

def log_warning(message: str, context: str, additional_info: Optional[Dict] = None) -> str:
    """Global function to log warnings"""
    return error_logger.log_warning(message, context, additional_info)

def log_info(message: str, context: str, additional_info: Optional[Dict] = None):
    """Global function to log information"""
    return error_logger.log_info(message, context, additional_info)