"""Shared site-level image-world prepass for sandbox-side generation.

Runs inside the E2B sandbox after the visual spec has been resolved on disk,
so the cohesion brief can reference the actual Gallery-selected direction.
Imported by ``html-generation/scripts/generate_html.py``.
"""

from __future__ import annotations

import json
import logging
import pathlib
import sys
from dataclasses import dataclass

_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent.parent / "lib"))
import llm_utils  # type: ignore[import-not-found]  # noqa: E402

logger = logging.getLogger(__name__)

PROMPTS_DIR = _SCRIPTS_DIR.parent / "assets" / "prompts"

PRIMARY_MODEL = "google/gemini-3-flash-preview"
FALLBACK_MODEL = "anthropic/claude-haiku-4-5"
TIMEOUT_SECS = 90
TEMPERATURE = 0.4

DEFAULT_IMAGE_WORLD_BRIEF = """## Shared Image World

Treat all generated imagery for this site as one family. Reuse one shared palette logic, lighting logic, material language, crop discipline, and overall polish level across the full set. Let subject matter vary only inside that shared treatment world; do not let each image invent a new visual universe.

## Variation Policy

Default to cohesive site-wide treatment. Portfolio, case-study, and project imagery may vary in subject matter or client context, but should still share treatment discipline through crop behavior, tonal range, background handling, and finish quality unless the user explicitly asks for stronger contrast.

## Avoid

Avoid generic SaaS abstractions, random accent colors, conflicting material worlds, and abrupt shifts in mood or camera language between related images."""


@dataclass(frozen=True)
class ImageWorldArtifacts:
    """Final brief plus the prompts used to produce it (for debug persistence)."""

    brief: str
    system_prompt: str
    user_prompt: str


def _format_build_requirements(build_requirements: list[str]) -> str:
    if not build_requirements:
        return "(none)"
    return "\n".join(f"- {item}" for item in build_requirements)


def _call_model(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    proxy_url: str,
) -> str:
    return llm_utils.call_llm(
        url=proxy_url,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        api_key=api_key,
        temperature=TEMPERATURE,
        timeout=TIMEOUT_SECS,
    )


def generate_image_world(
    *,
    operation: str,
    user_requirements: str,
    build_requirements: list[str],
    visual_specification: str | None,
    user_uploaded_assets: str,
    logo_info: dict[str, str | None],
    context_html: str,
    current_html: str | None,
    api_key: str,
    proxy_url: str,
) -> ImageWorldArtifacts:
    """Generate a compact image-world brief, failing open to a default memo.

    Tries Gemini 3 Flash, falls back to Claude Haiku 4.5, finally returns
    ``DEFAULT_IMAGE_WORLD_BRIEF`` so downstream callers always get a usable
    brief.
    """
    system_prompt = llm_utils.load_prompt("image_world_system.md", prompts_dir=PROMPTS_DIR)
    user_prompt = llm_utils.load_prompt(
        "image_world_user.md",
        {
            "operation": operation,
            "user_requirements": user_requirements,
            "build_requirements": _format_build_requirements(build_requirements),
            "visual_specification": visual_specification or "(none)",
            "user_uploaded_assets": user_uploaded_assets or "(none)",
            "logo_info": json.dumps(logo_info or {}, indent=2),
            "context_html": context_html or "(none)",
            "current_html": current_html or "(none)",
        },
        prompts_dir=PROMPTS_DIR,
    )

    raw: str | None = None
    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            raw = _call_model(
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                api_key=api_key,
                proxy_url=proxy_url,
            )
            break
        except Exception:
            logger.exception("image_world: %s failed", model)

    if raw:
        candidate = llm_utils.strip_markdown_fences(raw).strip()
        if candidate:
            return ImageWorldArtifacts(
                brief=candidate, system_prompt=system_prompt, user_prompt=user_prompt
            )

    return ImageWorldArtifacts(
        brief=DEFAULT_IMAGE_WORLD_BRIEF,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
