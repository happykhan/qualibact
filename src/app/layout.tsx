import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from 'next/font/google';
import { ThemeProvider } from "next-themes";
import "./globals.css";
import NavBar from "@/components/NavBar";
import AnnouncementBanner from "@/components/AnnouncementBanner";

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});
const jetbrains = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL('https://qualibact.org'),
  title: {
    default: 'QualiBact',
    template: '%s | QualiBact',
  },
  description: "Species-specific quality control of bacterial de novo genome assemblies",
  openGraph: {
    type: 'website',
    siteName: 'QualiBact',
    title: 'QualiBact',
    description: 'Species-specific quality control of bacterial de novo genome assemblies',
    url: 'https://qualibact.org',
  },
  twitter: {
    card: 'summary',
    title: 'QualiBact',
    description: 'Species-specific quality control of bacterial de novo genome assemblies',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${jetbrains.variable} antialiased min-h-screen flex flex-col`}
      >
        <ThemeProvider
          attribute="data-theme"
          defaultTheme="light"
          enableSystem={false}
          storageKey="gx-theme"
        >
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-[var(--gx-accent)] focus:text-[var(--gx-text-inverted)] focus:rounded"
          >
            Skip to content
          </a>
          <NavBar />
          <AnnouncementBanner />
          <main id="main-content" className="container py-8 flex-1">
            {children}
          </main>
          <footer className="gx-footer">
            <div className="gx-footer-inner">
              <h3>QualiBact</h3>
              <p className="text-sm">
                Species-specific quality control of bacterial de novo genome assemblies.
              </p>
              <p className="text-xs mt-3">
                Funded by the National Institute for Health Research (NIHR) under grant NIHR133307.
              </p>
            </div>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
