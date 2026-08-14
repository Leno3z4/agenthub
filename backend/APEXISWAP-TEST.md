# Apexiswap testnet adapter

Flow:
1. Factory.getPair
2. Read pair reserves
3. Router.getAmountsOut
4. Calculate amountOutMinimum
5. Build swapExactTokensForTokens
6. eth_call simulation
7. Estimate gas
8. Return unsigned transaction

This adapter never accepts or stores private keys. The existing wallet-signing
layer must sign and broadcast the returned transaction.

Before live testing, verify the factory/router addresses against the current
Apexiswap Arc Testnet deployment and use a small test amount.
