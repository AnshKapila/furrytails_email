// Resolves the deploy URL for metadata routes (sitemap, robots) and
// `layout.tsx`'s `metadataBase: new URL(...)`. Used by `app/sitemap.ts`,
// `app/robots.ts`, and the root layout so they advertise the same origin.
//
// Precedence:
// 1. NEXT_PUBLIC_SITE_URL — the backend injects this at publish time set to the
//    effective canonical URL (connected custom domain > user override >
//    .kite.space subdomain). It already carries an https:// scheme. Prefer it
//    over Vercel's auto-vars, which pick the shortest project domain (often the
//    .kite.space default, not the user's connected custom domain).
// 2. VERCEL_PROJECT_PRODUCTION_URL (production) / VERCEL_URL (previews) — set by
//    Vercel without a scheme.
// 3. localhost fallback (the URL the sandbox actually serves).
//
// Use `||`, not `??`: the sandbox preview writes these keys into `.env.local`
// present-but-EMPTY, and `??` only falls back on null/undefined. With `??` an
// empty NEXT_PUBLIC_SITE_URL returns "", and `new URL("")` throws — 500-ing
// every route in preview. `||` treats "" as absent so the next source wins.

export function getBaseUrl(): string {
  // Strip trailing slashes: callers build `${baseUrl}/${path}`, so a
  // user-edited value like "https://example.com/" would otherwise yield
  // double-slash canonical/sitemap URLs.
  return resolveBaseUrl().replace(/\/+$/, '');
}

function resolveBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_SITE_URL) return process.env.NEXT_PUBLIC_SITE_URL;
  const vercel =
    process.env.VERCEL_PROJECT_PRODUCTION_URL || process.env.VERCEL_URL;
  if (vercel) return `https://${vercel}`;
  return 'http://localhost:4321';
}
