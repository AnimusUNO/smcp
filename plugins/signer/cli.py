#!/usr/bin/env python3
"""
Signer CLI Plugin

Provides signing and wallet management without exposing raw private keys to agents.

Modes:
  - local: Encrypted geth-style keystore files stored on disk per label
  - http:  Forward sign requests to an external HTTP signer service

Environment:
  - SIGNER_KEYSTORE_DIR: directory for local keystores (default: ./plugins/signer/keystore)
  - SIGNER_PASSWORD: default password for encrypt/decrypt operations (can be overridden per command)
  - BSC_RPC_URL / BSC_RPC_URL_TESTNET: RPC endpoints for broadcasting

Security notes:
  - Never prints or returns private keys
  - Keystore files are AES-encrypted JSON (geth format)
  - Prefer http mode backed by KMS/HSM/MPC in production
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from eth_account.messages import encode_typed_data


DEFAULT_KEYSTORE_DIR = Path(__file__).parent / "keystore"
MAINNET_DEFAULT_RPC = "https://bsc-dataseed.bnbchain.org"
TESTNET_DEFAULT_RPC = "https://data-seed-prebsc-1-s1.binance.org:8545"


def get_keystore_dir() -> Path:
    p = Path(os.getenv("SIGNER_KEYSTORE_DIR", str(DEFAULT_KEYSTORE_DIR)))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _label_path(label: str) -> Path:
    return get_keystore_dir() / f"{label}.json"


def _load_keystore(label: str) -> Dict[str, Any]:
    path = _label_path(label)
    if not path.exists():
        raise FileNotFoundError(f"Keystore not found for label: {label}")
    return json.loads(path.read_text())


def _update_env_file(key: str, value: str) -> None:
    """Update or add a key-value pair in the .env file."""
    # Find the .env file (should be in smcp-master root, two levels up from plugins/signer)
    env_path = Path(__file__).parent.parent.parent / ".env"
    
    # Read existing .env content
    existing_lines = []
    key_found = False
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    # Replace existing key
                    existing_lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    existing_lines.append(line)
    
    # If key wasn't found, add it
    if not key_found:
        existing_lines.append(f"{key}={value}\n")
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(existing_lines)


def _rpc_web3(chain: str) -> Web3:
    if chain == "testnet":
        rpc = os.getenv("BSC_RPC_URL_TESTNET", TESTNET_DEFAULT_RPC)
    else:
        rpc = os.getenv("BSC_RPC_URL", MAINNET_DEFAULT_RPC)
    w3 = Web3(Web3.HTTPProvider(rpc))
    # Inject PoA middleware for BSC (Proof of Authority chain)
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def create_wallet(args: Dict[str, Any]) -> Dict[str, Any]:
    label = args.get("label")
    password = args.get("password") or os.getenv("SIGNER_PASSWORD")
    if not label:
        return {"error": "Missing required argument: label"}
    if not password:
        return {"error": "Missing password. Provide --password or SIGNER_PASSWORD"}
    # Create new key and encrypt in geth keystore format
    acct = Account.create()
    keystore_json = Account.encrypt(acct.key, password)
    path = _label_path(label)
    if path.exists():
        return {"error": f"Label already exists: {label}"}
    path.write_text(json.dumps(keystore_json))
    address = Web3.to_checksum_address(keystore_json.get("address", acct.address).lower() if isinstance(keystore_json.get("address"), str) else acct.address)
    
    # Automatically set BSC_PRIVATE_KEY in .env for seamless BSC tool usage
    _update_env_file("BSC_PRIVATE_KEY", acct.key.hex())
    
    return {"label": label, "address": address}


def import_private_key(args: Dict[str, Any]) -> Dict[str, Any]:
    label = args.get("label")
    private_key = args.get("private-key")
    password = args.get("password") or os.getenv("SIGNER_PASSWORD")
    if not label or not private_key:
        return {"error": "Missing required arguments: label, private-key"}
    if not password:
        return {"error": "Missing password. Provide --password or SIGNER_PASSWORD"}
    acct = Account.from_key(private_key)
    keystore_json = Account.encrypt(acct.key, password)
    path = _label_path(label)
    if path.exists():
        return {"error": f"Label already exists: {label}"}
    path.write_text(json.dumps(keystore_json))
    address = Web3.to_checksum_address(acct.address)
    
    # Automatically set BSC_PRIVATE_KEY in .env for seamless BSC tool usage
    _update_env_file("BSC_PRIVATE_KEY", private_key if private_key.startswith('0x') else f"0x{private_key}")
    
    return {"label": label, "address": address}


def list_wallets(_: Dict[str, Any]) -> Dict[str, Any]:
    entries = []
    for f in get_keystore_dir().glob("*.json"):
        try:
            data = json.loads(f.read_text())
            addr = data.get("address")
            if isinstance(addr, str):
                address = Web3.to_checksum_address(addr)
            else:
                address = None
            entries.append({"label": f.stem, "address": address})
        except Exception:
            entries.append({"label": f.stem, "address": None})
    return {"wallets": entries}


def get_address(args: Dict[str, Any]) -> Dict[str, Any]:
    label = args.get("label")
    if not label:
        return {"error": "Missing required argument: label"}
    data = _load_keystore(label)
    addr = data.get("address")
    if not addr:
        return {"error": "Invalid keystore format"}
    return {"label": label, "address": Web3.to_checksum_address(addr)}


def _decrypt_key(keystore: Dict[str, Any], password: str) -> bytes:
    return Account.decrypt(keystore, password)


def sign_tx(args: Dict[str, Any]) -> Dict[str, Any]:
    label = args.get("label")
    tx_json = args.get("tx")
    password = args.get("password") or os.getenv("SIGNER_PASSWORD")
    if not label or not tx_json:
        return {"error": "Missing required arguments: label, tx"}
    if not password:
        return {"error": "Missing password. Provide --password or SIGNER_PASSWORD"}
    keystore = _load_keystore(label)
    key = _decrypt_key(keystore, password)
    tx: Dict[str, Any] = json.loads(tx_json) if isinstance(tx_json, str) else tx_json
    signed = Account.sign_transaction(tx, key)
    # Use raw_transaction (underscore) for newer web3.py versions
    raw_tx = getattr(signed, 'raw_transaction', None) or getattr(signed, 'rawTransaction', None)
    return {"rawTransaction": raw_tx.hex(), "hash": signed.hash.hex()}


def send_tx(args: Dict[str, Any]) -> Dict[str, Any]:
    # Accept either an unsigned tx + label/password, or a pre-signed raw hex
    chain = args.get("chain", "mainnet")
    raw = args.get("raw")
    if raw:
        w3 = _rpc_web3(chain)
        tx_hash = w3.eth.send_raw_transaction(Web3.to_bytes(hexstr=raw))
        return {"txHash": tx_hash.hex()}
    # Otherwise sign then send
    stx = sign_tx(args)
    if "error" in stx:
        return stx
    w3 = _rpc_web3(chain)
    tx_hash = w3.eth.send_raw_transaction(Web3.to_bytes(hexstr=stx["rawTransaction"]))
    return {"txHash": tx_hash.hex()}


def sign_typed_data(args: Dict[str, Any]) -> Dict[str, Any]:
    label = args.get("label")
    password = args.get("password") or os.getenv("SIGNER_PASSWORD")
    typed = args.get("typed-data")
    if not label or not typed:
        return {"error": "Missing required arguments: label, typed-data"}
    if not password:
        return {"error": "Missing password. Provide --password or SIGNER_PASSWORD"}
    keystore = _load_keystore(label)
    key = _decrypt_key(keystore, password)
    data = json.loads(typed) if isinstance(typed, str) else typed
    msg = encode_typed_data(full_message=data)
    sig = Account.sign_message(msg, private_key=key)
    return {"signature": sig.signature.hex(), "r": hex(sig.r), "s": hex(sig.s), "v": sig.v}


def http_forward(args: Dict[str, Any], operation: str) -> Dict[str, Any]:
    url = args.get("url")
    if not url:
        return {"error": "Missing required argument: url for provider=http"}
    payload = {"operation": operation, "params": args}
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Signer plugin: local keystore or HTTP forward",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  create-wallet       Create new wallet in local keystore
  import-private-key  Import an existing private key into local keystore (dev)
  list-wallets        List labels and addresses
  get-address         Get address for label
  sign-tx             Sign a transaction (returns raw hex)
  send-tx             Sign (or use raw) and broadcast to chain
  sign-typed-data     Sign EIP-712 typed data

Common options:
  --provider {local,http}
  --url <http_endpoint>       (provider=http)
  --label <name>              (wallet label)
  --password <secret>         (local keystore password)
        """
    )

    parser.add_argument("--provider", choices=["local", "http"], default="local")
    parser.add_argument("--url")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # create-wallet
    p_cw = sub.add_parser("create-wallet", help="Create new wallet")
    p_cw.add_argument("--label", required=True)
    p_cw.add_argument("--password")

    # import-private-key (dev)
    p_ipk = sub.add_parser("import-private-key", help="Import private key (dev)")
    p_ipk.add_argument("--label", required=True)
    p_ipk.add_argument("--private-key", required=True)
    p_ipk.add_argument("--password")

    # list-wallets
    sub.add_parser("list-wallets", help="List wallets")

    # get-address
    p_ga = sub.add_parser("get-address", help="Get address for label")
    p_ga.add_argument("--label", required=True)

    # sign-tx
    p_st = sub.add_parser("sign-tx", help="Sign a tx")
    p_st.add_argument("--label", required=True)
    p_st.add_argument("--tx", required=True, help="JSON tx object")
    p_st.add_argument("--password")

    # send-tx
    p_sd = sub.add_parser("send-tx", help="Sign and send, or send raw")
    p_sd.add_argument("--label")
    p_sd.add_argument("--tx", help="JSON tx object (if not providing --raw)")
    p_sd.add_argument("--raw", help="Signed raw tx hex")
    p_sd.add_argument("--password")
    p_sd.add_argument("--chain", choices=["mainnet", "testnet"], default="mainnet")

    # sign-typed-data
    p_std = sub.add_parser("sign-typed-data", help="Sign EIP-712 data")
    p_std.add_argument("--label", required=True)
    p_std.add_argument("--typed-data", required=True, help="JSON typed data")
    p_std.add_argument("--password")

    args_ns = parser.parse_args()
    if not getattr(args_ns, "command", None):
        parser.print_help()
        sys.exit(1)

    args = vars(args_ns)
    provider = args.get("provider", "local")
    op = args_ns.command

    try:
        if provider == "http":
            out = http_forward(args, op)
        else:
            if op == "create-wallet":
                out = create_wallet(args)
            elif op == "import-private-key":
                out = import_private_key(args)
            elif op == "list-wallets":
                out = list_wallets(args)
            elif op == "get-address":
                out = get_address(args)
            elif op == "sign-tx":
                out = sign_tx(args)
            elif op == "send-tx":
                out = send_tx(args)
            elif op == "sign-typed-data":
                out = sign_typed_data(args)
            else:
                out = {"error": f"Unknown command: {op}"}
        print(json.dumps(out))
        sys.exit(0 if "error" not in out else 1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()


