#!/usr/bin/env python3
"""Cloudinary URL canonicalizer + checker.

Self-contained (stdlib only). The image-url-transforms skill ships this script so that
agents — and the html-generation pipeline — can validate Cloudinary URLs
against probe-confirmed rules without re-implementing the grammar.

Two ways to use:

1. **CLI** (agent invokes via bash, or a wrapper invokes via subprocess):

   ```bash
   python3 check_urls.py docs/iter1/prototype/index.html
   python3 check_urls.py --url "https://static.kite.ai/image/upload/c_scale,g_face,w_400/app/abc/iter1/hero.png"
   ```

   Prints ``{"issues": [...]}`` JSON. Exits 1 on any fatal issue, else 0.

2. **Library** (import from another Python script):

   - :func:`canonicalize_urls_in_text` — rewrite malformed Cloudinary URL
     shapes (V2-4097 transform-after-path, V2-4180 filename-mid-path) into
     canonical form in place.
   - :func:`find_issues` — return issue dicts (``severity``/``code``/
     ``location``/``hint``) for URL grammar violations the canonicalizer
     can't auto-repair (``g_face`` with a disallowed crop, ``e_trim,X``
     comma-joined).

Probe evidence behind each encoded rule lives in the V2-4260 decision record.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_CLOUDINARY_URL_RE = re.compile(
    r"https?://(?:res\.cloudinary\.com/[^/\s\"'<>)`]+|static\.kite\.ai)"
    r"/(?:image|video|raw)/upload/[^\s\"'<>)`\\]+"
)
_FILENAME_RE = re.compile(
    r"\.(?:png|jpe?g|webp|svg|gif|avif|ico|bmp|mp4|webm|mov)(?:[?#]|$)", re.IGNORECASE
)
_VERSION_RE = re.compile(r"^v\d+$")

# Closed set of Cloudinary transform-segment prefixes our own
# ``transform_cloudinary_url`` (backend/app/utils/cloudinary_utils.py:179-214)
# emits. A closed set avoids false-positive classification on underscored
# folder names like ``some_subfolder`` that the agent might legitimately use
# as part of a public_id.
_TRANSFORM_PREFIXES = (
    "c_",
    "w_",
    "h_",
    "ar_",
    "g_",
    "q_",
    "f_",
    "dpr_",
    "e_",
    "fl_",
    "b_",
    "r_",
    "a_",
    "o_",
    "bo_",
    "l_",
    "u_",
)

# Probe R1b: Cloudinary's verbatim error message names exactly these crops:
# c_crop, c_fill, c_thumb, c_lfill, c_fill_pad, c_auto, c_auto_pad.
_FACE_GRAVITY_OK_CROPS = {"crop", "fill", "thumb", "lfill", "fill_pad", "auto", "auto_pad"}


def _looks_like_transform(segment: str) -> bool:
    if "," in segment:
        return True
    return segment.startswith(_TRANSFORM_PREFIXES)


def _path_after_upload(url: str) -> tuple[str, list[str]]:
    parts = url.split("/upload/", 1)
    if len(parts) != 2:
        return "", []
    return parts[0] + "/upload", parts[1].split("/")


def canonicalize_url(url: str) -> str:
    """Rebuild a Cloudinary URL with transforms first, version, then public_id.

    Repairs the V2-4097 (``…/upload/app/<id>/<transforms>/<file>.png``) and
    V2-4180 (``…/upload/<transforms>/<file>.png/app/<id>/iter1``) shapes.
    Probe outputs R6b/R6c confirm both shapes return HTTP 404 from Cloudinary.
    """
    base, segments = _path_after_upload(url)
    if not segments:
        return url

    transforms: list[str] = []
    folder_parts: list[str] = []
    filename_parts: list[str] = []
    version: str | None = None
    for seg in segments:
        if _VERSION_RE.match(seg):
            version = seg
        elif _FILENAME_RE.search(seg):
            filename_parts.append(seg)
        elif _looks_like_transform(seg):
            transforms.append(seg)
        else:
            folder_parts.append(seg)

    if len(filename_parts) > 1:
        folder_parts.extend(filename_parts[:-1])
        filename_parts = filename_parts[-1:]

    out = [base, *transforms]
    if version:
        out.append(version)
    out.extend(folder_parts + filename_parts)
    return "/".join(out)


def canonicalize_urls_in_text(text: str) -> str:
    """Rewrite every Cloudinary URL in ``text`` into canonical form."""
    if "static.kite.ai" not in text and "res.cloudinary.com" not in text:
        return text
    return _CLOUDINARY_URL_RE.sub(lambda m: canonicalize_url(m.group(0)), text)


def inject_fauto_qauto(url: str) -> str:
    """Inject ``f_auto,q_auto`` into a Cloudinary URL if missing.

    Behaviour (from V2-10978 spec):

    1. Skip if both ``f_auto`` and ``q_auto`` are already present in any
       transform segment.
    2. If there is no transform segment, insert ``f_auto,q_auto/``
       immediately after ``/upload/``.
    3. If the first transform segment is ``e_trim`` (its own ``/``-segment),
       inject into the *next* segment — merged comma-joined with any existing
       sizing.  If there is no next transform segment, create one.
    4. Otherwise merge the missing flag(s) into the first transform segment,
       preserving order: ``f_auto,q_auto,<existing>``.
    """
    base, segments = _path_after_upload(url)
    if not segments:
        return url

    # Classify segments into leading transforms and the rest (path/filename).
    i = 0
    leading_transforms: list[str] = []
    while (
        i < len(segments)
        and _looks_like_transform(segments[i])
        and not _FILENAME_RE.search(segments[i])
    ):
        leading_transforms.append(segments[i])
        i += 1

    # Skip version segment for rest classification.
    version_idx: int | None = None
    if i < len(segments) and _VERSION_RE.match(segments[i]):
        version_idx = i
        i += 1

    rest = segments[i:]

    # Collect all transform parts to check for existing f_auto / q_auto.
    all_parts: list[str] = []
    for seg in leading_transforms:
        all_parts.extend(seg.split(","))

    has_fauto = "f_auto" in all_parts
    has_qauto = "q_auto" in all_parts
    if has_fauto and has_qauto:
        return url  # already present — idempotent

    # Build the injection token(s).
    missing: list[str] = []
    if not has_fauto:
        missing.append("f_auto")
    if not has_qauto:
        missing.append("q_auto")
    inject = ",".join(missing)

    if not leading_transforms:
        # No transforms at all → insert a new segment.
        new_transforms = [inject]
    elif leading_transforms[0] == "e_trim":
        # e_trim in its own segment — inject into the *next* transform
        # segment (or create one).
        if len(leading_transforms) > 1:
            leading_transforms[1] = inject + "," + leading_transforms[1]
        else:
            leading_transforms.insert(1, inject)
        new_transforms = leading_transforms
    else:
        # Merge into the first transform segment.
        leading_transforms[0] = inject + "," + leading_transforms[0]
        new_transforms = leading_transforms

    out = [base, *new_transforms]
    if version_idx is not None:
        out.append(segments[version_idx])
    out.extend(rest)
    return "/".join(out)


def inject_fauto_qauto_in_text(text: str) -> str:
    """Inject ``f_auto,q_auto`` into every Cloudinary URL in ``text``."""
    if "static.kite.ai" not in text and "res.cloudinary.com" not in text:
        return text
    return _CLOUDINARY_URL_RE.sub(lambda m: inject_fauto_qauto(m.group(0)), text)


def _issues_for_url(url: str) -> list[dict]:
    issues: list[dict] = []
    _base, segments = _path_after_upload(url)
    if not segments:
        return issues

    i = 0
    leading_transforms: list[str] = []
    while (
        i < len(segments)
        and _looks_like_transform(segments[i])
        and not _FILENAME_RE.search(segments[i])
    ):
        leading_transforms.append(segments[i])
        i += 1
    if i < len(segments) and _VERSION_RE.match(segments[i]):
        i += 1
    rest = segments[i:]

    misplaced_transform = next(
        (
            seg
            for seg in rest
            if _looks_like_transform(seg)
            and not _FILENAME_RE.search(seg)
            and not _VERSION_RE.match(seg)
        ),
        None,
    )
    filename_indices = [j for j, seg in enumerate(rest) if _FILENAME_RE.search(seg)]
    filename_misplaced = bool(filename_indices) and filename_indices[-1] != len(rest) - 1

    if misplaced_transform:
        issues.append(
            {
                "severity": "fatal",
                "code": "cloudinary-transform-after-path",
                "location": url,
                "hint": (
                    f"Transform segment `{misplaced_transform}` appears after a path segment; "
                    "Cloudinary returns HTTP 404 for this shape. Move all transforms into the "
                    "first segment(s) after `/upload/`."
                ),
            }
        )
    elif filename_misplaced:
        misplaced = rest[filename_indices[0]]
        issues.append(
            {
                "severity": "fatal",
                "code": "cloudinary-transform-after-path",
                "location": url,
                "hint": (
                    f"Filename `{misplaced}` appears before the folder path; Cloudinary returns "
                    "HTTP 404. The filename must be the last segment of the public_id, after "
                    "any folder segments (e.g. `…/upload/<transforms>/app/<id>/iter1/<file>.png`)."
                ),
            }
        )

    for seg in leading_transforms:
        parts = seg.split(",")
        if any(p in ("g_face", "g_faces") for p in parts):
            crops = [p[2:] for p in parts if p.startswith("c_")]
            bad = [c for c in crops if c not in _FACE_GRAVITY_OK_CROPS]
            if bad:
                issues.append(
                    {
                        "severity": "fatal",
                        "code": "cloudinary-face-gravity-crop",
                        "location": url,
                        "hint": (
                            f"`g_face` with `c_{bad[0]}` returns HTTP 400 from Cloudinary. "
                            "Use one of: c_crop, c_fill, c_thumb, c_lfill, c_fill_pad, c_auto, c_auto_pad."
                        ),
                    }
                )
        if "e_trim" in parts and len(parts) > 1:
            issues.append(
                {
                    "severity": "recoverable",
                    "code": "cloudinary-etrim-comma-joined",
                    "location": url,
                    "hint": (
                        f"`{seg}` comma-joins `e_trim` with other transforms; sizing then "
                        "computes against pre-trim bounds and the image renders as a tiny glyph. "
                        "Put `e_trim` in its own `/`-segment before the sizing chain "
                        "(e.g. `…/upload/e_trim/h_80/…`)."
                    ),
                }
            )

    # Check for missing f_auto / q_auto.
    all_transform_parts: list[str] = []
    for seg in leading_transforms:
        all_transform_parts.extend(seg.split(","))
    has_fauto = "f_auto" in all_transform_parts
    has_qauto = "q_auto" in all_transform_parts
    if not (has_fauto and has_qauto):
        missing = [x for x in ("f_auto", "q_auto") if x not in all_transform_parts]
        issues.append(
            {
                "severity": "recoverable",
                "code": "cloudinary-missing-transforms",
                "location": url,
                "hint": (
                    f"Missing `{','.join(missing)}` — Cloudinary will serve the original "
                    "format/quality, wasting bandwidth. Add `f_auto,q_auto` as a transform "
                    "segment after `/upload/` (or after `e_trim/` for logos)."
                ),
            }
        )
    return issues


def find_issues(text: str) -> list[dict]:
    """Scan ``text`` for Cloudinary URLs; return all issue dicts (deduped by URL)."""
    issues: list[dict] = []
    seen: set[str] = set()
    for match in _CLOUDINARY_URL_RE.finditer(text):
        url = match.group(0)
        if url in seen:
            continue
        seen.add(url)
        issues.extend(_issues_for_url(url))
    return issues


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Cloudinary URLs in an HTML file or a single URL.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("file", nargs="?", help="Path to an HTML file to scan")
    group.add_argument("--url", help="Single Cloudinary URL to validate")
    args = parser.parse_args()

    if args.url:
        issues = _issues_for_url(args.url)
    else:
        issues = find_issues(Path(args.file).read_text(encoding="utf-8"))

    print(json.dumps({"issues": issues}, indent=2))
    return 1 if any(i["severity"] == "fatal" for i in issues) else 0


if __name__ == "__main__":
    sys.exit(_main())
