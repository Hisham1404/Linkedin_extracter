"""
LinkedIn Post Extractor - Custom Exception Classes

This module defines a comprehensive hierarchy of custom exception classes
for the LinkedIn Post Extractor application, providing structured error
handling and categorization.
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum


class ErrorCategory(Enum):
    """Categorization of errors for better handling and reporting."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    BROWSER = "browser"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class LinkedInExtractorError(Exception):
    """Base exception class for LinkedIn Post Extractor application."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        
    def __str__(self):
        return self.message
        
    def __repr__(self):
        return f"{self.__class__.__name__}('{self.message}', error_code='{self.error_code}')"


class NetworkError(LinkedInExtractorError):
    """Raised when network-related errors occur."""
    pass


class AuthenticationError(LinkedInExtractorError):
    """Raised when authentication issues occur."""
    pass


class ExtractionError(LinkedInExtractorError):
    """Raised when content extraction fails."""
    pass


class ValidationError(LinkedInExtractorError):
    """Raised when input validation fails."""
    pass


class BrowserError(LinkedInExtractorError):
    """Raised when browser automation fails."""
    pass


class ScrollError(BrowserError):
    """Raised when scroll automation fails."""
    pass


class RateLimitError(NetworkError):
    """Raised when rate limiting is encountered."""
    pass


class ConfigurationError(LinkedInExtractorError):
    """Raised when configuration issues occur."""
    pass


def get_error_category(error: Exception) -> ErrorCategory:
    """Get the category of an error based on its type."""
    if isinstance(error, NetworkError):
        return ErrorCategory.NETWORK
    elif isinstance(error, AuthenticationError):
        return ErrorCategory.AUTHENTICATION
    elif isinstance(error, ExtractionError):
        return ErrorCategory.EXTRACTION
    elif isinstance(error, ValidationError):
        return ErrorCategory.VALIDATION
    elif isinstance(error, BrowserError):
        return ErrorCategory.BROWSER
    elif isinstance(error, ConfigurationError):
        return ErrorCategory.CONFIGURATION
    else:
        return ErrorCategory.UNKNOWN


def is_recoverable_error(error: Exception) -> bool:
    """Determine if an error is recoverable through retry."""
    if isinstance(error, (NetworkError, RateLimitError, ScrollError)):
        return True
    elif isinstance(error, (AuthenticationError, ValidationError, ConfigurationError)):
        return False
    else:
        return False


def create_error_context(user_action: str, system_state: Optional[Dict[str, Any]] = None,
                        additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create error context for better error reporting."""
    context = {
        "user_action": user_action,
        "system_state": system_state or {},
        "additional_info": additional_info or {},
        "timestamp": str(type(None)),  # Will be replaced with actual timestamp
    }
    return context


# Error handling utilities
def handle_error_with_context(error: Exception, context: Dict[str, Any], 
                            logger: Optional[logging.Logger] = None) -> None:
    """Handle an error with context information."""
    if logger:
        logger.error(f"Error: {error}", extra={"context": context})
    else:
        print(f"Error: {error} (Context: {context})")


def chain_exceptions(primary_error: Exception, secondary_error: Exception) -> Exception:
    """Chain exceptions to preserve error context."""
    return LinkedInExtractorError(
        f"Primary error: {primary_error}. Secondary error: {secondary_error}",
        context={"primary_error": str(primary_error), "secondary_error": str(secondary_error)}
    )


def format_error_message(error: Exception, include_context: bool = True) -> str:
    """Format error message for user display."""
    message = str(error)
    
    if include_context and isinstance(error, LinkedInExtractorError) and error.context:
        context_str = ", ".join([f"{k}: {v}" for k, v in error.context.items()])
        message = f"{message} (Context: {context_str})"
    
    return message


def get_error_severity(error: Exception) -> str:
    """Get the severity level of an error."""
    if isinstance(error, (AuthenticationError, ConfigurationError)):
        return "critical"
    elif isinstance(error, (NetworkError, BrowserError, ExtractionError)):
        return "high"
    elif isinstance(error, ValidationError):
        return "medium"
    else:
        return "low"


def create_error_report(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a comprehensive error report."""
    return {
        "error_type": type(error).__name__,
        "message": str(error),
        "category": get_error_category(error).value,
        "severity": get_error_severity(error),
        "recoverable": is_recoverable_error(error),
        "context": context or {},
        "error_code": getattr(error, 'error_code', None),
    }


# Export all public classes and functions
__all__ = [
    "LinkedInExtractorError",
    "NetworkError",
    "AuthenticationError", 
    "ExtractionError",
    "ValidationError",
    "BrowserError",
    "ScrollError",
    "RateLimitError",
    "ConfigurationError",
    "ErrorCategory",
    "get_error_category",
    "is_recoverable_error",
    "create_error_context",
    "handle_error_with_context",
    "chain_exceptions",
    "format_error_message",
    "get_error_severity",
    "create_error_report",
]
