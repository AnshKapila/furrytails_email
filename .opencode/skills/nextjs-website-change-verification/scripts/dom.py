"""Shared DOM-tree walks over extracted ``ElementData``.

One implementation of the parent-chain traversal, used by both detectors.
Every walk is capped at ``MAX_ANCESTOR_DEPTH`` so a selector cycle (possible
when nth-of-type selectors collide) can never loop forever.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Optional

from models import ElementData

MAX_ANCESTOR_DEPTH = 15


def iter_ancestors(elem: ElementData, elem_map: dict) -> Iterator[ElementData]:
    """Yield ``elem``'s ancestors, nearest first, up to MAX_ANCESTOR_DEPTH."""
    current = elem.parent_selector
    depth = 0
    while current and depth < MAX_ANCESTOR_DEPTH:
        parent = elem_map.get(current)
        if parent is None:
            return
        yield parent
        current = parent.parent_selector
        depth += 1


def is_descendant_of(elem: ElementData, ancestor_selector: str, elem_map: dict) -> bool:
    """True when ``ancestor_selector`` appears in ``elem``'s parent chain.

    Selectors are compared BEFORE resolving through ``elem_map`` so a match on
    an ancestor that extraction filtered out (e.g. an SVG internal) still
    counts; the walk only needs the map to continue past a non-matching link.
    """
    current = elem.parent_selector
    depth = 0
    while current and depth < MAX_ANCESTOR_DEPTH:
        if current == ancestor_selector:
            return True
        parent = elem_map.get(current)
        if parent is None:
            return False
        current = parent.parent_selector
        depth += 1
    return False


def find_clip_ancestor(elem: ElementData, elem_map: dict) -> Optional[ElementData]:
    """Nearest ancestor with ``overflow: hidden|clip``, or None."""
    for parent in iter_ancestors(elem, elem_map):
        if parent.overflow in ("hidden", "clip"):
            return parent
    return None
