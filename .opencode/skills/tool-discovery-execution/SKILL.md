---
name: tool-discovery-execution
description: >
  Use this skill to discover or invoke team integrations from the full
  provider-routed catalog, or platform data/action tools. Examples include
  sending Slack, creating a GitHub issue, adding a sheet row, searching Notion,
  using LinkedIn, Reddit, Exa, Apollo, Apify, or Printify, listing available
  integrations, answering questions from team data, and reading a private app
  link. Also use it when another skill requests an integration-backed action.
  For public web research use web-research; for a public website supplied as a
  design reference use website-design-content-extraction.
mode: sandbox
notification_title: "Using integrations"
agent_policies:
  orchestrator: orchestrator-policy.md
---

# tool-discovery-execution

Use the `kite-integrations` CLI (via the `bash` tool) to call the tool gateway. The gateway is team-scoped: it exposes the team's connected integrations plus the platform integrations. The CLI resolves the scope (`$TEAM_ID` if set, otherwise `$APPLICATION_ID`), token, and URL from the env — you never handle auth or identifiers yourself. In a sandbox without `kite-integrations` on PATH (e.g. the website orchestrator's), use the raw-endpoint fallback at the end of this section instead — same requests, hand-built.

Success means the user's request is fulfilled: the needed data is retrieved, the requested action runs on the target system, or the question is answered from available tools. After resolving access as described below, workflow on the chosen integration path is always **search → describe → execute**:

1. `search` — find what's available (connected integrations, platform integrations, matching tools).
2. `describe` — get a tool's input schema. Run this before the first execution of any tool. Use only parameter names that appear verbatim in `input_schema` or `configurable_props`; do not infer, abbreviate, or substitute similar-sounding names.
3. `execute` — run it.

For a multi-step request, first state a checklist with one item per external action, naming its app/tool and what it supplies to the next step; mark each item complete as you execute it.

## Integrations and tools — the vocabulary this skill uses

An **integration** is a provider — Mixpanel, Notion, Reddit. A **tool** is one function an integration exposes — read a report, run a query, create a page. Integration access comes in two kinds, and a brand can expose both when its public-data and account-action routes differ. Every tool name carries its kind and integration:

- **Connected integrations** — the team authenticated them, so their tools act on the *team's own account and data*. They appear in `connected_apps`, and their tools are named `composio:<tool_slug>` for integrations served by the default broker, `pipedream:<component_key>` for configured overrides such as `linkedin_ads`, or `mcp:<server_slug>/<tool>`. Broker routing is per integration, not per team; always use the names returned by `search`.
- **Platform integrations** — served through Kite-owned adapters. Most need no user authentication; Slack and GitHub are team-connected exceptions that use Kite's first-party bot/App installs. They appear in `platform_integrations`, and their tools are named `native:<integration>-<tool>` — e.g. Reddit is one platform integration whose tools include `native:reddit-list-tools` and `native:reddit-call-tool`. Each `tools[]` entry's `app` field names its integration. Kite's Slack connector (`native:slack-*`) acts through the team-level Kite bot install, and `native:github-api-request` acts through the team's Kite GitHub App. Neither brand has a brokered copy.

Native tools listed with an `endpoint` (e.g. image generation) are the same tools documented in their own skills — prefer those skills' recipes; this gateway lists them for discovery.

## Choose tools for the task — connected first, then platform, then offer to connect

Understand the task before picking any tool: list the data and actions it needs. A real task often needs **several tools across several integrations**, and one integration rarely covers everything — a connected CRM may hold the contacts while a platform integration supplies the enrichment and a not-yet-connected ads account holds the spend data. Read each integration's description (`connected_apps`, `platform_integrations`, and `tools[].description`) and map every need to the integration that actually provides it — never to the brand you find familiar.

Then, for **each** need, pick in this order:

1. **A connected integration whose tools cover it.** The team connected it because their data and configuration live there — use it even when a platform integration overlaps (their Semrush account beats the platform's DataForSEO for *their* rankings history).
2. **A platform integration.** No connection exists to prefer, and it costs the user nothing — use it rather than asking the user to connect an equivalent.
3. **A connectable integration the team hasn't connected.** Only for needs the first two can't serve: follow **Recipe: connect an unconnected integration** — do the parts you can already do, and offer the connect for the rest.

Cover the whole task, not just the first need you can serve: run the connected and platform parts now, and batch **every** missing connection into one message (see the multi-step-flow rule in the connect recipe) — never discover gaps one turn at a time.

**Exa, Apollo, Apify, and Printify are platform-only integrations.** When a task names one of these brands or supplies one of their URLs, skip `resolve`, do not look for it in `connected_apps`, do not pass it as the `app` argument, and never run `catalog-search`, `connect`, or a `composio:*` or `pipedream:*` tool for the same brand. Brokered copies are intentionally absent from the agent gateway. Start with a bare `search`, then use the exact `native:*` recipes under **Platform integrations** below.

**GitHub is native-only but team-connected.** It never appears in `connected_apps` and must not be passed to `kite-integrations connect`. Use `native:github-api-request` / `kite-github` for repository and account actions. A `409 provider_not_connected` means the team must install the Kite GitHub App from **Integrations** before the action can run.

**LinkedIn has separate read and account-action routes.** Use the platform tools for public profiles, companies, posts, jobs, and search. Those tools cannot act as the user: when the request needs their LinkedIn account (for example publishing a post), or the user explicitly asks to connect LinkedIn, check `connected_apps` and follow the normal resolve/connect recipe for the provider-routed `linkedin` app. Never claim LinkedIn is already connected merely because the read-only platform integration is available.

**Reddit has separate research and account-action routes.** Use the platform tools for public communities, posts, comments, users, and search. Those tools cannot act as the user: when the request needs their Reddit account (for example publishing or replying), or the user explicitly asks to connect Reddit, check `connected_apps` and follow the normal resolve/connect recipe for the provider-routed `reddit` app. Never claim Reddit cannot be connected merely because the research integration is available.

A question only the team's data can answer ("why isn't my website converting?", "how are we ranking?") is a tool request with no integration named. Decide what data answers it, then apply the same ladder: answer from connected integrations and platform integrations first, and when a needed source lives in an unconnected account (their analytics, ads, CRM), follow **Recipe: connect an unconnected integration** — report what you can already see and what the connection adds, rather than answering from general knowledge alone.

**Slack is native, not brokered.** To post to Slack use the `kite-slack` CLI. It acts as the Kite bot and never appears in `connected_apps`, so don't search for or expect `composio:slack*` or `pipedream:slack*` tools.

**GitHub uses one first-party App for account actions and repository sync.** Use `native:github-api-request` / `kite-github`; do not search for `composio:github*` or `pipedream:github*` tools. The Integrations page owns install, approval, repository-access configuration, and disconnect.

## Resolve access first — don't make the user choose the method

`resolve` applies the ladder above to one named service. Whenever a task needs to reach an external service other than the four platform-only integrations above — log into a site, pull data from it, post to it — **start by resolving how to reach it, then act in the same turn.** Do not ask the user "should I use the integration or the browser?" or wait to be told to check a login; decide from what's already available.

```bash
kite-integrations resolve x.com        # a domain…
kite-integrations resolve notion       # …or an app name
```

It returns `recommendation` plus a `next` field with the exact command to run. Act on it, best path first:

| `recommendation`          | What it means → what you do |
| ------------------------- | --------------------------- |
| `use_integration`         | The app is already connected. Go straight to `search`/`describe`/`execute` — no browser, no connect link. |
| `use_browser_login`       | A saved browser login exists for this service. Use the **browser-session** skill with `--profile <label>` — it's already logged in; do **not** ask the user to log in again unless it has expired. |
| `offer_integration_connect` | Not connected and no saved login, but the integration catalog supports the app. Follow **Recipe: connect an unconnected integration** — mint the link, hand back one `<connect-cta>`. |
| `offer_mcp`               | A custom/platform MCP server can serve it. `kite-integrations connect <slug>` and hand back the `<connect-cta>` (or tell the user they can add a custom MCP server in Integrations). |
| `use_native_tools`        | Kite already serves this brand natively — no login or connect needed. Go straight to `search`/`describe`/`execute` on the `native:<slug>-*` tool named in `next`; do **not** open a browser session for it. |
| `offer_browser`           | Nothing native and no saved login. Offer a **browser-session** handoff (the browser-session skill), or a custom MCP if the service has one. |

The order is deliberate: a connected integration beats a browser login (more robust), a **saved** browser login beats asking the user to connect a fresh integration (zero friction), and only when nothing is ready do you offer — the integration catalog first, then a custom MCP. Below those offers, a brand Kite serves natively (`use_native_tools`) beats scraping it, and the browser is the last resort. Native ranks below the connect offers on purpose: dual-mode brands (Reddit and LinkedIn) keep their connectable account offered for write/account actions the read-focused native tools don't cover. Resolve is read-only: it recommends, you run the follow-up command it names. If `resolve` isn't on PATH (an app/website sandbox with no `TEAM_ID`), fall back to the manual sequence: bare `search` (connected?) → `kite-browser profiles` (saved login?) → `catalog-search`/`connect` or a browser handoff.

## Gotchas

- **Always source app slugs from `connected_apps`.** Copy `connected_apps[].name_slug` verbatim; never substitute a brand name. Slugs may be version-suffixed, and connections are granular (`google_sheets`, `google_drive`, and `google_docs` are distinct). Use the returned slug unchanged in `app` and tool names.
- **Quote the params JSON in single quotes.** The params argument is one JSON object string (`'{"title": "…"}'`); double-quoting it invites shell expansion inside the JSON.
- **Search with one word at a time.** Use the most specific noun first (e.g. `message`, not `send message`); provider search may AND multi-word queries. If that returns nothing, try one related or broader noun.
- **Pass default `timeout: 120000` to bash for `execute`.** If provider documentation gives a longer expected duration, use twice that duration in milliseconds (a documented 5-minute action gets `600000`). If it times out, surface the timeout error instead of retrying blindly.
- **Results are real side effects — never re-run a succeeded action.** A successful write (a `kite-slack send`, a `kite-github api POST …`, or a `composio:*`/`pipedream:*` create) really changes data. Do not re-run it to verify or retry it.
- **Validate parsed responses before acting.** Required fields must be present, success responses must have the documented status/result shape, and errors must carry the documented `detail.code` and `detail.message`. Treat a missing `detail.retryable` as `false`. Surface malformed responses instead of acting on partial data.
- **Reduce large results in the sandbox before they reach you.** Whatever your `bash` command prints to stdout enters your context. Project with `jq` (or `python3`), push filters to the provider, and use `per_page` ≤ 30 so pages stay below 50 KB. If a response still exceeds 50 KB, project fewer fields before printing it; truncated output is not valid JSON.

## Search

List connected integrations, platform integrations, and matching tools. **Always start with a bare request** (no `query`, no `app`) — it returns `connected_apps` (the connected integrations, and the source of the valid `app` slugs) plus `platform_integrations` and every platform tool, so one call shows everything rungs 1 and 2 of the ladder can use. If `connected_apps` is empty, the team has not connected any third-party integrations. When the integration the user needs is in neither list, do **not** stop at "it's not connected" — follow **Recipe: connect an unconnected integration** below to hand the user a connect link.

```bash
kite-integrations search
```

Read the `name_slug` you need from `connected_apps`, then scope a second search to that exact slug:

```bash
kite-integrations search "page" notion
```

- `query` — optional keyword (1st arg); searches tool names and descriptions.
- `app` — optional connected-app slug (2nd arg). Omitting both skips per-app action search.

Response:

```json
{
  "team_id": "…",
  "connected_apps": [
    {
      "name_slug": "notion",
      "name": "team-workspace",
      "account_id": "apn_…",
      "healthy": true
    }
  ],
  "platform_integrations": [
    {
      "name_slug": "reddit",
      "name": "Reddit",
      "description": "Reddit posts, comments, communities, search, and user activity."
    }
  ],
  "tools": [
    {
      "name": "composio:NOTION_CREATE_PAGE",
      "provider": "composio",
      "app": "notion",
      "description": "Create a page",
      "connected": true,
      "invocation": "gateway",
      "endpoint": null
    },
    {
      "name": "native:reddit-list-tools",
      "provider": "native",
      "app": "reddit",
      "description": "Discover Monid data endpoints for Reddit…",
      "connected": true,
      "invocation": "gateway",
      "endpoint": null
    }
  ]
}
```

## Describe

```bash
kite-integrations describe composio:NOTION_CREATE_PAGE
```

Pass `tool_name` exactly as it appeared in a search result's `tools[].name` — do not retype, change case, or "correct" it. For `composio:*` tools, `input_schema` is the tool's JSON input schema. For `pipedream:*` tools, `input_schema.configurable_props` lists the params: `name` is the key to send, `optional: true`/`default` means skippable, everything else is required. Props with `remoteOptions: true` accept raw values (e.g. a channel name like `#general`) — there is no option-picker here. For `native:*` tools it's a standard JSON schema.

## Execute

```bash
kite-integrations execute composio:NOTION_CREATE_PAGE \
  '{"parent_page_id": "…", "title": "Weekly update"}'
```

- `tool_name` — exactly as it appeared in a search result (1st arg).
- `params` — a JSON object string (2nd arg, optional when the tool takes none).

Params above ~100 KB (e.g. base64 artwork) exceed the shell's per-argument limit — write the JSON object to a file and pass `@` plus the path instead:

```bash
kite-integrations execute native:printify-upload-artwork @/tmp/artwork-params.json
```

## Raw-endpoint fallback (no `kite-integrations` on PATH)

The CLI wraps three POST endpoints under
`$BACKEND_API_URL/api/v1/internal/tool-gateway/tools/` — `search`, `describe`,
`execute` — authed with `Authorization: Bearer $INTERNAL_API_TOKEN`. Bodies
mirror the CLI args, plus the scope field the CLI fills in for you: exactly one
of `"team_id": "$TEAM_ID"` or `"application_id": "$APPLICATION_ID"` (whichever
is set — both is rejected). On the `team_id` path also send
`-H "X-Sandbox-Session-Token: $KITE_SANDBOX_TOKEN"` — the gateway binds the call
to your session's own team and returns 403 for a `team_id` that isn't yours; the
`application_id` path omits this header:

```bash
curl -sS -X POST "$BACKEND_API_URL/api/v1/internal/tool-gateway/tools/execute" \
  -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  -H "X-Sandbox-Session-Token: $KITE_SANDBOX_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- << EOF
{
  "team_id": "$TEAM_ID",
  "tool_name": "composio:NOTION_CREATE_PAGE",
  "params": { "parent_page_id": "…", "title": "Weekly update" }
}
EOF
```

`search` takes optional `"query"` and `"app"`; `describe` takes `"tool_name"`.
Use `<<EOF` so scope variables expand in the JSON body; a quoted terminator
would send the literal string `"$TEAM_ID"` and cause a 422 UUID-parse error.

Response: `{ "tool_name": "…", "status": "success", "result": {…}, "latency_ms": 1843 }`. For `composio:*` tools the provider's return value is nested in `result.data`; for `pipedream:*` tools it is nested in `result.ret`; `native:*` tools return their own result shape directly in `result`. Native Slack and GitHub use the `kite-slack` / `kite-github` CLIs below.

## Platform integrations

`native:*` tools are the platform integrations' tools: they run through Kite-owned adapters and never get a broker connect link. Most are always available; Slack and GitHub require their first-party team installs. Their place in the ladder: when no relevant connected integration covers the need, use the platform integration rather than asking the user to connect an equivalent (e.g. keyword and competitor data via the DataForSEO catalog when no SEO account is connected) — a relevant **connected** integration still comes first, because the team's own account holds their data and configuration. Ask the user to connect only for data or actions that live in the team's own account (their analytics, their CRM records, their docs). The bare search lists them all; `describe` → `execute` them like any other tool. Most belong to an owning skill or CLI — when you hold the owner, use its recipes instead of raw `execute`:

- `native:research-*` — web search, page extract and scrape, brand tokens, page imagery (Firecrawl-backed) — owned by `web-research` (`kite-research` CLI).
- `native:images-*` — image generation, editing, background removal — owned by `images`.
- `native:dashboard-*` — publishing reports, dashboards, viewer sign-in, and team-wide report design rules — owned by `dashboard-building` (`kite-dashboards` CLI).
- `native:slack-*`, `native:github-api-request`, `native:integrations-*` — the `kite-slack`, `kite-github`, and `kite-integrations` recipes in this skill.
- `native:email-send` — send email as the team's own address; recipes live in the email skills when you hold them, otherwise `describe` → `execute` it directly.
- `native:crustdata-fetch-linkedin-profile` / `-posts` — a person's or company's public LinkedIn profile / recent original posts, given a LinkedIn URL. No owning skill; call directly.
- `native:brandfetch-brand` / `native:context-dev-company` / `native:pagespeed-audit` / `native:siftly-brand-research` — structured company data from platform datasources (brand identity, product catalog + site shape, Lighthouse scores, competitors/AEO) — owned by `company-deep-dive`.
- `native:printify-*` — team-scoped artwork, product, publishing, ordering, and blueprint operations — use the Printify recipe below.
- `native:clay-*`, `native:dataforseo-*`, and `native:{linkedin,reddit,exa,apollo,apify}-*` — dynamic **catalogs**, below.

**Catalogs.** Clay and DataForSEO expose their evolving hosted tool sets directly. Monid backs five narrower platform catalogs: **LinkedIn** (profiles, companies, posts, jobs, and search across available providers), **Reddit** (posts, comments, communities, and users), **Exa** (web search and page contents), **Apollo** (people/company search and enrichment), and **Apify** (specialized scraping and extraction actors). For a known LinkedIn URL that only needs a normalized profile or recent original posts, prefer the dedicated Crustdata tool; use the LinkedIn catalog for broader search, datasets, jobs, or provider choice.

Never guess catalog tool names or input fields. First execute `native:<catalog>-list-tools` with a focused 2–4 word noun phrase in `"query"`, then copy one returned `tools[].name` and read its `input_schema` and `price`. Execute `native:<catalog>-call-tool` with that exact name and the endpoint arguments **nested** in `params`. If discovery has no suitable match, refine the query once, then use the owning skill's fallback instead of forcing a mismatched endpoint.

```bash
kite-integrations execute native:dataforseo-call-tool \
  '{"tool_name": "<name from list-tools>", "params": { … }}'
```

The Monid payload may return `status: "RUNNING"` with a `runId` after bounded polling. Resume that same paid run by calling the same `native:<catalog>-call-tool` with the same `tool_name`, empty `params`, and `"run_id": "<runId>"`. Preserve the ID exactly; starting the tool again without `run_id` creates a new run and may charge twice.

Catalog calls are metered on the platform account. Prefer the least expensive suitable Monid result, start endpoint result limits at 10, and increase them only when the response returns all 10 and the user's question requires additional rows. Batch inputs when a tool accepts a list, and project large responses with `jq` (see the "Reduce large results" gotcha). A `503 gateway_not_configured` on any `native:*` tool means this environment lacks the platform credential: fall back per your skill's failure handling instead of retrying — this overrides the generic 503 row in _Errors_, which is for team integrations.

### Recipe: create and manage Printify products

Printify has fixed native operations rather than a dynamic catalog. Run `describe` before the first call so you have the current schema, then `execute` the exact tool:

- `native:printify-list-blueprints` — search products, inspect one blueprint's print providers, then inspect one provider's variant ids, prices, and print areas.
- `native:printify-upload-artwork` — upload a public image URL or base64 image and retain the returned artwork id. Prefer `url`; base64 params must be written to a file and passed as `@/path/to/params.json` (see _Execute_) — inline they exceed the shell's argument limit.
- `native:printify-create-product` — create a product using blueprint/provider/variant data and artwork ids returned by the upload tool.
- `native:printify-list-products` — list only products created for the current team through this gateway.
- `native:printify-publish-product`, `native:printify-update-product`, and `native:printify-order-product` — act only on products owned by the current team.

The safe creation order is **list blueprints → upload artwork → create product**. Never substitute an image id from another source: create and update reject artwork not uploaded for this team. Publishing, updating, and ordering reject product ids not created for this team. Ordering is a real paid side effect; use a stable caller-generated `external_id`, reuse it after an uncertain retry, and never repeat a successful order to verify it.

## Recipe: send a Slack message (`kite-slack`)

Slack posting goes through the platform-native Kite bot, not the team's generic integration provider, so it works without a broker connection — but it does require the team to have installed the Kite Slack bot from Team settings. The `kite-slack` CLI calls the tool gateway for you (scope, token, and URL are resolved from the env). Put generated message text in a quoted-heredoc file so newlines, dollar signs, and other shell characters arrive unchanged:

```bash
message_file=$(mktemp)
cat >"$message_file" <<'EOF'
*Weekly update*

Rankings improved for 12 keywords.
EOF
kite-slack send "#general" --text-file "$message_file"
rm -f "$message_file"
```

To reply inside an existing thread, pass the thread timestamp after the text file:

```bash
message_file=$(mktemp)
cat >"$message_file" <<'EOF'
Following up here 👇
EOF
kite-slack send "#general" --text-file "$message_file" "1718900000.123456"
rm -f "$message_file"
```

- `channel` — channel id (`C…`) or name (`#general`); both work for posting.
- `text` — the message. Use `--text-file <path>` for generated text; the positional form remains available for short static text.
- `thread_ts` *(optional)* — reply inside an existing thread instead of posting a new message.
- The message is attributed to **Kite** (the bot), not to a person. The result returns the posted message's `channel` and `ts`.
- `409 provider_not_connected` means the team hasn't installed the Kite Slack bot — tell the user to connect Slack in **Team settings**.
- `502 provider_error` with `Slack rejected the message: not_in_channel` (or `channel_not_found`) and `retryable: false` means the Kite bot isn't in that channel — tell the user to invite **@Kite** to it (`/invite @Kite` in Slack). Don't retry; it won't change until the bot is invited.

### Check channel access first (`kite-slack channel`)

When the user asks whether Kite can post somewhere, or before posting to a channel you're not confident the bot can reach, check it — never send a test message to find out:

```bash
kite-slack channel "#team-marketing"
```

Returns `{ channel_id, name, exists, is_member, is_private }`:

- `exists: true` — the channel is visible to the bot. `is_member: false` on a **public** channel is fine: the bot can post to any public channel without joining. On a private channel (`is_private: true`), `is_member` must be true to post.
- `exists: false` — no channel by that id/name is visible to the bot: either a typo, or a private channel the bot isn't in. If the user says the channel exists, ask them to run `/invite @Kite` in it, then check again.
- **Private channels can't be found by name** (the name lookup covers public channels only), so `exists: false` for a name the user insists on may be a private channel the bot is *already* in. Check it by channel id (`C…`/`G…`) if you have one; otherwise, once the user confirms the bot was invited, send directly — a `not_in_channel` error will still tell you if they were wrong.

### Change a channel's reply mode (`kite-slack reply-mode`)

Run this command whenever someone asks you to stop replying in a channel unless explicitly tagged (`tagged_only`), or to resume auto-replying in threads you're tagged into or started (`auto`). The ask is only fulfilled by running it — an acknowledgment without the command changes nothing:

```bash
kite-slack reply-mode "#team-marketing" tagged_only
```

- `mode` — `tagged_only` (act only on explicit @mentions) or `auto` (the default: follow threads you're tagged into or started and reply when relevant).
- Private channels resolve by id (`C…`/`G…`) only, same as the access check above.
- After it succeeds, confirm in one line what the channel now does (e.g. "Done — I'll only reply here when tagged."). Don't explain the modes or repeat the command.

## Recipe: call the team's Kite GitHub App (`kite-github`)

Use this path for GitHub account actions and repository import/sync. The CLI is a generic passthrough to the GitHub REST API; it resolves scope, token, and URL from the env, so you pass only the `method`, the server-relative `path`, and optionally a `body`/`query` JSON object:

```bash
kite-github api POST /repos/acme/website/issues \
  '{"title": "Broken link on pricing page", "body": "Found via the CMO."}'
```

- `method` — `GET`/`POST`/`PATCH`/`PUT`/`DELETE` (case-insensitive, 1st arg). Writes are allowed; they are bounded by the permissions the team granted the GitHub App at install.
- `path` — a server-relative GitHub API path starting with `/` (2nd arg; e.g. `/installation/repositories`, `/repos/{owner}/{repo}/issues`, `/repos/{owner}/{repo}/pulls`). Never a full `https://` URL.
- `body` *(optional, 3rd arg)* — a JSON object string for writes, e.g. `'{"title": "…"}'`.
- `query` *(optional, 4th arg)* — a JSON object string of query params, e.g. `'{"per_page": "100", "page": "2"}'`. Paginate explicitly; large responses are capped. To pass a query without a body, send `''` for the body: `kite-github api GET /search/issues '' '{"q": "…"}'`.
- **The result carries GitHub's own outcome**: `result.status` is the GitHub HTTP status and `result.body` is the parsed response. A GitHub `404`/`422` comes back here as `status: 404` — it is *not* a gateway error, so inspect `status` and branch on it (don't retry a 404 blindly).
- `409 provider_not_connected` from `kite-github` means the Kite GitHub App is not installed for this team. Do **not** run `kite-integrations connect github`; GitHub has no broker route. Tell the user to open **Integrations**, click **GitHub**, install it for an organization, grant the required repositories, and then retry this native call.
- **Listing installation repos** (`GET /installation/repositories`): repo objects are large, so a default page overflows the cap and returns `{"_truncated": true, …}` with no `repositories`. Request a small page (`'{"per_page": "10"}'`) and read `total_count` — a truncated body is *not* empty. Only `total_count == 0` means the App has no repos granted: tell the user to grant it access (specific or all repos) in GitHub's install settings, or offer to create/import one, and ask which.

**List/search endpoints return large objects — project them before they reach you (see the "Reduce large results" gotcha).** Use server-side filters and `jq` to keep only the fields needed to answer the user's question; never dump the whole response.

### Recipe: PRs merged in the last N days

Use the Search API (it filters by merge date server-side and returns leaner objects than `/pulls`), then project with `jq`. Compute the cutoff with `date`, build the query string with it, and read the projected rows from `result.body.items`:

```bash
since=$(date -u -d '7 days ago' +%Y-%m-%d 2>/dev/null || date -u -v-7d +%Y-%m-%d)
kite-github api GET /search/issues \
  '' "$(python3 -c 'import json,sys; print(json.dumps({"q": f"repo:OWNER/REPO is:pr is:merged merged:>={sys.argv[1]}", "per_page": "50"}))' "$since")" \
  | jq '[.result.body.items[] | {number, title, merged_or_closed: .closed_at, user: .user.login, url: .html_url}]'
```

Only the projected array reaches your context. If `result.body.total_count` exceeds the page, page through with `"page": "2"`, … rather than raising `per_page` past 100. For a raw list endpoint like `/repos/{owner}/{repo}/pulls`, keep `per_page` small (≈15–30) so the page stays under the cap, and `jq`-project the same way.

## Recipe: connect an unconnected integration

When the app the user needs is not connected, give them a connect link instead of stopping — and tell them you will resume their request automatically once they connect. The `kite-integrations` CLI drives this: it calls the tool gateway for you, so you pass only the app — no token, URL, or thread id.

When the user named the job but not the app ("email the list", "log this in our CRM") and no connected app covers it, first ask which tool the team uses for that job — name two or three common options — then connect the tool they actually use, not the one you assumed.

**Multi-step flows: collect every gap before asking.** When the request is a flow spanning several apps ("pull the numbers from PostHog, draft a doc in Notion, log it in HubSpot"), list every app the whole flow needs against `connected_apps` **before starting any step** — do not discover gaps one at a time and make the user authenticate over several turns. Resolve any named-job-but-not-app steps first (ask which tool, as above), then mint a connect link for **each** missing app (steps 1–2 below, once per app) and hand them all back in one message: a single opening sentence naming the flow, then a single `<connect-cta>` block whose body is a JSON **array** of `{"app", "ref", "reason"}` objects (`reason` a few words on what that app is for). The platform renders one bulleted **Connect** line per app on web (with its reason) and one button per app on Slack, with the reasons listed beneath the buttons. When the flow resumes after a connect, re-check `connected_apps` and re-offer only the apps still missing.

**App absent from `connected_apps` (e.g. the user asks for PostHog data and no PostHog is connected):**

1. Confirm it's supported and get the exact slug:

```bash
kite-integrations catalog-search "posthog"
```

Prints `{ "apps": [ { "name_slug", "name", "description" }, ... ] }`. If `apps` is empty, the app is **not supported** — tell the user that and stop. Otherwise take the exact `name_slug`. If the command itself fails (non-zero exit or an `error` field — e.g. a network blip), surface that error to the user rather than declaring the app unsupported.

2. Mint the connect link:

```bash
kite-integrations connect posthog
```

Prints `{ "app", "provider", "connect_url", "connect_ref" }`. Hand the link to the user by ending your final message with a single `<connect-cta>` block carrying the `connect_ref` — **not** the URL — the platform renders it as a **Connect** button on Slack and a bulleted link on the web. The body is one JSON object for a single app, or a JSON array (one entry per app, max 5) when a flow needs several connected. Keep the text before the block to one short sentence naming the flow — do not paste the raw URLs into your prose, and do not restate each app's reason there — then end the turn:

```
PostHog isn't connected yet. Connect it below and I'll pick your request back up automatically once you're done.

<connect-cta>
{"app": "PostHog", "ref": "<connect_ref>"}
</connect-cta>
```

For a flow needing several apps, put each app's reason in its `reason` field rather than spelling every app out in prose — every surface renders the reason next to its app (web: inline on the bullet; Slack: beneath the buttons), so a one-line opener is enough:

```
Connect these below and I'll pick your request back up.

<connect-cta>
[{"app": "PostHog", "ref": "<connect_ref>", "reason": "to pull your traffic numbers"}, {"app": "Notion", "ref": "<connect_ref>", "reason": "to create the report doc"}]
</connect-cta>
```

- `app` — the app's display name (the button reads "Connect <app>"); use the `name` from `catalog-search`, e.g. `PostHog`.
- `reason` — optional, a few words on what that app is for (not a full sentence); set it whenever the flow needs two or more apps so each bullet is self-explanatory. Skip it for a single-app CTA whose preceding sentence already says why.
- Run `catalog-search` and `connect` **before** composing your reply, and write that reply **once**. Announcing the link first ("connect it below…"), then minting, then re-writing the message with the block sends the user two near-identical messages — one without the button, one with it. The turn's shape is: mint silently (or with one short status line), then one complete reply ending in the block.
- `ref` — the `connect_ref` from the CLI for that app; one `kite-integrations connect` call per app. It is a short hex handle the platform swaps back for the real URL, so the link cannot be corrupted in transit. Never put a `connect_url` in the block and never write a connect URL into your prose. On the rare run where `connect_ref` comes back `null`, fall back to `"url": "<connect_url>"` for that entry, copied verbatim.
- Emit **at most one** `<connect-cta>` block, with a valid JSON body, and make it the **last thing** in the message. The block is only for handing back connect links — never for a working link.
- After emitting it, **end your turn**. The CLI already wired your conversation to the connect, so a new turn fires on its own once the user connects; you do not poll or wait. If the user instead replies again without connecting (so no resume has fired), re-offer the same link with a fresh `<connect-cta>` block — don't assume they connected, and don't mint a second link if the first is still valid.

**MCP server awaiting OAuth.** A configured MCP server appears in `connected_apps`, but `describe`/`execute` returns `409` with `detail.code: "provider_not_connected"` and a `detail.message` saying the server needs OAuth authorization. That specific 409 (an MCP slug that is already in `connected_apps`) is the trigger — distinct from a 409 for an app that simply isn't connected. Run `kite-integrations connect <slug>` with that server's slug to mint its authorization link, and hand it back the same way — one line of context plus a closing `<connect-cta>` block.

**Slack and GitHub are special native connect cases here.** Neither has a mintable broker link, so point the user to the first-party UI in prose (no `<connect-cta>`) and do not pass either slug to `kite-integrations connect`. Install Slack from **Integrations** or **Team settings**; install GitHub from **Integrations**.

## Errors

Every non-2xx response carries `detail: { code, message, retryable }`:

| HTTP | code                     | What to do                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 401  | —                        | `INTERNAL_API_TOKEN` missing or wrong. Check the env, stop.                                                                                                                                                                                                                                |
| 403  | —                        | Team-scoped call missing/invalid `X-Sandbox-Session-Token`, or the `team_id` isn't your session's team. Send the `-H "X-Sandbox-Session-Token: $KITE_SANDBOX_TOKEN"` header with the `$TEAM_ID` from your env — don't substitute another team's id. Stop.                                     |
| 404  | `application_not_found`  | Bad `$APPLICATION_ID`. Stop.                                                                                                                                                                                                                                                               |
| 404  | `team_not_found`         | Bad `$TEAM_ID`. Stop.                                                                                                                                                                                                                                                                       |
| 422  | `missing_identifier` (or a schema validation error) | The scope env is broken (neither or both of `$TEAM_ID` / `$APPLICATION_ID` reached the gateway). `kite-integrations` sends exactly one from the env; check the env and stop rather than retrying.                                                                                                    |
| 404  | `tool_not_found`         | Unknown tool name — re-run `search`, don't invent names.                                                                                                                                                                                                                                   |
| 409  | `provider_not_connected` | That exact slug isn't connected. **First run a bare `search` and check `connected_apps[].name_slug`** — the app is often connected under a different or version-suffixed slug (e.g. a `<brand>_v2` rather than `<brand>`); if so, retry with that exact slug. If it's genuinely absent, serve the request through a connected app with the same capability (e.g., `google_drive` reads Sheets/Docs files even when `google_sheets` is not connected); otherwise follow **Recipe: connect an unconnected integration** to hand the user a connect link (for an MCP server, this 409 is the trigger to mint its OAuth link). Don't retry the slug you guessed — retry only with a `name_slug` from `connected_apps`. |
| 422  | `invalid_params`         | Params don't match the schema. Re-run `describe` and fix; don't retry blindly.                                                                                                                                                                                                             |
| 429  | `rate_limited`           | Back off and retry once after a pause.                                                                                                                                                                                                                                                     |
| 502  | `provider_error`         | Upstream failure. Retry once **only when `detail.retryable` is true**; a `retryable: false` 502 (e.g. Slack `not_in_channel`/`channel_not_found`) won't change on retry — act on the message instead (e.g. ask the user to invite **@Kite** to the channel).                                  |
| 503  | `gateway_not_configured` | On a `native:*` tool: the platform credential is absent in this environment — fall back per your skill's failure handling (see _Platform integrations_). On team-integration work: tell the user "Integrations are not available in this workspace. Contact your administrator." and stop.                                                                                                       |

## Before returning

Verify that the needed data was retrieved, the requested action succeeded, or
the question was answered from available tools. For a multi-step request,
verify every checklist item names its app/tool and data handoff and is marked
complete. For retrieved data, confirm the needed fields are present in the
named tool's result. For an action, confirm its success status and result shape
match `describe` and the documented response. If a connect link is the required
next step, name the intentionally incomplete items in the context before the
single valid-JSON `<connect-cta>` block.
