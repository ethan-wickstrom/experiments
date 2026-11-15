"""Uppercase Latin.

Plain grotesque capitals on the capital stems ``p.cxl`` and ``p.cxr``. Verticals are ``p.cap_stem`` thick, bars and
the tops and bottoms of bowls ``p.cap_hair``; diagonals are a stated fraction of one of them. Round sides stop
``_ox(p)`` short of the cell's edge. A letter with a stem on the left and an open or round right side (B D E F K L
P R) sits a little right of H's stem, so that its visual centre is the cell's.

Straight strokes are placed by their corners, not by their centre lines, because a diagonal's corners are what
must meet a stem, a bar or the cell (``_span``, ``_reach``, ``_vee``). Those parts know the italic's slant, so a
diagonal keeps its thickness when the skeleton leans.
"""

from __future__ import annotations

import math

from rachis.geom import intersect, pt
from rachis.glyph import Draw, Knot, char
from rachis.params import Params
from rachis.parts import cut, dbowl, hbar, ring, vstem

# -- measurements this group derives from the parameters ----------------------------------------------------------


def _ox(p: Params) -> float:
    """How far the round side of a capital (O, Q, D; C and G on the left) stays from the cell's edge."""
    return p.sb_round - 12


def _sqc(p: Params) -> float:
    """The squareness of a capital's bowls: a little squarer than the lowercase's, because they are taller."""
    return p.sq + 0.02


def _dt(p: Params) -> float:
    """The thickness of a capital's full diagonal (A K V X Y Z, the leg of R): it looks as heavy as a stem."""
    return p.cap_stem * 0.95


def _lean(p: Params) -> float:
    """How far to the right an italic moves a point for each unit of height."""
    return math.tan(math.radians(p.slant))


# -- parts only the capitals use ----------------------------------------------------------------------------------


def _cut_len(p: Params, dx: float, dy: float, t: float, c: float = 0.0) -> float:
    """The length ``w`` of the horizontal cut of a straight stroke that is ``t`` thick once the master's slant is
    applied, and whose centre line advances ``dx - c * w`` while it climbs ``dy`` (negative when it descends).
    ``c`` is 0 when ``dx`` is measured along one edge of the stroke, 1 when it is measured from the outer end of
    one cut to the outer end of the other (the stroke lies inside that box), -1 when it is measured between their
    inner ends, and a half or minus a half when it is measured from the middle of one cut to an end of the other."""
    dx += _lean(p) * dy
    a = dy * dy - c * c * t * t
    b = c * t * t * dx
    return (-b + math.sqrt(b * b + a * t * t * (dx * dx + dy * dy))) / a


def _span(p: Params, xa: float, ya: float, sa: float, xb: float, yb: float, sb: float, t: float) -> list[Knot]:
    """A straight stroke ``t`` thick, cut flat at both ends, from the height ``ya`` to the height ``yb``. Its cut at
    ``ya`` has its left end (``sa`` = -1) or its right end (``sa`` = 1) at ``xa``; likewise ``xb`` and ``sb``. With
    equal sides, one edge of the stroke runs from (xa, ya) to (xb, yb); with opposite sides the stroke fills the
    box between the two points from corner to corner."""
    w = _cut_len(p, xb - xa, yb - ya, t, (sb - sa) / 2)
    return [Knot(pt(xa - sa * w / 2, ya), w, pen=0, line=True), Knot(pt(xb - sb * w / 2, yb), w, pen=0)]


def _reach(p: Params, xc: float, yc: float, xe: float, se: float, ye: float, t: float) -> list[Knot]:
    """A straight stroke ``t`` thick, cut flat at both ends, whose first cut is centred on (xc, yc), where another
    stroke hides it, and whose cut at the height ``ye`` has its left end (``se`` = -1) or its right end (``se`` = 1)
    at ``xe``."""
    w = _cut_len(p, xe - xc, ye - yc, t, se / 2)
    return [Knot(pt(xc, yc), w, pen=0, line=True), Knot(pt(xe - se * w / 2, ye), w, pen=0)]


def _vee_cuts(
    p: Params, x0: float, x1: float, y_top: float, y_bot: float, t: float, apex: float
) -> tuple[float, float]:
    """The lengths of the cuts of the left and the right stroke of ``_vee``. They differ only in an italic."""
    mid = (x0 + x1) / 2
    dy = y_bot - y_top
    return _cut_len(p, mid - apex / 2 - x0, dy, t), _cut_len(p, mid + apex / 2 - x1, dy, t)


def _vee(p: Params, x0: float, x1: float, y_top: float, y_bot: float, t: float, apex: float) -> list[complex]:
    """The polygon of a V, as ``parts.vee``: outer corners at ``x0`` and ``x1`` on ``y_top``, strokes ``t`` thick,
    a flat vertex ``apex`` wide on ``y_bot``; a caret when ``y_bot`` is above ``y_top``. Unlike ``parts.vee`` it
    keeps both strokes ``t`` thick in an italic, where one of them leans further than the other."""
    mid = (x0 + x1) / 2
    wl, wr = _vee_cuts(p, x0, x1, y_top, y_bot, t, apex)
    tl, tr = pt(x0, y_top), pt(x1, y_top)
    vl, vr = pt(mid - apex / 2, y_bot), pt(mid + apex / 2, y_bot)
    crotch = intersect(tl + wl, vl - tl, tr - wr, vr - tr)
    assert crotch is not None
    return [tl, vl, vr, tr, tr - wr, crotch, tl + wl]


def _vee_x(
    p: Params, x0: float, x1: float, y_top: float, y_bot: float, t: float, apex: float, y: float
) -> tuple[float, float]:
    """The x of the centre lines of the two strokes of ``_vee`` at the height ``y``: where a crossbar ends."""
    mid = (x0 + x1) / 2
    wl, wr = _vee_cuts(p, x0, x1, y_top, y_bot, t, apex)
    f = (y - y_top) / (y_bot - y_top)
    return x0 + wl / 2 + f * (mid - apex / 2 - x0), x1 - wr / 2 + f * (mid + apex / 2 - x1)


def _meet(a: tuple[complex, complex], b: tuple[complex, complex]) -> complex:
    """Where the line through the two points of ``a`` crosses the line through the two points of ``b``."""
    z = intersect(a[0], a[1] - a[0], b[0], b[1] - b[0])
    assert z is not None
    return z


# -- stems and bars -----------------------------------------------------------------------------------------------


@char("H")
def H(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.cxl, 0, p.cap, p.cap_stem))
    g.stroke(*vstem(p.cxr, 0, p.cap, p.cap_stem))
    g.stroke(*hbar(p.cxl, p.cxr, p.cap * 0.51, p.cap_hair))


@char("I")
def I(g: Draw) -> None:
    p = g.p
    # the serifs are as long as the foot of the figure one
    g.stroke(*vstem(p.mid, 0, p.cap, p.cap_stem))
    g.stroke(*hbar(p.mid - 196, p.mid + 196, p.cap - p.cap_hair / 2, p.cap_hair))
    g.stroke(*hbar(p.mid - 196, p.mid + 196, p.cap_hair / 2, p.cap_hair))


@char("T")
def T(g: Draw) -> None:
    p = g.p
    x0 = p.sb_round - 20
    g.stroke(*vstem(p.mid, 0, p.cap, p.cap_stem))
    g.stroke(*hbar(x0, p.width - x0, p.cap - p.cap_hair / 2, p.cap_hair))


@char("L")
def L(g: Draw) -> None:
    p = g.p
    x = p.cxl + 34
    g.stroke(*vstem(x, 0, p.cap, p.cap_stem))
    g.stroke(*hbar(x, p.width - p.sb_round - 2, p.cap_hair / 2, p.cap_hair))


@char("E")
def E(g: Draw) -> None:
    p = g.p
    x = p.cxl + 16
    right = p.width - p.sb_round - 14
    g.stroke(*vstem(x, 0, p.cap, p.cap_stem))
    g.stroke(*hbar(x, right, p.cap - p.cap_hair / 2, p.cap_hair))
    g.stroke(*hbar(x, right - 40, p.cap * 0.52, p.cap_hair))
    g.stroke(*hbar(x, right + 6, p.cap_hair / 2, p.cap_hair))


@char("F")
def F(g: Draw) -> None:
    p = g.p
    x = p.cxl + 24
    right = p.width - p.sb_round - 8
    g.stroke(*vstem(x, 0, p.cap, p.cap_stem))
    g.stroke(*hbar(x, right, p.cap - p.cap_hair / 2, p.cap_hair))
    g.stroke(*hbar(x, right - 44, p.cap * 0.49, p.cap_hair))


# -- rounds -------------------------------------------------------------------------------------------------------


@char("O")
def O(g: Draw) -> None:
    p = g.p
    x0 = _ox(p)
    g.stroke(*ring(x0, -p.over, p.width - x0, p.cap + p.over, p.cap_stem, p.cap_hair, _sqc(p)), closed=True)


@char("Q")
def Q(g: Draw) -> None:
    p = g.p
    x0 = _ox(p)
    g.stroke(*ring(x0, -p.over, p.width - x0, p.cap + p.over, p.cap_stem, p.cap_hair, _sqc(p)), closed=True)
    # the tail starts a little inside the counter, so that it crosses the bowl, and ends below the baseline
    g.stroke(*_reach(p, p.mid + 26, p.cap_hair + 0.075 * p.cap, p.mid + 176, 1, -0.20 * p.cap, p.cap_hair * 1.04))


@char("C")
def C(g: Draw) -> None:
    p = g.p
    x0, x1 = _ox(p) + 14, p.width - _ox(p) - 12
    cx = (x0 + x1) / 2 + 14
    top, bot = p.cap + p.over - p.cap_hair / 2, -p.over + p.cap_hair / 2
    g.stroke(
        cut(x1, p.cap - 148, p.cap_hair * 1.04, 138),
        Knot(pt(cx, top), p.cap_hair, dir=180, k=_sqc(p)),
        Knot(pt(x0 + p.cap_stem / 2, p.cap / 2), p.cap_stem, dir=-90, k=_sqc(p)),
        Knot(pt(cx, bot), p.cap_hair, dir=0),
        cut(x1 + 4, 144, p.cap_hair * 1.04, 40),
    )


@char("G")
def G(g: Draw) -> None:
    p = g.p
    x0, x1 = _ox(p) + 6, p.width - _ox(p) - 16
    cx = (x0 + x1) / 2 + 8
    top, bot = p.cap + p.over - p.cap_hair / 2, -p.over + p.cap_hair / 2
    xs = x1 - p.cap_stem / 2  # the spur: a short stem that rises from the bowl to the bar
    bar = p.cap * 0.44
    g.stroke(
        cut(x1 - 6, p.cap - 148, p.cap_hair * 1.04, 138),
        Knot(pt(cx, top), p.cap_hair, dir=180, k=_sqc(p)),
        Knot(pt(x0 + p.cap_stem / 2, p.cap / 2), p.cap_stem, dir=-90, k=_sqc(p)),
        Knot(pt(cx, bot), p.cap_hair, dir=0, k=_sqc(p)),
        Knot(pt(xs, bot + 0.24 * p.cap), p.cap_stem, pen=0, dir=90, line=True),
        Knot(pt(xs, bar + p.cap_hair / 2), p.cap_stem, pen=0),
    )
    g.stroke(*hbar(xs - 0.42 * (x1 - x0), xs, bar, p.cap_hair))


@char("S")
def S(g: Draw) -> None:
    p = g.p
    x0, x1 = _ox(p) + 20, p.width - _ox(p) - 20
    cx = (x0 + x1) / 2
    top, bot = p.cap + p.over - p.cap_hair / 2, -p.over + p.cap_hair / 2
    w = p.cap_stem
    g.stroke(
        cut(x1 - 10, p.cap - 150, p.cap_hair * 1.04, 140),
        Knot(pt(cx + 4, top), p.cap_hair, dir=180, k=p.sq),
        Knot(pt(x0 + w / 2 + 8, p.cap * 0.745), w, dir=-90),
        Knot(pt(cx, p.cap * 0.515), w * 1.02, dir=-27),
        Knot(pt(x1 - w / 2, p.cap * 0.262), w, dir=-90, k=p.sq),
        Knot(pt(cx - 4, bot), p.cap_hair, dir=180),
        cut(x0 - 8, 148, p.cap_hair * 1.04, 140),
    )


@char("U")
def U(g: Draw) -> None:
    p = g.p
    bot = -p.over + p.cap_hair / 2
    ys = bot + 1.08 * (p.mid - p.cxl)  # where the stems end and the bottom begins
    g.stroke(
        Knot(pt(p.cxl, p.cap), p.cap_stem, pen=0, line=True),
        Knot(pt(p.cxl, ys), p.cap_stem, pen=0, dir=-90, k=_sqc(p)),
        Knot(pt(p.mid, bot), p.cap_hair, dir=0, k=_sqc(p)),
        Knot(pt(p.cxr, ys), p.cap_stem, pen=0, dir=90, line=True),
        Knot(pt(p.cxr, p.cap), p.cap_stem, pen=0),
    )


@char("J")
def J(g: Draw) -> None:
    p = g.p
    x = p.cxr - 22
    x_end = _ox(p) + 22
    yc = p.cap_hair / 2
    # the elbow of j, wider than it is high
    rx, ry = 0.66 * (x - x_end), 0.31 * p.cap
    g.stroke(
        Knot(pt(x, p.cap), p.cap_stem, pen=0, line=True),
        Knot(pt(x, yc + ry), p.cap_stem, pen=0, dir=-90, k=_sqc(p)),
        Knot(pt(x - rx, yc), p.cap_hair, pen=90, dir=180, line=True),
        Knot(pt(x_end, yc), p.cap_hair, pen=90),
    )
    g.stroke(*hbar(x - 0.60 * (x - x_end), x, p.cap - p.cap_hair / 2, p.cap_hair))


# -- stems with bowls ---------------------------------------------------------------------------------------------


@char("D")
def D(g: Draw) -> None:
    p = g.p
    x = p.cxl + 6
    edge = p.width - _ox(p)
    g.stroke(*vstem(x, 0, p.cap, p.cap_stem))
    g.stroke(*dbowl(x, edge, 0, p.cap, p.cap_stem, p.cap_hair, _sqc(p), 0.26 * (edge - x)))


@char("P")
def P(g: Draw) -> None:
    p = g.p
    x = p.cxl + 16
    edge = p.width - _ox(p) - 4
    waist = p.cap * 0.43
    g.stroke(*vstem(x, 0, p.cap, p.cap_stem))
    g.stroke(*dbowl(x, edge, waist - p.cap_hair / 2, p.cap, p.cap_stem, p.cap_hair, _sqc(p), 0.36 * (edge - x)))


@char("R")
def R(g: Draw) -> None:
    p = g.p
    x = p.cxl + 8
    edge = p.width - _ox(p) - 22
    waist = p.cap * 0.455
    g.stroke(*vstem(x, 0, p.cap, p.cap_stem))
    g.stroke(*dbowl(x, edge, waist - p.cap_hair / 2, p.cap, p.cap_stem, p.cap_hair, _sqc(p), 0.36 * (edge - x)))
    g.stroke(*_reach(p, p.mid + 4, waist, p.width - _ox(p) + 2, 1, 0, _dt(p)))


@char("B")
def B(g: Draw) -> None:
    p = g.p
    x = p.cxl + 8
    upper, lower = p.width - _ox(p) - 38, p.width - _ox(p) - 10
    waist = p.cap * 0.53
    g.stroke(*vstem(x, 0, p.cap, p.cap_stem))
    g.stroke(
        *dbowl(x, upper, waist - p.cap_hair / 2, p.cap, p.cap_stem * 0.96, p.cap_hair, _sqc(p), 0.42 * (upper - x))
    )
    g.stroke(*dbowl(x, lower, 0, waist + p.cap_hair / 2, p.cap_stem, p.cap_hair, _sqc(p), 0.42 * (lower - x)))


# -- diagonals ----------------------------------------------------------------------------------------------------


@char("A")
def A(g: Draw) -> None:
    p = g.p
    t = _dt(p)
    x0, x1 = p.sb_round - 30, p.width - p.sb_round + 30
    apex = t * 0.72
    g.poly(_vee(p, x0, x1, 0, p.cap, t, apex))
    y = p.cap * 0.25
    xl, xr = _vee_x(p, x0, x1, 0, p.cap, t, apex, y)
    g.stroke(*hbar(xl, xr, y, p.cap_hair))


@char("V")
def V(g: Draw) -> None:
    p = g.p
    t = _dt(p)
    x0 = p.sb_round - 28
    g.poly(_vee(p, x0, p.width - x0, p.cap, 0, t, t * 0.80))


@char("Y")
def Y(g: Draw) -> None:
    p = g.p
    x0 = p.sb_round - 30
    yj = p.cap * 0.40  # where the arms reach the stem
    g.poly(_vee(p, x0, p.width - x0, p.cap, yj, _dt(p), p.cap_stem))
    g.stroke(*vstem(p.mid, 0, yj + 0.3 * p.cap_stem, p.cap_stem))


@char("X")
def X(g: Draw) -> None:
    p = g.p
    t = _dt(p)
    x0, x1 = p.sb_round - 22, p.width - p.sb_round + 22
    g.stroke(*_span(p, x0, 0, -1, x1 - 8, p.cap, 1, t))
    g.stroke(*_span(p, x1, 0, 1, x0 + 8, p.cap, -1, t))


@char("Z")
def Z(g: Draw) -> None:
    p = g.p
    x0, x1 = p.sb_round + 4, p.width - p.sb_round - 4
    g.stroke(*hbar(x0 + 8, x1, p.cap - p.cap_hair / 2, p.cap_hair))
    g.stroke(*hbar(x0, x1 + 6, p.cap_hair / 2, p.cap_hair))
    g.stroke(*_span(p, x0, 0, -1, x1, p.cap, 1, _dt(p)))


@char("K")
def K(g: Draw) -> None:
    p = g.p
    x = p.cxl + 4
    t = _dt(p)
    xe = p.width - p.sb_round + 26
    g.stroke(*vstem(x, 0, p.cap, p.cap_stem))
    # the arm starts on a vertical cut inside the stem and ends with its corner at (xe, cap)
    xs, ya = x + 0.12 * p.cap_stem, p.cap * 0.36
    w = _cut_len(p, xe - xs, p.cap - ya, t, 0.5)
    slope = (xe - w / 2 - xs) / (p.cap - ya)
    g.stroke(Knot(pt(xs, ya), w / slope, pen=90, line=True), Knot(pt(xe - w / 2, p.cap), w, pen=0))
    # the leg leaves the arm a third of the way up it
    yj = ya + 0.34 * (p.cap - ya)
    g.stroke(*_reach(p, xs + slope * (yj - ya), yj, xe + 8, 1, 0, t))


@char("N")
def N(g: Draw) -> None:
    p = g.p
    s = p.cap_stem * 0.96
    x0, x1 = p.cap_sb, p.width - p.cap_sb
    g.stroke(*vstem(x0 + s / 2, 0, p.cap, s))
    g.stroke(*vstem(x1 - s / 2, 0, p.cap, s))
    g.stroke(*_span(p, x1, 0, 1, x0, p.cap, -1, p.cap_stem * 0.88))


@char("M")
def M(g: Draw) -> None:
    p = g.p
    s = p.cap_stem * 0.90
    x0 = p.cap_sb - 20
    x1 = p.width - x0
    g.stroke(*vstem(x0 + s / 2, 0, p.cap, s))
    g.stroke(*vstem(x1 - s / 2, 0, p.cap, s))
    t = p.cap_hair * 0.88  # thinned, and by more in the Bold, so that the three counters stay open
    g.poly(_vee(p, x0 + 0.35 * s, x1 - 0.35 * s, p.cap, p.cap * 0.30, t, 0.7 * t))


@char("W")
def W(g: Draw) -> None:
    p = g.p
    to, ti = p.cap_stem * 0.84, p.cap_stem * 0.72  # outer and inner strokes
    x0, x1 = 21.0, p.width - 21.0
    a = 0.5 * ti  # the flat of each vertex
    v0 = x0 + 0.25 * (x1 - x0)  # the middle of the left vertex
    v1 = p.width - v0
    top = p.cap * 0.80  # the height of the middle vertex
    wo_l = _cut_len(p, v0 - a / 2 - x0, -p.cap, to)
    wo_r = _cut_len(p, v1 + a / 2 - x1, -p.cap, to)
    wi_l = _cut_len(p, p.mid - v0 - a, top, ti, -1)
    wi_r = _cut_len(p, p.mid - v1 + a, top, ti, 1)
    # each stroke's two edges, as pairs of points
    outer_l = pt(x0 + wo_l, p.cap), pt(v0 - a / 2 + wo_l, 0)  # the inner edge of the left outer stroke
    outer_r = pt(x1 - wo_r, p.cap), pt(v1 + a / 2 - wo_r, 0)
    upper_l = pt(v0 + a / 2 - wi_l, 0), pt(p.mid - a / 2, top)  # the upper edge of the left inner stroke
    upper_r = pt(v1 - a / 2 + wi_r, 0), pt(p.mid + a / 2, top)
    lower_l = pt(v0 + a / 2, 0), pt(p.mid - a / 2 + wi_l, top)  # its lower edge
    lower_r = pt(v1 - a / 2, 0), pt(p.mid + a / 2 - wi_r, top)
    g.poly(
        [
            pt(x0, p.cap),
            pt(v0 - a / 2, 0),
            lower_l[0],
            _meet(lower_l, lower_r),
            lower_r[0],
            pt(v1 + a / 2, 0),
            pt(x1, p.cap),
            outer_r[0],
            _meet(outer_r, upper_r),
            upper_r[1],
            upper_l[1],
            _meet(outer_l, upper_l),
            outer_l[0],
        ]
    )
