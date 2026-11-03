"""Free disk during a long Harbor sweep without racing its image pulls (ledger G8).

Task images are 0.5 to 15 GB, a sweep pulls one per task, and Harbor's ``--delete`` removes only images it built,
not the prebuilt ones it pulled. ``docker image prune -af`` running beside a sweep removed layers a concurrent pull
was still extracting, and those trials failed before the agent started. This removes only images that no container
uses and that were already unused at the previous pass, one ``docker rmi`` at a time, so an image is never removed
in the seconds between its pull and the creation of its container.

    python -m bench.prune --while-pid <harbor pid> [--interval 60] [--log prune.log]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time


def _docker(*args: str) -> str:
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=120, check=False)
    return result.stdout if result.returncode == 0 else ""


def unused_images() -> set[str]:
    """Images no container (running or stopped) was created from."""
    images = set(_docker("image", "ls", "-q", "--no-trunc").split())
    containers = _docker("ps", "-aq", "--no-trunc").split()
    used = set(_docker("inspect", "--format", "{{.Image}}", *containers).split()) if containers else set()
    return images - used


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def prune_while(pid: int | None, interval: float, log: str | None) -> None:
    previous: set[str] = set()
    out = open(log, "a", encoding="utf-8") if log else sys.stderr  # noqa: SIM115 - lives as long as the loop
    while pid is None or alive(pid):
        unused = unused_images()
        for image in sorted(unused & previous):  # unused at two passes in a row
            removed = subprocess.run(["docker", "rmi", image], capture_output=True, text=True, check=False)
            status = "removed" if removed.returncode == 0 else f"kept ({removed.stderr.strip()[:120]})"
            print(f"{time.strftime('%H:%M:%S')} {image[:19]} {status}", file=out, flush=True)
        previous = unused
        time.sleep(interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--while-pid", type=int, help="stop when this process exits (default: run until killed)")
    parser.add_argument("--interval", type=float, default=60.0, help="seconds between passes")
    parser.add_argument("--log", help="append what was removed to this file (default: stderr)")
    args = parser.parse_args(argv)
    prune_while(args.while_pid, args.interval, args.log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
