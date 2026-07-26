"""Scanner configuration — hardcoded thresholds + CLI-tunable fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScanConfig:
    url: str
    viewport_width: int = 1920
    code_path: Optional[str] = None
    output: str = "/tmp/qa_scan_report.md"
    # Directory where viewport screenshots are saved during the scan.
    # Defaults to a ``screenshots/`` subdirectory next to the output file.
    # Set to None to skip screenshot capture entirely.
    screenshots_dir: Optional[str] = None

    # Hardcoded scan constants
    VIEWPORT_HEIGHT: int = 1080
    SCROLL_OVERLAP: float = 0.10
    STABILIZATION_TIMEOUT: int = 10_000
    STABILITY_DELAY: float = 0.3
    STABILITY_THRESHOLD: float = 2.0
    MIN_OVERLAP_RATIO: float = 0.05
    MIN_OVERFLOW_PX: float = 5.0
    IGNORE_STICKY: bool = True
    CONFIDENCE_HIGH: float = 0.75
    CONFIDENCE_MEDIUM: float = 0.50
    CODE_MAX_KB: int = 500
    MAX_MATCHES_PER_ISSUE: int = 5

    # AI verification
    enable_verification: bool = True
    # Path to the iteration's visual_spec.md. When set and readable, its text is
    # injected into every verification prompt as design intent so intentional
    # collisions/clipping/low-contrast treatments documented in the spec are
    # dismissed, and deterministic contrast violations also go through AI
    # verification (they may be intentional per the spec).
    visual_spec_path: Optional[str] = None
    verification_model: str = "anthropic/claude-sonnet-4-6"  # OpenRouter model ID
    verification_padding: int = 150  # px padding around issue region for per-issue crops
    verification_concurrency: int = 10  # max parallel Claude calls
