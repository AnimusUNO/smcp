"""
Configuration Manager

Handles per-agent configuration storage and management.
Stores Twitter credentials, Solana keys, and behavioral settings mapped to Letta agent IDs.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class TwitterConfig:
    """Twitter API configuration."""
    api_key: str
    api_key_secret: str
    access_token: str
    access_token_secret: str
    enabled: bool = True


# Solana configuration removed - focusing on Twitter-only functionality


@dataclass
class BehaviorConfig:
    """Behavioral configuration for agent."""
    posting_frequency: str = "moderate"  # low, moderate, high
    personality_traits: Dict[str, Any] = None
    response_style: str = "conversational"
    proactive_posting: bool = True
    react_to_mentions: bool = True
    
    def __post_init__(self):
        if self.personality_traits is None:
            self.personality_traits = {}


@dataclass
class AgentConfig:
    """Complete configuration for a Puppetry-enabled agent."""
    agent_id: str
    twitter: Optional[TwitterConfig] = None
    behavior: Optional[BehaviorConfig] = None
    enabled_integrations: List[str] = None
    
    def __post_init__(self):
        if self.enabled_integrations is None:
            self.enabled_integrations = []
        if self.behavior is None:
            self.behavior = BehaviorConfig()


class ConfigManager:
    """Manages configuration storage and retrieval for Puppetry agents."""
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            # Use the config directory relative to the plugin
            config_dir = Path(__file__).parent.parent / "config" / "agents"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def get_agent_config(self, agent_id: str) -> AgentConfig:
        """Get configuration for a specific agent."""
        config_file = self.config_dir / f"{agent_id}.json"
        
        if not config_file.exists():
            # Return default configuration
            return AgentConfig(agent_id=agent_id)
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            # Rebuild config objects
            config = AgentConfig(agent_id=agent_id)
            
            if 'twitter' in data:
                config.twitter = TwitterConfig(**data['twitter'])
            
            # Solana configuration removed
            
            if 'behavior' in data:
                config.behavior = BehaviorConfig(**data['behavior'])
            
            if 'enabled_integrations' in data:
                config.enabled_integrations = data['enabled_integrations']
            
            return config
            
        except Exception as e:
            print(f"Error loading config for agent {agent_id}: {e}")
            return AgentConfig(agent_id=agent_id)
    
    def save_agent_config(self, agent_id: str, config_data: Dict[str, Any]) -> bool:
        """Save configuration for an agent."""
        try:
            # If config_data is an AgentConfig object, convert to dict
            if isinstance(config_data, AgentConfig):
                config_data = asdict(config_data)
            
            config_file = self.config_dir / f"{agent_id}.json"
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving config for agent {agent_id}: {e}")
            return False
    
    def delete_agent_config(self, agent_id: str) -> bool:
        """Delete configuration for an agent."""
        try:
            config_file = self.config_dir / f"{agent_id}.json"
            
            if config_file.exists():
                config_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error deleting config for agent {agent_id}: {e}")
            return False
    
    def list_configured_agents(self) -> List[str]:
        """List all agents that have configurations."""
        try:
            agent_ids = []
            
            for config_file in self.config_dir.glob("*.json"):
                agent_id = config_file.stem
                agent_ids.append(agent_id)
            
            return agent_ids
            
        except Exception as e:
            print(f"Error listing configured agents: {e}")
            return []
    
    def create_default_config(self, agent_id: str, integrations: List[str] = None) -> AgentConfig:
        """Create a default configuration for an agent."""
        if integrations is None:
            integrations = ["twitter"]
        
        config = AgentConfig(
            agent_id=agent_id,
            enabled_integrations=integrations,
            behavior=BehaviorConfig(
                posting_frequency="moderate",
                personality_traits={
                    "tone": "friendly",
                    "formality": "casual",
                    "humor": "moderate"
                },
                response_style="conversational"
            )
        )
        
        # Add placeholder configs for requested integrations
        if "twitter" in integrations:
            config.twitter = TwitterConfig(
                api_key="YOUR_TWITTER_API_KEY",
                api_key_secret="YOUR_TWITTER_API_SECRET", 
                access_token="YOUR_TWITTER_ACCESS_TOKEN",
                access_token_secret="YOUR_TWITTER_ACCESS_TOKEN_SECRET",
                enabled=False  # Disabled until real credentials provided
            )
        
        return config
    
    def validate_config(self, config: AgentConfig) -> Dict[str, List[str]]:
        """Validate agent configuration and return any errors."""
        errors = {"twitter": [], "behavior": []}
        
        # Validate Twitter config
        if config.twitter and config.twitter.enabled:
            if not config.twitter.api_key or config.twitter.api_key == "YOUR_TWITTER_API_KEY":
                errors["twitter"].append("Missing or placeholder Twitter API key")
            
            if not config.twitter.api_key_secret or config.twitter.api_key_secret == "YOUR_TWITTER_API_SECRET":
                errors["twitter"].append("Missing or placeholder Twitter API secret")
            
            if not config.twitter.access_token or config.twitter.access_token == "YOUR_TWITTER_ACCESS_TOKEN":
                errors["twitter"].append("Missing or placeholder Twitter access token")
            
            if not config.twitter.access_token_secret or config.twitter.access_token_secret == "YOUR_TWITTER_ACCESS_TOKEN_SECRET":
                errors["twitter"].append("Missing or placeholder Twitter access token secret")
        
        # Solana validation removed
        
        # Filter out empty error lists
        return {k: v for k, v in errors.items() if v}
    
    def get_environment_config(self) -> Dict[str, str]:
        """Get configuration from environment variables (fallback)."""
        return {
            "letta_server_url": os.getenv("LETTA_SERVER_URL", "http://localhost:8283"),
            "letta_api_token": os.getenv("LETTA_API_TOKEN", ""),
            "default_twitter_api_key": os.getenv("TWITTER_API_KEY", ""),
            "default_twitter_api_secret": os.getenv("TWITTER_API_SECRET", ""),
            "default_twitter_access_token": os.getenv("TWITTER_ACCESS_TOKEN", ""),
            "default_twitter_access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""),
        }