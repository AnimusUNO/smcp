#!/usr/bin/env python3
"""
PancakeSwap (BSC) CLI Plugin

Implements common PancakeSwap V2 actions on BNB Chain (BSC):
 - Quote and perform token swaps
 - Add/Remove liquidity (V2)
 - Fetch pair addresses and reserves

Focuses on safe, explicit transaction building with optional broadcast.
Docs referenced: https://docs.pancakeswap.finance/earn/pancakeswap-pools/liquidity-guide

Environment variables:
  - BSC_RPC_URL / BSC_RPC_URL_TESTNET
  - BSC_PRIVATE_KEY
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware


FACTORY_V2 = Web3.to_checksum_address("0xCA143Ce32Fe78f1f7019d7d551a6402fC5350c73")
ROUTER_V2 = Web3.to_checksum_address("0x10ED43C718714eb63d5aA57B78B54704E256024E")
WBNB = Web3.to_checksum_address("0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")

# Testnet defaults
FACTORY_V2_TESTNET = Web3.to_checksum_address("0x6725F303b657a9451d8BA641348b6761A6CC7a17")
ROUTER_V2_TESTNET = Web3.to_checksum_address("0xD99D1c33F9fC3444f8101754aBC46c52416550D1")
WBNB_TESTNET = Web3.to_checksum_address("0xae13d989dac2f0debff460ac112a837c89baa7cd")


FACTORY_ABI = [
    {"constant": True, "inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}], "name": "getPair", "outputs": [{"name": "pair", "type": "address"}], "type": "function"}
]

PAIR_ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [{"name": "_reserve0", "type": "uint112"}, {"name": "_reserve1", "type": "uint112"}, {"name": "_blockTimestampLast", "type": "uint32"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]

ROUTER_ABI = [
    {"name": "getAmountsOut", "outputs": [{"name": "amounts", "type": "uint256[]"}], "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "path", "type": "address[]"}], "stateMutability": "view", "type": "function"},
    {"name": "getAmountsIn", "outputs": [{"name": "amounts", "type": "uint256[]"}], "inputs": [{"name": "amountOut", "type": "uint256"}, {"name": "path", "type": "address[]"}], "stateMutability": "view", "type": "function"},
    {"name": "swapExactTokensForTokens", "outputs": [{"name": "amounts", "type": "uint256[]"}], "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "amountOutMin", "type": "uint256"}, {"name": "path", "type": "address[]"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"name": "swapExactETHForTokens", "outputs": [{"name": "amounts", "type": "uint256[]"}], "inputs": [{"name": "amountOutMin", "type": "uint256"}, {"name": "path", "type": "address[]"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"name": "swapExactTokensForETH", "outputs": [{"name": "amounts", "type": "uint256[]"}], "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "amountOutMin", "type": "uint256"}, {"name": "path", "type": "address[]"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"name": "addLiquidity", "outputs": [{"name": "amountA", "type": "uint256"}, {"name": "amountB", "type": "uint256"}, {"name": "liquidity", "type": "uint256"}], "inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}, {"name": "amountADesired", "type": "uint256"}, {"name": "amountBDesired", "type": "uint256"}, {"name": "amountAMin", "type": "uint256"}, {"name": "amountBMin", "type": "uint256"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"name": "removeLiquidity", "outputs": [{"name": "amountA", "type": "uint256"}, {"name": "amountB", "type": "uint256"}], "inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}, {"name": "liquidity", "type": "uint256"}, {"name": "amountAMin", "type": "uint256"}, {"name": "amountBMin", "type": "uint256"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
]

MAINNET_DEFAULT_RPC = "https://bsc-dataseed.bnbchain.org"
TESTNET_DEFAULT_RPC = "https://data-seed-prebsc-1-s1.binance.org:8545"


def get_web3(chain: str) -> Tuple[Web3, str, str, str]:
    if chain == "testnet":
        rpc = os.getenv("BSC_RPC_URL_TESTNET", TESTNET_DEFAULT_RPC)
        w3 = Web3(Web3.HTTPProvider(rpc))
        # Inject PoA middleware for BSC (Proof of Authority chain)
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        return w3, FACTORY_V2_TESTNET, ROUTER_V2_TESTNET, WBNB_TESTNET
    rpc = os.getenv("BSC_RPC_URL", MAINNET_DEFAULT_RPC)
    w3 = Web3(Web3.HTTPProvider(rpc))
    # Inject PoA middleware for BSC (Proof of Authority chain)
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3, FACTORY_V2, ROUTER_V2, WBNB


def checksum(address: str) -> str:
    return Web3.to_checksum_address(address)


def get_factory(w3: Web3, factory: str):
    return w3.eth.contract(address=factory, abi=FACTORY_ABI)


def get_router(w3: Web3, router: str):
    return w3.eth.contract(address=router, abi=ROUTER_ABI)


def get_pair_info(args: Dict[str, Any]) -> Dict[str, Any]:
    w3, factory_addr, _, _ = get_web3(args.get("chain", "mainnet"))
    # Argparse converts hyphens to underscores
    token_a = checksum(args["token_a"]) if args.get("token_a") else None
    token_b = checksum(args["token_b"]) if args.get("token_b") else None
    if not token_a or not token_b:
        return {"error": "Missing required arguments: token-a, token-b"}
    factory = get_factory(w3, factory_addr)
    pair = factory.functions.getPair(token_a, token_b).call()
    if int(pair, 16) == 0:
        return {"pair": None, "exists": False}
    pair_addr = Web3.to_checksum_address(pair)
    pair_c = w3.eth.contract(address=pair_addr, abi=PAIR_ABI)
    r0, r1, ts = pair_c.functions.getReserves().call()
    t0 = pair_c.functions.token0().call()
    t1 = pair_c.functions.token1().call()
    return {"pair": pair_addr, "exists": True, "reserves": {"reserve0": str(r0), "reserve1": str(r1)}, "token0": Web3.to_checksum_address(t0), "token1": Web3.to_checksum_address(t1), "updatedAt": int(ts)}


def quote_out(args: Dict[str, Any]) -> Dict[str, Any]:
    w3, _, router_addr, wbnb = get_web3(args.get("chain", "mainnet"))
    amount_in = int(args["amount_in"]) if args.get("amount_in") else None
    path: List[str] = []
    if args.get("path"):
        path = [checksum(p) for p in json.loads(args["path"]) if p]
    else:
        token_in = checksum(args["token_in"]) if args.get("token_in") else None
        token_out = checksum(args["token_out"]) if args.get("token_out") else None
        if not token_in or not token_out:
            return {"error": "Provide either --path JSON or --token-in/--token-out"}
        path = [token_in, token_out]
    if amount_in is None or not path:
        return {"error": "Missing required arguments: amount-in and swap path"}
    router = get_router(w3, router_addr)
    amounts = router.functions.getAmountsOut(amount_in, path).call()
    return {"path": path, "amounts": [str(a) for a in amounts]}


def quote_in(args: Dict[str, Any]) -> Dict[str, Any]:
    w3, _, router_addr, _ = get_web3(args.get("chain", "mainnet"))
    amount_out = int(args["amount_out"]) if args.get("amount_out") else None
    path: List[str] = []
    if args.get("path"):
        path = [checksum(p) for p in json.loads(args["path"]) if p]
    else:
        token_in = checksum(args["token_in"]) if args.get("token_in") else None
        token_out = checksum(args["token_out"]) if args.get("token_out") else None
        if not token_in or not token_out:
            return {"error": "Provide either --path JSON or --token-in/--token-out"}
        path = [token_in, token_out]
    if amount_out is None or not path:
        return {"error": "Missing required arguments: amount-out and swap path"}
    router = get_router(w3, router_addr)
    amounts = router.functions.getAmountsIn(amount_out, path).call()
    return {"path": path, "amounts": [str(a) for a in amounts]}


def _base_tx(w3: Web3, from_addr: str, gas_price_gwei: Optional[float]):
    gas_price = w3.eth.gas_price if gas_price_gwei is None else int(gas_price_gwei * 1e9)
    return {"from": from_addr, "nonce": w3.eth.get_transaction_count(from_addr), "gasPrice": gas_price}


def _maybe_send(w3: Web3, tx, private_key: Optional[str], broadcast: bool):
    if not broadcast:
        return {"unsignedTx": {k: (hex(v) if isinstance(v, int) else v) for k, v in tx.items()}}
    if not private_key:
        return {"error": "Missing private key; set BSC_PRIVATE_KEY in .env"}
    try:
        from eth_account import Account
        signed = Account.sign_transaction(tx, private_key)
        # Use raw_transaction (underscore) for newer web3.py versions
        raw_tx = getattr(signed, 'raw_transaction', None) or getattr(signed, 'rawTransaction', None)
        h = w3.eth.send_raw_transaction(raw_tx)
        return {"txHash": h.hex()}
    except Exception as e:
        return {"error": str(e)}


def swap_auto(args: Dict[str, Any]) -> Dict[str, Any]:
    """Smart swap that automatically handles approvals and native BNB."""
    w3, _, router_addr, wbnb = get_web3(args.get("chain", "mainnet"))
    amount_in = int(args["amount_in"]) if args.get("amount_in") else None
    # Handle empty string or missing amount_out_min
    amount_out_min_str = args.get("amount_out_min", "0")
    amount_out_min = int(amount_out_min_str) if amount_out_min_str and amount_out_min_str != "" else 0
    path = [checksum(p) for p in json.loads(args["path"]) ] if args.get("path") else None
    to = checksum(args["to"]) if args.get("to") else None
    slippage_percent = float(args.get("slippage", 5.0))  # Default 5% slippage
    gas_price_gwei = args.get("gas_price_gwei")
    if gas_price_gwei is not None:
        gas_price_gwei = float(gas_price_gwei)
    private_key = args.get("private_key") or os.getenv("BSC_PRIVATE_KEY")
    if "broadcast" in args:
        broadcast = bool(args.get("broadcast"))
    else:
        broadcast = bool(private_key)
    
    if not amount_in or not path or not to:
        return {"error": "Missing required: amount-in, path(JSON), to"}
    if not private_key:
        return {"error": "Missing private key; set BSC_PRIVATE_KEY in .env"}
    
    from eth_account import Account
    from_addr = Web3.to_checksum_address(Account.from_key(private_key).address)
    
    # Get the input token from path
    token_in = path[0]
    
    # Check if this is a native BNB swap (input token is WBNB)
    is_native_bnb_swap = token_in.lower() == wbnb.lower()
    
    approval_txhash = None
    
    # Skip approval for native BNB swaps
    if not is_native_bnb_swap:
        # Check if approval is needed for token swaps
        erc20_abi = [
            {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
        ]
        
        token_contract = w3.eth.contract(address=token_in, abi=erc20_abi)
        current_allowance = token_contract.functions.allowance(from_addr, router_addr).call()
        
        approval_needed = current_allowance < amount_in
        
        if approval_needed:
            # Need approval - execute it first
            max_approval = 2**256 - 1  # Unlimited approval
            approve_tx = token_contract.functions.approve(router_addr, max_approval).build_transaction({
                "from": from_addr,
                "nonce": w3.eth.get_transaction_count(from_addr),
                "gasPrice": w3.eth.gas_price if gas_price_gwei is None else int(gas_price_gwei * 1e9)
            })
            
            # Estimate gas
            try:
                gas = w3.eth.estimate_gas(approve_tx)
                approve_tx["gas"] = int(gas * 1.2)
            except Exception as e:
                return {"error": f"Approval gas estimation failed: {str(e)}"}
            
            # Sign and send approval if broadcasting
            if broadcast:
                try:
                    signed_approve = Account.sign_transaction(approve_tx, private_key)
                    raw_tx = getattr(signed_approve, 'raw_transaction', None) or getattr(signed_approve, 'rawTransaction', None)
                    approval_txhash = w3.eth.send_raw_transaction(raw_tx).hex()
                    # Wait for approval to be mined
                    receipt = w3.eth.wait_for_transaction_receipt(Web3.to_bytes(hexstr=approval_txhash), timeout=120)
                    if receipt.status != 1:
                        return {"error": f"Approval transaction failed. TxHash: {approval_txhash}"}
                except Exception as e:
                    return {"error": f"Approval transaction failed: {str(e)}"}
            else:
                # If not broadcasting, return the unsigned approval tx
                return {
                    "approval_needed": True,
                    "unsigned_approval_tx": {k: (hex(v) if isinstance(v, int) else v) for k, v in approve_tx.items()},
                    "message": "Approval needed but broadcast=false. Approve first, then retry swap."
                }
    
    # ALWAYS calculate fresh amount_out_min from current quote + slippage
    # This ensures we use latest price and user's slippage tolerance
    router = get_router(w3, router_addr)
    amounts_out = router.functions.getAmountsOut(amount_in, path).call()
    expected_out = amounts_out[-1]
    amount_out_min = int(expected_out * (1 - slippage_percent / 100))
    
    # Always use fresh deadline
    deadline = int(w3.eth.get_block("latest").timestamp) + 1800
    
    # Build transaction based on swap type
    if is_native_bnb_swap:
        # Native BNB → Token swap (no approval needed)
        base_tx = _base_tx(w3, from_addr, gas_price_gwei)
        base_tx["value"] = amount_in  # Send BNB with transaction
        tx = router.functions.swapExactETHForTokens(
            amount_out_min, 
            path, 
            to, 
            deadline
        ).build_transaction(base_tx)
    else:
        # Token → Token swap (approval handled above)
        tx = router.functions.swapExactTokensForTokens(
            amount_in, 
            amount_out_min, 
            path, 
            to, 
            deadline
        ).build_transaction(_base_tx(w3, from_addr, gas_price_gwei))
    
    # Estimate gas
    try:
        gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas * 1.2)
    except Exception:
        tx["gas"] = 400000
    
    result = _maybe_send(w3, tx, private_key, broadcast)
    
    # Add approval info to result
    if approval_txhash:
        result["approval_tx"] = approval_txhash
        result["approval_status"] = "completed"
    
    # Add swap type info
    result["swap_type"] = "native_bnb_to_token" if is_native_bnb_swap else "token_to_token"
    
    return result


def swap_exact_tokens_for_tokens(args: Dict[str, Any]) -> Dict[str, Any]:
    w3, _, router_addr, _ = get_web3(args.get("chain", "mainnet"))
    amount_in = int(args["amount_in"]) if args.get("amount_in") else None
    amount_out_min = int(args.get("amount_out_min", 0))
    path = [checksum(p) for p in json.loads(args["path"]) ] if args.get("path") else None
    to = checksum(args["to"]) if args.get("to") else None
    # Always use fresh deadline (30 minutes from now) - ignore any provided deadline to prevent expiration issues
    deadline = int(w3.eth.get_block("latest").timestamp) + 1800
    gas_price_gwei = args.get("gas_price_gwei")
    if gas_price_gwei is not None:
        gas_price_gwei = float(gas_price_gwei)
    private_key = args.get("private_key") or os.getenv("BSC_PRIVATE_KEY")
    if "broadcast" in args:
        broadcast = bool(args.get("broadcast"))
    else:
        broadcast = bool(private_key)
    if not amount_in or not path or not to:
        return {"error": "Missing required: amount-in, path(JSON), to"}
    if not private_key:
        return {"error": "Missing private key; set BSC_PRIVATE_KEY in .env"}
    from eth_account import Account
    from_addr = Web3.to_checksum_address(Account.from_key(private_key).address)
    router = get_router(w3, router_addr)
    tx = router.functions.swapExactTokensForTokens(amount_in, amount_out_min, path, to, deadline).build_transaction(_base_tx(w3, from_addr, gas_price_gwei))
    try:
        gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas * 1.2)
    except Exception:
        tx["gas"] = 400000
    return _maybe_send(w3, tx, private_key, broadcast)


def add_liquidity_v2(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add liquidity with automatic approval handling for both tokens."""
    w3, _, router_addr, _ = get_web3(args.get("chain", "mainnet"))
    token_a = checksum(args["token_a"]) if args.get("token_a") else None
    token_b = checksum(args["token_b"]) if args.get("token_b") else None
    amt_a_desired = int(args["amount_a_desired"]) if args.get("amount_a_desired") else None
    amt_b_desired = int(args["amount_b_desired"]) if args.get("amount_b_desired") else None
    amt_a_min = int(args.get("amount_a_min", 0))
    amt_b_min = int(args.get("amount_b_min", 0))
    to = checksum(args["to"]) if args.get("to") else None
    # Always use fresh deadline (30 minutes from now) - ignore any provided deadline to prevent expiration issues
    deadline = int(w3.eth.get_block("latest").timestamp) + 1800
    gas_price_gwei = args.get("gas_price_gwei")
    if gas_price_gwei is not None:
        gas_price_gwei = float(gas_price_gwei)
    private_key = args.get("private_key") or os.getenv("BSC_PRIVATE_KEY")
    if "broadcast" in args:
        broadcast = bool(args.get("broadcast"))
    else:
        broadcast = bool(private_key)
    if not token_a or not token_b or amt_a_desired is None or amt_b_desired is None or not to:
        return {"error": "Missing required: token-a, token-b, amount-a-desired, amount-b-desired, to"}
    if not private_key:
        return {"error": "Missing private key; set BSC_PRIVATE_KEY in .env"}
    
    from eth_account import Account
    from_addr = Web3.to_checksum_address(Account.from_key(private_key).address)
    
    # Handle token approvals for both tokens
    approval_txs = []
    erc20_abi = [
        {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
        {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
    ]
    
    # Check and approve both tokens if needed
    for token_addr, amount_needed, token_name in [(token_a, amt_a_desired, "token-a"), (token_b, amt_b_desired, "token-b")]:
        token_contract = w3.eth.contract(address=token_addr, abi=erc20_abi)
        current_allowance = token_contract.functions.allowance(from_addr, router_addr).call()
        
        if current_allowance < amount_needed:
            # Need approval for this token
            max_approval = 2**256 - 1  # Unlimited approval
            approve_tx = token_contract.functions.approve(router_addr, max_approval).build_transaction({
                "from": from_addr,
                "nonce": w3.eth.get_transaction_count(from_addr) + len(approval_txs),
                "gasPrice": w3.eth.gas_price if gas_price_gwei is None else int(gas_price_gwei * 1e9)
            })
            
            # Estimate gas
            try:
                gas = w3.eth.estimate_gas(approve_tx)
                approve_tx["gas"] = int(gas * 1.2)
            except Exception as e:
                return {"error": f"Approval gas estimation failed for {token_name}: {str(e)}"}
            
            # Sign and send approval if broadcasting
            if broadcast:
                try:
                    signed_approve = Account.sign_transaction(approve_tx, private_key)
                    raw_tx = getattr(signed_approve, 'raw_transaction', None) or getattr(signed_approve, 'rawTransaction', None)
                    approval_txhash = w3.eth.send_raw_transaction(raw_tx).hex()
                    # Wait for approval to be mined
                    receipt = w3.eth.wait_for_transaction_receipt(Web3.to_bytes(hexstr=approval_txhash), timeout=120)
                    if receipt.status != 1:
                        return {"error": f"Approval transaction failed for {token_name}. TxHash: {approval_txhash}"}
                    approval_txs.append({"token": token_name, "txHash": approval_txhash})
                except Exception as e:
                    return {"error": f"Approval transaction failed for {token_name}: {str(e)}"}
            else:
                # If not broadcasting, return the unsigned approval tx for the first token that needs it
                return {
                    "approval_needed": True,
                    "token_needing_approval": token_name,
                    "unsigned_approval_tx": {k: (hex(v) if isinstance(v, int) else v) for k, v in approve_tx.items()},
                    "message": f"Approval needed for {token_name} but broadcast=false. Approve both tokens first, then retry add-liquidity."
                }
    
    # Now add liquidity
    router = get_router(w3, router_addr)
    tx = router.functions.addLiquidity(token_a, token_b, amt_a_desired, amt_b_desired, amt_a_min, amt_b_min, to, deadline).build_transaction(_base_tx(w3, from_addr, gas_price_gwei))
    try:
        gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas * 1.25)
    except Exception:
        tx["gas"] = 600000
    
    result = _maybe_send(w3, tx, private_key, broadcast)
    
    # Add approval info to result
    if approval_txs:
        result["approvals"] = approval_txs
        result["approval_status"] = "completed"
    
    return result


def remove_liquidity_v2(args: Dict[str, Any]) -> Dict[str, Any]:
    w3, _, router_addr, _ = get_web3(args.get("chain", "mainnet"))
    token_a = checksum(args["token_a"]) if args.get("token_a") else None
    token_b = checksum(args["token_b"]) if args.get("token_b") else None
    liquidity = int(args["liquidity"]) if args.get("liquidity") else None
    amt_a_min = int(args.get("amount_a_min", 0))
    amt_b_min = int(args.get("amount_b_min", 0))
    to = checksum(args["to"]) if args.get("to") else None
    # Always use fresh deadline (30 minutes from now) - ignore any provided deadline to prevent expiration issues
    deadline = int(w3.eth.get_block("latest").timestamp) + 1800
    gas_price_gwei = args.get("gas_price_gwei")
    if gas_price_gwei is not None:
        gas_price_gwei = float(gas_price_gwei)
    private_key = args.get("private_key") or os.getenv("BSC_PRIVATE_KEY")
    if "broadcast" in args:
        broadcast = bool(args.get("broadcast"))
    else:
        broadcast = bool(private_key)
    if not token_a or not token_b or liquidity is None or not to:
        return {"error": "Missing required: token-a, token-b, liquidity, to"}
    if not private_key:
        return {"error": "Missing private key; set BSC_PRIVATE_KEY in .env"}
    from eth_account import Account
    from_addr = Web3.to_checksum_address(Account.from_key(private_key).address)
    router = get_router(w3, router_addr)
    tx = router.functions.removeLiquidity(token_a, token_b, liquidity, amt_a_min, amt_b_min, to, deadline).build_transaction(_base_tx(w3, from_addr, gas_price_gwei))
    try:
        gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas * 1.2)
    except Exception:
        tx["gas"] = 500000
    return _maybe_send(w3, tx, private_key, broadcast)


def main():
    parser = argparse.ArgumentParser(
        description="PancakeSwap V2 tools for BSC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  get-pair-info               Get pair address and reserves for token pair
  quote-out                   Quote output amounts for swap path and amount-in
  quote-in                    Quote input amounts for swap path and amount-out
  swap-auto                   Smart swap with automatic approval handling and slippage calculation
  swap-exact-tokens           Build/submit swapExactTokensForTokens tx
  add-liquidity-v2            Build/submit addLiquidity tx
  remove-liquidity-v2         Build/submit removeLiquidity tx

Examples:
  python cli.py get-pair-info --token-a 0x... --token-b 0x...
  python cli.py quote-out --amount-in 1000000000000000000 --token-in 0x... --token-out 0x...
  python cli.py swap-auto --amount-in 1e18 --path "[\"0x..\",\"0x..\"]" --to 0x... --slippage 5 --broadcast
  python cli.py swap-exact-tokens --amount-in 1e18 --path "[\"0x..\",\"0x..\"]" --to 0x... --broadcast --private-key $BSC_PRIVATE_KEY
        """
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    def add_common_chain(p):
        p.add_argument("--chain", choices=["mainnet", "testnet"], default="mainnet")

    # get-pair-info
    p_pair = sub.add_parser("get-pair-info", help="Get pair address and reserves")
    p_pair.add_argument("--token-a", required=True)
    p_pair.add_argument("--token-b", required=True)
    add_common_chain(p_pair)

    # quote-out
    p_qo = sub.add_parser("quote-out", help="Quote output amount")
    p_qo.add_argument("--amount-in", required=True)
    p_qo.add_argument("--path")
    p_qo.add_argument("--token-in")
    p_qo.add_argument("--token-out")
    add_common_chain(p_qo)

    # quote-in
    p_qi = sub.add_parser("quote-in", help="Quote input amount")
    p_qi.add_argument("--amount-out", required=True)
    p_qi.add_argument("--path")
    p_qi.add_argument("--token-in")
    p_qi.add_argument("--token-out")
    add_common_chain(p_qi)

    # swap-auto (smart swap with auto-approval)
    p_auto = sub.add_parser("swap-auto", help="Smart swap with auto approval and slippage")
    p_auto.add_argument("--amount-in", required=True)
    p_auto.add_argument("--amount-out-min", default="0")
    p_auto.add_argument("--path", required=True, help="JSON array of addresses")
    p_auto.add_argument("--to", required=True)
    p_auto.add_argument("--slippage", default="5.0", help="Slippage percentage (default: 5%)")
    p_auto.add_argument("--broadcast", action="store_true")
    p_auto.add_argument("--gas-price-gwei", type=float)
    add_common_chain(p_auto)

    # swap-exact-tokens
    p_swap = sub.add_parser("swap-exact-tokens", help="Swap exact tokens for tokens")
    p_swap.add_argument("--amount-in", required=True)
    p_swap.add_argument("--amount-out-min", default="0")
    p_swap.add_argument("--path", required=True, help="JSON array of addresses")
    p_swap.add_argument("--to", required=True)
    p_swap.add_argument("--deadline")
    p_swap.add_argument("--broadcast", action="store_true")
    p_swap.add_argument("--private-key")
    p_swap.add_argument("--gas-price-gwei", type=float)
    add_common_chain(p_swap)

    # add-liquidity-v2
    p_add = sub.add_parser("add-liquidity-v2", help="Add V2 liquidity")
    p_add.add_argument("--token-a", required=True)
    p_add.add_argument("--token-b", required=True)
    p_add.add_argument("--amount-a-desired", required=True)
    p_add.add_argument("--amount-b-desired", required=True)
    p_add.add_argument("--amount-a-min", default="0")
    p_add.add_argument("--amount-b-min", default="0")
    p_add.add_argument("--to", required=True)
    p_add.add_argument("--deadline")
    p_add.add_argument("--broadcast", action="store_true")
    p_add.add_argument("--private-key")
    p_add.add_argument("--gas-price-gwei", type=float)
    add_common_chain(p_add)

    # remove-liquidity-v2
    p_rem = sub.add_parser("remove-liquidity-v2", help="Remove V2 liquidity")
    p_rem.add_argument("--token-a", required=True)
    p_rem.add_argument("--token-b", required=True)
    p_rem.add_argument("--liquidity", required=True)
    p_rem.add_argument("--amount-a-min", default="0")
    p_rem.add_argument("--amount-b-min", default="0")
    p_rem.add_argument("--to", required=True)
    p_rem.add_argument("--deadline")
    p_rem.add_argument("--broadcast", action="store_true")
    p_rem.add_argument("--private-key")
    p_rem.add_argument("--gas-price-gwei", type=float)
    add_common_chain(p_rem)

    args_ns = parser.parse_args()
    if not getattr(args_ns, "command", None):
        parser.print_help()
        sys.exit(1)

    args = vars(args_ns)
    try:
        if args_ns.command == "get-pair-info":
            out = get_pair_info(args)
        elif args_ns.command == "quote-out":
            out = quote_out(args)
        elif args_ns.command == "quote-in":
            out = quote_in(args)
        elif args_ns.command == "swap-auto":
            out = swap_auto(args)
        elif args_ns.command == "swap-exact-tokens":
            out = swap_exact_tokens_for_tokens(args)
        elif args_ns.command == "add-liquidity-v2":
            out = add_liquidity_v2(args)
        elif args_ns.command == "remove-liquidity-v2":
            out = remove_liquidity_v2(args)
        else:
            out = {"error": f"Unknown command: {args_ns.command}"}
        print(json.dumps(out))
        sys.exit(0 if "error" not in out else 1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()


