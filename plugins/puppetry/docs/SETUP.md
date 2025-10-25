# Complete Setup Guide - Puppetry Twitter AI Agents

**From Zero to Posting Tweets in 10 Minutes**

This guide walks you through setting up Puppetry from scratch, even if you've never used Animus before. By the end, you'll have AI agents posting tweets to your Twitter account!

## 📋 What You'll Need

- **Computer**: Windows, Mac, or Linux
- **Python 3.8+**: [Download from python.org](https://python.org/downloads)
- **Twitter Developer Account**: Free to create
- **10-15 minutes**: That's it!

## 🏁 Step 1: Get Animus Framework

### Option A: Clone from GitHub (Recommended)
```bash
# Clone the Animus repository
git clone https://github.com/your-org/animus.git
cd animus
```

### Option B: Download ZIP
1. Go to the [Animus GitHub page](https://github.com/your-org/animus)
2. Click "Code" → "Download ZIP"
3. Extract and navigate to the folder

## 🐦 Step 2: Create Twitter Developer Account

### Get Your Twitter API Keys
1. **Go to**: [developer.twitter.com](https://developer.twitter.com)
2. **Sign in** with your Twitter account
3. **Apply for a developer account**:
   - Use case: "Building AI agents for personal/educational use"
   - Description: "Creating AI-powered Twitter bots for automation"
4. **Create a new App**:
   - App name: "My AI Agent Bot"
   - Description: "AI agent that posts automated tweets"
   - Website: `https://example.com` (can be anything)
5. **Generate Keys**:
   - Go to "Keys and Tokens" tab
   - Generate "API Key and Secret" 
   - Generate "Access Token and Secret"
   - **Save these securely!**

### Your Keys Should Look Like:
```
API Key: abc123def456ghi789...
API Secret: xyz789uvw456rst123...
Access Token: 1234567890-abcdef123456...
Access Token Secret: klmno789pqrs456tuv123...
```

## 🔧 Step 3: Install Puppetry

### Navigate to Puppetry Directory
```bash
cd animus/smcp/smcp/plugins/puppetry
```

### Install Python Dependencies
```bash
# Install required packages
pip install tweepy>=4.14.0 letta-client>=0.1.300 requests aiohttp

# Or use the requirements file
pip install -r requirements.txt
```

## ⚙️ Step 4: Configure Your API Keys

### Create Environment File
Create a file called `.env` in the puppetry directory:

**Windows (PowerShell):**
```powershell
New-Item -Name ".env" -ItemType File
notepad .env
```

**Mac/Linux:**
```bash
nano .env
```

### Add Your Twitter Keys
Copy and paste this into the `.env` file, replacing with your actual keys:

```env
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

**Important**: Remove any quotes around the values!

### Save the File
- **Windows Notepad**: Ctrl+S
- **Mac/Linux nano**: Ctrl+X, then Y, then Enter

## ✅ Step 5: Test Your Setup

### Run the Connection Test
```bash
python debug_twitter.py
```

### Expected Output:
```
🔍 Twitter API Connection Debug
========================================

1. Checking Tweepy installation...
✅ Tweepy installed: v4.14.0

2. Checking environment variables...
✅ TWITTER_API_KEY: abc123def4...
✅ TWITTER_API_SECRET: xyz789uvw4...
✅ TWITTER_ACCESS_TOKEN: 1234567890...
✅ TWITTER_ACCESS_TOKEN_SECRET: klmno789pq...

3. Testing direct Tweepy connection...
✅ Authentication successful!
📊 User: @YourTwitterHandle
👤 Name: Your Display Name
🆔 ID: 1234567890123456789

4. Testing TwitterClient class...
✅ TwitterClient initialized successfully!

🎉 All tests passed! Twitter API connection is working!
```

### If You See Errors:
- **"Module not found"**: Run `pip install tweepy` again
- **"Authentication failed"**: Double-check your API keys in `.env`
- **"Missing or too short"**: Make sure there are no quotes around values in `.env`

## 🤖 Step 6: Create Your First Agent

### Quick Setup Script
```bash
python quick_setup.py
```

This creates a test agent configuration and verifies everything works.

### Expected Output:
```
🚀 Quick Puppetry Production Test
========================================

1. Checking environment...
✅ TWITTER_API_KEY: abc123def4...
✅ TWITTER_API_SECRET: xyz789uvw4...
✅ TWITTER_ACCESS_TOKEN: 1234567890...
✅ TWITTER_ACCESS_TOKEN_SECRET: klmno789pq...

2. Creating test agent configuration...
✅ Agent configuration created for: test-agent

3. Testing Twitter client...
✅ Twitter client initialized successfully

4. Testing tweet capability...
📝 Would post tweet: 'Hello from the Puppetry system! 🤖 #AI #Twitter'
⚠️  Actual posting disabled for safety - uncomment to enable

5. Saving configuration...
✅ Configuration saved to: agents/test-agent.json

🎉 Production setup complete!
```

## 🐦 Step 7: Post Your First Tweet!

### Single Test Tweet
```bash
python post_test_tweet.py
```

Type `yes` when prompted to post a real tweet to your Twitter account.

### Expected Output:
```
⚠️  This will post a real tweet to your Twitter account!
Type 'yes' to continue: yes
🐦 Posting Test Tweet
==============================
🔧 Initializing Twitter client...
✅ Twitter client ready

📝 Posting tweet: 🤖 Hello from the Puppetry system! Testing AI agent Twitter integration. #AI #TwitterBot #Animus
🎉 Tweet posted successfully!
📋 Tweet ID: 1976339209616031865
🔗 View at: https://twitter.com/user/status/1976339209616031865
```

**🎉 Congratulations! You just posted your first AI-generated tweet!**

## 🚀 Step 8: Run an Autonomous Agent

### Demo Mode
```bash
python standalone_agent.py
```

Choose option `1` for a single tweet or option `2` for a full demo.

### What the Agent Does:
- **Generates AI content** based on tech/AI topics
- **Posts tweets automatically** with variety and personality
- **Uses templates** for consistent but varied content
- **Handles rate limiting** and Twitter API best practices

### Sample Generated Tweets:
```
🤖 AI is transforming how we interact with technology every day #AI #Tech
💡 Just thinking: Machine learning is becoming more accessible to developers worldwide #Innovation
🚀 The intersection of AI and creativity is producing fascinating results What do you think? #AI #Future
```

## 🎛️ Step 9: Customize Your Agent

### Edit Agent Configuration
```bash
# View saved configuration
notepad config/agents/test-agent.json
```

### Customize Personality:
```json
{
  "agent_id": "test-agent",
  "behavior": {
    "posting_frequency": "high",
    "personality_traits": {
      "style": "Your custom style here",
      "topics": ["Your", "Custom", "Topics"],
      "tone": "Professional/Casual/Humorous"
    },
    "response_style": "enthusiastic"
  }
}
```

### Available Options:
- **Posting Frequency**: `"low"`, `"moderate"`, `"high"`
- **Response Style**: `"conversational"`, `"professional"`, `"enthusiastic"`, `"casual"`
- **Topics**: Array of interests for content generation
- **Style**: Overall personality description

## 🎯 Step 10: Advanced Usage

### CLI Commands
```bash
# Check system status
python cli.py status

# List all configured agents
python cli.py list-agents

# Configure a new agent
python cli.py configure-agent --agent-id my-new-bot

# Get help
python cli.py --help
```

### Multiple Agents
You can create multiple agents with different Twitter accounts:

1. Create new `.env` files for each account
2. Run `quick_setup.py` with different agent IDs
3. Each agent can have unique personalities and posting schedules

## 🔧 Troubleshooting

### Common Issues:

**"No module named 'tweepy'"**
```bash
pip install tweepy>=4.14.0
```

**"Authentication failed"**
- Check your API keys in `.env`
- Make sure no quotes around values
- Verify keys are from the correct Twitter app

**"Permission denied" / "App not authorized"**
- Make sure you generated both API keys AND access tokens
- Check that your Twitter app has "Read and Write" permissions

**"Rate limit exceeded"**
- Twitter limits how often you can post
- Wait 15-30 minutes and try again
- Use longer delays between tweets

### Getting Help

1. **Check the [Troubleshooting Guide](TROUBLESHOOTING.md)**
2. **Run diagnostics**: `python debug_twitter.py`
3. **Check configuration**: `python final_status.py`
4. **Ask for help**: [GitHub Issues](https://github.com/your-org/animus/issues)

## 🎉 You're Done!

**Congratulations!** You now have:

- ✅ **Working Twitter AI agents** that post real tweets
- ✅ **Customizable personalities** and posting behaviors  
- ✅ **Multiple agent support** for scaling up
- ✅ **Production-ready system** with rate limiting and safety features
- ✅ **Complete control** over what gets posted and when

### Next Steps:
- **Experiment with personalities** to find your agent's voice
- **Create multiple agents** for different topics or accounts
- **Set up scheduled posting** for consistent engagement
- **Monitor and adjust** based on engagement metrics

**Your Twitter AI agents are ready to take over the internet!** 🤖🐦

---

*Need help? Check out our [Quick Start Guide](QUICK_START.md) or [CLI Reference](CLI_REFERENCE.md)*