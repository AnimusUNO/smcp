# SMCP

[![License: AGPLv3](https://img.shields.io/badge/License-AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0) [![Docs License: CC BY-SA 4.0](https://img.shields.io/badge/Docs%20License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)]
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol%20Compliant-green.svg)](https://modelcontextprotocol.io/)]
[![Animus Core Module](https://img.shields.io/badge/Animus-Core%20Module-blue.svg)](https://animus.uno)

**Animus Core Module: Model Context Protocol Server**

SMCP is a powerful, plugin-based Model Context Protocol (MCP) server for the Animus Letta AI framework. This server provides seamless integration between AI clients and external tools through a robust plugin architecture. As an Animus Core Module, it represents the official, production-ready implementation maintained by the Animus team.

## 🚀 Features

- **Plugin Architecture**: Easy-to-write plugins for any external service or tool
- **MCP Protocol Compliant**: Full support for the Model Context Protocol specification
- **SSE Transport**: Real-time server-sent events for efficient communication
- **JSON-RPC 2.0**: Standardized request/response handling
- **Auto-Discovery**: Automatic plugin detection and tool registration
- **Health Monitoring**: Built-in health checks and status reporting
- **Production Ready**: Comprehensive error handling and logging

## 📖 **Ready to Get Started?**

**New to SMCP?** Start with our comprehensive documentation:

- **[🚀 Getting Started Guide](docs/getting-started.md)** - **Complete setup in 5 minutes**
- **[🔌 Plugin Development](docs/plugin-development-guide.md)** - **Build your first plugin**
- **[📋 Examples](docs/examples.md)** - **Copy-paste working code**
- **[🚨 Troubleshooting](docs/troubleshooting.md)** - **Solve any problem quickly**

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Deployment Options

**Option 1: Master Animus Installer (Recommended)**
The master Animus installer will automatically deploy SMCP to the correct location within your Animus environment with all necessary configurations.

**Option 2: Standalone Repository**
SMCP can also function as a standalone repository for development, testing, or custom deployments.

### Quick Start (Standalone)

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**
   ```bash
   python smcp.py
   ```

The server will start on `http://localhost:8000` by default with **localhost + Docker container access** for development environments.

### Security Features

By default, the server binds to all interfaces (0.0.0.0) to allow connections from both the local machine and Docker containers running on the same host. This is ideal for development environments where Docker containers need to communicate with the MCP server.

**For localhost-only access** (more restrictive):
```bash
python smcp.py --host 127.0.0.1
```

**To allow external connections** (use with caution):
```bash
python smcp.py --allow-external
```

**Custom port**:
```bash
python smcp.py --port 9000
```

**Custom host binding**:
```bash
python smcp.py --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Master Animus Installer Integration

When deployed via the master Animus installer, SMCP is automatically:
- Installed to the correct location within your Animus environment
- Configured with appropriate environment variables
- Integrated with the Animus plugin management system
- Set up with proper networking and security configurations

> **Note**: The following configuration options apply to standalone deployments. When using the master installer, these are handled automatically.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PORT` | `8000` | Port for the MCP server |
| `MCP_PLUGINS_DIR` | `smcp/plugins/` | Directory containing plugins |
| `MCP_HOST` | `127.0.0.1` | Host to bind to (default: localhost-only for security) |

### Example Configuration

```bash
# Default: localhost-only (secure)
python smcp/mcp_server.py

# Custom port
export MCP_PORT=9000
python smcp/mcp_server.py

# Localhost-only (explicit)
python smcp.py --host 127.0.0.1

# Allow external connections (use with caution)
python smcp.py --allow-external

# Custom plugins directory
export MCP_PLUGINS_DIR=/path/to/custom/plugins
python smcp/mcp_server.py
```

## 🔌 Plugin Development

> **Note**: When deployed via the master Animus installer, plugins are automatically discovered and managed. The following applies to standalone deployments and custom plugin development.

For comprehensive plugin development documentation, see [docs/dev/plugin-development-guide.md](docs/dev/plugin-development-guide.md).

### Plugin Structure

Each plugin should follow this directory structure:

```
plugins/
├── your_plugin/
│   ├── __init__.py
│   ├── cli.py          # Main plugin interface
│   └── README.md       # Plugin documentation
```

### Plugin Deployment with Symlinks

The server supports symbolic links for flexible plugin deployment. You can centralize plugins in a designated location and use symlinks for discovery:

#### Centralized Plugin Management

```
# Central plugin repository
/opt/animus/plugins/
├── botfather/
├── devops/
└── custom-plugin/

# MCP server plugin directory with symlinks
smcp/plugins/
├── botfather -> /opt/animus/plugins/botfather
├── devops -> /opt/animus/plugins/devops
└── custom-plugin -> /opt/animus/plugins/custom-plugin
```

#### Benefits

- **Separation of Concerns**: Keep MCP server code separate from plugin implementations
- **Centralized Management**: Manage plugins in a designated repository
- **Dynamic Loading**: Add/remove plugins by creating/removing symlinks
- **Version Control**: Maintain plugins in separate repositories
- **Deployment Flexibility**: Deploy plugins independently of the MCP server

#### Environment Variable Override

You can override the plugin directory using the `MCP_PLUGINS_DIR` environment variable:

```bash
# Use custom plugin directory
export MCP_PLUGINS_DIR=/opt/animus/plugins
python smcp/mcp_server.py
```

### Creating a Plugin

1. **Create plugin directory**
   ```bash
   mkdir -p smcp/plugins/my_plugin
   ```

2. **Create the CLI interface** (`smcp/plugins/my_plugin/cli.py`)
   ```python
   #!/usr/bin/env python3
   """
   My Plugin CLI
   
   A sample plugin for the Animus Letta MCP Server.
   """
   
   import argparse
   import json
   import sys
   
   def main():
       parser = argparse.ArgumentParser(description="My Plugin CLI")
       subparsers = parser.add_subparsers(dest="command", help="Available commands")
       
       # Add your command
       cmd_parser = subparsers.add_parser("my-command", help="Execute my command")
       cmd_parser.add_argument("--param", required=True, help="Required parameter")
       cmd_parser.add_argument("--optional", default="default", help="Optional parameter")
       
       args = parser.parse_args()
       
       if args.command == "my-command":
           result = execute_my_command(args.param, args.optional)
           print(json.dumps(result))
       else:
           parser.print_help()
           sys.exit(1)
   
   def execute_my_command(param, optional):
       """Execute the main command logic."""
       # Your plugin logic here
       return {
           "status": "success",
           "param": param,
           "optional": optional,
           "message": "Command executed successfully"
       }
   
   if __name__ == "__main__":
       main()
   ```

3. **Make it executable**
   ```bash
   chmod +x smcp/plugins/my_plugin/cli.py
   ```

4. **Test your plugin**
   ```bash
   python smcp/plugins/my_plugin/cli.py my-command --param "test" --optional "value"
   ```

### Plugin Best Practices

1. **Command Structure**: Use descriptive command names with hyphens
2. **Parameter Validation**: Always validate required parameters
3. **Error Handling**: Return meaningful error messages
4. **JSON Output**: Return structured JSON for easy parsing
5. **Documentation**: Include help text for all commands and parameters

### Available Plugin Examples

- **botfather**: Telegram Bot API integration
- **devops**: Deployment and infrastructure management

## 🔗 MCP Protocol Integration

### Endpoints

- **SSE Endpoint**: `GET /sse` - Server-sent events for real-time communication
- **Message Endpoint**: `POST /messages/` - JSON-RPC 2.0 message handling

### Protocol Flow

1. **Connection**: Client establishes SSE connection
2. **Initialization**: Client sends `initialize` request
3. **Capability Exchange**: Server responds with available tools
4. **Tool Execution**: Client can call registered tools
5. **Event Streaming**: Server sends events via SSE

### Example Client Integration

```python
import httpx
import json

async def connect_to_mcp():
    base_url = "http://localhost:8000"
    
    # Initialize connection
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "clientInfo": {"name": "my-client", "version": "1.0.0"}
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/messages/", json=init_request)
        data = response.json()
        
        # List available tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = await client.post(f"{base_url}/messages/", json=tools_request)
        tools = response.json()["result"]["tools"]
        
        # Call a tool
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "health",
                "arguments": {}
            }
        }
        
        response = await client.post(f"{base_url}/messages/", json=call_request)
        result = response.json()["result"]
        
        return result
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v

# Run with coverage
python -m pytest tests/ --cov=smcp --cov-report=html
```

### Test Categories

- **Unit Tests**: Core functionality and plugin system
- **Integration Tests**: MCP protocol and endpoint testing
- **E2E Tests**: Complete workflow validation

## 📊 Monitoring

### Health Check

The server provides a built-in health check tool:

```bash
curl -X POST http://localhost:8000/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"health","arguments":{}}}'
```

### Logging

Logs are written to stdout and, by default, to `logs/mcp_server.log` with rotation. Configure behavior via environment variables:

- `MCP_LOG_LEVEL` (default `INFO`)
- `MCP_LOG_JSON` (set `true` for JSON logs)
- `MCP_LOG_FILE` (default `logs/mcp_server.log`)
- `MCP_LOG_ROTATION` (`size`, `time`, or `none`)
- `MCP_DISABLE_FILE_LOG` (set `true` to disable file logging)

See `docs/api-reference.md` for the full matrix.

## 🪙 Vibing Plugin: Recent Updates (Aster API)

Key operational changes to ensure smooth trading and better agent UX:

- Removed all dry-run flags; all vibing operations are real.
- Split tools:
  - `vibing_check-balance` (no params): overall balances + open orders
  - `vibing_check-position` (symbol required): P/L for a specific pair
- `vibing_open-trade`:
  - BUY uses `quoteOrderQty` (USDT)
  - SELL accepts explicit base `units`/`quantity` (top-level or in `thesis`)
  - Enforces `MIN_NOTIONAL` = $5.00; applies `LOT_SIZE`/`MARKET_LOT_SIZE`
  - Aster auth: signatures computed over stringified, sorted params; signed POSTs use `application/x-www-form-urlencoded`; signed GETs use canonical query strings; include `recvWindow`
- `vibing_monitor-trade`: queries `/api/v1/order` (all statuses), falls back to `/api/v1/openOrders` (open only)
- Agent behavior (system prompt):
  - After each tool, provide a concise human summary
  - After multi-step operations, always provide a final summary
  - Manual workflow guidance: balance → research → position → thesis → trade → tweet → monitor

See `animus/system_prompt.md` for the exact workflow and behavior requirements.

### Important: Use Vibing from the TUI (not directly via SMCP)

- The Vibing trading workflow should be run from the Animus TUI, which is production-ready and integrates all required capabilities (including Twitter posting via Puppetry).
- Invoking Vibing tools directly through this SMCP server was used for development/testing only and is not recommended for production:
  - It may not operate as efficiently or reliably as the TUI flow
  - It will not have access to the full Twitter plugins and orchestration needed for automated tweet posting
- Recommendation: Use the TUI’s Vibe mode for day-to-day trading operations. Reserve SMCP-level Vibing calls for development/debugging.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run linting
flake8 smcp/ tests/

# Run type checking
mypy smcp/

# Run tests with coverage
python -m pytest tests/ --cov=smcp --cov-report=html
```

## 📚 **Comprehensive Documentation**

### 🚀 **Getting Started**
- **[📖 Getting Started Guide](docs/getting-started.md)** - **NEW USERS START HERE!** Complete setup and first steps
- **[🔌 Plugin Development Guide](docs/plugin-development-guide.md)** - Create and deploy custom plugins
- **[📋 Examples Guide](docs/examples.md)** - **Practical examples** and code samples for all use cases

### 🔧 **Configuration & Deployment**
- **[🚀 Deployment Guide](docs/deployment-guide.md)** - **Production deployment** with systemd, Docker, and reverse proxy
- **[🔧 Configuration Guide](docs/api-reference.md)** - Complete API documentation and configuration options

### 🔗 **Integration & Troubleshooting**
- **[🔗 Letta MCP Connection Guide](docs/Letta-MCP-Connection-Guide.md)** - Connect Letta clients to SMCP
- **[🚨 Troubleshooting Guide](docs/troubleshooting.md)** - **Common issues and solutions** for all problems
- **[📊 Monitoring & Health Checks](docs/deployment-guide.md#monitoring-and-logging)** - Production monitoring setup

### 👨‍💻 **Developer Resources**
- **[📋 Examples Guide](docs/examples.md)** - **Practical examples** and code samples for all use cases

## 📄 License

This project uses dual licensing:

- **Code**: Licensed under the GNU Affero General Public License v3.0 (AGPLv3) - see the [LICENSE](LICENSE) file for details.
- **Documentation & Data**: Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License (CC-BY-SA 4.0) - see the [LICENSE-DOCS](LICENSE-DOCS) file for details.

**Important**: AGPLv3 is a copyleft license that requires any derivative works to also be open source. If you modify and distribute this software, you must make your source code available under the same license.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the protocol specification
- [FastMCP](https://github.com/microsoft/fastmcp) for the server framework
- The Animus team for the AI framework integration
- The Letta team for the kernel for AnimusOS

## 📞 Support

For support, questions, or contributions:

- **Author**: Mark Rizzn Hopkins
- **Website**: https://animus.uno
- **X (Twitter)**: https://x.com/animusuno

---

**Part of the Animus Suite** - A comprehensive AI framework for modern applications. 