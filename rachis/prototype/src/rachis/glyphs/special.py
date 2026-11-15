"""Glyphs that are not characters."""

from __future__ import annotations

from rachis.glyph import Draw, glyph
from rachis.pen import rect


@glyph(".notdef", upright=True)
def notdef(g: Draw) -> None:
    """What a font shows for a character it lacks: an empty box, cap-height tall."""
    p = g.p
    x0, x1 = p.cap_sb, p.width - p.cap_sb
    t = p.op * 0.8
    g.add(rect(x0, 0, x1, p.cap), slant=False)
    g.add(rect(x0 + t, t, x1 - t, p.cap - t).reversed(), slant=False)
