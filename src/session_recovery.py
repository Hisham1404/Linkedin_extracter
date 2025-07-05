"""
LinkedIn Post Extractor - Session Recovery and Checkpoint System

This module provides session recovery and checkpoint functionality to allow
resuming operations after interruptions or failures.
"""

import json
import logging
import os
import pickle
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import hashlib
import uuid

logger = logging.getLogger(__name__)


class CheckpointType(Enum):
    """Types of checkpoints that can be created."""
    INITIALIZATION = "initialization"
    URL_VALIDATION = "url_validation"
    BROWSER_STARTUP = "browser_startup"
    PAGE_NAVIGATION = "page_navigation"
    SCROLL_PROGRESS = "scroll_progress"
    CONTENT_EXTRACTION = "content_extraction"
    DATA_PROCESSING = "data_processing"
    MARKDOWN_GENERATION = "markdown_generation"
    COMPLETION = "completion"


class SessionState(Enum):
    """States that a session can be in."""
    ACTIVE = "active"
    PAUSED = "paused"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"


@dataclass
class Checkpoint:
    """Individual checkpoint data structure."""
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    checkpoint_type: CheckpointType = CheckpointType.INITIALIZATION
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = ""
    
    # Data
    session_data: Dict[str, Any] = field(default_factory=dict)
    extracted_data: List[Dict[str, Any]] = field(default_factory=list)
    progress_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Context
    url: Optional[str] = None
    scroll_position: int = 0
    posts_extracted: int = 0
    total_posts_estimate: Optional[int] = None
    
    # Technical details
    browser_state: Optional[Dict[str, Any]] = None
    extraction_config: Optional[Dict[str, Any]] = None
    error_count: int = 0
    retry_count: int = 0
    
    def __post_init__(self):
        """Post-process checkpoint data."""
        if not self.checkpoint_id:
            self.checkpoint_id = str(uuid.uuid4())
        
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary for serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat() if self.timestamp else None
        result['checkpoint_type'] = self.checkpoint_type.value if self.checkpoint_type else None
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """Create checkpoint from dictionary (for deserialization)."""
        # Make a copy to avoid modifying the original
        data = data.copy()
        
        # Convert timestamp string back to datetime
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Convert checkpoint_type string back to enum
        if 'checkpoint_type' in data and isinstance(data['checkpoint_type'], str):
            data['checkpoint_type'] = CheckpointType(data['checkpoint_type'])
        
        return cls(**data)
    
    def calculate_hash(self) -> str:
        """Calculate hash of checkpoint data for integrity verification."""
        data_str = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()


@dataclass
class SessionInfo:
    """Session information and metadata."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_checkpoint_time: Optional[datetime] = None
    state: SessionState = SessionState.ACTIVE
    
    # Configuration
    profile_url: str = ""
    output_directory: str = ""
    extraction_config: Dict[str, Any] = field(default_factory=dict)
    
    # Progress tracking
    total_checkpoints: int = 0
    current_checkpoint_type: Optional[CheckpointType] = None
    completion_percentage: float = 0.0
    
    # Recovery information
    recovery_attempts: int = 0
    last_error: Optional[str] = None
    can_resume: bool = True
    
    def __post_init__(self):
        """Post-process session info."""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        
        if not self.start_time:
            self.start_time = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session info to dictionary."""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat() if self.start_time else None
        result['last_checkpoint_time'] = self.last_checkpoint_time.isoformat() if self.last_checkpoint_time else None
        result['state'] = self.state.value if self.state else None
        result['current_checkpoint_type'] = self.current_checkpoint_type.value if self.current_checkpoint_type else None
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionInfo':
        """Create session info from dictionary (for deserialization)."""
        # Make a copy to avoid modifying the original
        data = data.copy()
        
        # Convert datetime strings back to datetime objects
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        
        if 'last_checkpoint_time' in data and isinstance(data['last_checkpoint_time'], str):
            data['last_checkpoint_time'] = datetime.fromisoformat(data['last_checkpoint_time'])
        
        # Convert enum strings back to enums
        if 'state' in data and isinstance(data['state'], str):
            data['state'] = SessionState(data['state'])
        
        if 'current_checkpoint_type' in data and isinstance(data['current_checkpoint_type'], str):
            data['current_checkpoint_type'] = CheckpointType(data['current_checkpoint_type'])
        
        return cls(**data)


class SessionRecoveryManager:
    """
    Manages session recovery and checkpoint operations.
    
    Provides functionality to:
    - Create and save checkpoints during extraction
    - Detect interrupted sessions
    - Resume operations from the last valid checkpoint
    - Manage session state and recovery
    """
    
    def __init__(self, 
                 checkpoint_dir: str = "checkpoints",
                 auto_checkpoint_interval: int = 30,
                 max_recovery_attempts: int = 3,
                 enable_compression: bool = True):
        """
        Initialize session recovery manager.
        
        Args:
            checkpoint_dir: Directory to store checkpoint files
            auto_checkpoint_interval: Automatic checkpoint interval in seconds
            max_recovery_attempts: Maximum number of recovery attempts
            enable_compression: Whether to compress checkpoint data
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.auto_checkpoint_interval = auto_checkpoint_interval
        self.max_recovery_attempts = max_recovery_attempts
        self.enable_compression = enable_compression
        
        # Current session
        self.current_session: Optional[SessionInfo] = None
        self.checkpoints: List[Checkpoint] = []
        self.last_checkpoint_time = 0.0
        
        # Recovery state
        self.recovery_mode = False
        self.recovered_session: Optional[SessionInfo] = None
        self.recovered_checkpoints: List[Checkpoint] = []
    
    def start_session(self, 
                     profile_url: str,
                     output_directory: str,
                     extraction_config: Optional[Dict[str, Any]] = None) -> SessionInfo:
        """
        Start a new extraction session.
        
        Args:
            profile_url: LinkedIn profile URL being extracted
            output_directory: Output directory for results
            extraction_config: Extraction configuration parameters
            
        Returns:
            SessionInfo object for the new session
        """
        self.current_session = SessionInfo(
            profile_url=profile_url,
            output_directory=output_directory,
            extraction_config=extraction_config or {}
        )
        
        self.checkpoints = []
        self.recovery_mode = False
        
        # Create initial checkpoint
        initial_checkpoint = self.create_checkpoint(
            checkpoint_type=CheckpointType.INITIALIZATION,
            description="Session started",
            session_data={
                "profile_url": profile_url,
                "output_directory": output_directory,
                "extraction_config": extraction_config
            }
        )
        
        self.save_session()
        
        logger.info(f"Started new session: {self.current_session.session_id}")
        return self.current_session
    
    def create_checkpoint(self,
                         checkpoint_type: CheckpointType,
                         description: str = "",
                         session_data: Optional[Dict[str, Any]] = None,
                         extracted_data: Optional[List[Dict[str, Any]]] = None,
                         progress_metrics: Optional[Dict[str, Any]] = None,
                         **kwargs) -> Checkpoint:
        """
        Create a new checkpoint.
        
        Args:
            checkpoint_type: Type of checkpoint
            description: Human-readable description
            session_data: Session-specific data
            extracted_data: Extracted content data
            progress_metrics: Progress tracking metrics
            **kwargs: Additional checkpoint parameters
            
        Returns:
            Created Checkpoint object
        """
        if not self.current_session:
            raise RuntimeError("No active session to create checkpoint for")
        
        checkpoint = Checkpoint(
            checkpoint_type=checkpoint_type,
            description=description,
            session_data=session_data or {},
            extracted_data=extracted_data or [],
            progress_metrics=progress_metrics or {},
            url=self.current_session.profile_url,
            **kwargs
        )
        
        self.checkpoints.append(checkpoint)
        self.current_session.total_checkpoints += 1
        self.current_session.current_checkpoint_type = checkpoint_type
        self.current_session.last_checkpoint_time = checkpoint.timestamp
        
        # Update completion percentage based on checkpoint type
        self.current_session.completion_percentage = self._calculate_completion_percentage(checkpoint_type)
        
        # Save checkpoint
        self._save_checkpoint(checkpoint)
        self.save_session()
        
        self.last_checkpoint_time = time.time()
        
        logger.info(f"Created checkpoint: {checkpoint_type.value} - {description}")
        return checkpoint
    
    def should_create_checkpoint(self) -> bool:
        """
        Check if an automatic checkpoint should be created based on time interval.
        
        Returns:
            True if a checkpoint should be created
        """
        return (time.time() - self.last_checkpoint_time) >= self.auto_checkpoint_interval
    
    def auto_checkpoint(self,
                       checkpoint_type: CheckpointType,
                       description: str = "Automatic checkpoint",
                       **kwargs) -> Optional[Checkpoint]:
        """
        Create an automatic checkpoint if the interval has passed.
        
        Args:
            checkpoint_type: Type of checkpoint
            description: Checkpoint description
            **kwargs: Additional checkpoint parameters
            
        Returns:
            Created checkpoint or None if not needed
        """
        if self.should_create_checkpoint():
            return self.create_checkpoint(checkpoint_type, description, **kwargs)
        return None
    
    def detect_interrupted_sessions(self) -> List[SessionInfo]:
        """
        Detect sessions that were interrupted and can potentially be recovered.
        
        Returns:
            List of interrupted SessionInfo objects
        """
        interrupted_sessions = []
        
        for session_file in self.checkpoint_dir.glob("session_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                session_info = SessionInfo.from_dict(session_data)
                
                # Check if session was interrupted
                if (session_info.state in [SessionState.ACTIVE, SessionState.PAUSED] and
                    session_info.can_resume):
                    interrupted_sessions.append(session_info)
                    
            except Exception as e:
                logger.warning(f"Failed to load session file {session_file}: {e}")
        
        return interrupted_sessions
    
    def can_recover_session(self, session_id: str) -> bool:
        """
        Check if a session can be recovered.
        
        Args:
            session_id: Session ID to check
            
        Returns:
            True if session can be recovered
        """
        session_file = self.checkpoint_dir / f"session_{session_id}.json"
        
        if not session_file.exists():
            return False
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            session_info = SessionInfo.from_dict(session_data)
            
            return (session_info.can_resume and
                    session_info.recovery_attempts < self.max_recovery_attempts and
                    session_info.state != SessionState.FAILED)
                    
        except Exception as e:
            logger.error(f"Failed to check session recovery status: {e}")
            return False
    
    def recover_session(self, session_id: str) -> bool:
        """
        Recover a session from checkpoints.
        
        Args:
            session_id: Session ID to recover
            
        Returns:
            True if recovery was successful
        """
        if not self.can_recover_session(session_id):
            logger.error(f"Cannot recover session {session_id}")
            return False
        
        try:
            # Load session info
            session_file = self.checkpoint_dir / f"session_{session_id}.json"
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.recovered_session = SessionInfo.from_dict(session_data)
            self.recovered_session.recovery_attempts += 1
            self.recovered_session.state = SessionState.RECOVERED
            
            # Load checkpoints
            self.recovered_checkpoints = self._load_session_checkpoints(session_id)
            
            # Set current session to recovered session
            self.current_session = self.recovered_session
            self.checkpoints = self.recovered_checkpoints
            self.recovery_mode = True
            
            logger.info(f"Successfully recovered session {session_id} with {len(self.checkpoints)} checkpoints")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recover session {session_id}: {e}")
            return False
    
    def get_recovery_point(self) -> Optional[Checkpoint]:
        """
        Get the checkpoint to resume from after recovery.
        
        Returns:
            Last valid checkpoint or None
        """
        if not self.recovery_mode or not self.checkpoints:
            return None
        
        # Return the last checkpoint
        return self.checkpoints[-1]
    
    def get_recovery_data(self) -> Dict[str, Any]:
        """
        Get all data needed to resume extraction.
        
        Returns:
            Dictionary with recovery data
        """
        if not self.recovery_mode:
            return {}
        
        last_checkpoint = self.get_recovery_point()
        if not last_checkpoint:
            return {}
        
        return {
            "session_info": self.current_session.to_dict() if self.current_session else {},
            "last_checkpoint": last_checkpoint.to_dict(),
            "extracted_data": last_checkpoint.extracted_data,
            "progress_metrics": last_checkpoint.progress_metrics,
            "session_data": last_checkpoint.session_data,
            "scroll_position": last_checkpoint.scroll_position,
            "posts_extracted": last_checkpoint.posts_extracted,
            "total_checkpoints": len(self.checkpoints)
        }
    
    def complete_session(self, 
                        final_data: Optional[Dict[str, Any]] = None,
                        success: bool = True) -> None:
        """
        Mark the current session as completed.
        
        Args:
            final_data: Final extraction data
            success: Whether the session completed successfully
        """
        if not self.current_session:
            return
        
        # Create final checkpoint
        final_checkpoint = self.create_checkpoint(
            checkpoint_type=CheckpointType.COMPLETION,
            description="Session completed" if success else "Session failed",
            session_data=final_data or {},
            progress_metrics={"success": success}
        )
        
        self.current_session.state = SessionState.COMPLETED if success else SessionState.FAILED
        self.current_session.completion_percentage = 100.0 if success else 0.0
        self.current_session.can_resume = False
        
        self.save_session()
        
        logger.info(f"Session {self.current_session.session_id} completed with status: {self.current_session.state.value}")
    
    def save_session(self) -> None:
        """Save current session info to disk."""
        if not self.current_session:
            return
        
        session_file = self.checkpoint_dir / f"session_{self.current_session.session_id}.json"
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_session.to_dict(), f, indent=2, default=str)
            
            logger.debug(f"Saved session info to {session_file}")
            
        except Exception as e:
            logger.error(f"Failed to save session info: {e}")
    
    def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to disk."""
        if not self.current_session:
            return
        
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{self.current_session.session_id}_{checkpoint.checkpoint_id}.json"
        
        try:
            checkpoint_data = checkpoint.to_dict()
            checkpoint_data['hash'] = checkpoint.calculate_hash()
            
            if self.enable_compression:
                # Save as compressed pickle for large data
                import gzip
                pickle_file = checkpoint_file.with_suffix('.pkl.gz')
                with gzip.open(pickle_file, 'wb') as f:
                    pickle.dump(checkpoint_data, f)
            else:
                # Save as JSON
                with open(checkpoint_file, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint_data, f, indent=2, default=str)
            
            logger.debug(f"Saved checkpoint to {checkpoint_file}")
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def _load_session_checkpoints(self, session_id: str) -> List[Checkpoint]:
        """Load all checkpoints for a session."""
        checkpoints = []
        
        # Look for both JSON and compressed pickle files
        checkpoint_patterns = [
            f"checkpoint_{session_id}_*.json",
            f"checkpoint_{session_id}_*.pkl.gz"
        ]
        
        checkpoint_files = []
        for pattern in checkpoint_patterns:
            checkpoint_files.extend(self.checkpoint_dir.glob(pattern))
        
        for checkpoint_file in sorted(checkpoint_files):
            try:
                if checkpoint_file.suffix == '.gz':
                    # Load compressed pickle
                    import gzip
                    with gzip.open(checkpoint_file, 'rb') as f:
                        checkpoint_data = pickle.load(f)
                else:
                    # Load JSON
                    with open(checkpoint_file, 'r', encoding='utf-8') as f:
                        checkpoint_data = json.load(f)
                
                # Verify checkpoint integrity
                stored_hash = checkpoint_data.pop('hash', None)
                
                # Use from_dict for proper deserialization
                checkpoint = Checkpoint.from_dict(checkpoint_data)
                
                if stored_hash and checkpoint.calculate_hash() != stored_hash:
                    logger.warning(f"Checkpoint integrity check failed for {checkpoint_file}")
                    continue
                
                checkpoints.append(checkpoint)
                
            except Exception as e:
                logger.warning(f"Failed to load checkpoint {checkpoint_file}: {e}")
        
        # Sort checkpoints by timestamp to ensure correct order
        checkpoints.sort(key=lambda c: c.timestamp if c.timestamp else datetime.min.replace(tzinfo=timezone.utc))
        
        return checkpoints
    
    def _calculate_completion_percentage(self, checkpoint_type: CheckpointType) -> float:
        """Calculate completion percentage based on checkpoint type."""
        checkpoint_weights = {
            CheckpointType.INITIALIZATION: 5.0,
            CheckpointType.URL_VALIDATION: 10.0,
            CheckpointType.BROWSER_STARTUP: 15.0,
            CheckpointType.PAGE_NAVIGATION: 25.0,
            CheckpointType.SCROLL_PROGRESS: 60.0,
            CheckpointType.CONTENT_EXTRACTION: 80.0,
            CheckpointType.DATA_PROCESSING: 90.0,
            CheckpointType.MARKDOWN_GENERATION: 95.0,
            CheckpointType.COMPLETION: 100.0
        }
        
        return checkpoint_weights.get(checkpoint_type, 0.0)
    
    def cleanup_old_sessions(self, days_old: int = 7) -> int:
        """
        Clean up old session and checkpoint files.
        
        Args:
            days_old: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        
        for file_path in self.checkpoint_dir.glob("*"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete old file {file_path}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} old checkpoint files")
        return deleted_count
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session."""
        if not self.current_session:
            return {"error": "No active session"}
        
        return {
            "session_id": self.current_session.session_id,
            "state": self.current_session.state.value,
            "profile_url": self.current_session.profile_url,
            "start_time": self.current_session.start_time.isoformat(),
            "completion_percentage": self.current_session.completion_percentage,
            "total_checkpoints": self.current_session.total_checkpoints,
            "current_checkpoint_type": self.current_session.current_checkpoint_type.value if self.current_session.current_checkpoint_type else None,
            "recovery_mode": self.recovery_mode,
            "can_resume": self.current_session.can_resume
        }


# Convenience functions
def create_recovery_manager(checkpoint_dir: str = "checkpoints",
                          auto_checkpoint_interval: int = 30) -> SessionRecoveryManager:
    """
    Create a session recovery manager with common settings.
    
    Args:
        checkpoint_dir: Directory for checkpoint storage
        auto_checkpoint_interval: Automatic checkpoint interval in seconds
        
    Returns:
        SessionRecoveryManager instance
    """
    return SessionRecoveryManager(
        checkpoint_dir=checkpoint_dir,
        auto_checkpoint_interval=auto_checkpoint_interval
    )


def find_recoverable_sessions(checkpoint_dir: str = "checkpoints") -> List[SessionInfo]:
    """
    Find all recoverable sessions in the checkpoint directory.
    
    Args:
        checkpoint_dir: Directory to search for sessions
        
    Returns:
        List of recoverable SessionInfo objects
    """
    manager = SessionRecoveryManager(checkpoint_dir=checkpoint_dir)
    return manager.detect_interrupted_sessions()


# Global recovery manager instance
_global_recovery_manager: Optional[SessionRecoveryManager] = None


def get_global_recovery_manager() -> SessionRecoveryManager:
    """Get or create the global recovery manager instance."""
    global _global_recovery_manager
    if _global_recovery_manager is None:
        _global_recovery_manager = create_recovery_manager()
    return _global_recovery_manager


# Export main classes and functions
__all__ = [
    "SessionRecoveryManager",
    "SessionInfo",
    "Checkpoint",
    "CheckpointType",
    "SessionState",
    "create_recovery_manager",
    "find_recoverable_sessions",
    "get_global_recovery_manager"
]
