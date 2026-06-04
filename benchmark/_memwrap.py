"""Run a child executable and record its peak RSS and wall time.

Invoked as ``python -m benchmark._memwrap <mem_file> <exe> [args...]``. The child
inherits this process's stdin/stdout/stderr, so the harness still pipes the
problem in and captures the reconstruction out untouched. After the child exits
we read ``RUSAGE_CHILDREN`` — which, because this wrapper's only child is the
algorithm binary, reflects that binary alone — and write two lines to
``<mem_file>``: peak memory in MB, then child wall time in seconds.

POSIX only (uses ``resource``). On platforms without it the child still runs and
the memory file is simply left without a memory line.
"""

from __future__ import annotations

import subprocess
import sys
import time

try:
    import resource
except ImportError:  # pragma: no cover - non-POSIX fallback
    resource = None  # type: ignore[assignment]


def _windows_peak_mb(process: subprocess.Popen) -> float | None:
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return None

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(ProcessMemoryCounters)
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(
        wintypes.HANDLE(process._handle),  # type: ignore[attr-defined]
        ctypes.byref(counters),
        counters.cb,
    )
    if not ok:
        return None
    return counters.PeakWorkingSetSize / (1024 * 1024)


def _peak_mb(usage: "resource.struct_rusage") -> float:
    # ru_maxrss is bytes on macOS, kilobytes on Linux.
    maxrss = usage.ru_maxrss
    if sys.platform == "darwin":
        return maxrss / (1024 * 1024)
    return maxrss / 1024


def main() -> int:
    mem_path = sys.argv[1]
    argv = sys.argv[2:]

    start = time.perf_counter()
    process = subprocess.Popen(argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    peak_mb = None
    while process.poll() is None:
        current_peak = _windows_peak_mb(process)
        if current_peak is not None:
            peak_mb = max(peak_mb or 0.0, current_peak)
        time.sleep(0.01)
    current_peak = _windows_peak_mb(process)
    if current_peak is not None:
        peak_mb = max(peak_mb or 0.0, current_peak)
    elapsed = time.perf_counter() - start

    lines = []
    if peak_mb is not None:
        lines.append(repr(peak_mb))
    elif resource is not None:
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        lines.append(repr(_peak_mb(usage)))
    else:
        lines.append("")
    lines.append(repr(elapsed))

    try:
        with open(mem_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    except OSError:
        pass

    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
