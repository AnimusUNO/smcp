# Vibing Plugin Refactoring

## Structure After Refactoring

- `aster_client.py` - AsterClient class and API wrapper (DONE)
- `config.py` - Configuration management (DONE)
- `utils.py` - Utility functions like round_to_step (DONE)
- `trading_logic.py` - All trading operations (research_coin, propose_thesis, open_trade, etc.) (IN PROGRESS)
- `cli.py` - CLI interface only, imports from above modules (TO UPDATE)

## Functions to Move to trading_logic.py

- research_coin
- propose_thesis
- open_trade
- monitor_trade
- check_balance
- check_position
- general_research
- start_autonomous
- stop_autonomous
- stop_all_trades

## Imports Needed in trading_logic.py

- from aster_client import AsterClient
- from config import load_config
- from utils import round_to_step
- Standard library imports (json, logging, datetime, etc.)

## CLI.py Will Import

- from aster_client import AsterClient
- from config import load_config
- from trading_logic import (all trading functions)
- Keep only: argparse setup, main() function, command routing

