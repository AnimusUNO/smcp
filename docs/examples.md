# Examples Guide

This guide provides practical examples of how to use SMCP, from basic operations to advanced integrations.

## 🚀 Quick Examples

### Basic Health Check
```bash
# Check if SMCP is running
curl -X POST http://localhost:8000/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"health","arguments":{}}}'
```

### List Available Tools
```bash
# Get all available tools
curl -X POST http://localhost:8000/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

## 🔌 Plugin Examples

### BotFather Plugin Usage
```bash
# Get bot information
python smcp/plugins/botfather/cli.py get-me

# Send message
python smcp/plugins/botfather/cli.py send-message \
  --chat_id "123456789" \
  --text "Hello from SMCP!"

# Get updates
python smcp/plugins/botfather/cli.py get-updates
```

### DevOps Plugin Usage
```bash
# Check system status
python smcp/plugins/devops/cli.py system-status

# Deploy application
python smcp/plugins/devops/cli.py deploy \
  --app "my-app" \
  --environment "production"

# Monitor resources
python smcp/plugins/devops/cli.py monitor \
  --metric "cpu" \
  --duration "1h"
```

## 🌐 Client Integration Examples

### Python Client
```python
import httpx
import json
import asyncio

class SMCPClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def initialize(self):
        """Initialize connection to SMCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "clientInfo": {"name": "python-client", "version": "1.0.0"}
            }
        }
        
        response = await self.client.post(f"{self.base_url}/messages/", json=request)
        return response.json()
    
    async def list_tools(self):
        """Get list of available tools."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = await self.client.post(f"{self.base_url}/messages/", json=request)
        return response.json()
    
    async def call_tool(self, tool_name, arguments=None):
        """Call a specific tool."""
        if arguments is None:
            arguments = {}
            
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = await self.client.post(f"{self.base_url}/messages/", json=request)
        return response.json()
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()

# Usage example
async def main():
    client = SMCPClient()
    
    try:
        # Initialize connection
        init_result = await client.initialize()
        print(f"Initialization: {init_result}")
        
        # List available tools
        tools_result = await client.list_tools()
        print(f"Available tools: {tools_result}")
        
        # Call health check
        health_result = await client.call_tool("health")
        print(f"Health check: {health_result}")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript/Node.js Client
```javascript
const axios = require('axios');

class SMCPClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
    
    async initialize() {
        const request = {
            jsonrpc: '2.0',
            id: 1,
            method: 'initialize',
            params: {
                protocolVersion: '2025-03-26',
                capabilities: { tools: {}, resources: {}, prompts: {} },
                clientInfo: { name: 'javascript-client', version: '1.0.0' }
            }
        };
        
        const response = await this.client.post('/messages/', request);
        return response.data;
    }
    
    async listTools() {
        const request = {
            jsonrpc: '2.0',
            id: 2,
            method: 'tools/list',
            params: {}
        };
        
        const response = await this.client.post('/messages/', request);
        return response.data;
    }
    
    async callTool(toolName, arguments = {}) {
        const request = {
            jsonrpc: '2.0',
            id: 3,
            method: 'tools/call',
            params: {
                name: toolName,
                arguments: arguments
            }
        };
        
        const response = await this.client.post('/messages/', request);
        return response.data;
    }
}

// Usage example
async function main() {
    const client = new SMCPClient();
    
    try {
        // Initialize connection
        const initResult = await client.initialize();
        console.log('Initialization:', initResult);
        
        // List available tools
        const toolsResult = await client.listTools();
        console.log('Available tools:', toolsResult);
        
        // Call health check
        const healthResult = await client.callTool('health');
        console.log('Health check:', healthResult);
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

### cURL Examples
```bash
#!/bin/bash

# Initialize connection
echo "Initializing connection..."
INIT_RESPONSE=$(curl -s -X POST http://localhost:8000/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
      "clientInfo": {"name": "bash-client", "version": "1.0.0"}
    }
  }')

echo "Initialization response: $INIT_RESPONSE"

# List tools
echo "Listing available tools..."
TOOLS_RESPONSE=$(curl -s -X POST http://localhost:8000/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }')

echo "Tools response: $TOOLS_RESPONSE"

# Health check
echo "Performing health check..."
HEALTH_RESPONSE=$(curl -s -X POST http://localhost:8000/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "health",
      "arguments": {}
    }
  }')

echo "Health check response: $HEALTH_RESPONSE"
```

## 🔄 Real-time Communication

### SSE (Server-Sent Events) Example
```python
import asyncio
import aiohttp

async def listen_to_events():
    """Listen to real-time events from SMCP server."""
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/sse') as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data:
                        try:
                            event = json.loads(data)
                            print(f"Received event: {event}")
                        except json.JSONDecodeError:
                            print(f"Invalid JSON: {data}")

# Run the event listener
asyncio.run(listen_to_events())
```

### WebSocket-like Behavior with SSE
```javascript
class SMCPEventSource {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect() {
        try {
            this.eventSource = new EventSource(`${this.baseUrl}/sse`);
            
            this.eventSource.onopen = () => {
                console.log('Connected to SMCP server');
                this.reconnectAttempts = 0;
            };
            
            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing message:', error);
                }
            };
            
            this.eventSource.onerror = (error) => {
                console.error('SSE connection error:', error);
                this.reconnect();
            };
            
        } catch (error) {
            console.error('Error creating EventSource:', error);
        }
    }
    
    handleMessage(data) {
        console.log('Received message:', data);
        
        // Handle different message types
        switch (data.type) {
            case 'tool_result':
                console.log('Tool execution result:', data.result);
                break;
            case 'error':
                console.error('Server error:', data.error);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
            
            setTimeout(() => {
                this.disconnect();
                this.connect();
            }, 1000 * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Usage
const eventSource = new SMCPEventSource();
eventSource.connect();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    eventSource.disconnect();
});
```

## 🧪 Testing Examples

### Unit Test Example
```python
import pytest
import httpx
from unittest.mock import patch

class TestSMCPClient:
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient() as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.post(
            "http://localhost:8000/messages/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "health", "arguments": {}}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert "result" in data
    
    @pytest.mark.asyncio
    async def test_invalid_method(self, client):
        """Test invalid method handling."""
        response = await client.post(
            "http://localhost:8000/messages/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "invalid_method",
                "params": {}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found
```

### Integration Test Example
```python
import pytest
import asyncio
import subprocess
import time
import httpx

class TestSMCPIntegration:
    @pytest.fixture(scope="class")
    def smcp_server(self):
        """Start SMCP server for testing."""
        process = subprocess.Popen([
            "python", "smcp/mcp_server.py", "--port", "8001"
        ])
        
        # Wait for server to start
        time.sleep(3)
        
        yield process
        
        # Cleanup
        process.terminate()
        process.wait()
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, smcp_server):
        """Test complete workflow from initialization to tool execution."""
        async with httpx.AsyncClient() as client:
            # Step 1: Initialize
            init_response = await client.post(
                "http://localhost:8001/messages/",
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
            
            assert init_response.status_code == 200
            init_data = init_response.json()
            assert "result" in init_data
            
            # Step 2: List tools
            tools_response = await client.post(
                "http://localhost:8001/messages/",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
            )
            
            assert tools_response.status_code == 200
            tools_data = tools_response.json()
            assert "result" in tools_data
            assert "tools" in tools_data["result"]
            
            # Step 3: Call health tool
            health_response = await client.post(
                "http://localhost:8001/messages/",
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "health", "arguments": {}}
                }
            )
            
            assert health_response.status_code == 200
            health_data = health_response.json()
            assert "result" in health_data
            assert health_data["result"]["status"] == "healthy"
```

## 🔧 Advanced Examples

### Custom Plugin Integration
```python
import subprocess
import json
import tempfile
import os

class CustomPluginManager:
    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
    
    def list_plugins(self):
        """List all available plugins."""
        plugins = []
        for item in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, item)
            if os.path.isdir(plugin_path):
                cli_path = os.path.join(plugin_path, "cli.py")
                if os.path.exists(cli_path):
                    plugins.append({
                        "name": item,
                        "path": plugin_path,
                        "cli_path": cli_path
                    })
        return plugins
    
    def execute_plugin(self, plugin_name, command, arguments=None):
        """Execute a plugin command."""
        if arguments is None:
            arguments = {}
        
        plugin_info = next((p for p in self.list_plugins() if p["name"] == plugin_name), None)
        if not plugin_info:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        
        cmd = ["python", plugin_info["cli_path"], command]
        
        # Add arguments
        for key, value in arguments.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key}")
            else:
                cmd.extend([f"--{key}", str(value)])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=plugin_info["path"]
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"output": result.stdout, "status": "success"}
            else:
                return {
                    "error": result.stderr,
                    "status": "error",
                    "return_code": result.returncode
                }
                
        except Exception as e:
            return {"error": str(e), "status": "exception"}

# Usage
plugin_manager = CustomPluginManager("smcp/plugins")

# List available plugins
plugins = plugin_manager.list_plugins()
print("Available plugins:", [p["name"] for p in plugins])

# Execute plugin command
if plugins:
    result = plugin_manager.execute_plugin(
        plugins[0]["name"],
        "help"
    )
    print(f"Plugin result: {result}")
```

### Load Balancing Example
```python
import random
import asyncio
import httpx
from typing import List

class SMCPLoadBalancer:
    def __init__(self, servers: List[str]):
        self.servers = servers
        self.current_index = 0
        self.health_status = {server: True for server in servers}
    
    def get_next_server(self) -> str:
        """Get next server using round-robin."""
        if not self.servers:
            raise ValueError("No servers available")
        
        # Find next healthy server
        attempts = 0
        while attempts < len(self.servers):
            server = self.servers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.servers)
            
            if self.health_status[server]:
                return server
            
            attempts += 1
        
        # If no healthy servers, reset health status
        self.health_status = {server: True for server in self.servers}
        return self.servers[0]
    
    async def check_server_health(self, server: str) -> bool:
        """Check if a server is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{server}/messages/",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {"name": "health", "arguments": {}}
                    }
                )
                return response.status_code == 200
        except:
            return False
    
    async def monitor_health(self):
        """Monitor health of all servers."""
        while True:
            for server in self.servers:
                is_healthy = await self.check_server_health(server)
                self.health_status[server] = is_healthy
                
                if not is_healthy:
                    print(f"Server {server} is unhealthy")
                else:
                    print(f"Server {server} is healthy")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def execute_request(self, request_data: dict):
        """Execute request through load balancer."""
        server = self.get_next_server()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{server}/messages/",
                    json=request_data
                )
                return response.json()
        except Exception as e:
            # Mark server as unhealthy
            self.health_status[server] = False
            raise e

# Usage example
async def main():
    # Initialize load balancer with multiple SMCP servers
    lb = SMCPLoadBalancer([
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002"
    ])
    
    # Start health monitoring
    health_task = asyncio.create_task(lb.monitor_health())
    
    try:
        # Execute requests through load balancer
        for i in range(5):
            result = await lb.execute_request({
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {"name": "health", "arguments": {}}
            })
            print(f"Request {i} result: {result}")
            await asyncio.sleep(1)
    
    finally:
        health_task.cancel()

# Run the example
# asyncio.run(main())
```

## 📚 More Examples

For additional examples and use cases:

- **Plugin Development**: See the [Plugin Development Guide](plugin-development-guide.md)
- **API Reference**: Check the [Complete API Documentation](api-reference.md)
- **Deployment**: Review the [Deployment Guide](deployment-guide.md)
- **Troubleshooting**: Visit the [Troubleshooting Guide](troubleshooting.md)

---

**Have a specific use case?** Check our [GitHub Issues](https://github.com/sanctumos/smcp/issues) or create a new one with your requirements!
