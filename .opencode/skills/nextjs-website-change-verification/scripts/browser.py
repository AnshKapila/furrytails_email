"""Playwright control + page stabilization + scroll-and-extract loop."""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any, Optional

from config import ScanConfig
from extraction import EXTRACTION_JS, _raw_to_element
from models import Viewport, ViewportSnapshot
from playwright.async_api import async_playwright

logger = logging.getLogger("qa_scanner")


# React/Next.js hydration-mismatch console.error signatures. We do NOT treat
# every console.error as fatal — favicon 404s, third-party script noise, and
# benign dev warnings would flood the gate. We only flag messages carrying
# these React hydration markers, which always mean the server and client
# rendered different trees (the user sees a flash, a layout snap, or a blank
# region). An uncaught `pageerror` is captured unconditionally below — it needs
# no allowlist because it already aborted a render.
_HYDRATION_MARKERS = (
    "hydration failed",
    "while hydrating",
    "did not match",
    "text content does not match",
    "hydration mismatch",
    "server-rendered html",
    "server rendered html",
)

# Mirrors html-generation's runtime_render checker: an unhandledrejection has
# no synchronous throw site, so an in-page listener is the only way to see it.
# Buffered on `window` and drained after the scan settles.
_RUNTIME_INIT_SCRIPT = """
window.__runtimeErrors = [];
window.addEventListener('unhandledrejection', function (e) {
    var reason = e.reason;
    window.__runtimeErrors.push({
        kind: 'unhandledrejection',
        message: String((reason && reason.message) || reason),
        stack: (reason && reason.stack) || ''
    });
});
"""


class BrowserController:
    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._current_viewport = Viewport(width=width, height=height)
        # pageerror / hydration-console / crash events, collected via listeners
        # attached at launch so nothing fires before we are listening.
        self._runtime_errors: list[dict] = []

    @property
    def page(self):
        assert self._page is not None, "Call launch() first"
        return self._page

    @property
    def current_viewport(self) -> Viewport:
        return self._current_viewport

    def _on_page_error(self, exc) -> None:
        message = getattr(exc, "message", None) or str(exc)
        self._runtime_errors.append(
            {"kind": "pageerror", "message": message, "stack": getattr(exc, "stack", "") or ""}
        )

    def _on_console(self, msg) -> None:
        if msg.type != "error":
            return
        text = msg.text or ""
        lowered = text.lower()
        if any(marker in lowered for marker in _HYDRATION_MARKERS):
            self._runtime_errors.append({"kind": "hydration", "message": text, "stack": ""})

    def _on_crash(self, _page) -> None:
        self._runtime_errors.append(
            {"kind": "crash", "message": "Renderer process crashed during render", "stack": ""}
        )

    async def launch(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context(
            viewport={"width": self._width, "height": self._height},
            color_scheme="dark",
        )
        self._page = await self._context.new_page()
        # Attach before any navigation so the first render's errors are caught.
        await self._page.add_init_script(_RUNTIME_INIT_SCRIPT)
        self._page.on("pageerror", self._on_page_error)
        self._page.on("console", self._on_console)
        self._page.on("crash", self._on_crash)

    async def navigate(self, url: str) -> None:
        # 30 s is tight enough to stay inside the 180 s validate_files.py cap
        # while still surfacing a hung server rather than silently burning budget.
        await self.page.goto(url, wait_until="domcontentloaded", timeout=30_000)

    async def collect_runtime_errors(self) -> list[dict]:
        """Drain runtime errors captured since launch (pageerror, hydration
        console.error, crash) merged with the in-page unhandledrejection buffer.

        Deduped by (kind, message): the same hydration error fires on every
        client re-render, and we want one finding per distinct cause.
        """
        errors = list(self._runtime_errors)
        try:
            in_page = await self.page.evaluate("() => window.__runtimeErrors || []")
            if isinstance(in_page, list):
                errors.extend(e for e in in_page if isinstance(e, dict))
        except Exception:
            pass

        seen: set[tuple] = set()
        out: list[dict] = []
        for e in errors:
            key = (e.get("kind"), e.get("message"))
            if key in seen:
                continue
            seen.add(key)
            out.append(e)
        return out

    async def evaluate(self, expression: str) -> Any:
        return await self.page.evaluate(expression)

    async def scroll_to(self, y: float) -> None:
        await self.page.evaluate(f"window.scrollTo(0, {y})")

    async def get_scroll_height(self) -> float:
        return await self.page.evaluate("document.documentElement.scrollHeight")

    async def get_page_title(self) -> str:
        return await self.page.title()

    async def close(self) -> None:
        # Each step is isolated so a crash at one level does not orphan the
        # remaining resources (Chromium process + Playwright driver subprocess).
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass


# Stamp elements that carry a RUNNING CSS animation before the disable CSS
# below zeroes every animation-duration. Extraction reads live computed styles
# *after* the disable CSS lands, so without this stamp every element reports
# 0s and the clipping detector's marquee/ticker suppressor
# (_has_running_animation) can never fire — a frozen marquee then reads as
# clipped text. Idempotent: re-runs after the disable CSS see 0s durations and
# stamp nothing new.
STAMP_ANIMATIONS_JS = """
() => {
    for (const el of document.querySelectorAll('*')) {
        if (el.hasAttribute('data-qa-animated')) continue;
        const style = getComputedStyle(el);
        const names = (style.animationName || 'none').split(',');
        if (names.every(n => { n = n.trim(); return n === '' || n === 'none'; })) continue;
        const durations = (style.animationDuration || '0s').split(',');
        if (durations.every(d => { d = d.trim(); return d === '' || d === '0s' || d === '0ms'; })) continue;
        el.setAttribute('data-qa-animated', '1');
    }
}
"""

# Hit-test every visible interactive element against the browser's REAL paint
# order. z-index arithmetic cannot resolve stacking contexts (transforms,
# opacity, isolation); document.elementFromPoint can — it also skips
# pointer-events:none overlays (scrims, gradients) automatically, so the most
# common intentional-overlay pattern self-suppresses.
#
# A target counts as blocked when ≥60% of its sampled points land on a foreign
# element (not an ancestor or descendant). Fixed/sticky blockers over
# in-flow targets are skipped — page content legitimately passes under a
# pinned navbar at some scroll offsets. A fixed blocker over a fixed target
# (a drawer overlay covering its own toggle button) stays flagged: that pair
# co-moves, so the blockage is scroll-independent and the control is dead.
#
# Blockers inside a dev-tooling / platform-injected overlay are ignored: the
# platform's own error overlay (``#custom-vite-error-overlay``), the Next.js
# dev error/toast portal, and the ``#kite-badge`` chip are not part of the
# generated site. When the error overlay is up the whole page is captured by
# it, which would otherwise flag every control as blocked and bury the real
# ``runtime-error`` finding under noise. This is a SUPERSET of
# ``_PLATFORM_ROOTS`` in app/services/qa_services/dom_extraction.js
# (``#custom-vite-error-overlay`` + ``#kite-badge``): the hit-test additionally
# ignores the Next.js dev portals. TODO: consolidate the overlay-selector
# lists into one shared source.
HIT_TEST_JS = """
() => {
    const OVERLAY_ROOTS = '#custom-vite-error-overlay, #kite-badge, nextjs-portal, ' +
        '[data-nextjs-dialog-overlay], [data-nextjs-toast], vite-error-overlay, #vite-error-overlay';
    function shortSelector(el) {
        if (el.id) return '#' + CSS.escape(el.id);
        const parts = [];
        let cur = el;
        while (cur && cur !== document.body && cur !== document.documentElement) {
            let sel = cur.tagName.toLowerCase();
            if (cur.id) { parts.unshift('#' + CSS.escape(cur.id)); break; }
            const parent = cur.parentElement;
            if (parent) {
                const sibs = Array.from(parent.children).filter(c => c.tagName === cur.tagName);
                if (sibs.length > 1) sel += ':nth-of-type(' + (sibs.indexOf(cur) + 1) + ')';
            }
            parts.unshift(sel);
            cur = cur.parentElement;
        }
        return parts.join(' > ');
    }
    function isFixedish(el) {
        let cur = el;
        while (cur && cur !== document.body) {
            const p = getComputedStyle(cur).position;
            if (p === 'fixed' || p === 'sticky') return true;
            cur = cur.parentElement;
        }
        return false;
    }
    function describe(el) {
        const r = el.getBoundingClientRect();
        return {
            selector: shortSelector(el),
            tag_name: el.tagName.toLowerCase(),
            text: (el.textContent || '').trim().substring(0, 80),
            bbox: {x: r.x, y: r.y, width: r.width, height: r.height},
        };
    }

    const out = [];
    const INTERACTIVE = 'a[href], button, [role="button"], input[type="submit"], input[type="button"], summary';
    for (const el of document.querySelectorAll(INTERACTIVE)) {
        const r = el.getBoundingClientRect();
        if (r.width < 8 || r.height < 8) continue;
        if (r.bottom <= 0 || r.top >= innerHeight || r.right <= 0 || r.left >= innerWidth) continue;
        const style = getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') continue;
        if (parseFloat(style.opacity) === 0) continue;
        if (el.closest('[aria-hidden="true"]') || el.closest('[inert]')) continue;
        if (el.disabled) continue;

        const points = [
            [r.left + r.width * 0.5, r.top + r.height * 0.5],
            [r.left + r.width * 0.25, r.top + r.height * 0.3],
            [r.left + r.width * 0.75, r.top + r.height * 0.3],
            [r.left + r.width * 0.25, r.top + r.height * 0.7],
            [r.left + r.width * 0.75, r.top + r.height * 0.7],
        ];
        let tested = 0;
        const blockers = new Map();
        for (const [x, y] of points) {
            if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) continue;
            tested++;
            const hit = document.elementFromPoint(x, y);
            if (!hit || hit === el || el.contains(hit) || hit.contains(el)) continue;
            // A dev-tooling / platform overlay is not a real blocker — the
            // generated site does not ship it. Skip it like pointer-events:none.
            if (hit.closest(OVERLAY_ROOTS)) continue;
            blockers.set(hit, (blockers.get(hit) || 0) + 1);
        }
        if (tested < 3) continue;
        let blocker = null, count = 0;
        for (const [candidate, n] of blockers) {
            if (n > count) { blocker = candidate; count = n; }
        }
        if (!blocker || count < Math.ceil(tested * 0.6)) continue;
        // In-flow content sliding under a pinned bar is normal scrolling, not
        // a defect — only co-pinned or fully in-flow blockages count.
        if (isFixedish(blocker) && !isFixedish(el)) continue;
        out.push({
            target: describe(el),
            blocker: describe(blocker),
            blocked_ratio: count / tested,
        });
    }
    return out;
}
"""

# Detect a dev-server error overlay covering the page. A hydration mismatch or
# runtime throw makes Vite/Next mount a full-viewport error overlay; the site
# the user actually sees is not rendered. Any visual scan behind it measures a
# DOM the user never sees, so the whole scan is voided down to the runtime
# error. Only a viewport-scale overlay counts (a small toast is not an error
# state). Returns the overlay's text (the error message) or None.
ERROR_OVERLAY_JS = """
() => {
    const el = document.querySelector(
        '#custom-vite-error-overlay, [data-nextjs-dialog-overlay], ' +
        'vite-error-overlay, #vite-error-overlay'
    );
    if (!el) return null;
    const r = el.getBoundingClientRect();
    if (r.width < innerWidth * 0.5 || r.height < innerHeight * 0.5) return null;
    return ((el.innerText || 'dev server error overlay').trim()).slice(0, 500);
}
"""

DISABLE_ANIMATIONS_CSS = """
*, *::before, *::after {
    animation-duration: 0s !important;
    animation-delay: 0s !important;
    transition-duration: 0s !important;
    transition-delay: 0s !important;
    scroll-behavior: auto !important;
}
"""

LAYOUT_SNAPSHOT_JS = """
() => {
    const snapshot = {};
    const selectors = ['header', 'nav', 'main', 'footer', 'h1', 'h2', 'h3',
                        '[role="banner"]', '[role="navigation"]', '[role="main"]'];
    let idx = 0;
    for (const sel of selectors) {
        for (const el of document.querySelectorAll(sel)) {
            const rect = el.getBoundingClientRect();
            snapshot[`${sel}_${idx}`] = {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
            idx++;
        }
    }
    return snapshot;
}
"""

WAIT_IMAGES_JS = """
() => {
    const images = Array.from(document.images);
    return Promise.all(
        images.filter(img => !img.complete).map(img => new Promise((resolve) => {
            img.addEventListener('load', resolve);
            img.addEventListener('error', resolve);
            setTimeout(resolve, 3000);
        }))
    );
}
"""


async def stabilize_page(ctrl: BrowserController, config: ScanConfig) -> None:
    page = ctrl.page
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=config.STABILIZATION_TIMEOUT)
    except Exception:
        pass

    # Must run before DISABLE_ANIMATIONS_CSS zeroes the durations it inspects.
    try:
        await page.evaluate(STAMP_ANIMATIONS_JS)
    except Exception:
        pass

    for attempt in range(3):
        try:
            await page.add_style_tag(content=DISABLE_ANIMATIONS_CSS)
            break
        except Exception:
            if attempt < 2:
                await asyncio.sleep(0.3)

    try:
        await page.evaluate("document.fonts.ready")
    except Exception:
        pass
    try:
        await page.evaluate(WAIT_IMAGES_JS)
    except Exception:
        pass
    try:
        await page.wait_for_load_state("networkidle", timeout=config.STABILIZATION_TIMEOUT)
    except Exception:
        pass

    # Dual-snapshot stability check
    snapshot_a = await ctrl.evaluate(LAYOUT_SNAPSHOT_JS)
    await asyncio.sleep(config.STABILITY_DELAY)
    snapshot_b = await ctrl.evaluate(LAYOUT_SNAPSHOT_JS)

    if isinstance(snapshot_a, dict) and isinstance(snapshot_b, dict):
        t = config.STABILITY_THRESHOLD
        for key in snapshot_a:
            if key in snapshot_b:
                a, b = snapshot_a[key], snapshot_b[key]
                if any(abs(a.get(k, 0) - b.get(k, 0)) > t for k in ("x", "y", "width", "height")):
                    logger.debug("Layout not fully stable at snapshot")
                    break


async def scroll_and_extract(
    ctrl: BrowserController,
    config: ScanConfig,
) -> AsyncGenerator[ViewportSnapshot, None]:
    viewport = ctrl.current_viewport
    scroll_height = await ctrl.get_scroll_height()
    step = viewport.height * (1.0 - config.SCROLL_OVERLAP)
    current_y = 0.0
    snap_index = 0

    # Prepare screenshots directory once (None = skip)
    screenshots_dir = config.screenshots_dir
    if screenshots_dir is not None:
        os.makedirs(screenshots_dir, exist_ok=True)

    while current_y < scroll_height:
        await ctrl.scroll_to(current_y)
        await stabilize_page(ctrl, config)

        raw_elements = await ctrl.evaluate(EXTRACTION_JS)
        elements = []
        for raw in raw_elements or []:
            el = _raw_to_element(raw)
            if el:
                elements.append(el)

        # Z-order hit-test at this scroll position — needs the live page, so
        # it runs here rather than in a pure detector. Best-effort.
        blocked_hits: list = []
        try:
            blocked_hits = await ctrl.evaluate(HIT_TEST_JS) or []
        except Exception:
            logger.debug("Hit-test failed at scroll_y=%s", current_y)

        # Capture viewport screenshot — store raw bytes for per-issue cropping
        screenshot_path: Optional[str] = None
        screenshot_bytes: Optional[bytes] = None
        if screenshots_dir is not None:
            screenshot_path = os.path.join(
                screenshots_dir, f"scroll_{int(current_y):06d}_{snap_index:03d}.png"
            )
            try:
                screenshot_bytes = await ctrl.page.screenshot(type="png")
                with open(screenshot_path, "wb") as _f:
                    _f.write(screenshot_bytes)
            except Exception:
                logger.debug("Screenshot failed at scroll_y=%s", current_y)
                screenshot_path = None
                screenshot_bytes = None

        snap_index += 1

        yield ViewportSnapshot(
            viewport=Viewport(width=viewport.width, height=viewport.height, scroll_y=current_y),
            scroll_position=current_y,
            elements=elements,
            url=ctrl.page.url,
            page_title=await ctrl.get_page_title(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            screenshot_path=screenshot_path,
            screenshot_bytes=screenshot_bytes,
            blocked_hits=blocked_hits,
        )

        current_y += step
        new_height = await ctrl.get_scroll_height()
        if new_height > scroll_height:
            scroll_height = new_height
