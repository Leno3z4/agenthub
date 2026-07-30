import "./globals.css";

export const metadata = {
  title: "Alias — Autonomous Trading Infrastructure",
  description:
    "Alias is the execution layer between autonomous agents and perpetual markets.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
