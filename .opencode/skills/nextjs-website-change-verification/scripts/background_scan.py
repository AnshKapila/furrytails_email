#!/usr/bin/env python3
"""Detached reporting-only QA scan runner.

Spawned by ``validate_files.py`` after its blocking checks pass, so the coding
agent never waits on the scan and never sees its findings. Owns the whole
detach lifecycle: the scan cap (``KITE_QA_MAX_CALLS``), the in-flight lockfile
dedup, running the scan, and recording the qa_scan Loki event + cross-round
issue state. Every outcome here — findings, dev server down, infra failure —
is telemetry; nothing reaches the coding agent.

Imports ``validate_files`` as a sibling module (one-directional: that script
never imports this one), which works both when spawned as a script (the
scripts dir is sys.path[0]) and in tests that put the scripts dir on sys.path.

Usage: python3 background_scan.py <iter_name>   (or ITERATION_ID env)
"""

from __future__ import annotations

import os
import pathlib
import sys

import validate_files as vf


def _qa_scan_cap() -> int:
    try:
        return int(os.environ.get("KITE_QA_MAX_CALLS", "3"))
    except ValueError:
        return 3


def _acquire_lock(lock: pathlib.Path) -> bool:
    """Atomically claim the scan lock; return False if another live scan holds it.

    ``O_CREAT | O_EXCL`` makes creation the mutual-exclusion primitive, so two
    validations racing here cannot both pass — exactly one wins the create. A
    pre-existing lock is honored only while its recorded pid is alive; a stale
    lock (dead pid / unreadable) is reclaimed by unlinking and retrying once.
    """
    for _ in range(2):
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            try:
                os.kill(int(lock.read_text().strip()), 0)
                return False  # a live scan already holds the lock
            except (OSError, ValueError):
                # Stale lock — remove and retry the atomic create once.
                try:
                    lock.unlink()
                except OSError:
                    pass
                continue
        else:
            with os.fdopen(fd, "w") as fh:
                fh.write(str(os.getpid()))
            return True
    return False


def run(iter_name: str, iter_dir: pathlib.Path) -> int:
    """Gate (live-pid lock, then cap), run the scan, record telemetry, unlock.

    The lock is taken FIRST and atomically, so the cap read/increment below
    happens under mutual exclusion — two concurrent validations can no longer
    both pass the cap and launch overlapping Playwright scans.
    """
    lock = iter_dir / ".qa_scan_running"
    iter_dir.mkdir(parents=True, exist_ok=True)
    if not _acquire_lock(lock):
        print(f"QA scan already running for {iter_name} — nothing to do", file=sys.stderr)
        return 0

    try:
        counter_path = iter_dir / ".qa_validate_count"
        try:
            call_count = int(counter_path.read_text()) if counter_path.exists() else 0
        except (OSError, ValueError):
            call_count = 0
        if call_count >= _qa_scan_cap():
            print(
                f"QA scan cap reached for {iter_name} ({call_count}) — nothing to do",
                file=sys.stderr,
            )
            return 0

        attempt = call_count + 1
        counter_path.write_text(str(attempt))
        try:
            qa_issues, dropped_count = vf._run_qa_scan(iter_name, iter_dir)
        except Exception as exc:  # noqa: BLE001 - any failure is an error event
            vf._log_qa_event(vf._build_qa_event("error", [], attempt, 0, iter_name))
            print(f"background QA scan failed: {exc}", file=sys.stderr)
            return 1
        vf._record_qa_verdict(
            "failed" if qa_issues else "success",
            qa_issues,
            iter_name,
            iter_dir,
            attempt,
            dropped_count,
        )
        print(
            f"background QA scan complete: {len(qa_issues)} finding(s) recorded, "
            f"{dropped_count} dropped by the verifier for {iter_name} (attempt {attempt})",
            file=sys.stderr,
        )
        return 0
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def main() -> int:
    iter_name = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ITERATION_ID")
    if not iter_name:
        print("no iter_name: pass as arg or set ITERATION_ID env", file=sys.stderr)
        return 2
    efs = os.environ.get("EFS_APP_PATH")
    if not efs:
        print("EFS_APP_PATH env var not set", file=sys.stderr)
        return 2
    return run(iter_name, pathlib.Path(efs) / "iterations" / iter_name)


if __name__ == "__main__":
    sys.exit(main())
