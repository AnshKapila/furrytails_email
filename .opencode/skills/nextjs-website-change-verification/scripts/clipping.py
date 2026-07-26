"""Clipping detection — content cut off by ``overflow:hidden|clip``."""

from __future__ import annotations

from config import ScanConfig
from dom import find_clip_ancestor, is_descendant_of, iter_ancestors
from models import (
    CONF_MEDIUM,
    SEV_CRITICAL,
    SEV_HIGH,
    SEV_LOW,
    SEV_MEDIUM,
    TYPE_CLIPPING,
    BoundingBox,
    ClippingIssue,
    ElementData,
    Viewport,
)

_MIN_VISIBLE_DIM = 50.0


def _is_meaningfully_visible(elem: ElementData, viewport: Viewport) -> bool:
    vp_box = BoundingBox(x=0, y=0, width=viewport.width, height=viewport.height)
    vis = elem.bbox.intersection_bbox(vp_box)
    if vis is None:
        return False
    return vis.width >= _MIN_VISIBLE_DIM and vis.height >= _MIN_VISIBLE_DIM


def _clipping_severity(ov_x: float, ov_y: float, elem: ElementData) -> str:
    total = ov_x + ov_y
    size = elem.bbox.width + elem.bbox.height
    ratio = total / max(size, 1)
    has_text = bool(elem.text_content.strip())
    if ratio > 0.3 and has_text:
        return SEV_CRITICAL
    if ratio > 0.15 and has_text:
        return SEV_HIGH
    if ratio > 0.05:
        return SEV_MEDIUM
    return SEV_LOW


def _clipped_region(elem: ElementData, ov_x: float, ov_y: float) -> BoundingBox:
    """Return the bounding box of the clipped region.

    When only one axis overflows return that strip.  When both axes overflow the
    actual clipped area is L-shaped; we return the full element bbox so the user
    can see the entire affected element rather than a tiny meaningless corner.
    """
    if ov_x > 0 and ov_y > 0:
        # L-shaped overflow — show the whole element so the crop is useful.
        return elem.bbox
    if ov_x > 0:
        return BoundingBox(
            x=elem.bbox.right - ov_x,
            y=elem.bbox.y,
            width=ov_x,
            height=elem.bbox.height,
        )
    return BoundingBox(
        x=elem.bbox.x,
        y=elem.bbox.bottom - ov_y,
        width=elem.bbox.width,
        height=ov_y,
    )


def _has_running_animation(elem: ElementData) -> bool:
    styles = elem.computed_styles or {}
    # Stamped by STAMP_ANIMATIONS_JS before the scanner's disable-animations
    # CSS zeroes every animation-duration; the live computed values below are
    # only truthful when extraction runs without that CSS (tests, direct use).
    if styles.get("qa-animated") == "1":
        return True
    names = str(styles.get("animation-name") or "none")
    if all(n.strip() in ("", "none") for n in names.split(",")):
        return False
    durations = str(styles.get("animation-duration") or "0s")
    return any(d.strip() not in ("", "0s", "0ms") for d in durations.split(","))


def _rides_animation(elem: ElementData, ancestor: ElementData, elem_map: dict) -> bool:
    """True when elem moves under a running CSS animation below ``ancestor``.

    A marquee/ticker is wide content carried across an ``overflow:hidden``
    edge by a CSS animation — the clipping is the design, and a static
    geometry snapshot of it reads as cut-off text (a frozen marquee always
    has letters split at both edges). Walk from elem up to the clipping
    ancestor: an animation anywhere on that path means elem's overflow is
    intentional motion, not a defect.
    """
    if _has_running_animation(elem):
        return True
    # Walk elem → clipping ancestor via the shared, cycle-safe (depth-capped)
    # traversal, stopping before the ancestor itself.
    for node in iter_ancestors(elem, elem_map):
        if node.selector == ancestor.selector:
            break
        if _has_running_animation(node):
            return True
    return False


def _animated_clip_hosts(elements: list, elem_map: dict) -> set:
    """Selectors of overflow-hidden elements whose overflow is animated content.

    These hosts fail the self-clip scroll-extent check by construction (the
    animated track is wider than the viewport on purpose), so the self-clip
    issue is suppressed for them. Their non-animated children still get the
    child-extends-beyond-ancestor check.
    """
    hosts: set = set()
    for elem in elements:
        if not _has_running_animation(elem):
            continue
        if elem.overflow in ("hidden", "clip"):
            hosts.add(elem.selector)
        ancestor = find_clip_ancestor(elem, elem_map)
        if ancestor:
            hosts.add(ancestor.selector)
    return hosts


def _overflow_is_informational(
    elem: ElementData, elements: list, elem_map: dict, threshold: float
) -> bool:
    """True when the element's clipped overflow involves actual content.

    A self-clip verdict is only a defect when the content being cut off is
    informational: the element's own text, a text/img descendant whose box
    extends past the element's bounds, or a text descendant whose own text
    overflows its box (a block child's bbox stops at the container even when
    its nowrap text runs past it — the overflow lives in its scroll extent).
    Purely decorative protrusions — an absolutely-positioned SVG wave, a
    background blob div — produce scroll-extent overflow on their section
    without any content crossing the edge, and clipping them IS the design
    (standard wave/curve divider technique).
    """
    if elem.has_own_text:
        return True
    for other in elements:
        if other.selector == elem.selector:
            continue
        if not (other.text_content.strip() or other.tag_name.lower() == "img"):
            continue
        if not is_descendant_of(other, elem.selector, elem_map):
            continue
        beyond_x = max(other.bbox.right - elem.bbox.right, elem.bbox.x - other.bbox.x)
        beyond_y = max(other.bbox.bottom - elem.bbox.bottom, elem.bbox.y - other.bbox.y)
        if beyond_x > threshold or beyond_y > threshold:
            return True
        if other.has_own_text and (
            other.scroll_width - other.bbox.width > threshold
            or other.scroll_height - other.bbox.height > threshold
        ):
            return True
    return False


# A carousel's slide series spans well past its clip viewport; a slightly
# overflowing (defective) card row does not. 1.5× keeps real layout breaks
# flagged while suppressing multi-slide tracks.
_CAROUSEL_SERIES_WIDTH_RATIO = 1.5


def _is_horizontal_carousel_series(
    elem: ElementData, ancestor: ElementData, elements: list
) -> bool:
    """True when ``elem`` is one slide of a horizontal series clipped by design.

    Carousels/sliders lay ≥3 same-tag siblings in one row whose combined span
    is far wider than the clipping ancestor — a static geometry snapshot sees
    the off-screen slides as "clipped content", but the clipping IS the
    mechanism of the component.
    """
    if not elem.parent_selector:
        return False
    siblings = [
        e
        for e in elements
        if e.parent_selector == elem.parent_selector and e.tag_name == elem.tag_name
    ]
    if len(siblings) < 3:
        return False
    same_row = [s for s in siblings if abs(s.bbox.y - elem.bbox.y) < max(elem.bbox.height, 1) * 0.5]
    if len(same_row) < 3:
        return False
    span = max(s.bbox.right for s in same_row) - min(s.bbox.x for s in same_row)
    return span >= ancestor.bbox.width * _CAROUSEL_SERIES_WIDTH_RATIO


def _hosts_horizontal_carousel(elem: ElementData, elements: list, elem_map: dict) -> bool:
    """True when a descendant slide-series makes ``elem`` a carousel viewport."""
    seen_parents: set = set()
    for e in elements:
        if not e.parent_selector or e.parent_selector in seen_parents:
            continue
        if e.parent_selector != elem.selector and not is_descendant_of(e, elem.selector, elem_map):
            continue
        seen_parents.add(e.parent_selector)
        if _is_horizontal_carousel_series(e, elem, elements):
            return True
    return False


def _is_defective_self_clip(
    elem: ElementData,
    ov_x: float,
    ov_y: float,
    elements: list,
    elem_map: dict,
    self_clip_threshold: float,
    child_clip_threshold: float,
) -> bool:
    """One home for the self-clip verdict: overflow big enough to matter,
    involving actual content, and not one of the intentional-design shapes.

    Each suppressor exists because a real component pattern reads as clipping
    in a static geometry snapshot; new ones belong HERE, not as extra clauses
    at the call site:
    - wave: a shallow (<12%) vertical-only bleed on a section container — the
      standard curved/diagonal divider technique.
    - carousel host: a horizontal slide series far wider than its viewport —
      the clipping IS the component's mechanism.
    - interactive reveal: a clickable card clipping sideways is a collapsed
      accordion (click to expand). Vertical text cut-off on clickable elements
      stays flagged — a card with its copy chopped at the bottom is still
      broken.
    - decorative-only overflow: nothing informational (own text, text/img
      descendant) crosses the edge.
    """
    if ov_x <= self_clip_threshold and ov_y <= self_clip_threshold:
        return False
    horizontal_only = ov_x > self_clip_threshold and ov_y <= child_clip_threshold
    is_wave = (
        ov_y > 0
        and ov_x == 0
        and ov_y / max(elem.bbox.height, 1) < 0.12
        and elem.tag_name.lower()
        in ("section", "div", "article", "main", "aside", "header", "footer")
    )
    if is_wave:
        return False
    if horizontal_only and _hosts_horizontal_carousel(elem, elements, elem_map):
        return False
    if horizontal_only and (elem.computed_styles or {}).get("cursor") == "pointer":
        return False
    return _overflow_is_informational(elem, elements, elem_map, child_clip_threshold)


def _is_defective_ancestor_clip(
    elem: ElementData,
    ancestor: ElementData,
    cx: float,
    cy: float,
    elements: list,
    child_clip_threshold: float,
) -> bool:
    """Verdict for Check 2 (child protrudes past an overflow:hidden ancestor).

    The one home for Check-2 suppressors, mirroring ``_is_defective_self_clip``
    — new ones belong HERE, not as inline clauses at the call site. A protrusion
    past the threshold is a defect unless it is one slide of a horizontal
    carousel series, where the clipping IS the component's mechanism.
    """
    if cx <= child_clip_threshold and cy <= child_clip_threshold:
        return False
    horizontal_only = cx > child_clip_threshold and cy <= child_clip_threshold
    if horizontal_only and _is_horizontal_carousel_series(elem, ancestor, elements):
        return False
    return True


def detect_clipping(
    elements: list, viewport: Viewport, scroll_y: float, url: str, config: ScanConfig
) -> list:
    issues = []
    elem_map = {e.selector: e for e in elements}
    threshold = config.MIN_OVERFLOW_PX
    self_clip_threshold = max(threshold, 25.0)
    child_clip_threshold = max(threshold, 10.0)
    animated_hosts = _animated_clip_hosts(elements, elem_map)

    for elem in elements:
        if not elem.is_visible or not elem.text_content.strip():
            continue
        if not _is_meaningfully_visible(elem, viewport):
            continue

        # Check 1: Self-clip (overflow:hidden element whose scrollWidth > clientWidth)
        if elem.overflow in ("hidden", "clip") and elem.selector not in animated_hosts:
            ov_x = max(0, elem.scroll_width - elem.bbox.width)
            ov_y = max(0, elem.scroll_height - elem.bbox.height)
            if _is_defective_self_clip(
                elem, ov_x, ov_y, elements, elem_map, self_clip_threshold, child_clip_threshold
            ):
                parts = []
                if ov_x > 0:
                    parts.append(f"{ov_x:.0f}px horizontally")
                if ov_y > 0:
                    parts.append(f"{ov_y:.0f}px vertically")
                text = elem.text_content[:50] or elem.tag_name
                issues.append(
                    ClippingIssue(
                        issue_type=TYPE_CLIPPING,
                        severity=_clipping_severity(ov_x, ov_y, elem),
                        confidence_score=0.0,
                        confidence_level=CONF_MEDIUM,
                        viewport=viewport,
                        scroll_position=scroll_y,
                        url=url,
                        reasoning=(
                            f"<{elem.tag_name}> ('{text}') has content overflowing by "
                            f"{' and '.join(parts)} with overflow:hidden."
                        ),
                        clipped_element=elem,
                        clipping_ancestor=elem,
                        clipped_region=_clipped_region(elem, ov_x, ov_y),
                        overflow_x=ov_x,
                        overflow_y=ov_y,
                    )
                )

        # Check 2: Element extends beyond overflow:hidden ancestor
        if elem.parent_selector:
            ancestor = find_clip_ancestor(elem, elem_map)
            if (
                ancestor
                and ancestor.selector != elem.selector
                and not _rides_animation(elem, ancestor, elem_map)
            ):
                cx = max(0, elem.bbox.right - ancestor.bbox.right)
                cy = max(0, elem.bbox.bottom - ancestor.bbox.bottom)
                cx = max(cx, max(0, ancestor.bbox.x - elem.bbox.x))
                cy = max(cy, max(0, ancestor.bbox.y - elem.bbox.y))
                if _is_defective_ancestor_clip(
                    elem, ancestor, cx, cy, elements, child_clip_threshold
                ):
                    text = elem.text_content[:50] or elem.tag_name
                    parts = []
                    if cx > 0:
                        parts.append(f"{cx:.0f}px horizontally")
                    if cy > 0:
                        parts.append(f"{cy:.0f}px vertically")
                    issues.append(
                        ClippingIssue(
                            issue_type=TYPE_CLIPPING,
                            severity=_clipping_severity(cx, cy, elem),
                            confidence_score=0.0,
                            confidence_level=CONF_MEDIUM,
                            viewport=viewport,
                            scroll_position=scroll_y,
                            url=url,
                            reasoning=(
                                f"<{elem.tag_name}> ('{text}') is clipped by "
                                f"<{ancestor.tag_name}> ({ancestor.selector}) by "
                                f"{' and '.join(parts)}."
                            ),
                            clipped_element=elem,
                            clipping_ancestor=ancestor,
                            clipped_region=_clipped_region(elem, cx, cy),
                            overflow_x=cx,
                            overflow_y=cy,
                        )
                    )

    return issues
