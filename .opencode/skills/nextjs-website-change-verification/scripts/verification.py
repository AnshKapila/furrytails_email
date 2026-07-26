"""LLM-backed verification of detected issues.

Pipeline:
1. Load prompt sections from ``references/verification.md``.
2. Crop a tight per-issue region from the cached viewport screenshot (PIL).
3. Build an issue-type-specific prompt + image payload.
4. POST through the sandbox metadata-proxy at localhost:8787 (OpenAI-compatible).
5. Fan out concurrently (semaphore caps parallelism) with model fallback chain.

Deterministic contrast issues (axe violations) skip verification — axe is
deterministic and the verifier's prompt biases toward rubber-stamping
deterministic findings. Contrast candidates derived from axe "incomplete"
results (needs_ai_verification=True) DO go through verification.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import sys
import urllib.error
import urllib.request

from config import ScanConfig
from models import (
    BASIS_DESIGN_INTENT,
    BASIS_VISUAL,
    VERDICT_CONFIRMED,
    VERDICT_DISMISSED,
    BlockedInteractionIssue,
    BoundingBox,
    ClippingIssue,
    CollisionIssue,
    ContrastIssue,
    ElementData,
    Issue,
)

try:
    from PIL import Image as _PILImage  # type: ignore[import-not-found]

    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

# Shared LLM utilities (proxy_url, etc.) — same lib used by plan/generate scripts.
# Path layout: skills/nextjs-website-change-verification/scripts/verification.py → skills/lib/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lib"))
import llm_utils  # noqa: E402

logger = logging.getLogger("qa_scanner")


def _load_verification_sections() -> dict[str, str]:
    """Load prompt sections from ``references/verification.md``.

    Convention: top-level ``# SECTION_NAME`` headings are section delimiters;
    ``##``+ headings are treated as section content. Do not use single-``#``
    headings for prose inside a section — they will create a bogus section key.
    """
    md_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "references", "verification.md"
    )
    sections: dict[str, str] = {}
    current: str = "VERIFICATION_BASE"
    buf: list[str] = []
    with open(md_path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.startswith("# "):
                sections[current] = "\n".join(buf).strip()
                current = line[2:].strip()
                buf = []
            else:
                buf.append(line)
    sections[current] = "\n".join(buf).strip()
    _EXPECTED = {
        "VERIFICATION_BASE",
        "VERIFICATION_DESIGN_INTENT",
        "VERIFICATION_COLLISION",
        "VERIFICATION_PARENT_OVERFLOW",
        "VERIFICATION_CLIPPING",
        "VERIFICATION_CONTRAST",
    }
    missing = _EXPECTED - sections.keys()
    if missing:
        raise ValueError(f"verification.md missing sections: {missing}")
    return sections


# Sections are loaded on first use so that a missing/malformed verification.md
# does NOT abort the import and kill the entire scan pipeline before any of the
# deterministic checks (collision, clipping, contrast) have a chance to run.
_sections: dict[str, str] | None = None


def _get_sections() -> dict[str, str]:
    global _sections
    if _sections is None:
        _sections = _load_verification_sections()
    return _sections


# Cap the spec excerpt so a sprawling visual spec cannot crowd out the issue
# details or the screenshot in the verifier's context.
_VISUAL_SPEC_MAX_CHARS = 8000


def load_design_intent(config: ScanConfig) -> str:
    """Render the design-intent prompt section from ``config.visual_spec_path``.

    Returns "" when no spec is configured, readable, and non-empty — the
    verification prompt then carries no design-intent block and behaves
    exactly as before.
    """
    path = config.visual_spec_path
    if not path:
        return ""
    try:
        with open(path, encoding="utf-8") as fh:
            spec = fh.read().strip()
    except OSError as exc:
        logger.warning("visual spec unreadable at %s: %s", path, exc)
        return ""
    if not spec:
        return ""
    if len(spec) > _VISUAL_SPEC_MAX_CHARS:
        spec = spec[:_VISUAL_SPEC_MAX_CHARS] + "\n[... truncated ...]"
    return _get_sections()["VERIFICATION_DESIGN_INTENT"].format(spec=spec)


# ---------------------------------------------------------------------------
# Per-issue screenshot cropping
# ---------------------------------------------------------------------------


def _union_bbox(a: BoundingBox, b: BoundingBox) -> BoundingBox:
    """Smallest bounding box enclosing both ``a`` and ``b``."""
    min_x = min(a.x, b.x)
    min_y = min(a.y, b.y)
    max_x = max(a.right, b.right)
    max_y = max(a.bottom, b.bottom)
    return BoundingBox(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)


def _get_issue_crop_region(issue: Issue) -> BoundingBox:
    """Return the bounding box region for an issue (viewport-relative coordinates)."""
    if isinstance(issue, CollisionIssue):
        return _union_bbox(issue.element_a.bbox, issue.element_b.bbox)
    if isinstance(issue, ClippingIssue):
        # For child-overflow, show both element and container so the protrusion is visible.
        if issue.clipped_element.selector != issue.clipping_ancestor.selector:
            return _union_bbox(issue.clipped_element.bbox, issue.clipping_ancestor.bbox)
        return issue.clipped_element.bbox
    if isinstance(issue, ContrastIssue):
        return issue.element.bbox
    if isinstance(issue, BlockedInteractionIssue):
        return _union_bbox(issue.target.bbox, issue.blocker.bbox)
    return BoundingBox(x=0, y=0, width=400, height=300)


def _crop_issue_from_viewport(
    viewport_png: bytes,
    issue: Issue,
    issue_id: str,
    config: ScanConfig,
    viewport_scroll_y: float = 0.0,
) -> tuple[str, str]:
    """Crop a tight per-issue region from a viewport screenshot.

    ``viewport_scroll_y`` is the scroll position at which the screenshot was
    taken.  For ContrastIssue the bbox coords are document-relative (axe-core
    adds ``window.scrollY`` to ``getBoundingClientRect().y``); subtracting
    ``viewport_scroll_y`` converts them back to viewport-relative so the crop
    lands on the correct pixel in the screenshot.

    Returns (base64_png_data, absolute_file_path). Returns ("", "") if PIL unavailable.
    """
    if not _HAS_PIL:
        return "", ""

    region = _get_issue_crop_region(issue)
    if isinstance(issue, ContrastIssue) and viewport_scroll_y != 0.0:
        region = BoundingBox(
            x=region.x,
            y=region.y - viewport_scroll_y,
            width=region.width,
            height=region.height,
        )
    padding = config.verification_padding

    img = _PILImage.open(io.BytesIO(viewport_png))
    img_w, img_h = img.size

    # Clip region to visible viewport before adding padding
    vis_x1 = max(0, int(region.x))
    vis_y1 = max(0, int(region.y))
    vis_x2 = min(img_w, int(region.x + region.width))
    vis_y2 = min(img_h, int(region.y + region.height))

    if vis_x2 <= vis_x1 or vis_y2 <= vis_y1:
        logger.warning(
            "Crop for %s: element bbox is outside viewport %dx%d; using clamped coords",
            issue_id,
            img_w,
            img_h,
        )
        vis_x1 = max(0, min(img_w - 1, int(region.x)))
        vis_y1 = max(0, min(img_h - 1, int(region.y)))
        vis_x2 = max(vis_x1 + 1, min(img_w, int(region.x + max(region.width, 1))))
        vis_y2 = max(vis_y1 + 1, min(img_h, int(region.y + max(region.height, 1))))

    left = max(0, vis_x1 - padding)
    top = max(0, vis_y1 - padding)
    right = min(img_w, vis_x2 + padding)
    bottom = min(img_h, vis_y2 + padding)

    if right - left < 50:
        right = min(img_w, left + 50)
    if bottom - top < 50:
        bottom = min(img_h, top + 50)

    cropped = img.crop((left, top, right, bottom))

    screenshots_dir = config.screenshots_dir or os.path.join(
        os.path.dirname(os.path.abspath(config.output)), "screenshots"
    )
    os.makedirs(screenshots_dir, exist_ok=True)
    file_path = os.path.join(screenshots_dir, f"{issue_id}_crop.png")
    cropped.save(file_path, "PNG")

    buf = io.BytesIO()
    cropped.save(buf, "PNG")
    b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    logger.debug(
        "Cropped screenshot for %s: %s (%dx%d)", issue_id, file_path, cropped.width, cropped.height
    )
    return b64_data, file_path


# ---------------------------------------------------------------------------
# AI verification
# ---------------------------------------------------------------------------


def _element_label_for_prompt(elem: ElementData) -> str:
    tag = elem.tag_name.lower()
    if tag == "img":
        return "[image]"
    if tag in ("svg", "canvas"):
        return f"[{tag} graphic]"
    if tag == "video":
        return "[video]"
    return f"[{tag}]"


def _clip_prompt_fields(issue: ClippingIssue) -> dict:
    is_self_clip = issue.clipped_element.selector == issue.clipping_ancestor.selector
    ox = f"{issue.overflow_x:.0f}"
    oy = f"{issue.overflow_y:.0f}"
    if is_self_clip:
        return {
            "clip_description": "An element's own content overflows its overflow:hidden boundary.",
            "clip_metric": f"Content overflow: {ox}px horizontal, {oy}px vertical",
            "clip_question": (
                "Confirm as a defect if any text, image, or meaningful content is visibly cut off "
                "at the element's boundary without a graceful affordance. Even if the surrounding "
                "page context implies the overflow is being demonstrated on purpose, the clipped "
                "content itself is the defect — text mid-word/mid-line truncation, a chopped image, "
                "or hidden controls all qualify. "
                "Dismiss ONLY when one of these graceful affordances is visibly present: "
                "(a) a text-overflow ellipsis ('…') at the cutoff, "
                "(b) a visible scrollbar, "
                "(c) a clear viewport-edge fade/reveal, "
                "(d) the overflowing content is purely decorative with no informational value "
                "(background pattern, gradient, wave/curve shape, diagonal divider at a section "
                "boundary), or "
                "(e) all informational content — cards, headings, body text, images — is fully "
                "rendered and readable within the visible area, and the only element that bleeds "
                "beyond the boundary is a decorative shape forming the section's curved or "
                "diagonal bottom edge. overflow:hidden on section/wrapper containers is a "
                "standard CSS technique for clipping wave/curve dividers; if the section's "
                "bottom edge is visibly non-rectangular (curved, diagonal) and every card and "
                "text block is complete, dismiss."
            ),
        }
    else:
        return {
            "clip_description": (
                "An element protrudes beyond its overflow:hidden parent container boundary."
            ),
            "clip_metric": f"Protrudes beyond container: {ox}px horizontal, {oy}px vertical",
            "clip_question": (
                "Confirm as a defect if the element visibly extends past its container's boundary "
                "in the screenshot — this represents a layout constraint violation regardless of "
                "whether the protrusion currently lands in whitespace, in neighboring content, or "
                "is itself being clipped at the container edge. Clipped text inside the protruding "
                "element (e.g., a partial word like 'Overf' instead of 'Overflowing') is itself a "
                "defect. "
                "Dismiss ONLY for clearly decorative peek-out patterns: a notification badge "
                "peeking from an avatar corner, a CSS drop-shadow, a tooltip/popover anchored to "
                "the element, or a deliberate overflow-peek decoration. Do NOT dismiss merely "
                "because the surrounding page labels the section as a demo, test, or example."
            ),
        }


def _build_verification_prompt(issue: Issue, design_intent: str = "") -> str:
    """Build an issue-type-specific verification prompt (same prompts as qa-agent).

    ``design_intent`` is the pre-rendered visual-spec section from
    ``load_design_intent`` — empty when no spec is available.
    """
    sections = _get_sections()
    base = sections["VERIFICATION_BASE"] + "\n\n"
    if design_intent:
        base += design_intent + "\n\n"

    if isinstance(issue, CollisionIssue):
        text_a = (
            issue.element_a.text_content[:80]
            if issue.element_a.text_content
            else _element_label_for_prompt(issue.element_a)
        )
        text_b = (
            issue.element_b.text_content[:80]
            if issue.element_b.text_content
            else _element_label_for_prompt(issue.element_b)
        )
        # Parent-overflow: element_b is direct parent of element_a
        if issue.element_a.parent_selector == issue.element_b.selector:
            return base + (sections["VERIFICATION_PARENT_OVERFLOW"] + "\n").format(
                tag_a=issue.element_a.tag_name,
                text_a=text_a,
                tag_b=issue.element_b.tag_name,
                overlap_ratio=f"{issue.overlap_ratio:.0%}",
                overlap_area=f"{issue.overlap_area:.0f}",
            )
        return base + (sections["VERIFICATION_COLLISION"] + "\n").format(
            tag_a=issue.element_a.tag_name,
            text_a=text_a,
            tag_b=issue.element_b.tag_name,
            text_b=text_b,
            overlap_ratio=f"{issue.overlap_ratio:.0%}",
            overlap_area=f"{issue.overlap_area:.0f}",
        )

    if isinstance(issue, ClippingIssue):
        text = (
            issue.clipped_element.text_content[:80]
            if issue.clipped_element.text_content
            else issue.clipped_element.tag_name
        )
        return base + (sections["VERIFICATION_CLIPPING"] + "\n").format(
            tag=issue.clipped_element.tag_name,
            text=text,
            **_clip_prompt_fields(issue),
        )

    if isinstance(issue, ContrastIssue):
        # Only incomplete-derived contrast issues reach verification (see
        # run_scan) — deterministic axe violations skip it.
        return base + (sections["VERIFICATION_CONTRAST"] + "\n").format(
            tag=issue.element.tag_name,
            text=issue.element.text_content[:80] or issue.element.tag_name,
            detail=issue.reasoning,
        )

    return base + f"ISSUE: {issue.reasoning}"


def _extract_json_from_text(text: str) -> dict:
    """Extract a JSON object from text that may contain surrounding prose."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    # Cannot parse a verdict — treat as unknown rather than confirmed so a
    # malformed or refused LLM response does not inflate the issue list.
    return {"verdict": "unknown", "reasoning": f"unparseable response: {text[:200]}"}


# Fallback chain for AI verification — mirrors the coding agent's model fallback order.
# All models here support vision (multimodal image + text input).
_VERIFICATION_FALLBACK_MODELS: tuple[str, ...] = (
    "google/gemini-2.5-pro",
    "openai/gpt-5",
)

# Error substrings that indicate the model is unavailable at the provider/router level.
# Mirrors agent.py _MODEL_UNAVAILABLE_MARKERS plus OpenRouter-specific patterns.
_MODEL_UNAVAILABLE_MARKERS: tuple[str, ...] = (
    "model not available",
    "model is unavailable",
    "not available for your account",
    "unsupported model",
    "no endpoints found",
    "model_not_found",
)


def _is_model_unavailable_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(m in msg for m in _MODEL_UNAVAILABLE_MARKERS)


def _is_retryable_error(exc: Exception) -> bool:
    """Return True for transient errors that should advance to the next fallback model.

    Covers model-unavailable responses, rate limits (429), server errors (5xx),
    network timeouts, and JSON parse failures from a partial/truncated response.
    Returning False means no further model should be tried and the issue is kept.
    """
    if _is_model_unavailable_error(exc):
        return True
    msg = str(exc).lower()
    # Rate limit or server-side transient failure
    if "http 429" in msg or "http 5" in msg:
        return True
    # urllib socket/connection timeouts
    if "timed out" in msg or "timeout" in msg or "connection" in msg:
        return True
    # Malformed/truncated JSON from the proxy
    if isinstance(exc, (json.JSONDecodeError, ValueError)) or "jsondecodeerror" in msg:
        return True
    return False


async def _post_proxy_verification(url: str, payload: dict, api_key: str) -> dict:
    """POST an OpenAI-compatible chat-completion request to the metadata-proxy."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    def _do() -> dict:
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            try:
                error_body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                error_body = ""
            raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc

    return await asyncio.to_thread(_do)


async def _verify_all_issues(
    issues: list,
    crop_b64_map: dict,
    config: ScanConfig,
    design_intent: str = "",
) -> list:
    """Verify every issue via the sandbox metadata-proxy using pre-computed per-issue crops.

    Returns EVERY issue with ``ai_verdict``/``ai_reasoning`` set — dismissed
    issues are kept (with ``ai_dismissal_basis``) so they can be reported as
    dropped findings; downstream consumers exclude them from actionable paths.

    Routes through localhost:8787 (same OpenAI-compatible pattern as other sandbox LLM scripts).
    On any error (missing API key, network failure) the issue stays confirmed.
    Cropping is handled upstream so this function only does AI calls.
    """
    if not crop_b64_map:
        return issues
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set — skipping AI verification")
        return issues

    proxy_url = llm_utils.proxy_url("qa_scanner.verify")

    semaphore = asyncio.Semaphore(config.verification_concurrency)

    async def _verify_one(issue: Issue) -> tuple[str, str, str]:
        crop_b64 = crop_b64_map.get(issue.issue_id)
        if not crop_b64:
            return VERDICT_CONFIRMED, "no crop available", BASIS_VISUAL

        prompt = _build_verification_prompt(issue, design_intent)
        payload = {
            "model": config.verification_model,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{crop_b64}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }

        async with semaphore:
            models_to_try = (config.verification_model, *_VERIFICATION_FALLBACK_MODELS)
            tried: set[str] = set()
            for model in models_to_try:
                if model in tried:
                    continue
                tried.add(model)
                payload["model"] = model
                try:
                    response = await _post_proxy_verification(proxy_url, payload, api_key)
                    choices = response.get("choices") or []
                    if not choices:
                        raise RuntimeError(f"proxy returned no choices: {response!r}")
                    text = (choices[0].get("message") or {}).get("content") or ""
                    result = _extract_json_from_text(text)
                    return (
                        result.get("verdict", VERDICT_CONFIRMED),
                        result.get("reasoning", ""),
                        result.get("basis", BASIS_VISUAL),
                    )
                except Exception as exc:
                    if _is_retryable_error(exc):
                        logger.warning(
                            "Model %s transient error for %s (%s), trying fallback",
                            model,
                            issue.issue_id,
                            exc,
                        )
                        continue
                    # Non-retryable failure (auth error, unexpected exception) —
                    # stop trying and keep the issue as confirmed.
                    logger.warning(
                        "Verification non-retryable error for %s: %s", issue.issue_id, exc
                    )
                    return VERDICT_CONFIRMED, f"verification error: {exc}", BASIS_VISUAL
            logger.warning("All verification models unavailable for %s", issue.issue_id)
            return VERDICT_CONFIRMED, "all verification models unavailable", BASIS_VISUAL

    tasks = [_verify_one(issue) for issue in issues]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    dismissed = 0
    for issue, result in zip(issues, raw_results):
        if isinstance(result, BaseException):
            logger.warning("Verification gather error for %s: %s", issue.issue_id, result)
            continue
        verdict, reasoning, basis = result
        issue.ai_verdict = verdict
        issue.ai_reasoning = reasoning
        if verdict == VERDICT_DISMISSED:
            dismissed += 1
            issue.ai_dismissal_basis = (
                BASIS_DESIGN_INTENT if basis == BASIS_DESIGN_INTENT else BASIS_VISUAL
            )
        logger.debug("Verified %s: %s (%s) — %s", issue.issue_id, verdict, basis, reasoning)

    logger.info(
        "AI verification: %d/%d issues confirmed (%d dismissed)",
        len(issues) - dismissed,
        len(issues),
        dismissed,
    )
    return issues
