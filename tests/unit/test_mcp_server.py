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

# Import functions directly from smcp.py since they're not exported from the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the functions we want to test from smcp.py directly
import importlib.util
spec = importlib.util.spec_from_file_location("smcp_module", "smcp.py")
smcp_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smcp_module)

# Import the functions we want to test
discover_plugins = smcp_module.discover_plugins
get_plugin_help = smcp_module.get_plugin_help
execute_plugin_tool = smcp_module.execute_plugin_tool
create_tool_from_plugin = smcp_module.create_tool_from_plugin
register_plugin_tools = smcp_module.register_plugin_tools
plugin_registry = smcp_module.plugin_registry


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
        # Set environment variable to use our test directory
        plugins_dir = tmp_path / "plugins"
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
    
    @patch.object(smcp_module, "subprocess")
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
    
    @patch.object(smcp_module, "subprocess")
    def test_get_plugin_help_failure(self, mock_run):
        """Test plugin help retrieval failure."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Command failed"
        
        help_text = get_plugin_help("test_plugin", "/path/to/cli.py")
        
        assert help_text == ""
    
    @patch.object(smcp_module, "subprocess")
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
    
    @patch.object(smcp_module, "asyncio")
    async def test_execute_plugin_tool_success(self, mock_subprocess):
        """Test successful tool execution."""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"Success output", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        # Mock plugin registry
        with patch("smcp_module.plugin_registry", {"test_plugin": {"path": "/path/to/cli.py"}}):
            result = await execute_plugin_tool("test_plugin.test_command", {"arg1": "value1"})
        
        assert result == "Success output"
        mock_subprocess.assert_called_once()
    
    @patch.object(smcp_module, "asyncio")
    async def test_execute_plugin_tool_failure(self, mock_subprocess):
        """Test tool execution failure."""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Error output")
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process
        
        # Mock plugin registry
        with patch("smcp_module.plugin_registry", {"test_plugin": {"path": "/path/to/cli.py"}}):
            result = await execute_plugin_tool("test_plugin.test_command", {"arg1": "value1"})
        
        assert result == "Error: Error output"
    
    async def test_execute_plugin_tool_invalid_name(self):
        """Test tool execution with invalid tool name."""
        result = await execute_plugin_tool("invalid_tool_name", {})
        
        assert "Invalid tool name format" in result
    
    async def test_execute_plugin_tool_nonexistent_plugin(self):
        """Test tool execution with nonexistent plugin."""
        with patch.object(smcp_module, "plugin_registry", {}):
            result = await execute_plugin_tool("nonexistent_plugin.command", {})
        
        assert "Plugin 'nonexistent_plugin' not found" in result
    
    @patch.object(smcp_module, "asyncio")
    async def test_execute_plugin_tool_exception(self, mock_subprocess):
        """Test tool execution with exception."""
        mock_subprocess.side_effect = Exception("Subprocess error")
        
        with patch("smcp_module.plugin_registry", {"test_plugin": {"path": "/path/to/cli.py"}}):
            result = await execute_plugin_tool("test_plugin.test_command", {})
        
        assert "Error executing tool" in result


class TestToolCreation:
    """Test tool creation functionality."""
    
    def test_create_tool_from_plugin_click_button(self):
        """Test creating click-button tool."""
        tool = create_tool_from_plugin("botfather", "click-button")
        
        assert tool.name == "botfather.click-button"
        assert "click-button" in tool.description
        assert tool.inputSchema["type"] == "object"
    
    def test_create_tool_from_plugin_send_message(self):
        """Test creating send-message tool."""
        tool = create_tool_from_plugin("botfather", "send-message")
        
        assert tool.name == "botfather.send-message"
        assert "send-message" in tool.description
        assert tool.inputSchema["type"] == "object"
    
    def test_create_tool_from_plugin_deploy(self):
        """Test creating deploy tool."""
        tool = create_tool_from_plugin("devops", "deploy")
        
        assert tool.name == "devops.deploy"
        assert "deploy" in tool.description
        assert tool.inputSchema["type"] == "object"


class TestToolRegistration:
    """Test tool registration functionality."""
    
    @patch.object(smcp_module, "discover_plugins")
    @patch.object(smcp_module, "get_plugin_help")
    def test_register_plugin_tools(self, mock_help, mock_discover):
        """Test plugin tool registration."""
        # Mock discovered plugins
        mock_discover.return_value = {
            "test_plugin": {"path": "/path/to/cli.py"}
        }
        
        # Mock help text with commands
        mock_help.return_value = "Available commands:\n  test-command\n  another-command"
        
        # Mock server
        mock_server = Mock()
        
        # Mock global plugin_registry
        with patch.object(smcp_module, "plugin_registry", {}):
            register_plugin_tools(mock_server)
            
            # Verify server methods were called
            mock_server.list_tools.assert_called_once()
            mock_server.call_tool.assert_called_once()
    
    @patch.object(smcp_module, "discover_plugins")
    @patch.object(smcp_module, "get_plugin_help")
    def test_register_plugin_tools_no_commands(self, mock_help, mock_discover):
        """Test plugin tool registration with no commands."""
        mock_discover.return_value = {
            "test_plugin": {"path": "/path/to/cli.py"}
        }
        
        # Mock help text without commands section
        mock_help.return_value = "Just some help text"
        
        mock_server = Mock()
        
        with patch.object(smcp_module, "plugin_registry", {}):
            register_plugin_tools(mock_server)
            
            # Server methods should still be called even with no tools
            mock_server.list_tools.assert_called_once()
            mock_server.call_tool.assert_called_once()


# Health check tests removed - health_check function doesn't exist in current server implementation 