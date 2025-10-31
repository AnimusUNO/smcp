# Getting Started with SMCP

Welcome to SMCP (Animus Model Context Protocol Server)! This guide will help you get up and running quickly, whether you're using the master Animus installer or running SMCP standalone.

## 🚀 Quick Start Options

### Option 1: Master Animus Installer (Recommended)
The easiest way to get started is through the master Animus installer, which handles all configuration automatically:

```bash
# Install via master Animus installer
# (This will be documented in the main Animus documentation)
```

### Option 2: Standalone Installation
For development, testing, or custom deployments, you can run SMCP standalone:

```bash
# Clone the repository
git clone https://github.com/animusos/smcp.git
cd smcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python smcp.py
```

## 🔧 First-Time Setup

### Prerequisites Check
Before starting, ensure you have:
- **Python 3.8+** installed and accessible
- **pip** package manager available
- **Network access** for dependency installation

### Initial Configuration
SMCP comes with sensible defaults, but you can customize:

```bash
# Check available options
python smcp.py --help

# Run with custom port
python smcp.py --port 9000

# Run with custom host binding
python smcp.py --host 127.0.0.1
```

## 🌐 Accessing Your Server

### Default Endpoints
Once running, SMCP provides these endpoints:

- **Main Server**: `http://localhost:8000`
- **SSE Endpoint**: `http://localhost:8000/sse`
- **Message Endpoint**: `http://localhost:8000/messages/`

### Health Check
Verify your server is running:

```bash
curl -X POST http://localhost:8000/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"health","arguments":{}}}'
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "uptime": "0:00:30"
  }
}
```

## 🔌 Your First Plugin

### Built-in Plugins
SMCP comes with example plugins to get you started:

- **botfather**: Telegram Bot API integration
- **devops**: Deployment and infrastructure management

### Testing a Plugin
```bash
# Test the botfather plugin
python smcp/plugins/botfather/cli.py --help

# Test the devops plugin
python smcp/plugins/devops/cli.py --help
```

## 🔗 Connecting Clients

### Letta Client Connection
For Letta clients, see the [Letta MCP Connection Guide](Letta-MCP-Connection-Guide.md).

### Custom Client Example
```python
import httpx
import json

async def test_connection():
    async with httpx.AsyncClient() as client:
        # Initialize connection
        response = await client.post(
            "http://localhost:8000/messages/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                }
            }
        )
        print(f"Connection status: {response.status_code}")
        print(f"Response: {response.json()}")

# Run the test
import asyncio
asyncio.run(test_connection())
```

## 🚨 Common Issues & Solutions

### Port Already in Use
```bash
# Error: Address already in use
# Solution: Use a different port
python smcp.py --port 9000
```

### Permission Denied
```bash
# Error: Permission denied
# Solution: Check file permissions and run with appropriate user
chmod +x smcp.py
```

### Plugin Not Found
```bash
# Error: Plugin directory not found
# Solution: Set custom plugin directory
export MCP_PLUGINS_DIR=/path/to/your/plugins
python smcp.py
```

### Network Binding Issues
```bash
# Error: Cannot bind to address
# Solution: Use localhost-only binding
python smcp.py --host 127.0.0.1
```

## 📚 Next Steps

Now that you're up and running:

1. **Explore Plugins**: Check out the [Plugin Development Guide](plugin-development-guide.md)
2. **API Reference**: Review the [Complete API Documentation](api-reference.md)
3. **Architecture**: Understand the [MCP Reference Architecture](MCP-Reference-Architecture.md)
4. **Troubleshooting**: Visit the [Troubleshooting Guide](troubleshooting.md)

### Vibing Usage Guidance

For cryptocurrency trading with the Vibing plugin, use the Animus TUI (Vibe mode). Running Vibing via this SMCP server was for development/testing and is not recommended for production. The TUI provides:

- End-to-end orchestration of the trading workflow
- Integrated Twitter posting via Puppetry
- Better UX and visibility for long, multi-step flows

Note: Direct SMCP Vibing calls may be less efficient and won’t have full social posting access.

## 🆘 Need Help?

- **Documentation**: Check the [main documentation index](../README.md#-documentation)
- **Website**: https://animus.uno
- **X (Twitter)**: https://x.com/animusuno

---

**Ready to build amazing AI-powered applications?** Start with the [Plugin Development Guide](plugin-development-guide.md) to create your first custom plugin!
