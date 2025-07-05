"""
LinkedIn Post Extractor - Source Package

This package contains the core modules for LinkedIn post extraction including:
- URL validation and processing
- Web automation and scraping
- HTML parsing and content extraction
- Markdown generation and file output
- Error handling and logging
- Retry logic with exponential backoff
- Partial extraction handling
- Comprehensive error reporting
"""

__version__ = "0.1.0"
__author__ = "LinkedIn Post Extractor Team"
__description__ = "A Python tool for extracting LinkedIn posts and saving them as Markdown files"

# Import and export main classes for easy access
try:
    # Core modules
    from .url_validator import URLValidator, validate_linkedin_url
    from .browser_manager import WebDriverManager
    from .content_parser import ContentParser, parse_linkedin_profile
    from .markdown_generator import MarkdownGenerator, generate_markdown_from_posts
    from .scroll_automator import ScrollAutomator, create_scroll_automator
    
    # Progress tracking
    from .progress_tracker import (
        ProgressTracker, ProgressPhase, ProgressStats, ProgressCallback,
        create_progress_tracker, create_console_callback
    )
    
    # Error handling
    from .exceptions import (
        LinkedInExtractorError, NetworkError, AuthenticationError,
        ExtractionError, ValidationError, BrowserError, ScrollError,
        RateLimitError, ConfigurationError, ErrorCategory,
        get_error_category, is_recoverable_error
    )
    
    # Retry handling
    from .retry_handler import (
        RetryHandler, RetryConfig, RetryStats, RetryStrategy,
        retry_on_failure, retry_on_failure_async,
        create_retry_config, create_network_retry_config, create_browser_retry_config
    )
    
    # Partial extraction handling
    from .partial_extraction_handler import (
        PartialExtractionHandler, PartialExtractionResult, ExtractionStrategy,
        create_extraction_handler, create_lenient_extraction_handler, create_strict_extraction_handler
    )
    
    # Error reporting
    from .error_reporter import (
        ErrorReporter, ErrorSeverity, ErrorReport, ErrorContext, SystemInfo,
        ReportFormat, create_error_reporter, get_global_error_reporter, report_error
    )
    
    __all__ = [
        # Core functionality
        "URLValidator", "validate_linkedin_url",
        "WebDriverManager",
        "ContentParser", "parse_linkedin_profile",
        "MarkdownGenerator", "generate_markdown_from_posts",
        "ScrollAutomator", "create_scroll_automator",
        
        # Progress tracking
        "ProgressTracker", "ProgressPhase", "ProgressStats", "ProgressCallback",
        "create_progress_tracker", "create_console_callback",
        
        # Error handling
        "LinkedInExtractorError", "NetworkError", "AuthenticationError",
        "ExtractionError", "ValidationError", "BrowserError", "ScrollError",
        "RateLimitError", "ConfigurationError", "ErrorCategory",
        "get_error_category", "is_recoverable_error",
        
        # Retry handling
        "RetryHandler", "RetryConfig", "RetryStats", "RetryStrategy",
        "retry_on_failure", "retry_on_failure_async",
        "create_retry_config", "create_network_retry_config", "create_browser_retry_config",
        
        # Partial extraction
        "PartialExtractionHandler", "PartialExtractionResult", "ExtractionStrategy",
        "create_extraction_handler", "create_lenient_extraction_handler", "create_strict_extraction_handler",
        
        # Error reporting
        "ErrorReporter", "ErrorSeverity", "ErrorReport", "ErrorContext", "SystemInfo",
        "ReportFormat", "create_error_reporter", "get_global_error_reporter", "report_error",
    ]

except ImportError as e:
    # Fallback if some modules are not available
    __all__ = []
    import warnings
    warnings.warn(f"Some modules could not be imported: {e}")
