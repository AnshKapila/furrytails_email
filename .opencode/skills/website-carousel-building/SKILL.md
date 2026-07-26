---
name: website-carousel-building
description: >
  Use this skill when building or editing a carousel, slider, marquee, image
  gallery, testimonial rotator, logo strip, hero rotator, or swipeable card row
  — for example "make the testimonials slide", "add a logo marquee", "change
  the autoplay speed", or "turn this grid into a carousel". Detect whether the
  site is single-file HTML or Next.js, then use that framework's pattern below.
mode: both
---

# Carousel Rules

Choose the implementation from the existing project before writing code:

- **Next.js:** use this path when `package.json` depends on `next` and the
  project has an `app/`, `src/app/`, or `pages/` directory. Skip the CDN rules
  and use the React + Tailwind patterns in the Next.js section.
- **Single-file HTML:** use this path when the target is an `.html` file with
  inline scripts and no framework build. Use the Embla CDN and DOM contract
  below.

The host project chooses the implementation; do not change frameworks for a
carousel. A loop, autoplay, control, timing, or item-count preference in the
current user request or requirements overrides this skill's default for that
setting.

Success means slides come from one data source, controls hide when nothing can
scroll, and navigation wraps unless the request explicitly disables looping.

In single-file HTML, never hand-roll a slider with `setInterval` and manual
transforms; use Embla. The Next.js stepped-slider pattern is state-driven, and
its optional autoplay interval only advances state and is cleared on unmount.

## Library setup (CDN, single-file prototype)

Add these scripts to `<head>` once per HTML file, alongside Tailwind and Lucide. Pin the version.

```html
<script src="https://unpkg.com/embla-carousel@8.3.0/embla-carousel.umd.js"></script>
<!-- Add plugins only when needed: -->
<script src="https://unpkg.com/embla-carousel-autoplay@8.3.0/embla-carousel-autoplay.umd.js"></script>
<script src="https://unpkg.com/embla-carousel-class-names@8.3.0/embla-carousel-class-names.umd.js"></script>
<script src="https://unpkg.com/embla-carousel-fade@8.3.0/embla-carousel-fade.umd.js"></script>
```

Globals exposed by these UMD builds: `EmblaCarousel`, `EmblaCarouselAutoplay`, `EmblaCarouselClassNames`, `EmblaCarouselFade`.

The prototype CDN allowlist already includes `unpkg`, so no config change is needed.

## Required DOM structure

```html
<div class="embla overflow-hidden" data-carousel>
  <div class="embla__container flex">
    <!-- slide width controls how many show at once: 100% = 1, 50% = 2, 33.333% = 3 -->
    <div class="embla__slide flex-[0_0_100%] min-w-0 px-3">...</div>
    <div class="embla__slide flex-[0_0_100%] min-w-0 px-3">...</div>
    <div class="embla__slide flex-[0_0_100%] min-w-0 px-3">...</div>
  </div>

  <!-- Optional controls -->
  <button class="embla__prev" aria-label="Previous slide">
    <i data-lucide="chevron-left"></i>
  </button>
  <button class="embla__next" aria-label="Next slide">
    <i data-lucide="chevron-right"></i>
  </button>
  <div class="embla__dots flex gap-2 justify-center mt-6"></div>
</div>
```

Required:

- **Infinite navigation loop is the default; autoplay is opt-in.** Every Kite
  carousel uses Embla's `loop: true` so prev/next wraps at the ends; rely on
  that default. Set `data-loop="false"` only when the user explicitly asks for
  a non-wrapping slider. Add `data-autoplay="…"` only when the user asks for
  auto-advance or for a logo marquee, partner/award strip, or hero rotator.
  Testimonials, products, and galleries move on user action unless the request
  explicitly asks for autoplay.
- Keep `overflow-hidden` on the **embla viewport** (the outer `.embla`), never
  on an ancestor containing a sticky element; use `overflow-clip` on that
  ancestor instead.
- Slides use `flex-[0_0_X%]` (or `basis-X`) plus `min-w-0` so they keep their fixed width inside the flex container.
- Use responsive widths for breakpoints: `flex-[0_0_100%] md:flex-[0_0_50%] lg:flex-[0_0_33.333%]`.
- Do **not** set a fixed pixel height on the container that animates between slides — use natural height or `items-stretch` + matching slide content heights.
- `.embla__prev`, `.embla__next`, and `.embla__dots` may live either **inside** `.embla` or in a **sibling block under the same direct parent** (e.g. a header bar above the viewport or a centered footer row). The init code searches `root` first, then `root.parentElement` if that parent holds exactly one `[data-carousel]`. When two or more carousels share a parent, every carousel's controls MUST live inside its own `.embla`, otherwise the wrong carousel's buttons get wired.

## Initialization in the single-file prototype

The prototype renders routes via `app.innerHTML = \`...\`` inside `<script id="main_script">`. Carousels must be **re-initialized after every route render**, mirroring how `lucide.createIcons()` is re-run.

Add an `initCarousels()` function and call it from inside `render()` right after `lucide?.createIcons()`. Track active instances so they can be destroyed before re-init to avoid leaks across navigations.

```js
let _emblaInstances = [];

function initCarousels() {
  // Tear down old instances from the previous route render
  _emblaInstances.forEach(api => api.destroy());
  _emblaInstances = [];

  document.querySelectorAll('[data-carousel]').forEach(root => {
    const opts = {
      loop: root.dataset.loop !== 'false',
      align: root.dataset.align || 'start',
      dragFree: root.dataset.dragFree === 'true',
      slidesToScroll: Number(root.dataset.slidesToScroll || 1),
    };

    const plugins = [];
    if (root.dataset.autoplay && typeof EmblaCarouselAutoplay !== 'undefined') {
      plugins.push(
        EmblaCarouselAutoplay({
          delay: Number(root.dataset.autoplay) || 4000,
          stopOnInteraction: false,
          stopOnMouseEnter: true,
        })
      );
    }
    if (root.dataset.fade === 'true' && typeof EmblaCarouselFade !== 'undefined') {
      plugins.push(EmblaCarouselFade());
    }

    const api = EmblaCarousel(root, opts, plugins);
    _emblaInstances.push(api);

    // Controls usually live inside `.embla`, but layouts that center the
    // arrows in a header bar above/below put them in a sibling block. Allow
    // either by searching the immediate parent only when it owns exactly
    // one carousel — otherwise controls of a neighbouring carousel could
    // be hijacked.
    const parent = root.parentElement;
    const controlsScope =
      parent && parent.querySelectorAll('[data-carousel]').length === 1 ? parent : root;
    const prevBtn = controlsScope.querySelector('.embla__prev');
    const nextBtn = controlsScope.querySelector('.embla__next');
    const dotsContainer = controlsScope.querySelector('.embla__dots');

    prevBtn?.addEventListener('click', () => api.scrollPrev());
    nextBtn?.addEventListener('click', () => api.scrollNext());

    // Dots (optional — only build if container present).
    // Dot colors live in inline styles, not Tailwind classes, because the
    // Tailwind CDN's JIT can miss utilities that are only toggled at runtime
    // (the active class is never present at page-load, so it does not always
    // make it into the generated stylesheet). Inline styles always win the
    // cascade and never depend on JIT detection.
    if (dotsContainer) {
      const DOT_IDLE_BG = 'rgb(209, 213, 219)'; // gray-300
      const DOT_ACTIVE_BG = 'rgb(17, 24, 39)'; // gray-900
      const dots = api.scrollSnapList().map((_, i) => {
        const b = document.createElement('button');
        b.className = 'embla__dot w-2 h-2 rounded-full transition-colors';
        b.style.backgroundColor = DOT_IDLE_BG;
        b.setAttribute('aria-label', `Go to slide ${i + 1}`);
        b.addEventListener('click', () => api.scrollTo(i));
        return b;
      });
      dotsContainer.replaceChildren(...dots);
      const sync = () => {
        const selected = api.selectedScrollSnap();
        dots.forEach((d, i) => {
          d.style.backgroundColor = i === selected ? DOT_ACTIVE_BG : DOT_IDLE_BG;
        });
      };
      api.on('select', sync);
      api.on('reInit', sync);
      sync();
    }

    // Hide controls when the carousel has nothing to scroll to.
    // With `loop: true`, Embla disables containScroll, so scrollSnapList()
    // returns one snap per slide even when all slides fit the viewport.
    // Use canScrollPrev/Next, which respect actual reachable extent.
    // Dots also hide on multi-card layouts (≥2 cards visible) because a
    // single-active-dot indicator is ambiguous when several slides share
    // the viewport — arrows still work.
    const syncControls = () => {
      const hasOverflow = api.canScrollPrev() || api.canScrollNext();
      const firstSlide = root.querySelector('.embla__slide');
      const viewportW = root.clientWidth || 1;
      const slideRatio = firstSlide
        ? firstSlide.getBoundingClientRect().width / viewportW
        : 1;
      const isSingleCardView = slideRatio >= 0.8;
      prevBtn?.classList.toggle('hidden', !hasOverflow);
      nextBtn?.classList.toggle('hidden', !hasOverflow);
      dotsContainer?.classList.toggle('hidden', !hasOverflow || !isSingleCardView);
    };
    api.on('reInit', syncControls);
    api.on('resize', syncControls);
    syncControls();

    // Loop self-check: if `loop: true` was requested but Embla silently
    // disabled it (slide count below the loop minimum for the chosen
    // slides-per-view), the carousel renders as a static row or a non-
    // wrapping slider. Log once so the failure surfaces during development
    // instead of looking like a "broken" carousel. End users see nothing.
    if (opts.loop) {
      const totalSlides = api.slideNodes().length;
      const visibleSlides = api.slidesInView().length || 1;
      const loopMin = visibleSlides * 2 + 1;
      if (totalSlides < loopMin) {
        // eslint-disable-next-line no-console
        console.warn(
          `[carousel] loop: true requested but ${totalSlides} slide(s) ` +
            `is below the loop minimum of ${loopMin} for ${visibleSlides}-per-view. ` +
            `Add ${loopMin - totalSlides} more slide(s) or reduce slides-per-view. ` +
            `Embla disables loop silently in this state.`
        );
      }
    }
  });
}
```

`initCarousels()` hides `.embla__prev` / `.embla__next` whenever the carousel has nothing to scroll to (e.g. responsive slide widths make all slides fit at a given breakpoint), and additionally hides `.embla__dots` on multi-card layouts (slide width < ~80% of the viewport — i.e. 2-per-view, 3-per-view, logo strips). Dots are only useful when one slide owns the viewport; once 2+ cards are visible at once, a single-active-dot indicator does not map to anything the user can point at. Keep both behaviors — `scrollSnapList().length` alone is misleading because `loop: true` disables Embla's `containScroll`, so it returns one snap per slide even when the viewport already holds them all. The 80% threshold lets the "85% mobile peek" pattern still show dots while every 50%/33%/logo-strip layout hides them.

## Verify the carousel can actually scroll

Because controls auto-hide when nothing scrolls and `loop: true` cannot wrap a too-short slide list cleanly, a carousel built with too few slides renders as a static row — even with manual prev/next, the wrap-around either flickers or refuses to scroll. Every Kite carousel uses `loop: true`, so the loop-minimum column below always applies. Check the slide budget against the desktop breakpoint (the breakpoint with the most slides per view, i.e. the smallest slide width):

| Slide width on desktop | Slides per view | Min items for clean loop |
| --- | --- | --- |
| `flex-[0_0_100%]` | 1 | 3 |
| `flex-[0_0_50%]` | 2 | 5 |
| `flex-[0_0_33.333%]` | 3 | 7 |

Apply the slides-per-view requested by the user prompt:

- `slides per view: 1` → `flex-[0_0_100%]`
- `slides per view: 2` → `flex-[0_0_100%] md:flex-[0_0_50%]`
- `slides per view: 3` → `flex-[0_0_100%] md:flex-[0_0_50%] lg:flex-[0_0_33.333%]`

Count the entries in the data array that drives `.embla__container`. When the count is below the desktop minimum above, the carousel will not loop cleanly at the most common viewport — Embla silently disables `loop` when the slide budget is too thin, and the carousel either renders as a static row (slides fit the viewport exactly) or behaves as a non-wrapping slider with dead ends. Two paths:

- **Existing section being converted (orchestrator gating active).** Do **not** invent placeholder slides, duplicate existing slides, or silently degrade. Stop the edit and report back with: how many items the section has now, how many are needed for the requested slides-per-view, and one suggested resolution. The orchestrator has already pre-queried the count and will ask the user before retrying.
- **Brand-new carousel section being authored from scratch.** Generate at least the loop-minimum number of slides for the requested slides-per-view from the user's brand, content, and conversation context — same authoring quality as the rest of the page. If the user explicitly capped the item count below the minimum ("a carousel of my 2 products"), drop down to 1-slide-per-view AND set `data-loop="false"` on the root so the carousel becomes a non-wrapping slider with working prev/next ends instead of a broken loop.

Inside `render()`:

```js
route.render(params);
lucide?.createIcons();
initCarousels();        // <-- add this
announcePageChange(route.title);
```

## Recipes

### 1. Testimonial / product slider (manual, infinite wrap)

```html
<div class="embla overflow-hidden" data-carousel>
  <div class="embla__container flex">
    <!-- Slides driven by data.testimonials -->
  </div>
  <div class="flex items-center justify-between mt-6">
    <div class="embla__dots flex gap-2"></div>
    <div class="flex gap-2">
      <button class="embla__prev p-2 rounded-full border" aria-label="Previous">
        <i data-lucide="chevron-left" class="w-4 h-4"></i>
      </button>
      <button class="embla__next p-2 rounded-full border" aria-label="Next">
        <i data-lucide="chevron-right" class="w-4 h-4"></i>
      </button>
    </div>
  </div>
</div>
```

Generate slides from JSON data, never hard-code them in markup:

```js
const slides = data.testimonials.map(t => `
  <div class="embla__slide flex-[0_0_100%] md:flex-[0_0_50%] min-w-0 px-3">
    <blockquote class="...">${t.quote}</blockquote>
    <cite class="...">${t.author}</cite>
  </div>
`).join('');
```

### 2. Logo strip — continuous infinite marquee

Use `loop: true` + Autoplay with a small delay and `playOnInit: true`. Set `slidesToScroll: 1` and `align: 'start'`. Embla handles the seamless wrap internally — **do not duplicate the first slide** like a hand-rolled marquee would.

```html
<div
  class="embla overflow-hidden"
  data-carousel
  data-loop="true"
  data-autoplay="1500"
  data-slides-to-scroll="1"
>
  <div class="embla__container flex items-center">
    <!-- one slide per logo, no duplicates -->
  </div>
</div>
```

Pair with `dragFree: true` (set `data-drag-free="true"`) for a wheel-like continuous feel.

### 3. Hero rotator with fade

```html
<script src="https://unpkg.com/embla-carousel-fade@8.3.0/embla-carousel-fade.umd.js"></script>

<div class="embla relative" data-carousel data-autoplay="6000" data-loop="true" data-fade="true">
  <div class="embla__container flex">
    <div class="embla__slide flex-[0_0_100%] min-w-0">
      <img src="..." class="w-full h-[70vh] object-cover" />
    </div>
    <!-- more slides -->
  </div>
</div>
```

Fade slides keep stacking-context; the viewport does **not** need `overflow-hidden` when fade is used. The base `initCarousels()` above already pushes `EmblaCarouselFade()` into `plugins` whenever `data-fade="true"` is set and the plugin script is loaded.

### 4. Cards that swipe on mobile, sit static on desktop

Apply `flex-[0_0_85%] md:flex-[0_0_33.333%]` on `.embla__slide` and leave the carousel root as `data-carousel` only (no `data-autoplay`). On mobile the section behaves as a swipeable list with infinite wrap when the user drags or taps the arrows; on desktop the slides fit a single row, `canScrollPrev/Next` return false, and `syncControls` hides the arrows so Embla becomes an inert layout. No viewport gating or `resize` listener needed. This pattern still has to satisfy the loop-minimum table — at `slides per view: 3` you need 7+ items, otherwise drop to 2 per view (5+ items) or 1 per view (3+ items).

## Editing rules

When the user asks to change a carousel:

1. **Adding or removing slides** → edit the **data array** in `<script id="content">`, not the markup template. The renderer regenerates DOM; the carousel reinitializes on next render. Embla recomputes its scroll snaps automatically.
2. **Change autoplay speed** → edit `data-autoplay="<ms>"` on the carousel root, not the script. One value, one source of truth.
3. **Toggle loop / dots / arrows** → flip the `data-*` attribute or remove/add the `.embla__dots` / `.embla__prev` / `.embla__next` element. The init script reads the DOM each time.
4. **Change slides-per-view** → edit the `flex-[0_0_X%]` utility class on `.embla__slide`. Use responsive variants for breakpoints — do not duplicate slides.
5. **Change dot or arrow styling** → edit the Tailwind classes on the dot template inside `initCarousels()` for size/shape/transition, and edit the `DOT_IDLE_BG` / `DOT_ACTIVE_BG` constants for active vs idle color (inline styles — Tailwind JIT can miss runtime-toggled utilities). Arrows still use Tailwind classes in markup on `.embla__prev` / `.embla__next`.
6. **Add a brand-new carousel section** → add the DOM structure + the data entries; you do not need to extend `initCarousels()` unless you introduce a new plugin variant (fade, class-names, autoplay).
7. **Fix a "stuck" carousel after route change** → confirm `initCarousels()` is called from `render()` after `lucide?.createIcons()`, and that the old instances are destroyed before re-init.

## Never do

- Apply scroll-reveal, fade-in, or any class that sets `transform` or `transition: transform …` to `.embla__container` (e.g. a `.reveal` / `.animate-in` / `data-aos` class on the same element). Embla owns the `transform` of that element and writes `translate3d(...)` on every tick — a transform `transition` makes every drag and snap animate over the reveal duration (carousel looks stuck), and the pre-active `translateY(...)` makes Embla measure a translated container. Put reveal classes on the outer `.embla` viewport or a wrapping section instead.
- Duplicate the first slide manually for a "seamless loop". Embla's `loop: true` handles wrap-around. Duplicates create double-render artifacts on resize.
- Render carousel slides directly into HTML markup when the data lives in the JSON `<script id="content">` block — keep one source of truth.
- Wire prev/next/dots before `EmblaCarousel(...)` is constructed — `api.scrollSnapList()` returns empty until init.
- Add a global `.embla__slide { flex: 0 0 X% }` rule (or any other global `.embla__slide` width / `flex-basis` selector) in a `<style>` block or external stylesheet. Slide widths belong on the per-slide Tailwind class (`flex-[0_0_X%]`, `md:flex-[0_0_50%]`, etc.) so every carousel on the page can pick its own slides-per-view. A global rule loaded after the Tailwind CDN wins the cascade and silently overrides every carousel's intended width — including the one you just authored.

## Next.js patterns

Next.js templates ship no carousel package. Build moving sections from React
and Tailwind already in the project. Keep slide content in one array; for an
embedded-CMS block, map the block's prop array according to `cms-management`
and preserve the schema/component/renderer registration triple. These patterns
have no carousel-package dependency; do not install or branch on
`embla-carousel-react`.

### Pattern selector

| Request | Pattern |
| --- | --- |
| Swipeable cards or galleries on mobile, static grid on desktop | Scroll-snap row |
| Testimonial/image slider with arrows or dots; hero rotator | Stepped slider |
| Logo strip, ticker, continuous motion | CSS marquee |

Prefer scroll snap when the design does not require arrows, dots, or
auto-advance. It needs no client-side state.

### Scroll-snap row

```tsx
<div className="flex snap-x snap-mandatory gap-6 overflow-x-auto px-6 scroll-px-6 md:grid md:grid-cols-3 md:overflow-visible md:px-0">
  {items.map((item) => (
    <div key={item.id} className="w-[85%] shrink-0 snap-start md:w-auto">
      {/* card */}
    </div>
  ))}
</div>
```

### Stepped slider

Use a client component because state and click handlers require `'use client'`.
Track one index, wrap it with modulo arithmetic, and translate one strip inside
an overflow-hidden viewport.

```tsx
'use client';

import { useState } from 'react';

type Testimonial = { id: string; quote: string; name: string; role: string };

export function TestimonialSlider({ items }: { items: Testimonial[] }) {
  const [index, setIndex] = useState(0);
  const step = (delta: number) =>
    setIndex((current) => (current + delta + items.length) % items.length);

  return (
    <div>
      <div className="overflow-hidden">
        <div
          className="flex transition-transform duration-500 ease-out"
          style={{ transform: `translateX(-${index * 100}%)` }}
        >
          {items.map((item, itemIndex) => (
            <div
              key={item.id}
              className="w-full shrink-0 px-3"
              aria-hidden={itemIndex !== index}
            >
              {/* slide */}
            </div>
          ))}
        </div>
      </div>
      <div className="mt-6 flex items-center justify-between">
        <div className="flex gap-2">
          {items.map((item, itemIndex) => (
            <button
              key={item.id}
              aria-label={`Go to slide ${itemIndex + 1}`}
              onClick={() => setIndex(itemIndex)}
              className={`h-2 w-2 rounded-full ${itemIndex === index ? 'bg-current' : 'bg-current/30'}`}
            />
          ))}
        </div>
        <div className="flex gap-2">
          <button onClick={() => step(-1)} aria-label="Previous slide">Previous</button>
          <button onClick={() => step(1)} aria-label="Next slide">Next</button>
        </div>
      </div>
    </div>
  );
}
```

For multi-card layouts, set each slide to `w-full md:w-1/2 lg:w-1/3` and
translate by `index * (100 / visibleSlides)` percent. For a hero rotator, stack
slides with `absolute inset-0` and toggle opacity instead of translating. Add an
interval only when the user asks for auto-advance, and clear it on unmount.

### CSS marquee

Duplicate the track exactly once and animate it to `-50%`. Mark the duplicate
half `aria-hidden` so assistive technology reads each item once.

```tsx
export function LogoMarquee({ logos }: { logos: string[] }) {
  const track = [...logos, ...logos];
  return (
    <div className="overflow-hidden">
      <style>{`@keyframes marquee { to { transform: translateX(-50%); } }`}</style>
      <div className="flex w-max items-center gap-16 [animation:marquee_30s_linear_infinite] motion-reduce:[animation:none]">
        {track.map((logo, index) => (
          <span key={logo + "-" + index} aria-hidden={index >= logos.length} className="shrink-0">
            {logo}
          </span>
        ))}
      </div>
    </div>
  );
}
```

Keep `overflow-hidden` on the track's direct parent and `w-max` on the moving
child. Use marquees only for decorative logos, short taglines, or repeated
brand words, not navigation or required reading.

### Next.js constraints

- Use only installed dependencies. Do not add carousel, slider, animation, or
  icon packages; use inline SVG for controls.
- Keep all repeated slide content in one mapped array.
- Use state-driven transitions for stepped sliders and CSS animation for
  marquees; do not mutate transforms on an interval.
- Let containers size to their content instead of animating height.
- Keep `'use client'` as the first statement in every stateful slider.
- Keep `overflow-hidden` off ancestors of sticky elements; use
  `overflow-clip` on those ancestors instead.

## Verify before returning

- For single-file HTML, confirm the `.embla` → `.embla__container` →
  `.embla__slide` hierarchy and call `initCarousels()` after each route render.
- Generate data-driven slides from their source array; do not duplicate content
  in markup.
- Keep slide widths on per-slide classes and meet the loop-minimum table for the
  selected slides per view: 3 slides for 1-per-view, 5 for 2-per-view, and 7
  for 3-per-view.
- Keep carousel-owned transforms free of reveal effects and interval-driven
  mutations, and keep sticky ancestors free of `overflow-hidden`.
- Confirm `data-carousel`, plugin scripts, and `.embla__prev`, `.embla__next`,
  and `.embla__dots` selectors match the initialization code.
- For Next.js, use only installed dependencies and confirm stateful sliders
  start with `'use client'`.
