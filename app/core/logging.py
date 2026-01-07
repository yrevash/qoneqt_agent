"""
Comprehensive Logging System
Logs every action, request, and system event with structured logging
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import traceback


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing and analysis"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'action'):
            log_data['action'] = record.action
        if hasattr(record, 'metadata'):
            log_data['metadata'] = record.metadata
        
        return json.dumps(log_data)


class AuditLogger:
    """Audit logger for tracking all system actions"""
    
    def __init__(self, name: str = "audit"):
        self.logger = logging.getLogger(name)
    
    def log_action(
        self,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ):
        """Log a user action or system event"""
        extra = {
            'action': action,
            'user_id': user_id,
            'metadata': {
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details or {},
                'success': success,
            }
        }
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(
            level,
            f"Action: {action} | User: {user_id} | Success: {success}",
            extra=extra
        )


class RequestLogger:
    """Logger for HTTP requests and API calls"""
    
    def __init__(self, name: str = "api"):
        self.logger = logging.getLogger(name)
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log an HTTP request"""
        extra = {
            'request_id': request_id,
            'user_id': user_id,
            'metadata': {
                'method': method,
                'path': path,
                'status_code': status_code,
                'duration_ms': duration_ms,
                **(metadata or {})
            }
        }
        
        level = logging.INFO if status_code < 400 else logging.WARNING
        self.logger.log(
            level,
            f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
            extra=extra
        )


class AgentLogger:
    """Logger for agent actions and decisions"""
    
    def __init__(self, name: str = "agent"):
        self.logger = logging.getLogger(name)
    
    def log_decision(
        self,
        agent_id: str,
        decision_type: str,
        decision: str,
        reasoning: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log an agent decision"""
        extra = {
            'user_id': agent_id,
            'action': f'agent_decision_{decision_type}',
            'metadata': {
                'decision': decision,
                'reasoning': reasoning,
                **(metadata or {})
            }
        }
        
        self.logger.info(
            f"Agent {agent_id} - {decision_type}: {decision}",
            extra=extra
        )


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_json: bool = True,
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """
    Setup comprehensive logging system
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        enable_json: Use JSON formatting
        enable_console: Enable console output
        enable_file: Enable file logging
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Choose formatter
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handlers
    if enable_file:
        # General application log (rotating by size)
        app_handler = RotatingFileHandler(
            log_path / "app.log",
            maxBytes=50_000_000,  # 50MB
            backupCount=10
        )
        app_handler.setFormatter(formatter)
        root_logger.addHandler(app_handler)
        
        # Error log (rotating by time)
        error_handler = TimedRotatingFileHandler(
            log_path / "error.log",
            when='midnight',
            interval=1,
            backupCount=30
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        # Audit log (never rotate, for compliance)
        audit_handler = logging.FileHandler(log_path / "audit.log")
        audit_handler.setFormatter(formatter)
        
        audit_logger = logging.getLogger("audit")
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        
        # API request log
        api_handler = TimedRotatingFileHandler(
            log_path / "api.log",
            when='midnight',
            interval=1,
            backupCount=30
        )
        api_handler.setFormatter(formatter)
        
        api_logger = logging.getLogger("api")
        api_logger.addHandler(api_handler)
        api_logger.setLevel(logging.INFO)
        
        # Agent activity log
        agent_handler = TimedRotatingFileHandler(
            log_path / "agent.log",
            when='midnight',
            interval=1,
            backupCount=30
        )
        agent_handler.setFormatter(formatter)
        
        agent_logger = logging.getLogger("agent")
        agent_logger.addHandler(agent_handler)
        agent_logger.setLevel(logging.INFO)
    
    # Log startup
    logging.info("Logging system initialized", extra={
        'action': 'system_startup',
        'metadata': {
            'log_level': log_level,
            'log_dir': log_dir,
            'json_enabled': enable_json,
        }
    })


# Convenience functions
def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    return AuditLogger()


def get_request_logger() -> RequestLogger:
    """Get request logger instance"""
    return RequestLogger()


def get_agent_logger() -> AgentLogger:
    """Get agent logger instance"""
    return AgentLogger()
