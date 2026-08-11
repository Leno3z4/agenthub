"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { signIn, useSession } from "next-auth/react";
import { Check } from "lucide-react";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import {
  arcTestnet,
  arbitrumSepolia,
} from "viem/chains";
import { getWalletClient } from "wagmi/actions";
import {
  useAccount,
  useWalletClient,
  usePublicClient,
  useSwitchChain,
} from "wagmi";

import { config } from "../providers";
import {
  linkWallet,
  confirmPermissions,
  createAgent,
  getAgentStatus,
  getAgentProfile,
  repairAgent,
} from "../../lib/api";
import { approveAgent } from "../../lib/hyperliquid";
import { depositUSDC } from "../../lib/deposit";

const STEPS = [
  {
    title: "Sign in",
    desc: "Continue with Google or X",
  },
  {
    title: "Connect wallet",
    desc: "Import your burner wallet",
  },
  {
    title: "Fund wallet",
    desc: "Bridge USDC into HyperCore",
  },
  {
    title: "Connect your agent",
    desc: "Give your agent the Alias setup prompt",
  },
  {
    title: "Authorize",
    desc: "Grant delegated trading permission",
  },
];

export default function Onboarding() {
  const router = useRouter();
  const { data: session, status } = useSession();

  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [amount, setAmount] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [agentAddress, setAgentAddress] = useState("");
  const [userId, setUserId] = useState("");
  const [agentPrompt, setAgentPrompt] = useState("");
  const [agentConnected, setAgentConnected] = useState(false);
  const [copied, setCopied] = useState(false);
  const [agentError, setAgentError] = useState("");
  const [initialized, setInitialized] = useState(false);

  const { address } = useAccount();
  const { data: walletClient } = useWalletClient();
  const publicClient = usePublicClient();
  const { switchChainAsync } = useSwitchChain();

  useEffect(() => {
    if (
      status !== "authenticated" ||
      !session?.user ||
      initialized
    ) {
      return;
    }

    setInitialized(true);
    initializeUser();
  }, [status, session, initialized]);

  useEffect(() => {
    if (
      step !== 1 ||
      !userId ||
      !walletClient ||
      !address
    ) {
      return;
    }

    setupWallet();
  }, [step, userId, walletClient, address]);

  useEffect(() => {
    if (
      step !== 3 ||
      !userId ||
      !apiKey ||
      agentPrompt
    ) {
      return;
    }

    prepareAgentConnection();
  }, [step, userId, apiKey, agentPrompt]);

  useEffect(() => {
    if (step !== 3 || !userId || !apiKey) {
      return;
    }

    const check = async () => {
      try {
        const data = await getAgentStatus(
          userId,
          apiKey
        );

        if (data.agent_connected) {
          setAgentConnected(true);
        }
      } catch (err) {
        console.error(err);
      }
    };

    check();

    const interval = setInterval(check, 3000);
    return () => clearInterval(interval);
  }, [step, userId, apiKey]);

  useEffect(() => {
    if (agentConnected) {
      setStep(4);
    }
  }, [agentConnected]);

  async function initializeUser() {
    if (!session?.user) {
      return;
    }

    try {
      setLoading(true);

      const existingUserId = session.user.id;
      const existingApiKey = session.user.apiKey || "";

      setUserId(existingUserId);
      setApiKey(existingApiKey);

      localStorage.setItem(
        "alias_user_id",
        existingUserId
      );

      if (existingApiKey) {
        localStorage.setItem(
          "alias_api_key",
          existingApiKey
        );
      }

      if (!existingApiKey) {
        setStep(1);
        return;
      }

      const profile = await getAgentProfile(
        existingUserId,
        existingApiKey
      );

      if (profile.wallet_address) {
        localStorage.setItem(
          "alias_arc_address",
          profile.wallet_address
        );
      }

      if (
        profile.wallet_connected &&
        profile.agent_created
      ) {
        const repair = await repairAgent(
          existingUserId,
          existingApiKey
        );

        if (repair.agent_address) {
          setAgentAddress(repair.agent_address);

          localStorage.setItem(
            "alias_agent_address",
            repair.agent_address
          );
        }

        if (repair.repaired) {
          setStep(4);
          return;
        }

        if (profile.permissions_approved) {
          router.replace("/dashboard");
          return;
        }

        setStep(4);
        return;
      }

      if (profile.wallet_connected) {
        setStep(3);
        return;
      }

      setStep(1);
    } catch (err) {
      console.error(err);
      setAgentError(
        err instanceof Error
          ? err.message
          : "Failed to restore your Alias account."
      );
      setStep(1);
    } finally {
      setLoading(false);
    }
  }

  async function setupWallet() {
    if (
      !walletClient ||
      !address ||
      !userId
    ) {
      return;
    }

    try {
      setLoading(true);
      setAgentError("");

      const data = await linkWallet({
        wallet_address: address,
      });

      localStorage.setItem(
        "alias_user_id",
        userId
      );

      localStorage.setItem(
        "alias_arc_address",
        address
      );

      if (!data.api_key) {
        throw new Error(
          "Wallet linking succeeded but no API key was returned."
        );
      }

      if (!data.agent_address) {
        throw new Error(
          "Wallet linking succeeded but no agent address was returned."
        );
      }

      /*
       * /wallet/link rotates the API key in the current backend.
       * Make the newly returned key the active browser credential.
       */
      setApiKey(data.api_key);
      localStorage.setItem(
        "alias_api_key",
        data.api_key
      );

      setAgentAddress(data.agent_address);
      localStorage.setItem(
        "alias_agent_address",
        data.agent_address
      );

      setStep(2);
    } catch (err) {
      console.error(err);
      setAgentError(
        err instanceof Error
          ? err.message
          : "Failed to link wallet."
      );
    } finally {
      setLoading(false);
    }
  }

  async function fundWallet() {
    if (
      !walletClient ||
      !publicClient ||
      !address
    ) {
      setAgentError("Connect your wallet first.");
      return;
    }

    const numericAmount = Number(amount);

    if (
      !Number.isFinite(numericAmount) ||
      numericAmount <= 0
    ) {
      setAgentError("Enter a valid USDC amount.");
      return;
    }

    try {
      setLoading(true);
      setAgentError("");

      await depositUSDC({
        walletClient,
        publicClient,
        userId,
        apiKey,
        amount: numericAmount,
      });

      setStep(3);
    } catch (err) {
      console.error(err);
      setAgentError(
        err instanceof Error
          ? err.message
          : "Deposit failed."
      );
    } finally {
      setLoading(false);
    }
  }

  async function prepareAgentConnection() {
    try {
      setLoading(true);
      setAgentError("");

      const data = await createAgent(
        userId,
        apiKey
      );

      const backendUrl =
        process.env.NEXT_PUBLIC_BACKEND_URL ||
        "https://agenthub-g0m8.onrender.com";

      setAgentPrompt(
        data.prompt.replaceAll(
          "{base_url}",
          backendUrl
        )
      );
    } catch (err) {
      console.error(err);
      setAgentError(
        err instanceof Error
          ? err.message
          : "Failed to create agent connection."
      );
    } finally {
      setLoading(false);
    }
  }

  async function copyPrompt() {
    if (!agentPrompt) {
      return;
    }

    await navigator.clipboard.writeText(agentPrompt);
    setCopied(true);

    setTimeout(() => {
      setCopied(false);
    }, 1500);
  }

  async function checkAgentConnection() {
    try {
      setLoading(true);
      setAgentError("");

      const data = await getAgentStatus(
        userId,
        apiKey
      );

      if (!data.agent_connected) {
        setAgentError(
          "Agent has not connected yet."
        );
        return;
      }

      setAgentConnected(true);
    } catch (err) {
      console.error(err);
      setAgentError(
        err instanceof Error
          ? err.message
          : "Could not check agent connection."
      );
    } finally {
      setLoading(false);
    }
  }

  async function authorizeAgent() {
    if (
      !agentAddress ||
      !/^0x[a-fA-F0-9]{40}$/.test(agentAddress)
    ) {
      setAgentError(
        `Invalid or missing agent address: ${
          agentAddress || "(empty)"
        }`
      );
      return;
    }

    if (!walletClient) {
      setAgentError("Wallet is not connected.");
      return;
    }

    try {
      setLoading(true);
      setAgentError("");

      /*
       * Hyperliquid testnet EIP-712 signatures use
       * Arbitrum Sepolia (421614 / 0x66eee).
       * Alias remains on Arc outside the authorization step.
       */
      try {
        await walletClient.request({
          method: "wallet_addEthereumChain",
          params: [
            {
              chainId: "0x66eee",
              chainName: "Arbitrum Sepolia",
              nativeCurrency: {
                name: "Ether",
                symbol: "ETH",
                decimals: 18,
              },
              rpcUrls: [
                arbitrumSepolia.rpcUrls.default.http[0],
              ],
              blockExplorerUrls: [
                arbitrumSepolia.blockExplorers.default.url,
              ],
            },
          ],
        });
      } catch (err) {
        console.log(
          "Arbitrum Sepolia already exists or was rejected:",
          err
        );
      }

      await switchChainAsync({
        chainId: arbitrumSepolia.id,
      });

      await new Promise((resolve) =>
        setTimeout(resolve, 500)
      );

      const hyperliquidWalletClient =
        await getWalletClient(config, {
          chainId: arbitrumSepolia.id,
        });

      if (!hyperliquidWalletClient) {
        throw new Error(
          "Could not access the wallet on Arbitrum Sepolia."
        );
      }

      await approveAgent({
        walletClient: hyperliquidWalletClient,
        agentAddress,
      });

      await confirmPermissions(
        userId,
        apiKey
      );

      await switchChainAsync({
        chainId: arcTestnet.id,
      });

      router.push("/dashboard");
    } catch (err) {
      console.error(err);

      setAgentError(
        err instanceof Error
          ? err.message
          : "Failed to authorize agent."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleGoogleLogin() {
    signIn("google", {
      callbackUrl: "/onboarding",
    });
  }

  function handleXLogin() {
    signIn("twitter", {
      callbackUrl: "/onboarding",
    });
  }

  return (
    <main className="max-w-md mx-auto px-5 py-16">
      <div className="font-mono tracking-widest text-sm mb-8">
        ALIAS — SETUP
      </div>

      <ol className="space-y-1 mb-10">
        {STEPS.map((stepItem, i) => (
          <li
            key={stepItem.title}
            className="flex items-center gap-3 py-2"
          >
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono ${
                i < step
                  ? "bg-signal text-[#071a2e]"
                  : i === step
                  ? "border border-signal text-signal"
                  : "border border-line text-dim"
              }`}
            >
              {i < step ? <Check size={12} /> : i + 1}
            </span>

            <div>
              <div
                className={`font-mono text-sm ${
                  i === step
                    ? "text-white"
                    : "text-dim"
                }`}
              >
                {stepItem.title}
              </div>

              {i === step && (
                <div className="text-xs text-dim">
                  {stepItem.desc}
                </div>
              )}
            </div>
          </li>
        ))}
      </ol>

      {step === 0 ? (
        <div className="space-y-3">
          <button
            onClick={handleGoogleLogin}
            className="w-full bg-signal text-[#071a2e] font-mono font-semibold py-2.5 rounded"
          >
            Continue with Google
          </button>

          <button
            onClick={handleXLogin}
            className="w-full border border-line text-white font-mono font-semibold py-2.5 rounded"
          >
            Continue with X
          </button>
        </div>
      ) : step === 1 ? (
        <div className="flex flex-col items-center gap-4">
          <ConnectButton />
        </div>
      ) : step === 2 ? (
        <div className="space-y-4">
          <input
            type="number"
            min="0"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="Amount (USDC)"
            className="w-full border border-line rounded bg-transparent px-3 py-2"
          />

          <button
            onClick={fundWallet}
            disabled={loading || !amount}
            className="w-full bg-signal text-[#071a2e] py-2.5 rounded"
          >
            {loading ? "Depositing..." : "Deposit"}
          </button>
        </div>
      ) : step === 3 ? (
        <div className="space-y-4">
          <div className="text-sm text-dim">
            Copy this prompt and paste it into the agent you want to
            connect to Alias.
          </div>

          <textarea
            readOnly
            value={
              loading
                ? "Generating setup prompt..."
                : agentPrompt
            }
            className="w-full min-h-64 border border-line rounded bg-transparent px-3 py-2 font-mono text-xs"
          />

          <button
            onClick={copyPrompt}
            disabled={loading || !agentPrompt}
            className="w-full border border-line text-white py-2.5 rounded"
          >
            {copied ? "Copied" : "Copy Setup Prompt"}
          </button>

          <button
            onClick={checkAgentConnection}
            disabled={loading}
            className="w-full bg-signal text-[#071a2e] py-2.5 rounded"
          >
            {loading
              ? "Checking..."
              : "I've Connected My Agent"}
          </button>

          {agentError && (
            <div className="text-xs text-red-400 font-mono">
              {agentError}
            </div>
          )}

          <div className="text-xs text-dim text-center">
            {agentConnected
              ? "Agent connected."
              : "Waiting for your agent to connect..."}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <button
            onClick={authorizeAgent}
            disabled={loading}
            className="w-full bg-signal text-[#071a2e] py-2.5 rounded"
          >
            {loading
              ? "Authorizing..."
              : "Approve Trading"}
          </button>

          {agentError && (
            <div className="text-xs text-red-400 font-mono">
              {agentError}
            </div>
          )}
        </div>
      )}

      <p className="text-dim text-xs text-center mt-4 font-mono">
        Connect → Authorize → Bridge → Dashboard
      </p>
    </main>
  );
}
