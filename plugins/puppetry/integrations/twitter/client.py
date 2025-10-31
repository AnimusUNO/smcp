"""
Twitter Integration

Handles Twitter API interactions for Letta agents.
Ported from Puppet Engine to work with Animus architecture.
"""

import asyncio
import time
import random
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    from twitter_api_v2 import TwitterAPIv2
    TWITTER_LIB = "twitter-api-v2"
except ImportError:
    try:
        import tweepy
        TwitterAPIv2 = None  # Will use tweepy instead
        TWITTER_LIB = "tweepy"
    except ImportError:
        print("Warning: No Twitter library available. Install with: pip install tweepy or pip install twitter-api-v2")
        TwitterAPIv2 = None
        tweepy = None
        TWITTER_LIB = None

import sys
from pathlib import Path

# Add puppetry root to path for imports
PUPPETRY_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PUPPETRY_ROOT))

from core.agent_bridge import LettaAgentBridge
from core.config_manager import ConfigManager, TwitterConfig


@dataclass
class Tweet:
    """Represents a tweet."""
    id: str
    text: str
    author_id: str
    created_at: str
    reply_to_id: Optional[str] = None
    is_mention: bool = False


class TwitterClient:
    """Twitter API client for a specific agent."""
    
    def __init__(self, config: TwitterConfig):
        self.config = config
        self.client = None
        self.user_id = None
        self.lib_type = None
        
        if config.enabled:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Twitter client with available library."""
        try:
            # Try twitter-api-v2 first
            if TwitterAPIv2:
                self.client = TwitterAPIv2(
                    consumer_key=self.config.api_key,
                    consumer_secret=self.config.api_key_secret,
                    access_token=self.config.access_token,
                    access_token_secret=self.config.access_token_secret
                )
                me = self.client.get_me()
                if me and me.data:
                    self.user_id = me.data.id
                    self.lib_type = "twitter-api-v2"
                    print(f"Twitter client (twitter-api-v2) initialized for user ID: {self.user_id}")
                    return
            
            # Fallback to tweepy
            elif tweepy:
                # Create tweepy client with OAuth 1.0a
                self.client = tweepy.Client(
                    consumer_key=self.config.api_key,
                    consumer_secret=self.config.api_key_secret,
                    access_token=self.config.access_token,
                    access_token_secret=self.config.access_token_secret
                )
                
                # Test authentication and get user info
                me = self.client.get_me()
                if me and me.data:
                    self.user_id = me.data.id
                    self.lib_type = "tweepy"
                    print(f"Twitter client (tweepy) initialized for user: @{me.data.username}")
                    return
            
            print("No suitable Twitter library available")
            self.client = None
            
        except Exception as e:
            print(f"Failed to initialize Twitter client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Twitter client is available."""
        return self.client is not None
    
    async def post_tweet(self, text: str) -> Optional[str]:
        """Post a tweet."""
        if not self.client:
            return None
            
        try:
            if self.lib_type == "twitter-api-v2":
                response = self.client.create_tweet(text=text)
                if response and response.data:
                    return response.data.get('id')
            elif self.lib_type == "tweepy":
                response = self.client.create_tweet(text=text)
                if response and response.data:
                    return response.data['id']
            return None
            
        except Exception as e:
            print(f"Failed to post tweet: {e}")
            return None
    
    async def reply_to_tweet(self, tweet_id: str, text: str) -> Optional[str]:
        """Reply to a tweet."""
        if not self.client:
            return None
            
        try:
            if self.lib_type == "twitter-api-v2":
                response = self.client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=tweet_id
                )
                if response and response.data:
                    return response.data.get('id')
            elif self.lib_type == "tweepy":
                response = self.client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=tweet_id
                )
                if response and response.data:
                    return response.data['id']
            return None
            
        except Exception as e:
            print(f"Failed to reply to tweet {tweet_id}: {e}")
            return None
    
    async def get_mentions(self, since_id: Optional[str] = None) -> List[Tweet]:
        """Get mentions for the authenticated user."""
        if not self.client or not self.user_id:
            return []
            
        try:
            params = {
                'tweet.fields': 'created_at,author_id,in_reply_to_user_id,conversation_id',
                'max_results': 10
            }
            
            if since_id:
                params['since_id'] = since_id
            
            response = self.client.get_users_mentions(
                id=self.user_id,
                **params
            )
            
            mentions = []
            if response and response.data:
                for tweet in response.data:
                    mentions.append(Tweet(
                        id=tweet.id,
                        text=tweet.text,
                        author_id=tweet.author_id,
                        created_at=tweet.created_at,
                        reply_to_id=getattr(tweet, 'in_reply_to_user_id', None),
                        is_mention=True
                    ))
            
            return mentions
            
        except Exception as e:
            print(f"Failed to get mentions: {e}")
            return []


class TwitterIntegration:
    """Main Twitter integration for Puppetry."""
    
    def __init__(self):
        self.agent_bridge = LettaAgentBridge()
        self.config_manager = ConfigManager()
        self.active_clients: Dict[str, TwitterClient] = {}
        self.mention_tracking: Dict[str, str] = {}  # agent_id -> last_mention_id
        
        # Behavioral settings
        self.posting_intervals = {
            "low": (3600, 7200),      # 1-2 hours
            "moderate": (1800, 3600),  # 30min-1hour 
            "high": (900, 1800)        # 15-30min
        }
        
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    def is_available(self) -> bool:
        """Check if Twitter integration is available."""
        return TwitterAPIv2 is not None
    
    def start_for_agent(self, agent_id: str, config) -> Dict[str, Any]:
        """Start Twitter integration for a specific agent."""
        try:
            # Get agent configuration
            agent_config = self.config_manager.get_agent_config(agent_id)
            
            if not agent_config.twitter or not agent_config.twitter.enabled:
                return {"success": False, "error": "Twitter not configured or disabled"}
            
            # Create Twitter client
            client = TwitterClient(agent_config.twitter)
            
            if not client.is_available():
                return {"success": False, "error": "Failed to initialize Twitter client"}
            
            # Store client
            self.active_clients[agent_id] = client
            
            # Start behavior tasks
            if not self._running:
                self._running = True
                self._start_background_tasks()
            
            return {"success": True, "message": f"Twitter started for agent {agent_id}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop_for_agent(self, agent_id: str):
        """Stop Twitter integration for an agent."""
        if agent_id in self.active_clients:
            del self.active_clients[agent_id]
        
        if agent_id in self.mention_tracking:
            del self.mention_tracking[agent_id]
        
        # Stop background tasks if no active clients
        if not self.active_clients and self._running:
            self._stop_background_tasks()
    
    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        self._tasks = [
            asyncio.create_task(self._mention_monitor()),
            asyncio.create_task(self._posting_scheduler())
        ]
    
    def _stop_background_tasks(self):
        """Stop background tasks."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks = []
    
    async def _mention_monitor(self):
        """Monitor mentions for all active agents."""
        while self._running:
            try:
                for agent_id, client in self.active_clients.items():
                    await self._check_mentions(agent_id, client)
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"Error in mention monitor: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_mentions(self, agent_id: str, client: TwitterClient):
        """Check mentions for a specific agent."""
        try:
            since_id = self.mention_tracking.get(agent_id)
            mentions = await client.get_mentions(since_id=since_id)
            
            if mentions:
                # Update tracking
                self.mention_tracking[agent_id] = mentions[0].id
                
                # Process each mention
                for mention in mentions:
                    await self._process_mention(agent_id, mention)
            
        except Exception as e:
            print(f"Error checking mentions for agent {agent_id}: {e}")
    
    async def _process_mention(self, agent_id: str, mention: Tweet):
        """Process a single mention."""
        try:
            # Send mention to Letta agent for response
            prompt = f"You've been mentioned on Twitter: \"{mention.text}\". Please respond appropriately."
            
            response = self.agent_bridge.send_message(agent_id, prompt)
            
            if response:
                # Clean up response for Twitter (remove quotes, trim length)
                twitter_response = self._prepare_twitter_response(response)
                
                # Reply to the mention
                client = self.active_clients.get(agent_id)
                if client:
                    await client.reply_to_tweet(mention.id, twitter_response)
                    print(f"Replied to mention for agent {agent_id}")
            
        except Exception as e:
            print(f"Error processing mention for agent {agent_id}: {e}")
    
    def _prepare_twitter_response(self, response: str) -> str:
        """Prepare Letta response for Twitter posting."""
        # Remove quotes if wrapped
        if response.startswith('"') and response.endswith('"'):
            response = response[1:-1]
        
        # Truncate to Twitter limit (280 chars, leave some buffer)
        if len(response) > 270:
            response = response[:270] + "..."
        
        return response
    
    async def _posting_scheduler(self):
        """Schedule proactive posts for agents."""
        while self._running:
            try:
                for agent_id in self.active_clients.keys():
                    await self._maybe_post_proactive(agent_id)
                
                # Check every 10 minutes
                await asyncio.sleep(600)
                
            except Exception as e:
                print(f"Error in posting scheduler: {e}")
                await asyncio.sleep(900)  # Wait longer on error
    
    async def _maybe_post_proactive(self, agent_id: str):
        """Maybe post a proactive tweet for an agent."""
        try:
            # Get agent configuration
            agent_config = self.config_manager.get_agent_config(agent_id)
            
            if not agent_config.behavior.proactive_posting:
                return
            
            # Check posting frequency
            frequency = agent_config.behavior.posting_frequency
            min_interval, max_interval = self.posting_intervals.get(frequency, (1800, 3600))
            
            # Random chance based on frequency
            if random.random() > 0.1:  # 10% chance per check
                return
            
            # Generate proactive content
            prompt = "Generate an interesting, engaging tweet that reflects your personality. Keep it under 270 characters."
            
            response = self.agent_bridge.send_message(agent_id, prompt)
            
            if response:
                twitter_response = self._prepare_twitter_response(response)
                
                # Post the tweet
                client = self.active_clients.get(agent_id)
                if client:
                    tweet_id = await client.post_tweet(twitter_response)
                    if tweet_id:
                        print(f"Posted proactive tweet for agent {agent_id}: {tweet_id}")
            
        except Exception as e:
            print(f"Error posting proactive tweet for agent {agent_id}: {e}")
    
    async def handle_mention_event(self, event):
        """Handle mention events from Thalamus event bus."""
        agent_id = event.agent_id
        mention_data = event.data
        
        # Process the mention
        mention = Tweet(**mention_data)
        await self._process_mention(agent_id, mention)
    
    async def handle_scheduled_post_event(self, event):
        """Handle scheduled post events from Thalamus event bus."""
        agent_id = event.agent_id
        post_data = event.data
        
        client = self.active_clients.get(agent_id)
        if client:
            tweet_id = await client.post_tweet(post_data.get("text", ""))
            if tweet_id:
                print(f"Posted scheduled tweet for agent {agent_id}: {tweet_id}")
    
    def get_active_agents(self) -> List[str]:
        """Get list of agents with active Twitter integration."""
        return list(self.active_clients.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Twitter integration statistics."""
        return {
            "active_agents": len(self.active_clients),
            "monitored_mentions": len(self.mention_tracking),
            "available": self.is_available()
        }