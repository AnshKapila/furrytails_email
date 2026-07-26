"""Collision detection engine — pairwise overlap + parent-overflow.

A long list of suppressors filters out intentional layering:
sticky/fixed descendants, ancestor relationships, ARIA overlay roles,
shared text containment, and ancestor-shadowing dedup.
"""

from __future__ import annotations

from typing import Optional

import dom
from config import ScanConfig
from models import (
    CONF_MEDIUM,
    SEV_CRITICAL,
    SEV_HIGH,
    SEV_LOW,
    SEV_MEDIUM,
    TYPE_COLLISION,
    BoundingBox,
    CollisionIssue,
    ElementData,
    Viewport,
)

_PARENT_OVERFLOW_MIN_PX = 20.0
_PARENT_OVERFLOW_SKIP_TAGS = frozenset({"svg", "canvas", "video", "iframe", "embed", "object"})
_INTENTIONAL_OVERLAY_ROLES = frozenset(
    {
        "dialog",
        "alertdialog",
        "tooltip",
        "menu",
        "listbox",
        "combobox",
        "tree",
        "popup",
        "banner",
        "toolbar",
        "tabpanel",
        "tab",
        "menubar",
        "menuitem",
        "navigation",
        "complementary",
    }
)
_OVERLAY_TAGS = frozenset(
    {
        "dialog",
        "details",
        "summary",
        "nav",
        "header",
        "footer",
        "aside",
        "select",
        "option",
        "optgroup",
    }
)
_CONTAINER_TAGS = frozenset(
    {
        "div",
        "section",
        "article",
        "main",
        "aside",
        "header",
        "footer",
        "nav",
        "form",
        "fieldset",
        "ul",
        "ol",
        "li",
        "dl",
        "dd",
        "dt",
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "td",
        "th",
        "figure",
        "figcaption",
        "picture",
        "video",
        "audio",
    }
)
_CONTENT_TAGS = frozenset(
    {
        "p",
        "span",
        "a",
        "button",
        "input",
        "textarea",
        "select",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "label",
        "img",
        "svg",
        "strong",
        "em",
        "b",
        "i",
        "code",
        "pre",
        "blockquote",
    }
)
_MAX_VISUAL_SURFACE_AREA = 50_000
# Visual media tags count as meaningful content for severity purposes: an
# <img> occluding a headline is as broken as text-on-text.
_VISUAL_CONTENT_TAGS = frozenset({"img", "svg", "canvas", "video", "picture"})
# Sticky elements at least this fraction of the viewport height are
# scroll-coupled pinned canvases (e.g. a sticky h-screen hero), not navbars —
# their content still participates in collision detection.
_PINNED_SECTION_VIEWPORT_RATIO = 0.8
# An opaque "curtain sheet" sliding over a pinned canvas must span most of the
# viewport width; narrower opaque elements are floating cards, not curtains.
_CURTAIN_SHEET_WIDTH_RATIO = 0.8


def _has_visual_surface(elem: ElementData) -> bool:
    if elem.bbox.area >= _MAX_VISUAL_SURFACE_AREA:
        return False
    bg = elem.background_color
    return bg is not None and bg.a > 0.5


def _is_content_element(elem: ElementData) -> bool:
    tag = elem.tag_name.lower()
    if tag in _CONTENT_TAGS:
        return True
    if tag in _CONTAINER_TAGS:
        text = elem.text_content.strip()
        if text and len(text) < 80:
            return True
        if text and _has_visual_surface(elem):
            return True
        return False
    if tag in ("svg", "canvas", "img", "video"):
        return True
    return False


def _expand_with_descendants(roots: set, elements: list) -> set:
    if not roots:
        return set()
    elem_map = {e.selector: e for e in elements}
    result = set(roots)
    for e in elements:
        if e.selector in result:
            continue
        current = e.parent_selector
        depth = 0
        while current and depth < 15:
            if current in roots:
                result.add(e.selector)
                break
            parent = elem_map.get(current)
            if not parent:
                break
            current = parent.parent_selector
            depth += 1
    return result


def _build_sticky_fixed_descendants(elements: list, viewport_height: float) -> set:
    """Selectors of fixed/sticky elements (and their descendants) whose overlaps
    are intentional layering. Full-viewport pinned sections are excluded: they
    are scroll-coupled canvases whose content must still be collision-checked."""
    sticky_fixed = {
        e.selector
        for e in elements
        if e.position == "fixed"
        or (
            e.position == "sticky"
            and e.bbox.height < viewport_height * _PINNED_SECTION_VIEWPORT_RATIO
        )
    }
    return _expand_with_descendants(sticky_fixed, elements)


def _build_pinned_descendants(elements: list, viewport_height: float) -> set:
    """Selectors of full-viewport pinned (sticky) sections and their
    descendants — the scroll-coupled canvases that later sections slide over."""
    pinned = {
        e.selector
        for e in elements
        if e.position == "sticky"
        and e.bbox.height >= viewport_height * _PINNED_SECTION_VIEWPORT_RATIO
    }
    return _expand_with_descendants(pinned, elements)


def _is_backed_by_opaque_sheet(elem: ElementData, elem_map: dict, viewport_width: float) -> bool:
    """True if the element or an ancestor paints an opaque full-width sheet.

    Content riding an opaque sheet over a pinned canvas is the intended
    scroll-coupled curtain effect — the pinned content is hidden behind the
    sheet, not colliding with it. Opaque ancestors narrower than a sheet
    (floating cards) don't count: a card drifting over pinned text is a
    genuine occlusion candidate."""
    current: Optional[ElementData] = elem
    depth = 0
    while current and depth < 15:
        bg = current.background_color
        if (
            bg is not None
            and bg.a > 0.5
            and current.bbox.width >= viewport_width * _CURTAIN_SHEET_WIDTH_RATIO
        ):
            return True
        current = elem_map.get(current.parent_selector) if current.parent_selector else None
        depth += 1
    return False


def _is_ancestor_of(ancestor: ElementData, descendant: ElementData, all_elements: list) -> bool:
    elem_map = {e.selector: e for e in all_elements}
    return dom.is_descendant_of(descendant, ancestor.selector, elem_map)


def _is_related(a: ElementData, b: ElementData, all_elements: list) -> bool:
    if a.parent_selector == b.selector or b.parent_selector == a.selector:
        return True
    if _is_ancestor_of(b, a, all_elements):
        return True
    if _is_ancestor_of(a, b, all_elements):
        return True
    if (
        a.parent_selector
        and a.parent_selector == b.parent_selector
        and a.position == "static"
        and b.position == "static"
    ):
        return True
    return False


def _is_intentional_overlay(
    a: ElementData,
    b: ElementData,
    sticky_fixed_descendants: set,
    pinned: set,
    ignore_sticky: bool,
) -> bool:
    if (a.aria_role or "").lower() in _INTENTIONAL_OVERLAY_ROLES:
        return True
    if (b.aria_role or "").lower() in _INTENTIONAL_OVERLAY_ROLES:
        return True
    if a.tag_name.lower() in _OVERLAY_TAGS or b.tag_name.lower() in _OVERLAY_TAGS:
        return True
    if ignore_sticky:
        # A fixed/sticky element itself is a layering primitive (navbar,
        # pinned canvas backdrop) — pairs with it are intentional. Descendant
        # membership extends only to short bars; descendants of full-viewport
        # pinned sections stay checkable (see _build_sticky_fixed_descendants).
        if a.position in ("fixed", "sticky") or b.position in ("fixed", "sticky"):
            return True
        if a.selector in sticky_fixed_descendants or b.selector in sticky_fixed_descendants:
            return True
    if a.position == "absolute" and b.position == "relative":
        return True
    if b.position == "absolute" and a.position == "relative":
        return True
    if abs(a.z_index - b.z_index) > 10:
        return True
    cross_pinned = (a.selector in pinned) != (b.selector in pinned)
    if _fully_contains(a.bbox, b.bbox) and _containment_is_intentional(a, b, cross_pinned):
        return True
    if _fully_contains(b.bbox, a.bbox) and _containment_is_intentional(b, a, cross_pinned):
        return True
    return False


def _containment_is_intentional(outer: ElementData, inner: ElementData, cross_pinned: bool) -> bool:
    # Bbox containment is intentional layering (hero text inside its own
    # full-bleed background image) — except across a pinned-canvas boundary:
    # a visual element from another section fully inside pinned text's bbox
    # (a card drifting over a pinned headline) occludes glyphs.
    if not cross_pinned:
        return True
    inner_is_visual = inner.tag_name.lower() in _VISUAL_CONTENT_TAGS
    outer_has_text = bool(outer.text_content.strip())
    return not (inner_is_visual and outer_has_text)


def _fully_contains(outer: BoundingBox, inner: BoundingBox) -> bool:
    return (
        outer.x <= inner.x
        and outer.y <= inner.y
        and outer.right >= inner.right
        and outer.bottom >= inner.bottom
    )


def _is_shared_text(a: ElementData, b: ElementData) -> bool:
    ta, tb = a.text_content.strip(), b.text_content.strip()
    if not ta or not tb:
        return False
    return ta in tb or tb in ta


def _is_stretched_link(a: ElementData, b: ElementData, overlap_ratio: float) -> bool:
    """An <a> almost fully covering an <img> is a linked image (the anchor
    wraps or overlays the card thumbnail for click area), not an occlusion —
    an image carries no text to obscure."""
    tags = {a.tag_name.lower(), b.tag_name.lower()}
    return tags == {"a", "img"} and overlap_ratio > 0.9


def _parent_is_inline(parent: ElementData) -> bool:
    """Inline boxes don't establish a containing block — a link's line box
    routinely extends past its inline <span> parent's rect with no visual
    defect, so parent-overflow against an inline parent is not a real escape."""
    return (parent.computed_styles or {}).get("display") == "inline"


def _find_clip_ancestor(elem: ElementData, all_elements: list) -> Optional[ElementData]:
    elem_map = {e.selector: e for e in all_elements}
    return dom.find_clip_ancestor(elem, elem_map)


def _is_clipped_away_from(inner: ElementData, outer: ElementData, all_elements: list) -> bool:
    clip = _find_clip_ancestor(inner, all_elements)
    if clip is None:
        return False
    if _is_ancestor_of(clip, outer, all_elements):
        return False
    return not clip.bbox.intersects(outer.bbox)


def _dedup_ancestor_shadows_collisions(issues: list, all_elements: list) -> list:
    discard: set = set()
    for i, issue_i in enumerate(issues):
        if i in discard:
            continue
        for j, issue_j in enumerate(issues):
            if j <= i or j in discard:
                continue
            if issue_i.element_b.selector == issue_j.element_b.selector:
                if _is_ancestor_of(issue_i.element_a, issue_j.element_a, all_elements):
                    discard.add(i)
                    break
                if _is_ancestor_of(issue_j.element_a, issue_i.element_a, all_elements):
                    discard.add(j)
            elif issue_i.element_a.selector == issue_j.element_a.selector:
                if _is_ancestor_of(issue_i.element_b, issue_j.element_b, all_elements):
                    discard.add(i)
                    break
                if _is_ancestor_of(issue_j.element_b, issue_i.element_b, all_elements):
                    discard.add(j)
    return [iss for idx, iss in enumerate(issues) if idx not in discard]


def _is_meaningful_content(elem: ElementData) -> bool:
    return bool(elem.text_content.strip()) or elem.tag_name.lower() in _VISUAL_CONTENT_TAGS


def _text_lines_cross_visual(a: ElementData, b: ElementData, overlap_bbox: BoundingBox) -> bool:
    """True when whole lines of a text element cross a visual element.

    A tall text block clipping a large image produces a small area ratio even
    when several lines of text are unreadable — measure the overlap in text
    lines instead: at least 2 line-heights tall and a character wide."""
    a_visual = a.tag_name.lower() in _VISUAL_CONTENT_TAGS
    b_visual = b.tag_name.lower() in _VISUAL_CONTENT_TAGS
    if a.text_content.strip() and b_visual and not a_visual:
        text_elem = a
    elif b.text_content.strip() and a_visual and not b_visual:
        text_elem = b
    else:
        return False
    line_height = max(text_elem.font_size, 8.0) * 1.2
    return overlap_bbox.height >= 2 * line_height and overlap_bbox.width >= text_elem.font_size


def _collision_severity(
    overlap_ratio: float, a: ElementData, b: ElementData, overlap_bbox: Optional[BoundingBox]
) -> str:
    # Escalate when text is occluded by meaningful content: at least one side
    # has text and both sides are content (text or visual media). Pure
    # decoration pairs (e.g. two empty divs) stay at medium/low.
    has_text = bool(a.text_content.strip()) or bool(b.text_content.strip())
    text_occluded = has_text and _is_meaningful_content(a) and _is_meaningful_content(b)
    if overlap_ratio > 0.5 and text_occluded:
        return SEV_CRITICAL
    if overlap_ratio > 0.3 and text_occluded:
        return SEV_HIGH
    if overlap_bbox is not None and _text_lines_cross_visual(a, b, overlap_bbox):
        return SEV_HIGH
    if overlap_ratio > 0.1:
        return SEV_MEDIUM
    return SEV_LOW


def detect_collisions(
    elements: list, viewport: Viewport, scroll_y: float, url: str, config: ScanConfig
) -> list:
    issues = []
    elem_map = {e.selector: e for e in elements}
    sticky_fixed = _build_sticky_fixed_descendants(elements, viewport.height)
    pinned = _build_pinned_descendants(elements, viewport.height)

    candidates = [
        e
        for e in elements
        if e.is_visible and e.opacity > 0 and e.bbox.area > 4 and _is_content_element(e)
    ]
    candidates.sort(key=lambda e: e.stacking_order)

    for i, ea in enumerate(candidates):
        for eb in candidates[i + 1 :]:
            if not ea.bbox.intersects(eb.bbox):
                continue
            if _is_related(ea, eb, elements):
                continue
            if _is_intentional_overlay(ea, eb, sticky_fixed, pinned, config.IGNORE_STICKY):
                continue
            if _is_shared_text(ea, eb):
                continue
            if _is_clipped_away_from(ea, eb, elements) or _is_clipped_away_from(eb, ea, elements):
                continue

            # Cross-curtain pairs: one element inside a pinned canvas, the
            # other scrolling over it. Opaque-backed outside content is the
            # intended curtain hiding the canvas; transparent-backed content
            # floating over pinned text is a genuine occlusion candidate.
            a_pinned = ea.selector in pinned
            b_pinned = eb.selector in pinned
            if a_pinned != b_pinned:
                outside = eb if a_pinned else ea
                if _is_backed_by_opaque_sheet(outside, elem_map, viewport.width):
                    continue

            overlap_area = ea.bbox.intersection_area(eb.bbox)
            smaller_area = min(ea.bbox.area, eb.bbox.area)
            overlap_ratio = overlap_area / smaller_area if smaller_area > 0 else 0
            if overlap_ratio < config.MIN_OVERLAP_RATIO:
                continue
            if _is_stretched_link(ea, eb, overlap_ratio):
                continue
            overlap_bbox = ea.bbox.intersection_bbox(eb.bbox)
            if overlap_bbox is None:
                continue

            text_a = ea.text_content[:50] or ea.tag_name
            text_b = eb.text_content[:50] or eb.tag_name
            issues.append(
                CollisionIssue(
                    issue_type=TYPE_COLLISION,
                    severity=_collision_severity(overlap_ratio, ea, eb, overlap_bbox),
                    confidence_score=0.0,
                    confidence_level=CONF_MEDIUM,
                    viewport=viewport,
                    scroll_position=scroll_y,
                    url=url,
                    reasoning=(
                        f"<{ea.tag_name}> ('{text_a}') overlaps <{eb.tag_name}> ('{text_b}') "
                        f"by {overlap_ratio:.0%} of the smaller element."
                    ),
                    element_a=ea,
                    element_b=eb,
                    overlap_bbox=overlap_bbox,
                    overlap_area=overlap_area,
                    overlap_ratio=overlap_ratio,
                )
            )

    issues = _dedup_ancestor_shadows_collisions(issues, elements)

    # Parent overflow collisions
    for elem in elements:
        if not elem.is_visible or elem.position in ("absolute", "fixed", "sticky"):
            continue
        if not elem.parent_selector or elem.tag_name.lower() in _PARENT_OVERFLOW_SKIP_TAGS:
            continue
        if not (elem.text_content.strip() or elem.tag_name.lower() == "img"):
            continue
        parent = elem_map.get(elem.parent_selector)
        if not parent or parent.overflow in ("hidden", "clip") or parent.bbox.area < 400:
            continue
        if _parent_is_inline(parent):
            continue

        ov_right = max(0.0, elem.bbox.right - parent.bbox.right)
        ov_left = max(0.0, parent.bbox.x - elem.bbox.x)
        ov_bottom = max(0.0, elem.bbox.bottom - parent.bbox.bottom)
        ov_top = max(0.0, parent.bbox.y - elem.bbox.y)
        ov_x = max(ov_right, ov_left)
        ov_y = max(ov_bottom, ov_top)

        if ov_x < _PARENT_OVERFLOW_MIN_PX and ov_y < _PARENT_OVERFLOW_MIN_PX:
            continue

        if ov_x >= ov_y:
            ox = (
                elem.bbox.right - parent.bbox.right
                if ov_right >= ov_left
                else parent.bbox.x - elem.bbox.x
            )
            overlap_bbox = BoundingBox(
                x=parent.bbox.right if ov_right >= ov_left else elem.bbox.x,
                y=max(elem.bbox.y, parent.bbox.y),
                width=abs(ox),
                # Clamp to 0: when elem and parent don't overlap vertically the
                # min−max expression is negative, which would produce an invalid bbox.
                height=max(
                    0.0,
                    min(elem.bbox.bottom, parent.bbox.bottom) - max(elem.bbox.y, parent.bbox.y),
                ),
            )
        else:
            oy = (
                elem.bbox.bottom - parent.bbox.bottom
                if ov_bottom >= ov_top
                else parent.bbox.y - elem.bbox.y
            )
            overlap_bbox = BoundingBox(
                x=max(elem.bbox.x, parent.bbox.x),
                y=parent.bbox.bottom if ov_bottom >= ov_top else elem.bbox.y,
                # Same clamp for horizontal dimension.
                width=max(
                    0.0,
                    min(elem.bbox.right, parent.bbox.right) - max(elem.bbox.x, parent.bbox.x),
                ),
                height=abs(oy),
            )

        # The protruding strip is only a visible defect if it is actually
        # painted. When an ancestor with overflow:hidden clips the strip away
        # entirely (carousel slides outside the slider viewport, marquee
        # content beyond the track), nothing visibly overflows — cut-off
        # *content* is the clipping detector's domain, with its own
        # intentionality rules.
        clip = _find_clip_ancestor(elem, elements)
        if clip is not None and not clip.bbox.intersects(overlap_bbox):
            continue

        # overlap_area = (horizontal overflow magnitude) × (vertical overlap height),
        # or (vertical overflow magnitude) × (horizontal overlap width) — the actual
        # area of the strip that protrudes outside the parent.  The previous formula
        # mixed the two axes, inflating severity for thin protrusions on tall parents.
        overlap_area = (
            max(ov_x, 1.0) * max(overlap_bbox.height, 1.0)
            if ov_x >= ov_y
            else max(overlap_bbox.width, 1.0) * max(ov_y, 1.0)
        )
        smaller_area = min(elem.bbox.area, parent.bbox.area)
        overlap_ratio = overlap_area / smaller_area if smaller_area > 0 else 0.0
        text_elem = elem.text_content[:50] if elem.text_content else elem.tag_name

        issues.append(
            CollisionIssue(
                issue_type=TYPE_COLLISION,
                # Reuse of _collision_severity for overflow: `b` is the parent
                # container, which (holding the child's text) almost always reads
                # as meaningful content, so escalation is driven by overlap_ratio
                # alone. The "text_occluded" framing is a proxy here — the real
                # defect is the child escaping its container, not occlusion.
                severity=_collision_severity(overlap_ratio, elem, parent, overlap_bbox),
                confidence_score=0.0,
                confidence_level=CONF_MEDIUM,
                viewport=viewport,
                scroll_position=scroll_y,
                url=url,
                reasoning=(
                    f"<{elem.tag_name}> ('{text_elem}') overflows its container "
                    f"<{parent.tag_name}> by {ov_x:.0f}px h / {ov_y:.0f}px v."
                ),
                element_a=elem,
                element_b=parent,
                overlap_bbox=overlap_bbox,
                overlap_area=overlap_area,
                overlap_ratio=overlap_ratio,
            )
        )

    return issues
