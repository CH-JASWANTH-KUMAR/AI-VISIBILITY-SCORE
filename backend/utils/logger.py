"""
Structured Logging Utility
Production-grade logging with timestamps and context
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "ai_visibility", level: str = "INFO") -> logging.Logger:
    """
    Setup structured logger with console and file handlers
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # File handler for detailed logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"ai_visibility_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Format with timestamp
    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_format = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(console_format)
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def log_api_call(logger: logging.Logger, provider: str, prompt: str, response: str, elapsed: float, tokens: int):
    """Log API call details"""
    logger.info(
        f"API Call | Provider: {provider} | "
        f"Prompt: {prompt[:50]}... | "
        f"Response: {response[:50]}... | "
        f"Time: {elapsed:.2f}s | Tokens: {tokens}"
    )


def log_error(logger: logging.Logger, error: Exception, context: str = ""):
    """Log error with context"""
    logger.error(
        f"Error | {context} | "
        f"Type: {type(error).__name__} | "
        f"Message: {str(error)}"
    )


# Create default logger
default_logger = setup_logger()
