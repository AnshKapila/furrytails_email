"""Per-issue confidence scoring + threshold filtering."""

from __future__ import annotations

from config import ScanConfig
from models import (
    CONF_HIGH,
    CONF_MEDIUM,
    ROLE_BODY_TEXT,
    ROLE_BUTTON_TEXT,
    ROLE_CAPTION,
    ROLE_DECORATIVE,
    ROLE_HEADING,
    ROLE_LABEL,
    ROLE_LINK,
    ROLE_PLACEHOLDER,
    BlockedInteractionIssue,
    ClippingIssue,
    CollisionIssue,
    ContrastIssue,
)

_SEMANTIC_IMPORTANCE = {
    ROLE_HEADING: 1.0,
    ROLE_BUTTON_TEXT: 1.0,
    ROLE_BODY_TEXT: 0.8,
    ROLE_LINK: 0.8,
    ROLE_LABEL: 0.7,
    ROLE_CAPTION: 0.5,
    ROLE_PLACEHOLDER: 0.3,
    ROLE_DECORATIVE: 0.1,
}


def _score_collision(issue: CollisionIssue) -> float:
    signals = [
        min(issue.overlap_ratio * 2, 1.0),
        1.0
        if (issue.element_a.text_content.strip() and issue.element_b.text_content.strip())
        else 0.3,
        0.8 if abs(issue.element_a.z_index - issue.element_b.z_index) < 5 else 0.3,
        1.0
        if (issue.element_a.position == "static" and issue.element_b.position == "static")
        else 0.6,
    ]
    return sum(signals) / len(signals)


def _score_clipping(issue: ClippingIssue) -> float:
    total = issue.overflow_x + issue.overflow_y
    size = issue.clipped_element.bbox.width + issue.clipped_element.bbox.height
    signals = [
        min((total / max(size, 1)) * 3, 1.0),
        0.9 if issue.clipped_element.text_content.strip() else 0.4,
        _SEMANTIC_IMPORTANCE.get(issue.clipped_element.semantic_role, 0.5),
    ]
    return sum(signals) / len(signals)


def score_and_filter(issues: list, config: ScanConfig) -> list:
    """Score heuristic detections (collision, clipping) and filter by confidence.

    Contrast issues are NOT rescored — axe-core's WCAG checks are
    deterministic (the foreground/background colors and contrast ratio are
    computed exactly), so a heuristic-mean score adds no information and
    actively misclassifies borderline-but-real failures as MEDIUM. The
    confidence_score/level set by contrast.py is preserved as-is.
    """
    result = []
    for issue in issues:
        # Deterministic browser signals keep their own confidence: axe computes
        # exact contrast ratios; blocked-interaction comes from the browser's
        # authoritative elementFromPoint hit-test.
        if isinstance(issue, (ContrastIssue, BlockedInteractionIssue)):
            result.append(issue)
            continue

        if isinstance(issue, CollisionIssue):
            score = _score_collision(issue)
        elif isinstance(issue, ClippingIssue):
            score = _score_clipping(issue)
        else:
            score = 0.5

        if score >= config.CONFIDENCE_HIGH:
            level = CONF_HIGH
        elif score >= config.CONFIDENCE_MEDIUM:
            level = CONF_MEDIUM
        else:
            continue  # discard LOW

        issue.confidence_score = score
        issue.confidence_level = level
        result.append(issue)
    return result
