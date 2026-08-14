# Alias EVM Step 2 + Step 3

This package implements:

1. Uniswap v3 pool discovery.
2. Quoter V2 exact-input quotes.
3. ERC-20 allowance/approval transaction building.
4. SwapRouter02 `exactInputSingle` transaction building.
5. `eth_call` simulation before a swap transaction is returned.
6. Gas estimation.
7. Read-only/build-only FastAPI endpoints.

## Important network note

Arc's official docs currently say Arc Testnet is the testnet environment and
that its App Kit Swap capability on testnet is limited to USDC, EURC and
cirBTC. Arc's official contract-address page currently lists Arc Testnet
addresses but does not list Uniswap v3 deployments.

Therefore this package deliberately DOES NOT hard-code an alleged Uniswap
testnet deployment.

The v3 addresses must be populated from the verified deployment for whichever
network you target.

## API

### Discover pools

POST `/evm/pools`

```json
{
  "token_in": "0x...",
  "token_out": "0x...",
  "fees": [100, 500, 3000, 10000]
}
```

### Quote

POST `/evm/quote`

```json
{
  "token_in": "0x...",
  "token_out": "0x...",
  "amount_in": 1000000,
  "fee": 3000,
  "slippage_bps": 100
}
```

### Build approval

POST `/evm/approval/build`

### Build + simulate swap

POST `/evm/swap/build`

The swap endpoint does NOT sign or broadcast. It returns calldata only after
`eth_call` succeeds and gas estimation succeeds.

## Production sequence

1. Discover the deepest pool.
2. Quote exact input.
3. Apply trade policy.
4. Build approval if needed.
5. Send approval through the existing agent-wallet signing path.
6. Re-check allowance.
7. Build swap.
8. Simulate swap.
9. Sign with the existing agent wallet.
10. Broadcast.
11. Persist pending transaction.
12. Poll receipt.
13. Update the agent position.

Do not expose a private key through these routes.
