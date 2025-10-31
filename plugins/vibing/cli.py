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
import signal
import subprocess
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
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.base_url = "https://sapi.asterdex.com"
        self.api_key = api_key
        self.api_secret = api_secret
        
    def _get_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for authenticated endpoints"""
        query_string = '&'.join([f"{k}={str(v)}" for k, v in sorted(params.items())])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
    def _request(self, method: str, endpoint: str, params: Dict[str, Any] = None, signed: bool = False) -> Dict[str, Any]:
        """Make request to Aster API"""
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
            
        if signed:
            if not params:
                params = {}
            params['timestamp'] = int(time.time() * 1000)
            # Generate signature BEFORE adding it to params
            signature = self._get_signature(params)
            params['signature'] = signature
            
        try:
            if method == 'POST' and signed:
                # For POST requests with signatures, send data in request body as query string format
                # Set Content-Type header for form data
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                # Convert params dict to query string format for request body
                request_body = '&'.join([f"{k}={str(v)}" for k, v in sorted(params.items())])
                response = requests.post(url, headers=headers, data=request_body)
            elif method == 'GET' and signed:
                # For GET requests with signatures, manually construct query string to match signature exactly
                # Use the same format as signature generation: sorted params with string values
                query_string = '&'.join([f"{k}={str(v)}" for k, v in sorted(params.items())])
                full_url = f"{url}?{query_string}"
                response = requests.get(full_url, headers=headers)
            else:
                # For unsigned requests, send params in query string
                response = requests.request(method, url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    def get_symbol_filters(self, symbol: str) -> Dict[str, Any]:
        """Fetch exchange filters for a symbol (LOT_SIZE, MARKET_LOT_SIZE, MIN_NOTIONAL)."""
        try:
            info = self._request('GET', '/api/v1/exchangeInfo', {"symbol": symbol})
            # Some APIs return {symbols:[{symbol, filters:[...] }]} ; normalize
            symbols = info.get('symbols') if isinstance(info, dict) else None
            if isinstance(symbols, list):
                match = next((s for s in symbols if s.get('symbol') == symbol), None)
                if match:
                    filters = match.get('filters', [])
                else:
                    filters = []
            elif isinstance(info, list):
                match = next((s for s in info if s.get('symbol') == symbol), None)
                filters = match.get('filters', []) if match else []
            else:
                filters = info.get('filters', []) if isinstance(info, dict) else []

            result = {}
            for f in filters:
                ftype = f.get('filterType') or f.get('type')
                if ftype in ['LOT_SIZE', 'MARKET_LOT_SIZE', 'MIN_NOTIONAL']:
                    result[ftype] = f
            return result
        except Exception as e:
            logger.warning(f"Could not fetch exchange filters for {symbol}: {e}")
            return {}

def round_to_step(value: float, step: float) -> float:
    """Round value down to nearest step to satisfy LOT_SIZE stepSize."""
    if step <= 0:
        return value
    import math
    precision = max(0, len(str(step).split('.')[-1]))
    stepped = math.floor(value / step) * step
    return round(stepped, precision)

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
        config = load_config()
        client = AsterClient(
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret')
        )
        
        # Get 24hr stats
        stats = client._request('GET', '/api/v1/ticker/24hr', {'symbol': symbol})
        
        # Get order book
        depth = client._request('GET', '/api/v1/depth', {'symbol': symbol, 'limit': 100})
        
        analysis = {
            "symbol": symbol,
            "price_change_24h": stats.get('priceChange'),
            "volume_24h": stats.get('volume'),
            "current_price": stats.get('lastPrice'),
            "bid_ask_spread": float(depth['asks'][0][0]) - float(depth['bids'][0][0]) if depth.get('asks') and depth.get('bids') else 0.01,
            "market_activity": "HIGH" if float(stats.get('volume', 0)) > 1000000 else "MEDIUM",
            "sentiment": "The market shows a medium level of activity with minor price changes."
        }
        
        return {
            "success": True,
            "analysis": analysis,
            "raw_data": {
                "stats": stats,
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
    position_data = args.get('position_data', {})
    portfolio_data = args.get('portfolio_data', {})
    # Handle JSON string input
    if isinstance(research_data, str):
        try:
            import json
            research_data = json.loads(research_data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in research_data"}
    if isinstance(position_data, str):
        try:
            import json
            position_data = json.loads(position_data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in position_data"}
    if isinstance(portfolio_data, str):
        try:
            import json
            portfolio_data = json.loads(portfolio_data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in portfolio_data"}
    
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

        # Position-aware adjustments
        try:
            held_qty = float(position_data.get('position', {}).get('quantity', 0) or 0)
        except Exception:
            held_qty = 0
        if held_qty <= 0 and thesis["direction"] == "SELL":
            thesis["direction"] = "BUY"
            reasons.append("No holdings to sell; flipping to BUY")

        # Portfolio-aware sizing (proposed_size_usdt)
        # Derive available USDT from portfolio_data (check_balance result)
        usdt_available = None
        try:
            balances = portfolio_data.get('position', {}).get('balances', []) or portfolio_data.get('balances', [])
            for b in balances:
                if b.get('asset') == 'USDT':
                    usdt_available = float(b.get('free', 0))
                    break
        except Exception:
            usdt_available = None

        # Map confidence to base sizing bands (mirrors runtime)
        def band_from_conf(conf: float) -> float:
            if conf >= 80:
                return 0.12
            elif conf >= 60:
                return 0.08
            elif conf >= 40:
                return 0.04
            else:
                return 0.0

        proposed_size_usdt = 0.0
        if usdt_available is not None:
            proposed_size_usdt = usdt_available * band_from_conf(confidence)
            if proposed_size_usdt < 5.0 and proposed_size_usdt > 0:
                proposed_size_usdt = 5.0
        thesis["proposed_size_usdt"] = proposed_size_usdt

        # If SELL and we have holdings, propose units to sell; bound by holdings and min notional
        if thesis["direction"] == "SELL" and held_qty > 0:
            # Convert USDT size to units using current price; if no size available, default to 25% of holdings
            client = AsterClient(api_key=load_config().get('api_key'), api_secret=load_config().get('api_secret'))
            ticker = client._request('GET', '/api/v1/ticker/price', {"symbol": symbol})
            if isinstance(ticker, list):
                ticker = next((t for t in ticker if t.get('symbol') == symbol), {})
            price = float(ticker.get('price', 0) or 0)
            proposed_units = 0.0
            if price > 0 and proposed_size_usdt > 0:
                proposed_units = proposed_size_usdt / price
            if proposed_units == 0.0:
                proposed_units = held_qty * 0.25
            if proposed_units > held_qty:
                proposed_units = held_qty
            thesis["proposed_units_sell"] = proposed_units
        
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
    
    # Handle JSON string input (thesis should be a dict, but sometimes comes as JSON string)
    if isinstance(thesis, str):
        try:
            import json
            # First check if it's a double-encoded JSON string
            thesis_str = thesis
            try:
                # Try parsing once
                thesis = json.loads(thesis_str)
                # If result is still a string, it was double-encoded
                if isinstance(thesis, str):
                    thesis = json.loads(thesis)
            except (json.JSONDecodeError, TypeError):
                # If double parsing fails, try single parse
                thesis = json.loads(thesis_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse thesis JSON: {str(e)}")
            logger.error(f"Thesis string (first 200 chars): {thesis_str[:200] if len(thesis_str) > 200 else thesis_str}")
            return {"error": f"Invalid JSON in thesis: {str(e)}. Please ensure thesis is a valid JSON object with 'direction', 'confidence', and 'reasoning' fields. Received: {thesis_str[:100]}..."}
    
    # Validate thesis structure
    if not symbol or not thesis:
        return {"error": "Symbol and thesis required"}
    
    if not isinstance(thesis, dict):
        return {"error": f"Thesis must be a dictionary/object, but got {type(thesis).__name__}. Please construct thesis as an object: {{'direction': 'BUY', 'confidence': 50, 'reasoning': '...'}}"}
        
    try:
        client = AsterClient(
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret')
        )
        
        # Calculate position size based on confidence
        confidence = thesis.get('confidence', 0)
        
        # Validate confidence and set minimum position size
        if confidence <= 0:
            confidence = 50  # Default to 50% confidence if not specified or invalid
            logger.warning(f"No valid confidence in thesis, using default: {confidence}%")
        
        # Prefer explicit proposed size from thesis if present
        proposed_size_usdt = float(thesis.get('proposed_size_usdt', 0) or 0)
        if proposed_size_usdt > 0:
            position_size = proposed_size_usdt
        else:
            base_size = 20  # Base position size in quote currency (adjusted for $20 balance)
            position_size = (base_size * confidence) / 100
        
        # Ensure minimum position size meets Aster exchange requirements
        # MIN_NOTIONAL filter requires minimum order value of $5.00
        MIN_ORDER_VALUE = 5.0
        if position_size < MIN_ORDER_VALUE:
            position_size = MIN_ORDER_VALUE  # Minimum $5 order to meet MIN_NOTIONAL requirement
            logger.warning(f"Position size too small ({position_size}), using minimum: ${MIN_ORDER_VALUE} (MIN_NOTIONAL requirement)")
        
        # Determine order parameters based on side
        side = thesis.get('direction', 'BUY')
        
        # Validate direction
        if side not in ['BUY', 'SELL']:
            side = 'BUY'  # Default to BUY if invalid direction
            logger.warning(f"Invalid direction '{thesis.get('direction')}', using default: BUY")
        
        logger.info(f"Opening {side} order for {symbol} with position size: ${position_size:.2f}")
        
        if side == 'BUY':
            # For BUY orders, use quoteOrderQty (USDT amount). If explicit base units are provided, convert to notional at live price.
            explicit_units_buy = None
            try:
                if isinstance(args.get('units'), (int, float, str)):
                    explicit_units_buy = float(args.get('units'))
                elif isinstance(args.get('quantity'), (int, float, str)):
                    explicit_units_buy = float(args.get('quantity'))
            except (TypeError, ValueError):
                explicit_units_buy = None
            try:
                if explicit_units_buy is None and isinstance(thesis.get('units'), (int, float, str)):
                    explicit_units_buy = float(thesis.get('units'))
                elif explicit_units_buy is None and isinstance(thesis.get('quantity'), (int, float, str)):
                    explicit_units_buy = float(thesis.get('quantity'))
            except (TypeError, ValueError):
                explicit_units_buy = None

            final_notional = position_size
            if explicit_units_buy is not None and explicit_units_buy > 0:
                # Convert base units into quote notional using live price
                ticker = client._request('GET', '/api/v1/ticker/price', {"symbol": symbol})
                if isinstance(ticker, list):
                    ticker = next((t for t in ticker if t.get('symbol') == symbol), {})
                price_for_buy = float(ticker.get('price', 0) or 0)
                if price_for_buy > 0:
                    final_notional = explicit_units_buy * price_for_buy
            # Enforce minimum notional $5
            if final_notional < MIN_ORDER_VALUE:
                final_notional = MIN_ORDER_VALUE

            order_params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quoteOrderQty": str(final_notional),
                "recvWindow": "5000"  # 5 second window as recommended by Aster API
            }
        else:
            # For SELL orders, Aster requires quantity of BASE asset (e.g., ASTER in ASTERUSDT)
            # Prefer an explicit unit quantity if provided either at the top level or in thesis.
            explicit_units = None
            try:
                if isinstance(args.get('units'), (int, float, str)):
                    explicit_units = float(args.get('units'))
                elif isinstance(args.get('quantity'), (int, float, str)):
                    explicit_units = float(args.get('quantity'))
            except (TypeError, ValueError):
                explicit_units = None
            try:
                if isinstance(thesis.get('units'), (int, float, str)):
                    explicit_units = float(thesis.get('units'))
                elif isinstance(thesis.get('quantity'), (int, float, str)):
                    explicit_units = float(thesis.get('quantity'))
                elif isinstance(thesis.get('proposed_units_sell'), (int, float, str)):
                    explicit_units = float(thesis.get('proposed_units_sell'))
            except (TypeError, ValueError):
                explicit_units = None

            # Resolve quantity target
            if explicit_units is not None and explicit_units > 0:
                desired_quantity = float(explicit_units)
            else:
                # No explicit units; convert desired notional (position_size USDT) into base quantity via live price
                ticker = client._request('GET', '/api/v1/ticker/price', {"symbol": symbol})
                if isinstance(ticker, list):
                    ticker = next((t for t in ticker if t.get('symbol') == symbol), {})
                price = float(ticker.get('price', 0) or 0)
                if price <= 0:
                    return {"error": f"Could not fetch price for {symbol} to size SELL order"}
                desired_quantity = position_size / price

            # Apply exchange filters for proper rounding/limits
            filters = client.get_symbol_filters(symbol)
            lot = filters.get('MARKET_LOT_SIZE') or filters.get('LOT_SIZE') or {}
            step_size = float(lot.get('stepSize', 0) or lot.get('step_size', 0) or 0)
            min_qty = float(lot.get('minQty', 0) or lot.get('min_qty', 0) or 0)
            min_notional = float((filters.get('MIN_NOTIONAL') or {}).get('minNotional', 0) or 0)

            quantity = desired_quantity
            if step_size > 0:
                quantity = round_to_step(quantity, step_size)
            if min_qty > 0 and quantity < min_qty:
                quantity = min_qty

            # Re-check notional with current price
            try:
                ticker_for_min = client._request('GET', '/api/v1/ticker/price', {"symbol": symbol})
                if isinstance(ticker_for_min, list):
                    ticker_for_min = next((t for t in ticker_for_min if t.get('symbol') == symbol), {})
                current_price = float(ticker_for_min.get('price', 0) or 0)
            except Exception:
                current_price = 0
            if current_price > 0 and min_notional > 0 and (quantity * current_price) < max(min_notional, MIN_ORDER_VALUE):
                # Increase to meet min notional
                quantity = max(quantity, (max(min_notional, MIN_ORDER_VALUE) / current_price))
                if step_size > 0:
                    quantity = round_to_step(quantity, step_size)
                logger.warning(f"Adjusted SELL quantity to meet MIN_NOTIONAL: {quantity}")

            order_params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": str(round(quantity, 6)),
                "recvWindow": "5000"  # 5 second window as recommended by Aster API
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
            api_secret=config.get('api_secret')
        )
        
        # First, let's test if our API key is working by getting account info
        try:
            account_info = client._request('GET', '/api/v1/account', {
                "recvWindow": "5000"
            }, signed=True)
            logger.info(f"Account info retrieved successfully: {len(account_info.get('balances', []))} balances")
        except Exception as e:
            return {"error": f"API key authentication failed: {str(e)}"}
        
        # Now try to get all open orders to see what's available
        try:
            open_orders = client._request('GET', '/api/v1/openOrders', {
                "recvWindow": "5000"
            }, signed=True)
            logger.info(f"Retrieved {len(open_orders) if isinstance(open_orders, list) else 0} open orders")
            
            # Log all available order IDs for debugging
            if isinstance(open_orders, list):
                order_ids = [order.get('orderId') for order in open_orders]
                logger.info(f"Available order IDs: {order_ids}")
            
            # Find the specific order by orderId
            target_order = None
            if isinstance(open_orders, list):
                for order in open_orders:
                    if str(order.get('orderId')) == str(order_id):
                        target_order = order
                        break
            
            if target_order:
                order = target_order
                logger.info(f"Found order {order_id} in open orders")
            else:
                return {
                    "error": f"Order {order_id} not found in open orders. Available orders: {[o.get('orderId') for o in open_orders] if isinstance(open_orders, list) else 'None'}",
                    "open_orders": open_orders
                }
                
        except Exception as e2:
            return {"error": f"Could not retrieve open orders: {str(e2)}"}
        
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

def check_balance(args: Dict[str, Any]) -> Dict[str, Any]:
    """Check current account balances and open orders"""
    config = load_config()
    try:
        client = AsterClient(
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret')
        )
        
        # Get real account information
        account_info = client._request('GET', '/api/v1/account', {
            "recvWindow": "5000"
        }, signed=True)
        mock_balances = account_info.get('balances', [])
        
        # Get open orders
        open_orders = client._request('GET', '/api/v1/openOrders', {
            "recvWindow": "5000"
        }, signed=True)
        mock_open_orders = open_orders if isinstance(open_orders, list) else []
        
        # Filter out zero balances
        non_zero_balances = [bal for bal in mock_balances if float(bal.get('free', 0)) > 0 or float(bal.get('locked', 0)) > 0]
        
        position_summary = {
            "balances": non_zero_balances,
            "open_orders": mock_open_orders,
            "total_orders": len(mock_open_orders),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "position": position_summary
        }
        
    except Exception as e:
        logger.error(f"Balance check failed: {str(e)}")
        return {"error": str(e)}

def check_position(args: Dict[str, Any]) -> Dict[str, Any]:
    """Check position and calculate P/L for a specific trading pair"""
    symbol = args.get('symbol')
    config = load_config()
    
    if not symbol:
        return {"error": "Symbol parameter is required (e.g., ASTERUSDT)"}
    
    try:
        client = AsterClient(
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret')
        )
        
        # Extract base asset from symbol (e.g., ASTERUSDT -> ASTER)
        base_asset = symbol.replace('USDT', '').replace('BTC', '').replace('BNB', '')
        
        # Get account balances
        account_info = client._request('GET', '/api/v1/account', {
            "recvWindow": "5000"
        }, signed=True)
        balances = account_info.get('balances', [])
        
        # Find balance for base asset
        base_balance = 0.0
        for bal in balances:
            if bal.get('asset') == base_asset:
                base_balance = float(bal.get('free', 0)) + float(bal.get('locked', 0))
                break
        
        if base_balance == 0:
            return {
                "success": True,
                "position": {
                    "symbol": symbol,
                    "base_asset": base_asset,
                    "quantity": 0.0,
                    "message": f"No {base_asset} balance found"
                }
            }
        
        # Get trade history for this symbol
        # Convert all parameters to strings to ensure consistent signature generation
        trades = client._request('GET', '/api/v1/userTrades', {
            "symbol": symbol,
            "recvWindow": "5000",
            "limit": "1000"  # Get up to 1000 recent trades
        }, signed=True)
        
        if not isinstance(trades, list):
            return {"error": f"Could not retrieve trade history for {symbol}"}
        
        # Filter only BUY trades and calculate weighted average entry price
        buy_trades = [t for t in trades if t.get('side') == 'BUY']
        
        if not buy_trades:
            return {
                "success": True,
                "position": {
                    "symbol": symbol,
                    "base_asset": base_asset,
                    "quantity": base_balance,
                    "message": "No BUY trades found in history"
                }
            }
        
        # Calculate weighted average entry price
        total_cost = 0.0
        total_quantity = 0.0
        
        for trade in buy_trades:
            qty = float(trade.get('qty', 0))
            price = float(trade.get('price', 0))
            if qty > 0 and price > 0:
                total_cost += qty * price
                total_quantity += qty
        
        if total_quantity == 0:
            avg_entry_price = 0.0
        else:
            avg_entry_price = total_cost / total_quantity
        
        # Get current market price
        ticker = client._request('GET', '/api/v1/ticker/price', {
            "symbol": symbol
        })
        
        if isinstance(ticker, list):
            ticker = next((t for t in ticker if t.get('symbol') == symbol), {})
        
        current_price = float(ticker.get('price', 0))
        
        if current_price == 0:
            return {"error": f"Could not get current price for {symbol}"}
        
        # Calculate P/L metrics
        position_value = base_balance * current_price
        cost_basis = base_balance * avg_entry_price
        unrealized_pnl = position_value - cost_basis
        unrealized_pnl_percent = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        position_summary = {
            "symbol": symbol,
            "base_asset": base_asset,
            "quantity": base_balance,
            "average_entry_price": avg_entry_price,
            "current_price": current_price,
            "position_value_usdt": position_value,
            "cost_basis_usdt": cost_basis,
            "unrealized_pnl_usdt": unrealized_pnl,
            "unrealized_pnl_percent": unrealized_pnl_percent,
            "total_buy_trades": len(buy_trades),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "position": position_summary
        }
        
    except Exception as e:
        logger.error(f"Position check failed: {str(e)}")
        return {"error": str(e)}

def general_research(args: Dict[str, Any]) -> Dict[str, Any]:
    """Research all trading pairs to find trending coins"""
    config = load_config()
    try:
        client = AsterClient(
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret')
        )
        
        # Get real ticker data for all pairs
        tickers = client._request('GET', '/api/v1/ticker/24hr')
        mock_tickers = tickers if isinstance(tickers, list) else []
        
        # Smart filtering for trending coins
        trending_coins = []
        high_volume_coins = []
        high_change_coins = []
        newly_listed_coins = []
        
        for ticker in mock_tickers:
            symbol = ticker.get('symbol', '')
            price_change_percent = float(ticker.get('priceChangePercent', 0))
            volume = float(ticker.get('volume', 0))
            base_asset = ticker.get('baseAsset', '')
            
            # Skip major coins (BTC, ETH, BNB) - focus on altcoins/memecoins
            if any(major in symbol for major in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']):
                continue
                
            coin_data = {
                "symbol": symbol,
                "price_change_percent": price_change_percent,
                "volume": volume,
                "base_asset": base_asset,
                "quote_asset": ticker.get('quoteAsset'),
                "price_change": ticker.get('priceChange'),
                "trade_count": ticker.get('count'),
                "score": 0  # Will calculate smart score
            }
            
            # High volume coins (top 3)
            if volume > 500000:  # Minimum volume threshold
                high_volume_coins.append(coin_data)
            
            # High change coins (top 2) - both positive and negative
            if abs(price_change_percent) > 10.0:  # Significant movement
                high_change_coins.append(coin_data)
            
            # Newly listed coins (simulate - in real implementation, check listing time)
            # For demo, consider coins with low trade count as "newly listed"
            if ticker.get('count', 0) < 1000:  # Low trade count suggests new listing
                newly_listed_coins.append(coin_data)
        
        # Sort and select top performers
        high_volume_coins.sort(key=lambda x: x['volume'], reverse=True)
        high_change_coins.sort(key=lambda x: abs(x['price_change_percent']), reverse=True)
        newly_listed_coins.sort(key=lambda x: x['volume'], reverse=True)
        
        # Smart selection: Top 3 volume + Top 2 change + Top 2 newly listed
        selected_coins = []
        
        # Add top 3 by volume
        selected_coins.extend(high_volume_coins[:3])
        
        # Add top 2 by price change (avoid duplicates)
        for coin in high_change_coins[:2]:
            if not any(c['symbol'] == coin['symbol'] for c in selected_coins):
                selected_coins.append(coin)
        
        # Add top 2 newly listed (avoid duplicates)
        for coin in newly_listed_coins[:2]:
            if not any(c['symbol'] == coin['symbol'] for c in selected_coins):
                selected_coins.append(coin)
        
        # Limit to 5-7 coins total
        trending_coins = selected_coins[:7]
        
        # Sort by volume and price change
        trending_coins.sort(key=lambda x: (x['volume'], abs(x['price_change_percent'])), reverse=True)
        
        research_summary = {
            "total_pairs_analyzed": len(mock_tickers),
            "trending_coins": trending_coins[:7],  # Top 7
            "discovery_criteria": {
                "top_volume_count": 3,
                "top_change_count": 2,
                "newly_listed_count": 2,
                "min_volume_threshold": 500000,
                "min_change_threshold": 10.0,
                "newly_listed_max_trades": 1000,
                "exclude_major_coins": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "research": research_summary
        }
        
    except Exception as e:
        logger.error(f"General research failed: {str(e)}")
        return {"error": str(e)}

def start_autonomous(args: Dict[str, Any]) -> Dict[str, Any]:
    """Start autonomous trading script"""
    import subprocess
    import os
    from pathlib import Path
    
    max_trades = args.get('max_trades', 5)
    interval_minutes = args.get('interval_minutes', 15)
    try:
        # Check if already running
        pid_file = Path(__file__).parent / "runtime.pid"
        if pid_file.exists():
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
                # Check if process is still running
                try:
                    os.kill(old_pid, 0)
                    return {
                        "success": False,
                        "message": "Autonomous trading is already running",
                        "pid": old_pid
                    }
                except OSError:
                    # Process not running, remove stale PID file
                    pid_file.unlink()
        
        # Get runtime script path
        runtime_script = Path(__file__).parent / "runtime.py"
        
        # Start runtime as background process
        process = subprocess.Popen(
            [
                sys.executable, 
                str(runtime_script),
                "--max-trades", str(max_trades),
                "--interval-minutes", str(interval_minutes)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(Path(__file__).parent)
        )
        
        # Save PID
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        autonomous_config = {
            "max_trades": max_trades,
            "interval_minutes": interval_minutes,
            "pid": process.pid,
            "status": "STARTING",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Starting autonomous trading (PID: {process.pid})")
        
        return {
            "success": True,
            "message": f"Autonomous trading started",
            "config": autonomous_config
        }
        
    except Exception as e:
        logger.error(f"Failed to start autonomous trading: {str(e)}")
        return {"error": str(e)}

def stop_autonomous(args: Dict[str, Any]) -> Dict[str, Any]:
    """Stop autonomous trading script"""
    import os
    from pathlib import Path
    
    try:
        pid_file = Path(__file__).parent / "runtime.pid"
        
        if not pid_file.exists():
            return {
                "success": False,
                "message": "No autonomous trading process found"
            }
        
        # Read PID
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Kill process
        try:
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Stopped autonomous trading (PID: {pid})")
        except OSError as e:
            logger.warning(f"Process {pid} not found: {e}")
        
        # Remove PID file
        pid_file.unlink()
        
        return {
            "success": True,
            "message": "Autonomous trading stopped",
            "pid": pid,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop autonomous trading: {str(e)}")
        return {"error": str(e)}

def stop_all_trades(args: Dict[str, Any]) -> Dict[str, Any]:
    """Emergency stop - cancel all open orders"""
    config = load_config()
    try:
        client = AsterClient(
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret')
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
  check-balance    Check account balances and open orders
  check-position   Check position and P/L for a trading pair (requires --symbol)
  general-research Research all trading pairs for trending coins
  start-autonomous Start autonomous trading script
  stop-autonomous  Stop autonomous trading script
  stop-all         Emergency stop - cancel all trades

Examples:
  python cli.py research-coin --symbol BTCUSDT
  python cli.py propose-thesis --symbol BTCUSDT --research-data '{"analysis":...}'
  python cli.py open-trade --symbol BTCUSDT --thesis '{"direction":"BUY"...}'
  python cli.py monitor-trade --symbol BTCUSDT --order-id 12345
  python cli.py check-balance
  python cli.py check-position --symbol ASTERUSDT
  python cli.py general-research
  python cli.py start-autonomous --max-trades 5
  python cli.py stop-autonomous
  python cli.py stop-all
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Research coin command
    research_parser = subparsers.add_parser("research-coin", help="Research a coin")
    research_parser.add_argument("--symbol", required=True, help="Trading pair symbol")
    
    # Propose thesis command
    thesis_parser = subparsers.add_parser("propose-thesis", help="Form trading thesis")
    thesis_parser.add_argument("--symbol", required=True, help="Trading pair symbol")
    thesis_parser.add_argument("--research-data", "--research_data", required=True, help="Research data in JSON format")
    
    # Open trade command
    trade_parser = subparsers.add_parser("open-trade", help="Open a new trade")
    trade_parser.add_argument("--symbol", required=True, help="Trading pair symbol")
    trade_parser.add_argument("--thesis", required=True, help="Thesis data in JSON format")
    trade_parser.add_argument("--units", required=False, help="Optional base units for SELL")
    trade_parser.add_argument("--quantity", required=False, help="Optional alias for units for SELL")
    
    # Monitor trade command
    monitor_parser = subparsers.add_parser("monitor-trade", help="Monitor a trade")
    monitor_parser.add_argument("--symbol", required=True, help="Trading pair symbol")
    monitor_parser.add_argument("--order-id", "--order_id", required=True, help="Order ID to monitor")
    
    # Check balance command
    balance_parser = subparsers.add_parser("check-balance", help="Check account balances and open orders")
    
    # Check position command
    position_parser = subparsers.add_parser("check-position", help="Check position and P/L for a trading pair")
    position_parser.add_argument("--symbol", required=True, help="Trading pair symbol (e.g., ASTERUSDT)")
    
    # General research command
    general_parser = subparsers.add_parser("general-research", help="Research all trading pairs for trending coins")
    
    # Start autonomous command
    start_parser = subparsers.add_parser("start-autonomous", help="Start autonomous trading script")
    start_parser.add_argument("--max-trades", "--max_trades", type=int, default=5, help="Maximum number of concurrent trades")
    start_parser.add_argument("--interval-minutes", "--interval_minutes", type=int, default=15, help="Research interval in minutes")
    
    # Stop autonomous command
    stop_auto_parser = subparsers.add_parser("stop-autonomous", help="Stop autonomous trading script")
    
    # Stop all command
    stop_parser = subparsers.add_parser("stop-all", help="Stop all trades")
    
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
                    "thesis": thesis
                }
                # Include optional units/quantity if provided
                if getattr(args, 'units', None) is not None:
                    params["units"] = args.units
                if getattr(args, 'quantity', None) is not None:
                    params["quantity"] = args.quantity
                result = open_trade(params)
            except json.JSONDecodeError as e:
                result = {"error": f"Invalid thesis JSON: {str(e)}"}
        elif args.command == "monitor-trade":
            result = monitor_trade(vars(args))
        elif args.command == "check-balance":
            result = check_balance(vars(args))
        elif args.command == "check-position":
            result = check_position(vars(args))
        elif args.command == "general-research":
            result = general_research(vars(args))
        elif args.command == "start-autonomous":
            result = start_autonomous(vars(args))
        elif args.command == "stop-autonomous":
            result = stop_autonomous(vars(args))
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
