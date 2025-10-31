#!/usr/bin/env python3
"""
Twitter API Diagnostic Tool

Tests what endpoints are actually available with your credentials.
"""

import os
import sys
import tweepy
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


def test_twitter_api():
    """Test what Twitter API endpoints are available."""
    print("🔍 TWITTER API DIAGNOSTIC TOOL")
    print("=" * 40)
    
    try:
        # Create OAuth1 authentication
        auth = tweepy.OAuth1UserHandler(
            os.getenv('TWITTER_API_KEY'),
            os.getenv('TWITTER_API_SECRET'),
            os.getenv('TWITTER_ACCESS_TOKEN'),
            os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        
        # Create API v1.1 client
        api = tweepy.API(auth, wait_on_rate_limit=True)
        
        print("🔐 Testing authentication...")
        
        # Test 1: Basic authentication
        try:
            me = api.verify_credentials()
            if me:
                print(f"✅ Authentication successful: @{me.screen_name}")
                print(f"   User ID: {me.id}")
                print(f"   Followers: {me.followers_count}")
                print(f"   Created: {me.created_at}")
            else:
                print("❌ Authentication failed")
                return
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return
        
        # Test 2: Rate limit status
        try:
            print("\n📊 Checking rate limits...")
            limits = api.get_rate_limit_status()
            
            # Check key endpoints
            endpoints_to_check = [
                ('statuses', '/statuses/update'),
                ('search', '/search/tweets'),
                ('statuses', '/statuses/mentions_timeline'),
                ('statuses', '/statuses/user_timeline'),
            ]
            
            for resource, endpoint in endpoints_to_check:
                if resource in limits['resources'] and endpoint in limits['resources'][resource]:
                    limit_info = limits['resources'][resource][endpoint]
                    remaining = limit_info['remaining']
                    limit_total = limit_info['limit']
                    print(f"   {endpoint}: {remaining}/{limit_total} requests remaining")
                else:
                    print(f"   {endpoint}: Not available")
                    
        except Exception as e:
            print(f"⚠️  Rate limit check error: {e}")
        
        # Test 3: Search tweets (should work with Standard v1.1)
        try:
            print(f"\n🔍 Testing search tweets...")
            results = api.search_tweets(q="twitter", count=1, tweet_mode="extended")
            if results:
                print(f"✅ Search tweets works! Found {len(results)} result(s)")
                if results:
                    tweet = results[0]
                    print(f"   Sample: @{tweet.user.screen_name}: {tweet.full_text[:50]}...")
            else:
                print("⚠️  Search returned no results")
        except Exception as e:
            print(f"❌ Search tweets error: {e}")
        
        # Test 4: Get user timeline (should work)
        try:
            print(f"\n📝 Testing user timeline...")
            timeline = api.user_timeline(count=1, tweet_mode="extended")
            if timeline:
                print(f"✅ User timeline works! Found {len(timeline)} tweet(s)")
                if timeline:
                    tweet = timeline[0]
                    print(f"   Your latest: {tweet.full_text[:50]}...")
            else:
                print("⚠️  Timeline returned no results")
        except Exception as e:
            print(f"❌ User timeline error: {e}")
        
        # Test 5: Post tweet (the crucial test)
        try:
            print(f"\n💬 Testing tweet posting...")
            test_message = f"api diagnostic test {datetime.now().strftime('%H:%M:%S')}"
            
            # Ask before posting
            response = input(f"Post test tweet: '{test_message}'? (y/n): ")
            if response.lower() == 'y':
                tweet = api.update_status(test_message)
                print(f"✅ Tweeting works! Posted tweet ID: {tweet.id}")
                print(f"🔗 https://twitter.com/{me.screen_name}/status/{tweet.id}")
                
                # Clean up - delete the test tweet
                cleanup = input("Delete test tweet? (y/n): ")
                if cleanup.lower() == 'y':
                    api.destroy_status(tweet.id)
                    print("🗑️  Test tweet deleted")
            else:
                print("⏭️  Skipped tweet posting test")
        except Exception as e:
            print(f"❌ Tweet posting error: {e}")
        
        # Test 6: Mentions timeline (likely to fail)
        try:
            print(f"\n📬 Testing mentions timeline...")
            mentions = api.mentions_timeline(count=1, tweet_mode="extended")
            if mentions:
                print(f"✅ Mentions timeline works! Found {len(mentions)} mention(s)")
            else:
                print("📭 No mentions found")
        except Exception as e:
            print(f"❌ Mentions timeline error: {e}")
        
        print(f"\n" + "=" * 40)
        print(f"🎯 DIAGNOSIS COMPLETE")
        print(f"💡 Based on results above:")
        print(f"   - If search works: We can find mentions by searching")
        print(f"   - If posting works: We can reply to mentions")
        print(f"   - If mentions fails: Expected with Standard v1.1")
        
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_twitter_api()