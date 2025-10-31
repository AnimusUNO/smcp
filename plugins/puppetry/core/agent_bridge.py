"""
Letta Agent Bridge

Handles integration with Letta server for agent management.
Uses the same pattern as animus-chat for agent discovery and binding.
"""

import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

# Try to load .env file if it exists
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")

# Load .env file on import
load_env_file()

try:
    from letta_client import Letta as LettaSDK
    from letta_client import MessageCreate
except ImportError:
    print("Warning: letta_client not available. Install with: pip install letta-client")
    LettaSDK = None
    MessageCreate = None


@dataclass
class Agent:
    """Represents a Letta agent."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None


class LettaAgentBridge:
    """Bridge to Letta server for agent operations."""
    
    def __init__(self):
        self.client = None
        self.server_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
        self.api_token = os.getenv("LETTA_API_TOKEN")
        
        if not self.api_token:
            print("Warning: LETTA_API_TOKEN not set. Agent operations may fail.")
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Letta client connection."""
        if not LettaSDK:
            return
            
        try:
            self.client = LettaSDK(
                base_url=self.server_url,
                token=self.api_token
            )
            print(f"Letta client initialized: {self.server_url}")
        except Exception as e:
            print(f"Failed to initialize Letta client: {e}")
            self.client = None
    
    def health_check(self) -> bool:
        """Check if Letta server is accessible."""
        if not self.client:
            return False
            
        try:
            self.client.health.check()
            return True
        except Exception as e:
            print(f"Letta health check failed: {e}")
            return False
    
    def list_agents(self) -> List[Agent]:
        """List all available agents from Letta server."""
        if not self.client:
            return []
        
        try:
            agents_response = self.client.agents.list()
            agents = []
            
            for agent in agents_response:
                agents.append(Agent(
                    id=agent.id,
                    name=agent.name or f"Agent {agent.id}",
                    description=agent.description,
                    created_at=agent.created_at
                ))
            
            return agents
            
        except Exception as e:
            print(f"Failed to list agents: {e}")
            return []
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get a specific agent by ID."""
        if not self.client:
            return None
            
        try:
            # First try to get the agent from the agents list
            agents = self.client.agents.list()
            for agent in agents:
                if agent.id == agent_id:
                    return Agent(
                        id=agent.id,
                        name=agent.name or f"Agent {agent.id}",
                        description=agent.description,
                        created_at=agent.created_at
                    )
            return None
            
        except Exception as e:
            print(f"Failed to get agent {agent_id}: {e}")
            return None
    
    def send_message(self, agent_id: str, message: str) -> Optional[str]:
        """Send a message to an agent and get response."""
        if not self.client:
            return None
            
        try:
            # Create message object
            message_obj = MessageCreate(
                role="user",
                text=message
            )
            
            # Send message to agent
            response = self.client.agents.create_message(
                agent_id=agent_id,
                message=message_obj
            )
            
            # Extract response text
            if response and hasattr(response, 'messages'):
                for msg in response.messages:
                    if msg.role == "assistant":
                        return msg.text
            
            return None
            
        except Exception as e:
            print(f"Failed to send message to agent {agent_id}: {e}")
            return None
    
    def get_agent_memory(self, agent_id: str) -> Dict[str, Any]:
        """Get agent memory context."""
        if not self.client:
            return {}
            
        try:
            # Get agent's memory/context
            memory = self.client.agents.get_memory(agent_id)
            return memory if memory else {}
            
        except Exception as e:
            print(f"Failed to get memory for agent {agent_id}: {e}")
            return {}
    
    def update_agent_memory(self, agent_id: str, memory_update: Dict[str, Any]) -> bool:
        """Update agent memory with new information."""
        if not self.client:
            return False
            
        try:
            # Update agent memory
            self.client.agents.update_memory(agent_id, memory_update)
            return True
            
        except Exception as e:
            print(f"Failed to update memory for agent {agent_id}: {e}")
            return False