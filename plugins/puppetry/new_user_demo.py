#!/usr/bin/env python3
"""
New User Demo - Following Documentation

This script simulates exactly what a new user would do following our SETUP.md guide.
It demonstrates the complete journey from setup to posting tweets.
"""

import os
import sys
import time
from pathlib import Path

def print_step(step_num, title, description):
    """Print a formatted step."""
    print(f"\n📋 STEP {step_num}: {title}")
    print("=" * 60)
    print(f"📖 {description}")
    print()

def print_success(message):
    """Print success message."""
    print(f"✅ {message}")

def print_info(message):
    """Print info message."""
    print(f"💡 {message}")

def print_command(command):
    """Print command to run."""
    print(f"💻 Run: {command}")

def wait_for_enter(prompt="Press Enter to continue..."):
    """Wait for user input."""
    input(f"⏸️  {prompt}")

def main():
    """Simulate the new user experience."""
    
    print("🚀 PUPPETRY - NEW USER DEMO")
    print("Following the Complete Setup Guide")
    print("=" * 60)
    print()
    print("This demo shows exactly what a new user experiences")
    print("when following our documentation to set up Twitter AI agents.")
    print()
    
    wait_for_enter("Ready to start the demo?")
    
    # Step 1: Prerequisites Check
    print_step(1, "Prerequisites Check", 
               "What You Need: Python 3.8+, Twitter Developer Account, 10-15 minutes")
    
    print(f"🐍 Python Version: {sys.version}")
    if sys.version_info >= (3, 8):
        print_success("Python 3.8+ requirement met")
    else:
        print("❌ Need Python 3.8+")
        return
        
    print_info("✅ Animus framework: Already cloned (we're here!)")
    print_info("✅ Twitter Developer Account: Assumed user has API keys")
    
    wait_for_enter()
    
    # Step 2: Navigate to Puppetry
    print_step(2, "Navigate to Puppetry Directory",
               "cd animus/smcp/smcp/plugins/puppetry")
    
    current_dir = Path.cwd()
    print(f"📂 Current directory: {current_dir}")
    
    if "puppetry" in str(current_dir):
        print_success("Already in Puppetry directory!")
    else:
        print_info("User would navigate here: cd animus/smcp/smcp/plugins/puppetry")
    
    wait_for_enter()
    
    # Step 3: Check Files
    print_step(3, "Verify Installation Files",
               "Check that all required scripts and documentation exist")
    
    required_files = [
        ("requirements.txt", "Python dependencies"),
        ("debug_twitter.py", "Connection testing"),
        ("post_test_tweet.py", "First tweet posting"), 
        ("standalone_agent.py", "Autonomous agent demo"),
        ("README.md", "Main documentation"),
        ("docs/SETUP.md", "Setup guide"),
        ("docs/QUICK_START.md", "Quick start guide")
    ]
    
    all_present = True
    for filename, description in required_files:
        if Path(filename).exists():
            print_success(f"{filename} - {description}")
        else:
            print(f"❌ Missing: {filename}")
            all_present = False
    
    if all_present:
        print_success("All required files are present!")
    
    wait_for_enter()
    
    # Step 4: Install Dependencies  
    print_step(4, "Install Dependencies",
               "pip install tweepy>=4.14.0 letta-client>=0.1.300 requests aiohttp")
    
    print_command("pip install -r requirements.txt")
    
    # Test imports
    print("🔍 Testing imports...")
    deps = ["tweepy", "requests", "aiohttp"]
    for dep in deps:
        try:
            __import__(dep)
            print_success(f"{dep} - Available")
        except ImportError:
            print(f"❌ {dep} - Would need installation")
    
    wait_for_enter()
    
    # Step 5: Environment Configuration
    print_step(5, "Configure Twitter API Keys",
               "Create .env file with your Twitter API credentials")
    
    print_command("Create .env file:")
    print("""
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here  
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
""")
    
    env_path = Path(".env")
    if env_path.exists():
        print_success(".env file exists")
        
        # Check contents without revealing secrets
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        required_keys = ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"]
        found_keys = [key for key in required_keys if key in env_content]
        
        print_info(f"Found {len(found_keys)}/4 required API keys")
        
        if len(found_keys) == 4:
            print_success("All Twitter API keys configured!")
        else:
            print_info("User would add their Twitter API keys here")
    else:
        print_info("User would create .env file with their Twitter API credentials")
    
    wait_for_enter()
    
    # Step 6: Test Connection
    print_step(6, "Test Your Setup",
               "python debug_twitter.py - Should see: '🎉 All tests passed!'")
    
    print_command("python debug_twitter.py")
    print()
    print("Expected output:")
    print("""
🔍 Twitter API Connection Debug
========================================
1. Checking Tweepy installation... ✅
2. Checking environment variables... ✅ 
3. Testing direct Tweepy connection... ✅
4. Testing TwitterClient class... ✅
🎉 All tests passed! Twitter API connection is working!
""")
    
    wait_for_enter()
    
    # Step 7: Create First Agent
    print_step(7, "Create Your First Agent",
               "python quick_setup.py - Creates test agent configuration")
    
    print_command("python quick_setup.py")
    print()
    print("This creates a configured AI agent ready to post tweets!")
    
    wait_for_enter()
    
    # Step 8: Post First Tweet
    print_step(8, "Post Your First Tweet!",
               "python post_test_tweet.py - Posts a real tweet to Twitter")
    
    print_command("python post_test_tweet.py")
    print()
    print("⚠️  This posts a REAL tweet to your Twitter account!")
    print("Expected result:")
    print("""
🐦 Posting Test Tweet
==============================
✅ Twitter client ready
📝 Posting tweet: 🤖 Hello from the Puppetry system! Testing AI agent...
🎉 Tweet posted successfully!
📋 Tweet ID: 1234567890123456789
🔗 View at: https://twitter.com/user/status/1234567890123456789
""")
    
    wait_for_enter()
    
    # Step 9: Run Autonomous Agent
    print_step(9, "Run Autonomous Agent Demo",
               "python standalone_agent.py - AI agent posts multiple tweets")
    
    print_command("python standalone_agent.py")
    print()
    print("What this does:")
    print("• Creates an AI agent with tech/AI personality")
    print("• Generates contextual, engaging tweets automatically")
    print("• Posts multiple tweets with delays") 
    print("• Shows the full autonomous Twitter agent experience")
    
    wait_for_enter()
    
    # Step 10: Success!
    print_step(10, "🎉 SUCCESS!", 
               "You now have working Twitter AI agents!")
    
    print("🏆 CONGRATULATIONS!")
    print()
    print("You've successfully:")
    print_success("✅ Set up the Puppetry system")
    print_success("✅ Configured Twitter API integration") 
    print_success("✅ Posted real tweets to your Twitter account")
    print_success("✅ Created autonomous AI agents")
    print_success("✅ Demonstrated full Twitter automation")
    print()
    
    print("🚀 WHAT'S NEXT?")
    print("• Customize agent personalities and topics")
    print("• Create multiple agents for different accounts")
    print("• Set up scheduled posting with cron jobs")
    print("• Explore advanced CLI commands")
    print("• Build custom integrations and behaviors")
    print()
    
    print("📚 USEFUL COMMANDS:")
    print("• python final_status.py    - System status report")
    print("• python cli.py --help      - All CLI commands")  
    print("• python cli.py status      - Agent management")
    print()
    
    print("🤖 Your Twitter AI agents are ready to take over the internet!")
    print()
    print("📖 Full documentation: README.md, docs/SETUP.md, docs/QUICK_START.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped by user. Thanks for trying Puppetry!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()