export async function executeAchSwap({
  walletClient,
  publicClient,
  tokenIn,
  tokenOut,
  amountIn,
  slippageBps = 100,
}) {
  if (!walletClient) {
    throw new Error("Wallet is not connected.");
  }

  if (!publicClient) {
    throw new Error("Public client is unavailable.");
  }

  const [account] = await walletClient.getAddresses();

  if (!account) {
    throw new Error("Wallet account is unavailable.");
  }

  const response = await fetch("/api/backend/evm/achswap/swap", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      token_in: tokenIn,
      token_out: tokenOut,
      amount_in: amountIn.toString(),
      slippage_bps: slippageBps,
      sender: account,
    }),
    cache: "no-store",
  });

  const text = await response.text();

  if (!response.ok) {
    throw new Error(
      text || `AchSwap returned ${response.status}.`
    );
  }

  const result = text ? JSON.parse(text) : null;

  if (!result) {
    throw new Error("AchSwap returned an empty response.");
  }

  if (result.status === "approval_required") {
    const approval = result.approval;

    const approvalHash = await walletClient.sendTransaction({
      account,
      to: approval.to,
      data: approval.data,
      value: BigInt(approval.value || "0"),
      chainId: approval.chainId,
    });

    const approvalReceipt =
      await publicClient.waitForTransactionReceipt({
        hash: approvalHash,
      });

    if (approvalReceipt.status !== "success") {
      throw new Error("Token approval transaction reverted.");
    }
  }

  const swapResponse = await fetch(
    "/api/backend/evm/achswap/swap",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token_in: tokenIn,
        token_out: tokenOut,
        amount_in: amountIn.toString(),
        slippage_bps: slippageBps,
        sender: account,
      }),
      cache: "no-store",
    }
  );

  const swapText = await swapResponse.text();

  if (!swapResponse.ok) {
    throw new Error(
      swapText || `AchSwap returned ${swapResponse.status}.`
    );
  }

  const swapResult = swapText
    ? JSON.parse(swapText)
    : null;

  if (!swapResult || swapResult.status !== "ready") {
    throw new Error(
      "AchSwap did not return a ready swap transaction."
    );
  }

  const tx = swapResult.swap;

  const swapHash = await walletClient.sendTransaction({
    account,
    to: tx.to,
    data: tx.data,
    value: BigInt(tx.value || "0"),
    chainId: tx.chainId,
  });

  const receipt =
    await publicClient.waitForTransactionReceipt({
      hash: swapHash,
    });

  if (receipt.status !== "success") {
    throw new Error("AchSwap transaction reverted.");
  }

  return {
    hash: swapHash,
    receipt,
    quote: swapResult.quote,
  };
}