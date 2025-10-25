# Quick Start Guide - Puppetry Twitter AI Agents

**5-Minute Setup for Experienced Users**

Get Twitter AI agents posting in under 5 minutes. This guide assumes you're familiar with Python, APIs, and command line tools.

## ⚡ TL;DR - One Command Setup

```bash
# 1. Navigate to Puppetry
cd animus/smcp/smcp/plugins/puppetry

# 2. Install deps, configure, and test
pip install -r requirements.txt && \
echo "TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret  
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret" > .env && \
python debug_twitter.py && \
python post_test_tweet.py
```

## 📋 Prerequisites Checklist

- ✅ Python 3.8+
- ✅ Twitter Developer Account ([get here](https://developer.twitter.com))
- ✅ API Keys: Consumer Key/Secret + Access Token/Secret
- ✅ Animus framework cloned

## 🚀 5-Minute Setup

### 1. Install & Configure (60 seconds)
```bash
cd animus/smcp/smcp/plugins/puppetry
pip install tweepy>=4.14.0 letta-client>=0.1.300

# Create .env with your Twitter API credentials (no quotes)
cat > .env << EOF
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
EOF
```

### 2. Test Connection (30 seconds)
```bash
python debug_twitter.py
# Should see: "🎉 All tests passed! Twitter API connection is working!"
```

### 3. Post First Tweet (60 seconds)
```bash
echo "yes" | python post_test_tweet.py
# Posts live tweet to your Twitter account
```

### 4. Run Autonomous Agent (60 seconds)
```bash
echo "2" | python standalone_agent.py
# Runs demo with 3 AI-generated tweets
```

### 5. Create Production Agent (30 seconds)
```bash
python quick_setup.py
# Sets up configured agent for ongoing use
```

## 🎯 Key Commands

| Command | Purpose |
|---------|---------|
| `python debug_twitter.py` | Test API connection |
| `python post_test_tweet.py` | Post single tweet |
| `python standalone_agent.py` | Run autonomous demo |
| `python quick_setup.py` | Create agent config |
| `python cli.py --help` | Full CLI reference |
| `python final_status.py` | System status report |

## ⚙️ Configuration

### Agent Configuration
```json
{
  "agent_id": "my-agent",
  "twitter": {
    "api_key": "...",
    "enabled": true
  },
  "behavior": {
    "posting_frequency": "high|moderate|low",
    "response_style": "enthusiastic|professional|casual",
    "personality_traits": {
      "style": "AI enthusiast with tech focus",
      "topics": ["AI", "technology", "programming"]
    }
  }
}
```

### Environment Variables
```bash
# Required
TWITTER_API_KEY=abc123...
TWITTER_API_SECRET=xyz789...
TWITTER_ACCESS_TOKEN=1234567890-abc...
TWITTER_ACCESS_TOKEN_SECRET=def456...

# Optional  
LETTA_SERVER_URL=http://localhost:8283
LETTA_API_TOKEN=your_token
```

## 🔧 API Usage

### Standalone Agent
```python
from puppetry.standalone_agent import StandaloneTwitterAgent

agent = StandaloneTwitterAgent(
    agent_name="Tech Bot",
    personality={
        "style": "Technical and engaging",
        "topics": ["AI", "ML", "Python"],
        "tone": "Professional"
    }
)

await agent.initialize()
await agent.post_tweet()
```

### Twitter Client
```python
from puppetry.integrations.twitter.client import TwitterClient, TwitterConfig

config = TwitterConfig(
    api_key=os.getenv('TWITTER_API_KEY'),
    api_key_secret=os.getenv('TWITTER_API_SECRET'),
    access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
    access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
)

client = TwitterClient(config)
tweet_id = await client.post_tweet("Hello from AI! 🤖")
```

## 🎛️ CLI Operations

### Agent Management
```bash
# List agents
python cli.py list-agents

# Start agent with Twitter behaviors
python cli.py start-agent --agent-id my-bot --behaviors twitter

# Configure agent
python cli.py configure-agent --agent-id my-bot

# System status
python cli.py status
```

### Batch Operations
```bash
# Setup multiple agents
for agent in bot1 bot2 bot3; do
  python cli.py configure-agent --agent-id $agent
done

# Start all agents
python cli.py list-agents | grep agent_id | while read agent; do
  python cli.py start-agent --agent-id $agent --behaviors twitter
done
```

## 📊 Production Deployment

### Multiple Accounts
1. Create separate `.env` files per account:
   ```bash
   .env.account1
   .env.account2
   ```

2. Use environment-specific scripts:
   ```bash
   env $(cat .env.account1 | xargs) python standalone_agent.py
   ```

### Scheduling
```bash
# Cron job for regular posting (every 30 minutes)
*/30 * * * * cd /path/to/puppetry && python standalone_agent.py

# Systemd service for continuous operation
[Unit]
Description=Puppetry Twitter Agent
After=network.target

[Service]
Type=simple
User=your-user
ExecStart=/usr/bin/python3 /path/to/puppetry/standalone_agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Monitoring
```bash
# Health check endpoint
curl -f http://localhost:8283/health || alert "Letta server down"

# Tweet verification
python -c "
from integrations.twitter.client import TwitterClient, TwitterConfig
import os
# ... setup config ...
client = TwitterClient(config)
assert client.is_available(), 'Twitter client failed'
print('✅ All systems operational')
"
```

## 🐛 Debugging

### Quick Diagnostics
```bash
# Full system check
python final_status.py

# Twitter-specific debug
python debug_twitter.py

# Check logs
tail -f ~/.letta/logs/server.log
```

### Common Fixes
```bash
# Dependencies
pip install --upgrade tweepy letta-client

# Reset configuration
rm -rf config/agents/*.json && python quick_setup.py

# Clear Twitter cache
rm -rf ~/.tweepy_cache/
```

## 🔗 Integration Points

### SMCP Plugin
- Auto-discovered at `smcp/plugins/puppetry/`
- Follows SMCP plugin conventions
- Integrates with Animus event bus

### Letta Agent Bridge
- Connects to existing Letta server
- Uses agent registry for enumeration  
- No agent creation - binding only

### Thalamus Event System
- Reflex events: Immediate responses
- Normal events: Scheduled actions
- Background events: Analytics, memory

## 🎯 Next Steps

1. **Scale Up**: Create multiple agents with different personalities
2. **Automate**: Set up cron jobs or systemd services  
3. **Monitor**: Implement health checks and alerting
4. **Customize**: Extend with new integrations or behaviors
5. **Optimize**: Tune posting frequency and engagement strategies

## 📚 Full Documentation

- **[Complete Setup Guide](SETUP.md)** - Detailed walkthrough
- **[CLI Reference](CLI_REFERENCE.md)** - All commands
- **[API Reference](API_REFERENCE.md)** - Programmatic usage
- **[Architecture](ARCHITECTURE.md)** - System design
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues

---

**Got questions?** Check the [main README](../README.md) or [open an issue](https://github.com/your-org/animus/issues).

*Happy tweeting! 🐦🤖*