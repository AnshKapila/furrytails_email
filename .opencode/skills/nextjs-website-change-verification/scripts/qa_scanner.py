#!/usr/bin/env python3
"""
qa_scanner.py — CLI entry point for the Kite iteration QA scanner.

Detects collision, clipping, and contrast issues via Playwright DOM analysis.
Optional AI verification routes through the sandbox metadata-proxy (localhost:8787)
using the same OpenAI-compatible pattern as other sandbox LLM scripts.

Pipeline lives in ``pipeline.py``; this file only parses CLI args, runs the
pipeline, and writes the JSON report plus the interactive HTML report.

Usage:
    python3 qa_scanner.py <URL> [--viewports 1920]
                          [--code-path /path/to/src] [--output /tmp/qa_scan.json]
                          [--no-verify] [--verbose]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

from config import ScanConfig  # noqa: E402
from models import TYPE_RUNTIME, is_actionable  # noqa: E402
from pipeline import run_scan  # noqa: E402
from report import write_html_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic QA scanner: collision, clipping, contrast detection via Playwright"
    )
    parser.add_argument("url", help="URL to scan")
    parser.add_argument(
        "--viewports",
        type=int,
        default=1920,
        metavar="WIDTH",
        help="Viewport width (default: 1920)",
    )
    parser.add_argument(
        "--code-path", default=None, help="Path to source code directory for issue-to-code matching"
    )
    parser.add_argument(
        "--output",
        default="/tmp/qa_scan_report.json",
        help="Output report path (default: /tmp/qa_scan_report.json)",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Disable AI verification (skip Claude vision calls)",
    )
    parser.add_argument(
        "--visual-spec",
        default=None,
        help="Path to the iteration's visual_spec.md — injected into verification "
        "prompts as design intent so intentional overlaps/clipping/low-contrast "
        "treatments documented in the spec are dismissed",
    )
    parser.add_argument(
        "--verification-model",
        default="anthropic/claude-sonnet-4-6",
        help="Model for AI verification via metadata-proxy (default: anthropic/claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--verification-padding",
        type=int,
        default=150,
        help="Padding in px around issue region for per-issue crop (default: 150)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger("qa_scanner").setLevel(logging.DEBUG)

    # Screenshots go into a ``screenshots/`` subdirectory next to the report
    out_base = os.path.splitext(os.path.abspath(args.output))[0]
    screenshots_dir = os.path.join(os.path.dirname(out_base), "screenshots")

    config = ScanConfig(
        url=args.url,
        viewport_width=args.viewports,
        code_path=args.code_path,
        output=args.output,
        screenshots_dir=screenshots_dir,
        enable_verification=not args.no_verify,
        verification_model=args.verification_model,
        verification_padding=args.verification_padding,
        visual_spec_path=args.visual_spec,
    )

    out_dir = os.path.dirname(os.path.abspath(config.output))
    os.makedirs(out_dir, exist_ok=True)

    json_path = config.output
    if not json_path.endswith(".json"):
        json_path = os.path.splitext(json_path)[0] + ".json"

    try:
        report, issues = asyncio.run(run_scan(config))
    except Exception as exc:
        # Infrastructure failure (Playwright missing, browser crash, OOM, etc.)
        # Write a minimal error report so validate_files.py can read it, then
        # exit 2 so the caller recognises this as an infra failure (not a
        # "found critical issues" result).
        error_report: dict = {"error": str(exc), "issues": [], "elapsed_seconds": 0}
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(error_report, f)
        except Exception:
            pass
        print(f"QA scan infrastructure failure: {exc}", file=sys.stderr)
        sys.exit(2)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Interactive HTML report for humans — sidebar issue list + clickable
    # highlights over the full-page screenshot. Best-effort: the scan verdict
    # never depends on it.
    html_path = os.path.splitext(json_path)[0] + ".html"
    try:
        write_html_report(report, html_path)
    except Exception as exc:
        print(f"HTML report generation failed: {exc}", file=sys.stderr)

    actionable = [
        i for i in issues if is_actionable(i.severity, dropped=i.ai_verdict == "dismissed")
    ]
    runtime_issues = [i for i in report.get("issues", []) if i.get("type") == TYPE_RUNTIME]
    n = len(actionable) + len(runtime_issues)
    print(
        f"QA scan complete: {n} critical/high-severity issue(s) found "
        f"({len(runtime_issues)} runtime) in {report['elapsed_seconds']}s → {json_path}",
        file=sys.stderr,
    )
    # Exit 1 when actionable issues were found so the caller can distinguish
    # "clean scan" (0) from "scan found problems" (1) vs "infra failure" (2).
    sys.exit(1 if (actionable or runtime_issues) else 0)


if __name__ == "__main__":
    main()
