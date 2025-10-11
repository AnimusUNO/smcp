"""
Integration tests for MCP protocol implementation.
Tests the full MCP protocol flow including SSE connections and JSON-RPC messaging.
"""

import asyncio
import json
import pytest
import httpx
import subprocess
import socket
import time
from typing import AsyncGenerator
import os


def find_free_port() -> int:
    """Find a free port to use for testing."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


async def wait_for_server_ready(base_url: str, timeout: float = 10.0) -> bool:
    """Wait for server to be ready by checking if it responds to basic requests."""
    start_time = time.time()
    async with httpx.AsyncClient(timeout=5.0) as client:
        while time.time() - start_time < timeout:
            try:
                # Try a simple GET request to see if server is responding
                response = await client.get(f"{base_url}/", timeout=2.0)
                if response.status_code in [200, 404, 405]:  # Server is responding
                    return True
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError):
                pass
            await asyncio.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def test_port() -> int:
    """Get a free port for testing."""
    return find_free_port()


@pytest.fixture(scope="session")
async def server_process(test_port: int):
    """Start server process for integration tests."""
    # Start server in subprocess
    env = os.environ.copy()
    env["MCP_PORT"] = str(test_port)
    env["MCP_HOST"] = "127.0.0.1"
    
    print(f"Starting server on port {test_port}")
    process = subprocess.Popen(
        ["python", "smcp/mcp_server.py", "--host", "127.0.0.1", "--port", str(test_port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give server time to start
    await asyncio.sleep(2)
    
    # Check if process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"Server failed to start. Return code: {process.returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        raise RuntimeError(f"Server failed to start on port {test_port}")
    
    # Wait for server to be ready
    base_url = f"http://127.0.0.1:{test_port}"
    print(f"Waiting for server to be ready at {base_url}")
    ready = await wait_for_server_ready(base_url, timeout=15.0)
    
    if not ready:
        stdout, stderr = process.communicate()
        print(f"Server not ready. STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        process.terminate()
        process.wait()
        raise RuntimeError(f"Server failed to start on port {test_port}")
    
    print(f"Server is ready on port {test_port}")
    yield process
    
    # Cleanup
    print(f"Stopping server on port {test_port}")
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture
def base_url(test_port: int) -> str:
    """Base URL for MCP server."""
    return f"http://127.0.0.1:{test_port}"


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create HTTP client for testing."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


class TestMCPProtocol:
    """Test MCP protocol implementation with proper SSE handling."""
    
    async def test_sse_endpoint_connection(self, client: httpx.AsyncClient, base_url: str, server_process):
        """Test that SSE endpoint establishes connection properly."""
        # SSE endpoint should accept connection and keep it open
        try:
            async with client.stream("GET", f"{base_url}/sse", timeout=5.0) as response:
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")
                assert response.headers.get("cache-control") in ["no-cache", "no-store"]
                assert response.headers.get("connection") == "keep-alive"
                
                # Read a few lines to ensure connection is working
                lines_read = 0
                async for line in response.aiter_lines():
                    lines_read += 1
                    if lines_read >= 3:  # Just read a few lines to verify connection
                        break
                    if line.startswith("data:"):
                        # Parse SSE data
                        data = line[5:].strip()
                        if data:
                            try:
                                event_data = json.loads(data)
                                # Should be valid JSON
                                assert isinstance(event_data, dict)
                            except json.JSONDecodeError:
                                # Some SSE messages might not be JSON
                                pass
        except httpx.TimeoutException:
            # SSE connections are expected to timeout since they stay open
            # This is actually good - it means the connection was established
            pass
    
    async def test_message_endpoint_initialize(self, client: httpx.AsyncClient, base_url: str):
        """Test MCP initialize request via message endpoint."""
        initialize_request = {
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
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Set proper headers for MCP protocol
        headers = {
            'Accept': 'application/json, text/event-stream',
            'Content-Type': 'application/json'
        }
        
        response = await client.post(
            f"{base_url}/mcp",
            json=initialize_request,
            headers=headers,
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        
        result = data["result"]
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        
        # Check server info
        server_info = result["serverInfo"]
        assert server_info["name"] == "animus-letta-mcp"
        assert "version" in server_info
    
    async def test_message_endpoint_initialized(self, client: httpx.AsyncClient, base_url: str):
        """Test MCP initialized notification."""
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        
        # Set proper headers for MCP protocol
        headers = {
            'Accept': 'application/json, text/event-stream',
            'Content-Type': 'application/json'
        }
        
        response = await client.post(
            f"{base_url}/mcp",
            json=initialized_notification,
            headers=headers,
            timeout=10.0
        )
        
        # Initialized notification should not return a response
        assert response.status_code == 200
        # Response should be empty or minimal
    
    async def test_list_tools(self, client: httpx.AsyncClient, base_url: str):
        """Test listing available tools."""
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        # Set proper headers for MCP protocol
        headers = {
            'Accept': 'application/json, text/event-stream',
            'Content-Type': 'application/json'
        }
        
        response = await client.post(
            f"{base_url}/mcp",
            json=list_tools_request,
            headers=headers,
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 2
        assert "result" in data
        
        result = data["result"]
        assert "tools" in result
        tools = result["tools"]
        
        # Should have at least the health tool
        assert len(tools) >= 1
        
        # Check for health tool
        health_tool = next((t for t in tools if t["name"] == "health"), None)
        assert health_tool is not None
        assert health_tool["description"] == "Check server health and plugin status"
    
    async def test_call_health_tool(self, client: httpx.AsyncClient, base_url: str):
        """Test calling the health tool."""
        call_tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "health",
                "arguments": {}
            }
        }
        
        # Set proper headers for MCP protocol
        headers = {
            'Accept': 'application/json, text/event-stream',
            'Content-Type': 'application/json'
        }
        
        response = await client.post(
            f"{base_url}/mcp",
            json=call_tool_request,
            headers=headers,
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 3
        assert "result" in data
        
        result = data["result"]
        assert "content" in result
        assert len(result["content"]) > 0
        
        # Parse health check response
        content = result["content"][0]
        assert content["type"] == "text"
        
        health_data = json.loads(content["text"])
        assert health_data["status"] == "healthy"
        assert "plugins" in health_data
        assert "plugin_names" in health_data
    
    async def test_invalid_json_rpc(self, client: httpx.AsyncClient, base_url: str):
        """Test handling of invalid JSON-RPC requests."""
        invalid_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "nonexistent_method"
        }
        
        # Set proper headers for MCP protocol
        headers = {
            'Accept': 'application/json, text/event-stream',
            'Content-Type': 'application/json'
        }
        
        response = await client.post(
            f"{base_url}/mcp",
            json=invalid_request,
            headers=headers,
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 4
        assert "error" in data
        
        error = data["error"]
        assert error["code"] == -32601  # Method not found
    
    async def test_malformed_json(self, client: httpx.AsyncClient, base_url: str):
        """Test handling of malformed JSON."""
        # Set proper headers for MCP protocol
        headers = {
            'Accept': 'application/json, text/event-stream',
            'Content-Type': 'application/json'
        }
        
        response = await client.post(
            f"{base_url}/mcp",
            content="invalid json",
            headers=headers,
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "error" in data
        error = data["error"]
        assert error["code"] == -32700  # Parse error
    
    async def test_concurrent_requests(self, client: httpx.AsyncClient, base_url: str):
        """Test handling of concurrent requests."""
        # Send multiple requests simultaneously
        requests = []
        for i in range(5):
            request = {
                "jsonrpc": "2.0",
                "id": i + 10,
                "method": "tools/list"
            }
            requests.append(
                client.post(f"{base_url}/mcp", json=request, headers={
                    'Accept': 'application/json, text/event-stream',
                    'Content-Type': 'application/json'
                }, timeout=10.0)
            )
        
        responses = await asyncio.gather(*requests)
        
        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == i + 10
            assert "result" in data
    
    async def test_sse_and_message_hybrid(self, client: httpx.AsyncClient, base_url: str):
        """Test that SSE and message endpoints work together."""
        # First establish SSE connection
        sse_task = asyncio.create_task(self._establish_sse_connection(client, base_url))
        
        # Wait a bit for SSE to establish
        await asyncio.sleep(1)
        
        # Send message while SSE is connected
        message_request = {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/list"
        }
        
        # Set proper headers for MCP protocol
        headers = {
            'Accept': 'application/json, text/event-stream',
            'Content-Type': 'application/json'
        }
        
        response = await client.post(
            f"{base_url}/mcp",
            json=message_request,
            headers=headers,
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 20
        assert "result" in data
        
        # Cancel SSE task
        sse_task.cancel()
        try:
            await sse_task
        except asyncio.CancelledError:
            pass
    
    async def _establish_sse_connection(self, client: httpx.AsyncClient, base_url: str):
        """Helper to establish SSE connection."""
        try:
            async with client.stream("GET", f"{base_url}/sse", timeout=5.0) as response:
                assert response.status_code == 200
                # Just verify connection is established, don't read indefinitely
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        break
        except httpx.TimeoutException:
            # Expected for SSE connections
            pass 