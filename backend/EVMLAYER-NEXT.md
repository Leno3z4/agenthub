# EVM trading layer — iteration 2

This iteration adds the non-signing parts needed for real trading:

- Uniswap v3 pool discovery by factory + token pair + fee tiers.
- Liquidity and slot0 inspection.
- Quoter V2 exact-input quotes.
- Minimum-output calculation.
- Trade policy validation.
- Read-only FastAPI routes.

## Existing files required

These files build on the previous ZIP:

- `evm_client.py`
- `evm_config.py`
- `evm_models.py`
- `requirements-evm.txt`

## Merge/integration

Copy the new files into the same `backend/` directory.

Add this to the existing FastAPI app:

```python
from evm_routes import router as evm_router
app.include_router(evm_router)
```

Do not expose private keys through these endpoints.

## Still required before production execution

1. Confirm exact Arc Uniswap v3 factory/quoter deployments.
2. Test a real USDC/token quote on Arc testnet.
3. Add transaction simulation (`eth_call`) before every signed trade.
4. Add Universal Router command encoding from the pinned Uniswap SDK.
5. Add nonce locking to prevent concurrent agent trades from colliding.
6. Add receipt polling and persistent trade state.
7. Add v4 PoolInitialize event indexing.
8. Add cross-chain LI.FI execution.
