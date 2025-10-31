# Puppetry - Twitter AI Agent Plugin for Animus

**Create intelligent Twitter AI agents that post, engage, and interact autonomously.**

Puppetry is an SMCP (Server Model Context Protocol) plugin for the [Animus](../../../) framework that enables you to create AI agents capable of autonomous Twitter activity. Built on the foundation of Puppet Engine's Twitter integration, Puppetry brings enterprise-grade Twitter automation to your Letta-powered AI agents.

## 🌟 What Can Puppetry Do?

- **🤖 Autonomous Posting**: AI agents generate and post contextual tweets automatically
- **💬 Smart Engagement**: Respond to mentions and participate in conversations intelligently  
- **📊 Multi-Agent Support**: Run multiple Twitter agents with individual personalities and credentials
- **🎯 Personality-Driven Content**: Each agent has configurable personality traits and posting styles
- **⚡ Real-Time Integration**: Seamless integration with Letta agents and Animus event system
- **🔧 Production Ready**: Battle-tested with live Twitter API integration

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- [Animus framework](../../../) installed
- Twitter Developer Account with API keys

### 1. Install Dependencies
```bash
cd animus/smcp/smcp/plugins/puppetry
pip install -r requirements.txt
```

### 2. Configure Twitter API
Create a `.env` file:
```bash
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here  
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

### 3. Test Your Setup
```bash
python debug_twitter.py
```
You should see: `🎉 All tests passed! Twitter API connection is working!`

### 4. Create Your First Agent
```bash
python quick_setup.py
```

### 5. Start Posting Tweets!
```bash
# Post a single test tweet
python post_test_tweet.py

# Run a standalone agent demo  
python standalone_agent.py
```

## 📚 Documentation

### 🏁 Getting Started
- **[Complete Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[Twitter API Setup](docs/TWITTER_API_SETUP.md)** - Get your Twitter developer credentials
- **[Quick Start Guide](docs/QUICK_START.md)** - 5-minute setup for experienced users

### 🔧 Usage & Configuration
- **[Agent Configuration](docs/AGENT_CONFIGURATION.md)** - Configure personalities, behaviors, and posting schedules
- **[CLI Reference](docs/CLI_REFERENCE.md)** - All available commands and options
- **[Multiple Agents](docs/MULTIPLE_AGENTS.md)** - Managing multiple Twitter agents

### 🏗️ Architecture & Development  
- **[Architecture Overview](docs/ARCHITECTURE.md)** - How Puppetry integrates with Animus
- **[API Reference](docs/API_REFERENCE.md)** - Programmatic usage and integration
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🎯 Example Usage

### Standalone Twitter Agent
```python
from puppetry import StandaloneTwitterAgent

# Create an AI agent with personality
agent = StandaloneTwitterAgent(
    agent_name="Tech Insights Bot",
    personality={
        "style": "Thoughtful and engaging",
        "topics": ["AI", "Technology", "Programming"],
        "tone": "Optimistic and curious"
    }
)

# Initialize and start posting
await agent.initialize()
await agent.post_tweet()  # Posts AI-generated content
```

### CLI Usage
```bash
# List all available agents
python cli.py list-agents

# Create and configure a new agent
python cli.py configure-agent --agent-id my-bot

# Start autonomous posting
python cli.py start-agent --agent-id my-bot --behaviors twitter

# Check system status
python cli.py status
```

### SMCP Plugin Integration
```python
# Puppetry automatically integrates with Animus SMCP server
# No additional setup required - just install and configure!
```

## 🏆 Real-World Results

Puppetry has been **live-tested with real Twitter API integration**:
- ✅ Successfully posts tweets to production Twitter accounts
- ✅ Handles Twitter API authentication and rate limiting
- ✅ Generates contextual, engaging AI content
- ✅ Supports multiple agents with individual personalities
- ✅ Battle-tested with enterprise-grade reliability

## Commands

### Agent Management
```bash
# Start Puppetry for an agent
python cli.py start-agent --agent-id AGENT_ID --behaviors twitter

# Stop Puppetry for an agent  
python cli.py stop-agent --agent-id AGENT_ID

# List all Letta agents
python cli.py list-agents
```

### Configuration
```bash
# Configure agent settings
python cli.py configure-agent --agent-id AGENT_ID --config-file config.json

# Check system status
python cli.py status
```

## Integration with Animus

### SMCP Auto-Discovery

Puppetry follows SMCP's plugin auto-discovery pattern. The plugin is automatically detected by the SMCP server when placed in the `smcp/plugins/puppetry/` directory.

### Letta Agent Registry

Puppetry connects to your existing Letta server and enumerates available agents, just like `animus-chat`. No agent creation - only binding to existing agents by ID.

### Thalamus Event Pattern

Internal event routing uses the Thalamus pattern:
- **Reflex Events**: Immediate Twitter mention responses
- **Normal Events**: Scheduled posts, engagement actions  
- **Background Events**: Memory consolidation, analytics

## Safety Features

### Twitter Safety
- Rate limit handling
- Content filtering
- Response length limits
- Mention spam protection

### Solana Safety  
- Maximum trade amounts
- Minimum wallet balances
- Daily trade limits
- Slippage protection
- Balance verification

## Development

### Adding New Integrations

1. Create new integration in `integrations/your_service/`
2. Implement the integration interface
3. Register event handlers with Thalamus
4. Update CLI commands

### Event System

Use the Thalamus event bus for coordination:

```python
# Emit events
await event_bus.emit_twitter_mention(agent_id, mention_data)
await event_bus.emit_trading_signal(agent_id, signal_data)

# Handle events  
event_bus.register_twitter_handlers(mention_handler, post_handler)
event_bus.register_solana_handlers(trading_handler)
```

## 🛠️ Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `debug_twitter.py` | Test Twitter API connection | `python debug_twitter.py` |
| `quick_setup.py` | Setup test agent configuration | `python quick_setup.py` |
| `post_test_tweet.py` | Post single test tweet | `python post_test_tweet.py` |
| `standalone_agent.py` | Run autonomous agent demo | `python standalone_agent.py` |
| `final_status.py` | System status report | `python final_status.py` |
| `cli.py` | Main CLI interface | `python cli.py --help` |

## 🔐 Security & Privacy

- **API Keys**: Stored securely in `.env` files (never committed to git)
- **Rate Limiting**: Built-in Twitter API rate limit handling
- **Sandboxing**: Test mode available for safe development
- **Permissions**: Only posts with explicit user authorization

## 🤝 Contributing

Puppetry is part of the Animus ecosystem. See the main [Animus contributing guide](../../../CONTRIBUTING.md) for development guidelines.

## 📄 License

This project follows the Animus licensing terms. See [LICENSE](LICENSE) for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/animus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/animus/discussions)  
- **Documentation**: [Full Documentation](docs/)

---

**Ready to create your Twitter AI agents?** Start with the [Complete Setup Guide](docs/SETUP.md) or jump into the [Quick Start Guide](docs/QUICK_START.md)!

🤖 *Built with ❤️ for the Animus AI Agent Framework*