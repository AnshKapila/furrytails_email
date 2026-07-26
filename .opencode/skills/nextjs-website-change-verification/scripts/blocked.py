"""Blocked-interaction detection — links/buttons covered in the real paint order.

The hit-testing itself runs in-page (``browser.HIT_TEST_JS``) because it needs
the live document; this module converts the raw hit dicts into typed issues.
"""

from __future__ import annotations

from models import (
    CONF_HIGH,
    ROLE_BUTTON_TEXT,
    ROLE_LINK,
    SEV_CRITICAL,
    TYPE_BLOCKED,
    BlockedInteractionIssue,
    BoundingBox,
    ElementData,
    Viewport,
)


def _hit_to_element(raw: dict) -> ElementData:
    """Synthetic ElementData from a HIT_TEST_JS element dict — only the fields
    used downstream (dedup, cropping, code-matching, reports) are populated."""
    bbox = raw.get("bbox") or {}
    tag = (raw.get("tag_name") or "?").lower()
    return ElementData(
        selector=raw.get("selector") or "?",
        tag_name=tag,
        text_content=raw.get("text") or "",
        bbox=BoundingBox(
            x=float(bbox.get("x", 0)),
            y=float(bbox.get("y", 0)),
            width=float(bbox.get("width", 0)),
            height=float(bbox.get("height", 0)),
        ),
        computed_styles={},
        z_index=0,
        stacking_order=0,
        is_visible=True,
        parent_selector=None,
        overflow="visible",
        scroll_width=float(bbox.get("width", 0)),
        scroll_height=float(bbox.get("height", 0)),
        semantic_role=ROLE_BUTTON_TEXT if tag == "button" else ROLE_LINK,
        foreground_color=None,
        background_color=None,
        font_size=16.0,
        opacity=1.0,
        position="static",
        aria_role=None,
    )


def detect_blocked_interactions(
    blocked_hits: list, viewport: Viewport, scroll_y: float, url: str
) -> list:
    """Convert raw hit-test results into BlockedInteractionIssues.

    Always critical: a covered control is functionally broken regardless of how
    the page looks — and the blocker may be visually invisible, which is
    exactly why no screenshot-based check can stand in for this one.
    """
    issues = []
    for raw in blocked_hits or []:
        target = _hit_to_element(raw.get("target") or {})
        blocker = _hit_to_element(raw.get("blocker") or {})
        ratio = float(raw.get("blocked_ratio", 0.0))
        label = target.text_content[:50] or target.tag_name
        issues.append(
            BlockedInteractionIssue(
                issue_type=TYPE_BLOCKED,
                severity=SEV_CRITICAL,
                confidence_score=0.9,
                confidence_level=CONF_HIGH,
                viewport=viewport,
                scroll_position=scroll_y,
                url=url,
                reasoning=(
                    f"<{target.tag_name}> ('{label}') is not clickable: "
                    f"{ratio:.0%} of its surface is captured by "
                    f"<{blocker.tag_name}> ({blocker.selector}) in the paint order. "
                    f"Users cannot activate this control."
                ),
                target=target,
                blocker=blocker,
                blocked_ratio=ratio,
            )
        )
    return issues
