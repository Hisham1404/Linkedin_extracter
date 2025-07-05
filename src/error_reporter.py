"""
LinkedIn Post Extractor - Error Reporting System

This module provides comprehensive error reporting capabilities including:
- Structured error logging with JSON format
- User-friendly error messages with actionable guidance
- Error categorization and severity levels
- Diagnostic information collection
- Error analytics and trending
- Integration with monitoring systems
"""

import logging
import json
import traceback
import sys
import os
import platform
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import uuid

try:
    from .exceptions import (
        LinkedInExtractorError, NetworkError, AuthenticationError,
        ExtractionError, ValidationError, BrowserError, ScrollError,
        RateLimitError, ConfigurationError, get_error_category,
        is_recoverable_error
    )
    from .retry_handler import RetryStats
    from .partial_extraction_handler import PartialExtractionResult
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from exceptions import (
        LinkedInExtractorError, NetworkError, AuthenticationError,
        ExtractionError, ValidationError, BrowserError, ScrollError,
        RateLimitError, ConfigurationError, get_error_category,
        is_recoverable_error
    )
    from retry_handler import RetryStats
    from partial_extraction_handler import PartialExtractionResult

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"    # System failure, cannot continue
    HIGH = "high"           # Major functionality affected
    MEDIUM = "medium"       # Some functionality affected
    LOW = "low"            # Minor issues, degraded performance
    INFO = "info"          # Informational, no impact


class ReportFormat(Enum):
    """Error report output formats."""
    JSON = "json"
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"


@dataclass
class SystemInfo:
    """System information for diagnostic purposes."""
    python_version: str = field(default_factory=lambda: sys.version)
    platform: str = field(default_factory=platform.platform)
    architecture: str = field(default_factory=lambda: platform.architecture()[0])
    processor: str = field(default_factory=lambda: platform.processor() or "unknown")
    memory_mb: Optional[int] = None
    disk_space_mb: Optional[int] = None
    
    def __post_init__(self):
        """Collect additional system information."""
        try:
            import psutil
            self.memory_mb = int(psutil.virtual_memory().total / (1024 * 1024))
            self.disk_space_mb = int(psutil.disk_usage('/').total / (1024 * 1024))
        except ImportError:
            # psutil not available, use basic info
            pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert SystemInfo to dictionary."""
        return {
            "python_version": self.python_version,
            "platform": self.platform,
            "architecture": self.architecture,
            "processor": self.processor,
            "memory_mb": self.memory_mb,
            "disk_space_mb": self.disk_space_mb
        }


@dataclass 
class ErrorContext:
    """Contextual information about the error."""
    module_name: str
    function_name: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    user_action: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    environment_vars: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ErrorReport:
    """Comprehensive error report structure."""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    error_type: str = ""
    error_message: str = ""
    error_category: Optional[str] = None
    
    # Technical details
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[ErrorContext] = None
    system_info: Optional[SystemInfo] = None
    
    # User-facing information
    user_message: str = ""
    suggested_actions: List[str] = field(default_factory=list)
    documentation_links: List[str] = field(default_factory=list)
    
    # Diagnostic information
    retry_info: Optional[Dict[str, Any]] = None
    partial_extraction_info: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    
    # Classification
    is_recoverable: bool = True
    is_user_error: bool = False
    requires_immediate_attention: bool = False
    
    def __post_init__(self):
        """Post-process the error report."""
        if not self.error_id:
            self.error_id = str(uuid.uuid4())
        
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, Enum):
                    result[key] = value.value
                elif hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()
                else:
                    result[key] = value
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class ErrorReporter:
    """
    Comprehensive error reporting system.
    
    Provides structured error logging, user-friendly messages,
    diagnostic information collection, and actionable guidance.
    """
    
    def __init__(self, 
                 log_file: Optional[str] = None,
                 include_system_info: bool = True,
                 collect_performance_metrics: bool = True):
        """
        Initialize the error reporter.
        
        Args:
            log_file: Path to error log file
            include_system_info: Whether to collect system information
            collect_performance_metrics: Whether to collect performance metrics
        """
        self.log_file = log_file
        self.include_system_info = include_system_info
        self.collect_performance_metrics = collect_performance_metrics
        
        # Error tracking
        self.error_history: List[ErrorReport] = []
        self.error_counts: Dict[str, int] = {}
        self.session_id = str(uuid.uuid4())
        
        # System information (collected once)
        self.system_info = SystemInfo() if include_system_info else None
        
        # Setup structured logging
        self._setup_structured_logging()
        
        # Error message templates
        self._initialize_error_templates()
    
    def _setup_structured_logging(self):
        """Setup structured JSON logging for errors."""
        if self.log_file:
            # Create error log directory if it doesn't exist
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Setup JSON formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Create file handler for structured logs
            handler = logging.FileHandler(self.log_file)
            handler.setFormatter(formatter)
            
            # Create error logger
            self.error_logger = logging.getLogger('linkedin_extractor.errors')
            self.error_logger.addHandler(handler)
            self.error_logger.setLevel(logging.ERROR)
    
    def _initialize_error_templates(self):
        """Initialize user-friendly error message templates."""
        self.error_templates = {
            NetworkError.__name__: {
                "message": "Network connection issue encountered",
                "actions": [
                    "Check your internet connection",
                    "Verify the LinkedIn URL is accessible",
                    "Try again in a few moments",
                    "Check if LinkedIn is experiencing outages"
                ],
                "docs": ["https://github.com/linkedin-extractor/docs/network-issues"]
            },
            
            BrowserError.__name__: {
                "message": "Web browser automation issue",
                "actions": [
                    "Ensure Chrome browser is installed and up-to-date",
                    "Check if Chrome is blocked by antivirus software",
                    "Try running with --verbose flag for more details",
                    "Restart the application"
                ],
                "docs": ["https://github.com/linkedin-extractor/docs/browser-setup"]
            },
            
            AuthenticationError.__name__: {
                "message": "LinkedIn authentication or access issue",
                "actions": [
                    "Verify the LinkedIn profile URL is correct",
                    "Check if the profile is public or requires login",
                    "Try accessing the profile in a web browser",
                    "Consider using a different LinkedIn URL format"
                ],
                "docs": ["https://github.com/linkedin-extractor/docs/authentication"]
            },
            
            ExtractionError.__name__: {
                "message": "Content extraction issue",
                "actions": [
                    "Try the extraction again",
                    "Check if LinkedIn has changed their page structure",
                    "Enable verbose logging to see detailed error information",
                    "Report the issue if it persists"
                ],
                "docs": ["https://github.com/linkedin-extractor/docs/extraction-issues"]
            },
            
            ValidationError.__name__: {
                "message": "Input validation error",
                "actions": [
                    "Check the LinkedIn URL format",
                    "Ensure the profile URL is complete and valid",
                    "Try using the full LinkedIn profile URL",
                    "Remove any extra parameters from the URL"
                ],
                "docs": ["https://github.com/linkedin-extractor/docs/url-validation"]
            },
            
            RateLimitError.__name__: {
                "message": "Rate limit exceeded",
                "actions": [
                    "Wait a few minutes before trying again",
                    "Reduce the frequency of requests",
                    "Consider using longer delays between operations",
                    "Try again during off-peak hours"
                ],
                "docs": ["https://github.com/linkedin-extractor/docs/rate-limiting"]
            },
            
            ConfigurationError.__name__: {
                "message": "Configuration issue",
                "actions": [
                    "Check the application configuration",
                    "Verify all required dependencies are installed",
                    "Review the command-line arguments",
                    "Check file permissions for output directory"
                ],
                "docs": ["https://github.com/linkedin-extractor/docs/configuration"]
            }
        }
    
    def create_error_context(self, 
                           module_name: str,
                           function_name: str,
                           user_action: Optional[str] = None,
                           input_data: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """
        Create error context information.
        
        Args:
            module_name: Name of the module where error occurred
            function_name: Name of the function where error occurred
            user_action: Description of user action that triggered the error
            input_data: Sanitized input data (remove sensitive information)
            
        Returns:
            ErrorContext object
        """
        # Get caller information from stack trace
        frame = sys._getframe(1)
        
        # Sanitize input data (remove sensitive information)
        sanitized_input = {}
        if input_data:
            for key, value in input_data.items():
                if any(sensitive in key.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                    sanitized_input[key] = "[REDACTED]"
                elif isinstance(value, str) and len(value) > 200:
                    sanitized_input[key] = value[:200] + "..."
                else:
                    sanitized_input[key] = value
        
        return ErrorContext(
            module_name=module_name,
            function_name=function_name,
            line_number=frame.f_lineno,
            file_path=frame.f_code.co_filename,
            user_action=user_action,
            input_data=sanitized_input if sanitized_input else None
        )
    
    def report_error(self,
                    exception: Exception,
                    context: Optional[ErrorContext] = None,
                    severity: Optional[ErrorSeverity] = None,
                    retry_info: Optional[RetryStats] = None,
                    partial_extraction_info: Optional[PartialExtractionResult] = None,
                    performance_metrics: Optional[Dict[str, Any]] = None) -> ErrorReport:
        """
        Create and log a comprehensive error report.
        
        Args:
            exception: The exception that occurred
            context: Error context information
            severity: Error severity level (auto-detected if None)
            retry_info: Retry statistics if applicable
            partial_extraction_info: Partial extraction results if applicable
            performance_metrics: Performance metrics if available
            
        Returns:
            ErrorReport object
        """
        # Determine error severity if not provided
        if severity is None:
            severity = self._determine_severity(exception)
        
        # Get error category
        error_category = get_error_category(exception)
        
        # Get error template
        template = self.error_templates.get(type(exception).__name__, {})
        
        # Create error report
        report = ErrorReport(
            severity=severity,
            error_type=type(exception).__name__,
            error_message=str(exception),
            error_category=error_category.value if error_category else None,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            stack_trace=traceback.format_exc(),
            context=context,
            system_info=self.system_info,
            user_message=template.get("message", "An error occurred"),
            suggested_actions=template.get("actions", []),
            documentation_links=template.get("docs", []),
            is_recoverable=is_recoverable_error(exception),
            is_user_error=self._is_user_error(exception),
            requires_immediate_attention=severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]
        )
        
        # Add retry information if available
        if retry_info:
            report.retry_info = {
                'total_attempts': retry_info.total_attempts,
                'successful_attempts': retry_info.successful_attempts,
                'failed_attempts': retry_info.failed_attempts,
                'average_delay': retry_info.average_delay,
                'total_delay': retry_info.total_delay
            }
        
        # Add partial extraction information if available
        if partial_extraction_info:
            report.partial_extraction_info = partial_extraction_info.to_dict()
        
        # Add performance metrics if available
        if performance_metrics:
            report.performance_metrics = performance_metrics
        
        # Log the error
        self._log_error_report(report)
        
        # Track error for analytics
        self._track_error(report)
        
        return report
    
    def _determine_severity(self, exception: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type."""
        if isinstance(exception, (SystemExit, KeyboardInterrupt)):
            return ErrorSeverity.CRITICAL
        elif isinstance(exception, (BrowserError, ConfigurationError)):
            return ErrorSeverity.HIGH
        elif isinstance(exception, (NetworkError, AuthenticationError, ExtractionError)):
            return ErrorSeverity.MEDIUM
        elif isinstance(exception, (ValidationError, RateLimitError)):
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.MEDIUM
    
    def _is_user_error(self, exception: Exception) -> bool:
        """Determine if the error is likely caused by user input."""
        return isinstance(exception, (ValidationError, ConfigurationError))
    
    def _log_error_report(self, report: ErrorReport):
        """Log the error report using structured logging."""
        # Log to error logger if available
        if hasattr(self, 'error_logger'):
            self.error_logger.error(
                "Error Report",
                extra={
                    'error_report': report.to_dict(),
                    'session_id': self.session_id
                }
            )
        
        # Log to file if specified
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(report.to_json() + '\n')
            except Exception as e:
                logger.warning(f"Failed to write error report to file: {e}")
    
    def _track_error(self, report: ErrorReport):
        """Track error for analytics purposes."""
        # Add to error history
        self.error_history.append(report)
        
        # Update error counts
        error_key = f"{report.error_type}:{report.error_category}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Limit history size to prevent memory issues
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get error summary for the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with error summary statistics
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_errors = [
            error for error in self.error_history 
            if error.timestamp >= cutoff_time
        ]
        
        # Calculate statistics
        total_errors = len(recent_errors)
        
        error_types = {}
        severity_counts = {}
        recoverable_count = 0
        
        for error in recent_errors:
            # Count by error type
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            
            # Count by severity
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
            # Count recoverable errors
            if error.is_recoverable:
                recoverable_count += 1
        
        return {
            'time_period_hours': hours,
            'total_errors': total_errors,
            'error_types': error_types,
            'severity_distribution': severity_counts,
            'recoverable_errors': recoverable_count,
            'recovery_rate': recoverable_count / total_errors if total_errors > 0 else 0,
            'most_common_error': max(error_types.items(), key=lambda x: x[1]) if error_types else None
        }
    
    def generate_report(self, 
                       format: ReportFormat = ReportFormat.TEXT,
                       include_history: bool = True,
                       max_errors: int = 50) -> str:
        """
        Generate a comprehensive error report.
        
        Args:
            format: Output format for the report
            include_history: Whether to include error history
            max_errors: Maximum number of errors to include
            
        Returns:
            Formatted error report string
        """
        if format == ReportFormat.JSON:
            return self._generate_json_report(include_history, max_errors)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown_report(include_history, max_errors)
        elif format == ReportFormat.HTML:
            return self._generate_html_report(include_history, max_errors)
        else:
            return self._generate_text_report(include_history, max_errors)
    
    def _generate_text_report(self, include_history: bool, max_errors: int) -> str:
        """Generate text format error report."""
        lines = []
        lines.append("LinkedIn Post Extractor - Error Report")
        lines.append("=" * 50)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Session ID: {self.session_id}")
        lines.append("")
        
        # Summary
        summary = self.get_error_summary()
        lines.append("Error Summary (Last 24 Hours)")
        lines.append("-" * 30)
        lines.append(f"Total Errors: {summary['total_errors']}")
        lines.append(f"Recovery Rate: {summary['recovery_rate']:.1%}")
        
        if summary['most_common_error']:
            error_type, count = summary['most_common_error']
            lines.append(f"Most Common: {error_type} ({count} times)")
        
        lines.append("")
        
        # Error distribution
        if summary['error_types']:
            lines.append("Error Types:")
            for error_type, count in summary['error_types'].items():
                lines.append(f"  • {error_type}: {count}")
            lines.append("")
        
        # Recent errors
        if include_history and self.error_history:
            lines.append("Recent Errors")
            lines.append("-" * 15)
            
            recent_errors = self.error_history[-max_errors:]
            for error in reversed(recent_errors):
                lines.append(f"[{error.timestamp.strftime('%H:%M:%S')}] {error.severity.value.upper()}: {error.error_type}")
                lines.append(f"  Message: {error.user_message}")
                if error.suggested_actions:
                    lines.append(f"  Actions: {'; '.join(error.suggested_actions[:2])}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_json_report(self, include_history: bool, max_errors: int) -> str:
        """Generate JSON format error report."""
        report_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'session_id': self.session_id,
            'summary': self.get_error_summary(),
            'system_info': self.system_info.to_dict() if self.system_info else None
        }
        
        if include_history:
            recent_errors = self.error_history[-max_errors:]
            report_data['errors'] = [error.to_dict() for error in recent_errors]
        
        return json.dumps(report_data, indent=2, default=str)
    
    def _generate_markdown_report(self, include_history: bool, max_errors: int) -> str:
        """Generate Markdown format error report."""
        lines = []
        lines.append("# LinkedIn Post Extractor - Error Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Session ID:** `{self.session_id}`")
        lines.append("")
        
        # Summary
        summary = self.get_error_summary()
        lines.append("## Error Summary (Last 24 Hours)")
        lines.append("")
        lines.append(f"- **Total Errors:** {summary['total_errors']}")
        lines.append(f"- **Recovery Rate:** {summary['recovery_rate']:.1%}")
        
        if summary['most_common_error']:
            error_type, count = summary['most_common_error']
            lines.append(f"- **Most Common:** {error_type} ({count} times)")
        
        lines.append("")
        
        # Error distribution
        if summary['error_types']:
            lines.append("### Error Types")
            lines.append("")
            for error_type, count in summary['error_types'].items():
                lines.append(f"- **{error_type}:** {count}")
            lines.append("")
        
        # Recent errors
        if include_history and self.error_history:
            lines.append("## Recent Errors")
            lines.append("")
            
            recent_errors = self.error_history[-max_errors:]
            for error in reversed(recent_errors):
                lines.append(f"### {error.error_type} - {error.severity.value.title()}")
                lines.append(f"**Time:** {error.timestamp.strftime('%H:%M:%S')}")
                lines.append(f"**Message:** {error.user_message}")
                
                if error.suggested_actions:
                    lines.append("**Suggested Actions:**")
                    for action in error.suggested_actions:
                        lines.append(f"- {action}")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_html_report(self, include_history: bool, max_errors: int) -> str:
        """Generate HTML format error report."""
        # This is a basic HTML template - could be enhanced with CSS styling
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LinkedIn Post Extractor - Error Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .error {{ border: 1px solid #ddd; margin: 10px 0; padding: 10px; border-radius: 5px; }}
                .critical {{ border-color: #ff0000; }}
                .high {{ border-color: #ff8800; }}
                .medium {{ border-color: #ffaa00; }}
                .low {{ border-color: #ffdd00; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>LinkedIn Post Extractor - Error Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Session ID: {self.session_id}</p>
            </div>
        """
        
        # Add summary
        summary = self.get_error_summary()
        html += f"""
            <div class="summary">
                <h2>Error Summary (Last 24 Hours)</h2>
                <ul>
                    <li>Total Errors: {summary['total_errors']}</li>
                    <li>Recovery Rate: {summary['recovery_rate']:.1%}</li>
        """
        
        if summary['most_common_error']:
            error_type, count = summary['most_common_error']
            html += f"<li>Most Common: {error_type} ({count} times)</li>"
        
        html += "</ul></div>"
        
        # Add recent errors
        if include_history and self.error_history:
            html += "<h2>Recent Errors</h2>"
            
            recent_errors = self.error_history[-max_errors:]
            for error in reversed(recent_errors):
                html += f"""
                <div class="error {error.severity.value}">
                    <h3>{error.error_type} - {error.severity.value.title()}</h3>
                    <p><strong>Time:</strong> {error.timestamp.strftime('%H:%M:%S')}</p>
                    <p><strong>Message:</strong> {error.user_message}</p>
                """
                
                if error.suggested_actions:
                    html += "<p><strong>Suggested Actions:</strong></p><ul>"
                    for action in error.suggested_actions:
                        html += f"<li>{action}</li>"
                    html += "</ul>"
                
                html += "</div>"
        
        html += "</body></html>"
        return html
    
    def clear_history(self):
        """Clear error history and reset counters."""
        self.error_history.clear()
        self.error_counts.clear()
        logger.info("Error history cleared")
    
    def export_errors(self, 
                     file_path: str,
                     format: ReportFormat = ReportFormat.JSON,
                     max_errors: int = 1000):
        """
        Export error reports to file.
        
        Args:
            file_path: Path to export file
            format: Export format
            max_errors: Maximum number of errors to export
        """
        try:
            report_content = self.generate_report(format, True, max_errors)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Error report exported to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export error report: {e}")


# Utility functions
def create_error_reporter(log_file: Optional[str] = None,
                         include_system_info: bool = True) -> ErrorReporter:
    """
    Create a configured error reporter.
    
    Args:
        log_file: Path to error log file
        include_system_info: Whether to collect system information
        
    Returns:
        Configured ErrorReporter instance
    """
    return ErrorReporter(
        log_file=log_file,
        include_system_info=include_system_info
    )


# Global error reporter instance
_global_reporter: Optional[ErrorReporter] = None


def get_global_error_reporter() -> ErrorReporter:
    """Get or create the global error reporter instance."""
    global _global_reporter
    if _global_reporter is None:
        _global_reporter = create_error_reporter()
    return _global_reporter


def report_error(exception: Exception,
                module_name: str,
                function_name: str,
                **kwargs) -> ErrorReport:
    """
    Convenience function to report an error using the global reporter.
    
    Args:
        exception: The exception that occurred
        module_name: Name of the module where error occurred
        function_name: Name of the function where error occurred
        **kwargs: Additional arguments for error reporting
        
    Returns:
        ErrorReport object
    """
    reporter = get_global_error_reporter()
    context = reporter.create_error_context(module_name, function_name)
    return reporter.report_error(exception, context, **kwargs)


# Import required for datetime operations
from datetime import timedelta
