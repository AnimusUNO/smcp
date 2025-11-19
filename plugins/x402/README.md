# x402 Plugin for SMCP

SMCP integration plugin for the x402 vending machine server. Enables agents to interact with the x402 payment-required vending machine.

## Features

- **List Items**: Get all available items from the vending machine
- **Check Item**: Get details of a specific item
- **Health Check**: Check x402 server health and status
- **Monitor Purchases**: Monitor for new purchases (lightweight polling)

## Setup

### Environment Variables

Set the following environment variable:

- `X402_SERVER_URL`: URL of the x402 vending machine server (e.g., `https://vending-machine-x402-production.up.railway.app`)

### Installation

The plugin uses `requests` which should already be in the main SMCP requirements.txt. If not, install it:

```bash
pip install requests>=2.31.0
```

## Available Tools

### `x402_list-items`

List all available items from the x402 vending machine.

**Example:**
```json
{
  "command": "x402_list-items"
}
```

### `x402_check-item`

Check details of a specific item.

**Parameters:**
- `item_id` (string, required): Item ID to check (e.g., 'coffee', 'energy-drink')

**Example:**
```json
{
  "command": "x402_check-item",
  "item_id": "coffee"
}
```

### `x402_health-check`

Check x402 server health and status.

**Example:**
```json
{
  "command": "x402_health-check"
}
```

### `x402_monitor-purchases`

Monitor for new purchases. Use this periodically to check for new purchases that may require agent response (e.g., posting tweets about purchases).

**Note:** Currently checks server health. Full purchase monitoring requires the x402 server to expose a `/purchases` endpoint in the future.

**Example:**
```json
{
  "command": "x402_monitor-purchases"
}
```

## Usage

The plugin is automatically discovered by the SMCP server. Once the `X402_SERVER_URL` environment variable is set, the tools will be available to agents.

## Architecture

- **Polling-based monitoring**: Lightweight polling approach for purchase monitoring
- **Environment-based configuration**: Server URL configured via environment variable (no hardcoding)
- **Error handling**: Comprehensive error handling and logging

## Future Enhancements

- Add `/purchases` endpoint to x402 server for full purchase history
- Webhook support for real-time purchase notifications
- Purchase filtering and search capabilities

