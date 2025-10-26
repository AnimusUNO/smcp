#!/usr/bin/env python3
"""
Vibing Plugin - Autonomous Trading for Letta Agents

Enables agents to research coins, form trading theses, and execute trades
through the Aster API with clear reasoning and safety controls.

Copyright (c) 2025 Animus Team
"""

import argparse
import json
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import hmac
import hashlib
import time
import requests
from datetime import datetime

# Add the vibing directory to Python path for imports
VIBING_DIR = Path(__file__).parent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(VIBING_DIR / "vibing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vibing")

class AsterClient:
    """Wrapper for Aster API interactions"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, dry_run: bool = True):
        self.base_url = "https://sapi.asterdex.com"
        self.api_key = api_key
        self.api_secret = api_secret
        self.dry_run = dry_run
        
    def _get_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for authenticated endpoints"""
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
    def _request(self, method: str, endpoint: str, params: Dict[str, Any] = None, signed: bool = False) -> Dict[str, Any]:
        """Make request to Aster API"""
        if self.dry_run and signed:
            logger.info(f"[DRY RUN] Would make {method} request to {endpoint} with params {params}")
            return {"dry_run": True}
            
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
            
        if signed:
            if not params:
                params = {}
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._get_signature(params)
            
        try:
            response = requests.request(method, url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise

def load_config() -> Dict[str, Any]:
    """Load API credentials from .env file and settings from config file"""
    # Load .env file
    env_file = VIBING_DIR / '.env'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    # Get credentials from environment
    config = {
        'api_key': os.getenv('API_KEY', ''),
        'api_secret': os.getenv('API_SECRET_KEY', '')
    }
    
    # Load additional settings from config file
    config_file = VIBING_DIR / 'config' / 'config.json'
    if config_file.exists():
        with open(config_file) as f:
            config.update(json.load(f))
            
    return config

def research_coin(args: Dict[str, Any]) -> Dict[str, Any]:
    """Research a coin using available market data"""
    symbol = args.get('symbol')
    if not symbol:
        return {"error": "Symbol is required"}
        
    try:
        client = AsterClient()
        
        # Get 24hr stats
        stats = client._request('GET', '/api/v1/ticker/24hr', {'symbol': symbol})
        
        # Get recent trades
        trades = client._request('GET', '/api/v1/trades', {'symbol': symbol, 'limit': 100})
        
        # Get order book
        depth = client._request('GET', '/api/v1/depth', {'symbol': symbol, 'limit': 100})
        
        analysis = {
            "symbol": symbol,
            "price_change_24h": stats.get('priceChange'),
            "volume_24h": stats.get('volume'),
            "current_price": stats.get('lastPrice'),
            "bid_ask_spread": float(depth['asks'][0][0]) - float(depth['bids'][0][0]),
            "market_activity": "HIGH" if float(stats.get('volume', 0)) > 1000000 else "MEDIUM"
        }
        
        return {
            "success": True,
            "analysis": analysis,
            "raw_data": {
                "stats": stats,
                "recent_trades": trades,
                "order_book": depth
            }
        }
        
    except Exception as e:
        logger.error(f"Research failed: {str(e)}")
        return {"error": str(e)}

def propose_thesis(args: Dict[str, Any]) -> Dict[str, Any]:
    """Form a trading thesis based on research"""
    symbol = args.get('symbol')
    research_data = args.get('research_data', {})
    
    # Handle JSON string input
    if isinstance(research_data, str):
        try:
            import json
            research_data = json.loads(research_data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in research_data"}
    
    if not symbol or not research_data:
        return {"error": "Symbol and research data required"}
        
    try:
        analysis = research_data.get('analysis', {})
        
        # Simple thesis formation logic
        price_change = float(analysis.get('price_change_24h', 0))
        volume = float(analysis.get('volume_24h', 0))
        spread = float(analysis.get('bid_ask_spread', 0))
        
        confidence = 0
        reasons = []
        
        if abs(price_change) > 5:
            confidence += 20
            reasons.append(f"Strong price movement ({price_change}%)")
            
        if volume > 1000000:
            confidence += 20
            reasons.append("High trading volume")
            
        if spread < 0.1:
            confidence += 10
            reasons.append("Tight bid-ask spread")
            
        # Determine risk level with proper case
        if abs(price_change) > 10:
            risk_level = "HIGH"
        elif abs(price_change) > 5:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        thesis = {
            "symbol": symbol,
            "direction": "BUY" if price_change > 0 else "SELL",
            "confidence": confidence,
            "risk_level": risk_level,
            "reasons": reasons,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "thesis": thesis
        }
        
    except Exception as e:
        logger.error(f"Thesis formation failed: {str(e)}")
        return {"error": str(e)}

def open_trade(args: Dict[str, Any]) -> Dict[str, Any]:
    """Open a new trade based on thesis"""
    symbol = args.get('symbol')
    thesis = args.get('thesis', {})
    config = load_config()
    
    # Handle JSON string input
    if isinstance(thesis, str):
        try:
            import json
            thesis = json.loads(thesis)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in thesis"}
    
    if not symbol or not thesis:
        return {"error": "Symbol and thesis required"}
        
    try:
        client = AsterClient(
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret'),
            dry_run=args.get('dry_run', True)
        )
        
        # Calculate position size based on confidence
        confidence = thesis.get('confidence', 0)
        base_size = 20  # Base position size in quote currency (adjusted for $20 balance)
        position_size = (base_size * confidence) / 100
        
        # Determine order parameters based on side
        side = thesis.get('direction', 'BUY')
        if side == 'BUY':
            # For BUY orders, use quoteOrderQty (USDT amount)
            order_params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quoteOrderQty": str(position_size)
            }
        else:
            # For SELL orders, use quantity (BNB amount)
            # Convert USDT amount to BNB amount (approximate)
            bnb_quantity = position_size / 600  # Assuming BNB price around $600
            order_params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": str(round(bnb_quantity, 6))
            }
        
        result = client._request('POST', '/api/v1/order', order_params, signed=True)
        
        return {
            "success": True,
            "order": result,
            "thesis": thesis
        }
        
    except Exception as e:
        logger.error(f"Trade opening failed: {str(e)}")
        return {"error": str(e)}

def monitor_trade(args: Dict[str, Any]) -> Dict[str, Any]:
    """Monitor an open trade"""
    symbol = args.get('symbol')
    order_id = args.get('order_id')
    config = load_config()
    
    if not symbol or not order_id:
        return {"error": "Symbol and order_id required"}
        
    try:
        client = AsterClient(
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret'),
            dry_run=args.get('dry_run', True)
        )
        
        if args.get('dry_run', True):
            # Mock data for dry run
            mock_order = {
                "symbol": symbol,
                "orderId": order_id,
                "status": "FILLED",
                "price": "50000.00",  # Mock entry price
                "executedQty": "1.0"
            }
            mock_ticker = {
                "symbol": symbol,
                "price": "51000.00"  # Mock current price
            }
            order = mock_order
            ticker = mock_ticker
            logger.info(f"[DRY RUN] Mocked order data: {json.dumps(order, indent=2)}")
            logger.info(f"[DRY RUN] Mocked ticker data: {json.dumps(ticker, indent=2)}")
        else:
            # Get real order status
            order = client._request('GET', '/api/v1/order', {
                "symbol": symbol,
                "orderId": order_id
            }, signed=True)
            
            # Get current market price
            ticker = client._request('GET', '/api/v1/ticker/price', {
                "symbol": symbol
            })
        
        current_price = float(ticker.get('price', 0))
        entry_price = float(order.get('price', 0))
        
        # Avoid division by zero
        if entry_price == 0:
            pnl = 0
        else:
            pnl = ((current_price - entry_price) / entry_price) * 100
        
        status = {
            "symbol": symbol,
            "order_id": order_id,
            "status": order.get('status'),
            "entry_price": entry_price,
            "current_price": current_price,
            "pnl_percent": pnl,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "status": status,
            "raw_order": order
        }
        
    except Exception as e:
        logger.error(f"Trade monitoring failed: {str(e)}")
        return {"error": str(e)}

def stop_all_trades(args: Dict[str, Any]) -> Dict[str, Any]:
    """Emergency stop - cancel all open orders"""
    config = load_config()
    
    try:
        client = AsterClient(
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret'),
            dry_run=args.get('dry_run', True)
        )
        
        # Cancel all open orders
        result = client._request('DELETE', '/api/v1/allOpenOrders', {}, signed=True)
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Stop all trades failed: {str(e)}")
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(
        description="Vibing plugin for autonomous trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  research-coin     Research a coin using market data
  propose-thesis    Form a trading thesis
  open-trade       Open a new trade
  monitor-trade    Monitor an open trade
  stop-all         Emergency stop - cancel all trades

Examples:
  python cli.py research-coin --symbol BTCUSDT
  python cli.py propose-thesis --symbol BTCUSDT --research-data '{"analysis":...}'
  python cli.py open-trade --symbol BTCUSDT --thesis '{"direction":"BUY"...}'
  python cli.py monitor-trade --symbol BTCUSDT --order-id 12345
  python cli.py stop-all --dry-run false
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Research coin command
    research_parser = subparsers.add_parser("research-coin", help="Research a coin")
    research_parser.add_argument("--symbol", required=True, help="Trading pair symbol")
    
    # Propose thesis command
    thesis_parser = subparsers.add_parser("propose-thesis", help="Form trading thesis")
    thesis_parser.add_argument("--symbol", required=True, help="Trading pair symbol")
    thesis_parser.add_argument("--research-data", required=True, help="Research data in JSON format")
    
    # Open trade command
    trade_parser = subparsers.add_parser("open-trade", help="Open a new trade")
    trade_parser.add_argument("--symbol", required=True, help="Trading pair symbol")
    trade_parser.add_argument("--thesis", required=True, help="Thesis data in JSON format")
    trade_parser.add_argument("--dry-run", "--dry_run", type=bool, default=True, help="Dry run mode")
    
    # Monitor trade command
    monitor_parser = subparsers.add_parser("monitor-trade", help="Monitor a trade")
    monitor_parser.add_argument("--symbol", required=True, help="Trading pair symbol")
    monitor_parser.add_argument("--order-id", required=True, help="Order ID to monitor")
    monitor_parser.add_argument("--dry-run", "--dry_run", type=bool, default=True, help="Dry run mode")
    
    # Stop all command
    stop_parser = subparsers.add_parser("stop-all", help="Stop all trades")
    stop_parser.add_argument("--dry-run", "--dry_run", type=bool, default=True, help="Dry run mode")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "research-coin":
            result = research_coin(vars(args))
        elif args.command == "propose-thesis":
            result = propose_thesis(vars(args))
        elif args.command == "open-trade":
            # Parse thesis JSON string
            try:
                thesis = json.loads(args.thesis)
                params = {
                    "symbol": args.symbol,
                    "thesis": thesis,
                    "dry_run": args.dry_run
                }
                result = open_trade(params)
            except json.JSONDecodeError as e:
                result = {"error": f"Invalid thesis JSON: {str(e)}"}
        elif args.command == "monitor-trade":
            result = monitor_trade(vars(args))
        elif args.command == "stop-all":
            result = stop_all_trades(vars(args))
        else:
            result = {"error": f"Unknown command: {args.command}"}
        
        print(json.dumps(result, indent=2))
        sys.exit(0 if "error" not in result else 1)
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
