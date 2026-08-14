# Alias EVM trading layer

This branch adds the first EVM execution boundary without changing the
existing Hyperliquid implementation.

## Current scope

- Arc chain configuration.
- ERC-20 balance/allowance helpers.
- ERC-20 approval transaction builder.
- Uniswap Universal Router transaction builder.
- Local transaction signing helper.
- Raw transaction submission helper.
- v4 PoolKey/PoolId and StateView helpers.

## Important

The Universal Router command encoding is deliberately not guessed here.
The swap command bytes must come from a pinned/tested Uniswap encoder before
production execution is enabled.

Likewise, `ARC_UNISWAP_STATE_VIEW` must be populated with the exact Arc
deployment being targeted.

This keeps the dangerous part explicit instead of silently constructing an
incorrect swap.

## Next step

Add:

1. pool discovery/indexer;
2. tested v3/v4 quoting;
3. Universal Router command encoding;
4. trade limits/slippage/price-impact checks;
5. agent-facing buy/sell endpoints;
6. cross-chain LI.FI adapter;
7. withdrawal routing.
