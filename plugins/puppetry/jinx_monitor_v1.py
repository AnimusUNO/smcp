#!/usr/bin/env python3
"""
Jinx Monitor v1.1 - Twitter API v1.1 Compatible

Uses Twitter API v1.1 for mention monitoring (works with your current credentials).
"""

import os
import sys
import asyncio
import json
import random
import time
import tweepy
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


class JinxMonitorV1:
    """Jinx - Persistent chaotic monitoring agent using Twitter API v1.1."""
    
    def __init__(self):
        self.config = self.load_jinx_config()
        self.api = None
        self.client = None
        self.username = None
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
    
    def initialize(self):
        """Initialize Twitter API v1.1 client."""
        print("🔥 Starting Jinx Monitor v1.1 - compatible chaos...")
        
        try:
            # Create OAuth1 authentication
            auth = tweepy.OAuth1UserHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET'),
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            
            # Create API v1.1 client
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Test authentication
            me = self.api.verify_credentials()
            if me:
                self.username = me.screen_name
                print(f"✅ Twitter API v1.1 authenticated: @{self.username}")
                
                # Also create v2 client for posting (it might work for posting)
                try:
                    self.client = tweepy.Client(
                        consumer_key=os.getenv('TWITTER_API_KEY'),
                        consumer_secret=os.getenv('TWITTER_API_SECRET'),
                        access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                        access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
                    )
                    print("✅ v2 client also available for posting")
                except:
                    print("⚠️ v2 client failed, using v1.1 only")
                    self.client = None
                
                return True
            else:
                print("❌ Authentication failed")
                return False
                
        except Exception as e:
            print(f"❌ Twitter initialization error: {e}")
            return False
    
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
    
    def check_mentions(self):
        """Check for new mentions using Twitter API v1.1."""
        try:
            # Get mentions using v1.1 API
            mentions = self.api.mentions_timeline(count=10, tweet_mode='extended')
            
            if not mentions:
                return 0
            
            replied_count = 0
            
            for mention in mentions:
                # Skip if already replied to this mention
                if mention.id in self.replied_mentions:
                    continue
                
                # Skip if it's our own tweet
                if mention.user.screen_name.lower() == self.username.lower():
                    continue
                
                mention_text = mention.full_text
                mention_id = mention.id
                mention_user = mention.user.screen_name
                
                print(f"📩 NEW mention from @{mention_user}: {mention_text[:50]}...")
                
                # Generate chaotic reply
                reply_text = self.generate_chaotic_reply(mention_text)
                
                try:
                    # Try v2 client first for replying
                    if self.client:
                        response = self.client.create_tweet(
                            text=f"@{mention_user} {reply_text}",
                            in_reply_to_tweet_id=mention_id
                        )
                        if response.data:
                            reply_id = response.data['id']
                            print(f"💀 jinx replied (v2): {reply_text}")
                            print(f"🔗 https://twitter.com/{self.username}/status/{reply_id}")
                            replied_count += 1
                            self.replied_mentions.add(mention_id)
                        else:
                            raise Exception("v2 reply failed")
                    else:
                        # Fallback to v1.1 API
                        reply_tweet = self.api.update_status(
                            status=f"@{mention_user} {reply_text}",
                            in_reply_to_status_id=mention_id
                        )
                        print(f"💀 jinx replied (v1.1): {reply_text}")
                        print(f"🔗 https://twitter.com/{self.username}/status/{reply_tweet.id}")
                        replied_count += 1
                        self.replied_mentions.add(mention_id)
                        
                except Exception as reply_error:
                    print(f"❌ failed to reply to @{mention_user}: {reply_error}")
                
                # Small delay between replies
                time.sleep(2)
            
            return replied_count
            
        except Exception as e:
            print(f"⚠️ mention check error: {e}")
            return 0
    
    def post_proactive_chaos(self):
        """Post proactive chaotic content."""
        tweet_text = self.generate_chaotic_tweet()
        print(f"🔥 jinx chaos post: {tweet_text}")
        
        try:
            # Try v2 client first
            if self.client:
                response = self.client.create_tweet(text=tweet_text)
                if response.data:
                    tweet_id = response.data['id']
                    print(f"💀 chaos deployed (v2): {tweet_id}")
                    print(f"🔗 https://twitter.com/{self.username}/status/{tweet_id}")
                    return True
                else:
                    raise Exception("v2 post failed")
            else:
                # Fallback to v1.1
                tweet = self.api.update_status(tweet_text)
                print(f"💀 chaos deployed (v1.1): {tweet.id}")
                print(f"🔗 https://twitter.com/{self.username}/status/{tweet.id}")
                return True
                
        except Exception as e:
            print(f"❌ chaos deployment failed: {e}")
            return False
    
    def monitor_loop(self):
        """Main monitoring loop."""
        print("\n🚀 jinx monitor v1.1 active - watching for mentions...")
        print("💡 mention checking: every 60 seconds (v1.1 rate limits)")
        print("🔥 proactive posting: every 3-4 minutes")
        print("⌨️  press ctrl+c to stop")
        print("=" * 60)
        
        mention_interval = 60  # Check mentions every 60 seconds (v1.1 is more limited)
        post_interval = random.randint(180, 240)  # Post every 3-4 minutes
        
        self.last_mention_check = time.time()
        self.last_proactive_post = time.time()
        
        while True:
            try:
                current_time = time.time()
                
                # Check mentions
                if current_time - self.last_mention_check >= mention_interval:
                    print(f"\n🔍 [{datetime.now().strftime('%H:%M:%S')}] checking mentions...")
                    reply_count = self.check_mentions()
                    
                    if reply_count > 0:
                        print(f"✅ replied to {reply_count} mention(s)")
                    else:
                        print("📭 no new mentions")
                    
                    self.last_mention_check = current_time
                
                # Proactive posting
                if current_time - self.last_proactive_post >= post_interval:
                    print(f"\n🎯 [{datetime.now().strftime('%H:%M:%S')}] chaos time...")
                    self.post_proactive_chaos()
                    
                    self.last_proactive_post = current_time
                    # Randomize next post interval
                    post_interval = random.randint(180, 240)
                    print(f"⏰ next chaos in {post_interval//60}:{post_interval%60:02d}")
                
                # Small sleep to prevent busy waiting
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("\n\n💥 jinx monitor stopped by user")
                break
            except Exception as e:
                print(f"\n⚠️ monitor error: {e}")
                print("🔄 continuing monitoring...")
                time.sleep(30)


def main():
    """Main monitoring function."""
    print("💀 JINX MONITOR v1.1 - API COMPATIBLE MODE")
    print("=" * 48)
    
    jinx = JinxMonitorV1()
    
    if not jinx.initialize():
        print("❌ Jinx monitor initialization failed")
        return
    
    jinx.monitor_loop()
    
    print("👋 jinx has left the monitoring station")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n💥 chaos monitoring interrupted")
        print("jinx protocol: deactivated")
    except Exception as e:
        print(f"\n❌ monitor system error: {e}")
        import traceback
        traceback.print_exc()