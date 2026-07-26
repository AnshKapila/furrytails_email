import type { Metadata } from 'next';
import Script from 'next/script';
import DevErrorOverlay from '@/components/dev-error-overlay';
import { getBaseUrl } from '@/lib/site-url';
import { cormorant, inter } from './fonts';
import './globals.css';

// metadataBase resolves the relative `alternates.canonical` and
// `openGraph.url` paths that route pages export into absolute URLs, and
// follows the deploy URL (preview, production, custom domain) instead of a
// domain frozen at generation time.
export const metadata: Metadata = {
  metadataBase: new URL(getBaseUrl()),
  title: 'Furrytail — Natural care, considered',
  description: 'Join the Furrytail early access list for a new natural pet care ritual.',
  twitter: { card: 'summary_large_image' },
  icons: {
    icon: 'https://static.kite.ai/image/upload/v1785039469/app/eaccac4c-a287-4e55-89be-8007fdbfaef1/sfz9mtw46huqdvgxykuq.png',
    shortcut: 'https://static.kite.ai/image/upload/v1785039469/app/eaccac4c-a287-4e55-89be-8007fdbfaef1/sfz9mtw46huqdvgxykuq.png',
    apple: 'https://static.kite.ai/image/upload/v1785039469/app/eaccac4c-a287-4e55-89be-8007fdbfaef1/sfz9mtw46huqdvgxykuq.png',
  },
};

// Cache-bust for the stamp-driven SDK: a content hash DERIVED at build time in
// next.config.js from public/kite-analytics.js itself — never hand-bumped, so an
// SDK edit can't ship with a stale ?v= (returning visitors always re-fetch).
const KITE_SDK_VERSION = process.env.NEXT_PUBLIC_KITE_SDK_HASH || 'dev';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
      </head>
      {/* suppressHydrationWarning (html above + body): extensions and the */}
      {/* preview iframe host stamp attributes on both before React hydrates */}
      {/* (Grammarly marks <body>); the mismatch is attribute-only and */}
      {/* harmless, but would open the dev error overlay. */}
      <body suppressHydrationWarning className={`${cormorant.variable} ${inter.variable}`}>
        {process.env.NODE_ENV !== 'production' && <DevErrorOverlay />}
        {children}
      </body>
    </html>
  );
}
