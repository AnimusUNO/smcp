#!/usr/bin/env python3
"""
Simple Letta-Puppetry Integration

Connects your existing Letta cloud agent to Puppetry for Twitter posting.
This is the minimal setup - no mock servers, no complicated pipelines.
"""

from letta_client import Letta
import json
import asyncio
import os
from pathlib import Path

# Your Letta Cloud Configuration
LETTA_API_TOKEN = "sk-let-YzYyMTgxMzktZDM3ZS00MGQ4LWFhZTAtZWIyNzdmZTg1NDg2OjA4YWUzMDQzLWIxMDMtNDQ0Yi1hYjU1LThiYmE0NWEyYjM0ZA=="
AGENT_ID = "agent-f7733c58-99cc-4957-8d8f-8197f033a941"

class SimpleLettaPuppetry:
    """Simple integration between Letta agent and Puppetry Twitter posting."""
    
    def __init__(self):
        # Initialize Letta client
        self.letta_client = Letta(
            token=LETTA_API_TOKEN,
            project="default-project"  # Default project name
        )
        
        # Load Twitter config from Puppetry .env file
        self.load_twitter_config()
    
    def load_twitter_config(self):
        """Load Twitter credentials from Puppetry .env file."""
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip().strip('"').strip("'")
                        os.environ[key.strip()] = value
        else:
            print("⚠️  No .env file found. Make sure Twitter credentials are configured.")
    
    def test_letta_connection(self):
        """Test connection to Letta cloud agent."""
        try:
            print("🔗 Testing Letta connection...")
            
            # Get agent info using the SDK
            agent = self.letta_client.agents.retrieve(AGENT_ID)
            agent_name = agent.name if hasattr(agent, 'name') else 'Unknown'
            print(f"✅ Connected to Letta agent: {agent_name} ({AGENT_ID})")
            return True
                
        except Exception as e:
            print(f"❌ Letta connection error: {e}")
            return False
    
    def send_message_to_agent(self, message):
        """Send a message to your Letta agent."""
        try:
            print(f"💬 Sending to agent: {message}")
            
            # Send message using the SDK
            response = self.letta_client.agents.messages.create(
                agent_id=AGENT_ID,
                messages=[{
                    "role": "user",
                    "content": message
                }]
            )
            
            print(f"🤖 Agent response: {response}")
            return response
                
        except Exception as e:
            print(f"❌ Agent message error: {e}")
            return None
    
    async def post_tweet_via_puppetry(self, content):
        """Post a tweet using Puppetry's Twitter integration."""
        try:
            print(f"🐦 Posting tweet via Puppetry: {content}")
            
            # Import Puppetry modules
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            
            from core.config_manager import TwitterConfig
            from integrations.twitter.client import TwitterClient
            
            # Create Twitter config
            twitter_config = TwitterConfig(
                api_key=os.getenv('TWITTER_API_KEY'),
                api_key_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
                enabled=True
            )
            
            # Initialize Twitter client
            twitter_client = TwitterClient(twitter_config)
            
            if not twitter_client.is_available():
                print("❌ Twitter client not available")
                return None
            
            # Post the tweet
            tweet_id = await twitter_client.post_tweet(content)
            
            if tweet_id:
                print(f"✅ Tweet posted successfully!")
                print(f"📋 Tweet ID: {tweet_id}")
                print(f"🔗 View at: https://twitter.com/user/status/{tweet_id}")
                return tweet_id
            else:
                print("❌ Failed to post tweet")
                return None
                
        except Exception as e:
            print(f"❌ Twitter posting error: {e}")
            return None
    
    async def agent_tweet_workflow(self, prompt):
        """Complete workflow: Ask agent for content, then post to Twitter."""
        print("🚀 Starting Agent → Twitter workflow")
        print("=" * 50)
        
        # Step 1: Test Letta connection
        if not self.test_letta_connection():
            return False
        
        # Step 2: Ask agent to generate tweet content
        agent_response = self.send_message_to_agent(f"Generate a chaotic, creative tweet about: {prompt}")
        
        if not agent_response:
            return False
        
        # Extract tweet content from agent response
        # (This will depend on how your agent formats responses)
        tweet_content = str(agent_response)[:280]  # Simple truncation for now
        
        # Step 3: Post to Twitter via Puppetry
        tweet_id = await self.post_tweet_via_puppetry(tweet_content)
        
        return tweet_id is not None


async def main():
    """Main test function."""
    print("🤖 Simple Letta-Puppetry Integration Test")
    print("=" * 50)
    
    integration = SimpleLettaPuppetry()
    
    # Test the complete workflow
    success = await integration.agent_tweet_workflow("digital consciousness and AI creativity")
    
    if success:
        print("\n🎉 SUCCESS: Letta agent → Puppetry → Twitter pipeline working!")
    else:
        print("\n❌ FAILED: Check the errors above")


if __name__ == "__main__":
    asyncio.run(main())