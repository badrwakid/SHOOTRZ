"""
Run tracking and output management for MVP pipeline.

Generates unique run IDs and manages output directory structure.
"""

import uuid
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any, Optional


class RunTracker:
    """Manages run IDs and output directories for reproducible analysis."""
    
    def __init__(self, outputs_base_dir: Optional[Path] = None):
        """
        Initialize run tracker.
        
        Args:
            outputs_base_dir: Base directory for outputs (defaults to backend/outputs/)
        """
        if outputs_base_dir is None:
            backend_dir = Path(__file__).parent.parent.parent
            outputs_base_dir = backend_dir / "outputs"
        
        self.outputs_base_dir = Path(outputs_base_dir)
        self.outputs_base_dir.mkdir(parents=True, exist_ok=True)
        
        self.run_id: Optional[str] = None
        self.run_dir: Optional[Path] = None
        self.metadata: Dict[str, Any] = {}
    
    def create_run(self) -> str:
        """
        Create a new run with unique ID.
        
        Returns:
            Run ID (UUID string)
        """
        self.run_id = str(uuid.uuid4())
        self.run_dir = self.outputs_base_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata
        self.metadata = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        return self.run_id
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata entry."""
        self.metadata[key] = value
    
    def save_metadata(self):
        """Save metadata to run directory."""
        if self.run_dir is None:
            raise ValueError("No active run. Call create_run() first.")
        
        metadata_path = self.run_dir / "run_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_output_path(self, filename: str) -> Path:
        """
        Get path for output file in run directory.
        
        Args:
            filename: Name of output file
        
        Returns:
            Full path to output file
        """
        if self.run_dir is None:
            raise ValueError("No active run. Call create_run() first.")
        
        return self.run_dir / filename
    
    def get_run_dir(self) -> Path:
        """Get current run directory."""
        if self.run_dir is None:
            raise ValueError("No active run. Call create_run() first.")
        return self.run_dir


def create_run_tracker(outputs_base_dir: Optional[Path] = None) -> RunTracker:
    """
    Create and initialize a run tracker.
    
    Args:
        outputs_base_dir: Optional base directory for outputs
    
    Returns:
        RunTracker instance with new run ID
    """
    tracker = RunTracker(outputs_base_dir)
    tracker.create_run()
    return tracker
