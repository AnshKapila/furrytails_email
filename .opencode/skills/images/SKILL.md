---
name: images
description: >
  Use this skill when a task works with the website's image assets — creating a
  new raster image, editing one, removing a background, finding an asset that
  already exists, or turning a local file into a hosted image the site can
  embed. Examples: "create a hero image", "change this photo", "remove the
  background", "the team photo I shared earlier", "put this image on the
  site". Also use it when creating or redesigning a page whose photo,
  illustration, background art, texture, or logo slot has no suitable approved
  asset, even when the user did not explicitly ask for image work. Use
  `website-product-ui-library` for dashboards, charts, workflows, and other
  product UI that should be rendered as code.
mode: sandbox
notification_title: "Working on images"
agent_policies:
  orchestrator: orchestrator-policy.md
---

# Images

Create, find, and manage the website's visual assets. This skill is globally
available to sandbox agents; no specialist-agent handoff is required. Image
work is done when the verification checks in rule 7 below pass and every
embedded URL came from a recipe response.

## Brand and brief

1. Read user-confirmed brand, audience, and positioning context from the
   knowledge wiki—the application's stored brand facts—through
   `wiki-management`. For website imagery, also load the selected design spec
   with the recipe below when one exists.
2. Apply explicit visual direction from the current task. It overrides every
   source below.
3. For choices the task does not specify, use user-confirmed wiki facts. Never
   contradict them.
4. For remaining website-imagery details, use the selected design spec. Ignore
   any design-spec detail that conflicts with the current task or wiki facts.
5. State assumptions for any needed choice these sources do not cover; do not
   present an assumption as established brand.
6. Define the concept before generating: message, visual motif, image or
   illustration treatment, channel, aspect ratio or dimensions, copy constraints,
   and required variants. Do not change the brief's audience, claim, or call to
   action while interpreting it visually.
7. After generation, verify that dimensions and format match the request; the
   intended subject and required text are fully inside the frame; rendered text
   exactly matches the requested copy; and colors and style do not conflict with
   confirmed wiki facts. Confirm each CDN URL returns a successful response. For
   every missing or failed variant, report its name and the returned status or
   error message.

If a visual must be placed into a page and the current agent cannot edit the
website, delegate placement to `web-developer` through `work-delegation` with
the chosen URL, crop or safe-area notes, and acceptance criteria.

Use the `bash` tool to call the platform's shared image routes. Pick the recipe by intent:

| Intent             | Use when                                                                                      |
| ------------------ | --------------------------------------------------------------------------------------------- |
| `search`           | List what is already stored for this website — check here before generating or fetching.      |
| `generate`         | Create one or more new images (hero, product, logo, …). 1–10 images per call.                 |
| `edit`             | Modify an existing image referenced by URL.                                                   |
| `remove-background`| Make a transparent PNG of uploaded artwork — preserves the original pixels exactly.           |
| `upload`           | Turn a file on local disk (downloaded, captured, produced by another tool) into a hosted URL. |
| `design-spec`      | Read the website's imagery style / palette before composing prompts.                          |

Read [`references/prompt-authoring.md`](references/prompt-authoring.md) before
composing any `generate` or `edit` prompt. It contains mandatory rules for
required elements, text handling, ending sentences, and logo overrides; apply
every rule before submitting the image request.

## Gotchas

- **Use `<<EOF`, never `<<'EOF'`.** Quoted heredoc terminators suppress shell variable expansion, so the platform receives the literal string `"$APPLICATION_ID"` and rejects it with a 422 UUID-parse error. Every recipe below relies on `$BACKEND_API_URL`, `$INTERNAL_API_TOKEN`, and `$APPLICATION_ID` being expanded by the shell before curl posts.
- **Pass `timeout: 300000` to bash for `generate` / `edit`.** A 10-image batch routinely takes more than the bash tool's 2-minute default; without the override the curl gets killed mid-flight and images never upload.
- **Embed the returned `url` directly.** It's a CDN URL already scoped to this application — no further upload step needed.
- **For normal generation or editing, always request a new slug.** Cloudinary's CDN caches by URL path. Re-uploading under the same `name` keeps serving the stale cached version to browsers for up to 30 minutes, even with `invalidate: true`. Pick a `name` that differs from every existing image slug—for example, append a content-derived suffix such as `-alt`, `-warm`, `-american`, or `-r1`—and use it in every HTML/JSX `src` reference written in this turn. **Exception: 504 recovery only.** Re-issue the same slug with `skip_if_exists: true` to retrieve an image already uploaded by the timed-out call, not to create a new one; see **Timeouts (504)**.

## Generate (1–10 images per call)

```bash
curl -sS -X POST "$BACKEND_API_URL/api/v1/internal/shared-tools/images/generate" \
  -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "application_id": "$APPLICATION_ID",
  "folder": "iter1",
  "message_id": "$OR_TRACE_MESSAGE_ID",
  "trace_node": "$OR_TRACE_NODE_NAME",
  "requests": [
    { "prompt": "wide-angle photo of a modern coworking lounge, warm lighting", "aspect_ratio": "16:9", "name": "hero-lounge" },
    { "prompt": "minimalist line-art logo of a mountain peak", "aspect_ratio": "1:1", "is_logo": true, "name": "brand-logo" }
  ]
}
EOF
```

Images upload to `app/<application_id>/<folder>/<name>` when `folder` is set, or `app/<application_id>/<name>` when omitted.

Top-level fields:

- `application_id` (required) — application UUID.
- `folder` — optional subfolder for organizing uploads (e.g. an iteration ID like `iter1`). When set, images upload to `app/<application_id>/<folder>/<name>` instead of the flat `app/<application_id>/<name>`. **Must match the iteration ID embedded in `Image Base URL` so predetermined HTML `<img src>` URLs resolve.**
- `message_id` / `trace_node` — include on every `generate` call, always as the literal values `"$OR_TRACE_MESSAGE_ID"` / `"$OR_TRACE_NODE_NAME"` (the shell expands them; an empty value is fine). They attach the image generations to this run's observability trace.
- `skip_if_exists` — optional, defaults to `false`. Recovery-only flag: see **Timeouts (504)** under Errors. Leave it `false` for normal generation; to regenerate an image, leave it `false` and request a new slug (per the new-slug rule under Gotchas) rather than setting this flag.
- `quality` — `"premium"` serves a higher-quality model tier; use it for standalone creative deliverables (task runs — `$TASK_ARTIFACTS_DIR` set). Website page imagery stays on the default `"standard"`.

Per-request fields:

- `prompt` (required) — authored per the rules in `references/prompt-authoring.md`.
- `aspect_ratio` — one of `16:9 | 4:3 | 1:1 | 3:4 | 21:9`. Defaults to `16:9`.
- `is_logo` — `true` for a transparent-background logo.
- To place an **existing** exact logo onto a generated image, compose the two hosted assets with an overlay URL transform (`image-url-transforms` skill) — image models cannot reproduce a brand mark exactly, so generate the visual without it and overlay the real file.
- `name` — optional filename. Must be unique in the batch and match `^[a-z0-9][a-z0-9_-]{0,63}$` (lowercase, digits, `-`, `_`). Becomes the last path segment of the returned Cloudinary URL. Auto-generated if omitted.

Response:

```json
{
  "images": [
    { "url": "https://static.kite.ai/…", "public_id": "app/…/hero", "prompt": "…", "aspect_ratio": "16:9", "width": 1920, "height": 1080, "bytes": 245678, "source": "image-generation-service" }
  ],
  "errors": [],
  "total_requested": 2, "total_succeeded": 2, "total_failed": 0
}
```

### Consuming `docs/<iter>/images.json` from the `html-generation` skill

The planner writes each iteration's image metadata to `images.json`. When
dispatching that output, set `folder` to the iteration ID (the directory name
under `docs/`, e.g. `iter1`) and map each entry into `requests[]` as follows:

- `slug` → `name`
- `prompt` → `prompt`
- `aspect_ratio` → `aspect_ratio`
- `is_logo` → `is_logo`

Max 10 entries per call. If `images.json` has more, split it into batches of at
most 10 and emit all independent `bash` calls in parallel in the same turn.
Serialize batches only when a later prompt depends on an earlier image. Do not
use `task` sub-agents.

## Edit (1+ reference images)

```bash
curl -sS -X POST "$BACKEND_API_URL/api/v1/internal/shared-tools/images/edit" \
  -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "application_id": "$APPLICATION_ID",
  "reference_images": ["https://static.kite.ai/app/…/hero.png"],
  "prompt": "change the sky to a warm sunset",
  "aspect_ratio": "16:9",
  "is_logo": false,
  "name": "hero-sunset"
}
EOF
```

- `reference_images` (required, 1-10) — `http://` or `https://` URLs. Pass one for a simple targeted edit, multiple to combine, blend, or use as style references. Other URL schemes are rejected (422).
- `prompt` (required) — what to change.
- `aspect_ratio` — defaults to `1:1`; pass the source image's ratio explicitly to preserve it.
- `is_logo` — `true` if the source is a logo so the edit keeps a transparent background.
- `name` — optional, same rules as `generate`.

Returns `{ url, public_id, prompt, width, height, bytes }` for the edited image. Use `edit` whenever the existing image's pixels need to change. For pure background removal use `remove-background` — it preserves artwork pixel-for-pixel.

## Remove background (preserve original pixels)

For "remove the white background", "make it transparent", "isolate the logo" on uploaded or existing artwork. Output is a transparent PNG containing the original pixels — nothing is regenerated.

```bash
curl -sS -X POST "$BACKEND_API_URL/api/v1/internal/shared-tools/images/remove-background" \
  -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "application_id": "$APPLICATION_ID",
  "image_url": "https://static.kite.ai/app/…/uploaded-logo.png"
}
EOF
```

- `image_url` (required) — `https://` URL. Cloudinary URLs work best.

Response: `{ url, original_url, provider, bytes }`. Embed `url` directly.

## Search existing assets

List what is already uploaded for this website: user attachments, earlier
generations, extracted logos. An asset already on the site's CDN is always
preferable to generating or fetching a new one — check here first when the
user references an image they shared earlier or when you need the URL of an
asset produced earlier in the conversation.

```bash
curl -sS -X POST "$BACKEND_API_URL/api/v1/internal/shared-tools/images/search" \
  -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "application_id": "'"$APPLICATION_ID"'", "max_results": 30 }'
```

- `resource_type` — optional filter: `"image"`, `"video"`, or `"raw"`.
- `max_results` — 1–500, defaults to 30. Results come newest first.

Response: `{ total_count, resources, next_cursor }`. Each entry in
`resources[]` has:

- `url` — the CDN URL you embed
- `filename`, `format`, `bytes`, `width`, `height`
- `tags` — AI-generated content tags
- `context.custom.alt`, `context.custom.caption` — human-set metadata

The endpoint returns the website's whole folder; for keyword filtering (e.g.
"team photo") match client-side against filename, tags, alt, and caption — a
hit in any of those fields counts.

## Upload a local file

When an image exists only on local disk and the website must embed it — after
downloading, capturing, or producing it with another tool. (Images from
`generate` / `edit` / `remove-background` are already hosted; embed their
returned `url` directly, no upload step.)

```bash
curl -sS -X POST "$BACKEND_API_URL/api/v1/internal/shared-tools/images/upload" \
  -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  -F "application_id=$APPLICATION_ID" \
  -F "file=@/path/to/local/image.png" \
  -F "name=hero-image"
```

- `name` — optional slug, same rules as `generate` (`^[a-z0-9][a-z0-9_-]{0,63}$`);
  derived from the file's name when omitted. The new-slug rule under Gotchas
  applies here too — re-uploading under an existing slug serves the stale
  cached version.
- `folder` — optional subfolder, same semantics as `generate`.
- Upload **raster files only** (PNG/JPG/WebP). For an authored SVG, rasterize
  it first (next section) and upload the PNG — the CDN's own SVG-to-PNG
  conversion garbles text (negative `letter-spacing` mirrors and clips glyphs).

Response: `{ url, public_id, filename, width, height, bytes }`. Embed only the
returned `url`; if the request fails, report the error and do not invent a URL.

## Rasterize an authored SVG

When a deliverable needs exact text or logo placement, authoring it as SVG is
fine — but the deliverable is always the PNG. The sandbox browser is the only
faithful rasterizer here (ImageMagick lacks an SVG delegate; the CDN's
converter mangles text), and it also resolves remote `<image href>` logos:

```bash
kite-browser create "file://$PWD/visual.svg" && \
  kite-browser set viewport 1080 1080 && kite-browser wait 400 && \
  kite-browser screenshot --full /tmp/visual.png && kite-browser close
```

Set the viewport to the SVG's own `width`/`height` attributes so the capture
is 1:1. Then upload `/tmp/visual.png` with the recipe above and verify the
returned CDN URL renders the text correctly.

## Get design spec (imagery style + palette context)

```bash
curl -sS -X POST "$BACKEND_API_URL/api/v1/internal/shared-tools/images/design-spec" \
  -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "application_id": "'"$APPLICATION_ID"'" }'
```

Response: `{ application_id, iteration_id, design_spec, source_filename }`. The `design_spec` field is the markdown body of `design_spec.md` (or `visual_spec.md` fallback) for the website's currently selected iteration. A `404` with `code: no_iteration_selected` means the design hasn't been selected yet — proceed without spec context.

## Errors

- `401` — `INTERNAL_API_TOKEN` missing or wrong. Check the env, stop retrying.
- `404` (design-spec only) — no application, no selected iteration, or no `design_spec.md` / `visual_spec.md` written yet. Carry on without spec context.
- `422` — body schema error (missing `application_id`, >10 requests, bad `aspect_ratio`, non-http URL, empty or malformed `upload` file/slug). Fix locally, don't retry blindly.
- `502` (remove-background only) — provider rejected the image or timed out. Safe to retry once.
- `504` (`generate`) — gateway timeout; the image often generated anyway. Recover via **Timeouts (504)** below rather than a plain retry.
- other `5xx` — upstream model hiccup. Safe to retry once; if it fails again, surface the error to the user.

### Timeouts (504)

A `504 Gateway Time-out` on `generate` means the gateway stopped waiting (~60s) while the backend kept generating and uploading. Recover by reclaiming the finished uploads:

1. Wait 2 minutes (`sleep 120`) so the in-flight generation can finish uploading, premium images can take longer.
2. Re-issue the **same** request (same `application_id`, `folder`, and `name`s) with `"skip_if_exists": true`. Tool will respond with images uploaded in the previous request.
3. On another `504`, repeat the wait and re-issue up to twice more (never more than 7 minutes) before reporting failure.

The recovery request must carry `skip_if_exists` after a wait. Immediate re-issue will cause a re generation of the same prompts and cause 504 again.

Set `skip_if_exists` only for this recovery case. To create a fresh image — including when the user asks to regenerate something they can already see — call `generate` normally (with `skip_if_exists` omitted) and request a new slug, per the new-slug rule under Gotchas.
