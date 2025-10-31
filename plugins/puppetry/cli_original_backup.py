#!/usr/bin/env python3
"""
Puppetry CLI Plugin

Unified Animus + Puppet Engine integration for SMCP.
Provides AI Twitter agents with autonomous behaviors and Solana trading.

This plugin bridges Letta agents with performative Twitter behaviors,
following the Animus architecture pattern where:
- Letta = agent registry + cognition endpoint  
- Thalamus = internal event bus pattern
- Puppet Engine = performative layer (Twitter, Solana, behaviors)

Copyright (c) 2025 Animus Team

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import argparse
import json
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Add the puppetry directory to Python path for imports
PUPPETRY_DIR = Path(__file__).parent
sys.path.insert(0, str(PUPPETRY_DIR))

try:
    from core.agent_bridge import LettaAgentBridge
    from core.config_manager import ConfigManager
    from core.event_bus import ThalamusEventBus
    from integrations.twitter.client import TwitterIntegration
except ImportError as e:
    print(f"Error importing Puppetry modules: {e}")
    print("Ensure all dependencies are installed and modules are properly configured.")
    sys.exit(1)


class PuppetryPlugin:
    """Main Puppetry plugin class that coordinates all functionality."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.agent_bridge = LettaAgentBridge()
        self.event_bus = ThalamusEventBus()
        self.twitter = TwitterIntegration()
        
    def start_agent(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Start Puppetry behaviors for a specific Letta agent."""
        agent_id = args.get("agent-id")
        behaviors = args.get("behaviors", ["twitter"])
        
        if not agent_id:
            return {"error": "Missing required argument: agent-id"}
        
        try:
            # Verify agent exists in Letta
            agent = self.agent_bridge.get_agent(agent_id)
            if not agent:
                return {"error": f"Agent {agent_id} not found in Letta server"}
            
            # Load configuration for this agent
            config = self.config_manager.get_agent_config(agent_id)
            
            # Start requested behaviors
            started_behaviors = []
            
            if "twitter" in behaviors:
                twitter_result = self.twitter.start_for_agent(agent_id, config)
                if twitter_result.get("success"):
                    started_behaviors.append("twitter")
            
            # Register with event bus
            self.event_bus.register_agent(agent_id, started_behaviors)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "started_behaviors": started_behaviors,
                "message": f"Puppetry started for agent {agent_id}"
            }
            
        except Exception as e:
            return {"error": f"Failed to start agent: {str(e)}"}
    
    def stop_agent(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stop Puppetry behaviors for a specific agent."""
        agent_id = args.get("agent-id")
        
        if not agent_id:
            return {"error": "Missing required argument: agent-id"}
        
        try:
            # Stop behaviors
            self.twitter.stop_for_agent(agent_id)
            self.event_bus.unregister_agent(agent_id)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "message": f"Puppetry stopped for agent {agent_id}"
            }
            
        except Exception as e:
            return {"error": f"Failed to stop agent: {str(e)}"}
    
    def list_agents(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all Letta agents available for Puppetry."""
        try:
            agents = self.agent_bridge.list_agents()
            active_agents = self.event_bus.get_active_agents()
            
            return {
                "success": True,
                "total_agents": len(agents),
                "active_puppetry_agents": len(active_agents),
                "agents": [
                    {
                        "id": agent.id,
                        "name": agent.name,
                        "puppetry_active": agent.id in active_agents,
                        "behaviors": active_agents.get(agent.id, [])
                    }
                    for agent in agents
                ]
            }
            
        except Exception as e:
            return {"error": f"Failed to list agents: {str(e)}"}
    
    def configure_agent(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Configure Puppetry settings for an agent."""
        agent_id = args.get("agent-id")
        config_file = args.get("config-file")
        
        if not agent_id:
            return {"error": "Missing required argument: agent-id"}
            
        if not config_file or not os.path.exists(config_file):
            return {"error": "Missing or invalid config-file"}
        
        try:
            # Load and validate configuration
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Save configuration for agent
            self.config_manager.save_agent_config(agent_id, config_data)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "message": "Configuration updated successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to configure agent: {str(e)}"}
    
    def status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get Puppetry system status."""
        try:
            letta_status = self.agent_bridge.health_check()
            active_agents = self.event_bus.get_active_agents()
            
            return {
                "success": True,
                "letta_connected": letta_status,
                "active_agents": len(active_agents),
                "behaviors_running": sum(len(behaviors) for behaviors in active_agents.values()),
                "twitter_enabled": self.twitter.is_available()
            }
            
        except Exception as e:
            return {"error": f"Failed to get status: {str(e)}"}


def main():
    """Main CLI entry point following SMCP plugin pattern."""
    parser = argparse.ArgumentParser(
        description="Puppetry - Unified Animus + Puppet Engine integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  start-agent      Start Puppetry behaviors for a Letta agent
  stop-agent       Stop Puppetry behaviors for an agent
  list-agents      List all available Letta agents
  configure-agent  Configure Puppetry settings for an agent
  status          Get Puppetry system status

Examples:
  python cli.py start-agent --agent-id agent-123 --behaviors twitter
  python cli.py stop-agent --agent-id agent-123
  python cli.py list-agents
  python cli.py configure-agent --agent-id agent-123 --config-file config.json
  python cli.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start agent command
    start_parser = subparsers.add_parser("start-agent", help="Start Puppetry for an agent")
    start_parser.add_argument("--agent-id", required=True, help="Letta agent ID")
    start_parser.add_argument("--behaviors", nargs="*", default=["twitter"], 
                             help="Behaviors to enable (currently only twitter)")
    
    # Stop agent command
    stop_parser = subparsers.add_parser("stop-agent", help="Stop Puppetry for an agent")
    stop_parser.add_argument("--agent-id", required=True, help="Letta agent ID")
    
    # List agents command
    list_parser = subparsers.add_parser("list-agents", help="List all available agents")
    
    # Configure agent command
    config_parser = subparsers.add_parser("configure-agent", help="Configure agent settings")
    config_parser.add_argument("--agent-id", required=True, help="Letta agent ID")
    config_parser.add_argument("--config-file", required=True, help="Path to configuration JSON file")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Get system status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        plugin = PuppetryPlugin()
        
        if args.command == "start-agent":
            result = plugin.start_agent({
                "agent-id": args.agent_id,
                "behaviors": args.behaviors
            })
        elif args.command == "stop-agent":
            result = plugin.stop_agent({
                "agent-id": args.agent_id
            })
        elif args.command == "list-agents":
            result = plugin.list_agents({})
        elif args.command == "configure-agent":
            result = plugin.configure_agent({
                "agent-id": args.agent_id,
                "config-file": args.config_file
            })
        elif args.command == "status":
            result = plugin.status({})
        else:
            result = {"error": f"Unknown command: {args.command}"}
        
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("success") else 1)
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()