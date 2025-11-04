# Animus MCP Plugins: Binance Smart Chain (BSC) + PancakeSwap

This document explains the BSC and PancakeSwap MCP tools added to this codebase, how agents use them autonomously with on-agent keys, configuration, and example flows.

## Overview

- **Purpose**: Give Animus agents first-class, autonomous access to BSC and PancakeSwap V2 actions.
- **Components**:
  - `bsc` plugin: Wallet utilities, ERC-20 operations, send, approvals, gas/nonce.
  - `pancakeswap` plugin: Quotes, swaps, V2 add/remove liquidity.
  - `signer` plugin (optional): Local encrypted keystore + HTTP forwarder for external signers.
- **Discovery**: Plugins are auto-discovered by the MCP server from `plugins/*/cli.py`.

## What agents can do

- **Signer (wallets and signatures)**: `signer.*` (optional)
  - `signer.create-wallet`, `signer.import-private-key`, `signer.list-wallets`, `signer.get-address`, `signer.sign-tx`, `signer.send-tx`, `signer.sign-typed-data`.
- **BSC utilities**: `bsc.*`
  - `bsc.create-wallet` (on-agent key generation)
  - `bsc.get-balance`, `bsc.get-token-balance`, `bsc.allowance`, `bsc.approve`, `bsc.send-native`, `bsc.send-erc20`, `bsc.gas-price`, `bsc.nonce`.
- **PancakeSwap V2**: `pancakeswap.*`
  - `pancakeswap.get-pair-info`, `pancakeswap.quote-out`, `pancakeswap.quote-in`, `pancakeswap.swap-exact-tokens`, `pancakeswap.add-liquidity-v2`, `pancakeswap.remove-liquidity-v2`.

## Addresses and networks

- **Mainnet**
  - Factory V2: `0xCA143Ce32Fe78f1f7019d7d551a6402fC5350c73`
  - Router V2: `0x10ED43C718714eb63d5aA57B78B54704E256024E`
  - WBNB:      `0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c`
- **Testnet (BSC Testnet)**
  - Factory V2: `0x6725F303b657a9451d8BA641348b6761A6CC7a17`
  - Router V2:  `0xD99D1c33F9fC3444f8101754aBC46c52416550D1`
  - WBNB:       `0xae13d989dac2f0debff460ac112a83789baa7cd`

## Installation & run

- **Prereqs**: Python 3.8+, pip
- **Windows quickstart**:
```powershell
py -3 -m venv venv
.\venv\Scripts\activate
pip install -r smcp-master\requirements.txt
python smcp-master\smcp.py --host 127.0.0.1 --port 8000
```
- **Linux/macOS quickstart**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r smcp-master/requirements.txt
python smcp-master/smcp.py --host 127.0.0.1 --port 8000
```

## Configuration

- **RPC endpoints**
  - `BSC_RPC_URL`: mainnet RPC (default `https://bsc-dataseed.binance.org`)
  - `BSC_RPC_URL_TESTNET`: testnet RPC (default `https://data-seed-prebsc-1-s1.binance.org:8545`)
- **Keys for autonomous operation**
  - Agents can pass `--private-key` in args, or set `BSC_PRIVATE_KEY` on the server process.
  - Tools auto-broadcast when a private key is present unless `broadcast:false` is provided.
- **Optional signer plugin**
  - `SIGNER_KEYSTORE_DIR`, `SIGNER_PASSWORD` for local encrypted keystore; or `--provider http --url <endpoint>` to forward to an external signer.

## Autonomous (keyed) agent flow

1) Create a wallet (on-agent key generation)
   - tool: `bsc.create-wallet`
   - result: `{ "address": "0x...", "privateKey": "0x..." }`
   - Store `privateKey` in the agent’s secure memory/kv store.
2) Fund the address with BNB and any required tokens.
3) Execute actions by passing the private key or using `BSC_PRIVATE_KEY` in env.

### Examples

- Approve token to Router V2 (mainnet):
```json
{
  "tool": "bsc.approve",
  "arguments": {
    "token": "0xToken",
    "spender": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
    "amount": "1000000000000000000",
    "from": "0xYourAddr",
    "private-key": "0x..."
  }
}
```

- Swap exact tokens (path [tokenIn, tokenOut])
```json
{
  "tool": "pancakeswap.swap-exact-tokens",
  "arguments": {
    "amount-in": "1000000000000000000",
    "amount-out-min": "0",
    "path": "[\"0xIn\",\"0xOut\"]",
    "to": "0xYourAddr",
    "private-key": "0x..."
  }
}
```

- Add V2 liquidity
```json
{
  "tool": "pancakeswap.add-liquidity-v2",
  "arguments": {
    "token-a": "0xTokenA",
    "token-b": "0xTokenB",
    "amount-a-desired": "1000000000000000000",
    "amount-b-desired": "250000000",
    "amount-a-min": "0",
    "amount-b-min": "0",
    "to": "0xYourAddr",
    "private-key": "0x..."
  }
}
```

- Remove V2 liquidity
```json
{
  "tool": "pancakeswap.remove-liquidity-v2",
  "arguments": {
    "token-a": "0xTokenA",
    "token-b": "0xTokenB",
    "liquidity": "1000000000000000",
    "amount-a-min": "0",
    "amount-b-min": "0",
    "to": "0xYourAddr",
    "private-key": "0x..."
  }
}
```

- Read balances and allowances
```json
{ "tool": "bsc.get-balance", "arguments": { "address": "0xAddr" } }
{ "tool": "bsc.get-token-balance", "arguments": { "address": "0xAddr", "token": "0xToken" } }
{ "tool": "bsc.allowance", "arguments": { "token": "0xToken", "owner": "0xAddr", "spender": "0xSpender" } }
```

### Dry run and external signing
- To build but not send, add `"broadcast": false` in arguments; the tool returns `unsignedTx`.
- You can then use the `signer` plugin to sign/broadcast, or forward to an external KMS signer.

## Security considerations

- Treat `privateKey` as sensitive. Prefer `BSC_PRIVATE_KEY` environment variable loaded by the server process when possible.
- For production: consider a signer backend (KMS/HSM/MPC) through the `signer` plugin with policies and monitoring.
- Always set sane `amount-out-min` (slippage) and deadlines for swaps to reduce MEV risk.

## File locations

- `plugins/bsc/cli.py` — BSC wallet/ERC-20 utilities (includes `create-wallet`).
- `plugins/pancakeswap/cli.py` — PancakeSwap V2 actions (quotes, swaps, liquidity).
- `plugins/signer/cli.py` — Optional signer (local keystore + HTTP forward).
- `smcp.py` — MCP server; auto-discovers plugins and registers tools.

## References

- PancakeSwap docs: [How to Add/Remove Liquidity (EVM)](https://docs.pancakeswap.finance/earn/pancakeswap-pools/liquidity-guide)
