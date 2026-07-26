"""Data types and constants for the QA scanner.

Stdlib dataclasses only — no Pydantic. Shared across detection, scoring,
dedup, verification, and reporting modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Semantic role constants
ROLE_HEADING = "heading"
ROLE_BODY_TEXT = "body_text"
ROLE_BUTTON_TEXT = "button_text"
ROLE_PLACEHOLDER = "placeholder"
ROLE_DECORATIVE = "decorative"
ROLE_CAPTION = "caption"
ROLE_LINK = "link"
ROLE_LABEL = "label"

# Issue type constants
TYPE_COLLISION = "collision"
TYPE_CLIPPING = "clipping"
TYPE_CONTRAST = "contrast"
# Z-order defects: an interactive element (link/button) whose click target is
# covered by a foreign element in the browser's real paint order. Detected by
# hit-testing (elementFromPoint), so — like runtime errors — it is a
# deterministic browser signal that skips AI verification (a click blocker can
# be visually invisible, so a screenshot proves nothing either way).
TYPE_BLOCKED = "blocked-interaction"
# Runtime errors (uncaught exceptions, hydration mismatches, renderer crashes).
# Unlike the visual types these are deterministic browser signals, so they skip
# the heuristic scoring / dedup / AI-verification path.
TYPE_RUNTIME = "runtime-error"

# Severity constants
SEV_CRITICAL = "critical"
SEV_HIGH = "high"
SEV_MEDIUM = "medium"
SEV_LOW = "low"

# Confidence constants
CONF_HIGH = "high"
CONF_MEDIUM = "medium"
CONF_LOW = "low"

# AI-verification verdict + dismissal basis + Kite Inspector dropped_source
# vocabularies, named so a typo can't silently mis-route a dropped finding.
VERDICT_CONFIRMED = "confirmed"
VERDICT_DISMISSED = "dismissed"
# ``ai_dismissal_basis`` values.
BASIS_DESIGN_INTENT = "design-intent"  # dismissal relied on the visual spec
BASIS_VISUAL = "visual"  # dismissal (or confirm) judged from pixels alone
# Kite Inspector ``dropped_source`` values.
DROPPED_SOURCE_VISUAL_SPEC = "visual_spec"
DROPPED_SOURCE_AI = "ai"


def dropped_source_for_basis(ai_dismissal_basis: Optional[str]) -> str:
    """Map an ``ai_dismissal_basis`` to Kite Inspector's ``dropped_source``.

    A spec-sanctioned dismissal is ``visual_spec``; every other dismissal
    (visual false-positive call) is ``ai``.
    """
    return (
        DROPPED_SOURCE_VISUAL_SPEC
        if ai_dismissal_basis == BASIS_DESIGN_INTENT
        else DROPPED_SOURCE_AI
    )


# The canonical "worth acting on" cut, shared by the scanner exit code and
# every same-process consumer. Two out-of-process consumers CANNOT import this
# module and carry mirrored copies with keep-in-sync comments:
# validate_files.py (loaded standalone, stdlib-only by design) and
# backend/app/services/qa_issue_reporter.py (platform backend must not import
# sandbox skill scripts).
ACTIONABLE_SEVERITIES = frozenset({SEV_CRITICAL, SEV_HIGH})


def is_actionable(severity: str, dropped: bool = False) -> bool:
    """True when a finding is worth acting on: critical/high severity and not
    rejected by the AI verifier."""
    return severity in ACTIONABLE_SEVERITIES and not dropped


@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def area(self) -> float:
        return self.width * self.height

    def intersects(self, other: BoundingBox) -> bool:
        return not (
            self.right <= other.x
            or other.right <= self.x
            or self.bottom <= other.y
            or other.bottom <= self.y
        )

    def intersection_area(self, other: BoundingBox) -> float:
        if not self.intersects(other):
            return 0.0
        iw = min(self.right, other.right) - max(self.x, other.x)
        ih = min(self.bottom, other.bottom) - max(self.y, other.y)
        return iw * ih

    def intersection_bbox(self, other: BoundingBox) -> Optional[BoundingBox]:
        if not self.intersects(other):
            return None
        ix = max(self.x, other.x)
        iy = max(self.y, other.y)
        iw = min(self.right, other.right) - ix
        ih = min(self.bottom, other.bottom) - iy
        return BoundingBox(x=ix, y=iy, width=iw, height=ih)


@dataclass
class RGBA:
    r: int
    g: int
    b: int
    a: float = 1.0


@dataclass
class ElementData:
    selector: str
    tag_name: str
    text_content: str
    bbox: BoundingBox
    computed_styles: dict
    z_index: int
    stacking_order: int
    is_visible: bool
    parent_selector: Optional[str]
    overflow: str
    scroll_width: float
    scroll_height: float
    semantic_role: str
    foreground_color: Optional[RGBA]
    background_color: Optional[RGBA]
    font_size: float
    opacity: float
    position: str
    aria_role: Optional[str]
    has_own_text: bool = True


@dataclass
class Viewport:
    width: int
    height: int
    scroll_y: float = 0.0


@dataclass
class ViewportSnapshot:
    viewport: Viewport
    scroll_position: float
    elements: list
    url: str
    page_title: str
    timestamp: str
    screenshot_path: Optional[str] = None  # Absolute EFS path, or None if not captured
    screenshot_bytes: Optional[bytes] = None  # Raw PNG bytes for per-issue cropping
    blocked_hits: list = field(default_factory=list)  # HIT_TEST_JS results (raw dicts)


@dataclass
class SourceFile:
    path: str
    relative_path: str
    content: str
    extension: str
    size_bytes: int


@dataclass
class MatchResult:
    file_path: str
    relative_path: str
    line_number: int
    line_content: str
    context_before: list
    context_after: list
    match_reason: str


@dataclass
class Issue:
    issue_type: str
    severity: str
    confidence_score: float
    confidence_level: str
    viewport: Viewport
    scroll_position: float
    url: str
    reasoning: str
    issue_id: Optional[str] = None
    code_references: list = field(default_factory=list)
    screenshot: Optional[str] = None  # EFS path to the per-issue crop (or viewport fallback)
    ai_verdict: Optional[str] = None  # "confirmed" | "dismissed" | None (not verified)
    ai_reasoning: Optional[str] = None  # Claude's one-line reasoning for the verdict
    # "design-intent" when a dismissal relied on the visual spec, else "visual".
    # Lets Kite Inspector separate spec-sanctioned drops from AI false-positive
    # calls (dropped_source: visual_spec vs ai).
    ai_dismissal_basis: Optional[str] = None


@dataclass
class CollisionIssue(Issue):
    element_a: ElementData = field(kw_only=True)
    element_b: ElementData = field(kw_only=True)
    overlap_bbox: BoundingBox = field(kw_only=True)
    overlap_area: float = 0.0
    overlap_ratio: float = 0.0


@dataclass
class ClippingIssue(Issue):
    clipped_element: ElementData = field(kw_only=True)
    clipping_ancestor: ElementData = field(kw_only=True)
    clipped_region: Optional[BoundingBox] = None
    overflow_x: float = 0.0
    overflow_y: float = 0.0


@dataclass
class BlockedInteractionIssue(Issue):
    target: ElementData = field(kw_only=True)  # the covered link/button
    blocker: ElementData = field(kw_only=True)  # the element that wins the hit-test
    blocked_ratio: float = 0.0  # fraction of sampled points captured by the blocker


@dataclass
class ContrastIssue(Issue):
    element: ElementData = field(kw_only=True)
    foreground_color: RGBA = field(kw_only=True)
    background_color: RGBA = field(kw_only=True)
    contrast_lc: float = 0.0
    required_lc: float = 0.0
    semantic_role: str = ROLE_BODY_TEXT
    # True for issues derived from axe "incomplete" results (axe could not
    # compute the contrast deterministically) — these must go through AI
    # vision verification instead of the deterministic skip.
    needs_ai_verification: bool = False
