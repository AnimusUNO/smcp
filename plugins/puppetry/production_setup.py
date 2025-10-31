#!/usr/bin/env python3
"""
Production Twitter Agent Setup
Sets up a real AI agent that will actually post to Twitter
"""

import os
import sys
import json
from datetime import datetime, timedelta
import time

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config_manager import ConfigManager
from integrations.twitter.client import TwitterClient

def create_production_agent():
    """Create a production-ready Twitter agent configuration."""
    
    print("🚀 Setting up Production Twitter Agent")
    print("=" * 50)
    
    # Get agent details from user
    print("\n📝 Agent Configuration:")
    agent_id = input("Enter Agent ID (e.g., 'my-twitter-bot'): ").strip()
    if not agent_id:
        agent_id = "production-agent"
        print(f"Using default: {agent_id}")
    
    personality = input("Enter Agent Personality (e.g., 'Tech enthusiast who loves AI'): ").strip()
    if not personality:
        personality = "AI enthusiast who shares insights about technology and automation"
        print(f"Using default: {personality}")
    
    # Initialize configuration manager
    config_manager = ConfigManager()
    
    # Create agent configuration
    print(f"\n⚙️  Creating configuration for {agent_id}...")
    
    config_data = {
        "agent_id": agent_id,
        "twitter": {
            "api_key": os.getenv("TWITTER_API_KEY", ""),
            "api_key_secret": os.getenv("TWITTER_API_SECRET", ""),
            "access_token": os.getenv("TWITTER_ACCESS_TOKEN", ""),
            "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
        },
        "behavior": {
            "personality": personality,
            "posting_frequency": "medium",
            "engagement_style": "friendly",
            "topics": ["AI", "technology", "automation", "innovation"],
            "tone": "professional but approachable"
        }
    }
    
    # Save configuration
    success = config_manager.save_agent_config(agent_id, config_data)
    if success:
        print("✅ Agent configuration saved!")
    else:
        print("❌ Failed to save configuration")
        return False
    
    # Test Twitter connection
    print(f"\n🐦 Testing Twitter API connection...")
    
    try:
        from core.config_manager import TwitterConfig
        twitter_config = TwitterConfig(**config_data["twitter"])
        twitter_client = TwitterClient(twitter_config)
        
        # Test authentication using is_available method
        if twitter_client.is_available():
            print("✅ Twitter API connection successful!")
            print("� Client initialized and ready for posting")
        else:
            print("❌ Twitter API connection failed!")
            print("   Check your credentials in .env file")
            return False
            
    except Exception as e:
        print(f"❌ Twitter connection error: {e}")
        print("   Make sure you've added your Twitter credentials to .env file")
        return False
    
    return True, agent_id, config_data

async def post_test_tweet(agent_id, config_data):
    """Post a test tweet to verify everything works."""
    
    print(f"\n🧪 Test Tweet:")
    test_message = f"Hello from {agent_id}! 🤖 This is an AI agent powered by the Puppetry system. Testing automated Twitter integration! #AI #Automation"
    
    print(f"📝 Message: {test_message}")
    
    confirm = input("\n⚠️  Do you want to post this test tweet? (y/N): ").strip().lower()
    
    if confirm == 'y':
        try:
            from core.config_manager import TwitterConfig
            twitter_config = TwitterConfig(**config_data["twitter"])
            twitter_client = TwitterClient(twitter_config)
            
            result = await twitter_client.post_tweet(test_message)
            
            if result:
                print("✅ Test tweet posted successfully!")
                print(f"🔗 Tweet ID: {result}")
                return True
            else:
                print("❌ Failed to post tweet")
                return False
                
        except Exception as e:
            print(f"❌ Tweet posting error: {e}")
            return False
    else:
        print("⏭️  Skipping test tweet")
        return True

def setup_production_monitoring(agent_id):
    """Show how to monitor the production agent."""
    
    print(f"\n📊 Production Monitoring for {agent_id}")
    print("-" * 40)
    
    print("🔍 To monitor your agent in production:")
    print(f"   1. Check logs: tail -f logs/{agent_id}.log")
    print(f"   2. View status: python cli.py status --agent-id {agent_id}")
    print(f"   3. List tweets: python cli.py list-tweets --agent-id {agent_id}")
    
    print(f"\n🚀 To start autonomous posting:")
    print(f"   python cli.py start-agent --agent-id {agent_id} --behaviors twitter")
    
    print(f"\n⏹️  To stop the agent:")
    print(f"   python cli.py stop-agent --agent-id {agent_id}")

async def main():
    """Main setup function."""
    
    try:
        # Check environment setup
        print("🔍 Checking environment setup...")
        
        required_vars = ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"]
        missing_vars = [var for var in required_vars if not os.getenv(var) or os.getenv(var) == f"YOUR_ACTUAL_{var}_HERE"]
        
        if missing_vars:
            print("❌ Missing Twitter credentials!")
            print("   Please add these to your .env file:")
            for var in missing_vars:
                print(f"   {var}=your_actual_value_here")
            print("\n   Get credentials from: https://developer.twitter.com")
            return False
        
        print("✅ Environment variables found!")
        
        # Create production agent
        result = create_production_agent()
        if not result:
            return False
            
        success, agent_id, config_data = result
        
        # Test tweet (optional)
        await post_test_tweet(agent_id, config_data)
        
        # Show monitoring instructions
        setup_production_monitoring(agent_id)
        
        print(f"\n🎉 Production Agent Setup Complete!")
        print(f"🤖 Agent '{agent_id}' is ready for autonomous Twitter posting!")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)