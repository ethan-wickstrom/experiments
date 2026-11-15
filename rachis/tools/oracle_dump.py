"""Dump every outline of the Python prototype in the line format of `rachis dump`.

Run with the prototype's interpreter:  prototype/.venv/bin/python tools/oracle_dump.py [--module NAME]
"""

from __future__ import annotations

import sys

from rachis import glyphs as glyph_modules
from rachis.geom import Line
from rachis.glyph import REGISTRY, build
from rachis.params import MASTERS


def main() -> None:
    module = sys.argv[sys.argv.index("--module") + 1] if "--module" in sys.argv else None
    glyph_modules.load()
    out: list[str] = []
    for p in MASTERS.values():
        for spec in REGISTRY.values():
            if module is not None and spec.module.rsplit(".", 1)[-1] != module:
                continue
            try:
                g = build(spec, p)
            except Exception as e:  # the oracle reports a failing program as the Rust side does
                out.append(f"G\t{p.name}\t{spec.name}\t{0.0:.6f}")
                out.append(f"E\t{e}")
                continue
            out.append(f"G\t{p.name}\t{g.name}\t{g.advance:.6f}")
            for c in g.contours:
                out.append(f"C\t{len(c.segs)}")
                for s in c.segs:
                    if isinstance(s, Line):
                        out.append(f"L\t{s.p0.real:.6f}\t{s.p0.imag:.6f}\t{s.p1.real:.6f}\t{s.p1.imag:.6f}")
                    else:
                        v = (s.p0, s.c1, s.c2, s.p3)
                        out.append("B\t" + "\t".join(f"{z.real:.6f}\t{z.imag:.6f}" for z in v))
            for name, z in g.components:
                out.append(f"K\t{name}\t{z.real:.6f}\t{z.imag:.6f}")
            for name, z in sorted(g.anchors.items()):
                out.append(f"A\t{name}\t{z.real:.6f}\t{z.imag:.6f}")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
