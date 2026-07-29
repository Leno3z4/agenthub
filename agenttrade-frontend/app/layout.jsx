import "./globals.css";

export const metadata = {
  title: "AgentTrade",
  description: "Infrastructure for autonomous AI agent perpetual futures trading",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
