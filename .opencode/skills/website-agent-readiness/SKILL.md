---
name: website-agent-readiness
description: >
  Use this skill when making a website easy for AI agents and answer engines
  to read, navigate, and act on — e.g. "make my site AI-ready", "optimize for
  AI search", "let AI agents use my site", "block AI training on my content" —
  and when asked to audit or score a site's agent readiness ("is this site
  agent-ready?", "run an agent-readiness check"), or an audit flags failing
  checks. It owns the site's AI-crawler access policy and content-usage
  signals, the scored live-site readiness audit, keeps the machine-readable
  discovery files complete, and says which agent standards to skip because
  they would be dishonest for this kind of site. For writing llms.txt itself
  use website-aeo-metadata-management; for sitemap.xml use
  website-sitemap-management; for structured data use
  website-seo-metadata-management.
mode: both
---

# Website Agent Readiness

Make the site score well on agent-readiness checks (the checks behind scanners like isitagentready.com): AI agents must be able to discover the site's structure, read its content cheaply, and know what they are allowed to do with it. This skill owns the AI-facing access policy; the discovery files themselves have owner skills (see cross-references below).

## What "agent-ready" means for a Kite site

| Dimension | Check | Where it lives | Status on a fresh site |
| --- | --- | --- | --- |
| Discoverability | `robots.txt` exists and names a `Sitemap:` (absolute URL) | Next.js: `src/app/robots.ts` · classic: `frontend/public/robots.txt` | Ships by default — keep it intact |
| Discoverability | `sitemap.xml` lists every route | Next.js: `src/app/sitemap.ts` · classic: `website-sitemap-management` skill | Ships by default; extend per new route |
| Content | `/llms.txt` gives agents a curated site map | `website-aeo-metadata-management` skill | Generated at build; regenerate after structural changes |
| Bot access | AI crawlers are named explicitly in `robots.txt` | The `AI_CRAWLERS` rule block (Next.js) / the AI user-agent group (classic) | Ships by default — all allowed |
| Bot access | Content Signals declare what AI may do with the content | Classic: `Content-Signal:` line in `robots.txt` · Next.js: only via the route-handler upgrade below | Classic ships `search=yes, ai-input=yes`; `ai-train` is left undeclared — the owner's call |
| Capabilities | MCP server card, agent-skills index, API catalog, OAuth discovery | — | **Deliberately absent — never fabricate these (see below)** |

## Auditing a live site (scored readiness report)

When the `kite-aeo` CLI is available (task sandboxes have it), audit with the platform's scored probe instead of fetching URLs by hand:

```
kite-aeo agent-readiness <application_id>
```

The platform live-probes the application's domain — its tracked domain, or the published URL when none is tracked — across the four dimensions above and returns a per-check report with one line of evidence per check. The platform also records every report in its observability stores, so reference the score and failing check ids; never paste the full report JSON into results or wiki pages.

- Read results with the table above. `capabilities` checks (MCP server card, agent-skills index, API catalog, OAuth) are informational on generated sites — the platform marks them not-applicable and excludes them from the score. Report them as informational, never as defects, and never "fix" them by fabricating files.
- In a task context, failing `discoverability` / `content` / `bot_access` checks are findings for your report or recommendations. Change site files only when the task explicitly asks for fixes — then use the mechanics sections below through the normal website-draft flow.
- The command fails when the application has no tracked domain and no published URL. An unpublished site cannot be probed — say so in your result instead of probing a preview or localhost URL.

## The AI crawler roster and what each bot does

Edits to AI access are per-intent, not per-file. Know what each user-agent controls before touching it:

| User-agent | Controls |
| --- | --- |
| `GPTBot` / `ClaudeBot` | OpenAI / Anthropic **model training** crawls |
| `OAI-SearchBot` / `Claude-SearchBot` | ChatGPT / Claude **search indexing** (being findable in AI search) |
| `ChatGPT-User` / `Claude-User` / `Perplexity-User` | **On-demand fetches** when a person asks the assistant to read this site |
| `PerplexityBot` | Perplexity answer-engine indexing |
| `Google-Extended` | Gemini training/grounding (does **not** affect Google Search ranking) |
| `Applebot-Extended` | Apple foundation-model training (does **not** affect Siri/Spotlight) |
| `Meta-ExternalAgent` | Meta AI training/indexing |
| `Amazonbot` | Alexa/Rufus answers |
| `DuckAssistBot` | DuckDuckGo AI answers |
| `CCBot` | Common Crawl corpus (feeds many model trainers) |

## Translating user intent into policy edits

- **"Make the site AI-ready" / "optimize for AI search" (default posture)** — verify the shipped state is intact: AI crawlers allowed, `Sitemap:` absolute, `/llms.txt` present and current. Fix drift; add nothing exotic.
- **"Block AI training but stay visible in AI answers"** — disallow the training crawlers (`GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `Meta-ExternalAgent`, `CCBot`); keep search/on-demand agents (`OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`, `Claude-User`, `PerplexityBot`, `Perplexity-User`, `Amazonbot`, `DuckAssistBot`) allowed. On classic sites also set `Content-Signal: ai-train=no, search=yes, ai-input=yes`.
- **"Block all AI"** — disallow every bot in the roster and set `Content-Signal: ai-train=no, search=yes, ai-input=no`. Warn the user first: this removes the site from AI answers and directly conflicts with any AI-visibility (AEO) work the team is doing. Never leave `search=no` unless the user explicitly wants out of search engines too.
- **A readiness audit flagged a failing check** — fix only the flagged dimension using the table above; do not bolt on unrelated standards to chase a score.

## Mechanics per framework

### Next.js sites (`src/app/robots.ts`)

The template ships a typed metadata route with a `*` rule plus an `AI_CRAWLERS` rule block. To restrict a bot, move it out of `AI_CRAWLERS` into its own rule with `disallow: '/'`:

```ts
rules: [
  { userAgent: '*', allow: '/', disallow: '/api/' },
  { userAgent: AI_CRAWLERS, allow: '/', disallow: '/api/' },
  { userAgent: ['GPTBot', 'ClaudeBot', 'CCBot'], disallow: '/' }, // training opt-out
],
```

Never replace `robots.ts` with a static `public/robots.txt` — the static file cannot compute the absolute `Sitemap:` URL, and crawlers silently ignore relative `Sitemap:` lines.

**Content Signals on Next.js** (only when the user asks to declare AI-usage preferences): the typed metadata route cannot emit a `Content-Signal:` line. Replace `src/app/robots.ts` with a route handler at `src/app/robots.txt/route.ts` (delete `robots.ts` in the same change — the two conflict):

```ts
import { getBaseUrl } from '../../lib/site-url';

export const dynamic = 'force-static';

export function GET(): Response {
  const body = [
    'User-agent: *',
    'Allow: /',
    'Disallow: /api/',
    '',
    'Content-Signal: ai-train=no, search=yes, ai-input=yes',
    '',
    `Sitemap: ${getBaseUrl()}/sitemap.xml`,
    '',
  ].join('\n');
  return new Response(body, {
    headers: { 'Content-Type': 'text/plain' },
  });
}
```

Carry the AI-crawler rule groups from the old `robots.ts` into the text body, and set the `Content-Signal` values to match the user's stated policy.

### Classic HTML sites (`frontend/public/robots.txt`)

A plain text file that ships the `*` rule, a `Content-Signal: search=yes, ai-input=yes` line, and the named AI user-agent group. Edit directives directly. Keep the `Sitemap:` line last and absolute — the publish step rewrites its URL to the connected domain.

## Never fabricate capability standards

Generated Kite sites have **no MCP server, no public API, no agent-skills documents, no OAuth-protected resources, and no agent payment rails**. Do not create:

- `/.well-known/mcp/server-card.json` or `/.well-known/mcp.json`
- `/.well-known/agent-skills/index.json`
- `/.well-known/api-catalog`
- OAuth discovery metadata (`/.well-known/oauth-authorization-server`, `/.well-known/oauth-protected-resource`)
- Payment endpoints (x402 responses, commerce protocol manifests)

A fabricated capability file is worse than a missing one: agents read it, act on it, and fail against endpoints that do not exist. These checks are allowed to fail on a readiness report. If the user insists on one of these, tell them it requires a real backing service that generated sites do not have, and stop there.

## Verify before finishing

1. `robots.txt` renders with the intended rule groups and an absolute `Sitemap:` URL (on Next.js, check the route output, not just the source).
2. `sitemap.xml` covers every current route — if routes changed in this edit, extend it (Next.js `src/app/sitemap.ts`) or load `website-sitemap-management` (classic).
3. `/llms.txt` still reflects the site — if pages, titles, or positioning changed in this edit, load `website-aeo-metadata-management` and regenerate it.
4. If you restricted any AI access, restate to the user exactly what is now blocked and what stays visible, in one sentence.
