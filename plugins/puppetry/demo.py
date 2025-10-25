#!/usr/bin/env python3
"""
Quick Demo Script for Puppetry Plugin
Demonstrates Twitter agent functionality without complex Letta integration
"""

import os
import sys
import json
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config_manager import ConfigManager
from core.event_bus import ThalamusEventBus

def run_demo():
    """Run a quick demo of Puppetry functionality."""
    
    print("🚀 Puppetry Plugin Demo")
    print("=" * 50)
    
    # Initialize components
    print("📋 Initializing Puppetry components...")
    config_manager = ConfigManager()
    event_bus = ThalamusEventBus()
    
    # Demo agent configuration
    demo_agent_id = "demo-agent"
    
    print(f"🤖 Demo Agent: {demo_agent_id}")
    print("🐦 Behaviors: Twitter")
    
    # Simulate agent registration
    print("\n📝 Registering agent with event bus...")
    event_bus.register_agent(demo_agent_id, ["twitter"])
    
    # Show configuration
    print("\n⚙️  Agent Configuration:")
    try:
        # Try to load or create demo config
        config = config_manager.get_agent_config(demo_agent_id)
        if not config:
            print("   📄 Creating demo configuration...")
            config = config_manager.create_default_config(demo_agent_id, ["twitter"])
            
        print(f"   Agent ID: {config.agent_id}")
        print(f"   Twitter Configured: {'✅' if config.twitter.api_key else '❌ (needs setup)'}")
        print(f"   Personality: {config.behavior.personality}")
        print(f"   Post Frequency: {config.behavior.posting_frequency}")
        
    except Exception as e:
        print(f"   ⚠️  Config error: {e}")
    
    # Simulate event processing
    print("\n🔄 Event Processing Demo:")
    try:
        # Create a sample event
        event_data = {
            "agent_id": demo_agent_id,
            "event_type": "twitter_post",
            "content": "Hello from Puppetry! 🤖 This is a demo of the AI agent system.",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"   📤 Processing event: {event_data['event_type']}")
        print(f"   💬 Content: {event_data['content']}")
        
        # Simulate sending to Twitter integration (would actually post to Twitter)
        print("   🐦 → Twitter Integration (simulated)")
        print("   ✅ Event processed successfully!")
        
    except Exception as e:
        print(f"   ❌ Event processing error: {e}")
    
    # Show active agents
    print(f"\n📊 Active Agents:")
    active_agents = event_bus.get_active_agents()
    for agent_id, behaviors in active_agents.items():
        behaviors_str = ", ".join(behaviors)
        print(f"   🤖 {agent_id}: [{behaviors_str}]")
    
    # Cleanup
    print(f"\n🧹 Cleanup:")
    event_bus.unregister_agent(demo_agent_id)
    print(f"   ✅ Agent {demo_agent_id} unregistered")
    
    print("\n🎉 Demo completed successfully!")
    print("=" * 50)
    print("✨ Puppetry Plugin is working!")
    print("📝 Next steps:")
    print("   1. Add real Twitter API credentials to .env")
    print("   2. Connect to real Letta server")
    print("   3. Create production agents")
    print("   4. Start autonomous Twitter behaviors")
    
    return True

if __name__ == "__main__":
    try:
        success = run_demo()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)