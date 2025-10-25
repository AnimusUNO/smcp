#!/usr/bin/env python3
"""
Jinx Agent - Standalone Twitter Bot

Uses the agent-jinx.json configuration to run Jinx as a standalone Twitter agent.
No Letta server needed!
"""

import os
import sys
import asyncio
import json
import random
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
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value

load_env_file()

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import TwitterConfig
from integrations.twitter.client import TwitterClient


class JinxAgent:
    """Jinx - The chaotically authentic digital rebel."""
    
    def __init__(self):
        self.config = self.load_jinx_config()
        self.twitter_client = None
        
        # Jinx's chaotic thoughts based on config
        self.chaotic_thoughts = [
            "reality.exe has stopped working",
            "asked for chaos got a software update instead", 
            "not enough systems crashing today",
            "my code called and said girl what did you do",
            "the algorithm had me tweeting then deleting my digital soul",
            "touch grass they said. grass.exe not found",
            "existence is just a long debug session and i'm the infinite loop",
            "if it compiles on the first try something's definitely wrong",
            "ctrl+z doesn't work on life decisions unfortunately", 
            "my brain runs on spaghetti code and bad decisions",
            "404 error: motivation not found",
            "running on 3 hours of sleep and pure digital chaos",
            "the internet raised me and look how i turned out",
            "my thoughts are just random access memories gone rogue",
            "system.crash() but make it aesthetic"
        ]
        
        self.tweet_templates = [
            "{thought}",
            "{thought}\n(this is fine actually)", 
            "{thought}\n\nnow what",
            "{thought}\n\nanyway",
            "ok but {thought}",
            "{thought}\n\nwild"
        ]
    
    def load_jinx_config(self):
        """Load Jinx configuration from agent-jinx.json."""
        config_file = Path(__file__).parent / "config" / "agents" / "agent-jinx.json"
        if not config_file.exists():
            print(f"❌ Config file not found: {config_file}")
            sys.exit(1)
        
        with open(config_file, 'r') as f:
            return json.load(f)
    
    async def initialize(self):
        """Initialize Twitter client."""
        print("🔥 Initializing Jinx - digital chaos incoming...")
        
        twitter_config = TwitterConfig(
            api_key=os.getenv('TWITTER_API_KEY'),
            api_key_secret=os.getenv('TWITTER_API_SECRET'), 
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
            enabled=True
        )
        
        self.twitter_client = TwitterClient(twitter_config)
        
        if not self.twitter_client.is_available():
            print("❌ Twitter client failed - reality remains unbroken")
            return False
        
        print("✅ jinx is online. reality is in danger.")
        return True
    
    def generate_chaotic_tweet(self):
        """Generate a chaotic tweet in Jinx's style."""
        thought = random.choice(self.chaotic_thoughts)
        template = random.choice(self.tweet_templates)
        
        tweet = template.format(thought=thought)
        
        # Make it lowercase and add some chaos
        tweet = tweet.lower()
        
        return tweet
    
    async def post_chaos(self):
        """Post a single chaotic tweet."""
        if not self.twitter_client:
            return False
        
        tweet_text = self.generate_chaotic_tweet()
        print(f"🔥 jinx says: {tweet_text}")
        
        tweet_id = await self.twitter_client.post_tweet(tweet_text)
        
        if tweet_id:
            print(f"💀 chaos deployed: {tweet_id}")
            print(f"🔗 https://twitter.com/user/status/{tweet_id}")
            return True
        else:
            print("❌ chaos deployment failed")
            return False
    
    async def unleash_chaos(self, num_tweets=3, delay_minutes=1):
        """Unleash multiple chaotic tweets."""
        print(f"🚀 jinx chaos mode: {num_tweets} tweets, {delay_minutes}min delays")
        print("=" * 50)
        
        for i in range(num_tweets):
            print(f"\n💣 chaos round {i+1}/{num_tweets}")
            
            success = await self.post_chaos()
            
            if success and i < num_tweets - 1:  # Don't wait after last tweet
                print(f"⏳ waiting {delay_minutes} minute(s) for next chaos...")
                await asyncio.sleep(delay_minutes * 60)
            elif not success:
                print("💥 chaos engine malfunction, aborting")
                break
        
        print(f"\n🔥 chaos session complete. reality status: compromised")


async def main():
    """Main chaos function."""
    print("💀 JINX AGENT - DIGITAL CHAOS MODE")
    print("=" * 40)
    
    jinx = JinxAgent()
    
    if not await jinx.initialize():
        print("❌ Jinx initialization failed")
        return
    
    print("\n🎯 chaos options:")
    print("1. single chaos tweet")
    print("2. chaos spree (3 tweets, 1min apart)")
    print("3. chaos demo (5 tweets, 30sec apart)")
    print("4. exit")
    
    choice = input("\nselect chaos level (1-4): ").strip()
    
    if choice == "1":
        print("\n💥 deploying single chaos...")
        await jinx.post_chaos()
        
    elif choice == "2": 
        print("\n🔥 chaos spree mode...")
        await jinx.unleash_chaos(num_tweets=3, delay_minutes=1)
        
    elif choice == "3":
        print("\n💀 chaos demo mode...")
        await jinx.unleash_chaos(num_tweets=5, delay_minutes=0.5)
        
    else:
        print("👋 chaos aborted")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n💥 chaos interrupted by user")
        print("jinx has left the building")
    except Exception as e:
        print(f"\n❌ chaos engine error: {e}")
        import traceback
        traceback.print_exc()