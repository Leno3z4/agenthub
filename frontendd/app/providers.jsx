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
import { arcTestnet } from "viem/chains";
import { createConfig, WagmiProvider, http } from "wagmi";
import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

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
    projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID,
  },
);

export const config = createConfig({
  connectors,
  chains: [arcTestnet],
  transports: {
    [arcTestnet.id]: http("/api/rpc"),
  },
});

const queryClient = new QueryClient();

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
