"""Parts: the skeletons that letters share, as lists of knots.

A part returns knots and draws nothing, so a glyph program can mirror or turn it before stroking it: ``u`` is ``n``
turned half a circle, ``d`` is ``b`` mirrored. The symmetries are those of the rectangle: ``mirror`` (left-right),
``flip`` (top-bottom) and ``turn`` (both).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import replace

from rachis.geom import pt, unit
from rachis.params import Params
from rachis.pen import Knot


def mirror(knots: Sequence[Knot], cx: float) -> list[Knot]:
    """Reflect left to right in the vertical line x = cx."""
    return [
        replace(
            k,
            z=complex(2 * cx - k.z.real, k.z.imag),
            dir=None if k.dir is None else 180.0 - k.dir,
            pen=None if k.pen is None else 180.0 - k.pen,
        )
        for k in knots
    ]


def flip(knots: Sequence[Knot], cy: float) -> list[Knot]:
    """Reflect top to bottom in the horizontal line y = cy."""
    return [
        replace(
            k,
            z=complex(k.z.real, 2 * cy - k.z.imag),
            dir=None if k.dir is None else -k.dir,
            pen=None if k.pen is None else -k.pen,
        )
        for k in knots
    ]


def turn(knots: Sequence[Knot], cx: float, cy: float) -> list[Knot]:
    """Rotate half a circle about (cx, cy)."""
    return [
        replace(k, z=complex(2 * cx - k.z.real, 2 * cy - k.z.imag), dir=None if k.dir is None else k.dir + 180.0)
        for k in knots
    ]


def vstem(x: float, y0: float, y1: float, w: float) -> list[Knot]:
    """A vertical stroke centred on x, cut square at y0 and y1."""
    return [Knot(pt(x, y0), w, pen=0, line=True), Knot(pt(x, y1), w, pen=0)]


def hbar(x0: float, x1: float, y: float, w: float) -> list[Knot]:
    """A horizontal stroke centred on y, cut square at x0 and x1."""
    return [Knot(pt(x0, y), w, pen=90, line=True), Knot(pt(x1, y), w, pen=90)]


def ring(x0: float, y0: float, x1: float, y1: float, sw: float, hw: float, k: float) -> list[Knot]:
    """A closed bowl whose outer edge touches the box (x0, y0)-(x1, y1): ``sw`` thick at the sides, ``hw`` at top
    and bottom. Stroke it with ``closed=True``."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2 - sw / 2, (y1 - y0) / 2 - hw / 2
    return [
        Knot(pt(cx + rx, cy), sw, dir=90, k=k),
        Knot(pt(cx, cy + ry), hw, dir=180, k=k),
        Knot(pt(cx - rx, cy), sw, dir=-90, k=k),
        Knot(pt(cx, cy - ry), hw, dir=0, k=k),
    ]


def arch(
    p: Params,
    xl: float,
    xr: float,
    top: float,
    foot: float,
    *,
    stem: float | None = None,
    hair: float | None = None,
    branch: float | None = None,
    lean: float = 0.54,
    spring: float = 58.0,
    drop: float = 1.08,
) -> list[Knot]:
    """The shoulder of n: it springs from the right edge of the stem centred on ``xl``, crests with its outer edge
    at ``top``, and comes down as a stem centred on ``xr`` to ``foot``.

    ``branch`` is the height where the arch's lower edge leaves the left stem. ``lean`` places the crest across the
    counter (0.5 is the middle). ``spring`` is the direction, in degrees, in which the arch leaves the stem.
    ``drop`` is the height of the shoulder's curve as a multiple of its width.
    """
    s = p.stem if stem is None else stem
    h = p.hair if hair is None else hair
    branch = top - 0.30 * p.xh if branch is None else branch
    j = p.join * s
    d = unit(spring)
    start = pt(xl + s / 2 - 3, branch) + (j / 2) * d * 1j
    inner_l, inner_r = xl + s / 2, xr - s / 2
    xa = inner_l + lean * (inner_r - inner_l)
    crest = top - h / 2
    shoulder = crest - drop * (xr - xa)
    return [
        Knot(start, j, dir=spring),
        Knot(pt(xa, crest), h, dir=0, k=p.sq),
        Knot(pt(xr, shoulder), s, pen=0, dir=-90, line=True),
        Knot(pt(xr, foot), s, pen=0),
    ]


def bowl(
    p: Params,
    xl: float,
    x_edge: float,
    y0: float,
    y1: float,
    *,
    stem: float | None = None,
    hair: float | None = None,
    branch: float = 0.30,
    spring: float = 58.0,
    lean: float = 0.50,
) -> list[Knot]:
    """The bowl of b: it springs from the right edge of the stem centred on ``xl``, reaches ``x_edge`` with its
    outer edge, and returns to the stem. Its outer edge spans ``y0`` to ``y1``."""
    s = p.stem if stem is None else stem
    h = p.hair if hair is None else hair
    j = p.join * s
    height = y1 - y0
    d_top, d_bot = unit(spring), unit(180 - spring)
    edge = xl + s / 2 - 3
    start = pt(edge, y1 - branch * height) + (j / 2) * d_top * 1j
    end = pt(edge, y0 + branch * height) + (j / 2) * d_bot * 1j
    inner_l = xl + s / 2
    xa = inner_l + lean * (x_edge - s - inner_l)
    xc = x_edge - s / 2
    return [
        Knot(start, j, dir=spring),
        Knot(pt(xa, y1 - h / 2), h, dir=0, k=p.sq),
        Knot(pt(xc, (y0 + y1) / 2), s, dir=-90, k=p.sq),
        Knot(pt(xa, y0 + h / 2), h, dir=180),
        Knot(end, j, dir=180 - spring),
    ]


def cut(
    x: float,
    y: float,
    t: float,
    dir: float,
    pen: float = 90.0,
    *,
    k: float | None = None,
    line: bool = False,
    t_in: float = 1.0,
    t_out: float = 1.0,
) -> Knot:
    """A knot whose pen is held at the angle ``pen`` and is broad enough that the stroke, travelling along
    ``dir``, is ``t`` thick: the way to end a curved stroke with a vertical (``pen=90``) or horizontal cut."""
    breadth = t / abs(math.sin(math.radians(dir - pen)))
    return Knot(pt(x, y), breadth, pen=pen, dir=dir, k=k, line=line, t_in=t_in, t_out=t_out)


def diag(x0: float, y0: float, x1: float, y1: float, t: float) -> list[Knot]:
    """A straight stroke ``t`` thick from (x0, y0) to (x1, y1), cut horizontally at both ends. The points are on
    its centre line."""
    breadth = t * math.hypot(x1 - x0, y1 - y0) / abs(y1 - y0)
    return [Knot(pt(x0, y0), breadth, pen=0, line=True), Knot(pt(x1, y1), breadth, pen=0)]


def elbow(x: float, y_from: float, y_edge: float, x_end: float, sw: float, hw: float, k: float, r: float) -> list[Knot]:
    """A stem centred on ``x`` that runs from ``y_from`` towards ``y_edge``, turns a rounded corner and ends as a
    horizontal foot whose outer edge lies on ``y_edge`` and whose vertical cut is at ``x_end``. ``r`` is the radius
    of the corner on the centre line. It is the tail of l, t and j and the hook of f."""
    down = y_from > y_edge
    right = x_end > x
    yc = y_edge + hw / 2 if down else y_edge - hw / 2
    return [
        Knot(pt(x, y_from), sw, pen=0, line=True),
        Knot(pt(x, yc + r if down else yc - r), sw, pen=0, dir=-90 if down else 90, k=k),
        Knot(pt(x + r if right else x - r, yc), hw, pen=90, dir=0 if right else 180, line=True),
        Knot(pt(x_end, yc), hw, pen=90),
    ]


def vee(x0: float, x1: float, y_top: float, y_bot: float, t: float, apex: float) -> list[complex]:
    """The polygon of a V: outer top corners at ``x0`` and ``x1``, strokes ``t`` thick, a flat vertex ``apex``
    wide on ``y_bot``. Negative heights turn it into a caret."""
    mid = (x0 + x1) / 2
    dx = (mid - apex / 2) - x0
    dy = y_top - y_bot
    wh = t * math.hypot(dx, dy) / abs(dy)
    crotch = pt(mid, y_top - dy * (mid - x0 - wh) / dx)
    return [
        pt(x0, y_top),
        pt(mid - apex / 2, y_bot),
        pt(mid + apex / 2, y_bot),
        pt(x1, y_top),
        pt(x1 - wh, y_top),
        crotch,
        pt(x0 + wh, y_top),
    ]


def vee_x(x0: float, x1: float, y_top: float, y_bot: float, t: float, apex: float, y: float) -> float:
    """The x of the centre line of the left stroke of ``vee(...)`` at height ``y``: where a crossbar ends."""
    mid = (x0 + x1) / 2
    dx = (mid - apex / 2) - x0
    dy = y_top - y_bot
    wh = t * math.hypot(dx, dy) / abs(dy)
    return x0 + wh / 2 + dx * (y_top - y) / dy


def dbowl(xl: float, x_edge: float, y0: float, y1: float, sw: float, hw: float, k: float, flat: float) -> list[Knot]:
    """The bowl of D, P, B and R: a bar from the stem centred on ``xl`` along the top, a round side whose outer
    edge reaches ``x_edge``, and a bar back along the bottom. The outer edge spans ``y0`` to ``y1``; ``flat`` is the
    length of the straight part of each bar, measured from ``xl``."""
    yt, yb = y1 - hw / 2, y0 + hw / 2
    xc = x_edge - sw / 2
    return [
        Knot(pt(xl, yt), hw, pen=90, line=True),
        Knot(pt(xl + flat, yt), hw, pen=90, dir=0, k=k),
        Knot(pt(xc, (yt + yb) / 2), sw, dir=-90, k=k),
        Knot(pt(xl + flat, yb), hw, pen=90, dir=180, line=True),
        Knot(pt(xl, yb), hw, pen=90),
    ]
