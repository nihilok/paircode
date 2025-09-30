"""Configuration service for managing PairCode settings."""
import json
from pathlib import Path
from typing import Dict, Optional


class ConfigService:
    """Service for managing PairCode configuration."""
    
    DEFAULT_CONFIG_PATH = Path.home() / ".paircode_config.json"
    
    DEFAULT_CODER_NAME = "Alice"
    DEFAULT_TESTER_NAME = "Bob"
    DEFAULT_SUPERVISOR_NAME = "Chief"
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the config service.
        
        Args:
            config_path: Path to the config file. Defaults to ~/.paircode_config.json
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
    
    def load(self) -> Dict[str, str]:
        """Load configuration from disk.
        
        Returns:
            Dictionary containing configuration values
        """
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def save(self, config: Dict[str, str]) -> None:
        """Save configuration to disk.
        
        Args:
            config: Dictionary containing configuration values to save
        """
        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def update(self, **kwargs) -> Dict[str, str]:
        """Update configuration with new values.
        
        Args:
            **kwargs: Configuration keys and values to update
            
        Returns:
            The updated configuration dictionary
        """
        config = self.load()
        
        # Only update non-None values
        for key, value in kwargs.items():
            if value is not None:
                config[key] = value
        
        self.save(config)
        return config
    
    def get_agent_names(self) -> tuple[str, str, str]:
        """Get configured agent names or defaults.
        
        Returns:
            Tuple of (coder_name, tester_name, supervisor_name)
        """
        config = self.load()
        
        coder_name = config.get("agent_coder", self.DEFAULT_CODER_NAME)
        tester_name = config.get("agent_tester", self.DEFAULT_TESTER_NAME)
        supervisor_name = config.get("supervisor_name", self.DEFAULT_SUPERVISOR_NAME)
        
        return coder_name, tester_name, supervisor_name
