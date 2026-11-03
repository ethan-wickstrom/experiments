"""Free disk during a long Harbor sweep without racing its image pulls (ledger G8).

Task images are 0.5 to 15 GB, a sweep pulls one per task, and Harbor's ``--delete`` removes only images it built,
not the prebuilt ones it pulled. ``docker image prune -af`` running beside a sweep removed layers a concurrent pull
was still extracting, and those trials failed before the agent started. This removes only images that no container
uses and that were already unused at the previous pass, one ``docker rmi`` at a time, so an image is never removed
in the seconds between its pull and the creation of its container. Images of tasks the job has yet to finish are
kept too: a later trial of the same task needs them, and idleness alone does not show that none will (F2). An image
pulled by digest has no tag to name its task, so the task is learned from the containers created from it, whose
compose project Harbor names after the trial (``<task>__<id>__env``), and remembered after they are gone. Containers
are read both as they stand and from Docker's event log since the previous pass, so one created and removed between
two passes is not missed.

    python -m bench.prune --while-pid <harbor pid> [--interval 60] [--log prune.log]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from collections.abc import Callable


def _docker(*args: str) -> str:
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=120, check=False)
    return result.stdout if result.returncode == 0 else ""


def scan() -> tuple[set[str], dict[str, str]]:
    """Every image's id, and each image some container (running or stopped) was created from, with the task of that
    container's trial ("" for a container that is not a Harbor trial's)."""
    images = set(_docker("image", "ls", "-q", "--no-trunc").split())
    containers = _docker("ps", "-aq", "--no-trunc").split()
    used: dict[str, str] = {}
    if containers:
        shown = '{{.Image}} {{index .Config.Labels "com.docker.compose.project"}}'
        for line in _docker("inspect", "--format", shown, *containers).splitlines():
            image, _, project = line.partition(" ")
            used[image] = project.split("__")[0] if "__" in project else used.get(image, "")
    return images, used


def created_between(since: float, until: float) -> dict[str, str]:
    """Each image a Harbor trial's container was created from in [since, until), with that trial's task."""
    shown = '{{.Actor.Attributes.image}}\t{{index .Actor.Attributes "com.docker.compose.project"}}'
    events = _docker(
        "events", "--since", f"{since:.3f}", "--until", f"{until:.3f}",
        "--filter", "type=container", "--filter", "event=create", "--format", shown,
    )  # fmt: skip
    tasks: dict[str, str] = {}
    for line in events.splitlines():
        reference, _, project = line.partition("\t")
        if "__" in project:
            image = _docker("image", "inspect", "--format", "{{.Id}}", reference).strip()
            if image:
                tasks[image] = project.split("__")[0]
    return tasks


def unused_images() -> set[str]:
    """Images no container (running or stopped) was created from."""
    images, used = scan()
    return images - set(used)


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def prune_while(
    pid: int | None, interval: float, log: str | None, pending: Callable[[], set[str]] | None = None
) -> None:
    """Remove unused images while ``pid`` runs, except the images of the tasks ``pending`` names."""
    previous: set[str] = set()
    tasks: dict[str, str] = {}  # image -> the task whose trial last used it, remembered after its containers go
    out = open(log, "a", encoding="utf-8") if log else sys.stderr  # noqa: SIM115 - lives as long as the loop
    since = time.time()
    while pid is None or alive(pid):
        now = time.time()
        tasks.update(created_between(since, now))
        since = now
        images, used = scan()
        tasks.update((image, task) for image, task in used.items() if task)
        keep = pending() if pending is not None else set()
        unused = {image for image in images - set(used) if tasks.get(image) not in keep}
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
