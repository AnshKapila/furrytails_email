---
name: website-scroll-management
description: "Use this skill when a section pins an image while text or steps scroll past it, when cards move horizontally as the user scrolls vertically, when a vertical timeline highlights each step as it enters the viewport, or when a sidebar or top-bar nav reflects the section the user is scrolled to. Triggers on 'make the text and image scroll together', 'pin this image as I scroll', 'walk me through this as I scroll down', 'scroll-driven horizontal cards', 'highlight the current section as I scroll', 'the active nav stays stuck on Works', 'sticky image with scrolling chapters', 'pinned section with horizontal track', 'scrollytelling', 'scroll-spy sidebar'. Fire this even when the user just says 'the active link doesn't update' or 'the text doesn't match the image as I scroll'. For carousels the user navigates manually via prev/next, drag, dots, or autoplay, prefer the website-carousel-building skill instead — website-scroll-management is for UI driven strictly by page-scroll position."
mode: both
---

# Scroll-Link Rules

Use this skill for any UI whose state is driven strictly by page-scroll position — no clickable prev/next, no drag, no autoplay timer. Four patterns: `sticky-text` (pinned visual that swaps as chapters scroll past), `horizontal-motion` (pinned section whose inner track translates sideways as the page scrolls), `timeline` (vertical steps highlighted as they enter the viewport), and `scroll-spy` (nav whose active link follows the scrolled-to section).

## When to use

Reach for this skill when the spec or user asks for any of:

- A sticky image/video/product mock that stays pinned while text chapters scroll past, swapping per chapter.
- A horizontal strip of cards/panels that advances on vertical scroll, with no clickable controls.
- A vertical timeline/process whose active step is set by scroll position, not clicks.
- A sticky sidebar, top-bar, or table-of-contents nav whose active link should follow scroll position rather than the URL hash.
- Bug reports like "the text doesn't match the image when I scroll", "make this scroll smoothly", "pin this", "the active sidebar link stays on Works even when I scroll to Process".

Do **not** use this skill when:

- The user advances the section via button, drag, dot, or autoplay timer — that is a `website-carousel-building` task (mutually exclusive on a given section).
- The section is a pure CSS `scroll-snap` row with no chapter-text pairing and no horizontal pin — that is a styling concern.
- The user wants a decorative parallax background — that belongs in CSS rules, not this skill.

## Required DOM contract

Every scroll-linked UI is rooted at `[data-website-scroll-management]` and declares its pattern via `data-scroll-pattern`:

```html
<section
  class="overflow-clip"
  data-website-scroll-management
  data-scroll-pattern="sticky-text"  <!-- or "horizontal-motion", "timeline", or "scroll-spy" -->
>
  <!-- Pattern-specific markup, see recipes below -->
</section>
```

Required everywhere:

- **The contract is all-or-nothing — never ship the scaffold without the attributes and the init.** The motion is driven entirely by JS that the init code wires onto `[data-website-scroll-management]`. If you emit the *visual* scaffold of a pinned/horizontal section (a `sticky` + `h-screen` viewport, a `will-change-transform` flex strip, viewport-relative card widths like `w-[..vw]`/`flex-[0_0_..%]`) you MUST also add `data-website-scroll-management`, `data-scroll-pattern`, `data-scroll-viewport`, `data-scroll-strip` (and `data-chapter-index` where the pattern uses images) AND run the init. A scaffold without these attributes is a **dead strip**: nothing translates it, the off-screen cards stay clipped and unreachable, and the user sees cards fly past with blank space below. If you are not going to wire the full contract, render a plain **static** grid/row instead — never a half-built scroller.
- Exactly one of the four `data-scroll-pattern` values per root: `sticky-text`, `horizontal-motion`, `timeline`, or `scroll-spy`. The init code dispatches on this attribute.
- `overflow-clip` on section roots (`sticky-text`, `horizontal-motion`, `timeline`) or any ancestor that scopes their layout. **Never `overflow-hidden`/`auto`/`scroll` (any axis) on the section or ANY ancestor up to `<body>`** — each makes that ancestor the sticky element's scroll container, so the pinned viewport scrolls away vertically (cards drift up and out, blank space below) instead of holding. This includes `overflow-x-hidden` on `<body>`/page wrappers added for the mobile no-horizontal-scroll rule: use `overflow-x-clip` there. Init patches offending ancestors to `clip` as a safety net, but author the markup with `clip` so the pin is correct before JS runs. `scroll-spy` roots are usually `<nav>` and need no `overflow-clip` unless the nav itself clips children.
- Slot data (chapters, steps, panels) lives in a single shared array — JSON `<script id="content">` on the HTML build, or a typed `chapters` constant on Next.js. Strict invariant: one array row = one chapter element = one image (when the pattern uses images). Never parallel arrays.

### Pattern: `sticky-text` — sticky visual, scrolling text chapters

Use `sticky-text` whenever a pinned element on one side swaps/advances as text chapters scroll past it on the other. **The sticky element does not have to be an image** — a sticky **number, eyebrow, step label, or progress indicator** that advances per chapter is the same mechanic. A numbered "How it Works" / "Our process" / "what happens at each stage" section (a sticky `01 02 03 …` that follows the active step while the step copy scrolls) **is `sticky-text`**, not a custom build. Treat the number/label exactly like the image: one `[data-chapter-index]` element per chapter inside `[data-scroll-image]`, styled active via `[data-active="true"]`/opacity, driven by the single observer. Do not hand-roll a `translateY(-N%)` number reel against a scroll-progress divisor — that mis-maps the active step (skips the first, races the last), which is the failure this pattern exists to prevent.

An optional full-width header sits above a two-column grid pairing the sticky visual with the chapter stack as parallel columns.

```html
<section class="overflow-clip" data-website-scroll-management data-scroll-pattern="sticky-text">
  <header class="mb-16 max-w-2xl"><h2>...</h2><p>...</p></header>

  <div class="grid md:grid-cols-2 gap-12">
    <!-- Sticky image column. Image-left and image-right are both valid. -->
    <div class="hidden md:block">
      <div class="sticky top-24 h-[80vh]" data-scroll-image>
        <img data-chapter-index="0" src="..." class="absolute inset-0 w-full h-full object-cover" />
        <img data-chapter-index="1" src="..." class="absolute inset-0 w-full h-full object-cover" />
        <img data-chapter-index="2" src="..." class="absolute inset-0 w-full h-full object-cover" />
      </div>
    </div>

    <!-- Chapter column, parallel to the sticky image. -->
    <div class="space-y-[60vh]">
      <article data-scroll-chapter data-chapter-index="0">
        <img class="md:hidden mb-6 w-full" src="..." /><h3>...</h3><p>...</p>
      </article>
      <article data-scroll-chapter data-chapter-index="1">
        <img class="md:hidden mb-6 w-full" src="..." /><h3>...</h3><p>...</p>
      </article>
      <!-- ... -->
    </div>
  </div>
</section>
```

- Header lives above the grid, full-width. For "title on the left, content on the right", lift the title above the grid and use image-on-right (or -left) for the visual emphasis.
- Put the chapter stack in the column **parallel** to the sticky image. A chapter sharing the image's column ends up below it, and its observer fires while the chapter is still off-screen — the image swaps with no text beside it.
- The text column carries `space-y-[60vh]` (or similar) so each chapter has room to own the viewport while "active".
- The mobile-only `<img class="md:hidden mb-6 …">` inside each chapter is the stacked-fallback image; below `md:` the sticky column is hidden and each chapter renders its image inline.
- `data-chapter-index` MUST be on every chapter and every sticky image — the init code uses these to keep text and image in lockstep. No other matching mechanism is allowed.

### Pattern: `horizontal-motion` — pinned section, horizontal scroll track

```html
<section
  class="overflow-clip max-md:!h-auto"
  data-website-scroll-management
  data-scroll-pattern="horizontal-motion"
  data-scroll-pace="1.5"
>
  <!-- Optional section header: full-width, in normal flow ABOVE the sticky
       viewport. NEVER place it inside [data-scroll-viewport]. -->
  <header class="max-w-7xl mx-auto px-6 mb-12 leading-tight"><h2>...</h2><p>...</p></header>

  <div class="sticky top-0 h-screen flex items-center max-md:static max-md:h-auto" data-scroll-viewport>
    <div class="w-full flex items-stretch gap-6 will-change-transform overflow-x-auto snap-x" data-scroll-strip>
      <article class="flex-[0_0_80%] md:flex-[0_0_40%] min-w-0 h-[70vh] snap-center">...</article>
      <article class="flex-[0_0_80%] md:flex-[0_0_40%] min-w-0 h-[70vh] snap-center">...</article>
      <article class="flex-[0_0_80%] md:flex-[0_0_40%] min-w-0 h-[70vh] snap-center">...</article>
      <!-- N panels -->
    </div>
  </div>
</section>
```

- All cards are flex children of `[data-scroll-strip]`; init slides them with one `transform: translate3d(-Npx,0,0)` on the strip. `overflow-clip` on the section does the clipping. Never per-card absolute `left` math or scroll-progress conditional rendering — a `Math.max(0,x)` clamp pins off-screen cards onto the same x-position and stacks their text.
- **`w-full` on `[data-scroll-strip]` is mandatory.** The strip is a flex *item* of the flex viewport, so without an explicit width it shrinks to content — and the panels' percentage bases (`flex-[0_0_40%]`) resolve against that indefinite width, collapsing every card to a ~60px sliver with all panels visible at once and zero horizontal travel. `w-full` gives the percentages a definite, viewport-sized base. (Init also force-sets `width: 100%` at runtime as a self-heal, but author it in markup.)
- Panel widths are viewport-relative: `flex-[0_0_80%]` mobile, `flex-[0_0_40%]` desktop (or `flex-[0_0_33.333%]` for 3-up). Fixed-pixel widths (`w-[300px]`) collapse the strip under one viewport on desktop and make the motion invisible.
- **Do not set section height in markup.** `_initHorizontalMotion` measures `distance = strip.scrollWidth − viewport.clientWidth`, then sets `section height = (distance × pace) + window.innerHeight`; `pace` comes from `data-scroll-pace` (default `1.5`). When `distance ≤ 0` (strip fits in the viewport) the section is left at natural height — pinning with nothing to translate produces a dead stretch where the user scrolls and "nothing happens". A vh heuristic like `(panels × width% + 100)vh` is forbidden — vw strip width and vh height drift apart (gaps, aspect ratio, image load) and cards fly past before entering / leave blank space below.
- Panel height fills most of the pinned viewport: `h-[70vh]` (or `aspect-[3/4]` + `max-h-[80vh]`). The viewport is `h-screen` with `items-center`/`items-stretch`; panels under ~50vh leave empty bands above/below.
- `[data-scroll-viewport]` is the sticky frame; `[data-scroll-strip]` is the translating element. `will-change-transform` keeps the strip on its own GPU layer.
- **The section header/intro goes ABOVE `[data-scroll-viewport]`, in normal section flow — never inside it.** The viewport is `h-screen` and holds the full-height (`h-[70vh]`) strip; adding a header inside it (especially with `justify-center`) pushes the combined content past one viewport, and the section's `overflow-clip` then cuts the header's top off (clipped "Our gear" title). Keep the viewport's content to just the strip. Also avoid `leading-none` on a large display heading inside any `overflow-clip` scroll section — set `leading-tight` (or add `pb`) so tall ascenders/descenders are not clipped by the line box.
- **Progressive enhancement — author the strip as a native swipe row** (`overflow-x-auto snap-x`, all breakpoints, no `md:` overrides). The init code *upgrades* it on desktop when it takes over: it sets `overflow-x: visible` + `scroll-snap-type: none` inline (the transform must move cards INTO view, not slide a scroll container's box off-screen) and restores the swipe row on mobile, reduced motion, and teardown. This is the no-JS guarantee: if the runtime script is missing, still loading, or crashed, the section degrades to a swipeable row where every card stays reachable — never clipped cards beside a blank band.
- **Panel images must NOT use `loading="lazy"`.** Every panel except the first starts off-screen by design, so a lazy loader never fetches them until they scroll into view — but the JS reveals them via `transform`, not native scroll, so the loader never fires and the user sees empty/broken image boxes. Use `loading="eager"` (or omit `loading`) on `horizontal-motion` panel images and on every `[data-scroll-image]` in `sticky-text`.

### Pattern: `timeline` — vertical step reveal

```html
<section class="overflow-clip" data-website-scroll-management data-scroll-pattern="timeline">
  <ol class="relative space-y-32 border-l border-gray-200 pl-8">
    <li data-scroll-step data-chapter-index="0" data-active="false"><h3>...</h3><p>...</p></li>
    <li data-scroll-step data-chapter-index="1" data-active="false"><h3>...</h3><p>...</p></li>
    <!-- N steps -->
  </ol>
</section>
```

- Style the active step via `[data-active="true"]` selectors (weight, brand color, indicator dot). Init flips `data-active` on the step owning the viewport center and clears the others — only one is `true` at a time.

### Pattern: `scroll-spy` — nav active state follows scroll position

```html
<nav data-website-scroll-management data-scroll-pattern="scroll-spy">
  <a href="#works" data-active="true">Works</a>
  <a href="#process" data-active="false">Process</a>
  <a href="#about" data-active="false">About</a>
</nav>
```

Each target section elsewhere carries the matching `id` (`<section id="works">…`).

- Each link's `href="#…"` names its section. Init pairs each link with `getElementById`, watches each section with one observer, and sets `data-active="true"` on the link whose section owns the viewport center (others `false`).
- Style the active link via `[data-active="true"]` (bullet, weight, color) — same convention as `timeline`.
- Anchor clicks still work: the browser jumps to `#process`, then the next intersection callback confirms the active link.
- Use for sticky sidebar nav, top-bar tab strips, table-of-contents indicators, in-page progress dots. A `hashchange` listener alone fails — scrolling never changes the URL, so the active state would freeze on the last click.
- Safe outside long-pinned layouts: drop the nav wherever it lives (sticky sidebar, fixed top bar, in-flow header) and add the two `data-*` attributes; init finds it via the `data-website-scroll-management` root.

## Initialization (HTML single-file prototype)

The prototype renders routes via `app.innerHTML = \`...\`` inside `<script id="main_script">`, so scroll-linked sections must be **re-initialized after every route render** (like `lucide.createIcons()` / `initCarousels()`).

The canonical init code is in [`references/init.js`](references/init.js) — transcribe it **verbatim** into the one `<script id="main_script">` block. It defines `initScrollLinks()` plus the four per-pattern initializers and `_patchAncestorOverflow`, and tears down prior observers/listeners on each call to avoid leaks across SPA navigations. Do not re-derive this logic; the measured-height, ancestor-overflow, and single-observer details are load-bearing (see **Never do**).

Call it inside `render()`:

```js
route.render(params);
lucide?.createIcons();
initCarousels();
initScrollLinks();        // <-- add this
announcePageChange(route.title);
```

## Mobile fallback (always required)

Below `md:` every pattern degrades to a stacked layout — non-negotiable, since sticky+scroll-text and horizontal-pin do not fit narrow viewports and would break the "no horizontal scroll on mobile" design guarantee.

- **sticky-text**: hide the sticky column with `hidden md:block`; each chapter's own `md:hidden` image becomes the mobile view.
- **horizontal-motion**: `max-md:!h-auto` on the section, `max-md:static` on `[data-scroll-viewport]`. The strip is already a native swipe row (`overflow-x-auto snap-x`) and init does not upgrade it below `md`, so mobile gets the swipe row as-is. Init clears the JS height below `md` and does not translate. Stack vertically only if the spec asks.
- **timeline**: works as-is; just reduce vertical spacing under `md:`.

## Reduced-motion fallback (always required)

The init code checks `(prefers-reduced-motion: reduce)` itself and reacts live to changes: `_initHorizontalMotion` treats it exactly like the mobile branch (clears the JS-set section height, writes a zero translate, no pin), and `_initStickyText` still swaps images per chapter (content parity) but instantly, with no animated crossfade. `timeline`/`scroll-spy` only flip `data-active` state, which is safe.

Content stays reachable under reduce without extra classes: the strip is authored as a native swipe row and init only upgrades it to the translated overflow-visible mode when motion is allowed — under reduce it leaves (or restores) the swipe row, so every panel can still be swiped to. Wrap any other scroll-coupled decorative styles in `@media (prefers-reduced-motion: no-preference)`.

## Data shape (single source of truth)

Chapter/step/panel data lives in one shared array, never duplicated. Re-use `<script id="content">` on the HTML build and a typed `const chapters` on Next.js:

```json
{
  "chapters": [
    { "heading": "Discover", "body": "...", "image": "{IMAGE_BASE_URL}/process-discover.png" },
    { "heading": "Define",   "body": "...", "image": "{IMAGE_BASE_URL}/process-define.png" }
  ]
}
```

- `image` is required for `sticky-text` and `horizontal-motion`, optional for `timeline`.
- The renderer iterates `chapters` once to emit both the text markup and (for `sticky-text`) the sticky-image stack — one source array, two emit sites guarantees text[i] pairs with image[i].

## Editing rules

When the user asks to change a scroll-linked section:

1. **Add/remove a chapter** → edit the `chapters` array; the renderer regenerates DOM and `initScrollLinks()` re-runs on the next route render.
2. **Swap an image** → edit `chapters[i].image`; sticky stack and mobile inline image share the source.
3. **Reorder chapters** → reorder the array; `data-chapter-index` is emitted from the loop index, so indices stay consistent.
4. **Change the active deadband** → edit the `rootMargin` constants in `_initStickyText`/`_initTimeline` (`references/init.js`). Keep top/bottom inset symmetric so swaps happen at viewport center.
5. **Change scroll speed** (`horizontal-motion`) → edit `data-scroll-pace` on the section root (default `1.5`; higher = slower horizontal reveal). Do not set inline `height` — init measures the strip.
6. **Convert a static text+image grid into `sticky-text`** → add `data-website-scroll-management data-scroll-pattern="sticky-text"`, wrap the visual column in `[data-scroll-image]` with one image per chapter, tag each chapter with `data-scroll-chapter` + `data-chapter-index`, add the mobile fallback image inside each chapter, and add `overflow-clip` to the section. No JS changes needed.
7. **Fix a nav whose active link stays stuck as the user scrolls** → add `data-website-scroll-management data-scroll-pattern="scroll-spy"` on the `<nav>`, `data-active="false"` on each `<a>`, confirm each `href="#…"` matches an existing section `id`, and switch the active-item CSS to `[data-active="true"]`. Drop any `hashchange`/`location.hash` handler — the observer takes over.

## Never do

- Hand-roll a numbered "How it Works" / "Our process" section as a sticky `translateY(-N%)` number reel driven by a scroll-progress divisor. That is `sticky-text` with the number as the sticky visual — the divisor mis-maps the active step (first step never activates, last races by). Use the contract.
- Place the section header/intro inside `[data-scroll-viewport]` on `horizontal-motion`. The `h-screen` viewport already holds the full-height strip; a header inside it overflows the viewport and the section's `overflow-clip` cuts the header's top. Put the header above the viewport in normal flow.
- Apply `transition: transform`/`translate`/`top` to `[data-scroll-strip]`, the sticky element, or any transformed ancestor. `requestAnimationFrame` writes the transform every tick; a transition lags every frame. (Same family as the website-carousel-building skill's `.embla__container` rule.)
- Apply `.reveal`, `.animate-in`, `data-aos`, or any scroll-reveal class to `[data-scroll-image]`, `[data-scroll-strip]`, or their direct parents — they set their own `transform`/`transition` and fight the init code.
- Use `overflow-hidden`/`auto`/`scroll` (any axis, including `overflow-x-hidden` for the mobile guard) on a `[data-website-scroll-management]` section or ANY ancestor up to and including `<body>` that contains a `position: sticky` descendant. Each makes that element the sticky scroll container and breaks the pin — the strip scrolls up and out instead of staying fixed. Use `overflow-clip`/`overflow-x-clip` instead. This is the recurring root cause of "the horizontal section scrolls past before the images come in, with blank space below".
- Emit the pinned/horizontal **scaffold without the contract**: a `sticky h-screen` viewport or a `will-change-transform` flex strip of viewport-width cards that lacks `data-website-scroll-management`/`data-scroll-pattern`/`data-scroll-viewport`/`data-scroll-strip` and the init wiring. With no JS the strip never translates, `overflow` clips the off-screen cards, and the user sees them fly past with blank space below — this is the #1 recurring failure. Either wire the full contract or render a static grid; never the half-built middle.
- Put `loading="lazy"` on `horizontal-motion` panel images or `sticky-text` `[data-scroll-image]` images. Off-screen-by-design panels are revealed by `transform`, not native scroll, so a lazy loader never fires and the images render as empty/broken boxes. Use `loading="eager"` or omit it.
- Author `md:overflow-visible`/`md:snap-none` (or plain `overflow-visible`) on the strip. Overflow-visible is the *JS-upgraded* state, applied inline by init when it takes over — authoring it in markup removes the no-JS fallback, so a missing or crashed script leaves clipped, unreachable cards beside a blank band (the recurring "4th card cut off, no 5th/6th" bug). Author `overflow-x-auto snap-x` and let init upgrade.
- Run two `IntersectionObserver`s with different thresholds for the same section. The single observer in `_initStickyText` is what guarantees text[i] and image[i] stay in lockstep.
- Duplicate the chapter list across two arrays (one text, one images). Single source of truth in `chapters[]` only — drift is the most common "text doesn't match image" bug.
- Animate the sticky element's `height` between chapters — layout shift breaks the observer thresholds. Keep height fixed (`h-[80vh]`).
- Set inline `height`/`min-height` or a vh-based Tailwind height (`h-[340vh]`, `style="height: Nvh"`) on a `horizontal-motion` section. Init owns height from the measured strip; author-set vh heights are the #1 cause of cards flying past (range too short) and blank space below (range too long).
- Absolutely position each card in a `horizontal-motion` strip, or conditionally render cards by scroll progress. One `transform: translate3d` on `[data-scroll-strip]` slides every card together; per-card math (especially clamping `left` to a minimum of `0`) collapses off-screen-left cards onto the same x-position and stacks their text.
- Use `scroll-snap` on the page-level scroll container while a website-scroll-management section is pinned — the browser fights the rAF loop.
- Compute scroll progress against an arbitrary divisor (`-rect.top / (innerHeight*0.8)`, `-rect.top / 600`) without checking the section's real pin range. For any sticky pinned section with a scroll-driven animation, the pin range — `section.height − window.innerHeight` (minus the sticky `top` offset for `top-[Nvh]`) — must be **≥** the denominator used for `scrollProgress`. If the denominator exceeds the pin range, the animation only partly completes before the pin ends and elements are whisked away mid-animation.

## Next.js variant (when editing a Next.js project)

For App Router projects (`frontend/src/app/**` and similar), the same DOM contract, data shape, and rules apply. **Do NOT hand-roll a static `sticky` + `overflow` + `will-change-transform` row** — that is the dead-strip bug above, and it is the most common way this breaks in Next.js. Instead, wrap the section in the canonical `ScrollLink` **client component** (see [`references/nextjs.tsx`](references/nextjs.tsx)), which emits `data-website-scroll-management`/`data-scroll-pattern`, renders `<section>` for the three section patterns and `<nav>` for `scroll-spy`, and runs the ancestor-overflow patch. Inline the matching `_init…` body from `references/init.js`, or import a shared helper from `src/lib/website-scroll-management.ts`, and return its teardown from the effect. If you will not wire that client component and init, render a plain static grid instead — never a sticky/transform scaffold with no JS. Chapter data is a typed `const chapters: Chapter[]` in `src/data/content.ts`; panel images use `loading="eager"`. Mobile and reduced-motion fallbacks are identical.
