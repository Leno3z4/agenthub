"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { signIn, useSession } from "next-auth/react";
import { Check } from "lucide-react";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { arcTestnet, arbitrumSepolia } from "viem/chains";
import { getWalletClient } from "wagmi/actions";
import {
  useAccount,
  useWalletClient,
  usePublicClient,
  useSwitchChain,
  useDisconnect,
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


const STEPS = [
  { title: "Sign in", desc: "Continue with Google or X" },
  { title: "Connect wallet", desc: "Import your burner wallet" },
  { title: "Connect your agent", desc: "Give your agent the Alias setup prompt" },
  { title: "Authorize", desc: "Grant delegated trading permission" },
];

export default function Onboarding() {
  const router = useRouter();
  const { data: session, status } = useSession();

  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
 
  const [agentAddress, setAgentAddress] = useState("");
  const [agentPrompt, setAgentPrompt] = useState("");
  const [agentConnected, setAgentConnected] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [initialized, setInitialized] = useState(false);
  const [riskAcknowledged, setRiskAcknowledged] = useState(false);
  const userId = session?.user?.id || "";
  const { disconnect } = useDisconnect();
  const { address } = useAccount();
  const { data: walletClient } = useWalletClient();
  const publicClient = usePublicClient();
  const { switchChainAsync } = useSwitchChain();

  useEffect(() => {
    if (
      status !== "authenticated" ||
      !userId ||
      initialized
    ) {
      return;
    }

    setInitialized(true);
    initializeUser(userId);
  }, [status, userId, initialized]);

  useEffect(() => {
    if (
      step !== 2 ||
      !userId ||
      agentPrompt
    ) {
      return;
    }

    prepareAgentConnection(userId);
  }, [step, userId, agentPrompt]);
  useEffect(() => {
    if (status === "authenticated") {
      disconnect();
    }
  }, [status]);
  useEffect(() => {
    if (step !== 3 || !userId) {
      return;
    }

    let cancelled = false;

    async function check() {
      try {
        const data = await getAgentStatus(userId);

        if (!cancelled && data.agent_connected) {
          setAgentConnected(true);
        }
      } catch (err) {
        console.error(err);
      }
    }

    check();
    const interval = setInterval(check, 3000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [step, userId]);

  useEffect(() => {
    if (agentConnected) {
      setStep(3);
    }
  }, [agentConnected]);

  async function initializeUser(currentUserId) {
    try {
      setLoading(true);
      setError("");

      const profile = await getAgentProfile(currentUserId);
      if (profile.agent_address) {
        setAgentAddress(profile.agent_address);
      }

      if (
        profile.wallet_connected &&
        profile.agent_created
      ) {
        const repair = await repairAgent(currentUserId);

        if (repair.agent_address) {
          setAgentAddress(repair.agent_address);
        }

        if (repair.repaired) {
          setStep(3);
          return;
        }

        if (profile.permissions_approved) {
          router.replace("/dashboard");
          return;
        }

        setStep(3);
        return;
      }

      if (profile.wallet_connected) {
        setStep(2);
        return;
      }

      setStep(1);
    } catch (err) {
      console.error(err);

      setError(
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
    if (!walletClient || !address || !userId) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const data = await linkWallet({
        wallet_address: address,
      });

      if (!data.agent_address) {
        throw new Error(
          "Wallet linking succeeded but no agent address was returned."
        );
      }

      setAgentAddress(data.agent_address);
      setStep(2);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to link wallet."
      );
    } finally {
      setLoading(false);
    }
  }

  



  async function prepareAgentConnection(currentUserId) {
    try {
      setLoading(true);
      setError("");

      const data = await createAgent(currentUserId);
      const backendUrl =
        process.env.NEXT_PUBLIC_BACKEND_URL ||
        "https://agenthub-g0m8.onrender.com";

      setAgentPrompt(
        data.prompt.replaceAll("{base_url}", backendUrl)
      );
    } catch (err) {
      console.error(err);

      setError(
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

    setTimeout(() => setCopied(false), 1500);
  }

  async function checkAgentConnection() {
    try {
      setLoading(true);
      setError("");

      const data = await getAgentStatus(userId);

      if (!data.agent_connected) {
        setError("Agent has not connected yet.");
        return;
      }

      setAgentConnected(true);
    } catch (err) {
      console.error(err);

      setError(
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
      setError(
        `Invalid or missing agent address: ${
          agentAddress || "(empty)"
        }`
      );
      return;
    }

    if (!walletClient) {
      setError("Wallet is not connected.");
      return;
    }

    try {
      setLoading(true);
      setError("");

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

      await confirmPermissions(userId);

      await switchChainAsync({
        chainId: arcTestnet.id,
      });

      router.push("/dashboard");
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to authorize agent."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleGoogleLogin() {
    signIn("google", { callbackUrl: "/onboarding" });
  }

  function handleXLogin() {
    signIn("twitter", { callbackUrl: "/onboarding" });
  }

  return (
    <main className="max-w-md mx-auto px-5 py-16">
      <div className="font-mono tracking-widest text-sm mb-8">
        ALIAS — SETUP
      </div>

      <ol className="space-y-1 mb-10">
        {STEPS.map((item, i) => (
          <li
            key={item.title}
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
                  i === step ? "text-white" : "text-dim"
                }`}
              >
                {item.title}
              </div>

              {i === step && (
                <div className="text-xs text-dim">
                  {item.desc}
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
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
          <p className="text-sm font-medium">
            Before you connect
          </p>
        
          <p className="mt-2 text-xs leading-5 text-white/60">
            Alias gives connected agents the ability to execute trades on your
            behalf. Trading can result in partial or total loss of funds. You are
            responsible for your agent's actions and for the permissions you grant.
          </p>
        
          <label className="mt-4 flex cursor-pointer items-start gap-3 text-xs">
            <input
              type="checkbox"
              checked={riskAcknowledged}
              onChange={(e) => setRiskAcknowledged(e.target.checked)}
            />
            <span>
              I understand the risks and authorize Alias to proceed.
            </span>
          </label>
        </div>
        disabled={!riskAcknowledged || loading}
        <div className="flex flex-col items-center gap-4">
          <ConnectButton />

          {address && walletClient && (
            <button
              onClick={setupWallet}
              disabled={loading}
              className="w-full bg-signal text-[#071a2e] py-2.5 rounded"
            >
              {loading ? "Connecting..." : "Continue"}
            </button>
          )}
        </div>
      
      ) : step === 2 ? (
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
            disabled={!agentPrompt}
            className="w-full bg-signal text-[#071a2e] py-2.5 rounded"
          >
            {copied ? "Copied" : "Copy setup prompt"}
          </button>

          <button
            onClick={checkAgentConnection}
            disabled={loading}
            className="w-full border border-line text-white py-2.5 rounded"
          >
            {loading ? "Checking..." : "Check connection"}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="border border-line rounded p-4">
            <div className="font-mono text-xs text-dim mb-2">
              DELEGATED AGENT
            </div>

            <div className="font-mono text-xs break-all">
              {agentAddress || "Loading..."}
            </div>
          </div>

          <button
            onClick={authorizeAgent}
            disabled={loading || !agentAddress}
            className="w-full bg-signal text-[#071a2e] py-2.5 rounded"
          >
            {loading ? "Authorizing..." : "Approve Trading"}
          </button>
        </div>
      )}

      {error && (
        <div className="mt-6 border border-red-500/40 rounded p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {loading && step === 0 && (
        <div className="mt-6 text-xs text-dim font-mono">
          Restoring Alias session...
        </div>
      )}

      <div className="mt-6 text-center text-xs text-dim font-mono">
        Connect - Authorize - Dashboard
      </div>
    </main>
  );
}
