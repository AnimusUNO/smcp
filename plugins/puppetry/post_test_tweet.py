#!/usr/bin/env python3
"""
Post a single test tweet to verify everything is working
"""

import os
import sys
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

from core.config_manager import TwitterConfig
from integrations.twitter.client import TwitterClient


async def post_test_tweet():
    """Post a single test tweet."""
    print("🐦 Posting Test Tweet")
    print("=" * 30)
    
    # Create Twitter configuration
    twitter_config = TwitterConfig(
        api_key=os.getenv('TWITTER_API_KEY'),
        api_key_secret=os.getenv('TWITTER_API_SECRET'),
        access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
        enabled=True
    )
    
    # Initialize Twitter client
    print("🔧 Initializing Twitter client...")
    twitter_client = TwitterClient(twitter_config)
    
    if not twitter_client.is_available():
        print("❌ Twitter client failed to initialize")
        return
    
    print("✅ Twitter client ready")
    
    # Post the test tweet
    test_tweet = "🤖 Hello from the Puppetry system! Testing AI agent Twitter integration. #AI #TwitterBot #Animus"
    print(f"\n📝 Posting tweet: {test_tweet}")
    
    tweet_id = await twitter_client.post_tweet(test_tweet)
    
    if tweet_id:
        print(f"🎉 Tweet posted successfully!")
        print(f"📋 Tweet ID: {tweet_id}")
        print(f"🔗 View at: https://twitter.com/user/status/{tweet_id}")
    else:
        print("❌ Failed to post tweet")


if __name__ == "__main__":
    # Confirm before posting
    print("⚠️  This will post a real tweet to your Twitter account!")
    confirm = input("Type 'yes' to continue: ")
    
    if confirm.lower() == 'yes':
        asyncio.run(post_test_tweet())
    else:
        print("❌ Tweet posting cancelled")