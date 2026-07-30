import "./globals.css";

export const metadata = {
  title: "Alias",
  description: "Infrastructure for autonomous AI agent perpetual futures trading",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
