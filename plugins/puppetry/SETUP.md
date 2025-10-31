# Environment Setup Guide

## 🔧 **Environment Variables Setup**

The Puppetry plugin uses environment variables for configuration. You have two options:

### **Option 1: Using .env File (Recommended)**

1. **Copy the example file:**
   ```bash
   cd "c:\Users\kamal\Documents\Kahmah\doings\dapp\combo\animus\smcp\smcp\plugins\puppetry"
   copy .env.example .env
   ```

2. **Edit the .env file with your credentials:**
   ```bash
   # Letta Configuration
   LETTA_SERVER_URL=https://api.letta.com
   LETTA_API_TOKEN=your_actual_letta_token_here

   # Twitter API Configuration
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_api_secret
   TWITTER_ACCESS_TOKEN=your_twitter_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
   ```

3. **The plugin will automatically load this file!**

### **Option 2: PowerShell Environment Variables**

Set them temporarily for your current session:
```powershell
$env:LETTA_API_TOKEN = "your_token_here"
$env:LETTA_SERVER_URL = "https://api.letta.com"
$env:TWITTER_API_KEY = "your_key_here"
# ... etc
```

## 🌐 **Getting Real Letta Credentials**

### **Step 1: Create Letta Account**
1. Go to https://letta.com
2. Sign up for an account
3. Verify your email

### **Step 2: Get API Token** 
1. Log in to your Letta dashboard
2. Navigate to Settings → API Keys
3. Generate a new API key
4. Copy the token

### **Step 3: Find Your Server URL**
- For Letta Cloud: `https://api.letta.com`
- For Self-hosted: Your server's URL

## 🐦 **Getting Twitter API Credentials**

### **Step 1: Twitter Developer Account**
1. Go to https://developer.twitter.com
2. Apply for a developer account
3. Create a new app

### **Step 2: Get API Keys**
1. In your app dashboard, go to "Keys and tokens"
2. Copy these values:
   - API Key (Consumer Key)
   - API Secret (Consumer Secret)  
   - Access Token
   - Access Token Secret

## 🧪 **Testing Setup**

### **For Testing (Mock Server)**
```bash
# Use mock server (no real credentials needed)
LETTA_SERVER_URL=http://localhost:8283
LETTA_API_TOKEN=mock_token  # Any value works

# Start mock server in one terminal:
python mock_letta_server.py

# Test in another terminal:
python cli.py start-agent --agent-id demo-agent --behaviors twitter
```

### **For Production (Real APIs)**
```bash
# Use your real credentials in .env file
python cli.py start-agent --agent-id your-real-agent-id --behaviors twitter
```

## 📁 **File Locations**

```
puppetry/
├── .env              ← Your credentials (create this)
├── .env.example      ← Template file  
├── cli.py            ← Main entry point
└── core/
    ├── agent_bridge.py    ← Loads .env automatically
    └── config_manager.py  ← Uses environment variables
```

## 🔒 **Security Notes**

- **Never commit `.env` files to git**
- **Keep your API tokens secure**
- **Use different tokens for development vs production**
- **Rotate your tokens regularly**

## ❗ **Common Issues**

| Issue | Solution |
|-------|----------|
| `LETTA_API_TOKEN not set` | Create `.env` file with your token |
| `Connection refused` | Make sure Letta server is running |  
| `Twitter API 401` | Check your Twitter credentials |
| `Agent not found` | Verify agent ID exists in Letta |