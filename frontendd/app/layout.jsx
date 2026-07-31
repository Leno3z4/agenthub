import "./globals.css";
import Providers from "./providers";

export const metadata = {
  title: "Alias",
  description:
    "Autonomous trading infrastructure for agents and perpetual markets.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
