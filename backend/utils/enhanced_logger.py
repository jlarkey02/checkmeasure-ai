import logging
import logging.handlers
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
import traceback
import sys

class EnhancedLogger:
    """Enhanced logging system with file rotation, structured logging, and debug capabilities"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure different loggers for different purposes
        self.app_logger = self._setup_logger("app", "app.log", logging.INFO)
        self.error_logger = self._setup_logger("error", "error.log", logging.ERROR)
        self.debug_logger = self._setup_logger("debug", "debug.log", logging.DEBUG)
        self.claude_logger = self._setup_logger("claude", "claude-vision.log", logging.DEBUG)
        
        # In-memory storage for recent logs (for dashboard)
        self.recent_logs: List[Dict] = []
        self.max_recent_logs = 1000
        
    def _setup_logger(self, name: str, filename: str, level: int) -> logging.Logger:
        """Setup a logger with rotation and formatting"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create rotating file handler (10MB max, keep 7 files)
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / filename,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=7,
            encoding='utf-8'
        )
        
        # Create formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Also log to console for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_request(self, request_id: str, endpoint: str, method: str, 
                   params: Optional[Dict] = None, body: Optional[Dict] = None) -> None:
        """Log API request with structured data"""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "params": params,
            "body": body if body and len(str(body)) < 1000 else "Large body omitted"
        }
        
        self.app_logger.info(f"Request {request_id}: {method} {endpoint}")
        self.debug_logger.debug(json.dumps(log_entry, indent=2))
        
        # Store in memory
        self._add_to_recent(log_entry, "request")
        
    def log_response(self, request_id: str, status_code: int, 
                    response_time_ms: float, response_data: Optional[Dict] = None) -> None:
        """Log API response with timing"""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "response_preview": str(response_data)[:200] if response_data else None
        }
        
        self.app_logger.info(
            f"Response {request_id}: {status_code} in {response_time_ms:.2f}ms"
        )
        self.debug_logger.debug(json.dumps(log_entry, indent=2))
        
        # Store in memory
        self._add_to_recent(log_entry, "response")
    
    def log_error(self, error: Exception, context: str, 
                 request_id: Optional[str] = None, 
                 additional_info: Optional[Dict] = None) -> str:
        """Log error with full context and return error ID"""
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        error_details = {
            "error_id": error_id,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "additional_info": additional_info or {}
        }
        
        # Log to error logger
        self.error_logger.error(
            f"Error {error_id} in {context}: {type(error).__name__}: {str(error)}"
        )
        
        # Log full details to debug logger
        self.debug_logger.error(json.dumps(error_details, indent=2))
        
        # Store in memory
        self._add_to_recent(error_details, "error")
        
        return error_id
    
    def log_claude_vision(self, action: str, prompt: Optional[str] = None, 
                         response: Optional[Dict] = None, cost: Optional[float] = None,
                         processing_time_ms: Optional[float] = None) -> None:
        """Log Claude Vision API interactions"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "prompt_preview": prompt[:200] if prompt else None,
            "response_preview": str(response)[:200] if response else None,
            "cost_usd": cost,
            "processing_time_ms": processing_time_ms
        }
        
        self.claude_logger.info(
            f"Claude Vision {action}: "
            f"{'$' + str(cost) if cost else ''} "
            f"{processing_time_ms:.2f}ms" if processing_time_ms else ""
        )
        self.claude_logger.debug(json.dumps(log_entry, indent=2))
        
        # Store in memory
        self._add_to_recent(log_entry, "claude_vision")
    
    def log_processing_step(self, step_name: str, status: str, 
                           duration_ms: Optional[float] = None,
                           details: Optional[Dict] = None) -> None:
        """Log individual processing steps for debugging"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "status": status,
            "duration_ms": duration_ms,
            "details": details
        }
        
        level = logging.INFO if status == "success" else logging.WARNING
        self.debug_logger.log(
            level,
            f"Processing step '{step_name}': {status} "
            f"({duration_ms:.2f}ms)" if duration_ms else ""
        )
        
        if details:
            self.debug_logger.debug(json.dumps(details, indent=2))
        
        # Store in memory
        self._add_to_recent(log_entry, "processing_step")
    
    def _add_to_recent(self, entry: Dict, entry_type: str) -> None:
        """Add log entry to in-memory storage for dashboard"""
        entry["log_type"] = entry_type
        self.recent_logs.append(entry)
        
        # Keep only recent logs
        if len(self.recent_logs) > self.max_recent_logs:
            self.recent_logs = self.recent_logs[-self.max_recent_logs:]
    
    def get_recent_logs(self, log_type: Optional[str] = None, 
                       limit: int = 100) -> List[Dict]:
        """Get recent logs for dashboard display"""
        logs = self.recent_logs
        
        if log_type:
            logs = [log for log in logs if log.get("log_type") == log_type]
        
        return logs[-limit:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        errors = [log for log in self.recent_logs if log.get("log_type") == "error"]
        
        if not errors:
            return {
                "total_errors": 0,
                "error_types": {},
                "recent_errors": []
            }
        
        error_types = {}
        for error in errors:
            error_type = error.get("error_type", "Unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(errors),
            "error_types": error_types,
            "recent_errors": errors[-5:]
        }
    
    def export_logs(self, start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   log_types: Optional[List[str]] = None) -> List[Dict]:
        """Export logs for analysis"""
        logs = self.recent_logs
        
        # Filter by date if provided
        if start_date or end_date:
            filtered_logs = []
            for log in logs:
                try:
                    log_time = datetime.fromisoformat(log.get("timestamp", ""))
                    if start_date and log_time < start_date:
                        continue
                    if end_date and log_time > end_date:
                        continue
                    filtered_logs.append(log)
                except:
                    continue
            logs = filtered_logs
        
        # Filter by type if provided
        if log_types:
            logs = [log for log in logs if log.get("log_type") in log_types]
        
        return logs
    
    def clear_old_logs(self, days_to_keep: int = 7) -> None:
        """Clear log files older than specified days"""
        import glob
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for log_file in self.log_dir.glob("*.log.*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                self.app_logger.info(f"Deleted old log file: {log_file}")

# Global logger instance
enhanced_logger = EnhancedLogger()

# Convenience functions
def log_request(request_id: str, endpoint: str, method: str, **kwargs):
    return enhanced_logger.log_request(request_id, endpoint, method, **kwargs)

def log_response(request_id: str, status_code: int, response_time_ms: float, **kwargs):
    return enhanced_logger.log_response(request_id, status_code, response_time_ms, **kwargs)

def log_error(error: Exception, context: str, request_id=None, additional_info=None, **kwargs) -> str:
    # Handle both calling styles - named parameters or kwargs
    if kwargs and additional_info:
        # If both are provided, merge kwargs into additional_info
        additional_info = {**additional_info, **kwargs}
    elif kwargs and not additional_info:
        # If only kwargs provided, use them as additional_info
        additional_info = kwargs
    return enhanced_logger.log_error(error, context, request_id, additional_info)

def log_claude_vision(action: str, **kwargs):
    return enhanced_logger.log_claude_vision(action, **kwargs)

def log_processing_step(step_name: str, status: str, **kwargs):
    return enhanced_logger.log_processing_step(step_name, status, **kwargs)