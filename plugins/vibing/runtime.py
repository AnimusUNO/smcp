#!/usr/bin/env python3
"""
Vibing Runtime - Autonomous Trading Mode

Manages the autonomous trading lifecycle for agents in /vibe mode.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add the vibing directory to Python path
VIBING_DIR = Path(__file__).parent
sys.path.append(str(VIBING_DIR))

from cli import research_coin, propose_thesis, open_trade, monitor_trade, stop_all_trades, check_balance, general_research, load_config, check_position

# Configure logging: ensure runtime has its own file handler even if cli.py already configured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("vibing.runtime")
logger.propagate = False
_has_runtime_file = False
for h in logger.handlers:
    try:
        if isinstance(h, logging.FileHandler) and str(getattr(h, 'baseFilename', '')).endswith('runtime.log'):
            _has_runtime_file = True
            break
    except Exception:
        pass
if not _has_runtime_file:
    _fh = logging.FileHandler(VIBING_DIR / "runtime.log")
    _fh.setLevel(logging.INFO)
    _fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_fh)
    # Also mirror to stdout for visibility
    _sh = logging.StreamHandler()
    _sh.setLevel(logging.INFO)
    _sh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_sh)


def calculate_position_size(confidence: int, total_usdt: float) -> float:
    """
    Calculate position size based on confidence level
    Strong thesis (>80%): 10-15% of total
    Good thesis (60-80%): 5-10%
    Moderate (40-60%): 3-5%
    Weak (<40%): Skip
    """
    if confidence >= 80:
        return total_usdt * 0.12  # 12%
    elif confidence >= 60:
        return total_usdt * 0.08  # 8%
    elif confidence >= 40:
        return total_usdt * 0.04  # 4%
    else:
        return 0


def check_portfolio_health(balances: list) -> Dict[str, Any]:
    """
    Check portfolio health and return analysis
    Returns: {
        'usdt_balance': float,
        'total_value': float,
        'usdt_percent': float,
        'largest_holding': {'asset': str, 'percent': float},
        'needs_rebalance': bool,
        'can_trade': bool
    }
    """
    total_value = 0.0
    usdt_balance = 0.0
    holdings = {}
    
    for bal in balances:
        asset = bal.get('asset', '')
        free = float(bal.get('free', 0))
        locked = float(bal.get('locked', 0))
        total = free + locked
        
        if total == 0:
            continue
            
        holdings[asset] = total
        total_value += total
        
        if asset == 'USDT':
            usdt_balance = total
    
    usdt_percent = (usdt_balance / total_value * 100) if total_value > 0 else 0
    
    # Find largest holding
    largest_holding = {'asset': 'USDT', 'percent': usdt_percent}
    for asset, amount in holdings.items():
        if asset != 'USDT':
            percent = (amount / total_value * 100)
            if percent > largest_holding['percent']:
                largest_holding = {'asset': asset, 'percent': percent}
    
    # Determine if rebalance needed
    needs_rebalance = usdt_percent < 15  # Less than 15% USDT
    can_trade = usdt_balance > 20  # At least $20 USDT
    
    return {
        'usdt_balance': usdt_balance,
        'total_value': total_value,
        'usdt_percent': usdt_percent,
        'largest_holding': largest_holding,
        'needs_rebalance': needs_rebalance,
        'can_trade': can_trade,
        'holdings': holdings
    }


class VibingRuntime:
    """Runtime manager for autonomous trading"""
    
    def __init__(self, max_trades: int = 5, interval_minutes: int = 15):
        self.max_trades = max_trades
        self.interval_minutes = interval_minutes
        self.active_trades: Dict[str, Dict[str, Any]] = {}
        self.discovered_coins = []
        self.running = True
        self.portfolio_health = {}
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info("Shutdown signal received, closing trades...")
        self.running = False
        
        # Emergency stop all trades
        try:
            result = stop_all_trades({})
            logger.info(f"Emergency stop result: {result}")
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            
        sys.exit(0)
    
    async def research_and_analyze(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Research a coin and form a thesis"""
        try:
            # Research the coin
            research_result = research_coin({
                "symbol": symbol
            })
            if "error" in research_result:
                logger.error(f"Research failed for {symbol}: {research_result['error']}")
                return None
                
            # Form a thesis
            thesis_result = propose_thesis({
                "symbol": symbol,
                "research_data": research_result
            })
            if "error" in thesis_result:
                logger.error(f"Thesis formation failed for {symbol}: {thesis_result['error']}")
                return None
                
            thesis = thesis_result["thesis"]

            # Smart direction correction: avoid SELL when we don't hold the base asset
            try:
                pos = check_position({"symbol": symbol})
                held_qty = float(pos.get("position", {}).get("quantity", 0) or 0)
            except Exception:
                held_qty = 0
            if thesis.get("direction") == "SELL" and held_qty <= 0:
                thesis["direction"] = "BUY"
                thesis_result["thesis"] = thesis
                logger.info(f"Adjusted direction to BUY for {symbol} (no holdings to SELL)")

            # Portfolio-guided bias (rebalance awareness)
            try:
                usdt_percent = float(self.portfolio_health.get('usdt_percent', 0))
            except Exception:
                usdt_percent = 0
            if usdt_percent >= 50 and thesis.get("direction") == "SELL" and held_qty <= 0:
                thesis["direction"] = "BUY"
                thesis_result["thesis"] = thesis
                logger.info(f"Biasing to BUY for {symbol} due to high USDT allocation ({usdt_percent:.1f}%)")

            # Log the reasoning
            logger.info(f"\nTrading Thesis for {symbol}:")
            logger.info(f"Direction: {thesis['direction']}")
            logger.info(f"Confidence: {thesis['confidence']}%")
            logger.info(f"Risk Level: {thesis['risk_level']}")
            logger.info("Reasons:")
            for reason in thesis["reasons"]:
                logger.info(f"- {reason}")
                
            return thesis_result
            
        except Exception as e:
            logger.error(f"Research and analysis failed for {symbol}: {e}")
            return None
    
    async def execute_trade(self, symbol: str, thesis: Dict[str, Any]) -> Optional[str]:
        """Execute a trade based on thesis"""
        try:
            # Only trade if confidence meets threshold
            # if thesis["confidence"] < 50:
            if thesis["confidence"] < 30:
                logger.info(f"Skipping trade for {symbol} - confidence too low ({thesis['confidence']}%)")
                return None
                
            # Open the trade (SELL sized by holdings)
            open_args = {"symbol": symbol, "thesis": thesis}
            if thesis.get("direction") == "SELL":
                try:
                    pos = check_position({"symbol": symbol})
                    qty = float(pos.get("position", {}).get("quantity", 0) or 0)
                except Exception:
                    qty = 0
                if qty <= 0:
                    logger.info(f"Skipping SELL for {symbol} - no holdings")
                    return None
                open_args["units"] = qty

            trade_result = open_trade(open_args)
            
            if "error" in trade_result:
                logger.error(f"Trade execution failed for {symbol}: {trade_result['error']}")
                return None
                
            order = trade_result["order"]
            order_id = order.get("orderId")
            
            logger.info(f"\nTrade opened for {symbol}:")
            logger.info(f"Order ID: {order_id}")
            logger.info(f"Side: {order.get('side')}")
            logger.info(f"Type: {order.get('type')}")
            logger.info(f"Quantity: {order.get('origQty')}")
            
            # Store trade info
            self.active_trades[symbol] = {
                "order_id": order_id,
                "thesis": thesis,
                "entry_time": datetime.now().isoformat()
            }
            
            return order_id
            
        except Exception as e:
            logger.error(f"Trade execution failed for {symbol}: {e}")
            return None
    
    async def monitor_trades(self):
        """Monitor active trades"""
        while self.running:
            for symbol, trade_info in list(self.active_trades.items()):
                try:
                    result = monitor_trade({
                        "symbol": symbol,
                        "order_id": trade_info["order_id"]
                    })
                    
                    if "error" in result:
                        logger.error(f"Trade monitoring failed for {symbol}: {result['error']}")
                        continue
                        
                    status = result["status"]
                    
                    # Log status
                    logger.info(f"\nTrade Status for {symbol}:")
                    logger.info(f"Status: {status['status']}")
                    logger.info(f"Entry Price: {status['entry_price']}")
                    logger.info(f"Current Price: {status['current_price']}")
                    logger.info(f"PnL: {status['pnl_percent']:.2f}%")
                    
                    # Simple exit logic - close trade if PnL exceeds thresholds
                    pnl = float(status["pnl_percent"])
                    if pnl <= -5 or pnl >= 10:
                        logger.info(f"Closing trade for {symbol} - PnL threshold reached ({pnl:.2f}%)")
                        await self.close_trade(symbol, trade_info["order_id"])
                    
                except Exception as e:
                    logger.error(f"Trade monitoring failed for {symbol}: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def close_trade(self, symbol: str, order_id: str):
        """Close a specific trade"""
        try:
            # Place closing order
            original_side = self.active_trades[symbol]["thesis"].get("direction", "BUY")
            close_side = "SELL" if original_side == "BUY" else "BUY"

            # Determine precise quantity/notional to close using check_position
            pos = check_position({"symbol": symbol})
            if "error" in pos:
                logger.error(f"Could not get position for closing {symbol}: {pos['error']}")
                return
            qty = float(pos.get("position", {}).get("quantity", 0) or 0)
            if qty <= 0:
                logger.info(f"No position quantity found for {symbol}; skipping close")
                del self.active_trades[symbol]
                return

            close_params = {"symbol": symbol, "thesis": {"direction": close_side, "confidence": 100, "reasoning": "Autonomous close"}}
            if close_side == "SELL":
                # Close long: sell base units equal to held quantity
                close_params["units"] = qty
            else:
                # Close short: buy back base units; open_trade will convert units to quote notional
                close_params["units"] = qty

            result = open_trade(close_params)
            
            if "error" in result:
                logger.error(f"Trade closing failed for {symbol}: {result['error']}")
                return
                
            logger.info(f"Closed trade for {symbol}")
            del self.active_trades[symbol]
            
        except Exception as e:
            logger.error(f"Trade closing failed for {symbol}: {e}")
    
    async def discover_trending_coins(self) -> list:
        """Discover trending coins using general-research"""
        try:
            result = general_research({})
            if "error" in result:
                logger.error(f"Discovery failed: {result['error']}")
                return []
            
            trending_coins = result.get('research', {}).get('trending_coins', [])
            symbols = [coin['symbol'] for coin in trending_coins]
            logger.info(f"Discovered {len(symbols)} trending coins: {symbols}")
            return symbols
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return []
    
    async def check_and_rebalance(self) -> bool:
        """Check portfolio health and rebalance if needed"""
        try:
            result = check_balance({})
            if "error" in result:
                logger.error(f"Position check failed: {result['error']}")
                return False
            
            balances = result.get('position', {}).get('balances', [])
            self.portfolio_health = check_portfolio_health(balances)
            
            logger.info(f"Portfolio health: {self.portfolio_health['usdt_percent']:.1f}% USDT")
            logger.info(f"Largest holding: {self.portfolio_health['largest_holding']['asset']} "
                       f"({self.portfolio_health['largest_holding']['percent']:.1f}%)")
            
            return self.portfolio_health['can_trade']
            
        except Exception as e:
            logger.error(f"Portfolio check failed: {e}")
            return False
    
    async def autonomous_cycle(self):
        """One complete autonomous trading cycle"""
        logger.info("\n=== Starting Autonomous Trading Cycle ===")
        
        # Step 1: Check portfolio health
        can_trade = await self.check_and_rebalance()
        if not can_trade:
            logger.warning("Portfolio doesn't meet trading criteria - skipping cycle")
            return
        
        # Step 2: Discover trending coins (if needed)
        if len(self.active_trades) < self.max_trades:
            discovered = await self.discover_trending_coins()
            for symbol in discovered[:self.max_trades - len(self.active_trades)]:
                if symbol not in self.active_trades:
                    # Step 3: Research coin
                    thesis_result = await self.research_and_analyze(symbol)
                    if thesis_result:
                        # Step 4: Execute trade
                        await self.execute_trade(symbol, thesis_result["thesis"])
        
        logger.info("=== Cycle Complete ===\n")
    
    async def run(self):
        """Main runtime loop"""
        logger.info(f"Starting Vibing Runtime")
        logger.info(f"Max trades: {self.max_trades}")
        logger.info(f"Research interval: {self.interval_minutes} minutes")
        
        # Start trade monitoring
        monitor_task = asyncio.create_task(self.monitor_trades())
        
        while self.running:
            # Run autonomous cycle
            await self.autonomous_cycle()
            
            # Wait for interval
            await asyncio.sleep(self.interval_minutes * 60)
        
        # Cleanup
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Vibing Runtime for Autonomous Trading")
    parser.add_argument("--max-trades", "--max_trades", type=int, default=5, help="Maximum concurrent trades")
    parser.add_argument("--interval-minutes", "--interval_minutes", type=int, default=15, help="Research interval in minutes")
    
    args = parser.parse_args()
    
    runtime = VibingRuntime(
        max_trades=args.max_trades,
        interval_minutes=args.interval_minutes
    )
    
    try:
        asyncio.run(runtime.run())
    except KeyboardInterrupt:
        logger.info("Runtime stopped by user")
    except Exception as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
