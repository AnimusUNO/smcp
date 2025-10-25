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

from cli import research_coin, propose_thesis, open_trade, monitor_trade, stop_all_trades

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(VIBING_DIR / "runtime.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vibing.runtime")

class VibingRuntime:
    """Runtime manager for autonomous trading"""
    
    def __init__(self, symbols: list, dry_run: bool = True):
        self.symbols = symbols
        self.dry_run = dry_run
        self.active_trades: Dict[str, Dict[str, Any]] = {}
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info("Shutdown signal received, closing trades...")
        self.running = False
        
        # Emergency stop all trades
        try:
            result = stop_all_trades({"dry_run": self.dry_run})
            logger.info(f"Emergency stop result: {result}")
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            
        sys.exit(0)
    
    async def research_and_analyze(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Research a coin and form a thesis"""
        try:
            # Research the coin
            research_result = research_coin({"symbol": symbol})
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
            if thesis["confidence"] < 50:
                logger.info(f"Skipping trade for {symbol} - confidence too low ({thesis['confidence']}%)")
                return None
                
            # Open the trade
            trade_result = open_trade({
                "symbol": symbol,
                "thesis": thesis,
                "dry_run": self.dry_run
            })
            
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
                        "order_id": trade_info["order_id"],
                        "dry_run": self.dry_run
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
            close_side = "SELL" if self.active_trades[symbol]["thesis"]["direction"] == "BUY" else "BUY"
            
            result = open_trade({
                "symbol": symbol,
                "thesis": {"direction": close_side},
                "dry_run": self.dry_run
            })
            
            if "error" in result:
                logger.error(f"Trade closing failed for {symbol}: {result['error']}")
                return
                
            logger.info(f"Closed trade for {symbol}")
            del self.active_trades[symbol]
            
        except Exception as e:
            logger.error(f"Trade closing failed for {symbol}: {e}")
    
    async def run(self):
        """Main runtime loop"""
        logger.info(f"Starting Vibing Runtime (Dry Run: {self.dry_run})")
        logger.info(f"Monitoring symbols: {', '.join(self.symbols)}")
        
        # Start trade monitoring
        monitor_task = asyncio.create_task(self.monitor_trades())
        
        while self.running:
            for symbol in self.symbols:
                if symbol not in self.active_trades:
                    # Research and potentially open new trade
                    thesis_result = await self.research_and_analyze(symbol)
                    if thesis_result:
                        await self.execute_trade(symbol, thesis_result["thesis"])
            
            await asyncio.sleep(300)  # Check for new trades every 5 minutes
        
        # Cleanup
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Vibing Runtime for Autonomous Trading")
    parser.add_argument("--symbols", required=True, help="Comma-separated list of trading pairs")
    parser.add_argument("--dry-run", type=bool, default=True, help="Run in dry-run mode")
    
    args = parser.parse_args()
    
    symbols = [s.strip() for s in args.symbols.split(",")]
    runtime = VibingRuntime(symbols=symbols, dry_run=args.dry_run)
    
    try:
        asyncio.run(runtime.run())
    except KeyboardInterrupt:
        logger.info("Runtime stopped by user")
    except Exception as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
