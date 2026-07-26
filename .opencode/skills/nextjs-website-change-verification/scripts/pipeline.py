"""End-to-end scan orchestrator.

Pipeline: launch → navigate → stabilize → scroll-extract-detect → axe contrast
→ score → dedup → assign IDs → code-match → crop → AI verify (non-contrast)
→ assemble JSON report.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

from blocked import detect_blocked_interactions
from browser import ERROR_OVERLAY_JS, BrowserController, scroll_and_extract, stabilize_page
from clipping import detect_clipping
from code_matching import collect_source_files, match_issues_to_code
from collision import detect_collisions
from config import ScanConfig
from contrast import detect_contrast_via_axe
from dedup import _dedup
from models import (
    SEV_CRITICAL,
    TYPE_BLOCKED,
    TYPE_CLIPPING,
    TYPE_COLLISION,
    TYPE_CONTRAST,
    TYPE_RUNTIME,
    VERDICT_DISMISSED,
    BlockedInteractionIssue,
    ContrastIssue,
    Viewport,
    dropped_source_for_basis,
)
from scoring import score_and_filter
from verification import (
    _HAS_PIL,
    _crop_issue_from_viewport,
    _get_issue_crop_region,
    _verify_all_issues,
    load_design_intent,
)

logger = logging.getLogger("qa_scanner")


def _absolute_region(issue) -> dict:
    """Document-absolute bounding box of the issue region, as a plain dict.

    Collision/clipping bboxes are viewport-relative to the scroll position of
    the snapshot they were detected in; contrast bboxes are already
    document-absolute (axe adds ``window.scrollY``). The HTML report uses these
    coordinates to place highlight overlays on the full-page screenshot.
    """
    region = _get_issue_crop_region(issue)
    y = region.y if isinstance(issue, ContrastIssue) else region.y + issue.scroll_position
    return {
        "x": round(region.x, 1),
        "y": round(y, 1),
        "width": round(region.width, 1),
        "height": round(region.height, 1),
    }


async def run_scan(config: ScanConfig) -> tuple[dict, list]:
    start = time.monotonic()
    ctrl = BrowserController(config.viewport_width, config.VIEWPORT_HEIGHT)

    all_issues = []
    total_elements = 0
    contrast_skipped: Optional[str] = None
    # Runtime errors (pageerror / hydration mismatch / crash) captured by the
    # browser controller across the whole session. Collected before close.
    runtime_errors: list[dict] = []
    # Maps scroll_y → screenshot path for resolving per-issue screenshots
    scroll_screenshots: dict[float, str] = {}
    # Maps scroll_y → raw PNG bytes for per-issue cropping
    scroll_screenshot_bytes: dict[float, bytes] = {}
    # Full-page screenshot path for the interactive HTML report (best-effort)
    full_page_screenshot: Optional[str] = None

    error_overlay: Optional[str] = None

    try:
        await ctrl.launch()
        await ctrl.navigate(config.url)
        await stabilize_page(ctrl, config)

        # If a dev-server error overlay is up, the rendered site is the error,
        # not the app. Void all visual detection (collision/clipping/contrast/
        # blocked) — every finding behind the overlay is invisible to the user
        # — and report only the runtime error that caused it.
        try:
            error_overlay = await ctrl.page.evaluate(ERROR_OVERLAY_JS)
        except Exception:
            error_overlay = None

        if error_overlay:
            logger.warning(
                "error overlay present — skipping visual detection: %s",
                error_overlay[:120],
            )
        else:
            async for snapshot in scroll_and_extract(ctrl, config):
                elements = snapshot.elements
                total_elements = max(total_elements, len(elements))
                viewport = snapshot.viewport
                scroll_y = snapshot.scroll_position
                url = snapshot.url

                if snapshot.screenshot_path:
                    scroll_screenshots[scroll_y] = snapshot.screenshot_path
                if snapshot.screenshot_bytes:
                    scroll_screenshot_bytes[scroll_y] = snapshot.screenshot_bytes

                all_issues.extend(detect_collisions(elements, viewport, scroll_y, url, config))
                all_issues.extend(detect_clipping(elements, viewport, scroll_y, url, config))
                all_issues.extend(
                    detect_blocked_interactions(snapshot.blocked_hits, viewport, scroll_y, url)
                )

            # Contrast runs once per page (axe inspects the whole DOM regardless
            # of viewport scroll). ``None`` means axe is unavailable or errored —
            # zero contrast checks ran, which is surfaced in the report rather
            # than masked as a clean result.
            axe_contrast = await detect_contrast_via_axe(ctrl.page, ctrl.current_viewport, url)
            if axe_contrast is not None:
                all_issues.extend(axe_contrast)
                logger.info("contrast: %d issues via axe-core", len(axe_contrast))
            else:
                contrast_skipped = "axe-core unavailable — no contrast checks ran"
                logger.warning("contrast: %s", contrast_skipped)

        # Drain runtime errors now, while the page is alive and hydration has
        # had the full scan (navigate → stabilize → scroll → contrast) to fire.
        runtime_errors = await ctrl.collect_runtime_errors()
        if runtime_errors:
            logger.info("runtime: %d error(s) captured", len(runtime_errors))
        # The overlay text is the error itself — surface it even if the JS
        # listeners missed the underlying throw, so the scan is never silently
        # empty when the site failed to render.
        if error_overlay and not runtime_errors:
            runtime_errors = [{"kind": "error-overlay", "message": error_overlay, "stack": ""}]

        # Full-page screenshot for the interactive HTML report — one image the
        # report overlays issue highlights on. Best-effort: the scan verdict
        # never depends on it.
        if config.screenshots_dir:
            try:
                os.makedirs(config.screenshots_dir, exist_ok=True)
                path = os.path.join(config.screenshots_dir, "full_page.png")
                await ctrl.page.screenshot(path=path, full_page=True, type="png")
                full_page_screenshot = path
            except Exception as exc:
                logger.warning("full-page screenshot failed: %s", exc)
    finally:
        await ctrl.close()

    # Unverifiable hypotheses: axe "incomplete" contrast candidates exist only
    # to be AI-verified (axe could not compute a ratio; the crop decides).
    # Without verification they are speculation, not findings — drop them so
    # no-verify runs (evals, local harnesses) don't report unreviewed guesses.
    if not config.enable_verification:
        all_issues = [
            i for i in all_issues if not (isinstance(i, ContrastIssue) and i.needs_ai_verification)
        ]

    # Score and filter low-confidence issues
    scored = score_and_filter(all_issues, config)

    # Deduplicate across scroll positions
    viewport = Viewport(width=config.viewport_width, height=config.VIEWPORT_HEIGHT)
    deduped = _dedup(scored, viewport)

    # Assign stable IDs
    counters = {TYPE_COLLISION: 0, TYPE_CLIPPING: 0, TYPE_CONTRAST: 0, TYPE_BLOCKED: 0}
    for issue in deduped:
        prefix = issue.issue_type
        issue.issue_id = f"{prefix}-{counters[prefix]:03d}"
        counters[prefix] += 1

    # Code matching
    code_references_map: dict = {}
    if config.code_path:
        source_files = collect_source_files(config.code_path, config.CODE_MAX_KB)
        if source_files:
            code_references_map = match_issues_to_code(
                deduped, source_files, config.MAX_MATCHES_PER_ISSUE
            )

    # Build nearest-screenshot lookup from the scroll→path map captured above
    _screenshot_scroll_keys = sorted(scroll_screenshots.keys())

    def _nearest_screenshot(scroll_y: float) -> Optional[str]:
        if not _screenshot_scroll_keys:
            return None
        closest = min(_screenshot_scroll_keys, key=lambda y: abs(y - scroll_y))
        return scroll_screenshots[closest]

    # Attach code references and viewport screenshot fallback
    for idx, issue in enumerate(deduped):
        refs = code_references_map.get(idx, [])
        issue.code_references = [
            {
                "file": m.relative_path,
                "line": m.line_number,
                "snippet": m.line_content,
                "context": m.context_before + [m.line_content] + m.context_after,
                "reason": m.match_reason,
            }
            for m in refs
        ]
        issue.screenshot = _nearest_screenshot(issue.scroll_position)

    # Per-issue cropped screenshots — always done when PIL is available
    crop_b64_map: dict[str, str] = {}
    if scroll_screenshot_bytes and _HAS_PIL:
        _crop_scroll_keys = sorted(scroll_screenshot_bytes.keys())
        for issue in deduped:
            closest_y = min(_crop_scroll_keys, key=lambda y: abs(y - issue.scroll_position))
            vp_bytes = scroll_screenshot_bytes[closest_y]
            try:
                crop_b64, crop_path = _crop_issue_from_viewport(
                    vp_bytes, issue, issue.issue_id, config, viewport_scroll_y=closest_y
                )
                if crop_path:
                    issue.screenshot = crop_path
                if crop_b64:
                    crop_b64_map[issue.issue_id] = crop_b64
            except Exception as exc:
                logger.debug("Crop failed for %s: %s", issue.issue_id, exc)

    # AI verification — uses pre-computed crops. Deterministic ContrastIssues
    # (axe violations) normally skip verification: axe is battle-tested, and the
    # LLM verifier's prompt is biased toward rubber-stamping deterministic
    # findings (so it adds no real signal but adds latency + cost).
    # ContrastIssues derived from axe "incomplete" results
    # (needs_ai_verification=True) are heuristic candidates and DO go through
    # verification. When a visual spec is available (design intent injected via
    # load_design_intent), deterministic violations go through verification too
    # — the spec may document the low-contrast treatment as intentional, and
    # only the verifier can weigh that.
    # Verification routing, one predicate per issue:
    # - Blocked-interaction issues always skip verification: the blocker is
    #   often visually invisible (a transparent overlay), so a screenshot
    #   cannot confirm or refute the hit-test — which is itself the browser's
    #   authoritative paint-order answer.
    # - Deterministic axe contrast violations skip it too (axe's ratio math is
    #   exact and the verifier tends to rubber-stamp it) — unless a visual
    #   spec exists, because only the verifier can weigh documented design
    #   intent against the numbers.
    if config.enable_verification and crop_b64_map:
        design_intent = load_design_intent(config)

        def _skips_verification(issue) -> bool:
            if isinstance(issue, BlockedInteractionIssue):
                return True
            return (
                isinstance(issue, ContrastIssue)
                and not issue.needs_ai_verification
                and not design_intent
            )

        unverified = [i for i in deduped if _skips_verification(i)]
        verifiable = [i for i in deduped if not _skips_verification(i)]
        deduped = unverified + await _verify_all_issues(
            verifiable, crop_b64_map, config, design_intent
        )

    elapsed = time.monotonic() - start

    # Build output. Dismissed issues stay in the JSON (marked ``dropped``) so
    # Kite Inspector can track what the verifier rejected and why — but they
    # are excluded from the per-type counts every actionable consumer reads.
    kept = [i for i in deduped if i.ai_verdict != VERDICT_DISMISSED]
    summary = {
        "total": len(kept) + len(runtime_errors),
        TYPE_COLLISION: sum(1 for i in kept if i.issue_type == TYPE_COLLISION),
        TYPE_CLIPPING: sum(1 for i in kept if i.issue_type == TYPE_CLIPPING),
        TYPE_CONTRAST: sum(1 for i in kept if i.issue_type == TYPE_CONTRAST),
        TYPE_BLOCKED: sum(1 for i in kept if i.issue_type == TYPE_BLOCKED),
        TYPE_RUNTIME: len(runtime_errors),
        "dropped": len(deduped) - len(kept),
    }

    issues_out = []
    for issue in deduped:
        dropped = issue.ai_verdict == VERDICT_DISMISSED
        issues_out.append(
            {
                "id": issue.issue_id,
                "type": issue.issue_type,
                "severity": issue.severity,
                "confidence": round(issue.confidence_score, 3),
                "confidence_level": issue.confidence_level,
                "scroll_position": issue.scroll_position,
                "region": _absolute_region(issue),
                "screenshot": issue.screenshot,
                "reasoning": issue.reasoning,
                "ai_verdict": issue.ai_verdict,
                "ai_reasoning": issue.ai_reasoning,
                "dropped": dropped,
                # Kite Inspector's dropped_source contract: spec-sanctioned
                # drops vs the verifier's own visual false-positive calls.
                "dropped_source": dropped_source_for_basis(issue.ai_dismissal_basis)
                if dropped
                else None,
                "dropped_reason": issue.ai_reasoning if dropped else None,
                "code_references": issue.code_references,
            }
        )

    # Runtime errors are deterministic browser signals — always critical, no
    # screenshot/crop, no AI verification. They reuse the same issue shape so
    # validate_files.py's _normalize_qa_issues surfaces them like any other
    # blocking finding (severity → gate, reasoning → agent-facing hint).
    for idx, err in enumerate(runtime_errors):
        message = err.get("message", "") or "unknown runtime error"
        stack = err.get("stack", "") or ""
        frame = next((ln.strip() for ln in stack.splitlines() if ln.strip().startswith("at ")), "")
        reasoning = f"{err.get('kind', 'runtime')}: {message}"
        if frame:
            reasoning += f"\n{frame}"
        issues_out.append(
            {
                "id": f"{TYPE_RUNTIME}-{idx:03d}",
                "type": TYPE_RUNTIME,
                "severity": SEV_CRITICAL,
                "confidence": 1.0,
                "confidence_level": "high",
                "scroll_position": 0,
                "region": None,
                "screenshot": None,
                "reasoning": reasoning,
                "ai_verdict": None,
                "ai_reasoning": None,
                "dropped": False,
                "dropped_source": None,
                "dropped_reason": None,
                "code_references": [],
            }
        )

    report = {
        "url": config.url,
        "viewports": [{"width": config.viewport_width, "height": config.VIEWPORT_HEIGHT}],
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "total_elements": total_elements,
        "full_page_screenshot": full_page_screenshot,
        "summary": summary,
        "issues": issues_out,
    }
    if contrast_skipped:
        report["contrast_skipped"] = contrast_skipped
    if error_overlay:
        # Marks a scan voided by a dev-server error overlay: only the runtime
        # error is reported; visual detection was skipped as unmeasurable.
        report["error_state"] = error_overlay
    return report, deduped
