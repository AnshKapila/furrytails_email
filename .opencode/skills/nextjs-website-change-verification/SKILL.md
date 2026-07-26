---
name: nextjs-website-change-verification
description: >
  Use this skill when a newly generated or remixed Next.js iteration needs a
  full readiness check before it is marked complete — for example after "build
  a new design", "remix this version", or a repair to a failed generation. Use
  `website-change-verification` for targeted visible edits; simple incremental
  code edits follow the host prompt's normal validation.
mode: sandbox
---

# qa

Runs `validate_files.py <iter>`: executes `pnpm typecheck` from the iteration
root, scans generated source for known Next.js runtime-blocking patterns
(including invalid late `@import` rules in `globals.css`), then smoke-renders
the homepage once. On a clean pass it also detaches a background QA scan
(collision, clipping, contrast, blocked interaction) against the running dev
server. That scan is reporting-only telemetry: the verdict returns before it
finishes, its findings are logged and written to JSON + interactive HTML
reports under `docs/qa/`, and they never fail the verdict or require action
from you.

## Validate

```bash
python3 .opencode/skills/nextjs-website-change-verification/scripts/validate_files.py
```

Invoke via the `bash` tool with `timeout: 600000` (10 min). No arg needed — the
iteration id (`iter1`, `iter2`, `iter3`) is read from the `ITERATION_ID` sandbox
env var. Pass it as a positional arg only to override (standalone/testing). The
path is relative to the agent's run dir, where the skill tree is staged — not
the app root.

### Validate output

Stdout: one line of JSON.

```json
{
  "status": "success" | "failed" | "error",
  "issues": [{"code": "tsc-error | build-error | build-timeout | css-import-order | server-component-event-handler | server-component-browser-global | dev-server-error | ...", "location": "src/app/page.tsx:14:5", "hint": "..."}],
  "iteration_id": "iter1"
}
```

- `issues` — flat list combining typecheck errors and static source checks. Background QA scan findings never appear here (reporting-only, see above).

Top-level `status` values:
- `success` — typecheck clean and no blocking static/runtime issues; the background QA scan has been detached.
- `failed` — typecheck errors, static source issues, or a preview that crashes when rendered (`dev-server-error`, with the captured 500 response body in the hint). `issues` contains actionable findings.
- `error` — validation could not run: a preflight problem (missing iter dir, pnpm/`next` not installed). Not fixable by editing website code — exit, do not retry.

Let the platform manage the dev server lifecycle: when the preview is broken, fix the generated code and re-validate — HMR/autorestart picks the fix up on its own, so there is never a reason to restart or re-permission the server yourself.

## Handling the verdict

- **`success`** — communicate the iteration is ready and return control.
- **`failed`** — fix and re-validate:
  - For `tsc-error` issues: edit the affected file and re-validate.
  - For `build-error`: `next build` failed on code that `tsc --noEmit` accepted. This may be a SWC parse error (e.g. mismatched JSX tags), a static-prerender failure, or another build-time issue. The hint carries the build output tail — read it for the file and error, fix the cause, then re-validate.
  - For `build-timeout`: the production build timed out. This usually means the iteration has too many pages or a non-terminating import cycle. Simplify and re-validate.
  - For `css-import-order`: move all `@import` statements before other rules in `src/app/globals.css`. Prefer deleting raw Google Fonts imports and loading fonts via `next/font/google`.
  - For `server-component-event-handler`: the file has a JSX DOM event handler in a Server Component. Add `'use client'` as the first statement in that file, or move the interactive form/button logic into a child Client Component, then re-validate.
  - For `server-component-browser-global`: the file reads browser-only globals (`window`, `document`, `localStorage`, `sessionStorage`, or `navigator`) in a Server Component. Add `'use client'` as the first statement in that file, or move the browser-dependent logic into a child Client Component, then re-validate.
  - For `dev-server-error`: the preview serves a 500 when rendered (the hint carries the captured response body) — a runtime fault `pnpm typecheck` missed (a config/middleware syntax error, a bad import, a throwing server component, a request-time Payload/DB read). Read the dev server logs (`pm2 logs nextjs-$ITERATION_ID --lines 50 --nostream --err`) for the full stack, fix the cause in the generated code, then re-validate. Do not restart or re-permission the dev server — fixing the code lets it recover via HMR/autorestart.
- **`error`** — exit non-zero immediately; do not retry.
