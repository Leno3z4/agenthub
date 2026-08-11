import {
  depositParams,
  deposit as registerDeposit,
} from "./api";

import {
  getUsdcContract,
  getTokenMessengerV2Contract,
} from "./contracts";

export async function depositUSDC({
  walletClient,
  publicClient,
  userId,
  amount,
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

  const numericAmount = Number(amount);

  if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
    throw new Error("Enter a valid USDC amount.");
  }

  const amountUnits = BigInt(
    Math.floor(numericAmount * 1_000_000)
  );

  if (amountUnits <= 0n) {
    throw new Error("Enter a valid USDC amount.");
  }

  console.log("========== HYPERCORE CCTP DEPOSIT ==========");
  console.log("Wallet:", account);
  console.log("Amount:", numericAmount);
  console.log("USDC units:", amountUnits.toString());

  const params = await depositParams(
    amountUnits.toString(),
    account
  );

  const usdc = getUsdcContract(walletClient);
  const tokenMessenger =
    getTokenMessengerV2Contract(walletClient);

  const approveHash = await usdc.write.approve([
    tokenMessenger.address,
    amountUnits,
  ]);

  await publicClient.waitForTransactionReceipt({
    hash: approveHash,
  });

  console.log(
    "TokenMessengerV2 approval confirmed:",
    approveHash
  );

  const burnHash =
    await tokenMessenger.write.depositForBurnWithHook([
      amountUnits,
      Number(params.destinationDomain),
      params.mintRecipient,
      params.burnToken,
      params.destinationCaller,
      BigInt(params.maxFee),
      Number(params.minFinalityThreshold),
      params.hookData,
    ]);

  const receipt =
    await publicClient.waitForTransactionReceipt({
      hash: burnHash,
    });

  if (receipt.status !== "success") {
    throw new Error(
      "CCTP HyperCore deposit transaction reverted."
    );
  }

  console.log("CCTP burn confirmed:", burnHash);

  if (userId) {
    try {
      await registerDeposit(
        userId,
        burnHash,
        amountUnits.toString()
      );
    } catch (error) {
      console.error(
        "Failed to register deposit with backend:",
        error
      );
    }
  }

  return {
    hash: burnHash,
    amount: numericAmount,
  };
}
