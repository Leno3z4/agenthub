import { getGatewayWalletContract, getUsdcContract } from "./contracts";

export async function depositUSDC({
  walletClient,
  publicClient,
  amount,
}) {
  const [account] = await walletClient.getAddresses();

  const amountUnits = BigInt(
    Math.floor(Number(amount) * 1_000_000)
  );

  if (amountUnits <= 0n) {
    throw new Error("Enter a valid USDC amount.");
  }

  const usdc = getUsdcContract(walletClient);
  const gatewayWallet = getGatewayWalletContract(walletClient);

  console.log("========== GATEWAY DEPOSIT ==========");
  console.log("Wallet:", account);
  console.log("Amount:", amount);
  console.log("USDC units:", amountUnits.toString());
  console.log("Gateway:", gatewayWallet.address);

  const approveHash = await usdc.write.approve([
    gatewayWallet.address,
    amountUnits,
  ]);

  await publicClient.waitForTransactionReceipt({
    hash: approveHash,
  });

  console.log("Gateway approval confirmed:", approveHash);

  const depositHash = await gatewayWallet.write.deposit([
    process.env.NEXT_PUBLIC_ARC_USDC_ADDRESS,
    amountUnits,
  ]);

  const receipt = await publicClient.waitForTransactionReceipt({
    hash: depositHash,
  });

  if (receipt.status !== "success") {
    throw new Error("Gateway deposit transaction reverted.");
  }

  console.log("Gateway deposit confirmed:", depositHash);

  return {
    hash: depositHash,
    amount: Number(amount),
  };
}
