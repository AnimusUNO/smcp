#!/usr/bin/env python3
"""
BSC CLI Plugin

Wallet and ERC-20 utilities for Binance Smart Chain. Provides read operations
and transaction builders with optional broadcast for safe agent automation.

Environment variables:
  - BSC_RPC_URL: HTTP RPC endpoint (defaults to public BSC endpoints)
  - BSC_RPC_URL_TESTNET: HTTP RPC for testnet
  - BSC_PRIVATE_KEY: hex private key for signing transactions

Copyright (c) 2025 Animus
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.types import TxParams
from eth_account import Account


ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]


MAINNET_DEFAULT_RPC = "https://bsc-dataseed.bnbchain.org"
TESTNET_DEFAULT_RPC = "https://data-seed-prebsc-1-s1.binance.org:8545"


def get_web3(chain: str) -> Web3:
    if chain == "testnet":
        rpc = os.getenv("BSC_RPC_URL_TESTNET", TESTNET_DEFAULT_RPC)
        w3 = Web3(Web3.HTTPProvider(rpc))
        # Inject PoA middleware for BSC (Proof of Authority chain)
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        return w3
    rpc = os.getenv("BSC_RPC_URL", MAINNET_DEFAULT_RPC)
    w3 = Web3(Web3.HTTPProvider(rpc))
    # Inject PoA middleware for BSC (Proof of Authority chain)
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def checksum(address: str) -> str:
    return Web3.to_checksum_address(address)


def build_base_tx(w3: Web3, from_addr: str, gas_price_gwei: Optional[float]) -> TxParams:
    gas_price = w3.eth.gas_price if gas_price_gwei is None else int(gas_price_gwei * 1e9)
    return {
        "from": from_addr,
        "nonce": w3.eth.get_transaction_count(from_addr),
        "gasPrice": gas_price,
    }


def maybe_send(w3: Web3, tx: TxParams, private_key: Optional[str], broadcast: bool) -> Dict[str, Any]:
    if not broadcast:
        return {"unsignedTx": {k: (hex(v) if isinstance(v, int) else v) for k, v in tx.items()}}
    if not private_key:
        return {"error": "Missing private key; set --private-key or BSC_PRIVATE_KEY"}
    try:
        signed = w3.eth.account.sign_transaction(tx, private_key)
        # Use raw_transaction (underscore) for newer web3.py versions
        raw_tx = getattr(signed, 'raw_transaction', None) or getattr(signed, 'rawTransaction', None)
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        return {"txHash": tx_hash.hex()}
    except Exception as e:
        return {"error": str(e)}


def get_balance(args: Dict[str, Any]) -> Dict[str, Any]:
    w3 = get_web3(args.get("chain", "mainnet"))
    address = checksum(args["address"]) if args.get("address") else None
    if not address:
        return {"error": "Missing required argument: address"}
    wei = w3.eth.get_balance(address)
    return {"address": address, "balanceWei": str(wei), "balanceEth": float(wei) / 1e18}


def get_token_balance(args: Dict[str, Any]) -> Dict[str, Any]:
    w3 = get_web3(args.get("chain", "mainnet"))
    address = checksum(args["address"]) if args.get("address") else None
    token = checksum(args["token"]) if args.get("token") else None
    if not address or not token:
        return {"error": "Missing required arguments: address, token"}
    erc20 = w3.eth.contract(address=token, abi=ERC20_ABI)
    bal = erc20.functions.balanceOf(address).call()
    decimals = erc20.functions.decimals().call()
    symbol = erc20.functions.symbol().call()
    return {"address": address, "token": token, "symbol": symbol, "decimals": decimals, "balanceRaw": str(bal), "balance": float(bal) / (10 ** decimals)}


def allowance(args: Dict[str, Any]) -> Dict[str, Any]:
    w3 = get_web3(args.get("chain", "mainnet"))
    token = checksum(args["token"]) if args.get("token") else None
    owner = checksum(args["owner"]) if args.get("owner") else None
    spender = checksum(args["spender"]) if args.get("spender") else None
    if not token or not owner or not spender:
        return {"error": "Missing required arguments: token, owner, spender"}
    erc20 = w3.eth.contract(address=token, abi=ERC20_ABI)
    val = erc20.functions.allowance(owner, spender).call()
    return {"token": token, "owner": owner, "spender": spender, "allowance": str(val)}


def approve(args: Dict[str, Any]) -> Dict[str, Any]:
    w3 = get_web3(args.get("chain", "mainnet"))
    token = checksum(args["token"]) if args.get("token") else None
    spender = checksum(args["spender"]) if args.get("spender") else None
    amount = int(args["amount"]) if args.get("amount") is not None else None
    from_addr = checksum(args["from"]) if args.get("from") else None
    # Argparse converts hyphens to underscores
    gas_price_gwei = args.get("gas_price_gwei")
    if gas_price_gwei is not None:
        gas_price_gwei = float(gas_price_gwei)
    private_key = args.get("private_key") or os.getenv("BSC_PRIVATE_KEY")
    # Default to broadcast if a private key is available and broadcast not explicitly set
    if "broadcast" in args:
        broadcast = bool(args.get("broadcast"))
    else:
        broadcast = bool(private_key)
    if not token or not spender or amount is None:
        return {"error": "Missing required arguments: token, spender, amount"}
    if not from_addr and not private_key:
        return {"error": "Provide sender address via from parameter or BSC_PRIVATE_KEY env"}
    if not from_addr and private_key:
        from_addr = Web3.to_checksum_address(Account.from_key(private_key).address)
    erc20 = w3.eth.contract(address=token, abi=ERC20_ABI)
    tx = erc20.functions.approve(spender, amount).build_transaction(build_base_tx(w3, from_addr, gas_price_gwei))
    # Estimate gas and set
    try:
        gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas * 1.2)
    except Exception:
        tx["gas"] = 150000
    return maybe_send(w3, tx, private_key, broadcast)


def send_native(args: Dict[str, Any]) -> Dict[str, Any]:
    w3 = get_web3(args.get("chain", "mainnet"))
    to = checksum(args["to"]) if args.get("to") else None
    # Argparse converts hyphens to underscores
    value_eth = float(args["amount_eth"]) if args.get("amount_eth") else None
    gas_price_gwei = args.get("gas_price_gwei")
    if gas_price_gwei is not None:
        gas_price_gwei = float(gas_price_gwei)
    private_key = args.get("private_key") or os.getenv("BSC_PRIVATE_KEY")
    if "broadcast" in args:
        broadcast = bool(args.get("broadcast"))
    else:
        broadcast = bool(private_key)
    if not to or value_eth is None:
        return {"error": "Missing required arguments: to, amount-eth"}
    if not private_key:
        return {"error": "Missing private key; set BSC_PRIVATE_KEY in .env"}
    from_addr = Web3.to_checksum_address(Account.from_key(private_key).address)
    base = build_base_tx(w3, from_addr, gas_price_gwei)
    tx: TxParams = {**base, "to": to, "value": int(value_eth * 1e18)}
    try:
        gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas * 1.2)
    except Exception:
        tx["gas"] = 21000
    return maybe_send(w3, tx, private_key, broadcast)


def send_erc20(args: Dict[str, Any]) -> Dict[str, Any]:
    w3 = get_web3(args.get("chain", "mainnet"))
    token = checksum(args["token"]) if args.get("token") else None
    to = checksum(args["to"]) if args.get("to") else None
    amount = int(args["amount"]) if args.get("amount") else None
    # Argparse converts hyphens to underscores
    gas_price_gwei = args.get("gas_price_gwei")
    if gas_price_gwei is not None:
        gas_price_gwei = float(gas_price_gwei)
    private_key = args.get("private_key") or os.getenv("BSC_PRIVATE_KEY")
    if "broadcast" in args:
        broadcast = bool(args.get("broadcast"))
    else:
        broadcast = bool(private_key)
    if not token or not to or amount is None:
        return {"error": "Missing required arguments: token, to, amount"}
    if not private_key:
        return {"error": "Missing private key; set BSC_PRIVATE_KEY in .env"}
    from_addr = Web3.to_checksum_address(Account.from_key(private_key).address)
    erc20 = w3.eth.contract(address=token, abi=ERC20_ABI)
    tx = erc20.functions.transfer(to, amount).build_transaction(build_base_tx(w3, from_addr, gas_price_gwei))
    try:
        gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas * 1.2)
    except Exception:
        tx["gas"] = 100000
    return maybe_send(w3, tx, private_key, broadcast)


def gas_price(args: Dict[str, Any]) -> Dict[str, Any]:
    w3 = get_web3(args.get("chain", "mainnet"))
    gp = w3.eth.gas_price
    return {"gasPriceWei": str(gp), "gasPriceGwei": float(gp) / 1e9}


def nonce(args: Dict[str, Any]) -> Dict[str, Any]:
    w3 = get_web3(args.get("chain", "mainnet"))
    address = checksum(args["address"]) if args.get("address") else None
    if not address:
        return {"error": "Missing required argument: address"}
    return {"address": address, "nonce": w3.eth.get_transaction_count(address)}


def create_wallet(_: Dict[str, Any]) -> Dict[str, Any]:
    acct = Account.create()
    return {"address": acct.address, "privateKey": acct.key.hex()}


def wrap_bnb(args: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap native BNB to WBNB."""
    w3 = get_web3(args.get("chain", "mainnet"))
    amount = args.get("amount")
    
    if not amount:
        return {"error": "Missing required argument: amount"}
    
    amount_wei = int(amount)
    
    # WBNB contract address
    if args.get("chain") == "testnet":
        wbnb_address = "0xae13d989dac2f0debff460ac112a837c89baa7cd"
    else:
        wbnb_address = "0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
    
    wbnb_address = checksum(wbnb_address)
    
    # WBNB deposit ABI
    wbnb_abi = [
        {"constant": False, "inputs": [], "name": "deposit", "outputs": [], "payable": True, "type": "function"}
    ]
    
    private_key = args.get("private_key") or os.getenv("BSC_PRIVATE_KEY")
    gas_price_gwei = args.get("gas_price_gwei")
    if gas_price_gwei is not None:
        gas_price_gwei = float(gas_price_gwei)
    
    if "broadcast" in args:
        broadcast = bool(args.get("broadcast"))
    else:
        broadcast = bool(private_key)
    
    if not private_key:
        return {"error": "Missing private key; set BSC_PRIVATE_KEY in .env"}
    
    from_addr = checksum(Account.from_key(private_key).address)
    
    # Build wrap transaction (deposit with BNB value)
    wbnb_contract = w3.eth.contract(address=wbnb_address, abi=wbnb_abi)
    base_tx = build_base_tx(w3, from_addr, gas_price_gwei)
    base_tx["value"] = amount_wei  # Send BNB with the transaction
    
    tx = wbnb_contract.functions.deposit().build_transaction(base_tx)
    
    # Estimate gas
    try:
        gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas * 1.2)
    except Exception:
        tx["gas"] = 60000
    
    return maybe_send(w3, tx, private_key, broadcast)


def unwrap_bnb(args: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap WBNB to native BNB."""
    w3 = get_web3(args.get("chain", "mainnet"))
    amount = args.get("amount")
    
    if not amount:
        return {"error": "Missing required argument: amount"}
    
    amount_wei = int(amount)
    
    # WBNB contract address
    if args.get("chain") == "testnet":
        wbnb_address = "0xae13d989dac2f0debff460ac112a837c89baa7cd"
    else:
        wbnb_address = "0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
    
    wbnb_address = checksum(wbnb_address)
    
    # WBNB withdraw ABI
    wbnb_abi = [
        {"constant": False, "inputs": [{"name": "wad", "type": "uint256"}], "name": "withdraw", "outputs": [], "type": "function"}
    ]
    
    private_key = args.get("private_key") or os.getenv("BSC_PRIVATE_KEY")
    gas_price_gwei = args.get("gas_price_gwei")
    if gas_price_gwei is not None:
        gas_price_gwei = float(gas_price_gwei)
    
    if "broadcast" in args:
        broadcast = bool(args.get("broadcast"))
    else:
        broadcast = bool(private_key)
    
    if not private_key:
        return {"error": "Missing private key; set BSC_PRIVATE_KEY in .env"}
    
    from_addr = checksum(Account.from_key(private_key).address)
    
    # Build unwrap transaction
    wbnb_contract = w3.eth.contract(address=wbnb_address, abi=wbnb_abi)
    tx = wbnb_contract.functions.withdraw(amount_wei).build_transaction(
        build_base_tx(w3, from_addr, gas_price_gwei)
    )
    
    # Estimate gas
    try:
        gas = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas * 1.2)
    except Exception:
        tx["gas"] = 50000
    
    return maybe_send(w3, tx, private_key, broadcast)


def main():
    parser = argparse.ArgumentParser(
        description="BSC wallet and ERC-20 utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  get-balance           Get native BNB balance for an address
  get-token-balance     Get ERC-20 balance for an address
  allowance             Get ERC-20 allowance for owner/spender
  approve               Approve ERC-20 spender for amount
  send-native           Send BNB to an address
  send-erc20            Send ERC-20 tokens to an address
  wrap-bnb              Wrap native BNB to WBNB
  unwrap-bnb            Unwrap WBNB to native BNB
  gas-price             Get current gas price
  nonce                 Get transaction count (nonce) for address

Examples:
  python cli.py get-balance --address 0x... --chain mainnet
  python cli.py get-token-balance --address 0x... --token 0x...
  python cli.py approve --token 0x... --spender 0x... --amount 1000000000000000000 --from 0x...
  python cli.py unwrap-bnb --amount 1000000000000000000 --broadcast
  python cli.py send-native --to 0x... --amount-eth 0.01 --broadcast --private-key $BSC_PRIVATE_KEY
        """
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    def add_common_chain(p):
        p.add_argument("--chain", choices=["mainnet", "testnet"], default="mainnet")

    # get-balance
    p_bal = sub.add_parser("get-balance", help="Get native BNB balance")
    p_bal.add_argument("--address", required=True)
    add_common_chain(p_bal)

    # get-token-balance
    p_tbal = sub.add_parser("get-token-balance", help="Get ERC-20 token balance")
    p_tbal.add_argument("--address", required=True)
    p_tbal.add_argument("--token", required=True)
    add_common_chain(p_tbal)

    # allowance
    p_allow = sub.add_parser("allowance", help="Get ERC-20 allowance")
    p_allow.add_argument("--token", required=True)
    p_allow.add_argument("--owner", required=True)
    p_allow.add_argument("--spender", required=True)
    add_common_chain(p_allow)

    # approve
    p_app = sub.add_parser("approve", help="Approve ERC-20 spender")
    p_app.add_argument("--token", required=True)
    p_app.add_argument("--spender", required=True)
    p_app.add_argument("--amount", required=True)
    p_app.add_argument("--from")
    p_app.add_argument("--private-key")
    p_app.add_argument("--broadcast", action="store_true")
    p_app.add_argument("--gas-price-gwei", type=float)
    add_common_chain(p_app)

    # send-native
    p_sn = sub.add_parser("send-native", help="Send BNB")
    p_sn.add_argument("--to", required=True)
    p_sn.add_argument("--amount-eth", required=True)
    p_sn.add_argument("--private-key")
    p_sn.add_argument("--broadcast", action="store_true")
    p_sn.add_argument("--gas-price-gwei", type=float)
    add_common_chain(p_sn)

    # send-erc20
    p_se = sub.add_parser("send-erc20", help="Send ERC-20 token")
    p_se.add_argument("--token", required=True)
    p_se.add_argument("--to", required=True)
    p_se.add_argument("--amount", required=True)
    p_se.add_argument("--private-key")
    p_se.add_argument("--broadcast", action="store_true")
    p_se.add_argument("--gas-price-gwei", type=float)
    add_common_chain(p_se)

    # gas-price
    p_gp = sub.add_parser("gas-price", help="Get gas price")
    add_common_chain(p_gp)

    # wrap-bnb
    p_wrap = sub.add_parser("wrap-bnb", help="Wrap native BNB to WBNB")
    p_wrap.add_argument("--amount", required=True, help="Amount of BNB to wrap (in wei)")
    p_wrap.add_argument("--broadcast", action="store_true")
    p_wrap.add_argument("--gas-price-gwei", type=float)
    add_common_chain(p_wrap)

    # unwrap-bnb
    p_unwrap = sub.add_parser("unwrap-bnb", help="Unwrap WBNB to native BNB")
    p_unwrap.add_argument("--amount", required=True, help="Amount of WBNB to unwrap (in wei)")
    p_unwrap.add_argument("--broadcast", action="store_true")
    p_unwrap.add_argument("--gas-price-gwei", type=float)
    add_common_chain(p_unwrap)

    # nonce
    p_nc = sub.add_parser("nonce", help="Get address nonce")
    p_nc.add_argument("--address", required=True)
    add_common_chain(p_nc)

    # create-wallet (returns address and private key)
    sub.add_parser("create-wallet", help="Create a new wallet and return private key")

    args_ns = parser.parse_args()

    if not getattr(args_ns, "command", None):
        parser.print_help()
        sys.exit(1)

    args = vars(args_ns)
    try:
        if args_ns.command == "get-balance":
            out = get_balance(args)
        elif args_ns.command == "get-token-balance":
            out = get_token_balance(args)
        elif args_ns.command == "allowance":
            out = allowance(args)
        elif args_ns.command == "approve":
            out = approve(args)
        elif args_ns.command == "send-native":
            out = send_native(args)
        elif args_ns.command == "send-erc20":
            out = send_erc20(args)
        elif args_ns.command == "gas-price":
            out = gas_price(args)
        elif args_ns.command == "wrap-bnb":
            out = wrap_bnb(args)
        elif args_ns.command == "unwrap-bnb":
            out = unwrap_bnb(args)
        elif args_ns.command == "nonce":
            out = nonce(args)
        elif args_ns.command == "create-wallet":
            out = create_wallet(args)
        else:
            out = {"error": f"Unknown command: {args_ns.command}"}
        print(json.dumps(out))
        sys.exit(0 if "error" not in out else 1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()


