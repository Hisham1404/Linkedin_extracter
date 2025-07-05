"""
LinkedIn Post Extractor - Partial Extraction Handler

This module provides graceful degradation for partial extraction failures,
allowing the system to continue processing when some data cannot be extracted.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ExtractionStrategy(Enum):
    """Strategies for handling partial extraction failures."""
    SKIP_FAILED = "skip_failed"
    RETRY_FAILED = "retry_failed"
    FALLBACK_EXTRACTION = "fallback_extraction"
    PARTIAL_CONTENT = "partial_content"


@dataclass
class PartialExtractionResult:
    """Result of partial extraction operation."""
    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    success_rate: float = 0.0
    quality_score: float = 0.0
    
    # Detailed results
    extracted_data: List[Dict[str, Any]] = field(default_factory=list)
    failed_extractions: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Statistics
    success_count: int = 0
    failure_count: int = 0
    
    def __post_init__(self):
        """Calculate derived statistics."""
        if self.total_items > 0:
            self.success_rate = self.successful_items / self.total_items
            self.quality_score = min(self.success_rate * 1.2, 1.0)  # Boost quality slightly
        
        # Sync counts
        self.success_count = self.successful_items
        self.failure_count = self.failed_items
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_items": self.total_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "success_rate": self.success_rate,
            "quality_score": self.quality_score,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "warnings": self.warnings,
            "extracted_data_count": len(self.extracted_data),
            "failed_extractions_count": len(self.failed_extractions)
        }


class PartialExtractionHandler:
    """
    Handler for graceful degradation during partial extraction failures.
    """
    
    def __init__(self, 
                 strategy: ExtractionStrategy = ExtractionStrategy.SKIP_FAILED,
                 min_success_rate: float = 0.5,
                 quality_threshold: float = 0.7):
        """
        Initialize partial extraction handler.
        
        Args:
            strategy: Strategy for handling failures
            min_success_rate: Minimum acceptable success rate
            quality_threshold: Minimum quality threshold
        """
        self.strategy = strategy
        self.min_success_rate = min_success_rate
        self.quality_threshold = quality_threshold
    
    def handle_partial_extraction(self, 
                                 extraction_results: List[Tuple[bool, Any, Optional[str]]],
                                 context: Optional[Dict[str, Any]] = None) -> PartialExtractionResult:
        """
        Handle partial extraction results.
        
        Args:
            extraction_results: List of (success, data, error_message) tuples
            context: Additional context information
            
        Returns:
            PartialExtractionResult with processed data
        """
        result = PartialExtractionResult()
        result.total_items = len(extraction_results)
        
        successful_data = []
        failed_data = []
        warnings = []
        
        for i, (success, data, error_msg) in enumerate(extraction_results):
            if success:
                result.successful_items += 1
                successful_data.append({
                    "index": i,
                    "data": data,
                    "timestamp": None  # Could add timestamp here
                })
            else:
                result.failed_items += 1
                failed_data.append({
                    "index": i,
                    "error": error_msg or "Unknown error",
                    "partial_data": data if data else None
                })
                
                if error_msg:
                    warnings.append(f"Item {i}: {error_msg}")
        
        # Calculate final statistics
        result.extracted_data = successful_data
        result.failed_extractions = failed_data
        result.warnings = warnings
        
        # Apply strategy
        if self.strategy == ExtractionStrategy.SKIP_FAILED:
            # Keep only successful extractions
            pass
        elif self.strategy == ExtractionStrategy.PARTIAL_CONTENT:
            # Try to include partial data from failed extractions
            for failed_item in failed_data:
                if failed_item.get("partial_data"):
                    result.extracted_data.append({
                        "index": failed_item["index"],
                        "data": failed_item["partial_data"],
                        "partial": True
                    })
                    result.successful_items += 1
                    result.failed_items -= 1
        
        # Recalculate final statistics
        result.__post_init__()
        
        # Check if result meets minimum requirements
        if result.success_rate < self.min_success_rate:
            warnings.append(f"Success rate {result.success_rate:.1%} below threshold {self.min_success_rate:.1%}")
        
        if result.quality_score < self.quality_threshold:
            warnings.append(f"Quality score {result.quality_score:.1%} below threshold {self.quality_threshold:.1%}")
        
        result.warnings = warnings
        
        logger.info(f"Partial extraction completed: {result.successful_items}/{result.total_items} items "
                   f"({result.success_rate:.1%} success rate, {result.quality_score:.1%} quality score)")
        
        return result
    
    def is_acceptable_result(self, result: PartialExtractionResult) -> bool:
        """
        Check if the partial extraction result is acceptable.
        
        Args:
            result: Partial extraction result to check
            
        Returns:
            True if acceptable, False otherwise
        """
        return (result.success_rate >= self.min_success_rate and
                result.quality_score >= self.quality_threshold)
    
    def get_recovery_suggestions(self, result: PartialExtractionResult) -> List[str]:
        """
        Get suggestions for improving extraction results.
        
        Args:
            result: Partial extraction result
            
        Returns:
            List of recovery suggestions
        """
        suggestions = []
        
        if result.success_rate < 0.3:
            suggestions.append("Very low success rate - check if the page structure has changed")
            suggestions.append("Consider updating the extraction selectors")
        elif result.success_rate < 0.6:
            suggestions.append("Moderate success rate - some extraction patterns may need adjustment")
            suggestions.append("Review failed extractions for common patterns")
        
        if result.quality_score < 0.5:
            suggestions.append("Low quality score - extracted data may be incomplete")
            suggestions.append("Consider implementing fallback extraction methods")
        
        if result.failed_items > result.successful_items:
            suggestions.append("More failures than successes - major extraction issue likely")
            suggestions.append("Check network connectivity and page loading")
        
        return suggestions


# Convenience functions
def create_extraction_handler(strategy: ExtractionStrategy = ExtractionStrategy.SKIP_FAILED,
                            min_success_rate: float = 0.5) -> PartialExtractionHandler:
    """
    Create a partial extraction handler with common settings.
    
    Args:
        strategy: Extraction strategy
        min_success_rate: Minimum acceptable success rate
        
    Returns:
        PartialExtractionHandler instance
    """
    return PartialExtractionHandler(
        strategy=strategy,
        min_success_rate=min_success_rate
    )


def create_lenient_extraction_handler() -> PartialExtractionHandler:
    """Create a lenient extraction handler that accepts more failures."""
    return PartialExtractionHandler(
        strategy=ExtractionStrategy.PARTIAL_CONTENT,
        min_success_rate=0.3,
        quality_threshold=0.4
    )


def create_strict_extraction_handler() -> PartialExtractionHandler:
    """Create a strict extraction handler that requires high success rates."""
    return PartialExtractionHandler(
        strategy=ExtractionStrategy.SKIP_FAILED,
        min_success_rate=0.8,
        quality_threshold=0.9
    )


# Export main classes and functions
__all__ = [
    "PartialExtractionHandler",
    "PartialExtractionResult",
    "ExtractionStrategy",
    "create_extraction_handler",
    "create_lenient_extraction_handler",
    "create_strict_extraction_handler"
]
