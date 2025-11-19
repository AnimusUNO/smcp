#!/usr/bin/env python3
"""
Configuration Management for Vibing Plugin

Handles loading API credentials from environment variables, .env files, and config files.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

# Add the vibing directory to Python path for imports
VIBING_DIR = Path(__file__).parent


def load_config() -> Dict[str, Any]:
    """Load API credentials from environment variables, .env file, or config file"""
    # Priority 1: Check environment variables directly (for Railway/production)
    api_key = os.getenv('API_KEY', '')
    api_secret = os.getenv('API_SECRET_KEY', '')
    
    config = {
        'api_key': api_key,
        'api_secret': api_secret
    }
    
    # Priority 2: If credentials not found in env, try loading from .env file (for local development)
    if not (api_key and api_secret):
        env_file = VIBING_DIR / '.env'
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
            
            # Re-check after loading .env
            config['api_key'] = os.getenv('API_KEY', '')
            config['api_secret'] = os.getenv('API_SECRET_KEY', '')
    
    # Priority 3: Load additional settings from config file
    config_file = VIBING_DIR / 'config' / 'config.json'
    if config_file.exists():
        with open(config_file) as f:
            config.update(json.load(f))
            
    return config

