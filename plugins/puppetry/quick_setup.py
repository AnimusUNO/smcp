#!/usr/bin/env python3
"""
Quick production setup for Puppetry Twitter Agent
Non-interactive version for testing
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value

load_env_file()

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import ConfigManager, TwitterConfig, BehaviorConfig, AgentConfig
from core.agent_bridge import LettaAgentBridge
from integrations.twitter.client import TwitterClient


async def quick_test():
    """Quick test of the complete Puppetry system."""
    print("🚀 Quick Puppetry Production Test")
    print("=" * 40)
    
    # Step 1: Check environment
    print("\n1. Checking environment...")
    required_vars = [
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET', 
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print(f"❌ Missing {var}")
            return
        print(f"✅ {var}: {value[:10]}...")
    
    # Step 2: Create test agent configuration
    print("\n2. Creating test agent configuration...")
    agent_id = "test-agent"
    
    twitter_config = TwitterConfig(
        api_key=os.getenv('TWITTER_API_KEY'),
        api_key_secret=os.getenv('TWITTER_API_SECRET'),
        access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
        enabled=True
    )
    
    behavior_config = BehaviorConfig(
        posting_frequency="high",
        response_style="enthusiastic",
        proactive_posting=True,
        react_to_mentions=True,
        personality_traits={
            "style": "AI enthusiast sharing insights about technology and artificial intelligence",
            "topics": ["AI", "technology", "innovation", "programming"]
        }
    )
    
    agent_config = AgentConfig(
        agent_id=agent_id,
        twitter=twitter_config,
        behavior=behavior_config,
        enabled_integrations=["twitter"]
    )
    
    print(f"✅ Agent configuration created for: {agent_id}")
    
    # Step 3: Initialize TwitterClient
    print("\n3. Testing Twitter client...")
    twitter_client = TwitterClient(twitter_config)
    
    if not twitter_client.is_available():
        print("❌ Twitter client failed to initialize")
        return
    
    print("✅ Twitter client initialized successfully")
    
    # Step 4: Test tweet posting (commented out for safety)
    print("\n4. Testing tweet capability...")
    print("📝 Would post tweet: 'Hello from the Puppetry system! 🤖 #AI #Twitter'")
    print("⚠️  Actual posting disabled for safety - uncomment to enable")
    
    # Uncomment the following lines to actually post a tweet:
    # test_tweet = "Hello from the Puppetry system! 🤖 #AI #Twitter"
    # tweet_id = await twitter_client.post_tweet(test_tweet)
    # if tweet_id:
    #     print(f"✅ Tweet posted successfully! ID: {tweet_id}")
    # else:
    #     print("❌ Failed to post tweet")
    
    # Step 5: Save configuration
    print("\n5. Saving configuration...")
    config_manager = ConfigManager()
    success = config_manager.save_agent_config(agent_id, agent_config)
    if success:
        print(f"✅ Configuration saved to: agents/{agent_id}.json")
    else:
        print("❌ Failed to save configuration")
    
    print("\n🎉 Production setup complete!")
    print("\nTo start the agent:")
    print(f"   python cli.py start-agent --agent-id {agent_id}")
    print("\nTo post a test tweet, uncomment the posting code in this script.")


if __name__ == "__main__":
    asyncio.run(quick_test())