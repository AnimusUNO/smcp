# Vibing Plugin

Autonomous trading plugin for Letta agents that enables research-driven trading through the Aster API.

## Features

- Coin research and analysis
- Automated thesis formation
- Trade execution with clear reasoning
- Real-time trade monitoring
- Emergency stop functionality
- Dry-run mode for testing
- Comprehensive logging

## Commands

- `research-coin`: Analyze a trading pair using market data
- `propose-thesis`: Form a trading thesis based on research
- `open-trade`: Execute a trade based on thesis
- `monitor-trade`: Track an open trade's status
- `stop-all`: Emergency stop - cancel all trades

## Configuration

Create a `config/config.json` file with your Aster API credentials:

```json
{
    "api_key": "your_api_key",
    "api_secret": "your_api_secret"
}
```

## Usage

### CLI Usage

```bash
# Research a coin
python cli.py research-coin --symbol BTCUSDT

# Form a thesis
python cli.py propose-thesis --symbol BTCUSDT --research-data '{"analysis":...}'

# Open a trade
python cli.py open-trade --symbol BTCUSDT --thesis '{"direction":"BUY"...}' --dry-run true

# Monitor a trade
python cli.py monitor-trade --symbol BTCUSDT --order-id 12345 --dry-run true

# Emergency stop
python cli.py stop-all --dry-run false
```

### Runtime Usage

The runtime script enables continuous autonomous trading:

```bash
# Start runtime in dry-run mode
python runtime.py --symbols BTCUSDT,ETHUSDT --dry-run true

# Start runtime in live mode
python runtime.py --symbols BTCUSDT,ETHUSDT --dry-run false
```

## Safety Features

- Dry-run mode for testing
- Confidence thresholds for trade execution
- Clear reasoning and logging
- Emergency stop functionality
- Graceful shutdown handling

## Logging

Logs are written to:
- `vibing.log`: CLI operations
- `runtime.log`: Runtime operations

## Dependencies

- Python 3.8+
- requests
- Aster API access
