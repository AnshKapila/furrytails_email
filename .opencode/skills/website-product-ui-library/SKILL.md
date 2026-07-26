---
name: website-product-ui-library
description: >
  Use this skill when a software, SaaS, app, dashboard, or platform website
  needs a product visual rendered as code — for example "show the dashboard",
  "add an analytics panel", "build an app preview", or "visualize the
  workflow". Use it for UI-like dashboards, tables, charts, workflows,
  integrations, and admin screens. Use `images` for photographs,
  editorial imagery, or a product screenshot the user explicitly requests.
mode: sandbox
---

# Digital product UI rendering

Apply this workflow before writing product UI code. Start with the brief
working plan defined below, then choose the implementation and build the
surface.

For digital product websites (SaaS, apps, dashboards, platforms), render
UI-like product visuals as code by default. Resolve competing directions in
this order:

1. Follow the user's explicit request for a screenshot, generated image, or
   supplied image.
2. Follow the host prompt's file, dependency, and validation constraints.
3. Otherwise apply this skill's coded-UI preference and realism rules.

## Choose the implementation

- **Next.js with `src/components/ui/` and `components.json`:** reuse the shared
  component library and existing theme.
- **Next.js without the library:** initialize it only when the host prompt
  explicitly permits skill-directed dependency installation. Otherwise compose
  the product surface from the installed React, Tailwind, and icon stack; do
  not edit package files or install dependencies.
- **Single-file HTML:** compose the same product surfaces with semantic HTML,
  Tailwind/CSS, and inline SVG. Do not install a React component library.

The component library changes how the chrome is built, not the realism rules
below. Marketing sections such as heroes, pricing, and calls to action keep
their existing bespoke design language.

## Next.js component-library workflow

Use this workflow when the library already exists or the host prompt explicitly
permits its installation. When neither is true, skip installation and use the
same composition and verification rules with native React/Tailwind elements.

### 1. Install only when the host permits it

```bash
pnpm dlx shadcn@latest init -y -b radix -p nova
pnpm dlx shadcn@latest add -y button card badge tabs table input select avatar separator tooltip progress chart
```

Add only extra components the mockup actually uses. The install creates
`src/components/ui/`, `src/lib/utils.ts`, and `components.json`; chart support
also installs its chart dependency.

### 2. Repair initialization side effects after a new install

1. Preserve the brand fonts from `src/app/fonts.ts`. If initialization added a
   Geist import or changed the root element's font classes, remove that change.
2. Resolve theme-token collisions. Library surface tokens such as
   `background`, `card`, `primary`, `secondary`, `muted`, `accent`, `border`,
   `input`, and `ring` must not reuse a brand token with a different meaning.
   Rename a conflicting brand text token (for example, `muted` to `ink-soft`)
   and use `muted-foreground` for secondary text.

### 3. Theme the library

Replace the generated neutral defaults in both `:root` and `.dark` with values
derived from the site's brand:

- Map `primary` and `ring` to the brand accent.
- Use layered neutrals for background, card, popover, and their foregrounds.
- Set border, muted, and muted-foreground one step from their surfaces.
- Build chart colors from the accent plus distinguishable neighboring hues.
- Cap container radii in product chrome at `0.5rem`; avatars, toggles, radio
  buttons, and circular icon buttons keep their natural full radius.

Configure library components through props and `className`; treat
`src/components/ui/` as read-only. When one mockup needs a different surface,
override variables on its wrapper instead of forking component files.

### 4. Compose the mockup

- Use library cards, tables, tabs, badges, avatars, form controls, progress, and
  separators when installed. Otherwise build semantic equivalents with the
  existing stack rather than imitating unavailable imports.
- Place each interactive mockup in its own client component so route pages stay
  server-rendered.
- Wrap tooltips once in `TooltipProvider`.
- Build charts with the library's chart container and real data arrays. Label
  axes and include units.
- Put the product UI in a fixed-width desktop inner canvas and scale that canvas
  proportionally inside an `overflow-hidden` aspect-ratio wrapper at narrower
  widths. Preserve the composition instead of reflowing it like a full app.

### 5. Verify the integration

- Run `pnpm exec tsc --noEmit`.
- Confirm no generated default theme values or font overrides remain.
- Confirm marketing sections did not adopt product-library components or
  tokens.
- Check the mockup at desktop, tablet, and phone widths for clipping or page
  overflow.

Continue using image tools for logos, real-world photography, and non-UI
illustration assets. Keep an existing product screenshot when the user asks to
retain the image-based treatment; otherwise prefer a coded surface.

*Plan before rendering*
Before writing HTML/CSS, make a brief working plan (not a user-facing
deliverable) that names the surface, dominant base UI, data-bearing components
and their population counts, visible controls, and background treatment. Use
that plan to satisfy the density rules below rather than pattern-matching to a
generic dashboard.

*Fidelity baseline*
Rendered product UIs are high-fidelity working-product surfaces, not wireframes or skeletons. Align them with design-spec tokens (color, typography, spacing, radius, shadows, motion tone) so they blend into the surrounding website. Use realistic component composition — cards, tables, charts, sidebars, status badges, forms, buttons — with clear typographic hierarchy. Render iconographic elements — icons, status glyphs, sparklines, connectors, logos within nodes, and button affordances — with Lucide or inline SVG; ordinary borders, fills, and CSS chart bars do not need SVG. Emojis are never product-UI iconography: use the site's existing Lucide integration instead. The product UI uses its own UI typeface, decoupled from the website's brand fonts: set `font-family: Inter, ui-sans-serif, system-ui, sans-serif` (Inter when loaded, native UI font otherwise — never a serif fallback). Use this sans-serif stack for all standard UI chrome — body, headings, timestamps, IDs, badges, metrics, source labels, table cells, and event-feed rows. Reserve monospace only for content that is literally code, command output, or log lines (a terminal pane, a code block, a raw log viewer); a dashboard, activity stream, or event feed that merely looks "technical" still uses the sans-serif stack. Use only two font weights anywhere in the product UI: regular (`font-normal`, 400) and medium (`font-medium`, 500). Do not use semibold (600), bold (700), or any weight above 500 — establish hierarchy through size, color, and spacing instead. Even headings, KPI values, and emphasized labels stay at medium (500). Cap typography to product-UI scale: headings at most 15px, body copy at most 13px (at the desktop-authored 1280px width — these scale down with the block). Keep container corners tight: on containers (cards, panels, modals, buttons, inputs, badges, dropdowns), border-radius must be one of `rounded-xs` (2px), `rounded-sm` (4px), `rounded-md` (6px), or `rounded-lg` (8px) — nothing larger than `rounded-lg`/8px, and no `rounded-xl` or above. This caps the design-spec radius token for product-UI surfaces. Inherently round controls are exempt: avatars, toggle switches, radio buttons, and circular icon buttons keep their natural full/50% radius.

*Anchor floating elements to a base UI*
Every product-visual block must have a single dominant base surface — a dashboard frame, app window, table, or full-page UI mock — that the rest of the composition sits on or around. Floating cards, badges, callouts, charts, and status pills are decorations *of* the base UI; they must visually attach to it (overlapping its edges, sitting inside it, or peeking out from behind it).

If the block contains only floating cards with no base surface behind them, it reads as decorative chrome, not product. Render the base UI first, then layer accents on top.

Concretely:
- The largest element in the block is the base UI (app frame, dashboard, table view).
- Floating accent cards overlap 15–25% of their width or height with the base,
  or are clipped to its edge.
- Accent cards touch the base — they never sit fully in empty space adjacent to it.
- For hero sections specifically: render one realistic product surface, then optionally 1–2 accent cards overlapping its corners.

*Backgrounds for product UIs*
Backgrounds are optional for rendered product visuals: none, subtle ambient, or full-bleed branded/contextual. Choose an intentional visual treatment per product visual block based on section intent:
- **Clean Isolated UI** — minimal or no background
- **Soft Ambient** — subtle tinted or textured background
- **Full-Bleed Branded** — gradient, mesh, or wave background
- **Dark Contextual** — dark or cinematic mood for compliance/infrastructure
- **Annotated Overlay** — floating callouts overlapping (not adjacent to) a clearly visible base UI
- **Layered Product Story** — multiple panes or cards showing product flow

If multiple product visual sections are present, use at least 2 treatment modes
that differ in background, base-UI structure, or accent placement. Do not use
the same mode in consecutive sections.

For integration or data-flow sections, use a mixed approach: product logos as images plus rendered nodes, connectors, and status states as HTML/CSS. Use CSS connectors for simple linear flows; use inline SVG connectors for branched or curved flows.

Canonical examples (adapt to current design tokens and section context — treat as references, not rigid templates):
- Dashboard preview section: render cards/charts/table as HTML/CSS instead of a screenshot
- Integrations section: SaaS logos as images, data pipeline nodes and connectors as HTML/CSS
- Workflow automation section: trigger/action pipeline blocks and statuses as HTML/CSS
- Annotated capability demo: base product UI plus floating callout cards
- Clean backgroundless product crop: no decorative backdrop around the UI block
- Branded hero product demo: UI composed over a full-bleed gradient/mesh/wave background

# Realism rules

The fidelity baseline above sets the goal; the rules below give the concrete checks that separate a realistic working-product surface from a marketing mockup of one. Sparse data, inconsistent surfaces, centered text inside product chrome, and pure-black dark mode are the strongest tells of generated UI.

*Data density signals realism*
Data-bearing components must be populated like a working product, not a tutorial slide.
- Tables: render 8–12 rows minimum. Include column headers, at least one sort affordance (caret/arrow on a sortable column), and a row count or pagination footer ("Showing 12 of 47").
- Lists and activity feeds: 5+ items with varied content lengths, varied timestamps (mix of "2m ago", "yesterday", "Mar 14"), and varied states.
- KPI rows: render 3 or 4 metrics side-by-side, not 2. Each metric pairs with a comparison signal (delta vs prior period, sparkline, or target).
- Every data view includes at least one control affordance visible in the chrome: search input, filter chips, date-range picker, column toggle, or segmented control. A table with no filter bar reads as a placeholder.
- Each row in a list or table carries 4+ distinct signals. For CRM deals: company + stage + owner avatar + last activity + value. For tasks: title + assignee + priority + due date + status. For logs: level + source + timestamp + message + trace ID. A row with only "name + value" is too sparse.

*Sibling surfaces share treatment*
Cards, tiles, and panels that sit in the same row or grid use the same background, border, radius, and elevation. If two KPI cards are side-by-side, they look identical — same fill, same stroke, same shadow. Reserve elevated, tinted, or accent-colored treatment for a single primary surface within a section, and only when the design hierarchy genuinely calls for it. If every card is "special", none are.

*Text alignment follows component type*
Inside product surfaces (dashboards, tables, lists, forms, settings panels), text is left-aligned — this is the single strongest tell of real product UI. Default every text element to left alignment and only center the narrow set of exceptions listed at the end of this rule. Center-aligning content inside product chrome (cards, table rows, list items, KPI tiles, sidebars, headers, form fields) instantly reads as a marketing page, not a working product. Do not apply `text-align: center` to any product-chrome element.
- KPI and stat cards: label, value, and delta all left-aligned within the card.
- Table rows and list items: identifiers, names, and metadata left-aligned; numeric values (currency, counts, percentages, durations) right-aligned in their column so digit places line up.
- Section headers (e.g. "Active Deals", "Recent Activity"): left-aligned title, with any action link ("View All", "Export") right-aligned on the same baseline.
- Form labels and inputs: left-aligned within their field group.
- Center alignment is reserved for: empty states, modal confirmation copy, auth screens (login/signup), and short standalone CTAs. Do not center-align content inside dashboards, tables, KPI cards, or list rows.

*Scale proportionally on narrow viewports*
Rendered product UIs are designed at desktop width (a realistic app frame is ~1200–1440px wide). On narrower viewports the entire block scales down as a unit rather than reflowing — the goal is for the desktop composition to remain recognizable at any screen size, not to behave like a real responsive app.
- Author the product UI inside a fixed-width inner container (e.g. `width: 1280px`) and scale it via CSS `transform: scale()` with `transform-origin: top left`, or wrap it in a container that uses `aspect-ratio` + `width: 100%` so the inner contents scale uniformly.
- The outer wrapper of the product visual must have `overflow: hidden` and a defined aspect ratio so scaled content does not push surrounding sections.
- Do not use absolute pixel positioning for floating accent cards — anchor them with percentages or `inset` values so they track the base UI as it scales.
- Avoid fixed `min-width` on inner elements (tables, sidebars, KPI rows) that would force horizontal overflow before the wrapper scales.
- Text inside the product UI uses relative units (`em`, `rem`) so it scales with the surface; do not hard-code `font-size` in `px` on inner elements unless the entire block is also pixel-sized.
- Verify the product visual at three widths: ~1440px (desktop), ~768px (tablet), ~375px (mobile). The composition should look identical at all three — just smaller — with no clipped content, no horizontal scrollbars, and no broken floating-accent positions.

*Populate every slot with realistic content — never skeleton-shimmer placeholders*
A code-rendered product visual must read as an actual snapshot of the product working, not as a loading state. Every text slot in the mockup must contain plausible-real text for the domain you're depicting; every avatar slot must show a real-looking name or initials drawn from the page's testimonial / team / customer data; every number slot must show a plausible value with units.
- For a recruiting-platform "candidate row" mockup: render real candidate names ("Anjali Krishnan", "Marcus Webb"), real roles ("Senior PM", "Staff Engineer"), real screening status ("Phone screen scheduled", "Score: 87%") — pull from `content.ts` (e.g. reuse the testimonial author names you already authored) or invent plausible-domain values consistent with the brand.
- For an analytics-card mockup: render real metric labels ("Daily Active Users", "Latency P99", "Pipeline value"), real numbers ("1,247 events / 24h", "3.2ms", "$284k"), real time ranges ("Last 30 days").
- For an audit/compliance mockup: render real control IDs ("CC-6.1 Access Revocation"), real status tags ("PASSING / FAILING / NEEDS REVIEW"), real evidence references ("iam_policy_snapshot.json — collected 2m ago").
- For an integrations mockup: render real connector names ("Stripe → Snowflake — 12,408 events synced"), real status ("Active", "Paused 3h ago", "Re-authorizing").

*Hard prohibition: skeleton-bar placeholders are forbidden inside rendered product visuals*
The shape that defines a skeleton-bar placeholder is *structural*, not color-specific: any **self-closing `<div />`** (or `<div>` with no rendered text/icon/data children) that combines a width class (`w-N`, `w-fraction`, `w-full`), a height class (`h-N`), and a background-color class — used in place of a label, name, value, paragraph, status pill, chart, or tag — is a skeleton bar regardless of which color token is used.

Forbidden color tokens (non-exhaustive — the rule covers *any* color, including ones not listed here when used in the structural shape above):
- Neutral palette: `bg-gray-*`, `bg-neutral-*`, `bg-slate-*`, `bg-zinc-*`, `bg-stone-*` (typical on light-themed iters)
- Opacity-suffix variants: `bg-white/N`, `bg-black/N`, `bg-current/N`, `bg-{any-color}/N` for any N (typical on dark-themed iters — `bg-white/5`, `bg-white/10`, `bg-white/20`, `bg-white/40`, `bg-white/60` are all the same anti-pattern as `bg-gray-200` on a light surface; tested in the wild on app 87e87bb8 where the model used `bg-white/N` to evade an earlier version of this rule that only listed neutral-palette tokens)
- Brand-tinted variants: `bg-{accent}/N`, `bg-[#hex]/N`, `bg-[hexcolor]` solid pills with no label inside

Specific shapes that count as skeleton bars and must not appear:
- `<div className="h-N w-M {bg-color} rounded" />` (self-closing, no children) — fake text/label/value/paragraph
- `<div className="px-N py-N {bg-color} rounded-full w-N h-N" />` (self-closing) — fake status pill or tag chip
- Avatar circles containing only single letters generated from indices (`String.fromCharCode(64 + i)` → "A", "B", "C") instead of real names or initials
- Card chrome (browser traffic-light dots, dark header bar, generic "PASSING" badge) without any populated content inside the card body
- Tinted-brand-color rectangles standing in for "a chart" or "a data viz" with no actual lines, bars, axes, labels, or numeric ticks
- Stacks of `<div>` rows where the rows differ only by `w-N` width — that's a "skeleton paragraph" regardless of which color the rows use

These shapes visually mimic broken-raster failures even though the underlying mechanism is different. Reviewers cannot tell them apart on screenshot, so they read as the same defect. Use real values; if you cannot invent realistic-domain values, render fewer/simpler UI elements (a sparkline with real axis labels, an icon + label pair, a single-row example) populated with real content instead of a wider mockup populated with placeholders.

Self-check before returning: scan your own output for any self-closing `<div ... />` whose className contains a `bg-*` class and a width-or-height class but no children. Every such element inside a rendered product visual must be reworked into a populated element (with real text, real icon, real value) — or removed.

*Wrong vs right (worked example for a "How it works" candidate-screening mockup)*

Wrong — skeleton bars, indexed-letter avatars, empty pills:

```tsx
<div className="flex items-center gap-4 p-4 rounded-2xl border border-gray-100">
  <div className="h-12 w-12 rounded-full bg-white flex items-center justify-center font-bold text-gray-400">
    {String.fromCharCode(64 + i)}
  </div>
  <div className="flex-1">
    <div className="h-4 w-32 bg-gray-200 rounded mb-2"></div>
    <div className="h-3 w-24 bg-gray-100 rounded"></div>
  </div>
  <div className="h-8 w-16 bg-[#1A4331]/10 rounded-full" />
</div>
```

Right — real values, real labels, real status pill text:

```tsx
{[
  { name: "Anjali Krishnan", role: "Senior Product Manager", status: "Score 92" },
  { name: "Marcus Webb", role: "Staff Engineer", status: "Score 88" },
  { name: "Yuki Tanaka", role: "Design Lead", status: "Score 84" },
].map((c) => (
  <div key={c.name} className="flex items-center gap-4 p-4 rounded-lg border border-gray-100">
    <div className="h-12 w-12 rounded-full bg-[#1A4331]/10 flex items-center justify-center font-medium text-[#1A4331] text-sm">
      {c.name.split(" ").map((n) => n[0]).join("")}
    </div>
    <div className="flex-1">
      <div className={`${bodyFont.className} text-sm font-medium text-gray-900`}>{c.name}</div>
      <div className={`${bodyFont.className} text-xs text-gray-500`}>{c.role}</div>
    </div>
    <div className={`${bodyFont.className} px-3 py-1 rounded-lg bg-[#1A4331]/10 text-[#1A4331] text-xs font-medium`}>
      {c.status}
    </div>
  </div>
))}
```

Both versions are valid HTML/CSS. Only the right version is acceptable as authored output — the wrong version reads as a broken/loading state.

*Dark surfaces use layered grays, not pure black*
A dark product UI feels real because of its surface hierarchy. Near-black with pure-white text is the most common tell of generated dark mode. Follow the design-spec dark tokens when they exist; when they don't, use the layered-gray pattern below.
- Page background: a deep neutral in the `#0f1115`–`#16171a` range. Avoid `#000` and `#0a0a0a`.
- Card and panel surface: one step lighter than the page (e.g. `#1a1b1f`–`#1e2025`), with a subtle 1px border in a slightly lighter gray (`#26282d`) to define edges.
- Elevated surface (modals, popovers, dropdowns): two steps lighter than the page.
- Primary text: `#e6e8eb`–`#f0f2f5`. Avoid pure `#fff` — it vibrates against dark surfaces.
- Secondary/meta text: a desaturated mid-gray (`#9ba1a8`–`#a7adb4`).
- Accent colors (status, links, primary actions) keep their saturation but are used sparingly — one accent per surface, not on every card.

# Self-validate before returning

Before returning your output, validate it against every check below. If any
check fails, revise the code and validate again.

1. The block has a single dominant base UI; accent cards overlap or anchor to it rather than floating in empty space.
2. The background treatment is intentional and, across multiple product sections, varies between at least 2 modes.
3. The densest component (table, list, feed) shows enough data that pagination or scroll would realistically be needed.
4. Sibling cards or tiles in the same row share identical surface treatment.
5. At least one filter, sort, search, or date-range affordance is visible on every data view.
6. Each row in a list or table carries 4+ distinct signals.
7. All content inside dashboards, tables, KPI cards, and list rows is left-aligned, with numeric columns right-aligned. No `text-align: center` appears on any product-chrome element (centering is allowed only on empty states, modal confirmation copy, auth screens, and short standalone CTAs).
8. No emoji appears anywhere in the product UI — every icon, status glyph, and marker is a Lucide icon (`lucide-react` in JSX, inline Lucide SVG in plain HTML/CSS).
9. Only regular (400) and medium (500) font weights are used — no semibold, bold, or weight above 500 anywhere.
10. Dark themes use layered grays for page → surface → elevated, with off-white (not pure white) primary text.
11. The product UI block scales proportionally at narrow viewports — wrapper has `overflow: hidden` and a defined aspect ratio, floating accents use percentage-based positioning, and the composition remains intact at ~1440px, ~768px, and ~375px.
12. No skeleton-bar placeholders appear anywhere in the product visual: no self-closing `<div />` with `bg-*` + width + height and no children standing in for a label, value, status pill, paragraph, or chart. Every text slot, avatar slot, and number slot carries real domain-appropriate content; avatar circles render real initials drawn from named data, never indexed letters (`String.fromCharCode(64 + i)`).
