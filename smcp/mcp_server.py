#!/usr/bin/env python3
"""
Animus Letta MCP Server

A Server-Sent Events (SSE) server for orchestrating plugin execution using the official MCP library.
Compliant with Model Context Protocol (MCP) specification.

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
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Sequence
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import ContentBlock, ToolAnnotations, TextContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Plugin registry
plugin_registry: Dict[str, Dict[str, Any]] = {}


def discover_plugins() -> Dict[str, Dict[str, Any]]:
    """Discover available plugins by scanning the plugins directory."""
    plugins_dir_env = os.environ.get("MCP_PLUGINS_DIR")
    if plugins_dir_env:
        plugins_dir = Path(plugins_dir_env)
    else:
        plugins_dir = Path(__file__).parent / "plugins"
    plugins = {}
    
    if not plugins_dir.exists():
        logger.warning(f"Plugins directory not found: {plugins_dir}")
        return plugins
    
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


async def execute_plugin_tool(tool_name: str, arguments: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    """Execute a plugin tool."""
    try:
        # Parse tool name to get plugin and command
        if '.' not in tool_name:
            return {"error": f"Invalid tool name format: {tool_name}. Expected 'plugin.command'"}
        
        plugin_name, command = tool_name.split('.', 1)
        
        if plugin_name not in plugin_registry:
            return {"error": f"Plugin '{plugin_name}' not found"}
        
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
        await ctx.info(f"Executing: {' '.join(cmd_args)}")
        
        # Execute the command
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            result = stdout.decode().strip()
            await ctx.info(f"Command completed successfully: {result}")
            return {"result": result}
        else:
            error_msg = stderr.decode().strip()
            await ctx.error(f"Command failed: {error_msg}")
            return {"error": error_msg}
            
    except Exception as e:
        error_msg = f"Error executing tool {tool_name}: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return {"error": error_msg}


def create_tool_from_plugin(server_instance: FastMCP, plugin_name: str, command: str, cli_path: str) -> None:
    """Create a tool from a plugin command and register it with FastMCP."""
    
    # Get help to determine parameters
    help_text = get_plugin_help(plugin_name, cli_path)
    
    # Define tool properties based on command
    properties = {}
    required = []
    
    if command == "click-button":
        properties = {
            "button-text": {"type": "string", "description": "Text of the button to click"},
            "msg-id": {"type": "integer", "description": "Message ID containing the button"}
        }
        required = ["button-text", "msg-id"]
    elif command == "send-message":
        properties = {
            "message": {"type": "string", "description": "Message to send"}
        }
        required = ["message"]
    elif command == "deploy":
        properties = {
            "app-name": {"type": "string", "description": "Name of the application to deploy"},
            "environment": {"type": "string", "description": "Deployment environment", "default": "production"}
        }
        required = ["app-name"]
    elif command == "rollback":
        properties = {
            "app-name": {"type": "string", "description": "Name of the application to rollback"},
            "version": {"type": "string", "description": "Version to rollback to"}
        }
        required = ["app-name", "version"]
    elif command == "status":
        properties = {
            "app-name": {"type": "string", "description": "Name of the application"}
        }
        required = ["app-name"]
    elif command == "workflow-command":
        properties = {
            "param": {"type": "string", "description": "Parameter for workflow"}
        }
        required = ["param"]
    elif command == "test-command":
        properties = {}
        required = []
    elif command == "error-command":
        properties = {}
        required = []
    elif command == "concurrent-command":
        properties = {}
        required = []
    
    if properties is not None:
        tool_name = f"{plugin_name}.{command}"
        
        @server_instance.tool(
            name=tool_name,
            description=f"{plugin_name} {command} command",
            annotations=ToolAnnotations(
                title=f"{plugin_name.title()} {command.replace('-', ' ').title()}",
                readOnlyHint=False,
                destructiveHint=True,
                idempotentHint=False,
                openWorldHint=True
            )
        )
        async def plugin_tool(ctx: Context, **kwargs) -> Sequence[ContentBlock]:
            """Execute a plugin command."""
            result = await execute_plugin_tool(tool_name, kwargs, ctx)
            
            if "error" in result:
                await ctx.error(f"Tool execution failed: {result['error']}")
                return [TextContent(type="text", text=f"Error: {result['error']}")]
            else:
                return [TextContent(type="text", text=str(result["result"]))]
        
        logger.info(f"Registered tool: {tool_name}")


def register_plugin_tools(server_instance: FastMCP) -> None:
    """Register all discovered plugin tools with the FastMCP server."""
    global plugin_registry
    
    # Discover plugins
    plugin_registry = discover_plugins()
    logger.info(f"Discovered {len(plugin_registry)} plugins")
    
    # Register tools for each plugin
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
                        create_tool_from_plugin(server_instance, plugin_name, command, cli_path)


# Global server instance (will be configured in main)
def create_server(host: str, port: int) -> FastMCP:
    """Create and configure the FastMCP server instance."""
    return FastMCP(
        name="animus-letta-mcp",
        instructions="A plugin-based MCP server for Animus Letta operations",
        sse_path="/sse",
        message_path="/messages/",
        host=host,
        port=port
    )

# Global server instance (will be set in main)
server = None


def create_health_tool(server_instance: FastMCP):
    """Create the health check tool."""
    @server_instance.tool(
        name="health",
        description="Check server health and plugin status",
        annotations=ToolAnnotations(
            title="Health Check",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False
        )
    )
    async def health_check(ctx: Context) -> Sequence[ContentBlock]:
        """Check server health and plugin status."""
        # Only log if context is available (during actual requests)
        try:
            await ctx.info("Health check requested")
        except ValueError:
            # Context not available in unit tests, skip logging
            pass
        
        status = {
            "status": "healthy",
            "plugins": len(plugin_registry),
            "plugin_names": list(plugin_registry.keys())
        }
        
        return [TextContent(type="text", text=json.dumps(status, indent=2))]


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Animus Letta MCP Server - A plugin-based MCP server for AI operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smcp/mcp_server.py                    # Run with localhost + Docker containers (default)
  python smcp/mcp_server.py --host 127.0.0.1   # Localhost-only (more restrictive)
  python smcp/mcp_server.py --allow-external   # Allow external connections
  python smcp/mcp_server.py --port 9000        # Run on custom port
        """
    )
    
    parser.add_argument(
        "--allow-external",
        action="store_true",
        help="Allow external connections (default: localhost + Docker containers)"
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
        help="Host to bind to (default: 0.0.0.0 for localhost + Docker, 127.0.0.1 for localhost-only)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Determine host binding based on security settings
    if args.host:
        host = args.host
    elif args.allow_external:
        host = "0.0.0.0"
        logger.warning("⚠️  WARNING: External connections are allowed. This may pose security risks.")
    else:
        # Default: Bind to 0.0.0.0 to allow localhost + Docker containers
        host = "0.0.0.0"
        logger.info("🔒 Security: Server bound to all interfaces (localhost + Docker containers). Use --host 127.0.0.1 for localhost-only.")
    
    logger.info(f"Starting Animus Letta MCP Server on {host}:{args.port}...")
    
    # Create server instance
    global server
    server = create_server(host, args.port)
    
    # Create health tool
    create_health_tool(server)
    
    # Register plugin tools
    register_plugin_tools(server)
    
    # Run the server with SSE transport
    logger.info("Starting server with SSE transport...")
    server.run(transport="sse")


if __name__ == "__main__":
    main() 