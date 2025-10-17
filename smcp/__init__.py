"""
SMCP Package - Animus Letta MCP Server

This package provides the main MCP server functionality.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import smcp.py
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import the main function from smcp.py (the file, not this package)
import importlib.util
spec = importlib.util.spec_from_file_location("smcp_module", parent_dir / "smcp.py")
smcp_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smcp_module)

# Export the main function
main = smcp_module.main

__version__ = "3.0.0"
__all__ = ["main"]
