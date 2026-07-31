"use client";

import "@rainbow-me/rainbowkit/styles.css";

import { ReactNode } from "react";

import {
  getDefaultConfig,
  RainbowKitProvider,
} from "@rainbow-me/rainbowkit";

import {
  WagmiProvider,
  http,
} from "wagmi";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const arc = {
  id: Number(process.env.NEXT_PUBLIC_ARC_CHAIN_ID),
  name: "Arc",
  network: "arc",
  nativeCurrency: {
    name: "ARC",
    symbol: "ARC",
    decimals: 18,
  },
  rpcUrls: {
    default: {
      http: [process.env.NEXT_PUBLIC_ARC_RPC_URL!],
    },
  },
  blockExplorers: {
    default: {
      name: "Arc Explorer",
      url: process.env.NEXT_PUBLIC_ARC_EXPLORER!,
    },
  },
} as const;

const config = getDefaultConfig({
  appName: "Alias",
  projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID!,
  chains: [arc],
  transports: {
    [arc.id]: http(process.env.NEXT_PUBLIC_ARC_RPC_URL),
  },
});

const queryClient = new QueryClient();

export default function Providers({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider>
          {children}
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
