import "./globals.css";

export const metadata = {
  title: "Alias",
  description:
    "Autonomous trading infrastructure for agents and perpetual markets.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
