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
    # Use environment variable if set, otherwise use relative path
    plugins_dir_env = os.getenv("MCP_PLUGINS_DIR")
    if plugins_dir_env:
        plugins_dir = Path(plugins_dir_env)
    else:
        # Use relative path from current script location
        plugins_dir = Path(__file__).parent / "plugins"
    plugins = {}
    
    if not plugins_dir.exists():
        logger.warning(f"Plugins directory not found: {plugins_dir}")
        return plugins
    
    # Disabled plugins to keep tool count under Letta's recommended 23-tool limit
    disabled_plugins = os.getenv("MCP_DISABLED_PLUGINS", "botfather,devops").split(",")
    disabled_plugins = [p.strip() for p in disabled_plugins if p.strip()]
    
    logger.info("Discovering plugins...")
    if disabled_plugins:
        logger.info(f"Disabled plugins: {disabled_plugins}")
    
    for plugin_dir in plugins_dir.iterdir():
        if plugin_dir.is_dir():
            plugin_name = plugin_dir.name
            
            # Skip disabled plugins
            if plugin_name in disabled_plugins:
                logger.info(f"Skipping disabled plugin: {plugin_name}")
                continue
            
            cli_path = plugin_dir / "cli.py"
            if cli_path.exists():
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
        # Parse tool name to get plugin and command (format: plugin_command)
        if '_' not in tool_name:
            return f"Invalid tool name format: {tool_name}. Expected 'plugin_command'"
        
        plugin_name, command = tool_name.split('_', 1)
        
        if plugin_name not in plugin_registry:
            return f"Plugin '{plugin_name}' not found"
        
        plugin_info = plugin_registry[plugin_name]
        cli_path = plugin_info["path"]
        
        # Build command arguments
        cmd_args = [sys.executable, cli_path, command]
        
        # Filter out Letta-specific parameters that shouldn't be passed to plugins
        letta_params = {'request_heartbeat'}
        
        # Add arguments (excluding Letta-specific ones)
        for key, value in arguments.items():
            if key in letta_params:
                continue  # Skip Letta-specific parameters
            if isinstance(value, bool):
                if value:
                    cmd_args.append(f"--{key}")
            else:
                cmd_args.extend([f"--{key}", str(value)])
        
        logger.info(f"Executing plugin command: {' '.join(cmd_args)}")
        
        # Execute the command with current environment variables
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy()  # Pass environment variables to subprocess
        )
        
        stdout, stderr = await process.communicate()
        
        stdout_text = stdout.decode().strip()
        stderr_text = stderr.decode().strip()
        
        logger.info(f"Tool stdout: {stdout_text}")
        if stderr_text:
            logger.warning(f"Tool stderr: {stderr_text}")
        
        if process.returncode == 0:
            metrics["tool_calls_success"] += 1
            
            # Reload .env for wallet operations that may have updated it
            if tool_name in ['signer_create-wallet', 'signer_import-private-key']:
                from dotenv import load_dotenv
                load_dotenv(override=True)
                logger.info("Reloaded .env file after wallet operation")
            
            return stdout_text
        else:
            metrics["tool_calls_error"] += 1
            error_msg = stderr_text if stderr_text else stdout_text
            if not error_msg:
                error_msg = f"Command failed with return code {process.returncode}"
            return f"Error: {error_msg}"
            
    except Exception as e:
        error_msg = f"Error executing tool {tool_name}: {e}"
        logger.error(error_msg)
        metrics["tool_calls_error"] += 1
        return error_msg


def create_tool_from_plugin(plugin_name: str, command: str) -> Tool:
    """Create an MCP Tool from a plugin command."""
    # Use underscore instead of dot for OpenAI compatibility (must match ^[a-zA-Z0-9_-]+$)
    tool_name = f"{plugin_name}_{command}"
    
    # Create a description based on the plugin and command
    description = f"Execute {plugin_name} {command} command"
    
    # Define schemas for known tools with proper parameter definitions
    # Note: Use underscore format (plugin_command) for OpenAI compatibility
    tool_schemas = {
        "signer_create-wallet": {
            "description": "Create a new wallet in the local keystore. Automatically enables BSC operations without exposing private key to LLM. Uses SIGNER_PASSWORD from environment for encryption. Returns wallet label and address only.",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Unique label/name for the wallet"
                }
            },
            "required": ["label"]
        },
        "signer_import-private-key": {
            "description": "Import an existing private key into local keystore. Automatically enables BSC operations without exposing private key to LLM. Uses SIGNER_PASSWORD from environment for encryption. (development only)",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Unique label/name for the wallet"
                },
                "private-key": {
                    "type": "string",
                    "description": "Private key to import (hex format)"
                }
            },
            "required": ["label", "private-key"]
        },
        "signer_list-wallets": {
            "description": "List all wallets in the local keystore. Returns array of wallets with labels and addresses.",
            "properties": {},
            "required": []
        },
        "signer_get-address": {
            "description": "Get the address for a wallet by label",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Wallet label to look up"
                }
            },
            "required": ["label"]
        },
        "signer_sign-tx": {
            "description": "Sign a transaction and return the raw signed transaction hex. Uses SIGNER_PASSWORD from environment.",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Wallet label to sign with"
                },
                "tx": {
                    "type": "string",
                    "description": "JSON transaction object to sign"
                }
            },
            "required": ["label", "tx"]
        },
        "signer_send-tx": {
            "description": "Sign and broadcast a transaction to the blockchain, or broadcast a pre-signed raw transaction. Uses SIGNER_PASSWORD from environment.",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Wallet label to sign with (not required if providing raw)"
                },
                "tx": {
                    "type": "string",
                    "description": "JSON transaction object to sign (not required if providing raw)"
                },
                "raw": {
                    "type": "string",
                    "description": "Pre-signed raw transaction hex (if already signed)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which chain to broadcast to (default: mainnet)"
                }
            },
            "required": []
        },
        "signer_sign-typed-data": {
            "description": "Sign EIP-712 typed data (for permit signatures, etc). Uses SIGNER_PASSWORD from environment.",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Wallet label to sign with"
                },
                "typed-data": {
                    "type": "string",
                    "description": "JSON EIP-712 typed data to sign"
                }
            },
            "required": ["label", "typed-data"]
        },
        "bsc_get-balance": {
            "description": "Get native BNB balance for an address on BSC",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Wallet address to check (0x... format)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to query (default: mainnet)"
                }
            },
            "required": ["address"]
        },
        "bsc_get-token-balance": {
            "description": "Get ERC-20 token balance for an address on BSC",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Wallet address to check (0x... format)"
                },
                "token": {
                    "type": "string",
                    "description": "Token contract address (0x... format)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to query (default: mainnet)"
                }
            },
            "required": ["address", "token"]
        },
        "bsc_allowance": {
            "description": "Get ERC-20 token allowance for owner/spender pair",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "Token contract address (0x... format)"
                },
                "owner": {
                    "type": "string",
                    "description": "Token owner address (0x... format)"
                },
                "spender": {
                    "type": "string",
                    "description": "Spender address to check allowance for (0x... format)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to query (default: mainnet)"
                }
            },
            "required": ["token", "owner", "spender"]
        },
        "bsc_approve": {
            "description": "Approve ERC-20 token spender for a specific amount. Automatically uses your wallet's private key from environment - no credentials needed.",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "Token contract address (0x... format)"
                },
                "spender": {
                    "type": "string",
                    "description": "Spender address to approve (0x... format)"
                },
                "amount": {
                    "type": ["string", "number"],
                    "description": "Amount to approve in token's smallest unit (e.g., 1000000000000000000 for 1 token with 18 decimals)"
                },
                "broadcast": {
                    "type": "boolean",
                    "description": "Whether to broadcast transaction (default: true)"
                },
                "gas-price-gwei": {
                    "type": "number",
                    "description": "Gas price in Gwei (optional, uses network gas price if not provided)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to use (default: mainnet)"
                }
            },
            "required": ["token", "spender", "amount"]
        },
        "bsc_send-native": {
            "description": "Send native BNB to an address. Automatically uses your wallet's private key from environment - no credentials needed.",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient address (0x... format)"
                },
                "amount-eth": {
                    "type": ["string", "number"],
                    "description": "Amount to send in BNB (e.g., 0.01 for 0.01 BNB)"
                },
                "broadcast": {
                    "type": "boolean",
                    "description": "Whether to broadcast transaction (default: true)"
                },
                "gas-price-gwei": {
                    "type": "number",
                    "description": "Gas price in Gwei (optional, uses network gas price if not provided)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to use (default: mainnet)"
                }
            },
            "required": ["to", "amount-eth"]
        },
        "bsc_send-erc20": {
            "description": "Send ERC-20 tokens to an address. Automatically uses your wallet's private key from environment - no credentials needed.",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "Token contract address (0x... format)"
                },
                "to": {
                    "type": "string",
                    "description": "Recipient address (0x... format)"
                },
                "amount": {
                    "type": ["string", "number"],
                    "description": "Amount to send in token's smallest unit (e.g., 1000000000000000000 for 1 token with 18 decimals)"
                },
                "broadcast": {
                    "type": "boolean",
                    "description": "Whether to broadcast transaction (default: true)"
                },
                "gas-price-gwei": {
                    "type": "number",
                    "description": "Gas price in Gwei (optional, uses network gas price if not provided)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to use (default: mainnet)"
                }
            },
            "required": ["token", "to", "amount"]
        },
        "bsc_gas-price": {
            "description": "Get current gas price on BSC network",
            "properties": {
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to query (default: mainnet)"
                }
            },
            "required": []
        },
        "bsc_wrap-bnb": {
            "description": "Wrap native BNB to WBNB (Wrapped BNB). REQUIRED before adding liquidity on PancakeSwap with BNB pairs. Converts your native BNB balance to WBNB tokens. Automatically uses your wallet's private key from environment.",
            "properties": {
                "amount": {
                    "type": ["string", "number"],
                    "description": "Amount of native BNB to wrap in wei (e.g., 1000000000000000000 for 1 BNB)"
                },
                "broadcast": {
                    "type": "boolean",
                    "description": "Whether to broadcast transaction (default: true)"
                },
                "gas-price-gwei": {
                    "type": "number",
                    "description": "Gas price in Gwei (optional)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to use (default: mainnet)"
                }
            },
            "required": ["amount"]
        },
        "bsc_unwrap-bnb": {
            "description": "Unwrap WBNB to native BNB. Use this after selling tokens to convert WBNB back to spendable BNB. Automatically uses your wallet's private key from environment.",
            "properties": {
                "amount": {
                    "type": ["string", "number"],
                    "description": "Amount of WBNB to unwrap in wei (e.g., 1000000000000000000 for 1 WBNB)"
                },
                "broadcast": {
                    "type": "boolean",
                    "description": "Whether to broadcast transaction (default: true)"
                },
                "gas-price-gwei": {
                    "type": "number",
                    "description": "Gas price in Gwei (optional)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to use (default: mainnet)"
                }
            },
            "required": ["amount"]
        },
        "bsc_nonce": {
            "description": "Get transaction count (nonce) for an address on BSC",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Wallet address to check (0x... format)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to query (default: mainnet)"
                }
            },
            "required": ["address"]
        },
        "pancakeswap_get-pair-info": {
            "description": "Get PancakeSwap V2 pair address and reserves for a token pair. For BNB pairs, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c (mainnet)",
            "properties": {
                "token-a": {
                    "type": "string",
                    "description": "First token contract address (0x... format). For BNB, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
                },
                "token-b": {
                    "type": "string",
                    "description": "Second token contract address (0x... format). For BNB, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to query (default: mainnet)"
                }
            },
            "required": ["token-a", "token-b"]
        },
        "pancakeswap_quote-out": {
            "description": "Quote output amount for a PancakeSwap swap given input amount. Useful for price checking before swapping. IMPORTANT: For BNB swaps, use WBNB address: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c (mainnet) or 0xae13d989dac2f0debff460ac112a837c89baa7cd (testnet).",
            "properties": {
                "amount-in": {
                    "type": ["string", "number"],
                    "description": "Input amount in token's smallest unit (e.g., wei for 18 decimals)"
                },
                "token-in": {
                    "type": "string",
                    "description": "Input token contract address (0x... format). For BNB, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
                },
                "token-out": {
                    "type": "string",
                    "description": "Output token contract address (0x... format). For BNB, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
                },
                "path": {
                    "type": "string",
                    "description": "JSON array of token addresses for multi-hop swap. For BNB swaps use WBNB (0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c). Example: '[\"0xBB4CdB...\",\"0x06E08A9...\"]'"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to query (default: mainnet)"
                }
            },
            "required": ["amount-in"]
        },
        "pancakeswap_quote-in": {
            "description": "Quote required input amount for a PancakeSwap swap given desired output amount. Useful for exact output swaps. IMPORTANT: For BNB swaps, use WBNB address: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c (mainnet) or 0xae13d989dac2f0debff460ac112a837c89baa7cd (testnet).",
            "properties": {
                "amount-out": {
                    "type": ["string", "number"],
                    "description": "Desired output amount in token's smallest unit (e.g., wei for 18 decimals)"
                },
                "token-in": {
                    "type": "string",
                    "description": "Input token contract address (0x... format). For BNB, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
                },
                "token-out": {
                    "type": "string",
                    "description": "Output token contract address (0x... format). For BNB, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
                },
                "path": {
                    "type": "string",
                    "description": "JSON array of token addresses for multi-hop swap. For BNB swaps use WBNB (0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c). Example: '[\"0xBB4CdB...\",\"0x06E08A9...\"]'"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to query (default: mainnet)"
                }
            },
            "required": ["amount-out"]
        },
        "pancakeswap_swap-auto": {
            "description": "RECOMMENDED: Smart swap with NATIVE BNB SUPPORT - When swapping BNB for tokens, this tool automatically uses native BNB (no wrapping needed!). Just put WBNB address (0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c) as first token in path, and the tool detects it and uses your native BNB balance directly. For token→token swaps, handles approvals automatically. IMPORTANT: User has native BNB, not WBNB - always use this tool for BNB swaps so it uses native balance.",
            "properties": {
                "amount-in": {
                    "type": ["string", "number"],
                    "description": "Exact input amount in token's smallest unit (e.g., wei for 18 decimals)"
                },
                "path": {
                    "type": "string",
                    "description": "JSON array of token addresses defining the swap path. For BNB use WBNB (0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c on mainnet). Example: '[\"0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c\",\"0x06E08A9BFB83e0e791Cd1f24535aDA4fA4094444\"]'"
                },
                "to": {
                    "type": "string",
                    "description": "Recipient address for output tokens (0x... format)"
                },
                "slippage": {
                    "type": "number",
                    "description": "Slippage tolerance percentage. DEFAULT VALUES: 1-3% stablecoins, 5-10% major tokens, 20-30% small-cap/meme tokens. WARNING: If previous swap failed with INSUFFICIENT_OUTPUT_AMOUNT, you MUST increase slippage by 10-20%. Small-cap tokens like ANIMUS typically need 25-30% minimum. This auto-calculates from FRESH quote."
                },
                "amount-out-min": {
                    "type": ["string", "number"],
                    "description": "IGNORED - This parameter is ignored. The tool always recalculates from fresh quote + slippage. Leave empty."
                },
                "broadcast": {
                    "type": "boolean",
                    "description": "Whether to broadcast transactions (default: true)"
                },
                "gas-price-gwei": {
                    "type": "number",
                    "description": "Gas price in Gwei (optional)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to use (default: mainnet)"
                }
            },
            "required": ["amount-in", "path", "to"]
        },
        "pancakeswap_swap-exact-tokens": {
            "description": "Advanced: Manual swap for exact tokens. Requires manual approval and slippage calculation. Most users should use swap-auto instead. For BNB swaps, ALWAYS use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c (mainnet). Automatically uses your wallet's private key from environment.",
            "properties": {
                "amount-in": {
                    "type": ["string", "number"],
                    "description": "Exact input amount in token's smallest unit (e.g., wei for 18 decimals)"
                },
                "amount-out-min": {
                    "type": ["string", "number"],
                    "description": "Minimum output amount for slippage protection. CRITICAL: Calculate this from quote-out result. For 1% slippage: quote_result * 0.99. For 5% slippage: quote_result * 0.95. Never use 0 (no protection). Recommended: 1-5% slippage for stable pairs, 5-10% for volatile pairs."
                },
                "path": {
                    "type": "string",
                    "description": "JSON array of token addresses defining the swap path. For BNB swaps MUST use WBNB (0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c on mainnet). Example: '[\"0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c\",\"0x06E08A9BFB83e0e791Cd1f24535aDA4fA4094444\"]'"
                },
                "to": {
                    "type": "string",
                    "description": "Recipient address for output tokens (0x... format)"
                },
                "broadcast": {
                    "type": "boolean",
                    "description": "Whether to broadcast transaction (default: true)"
                },
                "gas-price-gwei": {
                    "type": "number",
                    "description": "Gas price in Gwei (optional, uses network gas price if not provided)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to use (default: mainnet)"
                }
            },
            "required": ["amount-in", "path", "to"]
        },
        "pancakeswap_add-liquidity-v2": {
            "description": "Add liquidity to a PancakeSwap V2 pair with AUTOMATIC APPROVAL HANDLING. This tool automatically checks and approves BOTH tokens (token-a and token-b) for the PancakeSwap router before adding liquidity. No manual approval needed! Automatically uses your wallet's private key from environment - no credentials needed. For BNB pairs, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c (mainnet)",
            "properties": {
                "token-a": {
                    "type": "string",
                    "description": "First token contract address (0x... format). For BNB, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
                },
                "token-b": {
                    "type": "string",
                    "description": "Second token contract address (0x... format). For BNB, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
                },
                "amount-a-desired": {
                    "type": ["string", "number"],
                    "description": "Desired amount of token A in smallest unit"
                },
                "amount-b-desired": {
                    "type": ["string", "number"],
                    "description": "Desired amount of token B in smallest unit"
                },
                "amount-a-min": {
                    "type": ["string", "number"],
                    "description": "Minimum amount of token A (slippage protection, default: 0)"
                },
                "amount-b-min": {
                    "type": ["string", "number"],
                    "description": "Minimum amount of token B (slippage protection, default: 0)"
                },
                "to": {
                    "type": "string",
                    "description": "Recipient address for LP tokens (0x... format)"
                },
                "broadcast": {
                    "type": "boolean",
                    "description": "Whether to broadcast transaction (default: true)"
                },
                "gas-price-gwei": {
                    "type": "number",
                    "description": "Gas price in Gwei (optional)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to use (default: mainnet)"
                }
            },
            "required": ["token-a", "token-b", "amount-a-desired", "amount-b-desired", "to"]
        },
        "pancakeswap_remove-liquidity-v2": {
            "description": "Remove liquidity from a PancakeSwap V2 pair. Automatically uses your wallet's private key from environment - no credentials needed. For BNB pairs, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c (mainnet)",
            "properties": {
                "token-a": {
                    "type": "string",
                    "description": "First token contract address (0x... format). For BNB, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
                },
                "token-b": {
                    "type": "string",
                    "description": "Second token contract address (0x... format). For BNB, use WBNB: 0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
                },
                "liquidity": {
                    "type": ["string", "number"],
                    "description": "Amount of LP tokens to burn"
                },
                "amount-a-min": {
                    "type": ["string", "number"],
                    "description": "Minimum amount of token A to receive (slippage protection, default: 0)"
                },
                "amount-b-min": {
                    "type": ["string", "number"],
                    "description": "Minimum amount of token B to receive (slippage protection, default: 0)"
                },
                "to": {
                    "type": "string",
                    "description": "Recipient address for withdrawn tokens (0x... format)"
                },
                "broadcast": {
                    "type": "boolean",
                    "description": "Whether to broadcast transaction (default: true)"
                },
                "gas-price-gwei": {
                    "type": "number",
                    "description": "Gas price in Gwei (optional)"
                },
                "chain": {
                    "type": "string",
                    "enum": ["mainnet", "testnet"],
                    "description": "Which BSC network to use (default: mainnet)"
                }
            },
            "required": ["token-a", "token-b", "liquidity", "to"]
        },
        "coinmarketcap_get-price": {
            "description": "Get latest price and comprehensive market data for any cryptocurrency from CoinMarketCap. Returns price, volume, market cap, price changes (1h/24h/7d/30d/60d/90d), supply data, rank, and more.",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Cryptocurrency symbol (e.g., BTC, ETH, BNB). Use this OR slug, not both."
                },
                "slug": {
                    "type": "string",
                    "description": "Cryptocurrency slug (e.g., bitcoin, ethereum). Use this OR symbol, not both."
                },
                "convert": {
                    "type": "string",
                    "description": "Currency to convert to (default: USD). Examples: USD, EUR, BTC"
                }
            },
            "required": []
        },
        "coinmarketcap_get-info": {
            "description": "Get comprehensive information about any cryptocurrency including description, website, social links, contract addresses, platform info, tags, and full market data. Most detailed tool for token research.",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Cryptocurrency symbol (e.g., BTC, ETH, BNB). Use this OR slug, not both."
                },
                "slug": {
                    "type": "string",
                    "description": "Cryptocurrency slug (e.g., bitcoin, ethereum). Use this OR symbol, not both."
                },
                "convert": {
                    "type": "string",
                    "description": "Currency to convert to for price data (default: USD). Examples: USD, EUR, BTC"
                }
            },
            "required": []
        },
        "coinmarketcap_search": {
            "description": "Search for cryptocurrencies by name or symbol on CoinMarketCap.",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (cryptocurrency name or symbol)"
                },
                "limit": {
                    "type": ["string", "number"],
                    "description": "Maximum number of results to return (default: 10)"
                }
            },
            "required": ["query"]
        },
        "coinmarketcap_global-metrics": {
            "description": "Get global cryptocurrency market metrics including total market cap, volume, and BTC dominance.",
            "properties": {
                "convert": {
                    "type": "string",
                    "description": "Currency to convert to (default: USD). Examples: USD, EUR, BTC"
                }
            },
            "required": []
        }
    }
    
    # Use predefined schema if available, otherwise use generic schema
    if tool_name in tool_schemas:
        schema_def = tool_schemas[tool_name]
        logger.info(f"Creating tool {tool_name} with defined schema: {schema_def['required']} required params")
        return Tool(
            name=tool_name,
            description=schema_def["description"],
            inputSchema={
                "type": "object",
                "properties": schema_def["properties"],
                "required": schema_def["required"],
                "additionalProperties": False
            }
        )
    else:
        # Fallback for unknown tools
        logger.warning(f"Creating tool {tool_name} with generic schema (no predefined schema found)")
    return Tool(
        name=tool_name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": True
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
    # Load environment variables from .env file at startup
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    logger.info(f"Loaded environment from {env_path}")
    
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
