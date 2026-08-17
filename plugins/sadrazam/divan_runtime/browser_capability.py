"""Probe the repository's pinned Playwright browser capability.

Kept out of doctor_checks so the health checks stay readable, and probed
out of process because the runtime core is stdlib-only by architecture
decision. Nothing is installed here: this reports whether the browser
capability the CI lane already uses is available on this machine too.
"""
from __future__ import annotations

from pathlib import Path

from .doctor import CapabilityReport, CapabilityState


def browser_capability() -> CapabilityReport:
    """Probe the repository's pinned Playwright without importing it.

    The runtime core is stdlib-only by architecture decision, so the probe
    runs out of process. Nothing new is installed: this reports whether the
    browser capability the CI lane already uses is available here too.
    """
    import json
    import subprocess
    import sys

    affects = "Web projelerinde gerçek tarayıcı kabul kanıtı."
    probe = (
        "import json;"
        "from playwright.sync_api import sync_playwright;"
        "d=sync_playwright().start();"
        "print(json.dumps({'path': d.chromium.executable_path}));"
        "d.stop()"
    )
    try:
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return CapabilityReport(
            capability_id="browser-qa",
            display_name="Tarayıcı testi",
            state=CapabilityState.DEGRADED,
            affects=affects,
            code="BROWSER_PROBE_FAILED",
            detail=type(error).__name__,
        )
    if completed.returncode != 0:
        return CapabilityReport(
            capability_id="browser-qa",
            display_name="Tarayıcı testi",
            state=CapabilityState.OFFLINE,
            affects=affects,
            code="BROWSER_NOT_INSTALLED",
            detail="playwright bu ortamda kullanılamıyor",
        )
    try:
        executable = json.loads(completed.stdout.strip().splitlines()[-1])["path"]
    except (ValueError, IndexError, KeyError):
        return CapabilityReport(
            capability_id="browser-qa",
            display_name="Tarayıcı testi",
            state=CapabilityState.DEGRADED,
            affects=affects,
            code="BROWSER_PROBE_UNREADABLE",
            detail="tarayıcı yoklaması okunamadı",
        )
    if not executable or not Path(executable).exists():
        return CapabilityReport(
            capability_id="browser-qa",
            display_name="Tarayıcı testi",
            state=CapabilityState.DEGRADED,
            affects=affects,
            code="BROWSER_BINARY_MISSING",
            detail="playwright var; chromium indirilmemiş",
        )
    return CapabilityReport(
        capability_id="browser-qa",
        display_name="Tarayıcı testi",
        state=CapabilityState.CERTIFIED,
        affects=affects,
        evidence=executable,
    )
