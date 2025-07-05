#!/usr/bin/env python3
"""
Progress Tracking and User Feedback System

This module provides comprehensive progress tracking for LinkedIn post extraction,
including real-time progress indicators, status updates, time estimates, and
user feedback mechanisms.
"""

import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Callable, Any, Union, Deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import logging
from collections import deque
import statistics

try:
    from tqdm import tqdm
    TqdmType = tqdm
except ImportError:
    tqdm = None
    TqdmType = None

try:
    from .session_recovery import CheckpointType, SessionState
except ImportError:
    # For direct execution
    from session_recovery import CheckpointType, SessionState

logger = logging.getLogger(__name__)


class ProgressPhase(Enum):
    """Progress phases for extraction process."""
    INITIALIZATION = "initialization"
    URL_VALIDATION = "url_validation"
    BROWSER_STARTUP = "browser_startup"
    PAGE_NAVIGATION = "page_navigation"
    CONTENT_LOADING = "content_loading"
    SCROLL_AUTOMATION = "scroll_automation"
    CONTENT_EXTRACTION = "content_extraction"
    DATA_PROCESSING = "data_processing"
    MARKDOWN_GENERATION = "markdown_generation"
    COMPLETION = "completion"


@dataclass
class PhaseTimingMetrics:
    """Timing metrics for individual phases."""
    phase: ProgressPhase
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None
    items_processed: int = 0
    processing_rate: float = 0.0  # items per second
    
    def complete(self) -> None:
        """Mark phase as completed and calculate final metrics."""
        if self.end_time is None:
            self.end_time = datetime.now(timezone.utc)
        
        self.duration = self.end_time - self.start_time
        
        # Ensure minimum duration for rate calculation
        duration_seconds = max(self.duration.total_seconds(), 0.001)
        
        if self.items_processed > 0:
            self.processing_rate = self.items_processed / duration_seconds


@dataclass
class RateCalculator:
    """Advanced rate calculation with moving averages."""
    window_size: int = 10
    measurements: Deque[float] = field(default_factory=lambda: deque(maxlen=10))
    timestamps: Deque[datetime] = field(default_factory=lambda: deque(maxlen=10))
    
    def __post_init__(self):
        """Initialize deques with correct maxlen."""
        self.measurements = deque(maxlen=self.window_size)
        self.timestamps = deque(maxlen=self.window_size)
    
    def add_measurement(self, value: float, timestamp: Optional[datetime] = None) -> None:
        """Add a measurement for rate calculation."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        self.measurements.append(value)
        self.timestamps.append(timestamp)
    
    def get_current_rate(self) -> float:
        """Calculate current rate (items per second)."""
        if len(self.measurements) < 2:
            return 0.0
        
        # Calculate rate over time window
        time_span = (self.timestamps[-1] - self.timestamps[0]).total_seconds()
        if time_span <= 0:
            return 0.0
        
        value_span = self.measurements[-1] - self.measurements[0]
        return value_span / time_span
    
    def get_average_rate(self) -> float:
        """Calculate average rate using moving window."""
        if len(self.measurements) < 2:
            return 0.0
        
        rates = []
        for i in range(1, len(self.measurements)):
            time_diff = (self.timestamps[i] - self.timestamps[i-1]).total_seconds()
            if time_diff > 0:
                value_diff = self.measurements[i] - self.measurements[i-1]
                rates.append(value_diff / time_diff)
        
        return statistics.mean(rates) if rates else 0.0
    
    def get_smoothed_rate(self, alpha: float = 0.3) -> float:
        """Calculate exponentially smoothed rate."""
        if len(self.measurements) < 2:
            return 0.0
        
        current_rate = self.get_current_rate()
        
        # Initialize smoothed rate on first call
        if not hasattr(self, '_last_smoothed_rate') or self._last_smoothed_rate is None:
            self._last_smoothed_rate = current_rate
        else:
            # Apply exponential smoothing
            self._last_smoothed_rate = alpha * current_rate + (1 - alpha) * self._last_smoothed_rate
        
        return self._last_smoothed_rate


@dataclass
class ProgressStats:
    """Statistics for progress tracking."""
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    current_phase: ProgressPhase = ProgressPhase.INITIALIZATION
    phase_start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Overall progress
    total_phases: int = 10
    completed_phases: int = 0
    overall_percentage: float = 0.0
    
    # Current phase progress
    phase_percentage: float = 0.0
    phase_items_total: Optional[int] = None
    phase_items_completed: int = 0
    
    # Extraction specific
    posts_extracted: int = 0
    posts_estimate: Optional[int] = None
    scroll_position: int = 0
    scroll_target: Optional[int] = None
    
    # Enhanced rate calculations
    extraction_rate: float = 0.0  # posts per minute
    extraction_rate_per_second: float = 0.0  # posts per second
    current_phase_rate: float = 0.0  # current phase processing rate
    average_phase_rate: float = 0.0  # average across all phases
    smoothed_extraction_rate: float = 0.0  # exponentially smoothed rate
    
    # Performance metrics
    bytes_processed: int = 0
    network_requests: int = 0
    
    # Enhanced time estimates
    elapsed_time: timedelta = field(default_factory=lambda: timedelta())
    estimated_remaining: Optional[timedelta] = None
    estimated_completion: Optional[datetime] = None
    estimated_remaining_conservative: Optional[timedelta] = None  # conservative estimate
    estimated_remaining_optimistic: Optional[timedelta] = None   # optimistic estimate
    
    # Phase-specific timing
    phase_elapsed_time: timedelta = field(default_factory=lambda: timedelta())
    phase_estimated_remaining: Optional[timedelta] = None
    average_phase_duration: Optional[timedelta] = None
    
    # Error tracking
    error_count: int = 0
    warning_count: int = 0
    retry_count: int = 0


@dataclass
class ProgressCallback:
    """Callback configuration for progress updates."""
    callback: Callable[[ProgressStats], None]
    frequency: float = 1.0  # seconds between calls
    last_called: float = field(default_factory=time.time)
    
    def should_call(self) -> bool:
        """Check if callback should be called based on frequency."""
        return (time.time() - self.last_called) >= self.frequency
    
    def call(self, stats: ProgressStats) -> None:
        """Call the callback and update last called time."""
        try:
            self.callback(stats)
            self.last_called = time.time()
        except Exception as e:
            logger.warning(f"Progress callback failed: {e}")


class ProgressTracker:
    """
    Comprehensive progress tracking system for LinkedIn post extraction.
    
    Provides real-time progress indicators, status updates, time estimates,
    and user feedback mechanisms integrated with session recovery.
    Enhanced with advanced rate calculations and timing metrics.
    """
    
    def __init__(self,
                 enable_tqdm: bool = True,
                 enable_logging: bool = True,
                 update_interval: float = 0.5,
                 save_stats: bool = True,
                 stats_file: Optional[str] = None,
                 rate_window_size: int = 10):
        """
        Initialize progress tracker.
        
        Args:
            enable_tqdm: Enable tqdm progress bars
            enable_logging: Enable progress logging
            update_interval: Update interval in seconds
            save_stats: Save progress stats to file
            stats_file: Custom stats file path
            rate_window_size: Window size for rate calculations
        """
        self.enable_tqdm = enable_tqdm and tqdm is not None
        self.enable_logging = enable_logging
        self.update_interval = update_interval
        self.save_stats = save_stats
        self.stats_file = Path(stats_file) if stats_file else Path("logs/progress_stats.json")
        
        # Progress state
        self.stats = ProgressStats()
        self.callbacks: List[ProgressCallback] = []
        self.phase_weights = self._get_phase_weights()
        
        # Enhanced timing and rate tracking
        self.phase_timings: Dict[ProgressPhase, PhaseTimingMetrics] = {}
        self.posts_rate_calculator = RateCalculator(window_size=rate_window_size)
        self.bytes_rate_calculator = RateCalculator(window_size=rate_window_size)
        self.overall_rate_calculator = RateCalculator(window_size=rate_window_size)
        
        # Phase history for better estimates
        self.phase_history: List[PhaseTimingMetrics] = []
        self.last_posts_count = 0
        self.last_bytes_count = 0
        self.last_update_time = datetime.now(timezone.utc)
        
        # Progress bars
        self.overall_pbar: Optional[Any] = None
        self.phase_pbar: Optional[Any] = None
        
        # Threading
        self._update_thread: Optional[threading.Thread] = None
        self._stop_updates = threading.Event()
        self._stats_lock = threading.Lock()
        
        # Session integration
        self.session_id: Optional[str] = None
        self.recovery_mode: bool = False
        
        logger.info("Progress tracker initialized with enhanced rate calculations")
    
    def _get_phase_weights(self) -> Dict[ProgressPhase, float]:
        """Get relative weights for each phase (sums to 100%)."""
        return {
            ProgressPhase.INITIALIZATION: 2.0,
            ProgressPhase.URL_VALIDATION: 3.0,
            ProgressPhase.BROWSER_STARTUP: 8.0,
            ProgressPhase.PAGE_NAVIGATION: 10.0,
            ProgressPhase.CONTENT_LOADING: 5.0,
            ProgressPhase.SCROLL_AUTOMATION: 40.0,
            ProgressPhase.CONTENT_EXTRACTION: 20.0,
            ProgressPhase.DATA_PROCESSING: 7.0,
            ProgressPhase.MARKDOWN_GENERATION: 4.0,
            ProgressPhase.COMPLETION: 1.0
        }
    
    def start_tracking(self, session_id: Optional[str] = None, recovery_mode: bool = False) -> None:
        """
        Start progress tracking.
        
        Args:
            session_id: Session ID for integration with recovery system
            recovery_mode: Whether this is a recovery session
        """
        with self._stats_lock:
            self.session_id = session_id
            self.recovery_mode = recovery_mode
            
            if not recovery_mode:
                self.stats = ProgressStats()
            
            if self.enable_tqdm and tqdm:
                self.overall_pbar = tqdm(
                    total=100,
                    desc="Overall Progress",
                    unit="%",
                    position=0,
                    leave=True
                )
                
                self.phase_pbar = tqdm(
                    total=100,
                    desc=f"Phase: {self.stats.current_phase.value}",
                    unit="%",
                    position=1,
                    leave=False
                )
        
        # Start update thread
        if not self._update_thread or not self._update_thread.is_alive():
            self._stop_updates.clear()
            self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()
        
        if self.enable_logging:
            logger.info(f"Progress tracking started (session: {session_id}, recovery: {recovery_mode})")
    
    def stop_tracking(self) -> None:
        """Stop progress tracking and cleanup resources."""
        self._stop_updates.set()
        
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=2.0)
        
        if self.overall_pbar:
            self.overall_pbar.close()
            self.overall_pbar = None
        
        if self.phase_pbar:
            self.phase_pbar.close()
            self.phase_pbar = None
        
        if self.save_stats:
            self._save_stats()
        
        if self.enable_logging:
            logger.info("Progress tracking stopped")
    
    def start_phase(self, phase: ProgressPhase, 
                   total_items: Optional[int] = None,
                   description: Optional[str] = None) -> None:
        """
        Start a new progress phase.
        
        Args:
            phase: The phase to start
            total_items: Total items in this phase (for phase progress)
            description: Custom description for the phase
        """
        with self._stats_lock:
            # Complete previous phase timing
            if self.stats.current_phase != phase:
                self._complete_current_phase()
                
                # Complete previous phase timing (but don't duplicate in history)
                if self.stats.current_phase in self.phase_timings:
                    prev_timing = self.phase_timings[self.stats.current_phase]
                    prev_timing.items_processed = self.stats.phase_items_completed
                    if prev_timing.end_time is None:  # Only complete if not already completed
                        prev_timing.complete()
            
            # Start new phase
            self.stats.current_phase = phase
            self.stats.phase_start_time = datetime.now(timezone.utc)
            self.stats.phase_percentage = 0.0
            self.stats.phase_items_total = total_items
            self.stats.phase_items_completed = 0
            
            # Initialize phase timing
            self.phase_timings[phase] = PhaseTimingMetrics(
                phase=phase,
                start_time=self.stats.phase_start_time
            )
            
            # Update overall progress and rates
            self._update_overall_progress()
            self._update_advanced_rates()
            
            # Update progress bars
            if self.phase_pbar:
                desc = description or f"Phase: {phase.value.replace('_', ' ').title()}"
                self.phase_pbar.set_description(desc)
                self.phase_pbar.reset()
        
        if self.enable_logging:
            logger.info(f"Started phase: {phase.value} (items: {total_items})")
    
    def update_phase_progress(self, 
                            items_completed: Optional[int] = None,
                            percentage: Optional[float] = None,
                            increment: int = 1) -> None:
        """
        Update progress within the current phase.
        
        Args:
            items_completed: Total items completed in this phase
            percentage: Direct percentage (0-100)
            increment: Number of items to increment by
        """
        with self._stats_lock:
            if items_completed is not None:
                self.stats.phase_items_completed = items_completed
            elif increment > 0:
                self.stats.phase_items_completed += increment
            
            if percentage is not None:
                self.stats.phase_percentage = max(0, min(100, percentage))
            elif self.stats.phase_items_total and self.stats.phase_items_total > 0:
                self.stats.phase_percentage = (
                    self.stats.phase_items_completed / self.stats.phase_items_total * 100
                )
            
            # Update overall progress
            self._update_overall_progress()
    
    def update_extraction_stats(self,
                              posts_extracted: Optional[int] = None,
                              posts_estimate: Optional[int] = None,
                              scroll_position: Optional[int] = None,
                              scroll_target: Optional[int] = None,
                              bytes_processed: Optional[int] = None) -> None:
        """
        Update extraction-specific statistics.
        
        Args:
            posts_extracted: Total posts extracted
            posts_estimate: Estimated total posts
            scroll_position: Current scroll position
            scroll_target: Target scroll position
            bytes_processed: Bytes of data processed
        """
        with self._stats_lock:
            current_time = datetime.now(timezone.utc)
            
            # Update basic stats
            if posts_extracted is not None:
                self.stats.posts_extracted = posts_extracted
            if posts_estimate is not None:
                self.stats.posts_estimate = posts_estimate
            if scroll_position is not None:
                self.stats.scroll_position = scroll_position
            if scroll_target is not None:
                self.stats.scroll_target = scroll_target
            if bytes_processed is not None:
                self.stats.bytes_processed = bytes_processed
            
            # Update rate calculators
            self.posts_rate_calculator.add_measurement(self.stats.posts_extracted, current_time)
            self.bytes_rate_calculator.add_measurement(self.stats.bytes_processed, current_time)
            self.overall_rate_calculator.add_measurement(self.stats.overall_percentage, current_time)
            
            # Update phase timing
            if self.stats.current_phase in self.phase_timings:
                timing = self.phase_timings[self.stats.current_phase]
                timing.items_processed = self.stats.phase_items_completed
            
            # Update all rate calculations
            self._update_advanced_rates()
            
            # Update time estimates
            self._update_enhanced_time_estimates()
            
            # Update timing for current phase
            self._update_phase_timing()
    
    def increment_error_count(self, error_type: str = "error") -> None:
        """
        Increment error counters.
        
        Args:
            error_type: Type of error ("error", "warning", "retry")
        """
        with self._stats_lock:
            if error_type == "error":
                self.stats.error_count += 1
            elif error_type == "warning":
                self.stats.warning_count += 1
            elif error_type == "retry":
                self.stats.retry_count += 1
    
    def complete_phase(self, phase: Optional[ProgressPhase] = None) -> None:
        """
        Mark a phase as completed.
        
        Args:
            phase: Phase to complete (current phase if None)
        """
        with self._stats_lock:
            if phase and phase != self.stats.current_phase:
                logger.warning(f"Completing phase {phase.value} but current phase is {self.stats.current_phase.value}")
            
            self.stats.phase_percentage = 100.0
            if self.stats.phase_items_total:
                self.stats.phase_items_completed = self.stats.phase_items_total
            
            # Complete the current phase timing
            if self.stats.current_phase in self.phase_timings:
                timing = self.phase_timings[self.stats.current_phase]
                timing.items_processed = self.stats.phase_items_completed
                timing.complete()
                # Add to history
                self.phase_history.append(timing)
            
            self._complete_current_phase()
            self._update_overall_progress()
    
    def add_callback(self, 
                    callback: Callable[[ProgressStats], None],
                    frequency: float = 1.0) -> None:
        """
        Add a progress callback.
        
        Args:
            callback: Function to call with progress stats
            frequency: Minimum seconds between calls
        """
        self.callbacks.append(ProgressCallback(callback, frequency))
        logger.debug(f"Added progress callback with frequency {frequency}s")
    
    def get_stats(self) -> ProgressStats:
        """Get current progress statistics."""
        with self._stats_lock:
            # Update elapsed time
            self.stats.elapsed_time = self._get_elapsed_time()
            
            # Update phase timing
            if self.stats.current_phase in self.phase_timings:
                timing = self.phase_timings[self.stats.current_phase]
                current_time = datetime.now(timezone.utc)
                self.stats.phase_elapsed_time = current_time - timing.start_time
            
            return self.stats
    
    def get_summary_report(self) -> Dict[str, Any]:
        """Get a comprehensive progress summary report."""
        stats = self.get_stats()
        
        return {
            "session_info": {
                "session_id": self.session_id,
                "recovery_mode": self.recovery_mode,
                "start_time": stats.start_time.isoformat(),
                "elapsed_time": str(stats.elapsed_time),
                "estimated_completion": stats.estimated_completion.isoformat() if stats.estimated_completion else None
            },
            "progress": {
                "overall_percentage": stats.overall_percentage,
                "current_phase": stats.current_phase.value,
                "phase_percentage": stats.phase_percentage,
                "completed_phases": stats.completed_phases,
                "total_phases": stats.total_phases
            },
            "extraction": {
                "posts_extracted": stats.posts_extracted,
                "posts_estimate": stats.posts_estimate,
                "extraction_rate": round(stats.extraction_rate, 2),
                "extraction_rate_per_second": round(stats.extraction_rate_per_second, 3),
                "smoothed_extraction_rate": round(stats.smoothed_extraction_rate, 2),
                "scroll_position": stats.scroll_position,
                "scroll_target": stats.scroll_target
            },
            "performance": {
                "bytes_processed": stats.bytes_processed,
                "network_requests": stats.network_requests,
                "error_count": stats.error_count,
                "warning_count": stats.warning_count,
                "retry_count": stats.retry_count
            },
            "time_estimates": {
                "estimated_remaining": str(stats.estimated_remaining) if stats.estimated_remaining else None,
                "estimated_completion": stats.estimated_completion.isoformat() if stats.estimated_completion else None,
                "conservative_remaining": str(stats.estimated_remaining_conservative) if stats.estimated_remaining_conservative else None,
                "optimistic_remaining": str(stats.estimated_remaining_optimistic) if stats.estimated_remaining_optimistic else None
            },
            "phase_metrics": {
                "current_phase_rate": round(stats.current_phase_rate, 3),
                "average_phase_rate": round(stats.average_phase_rate, 3),
                "phase_elapsed_time": str(stats.phase_elapsed_time),
                "phase_estimated_remaining": str(stats.phase_estimated_remaining) if stats.phase_estimated_remaining else None,
                "average_phase_duration": str(stats.average_phase_duration) if stats.average_phase_duration else None
            },
            "rate_summary": self.get_rate_summary(),
            "timing_summary": self.get_timing_summary()
        }
    
    def _complete_current_phase(self) -> None:
        """Mark current phase as completed and increment counter."""
        phase_index = list(ProgressPhase).index(self.stats.current_phase)
        if phase_index >= self.stats.completed_phases:
            self.stats.completed_phases = phase_index + 1
    
    def _update_overall_progress(self) -> None:
        """Update overall progress percentage based on phase weights."""
        total_progress = 0.0
        
        # Add completed phases
        for i, phase in enumerate(ProgressPhase):
            if i < self.stats.completed_phases:
                total_progress += self.phase_weights[phase]
        
        # Add current phase progress
        if self.stats.completed_phases < len(ProgressPhase):
            current_phase_list = list(ProgressPhase)
            if self.stats.completed_phases < len(current_phase_list):
                current_phase = current_phase_list[self.stats.completed_phases]
                phase_weight = self.phase_weights[current_phase]
                total_progress += (self.stats.phase_percentage / 100.0) * phase_weight
        
        self.stats.overall_percentage = min(100.0, total_progress)
    
    def _update_time_estimates(self) -> None:
        """Update time estimates based on current progress."""
        if self.stats.overall_percentage > 0:
            elapsed = self._get_elapsed_time()
            if elapsed.total_seconds() > 0:
                rate = self.stats.overall_percentage / elapsed.total_seconds()
                remaining_percentage = 100.0 - self.stats.overall_percentage
                
                if rate > 0:
                    remaining_seconds = remaining_percentage / rate
                    self.stats.estimated_remaining = timedelta(seconds=remaining_seconds)
                    self.stats.estimated_completion = datetime.now(timezone.utc) + self.stats.estimated_remaining
    
    def _update_advanced_rates(self) -> None:
        """Update advanced rate calculations using moving averages."""
        current_time = datetime.now(timezone.utc)
        
        # Calculate extraction rates
        self.stats.extraction_rate_per_second = self.posts_rate_calculator.get_average_rate()
        self.stats.extraction_rate = self.stats.extraction_rate_per_second * 60  # per minute
        self.stats.smoothed_extraction_rate = self.posts_rate_calculator.get_smoothed_rate() * 60
        
        # Calculate current phase rate
        if self.stats.current_phase in self.phase_timings:
            timing = self.phase_timings[self.stats.current_phase]
            phase_elapsed = (current_time - timing.start_time).total_seconds()
            if phase_elapsed > 0 and timing.items_processed > 0:
                self.stats.current_phase_rate = timing.items_processed / phase_elapsed
        
        # Calculate average phase rate from history
        if self.phase_history:
            total_rate = sum(timing.processing_rate for timing in self.phase_history if timing.processing_rate > 0)
            count = len([timing for timing in self.phase_history if timing.processing_rate > 0])
            self.stats.average_phase_rate = total_rate / count if count > 0 else 0.0
    
    def _update_enhanced_time_estimates(self) -> None:
        """Update enhanced time estimates with conservative and optimistic scenarios."""
        if self.stats.overall_percentage > 0:
            elapsed = self._get_elapsed_time()
            if elapsed.total_seconds() > 0:
                # Basic estimate using overall progress
                basic_rate = self.stats.overall_percentage / elapsed.total_seconds()
                remaining_percentage = 100.0 - self.stats.overall_percentage
                
                if basic_rate > 0:
                    basic_remaining = remaining_percentage / basic_rate
                    self.stats.estimated_remaining = timedelta(seconds=basic_remaining)
                    self.stats.estimated_completion = datetime.now(timezone.utc) + self.stats.estimated_remaining
                
                # Enhanced estimates using smoothed rates
                if self.stats.smoothed_extraction_rate > 0 and self.stats.posts_estimate:
                    remaining_posts = self.stats.posts_estimate - self.stats.posts_extracted
                    if remaining_posts > 0:
                        # Optimistic estimate (using current smoothed rate)
                        optimistic_minutes = remaining_posts / self.stats.smoothed_extraction_rate
                        self.stats.estimated_remaining_optimistic = timedelta(minutes=optimistic_minutes)
                        
                        # Conservative estimate (using 75% of current rate)
                        conservative_minutes = remaining_posts / (self.stats.smoothed_extraction_rate * 0.75)
                        self.stats.estimated_remaining_conservative = timedelta(minutes=conservative_minutes)
                
                # Phase-based estimates
                self._update_phase_based_estimates()
    
    def _update_phase_based_estimates(self) -> None:
        """Update estimates based on phase-specific historical data."""
        if not self.phase_history:
            return
        
        # Calculate average phase duration
        phase_durations = [timing.duration for timing in self.phase_history if timing.duration]
        if phase_durations:
            avg_duration = sum(phase_durations, timedelta()) / len(phase_durations)
            self.stats.average_phase_duration = avg_duration
        
        # Estimate remaining time based on remaining phases
        remaining_phases = len(ProgressPhase) - self.stats.completed_phases - 1  # -1 for current phase
        if remaining_phases > 0 and self.stats.average_phase_duration:
            phase_estimate = self.stats.average_phase_duration * remaining_phases
            
            # Add current phase estimate
            current_phase_progress = self.stats.phase_percentage / 100.0
            if current_phase_progress > 0 and self.stats.current_phase in self.phase_timings:
                current_timing = self.phase_timings[self.stats.current_phase]
                current_elapsed = datetime.now(timezone.utc) - current_timing.start_time
                if current_phase_progress > 0:
                    estimated_current_total = current_elapsed / current_phase_progress
                    current_phase_remaining = estimated_current_total - current_elapsed
                    phase_estimate += current_phase_remaining
            
            self.stats.phase_estimated_remaining = phase_estimate
    
    def _update_phase_timing(self) -> None:
        """Update timing statistics for the current phase."""
        if self.stats.current_phase not in self.phase_timings:
            return
        
        timing = self.phase_timings[self.stats.current_phase]
        current_time = datetime.now(timezone.utc)
        
        # Update phase elapsed time
        self.stats.phase_elapsed_time = current_time - timing.start_time
        
        # Update phase items processed
        timing.items_processed = self.stats.phase_items_completed
        
        # Calculate phase processing rate
        if self.stats.phase_elapsed_time.total_seconds() > 0 and timing.items_processed > 0:
            timing.processing_rate = timing.items_processed / self.stats.phase_elapsed_time.total_seconds()
    
    def get_rate_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all rate calculations."""
        return {
            "extraction_rates": {
                "per_second": round(self.stats.extraction_rate_per_second, 3),
                "per_minute": round(self.stats.extraction_rate, 2),
                "smoothed_per_minute": round(self.stats.smoothed_extraction_rate, 2)
            },
            "phase_rates": {
                "current_phase": round(self.stats.current_phase_rate, 3),
                "average_across_phases": round(self.stats.average_phase_rate, 3)
            },
            "rate_calculators": {
                "posts_measurements": len(self.posts_rate_calculator.measurements),
                "bytes_measurements": len(self.bytes_rate_calculator.measurements),
                "overall_measurements": len(self.overall_rate_calculator.measurements)
            }
        }
    
    def get_timing_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of timing metrics."""
        return {
            "overall_timing": {
                "elapsed": str(self.stats.elapsed_time),
                "estimated_remaining": str(self.stats.estimated_remaining) if self.stats.estimated_remaining else None,
                "estimated_completion": self.stats.estimated_completion.isoformat() if self.stats.estimated_completion else None
            },
            "enhanced_estimates": {
                "conservative_remaining": str(self.stats.estimated_remaining_conservative) if self.stats.estimated_remaining_conservative else None,
                "optimistic_remaining": str(self.stats.estimated_remaining_optimistic) if self.stats.estimated_remaining_optimistic else None
            },
            "phase_timing": {
                "current_phase_elapsed": str(self.stats.phase_elapsed_time),
                "phase_estimated_remaining": str(self.stats.phase_estimated_remaining) if self.stats.phase_estimated_remaining else None,
                "average_phase_duration": str(self.stats.average_phase_duration) if self.stats.average_phase_duration else None
            },
            "phase_history": [
                {
                    "phase": timing.phase.value,
                    "duration": str(timing.duration) if timing.duration else None,
                    "items_processed": timing.items_processed,
                    "processing_rate": round(timing.processing_rate, 3)
                }
                for timing in self.phase_history
            ]
        }
    
    def _get_elapsed_time(self) -> timedelta:
        """Get elapsed time since tracking started."""
        return datetime.now(timezone.utc) - self.stats.start_time
    
    def _update_loop(self) -> None:
        """Background update loop for progress indicators and callbacks."""
        while not self._stop_updates.wait(self.update_interval):
            try:
                current_stats = self.get_stats()
                
                # Update progress bars
                if self.overall_pbar:
                    self.overall_pbar.n = int(current_stats.overall_percentage)
                    self.overall_pbar.refresh()
                
                if self.phase_pbar:
                    self.phase_pbar.n = int(current_stats.phase_percentage)
                    self.phase_pbar.refresh()
                
                # Call callbacks
                for callback in self.callbacks:
                    if callback.should_call():
                        callback.call(current_stats)
                
            except Exception as e:
                logger.error(f"Error in progress update loop: {e}")
    
    def _save_stats(self) -> None:
        """Save progress statistics to file."""
        try:
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.get_summary_report(), f, indent=2, default=str)
                
            logger.debug(f"Progress stats saved to {self.stats_file}")
        except Exception as e:
            logger.error(f"Failed to save progress stats: {e}")


# Convenience functions
def create_progress_tracker(enable_tqdm: bool = True,
                          enable_logging: bool = True,
                          update_interval: float = 0.5) -> ProgressTracker:
    """
    Create a progress tracker with default settings.
    
    Args:
        enable_tqdm: Enable tqdm progress bars
        enable_logging: Enable progress logging
        update_interval: Update interval in seconds
    
    Returns:
        Configured ProgressTracker instance
    """
    return ProgressTracker(
        enable_tqdm=enable_tqdm,
        enable_logging=enable_logging,
        update_interval=update_interval
    )


def create_console_callback() -> Callable[[ProgressStats], None]:
    """
    Create a console output callback for progress updates.
    
    Returns:
        Console callback function
    """
    def console_callback(stats: ProgressStats) -> None:
        """Console progress callback with enhanced metrics."""
        elapsed = stats.elapsed_time
        remaining = stats.estimated_remaining
        
        print(f"\n=== Progress Update ===")
        print(f"Overall: {stats.overall_percentage:.1f}%")
        print(f"Phase: {stats.current_phase.value} ({stats.phase_percentage:.1f}%)")
        print(f"Posts: {stats.posts_extracted}")
        if stats.posts_estimate:
            print(f"Estimated total: {stats.posts_estimate}")
        print(f"Elapsed: {elapsed}")
        
        # Enhanced time estimates
        if remaining:
            print(f"Remaining: {remaining}")
        if stats.estimated_remaining_conservative:
            print(f"Conservative: {stats.estimated_remaining_conservative}")
        if stats.estimated_remaining_optimistic:
            print(f"Optimistic: {stats.estimated_remaining_optimistic}")
        
        # Enhanced rate information
        print(f"Rate: {stats.extraction_rate:.1f} posts/min")
        if stats.smoothed_extraction_rate > 0:
            print(f"Smoothed rate: {stats.smoothed_extraction_rate:.1f} posts/min")
        if stats.current_phase_rate > 0:
            print(f"Current phase rate: {stats.current_phase_rate:.2f} items/sec")
        
        # Phase timing
        if stats.phase_elapsed_time.total_seconds() > 0:
            print(f"Phase elapsed: {stats.phase_elapsed_time}")
        if stats.average_phase_duration:
            print(f"Avg phase duration: {stats.average_phase_duration}")
        
        # Error information
        if stats.error_count > 0:
            print(f"Errors: {stats.error_count}")
        if stats.warning_count > 0:
            print(f"Warnings: {stats.warning_count}")
        if stats.retry_count > 0:
            print(f"Retries: {stats.retry_count}")
        
        print("=" * 23)
    
    return console_callback


# Export main classes and functions
__all__ = [
    "ProgressPhase",
    "ProgressStats", 
    "ProgressCallback",
    "ProgressTracker",
    "PhaseTimingMetrics",
    "RateCalculator",
    "create_progress_tracker",
    "create_console_callback"
]
