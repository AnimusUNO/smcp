# API Reference

Complete API reference for the Animus Letta MCP Server.

## Overview

The Animus Letta MCP Server implements the Model Context Protocol (MCP) specification using Server-Sent Events (SSE) for real-time communication and HTTP POST for request/response handling.

## Endpoints

### SSE Endpoint

**URL**: `GET /sse`  
**Description**: Establishes a persistent Server-Sent Events connection for real-time server-to-client communication.

**Headers**:
- `Content-Type: text/event-stream`
- `Cache-Control: no-cache`
- `Connection: keep-alive`

**Response**: Continuous SSE stream with JSON-RPC 2.0 messages.

**Example**:
```bash
curl -N http://localhost:8000/sse
```

### Message Endpoint

**URL**: `POST /messages/`  
**Description**: Handles JSON-RPC 2.0 requests from clients.

**Headers**:
- `Content-Type: application/json`

**Request Body**: JSON-RPC 2.0 message

**Response**: JSON-RPC 2.0 response

**Example**:
```bash
curl -X POST http://localhost:8000/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## MCP Protocol

### Message Format

All messages follow the JSON-RPC 2.0 specification:

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "method-name",
  "params": {
    // Method-specific parameters
  }
}
```

### Response Format

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    // Method-specific result
  }
}
```

### Error Format

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": {
      // Additional error information
    }
  }
}
```

## Core Methods

### Initialize

**Method**: `initialize`  
**Description**: Initializes the MCP connection and negotiates protocol version.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "tools": {},
      "resources": {},
      "prompts": {}
    },
    "clientInfo": {
      "name": "client-name",
      "version": "1.0.0"
    }
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "tools": {
        "listChanged": true
      },
      "resources": {
        "listChanged": true
      },
      "prompts": {
        "listChanged": true
      }
    },
    "serverInfo": {
      "name": "animus-letta-mcp",
      "version": "3.0.0"
    }
  }
}
```

### Initialized

**Method**: `initialized`  
**Description**: Notification that client has completed initialization.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "initialized",
  "params": {}
}
```

**Response**: No response (notification)

### Tools List

**Method**: `tools/list`  
**Description**: Lists all available tools.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "health",
        "description": "Check server health and plugin status",
        "inputSchema": {
          "type": "object",
          "properties": {},
          "required": []
        }
      },
      {
        "name": "botfather.send-message",
        "description": "Send a message via Telegram Bot API",
        "inputSchema": {
          "type": "object",
          "properties": {
            "message": {
              "type": "string",
              "description": "Message to send"
            }
          },
          "required": ["message"]
        }
      }
    ]
  }
}
```

### Tools Call

**Method**: `tools/call`  
**Description**: Executes a tool with the provided arguments.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "health",
    "arguments": {}
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"status\":\"healthy\",\"plugins\":2,\"plugin_names\":[\"botfather\",\"devops\"]}"
      }
    ]
  }
}
```

## Error Codes

### Standard JSON-RPC 2.0 Errors

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON received |
| -32600 | Invalid Request | JSON-RPC request is invalid |
| -32601 | Method not found | Method does not exist |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Internal JSON-RPC error |

### MCP-Specific Errors

| Code | Message | Description |
|------|---------|-------------|
| -32000 | Connection closed | Connection was closed |
| -32001 | Tool not found | Requested tool does not exist |
| -32002 | Tool execution failed | Tool execution encountered an error |
| -32003 | Invalid tool arguments | Tool arguments are invalid |

## Plugin Tool Schema

### Tool Definition

Each plugin tool follows this schema:

```json
{
  "name": "plugin.command",
  "description": "Tool description",
  "inputSchema": {
    "type": "object",
    "properties": {
      "parameter-name": {
        "type": "string|number|boolean",
        "description": "Parameter description",
        "default": "default-value"
      }
    },
    "required": ["required-parameter"]
  }
}
```

### Tool Response

Tool responses are wrapped in content blocks:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Tool execution result"
    }
  ]
}
```

## Plugin Architecture

### Plugin Discovery

The server discovers plugins by scanning the plugin directory (default: `smcp/plugins/`) for subdirectories containing a `cli.py` file. Each plugin directory represents a plugin namespace.

### Plugin Directory Structure

```
smcp/plugins/
├── botfather/
│   ├── __init__.py
│   └── cli.py
├── devops/
│   ├── __init__.py
│   └── cli.py
└── custom-plugin/
    ├── __init__.py
    └── cli.py
```

### Symlink Support

The plugin discovery system fully supports symbolic links, enabling flexible plugin deployment architectures:

#### Centralized Plugin Management

You can centralize plugins in a designated location and use symlinks for discovery:

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

#### Benefits of Symlink Architecture

1. **Separation of Concerns**: Keep MCP server code separate from plugin implementations
2. **Centralized Management**: Manage plugins in a designated repository
3. **Dynamic Loading**: Add/remove plugins by creating/removing symlinks
4. **Version Control**: Maintain plugins in separate repositories
5. **Deployment Flexibility**: Deploy plugins independently of the MCP server

#### Symlink Examples

```bash
# Create symlink to centralized plugin
ln -s /opt/animus/plugins/botfather smcp/plugins/botfather

# Create symlink to user's custom plugin
ln -s /home/user/custom-plugins/my-plugin smcp/plugins/my-plugin

# Create symlink to network-mounted plugin
ln -s /mnt/network/plugins/enterprise-plugin smcp/plugins/enterprise-plugin
```

#### Environment Variable Override

You can override the plugin directory using the `MCP_PLUGINS_DIR` environment variable:

```bash
# Use custom plugin directory
export MCP_PLUGINS_DIR=/opt/animus/plugins
python smcp/mcp_server.py

# Or specify directly
MCP_PLUGINS_DIR=/opt/animus/plugins python smcp/mcp_server.py
```

### Plugin Execution

Plugins are executed as subprocesses with the following characteristics:

- **Isolation**: Each plugin runs in its own process
- **Timeout**: 10-second timeout for help command execution
- **Error Handling**: Failed plugins are logged but don't crash the server
- **Arguments**: Plugin arguments are passed as command-line flags

## SSE Events

### Connection Events

When a client connects to the SSE endpoint, the server may send:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list",
  "params": {
    "tools": [
      // List of available tools
    ]
  }
}
```

### Progress Events

For long-running operations:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/progress",
  "params": {
    "id": "operation-id",
    "progress": {
      "type": "indeterminate|percent",
      "value": 50
    }
  }
}
```

## Authentication

Currently, the server does not implement authentication. In production environments, consider:

1. **API Keys**: Add API key validation to requests
2. **OAuth**: Implement OAuth 2.0 flow
3. **JWT**: Use JWT tokens for session management
4. **Network Security**: Restrict access to trusted networks

## Rate Limiting

The server does not currently implement rate limiting. For production use, consider:

1. **Request Rate Limiting**: Limit requests per client
2. **Concurrent Connection Limits**: Limit simultaneous SSE connections
3. **Tool Execution Limits**: Limit concurrent tool executions

## Logging

### Log Format

Logs are written in structured format:

```
2025-07-11 15:21:07,215 - __main__ - INFO - Starting Animus Letta MCP Server...
2025-07-11 15:21:07,354 - __main__ - INFO - Registered tool: botfather.click-button
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General information about server operation
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may cause server failure

### Log Output

- **File**: `mcp.log` in the server directory
- **Console**: Standard output during development
- **Structured**: JSON format for production logging

## Health Check

### Health Tool

The built-in health tool provides server status:

```bash
curl -X POST http://localhost:8000/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"health","arguments":{}}}'
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"status\":\"healthy\",\"plugins\":2,\"plugin_names\":[\"botfather\",\"devops\"]}"
      }
    ]
  }
}
```

### Health Status

- **status**: `healthy` or `unhealthy`
- **plugins**: Number of discovered plugins
- **plugin_names**: List of plugin names

## Configuration

### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--allow-external` | `False` | Allow external connections (default: localhost only) |
| `--port` | `8000` | Port to run the server on |
| `--host` | `127.0.0.1` | Host to bind to (default: localhost for security) |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PORT` | `8000` | Server port |
| `MCP_PLUGINS_DIR` | `smcp/plugins/` | Plugin directory |
| `MCP_LOG_LEVEL` | `INFO` | Logging level |

### Security Configuration

By default, the server binds to `127.0.0.1` (localhost only) for security. This ensures that only processes running on the same machine can connect to the MCP server.

**Examples**:
```bash
# Default: localhost only (secure)
python smcp/mcp_server.py

# Allow external connections (use with caution)
python smcp/mcp_server.py --allow-external

# Custom port with localhost-only
python smcp/mcp_server.py --port 9000

# Custom host and port
python smcp/mcp_server.py --host 0.0.0.0 --port 8000
```

### Server Configuration

The server can be configured through environment variables or by modifying the server code:

```python
# Server configuration
server = FastMCP(
    name="animus-letta-mcp",
    instructions="A plugin-based MCP server for Animus Letta operations",
    sse_path="/sse",
    message_path="/messages/",
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MCP_PORT", "8000"))
)
```

## Examples

### Complete Client Integration

```python
import httpx
import json
import asyncio

async def mcp_client_example():
    """Complete MCP client integration example."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Step 1: Initialize connection
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "clientInfo": {"name": "example-client", "version": "1.0.0"}
            }
        }
        
        response = await client.post(f"{base_url}/messages/", json=init_request)
        print("Initialization:", response.json())
        
        # Step 2: Send initialized notification
        await client.post(f"{base_url}/messages/", json={
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        })
        
        # Step 3: List available tools
        tools_response = await client.post(f"{base_url}/messages/", json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        })
        
        tools = tools_response.json()["result"]["tools"]
        print(f"Available tools: {len(tools)}")
        
        # Step 4: Call health tool
        health_response = await client.post(f"{base_url}/messages/", json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "health",
                "arguments": {}
            }
        })
        
        health_result = health_response.json()["result"]
        print("Health check:", health_result)

# Run the example
asyncio.run(mcp_client_example())
```

### SSE Connection Example

```python
import httpx
import asyncio

async def sse_connection_example():
    """SSE connection example."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", f"{base_url}/sse") as response:
            print(f"SSE Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            
            # Read SSE events
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data:
                        try:
                            event = json.loads(data)
                            print(f"SSE Event: {event}")
                        except json.JSONDecodeError:
                            print(f"Raw SSE data: {data}")

# Run the example
asyncio.run(sse_connection_example())
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Server not running or wrong port
2. **404 Not Found**: Wrong endpoint URL
3. **Invalid JSON**: Malformed JSON-RPC request
4. **Method Not Found**: Unsupported MCP method
5. **Tool Not Found**: Plugin not loaded or tool not registered

### Debug Steps

1. **Check Server Status**: Verify server is running and listening
2. **Check Logs**: Review server logs for errors
3. **Test Endpoints**: Use curl to test individual endpoints
4. **Validate JSON**: Ensure JSON-RPC format is correct
5. **Check Plugins**: Verify plugins are discovered and loaded

---

For more information, see the [Plugin Development Guide](plugin-development-guide.md) and [README](../README.md). 