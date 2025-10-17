"""
Pytest configuration and fixtures for MCP Server tests.

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

import asyncio
import json
import os
import sys
import tempfile
import pytest
import aiohttp
from aiohttp.test_utils import TestClient, TestServer
from pathlib import Path
import pytest_asyncio
# Ensure pytest-asyncio plugin is loaded even if auto-discovery is disabled
pytest_plugins = ("pytest_asyncio",)

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functions directly from smcp.py since they're not exported from the package
import smcp


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_plugins_dir():
    """Create a temporary plugins directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        plugins_dir = Path(temp_dir) / "plugins"
        plugins_dir.mkdir()
        yield plugins_dir


@pytest.fixture
def mock_plugin_cli(temp_plugins_dir):
    """Create a mock plugin CLI for testing."""
    plugin_dir = temp_plugins_dir / "test_plugin"
    plugin_dir.mkdir()
    
    cli_path = plugin_dir / "cli.py"
    cli_content = '''#!/usr/bin/env python3
import argparse
import json
import sys

def test_command(args):
    return {"result": f"Test result: {args.get('param', 'default')}"}

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    test_parser = subparsers.add_parser("test-command")
    test_parser.add_argument("--param", default="default")
    
    args = parser.parse_args()
    
    if args.command == "test-command":
        result = test_command({"param": args.param})
        print(json.dumps(result))
        sys.exit(0)
    else:
        print(json.dumps({"error": "Unknown command"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open(cli_path, 'w') as f:
        f.write(cli_content)
    
    # Make it executable
    os.chmod(cli_path, 0o755)
    
    return cli_path


@pytest.fixture
def sample_jsonrpc_request():
    """Sample JSON-RPC request for testing."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "test_plugin.test-command",
            "arguments": {
                "param": "test_value"
            }
        }
    }


@pytest.fixture
def sample_jsonrpc_response():
    """Sample JSON-RPC response for testing."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "Test result: test_value"
                }
            ]
        }
    }


@pytest.fixture
def test_plugins_env(temp_plugins_dir):
    os.environ["MCP_PLUGINS_DIR"] = str(temp_plugins_dir)
    return temp_plugins_dir


@pytest.fixture
def temp_plugins_dir_with_plugins(request, temp_plugins_dir):
    # Create plugins as specified by the test param
    plugins = getattr(request, 'param', None)
    if plugins:
        for plugin in plugins:
            plugin_dir = temp_plugins_dir / plugin['name']
            plugin_dir.mkdir(parents=True, exist_ok=True)
            cli_path = plugin_dir / "cli.py"
            with open(cli_path, 'w') as f:
                f.write(plugin['cli_content'])
            os.chmod(cli_path, 0o755)
    os.environ["MCP_PLUGINS_DIR"] = str(temp_plugins_dir)
    return temp_plugins_dir


# FastMCP-specific fixtures removed - current server uses base MCP with SSE transport 