import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sample BFF Starter",
  description: "Next.js frontend for a FastAPI/Auth0 BFF starter.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
