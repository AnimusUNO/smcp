#!/usr/bin/env python3
"""
Standalone Twitter Agent - Production Ready

This demonstrates a working Twitter AI agent without requiring Letta server.
Perfect for showing the core Puppetry functionality.
"""

import os
import sys
import asyncio
import random
import time
from pathlib import Path
from datetime import datetime

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
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value

load_env_file()

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import TwitterConfig
from integrations.twitter.client import TwitterClient


class StandaloneTwitterAgent:
    """A simple Twitter AI agent that posts autonomously."""
    
    def __init__(self, agent_name: str, personality: dict):
        self.agent_name = agent_name
        self.personality = personality
        self.twitter_client = None
        self.running = False
        
        # Tweet templates based on personality
        self.tweet_templates = [
            "🤖 {thought} #AI #Tech",
            "💡 Just thinking: {thought} #Innovation", 
            "🚀 {thought} What do you think? #AI #Future",
            "🔮 {thought} #ArtificialIntelligence #Technology",
            "🌟 {thought} #AI #MachineLearning"
        ]
        
        self.thoughts = [
            "AI is transforming how we interact with technology every day",
            "The future of programming might be more conversational than we think",
            "Machine learning is becoming more accessible to developers worldwide", 
            "AI agents are starting to collaborate with humans in amazing ways",
            "The intersection of AI and creativity is producing fascinating results",
            "Automation is freeing humans to focus on more creative and strategic work",
            "Natural language processing is making computers more intuitive to use",
            "The democratization of AI tools is accelerating innovation globally"
        ]
    
    async def initialize(self):
        """Initialize the Twitter client."""
        print(f"🤖 Initializing {self.agent_name}...")
        
        twitter_config = TwitterConfig(
            api_key=os.getenv('TWITTER_API_KEY'),
            api_key_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
            enabled=True
        )
        
        self.twitter_client = TwitterClient(twitter_config)
        
        if not self.twitter_client.is_available():
            print("❌ Failed to initialize Twitter client")
            return False
        
        print(f"✅ {self.agent_name} is ready to tweet!")
        return True
    
    def generate_tweet(self) -> str:
        """Generate a tweet based on personality."""
        template = random.choice(self.tweet_templates)
        thought = random.choice(self.thoughts)
        
        return template.format(thought=thought)
    
    async def post_tweet(self) -> bool:
        """Post a single tweet."""
        if not self.twitter_client:
            return False
        
        tweet_text = self.generate_tweet()
        print(f"📝 Posting: {tweet_text}")
        
        tweet_id = await self.twitter_client.post_tweet(tweet_text)
        
        if tweet_id:
            print(f"✅ Tweet posted! ID: {tweet_id}")
            print(f"🔗 https://twitter.com/user/status/{tweet_id}")
            return True
        else:
            print("❌ Failed to post tweet")
            return False
    
    async def run_demo(self, num_tweets: int = 3, delay_minutes: float = 0.5):
        """Run a demonstration with multiple tweets."""
        print(f"🚀 Starting {self.agent_name} demo...")
        print(f"📊 Will post {num_tweets} tweets with {delay_minutes} minute delays")
        print("=" * 50)
        
        for i in range(num_tweets):
            print(f"\n📢 Tweet {i+1}/{num_tweets} - {datetime.now().strftime('%H:%M:%S')}")
            
            success = await self.post_tweet()
            
            if success:
                print("⏳ Waiting before next tweet...")
                await asyncio.sleep(delay_minutes * 60)  # Convert to seconds
            else:
                print("❌ Stopping demo due to tweet failure")
                break
        
        print(f"\n🎉 Demo complete! {self.agent_name} posted tweets successfully.")


async def main():
    """Main function to run the standalone agent."""
    print("🐦 Puppetry Standalone Twitter Agent")
    print("=" * 40)
    
    # Create agent with AI personality
    agent = StandaloneTwitterAgent(
        agent_name="AI Insights Bot",
        personality={
            "style": "Thoughtful and engaging",
            "topics": ["AI", "Technology", "Innovation", "Programming"],
            "tone": "Optimistic and curious"
        }
    )
    
    # Initialize
    if not await agent.initialize():
        print("❌ Failed to initialize agent")
        return
    
    # Ask user what to do
    print("\n🎯 What would you like to do?")
    print("1. Post a single tweet")
    print("2. Run demo (3 tweets with 30-second delays)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        print("\n📝 Posting single tweet...")
        await agent.post_tweet()
        
    elif choice == "2":
        print("\n🚀 Running demo...")
        await agent.run_demo(num_tweets=3, delay_minutes=0.5)  # 30 seconds
        
    else:
        print("👋 Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()