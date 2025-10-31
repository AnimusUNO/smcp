#!/usr/bin/env python3
"""
New User Journey Test

This script simulates the complete experience of a new user following our documentation
to set up Puppetry Twitter AI agents from scratch.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description, expect_success=True):
    """Run a command and report results."""
    print(f"\n🔧 {description}")
    print(f"💻 Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0 or not expect_success:
            print(f"✅ Success!")
            if result.stdout:
                print(f"📋 Output: {result.stdout[:200]}...")
            return True
        else:
            print(f"❌ Failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"🚨 Error: {result.stderr[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists."""
    print(f"\n📁 {description}")
    
    if Path(filepath).exists():
        print(f"✅ Found: {filepath}")
        return True
    else:
        print(f"❌ Missing: {filepath}")
        return False

def main():
    """Test the complete new user journey."""
    
    print("🚀 NEW USER JOURNEY TEST")
    print("=" * 50)
    print("Testing the complete Puppetry setup process as described in our documentation.")
    print()
    
    results = []
    
    # Test 1: Check we're in the right directory
    current_dir = Path.cwd()
    expected_dir = "puppetry"
    
    print(f"📍 Current directory: {current_dir}")
    if expected_dir in str(current_dir):
        print("✅ We're in the Puppetry directory")
        results.append(("Directory Check", True))
    else:
        print("⚠️  Not in Puppetry directory, but continuing...")
        results.append(("Directory Check", False))
    
    # Test 2: Check Python version
    print(f"\n🐍 Python version: {sys.version}")
    if sys.version_info >= (3, 8):
        print("✅ Python 3.8+ requirement met")
        results.append(("Python Version", True))
    else:
        print("❌ Python 3.8+ required")
        results.append(("Python Version", False))
    
    # Test 3: Check if requirements.txt exists
    results.append(("Requirements File", check_file_exists("requirements.txt", "Checking requirements.txt")))
    
    # Test 4: Check if key scripts exist
    key_scripts = [
        "debug_twitter.py",
        "quick_setup.py", 
        "post_test_tweet.py",
        "standalone_agent.py",
        "cli.py"
    ]
    
    script_results = []
    for script in key_scripts:
        script_results.append(check_file_exists(script, f"Checking {script}"))
    
    results.append(("Key Scripts", all(script_results)))
    
    # Test 5: Check .env file
    env_exists = check_file_exists(".env", "Checking .env configuration file")
    results.append((".env File", env_exists))
    
    if env_exists:
        print("\n🔐 Checking .env file contents...")
        try:
            with open(".env", "r") as f:
                env_content = f.read()
            
            required_keys = ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"]
            missing_keys = []
            
            for key in required_keys:
                if key not in env_content:
                    missing_keys.append(key)
            
            if not missing_keys:
                print("✅ All required Twitter API keys found in .env")
                results.append(("Environment Config", True))
            else:
                print(f"❌ Missing keys: {missing_keys}")
                results.append(("Environment Config", False))
                
        except Exception as e:
            print(f"❌ Error reading .env: {e}")
            results.append(("Environment Config", False))
    else:
        results.append(("Environment Config", False))
    
    # Test 6: Check if dependencies can be imported
    print(f"\n📦 Testing Python dependencies...")
    
    dependencies = ["tweepy", "requests", "aiohttp"]
    dep_results = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - OK")
            dep_results.append(True)
        except ImportError:
            print(f"❌ {dep} - Missing")
            dep_results.append(False)
    
    results.append(("Dependencies", all(dep_results)))
    
    # Test 7: Test debug script (if everything else works)
    if env_exists and all(dep_results):
        print(f"\n🐦 Testing Twitter API connection...")
        debug_success = run_command("python debug_twitter.py", "Running Twitter connection test")
        results.append(("Twitter Connection", debug_success))
    else:
        print(f"\n⚠️  Skipping Twitter test - missing dependencies or configuration")
        results.append(("Twitter Connection", False))
    
    # Test 8: Check documentation files
    doc_files = [
        "README.md",
        "docs/SETUP.md",
        "docs/QUICK_START.md"
    ]
    
    doc_results = []
    for doc_file in doc_files:
        doc_results.append(check_file_exists(doc_file, f"Checking {doc_file}"))
    
    results.append(("Documentation", all(doc_results)))
    
    # Generate final report
    print(f"\n🎯 NEW USER JOURNEY RESULTS")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 Overall Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 PERFECT! New users should have a smooth experience.")
    elif passed >= total * 0.8:
        print("👍 GOOD! Most new users should succeed with minor issues.")
    elif passed >= total * 0.6:
        print("⚠️  NEEDS WORK! Several issues may block new users.")
    else:
        print("❌ CRITICAL! Major issues will prevent new user success.")
    
    # Specific recommendations
    print(f"\n💡 RECOMMENDATIONS FOR NEW USERS:")
    
    if not results[0][1]:  # Directory
        print("• Navigate to the correct Puppetry directory first")
    
    if not results[1][1]:  # Python
        print("• Upgrade to Python 3.8+ before starting")
        
    if not results[5][1]:  # Dependencies
        print("• Run 'pip install -r requirements.txt' to install dependencies")
        
    if not results[4][1]:  # .env
        print("• Create .env file with Twitter API credentials")
        
    if not results[6][1]:  # Twitter connection
        print("• Verify Twitter API keys and permissions")
        
    if all([results[i][1] for i in [0,1,4,5,6]]):
        print("• ✅ Ready to run 'python post_test_tweet.py' to post first tweet!")
        print("• ✅ Ready to run 'python standalone_agent.py' for autonomous agent!")
    
    print(f"\n📚 DOCUMENTATION COMPLETENESS:")
    if results[7][1]:  # Documentation
        print("✅ All key documentation files are present")
        print("• New users can follow README.md → docs/SETUP.md → docs/QUICK_START.md")
    else:
        print("❌ Some documentation is missing - may confuse new users")

if __name__ == "__main__":
    main()