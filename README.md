# Sanctum Letta MCP Server

[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol%20Compliant-green.svg)](https://modelcontextprotocol.io/)

A powerful, plugin-based Model Context Protocol (MCP) server for the Sanctum Letta AI framework. This server provides seamless integration between AI clients and external tools through a robust plugin architecture.

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
   git clone https://github.com/markrizzn/sanctum-letta-mcp.git
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

The server will start on `http://localhost:8000` by default.

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PORT` | `8000` | Port for the MCP server |
| `MCP_PLUGINS_DIR` | `smcp/plugins/` | Directory containing plugins |

### Example Configuration

```bash
export MCP_PORT=9000
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
- The Sanctum Letta team for the AI framework integration

## 📞 Support

For support, questions, or contributions:

- **Author**: Mark Rizzn Hopkins
- **Repository**: https://github.com/markrizzn/sanctum-letta-mcp
- **Issues**: https://github.com/markrizzn/sanctum-letta-mcp/issues

---

**Part of the Sanctum Suite** - A comprehensive AI framework for modern applications. 