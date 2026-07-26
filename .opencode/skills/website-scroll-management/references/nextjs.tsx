// Canonical website-scroll-management wrapper for App Router (Next.js) projects.
// Same DOM contract, data shape, and rules as the HTML build. Renders
// `<section>` for the three section patterns and `<nav>` for `scroll-spy`.
// Inline the matching `_init…` body from `references/init.js` where marked, or
// import a shared helper from `src/lib/website-scroll-management.ts`, and return its teardown
// from the effect. Chapter data comes from a typed `const chapters: Chapter[]`
// in `src/data/content.ts`. Mobile and reduced-motion fallbacks are the same.

"use client";
import { useEffect, useRef } from "react";

type ScrollPattern =
  | "sticky-text"
  | "horizontal-motion"
  | "timeline"
  | "scroll-spy";

export function ScrollLink({
  pattern,
  children,
  className = "",
}: {
  pattern: ScrollPattern;
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLElement>(null);
  const isSpy = pattern === "scroll-spy";
  const rootClass = isSpy ? className : `overflow-clip ${className}`.trim();

  useEffect(() => {
    const root = ref.current;
    if (!root) return;

    // Ancestor-overflow patch — mirror `_patchAncestorOverflow` from
    // references/init.js. Run BEFORE the pattern's own init below. Walk up to
    // and including `<body>` (stop before `<html>`); treat hidden/auto/scroll
    // on any axis as pin-breaking and swap to `clip`.
    const patched: { el: HTMLElement; o: string; x: string; y: string }[] = [];
    const breaks = (v: string) =>
      v === "hidden" || v === "auto" || v === "scroll";
    for (
      let el: HTMLElement | null = root;
      el && el !== document.documentElement;
      el = el.parentElement
    ) {
      const cs = getComputedStyle(el);
      if (
        !breaks(cs.overflow) &&
        !breaks(cs.overflowX) &&
        !breaks(cs.overflowY)
      )
        continue;
      const s = el.style;
      patched.push({ el, o: s.overflow, x: s.overflowX, y: s.overflowY });
      s.overflow = "clip";
    }

    // Inline the matching _init… function body from references/init.js here,
    // or import a shared helper from src/lib/website-scroll-management.ts. Return its
    // teardown from this effect alongside the overflow restore below.

    return () => {
      patched.forEach(({ el, o, x, y }) => {
        el.style.overflow = o;
        el.style.overflowX = x;
        el.style.overflowY = y;
      });
      // ...then the pattern's own teardown.
    };
  }, [pattern]);

  const attrs = {
    ref,
    className: rootClass,
    "data-website-scroll-management": true,
    "data-scroll-pattern": pattern,
  };

  return isSpy ? (
    <nav {...attrs}>{children}</nav>
  ) : (
    <section {...attrs}>{children}</section>
  );
}
