"""DOM extraction — JavaScript injected into the page + Python-side adapters.

``EXTRACTION_JS`` is evaluated once per scroll position by the browser layer.
The resulting raw dicts are converted to ``ElementData`` by ``_raw_to_element``.
"""

from __future__ import annotations

from typing import Optional

from models import (
    RGBA,
    ROLE_BODY_TEXT,
    ROLE_BUTTON_TEXT,
    ROLE_CAPTION,
    ROLE_DECORATIVE,
    ROLE_HEADING,
    ROLE_LABEL,
    ROLE_LINK,
    BoundingBox,
    ElementData,
)

EXTRACTION_JS = """
() => {
    function getUniqueSelector(el) {
        if (el.id) return '#' + CSS.escape(el.id);
        if (el === document.body) return 'body';
        if (el === document.documentElement) return 'html';

        const parts = [];
        let current = el;
        while (current && current !== document.body && current !== document.documentElement) {
            let selector = current.tagName.toLowerCase();
            if (current.id) {
                selector = '#' + CSS.escape(current.id);
                parts.unshift(selector);
                break;
            }
            const parent = current.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(
                    c => c.tagName === current.tagName
                );
                if (siblings.length > 1) {
                    const index = siblings.indexOf(current) + 1;
                    selector += ':nth-of-type(' + index + ')';
                }
            }
            parts.unshift(selector);
            current = current.parentElement;
        }
        return parts.join(' > ');
    }

    // Reusable 1×1 canvas for resolving any CSS color format to raw RGBA bytes.
    // Canvas fillStyle always converts lab/oklch/hsl/etc. to sRGB internally,
    // so getImageData always returns correct bytes regardless of input format.
    const _colorCanvas = document.createElement('canvas');
    _colorCanvas.width = 1; _colorCanvas.height = 1;
    const _colorCtx = _colorCanvas.getContext('2d');

    function resolveColor(colorStr) {
        _colorCtx.clearRect(0, 0, 1, 1);
        _colorCtx.fillStyle = colorStr;
        _colorCtx.fillRect(0, 0, 1, 1);
        const d = _colorCtx.getImageData(0, 0, 1, 1).data;
        return { r: d[0], g: d[1], b: d[2], a: parseFloat((d[3] / 255).toFixed(4)) };
    }

    function parseColor(colorStr) {
        if (!colorStr || colorStr === 'transparent') return { r: 0, g: 0, b: 0, a: 0 };
        if (colorStr.startsWith('rgb')) {
            const match = colorStr.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
            if (match) {
                return {
                    r: parseInt(match[1]),
                    g: parseInt(match[2]),
                    b: parseInt(match[3]),
                    a: match[4] !== undefined ? parseFloat(match[4]) : 1.0,
                };
            }
        }
        // Fall back to canvas-based resolution for lab(), oklch(), hsl(), etc.
        return resolveColor(colorStr);
    }

    function getStackingOrder(el) {
        let order = 0;
        let current = el;
        while (current && current !== document.documentElement) {
            const style = getComputedStyle(current);
            const z = parseInt(style.zIndex) || 0;
            order += z;
            current = current.parentElement;
        }
        return order;
    }

    function isVisible(el, style) {
        if (style.display === 'none') return false;
        if (style.visibility === 'hidden') return false;
        if (parseFloat(style.opacity) === 0) return false;
        if (el.getAttribute('aria-hidden') === 'true') return false;
        if (el.hasAttribute('hidden')) return false;
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) return false;
        if (style.clip === 'rect(0px, 0px, 0px, 0px)') return false;
        if (style.clipPath === 'inset(50%)') return false;
        if (parseFloat(style.fontSize) === 0) return false;
        if (rect.width <= 1 && rect.height <= 1 && style.overflow === 'hidden') return false;
        let parent = el.parentElement;
        while (parent && parent !== document.body) {
            const ps = getComputedStyle(parent);
            if (ps.display === 'none' || ps.visibility === 'hidden') return false;
            if (parseFloat(ps.opacity) === 0) return false;
            if (parent.getAttribute('aria-hidden') === 'true') return false;
            parent = parent.parentElement;
        }
        return true;
    }

    function getParentSelector(el) {
        const parent = el.parentElement;
        if (!parent || parent === document.documentElement || parent === document.body) return null;
        return getUniqueSelector(parent);
    }

    const elements = [];
    const allEls = document.querySelectorAll(
        'body *:not(script):not(style):not(link):not(meta):not(noscript):not(br):not(hr)'
    );

    for (const el of allEls) {
        const style = getComputedStyle(el);
        const rect = el.getBoundingClientRect();

        if (rect.width === 0 && rect.height === 0 && style.display === 'none') continue;
        if (rect.bottom < -100 || rect.top > window.innerHeight + 100) continue;

        const textContent = (el.textContent || '').trim().substring(0, 200);
        const hasOwnText = Array.from(el.childNodes).some(
            n => n.nodeType === Node.TEXT_NODE && n.textContent.trim().length > 0
        );

        elements.push({
            has_own_text: hasOwnText,
            selector: getUniqueSelector(el),
            tag_name: el.tagName.toLowerCase(),
            text_content: textContent,
            bbox: {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
            },
            computed_styles: {
                display: style.display,
                position: style.position,
                overflow: style.overflow,
                'overflow-x': style.overflowX,
                'overflow-y': style.overflowY,
                'z-index': style.zIndex,
                opacity: style.opacity,
                visibility: style.visibility,
                color: style.color,
                'background-color': style.backgroundColor,
                'background-image': style.backgroundImage,
                'filter': style.filter,
                'mix-blend-mode': style.mixBlendMode,
                '-webkit-text-fill-color': style.webkitTextFillColor,
                'font-size': style.fontSize,
                cursor: style.cursor,
                'animation-name': style.animationName,
                'animation-duration': style.animationDuration,
                'qa-animated': el.getAttribute('data-qa-animated') || '',
            },
            z_index: parseInt(style.zIndex) || 0,
            stacking_order: getStackingOrder(el),
            is_visible: isVisible(el, style),
            parent_selector: getParentSelector(el),
            overflow: style.overflow,
            scroll_width: el.scrollWidth,
            scroll_height: el.scrollHeight,
            foreground_color: parseColor(style.color),
            background_color: parseColor(style.backgroundColor),
            font_size: parseFloat(style.fontSize) || 16,
            opacity: parseFloat(style.opacity) || 1.0,
            position: style.position,
            aria_role: el.getAttribute('role'),
        });
    }
    return elements;
}
"""


def _classify_semantic_role(raw: dict) -> str:
    tag = raw.get("tag_name", "").lower()
    aria = (raw.get("aria_role") or "").lower()
    styles = raw.get("computed_styles", {})

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6") or aria == "heading":
        return ROLE_HEADING
    if tag == "button" or aria == "button":
        return ROLE_BUTTON_TEXT
    if tag == "input" and styles.get("type") in ("submit", "button", "reset"):
        return ROLE_BUTTON_TEXT
    if tag == "a" or aria == "link":
        return ROLE_LINK
    if tag == "label" or aria == "label":
        return ROLE_LABEL
    if tag in ("figcaption", "caption") or aria == "caption":
        return ROLE_CAPTION
    if aria in ("presentation", "none"):
        return ROLE_DECORATIVE

    font_size = raw.get("font_size", 16)
    if isinstance(font_size, (int, float)) and font_size < 10:
        return ROLE_DECORATIVE

    return ROLE_BODY_TEXT


def _parse_rgba(raw: Optional[dict]) -> Optional[RGBA]:
    if not raw:
        return None
    return RGBA(
        r=int(raw.get("r", 0)),
        g=int(raw.get("g", 0)),
        b=int(raw.get("b", 0)),
        a=float(raw.get("a", 1.0)),
    )


# SVG-internal elements live in the SVG coordinate system (viewBox scaling,
# clipPath, transform chains) — CSS box semantics do not apply, so geometry
# checks on them are pure noise (an animated SVG dashboard reads as dozens of
# "clipped"/"overflowing" text nodes). The <svg> root itself stays: it IS a
# CSS box and participates in layout like an image.
_SVG_INTERNAL_TAGS = frozenset(
    {
        "g",
        "text",
        "tspan",
        "textpath",
        "path",
        "rect",
        "circle",
        "ellipse",
        "line",
        "polyline",
        "polygon",
        "defs",
        "use",
        "symbol",
        "marker",
        "clippath",
        "mask",
        "pattern",
        "foreignobject",
        "stop",
        "lineargradient",
        "radialgradient",
        "filter",
        "desc",
    }
)


def _raw_to_element(raw: dict) -> Optional[ElementData]:
    try:
        if raw.get("tag_name", "").lower() in _SVG_INTERNAL_TAGS:
            return None
        bbox_raw = raw["bbox"]
        return ElementData(
            selector=raw["selector"],
            tag_name=raw["tag_name"],
            text_content=raw.get("text_content", ""),
            bbox=BoundingBox(**bbox_raw),
            computed_styles=raw.get("computed_styles", {}),
            z_index=raw.get("z_index", 0),
            stacking_order=raw.get("stacking_order", 0),
            is_visible=raw.get("is_visible", True),
            parent_selector=raw.get("parent_selector"),
            overflow=raw.get("overflow", "visible"),
            scroll_width=raw.get("scroll_width", 0),
            scroll_height=raw.get("scroll_height", 0),
            semantic_role=_classify_semantic_role(raw),
            foreground_color=_parse_rgba(raw.get("foreground_color")),
            background_color=_parse_rgba(raw.get("background_color")),
            font_size=raw.get("font_size", 16),
            opacity=raw.get("opacity", 1.0),
            position=raw.get("position", "static"),
            aria_role=raw.get("aria_role"),
            has_own_text=bool(raw.get("has_own_text", True)),
        )
    except Exception:
        return None
