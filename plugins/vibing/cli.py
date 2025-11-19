#!/usr/bin/env python3
"""
Vibing Plugin - CLI Interface

CLI entry point for the vibing plugin. Imports trading logic from separate modules.
"""

import argparse
import json
import sys
from pathlib import Path

# Configure logging
from pathlib import Path
import logging

VIBING_DIR = Path(__file__).parent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(VIBING_DIR / "vibing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vibing")

# Import trading logic from separate modules
from trading_logic import (
    research_coin,
    propose_thesis,
    open_trade,
    monitor_trade,
    check_balance,
    check_position,
    general_research,
    start_autonomous,
    stop_autonomous,
    stop_all_trades
)


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
