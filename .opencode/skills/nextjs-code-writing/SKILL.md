---
name: nextjs-code-writing
description: >
  Use this skill when authoring or editing a generated Next.js website — it
  triggers any time work touches files under the iteration's `src/`, for
  example "add a section", "swap the hero", "fix the mobile menu", or "change
  this block". It covers both file-based sites and sites with an embedded CMS;
  classify each edit's owning surface before editing and also load
  `cms-management` when content, schemas, or block registration are involved.
  For single-file HTML websites, use `website-code-writing` instead.
mode: both
---

# Coding Rules — Next.js

These rules apply to every file you author or edit inside a Next.js iteration.
They cover both the file-based and embedded-CMS templates.

Resolve competing directions in this order: host prompt and protected-file
rules, explicit current user requirements, explicit rules in this skill,
existing project conventions, then implementation minimality. "Smallest"
means changing only the files and behavior required for the requested visible
outcome; a convention-preserving edit is not speculative even when it needs an
additional existing helper or shared component.

## Workflow discipline

1. Define success from the user request, the iteration's current source, and the host prompt's required response shape, available tools, and validation steps before writing code.
2. Use the smallest implementation that satisfies the request. Do not add speculative sections, styles, abstractions, files, or rewrites.
3. Read the relevant current structure before changing it: existing copy modules, components, routes, metadata exports, Tailwind class patterns, and nearby files.
4. Use deterministic tools for deterministic work: search, exact replacement, parsing, routing, validation, retries, and file checks.
5. Match the iteration's existing conventions even when another style seems preferable. Preserve routing, metadata, Tailwind patterns, data architecture, indentation, and naming.
6. Validate using the checks required by the host prompt. If a required check is unavailable or skipped, report that instead of implying it passed.
7. When a safe target is unclear, required input is missing, validation fails, image creation or referencing fails, or an edit cannot be uniquely located, report the specific missing input, failed check, or ambiguous visible target and stop.

## Choose the editing surface — per edit, not per site

Check for `src/payload.config.ts` to learn which template the site ships:
file-based (routes own rendering and import copy from `src/data/*`) or
embedded-CMS (the database owns content and routes render registered blocks).
On an embedded-CMS site the two surfaces coexist — components, styling,
routing, and metadata are still code files. Classify each edit by what owns
the value being changed, not the site as a whole:

- **Code-owned** — components, layout, styling, routing, metadata, non-CMS
  data modules: follow the file layout and template invariants below.
- **CMS-owned** — database content, `seed.json`, field schemas, collections,
  block registration: follow the embedded-CMS section below and load
  `cms-management` first.

A single request can span both — a new block type touches its component
(code) plus its schema and registration (CMS). Apply each part's rules.

## File-based site layout

- Routes live under `src/app/<route>/page.tsx`. Add a `layout.tsx` under a route only when that route group needs a wrapper distinct from the root layout.
- Shared components live under `src/components/<Name>.tsx`, one component per file, named after the file.
- Site-wide content data (text strings, lists, structured copy) lives under `src/data/content.ts` or split files like `src/data/<page>.ts` when the spec has multiple pages.
- Each route page pulls its copy from `src/data/<page>.ts`. Route files import the module and render strings from it — do not inline static brand copy twice.
- Tailwind classes are the styling system. Touch `globals.css` only when a rule cannot be expressed in `className`.
- Before adding or changing a Tailwind class, read the element's existing classes — a conflicting one already there can override yours by specificity or order (e.g. `relative` on a `fixed` element drops the sticky; a `globals.css` rule can out-specify a hover utility).
- Before moving an element to a new position, read its parent's positioning container (overlay, flex/grid slot, absolute wrapper). Adjust the element's position coordinates or flex-order within that container — do not move it into a different container unless the user explicitly names the destination.
- A color appears in several notations — `#168974`, `bg-[#168974]`, `var(--brand-green)`, `rgba(22, 137, 116, …)`, or an inline `style`. Find every notation, not just the spelling you were given.
- **Recoloring the whole site:** change the color tokens in `globals.css` once so every component using them reflows, then run a single tree-wide sweep (`sed`/`find -exec sed`) for any leftover hardcoded color classes (e.g. `text-white`, `bg-[#…]`). Don't recolor files one at a time — on a large site that times out.
- **HTML entities only in JSX markup text.** In any JS/TS string literal — data files, object values, string props (`title="l'attention"`) — write `&`, `'`, `"`, `<`, `>` as raw characters; entities like `&apos;` render literally there.
- The template ships `src/app/robots.ts` and `src/app/sitemap.ts` (Next.js serves them at `/robots.txt` and `/sitemap.xml`). `robots.ts` is complete — leave it alone. `sitemap.ts` ships listing only the homepage: update it so every route appears, and keep it in sync whenever a route is added, moved, or removed.

## File-based template invariants — do NOT modify or re-emit

These files ship with the iteration template and are protected by the host
prompt. Do not attempt to edit them or list them in a generation plan:

- `package.json`, `pnpm-lock.yaml`, `tsconfig.json`, `next.config.js`, `next-env.d.ts`, `postcss.config.js`, `middleware.ts`, `vercel.ts`, `redirects.csv`, `.npmrc`, `.nvmrc`
- `src/app/layout.tsx` (already provides `<html><body>{children}</body></html>` and brand metadata wiring)
- `src/app/globals.css` — read-only **except its `@theme` token block** (the color/font tokens that recolors and font changes edit); add other styles via `className` first
- `src/app/api/v1/kite-platform/**` (platform-provided routes — health, website-contact-form-management submit)
- `src/app/robots.ts`, `src/lib/site-url.ts` (crawl directives and the deploy-URL helper; `src/app/sitemap.ts` is editable and must list every route)
- `public/favicon.svg`

If a route needs a layout, it lives at `src/app/<route>/layout.tsx`, never overwriting the root layout.

## Embedded-CMS site layout

Content lives in the CMS database and is authored for initial generation in
`seed.json`; it does not live in route files or `src/data/*`. The
`cms-management` skill owns the seed shape, field grammar, collections, block
schema/component/registry triple, admin ergonomics, and validator.

Author visual block components under `src/components/blocks/<Name>.tsx`. Keep
their prop names identical to the corresponding CMS field schema because the
renderer spreads stored blocks directly into those components.

Treat these template files as read-only:

- `package.json`, lockfiles, TypeScript and Next.js config, middleware,
  deployment config, redirects, and runtime version files.
- `src/payload.config.ts`, generated payload types, collection/global schemas,
  and the seed runner, except when `cms-management` explicitly requires a
  schema or collection change.
- `src/app/(payload)/**`, the baked frontend layout and catch-all page, the
  block renderer, sitemap, robots file, global stylesheet, platform API routes,
  and favicon.

Prefer the fixed block library. When a new block type is necessary, add its
schema, component, and renderer registration together, then run the CMS
validator. Restyle the baked header and footer through their existing typed
`SiteSetting` prop; preserve their import and prop signatures.

## Existing font module — do NOT modify or re-emit

Existing sites may include a generated font module. Treat it as read-only:
import from it, but do not author or rewrite it.

- `src/app/fonts.ts` — exposes the site's selected Google Font for each
  typography role. Components import named exports from it (see Typography
  below).

## Typography

The planning step writes `src/app/fonts.ts` with one `next/font/google` instance per brand typography role: `heroFont`, `headingFont`, `subHeadingFont`, `bodyFont`. Apply them by importing the role you need and putting `${roleFont.className}` on the JSX element:

```tsx
import { bodyFont, headingFont, heroFont } from '@/app/fonts';

<h1 className={`${heroFont.className} text-7xl tracking-tight`}>...</h1>
<h2 className={`${headingFont.className} text-3xl`}>...</h2>
<p className={`${bodyFont.className} text-base leading-relaxed`}>...</p>
```

Use the role that matches the visual specification's typography hierarchy. Apply `bodyFont.className` to body copy and form elements; reuse it on the `<body>` element in route-level layouts only when the visual spec calls for a single default font. Reach for `fontFamily` styles, `<link>` tags for fonts, or `next/font` imports in components only when the visual specification calls for a font outside the four role exports — and only after confirming the font is in `google-font-map.json`.

When resizing text, move every breakpoint the same way — including the mobile base. A `text-Nxl md:text-Mxl` has a phone size and a desktop size; bigger means both go up, never let the phone size shrink.

When changing a font, the `font-<name>` utility class only works if a matching `--font-<name>` theme token exists in `globals.css`. A token named anything else (e.g. `--font-family-<name>`) leaves the utility dead and the font silently unchanged — rename the token to `--font-<name>` so the class actually applies.

Fonts always load through `src/app/fonts.ts` (`next/font`). Never add a raw `@import url('https://fonts.googleapis.com/…')` to `globals.css`: Next/PostCSS rejects any `@import` placed after a CSS rule and the build fails.

## Next.js App Router conventions

- Server components by default. Add `'use client'` as the FIRST line of any file that uses `useState`, `useEffect`, `useRef`, `useReducer`, `useContext`, browser globals (`window`, `document`, `localStorage`), or DOM event handlers (`onClick`, `onChange`, `onSubmit`, etc.). Missing this directive is a build error, not a warning — treat it as non-negotiable.
- Use `next/link` for in-app navigation.
- On file-based sites, per-route SEO uses `export const metadata = {...}` (or `generateMetadata` when values are dynamic) from each route's `page.tsx` or `layout.tsx`. On embedded-CMS sites, keep metadata in the CMS fields defined by `cms-management`; preserve the baked route renderer. Do not update `<title>`/`<meta>` via client-side JavaScript.
- Every route's metadata export includes all of:
  - `title` (~50–65 characters) and `description` (~120–160 characters), unique to the route.
  - `alternates: { canonical: '<route-path>' }` — the route's own path (e.g. `'/about'`), `'/'` only on the home route.
  - `openGraph: { url: '<route-path>', title, description, images: ['<image-url>'] }` — `url` is the route's own path; `images` is the route's hero or most representative approved image URL.
- Write `canonical` and `openGraph.url` as relative route paths. The root layout's `metadataBase` resolves them to absolute URLs at render time, so they stay correct when the site moves to a custom domain — hardcoded absolute domains go stale.
- Next.js replaces — it does not merge — nested metadata objects between layout and page. A page-level `openGraph` that omits `url` discards the inherited value, and every such page shares the homepage og:url. Restate `url` inside every page-level `openGraph`.
- Compute the current year at runtime (`new Date().getFullYear()`). Never hardcode the year.
- Imports must resolve against the installed dependencies listed in the user prompt's installed-packages section. Do NOT add icon libraries (`lucide-react`, `react-icons`, etc.), animation libraries, or any package the template doesn't ship with — use inline SVG instead.

## Images

### `<Image>` vs `<img>`

Use `<Image>` from `next/image` for content imagery. Use `<img>` only for purely decorative imagery without sizing constraints, or for a user-uploaded logo URL whose dimensions are unknown.

`<Image>` requires explicit `width` and `height`. Use the source metadata or
the dimensions returned by `images`. When only an aspect ratio is
available, use the matching dimensions below:

| aspect_ratio | width × height |
|---|---|
| `16:9` | `1600 × 900` |
| `4:3` | `1600 × 1200` |
| `1:1` | `1200 × 1200` |
| `3:4` | `1200 × 1600` |
| `21:9` | `2100 × 900` |

### LCP image

Set `priority` on the page's largest-contentful-paint image (typically the hero on the home route). `priority` triggers eager loading, emits a `<link rel="preload">`, and sets `fetchPriority="high"`. Without it the LCP `<Image>` lazy-loads like every other image and appears late. Every other `<Image>` keeps its default lazy behaviour — that is the optimisation.

### Image URL sources

- Reuse an existing site or user-supplied image only when its subject and role
  fit the new placement. Do not repurpose an unrelated image merely because it
  is already uploaded.
- When a page or section needs a new photo, illustration, background artwork,
  texture, or logo, load `images` and embed the returned CDN URL. Do not
  wait for a manifest entry and do not construct a URL yourself.
- Never hotlink or copy an image from an external website. If image creation
  fails, report the affected visual slot and the returned error instead of
  substituting a placeholder.
- Embed a user-uploaded brand logo directly when the design calls for it.

### Hosted image URL transforms

When embedding or adjusting a hosted image URL (logo trim, sizing, format,
zoom requests), load the `image-url-transforms` skill and follow its rules —
it owns the URL grammar, the logo-vs-content-image distinction, and the
zoom-via-CSS protocol.

## Section spacing

Drive section height from content, not from `min-height`. Let padding set the breathing room.

**Don't set `min-h-*` on a section that vertically centers its children.** When a section's minimum height exceeds its content height, vertical centering — `flex items-center`, `grid place-items-center`, `place-content-center`, `content-center` — distributes the surplus as blank space above and below, producing a large empty band. This constraint applies to the section wrapper only; centering within a bounded sub-container (card, badge, icon) is fine. Instead:
- Remove `min-h-*` from the section and let content determine the height.
- Use explicit `pt-*` / `pb-*` to control breathing room.
- Hero sections needing clearance below a fixed nav: use `pt-28 pb-20` (raise `pt` if the nav is taller, but keep it below `pt-32`).

**Scroll reveal animations must not rely on `min-h-*` for scroll distance.** A common pattern is adding `min-h-screen` so there is enough scroll travel for the animation to complete — this creates the same empty band. Instead:
- Trigger animations via `IntersectionObserver` on the content element itself (enter the viewport → start the animation).
- Keep section height content-driven; use viewport entry as the animation threshold, not section height.

**Symmetric vertical padding caps — apply to every section:**

| Section type | Max `py-*` |
|---|---|
| Standard feature / content section | `py-20` |
| Major feature section needing more air | `py-24` |
| Transitional / quote / callout section | `py-16` |
| Pre-footer CTA | `py-24` |

Cap symmetric `py-*` at the values above. `py-32` and larger create empty-looking spans of background color, especially on sections with sparse content or no imagery. Asymmetric pairs like `pt-28 pb-20` are fine when nav clearance or visual balance requires different top and bottom values.

## Component patterns

1. Add search & filters when displaying multiple products or many services.
2. Implement custom date picker and dropdown components consistent with the design of the website instead of system components.
3. Embed a Google Map only when a location is provided in the requirements. Do not guess a location. Do not use an API key.

    ```tsx
    <iframe
      src="https://www.google.com/maps?q=Lavelle+Road,+Bangalore&output=embed"
      allowFullScreen
    />
    ```

    In section copy near the map, use neutral language ("Find us on the map") unless the exact address is confirmed.

4. Reuse the navbar and footer on every page. File-based sites render them
   through the root or route-group layout. Embedded-CMS sites use the baked
   `Header` and `Footer` components fed by the `SiteSettings` global. Do not
   duplicate navigation chrome in pages or blocks.
   - Navbar links that point to homepage sections must use absolute paths with the hash (e.g. `href="/#features"`, `href="/#pricing"`) — never hash-only anchors (e.g. `href="#features"`). Hash-only anchors resolve relative to the current route, so they do nothing when clicked from a subpage. This applies to desktop nav, mobile nav, and footer nav links.
5. Mobile navigation drawer stacking:
   1. Z-index stack (highest to lowest): navbar with hamburger/close button (`z-50`) → drawer panel (`z-40`) → backdrop overlay (`z-30`).
   2. The hamburger button toggles the drawer open and closed.
   3. The backdrop overlay closes the drawer on click/tap.
   4. Modals and tooltips that must appear above the navbar use `z-[60]` or higher.
6. Contact forms POST `application/json` to `/api/v1/kite-platform/website-contact-form-management/submit`. The route is platform-provided in every Next.js iteration — never create or edit any file under `src/app/api/v1/kite-platform/`.
   - Form inputs must have `name` attributes (used as field labels in the email).
   - Form must have an email field (`type="email"` or `name="email"`).
   - All fields must have validation.
   - Request body shape: `{ email, subject?, text_body?, html_body?, json_body? }` — at least one of `text_body`, `html_body`, `json_body` is required. Map the form's `name`-attributed fields into `json_body` for arbitrary structured submissions.
7. When rendering product visuals (product previews, app screens, dashboard sections, integration/data-flow sections, workflow/automation sections, security diagrams, architecture diagrams, charts, metrics, admin/product UI), default to HTML/CSS/SVG instead of generated raster images.
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
   6. For the realism rules that govern populated content vs skeleton-bar placeholders inside rendered product visuals — including the worked wrong-vs-right example — follow the `website-product-ui-library` skill.
8. Trust strips ("Trusted by", "Our customers", "Our partners", "As featured in", logo strip, customer marquee):
   1. **If `user_uploaded_assets` includes specific brand logos** for the named companies (real customer logos provided by the user), embed those URLs as `<img>` elements with the `e_trim` Cloudinary transform. Layout as a flex/grid row with consistent gap.
   2. **Otherwise — render as wordmark-only chips.** Each company is a styled `<span>` with the company name in a consistent typographic treatment. No icons, no `<Image>`, no inline SVG glyph. Companies differ only by their name text. Example:

      ```tsx
      <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-6">
        {companies.map((name) => (
          <span
            key={name}
            className={`${bodyFont.className} font-semibold text-gray-500 tracking-wide uppercase text-sm`}
          >
            {name}
          </span>
        ))}
      </div>
      ```

      Adjust `text-gray-500` to a contrast-safe muted tone for the section's surface (`text-gray-400` on light, `text-gray-500` on light-gray, `text-white/60` on dark). Keep the same treatment across every chip — never vary weight, casing, or color per company.
   3. **Hard prohibitions:**
      - NEVER generate raster logos for fictional or placeholder companies (the image model produces low-detail abstract marks — dots, dashes, triangles — when asked to invent a brand identity it has no reference for). This is the dominant "company logos = dashes and dots" failure mode.
      - NEVER use the same inline SVG icon for multiple distinct companies, varying only the wordmark text beside it. That yields the "Acme / Globex / Initech all have the same layered-rectangle icon" failure — identical-looking entries that read as obviously fake.
      - NEVER generate an image for a fictional company logo in a trust strip.
      - NEVER author a unique inline SVG per company to fake variety. If you don't have a real brand mark, the chip pattern above is the only acceptable output.

## Analytics stamps (`data-kite-*`)

Analytics stamps apply only to classic-template sites. Payload sites use baked
block components and must not add `data-kite-*` attributes.

<!-- CANONICAL grammar. One derived condensation exists:
     backend/app/llm/coding/website_create/system-prompt-website-create.md § "Analytics stamps"
     (the create fan-out cannot load skills). Mirror vocabulary/rule changes there. -->

Author `data-kite-*` attributes (a closed vocabulary, every attribute listed below) on the interactive and section elements you write. A baked SDK (loaded by the template's `src/app/layout.tsx`) reads these stamps at runtime and emits one analytics event per interaction; the backend also reads them from your `.tsx` at deploy to build the site's event catalog. Stamps are plain HTML attributes — they never change layout or behaviour.

**Every `data-kite-*` value is a static double-quoted string literal** — `data-kite-cta-id="hero-primary"`, never `data-kite-cta-id={id}` or a template literal. The build gate blocks a `{expression}` value as a repairable `dynamic_stamp` error — build the slug in your head and write the final string. The SILENT failure is an element you forget to stamp at all: nothing errors, the interaction just never appears in analytics. **The ONE exception: `data-kite-item` (below) MUST be an expression when the items come from data** — a per-item property, not identity.

The vocabulary is **closed** — use only these attributes:

- **Page root** — on each route's top-level `<main>`: `data-kite-page-id="<route-slug>"` (e.g. `home`, `pricing`, `blog`) plus `data-kite-page-type="<type>"` describing the page's purpose (e.g. `landing`, `pricing`, `about`, `contact`, `article`). One of each per page.
- **Section** — on each major section's outer element, `data-kite-surface="<page>.<section>"` (e.g. `home.hero`, `home.pricing`) plus `data-kite-surface-type="<type>"`. Use one of `hero`, `features`, `pricing`, `cta`, `faq`, `contact`, `testimonial`, `gallery`, `footer`, or a lowercase slug naming the section's purpose. Author it on the outer element so the section's CTAs sit inside it.
- **CTA / button / link-as-action** (base rule, every CTA) — on the `<a>`/`<button>`: `data-kite-cta-id="<stable-id>"` (e.g. `hero-primary`, `pricing-pro`), `data-kite-role="primary"` (the section's main action) or `"secondary"` (a supporting/alternative action), and `data-kite-event="<semantic_name>"`. Event names are `{object}_{past-tense verb}` — name what HAPPENED, never the button label: `trial_started` (not `start_free_trial`), `plan_selected`, `demo_requested`, `contact_requested` (not `contact_us`). This matches the SDK's built-in vocabulary (`page_viewed`, `cta_clicked`, …). An id names ONE action site-wide: give each `data-kite-cta-id`/`-nav`/`-form-type`/`-expand` exactly one `data-kite-event` everywhere it appears — reuse the same id+event pair when the same action renders in several places, and give a DIFFERENT action a different id (the build gate blocks one id carrying two events as `duplicate_identity`).
- **Item dimension** — when a CTA or card renders inside a `.map()` over data (products, plans, services, portfolio items), keep `data-kite-cta-id` and `data-kite-event` identical across the loop (they name the SLOT) and add `data-kite-item={item.slug}` with a stable per-item slug from the data. Analytics then attributes each click, conversion, and view to the specific item ("which kite drives inquiries") instead of collapsing them. This is the one attribute written as an expression; add it to the item's card wrapper too when the card itself is the meaningful unit.
- **Conversion** — mark the element where the goal is genuinely COMPLETED, never a button that only leads toward it. First pick `<goal_type>` in this order: (1) the `PRIMARY CONVERSION GOAL: <goal_type> — …` line in the requirements; (2) infer from the business type — one of `signup`, `purchase`, `lead`, `inquiry`, `booking`, `subscribe`, `contact`, `download`, `quote`, `donate` (prefer a concrete value over `other`). Then place the stamp by how the goal completes:
  - **A form submit is the goal** (contact / booking / signup / quote form): put `data-kite-conversion="<goal_type>"`, `data-kite-event="<goal_type>_completed"`, and `data-kite-form-type="<type>"` on the `<form>` — not on the submit button (and do not give the submit button its own `data-kite-cta-id`). Add native validation to the fields (`required`, `type="email"`, etc.) so an invalid submit is blocked. When the form submits with JavaScript (`preventDefault` + a fetch/handler that then shows a success state — the usual case in a React app), ALSO add `data-kite-conversion-hook` to the `<form>` and call `window.__kite && window.__kite.conversion("<goal_type>")` inside the SUCCESS branch of the submit handler, so the conversion fires only on a real success.
  - **A direct action is the goal** (tap-to-call `tel:`, WhatsApp, `mailto:`, or an external link whose completion you cannot observe): put `data-kite-conversion="<goal_type>"` and `data-kite-event="<goal_type>_completed"` on that `<a>`/`<button>` — it converts on click. A click only proves INTENT (the email/call may never happen), so when the goal is `purchase`, `lead`, `inquiry`, `booking`, or `quote` and a form fits the design, build a form instead — a submitted form is a verifiable completion.
  - **A CTA only LEADS to the goal** (a hero button that scrolls to the form, or links to a contact page): do NOT add `data-kite-conversion`. Give it a normal `data-kite-cta-id` + `data-kite-event` — it is a click, not a conversion.

  Several CTAs may point at the same goal; only the completing element (the form, or the direct-action link) carries the conversion — the rest stay plain CTAs. When a page serves several DISTINCT goals (a contact form AND a download), still stamp `data-kite-conversion` on exactly ONE element — the primary goal from the requirements; the other goals keep plain `data-kite-event` names. A second conversion stamp triggers a `multiple_conversions` warning and the extractor nominates one anyway.
- **Nav link** — header/footer/in-page navigation `<a>`: `data-kite-nav="<slug-of-label>"` + `data-kite-nav-location="header"`, `"footer"`, or `"social"`. Leave `data-kite-event` off nav links; they emit a fixed `nav_clicked` event automatically.
- **Form** — on the `<form>` element, `data-kite-form-type="<type>"` (e.g. `contact`, `newsletter`). When the submit is the page conversion, also apply the Conversion rule above to the `<form>`.
- **Disclosure toggle** — a FAQ/accordion `<summary>` or toggle button: `data-kite-expand="<slug-of-question>"`.

If an element's role or conversion intent is genuinely unclear, omit the stamp rather than guess.

Give the hero at least one stamped CTA (primary or secondary) — a hero with no action is the page's most-viewed surface offering nothing measurable, and the hero→conversion funnel cannot exist without it. Skip this only when the design deliberately defers all action below the fold.

Worked example — the hero CTA only scrolls to the form, so it is a plain CTA; the
form is where the goal completes, so it carries the conversion (and fires it on
success via the hook because it submits with JS):

```tsx
<section data-kite-surface="home.hero" data-kite-surface-type="hero">
  <h1>{title}</h1>
  {/* leads to the goal → plain CTA, NOT a conversion */}
  <a href="#signup" data-kite-cta-id="hero-primary" data-kite-role="primary"
     data-kite-event="signup_started">Get started</a>
</section>

<form id="signup" data-kite-surface="home.form" data-kite-surface-type="form"
      data-kite-form-type="signup" data-kite-conversion="signup"
      data-kite-event="signup_completed" data-kite-conversion-hook
      onSubmit={async (e) => {
        e.preventDefault();
        const ok = await submitSignup(new FormData(e.currentTarget));
        if (ok) window.__kite && window.__kite.conversion('signup');
      }}>
  <input type="email" name="email" required />
  <button type="submit">Sign up</button>
</form>
```

The `window.__kite &&` guard makes the conversion a silent no-op when the SDK is not loaded (dev builds and previews without analytics) — keep it, and never let the conversion call gate the form's own success handling.

For a fire-and-forget goal, stamp the action link itself (it converts on click):
`<a href="tel:+15551234567" data-kite-cta-id="call" data-kite-conversion="contact" data-kite-event="contact_completed">Call us</a>`.

When **editing** an existing element that already carries `data-kite-*`, keep the attributes and their values intact and carry them with the element if you move it — restyle the markup around them freely.
