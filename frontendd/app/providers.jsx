"use client";

import "@rainbow-me/rainbowkit/styles.css";
import { SessionProvider } from "next-auth/react";

import {
  RainbowKitProvider,
  connectorsForWallets,
} from "@rainbow-me/rainbowkit";

import {
  metaMaskWallet,
  rabbyWallet,
  walletConnectWallet,
} from "@rainbow-me/rainbowkit/wallets";

import {
  arcTestnet,
  arbitrumSepolia,
} from "viem/chains";

import {
  createConfig,
  WagmiProvider,
  http,
} from "wagmi";

import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

// Arc's real testnet chain, shipped directly by viem — no need to
// hand-build this. The old version constructed it from
// NEXT_PUBLIC_ARC_CHAIN_ID / NEXT_PUBLIC_ARC_RPC_URL, which were never
// actually set anywhere (no .env.example entry, no fallback), so
// Number(undefined) silently became NaN and broke the whole wagmi
// config. Confirmed against docs.arc.io/arc/references/connect-to-arc,
// which uses this exact import.
const connectors = connectorsForWallets(
  [
    {
      groupName: "Wallets",
      wallets: [
        metaMaskWallet,
        rabbyWallet,
        walletConnectWallet,
      ],
    },
  ],
  {
    appName: "Alias",
    projectId:
      process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID,
  },
);

const config = createConfig({
  connectors,
  chains: [
    arcTestnet,
    arbitrumSepolia,
  ],
  
  transports: {
    [arcTestnet.id]: http("/api/rpc"),
    [arbitrumSepolia.id]: http(),
  },
});

const queryClient = new QueryClient();
export const config = createConfig({
  connectors,
  chains: [
    arcTestnet,
    arbitrumSepolia,
  ],
  transports: {
    [arcTestnet.id]: http("/api/rpc"),
    [arbitrumSepolia.id]: http(),
  },
});
export default function Providers({ children }) {
  return (
    <SessionProvider>
      <WagmiProvider config={config}>
        <QueryClientProvider client={queryClient}>
          <RainbowKitProvider>
            {children}
          </RainbowKitProvider>
        </QueryClientProvider>
      </WagmiProvider>
    </SessionProvider>
  );
}
