"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check } from "lucide-react";
import { ConnectButton } from "@rainbow-me/rainbowkit";

import {
  useAccount,
  useWalletClient,
  usePublicClient,
} from "wagmi";

import {
  linkWallet,
  confirmPermissions,
} from "../../lib/api";

import {
  approveAgent,
} from "../../lib/hyperliquid";

import {
  depositUSDC,
} from "../../lib/deposit";

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
    title: "Authorize",
    desc: "Grant delegated trading permission",
  },
  {
    title: "Connect your agent",
    desc: "Generate your Alias agent",
  },
  {
    title: "Fund wallet",
    desc: "Bridge USDC into HyperCore",
  },
];

export default function Onboarding() {
  const router = useRouter();

  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);

  const [apiKey, setApiKey] = useState("");
  const [agentAddress, setAgentAddress] = useState("");

  const {
    address,
    isConnected,
  } = useAccount();

  const {
    data: walletClient,
  } = useWalletClient();

  const publicClient =
    usePublicClient();

  useEffect(() => {
    if (isConnected) {
      setStep(1);
    }
  }, [isConnected]);

  async function setupWallet() {
    if (
      !walletClient ||
      !address
    ) {
      return;
    }

    try {
      setLoading(true);

      const data =
        await linkWallet(address);

      setApiKey(data.api_key);

      setAgentAddress(
        data.agent_address,
      );

      await approveAgent({
        walletClient,
        agentAddress:
          data.agent_address,
      });

      await confirmPermissions(
        address,
        data.api_key,
      );

      localStorage.setItem(
        "alias_arc_address",
        address,
      );

      localStorage.setItem(
        "alias_api_key",
        data.api_key,
      );

      localStorage.setItem(
        "alias_agent_address",
        data.agent_address,
      );

      setStep(4);
    } catch (err) {
      console.error(err);
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
      return;
    }

    try {
      setLoading(true);

      await depositUSDC({
        walletClient,
        publicClient,
        arcAddress: address,
        apiKey,
        amount: 1_000_000,
      });

      router.push("/dashboard");
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
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
              {i < step ? (
                <Check size={12} />
              ) : (
                i + 1
              )}
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
        <div className="flex justify-center">
          <ConnectButton />
        </div>
      ) : step < 4 ? (
        <button
          onClick={setupWallet}
          disabled={
            loading ||
            !isConnected
          }
          className="w-full bg-signal text-[#071a2e] font-mono font-semibold py-2.5 rounded"
        >
          {loading
            ? "Authorizing..."
            : "Continue"}
        </button>
      ) : (
        <button
          onClick={fundWallet}
          disabled={loading}
          className="w-full bg-signal text-[#071a2e] font-mono font-semibold py-2.5 rounded"
        >
          {loading
            ? "Bridging USDC..."
            : "Deposit 1 USDC"}
        </button>
      )}

      <p className="text-dim text-xs text-center mt-4 font-mono">
        Connect → Authorize → Bridge → Dashboard
      </p>
    </main>
  );
}
