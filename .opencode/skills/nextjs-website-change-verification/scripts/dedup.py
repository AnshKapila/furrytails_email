"""Cross-snapshot issue deduplication + final severity ordering."""

from __future__ import annotations

from models import (
    SEV_CRITICAL,
    SEV_HIGH,
    SEV_LOW,
    SEV_MEDIUM,
    BlockedInteractionIssue,
    BoundingBox,
    ClippingIssue,
    CollisionIssue,
    ContrastIssue,
    Issue,
    Viewport,
)


def _visibility_ratio(issue: Issue, viewport: Viewport) -> float:
    vp_box = BoundingBox(x=0, y=0, width=viewport.width, height=viewport.height)
    if isinstance(issue, CollisionIssue):
        a, b = issue.element_a.bbox, issue.element_b.bbox
        region = BoundingBox(
            x=min(a.x, b.x),
            y=min(a.y, b.y),
            width=max(a.right, b.right) - min(a.x, b.x),
            height=max(a.bottom, b.bottom) - min(a.y, b.y),
        )
    elif isinstance(issue, ClippingIssue):
        region = issue.clipped_element.bbox
    elif isinstance(issue, ContrastIssue):
        region = issue.element.bbox
    elif isinstance(issue, BlockedInteractionIssue):
        region = issue.target.bbox
    else:
        return 0.0
    if region.area <= 0:
        return 0.0
    return region.intersection_area(vp_box) / region.area


def _dedup(issues: list, viewport: Viewport) -> list:
    collisions = [i for i in issues if isinstance(i, CollisionIssue)]
    clippings = [i for i in issues if isinstance(i, ClippingIssue)]
    contrasts = [i for i in issues if isinstance(i, ContrastIssue)]
    blocked = [i for i in issues if isinstance(i, BlockedInteractionIssue)]

    def vis(i):
        return _visibility_ratio(i, viewport)

    # Dedup collisions by selector pair or text pair
    collisions.sort(key=lambda i: (-vis(i), -i.overlap_ratio))
    seen_col: set = set()
    deduped_col = []
    for issue in collisions:
        sel_key = "sel:" + "||".join(sorted([issue.element_a.selector, issue.element_b.selector]))
        ta = issue.element_a.text_content.strip()[:80]
        tb = issue.element_b.text_content.strip()[:80]
        txt_key = ("txt:" + "||".join(sorted([ta, tb]))) if (ta and tb) else None
        if sel_key in seen_col or (txt_key and txt_key in seen_col):
            continue
        # Spatial dedup
        dominated = False
        for other in deduped_col:
            overlap = issue.overlap_bbox.intersection_area(other.overlap_bbox)
            smaller = min(issue.overlap_bbox.area, other.overlap_bbox.area)
            if smaller > 0 and overlap / smaller > 0.7:
                tc = {
                    issue.element_a.text_content.strip()[:60],
                    issue.element_b.text_content.strip()[:60],
                }
                to = {
                    other.element_a.text_content.strip()[:60],
                    other.element_b.text_content.strip()[:60],
                }
                if tc & to:
                    dominated = True
                    break
        if dominated:
            continue
        seen_col.add(sel_key)
        if txt_key:
            seen_col.add(txt_key)
        deduped_col.append(issue)

    # Dedup clippings by selector or text
    clippings.sort(key=lambda i: (-vis(i), -i.confidence_score))
    seen_clip: set = set()
    deduped_clip = []
    for issue in clippings:
        sel_key = "sel:" + issue.clipped_element.selector
        txt = issue.clipped_element.text_content.strip()[:80]
        txt_key = ("txt:" + txt) if txt else None
        if sel_key in seen_clip or (txt_key and txt_key in seen_clip):
            continue
        seen_clip.add(sel_key)
        if txt_key:
            seen_clip.add(txt_key)
        deduped_clip.append(issue)

    # Dedup contrasts by selector or color+text
    contrasts.sort(key=lambda i: (-vis(i), -i.confidence_score))
    seen_cont: set = set()
    deduped_cont = []
    for issue in contrasts:
        sel_key = "sel:" + issue.element.selector
        fg, bg = issue.foreground_color, issue.background_color
        color_key = f"rgb({fg.r},{fg.g},{fg.b})-rgb({bg.r},{bg.g},{bg.b})"
        txt = issue.element.text_content.strip()[:80]
        txt_key = f"color+txt:{color_key}|{txt}" if txt else None
        short_key = f"color+short:{color_key}|{txt[:40]}" if txt else None
        if sel_key in seen_cont:
            continue
        if txt_key and txt_key in seen_cont:
            continue
        if short_key and short_key in seen_cont:
            continue
        seen_cont.add(sel_key)
        if txt_key:
            seen_cont.add(txt_key)
        if short_key:
            seen_cont.add(short_key)
        deduped_cont.append(issue)

    # Dedup blocked interactions by target selector (the same covered button
    # is re-detected at every scroll snapshot where it is visible)
    blocked.sort(key=lambda i: (-vis(i), -i.blocked_ratio))
    seen_blocked: set = set()
    deduped_blocked = []
    for issue in blocked:
        key = issue.target.selector
        if key in seen_blocked:
            continue
        seen_blocked.add(key)
        deduped_blocked.append(issue)

    result = deduped_col + deduped_clip + deduped_cont + deduped_blocked
    sev_order = {SEV_CRITICAL: 0, SEV_HIGH: 1, SEV_MEDIUM: 2, SEV_LOW: 3}
    result.sort(key=lambda i: (sev_order.get(i.severity, 4), -i.confidence_score))
    return result
