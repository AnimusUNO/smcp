"""
Unit tests for MCP server core functionality.
Tests plugin discovery, tool execution, and server components.
"""

import json
import pytest
import subprocess
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import os

# Import the functions we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from smcp.mcp_server import (
    discover_plugins,
    get_plugin_help,
    execute_plugin_tool,
    create_tool_from_plugin,
    register_plugin_tools,
    health_check,
    plugin_registry
)


class TestPluginDiscovery:
    """Test plugin discovery functionality."""
    
    def test_discover_plugins_with_env_var(self, tmp_path):
        """Test plugin discovery with MCP_PLUGINS_DIR environment variable."""
        # Create test plugins directory
        plugins_dir = tmp_path / "test_plugins"
        plugins_dir.mkdir()
        
        # Create a mock plugin
        plugin_dir = plugins_dir / "test_plugin"
        plugin_dir.mkdir()
        cli_file = plugin_dir / "cli.py"
        cli_file.write_text("# Test plugin")
        
        with patch.dict(os.environ, {"MCP_PLUGINS_DIR": str(plugins_dir)}):
            plugins = discover_plugins()
            
        assert "test_plugin" in plugins
        assert plugins["test_plugin"]["path"] == str(cli_file)
        assert "commands" in plugins["test_plugin"]
    
    def test_discover_plugins_default_path(self, tmp_path):
        """Test plugin discovery with default path."""
        # Mock the plugins directory relative to the script
        with patch("smcp.mcp_server.Path") as mock_path:
            mock_path.return_value.__truediv__.return_value = tmp_path / "plugins"
            plugins_dir = tmp_path / "plugins"
            plugins_dir.mkdir()
            
            # Create a mock plugin
            plugin_dir = plugins_dir / "test_plugin"
            plugin_dir.mkdir()
            cli_file = plugin_dir / "cli.py"
            cli_file.write_text("# Test plugin")
            
            plugins = discover_plugins()
            
        assert "test_plugin" in plugins
        assert plugins["test_plugin"]["path"] == str(cli_file)
    
    def test_discover_plugins_nonexistent_directory(self):
        """Test plugin discovery with nonexistent directory."""
        with patch.dict(os.environ, {"MCP_PLUGINS_DIR": "/nonexistent/path"}):
            plugins = discover_plugins()
            
        assert plugins == {}
    
    def test_discover_plugins_empty_directory(self, tmp_path):
        """Test plugin discovery with empty directory."""
        plugins_dir = tmp_path / "empty_plugins"
        plugins_dir.mkdir()
        
        with patch.dict(os.environ, {"MCP_PLUGINS_DIR": str(plugins_dir)}):
            plugins = discover_plugins()
            
        assert plugins == {}
    
    def test_discover_plugins_missing_cli_file(self, tmp_path):
        """Test plugin discovery with directory missing cli.py."""
        plugins_dir = tmp_path / "test_plugins"
        plugins_dir.mkdir()
        
        # Create plugin directory without cli.py
        plugin_dir = plugins_dir / "test_plugin"
        plugin_dir.mkdir()
        
        with patch.dict(os.environ, {"MCP_PLUGINS_DIR": str(plugins_dir)}):
            plugins = discover_plugins()
            
        assert plugins == {}


class TestPluginHelp:
    """Test plugin help functionality."""
    
    @patch("smcp.mcp_server.subprocess.run")
    def test_get_plugin_help_success(self, mock_run):
        """Test successful plugin help retrieval."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Available commands:\n  test-command\n  another-command"
        
        help_text = get_plugin_help("test_plugin", "/path/to/cli.py")
        
        assert help_text == "Available commands:\n  test-command\n  another-command"
        mock_run.assert_called_once_with(
            [sys.executable, "/path/to/cli.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
    
    @patch("smcp.mcp_server.subprocess.run")
    def test_get_plugin_help_failure(self, mock_run):
        """Test plugin help retrieval failure."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Command failed"
        
        help_text = get_plugin_help("test_plugin", "/path/to/cli.py")
        
        assert help_text == ""
    
    @patch("smcp.mcp_server.subprocess.run")
    def test_get_plugin_help_timeout(self, mock_run):
        """Test plugin help retrieval timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)
        
        help_text = get_plugin_help("test_plugin", "/path/to/cli.py")
        
        assert help_text == ""


class TestToolExecution:
    """Test tool execution functionality."""
    
    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context for testing."""
        ctx = AsyncMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        return ctx
    
    @patch("smcp.mcp_server.asyncio.create_subprocess_exec")
    async def test_execute_plugin_tool_success(self, mock_subprocess, mock_ctx):
        """Test successful tool execution."""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"Success output", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        # Mock plugin registry
        with patch("smcp.mcp_server.plugin_registry", {"test_plugin": {"path": "/path/to/cli.py"}}):
            result = await execute_plugin_tool("test_plugin.test_command", {"arg1": "value1"}, mock_ctx)
        
        assert result["result"] == "Success output"
        mock_ctx.info.assert_called()
        mock_subprocess.assert_called_once()
    
    @patch("smcp.mcp_server.asyncio.create_subprocess_exec")
    async def test_execute_plugin_tool_failure(self, mock_subprocess, mock_ctx):
        """Test tool execution failure."""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Error output")
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process
        
        # Mock plugin registry
        with patch("smcp.mcp_server.plugin_registry", {"test_plugin": {"path": "/path/to/cli.py"}}):
            result = await execute_plugin_tool("test_plugin.test_command", {"arg1": "value1"}, mock_ctx)
        
        assert result["error"] == "Error output"
        mock_ctx.error.assert_called()
    
    async def test_execute_plugin_tool_invalid_name(self, mock_ctx):
        """Test tool execution with invalid tool name."""
        result = await execute_plugin_tool("invalid_tool_name", {}, mock_ctx)
        
        assert "error" in result
        assert "Invalid tool name format" in result["error"]
    
    async def test_execute_plugin_tool_nonexistent_plugin(self, mock_ctx):
        """Test tool execution with nonexistent plugin."""
        with patch("smcp.mcp_server.plugin_registry", {}):
            result = await execute_plugin_tool("nonexistent_plugin.command", {}, mock_ctx)
        
        assert "error" in result
        assert "Plugin 'nonexistent_plugin' not found" in result["error"]
    
    @patch("smcp.mcp_server.asyncio.create_subprocess_exec")
    async def test_execute_plugin_tool_exception(self, mock_subprocess, mock_ctx):
        """Test tool execution with exception."""
        mock_subprocess.side_effect = Exception("Subprocess error")
        
        with patch("smcp.mcp_server.plugin_registry", {"test_plugin": {"path": "/path/to/cli.py"}}):
            result = await execute_plugin_tool("test_plugin.test_command", {}, mock_ctx)
        
        assert "error" in result
        assert "Subprocess error" in result["error"]
        mock_ctx.error.assert_called()


class TestToolCreation:
    """Test tool creation functionality."""
    
    @patch("smcp.mcp_server.get_plugin_help")
    def test_create_tool_from_plugin_click_button(self, mock_help):
        """Test creating click-button tool."""
        mock_help.return_value = "Help text"
        
        # Mock the server.tool decorator
        with patch("smcp.mcp_server.server") as mock_server:
            create_tool_from_plugin("botfather", "click-button", "/path/to/cli.py")
            
            # Verify tool was registered
            mock_server.tool.assert_called()
            call_args = mock_server.tool.call_args
            assert call_args[1]["name"] == "botfather.click-button"
            assert "button-text" in call_args[1]["description"]
    
    @patch("smcp.mcp_server.get_plugin_help")
    def test_create_tool_from_plugin_send_message(self, mock_help):
        """Test creating send-message tool."""
        mock_help.return_value = "Help text"
        
        with patch("smcp.mcp_server.server") as mock_server:
            create_tool_from_plugin("botfather", "send-message", "/path/to/cli.py")
            
            call_args = mock_server.tool.call_args
            assert call_args[1]["name"] == "botfather.send-message"
            assert "message" in call_args[1]["description"]
    
    @patch("smcp.mcp_server.get_plugin_help")
    def test_create_tool_from_plugin_deploy(self, mock_help):
        """Test creating deploy tool."""
        mock_help.return_value = "Help text"
        
        with patch("smcp.mcp_server.server") as mock_server:
            create_tool_from_plugin("devops", "deploy", "/path/to/cli.py")
            
            call_args = mock_server.tool.call_args
            assert call_args[1]["name"] == "devops.deploy"
            assert "app-name" in call_args[1]["description"]


class TestToolRegistration:
    """Test tool registration functionality."""
    
    @patch("smcp.mcp_server.discover_plugins")
    @patch("smcp.mcp_server.get_plugin_help")
    @patch("smcp.mcp_server.create_tool_from_plugin")
    def test_register_plugin_tools(self, mock_create_tool, mock_help, mock_discover):
        """Test plugin tool registration."""
        # Mock discovered plugins
        mock_discover.return_value = {
            "test_plugin": {"path": "/path/to/cli.py"}
        }
        
        # Mock help text with commands
        mock_help.return_value = "Available commands:\n  test-command\n  another-command"
        
        # Mock global plugin_registry
        with patch("smcp.mcp_server.plugin_registry", {}):
            register_plugin_tools()
            
            # Verify tools were created
            assert mock_create_tool.call_count == 2
            calls = mock_create_tool.call_args_list
            assert calls[0][0] == ("test_plugin", "test-command", "/path/to/cli.py")
            assert calls[1][0] == ("test_plugin", "another-command", "/path/to/cli.py")
    
    @patch("smcp.mcp_server.discover_plugins")
    @patch("smcp.mcp_server.get_plugin_help")
    @patch("smcp.mcp_server.create_tool_from_plugin")
    def test_register_plugin_tools_no_commands(self, mock_create_tool, mock_help, mock_discover):
        """Test plugin tool registration with no commands."""
        mock_discover.return_value = {
            "test_plugin": {"path": "/path/to/cli.py"}
        }
        
        # Mock help text without commands section
        mock_help.return_value = "Just some help text"
        
        with patch("smcp.mcp_server.plugin_registry", {}):
            register_plugin_tools()
            
            # No tools should be created
            mock_create_tool.assert_not_called()


class TestHealthTool:
    """Test health tool functionality."""
    
    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context for testing."""
        ctx = AsyncMock()
        ctx.info = AsyncMock()
        return ctx
    
    async def test_health_check_success(self, mock_ctx):
        """Test successful health check."""
        # Import the health check function
        from smcp.mcp_server import health_check
        
        # Mock plugin registry
        with patch("smcp.mcp_server.plugin_registry", {"test_plugin": {"path": "/path/to/cli.py"}}):
            result = await health_check(mock_ctx)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        health_data = json.loads(result[0].text)
        assert health_data["status"] == "healthy"
        assert health_data["plugins"] == 1
        assert "test_plugin" in health_data["plugin_names"]
    
    async def test_health_check_no_plugins(self, mock_ctx):
        """Test health check with no plugins."""
        from smcp.mcp_server import health_check
        
        with patch("smcp.mcp_server.plugin_registry", {}):
            result = await health_check(mock_ctx)
        
        health_data = json.loads(result[0].text)
        assert health_data["status"] == "healthy"
        assert health_data["plugins"] == 0
        assert health_data["plugin_names"] == [] 