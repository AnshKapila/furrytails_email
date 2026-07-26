---
name: website-code-writing
description: >
  Use this skill when writing or editing a generated single-file HTML/Vite
  website — for example adding a route, section, navigation behavior, content
  data, form, image, or product visual inside the `route.render()` architecture.
  Use it for the vanilla HTML/JavaScript template only. For Next.js App Router
  websites, use `nextjs-code-writing` instead.
mode: both
---

## Code Structure

1. Use the `Current HTML` as the structural foundation. Keep the `Current HTML` routing/meta architecture intact (including route-scoped SEO updates and `route.render()` behavior).
2. Wrap all runtime JavaScript (router, `render()` dispatcher, page-init code, event handlers, form handlers) in exactly one `<script id="main_script">` tag. Keep auxiliary scripts separate with their own IDs or none — CDN scripts (Lucide, Tailwind), `<script id="content" type="application/json">`, JSON-LD structured data, analytics. The platform's post-processing — initial-render boot fallback and website-contact-form-management runtime injection — is gated on this exact ID; splitting runtime code across multiple `<script>` blocks silently disables both.
3. Ensure links/buttons navigate only to valid existing routes/targets.
4. Keep implementation modular and maintainable; avoid brittle inline hacks.
5. Use a single element for text that shares the same styling. Do not use individual spans or separate divs for individual letters or text that are part of the same word or paragraph.
6. Inside the `render()` dispatcher, always call `route.render()` unconditionally since the inner HTML is added dynamically to the main tag. The script must also end with an initial top-level call — `render(location.pathname);` — so the home route paints on first load.
7. When using dates, always use JS to get the current date. Do not hardcode the year.
8. Ensure every link and button triggers the correct route navigation.
9. Ensure the current page is highlighted in the navigation bar.
10. Modularise factual content into a valid JSON object inside a script tag as defined below
    1. Modularise the content into normalised information that can be used across the entire website to avoid duplication. Do not group content page-wise or marketing copy into this tag. Focus on informational content like product info, company info, services, projects, events, etc.
    2. This script tag must contain a single valid JSON without any functions, comments, or trailing commas.
    3. **ONLY** use `assets[i].url` from the content spec for image URLs. These will be Cloudinary URLs.
    4. Exclude from this tag: navigation links, sitemap structure, assets, pages, and sections.
11. Keep the route object compatible with page-scoped SEO metadata:
    1. Each route should preserve a `title` and may include a `description`.
    2. `title` should be ~50–65 characters; `description` should be ~120–160 characters.
    3. The router must update `<title>`, `meta[name="description"]`, `og:title`, `og:description`, `twitter:title`, and `twitter:description` when the current route changes.
    4. Do not remove or bypass the template helper that applies route metadata to the document head.

## Protected files

These paths own platform deployment, security headers, supply chain, and agent runtime. They are read-only. (`next.config.mjs` and `tailwind.config.js` stay editable per the host prompt's rules — they are not in this list.)

- The `edit` and `write` tools deny them at the platform level. If the user explicitly asks to modify one of these paths, or the goal truly requires deployment/security/supply-chain changes, report it as out of scope and stop.
- If the user's underlying goal can be satisfied through normal app files, do that instead. Example: for asset-loading requests, copy or reference assets from allowed app-owned locations (`public/`, `src/`, content JSON, Cloudinary URLs) rather than changing Vite filesystem allowlists or package scripts.
- Read these paths freely with `read`/`grep`. To modify them, use only the `edit` and `write` tools (and rely on the platform deny). Treat every other modification path as blocked: `bash` redirects (`>`, `>>`, `tee`), in-place editors (`sed -i`, `perl -i`), inline interpreters (`python -c`, `node -e`, `awk`), rename/copy round-trips (`mv … _tmp && edit _tmp && mv _tmp …`, `cp … scratch && edit scratch && cp scratch …`), and any equivalent indirect form.

Locked paths (match anywhere in the working tree, not just root):

- `**/vercel.ts`, `**/vercel.json` — deployment config and CSP / security headers
- `**/middleware.ts` — platform middleware
- `api/**` — Vercel serverless mount
- `**/vite.config.js`, `**/vite.config.ts`
- `**/package.json`, `**/pnpm-workspace.yaml`, `**/pnpm-lock.yaml` — platform-managed. Don't add/upgrade/remove packages (no editing these, no `pnpm add`/`npm install`). Use the installed stack + inline SVG; if a package is genuinely required, stop and name it so the platform can add it.
- `**/redirects.csv`
- `**/drizzle.config.ts`
- `generators/**`
- `**/.opencode/**`, `**/.claude/**`, `**/.cursor/**`
- `**/workpad.json`

## Forbidden pm2 operations

The sandbox runs services under PM2, and the only legitimate agent uses are reading logs and restarting the dev server (`frontend`/`backend` for HTML-template apps; Next.js apps have no `frontend` and their `nextjs-*` dev servers self-heal via HMR + platform-managed autorestart, so do not restart them) — see the `website-error-debugging` skill for the exact commands. Every other pm2 operation manages platform-owned processes (the OpenRouter telemetry / billing proxy) or rewrites PM2 daemon state, and the platform restarts those itself when needed. If a task appears to require one of these, stop and report the request as out of scope.

- `pm2 start`, `pm2 stop`, `pm2 delete`, `pm2 restart` of any process other than `frontend`/`backend` — including `metadata-proxy`, `or-metadata-proxy`, `opencode-metadata-proxy`, `codex-metadata-proxy`
- `pm2 kill`, `pm2 resurrect`, `pm2 reload`, `pm2 reset`
- `pm2 save`, `pm2 set`, `pm2 unset`, `pm2 startup`, `pm2 unstartup`
- Any indirect form of the above (`pm2 list | xargs pm2 delete`, etc.)

## Workflow Discipline

1. Define success from the user request, current HTML, and the host prompt's required response shape, available tools, and validation steps before writing code.
2. Use the smallest implementation that satisfies the request. Do not add speculative sections, styles, abstractions, files, or rewrites.
3. Read the relevant current structure before changing it: existing text, classes, routes, data objects, metadata, template helpers, and nearby patterns.
4. Use deterministic tools for deterministic work: search, exact replacement, parsing, routing, validation, retries, and file checks.
5. Match the current website conventions even when another style seems preferable. Preserve routing, metadata, Tailwind patterns, data architecture, indentation, and naming.
6. Validate using the checks required by the host prompt. If a required check is unavailable or skipped, report that instead of implying it passed.
7. When a safe target is unclear, required input is missing, validation fails, an image cannot be generated, or an edit cannot be uniquely located, report the specific missing input, failed check, or ambiguous visible target and stop.

## Component Usage

1. Add search & filters when displaying multiple products or many services.
2. Implement custom date picker and dropdown components consistent with the design of the website instead of system components.
3. Embed a Google Map only when a location is provided in the requirements. Do not guess a location. Do not use an API key.
    
    ```html
    <iframe
      src="<https://www.google.com/maps?q=Lavelle+Road,+Bangalore&output=embed>"
      allowfullscreen
    ></iframe>
    ```
    
    In section copy near the map, use neutral language (“Find us on the map”) unless the exact address is confirmed.
    
4. The navbar & footer must be reused on every page and remain consistent across all routes. Do not omit the navbar & footer on any page or vary its structure between routes.
   - Navbar links that point to homepage sections must use absolute paths with the hash (e.g. `/#features`, `/#pricing`) — never hash-only anchors (e.g. `#features`, `#pricing`). Hash-only anchors resolve relative to the current page, so they do nothing when clicked from a subpage. This applies to desktop nav, mobile nav, and footer nav links.
5. Mobile navigation drawer stacking:
    1. Z-index stack (highest to lowest): navbar with hamburger/close button (`z-50`) → drawer panel (`z-40`) → backdrop overlay (`z-30`)
    2. The hamburger button must toggle the drawer open and closed
    3. The backdrop overlay must close the drawer on click/tap
    4. Modals and tooltips that must appear above the navbar use `z-[60]` or higher
6. For contact forms, assume that `submitContactForm` is present:
    - Form inputs must have `name` attributes (used as field labels in the email).
    - Form must have an email field (`type="email"` or `name="email"`).
    - All fields must have validation.
7. When rendering product visuals (product previews, app screens, dashboard sections, integration/data-flow sections, workflow/automation sections, security diagrams, architecture diagrams, charts, metrics, and admin/product UI), default to HTML/CSS/SVG instead of generated raster images.
    1. For SaaS/software sites, generated raster images are a secondary tool. Use them only for editorial hero backdrops, brand mood/supporting imagery, and portraits/testimonials when explicitly needed.
    2. Do not use generated raster images to depict product UI concepts such as dashboards, analytics panels, workflow builders, admin surfaces, integrations maps, architecture/security diagrams, charts, or metrics cards unless the user explicitly asks for an illustrative poster-style treatment.
    3. For integration/data-flow sections, a mixed approach is preferred: keep product logos as images when needed, and render nodes/connectors/status states using HTML/CSS/SVG.
    4. Use CSS connectors/arrows for simple linear flows; use inline SVG connectors for branched or curved flows where SVG gives clearer structure.
    5. Treat these examples as references, not templates. Adapt composition, spacing, and color to the current design tokens:
        - Dashboard preview: render cards/charts/table as HTML/CSS instead of using generated screenshots.
        - Analytics section: render charts, KPI chips, legends, and tables in HTML/CSS/SVG.
        - Integrations section: show SaaS logos as image assets, while rendering data pipeline blocks/connectors in HTML/CSS/SVG.
        - Workflow section: render trigger/action pipeline states as HTML/CSS.
        - Security or architecture section: render layered diagrams, trust boundaries, and callouts in HTML/CSS/SVG rather than as soft-focus raster art.
        - Annotated demo: combine a base dashboard panel with floating callout cards to explain capabilities.
        - Backgroundless product crop: render a clean isolated UI block without decorative backdrop.
        - Branded hero demo: render UI over a full-bleed gradient/mesh/wave background.

## Image Creation

To create images follow these rules:

1. Construct the image URL using the `Image Base URL` provided with a descriptive filename ending in `.png` appended to it. Each filename must be **3–5 hyphenated words** that describe both the section and the subject (e.g. `hero-aerial-city-skyline.png`, `about-team-group-photo.png`, `testimonials-sarah-chen-headshot.png`). Each filename must be unique across the entire website. Do not use placeholder CDN/stock URLs (e.g. [placeholder.com](http://placeholder.com/)). Avoid single-word names like `logo.png` or numbered names like `avatar-1.png` — always include context: `nav-brand-logo.png`, `testimonials-reviewer-avatar-woman.png`.
2. After the closing `</html>` tag, add an image manifest describing every image that needs to be created using these rules.
    - `name` is the filename slug used in the Image Base URL (without `.png`).
    - `description` is the image generation prompt created using the `Image Prompt Rules`
    
    ```
    <!--IMAGES
    [
      {"name": "hero-aerial-city-skyline", "description": "A sweeping aerial view of a modern city skyline at sunset…"},
      {"name": "nav-acme-brand-logo", "description": "Logo for Acme. type=wordmark; flat vector, crisp edges, no shadows, transparent background"}
    ]
    IMAGES-->
    ```
    
3. This manifest is the source of truth for image generation. Images missing from this list will not be generated.
4. Every image URL must appear as a static `src` attribute in the image tag of the HTML. Always inline the full `{IMAGE_BASE_URL}/<name>.png` path directly in `<img src="…">`. If you need to reference an image in a JS data structure, store the complete URL, not just the filename.
