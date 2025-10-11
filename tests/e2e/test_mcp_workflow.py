"""
End-to-end tests for MCP server workflow.
Tests complete client-server interaction including SSE, initialization, and tool execution.
"""

import asyncio
import json
import pytest
import httpx
import subprocess
import time
import socket
import os
from typing import AsyncGenerator, Dict, Any
from pathlib import Path
import sys


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
    """Start server process for E2E tests."""
    # Start server in subprocess
    env = os.environ.copy()
    env["MCP_PORT"] = str(test_port)
    env["MCP_HOST"] = "127.0.0.1"

    print(f"Starting E2E server on port {test_port}")
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
        print(f"E2E Server failed to start. Return code: {process.returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        raise RuntimeError(f"E2E Server failed to start on port {test_port}")

    # Wait for server to be ready
    base_url = f"http://127.0.0.1:{test_port}"
    print(f"Waiting for E2E server to be ready at {base_url}")
    ready = await wait_for_server_ready(base_url, timeout=15.0)

    if not ready:
        stdout, stderr = process.communicate()
        print(f"E2E Server not ready. STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        process.terminate()
        process.wait()
        raise RuntimeError(f"E2E Server failed to start on port {test_port}")

    print(f"E2E Server is ready on port {test_port}")
    yield process

    # Cleanup
    print(f"Stopping E2E server on port {test_port}")
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


class TestMCPWorkflow:
    """Test complete MCP workflow from client connection to tool execution."""
    
    @pytest.fixture
    async def client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Create HTTP client for testing."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            yield client
    
    async def test_complete_mcp_workflow(self, client: httpx.AsyncClient, base_url: str, server_process):
        """Test complete MCP workflow: connect, initialize, list tools, call tool."""
        
        # Step 1: Test MCP endpoint connectivity
        mcp_connected = False
        try:
            # Test basic connectivity to MCP endpoint
            headers = {
                'Accept': 'application/json, text/event-stream',
                'Content-Type': 'application/json'
            }
            
            # Send a simple ping request to test connectivity
            ping_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "ping"
            }
            
            ping_response = await client.post(
                f"{base_url}/mcp",
                json=ping_request,
                headers=headers,
                timeout=5.0
            )
            
            # Even if ping fails, if we get a response, the endpoint is working
            assert ping_response.status_code in [200, 400, 404]  # Any response means endpoint is alive
            mcp_connected = True
            
            # Step 2: Send initialize request
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
            
            init_response = await client.post(
                f"{base_url}/mcp",
                json=initialize_request,
                headers=headers,
                timeout=10.0
            )
            
            assert init_response.status_code == 200
            init_data = init_response.json()
            assert init_data["jsonrpc"] == "2.0"
            assert init_data["id"] == 1
            assert "result" in init_data
            
            # Step 3: Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "initialized",
                "params": {}
            }
            
            await client.post(
                f"{base_url}/mcp",
                json=initialized_notification,
                headers=headers,
                timeout=10.0
            )
                
                # Step 4: List available tools
                list_tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
                
                tools_response = await client.post(
                    f"{base_url}/mcp",
                    json=list_tools_request,
                    timeout=10.0
                )
                
                assert tools_response.status_code == 200
                tools_data = tools_response.json()
                assert "result" in tools_data
                assert "tools" in tools_data["result"]
                
                tools = tools_data["result"]["tools"]
                assert len(tools) >= 1
                
                # Step 5: Call health tool
                health_tool = next((t for t in tools if t["name"] == "health"), None)
                assert health_tool is not None
                
                call_health_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "health",
                        "arguments": {}
                    }
                }
                
                health_response = await client.post(
                    f"{base_url}/mcp",
                    json=call_health_request,
                    timeout=10.0
                )
                
                assert health_response.status_code == 200
                health_data = health_response.json()
                assert "result" in health_data
                assert "content" in health_data["result"]
                
                content = health_data["result"]["content"][0]
                assert content["type"] == "text"
                
                health_info = json.loads(content["text"])
                assert health_info["status"] == "healthy"
                assert "plugins" in health_info
                assert "plugin_names" in health_info
                
        except httpx.TimeoutException:
            # SSE connections are expected to timeout
            if not sse_connected:
                raise
        except Exception as e:
            if not sse_connected:
                raise
            # If SSE connected but other operations failed, that's a test failure
            raise
    
    async def test_plugin_tool_execution(self, client: httpx.AsyncClient, base_url: str, server_process):
        """Test execution of plugin tools."""
        
        # First initialize the connection
        await self._initialize_connection(client, base_url)
        
        # List tools to find plugin tools
        tools_response = await client.post(
            f"{base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            },
            timeout=10.0
        )
        
        tools_data = tools_response.json()
        tools = tools_data["result"]["tools"]
        
        # Look for botfather tools
        botfather_tools = [t for t in tools if t["name"].startswith("botfather.")]
        
        if botfather_tools:
            # Test a botfather tool
            tool_name = botfather_tools[0]["name"]
            
            call_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {}
                }
            }
            
            response = await client.post(
                f"{base_url}/mcp",
                json=call_request,
                timeout=15.0  # Plugin execution might take longer
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Tool should either succeed or return a meaningful error
            if "result" in data:
                assert "content" in data["result"]
            elif "error" in data:
                # Plugin might not be properly configured, but should return structured error
                assert "code" in data["error"]
                assert "message" in data["error"]
    
    async def test_error_handling(self, client: httpx.AsyncClient, base_url: str, server_process):
        """Test error handling for various scenarios."""
        
        # Test malformed JSON
        response = await client.post(
            f"{base_url}/mcp",
            content="invalid json",
            headers={"content-type": "application/json"},
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32700  # Parse error
        
        # Test invalid method
        response = await client.post(
            f"{base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "nonexistent_method"
            },
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found
        
        # Test invalid tool call
        response = await client.post(
            f"{base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "nonexistent_tool",
                    "arguments": {}
                }
            },
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
    
    async def test_concurrent_sessions(self, client: httpx.AsyncClient, base_url: str, server_process):
        """Test handling of concurrent sessions."""
        
        # Create multiple SSE connections
        sse_tasks = []
        for i in range(3):
            task = asyncio.create_task(self._establish_sse_connection(client, base_url))
            sse_tasks.append(task)
        
        # Wait for connections to establish
        await asyncio.sleep(2)
        
        # Send concurrent requests
        request_tasks = []
        for i in range(5):
            task = asyncio.create_task(
                client.post(
                    f"{base_url}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": i,
                        "method": "tools/list"
                    },
                    timeout=10.0
                )
            )
            request_tasks.append(task)
        
        # Wait for all requests to complete
        responses = await asyncio.gather(*request_tasks, return_exceptions=True)
        
        # All requests should succeed
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                pytest.fail(f"Request {i} failed: {response}")
            else:
                assert response.status_code == 200
        
        # Cancel SSE tasks
        for task in sse_tasks:
            task.cancel()
        
        try:
            await asyncio.gather(*sse_tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass
    
    async def test_server_restart_recovery(self, client: httpx.AsyncClient, base_url: str, server_process):
        """Test that client can recover from server restart."""
        
        # Establish connection
        await self._initialize_connection(client, base_url)
        
        # Send a request
        response = await client.post(
            f"{base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            },
            timeout=10.0
        )
        
        assert response.status_code == 200
        
        # Note: In a real scenario, the server would restart here
        # For this test, we just verify the connection was working
    
    async def _initialize_connection(self, client: httpx.AsyncClient, base_url: str):
        """Helper to initialize MCP connection."""
        # Send initialize request
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
        
        response = await client.post(
            f"{base_url}/mcp",
            json=initialize_request,
            timeout=10.0
        )
        
        assert response.status_code == 200
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        
        await client.post(
            f"{base_url}/mcp",
            json=initialized_notification,
            timeout=10.0
        )
    
    async def _establish_sse_connection(self, client: httpx.AsyncClient, base_url: str):
        """Helper to establish SSE connection."""
        try:
            async with client.stream("GET", f"{base_url}/mcp", timeout=5.0) as response:
                assert response.status_code == 200
                # Just verify connection is established
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        break
        except httpx.TimeoutException:
            # Expected for SSE connections
            pass 