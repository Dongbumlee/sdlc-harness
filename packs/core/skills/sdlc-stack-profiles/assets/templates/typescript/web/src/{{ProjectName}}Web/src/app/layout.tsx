import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import { publicConfig } from "@/lib/config";

import "./globals.css";

export const metadata: Metadata = {
  title: publicConfig.appName,
  description: `${publicConfig.appName} web application`,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-white focus:p-2"
          href="#main"
        >
          Skip to main content
        </a>
        <header>
          <p>{publicConfig.appName}</p>
          <nav aria-label="Primary">
            <ul>
              <li>
                <Link href="/">Items</Link>
              </li>
              <li>
                <Link href="/health">Health</Link>
              </li>
            </ul>
          </nav>
        </header>
        {children}
        <footer>
          <p>{publicConfig.appName} — server-rendered sample.</p>
        </footer>
      </body>
    </html>
  );
}
