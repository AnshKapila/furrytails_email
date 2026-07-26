import type { Metadata } from 'next';
import Script from 'next/script';
import {
  RUNTIME_ERROR_CAPTURE_SCRIPT,
  buildErrorProviderPin,
  buildPosthogInitScript,
  escapeJsonForScript,
  isValidPosthogToken,
  SCRIPT_INJECTOR_CDN_URL,
} from '@appsmithorg/template-frontend';
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
  // PostHog analytics — sits beside Pirsch. Per-site project token injected at
  // build via NEXT_PUBLIC_POSTHOG_KEY; production-only. The helpers come from
  // @appsmithorg/template-frontend (>=1.1.7 — the version that exports all
  // three), the same published-package channel the Payload layout uses; seeded
  // sites pick up helper changes at publish time. Returns null for a
  // missing/malformed token.
  // Capture-off on purpose FOR THIS TEMPLATE ONLY: the Kite analytics SDK below
  // emits page_viewed/page_engaged as the source of truth and the data-kite-*
  // stamps are the interaction vocabulary — posthog-js $pageview/$autocapture
  // would double-count and harvest element text. Consumers without the SDK
  // (Vite, Payload) keep the helper's capture-on defaults.
  const posthogScript =
    process.env.NODE_ENV === 'production'
      ? buildPosthogInitScript(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
          capturePageview: false,
          capturePageleave: false,
          autocapture: false,
        })
      : null;

  // Kite custom-event analytics envelope. The stamp-driven SDK
  // (/kite-analytics.js) reads window.__KITE_ENV__ and captures through
  // window.posthog. Production-only; needs both a PostHog project and a website
  // id. `<` escaped so no value can close the inline <script> (XSS guard).
  const kiteEnv =
    process.env.NODE_ENV === 'production' &&
    isValidPosthogToken(process.env.NEXT_PUBLIC_POSTHOG_KEY) &&
    process.env.NEXT_PUBLIC_KITE_WEBSITE_ID
      ? escapeJsonForScript({
          posthogToken: process.env.NEXT_PUBLIC_POSTHOG_KEY,
          websiteId: process.env.NEXT_PUBLIC_KITE_WEBSITE_ID,
          accountId: process.env.NEXT_PUBLIC_KITE_ACCOUNT_ID || undefined,
          goalType: process.env.NEXT_PUBLIC_KITE_GOAL_TYPE || undefined,
          schemaVersion: '1.0',
        })
      : null;

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Runtime error capture. Inlined first so window listeners attach before */}
        {/* any user code runs, catching async/window errors + unhandled rejections */}
        {/* that the global-error boundary (render errors only) never sees. Gated */}
        {/* on either analytics token. The provider pin (ANALYTICS_ERROR_PROVIDER, */}
        {/* set by provisioning to match the backend Errors view) is prepended so */}
        {/* writes go to the same provider reads do; absent, it falls back to */}
        {/* whichever SDK is present. Script + pin live in the shared package (one */}
        {/* source with the Vite runtime-error-capture plugin). */}
        {process.env.NODE_ENV === 'production' &&
          (process.env.NEXT_PUBLIC_PIRSCH_TOKEN ||
            process.env.NEXT_PUBLIC_POSTHOG_KEY) && (
            <script
              id="runtime-error-capture"
              dangerouslySetInnerHTML={{
                __html:
                  buildErrorProviderPin(
                    process.env.NEXT_PUBLIC_ANALYTICS_ERROR_PROVIDER,
                  ) + RUNTIME_ERROR_CAPTURE_SCRIPT,
              }}
            />
          )}
        {/* Script injector enables Kite's point-and-click editor inside the */}
        {/* preview iframe. Skipped in production builds — point-and-click is */}
        {/* an editing-time capability, not a runtime feature for end users. */}
        {process.env.NODE_ENV !== 'production' && (
          <Script src={SCRIPT_INJECTOR_CDN_URL} strategy="afterInteractive" />
        )}
        {/* Pirsch analytics. A static <script> (not next/script) so it sits in */}
        {/* the server HTML at parse time — pa.js then auto-tracks the first */}
        {/* pageview and SPA navigations. next/script's afterInteractive injects */}
        {/* post-load, after pa.js's load hooks have fired, so the initial */}
        {/* pageview is missed; beforeInteractive can strip data-* in app router */}
        {/* (vercel/next.js#49830). Token injected at build via */}
        {/* NEXT_PUBLIC_PIRSCH_TOKEN (deployment_service); absent in dev. */}
        {process.env.NODE_ENV === 'production' &&
          process.env.NEXT_PUBLIC_PIRSCH_TOKEN && (
            <script
              defer
              src="https://api.pirsch.io/pa.js"
              id="pianjs"
              data-code={process.env.NEXT_PUBLIC_PIRSCH_TOKEN}
            />
          )}
        {/* PostHog analytics (autocapture + pageviews). Inline so it sits in the */}
        {/* server HTML at parse time, beside Pirsch. */}
        {posthogScript && (
          <script
            id="posthog-analytics"
            dangerouslySetInnerHTML={{ __html: posthogScript }}
          />
        )}
        {/* Kite custom-event analytics SDK. Inline envelope (parse-time, after */}
        {/* PostHog init) then the deferred stamp-driven SDK from public/. */}
        {kiteEnv && (
          <>
            <script
              id="kite-analytics-env"
              dangerouslySetInnerHTML={{
                __html: `window.__KITE_ENV__=${kiteEnv};`,
              }}
            />
            <script src={`/kite-analytics.js?v=${KITE_SDK_VERSION}`} defer />
          </>
        )}
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
