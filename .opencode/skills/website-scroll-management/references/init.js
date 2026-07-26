// Canonical website-scroll-management init code for the HTML single-file prototype.
// Transcribe verbatim into the one `<script id="main_script">` block and call
// `initScrollLinks()` from inside `render()` (after `initCarousels()`, before
// `announcePageChange(...)`). Re-runs per route render; tears down prior
// observers/listeners so they do not leak across SPA navigations.

let _scrollLinkInstances = [];

// `position: sticky` does not pin inside an ancestor whose `overflow` is
// `hidden`/`auto`/`scroll` on EITHER axis — that ancestor becomes the sticky
// element's scroll container, so the pinned viewport scrolls away vertically
// instead of holding (cards drift up and out, leaving blank space below). The
// single most common offender is `overflow-x: hidden` on `<body>` or a
// top-level page wrapper, added for the "no horizontal scroll on mobile" rule.
// Walk from the section root up to AND INCLUDING `<body>` (stop before
// `<html>` so the document keeps scrolling), swap the offending overflow to
// `overflow: clip` (clips visually, keeps the mobile guard, no scroll
// container). Return a restore fn so teardown puts the inline styles back.
function _patchAncestorOverflow(root) {
  const patched = [];
  const breaks = v => v === 'hidden' || v === 'auto' || v === 'scroll';
  for (
    let el = root;
    el && el !== document.documentElement;
    el = el.parentElement
  ) {
    const cs = getComputedStyle(el);
    if (!breaks(cs.overflow) && !breaks(cs.overflowX) && !breaks(cs.overflowY))
      continue;
    const s = el.style;
    patched.push({ el, o: s.overflow, x: s.overflowX, y: s.overflowY });
    s.overflow = 'clip';
  }
  return () =>
    patched.forEach(({ el, o, x, y }) => {
      el.style.overflow = o;
      el.style.overflowX = x;
      el.style.overflowY = y;
    });
}

function initScrollLinks() {
  _scrollLinkInstances.forEach(teardown => teardown());
  _scrollLinkInstances = [];

  document
    .querySelectorAll('[data-website-scroll-management]')
    .forEach(root => {
      const pattern = root.dataset.scrollPattern;
      if (pattern === 'sticky-text') {
        _scrollLinkInstances.push(_initStickyText(root));
      } else if (pattern === 'horizontal-motion') {
        _scrollLinkInstances.push(_initHorizontalMotion(root));
      } else if (pattern === 'timeline') {
        _scrollLinkInstances.push(_initTimeline(root));
      } else if (pattern === 'scroll-spy') {
        _scrollLinkInstances.push(_initScrollSpy(root));
      }
      // No matching pattern → static render, no init needed.
    });
}

function _initStickyText(root) {
  const chapters = root.querySelectorAll('[data-scroll-chapter]');
  const images = root.querySelectorAll(
    '[data-scroll-image] [data-chapter-index]'
  );
  if (chapters.length === 0) return () => {};

  const restoreOverflow = _patchAncestorOverflow(root);
  const reduceMq = window.matchMedia('(prefers-reduced-motion: reduce)');

  // Single-source-of-truth invariant: equal chapter and image counts. If they
  // drift, log once for the builder — end users see nothing.
  if (images.length && images.length !== chapters.length) {
    // eslint-disable-next-line no-console
    console.warn(
      `[website-scroll-management] sticky-text: ${chapters.length} chapter(s) but ${images.length} image(s). ` +
        `Each chapter must pair with exactly one [data-chapter-index] image.`
    );
  }

  const setActive = index => {
    root.dataset.activeIndex = String(index);
    images.forEach(img => {
      const visible = Number(img.dataset.chapterIndex) === index;
      img.style.opacity = visible ? '1' : '0';
      // Reduced motion: still swap (content parity — each chapter keeps its
      // image) but instantly, with no animated crossfade.
      img.style.transition = reduceMq.matches
        ? 'none'
        : 'opacity 250ms ease-out';
    });
  };
  setActive(0);

  // rootMargin biases the trigger to the viewport center: a chapter goes
  // "active" once its top crosses the 40% line from the top and before its
  // bottom crosses the 40% line from the bottom. That deadband keeps the swap
  // stable while the user pauses mid-chapter.
  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          setActive(Number(entry.target.dataset.chapterIndex));
        }
      });
    },
    { rootMargin: '-40% 0px -40% 0px', threshold: 0 }
  );
  chapters.forEach(c => observer.observe(c));
  return () => {
    restoreOverflow();
    observer.disconnect();
  };
}

function _initHorizontalMotion(root) {
  const viewport = root.querySelector('[data-scroll-viewport]');
  const strip = root.querySelector('[data-scroll-strip]');
  if (!viewport || !strip) return () => {};

  const restoreOverflow = _patchAncestorOverflow(root);
  // Self-heal: the strip is a flex item of the flex viewport, so without an
  // explicit width it shrinks to content and the panels' percentage bases
  // (flex-[0_0_40%]) resolve against that indefinite width — every card
  // collapses to a sliver and there is zero horizontal travel. Markup should
  // carry w-full; force it here in case it was dropped.
  const priorStripWidth = strip.style.width;
  strip.style.width = '100%';

  // Progressive enhancement: the strip is AUTHORED as a native swipe row
  // (`overflow-x-auto snap-x`, all breakpoints) so that with no JS — script
  // crashed, still loading mid-generation, or reduced motion — every card
  // stays reachable by swiping instead of being clipped beside a blank band.
  // When this init takes over on desktop it upgrades the strip: overflow
  // visible (the transform must move cards INTO view, not slide a scroll
  // container's box off-screen) and snap off. The static branches restore
  // the native swipe row.
  const upgradeStrip = () => {
    strip.style.overflowX = 'visible';
    strip.style.scrollSnapType = 'none';
    if (strip.scrollLeft) strip.scrollLeft = 0;
  };
  const restoreStrip = () => {
    strip.style.overflowX = '';
    strip.style.scrollSnapType = '';
  };
  const mq = window.matchMedia('(max-width: 767px)');
  const reduceMq = window.matchMedia('(prefers-reduced-motion: reduce)');
  // Reduced motion disables the pin entirely, same as the mobile branch:
  // without this gate the JS would still set a multi-viewport section height
  // and translate the strip while the author's reduce CSS has unpinned the
  // sticky — the strip drifts past a giant empty band.
  const isStatic = () => mq.matches || reduceMq.matches;

  let raf = 0;
  let inside = false;
  let pinRange = 0;
  let distance = 0;
  let resizeObs = null;
  let warnedNoTravel = false;

  const pace = () => {
    const n = parseFloat(root.dataset.scrollPace || '1.5');
    return Number.isFinite(n) && n > 0 ? n : 1.5;
  };

  // Init OWNS the section height. Measure real horizontal travel in pixels,
  // then size the pin range to it (× pace). Never trust an author-set vh
  // height: vw strip width and vh height drift apart (gaps, aspect ratio,
  // image load), which makes cards fly past before they enter / leaves blank
  // space below the pin.
  const layout = () => {
    if (isStatic()) {
      root.style.height = '';
      pinRange = 0;
      distance = 0;
      strip.style.transform = 'translate3d(0,0,0)';
      restoreStrip();
      return;
    }
    upgradeStrip();
    distance = Math.max(0, strip.scrollWidth - viewport.clientWidth);
    if (distance <= 0) {
      // Strip fits inside the viewport: there is nothing to translate, so do
      // NOT pin — a pinned range with zero travel reads as a dead stretch
      // where the user scrolls and the page appears frozen.
      root.style.height = '';
      pinRange = 0;
      strip.style.transform = 'translate3d(0,0,0)';
      restoreStrip();
      if (!warnedNoTravel && strip.children.length > 1) {
        warnedNoTravel = true;
        // eslint-disable-next-line no-console
        console.warn(
          '[website-scroll-management] horizontal-motion: strip is not wider than the viewport ' +
            `(scrollWidth ${strip.scrollWidth}px <= viewport ${viewport.clientWidth}px). ` +
            'Check the strip has w-full and panels use viewport-relative widths ' +
            '(flex-[0_0_40%] / w-[40vw]) — rendering static, no pin.'
        );
      }
      return;
    }
    warnedNoTravel = false;
    pinRange = distance * pace();
    root.style.height = `${pinRange + window.innerHeight}px`;
  };

  const update = () => {
    raf = 0;
    if (isStatic() || pinRange <= 0 || distance <= 0) {
      strip.style.transform = 'translate3d(0,0,0)';
      return;
    }
    const rect = root.getBoundingClientRect();
    const progress = Math.min(1, Math.max(0, -rect.top / pinRange));
    strip.style.transform = `translate3d(${-progress * distance}px, 0, 0)`;
  };

  const schedule = () => {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      layout();
      update();
    });
  };

  const onScroll = () => {
    if (!inside) return;
    if (raf) return;
    raf = requestAnimationFrame(update);
  };

  // Only listen to scroll while the pinned section is near the viewport.
  const gate = new IntersectionObserver(
    entries => {
      inside = entries[0]?.isIntersecting ?? false;
      if (inside) schedule();
    },
    { rootMargin: '0px', threshold: 0 }
  );
  gate.observe(root);
  resizeObs = new ResizeObserver(schedule);
  resizeObs.observe(strip);
  mq.addEventListener('change', schedule);
  reduceMq.addEventListener('change', schedule);
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', schedule, { passive: true });
  // Late-loading images change strip.scrollWidth — remeasure when they land.
  strip.querySelectorAll('img').forEach(img => {
    if (!img.complete) img.addEventListener('load', schedule, { once: true });
  });
  schedule();

  return () => {
    restoreOverflow();
    gate.disconnect();
    resizeObs?.disconnect();
    mq.removeEventListener('change', schedule);
    reduceMq.removeEventListener('change', schedule);
    window.removeEventListener('scroll', onScroll);
    window.removeEventListener('resize', schedule);
    if (raf) cancelAnimationFrame(raf);
    root.style.height = '';
    strip.style.transform = '';
    strip.style.width = priorStripWidth;
    restoreStrip();
  };
}

function _initTimeline(root) {
  const steps = root.querySelectorAll('[data-scroll-step]');
  if (steps.length === 0) return () => {};

  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          steps.forEach(s => (s.dataset.active = 'false'));
          entry.target.dataset.active = 'true';
          root.dataset.activeIndex = String(entry.target.dataset.chapterIndex);
        }
      });
    },
    { rootMargin: '-40% 0px -40% 0px', threshold: 0 }
  );
  steps.forEach(s => observer.observe(s));
  return () => observer.disconnect();
}

function _initScrollSpy(root) {
  // Each nav link's href="#…" names the section it points to. Pair links with
  // their target sections and let one observer flip the active link on scroll.
  const pairs = Array.from(root.querySelectorAll('a[href^="#"]'))
    .map(link => {
      const id = link.getAttribute('href').slice(1);
      const section = id ? document.getElementById(id) : null;
      return section ? { link, section } : null;
    })
    .filter(Boolean);
  if (pairs.length === 0) return () => {};

  const setActive = section => {
    pairs.forEach(({ link, section: s }) => {
      link.dataset.active = s === section ? 'true' : 'false';
    });
  };
  setActive(pairs[0].section);

  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          setActive(entry.target);
        }
      });
    },
    { rootMargin: '-40% 0px -40% 0px', threshold: 0 }
  );
  pairs.forEach(({ section }) => observer.observe(section));
  return () => observer.disconnect();
}
