"""
Configuration loader for MVP pipeline.

Loads config from YAML and provides type-safe access to parameters.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import shutil


class MVPConfig:
    """Configuration manager for MVP pipeline."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config YAML (defaults to backend/config/mvp_config.yaml)
        """
        if config_path is None:
            # Default to mvp_config.yaml in backend/config/
            backend_dir = Path(__file__).parent.parent.parent
            config_path = backend_dir / "config" / "mvp_config.yaml"
        
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'pose_detection.model_complexity')
            default: Default value if key not found
        
        Returns:
            Config value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def save_snapshot(self, output_dir: Path) -> Path:
        """
        Save a snapshot of the config used for this run.
        
        Args:
            output_dir: Directory to save config snapshot
        
        Returns:
            Path to saved config file
        """
        output_path = output_dir / "config_used.yaml"
        shutil.copy(self.config_path, output_path)
        return output_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Return full config as dictionary."""
        return self.config.copy()


def load_config(config_path: Optional[str] = None) -> MVPConfig:
    """
    Load MVP configuration.
    
    Args:
        config_path: Optional path to config file
    
    Returns:
        MVPConfig instance
    """
    return MVPConfig(config_path)
