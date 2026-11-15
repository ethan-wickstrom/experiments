"""Structural checks on glyph programs: what must hold before a font is built from them."""

from __future__ import annotations

from collections.abc import Iterable

from rachis.glyph import REGISTRY, Glyph, build
from rachis.params import ITALIC_MASTERS, UPRIGHT_MASTERS, Params

# Glyphs may reach this far past the cell's sides before the check remarks on it.
SIDE_ALLOWANCE = 4.0


def check_glyphs(names: Iterable[str] | None = None) -> tuple[list[str], list[str]]:
    """Problems that must be fixed, and notes worth a look, for ``names`` (default: every registered glyph)."""
    problems: list[str] = []
    notes: list[str] = []
    for name in list(REGISTRY) if names is None else names:
        if name not in REGISTRY:
            problems.append(f"{name}: no such glyph")
            continue
        spec = REGISTRY[name]
        for group in (UPRIGHT_MASTERS, ITALIC_MASTERS):
            built: list[tuple[Params, Glyph]] = []
            for p in group:
                try:
                    built.append((p, build(spec, p)))
                except Exception as e:  # a glyph program may fail in any way; report it and go on
                    problems.append(f"{name} [{p.name}]: {type(e).__name__}: {e}")
            if len(built) != len(group):
                continue
            signatures = {g.signature() for _, g in built}
            if len(signatures) != 1:
                problems.append(
                    f"{name}: masters {', '.join(p.name for p in group)} differ in structure, so they cannot be "
                    f"interpolated: {' | '.join(g.signature() for _, g in built)}"
                )
            for p, g in built:
                for base, _ in g.components:
                    if base not in REGISTRY:
                        problems.append(f"{name}: component {base!r} is not a glyph")
                expected = 0.0 if spec.mark else (p.width if spec.advance is None else spec.advance)
                if g.advance != expected:
                    problems.append(f"{name} [{p.name}]: advance {g.advance}, expected {expected}")
                for i, c in enumerate(g.contours):
                    if abs(c.area()) < 1.0:
                        problems.append(f"{name} [{p.name}]: contour {i} has no area")
                    for s in c.segs:
                        if any(v != v or abs(v) > 1e5 for z in (s.start, s.end) for v in (z.real, z.imag)):
                            problems.append(f"{name} [{p.name}]: contour {i} has a wild coordinate")
                            break
                box = g.bounds()
                if box is None:
                    if not g.components and name != "space" and not name.startswith(("uni00A0", "nbspace")):
                        notes.append(f"{name} [{p.name}]: empty")
                    continue
                x0, y0, x1, y1 = box
                if not spec.upright and not p.italic and not spec.mark:
                    if x0 < -SIDE_ALLOWANCE or x1 > g.advance + SIDE_ALLOWANCE:
                        notes.append(f"{name} [{p.name}]: reaches outside its cell: x from {x0:.0f} to {x1:.0f}")
                    if y1 > p.asc + 260 or y0 < p.desc - 120:
                        notes.append(f"{name} [{p.name}]: very tall or deep: y from {y0:.0f} to {y1:.0f}")
    return problems, notes
