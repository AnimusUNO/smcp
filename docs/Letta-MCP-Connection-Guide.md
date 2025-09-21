# Complete Guide to Connecting MCP Servers to Letta

This guide provides comprehensive specifications for connecting Model Context Protocol (MCP) servers to Letta installations, with particular focus on Server-Sent Events (SSE) endpoints.

## ⚠️ CRITICAL UPDATE

**Previous versions of this documentation contained incorrect examples.** The key correction:

- **❌ WRONG**: Custom JSON objects like `{"type": "connection_established"}`
- **✅ CORRECT**: Pure JSON-RPC 2.0 messages for ALL communication

Letta uses the official MCP library which expects **JSON-RPC 2.0 over SSE** for all messages. Custom message types are not supported.

## Table of Contents

1. [Overview](#overview)
2. [MCP Server Types Supported](#mcp-server-types-supported)
3. [SSE Endpoint Specifications](#sse-endpoint-specifications)
4. [Authentication Methods](#authentication-methods)
5. [Configuration Methods](#configuration-methods)
6. [API Endpoints](#api-endpoints)
7. [Implementation Examples](#implementation-examples)
8. [Testing and Debugging](#testing-and-debugging)
9. [Troubleshooting](#troubleshooting)

## Overview

Letta supports three types of MCP server connections:
- **SSE (Server-Sent Events)**: For remote HTTP-based MCP servers
- **STDIO**: For local command-line MCP servers
- **Streamable HTTP**: For HTTP-based MCP servers with streaming capabilities

This guide focuses on **SSE endpoints** as they are the most common for remote MCP server implementations.

## MCP Server Types Supported

### SSE Server Configuration

```python
class SSEServerConfig(BaseServerConfig):
    type: MCPServerType = MCPServerType.SSE
    server_url: str = Field(..., description="The URL of the server (MCP SSE client will connect to this URL)")
    auth_header: Optional[str] = Field(None, description="The name of the authentication header (e.g., 'Authorization')")
    auth_token: Optional[str] = Field(None, description="The authentication token or API key value")
    custom_headers: Optional[dict[str, str]] = Field(None, description="Custom HTTP headers to include with SSE requests")
```

### STDIO Server Configuration

```python
class StdioServerConfig(BaseServerConfig):
    type: MCPServerType = MCPServerType.STDIO
    command: str = Field(..., description="The command to run (MCP 'local' client will run this command)")
    args: List[str] = Field(..., description="The arguments to pass to the command")
    env: Optional[dict[str, str]] = Field(None, description="Environment variables to set")
```

### Streamable HTTP Server Configuration

```python
class StreamableHTTPServerConfig(BaseServerConfig):
    type: MCPServerType = MCPServerType.STREAMABLE_HTTP
    server_url: str = Field(..., description="The URL path for the streamable HTTP server (e.g., 'example/mcp')")
    auth_header: Optional[str] = Field(None, description="The name of the authentication header (e.g., 'Authorization')")
    auth_token: Optional[str] = Field(None, description="The authentication token or API key value")
    custom_headers: Optional[dict[str, str]] = Field(None, description="Custom HTTP headers to include with streamable HTTP requests")
```

## SSE Endpoint Specifications

### Core Requirements

Your MCP server must implement a **Server-Sent Events (SSE) endpoint** that follows these specifications:

#### 1. HTTP Endpoint Requirements

- **Method**: GET
- **Content-Type**: `text/event-stream`
- **Connection**: Keep-alive
- **Cache-Control**: `no-cache`

**⚠️ CRITICAL**: SSE connections are persistent and never close automatically. Clients must implement timeouts or manual connection termination to prevent hanging.

#### 2. SSE Message Format

Each SSE message must follow the standard SSE format with **JSON-RPC 2.0 messages**:

```
data: <JSON_RPC_MESSAGE>\n\n
```

Where `<JSON_RPC_MESSAGE>` is a valid JSON-RPC 2.0 message. **ALL communication must use JSON-RPC 2.0 format** - there are no simple JSON objects or custom message types.

#### 3. MCP Protocol Messages

Your SSE endpoint must handle and respond to the following MCP protocol messages. **All messages must be valid JSON-RPC 2.0 messages**:

##### Initialization Message
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "clientInfo": {
      "name": "letta",
      "version": "1.0.0"
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "your-mcp-server",
      "version": "1.0.0"
    }
  }
}
```

##### List Tools Message
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "example_tool",
        "description": "An example tool",
        "inputSchema": {
          "type": "object",
          "properties": {
            "param1": {
              "type": "string",
              "description": "First parameter"
            }
          },
          "required": ["param1"]
        }
      }
    ]
  }
}
```

##### Call Tool Message
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "example_tool",
    "arguments": {
      "param1": "value1"
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Tool execution result"
      }
    ]
  }
}
```

#### 4. Error Handling

For errors, respond with:
```json
{
  "jsonrpc": "2.0",
  "id": <request_id>,
  "error": {
    "code": <error_code>,
    "message": "<error_message>"
  }
}
```

Common error codes:
- `-32600`: Invalid Request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

## Authentication Methods

Letta supports multiple authentication methods for MCP servers:

### 1. Bearer Token Authentication

```python
SSEServerConfig(
    server_name="my_server",
    server_url="https://api.example.com/mcp/sse",
    auth_header="Authorization",
    auth_token="Bearer your_token_here"
)
```

### 2. Custom Headers Authentication

```python
SSEServerConfig(
    server_name="my_server",
    server_url="https://api.example.com/mcp/sse",
    custom_headers={
        "X-API-Key": "your_api_key_here",
        "X-Custom-Header": "custom_value"
    }
)
```

### 3. No Authentication

```python
SSEServerConfig(
    server_name="my_server",
    server_url="https://api.example.com/mcp/sse"
)
```

## Configuration Methods

### Method 1: REST API (Recommended)

Use Letta's REST API to manage MCP servers:

#### Add MCP Server
```bash
curl -X PUT "http://localhost:8080/v1/tools/mcp/servers" \
  -H "Content-Type: application/json" \
  -H "user_id: your_user_id" \
  -d '{
    "server_name": "my_mcp_server",
    "type": "sse",
    "server_url": "https://api.example.com/mcp/sse",
    "auth_header": "Authorization",
    "auth_token": "Bearer your_token"
  }'
```

#### List MCP Servers
```bash
curl -X GET "http://localhost:8080/v1/tools/mcp/servers" \
  -H "user_id: your_user_id"
```

#### Test MCP Server Connection
```bash
curl -X POST "http://localhost:8080/v1/tools/mcp/servers/test" \
  -H "Content-Type: application/json" \
  -d '{
    "server_name": "my_mcp_server",
    "type": "sse",
    "server_url": "https://api.example.com/mcp/sse"
  }'
```

### Method 2: Configuration File (Legacy)

Create a configuration file at `~/.letta/mcp_config.json`:

```json
{
  "mcpServers": {
    "my_mcp_server": {
      "transport": "sse",
      "url": "https://api.example.com/mcp/sse",
      "headers": {
        "Authorization": "Bearer your_token_here"
      }
    }
  }
}
```

## API Endpoints

### MCP Server Management Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/tools/mcp/servers` | GET | List all configured MCP servers |
| `/v1/tools/mcp/servers` | PUT | Add a new MCP server |
| `/v1/tools/mcp/servers/{server_name}` | PATCH | Update an existing MCP server |
| `/v1/tools/mcp/servers/{server_name}` | DELETE | Remove an MCP server |
| `/v1/tools/mcp/servers/test` | POST | Test connection to an MCP server |

### Request/Response Schemas

#### Add/Update MCP Server Request
```json
{
  "server_name": "string",
  "type": "sse|stdio|streamable_http",
  "server_url": "string",
  "auth_header": "string (optional)",
  "auth_token": "string (optional)",
  "custom_headers": {
    "header_name": "header_value"
  }
}
```

#### MCP Server Response
```json
{
  "server_name": "string",
  "type": "sse|stdio|streamable_http",
  "server_url": "string",
  "auth_header": "string (optional)",
  "auth_token": "string (optional)",
  "custom_headers": {
    "header_name": "header_value"
  }
}
```

## Implementation Examples

### ⚠️ CRITICAL PROTOCOL REQUIREMENTS

**Letta uses the official MCP library** (`mcp.client.sse.sse_client`), which expects:

1. **Pure JSON-RPC 2.0 over SSE** - All messages must be valid JSON-RPC 2.0
2. **Bidirectional communication** - The MCP library sends requests and expects responses
3. **No custom message types** - No "connection_established" or other custom JSON objects
4. **Proper SSE format** - `data: <json-rpc-message>\n\n` for every message

### Working Example: DeepWiki MCP Server

A working example that Letta successfully connects to:
- **URL**: `https://mcp.deepwiki.com/sse`
- **Protocol**: JSON-RPC 2.0 over SSE
- **Tools**: `ask_question`, `search_repos`, etc.

This server demonstrates the correct protocol implementation.

### Python Flask SSE Server Example

```python
from flask import Flask, Response, request
import json
import uuid
import asyncio
import threading
from queue import Queue

app = Flask(__name__)

# Store active connections and message queues
connections = {}
message_queues = {}

@app.route('/mcp/sse')
def mcp_sse():
    def generate():
        # Generate unique connection ID
        conn_id = str(uuid.uuid4())
        connections[conn_id] = True
        message_queues[conn_id] = Queue()
        
        try:
            # Wait for client to send messages
            while connections.get(conn_id):
                # In a real implementation, you would handle bidirectional communication
                # This is a simplified example - you need to implement proper message handling
                pass
                
        except GeneratorExit:
            # Client disconnected
            connections.pop(conn_id, None)
            message_queues.pop(conn_id, None)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
    )

@app.route('/mcp/message', methods=['POST'])
def handle_mcp_message():
    message = request.json
    
    # Validate JSON-RPC 2.0 message
    if not isinstance(message, dict) or 'jsonrpc' not in message or message['jsonrpc'] != '2.0':
        return json.dumps({
            "jsonrpc": "2.0",
            "id": message.get('id'),
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        })
    
    # Handle different MCP message types
    if message.get('method') == 'initialize':
        response = {
            "jsonrpc": "2.0",
            "id": message.get('id'),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "example-mcp-server",
                    "version": "1.0.0"
                }
            }
        }
    elif message.get('method') == 'tools/list':
        response = {
            "jsonrpc": "2.0",
            "id": message.get('id'),
            "result": {
                "tools": [
                    {
                        "name": "example_tool",
                        "description": "An example tool",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "param1": {
                                    "type": "string",
                                    "description": "First parameter"
                                }
                            },
                            "required": ["param1"]
                        }
                    }
                ]
            }
        }
    elif message.get('method') == 'tools/call':
        # Execute the tool
        tool_name = message['params']['name']
        arguments = message['params']['arguments']
        
        # Your tool execution logic here
        result = execute_tool(tool_name, arguments)
        
        response = {
            "jsonrpc": "2.0",
            "id": message.get('id'),
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": result
                    }
                ]
            }
        }
    else:
        response = {
            "jsonrpc": "2.0",
            "id": message.get('id'),
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }
    
    return json.dumps(response)

def execute_tool(tool_name, arguments):
    # Implement your tool execution logic here
    if tool_name == "example_tool":
        return f"Executed {tool_name} with arguments: {arguments}"
    return "Tool not found"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**⚠️ IMPORTANT NOTE:** This Flask example is simplified and may not work directly with Letta. The MCP library expects a specific bidirectional communication protocol over SSE. For production use, consider using the official MCP server framework or implementing the full SSE protocol correctly.

### Node.js Express SSE Server Example

```javascript
const express = require('express');
const app = express();

app.use(express.json());

// Store active connections
const connections = new Map();

app.get('/mcp/sse', (req, res) => {
    // Set SSE headers
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });

    const connectionId = Date.now().toString();
    connections.set(connectionId, res);

    // Handle client disconnect
    req.on('close', () => {
        connections.delete(connectionId);
    });
});

app.post('/mcp/message', (req, res) => {
    const message = req.body;
    let response;

    // Validate JSON-RPC 2.0 message
    if (!message || message.jsonrpc !== '2.0') {
        response = {
            jsonrpc: "2.0",
            id: message?.id,
            error: {
                code: -32600,
                message: "Invalid Request"
            }
        };
        return res.json(response);
    }

    switch (message.method) {
        case 'initialize':
            response = {
                jsonrpc: "2.0",
                id: message.id,
                result: {
                    protocolVersion: "2024-11-05",
                    capabilities: {
                        tools: {}
                    },
                    serverInfo: {
                        name: "example-mcp-server",
                        version: "1.0.0"
                    }
                }
            };
            break;

        case 'tools/list':
            response = {
                jsonrpc: "2.0",
                id: message.id,
                result: {
                    tools: [
                        {
                            name: "example_tool",
                            description: "An example tool",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    param1: {
                                        type: "string",
                                        description: "First parameter"
                                    }
                                },
                                required: ["param1"]
                            }
                        }
                    ]
                }
            };
            break;

        case 'tools/call':
            const toolName = message.params.name;
            const arguments = message.params.arguments;
            
            // Execute tool logic here
            const result = executeTool(toolName, arguments);
            
            response = {
                jsonrpc: "2.0",
                id: message.id,
                result: {
                    content: [
                        {
                            type: "text",
                            text: result
                        }
                    ]
                }
            };
            break;

        default:
            response = {
                jsonrpc: "2.0",
                id: message.id,
                error: {
                    code: -32601,
                    message: "Method not found"
                }
            };
    }

    res.json(response);
});

function executeTool(toolName, arguments) {
    if (toolName === "example_tool") {
        return `Executed ${toolName} with arguments: ${JSON.stringify(arguments)}`;
    }
    return "Tool not found";
}

app.listen(5000, () => {
    console.log('MCP Server running on port 5000');
});
```

**⚠️ IMPORTANT NOTE:** This Node.js example is simplified and may not work directly with Letta. The MCP library expects a specific bidirectional communication protocol over SSE. For production use, consider using the official MCP server framework or implementing the full SSE protocol correctly.

### Recommended: Use Official MCP Server Framework

For production MCP servers, **strongly consider using the official MCP server framework**:

```bash
pip install mcp
```

**Example using official framework:**
```python
import mcp
import asyncio

# Define your tools
@mcp.tool()
async def example_tool(param1: str) -> str:
    """An example tool"""
    return f"Executed with parameter: {param1}"

# Run the server
if __name__ == "__main__":
    mcp.run(transport="sse", port=5000)
```

This ensures compatibility with Letta and other MCP clients.

## Testing and Debugging

### 1. Test Your SSE Endpoint

Use a simple curl command to test your SSE endpoint:

```bash
curl -N -H "Accept: text/event-stream" \
     -H "Cache-Control: no-cache" \
     https://your-mcp-server.com/mcp/sse
```

**⚠️ IMPORTANT**: This curl command will hang indefinitely. Use Ctrl+C to terminate it, or add a timeout:

```bash
timeout 10 curl -N -H "Accept: text/event-stream" \
     -H "Cache-Control: no-cache" \
     https://your-mcp-server.com/mcp/sse
```

### 2. Test with Letta

Use Letta's test endpoint to verify your MCP server:

```bash
curl -X POST "http://localhost:8080/v1/tools/mcp/servers/test" \
  -H "Content-Type: application/json" \
  -d '{
    "server_name": "test_server",
    "type": "sse",
    "server_url": "https://your-mcp-server.com/mcp/sse"
  }'
```

### 3. Common Test Scenarios

1. **Connection Test**: Verify the SSE endpoint responds with proper headers
2. **Initialization Test**: Ensure the server responds to `initialize` messages
3. **Tool Listing Test**: Verify `tools/list` returns valid tool definitions
4. **Tool Execution Test**: Test actual tool execution with `tools/call`

## Troubleshooting

### Common Issues

#### 1. Connection Refused
- **Cause**: Server not running or wrong URL
- **Solution**: Verify server is running and URL is correct

#### 2. CORS Errors
- **Cause**: Missing CORS headers
- **Solution**: Add appropriate CORS headers to your SSE endpoint

#### 3. Authentication Failures
- **Cause**: Incorrect auth headers or tokens
- **Solution**: Verify auth configuration in Letta matches your server

#### 4. Protocol Errors
- **Cause**: Invalid JSON-RPC messages
- **Solution**: Ensure all messages follow JSON-RPC 2.0 specification

#### 5. SSE Format Errors
- **Cause**: Incorrect SSE message format
- **Solution**: Ensure all messages follow `data: <json-rpc-message>\n\n` format with valid JSON-RPC 2.0

#### 6. JSON-RPC Protocol Errors
- **Cause**: Using custom JSON objects instead of JSON-RPC 2.0
- **Solution**: All messages must be valid JSON-RPC 2.0 with `jsonrpc: "2.0"` field

#### 7. Bidirectional Communication Issues
- **Cause**: Not implementing proper request/response handling
- **Solution**: The MCP library sends requests and expects responses over the same SSE connection

#### 8. SSE Connection Hanging
- **Cause**: SSE connections are persistent and never close automatically
- **Solution**: Implement timeouts in your client code and handle connection termination gracefully

### Debug Logs

Enable debug logging in Letta to see detailed MCP communication:

```python
import logging
logging.getLogger('letta.services.mcp').setLevel(logging.DEBUG)
```

### Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `MCPServerConnectionError` | Failed to connect to MCP server | Check server URL and network connectivity |
| `MCPTimeoutError` | Connection timed out | Check server response times and timeouts |
| `-32600` | Invalid Request | Verify JSON-RPC message format |
| `-32601` | Method not found | Implement required MCP methods |
| `-32602` | Invalid params | Check parameter validation |
| `-32603` | Internal error | Check server logs for internal errors |

## Best Practices

1. **Implement Proper Error Handling**: Always return valid JSON-RPC error responses
2. **Use Connection Pooling**: Manage multiple client connections efficiently
3. **Implement Heartbeats**: Send periodic keep-alive messages
4. **Validate Input**: Always validate tool parameters before execution
5. **Log Operations**: Implement comprehensive logging for debugging
6. **Handle Disconnections**: Gracefully handle client disconnections
7. **Rate Limiting**: Implement appropriate rate limiting for tool calls
8. **Security**: Use HTTPS and proper authentication for production servers

## Additional Resources

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Server-Sent Events Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Letta Documentation](https://animus.uno)

---

This guide provides the complete specifications needed to implement an MCP server that integrates seamlessly with Letta. Follow the SSE endpoint specifications carefully, and use the provided examples as starting points for your implementation.

> **Note**: This repository has been graduated to **Animus Core Module** status. Visit [animus.uno](https://animus.uno) for more information. 