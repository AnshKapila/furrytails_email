---
name: website-page-creation
description: >
  Use this skill when an edit adds a new page or route to an existing
  marketing website — a custom landing page for conversion, an SEO/AEO page,
  a blog post, a pricing page — including pages whose content comes from
  research, AEO, audit, or report findings. Initial app generation and edits
  to existing pages use their own flows; for a hosted internal report or
  dashboard, use dashboard building.
mode: sandbox
---

# Adding a new page

Before writing any code, detect which page pattern the app uses, then follow the matching section below.

## Step 1 — Detect the page pattern

1. Read `frontend/src/index.html`. If it contains a `const routes = {` declaration, the app uses the **SPA pattern** — go to Step 2A.
2. If `index.html` has no routes object, check whether `frontend/src/` contains multiple `.html` files (e.g. `about.html`, `pricing/index.html`). If yes, the app uses the **MPA pattern** — go to Step 2B.
3. If both a `const routes` object and multiple `.html` files exist, treat the app as **SPA** — the routes object is the primary routing mechanism.
4. If neither pattern is found (empty or new app), use the **SPA pattern** as the default.

## Step 2A — SPA pattern (render function)

Add the new page by making exactly these changes to `index.html`:

1. **Create a render function.** Add a `renderPageName()` function (camelCase matching the page name — e.g. `renderPricing`, `renderCareers`). The function sets `app.innerHTML` with the page HTML.
2. **Add a route entry.** Insert a new key in `const routes = { ... }` with the page path, title (50–65 chars), description (120–160 chars), and `render: renderPageName`.
3. **Do not modify the `render()` dispatcher.** It already handles all routes generically via `route.render()`. The new route entry is picked up automatically.
4. **Extract content into JSON.** Place all factual, translatable, or frequently-updated text for the new page into a JSON data file under `frontend/src/content/` (e.g. `pricing.json`). Import and render from that file in the render function.
5. **Navigation links.** Add links to the new page wherever page links already live — desktop nav, mobile nav, and footer nav — and return the route path (e.g. `/pricing`) in your response. Skip the links only when the orchestrator explicitly asks for an unlinked or standalone page (e.g. an ad landing page); then return the route path and note that the page is intentionally unlinked.
6. **Fix hash-only navbar links.** After adding the page, scan the navbar for hash-only anchor links (e.g. `#features`, `#pricing`). Convert them to absolute paths (e.g. `/#features`, `/#pricing`) so they navigate to the homepage section from any route. Apply the same fix to desktop nav, mobile nav, and footer nav links.

## Step 2B — MPA pattern (multiple HTML files)

Add the new page by creating a new HTML file:

1. **Match existing file organization.** Check how existing pages are structured — flat files (`about.html`) or nested directories (`about/index.html`). Follow the same convention.
2. **Copy shared layout from an existing page.** Read the home page (`index.html`) as the canonical reference for the navbar, footer, and `<head>` boilerplate. Replicate its layout skeleton into the new file. There is no shared component system — every page carries its own copy of the header, nav, and footer.
3. **SEO metadata.** Include `<title>` (50–65 chars), `<meta name="description">` (120–160 chars), and Open Graph / Twitter card tags.
4. **Extract content into JSON.** Place all factual, translatable, or frequently-updated text for the new page into a JSON data file under `frontend/src/content/` (e.g. `pricing.json`). Load and render from that file.
5. **Synchronize navigation across all pages.** Since every page has its own nav copy, adding a link to only one page leaves the rest inconsistent. Unless the orchestrator explicitly asks for an unlinked or standalone page (e.g. an ad landing page):
   - List all `index.html` files under `frontend/src/` (including the root).
   - Add the new page's nav link to each page's desktop nav, mobile nav, and footer nav (whichever sections already carry navigation links).

   Always return the route path (e.g. `/pricing`) in your response; for an intentionally unlinked page, note that it is unlinked.
6. **Fix hash-only navbar links.** After creating the new page, scan existing nav links in all pages (including the new one) for hash-only anchors (e.g. `href="#features"`, `href="#pricing"`). Convert them to absolute paths (e.g. `href="/#features"`, `href="/#pricing"`) so they navigate to the correct homepage section from any page. Apply the same fix to desktop nav, mobile nav, and footer nav. This step is independent of step 5 — run it even for an intentionally unlinked page, because the new page inherits the homepage's nav copy with its hash-only anchors.

After this skill finishes its work, the agent's system-prompt table will
direct it to `website-aeo-metadata-management` so that `/llms.txt` is refreshed to list
the new page. Refreshing the curated AI index is owned by that skill, not
by page creation — do not load it from here.
