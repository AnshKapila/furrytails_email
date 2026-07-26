import { existsSync, readFileSync } from "node:fs";

// Per-app redirects.csv is the platform's "bulk redirects" channel. The
// template ships a header-only file by default; only point Vercel at it once
// at least one redirect row has been added. Row validity is enforced by Vercel
// itself at build time.
// Vercel runs vercel.ts with cwd at the project root (where this file lives).
function hasRedirectRows(): boolean {
  if (!existsSync("redirects.csv")) return false;
  const dataRows = readFileSync("redirects.csv", "utf8")
    .split("\n")
    .slice(1)
    .filter(line => line.trim().length > 0);
  return dataRows.length > 0;
}

// Common headers for both layouts — security hardening that applies regardless
// of framework.
const SECURITY_HEADERS = [
  {
    source: "/(.*)",
    headers: [
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      {
        key: "Content-Security-Policy",
        value:
          "default-src * 'self' data: blob: 'unsafe-inline' 'unsafe-eval'; frame-ancestors *",
      },
    ],
  },
];

const REDIRECTS_CONFIG = hasRedirectRows()
  ? { bulkRedirectsPath: "redirects.csv" }
  : {};

// Only the Kite-generated app (a Vite SPA + Fastify API at `api/index.ts`) needs
// the explicit Functions/rewrites/output config below, so key on that entrypoint.
// Everything else is Next.js — imports are gated to Next.js and Kite's own
// non-Fastify apps are Next.js (including the Payload template, which ships
// `next.config.mjs` and no Fastify entrypoint) — so set its framework
// explicitly. (Omitting `framework` is not enough: the per-app Vercel project
// keeps its earlier preset, so Vercel skips the Next.js build and the deploy 404s.)
const hasFastifyApi = existsSync("api/index.ts");

// Plain object export — no `@vercel/config` import. Each deployed app has a
// frozen package.json from when it was generated; importing `@vercel/config`
// here would force every existing app to add the package as a dep before its
// next deploy. The Vercel docs explicitly support a bare typed export.
export const config = hasFastifyApi
  ? {
      framework: null,
      cleanUrls: true,
      outputDirectory: "frontend/dist/client",
      ...REDIRECTS_CONFIG,
      headers: SECURITY_HEADERS,
      rewrites: [
        { source: "/api/(.*)", destination: "/api" },
        { source: "/(.*)", destination: "/api" },
      ],
      functions: {
        "api/index.ts": {
          includeFiles:
            "{shared/openapi_spec.yaml,node_modules/.pnpm/@seriousme+openapi-schema-validator@*/node_modules/@seriousme/openapi-schema-validator/schemas/**/*.json,frontend/dist/client/**}",
        },
      },
    }
  : {
      // Next.js (imported repo or a Kite-generated Next.js app). Set the
      // framework explicitly so Vercel runs its Next.js build/output regardless
      // of the project's stored preset; add only headers and redirects on top.
      framework: "nextjs",
      ...REDIRECTS_CONFIG,
      headers: SECURITY_HEADERS,
    };
