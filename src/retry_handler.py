"""
LinkedIn Post Extractor - Retry Handler

This module provides comprehensive retry logic with exponential backoff,
circuit breaker pattern, and human-like delay mechanisms.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps
import statistics

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    RANDOM = "random"


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class RetryConfig:
    """Configuration for retry operations."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    
    # Circuit breaker settings
    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    
    # Human-like delay
    human_like_delay: bool = True
    human_delay_range: tuple = (0.5, 2.0)
    
    # Specific error handling
    recoverable_exceptions: tuple = (Exception,)
    non_recoverable_exceptions: tuple = (KeyboardInterrupt, SystemExit)
    
    def __post_init__(self):
        """Validate configuration."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")


@dataclass
class RetryStats:
    """Statistics for retry operations."""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    total_delay: float = 0.0
    average_delay: float = 0.0
    final_success: bool = False
    
    def __post_init__(self):
        """Calculate derived statistics."""
        if self.total_attempts > 0:
            self.average_delay = self.total_delay / self.total_attempts
    
    def add_attempt(self, success: bool, delay: float = 0.0):
        """Add an attempt to the statistics."""
        self.total_attempts += 1
        self.total_delay += delay
        
        if success:
            self.successful_attempts += 1
            self.final_success = True
        else:
            self.failed_attempts += 1
            self.final_success = False
        
        # Recalculate average
        self.average_delay = self.total_delay / self.total_attempts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "failed_attempts": self.failed_attempts,
            "total_delay": self.total_delay,
            "average_delay": self.average_delay,
            "final_success": self.final_success
        }


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    
    def reset(self):
        """Reset circuit breaker state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
    
    def record_success(self):
        """Record a successful request."""
        self.total_requests += 1
        self.successful_requests += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.reset()
    
    def record_failure(self):
        """Record a failed request."""
        self.total_requests += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
    
    def should_allow_request(self, config: RetryConfig) -> bool:
        """Check if request should be allowed based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def update_state(self, config: RetryConfig):
        """Update circuit breaker state based on failure count."""
        if self.failure_count >= config.failure_threshold:
            self.state = CircuitState.OPEN


class RetryHandler:
    """
    Comprehensive retry handler with exponential backoff, circuit breaker,
    and human-like delay patterns.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry handler.
        
        Args:
            config: Retry configuration (uses default if None)
        """
        self.config = config or RetryConfig()
        self.circuit_breaker = CircuitBreakerState()
        self.retry_history: List[RetryStats] = []
        
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt number.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        if self.config.backoff_strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.backoff_strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        elif self.config.backoff_strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * attempt
        elif self.config.backoff_strategy == RetryStrategy.RANDOM:
            delay = random.uniform(self.config.base_delay, self.config.max_delay)
        else:
            delay = self.config.base_delay
        
        # Apply maximum delay limit
        delay = min(delay, self.config.max_delay)
        
        # Apply jitter if enabled
        if self.config.jitter:
            jitter_factor = random.uniform(0.5, 1.5)
            delay *= jitter_factor
        
        # Add human-like delay if enabled
        if self.config.human_like_delay:
            human_delay = random.uniform(*self.config.human_delay_range)
            delay += human_delay
        
        return delay
    
    def is_recoverable_error(self, exception: Exception) -> bool:
        """
        Check if an exception is recoverable.
        
        Args:
            exception: Exception to check
            
        Returns:
            True if recoverable, False otherwise
        """
        if isinstance(exception, self.config.non_recoverable_exceptions):
            return False
        
        return isinstance(exception, self.config.recoverable_exceptions)
    
    def retry(self, 
              func: Callable,
              *args,
              **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries failed
        """
        stats = RetryStats()
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            # Check circuit breaker
            if self.config.circuit_breaker_enabled:
                if not self.circuit_breaker.should_allow_request(self.config):
                    logger.warning("Circuit breaker is open, failing fast")
                    raise RuntimeError("Circuit breaker is open")
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Record success
                stats.add_attempt(True)
                if self.config.circuit_breaker_enabled:
                    self.circuit_breaker.record_success()
                
                logger.info(f"Function succeeded on attempt {attempt}")
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if error is recoverable
                if not self.is_recoverable_error(e):
                    logger.error(f"Non-recoverable error on attempt {attempt}: {e}")
                    stats.add_attempt(False)
                    raise e
                
                # Record failure
                if self.config.circuit_breaker_enabled:
                    self.circuit_breaker.record_failure()
                    self.circuit_breaker.update_state(self.config)
                
                logger.warning(f"Attempt {attempt} failed: {e}")
                
                # Calculate delay for next attempt
                if attempt < self.config.max_attempts:
                    delay = self.calculate_delay(attempt)
                    stats.add_attempt(False, delay)
                    
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    stats.add_attempt(False)
        
        # All attempts failed
        self.retry_history.append(stats)
        logger.error(f"All {self.config.max_attempts} attempts failed")
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("All retry attempts failed with no exception captured")
    
    async def retry_async(self,
                         func: Callable,
                         *args,
                         **kwargs) -> Any:
        """
        Execute async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries failed
        """
        stats = RetryStats()
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            # Check circuit breaker
            if self.config.circuit_breaker_enabled:
                if not self.circuit_breaker.should_allow_request(self.config):
                    logger.warning("Circuit breaker is open, failing fast")
                    raise RuntimeError("Circuit breaker is open")
            
            try:
                # Execute async function
                result = await func(*args, **kwargs)
                
                # Record success
                stats.add_attempt(True)
                if self.config.circuit_breaker_enabled:
                    self.circuit_breaker.record_success()
                
                logger.info(f"Async function succeeded on attempt {attempt}")
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if error is recoverable
                if not self.is_recoverable_error(e):
                    logger.error(f"Non-recoverable error on attempt {attempt}: {e}")
                    stats.add_attempt(False)
                    raise e
                
                # Record failure
                if self.config.circuit_breaker_enabled:
                    self.circuit_breaker.record_failure()
                    self.circuit_breaker.update_state(self.config)
                
                logger.warning(f"Async attempt {attempt} failed: {e}")
                
                # Calculate delay for next attempt
                if attempt < self.config.max_attempts:
                    delay = self.calculate_delay(attempt)
                    stats.add_attempt(False, delay)
                    
                    logger.info(f"Async retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    stats.add_attempt(False)
        
        # All attempts failed
        self.retry_history.append(stats)
        logger.error(f"All {self.config.max_attempts} async attempts failed")
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("All async retry attempts failed with no exception captured")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry handler statistics."""
        if not self.retry_history:
            return {"total_operations": 0}
        
        total_ops = len(self.retry_history)
        successful_ops = sum(1 for stats in self.retry_history if stats.final_success)
        total_attempts = sum(stats.total_attempts for stats in self.retry_history)
        total_delay = sum(stats.total_delay for stats in self.retry_history)
        
        return {
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "success_rate": successful_ops / total_ops if total_ops > 0 else 0,
            "total_attempts": total_attempts,
            "average_attempts_per_operation": total_attempts / total_ops if total_ops > 0 else 0,
            "total_delay": total_delay,
            "average_delay_per_operation": total_delay / total_ops if total_ops > 0 else 0,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "circuit_breaker_failure_count": self.circuit_breaker.failure_count
        }
    
    def reset_circuit_breaker(self):
        """Reset the circuit breaker state."""
        self.circuit_breaker.reset()
        logger.info("Circuit breaker reset")
    
    def reset_stats(self):
        """Reset retry statistics."""
        self.retry_history.clear()
        logger.info("Retry statistics reset")


# Decorator for retry functionality
def retry_on_failure(config: Optional[RetryConfig] = None):
    """
    Decorator to add retry functionality to functions.
    
    Args:
        config: Retry configuration (uses default if None)
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = RetryHandler(config)
            return handler.retry(func, *args, **kwargs)
        return wrapper
    return decorator


def retry_on_failure_async(config: Optional[RetryConfig] = None):
    """
    Decorator to add retry functionality to async functions.
    
    Args:
        config: Retry configuration (uses default if None)
        
    Returns:
        Decorated async function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            handler = RetryHandler(config)
            return await handler.retry_async(func, *args, **kwargs)
        return wrapper
    return decorator


# Convenience functions
def create_retry_config(max_attempts: int = 3,
                       base_delay: float = 1.0,
                       max_delay: float = 60.0,
                       strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
                       **kwargs) -> RetryConfig:
    """
    Create a retry configuration with common settings.
    
    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        strategy: Retry strategy
        **kwargs: Additional configuration options
        
    Returns:
        RetryConfig instance
    """
    return RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_strategy=strategy,
        **kwargs
    )


def create_network_retry_config() -> RetryConfig:
    """Create retry configuration optimized for network operations."""
    return RetryConfig(
        max_attempts=5,
        base_delay=2.0,
        max_delay=30.0,
        backoff_strategy=RetryStrategy.EXPONENTIAL,
        exponential_base=2.0,
        jitter=True,
        human_like_delay=True,
        circuit_breaker_enabled=True,
        failure_threshold=3,
        recovery_timeout=60.0
    )


def create_browser_retry_config() -> RetryConfig:
    """Create retry configuration optimized for browser operations."""
    return RetryConfig(
        max_attempts=4,
        base_delay=3.0,
        max_delay=45.0,
        backoff_strategy=RetryStrategy.EXPONENTIAL,
        exponential_base=1.5,
        jitter=True,
        human_like_delay=True,
        human_delay_range=(1.0, 3.0),
        circuit_breaker_enabled=True,
        failure_threshold=5,
        recovery_timeout=120.0
    )


# Export main classes and functions
__all__ = [
    "RetryHandler",
    "RetryConfig", 
    "RetryStats",
    "RetryStrategy",
    "CircuitState",
    "CircuitBreakerState",
    "retry_on_failure",
    "retry_on_failure_async",
    "create_retry_config",
    "create_network_retry_config",
    "create_browser_retry_config"
]
