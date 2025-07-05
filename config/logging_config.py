"""
LinkedIn Post Extractor - Logging Configuration

This module provides centralized logging configuration for the LinkedIn Post Extractor.
It sets up colored console output, file logging, and appropriate log levels for
different components of the application.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

import colorlog

# Default log levels for different loggers
DEFAULT_LOG_LEVELS = {
    "selenium": logging.WARNING,
    "urllib3": logging.WARNING,
    "requests": logging.WARNING,
    "httpx": logging.WARNING,
}


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    verbose: bool = False
) -> logging.Logger:
    """
    Setup centralized logging configuration for the application.
    
    Args:
        log_level: Base log level for the application (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file. If None, only console logging is used
        verbose: Enable verbose logging (DEBUG level for all loggers)
        
    Returns:
        Configured logger instance for the main application
    """
    # Determine log level
    if verbose:
        level = logging.DEBUG
    else:
        level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create main logger
    logger = logging.getLogger("linkedin_extractor")
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Setup console handler with colors
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Color formatter for console
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Setup file handler if log file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler to prevent large log files
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)  # Always debug level for files
        
        # File formatter (no colors)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Configure third-party library log levels
    for logger_name, logger_level in DEFAULT_LOG_LEVELS.items():
        external_logger = logging.getLogger(logger_name)
        external_logger.setLevel(logger_level)
    
    # Log the configuration
    logger.info(f"Logging initialized - Level: {logging.getLevelName(level)}")
    if log_file:
        logger.info(f"Log file: {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger for a specific module or component.
    
    Args:
        name: Name of the logger (typically __name__ of the module)
        
    Returns:
        Logger instance configured as child of main application logger
    """
    return logging.getLogger(f"linkedin_extractor.{name}")


# Convenience function for quick setup
def configure_logging(verbose: bool = False, log_file: str = "logs/linkedin_extractor.log"):
    """
    Quick logging setup with default parameters.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
        log_file: Path to log file relative to project root
    """
    return setup_logging(
        log_level="DEBUG" if verbose else "INFO",
        log_file=log_file,
        verbose=verbose
    )
