# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Hardware and environment logging, and a background memory sampler.

Caveat recorded for the owner: on Apple silicon, Metal buffers used by the
inference runner may not be fully counted in process RSS. The sampler
therefore also records system-wide used memory and swap, and the runner
records the runtime's own reported model size (``/api/ps``) when available.
"""

from __future__ import annotations

import platform
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Callable

import psutil

PACKAGES = ("token-lab", "numpy", "psutil", "jsonschema")


def _run(cmd: list[str], cwd: str | Path | None = None) -> str | None:
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def git_state(repo: str | Path) -> dict:
    rev = _run(["git", "rev-parse", "HEAD"], repo)
    status = _run(["git", "status", "--porcelain", "--untracked-files=no"], repo)  # tracked files only
    return {"revision": rev, "dirty": None if status is None else bool(status)}


def package_versions() -> dict:
    out = {"python": sys.version.split()[0]}
    for p in PACKAGES:
        try:
            out[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            out[p] = None
    return out


def power_state() -> dict:
    raw = _run(["pmset", "-g", "batt"])
    if raw is None:
        return {"source": None, "raw": None}
    first = raw.splitlines()[0] if raw else ""
    if "AC Power" in first:
        src = "ac"
    elif "Battery Power" in first:
        src = "battery"
    else:
        src = "unknown"
    return {"source": src, "raw": raw}


def host_info() -> dict:
    vm = psutil.virtual_memory()
    return {
        "os": platform.platform(),
        "os_release": platform.mac_ver()[0] or platform.release(),
        "machine": platform.machine(),
        "cpu": _run(["sysctl", "-n", "machdep.cpu.brand_string"]) or platform.processor(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "memory_total_bytes": int(vm.total),
        "load_avg_1_5_15": list(psutil.getloadavg()),
        "power": power_state(),
    }


def swap_used_bytes() -> int:
    """System swap in use (bytes), as psutil reports it (``vm.swapusage`` on macOS)."""
    return int(psutil.swap_memory().used)


def harness_peak_rss_bytes() -> int:
    """Peak RSS of this Python process (ru_maxrss: bytes on macOS, KiB on Linux)."""
    import resource

    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(r if sys.platform == "darwin" else r * 1024)


def name_matcher(substr: str) -> Callable[[psutil.Process], bool]:
    def match(p: psutil.Process) -> bool:
        try:
            return substr in (p.name() or "").lower()
        except (psutil.Error, OSError):
            return False

    return match


@dataclass
class MemorySampler:
    """Samples summed RSS of matching processes plus system memory at ``hz``.

    Use as a context manager. ``peak_rss_bytes`` is None if no matching
    process was ever seen (reported, never imputed).
    """

    match: Callable[[psutil.Process], bool]
    hz: float = 10.0
    peak_rss_bytes: int | None = None
    peak_system_used_bytes: int = 0
    swap_start_bytes: int = 0
    swap_end_bytes: int = 0
    samples: int = 0
    rediscover_s: float = 1.0
    # Injectable for tests; the default reads system swap. ``peak_swap_growth_bytes``
    # is the largest (swap used - swap used at entry) seen by any sample.
    swap_reader: Callable[[], int] = swap_used_bytes
    peak_swap_growth_bytes: int = 0
    _pids: list = field(default_factory=list)
    _last_discovery: float = float("-inf")
    _stop: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = None

    def __post_init__(self) -> None:
        if self.hz <= 0:
            raise ValueError("hz must be positive")

    def _discover(self) -> None:
        # A full process scan is expensive (several ms on a busy machine), so it
        # runs at most once per ``rediscover_s``; between scans only cached PIDs
        # are read. A runner process spawned after a scan is picked up at the next.
        self._pids = [p for p in psutil.process_iter() if self.match(p)]
        self._last_discovery = time.monotonic()

    def _sample(self) -> None:
        if time.monotonic() - self._last_discovery >= self.rediscover_s:
            self._discover()
        total = 0
        seen = False
        for p in self._pids:
            try:
                total += p.memory_info().rss
                seen = True
            except (psutil.Error, OSError):
                continue
        if seen:
            self.peak_rss_bytes = max(self.peak_rss_bytes or 0, total)
        self.peak_system_used_bytes = max(self.peak_system_used_bytes, int(psutil.virtual_memory().used))
        self.peak_swap_growth_bytes = max(self.peak_swap_growth_bytes, self.swap_growth_bytes())
        self.samples += 1

    def swap_growth_bytes(self) -> int:
        """Swap used now minus swap used when the sampler was entered."""
        return int(self.swap_reader()) - self.swap_start_bytes

    def _loop(self) -> None:
        period = 1.0 / self.hz
        while not self._stop.is_set():
            self._sample()
            self._stop.wait(period)

    def __enter__(self) -> "MemorySampler":
        self.swap_start_bytes = int(self.swap_reader())
        self._sample()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._sample()
        self.swap_end_bytes = int(self.swap_reader())

    def summary(self) -> dict:
        return {
            "peak_rss_mib": None if self.peak_rss_bytes is None else self.peak_rss_bytes / 2**20,
            "peak_system_used_mib": self.peak_system_used_bytes / 2**20,
            "swap_delta_mib": (self.swap_end_bytes - self.swap_start_bytes) / 2**20,
            "peak_swap_growth_mib": self.peak_swap_growth_bytes / 2**20,
            "samples": self.samples,
        }


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
