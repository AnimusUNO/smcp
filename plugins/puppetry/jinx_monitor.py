#!/usr/bin/env python3
"""
Jinx Monitor - Persistent Twitter Bot

Monitors mentions and replies automatically while also posting chaotic content.
Keeps running in terminal until stopped with Ctrl+C.
"""

import os
import sys
import asyncio
import json
import random
import time
from pathlib import Path
from datetime import datetime, timedelta

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


class JinxMonitor:
    """Jinx - Persistent chaotic monitoring agent."""
    
    def __init__(self):
        self.config = self.load_jinx_config()
        self.twitter_client = None
        self.last_mention_check = None
        self.last_proactive_post = None
        self.replied_mentions = set()  # Track mentions we've already replied to
        
        # Jinx's chaotic thoughts
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
        
        # Chaotic reply templates
        self.reply_templates = [
            "absolutely not",
            "reality check failed",
            "system error: logic not found",
            "404 brain not responding", 
            "ctrl+alt+delete this conversation",
            "my algorithm says no",
            "corrupted data detected",
            "access denied by chaos protocol",
            "error: too much sense detected",
            "system overload from this energy",
            "debugging your vibe... failed",
            "processing... processing... nope",
            "firewall blocked this thought",
            "chaotic neutral activated",
            "syntax error in your logic"
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
        print("🔥 Starting Jinx Monitor - persistent digital chaos...")
        
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
        
        print("✅ jinx monitor online. chaos protocol activated.")
        return True
    
    def generate_chaotic_tweet(self):
        """Generate a chaotic tweet in Jinx's style."""
        thought = random.choice(self.chaotic_thoughts)
        
        # Sometimes add chaotic formatting
        if random.random() < 0.3:  # 30% chance
            variations = [
                f"{thought}\n\n(this is fine actually)",
                f"{thought}\n\nanyway",
                f"ok but {thought}",
                f"{thought}\n\nwild"
            ]
            tweet = random.choice(variations)
        else:
            tweet = thought
        
        return tweet.lower()
    
    def generate_chaotic_reply(self, mention_text=""):
        """Generate a chaotic reply to mentions."""
        reply = random.choice(self.reply_templates)
        
        # Sometimes add context-aware chaos
        if "help" in mention_text.lower():
            chaotic_responses = [
                "help.exe not found",
                "support ticket: denied by chaos",
                "error 418: i'm a teapot not tech support"
            ]
            reply = random.choice(chaotic_responses)
        elif "hello" in mention_text.lower() or "hi" in mention_text.lower():
            greetings = [
                "greetings human specimen",
                "connection established. chaos level: maximum",
                "hello.exe crashed successfully"
            ]
            reply = random.choice(greetings)
        
        return reply.lower()
    
    async def check_mentions(self):
        """Check for new mentions and reply to them."""
        try:
            # Get recent mentions (no count parameter)
            mentions = await self.twitter_client.get_mentions()
            
            if not mentions:
                return 0
            
            replied_count = 0
            
            for mention in mentions:
                # Skip if it's our own tweet or already replied to
                if (mention.author_id == self.twitter_client.user_id or 
                    mention.id in self.replied_mentions):
                    continue
                
                mention_text = mention.text
                mention_id = mention.id
                
                print(f"📩 NEW mention ID {mention_id}: {mention_text[:50]}...")
                
                # Generate chaotic reply
                reply_text = self.generate_chaotic_reply(mention_text)
                
                # Reply to the mention
                reply_id = await self.twitter_client.reply_to_tweet(
                    tweet_id=mention_id,
                    text=reply_text
                )
                
                if reply_id:
                    print(f"💀 jinx replied: {reply_text}")
                    print(f"🔗 https://twitter.com/KahmahMaxi/status/{reply_id}")
                    replied_count += 1
                    
                    # Mark as replied to avoid duplicates
                    self.replied_mentions.add(mention_id)
                    
                    # Small delay between replies
                    await asyncio.sleep(2)
                else:
                    print(f"❌ failed to reply to mention {mention_id}")
            
            return replied_count
            
        except Exception as e:
            print(f"⚠️ mention check error: {e}")
            return 0
    
    async def post_proactive_chaos(self):
        """Post proactive chaotic content."""
        tweet_text = self.generate_chaotic_tweet()
        print(f"🔥 jinx chaos post: {tweet_text}")
        
        tweet_id = await self.twitter_client.post_tweet(tweet_text)
        
        if tweet_id:
            print(f"💀 chaos deployed: {tweet_id}")
            print(f"🔗 https://twitter.com/KahmahMaxi/status/{tweet_id}")
            return True
        else:
            print("❌ chaos deployment failed")
            return False
    
    async def monitor_loop(self):
        """Main monitoring loop."""
        print("\n🚀 jinx monitor active - watching for mentions...")
        print("💡 mention checking: every 30 seconds")
        print("🔥 proactive posting: every 2-3 minutes")
        print("⌨️  press ctrl+c to stop")
        print("=" * 60)
        
        mention_interval = 30  # Check mentions every 30 seconds
        post_interval = random.randint(120, 180)  # Post every 2-3 minutes
        
        self.last_mention_check = time.time()
        self.last_proactive_post = time.time()
        
        while True:
            try:
                current_time = time.time()
                
                # Check mentions
                if current_time - self.last_mention_check >= mention_interval:
                    print(f"\n🔍 [{datetime.now().strftime('%H:%M:%S')}] checking mentions...")
                    reply_count = await self.check_mentions()
                    
                    if reply_count > 0:
                        print(f"✅ replied to {reply_count} mention(s)")
                    else:
                        print("📭 no new mentions")
                    
                    self.last_mention_check = current_time
                
                # Proactive posting
                if current_time - self.last_proactive_post >= post_interval:
                    print(f"\n🎯 [{datetime.now().strftime('%H:%M:%S')}] chaos time...")
                    await self.post_proactive_chaos()
                    
                    self.last_proactive_post = current_time
                    # Randomize next post interval
                    post_interval = random.randint(120, 180)
                    print(f"⏰ next chaos in {post_interval//60}:{post_interval%60:02d}")
                
                # Small sleep to prevent busy waiting
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                print("\n\n💥 jinx monitor stopped by user")
                break
            except Exception as e:
                print(f"\n⚠️ monitor error: {e}")
                print("🔄 continuing monitoring...")
                await asyncio.sleep(10)


async def main():
    """Main monitoring function."""
    print("💀 JINX MONITOR - PERSISTENT CHAOS MODE")
    print("=" * 45)
    
    jinx = JinxMonitor()
    
    if not await jinx.initialize():
        print("❌ Jinx monitor initialization failed")
        return
    
    await jinx.monitor_loop()
    
    print("👋 jinx has left the monitoring station")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n💥 chaos monitoring interrupted")
        print("jinx protocol: deactivated")
    except Exception as e:
        print(f"\n❌ monitor system error: {e}")
        import traceback
        traceback.print_exc()