#!/usr/bin/env python3
"""
x402 Plugin - SMCP Integration for x402 Vending Machine

Enables agents to interact with the x402 vending machine server:
- List available items
- Check item details
- Monitor purchases
- Get purchase history

Copyright (c) 2025 Animus Team
"""

import argparse
import json
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from pathlib import Path

# Add the x402 directory to Python path for imports
X402_DIR = Path(__file__).parent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(X402_DIR / "x402.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("x402")


def get_x402_server_url() -> str:
    """Get x402 server URL from environment variable."""
    url = os.getenv('X402_SERVER_URL', '').rstrip('/')
    if not url:
        logger.error("X402_SERVER_URL environment variable not set")
        return ""
    return url


class X402Client:
    """Client for interacting with x402 vending machine server."""
    
    def __init__(self, base_url: str):
        """Initialize x402 client."""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'SMCP-x402-plugin/1.0'
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make request to x402 server."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        return self._request('GET', '/health')
    
    def list_items(self) -> Dict[str, Any]:
        """Get list of all available items."""
        return self._request('GET', '/items')
    
    def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get details of a specific item."""
        return self._request('GET', f'/items/{item_id}')
    
    def get_discovery(self) -> Dict[str, Any]:
        """Get x402 discovery descriptor."""
        return self._request('GET', '/.well-known/x402')
    
    def get_purchases(self, limit: int = 50, since: Optional[str] = None) -> Dict[str, Any]:
        """Get recent purchases."""
        params = {'limit': limit}
        if since:
            params['since'] = since
        return self._request('GET', '/purchases', params=params)
    
    def get_fulfillments(self, limit: int = 50, since: Optional[str] = None) -> Dict[str, Any]:
        """Get fulfillment records."""
        params = {'limit': limit}
        if since:
            params['since'] = since
        return self._request('GET', '/fulfillments', params=params)


def list_items_command(args: argparse.Namespace) -> str:
    """List all available items from x402 server."""
    url = get_x402_server_url()
    if not url:
        return json.dumps({
            "success": False,
            "error": "X402_SERVER_URL environment variable not set"
        })
    
    try:
        client = X402Client(url)
        result = client.list_items()
        return json.dumps({
            "success": True,
            "data": result
        }, indent=2)
    except Exception as e:
        logger.error(f"Failed to list items: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


def check_item_command(args: argparse.Namespace) -> str:
    """Check details of a specific item."""
    url = get_x402_server_url()
    if not url:
        return json.dumps({
            "success": False,
            "error": "X402_SERVER_URL environment variable not set"
        })
    
    if not args.item_id:
        return json.dumps({
            "success": False,
            "error": "item_id is required"
        })
    
    try:
        client = X402Client(url)
        result = client.get_item(args.item_id)
        return json.dumps({
            "success": True,
            "data": result
        }, indent=2)
    except Exception as e:
        logger.error(f"Failed to check item: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


def health_check_command(args: argparse.Namespace) -> str:
    """Check x402 server health."""
    url = get_x402_server_url()
    if not url:
        return json.dumps({
            "success": False,
            "error": "X402_SERVER_URL environment variable not set"
        })
    
    try:
        client = X402Client(url)
        result = client.health_check()
        return json.dumps({
            "success": True,
            "data": result
        }, indent=2)
    except Exception as e:
        logger.error(f"Failed to check health: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


def monitor_purchases_command(args: argparse.Namespace) -> str:
    """
    Monitor for new purchases.
    
    Checks the x402 server for recent purchases. Returns purchases sorted by most recent first.
    Use the 'since' parameter to only get purchases after a specific timestamp.
    """
    url = get_x402_server_url()
    if not url:
        return json.dumps({
            "success": False,
            "error": "X402_SERVER_URL environment variable not set"
        })
    
    try:
        client = X402Client(url)
        
        # Get limit from args if provided, default to 10 for monitoring
        limit = getattr(args, 'limit', 10)
        since = getattr(args, 'since', None)
        
        result = client.get_purchases(limit=limit, since=since)
        
        return json.dumps({
            "success": True,
            "data": result,
            "new_purchases_count": result.get("total", 0)
        }, indent=2)
    except Exception as e:
        logger.error(f"Failed to monitor purchases: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


def main():
    """Main entry point for the plugin CLI."""
    parser = argparse.ArgumentParser(
        description="x402 Vending Machine Plugin for SMCP",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # list-items command
    list_parser = subparsers.add_parser('list-items', help='List all available items')
    
    # check-item command
    check_parser = subparsers.add_parser('check-item', help='Check details of a specific item')
    check_parser.add_argument('--item-id', '--item_id', type=str, required=True, help='Item ID to check')
    
    # health-check command
    health_parser = subparsers.add_parser('health-check', help='Check x402 server health')
    
    # monitor-purchases command
    monitor_parser = subparsers.add_parser('monitor-purchases', help='Monitor for new purchases')
    monitor_parser.add_argument('--limit', type=int, default=10, help='Maximum number of purchases to return (default: 10)')
    monitor_parser.add_argument('--since', type=str, help='ISO timestamp to filter purchases after (e.g., 2025-11-10T12:00:00)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'list-items':
        result = list_items_command(args)
    elif args.command == 'check-item':
        result = check_item_command(args)
    elif args.command == 'health-check':
        result = health_check_command(args)
    elif args.command == 'monitor-purchases':
        result = monitor_purchases_command(args)
    else:
        result = json.dumps({
            "success": False,
            "error": f"Unknown command: {args.command}"
        })
    
    print(result)
    sys.exit(0 if json.loads(result).get("success", False) else 1)


if __name__ == "__main__":
    main()

