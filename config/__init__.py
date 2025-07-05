"""
LinkedIn Post Extractor - Configuration Package

This package contains configuration modules for the LinkedIn Post Extractor including:
- Logging configuration and setup
- Application constants and selectors
- Default settings and templates
"""

from .constants import *
from .logging_config import configure_logging, get_logger, setup_logging

__all__ = [
    # Logging functions
    "configure_logging",
    "get_logger", 
    "setup_logging",
    
    # Constants (imported via *)
    "APP_NAME",
    "APP_VERSION",
    "LINKEDIN_SELECTORS",
    "WEBDRIVER_CONFIG",
    "OUTPUT_CONFIG",
    "MARKDOWN_TEMPLATE",
    "ERROR_MESSAGES",
    "SUCCESS_MESSAGES",
]
