# Sanctum Core Module: MCP Server

[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol%20Compliant-green.svg)](https://modelcontextprotocol.io/)

> **🚨 IMPORTANT NOTICE FOR NEW DEVELOPERS** 🚨
> 
> **This repository has been graduated to Sanctum Core Module status!**
> 
> **For new development, please use the canonical source:**
> **→ [github.com/sanctumos/smcp](https://github.com/sanctumos/smcp) ←**
> 
> This repository remains available for users who prefer to continue using this version, but new features and updates will be developed in the official Sanctum repository.

A powerful, plugin-based Model Context Protocol (MCP) server for the Sanctum AI framework. This server provides seamless integration between AI clients and external tools through a robust plugin architecture. As a Sanctum Core Module, it represents the official, production-ready implementation maintained by the Sanctum team.

## 🚀 Features

- **Plugin Architecture**: Easy-to-write plugins for any external service or tool
- **MCP Protocol Compliant**: Full support for the Model Context Protocol specification
- **SSE Transport**: Real-time server-sent events for efficient communication
- **JSON-RPC 2.0**: Standardized request/response handling
- **Auto-Discovery**: Automatic plugin detection and tool registration
- **Health Monitoring**: Built-in health checks and status reporting
- **Production Ready**: Comprehensive error handling and logging

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/sanctumos/smcp.git
   cd sanctum-letta-mcp
   ```

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
   python smcp/mcp_server.py
   ```

The server will start on `http://localhost:8000` by default with **localhost + Docker container access** for development environments.

### Security Features

By default, the server binds to all interfaces (0.0.0.0) to allow connections from both the local machine and Docker containers running on the same host. This is ideal for development environments where Docker containers need to communicate with the MCP server.

**For localhost-only access** (more restrictive):
```bash
python smcp/mcp_server.py --host 127.0.0.1
```

**To allow external connections** (use with caution):
```bash
python smcp/mcp_server.py --allow-external
```

**Custom port**:
```bash
python smcp/mcp_server.py --port 9000
```

**Custom host binding**:
```bash
python smcp/mcp_server.py --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PORT` | `8000` | Port for the MCP server |
| `MCP_PLUGINS_DIR` | `smcp/plugins/` | Directory containing plugins |
| `MCP_HOST` | `0.0.0.0` | Host to bind to (default: all interfaces for Docker compatibility) |

### Example Configuration

```bash
# Default: localhost + Docker containers
python smcp/mcp_server.py

# Custom port
export MCP_PORT=9000
python smcp/mcp_server.py

# Localhost-only (more restrictive)
python smcp/mcp_server.py --host 127.0.0.1

# Custom plugins directory
export MCP_PLUGINS_DIR=/path/to/custom/plugins
python smcp/mcp_server.py
```

## 🔌 Plugin Development

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
/opt/sanctum/plugins/
├── botfather/
├── devops/
└── custom-plugin/

# MCP server plugin directory with symlinks
smcp/plugins/
├── botfather -> /opt/sanctum/plugins/botfather
├── devops -> /opt/sanctum/plugins/devops
└── custom-plugin -> /opt/sanctum/plugins/custom-plugin
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
export MCP_PLUGINS_DIR=/opt/sanctum/plugins
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
   
   A sample plugin for the Sanctum Letta MCP Server.
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

Logs are written to `mcp.log` and stdout. Configure logging levels in `smcp/mcp_server.py`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 smcp/ tests/

# Run type checking
mypy smcp/

# Run tests with coverage
python -m pytest tests/ --cov=smcp --cov-report=html
```

## 📄 License

This project is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the protocol specification
- [FastMCP](https://github.com/microsoft/fastmcp) for the server framework
- The Sanctum team for the AI framework integration
- The Letta team for the kernel for SanctumOS

## 📞 Support

For support, questions, or contributions:

- **Author**: Mark Rizzn Hopkins
- **Repository**: https://github.com/sanctumos/smcp
- **Issues**: https://github.com/sanctumos/smcp/issues

---

**Part of the Sanctum Suite** - A comprehensive AI framework for modern applications.

> **Note**: This repository has been graduated to **Sanctum Core Module** status. The canonical source is now maintained at [github.com/sanctumos/smcp](https://github.com/sanctumos/smcp). This repository remains available for users who prefer to continue using this version. 