#!/usr/bin/env python3
"""
Animus Letta MCP Server - Base MCP Implementation

A Server-Sent Events (SSE) server for orchestrating plugin execution using the base MCP library.
Compliant with Model Context Protocol (MCP) specification and compatible with Letta's SSE client.

Copyright (c) 2025 Mark Rizzn Hopkins

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
import asyncio
import json
import logging
import logging.handlers
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Sequence
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool

# Global variables
server: Server | None = None
plugin_registry: Dict[str, Dict[str, Any]] = {}
metrics: Dict[str, Any] = {
    "start_time": time.time(),
    "plugins_discovered": 0,
    "tools_registered": 0,
    "tool_calls_total": 0,
    "tool_calls_success": 0,
    "tool_calls_error": 0,
}

# Configure logging
def setup_logging():
    """Set up logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "mcp_server.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from some libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    return logging.getLogger(__name__)

logger = setup_logging()


def discover_plugins() -> Dict[str, Dict[str, Any]]:
    """Discover available plugins in the plugins directory."""
    plugins_dir = Path("/root/sanctum/smcp/v1/plugins")
    plugins = {}
    
    if not plugins_dir.exists():
        logger.warning(f"Plugins directory not found: {plugins_dir}")
        return plugins
    
    logger.info("Discovering plugins...")
    
    for plugin_dir in plugins_dir.iterdir():
        if plugin_dir.is_dir():
            cli_path = plugin_dir / "cli.py"
            if cli_path.exists():
                plugin_name = plugin_dir.name
                plugins[plugin_name] = {
                    "path": str(cli_path),
                    "commands": {}
                }
                logger.info(f"Discovered plugin: {plugin_name}")
    
    metrics["plugins_discovered"] = len(plugins)
    logger.info(f"Discovered {len(plugins)} plugins: {list(plugins.keys())}")
    
    return plugins


def get_plugin_help(plugin_name: str, cli_path: str) -> str:
    """Get help output from a plugin CLI."""
    try:
        result = subprocess.run(
            [sys.executable, cli_path, "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            logger.error(f"Plugin {plugin_name} help command failed: {result.stderr}")
            return ""
    except Exception as e:
        logger.error(f"Error getting help for plugin {plugin_name}: {e}")
        return ""


async def execute_plugin_tool(tool_name: str, arguments: dict) -> str:
    """Execute a plugin tool with the given arguments."""
    try:
        # Parse tool name to get plugin and command
        if '.' not in tool_name:
            return f"Invalid tool name format: {tool_name}. Expected 'plugin.command'"
        
        plugin_name, command = tool_name.split('.', 1)
        
        if plugin_name not in plugin_registry:
            return f"Plugin '{plugin_name}' not found"
        
        plugin_info = plugin_registry[plugin_name]
        cli_path = plugin_info["path"]
        
        # Build command arguments
        cmd_args = [sys.executable, cli_path, command]
        
        # Add arguments
        for key, value in arguments.items():
            if isinstance(value, bool):
                if value:
                    cmd_args.append(f"--{key}")
            else:
                cmd_args.extend([f"--{key}", str(value)])
        
        logger.info(f"Executing plugin command: {' '.join(cmd_args)}")
        
        # Execute the command
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            result = stdout.decode().strip()
            metrics["tool_calls_success"] += 1
            return result
        else:
            error_msg = stderr.decode().strip()
            metrics["tool_calls_error"] += 1
            return f"Error: {error_msg}"
            
    except Exception as e:
        error_msg = f"Error executing tool {tool_name}: {e}"
        logger.error(error_msg)
        metrics["tool_calls_error"] += 1
        return error_msg


def create_tool_from_plugin(plugin_name: str, command: str) -> Tool:
    """Create an MCP Tool from a plugin command."""
    tool_name = f"{plugin_name}.{command}"
    
    # Create a description based on the plugin and command
    description = f"Execute {plugin_name} {command} command"
    
    # Create a valid schema that passes Letta's validation
    # Use a simple object schema with no properties (empty object)
    return Tool(
        name=tool_name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
    )


def register_plugin_tools(server: Server):
    """Register all discovered plugin tools with the MCP server."""
    global plugin_registry
    
    # Discover plugins
    plugin_registry = discover_plugins()
    
    # Collect all tools
    all_tools = []
    
    # Create tools for each plugin
    for plugin_name, plugin_info in plugin_registry.items():
        cli_path = plugin_info["path"]
        
        # Get help to extract available commands
        help_text = get_plugin_help(plugin_name, cli_path)
        lines = help_text.split('\n')
        in_commands_section = False
        
        for line in lines:
            if line.strip().startswith("Available commands:"):
                in_commands_section = True
                continue
            if in_commands_section:
                # End of commands section if we hit an empty line or Examples
                if not line.strip() or line.strip().startswith("Examples"):
                    in_commands_section = False
                    continue
                if line.startswith('  '):
                    parts = line.strip().split()
                    if parts and parts[0] not in ['usage:', 'options:', 'Available', 'Examples:']:
                        command = parts[0]
                        
                        # Create tool
                        tool = create_tool_from_plugin(plugin_name, command)
                        all_tools.append(tool)
                        
                        logger.info(f"Created tool: {tool.name}")
                        metrics["tools_registered"] += 1
    
    # Register the list_tools handler
    @server.list_tools()
    async def list_tools_handler():
        """Return the list of available tools."""
        logger.info(f"Returning {len(all_tools)} tools: {[tool.name for tool in all_tools]}")
        # Log the actual tool schemas for debugging
        for tool in all_tools:
            logger.info(f"Tool {tool.name} schema: {tool.inputSchema}")
        return all_tools
    
    # Register the call_tool handler
    @server.call_tool()
    async def call_tool_handler(tool_name: str, arguments: dict):
        """Handle tool calls."""
        logger.info(f"Tool call: {tool_name} with args: {arguments}")
        metrics["tool_calls_total"] += 1
        result = await execute_plugin_tool(tool_name, arguments)
        logger.info(f"Tool result: {result}")
        return [TextContent(type="text", text=str(result))]


def create_server(host: str, port: int) -> Server:
    """Create and configure the MCP server instance."""
    # Create base MCP server (not FastMCP)
    server = Server(name="animus-letta-mcp", version="1.0.0")
    
    return server


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Animus Letta MCP Server - Base MCP implementation with SSE transport",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mcp_server.py                    # Run with localhost-only (secure default)
  python mcp_server.py --host 127.0.0.1   # Localhost-only (explicit)
  python mcp_server.py --allow-external   # Allow external connections
  python mcp_server.py --port 9000        # Run on custom port
        """
    )
    
    parser.add_argument(
        "--allow-external",
        action="store_true",
        help="Allow external connections (default: localhost-only for security)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8000")),
        help="Port to run the server on (default: 8000 or MCP_PORT env var)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind to (default: 127.0.0.1 for localhost-only, 0.0.0.0 for all interfaces)"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Determine host binding
    if args.allow_external:
        host = "0.0.0.0"
        logger.warning("⚠️  WARNING: External connections are allowed. This may pose security risks.")
    else:
        host = args.host or "127.0.0.1"
        if host == "127.0.0.1":
            logger.info("🔒 Security: Server bound to localhost only. Use --allow-external for network access.")
    
    logger.info(f"Starting Animus Letta MCP Server on {host}:{args.port}...")
    
    # Create MCP server
    global server
    server = create_server(host, args.port)
    
    # Register plugin tools
    register_plugin_tools(server)
    
    # Create SSE transport
    sse_transport = SseServerTransport("/messages/")
    
    # Create Starlette app with SSE endpoints
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import Response
    
    async def sse_endpoint(request):
        """SSE connection endpoint."""
        # Use SSE transport's connect_sse method with proper streams
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            # Run the MCP server with the SSE streams
            await server.run(
                streams[0],  # read_stream
                streams[1],  # write_stream
                server.create_initialization_options()
            )
        # Return empty response to avoid NoneType error
        return Response()
    
    async def sse_post_endpoint(request):
        """Handle POST requests to /sse (for Letta compatibility)."""
        # Create a simple response for POST requests to /sse
        # This handles Letta's incorrect POST to /sse instead of /messages/
        try:
            # Try to parse the request body as JSON
            body = await request.body()
            if body:
                # If there's a body, it's likely a JSON-RPC message
                # Return a helpful error message
                return Response(
                    "POST requests to /sse should be sent to /messages/ instead. "
                    "Use GET /sse to establish SSE connection, then POST to /messages/ to send messages.",
                    status_code=400,
                    media_type="text/plain"
                )
            else:
                # Empty POST request
                return Response("Empty POST request", status_code=400)
        except Exception as e:
            return Response(f"Error processing request: {str(e)}", status_code=500)
    
    # Create Starlette app
    app = Starlette(routes=[
        Route("/sse", sse_endpoint, methods=["GET"]),
        Route("/sse", sse_post_endpoint, methods=["POST"]),
        Mount("/messages/", app=sse_transport.handle_post_message),
    ])
    
    # Start server with proper signal handling
    logger.info("Starting server with SSE transport...")
    import uvicorn
    import signal
    
    # Create server config
    config = uvicorn.Config(
        app,
        host=host,
        port=args.port,
        log_level="info"
    )
    
    # Create server instance
    server_instance = uvicorn.Server(config)
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        server_instance.should_exit = True
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start server
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())
