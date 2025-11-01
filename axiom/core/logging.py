"""
Structured logging with JSON format and per-run log files.

Provides context-aware logging with run_id tracking and file rotation.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from axiom.core.models import EET


class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON-structured logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.now(EET).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add run_id if available
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Custom formatter for human-readable text logs."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class RunLogger:
    """Logger with run context for structured logging."""
    
    def __init__(
        self,
        run_id: str,
        log_dir: str = "logs",
        log_format: str = "json",
        log_level: str = "INFO",
    ):
        """
        Initialize run logger.
        
        Args:
            run_id: Unique run identifier
            log_dir: Directory for log files
            log_format: Log format (json or text)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.run_id = run_id
        self.log_dir = Path(log_dir)
        self.log_format = log_format
        self.log_level = getattr(logging, log_level.upper())
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(f"axiom.{run_id}")
        self.logger.setLevel(self.log_level)
        self.logger.propagate = False
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # Add console handler
        self._add_console_handler()
        
        # Add file handler
        self._add_file_handler()
    
    def _add_console_handler(self) -> None:
        """Add console handler with appropriate formatter."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        if self.log_format == "json":
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(TextFormatter())
        
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self) -> None:
        """Add file handler for per-run logging."""
        log_file = self.log_dir / f"run_{self.run_id}.log"
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(self.log_level)
        
        if self.log_format == "json":
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(TextFormatter())
        
        self.logger.addHandler(file_handler)
    
    def _log_with_context(self, level: int, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log message with run context."""
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "",
            0,
            msg,
            (),
            None,
        )
        record.run_id = self.run_id
        if extra:
            record.extra = extra
        self.logger.handle(record)
    
    def debug(self, msg: str, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, msg, extra=kwargs)
    
    def info(self, msg: str, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, msg, extra=kwargs)
    
    def warning(self, msg: str, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, msg, extra=kwargs)
    
    def error(self, msg: str, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, msg, extra=kwargs)
    
    def exception(self, msg: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(msg, extra={"run_id": self.run_id, **kwargs})


def setup_logging(
    run_id: str,
    log_dir: str = "logs",
    log_format: str = "json",
    log_level: str = "INFO",
) -> RunLogger:
    """
    Setup structured logging for a run.
    
    Args:
        run_id: Unique run identifier
        log_dir: Directory for log files
        log_format: Log format (json or text)
        log_level: Logging level
        
    Returns:
        RunLogger instance
    """
    return RunLogger(run_id, log_dir, log_format, log_level)
