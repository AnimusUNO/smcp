# Plugin Development Guide

A comprehensive guide for developing plugins for the Animus Letta MCP Server.

## Overview

Plugins are the core of the MCP server's extensibility. Each plugin provides tools that can be called by AI clients through the MCP protocol. This guide will walk you through creating, testing, and deploying plugins.

## Plugin Architecture

### Directory Structure

```
smcp/plugins/
├── your_plugin/
│   ├── __init__.py          # Plugin metadata (optional)
│   ├── cli.py              # Main plugin interface (required)
│   ├── requirements.txt    # Plugin dependencies (optional)
│   ├── README.md          # Plugin documentation (recommended)
│   └── tests/             # Plugin tests (recommended)
```

### Core Components

1. **CLI Interface** (`cli.py`): The main entry point that defines commands and handles execution
2. **Command Structure**: Each command becomes a tool available to AI clients
3. **Parameter Validation**: Input validation and error handling
4. **JSON Output**: Structured responses for the MCP protocol

## Creating Your First Plugin

### Step 1: Create Plugin Directory

```bash
mkdir -p smcp/plugins/my_first_plugin
cd smcp/plugins/my_first_plugin
```

### Step 2: Create the CLI Interface

Create `cli.py` with this basic structure:

```python
#!/usr/bin/env python3
"""
My First Plugin

A sample plugin demonstrating basic plugin development.
"""

import argparse
import json
import sys
from typing import Dict, Any


def main():
    """Main entry point for the plugin CLI."""
    parser = argparse.ArgumentParser(
        description="My First Plugin - A sample plugin for Animus Letta MCP"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add your commands here
    setup_hello_command(subparsers)
    setup_calculate_command(subparsers)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the appropriate command
    if args.command == "hello":
        result = execute_hello(args.name, args.greeting)
    elif args.command == "calculate":
        result = execute_calculate(args.operation, args.a, args.b)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)
    
    # Output JSON result
    print(json.dumps(result, indent=2))


def setup_hello_command(subparsers):
    """Setup the hello command."""
    parser = subparsers.add_parser("hello", help="Say hello to someone")
    parser.add_argument("--name", required=True, help="Name to greet")
    parser.add_argument("--greeting", default="Hello", help="Greeting message")


def setup_calculate_command(subparsers):
    """Setup the calculate command."""
    parser = subparsers.add_parser("calculate", help="Perform a calculation")
    parser.add_argument("--operation", required=True, 
                       choices=["add", "subtract", "multiply", "divide"],
                       help="Mathematical operation")
    parser.add_argument("--a", required=True, type=float, help="First number")
    parser.add_argument("--b", required=True, type=float, help="Second number")


def execute_hello(name: str, greeting: str) -> Dict[str, Any]:
    """Execute the hello command."""
    message = f"{greeting}, {name}!"
    return {
        "status": "success",
        "message": message,
        "data": {
            "name": name,
            "greeting": greeting
        }
    }


def execute_calculate(operation: str, a: float, b: float) -> Dict[str, Any]:
    """Execute the calculate command."""
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return {
            "status": "success",
            "result": result,
            "operation": operation,
            "operands": [a, b]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "operation": operation,
            "operands": [a, b]
        }


if __name__ == "__main__":
    main()
```

### Step 3: Make it Executable

```bash
chmod +x cli.py
```

### Step 4: Test Your Plugin

```bash
# Test hello command
python cli.py hello --name "World" --greeting "Hi"

# Test calculate command
python cli.py calculate --operation add --a 5 --b 3
```

## Advanced Plugin Development

### Complex Parameter Types

For more complex plugins, you might need to handle different parameter types:

```python
def setup_advanced_command(subparsers):
    """Setup a command with complex parameters."""
    parser = subparsers.add_parser("advanced", help="Advanced command example")
    
    # String parameters
    parser.add_argument("--text", required=True, help="Text input")
    
    # Numeric parameters
    parser.add_argument("--number", type=int, default=10, help="Numeric input")
    parser.add_argument("--float", type=float, help="Float input")
    
    # Boolean parameters
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    
    # Choice parameters
    parser.add_argument("--mode", choices=["fast", "safe", "debug"], 
                       default="safe", help="Operation mode")
    
    # File parameters
    parser.add_argument("--input-file", type=str, help="Input file path")
    parser.add_argument("--output-file", type=str, help="Output file path")
```

### Error Handling

Always implement proper error handling:

```python
def execute_with_error_handling(func, *args, **kwargs):
    """Execute a function with proper error handling."""
    try:
        result = func(*args, **kwargs)
        return {
            "status": "success",
            "result": result
        }
    except ValueError as e:
        return {
            "status": "error",
            "error": f"Invalid input: {str(e)}",
            "error_type": "validation_error"
        }
    except FileNotFoundError as e:
        return {
            "status": "error",
            "error": f"File not found: {str(e)}",
            "error_type": "file_error"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unknown_error"
        }
```

### Async Operations

For plugins that need to perform async operations:

```python
import asyncio
import aiohttp

async def async_operation(url: str) -> Dict[str, Any]:
    """Perform an async operation."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.text()
            return {
                "status": "success",
                "url": url,
                "status_code": response.status,
                "data": data
            }

def execute_async_command(url: str) -> Dict[str, Any]:
    """Execute an async command."""
    try:
        result = asyncio.run(async_operation(url))
        return result
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

## Plugin Best Practices

### 1. Command Naming

- Use descriptive, hyphenated names: `send-message`, `deploy-app`, `check-status`
- Avoid camelCase or snake_case for command names
- Keep names short but clear

### 2. Parameter Design

- Use `--parameter-name` format for all parameters
- Make required parameters truly required
- Provide sensible defaults for optional parameters
- Use appropriate types (int, float, bool, str)

### 3. Output Format

- Always return JSON
- Include a `status` field ("success" or "error")
- Provide meaningful error messages
- Structure data logically

### 4. Error Handling

- Validate all inputs
- Handle expected errors gracefully
- Provide clear error messages
- Use appropriate HTTP status codes in responses

### 5. Documentation

- Include help text for all commands and parameters
- Document expected input/output formats
- Provide usage examples
- Keep README files updated

## Testing Your Plugin

### Unit Testing

Create a `tests/` directory in your plugin:

```python
# tests/test_my_plugin.py
import pytest
import json
import subprocess
from pathlib import Path

def test_hello_command():
    """Test the hello command."""
    result = subprocess.run([
        "python", "cli.py", "hello", "--name", "Test", "--greeting", "Hi"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "success"
    assert "Test" in data["message"]

def test_calculate_command():
    """Test the calculate command."""
    result = subprocess.run([
        "python", "cli.py", "calculate", "--operation", "add", "--a", "5", "--b", "3"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "success"
    assert data["result"] == 8
```

### Integration Testing

Test your plugin with the MCP server:

```python
# test_integration.py
import httpx
import json

async def test_plugin_integration():
    """Test plugin integration with MCP server."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Initialize connection
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        response = await client.post(f"{base_url}/messages/", json=init_request)
        assert response.status_code == 200
        
        # List tools to find your plugin
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = await client.post(f"{base_url}/messages/", json=tools_request)
        tools = response.json()["result"]["tools"]
        
        # Find your plugin's tools
        your_tools = [t for t in tools if t["name"].startswith("my_first_plugin.")]
        assert len(your_tools) > 0
        
        # Test calling your tool
        tool_name = your_tools[0]["name"]
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": {"name": "Test", "greeting": "Hi"}
            }
        }
        
        response = await client.post(f"{base_url}/messages/", json=call_request)
        result = response.json()["result"]
        assert "content" in result
```

## Plugin Examples

### BotFather Plugin

The BotFather plugin demonstrates integration with external APIs:

```python
#!/usr/bin/env python3
"""
BotFather Plugin

Telegram Bot API integration for Animus Letta MCP.
"""

import argparse
import json
import sys
import requests
from typing import Dict, Any

def setup_click_button_command(subparsers):
    """Setup the click-button command."""
    parser = subparsers.add_parser("click-button", help="Click a button in a message")
    parser.add_argument("--button-text", required=True, help="Text of the button to click")
    parser.add_argument("--msg-id", required=True, type=int, help="Message ID containing the button")

def setup_send_message_command(subparsers):
    """Setup the send-message command."""
    parser = subparsers.add_parser("send-message", help="Send a message")
    parser.add_argument("--message", required=True, help="Message to send")
    parser.add_argument("--chat-id", required=True, help="Chat ID to send to")

def execute_click_button(button_text: str, msg_id: int) -> Dict[str, Any]:
    """Execute the click-button command."""
    # Implementation would interact with Telegram Bot API
    return {
        "status": "success",
        "message": f"Clicked button '{button_text}' on message {msg_id}",
        "data": {
            "button_text": button_text,
            "message_id": msg_id
        }
    }

def execute_send_message(message: str, chat_id: str) -> Dict[str, Any]:
    """Execute the send-message command."""
    # Implementation would send message via Telegram Bot API
    return {
        "status": "success",
        "message": f"Sent message to chat {chat_id}",
        "data": {
            "message": message,
            "chat_id": chat_id
        }
    }
```

### DevOps Plugin

The DevOps plugin shows how to handle deployment operations:

```python
#!/usr/bin/env python3
"""
DevOps Plugin

Deployment and infrastructure management for Animus Letta MCP.
"""

import argparse
import json
import sys
from typing import Dict, Any

def setup_deploy_command(subparsers):
    """Setup the deploy command."""
    parser = subparsers.add_parser("deploy", help="Deploy an application")
    parser.add_argument("--app-name", required=True, help="Name of the application to deploy")
    parser.add_argument("--environment", default="production", help="Deployment environment")

def setup_rollback_command(subparsers):
    """Setup the rollback command."""
    parser = subparsers.add_parser("rollback", help="Rollback an application")
    parser.add_argument("--app-name", required=True, help="Name of the application to rollback")
    parser.add_argument("--version", required=True, help="Version to rollback to")

def execute_deploy(app_name: str, environment: str) -> Dict[str, Any]:
    """Execute the deploy command."""
    # Implementation would handle actual deployment
    return {
        "status": "success",
        "message": f"Deployed {app_name} to {environment}",
        "data": {
            "app_name": app_name,
            "environment": environment,
            "deployment_id": "deploy-12345"
        }
    }

def execute_rollback(app_name: str, version: str) -> Dict[str, Any]:
    """Execute the rollback command."""
    # Implementation would handle actual rollback
    return {
        "status": "success",
        "message": f"Rolled back {app_name} to version {version}",
        "data": {
            "app_name": app_name,
            "version": version,
            "rollback_id": "rollback-67890"
        }
    }
```

## Deployment

### Local Development

1. Place your plugin in `smcp/plugins/your_plugin/`
2. Make sure `cli.py` is executable
3. Restart the MCP server
4. Your tools will be automatically available

### Production Deployment

1. **Package your plugin**:
   ```bash
   tar -czf your_plugin.tar.gz your_plugin/
   ```

2. **Deploy to server**:
   ```bash
   scp your_plugin.tar.gz user@server:/path/to/plugins/
   ssh user@server "cd /path/to/plugins && tar -xzf your_plugin.tar.gz"
   ```

3. **Update MCP server configuration**:
   ```bash
   export MCP_PLUGINS_DIR=/path/to/plugins
   ```

4. **Restart the MCP server**

## Troubleshooting

### Common Issues

1. **Plugin not discovered**:
   - Check that `cli.py` exists and is executable
   - Verify the plugin directory structure
   - Check server logs for discovery errors

2. **Command not found**:
   - Ensure command names are properly defined in argparse
   - Check that help text includes "Available commands:" section
   - Verify command parsing logic

3. **Parameter validation errors**:
   - Check required parameter definitions
   - Verify parameter types and constraints
   - Test parameter parsing manually

4. **JSON output errors**:
   - Ensure all output is valid JSON
   - Check for non-serializable objects
   - Verify error handling returns proper JSON

### Debugging Tips

1. **Test CLI directly**:
   ```bash
   python your_plugin/cli.py --help
   python your_plugin/cli.py your-command --param value
   ```

2. **Check server logs**:
   ```bash
   tail -f mcp.log
   ```

3. **Verify tool registration**:
   ```bash
   curl -X POST http://localhost:8000/messages/ \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
   ```

## Resources

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/microsoft/fastmcp)
- [Python argparse Documentation](https://docs.python.org/3/library/argparse.html)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

---

**Need Help?** Visit [animus.uno](https://animus.uno) or follow [@animusuno](https://x.com/animusuno) for support.

> **Note**: This repository has been graduated to **Animus Core Module** status. Visit [animus.uno](https://animus.uno) for more information. 