"""System monitoring — CPU, RAM, disk, battery, processes, network."""

import platform
import os

try:
    import psutil
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


def _fmt_bytes(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def system_info() -> str:
    """Full system overview: OS, CPU, RAM, disk, battery."""
    if not _AVAILABLE:
        return "[ERROR] Install psutil: pip install psutil"

    lines = ["🖥️  SYSTEM INFO", "─" * 40]

    # OS
    lines.append(f"  OS       : {platform.system()} {platform.release()} ({platform.machine()})")
    lines.append(f"  Python   : {platform.python_version()}")
    lines.append(f"  Hostname : {platform.node()}")

    # CPU
    cpu_pct = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count()
    freq = psutil.cpu_freq()
    freq_str = f" @ {freq.current:.0f} MHz" if freq else ""
    lines.append(f"  CPU      : {cpu_pct}% used — {cpu_count} cores{freq_str}")

    # RAM
    mem = psutil.virtual_memory()
    lines.append(f"  RAM      : {_fmt_bytes(mem.used)} / {_fmt_bytes(mem.total)} ({mem.percent}%)")

    # Disk
    disk = psutil.disk_usage(os.sep)
    lines.append(f"  Disk     : {_fmt_bytes(disk.used)} / {_fmt_bytes(disk.total)} ({disk.percent}%)")

    # Battery
    bat = psutil.sensors_battery()
    if bat:
        plug = "⚡ plugged in" if bat.power_plugged else "🔋 on battery"
        lines.append(f"  Battery  : {bat.percent:.0f}% — {plug}")

    # Network
    net = psutil.net_io_counters()
    lines.append(f"  Network  : ↑ {_fmt_bytes(net.bytes_sent)} sent / ↓ {_fmt_bytes(net.bytes_recv)} recv")

    # Uptime
    boot = psutil.boot_time()
    import datetime
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot)
    h, m = divmod(int(uptime.total_seconds()) // 60, 60)
    lines.append(f"  Uptime   : {h}h {m}m")

    return "\n".join(lines)


def list_processes(args: dict = None) -> str:
    """List top processes by memory. args: {count?: int}"""
    if not _AVAILABLE:
        return "[ERROR] Install psutil: pip install psutil"

    count = int((args or {}).get("count", 10))
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x.get("memory_percent", 0), reverse=True)
    lines = [f"📊 Top {count} processes by memory:", "─" * 50]
    for p in procs[:count]:
        lines.append(
            f"  PID {p['pid']:>6} | {p['name'][:25]:<25} | "
            f"RAM {p.get('memory_percent', 0):.1f}% | CPU {p.get('cpu_percent', 0):.1f}%"
        )
    return "\n".join(lines)
