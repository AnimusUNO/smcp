# Railway Environment Variables

This document lists all environment variables needed for deploying the SMCP server to Railway.

## Required Environment Variables

### Core Server Variables
- **`PORT`** (Auto-set by Railway)
  - Railway automatically sets this. The server will use it automatically.
  - Default fallback: `8000` or `MCP_PORT` if set

### Vibing Plugin (Cryptocurrency Trading)
**Required if you want to use trading features:**
- **`API_KEY`** - Your Aster Finance API key
- **`API_SECRET_KEY`** - Your Aster Finance API secret key

### Puppetry Plugin (Twitter Integration)
**Required if you want to use Twitter posting features:**
- **`TWITTER_API_KEY`** - Twitter API consumer key
- **`TWITTER_API_KEY_SECRET`** - Twitter API consumer secret
- **`TWITTER_ACCESS_TOKEN`** - Twitter access token
- **`TWITTER_ACCESS_TOKEN_SECRET`** - Twitter access token secret

## Optional Environment Variables

### Server Configuration
- **`MCP_HOST`** - Host to bind to (default: `127.0.0.1`, but Railway should use `0.0.0.0`)
- **`MCP_PORT`** - Port override (Railway sets `PORT` automatically, but you can override with this)
- **`MCP_PLUGINS_DIR`** - Custom plugin directory path (default: `plugins/`)

### Logging Configuration
- **`MCP_LOG_LEVEL`** - Logging level (default: `INFO`)
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **`MCP_LOG_JSON`** - Enable JSON-formatted logs (set to `true` to enable)
- **`MCP_LOG_FILE`** - Log file path (default: `logs/mcp_server.log`)
- **`MCP_LOG_ROTATION`** - Log rotation strategy
  - Options: `size`, `time`, or `none`
- **`MCP_DISABLE_FILE_LOG`** - Disable file logging (set to `true` to disable)

## How to Set Environment Variables in Railway

1. Go to your Railway project dashboard
2. Select your service
3. Click on the **"Variables"** tab
4. Click **"New Variable"**
5. Add each variable with its value
6. Railway will automatically restart your service when variables are added/updated

## Minimum Setup for Basic Functionality

If you only want the server to run (without trading or Twitter features), you don't need any environment variables - Railway will automatically set `PORT`.

## Full Setup Example

For full functionality with both trading and Twitter features, set these variables:

```
API_KEY=your_aster_api_key_here
API_SECRET_KEY=your_aster_api_secret_here
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_KEY_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here
```

## Security Notes

⚠️ **Important**: Never commit these values to git. They are already in `.gitignore`, but make sure to:
- Set them only in Railway's dashboard (not in code)
- Use Railway's secret management features
- Rotate keys regularly
- Use read-only API keys when possible

