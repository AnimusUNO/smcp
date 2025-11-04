# PancakeSwap Add Liquidity Fix

## Problem
When trying to add liquidity on PancakeSwap, users were getting this error:
```
Error: TransferHelper: TRANSFER_FROM_FAILED
```

This error occurs because the PancakeSwap router needs approval to spend both tokens before it can add them to a liquidity pool.

## Root Cause
The `add_liquidity_v2` function in `plugins/pancakeswap/cli.py` was directly attempting to add liquidity without checking if the router had approval to spend the tokens. Unlike the `swap_auto` function which handles approvals automatically, the liquidity function was missing this critical step.

## Solution
Updated the `add_liquidity_v2` function to:

1. **Check allowances** for both token-a and token-b before adding liquidity
2. **Automatically approve** any token that needs approval (unlimited approval: 2^256-1)
3. **Wait for approval transactions** to be mined before proceeding
4. **Only then add liquidity** once both tokens are approved

This mirrors the approval handling logic from the `swap_auto` function.

## Changes Made

### 1. `smcp-master/plugins/pancakeswap/cli.py`
- Updated `add_liquidity_v2()` function (lines 340-434)
- Added automatic approval loop for both tokens
- Checks current allowance vs. amount needed
- Broadcasts approval transactions and waits for confirmation
- Returns approval info in the result

### 2. `smcp-master/smcp.py`
- Updated tool description for `pancakeswap_add-liquidity-v2` (line 675)
- Now clearly states: "AUTOMATIC APPROVAL HANDLING"
- Informs users that both tokens are automatically approved

## How It Works

When you call the tool with your parameters:

```json
{
  "token-a": "0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",  // WBNB
  "token-b": "0x06E08A9BFB83e0e791Cd1f24535aDA4fA4094444",  // ANIMUS
  "amount-a-desired": "180116205000000000",
  "amount-b-desired": "88075355241197750969350",
  "amount-a-min": 0,
  "amount-b-min": 0,
  "to": "0x3F8784acaFa0D3991Aae9C0042784BF190263466",
  "broadcast": true,
  "gas-price-gwei": 5,
  "chain": "mainnet"
}
```

The function will:

1. Check if token-a (WBNB) needs approval → Approve if needed
2. Check if token-b (ANIMUS) needs approval → Approve if needed
3. Wait for all approvals to be mined
4. Execute the add liquidity transaction
5. Return result with approval transaction hashes

## Example Response

```json
{
  "txHash": "0x...",
  "approvals": [
    {
      "token": "token-a",
      "txHash": "0x..."
    },
    {
      "token": "token-b", 
      "txHash": "0x..."
    }
  ],
  "approval_status": "completed"
}
```

## Testing

To test the fix:

1. Ensure your MCP server is running:
   ```bash
   cd smcp-master
   python smcp.py
   ```

2. Ask your Letta agent to add liquidity:
   ```
   "Create a PancakeSwap LP position using WBNB and ANIMUS"
   ```

3. The tool should now:
   - Automatically approve both tokens
   - Add liquidity successfully
   - Return transaction hashes for approvals and liquidity addition

## Notes

- **Unlimited Approval**: The function approves `2^256-1` (maximum uint256) to avoid needing approval again in the future
- **Gas Estimation**: Each approval transaction has gas estimated at 1.2x the estimate for safety
- **Timeout**: Approval transactions wait up to 120 seconds to be mined
- **Non-broadcast Mode**: If `broadcast=false`, returns the first unsigned approval transaction

## Security Considerations

- Approvals are done with unlimited amount for convenience
- Private key is loaded from `BSC_PRIVATE_KEY` environment variable
- No private keys are exposed to the LLM
- All transactions are signed locally

## Related Files

- `smcp-master/plugins/pancakeswap/cli.py` - PancakeSwap plugin implementation
- `smcp-master/smcp.py` - MCP server tool definitions
- `smcp-master/docs/bsc-pancakeswap.md` - PancakeSwap usage documentation

