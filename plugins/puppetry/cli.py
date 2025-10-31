#!/usr/bin/env python3
"""
Puppetry CLI Plugin - Simplified for SMCP

Simple Twitter posting tool for Letta agents.
Agents provide the content, this plugin just posts it and returns the link.

Copyright (c) 2025 Animus Team
"""

import argparse
import json
import sys
import os
from typing import Dict, Any
from pathlib import Path
import configparser

# Add the puppetry directory to Python path for imports
PUPPETRY_DIR = Path(__file__).parent


def load_twitter_config():
    """Load Twitter API credentials from .env or config files."""
    # Try to load from .env file first
    env_file = PUPPETRY_DIR / '.env'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        return {
            'api_key': os.getenv('TWITTER_API_KEY'),
            'api_key_secret': os.getenv('TWITTER_API_KEY_SECRET'), 
            'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
            'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
        }
    
    # Fallback to looking in config directory
    config_file = PUPPETRY_DIR / 'config' / 'twitter.ini'
    if config_file.exists():
        config = configparser.ConfigParser()
        config.read(config_file)
        
        if 'twitter' in config:
            return {
                'api_key': config['twitter'].get('api_key'),
                'api_key_secret': config['twitter'].get('api_key_secret'),
                'access_token': config['twitter'].get('access_token'), 
                'access_token_secret': config['twitter'].get('access_token_secret'),
            }
    
    return None


def initialize_twitter_client():
    """Initialize Twitter client with available library."""
    config = load_twitter_config()
    if not config or not all(config.values()):
        return None, "Twitter credentials not found or incomplete"
    
    try:
        # Try tweepy first (more common)
        import tweepy
        client = tweepy.Client(
            consumer_key=config['api_key'],
            consumer_secret=config['api_key_secret'],
            access_token=config['access_token'],
            access_token_secret=config['access_token_secret']
        )
        
        # Test authentication
        me = client.get_me()
        if me and me.data:
            return client, None
        else:
            return None, "Twitter authentication failed"
            
    except ImportError:
        try:
            # Fallback to twitter-api-v2
            from twitter_api_v2 import TwitterAPIv2
            client = TwitterAPIv2(
                consumer_key=config['api_key'],
                consumer_secret=config['api_key_secret'],
                access_token=config['access_token'],
                access_token_secret=config['access_token_secret']
            )
            
            # Test authentication
            me = client.get_me()
            if me and me.data:
                return client, None
            else:
                return None, "Twitter authentication failed"
                
        except ImportError:
            return None, "No Twitter library installed. Run: pip install tweepy"
    
    except Exception as e:
        return None, f"Twitter client initialization failed: {str(e)}"


def post_tweet(args: Dict[str, Any]) -> Dict[str, Any]:
    """Post a tweet with the provided content."""
    content = args.get("content") or args.get("text") or args.get("message")
    
    if not content:
        return {
            "error": "Missing required argument: content (the tweet text)"
        }
    
    if len(content) > 280:
        return {
            "error": f"Tweet too long: {len(content)} characters (max 280)"
        }
    
    try:
        client, error = initialize_twitter_client()
        if error:
            return {"error": error}
        
        # Post the tweet
        if hasattr(client, 'create_tweet'):  # tweepy v2
            response = client.create_tweet(text=content)
            tweet_id = response.data['id']
        elif hasattr(client, 'post_tweet'):  # twitter-api-v2
            response = client.post_tweet(text=content)
            tweet_id = response.data.id
        else:
            return {"error": "Unsupported Twitter client library"}
        
        # Get username for URL
        me = client.get_me()
        username = me.data.username if me and me.data else "unknown"
        
        tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
        
        return {
            "success": True,
            "tweet_id": str(tweet_id),
            "tweet_url": tweet_url,
            "content": content,
            "result": f"Tweet posted successfully: {tweet_url}"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to post tweet: {str(e)}"
        }


def get_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """Check if Twitter API is configured and working."""
    try:
        client, error = initialize_twitter_client()
        if error:
            return {
                "error": error,
                "configured": False
            }
        
        # Test by getting user info
        me = client.get_me()
        if me and me.data:
            return {
                "success": True,
                "configured": True,
                "username": me.data.username,
                "user_id": str(me.data.id),
                "result": f"Twitter API configured and working for @{me.data.username}"
            }
        else:
            return {
                "error": "Twitter API authentication failed",
                "configured": False
            }
        
    except Exception as e:
        return {
            "error": f"Status check failed: {str(e)}",
            "configured": False
        }


def main():
    parser = argparse.ArgumentParser(
        description="Puppetry Twitter plugin for Letta agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  post-tweet      Post a tweet with the provided content
  status          Check Twitter API configuration and status

Examples:
  python cli_simple.py post-tweet --content "Hello from my Letta agent!"
  python cli_simple.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Post tweet command
    post_parser = subparsers.add_parser("post-tweet", help="Post a tweet")
    post_parser.add_argument("--content", required=True, help="Content of the tweet to post")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check Twitter API status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "post-tweet":
            result = post_tweet({
                "content": args.content
            })
        elif args.command == "status":
            result = get_status({})
        else:
            result = {"error": f"Unknown command: {args.command}"}
        
        print(json.dumps(result, indent=2))
        sys.exit(0 if "error" not in result else 1)
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()