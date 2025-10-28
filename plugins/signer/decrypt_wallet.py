#!/usr/bin/env python3
"""
Decrypt a wallet keystore to retrieve the private key.
Usage: python decrypt_wallet.py <wallet_label>
"""
import json
import sys
import os
from pathlib import Path
from eth_account import Account
from web3 import Web3
from dotenv import load_dotenv

# Load .env file from the smcp-master root directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

def decrypt_wallet(label: str, password: str = None):
    """Decrypt a wallet keystore and return the private key."""
    # Get password from env if not provided
    if not password:
        password = os.getenv("SIGNER_PASSWORD")
        if not password:
            print("Error: No password provided and SIGNER_PASSWORD env var not set")
            return None
    
    # Find keystore file
    keystore_dir = Path(__file__).parent / "keystore"
    keystore_path = keystore_dir / f"{label}.json"
    
    if not keystore_path.exists():
        print(f"Error: Keystore not found for label '{label}'")
        print(f"Looking in: {keystore_path}")
        return None
    
    # Load and decrypt keystore
    try:
        with open(keystore_path, 'r') as f:
            keystore_json = json.load(f)
        
        # Decrypt the keystore
        private_key_bytes = Account.decrypt(keystore_json, password)
        private_key_hex = private_key_bytes.hex()
        
        # Get the address
        account = Account.from_key(private_key_bytes)
        address = Web3.to_checksum_address(account.address)
        
        print(f"\n{'='*60}")
        print(f"Wallet: {label}")
        print(f"Address: {address}")
        print(f"Private Key: 0x{private_key_hex}")
        print(f"{'='*60}\n")
        print("⚠️  WARNING: Keep this private key secure! Never share it.")
        
        return f"0x{private_key_hex}"
        
    except Exception as e:
        print(f"Error decrypting wallet: {e}")
        print("Check that your password is correct (SIGNER_PASSWORD in .env)")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python decrypt_wallet.py <wallet_label>")
        print("\nAvailable wallets:")
        keystore_dir = Path(__file__).parent / "keystore"
        for f in keystore_dir.glob("*.json"):
            print(f"  - {f.stem}")
        sys.exit(1)
    
    label = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    decrypt_wallet(label, password)

