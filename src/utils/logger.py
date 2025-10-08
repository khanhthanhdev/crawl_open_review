"""
Logging configuration for OpenReview Crawler.

This module provides centralized logging configuration with support for:
- Console and file output
- Rotating log files
- Structured logging
- Multiple log levels
- Easy configuration for different environments
"""

import logging
import logging.handlers
import sys

from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs for better parsing."""

    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        # Add any additional fields that might be useful
        if hasattr(record, 'funcName'):
            log_entry['function'] = record.funcName
        if hasattr(record, 'lineno'):
            log_entry['line'] = record.lineno
        if hasattr(record, 'pathname'):
            log_entry['file'] = Path(record.pathname).name

        return json.dumps(log_entry, ensure_ascii=False)


class CrawlerLogger:
    """Centralized logger configuration for the OpenReview crawler."""

    def __init__(self, name: str = "openreview_crawler"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # Set to lowest level, let handlers filter

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create formatters
        self.console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        self.file_formatter = StructuredFormatter()

        # Setup handlers
        self._setup_console_handler()
        self._setup_file_handler()

    def _setup_console_handler(self) -> None:
        """Setup console logging handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Console shows INFO and above
        console_handler.setFormatter(self.console_formatter)
        self.logger.addHandler(console_handler)

    def _setup_file_handler(self) -> None:
        """Setup rotating file handler for persistent logging."""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Rotating file handler (10MB per file, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "crawler.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File logs everything
        file_handler.setFormatter(self.file_formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger

    def set_level(self, level: str) -> None:
        """Set the logging level for all handlers.

        Args:
            level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # Update handler levels
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                # Console handler: INFO and above
                handler.setLevel(max(log_level, logging.INFO))
            else:
                # File handler: use the set level
                handler.setLevel(log_level)


# Global logger instance
_logger_instance: Optional[CrawlerLogger] = None


def get_logger(name: str = "openreview_crawler") -> logging.Logger:
    """Get or create the global logger instance.

    Args:
        name: Logger name (usually __name__ for module-specific logging)

    Returns:
        Configured logger instance
    """
    global _logger_instance

    if _logger_instance is None:
        _logger_instance = CrawlerLogger()

    # Return child logger for the specific module
    return _logger_instance.get_logger().getChild(name)


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    structured_file_logs: bool = True
) -> logging.Logger:
    """Setup logging configuration.

    Args:
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        structured_file_logs: Whether to use JSON structured logs for files

    Returns:
        Root logger instance
    """
    global _logger_instance

    # Create logger instance
    _logger_instance = CrawlerLogger()

    # Set level
    _logger_instance.set_level(level)

    # Configure handlers based on options
    if not log_to_console:
        # Remove console handler
        for handler in _logger_instance.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                _logger_instance.logger.removeHandler(handler)

    if not log_to_file:
        # Remove file handler
        for handler in _logger_instance.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                _logger_instance.logger.removeHandler(handler)

    return _logger_instance.get_logger()


def log_function_call(func_name: str, args: Dict[str, Any] = None, level: str = "DEBUG") -> None:
    """Log function calls with parameters.

    Args:
        func_name: Name of the function being called
        args: Dictionary of arguments passed to the function
        level: Logging level
    """
    logger = get_logger()
    message = f"Calling {func_name}"
    if args:
        # Sanitize sensitive information
        safe_args = {}
        for key, value in args.items():
            if 'password' in key.lower() or 'token' in key.lower():
                safe_args[key] = "***"
            else:
                safe_args[key] = str(value)[:100]  # Truncate long values

        message += f" with args: {safe_args}"

    getattr(logger, level.lower())(message)


def log_performance(operation: str, duration: float, extra_info: Dict[str, Any] = None) -> None:
    """Log performance metrics.

    Args:
        operation: Name of the operation
        duration: Duration in seconds
        extra_info: Additional performance information
    """
    logger = get_logger("performance")
    message = f"{operation} completed in {duration:.2f}s"

    if extra_info:
        message += f" - {extra_info}"

    logger.info(message)


def log_api_call(endpoint: str, method: str = "GET", status_code: int = None,
                 duration: float = None, error: str = None) -> None:
    """Log API calls with details.

    Args:
        endpoint: API endpoint URL
        method: HTTP method
        status_code: HTTP status code
        duration: Request duration in seconds
        error: Error message if any
    """
    logger = get_logger("api")

    if error:
        logger.error(f"API call failed: {method} {endpoint} - {error}")
    else:
        message = f"API call: {method} {endpoint}"
        if status_code:
            message += f" - Status: {status_code}"
        if duration:
            message += f" - Duration: {duration:.2f}s"

        logger.info(message)


# Convenience functions for common logging patterns
def log_crawl_start(venue: str, year: int, paper_count: int = None) -> None:
    """Log the start of a crawling operation."""
    logger = get_logger()
    message = f"Starting crawl for {venue} {year}"
    if paper_count:
        message += f" ({paper_count} papers)"
    logger.info(message)


def log_crawl_progress(current: int, total: int, paper_title: str = None) -> None:
    """Log crawling progress."""
    logger = get_logger()
    percentage = (current / total) * 100 if total > 0 else 0
    message = f"Progress: {current}/{total} ({percentage:.1f}%)"
    if paper_title:
        message += f" - {paper_title[:50]}..."
    logger.info(message)


def log_crawl_complete(venue: str, year: int, paper_count: int, duration: float) -> None:
    """Log completion of crawling operation."""
    logger = get_logger()
    logger.info(f"Crawl completed for {venue} {year}: {paper_count} papers in {duration:.2f}s")


def log_error_with_context(error: Exception, context: str = None, extra_data: Dict = None) -> None:
    """Log errors with additional context."""
    logger = get_logger()
    message = f"Error in {context}: {str(error)}" if context else f"Error: {str(error)}"

    if extra_data:
        message += f" - Context: {extra_data}"

    logger.error(message, exc_info=True)


# Initialize default logging on import
setup_logging()
