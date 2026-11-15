"""Compare two dumps (`rachis dump` and `oracle_dump.py`): the same glyphs, the same structure, the same numbers.

  python3 tools/oracle_diff.py RUST_DUMP PYTHON_DUMP [--tolerance 1e-4]
"""

from __future__ import annotations

import sys


def read(path: str) -> dict[tuple[str, str], list[list[str]]]:
    glyphs: dict[tuple[str, str], list[list[str]]] = {}
    current: list[list[str]] | None = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if parts[0] == "G":
                current = [parts]
                glyphs[(parts[1], parts[2])] = current
            elif current is not None:
                current.append(parts)
    return glyphs


def main() -> int:
    a, b = read(sys.argv[1]), read(sys.argv[2])
    tolerance = float(sys.argv[sys.argv.index("--tolerance") + 1]) if "--tolerance" in sys.argv else 1e-4
    bad: dict[str, str] = {}
    worst = 0.0
    for key in sorted(set(a) | set(b)):
        name = key[1]
        if key not in a or key not in b:
            bad.setdefault(name, f"only in the {'second' if key not in a else 'first'} dump")
            continue
        ra, rb = a[key], b[key]
        if [r[0] for r in ra] != [r[0] for r in rb] or len(ra) != len(rb):
            bad.setdefault(name, f"[{key[0]}] structure differs: {''.join(r[0] for r in ra)} vs {''.join(r[0] for r in rb)}")
            continue
        for la, lb in zip(ra, rb, strict=True):
            if la[0] == "E":
                continue
            start = 3 if la[0] == "G" else 2 if la[0] in "KA" else 1
            if la[:start] != lb[:start] and la[0] != "G":
                bad.setdefault(name, f"[{key[0]}] {la[:start]} vs {lb[:start]}")
                break
            for va, vb in zip(la[start:], lb[start:], strict=True):
                d = abs(float(va) - float(vb))
                worst = max(worst, d)
                if d > tolerance:
                    bad.setdefault(name, f"[{key[0]}] {la[0]} differs by {d:.6f}: {la} vs {lb}")
                    break
    for name, why in sorted(bad.items()):
        print(f"DIFF {name}: {why}")
    print(f"{len({k[1] for k in a})} glyphs in the first dump, {len({k[1] for k in b})} in the second; "
          f"{len(bad)} differ; largest difference among the rest {worst:.2e}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
