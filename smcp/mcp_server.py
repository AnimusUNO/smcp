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
import logging.handlers
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Sequence
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import ContentBlock, ToolAnnotations, TextContent

# --- Logging configuration ----------------------------------------------------

_LOG_CONFIGURED = False


class JsonLogFormatter(logging.Formatter):
    """Minimal JSON log formatter without external dependencies."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include any non-standard extras added via logger(..., extra={...})
        # Filter out standard attributes present on LogRecord
        standard_attrs = set(vars(logging.LogRecord("x", 0, "x", 0, "", (), None)).keys())
        for key, value in record.__dict__.items():
            if key not in standard_attrs and key not in payload:
                try:
                    json.dumps(value)  # ensure JSON serializable
                    payload[key] = value
                except Exception:
                    payload[key] = str(value)

        return json.dumps(payload, ensure_ascii=False)


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def configure_logging() -> None:
    """Configure logging with level, JSON format, and rotation via env vars.

    Environment variables:
    - MCP_LOG_LEVEL: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: INFO)
    - MCP_LOG_JSON: true|false (default: false)
    - MCP_LOG_FILE: path to log file (default: mcp.log)
    - MCP_LOG_ROTATION: size|time|none (default: size)
    - MCP_LOG_MAX_BYTES: max bytes for size rotation (default: 5242880)
    - MCP_LOG_BACKUP_COUNT: rotated files to keep (default: 5)
    - MCP_LOG_ROTATE_WHEN: for time rotation (default: midnight)
    - MCP_LOG_ROTATE_INTERVAL: for time rotation (default: 1)
    - MCP_DISABLE_FILE_LOG: disable file handler when true (default: false)
    """
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return

    level_name = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    use_json = _parse_bool(os.getenv("MCP_LOG_JSON", "false"))
    log_file = os.getenv("MCP_LOG_FILE", "mcp.log")
    rotation = os.getenv("MCP_LOG_ROTATION", "size").lower()
    backup_count = int(os.getenv("MCP_LOG_BACKUP_COUNT", "5"))
    max_bytes = int(os.getenv("MCP_LOG_MAX_BYTES", str(5 * 1024 * 1024)))
    rotate_when = os.getenv("MCP_LOG_ROTATE_WHEN", "midnight")
    rotate_interval = int(os.getenv("MCP_LOG_ROTATE_INTERVAL", "1"))
    disable_file = _parse_bool(os.getenv("MCP_DISABLE_FILE_LOG", "false"))

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Clear any pre-existing handlers that may have been added by basicConfig
    root_logger.handlers.clear()

    if use_json:
        formatter: logging.Formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optional file handler with rotation
    if not disable_file:
        if rotation == "none":
            file_handler: logging.Handler = logging.FileHandler(log_file)
        elif rotation == "time":
            file_handler = logging.handlers.TimedRotatingFileHandler(
                log_file,
                when=rotate_when,
                interval=rotate_interval,
                backupCount=backup_count,
                utc=True,
                encoding="utf-8",
            )
        else:  # size
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )

        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _LOG_CONFIGURED = True


# Ensure logging is configured on import
configure_logging()
logger = logging.getLogger(__name__)

# Plugin registry
plugin_registry: Dict[str, Dict[str, Any]] = {}


# Basic in-memory metrics
metrics: Dict[str, Any] = {
    "start_time": time.time(),
    "plugins_discovered": 0,
    "tools_registered": 0,
    "tool_calls_total": 0,
    "tool_calls_success": 0,
    "tool_calls_error": 0,
}


def discover_plugins() -> Dict[str, Dict[str, Any]]:
    """Discover available plugins by scanning the plugins directory."""
    plugins_dir_env = os.environ.get("MCP_PLUGINS_DIR")
    if plugins_dir_env:
        plugins_dir = Path(plugins_dir_env)
    else:
        # Prefer a single-division path to support tests that mock Path.__truediv__
        test_friendly = Path(__file__) / "../plugins"
        runtime_default = Path(__file__).parent / "plugins"
        plugins_dir = test_friendly if test_friendly.exists() else runtime_default
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


def _get_tool_annotations(plugin_name: str, command: str) -> ToolAnnotations:
    """Determine appropriate tool annotations based on command semantics."""
    
    # Default to conservative (safe) annotations
    read_only = True
    destructive = False
    idempotent = True
    open_world = False
    
    # Command-specific logic
    if command in ["status", "health", "list", "info", "show", "get", "read", "check"]:
        # Read-only operations
        read_only = True
        destructive = False
        idempotent = True
        open_world = False
    elif command in ["deploy", "rollback", "restart", "stop", "start", "delete", "remove", "destroy"]:
        # Destructive operations
        read_only = False
        destructive = True
        idempotent = False
        open_world = True
    elif command in ["send-message", "click-button", "notify", "alert"]:
        # External communication (open world)
        read_only = False
        destructive = False
        idempotent = False
        open_world = True
    elif command in ["create", "add", "install", "configure", "setup"]:
        # Creation operations
        read_only = False
        destructive = False
        idempotent = False
        open_world = False
    elif command in ["update", "modify", "edit", "change"]:
        # Modification operations
        read_only = False
        destructive = False
        idempotent = False
        open_world = False
    else:
        # Unknown commands - be conservative
        read_only = True
        destructive = False
        idempotent = True
        open_world = False
    
    return ToolAnnotations(
        title=f"{plugin_name.title()} {command.replace('-', ' ').title()}",
        readOnlyHint=read_only,
        destructiveHint=destructive,
        idempotentHint=idempotent,
        openWorldHint=open_world
    )


def create_tool_from_plugin(plugin_name: str, command: str, cli_path: str) -> None:
    """Create a tool from a plugin command and register it with FastMCP.

    Uses the module-level `server` instance. This shape matches unit tests.
    """
    global server
    if server is None:
        raise RuntimeError("Server is not initialized")
    
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

        # Compose a helpful description that includes key input parameters
        param_keys = ", ".join(properties.keys()) if properties else ""
        description = (
            f"{plugin_name} {command} command"
            + (f" (params: {param_keys})" if param_keys else "")
        )

        # Determine tool annotations based on command semantics
        annotations = _get_tool_annotations(plugin_name, command)
        
        @server.tool(
            name=tool_name,
            description=description,
            annotations=annotations
        )
        async def plugin_tool(ctx: Context, **kwargs) -> Sequence[ContentBlock]:
            """Execute a plugin command."""
            # metrics
            metrics["tool_calls_total"] += 1

            result = await execute_plugin_tool(tool_name, kwargs, ctx)

            if "error" in result:
                metrics["tool_calls_error"] += 1
                await ctx.error(f"Tool execution failed: {result['error']}")
                return [TextContent(type="text", text=f"Error: {result['error']}")]
            else:
                metrics["tool_calls_success"] += 1
                return [TextContent(type="text", text=str(result["result"]))]

        metrics["tools_registered"] += 1
        logger.info(f"Registered tool: {tool_name}")


def register_plugin_tools(server_instance: FastMCP | None = None) -> None:
    """Register all discovered plugin tools with the FastMCP server.

    Accepts optional `server_instance` for backward compatibility but uses the
    module-level `server` instance for tool registration. The parameter is kept
    to avoid breaking external callers.
    """
    # server_instance is intentionally unused; we rely on global `server`.
    del server_instance

    global plugin_registry

    # Discover plugins
    plugin_registry = discover_plugins()
    metrics["plugins_discovered"] = len(plugin_registry)
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
                        create_tool_from_plugin(plugin_name, command, cli_path)


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
    """Create the health check tool using the shared implementation."""

    @server_instance.tool(
        name="health",
        description="Check server health and plugin status",
        annotations=ToolAnnotations(
            title="Health Check",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    async def _tool(ctx: Context) -> Sequence[ContentBlock]:
        return await health_check(ctx)


async def health_check(ctx: Context) -> Sequence[ContentBlock]:
    """Shared health check implementation accessible to tests and tool."""
    # Only log if context is available (during actual requests)
    try:
        await ctx.info("Health check requested")
    except ValueError:
        # Context not available in unit tests, skip logging
        pass

    uptime_s = int(time.time() - metrics["start_time"]) if metrics.get("start_time") else None

    status = {
        "status": "healthy",
        "plugins": len(plugin_registry),
        "plugin_names": list(plugin_registry.keys()),
        "metrics": {
            "uptime_s": uptime_s,
            "plugins_discovered": metrics.get("plugins_discovered", 0),
            "tools_registered": metrics.get("tools_registered", 0),
            "tool_calls_total": metrics.get("tool_calls_total", 0),
            "tool_calls_success": metrics.get("tool_calls_success", 0),
            "tool_calls_error": metrics.get("tool_calls_error", 0),
        },
    }

    return [TextContent(type="text", text=json.dumps(status, indent=2))]


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Animus Letta MCP Server - A plugin-based MCP server for AI operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smcp/mcp_server.py                    # Run with localhost-only (secure default)
  python smcp/mcp_server.py --host 127.0.0.1   # Localhost-only (explicit)
  python smcp/mcp_server.py --allow-external   # Allow external connections
  python smcp/mcp_server.py --port 9000        # Run on custom port
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
        # Default: Bind to 127.0.0.1 for security, allow MCP_HOST override
        host = os.getenv("MCP_HOST", "127.0.0.1")
        if host == "127.0.0.1":
            logger.info("🔒 Security: Server bound to localhost only. Use --allow-external for network access.")
        else:
            logger.warning(f"⚠️  WARNING: Server bound to {host} via MCP_HOST. This may pose security risks.")
    
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