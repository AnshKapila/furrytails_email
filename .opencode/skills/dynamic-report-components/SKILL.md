---
name: dynamic-report-components
description: >
  Use this skill when a report should include live data that stays current
  every time it is opened — a chart, table, single metric, or list, including
  derived numbers like gaps, ratios, or computed rankings. E.g. "give me a
  report on GitHub stars for these repos", "chart signups from our
  analytics", "show current open issues in a table", or any report where the
  reader should see today's numbers, not the numbers from when you wrote
  them. Works in task results and chat replies, for any data reachable
  through the team's connected integrations. For static or historical
  numbers, write a normal markdown table or list instead.
mode: sandbox
---

# Dynamic Report Components

Embed live data in report markdown. You register the data query once with
`kite-report-queries`; the platform replays it every time someone views the
report, so the component always shows current numbers. The markdown itself
stays static — each component tag carries a static fallback for surfaces
that can't render live data.

Works anywhere your markdown is rendered: task results (`set-task-result`),
chat replies, and initiative dashboards (users can pin your components
there). Slack replies render tags natively too — charts become real Slack
charts, tables become sortable data tables — so use tags for Slack-bound
data instead of hand-drawing anything. Two artifacts make one component
work, and both are required:

1. A **registered query** — a spec you write and register via the
   `kite-report-queries` CLI, which returns the query id.
2. A **component tag** in your markdown, referencing that id.

## Step 1 — verify the query works

Any tool the team's tool gateway can execute can be pinned — `native:*`
platform tools, provider-namespaced actions (for example `composio:*` or
`pipedream:*`), and `mcp:*` tools for the team's connected apps and MCP servers
(discover and run them per `tool-discovery-execution`). Before pinning anything,
run the exact call yourself and confirm the fields you need exist.

For GitHub, use the CLI:

```sh
kite-github api GET /repos/vuejs/vue
```

For a connected app (analytics, CRM, sheets, …), run the tool through the
`kite-integrations` CLI (it resolves scope, token, and URL from the env) with the
same `tool_name` and `params` you intend to pin:

```sh
kite-integrations execute composio:POSTHOG_GET_INSIGHT '{"insight_id": "..."}'
```

Save the response — the `result` object in it is exactly what the replay will
hand to your extraction paths or transform later, so shape your paths against
it (see the envelope note in the rules below).

Never pin a redirecting call, even though it seems to work now. Only pin what
you verified — a redirect response does not count as verified. If the probe
answers with a redirect (e.g. GitHub HTTP 301 for a moved repo), re-probe the
canonical path it points to and pin that instead.

## Step 2 — write and register the query spec

Write a spec file to a scratch location OUTSIDE your artifacts directory
(e.g. `/tmp/repo-stats.json`) — it is only CLI input; once `create` returns
an id the registry row is the source of truth, and a spec left in artifacts
shows up as a useless file in the user's task Files list. The spec produces
a small table — named **columns**, plus **rows** — that any component can
render. Two modes:

**Row per call** (compare a few things): each call yields one row, named by
its `label` (which becomes an implicit leading `label` column):

```json
{
  "version": 1,
  "calls": [
    { "label": "react", "tool": "native:github-api-request",
      "params": { "method": "GET", "path": "/repos/react/react" } },
    { "label": "vue", "tool": "native:github-api-request",
      "params": { "method": "GET", "path": "/repos/vuejs/vue" } }
  ],
  "extract": {
    "columns": [
      { "name": "stars", "path": "$.body.stargazers_count" },
      { "name": "forks", "path": "$.body.forks_count" }
    ]
  },
  "ttl_seconds": 300
}
```

**Rows from one call** (a list the API returns): exactly one call; `rows`
selects the array, column paths resolve per element:

```json
{
  "version": 1,
  "calls": [
    { "tool": "native:github-api-request",
      "params": { "method": "GET", "path": "/repos/react/react/releases",
                  "query": { "per_page": "5" } } }
  ],
  "extract": {
    "rows": "$.body[*]",
    "columns": [
      { "name": "name", "path": "$.name" },
      { "name": "published", "path": "$.published_at" }
    ]
  },
  "ttl_seconds": 300
}
```

The same two modes work for connected apps — only the tool name and the
response envelope change. A `composio:*` tool's value lives under `$.data.`
(here, one analytics call returning all variants of an experiment):

```json
{
  "version": 1,
  "calls": [
    { "tool": "composio:POSTHOG_GET_EXPERIMENT",
      "params": { "experiment_id": "cta-color-test" } }
  ],
  "extract": {
    "rows": "$.data.results.variants[*]",
    "columns": [
      { "name": "variant", "path": "$.key" },
      { "name": "conversion", "path": "$.conversion_rate" }
    ]
  },
  "ttl_seconds": 900
}
```

(Discover the real tool name and params per `tool-discovery-execution` — do
not copy this one blind.)

Then register it:

```sh
kite-report-queries create /tmp/repo-stats.json
```

The response is `{"id": "<uuid>"}` — that id goes into your component tags.
`create` validates the spec grammar AND dry-runs the query: it executes your
calls once and runs the extraction/transform against the real results, so a
path that doesn't resolve fails here as a 422 naming the failing path — fix
the spec and re-run; nothing was stored. A `201` therefore means the query
verifiably works. Registering the same file twice creates two independent
queries, so register once and reuse the id across tags.

Rules:

- Each call names its own `tool` — any `native:*`, provider-namespaced, or `mcp:*` tool the
  gateway executes. One spec may mix providers (a GitHub number next to an
  analytics number), but any failed call fails the whole component.
- **Pin reads only, never writes.** Opening the report replays the pinned
  calls, so a pinned write (`create`, `send`, `update`, `delete`, …) would
  fire on every view by every viewer. Only pin tools that fetch data (GET
  requests, `get`/`list`/`search`/`query`-style actions). This has no
  exceptions: if a request seems to need a write to produce its data,
  don't build the component — explain why instead. This read-only constraint
  takes absolute priority over completeness.
- Extraction paths use a tiny subset of JSONPath: `$` root, dotted field
  names, `[*]` to descend into a list (e.g. `$.body.items[*].count`), and
  an all-digit segment as a list index (e.g. `$.body.results.0.value`).
  Nothing else — no filters, slices, computation, or expressions. Every
  column path must land on a scalar (string/number/bool/null), never an
  object.
- Need a **computed** value (delta, ratio, sum, sort) the API doesn't return
  directly? Use a transform (next section) instead of `extract`.
- **Paths resolve against each tool's response envelope**, which differs by
  provider: `native:github-api-request` wraps the GitHub payload as
  `{"status": ..., "body": ...}` (paths start `$.body.`); `composio:*` tools
  return `{"data": ..., "successful": ..., "error": ..., "log_id": ...}`
  with the provider's value in `data` (paths start `$.data.`); legacy
  `pipedream:*` tools return `{"exports": ..., "ret": ...}` with the provider's
  value in `ret` (paths start `$.ret.`); `mcp:*` tools return whatever shape that MCP
  server defines. Don't guess — shape paths against the `result` object you
  saved in Step 1.
- In row-per-call mode the **same column paths apply to every call**, so
  mixing providers with different envelopes in one `extract` spec won't
  resolve — use a transform for cross-provider components (it sees each raw
  result and can index into each shape).
- `ttl_seconds` (default 900) is how long the platform caches a fetch before
  hitting the provider again. Rule of thumb: keep the default 900 unless the
  user asks for updates within five minutes, in which case use 300. Don't go
  below 300 — lower values multiply provider calls.
- Keep specs small: every call replays against the live provider when a
  viewer opens the report, so each extra call adds latency and a failure
  point. Aim for 3–5 calls and 10–50 rows; avoid 100+ rows. When smallness
  conflicts with what the user asked to see, completeness takes priority:
  trim by aggregating or letting one call return more rows, never by omitting
  requested data.
- Several components may share one query id (e.g. a chart and a table of the
  same data) — the cache collapses them into one upstream fetch.

## Step 2b — transforms, for values the API doesn't return

When the numbers you want are *derived* (react's lead over vue, stars per
fork, a top-5 sorted by a computed score), declarative `extract` can't help —
register a **transform script** with the spec. Omit `extract` from the spec:

```json
{
  "version": 1,
  "calls": [
    { "label": "react", "tool": "native:github-api-request",
      "params": { "method": "GET", "path": "/repos/react/react" } },
    { "label": "vue", "tool": "native:github-api-request",
      "params": { "method": "GET", "path": "/repos/vuejs/vue" } }
  ],
  "ttl_seconds": 300
}
```

and write the transform — **JavaScript**, a single pure function, in its own
scratch file outside artifacts (e.g. `/tmp/star-gap.js`; like the spec, it is
CLI input only — the registry keeps the source after `create`):

```js
function transform(results) {
  const react = results[0].body.stargazers_count;
  const vue = results[1].body.stargazers_count;
  return {
    columns: ["metric", "value"],
    rows: [
      { metric: "gap", value: react - vue },
      { metric: "ratio", value: Number((react / vue).toFixed(2)) }
    ]
  };
}
```

then register both together:

```sh
kite-report-queries create /tmp/star-gap-spec.json /tmp/star-gap.js
```

Contract and limits:

- `results` is the array of raw gateway responses, one per call, in spec
  order. Return `{columns: [...], rows: [{...}]}` — same shape `extract`
  produces. Cells must be scalars.
- The script runs **sandboxed on the platform**: no network, no filesystem,
  no environment, a 2-second CPU budget, 64 MB of memory. `fetch`,
  `require`, `process`, and module imports do not exist — pure computation
  only. Exceeding either budget (or throwing) kills the script and the
  component renders its fallback, so keep transforms to simple arithmetic
  and sorting over the fetched rows.
- `extract` (in the spec) and a transform file are mutually exclusive —
  provide exactly one.
- **Prefer `extract` whenever it suffices**: if both would work equally well, always use
  `extract` — it is auditable data, cheaper, and can't fail at runtime.
  Reach for a transform only when the value genuinely must be computed and
  `extract` cannot produce it.
- Test the logic before registering: run your calls as in Step 1, then run
  the function against the saved responses with `node` in the sandbox.

## Step 3 — embed component tags in your markdown

In a task result (`set-task-result`) or directly in a chat reply. Use the id
that `create` returned. Exactly four tags exist — `<kite-chart>`,
`<kite-table>`, `<kite-metric>`, `<kite-list>` — a closed set: renderers
treat any other `kite-` tag as unsupported and show only its fallback text,
so never invent variants (no `<kite-graph>`, `<kite-piechart>`, …). Pick the
component that fits the data:

```markdown
<kite-chart query="8f2e41a0-…" type="bar" y="stars" title="GitHub stars">
Star counts as of writing: react ~238k, vue ~210k.
</kite-chart>

<kite-table query="8f2e41a0-…" title="Repository stats">
As of writing: react — 238k stars, 48k forks; vue — 210k stars, 33k forks.
</kite-table>

<kite-metric query="8f2e41a0-…" value="stars" title="react stars">
~238k stars as of writing.
</kite-metric>

<kite-list query="d41c77b2-…" title="Latest releases" primary="name" secondary="published">
Latest release as of writing: 19.1.0.
</kite-list>
```

Attributes:

- `query` — the id returned by `kite-report-queries create` (required, all
  tags).
- `title` — short caption (all tags).
- `<kite-chart>`: `type` — `bar` (default) or `line`; `x`/`y` — column names
  for the axes (default: first column / first numeric column).
- `<kite-metric>`: `value` — column holding the number (default: first
  numeric column); reads the **first row** only.
- `<kite-list>`: `primary`/`secondary` — item text and trailing value
  columns (default: first and second columns).
- `<kite-table>` renders all columns; no extra attributes.
- The tag's **inner text is the static fallback**: write the actual numbers
  you fetched in Step 1, so the report still informs when live data can't
  load (integration disconnected, surface without live rendering). Never
  leave it empty.

## Before returning

Validate that the query spec is valid JSON with `version`, `calls`, exactly
one of `extract` or a transform file, and `ttl_seconds`; every component tag
uses an id returned by `kite-report-queries create`; and every tag has a
non-empty static fallback containing the actual Step 1 values.

## Gotchas

- **No connection, no live component.** The replay runs on the team's
  connections. If Step 1 fails with `provider_not_connected` (409), skip the
  live component for that data and report plain numbers — it would only ever
  render its fallback. Never pin a call you couldn't run yourself.
- Any failed call fails the whole component (fallback renders); there is no
  partial data. Don't mix a flaky query into a spec other components depend
  on.
- A registered query is permanent and team-visible: anyone on the team who
  can see the report gets its live data, and users may pin your components
  to an initiative dashboard where they keep refreshing indefinitely. Pin
  stable, canonical calls.
