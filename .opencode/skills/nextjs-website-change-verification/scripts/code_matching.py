"""Source-file collection + issue-to-code substring matching.

Greps the generated app's source tree for class names and text snippets
extracted from each issue. Attaches the top-N matches to each issue so the
coding agent has a starting line to investigate.
"""

from __future__ import annotations

import os
import re

from models import (
    ClippingIssue,
    CollisionIssue,
    ContrastIssue,
    Issue,
    MatchResult,
    SourceFile,
)

_EXCLUDED_DIRS = frozenset(
    {
        "node_modules",
        ".git",
        "__pycache__",
        "dist",
        "build",
        ".next",
        ".nuxt",
        ".svelte-kit",
        "vendor",
        "coverage",
        ".cache",
        ".turbo",
        ".output",
        ".vercel",
        ".netlify",
        "out",
    }
)
_INCLUDED_EXTENSIONS = frozenset(
    {
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".less",
        ".sass",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".vue",
        ".svelte",
        ".astro",
    }
)
_EXTENSION_PRIORITY = {
    ".css": 0,
    ".scss": 0,
    ".less": 0,
    ".sass": 0,
    ".html": 1,
    ".htm": 1,
    ".vue": 1,
    ".svelte": 1,
    ".tsx": 2,
    ".jsx": 2,
    ".ts": 3,
    ".js": 3,
}
_CLASS_RE = re.compile(r"\.([\w-]+)")


def collect_source_files(code_path: str, max_kb: int = 500) -> list:
    code_path = os.path.abspath(code_path)
    if not os.path.isdir(code_path):
        return []
    max_bytes = max_kb * 1024
    candidates = []
    for root, dirs, files in os.walk(code_path):
        dirs[:] = [d for d in dirs if d not in _EXCLUDED_DIRS]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in _INCLUDED_EXTENSIONS:
                continue
            abs_path = os.path.join(root, fname)
            priority = _EXTENSION_PRIORITY.get(ext, 5)
            candidates.append((priority, abs_path))
    candidates.sort(key=lambda x: (x[0], x[1]))
    collected = []
    total = 0
    for _, abs_path in candidates:
        try:
            size = os.path.getsize(abs_path)
            if total + size > max_bytes:
                continue
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            ext = os.path.splitext(abs_path)[1].lower()
            collected.append(
                SourceFile(
                    path=abs_path,
                    relative_path=os.path.relpath(abs_path, code_path),
                    content=content,
                    extension=ext,
                    size_bytes=size,
                )
            )
            total += size
        except OSError:
            pass
    return collected


def _extract_search_terms(issue: Issue) -> list:
    terms = []
    if isinstance(issue, CollisionIssue):
        for label, el in [("a", issue.element_a), ("b", issue.element_b)]:
            for cls in _CLASS_RE.findall(el.selector):
                terms.append((cls, f"class from element_{label}"))
            txt = el.text_content.strip()[:60]
            if len(txt) >= 4:
                terms.append((txt, f"text content of element_{label}"))
    elif isinstance(issue, ClippingIssue):
        for label, el in [
            ("clipped", issue.clipped_element),
            ("ancestor", issue.clipping_ancestor),
        ]:
            for cls in _CLASS_RE.findall(el.selector):
                terms.append((cls, f"class from {label}"))
        txt = issue.clipped_element.text_content.strip()[:60]
        if len(txt) >= 4:
            terms.append((txt, "clipped element text"))
        terms.append(("overflow", "overflow CSS"))
    elif isinstance(issue, ContrastIssue):
        for cls in _CLASS_RE.findall(issue.element.selector):
            terms.append((cls, "class from element selector"))
        txt = issue.element.text_content.strip()[:60]
        if len(txt) >= 4:
            terms.append((txt, "contrast element text"))
        fg = issue.foreground_color
        terms.append((f"#{fg.r:02x}{fg.g:02x}{fg.b:02x}", "foreground color hex"))
    # Deduplicate
    seen, unique = set(), []
    for term, reason in terms:
        if term.lower() not in seen:
            seen.add(term.lower())
            unique.append((term, reason))
    return unique


def match_issues_to_code(issues: list, source_files: list, max_per_issue: int = 5) -> dict:
    result = {}
    for idx, issue in enumerate(issues):
        terms = _extract_search_terms(issue)
        if not terms:
            continue
        matches = []
        seen_locs: set = set()
        for term, reason in terms:
            term_lower = term.lower()
            for src in source_files:
                lines = src.content.splitlines()
                for i, line in enumerate(lines):
                    if term_lower in line.lower():
                        loc = (src.path, i + 1)
                        if loc in seen_locs:
                            continue
                        seen_locs.add(loc)
                        matches.append(
                            MatchResult(
                                file_path=src.path,
                                relative_path=src.relative_path,
                                line_number=i + 1,
                                line_content=line.rstrip(),
                                context_before=lines[max(0, i - 2) : i],
                                context_after=lines[i + 1 : i + 3],
                                match_reason=reason,
                            )
                        )
        if matches:

            def sort_key(m: MatchResult):
                ext_p = 0 if m.relative_path.endswith((".css", ".scss", ".less", ".sass")) else 1
                reason_p = 0 if "class" in m.match_reason else 1
                return (ext_p, reason_p)

            matches.sort(key=sort_key)
            result[idx] = matches[:max_per_issue]
    return result
