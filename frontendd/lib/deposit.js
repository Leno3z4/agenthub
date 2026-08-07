import {
  depositParams,
  deposit,
  bridgeStatus,
} from "./api";

import {
  getUsdcContract,
  getTokenMessengerContract,
} from "./contracts";


export async function depositUSDC({
  walletClient,
  publicClient,
  userId,
  apiKey,
  amount,
}) {
  // ---------------------------------------------------------------
  // Amount
  // ---------------------------------------------------------------

  const amountUnits = BigInt(
    Math.floor(Number(amount) * 1_000_000)
  );

  console.log("========== DEPOSIT ==========");
  console.log("INPUT:", amount);
  console.log(
    "MICRO USDC:",
    amountUnits.toString()
  );


  // ---------------------------------------------------------------
  // Get backend CCTP parameters
  // ---------------------------------------------------------------

  const [account] =
    await walletClient.getAddresses();

  console.log(
    "SOURCE WALLET:",
    account
  );

  const params = await depositParams(
    amountUnits.toString(),
    account,
  );

  console.log(
    "BACKEND CCTP PARAMS:",
    params
  );


  // ---------------------------------------------------------------
  // Contracts
  // ---------------------------------------------------------------

  const usdc =
    getUsdcContract(walletClient);

  const messenger =
    getTokenMessengerContract(walletClient);


  // ---------------------------------------------------------------
  // Approve USDC
  // ---------------------------------------------------------------

  console.log(
    "APPROVING USDC:",
    amountUnits.toString()
  );

  const approveHash =
    await usdc.write.approve([
      process.env.NEXT_PUBLIC_CCTP_TOKEN_MESSENGER,
      amountUnits,
    ]);

  console.log(
    "APPROVE TX:",
    approveHash
  );

  const approveReceipt =
    await publicClient.waitForTransactionReceipt({
      hash: approveHash,
    });

  console.log(
    "APPROVE RECEIPT:",
    approveReceipt
  );

  if (approveReceipt.status !== "success") {
    throw new Error(
      "USDC approval transaction reverted."
    );
  }


  // ---------------------------------------------------------------
  // depositForBurnWithHook
  // ---------------------------------------------------------------

  console.log(
    "===== depositForBurnWithHook args ====="
  );

  console.log({
    amount: params.amount,
    destinationDomain:
      params.destinationDomain,
    mintRecipient:
      params.mintRecipient,
    burnToken:
      params.burnToken,
    destinationCaller:
      params.destinationCaller,
    maxFee:
      params.maxFee,
    minFinalityThreshold:
      params.minFinalityThreshold,
    hookData:
      params.hookData,
  });

  console.log(
    "======================================="
  );


  const burnHash =
    await messenger.write.depositForBurnWithHook([
      BigInt(params.amount),
      Number(params.destinationDomain),
      params.mintRecipient,
      params.burnToken,
      params.destinationCaller,
      BigInt(params.maxFee),
      Number(params.minFinalityThreshold),
      params.hookData,
    ]);

  console.log(
    "BURN TX:",
    burnHash
  );


  // ---------------------------------------------------------------
  // Wait for burn confirmation
  // ---------------------------------------------------------------

  const burnReceipt =
    await publicClient.waitForTransactionReceipt({
      hash: burnHash,
    });

  console.log(
    "BURN RECEIPT:",
    burnReceipt
  );

  if (burnReceipt.status !== "success") {
    throw new Error(
      "depositForBurnWithHook transaction reverted."
    );
  }


  // ---------------------------------------------------------------
  // Tell AgentHub backend about the burn
  // ---------------------------------------------------------------

  await deposit(
    userId,
    apiKey,
    burnHash,
    amountUnits.toString(),
  );


  // ---------------------------------------------------------------
  // Poll Circle / Iris
  // ---------------------------------------------------------------

  const started = Date.now();

  while (
    Date.now() - started <
    10 * 60 * 1000
  ) {
    const status =
      await bridgeStatus(burnHash);

    console.log(
      "Bridge status:",
      status
    );

    if (status.complete) {
      return status;
    }

    if (
      status.status &&
      status.status.toLowerCase() ===
        "failed"
    ) {
      throw new Error(
        `Bridge failed: ${
          status.reason || "unknown reason"
        }`
      );
    }

    await new Promise(
      (resolve) =>
        setTimeout(resolve, 5000)
    );
  }

  throw new Error(
    "Bridge timed out."
  );
}
