"""Contrast detection — axe-core.

axe walks the visual stacking context, so it correctly resolves the painted
background for text overlaying absolute-positioned siblings (the "image card
with overlay text" pattern). The previous DOM-parent-walk APCA implementation
systematically false-positived on that pattern and was removed.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional

from models import (
    CONF_HIGH,
    CONF_MEDIUM,
    RGBA,
    ROLE_BODY_TEXT,
    ROLE_BUTTON_TEXT,
    ROLE_HEADING,
    ROLE_LINK,
    SEV_CRITICAL,
    SEV_HIGH,
    TYPE_CONTRAST,
    BoundingBox,
    ContrastIssue,
    ElementData,
    Viewport,
)

logger = logging.getLogger("qa_scanner")

_AXE_PATHS = (
    # Kite e2b template installs node + axe-core under /top/node — this is
    # the canonical path. The /usr/local + /usr fallbacks match Debian npm-global
    # defaults for other sandbox images.
    "/top/node/lib/node_modules/axe-core/axe.min.js",
    "/usr/local/lib/node_modules/axe-core/axe.min.js",
    "/usr/lib/node_modules/axe-core/axe.min.js",
)


def _load_axe_js() -> Optional[str]:
    """Return the contents of axe.min.js from the sandbox npm-global install,
    or ``None`` if not found. The e2b template installs axe-core@4.10.2 via
    ``npm install -g``; ``AXE_JS_PATH`` env var overrides for local dev."""
    override = os.environ.get("AXE_JS_PATH")
    candidates = (override, *_AXE_PATHS) if override else _AXE_PATHS
    for p in candidates:
        if p and os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    return f.read()
            except OSError as exc:
                logger.warning("axe.min.js read failed at %s: %s", p, exc)
    return None


def _coerce_float(value: Any, default: float) -> float:
    """Parse a numeric value that axe-core may return as a number or as a
    WCAG criterion string like ``"4.5:1"``. Falls back to ``default`` on
    anything unparseable so a single malformed node cannot abort the scan."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", value)
        if match:
            return float(match.group(1))
    return default


_HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
# Cap on heading-with-undeterminable-background candidates per scan — each one
# costs an AI verification call. Anything beyond the cap is logged, not silent.
_MAX_HEADING_INCOMPLETE = 5


def _hex_to_rgba(s: str) -> RGBA:
    """Parse axe's color string (``#rrggbb``, ``#rrggbbaa``, ``rgb(...)`` etc.)
    into an RGBA. Defaults gracefully on malformed input."""
    if not isinstance(s, str):
        return RGBA(0, 0, 0, 1.0)
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        try:
            if len(h) == 6:
                return RGBA(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
            if len(h) == 8:
                return RGBA(
                    int(h[0:2], 16),
                    int(h[2:4], 16),
                    int(h[4:6], 16),
                    int(h[6:8], 16) / 255.0,
                )
        except ValueError:
            pass
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", s)
    if m:
        return RGBA(
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3)),
            float(m.group(4)) if m.group(4) else 1.0,
        )
    return RGBA(0, 0, 0, 1.0)


_AXE_PROBE_JS = r"""
(axe_js_marker) => {
    // axe.min.js was injected via add_script_tag immediately before this call.
    // "incomplete" results are requested too: axe files near-invisible text
    // (exact 1:1 contrast) and text over gradients/images/overlapped
    // backgrounds there, not under violations.
    return axe.run(document, {runOnly:['color-contrast'], resultTypes:['violations', 'incomplete']})
        .then((res) => {
            const fmtNode = (n, kind, fallbackImpact) => {
                // Extract the contrast data + check message from any/all/none checks
                let data = null;
                let message = '';
                for (const key of ['any', 'all', 'none']) {
                    for (const c of (n[key] || [])) {
                        if (!message && c.message) message = c.message;
                        if (c.data && typeof c.data.contrastRatio === 'number') {
                            data = c.data;
                            break;
                        }
                    }
                    if (data) break;
                }
                // Violations are deterministic — require numeric contrast data.
                // Incomplete nodes often lack it (that is *why* they are incomplete).
                if (kind === 'violation' && !data) return null;
                // Look up the element + bbox so downstream cropping works.
                const targetArr = n.target || [];
                const sel = targetArr.flat().join(' > ');
                let bbox = null;
                let tag = '';
                let text = '';
                try {
                    const el = document.querySelector(sel);
                    if (el) {
                        const r = el.getBoundingClientRect();
                        bbox = {x: r.x + window.scrollX, y: r.y + window.scrollY, width: r.width, height: r.height};
                        tag = el.tagName.toLowerCase();
                        text = (el.textContent || '').trim().substring(0, 80);
                    }
                } catch (e) {}
                // axe returns expectedContrastRatio as a WCAG criterion
                // string like "4.5:1" or "3:1" — strip the ":1" suffix
                // so the Python side gets a plain numeric ratio.
                let expected = data ? data.expectedContrastRatio : 4.5;
                if (typeof expected === 'string') {
                    expected = parseFloat(expected) || 4.5;
                } else if (typeof expected !== 'number') {
                    expected = 4.5;
                }
                return {
                    kind: kind,
                    message: message,
                    selector: sel,
                    tag: tag,
                    text: text,
                    bbox: bbox,
                    ratio: data ? data.contrastRatio : null,
                    expected: expected,
                    fg: (data && data.fgColor) || '#000000',
                    bg: (data && data.bgColor) || '#ffffff',
                    impact: n.impact || fallbackImpact || 'serious',
                    html: (n.html || '').substring(0, 200),
                };
            };
            const out = [];
            for (const v of (res.violations || [])) {
                for (const n of (v.nodes || [])) {
                    const e = fmtNode(n, 'violation', v.impact);
                    if (e) out.push(e);
                }
            }
            for (const v of (res.incomplete || [])) {
                for (const n of (v.nodes || [])) {
                    const e = fmtNode(n, 'incomplete', v.impact);
                    if (e) out.push(e);
                }
            }
            return out;
        });
}
"""


async def detect_contrast_via_axe(page: Any, viewport: Viewport, url: str) -> Optional[list]:
    """Run axe-core color-contrast against the page. One call per scan run,
    not per scroll position — axe inspects the full DOM regardless of viewport
    scroll.

    Returns ``None`` if axe isn't available or its run errored (caller should
    fall back). Returns ``[]`` when axe ran successfully and found zero
    violations — a real "clean page" result that must NOT trigger fallback.
    """
    axe_js = _load_axe_js()
    if not axe_js:
        return None
    try:
        await page.add_script_tag(content=axe_js)
        # ``axe.run`` returns a Promise; Playwright awaits it.
        raw = await page.evaluate(_AXE_PROBE_JS, "v1")
    except Exception as exc:  # noqa: BLE001 — axe runtime failures should not abort the whole scan
        logger.warning("axe-core run failed: %s", exc)
        return None

    issues: list = []
    heading_candidates = 0
    heading_dropped = 0
    for n in raw or []:
        kind = n.get("kind", "violation")
        bbox_d = n.get("bbox") or {}
        bbox = BoundingBox(
            x=float(bbox_d.get("x", 0)),
            y=float(bbox_d.get("y", 0)),
            width=float(bbox_d.get("width", 0)),
            height=float(bbox_d.get("height", 0)),
        )
        fg = _hex_to_rgba(n.get("fg", "#000000"))
        bg = _hex_to_rgba(n.get("bg", "#ffffff"))
        tag = (n.get("tag") or "").lower() or "?"
        text = n.get("text") or "?"
        ratio = _coerce_float(n.get("ratio"), 0.0)
        expected = _coerce_float(n.get("expected"), 4.5)

        if kind == "violation":
            # Graduated deficit gate: severity scales with how far below the
            # WCAG threshold the text falls. Borderline failures (deficit
            # < 1.5, e.g. 3.5:1 body text needing 4.5:1) are skipped — they
            # generate too much noise on intentionally muted text.
            deficit = expected - ratio
            if deficit >= 3.0:
                sev = SEV_CRITICAL
            elif deficit >= 1.5:
                sev = SEV_HIGH
            else:
                continue
            needs_verification = False
            confidence = 0.95
            conf_level = CONF_HIGH
            reasoning = (
                f"<{tag}> ('{text}') WCAG contrast {ratio:.2f}:1 "
                f"(needs {expected}:1). fg={n.get('fg')}, bg={n.get('bg')}."
            )
        else:
            # axe "incomplete": no deterministic ratio. Two actionable cases —
            # near-invisible text (axe reports exact 1:1 as incomplete, not a
            # violation) and headings whose background axe could not resolve
            # (text over image/gradient/overlapping elements). Both are
            # candidates that MUST pass AI vision verification.
            message = n.get("message") or ""
            if not text or text == "?":
                continue
            if "1:1 contrast ratio" in message:
                sev = SEV_CRITICAL
                reasoning = (
                    f"<{tag}> ('{text}') has ~1:1 contrast with its background "
                    f"(near-invisible text). axe: {message}"
                )
            elif tag in _HEADING_TAGS:
                if heading_candidates >= _MAX_HEADING_INCOMPLETE:
                    heading_dropped += 1
                    continue
                heading_candidates += 1
                sev = SEV_HIGH
                reasoning = (
                    f"<{tag}> ('{text}') contrast could not be determined by axe "
                    f"({message or 'undetermined background'}); needs visual check."
                )
            else:
                continue
            needs_verification = True
            confidence = 0.6
            conf_level = CONF_MEDIUM
        semantic_role = (
            ROLE_HEADING
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6")
            else ROLE_BUTTON_TEXT
            if tag == "button"
            else ROLE_LINK
            if tag == "a"
            else ROLE_BODY_TEXT
        )
        # Synthetic ElementData — only fields used downstream by dedup,
        # cropping, code-matching, and report rendering are populated.
        synth_elem = ElementData(
            selector=n.get("selector") or "?",
            tag_name=tag,
            text_content=text,
            bbox=bbox,
            computed_styles={},
            z_index=0,
            stacking_order=0,
            is_visible=True,
            parent_selector=None,
            overflow="visible",
            scroll_width=bbox.width,
            scroll_height=bbox.height,
            semantic_role=semantic_role,
            foreground_color=fg,
            background_color=bg,
            font_size=16.0,
            opacity=1.0,
            position="static",
            aria_role=None,
            has_own_text=True,
        )
        issues.append(
            ContrastIssue(
                issue_type=TYPE_CONTRAST,
                severity=sev,
                confidence_score=confidence,
                confidence_level=conf_level,
                viewport=viewport,
                scroll_position=bbox.y,
                url=url,
                reasoning=reasoning,
                element=synth_elem,
                foreground_color=fg,
                background_color=bg,
                contrast_lc=ratio,  # WCAG ratio in the Lc field — different scale, same role
                required_lc=expected,
                semantic_role=semantic_role,
                needs_ai_verification=needs_verification,
            )
        )
    if heading_dropped:
        logger.info(
            "contrast: %d heading incomplete result(s) beyond the cap of %d dropped",
            heading_dropped,
            _MAX_HEADING_INCOMPLETE,
        )
    return issues
