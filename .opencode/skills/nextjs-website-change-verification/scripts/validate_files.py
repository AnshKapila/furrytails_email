#!/usr/bin/env python3
"""Validate a generated Next.js iteration via typecheck, build, skeleton-bar scan, then QA scan.

Reads `iterations/<iter>/` (seeded by `plan_files.py` and populated by
`generate_files.py`) and runs `pnpm typecheck` inside it, then (on clean
typecheck) a full `pnpm run build` to catch SWC compilation errors that
tsc misses, then statically scans every generated `.tsx` file for
runtime-blocking source patterns: skeleton-bar
placeholder shapes that the nextjs-code-writing prompt forbids but the LLM
occasionally ships anyway (V2-4606), DOM event handlers, and browser globals in
files missing a Client Component directive, then smoke-renders the homepage.
On clean validation it detaches a reporting-only QA scan (sibling
``background_scan.py``, which owns the cap/lock gate and telemetry) against
the running dev server to detect visual issues (collision, clipping,
contrast, blocked interaction).

Emits a single line of JSON describing the verdict:

    {"status": "success" | "failed" | "error", "issues": [...], "iteration_id": "..."}

TSC and static issues live in the flat `issues` list, each shaped as
`{code, location, hint}`.

The visual QA scan is REPORTING-ONLY and runs as a detached BACKGROUND task:
the verdict never waits on it and never reflects it. Its findings are logged
as `qa_scan` events (Loki/Grafana), written to the JSON report, and rendered
into the interactive HTML report on disk — the coding agent must not spend
fix passes on them.

Exit codes:
- 0 → status: success (no blocking issues; QA scan detached in the background)
- 1 → status: failed  (tsc errors, static source issues, or a broken preview)
- 2 → status: error   (infrastructure problem; do not retry)
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess  # noqa: S404 - intentional invocation of pnpm CLI / python3
import sys
import time
import urllib.error
import urllib.request

# Skills are pushed to the agent's run dir (e.g. iterations/<iter>/.opencode/skills),
# not the app root, so locate sibling-skill assets relative to this script's own
# tree rather than EFS_APP_PATH/.opencode/skills (empty on a fresh app).
SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent

# Lines like: `src/app/page.tsx(14,5): error TS2339: Property 'title' does not exist...`
_TSC_ERROR_RE = re.compile(
    r"^(?P<path>[^()\s][^()]*?)\((?P<line>\d+),(?P<col>\d+)\):\s+error\s+TS\d+:\s+(?P<msg>.+)$",
    re.MULTILINE,
)

# Skeleton-bar detection regexes. Match self-closing `<div ... />` or empty
# open/close `<div ...></div>` elements. Attribute spans use single-level
# brace balancing so `>` inside JSX expressions (arrow handlers, comparisons)
# does not abort the match.
_DIV_ATTRS = r"(?:[^>{]|\{[^{}]*\})*"
_DIV_SELF_CLOSE_RE = re.compile(rf"<div\s+({_DIV_ATTRS}?)\s*/>", re.DOTALL)
_DIV_EMPTY_PAIR_RE = re.compile(rf"<div\s+({_DIV_ATTRS}?)>\s*</div>", re.DOTALL)
_DIV_MATCHERS = (_DIV_SELF_CLOSE_RE, _DIV_EMPTY_PAIR_RE)
_CLASSNAME_RE = re.compile(r'className=(?:"([^"]*)"|\{`([^`]*)`\})', re.DOTALL)
_BG_TOKEN_RE = re.compile(r"\bbg-(?:\[[^\]]+\]|[a-zA-Z][\w-]*(?:/\d+)?)")
_WIDTH_TOKEN_RE = re.compile(r"\bw-(?:\[[^\]]+\]|[\w/.-]+)\b")
_HEIGHT_TOKEN_RE = re.compile(r"\bh-(?:\[[^\]]+\]|[\w/.-]+)\b")
_DIVIDER_DIMENSION_RE = re.compile(r"\b[wh]-(?:px|0\.5)\b")
# w-1 through w-4 (≤16 px) are indicator dots, waveform bars, and icon accents —
# not skeleton-bar placeholders. Real skeletons are wide (w-8+, w-full, w-1/2, etc.).
# Negative lookahead (?!/) prevents matching fractional widths (w-1/2, w-2/3, etc.).
_TINY_WIDTH_RE = re.compile(r"\bw-[1-4]\b(?!/)")
# aria-hidden="true" marks purely decorative elements that intentionally have no content.
_ARIA_HIDDEN_RE = re.compile(r'aria-hidden\s*=\s*(?:"true"|\{true\})')
# blur-* in classname = ambient background glow / blob effect. These are always empty
# and decorative; real skeleton bars never have blur applied.
_BLUR_CLASS_RE = re.compile(r"\bblur-")
_USE_CLIENT_DIRECTIVE_RE = re.compile(r"""(?:"use client"|'use client')\s*;?""")
_JSX_EVENT_HANDLER_ATTR_RE = re.compile(
    r"<[A-Za-z][A-Za-z0-9.:-]*(?:\s+[^<>]*?)?\s+(on[A-Z][A-Za-z0-9_]*)\s*=",
    re.DOTALL,
)
_BROWSER_GLOBAL_RE = re.compile(r"\b(window|document|localStorage|sessionStorage|navigator)\b")
_SCAN_SUBDIRS = ("src",)
_MAX_ISSUES_PER_FILE = 8

# Caddy-exposed preview ports per iteration (e2b/Caddyfile reverse-proxies
# 440N -> localhost:450N). QA targets the exposed 440N port — the same surface
# the preview serves — not the raw `next dev` port (450N), which is an internal
# detail that can churn or rebind independently of the stable Caddy contract.
# NOTE: these are PREVIEW ports (440N), not `next dev` ports — matches the
# `NEXTJS_ITER_PREVIEW_PORTS` vs `NEXTJS_ITER_DEV_PORTS` split in nextjs_preview.py.
# Do not "correct" these back to 450N; that reverts the Caddy-contract hardening.
_ITER_PREVIEW_PORTS: dict[str, int] = {"iter1": 4401, "iter2": 4402, "iter3": 4403}
_GLOBALS_CSS_IMPORT_ORDER_HINT = (
    "PostCSS requires all @import statements before other rules. "
    "Load fonts via next/font/google instead of raw @import."
)

# Severities we surface as actionable. axe-core maps WCAG contrast violations
# to "serious" (SEV_HIGH), not "critical", so gating on critical alone misses
# real accessibility failures. Confidence is intentionally NOT gated here —
# qa_scanner's confidence scorer downgrades borderline-but-real WCAG failures
# (small numeric deficit) to MEDIUM, which would empty the report.
# KEEP IN SYNC with models.is_actionable — this script is loaded standalone
# (stdlib-only, no sibling imports), so it cannot import the canonical copy.
_ACTIONABLE_SEVERITIES = {"critical", "high"}


CMS_VALIDATE_TIMEOUT_SECS = 180


class DevServerUnavailable(RuntimeError):
    """The iteration's preview server is not serving — a BLOCKING QA failure.

    Distinct from QA-tooling infra failures (scanner/LLM/report → ``error``): a
    down preview means the generated site is not running, which the coding agent
    must diagnose and fix (then re-validate). Surfaced as ``status: failed`` with
    a ``dev-server-down`` issue.
    """


def _emit(payload: dict) -> None:
    print(json.dumps(payload))


# ---------------------------------------------------------------------------
# Grafana instrumentation (sandbox → Loki via Alloy)
# ---------------------------------------------------------------------------
#
# QA runs entirely in-sandbox, so the backend never sees these verdicts. The
# established way to surface sandbox activity in Grafana is a structured log
# line under `$EFS_APP_PATH/logs/*.log`, which Grafana Alloy tails and ships to
# Loki (with application_id / creator_id attached as structured metadata). We
# write one `qa_scan` event per validate run: count of lines = "QA running",
# sum(issue_count) = "issues raised", sum(fixed_count) = "fixes done".


def _fixed_count(prev: list[dict], current: list[dict]) -> int:
    """Issues present last round but gone this round, keyed by (code, location)."""
    cur = {(i.get("code"), i.get("location")) for i in current}
    return sum(1 for i in prev if (i.get("code"), i.get("location")) not in cur)


def _build_qa_event(
    status: str,
    issues: list[dict],
    attempt: int,
    fixed_count: int,
    iter_name: str,
    dropped_count: int = 0,
) -> dict:
    by_code: dict[str, int] = {}
    for issue in issues:
        code = issue.get("code", "unknown")
        by_code[code] = by_code.get(code, 0) + 1
    return {
        "event": "qa_scan",
        "iteration_id": iter_name,
        "status": status,  # success | failed | error
        "attempt": attempt,  # 1 = initial, 2..3 = re-validations
        "issue_count": len(issues),  # "issues raised"
        "issues_by_code": by_code,  # drill-down (qa-collision, tsc-error, ...)
        "fixed_count": fixed_count,  # "fixes done" (resolved since last round)
        # Findings the AI verifier rejected (visual-spec design intent or a
        # visual false-positive call) — a Grafana view of suppression volume.
        "dropped_count": dropped_count,
    }


def _log_qa_event(event: dict) -> None:
    """Append one JSON line to `$EFS_APP_PATH/logs/qa.log` for Alloy→Loki.

    Best-effort: instrumentation must never break the scan, so any filesystem
    error is swallowed.
    """
    efs = os.environ.get("EFS_APP_PATH")
    if not efs:
        return
    try:
        log_dir = pathlib.Path(efs) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "qa.log").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event) + "\n")
    except OSError:
        pass


def _record_qa_verdict(
    status: str,
    issues: list[dict],
    iter_name: str,
    iter_dir: pathlib.Path,
    attempt: int,
    dropped_count: int = 0,
) -> None:
    """Persist cross-round issue state and ship the Loki event (no stdout).

    Computes "fixes done" by diffing this round's issues against the previous
    round's, persisted in `<iter_dir>/.qa_last_issues.json`. The sandbox FS
    survives across re-validation rounds, so this is the natural home for the
    cross-round delta. NOTE: a typecheck regression (prev round QA issues, this
    round tsc errors) counts the gone QA issues as "fixed" while raising the new
    tsc issues — accepted noise for a metric.
    """
    state = iter_dir / ".qa_last_issues.json"
    try:
        prev = json.loads(state.read_text(encoding="utf-8")) if state.exists() else []
    except (OSError, json.JSONDecodeError):
        prev = []
    fixed = _fixed_count(prev, issues)

    try:
        state.write_text(json.dumps(issues), encoding="utf-8")
    except OSError:
        pass
    _log_qa_event(_build_qa_event(status, issues, attempt, fixed, iter_name, dropped_count))


def _emit_verdict(
    status: str,
    issues: list[dict],
    iter_name: str,
    iter_dir: pathlib.Path,
    attempt: int,
) -> None:
    """Emit a real QA verdict: stdout JSON (agent contract) + Loki event."""
    payload: dict = {"status": status, "issues": issues, "iteration_id": iter_name}
    _emit(payload)
    _record_qa_verdict(status, issues, iter_name, iter_dir, attempt)


def _parse_tsc(output: str) -> list[dict]:
    issues: list[dict] = []
    for m in _TSC_ERROR_RE.finditer(output):
        issues.append(
            {
                "code": "tsc-error",
                "location": f"{m.group('path')}:{m.group('line')}:{m.group('col')}",
                "hint": m.group("msg").strip(),
            }
        )
    return issues


def _check_cms_fit(iter_dir: pathlib.Path) -> list[dict]:
    """Re-prove seed.json fits the Payload schema at QA time.

    Runs the `cms-management` validator's **structural** layer (field shape derived
    from the live config + bidirectional orphan-key + block-triple checks). The
    DB env is stripped on purpose: by QA time the seed is already committed to
    `payload_<iter>`, so a semantic Local-API write would hit a unique-slug
    conflict against the seeded docs and false-fail. The semantic invariant is
    gated at generate time (in an isolated scratch schema); here the structural
    re-check catches edits made after generation. Fit errors are returned as
    blocking `cms-fit` issues (path + hint) the agent repairs like a tsc error; a
    tooling failure is swallowed rather than masquerading as a content defect.
    """
    validator = SKILL_DIR.parent / "cms-management" / "scripts" / "validate_cms.mjs"
    if not validator.is_file() or not (iter_dir / "seed.json").is_file():
        return []
    # The validator flips the semantic layer on when APP_DATABASE_URL is set, so
    # structural-only must be enforced, not assumed of the inherited env.
    env = dict(os.environ)
    env.pop("APP_DATABASE_URL", None)
    try:
        proc = subprocess.run(  # noqa: S603 - args are static
            ["pnpm", "exec", "tsx", str(validator), "seed.json"],
            cwd=str(iter_dir),
            capture_output=True,
            text=True,
            check=False,
            timeout=CMS_VALIDATE_TIMEOUT_SECS,
            env=env,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []
    line = next((ln for ln in reversed((proc.stdout or "").splitlines()) if ln.strip()), "")
    try:
        result = json.loads(line)
    except (ValueError, json.JSONDecodeError):
        return []
    if result.get("ok"):
        return []
    return [
        {
            "code": "cms-fit",
            "location": f"seed.json:{e.get('path', '')}",
            "hint": f"{e.get('kind', 'fit-error')}: {e.get('hint', '')}",
        }
        for e in (result.get("errors") or [])
    ]


def _has_use_client_directive(source: str) -> bool:
    """Return true when the file starts with a valid Next.js client directive."""
    remaining = source.lstrip("\ufeff \t\r\n")
    while True:
        if remaining.startswith("//"):
            newline = remaining.find("\n")
            if newline == -1:
                return False
            remaining = remaining[newline + 1 :].lstrip(" \t\r\n")
            continue
        if remaining.startswith("/*"):
            end = remaining.find("*/")
            if end == -1:
                return False
            remaining = remaining[end + 2 :].lstrip(" \t\r\n")
            continue
        break
    return bool(_USE_CLIENT_DIRECTIVE_RE.match(remaining))


def _check_server_component_event_handlers(iter_dir: pathlib.Path) -> list[dict]:
    """Scan .tsx files for DOM event props in files missing ``"use client"``."""
    issues: list[dict] = []
    for subdir in _SCAN_SUBDIRS:
        scan_root = iter_dir / subdir
        if not scan_root.is_dir():
            continue
        for tsx_path in sorted(scan_root.rglob("*.tsx")):
            try:
                source = tsx_path.read_text(encoding="utf-8")
            except OSError:
                continue
            if _has_use_client_directive(source):
                continue
            rel_path = tsx_path.relative_to(iter_dir)
            seen_events: set[str] = set()
            for match in _JSX_EVENT_HANDLER_ATTR_RE.finditer(source):
                event_name = match.group(1)
                if event_name in seen_events:
                    continue
                seen_events.add(event_name)
                line_no = source.count("\n", 0, match.start(1)) + 1
                issues.append(
                    {
                        "code": "server-component-event-handler",
                        "location": f"{rel_path}:{line_no}",
                        "hint": (
                            f"JSX DOM event handler `{event_name}` appears in a Server Component. "
                            f"Add `'use client'` as the first statement in {rel_path}, or move the "
                            f"interactive form/button logic into a child Client Component. Next.js "
                            f"rejects event handlers in Server Components at preview startup."
                        ),
                    }
                )
    return issues


def _mask_comments_and_strings(source: str) -> str:
    """Replace comments and string contents with spaces while preserving offsets."""
    chars = list(source)
    i = 0
    while i < len(chars):
        char = chars[i]
        next_char = chars[i + 1] if i + 1 < len(chars) else ""
        if char == "/" and next_char == "/":
            chars[i] = chars[i + 1] = " "
            i += 2
            while i < len(chars) and chars[i] not in "\r\n":
                chars[i] = " "
                i += 1
            continue
        if char == "/" and next_char == "*":
            chars[i] = chars[i + 1] = " "
            i += 2
            while i < len(chars):
                if chars[i] == "*" and i + 1 < len(chars) and chars[i + 1] == "/":
                    chars[i] = chars[i + 1] = " "
                    i += 2
                    break
                if chars[i] not in "\r\n":
                    chars[i] = " "
                i += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
            chars[i] = " "
            i += 1
            while i < len(chars):
                current = chars[i]
                if current == "\\":
                    chars[i] = " "
                    if i + 1 < len(chars) and chars[i + 1] not in "\r\n":
                        chars[i + 1] = " "
                    i += 2
                    continue
                chars[i] = " " if current not in "\r\n" else current
                i += 1
                if current == quote:
                    break
            continue
        i += 1
    return "".join(chars)


def _is_jsx_text_occurrence(source: str, start: int, end: int) -> bool:
    """Return true for plain JSX text nodes such as ``<p>browser window</p>``."""
    prev = start - 1
    while prev >= 0 and source[prev] not in "<>{};":
        prev -= 1
    if prev < 0 or source[prev] != ">":
        return False

    next_pos = end
    while next_pos < len(source) and source[next_pos] not in "<{};":
        next_pos += 1
    return next_pos < len(source) and source[next_pos] == "<"


def _is_property_name_occurrence(source: str, start: int) -> bool:
    """Return true when a matched token is a property name, e.g. ``doc.document``."""
    prev = start - 1
    while prev >= 0 and source[prev].isspace():
        prev -= 1
    return prev >= 0 and source[prev] == "."


def _is_property_key_occurrence(source: str, end: int) -> bool:
    """Return true for property/type keys, e.g. ``{ document: value }``."""
    next_pos = end
    while next_pos < len(source) and source[next_pos].isspace():
        next_pos += 1
    if next_pos < len(source) and source[next_pos] == "?":
        next_pos += 1
        while next_pos < len(source) and source[next_pos].isspace():
            next_pos += 1
    return next_pos < len(source) and source[next_pos] == ":"


def _check_server_component_browser_globals(iter_dir: pathlib.Path) -> list[dict]:
    """Scan .tsx files for browser globals in files missing ``"use client"``."""
    issues: list[dict] = []
    for subdir in _SCAN_SUBDIRS:
        scan_root = iter_dir / subdir
        if not scan_root.is_dir():
            continue
        for tsx_path in sorted(scan_root.rglob("*.tsx")):
            try:
                source = tsx_path.read_text(encoding="utf-8")
            except OSError:
                continue
            if _has_use_client_directive(source):
                continue
            rel_path = tsx_path.relative_to(iter_dir)
            masked_source = _mask_comments_and_strings(source)
            seen_globals: set[str] = set()
            for match in _BROWSER_GLOBAL_RE.finditer(masked_source):
                global_name = match.group(1)
                if global_name in seen_globals:
                    continue
                if _is_property_name_occurrence(masked_source, match.start()):
                    continue
                if _is_property_key_occurrence(masked_source, match.end()):
                    continue
                if _is_jsx_text_occurrence(masked_source, match.start(), match.end()):
                    continue
                seen_globals.add(global_name)
                line_no = source.count("\n", 0, match.start(1)) + 1
                issues.append(
                    {
                        "code": "server-component-browser-global",
                        "location": f"{rel_path}:{line_no}",
                        "hint": (
                            f"Browser global `{global_name}` appears in a Server Component. "
                            f"Add `'use client'` as the first statement in {rel_path}, or move "
                            f"the browser-dependent logic into a child Client Component. Next.js "
                            f"server-rendering can crash at preview startup when Server Components "
                            f"read browser-only globals."
                        ),
                    }
                )
    return issues


# ---------------------------------------------------------------------------
# Production build check
# ---------------------------------------------------------------------------
#
# `pnpm typecheck` (tsc --noEmit) does NOT catch all errors that `next build`
# does.  In particular SWC rejects certain JSX patterns tsc accepts (e.g.
# mismatched tags inside conditional expressions).  Running `pnpm run build`
# compiles every file with SWC and catches the full class of errors generically.
#
# NOTE on `.next/` interaction: `next build` writes into the same `.next/`
# directory that the running `next dev` server uses.  After a successful build
# the dev server recompiles on the next request (HMR picks up the change), so
# the QA scan that follows can add a few seconds of warm-up but will still
# succeed.  If this proves flaky, an alternative is to build into an isolated
# `distDir` (requires patching next.config at runtime).

_BUILD_TIMEOUT_SECS = 300
_BUILD_OUTPUT_TAIL_LINES = 30


def _check_build_errors(iter_dir: pathlib.Path) -> list[dict]:
    """Run ``pnpm run build`` and surface any build errors.

    ``next build`` compiles all source files with SWC, catching parse errors
    that ``tsc --noEmit`` misses.  It can also fail for other reasons (e.g.
    static prerendering of server components that read from an unavailable
    DB).  Should only be called when typecheck has already passed (to avoid
    redundant error reports).
    """
    try:
        proc = subprocess.run(  # noqa: S603 - args are static, cwd is validated
            ["pnpm", "run", "build"],
            cwd=str(iter_dir),
            capture_output=True,
            text=True,
            check=False,
            timeout=_BUILD_TIMEOUT_SECS,
        )
    except subprocess.TimeoutExpired:
        return [
            {
                "code": "build-timeout",
                "location": str(iter_dir),
                "hint": f"`pnpm run build` timed out after {_BUILD_TIMEOUT_SECS}s.",
            }
        ]

    if proc.returncode == 0:
        return []

    output = (proc.stdout or "") + (proc.stderr or "")
    tail = output.strip().splitlines()[-_BUILD_OUTPUT_TAIL_LINES:]
    return [
        {
            "code": "build-error",
            "location": str(iter_dir),
            "hint": (
                "`next build` failed. This may be a SWC parse error (e.g. "
                "mismatched JSX tags), a static-prerender failure, or another "
                "build-time issue. Build output (last lines):\n" + "\n".join(tail)
            ),
        }
    ]


def _check_skeleton_bars(iter_dir: pathlib.Path) -> list[dict]:
    """Scan every .tsx file under `<iter>/src/` for skeleton-bar placeholders."""
    issues: list[dict] = []
    for subdir in _SCAN_SUBDIRS:
        scan_root = iter_dir / subdir
        if not scan_root.is_dir():
            continue
        for tsx_path in sorted(scan_root.rglob("*.tsx")):
            try:
                source = tsx_path.read_text(encoding="utf-8")
            except OSError:
                continue
            issues.extend(_scan_one_tsx(tsx_path, source, iter_dir))
    return issues


def _scan_one_tsx(tsx_path: pathlib.Path, source: str, iter_dir: pathlib.Path) -> list[dict]:
    matches: list[dict] = []
    rel_path = tsx_path.relative_to(iter_dir)
    seen_starts: set[int] = set()
    for div_re in _DIV_MATCHERS:
        for div_match in div_re.finditer(source):
            start = div_match.start()
            if start in seen_starts:
                continue
            seen_starts.add(start)
            attrs = div_match.group(1)
            if "aria-busy" in attrs and ("true" in attrs or "{true}" in attrs):
                continue
            if _ARIA_HIDDEN_RE.search(attrs):
                continue
            classname_match = _CLASSNAME_RE.search(attrs)
            if not classname_match:
                continue
            classname = (classname_match.group(1) or classname_match.group(2) or "").strip()
            if not _BG_TOKEN_RE.search(classname):
                continue
            if not _WIDTH_TOKEN_RE.search(classname):
                continue
            if not _HEIGHT_TOKEN_RE.search(classname):
                continue
            if _DIVIDER_DIMENSION_RE.search(classname):
                continue
            if _TINY_WIDTH_RE.search(classname):
                continue
            if _BLUR_CLASS_RE.search(classname):
                continue
            line_no = source.count("\n", 0, start) + 1
            matches.append(
                {
                    "line": line_no,
                    "classname": classname if len(classname) <= 120 else classname[:117] + "...",
                }
            )
    matches.sort(key=lambda m: m["line"])

    if not matches:
        return []

    issues: list[dict] = []
    for m in matches[:_MAX_ISSUES_PER_FILE]:
        issues.append(
            {
                "code": "placeholder-bar-mockup",
                "location": f"{rel_path}:{m['line']}",
                "hint": (
                    f"Empty <div /> or <div></div> with bg-color + width + height + no children "
                    f'(className="{m["classname"]}"). This is a skeleton-bar placeholder '
                    f"inside a rendered product visual — visually indistinguishable from "
                    f"the broken-raster failure Phase 1 was meant to prevent. Replace with "
                    f"populated content (real label / real value / real text from the block's "
                    f"props, authored in seed.json), or remove the element. See nextjs-code-writing "
                    f"SKILL.md § rule 7.6 and 7.7 for the populated-UI requirement and the "
                    f"wrong-vs-right worked example."
                ),
            }
        )
    remaining = len(matches) - _MAX_ISSUES_PER_FILE
    if remaining > 0:
        issues.append(
            {
                "code": "placeholder-bar-mockup",
                "location": f"{rel_path}:{matches[_MAX_ISSUES_PER_FILE]['line']}",
                "hint": (
                    f"... and {remaining} more skeleton-bar placeholders in {rel_path} "
                    f"(showing first {_MAX_ISSUES_PER_FILE}). After fixing the listed "
                    f"locations, re-run validate_files.py to surface the rest."
                ),
            }
        )
    return issues


def _check_nextjs_globals_css_import_order(iter_dir: pathlib.Path) -> list[dict]:
    """Flag the first ``@import`` in globals.css that appears after another rule."""
    css_path = iter_dir / "src" / "app" / "globals.css"
    try:
        css = css_path.read_text(encoding="utf-8")
    except OSError:
        return []

    seen_non_import_rule = False
    in_block_comment = False
    rel_path = css_path.relative_to(iter_dir)

    for line_no, line in enumerate(css.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
                stripped = stripped.split("*/", 1)[1].strip()
                if not stripped:
                    continue
            else:
                continue

        while stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block_comment = True
                stripped = ""
                break
            stripped = stripped.split("*/", 1)[1].strip()
        if not stripped or stripped.startswith("//"):
            continue

        if stripped.startswith("@import"):
            if seen_non_import_rule:
                return [
                    {
                        "code": "css-import-order",
                        "category": "css-import-order",
                        "severity": "high",
                        "location": f"{rel_path}:{line_no}",
                        "message": _GLOBALS_CSS_IMPORT_ORDER_HINT,
                        "hint": _GLOBALS_CSS_IMPORT_ORDER_HINT,
                    }
                ]
            continue

        if stripped.startswith("@charset"):
            continue

        seen_non_import_rule = True

    return []


# ---------------------------------------------------------------------------
# QA scan helpers
# ---------------------------------------------------------------------------


def _wait_for_dev_server(port: int, timeout: int = 30) -> bool:
    """Poll http://localhost:{port} until it responds or timeout elapses."""
    deadline = time.monotonic() + timeout
    url = f"http://localhost:{port}"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):  # noqa: S310
                return True
        except (urllib.error.URLError, OSError):
            time.sleep(2)
    return False


_SMOKE_CHECK_TIMEOUT_SECS = 45
_PREVIEW_ERROR_BODY_LIMIT = 1500


def _smoke_check_homepage(port: int) -> str | None:
    """Render the iteration homepage once and assert it does not 5xx.

    Returns None when the homepage serves a non-5xx response (it executed and
    rendered). Returns an actionable detail string — including the captured
    response body, the real runtime error — when the server never comes up or
    keeps returning a 5xx.

    This is the lightweight runtime gate on the validate path:
    `pnpm typecheck` compiles the code but never executes a request, so a
    runtime-only crash (a server component that throws on a bad Payload/DB read,
    a request-time config error) compiles clean yet 500s when the page is
    actually rendered. Hitting the homepage here catches that class of failure
    where the coding agent can still read it and fix it.
    """
    deadline = time.monotonic() + _SMOKE_CHECK_TIMEOUT_SECS
    url = f"http://localhost:{port}/"
    last_detail = f"preview server on port {port} did not respond"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5):  # noqa: S310
                # urlopen only returns for 2xx/3xx — the server executed and
                # rendered. (4xx/5xx raise HTTPError, handled below.)
                return None
        except urllib.error.HTTPError as exc:
            # A 4xx is a content/routing problem the cms-fit check owns, not a
            # server crash. A 5xx is a render crash — capture the body (the
            # Next.js error page / stack) and keep retrying in case the first
            # hit raced the dev server's on-demand compile.
            if exc.code < 500:
                return None
            body = b""
            try:
                body = exc.read()
            except OSError:
                pass
            last_detail = _format_preview_error(exc.code, body)
        except (urllib.error.URLError, OSError):
            # Connection refused/reset — server not up yet (compiling) or dead.
            pass
        time.sleep(2)
    return last_detail


def _format_preview_error(status: int, body: bytes) -> str:
    """Render a captured preview response (status + body tail) for an issue hint."""
    snippet = body.decode("utf-8", "replace").strip()[:_PREVIEW_ERROR_BODY_LIMIT]
    return f"homepage returned HTTP {status}. Response body (truncated):\n{snippet}"


def _find_qa_scanner() -> str | None:
    """Return the path to qa_scanner.py (sibling of this file), or None if missing."""
    candidate = pathlib.Path(__file__).parent / "qa_scanner.py"
    return str(candidate) if candidate.is_file() else None


def _qa_issue_location(raw: dict) -> str:
    """Pick a `file:line` location from a QA issue's code_references, falling back to URL."""
    refs = raw.get("code_references") or []
    if refs:
        first = refs[0]
        file = first.get("file")
        line = first.get("line")
        if file and line:
            return f"{file}:{line}"
        if file:
            return file
    return raw.get("url") or ""


def _normalize_qa_issues(raw_issues: list[dict]) -> list[dict]:
    """Filter to actionable QA issues and normalize to {code, location, hint}.

    Mirrors qa_scanner.py's actionable filter: severity in {critical, high},
    excluding findings the AI verifier dropped (spec-sanctioned or judged a
    false positive) — those stay in the JSON report for Kite Inspector only.
    """
    out: list[dict] = []
    for raw in raw_issues:
        if raw.get("severity") not in _ACTIONABLE_SEVERITIES:
            continue
        if raw.get("dropped"):
            continue
        out.append(
            {
                "code": f"qa-{raw.get('type', 'unknown')}",
                "location": _qa_issue_location(raw),
                "hint": raw.get("ai_reasoning") or raw.get("reasoning") or "",
            }
        )
    return out


def _run_qa_scan(iter_name: str, iter_dir: pathlib.Path) -> tuple[list[dict], int]:
    """Run qa_scanner.py against the iteration's dev server.

    Returns (issues, dropped_count): the normalized list of critical +
    high-severity findings, and how many findings the AI verifier dropped.
    The scanner writes the JSON report and the interactive HTML report next
    to each other under ``docs/qa/``.

    Raises ``DevServerUnavailable`` when the preview server is not serving,
    and plain ``RuntimeError`` for QA-tooling/env infra failures (scanner
    binary, LLM key, scanner crash, report I/O). Both are recorded as ``error``
    qa_scan events by the background caller — a spike in Grafana means the
    scanner is globally broken and must not be masked as green iterations.
    """
    port = _ITER_PREVIEW_PORTS.get(iter_name)
    if port is None:
        raise RuntimeError(f"No preview port configured for iteration {iter_name!r}")

    scanner = _find_qa_scanner()
    if scanner is None:
        raise RuntimeError("qa_scanner.py not found alongside validate_files.py")

    # The Caddy preview port falls through to `docs/<iter>/prototype/index.html`
    # via file_server *before* proxying to `next dev` (e2b/Caddyfile prototype-server).
    # A clean Next.js iter has no such file, but a re-seeded EFS tree that once ran
    # an HTML generation can leave a stale one — which would make us QA static HTML
    # on the preview port instead of the live Next.js app, silently passing. Fail
    # loudly rather than scan the wrong thing.
    stale_prototype = iter_dir.parent.parent / "docs" / iter_name / "prototype" / "index.html"
    if stale_prototype.is_file() and stale_prototype.stat().st_size > 0:
        raise RuntimeError(
            f"Stale prototype file {stale_prototype} shadows the Next.js preview on the "
            f"Caddy port — QA would scan static HTML, not the live app. Remove it and re-run."
        )

    if not _wait_for_dev_server(port, timeout=30):
        raise DevServerUnavailable(
            f"Preview server for {iter_name} is not responding on port {port} after 30 s, "
            f"so QA cannot scan it. First read the dev server logs "
            f"(`pm2 logs nextjs-{iter_name} --lines 50 --nostream --err`). If they show a "
            f"crash, fix its cause in the generated code (e.g. a next.config.js / middleware "
            f"syntax error, a bad import, or a runtime error `pnpm typecheck` did not catch) "
            f"and re-validate. If the logs show a slow or in-progress compile, just "
            f"re-validate. Do not restart or re-permission the dev server — the platform "
            f"owns its lifecycle."
        )

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set — QA scan requires LLM verification")

    qa_dir = iter_dir / "docs" / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)

    v = 1
    while (qa_dir / f"qa_scan_report_v{v}.json").exists():
        v += 1
    json_report = str(qa_dir / f"qa_scan_report_v{v}.json")
    url = f"http://localhost:{port}"
    code_path = str(iter_dir / "src")

    scanner_args = [
        "python3",
        scanner,
        url,
        "--viewports",
        "1920",
        "--code-path",
        code_path,
        "--output",
        json_report,
    ]
    # Design intent: the iteration's visual spec lets the verifier dismiss
    # intentional overlaps/clipping/low-contrast treatments the spec calls for.
    visual_spec = iter_dir / "visual_spec.md"
    if visual_spec.is_file():
        scanner_args += ["--visual-spec", str(visual_spec)]

    try:
        proc = subprocess.run(  # noqa: S603 - args are controlled
            scanner_args,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
            env=dict(os.environ),
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "qa_scanner.py timed out after 180 s (orphan Chromium processes may remain)"
        )
    except Exception as exc:
        raise RuntimeError(f"qa_scanner.py failed to launch: {exc}") from exc

    # Exit code 2 means infrastructure failure in qa_scanner (e.g. Playwright
    # not installed, browser crash). Exit codes 0 and 1 both indicate the
    # scanner ran to completion (0 = no actionable issues, 1 = critical/high-severity issues).
    if proc.returncode not in (0, 1):
        stderr_tail = (proc.stderr or "").strip().splitlines()[-5:]
        raise RuntimeError(
            f"qa_scanner.py exited with code {proc.returncode} (infra failure): "
            + " | ".join(stderr_tail)
        )

    try:
        report = json.loads(pathlib.Path(json_report).read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Could not read QA report {json_report}: {exc}") from exc

    raw_issues = report.get("issues", [])
    dropped_count = sum(1 for i in raw_issues if i.get("dropped"))
    return _normalize_qa_issues(raw_issues), dropped_count


# ---------------------------------------------------------------------------
# Background QA scan — reporting-only telemetry, detached from the agent
# ---------------------------------------------------------------------------


def _spawn_background_qa_scan(iter_name: str, iter_dir: pathlib.Path) -> None:
    """Detach the reporting-only QA scan (sibling ``background_scan.py``).

    The scan cap and in-flight lock live in the spawned process; this side
    only detaches it. Best-effort by design: spawn failures must never affect
    the agent-facing verdict.
    """
    script = pathlib.Path(__file__).parent / "background_scan.py"
    try:
        qa_dir = iter_dir / "docs" / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        with (qa_dir / "qa_scan_background.log").open("ab") as log_file:
            subprocess.Popen(  # noqa: S603 - args are controlled
                [sys.executable, str(script), iter_name],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=dict(os.environ),
            )
    except Exception as exc:  # noqa: BLE001 - telemetry must not block the verdict
        _log_qa_event(_build_qa_event("error", [], 0, 0, iter_name))
        print(f"background QA scan spawn failed: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    args = sys.argv[1:]

    # iter slug: positional arg overrides the ITERATION_ID env default.
    iter_name = args[0] if args else os.environ.get("ITERATION_ID")
    if not iter_name:
        _emit({"status": "error", "error": "no iter_name: pass as arg or set ITERATION_ID env"})
        return 2

    efs = os.environ.get("EFS_APP_PATH")
    if not efs:
        _emit({"status": "error", "error": "EFS_APP_PATH env var not set"})
        return 2
    # Iter project tree lives at $EFS_APP_PATH/iterations/<iter>/ per the
    # ecosystem config contract (e2b/generate-ecosystem-config.mjs).
    iter_dir = pathlib.Path(efs) / "iterations" / iter_name

    # attempt number shown in Loki events for static-check failures: 1 = before
    # the first QA scan, 2..N = after re-validations. Read-only here — only
    # background_scan.py consumes slots against KITE_QA_MAX_CALLS.
    _counter_path = iter_dir / ".qa_validate_count"
    try:
        _call_count = int(_counter_path.read_text()) if _counter_path.exists() else 0
    except (OSError, ValueError):
        _call_count = 0
    attempt = _call_count + 1

    if not (iter_dir / "package.json").is_file():
        _emit({"status": "error", "error": f"package.json missing: {iter_dir}"})
        return 2

    # Preflight: without node_modules, `pnpm typecheck` emits hundreds of
    # "Cannot find module 'next'" errors that swamp OpenCode's bash output
    # cap and force the agent into a long recovery loop. Emit one
    # actionable error instead. Probe for `node_modules/next/package.json`
    # specifically rather than just the directory's existence — a
    # half-installed iter (dir present, deps missing) is a real shape we
    # have seen and the bare-directory check waved it through.
    next_pkg = iter_dir / "node_modules" / "next" / "package.json"
    if not next_pkg.is_file():
        _emit(
            {
                "status": "error",
                "error": (
                    f"node_modules/next not installed at {iter_dir} — run "
                    f"`pnpm install --ignore-workspace --prefer-offline` inside "
                    f"{iter_dir} and re-run validate_files.py"
                ),
            }
        )
        return 2

    proc = subprocess.run(  # noqa: S603 - args are static, cwd is validated
        ["pnpm", "typecheck"],
        cwd=str(iter_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")

    issues: list[dict] = []
    if proc.returncode != 0:
        issues.extend(_parse_tsc(output))
        if not issues:
            # pnpm or tsc failed without emitting a structured error — surface
            # the raw tail so the agent has something to act on.
            tail = output.strip().splitlines()[-20:]
            issues.append(
                {
                    "code": "tsc-unstructured",
                    "location": str(iter_dir),
                    "hint": "\n".join(tail),
                }
            )
    else:
        # Typecheck passed — run a full production build to catch SWC
        # compilation errors that tsc --noEmit misses.
        issues.extend(_check_build_errors(iter_dir))
    issues.extend(_check_nextjs_globals_css_import_order(iter_dir))
    issues.extend(_check_skeleton_bars(iter_dir))
    issues.extend(_check_cms_fit(iter_dir))
    issues.extend(_check_server_component_event_handlers(iter_dir))
    issues.extend(_check_server_component_browser_globals(iter_dir))

    if issues:
        _emit_verdict("failed", issues, iter_name, iter_dir, attempt)
        return 1

    # Runtime smoke gate. `pnpm typecheck` compiles but never executes a
    # request, so a runtime-only crash (e.g. a server component that throws on
    # a bad Payload/DB read) passes typecheck yet 500s when rendered. Render
    # the homepage once so that failure is caught HERE — where the coding agent
    # can read it and fix it — instead of slipping through to the platform's
    # post-generation preview readiness poll as a terminal, non-retryable
    # failure. With the QA scan detached, this is also the only remaining
    # synchronous check that exercises the live server.
    port = _ITER_PREVIEW_PORTS.get(iter_name)
    if port is not None:
        smoke_detail = _smoke_check_homepage(port)
        if smoke_detail is not None:
            _emit_verdict(
                "failed",
                [
                    {
                        "code": "dev-server-error",
                        "location": f"iterations/{iter_name}",
                        "hint": (
                            f"{smoke_detail}\n\n"
                            f"The page compiles but crashes when rendered. Read the dev "
                            f"server logs (`pm2 logs nextjs-{iter_name} --lines 50 "
                            f"--nostream --err`) for the full stack, fix the runtime cause "
                            f"in the generated code, then re-validate. Do not restart or "
                            f"re-permission the dev server — the platform owns its lifecycle."
                        ),
                    }
                ],
                iter_name,
                iter_dir,
                attempt,
            )
            return 1

    # The visual QA scan is reporting-only telemetry: run it as a detached
    # background task so the coding agent never waits on it and never sees
    # its findings — QA findings must not trigger agent fix passes.
    _spawn_background_qa_scan(iter_name, iter_dir)

    _emit({"status": "success", "issues": [], "iteration_id": iter_name})
    return 0


if __name__ == "__main__":
    sys.exit(main())
