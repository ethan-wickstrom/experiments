"""Lowercase Latin.

The round letters are ``o`` and what is cut from it or joined to a stem; the arched ones are ``n``; the narrow ones
(``i j l t f r``) are a stem with a slab, a bar or a rounded elbow that fills the cell; the diagonal ones are straight
strokes cut flat. Measurements that only this group needs are the helpers at the top.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

from rachis.geom import pt, unit
from rachis.glyph import Draw, Knot, char
from rachis.params import Params
from rachis.parts import arch, bowl, cut, elbow, hbar, mirror, ring, turn, vee, vstem

# ---------------------------------------------------------------------------------------------------------------
# Measurements of this group. Each is derived from the parameters; those marked (request) stand in for a parameter
# that params.py does not have yet.

EDGE = 4.0  # an italic keeps its ink at least this far inside the cell's sides


def lean(p: Params, y: float) -> float:
    """How far the italic's shear moves a point at height ``y`` to the right; 0 in an upright master."""
    return math.tan(math.radians(p.slant)) * (y - p.slant_origin)


def nudge(p: Params, left: Iterable[tuple[float, float]] = (), right: Iterable[tuple[float, float]] = ()) -> float:
    """The shift in x that keeps a slanted letter inside its cell. ``left`` and ``right`` are the upright positions
    of the points that the slant carries furthest out on each side. It is 0 for an upright master, and 0 for an
    italic whose points stay inside."""
    if not p.italic:
        return 0.0
    lo = min((x + lean(p, y) for x, y in left), default=EDGE)
    hi = max((x + lean(p, y) for x, y in right), default=p.width - EDGE)
    return max(0.0, EDGE - lo) - max(0.0, hi - (p.width - EDGE))


def crowd(p: Params, k: float) -> float:
    """The factor by which a stroke thins in a letter that has more strokes than the cell has room for (m, w). It
    falls with the share of the cell that a stem takes, so the Bold thins more than the Light. (request)"""
    return 1.0 - k * p.stem / p.width


def diag_t(p: Params) -> float:
    """Thickness of the diagonals of v, x, y, z and k: a little under the stem, as a diagonal looks darker. (request)"""
    return 0.94 * p.stem


def corner_r(p: Params) -> float:
    """Radius, on the centre line, of the elbow of l, t and f: a fixed inner radius plus half the stem. (request)"""
    return 0.15 * p.xh + p.stem / 2


def tail_r(p: Params) -> float:
    """Radius of the hook of g and j: the curve starts at the baseline and ends on the descender line."""
    return -p.desc - p.hair / 2


def dot_y(p: Params) -> float:
    """Height of the centre of the dot of i and j: a sixth of the x-height clear above the stem. (request)"""
    return p.xh + p.xh / 6 + p.dot


def bar(ax: float, ay: float, bx: float, by: float, t: float, a_side: float = 0.0, b_side: float = 0.0) -> list[Knot]:
    """``parts.diag`` with its ends given by a corner instead of the centre: a straight stroke ``t`` thick from
    height ``ay`` to ``by``, cut horizontally. ``ax`` is the stroke's left corner at that end when ``a_side`` is -1,
    its right corner when +1 and its centre when 0; likewise ``bx`` and ``b_side``."""
    breadth = t
    ca, cb = ax, bx
    for _ in range(12):  # the breadth of the cut depends on the slope, and the slope on the breadth
        ca, cb = ax - a_side * breadth / 2, bx - b_side * breadth / 2
        breadth = t * math.hypot(cb - ca, by - ay) / abs(by - ay)
    return [Knot(pt(ca, ay), breadth, pen=0, line=True), Knot(pt(cb, by), breadth, pen=0)]


def shifted(knots: Iterable[Knot], dx: float) -> list[Knot]:
    """``knots`` moved ``dx`` to the right."""
    return [Knot(k.z + dx, k.w, k.pen, k.dir, k.line, k.t_in, k.t_out, k.k) for k in knots]


# ---------------------------------------------------------------------------------------------------------------
# space, and the round and arched letters


@char(" ")
def space(g: Draw) -> None:
    pass


@char("o")
def o(g: Draw) -> None:
    p = g.p
    g.stroke(*ring(p.sb_round, -p.over, p.width - p.sb_round, p.xh + p.over, p.stem, p.hair, p.sq), closed=True)


@char("n")
def n(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.xl, 0, p.xh, p.stem))
    g.stroke(*arch(p, p.xl, p.xr, p.xh + p.over, 0))


@char("h")
def h(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.xl, 0, p.asc, p.stem))
    g.stroke(*arch(p, p.xl, p.xr, p.xh + p.over, 0))


@char("u")
def u(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.xr, 0, p.xh, p.stem))
    g.stroke(*turn(arch(p, p.xl, p.xr, p.xh + p.over, 0), p.mid, p.xh / 2))


@char("m")
def m(g: Draw) -> None:
    p = g.p
    s, s_mid = p.stem * crowd(p, 0.70), p.stem * crowd(p, 1.05)  # the middle stem is the thinnest
    h = p.hair * crowd(p, 0.70)
    side = 0.6 * p.sb - 4
    dx = nudge(p, left=[(side, 0)], right=[(p.width - side, 0.75 * p.xh)])
    x0, x1, x2 = side + s / 2 + dx, p.mid + dx, p.width - side - s / 2 + dx
    top = p.xh + p.over
    branch = top - h - 0.11 * p.xh
    g.stroke(*vstem(x0, 0, p.xh, s))
    g.stroke(*arch(p, x0, x1, top, 0, stem=s_mid, hair=h, branch=branch, spring=66, drop=1.5))
    second = arch(p, x1, x2, top, 0, stem=s, hair=h, branch=branch, spring=66, drop=1.5)
    g.stroke(*shifted(second[:1], -(s - s_mid) / 2), *second[1:])  # it springs from the thinner stem


@char("b")
def b(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.xl, 0, p.asc, p.stem))
    g.stroke(*bowl(p, p.xl, p.width - p.sb_round, -p.over, p.xh + p.over))


@char("d")
def d(g: Draw) -> None:
    p = g.p
    dx = nudge(p, right=[(p.width - p.sb, p.asc)])
    g.stroke(*vstem(p.xr + dx, 0, p.asc, p.stem))
    g.stroke(*shifted(mirror(bowl(p, p.xl, p.width - p.sb_round, -p.over, p.xh + p.over), p.mid), dx))


@char("p")
def p_(g: Draw) -> None:
    p = g.p
    dx = nudge(p, left=[(p.sb, p.desc)])
    g.stroke(*vstem(p.xl + dx, p.desc, p.xh, p.stem))
    g.stroke(*shifted(bowl(p, p.xl, p.width - p.sb_round, -p.over, p.xh + p.over), dx))


@char("q")
def q(g: Draw) -> None:
    p = g.p
    dx = -0.08 * p.stem  # it stands a little to the left, to leave room for the foot
    g.stroke(*vstem(p.xr + dx, p.desc, p.xh, p.stem))
    g.stroke(*shifted(mirror(bowl(p, p.xl, p.width - p.sb_round, -p.over, p.xh + p.over), p.mid), dx))
    g.stroke(*hbar(p.xr + dx, p.width - 0.2 * p.sb_round, p.desc + p.hair / 2, p.hair))


@char("g")
def g_(g: Draw) -> None:
    p = g.p
    g.stroke(*mirror(bowl(p, p.xl, p.width - p.sb_round, -p.over, p.xh + p.over), p.mid))
    g.stroke(*elbow(p.xr, p.xh, p.desc, p.sb_round + 40, p.stem, p.hair, p.sq, tail_r(p)))


# ---------------------------------------------------------------------------------------------------------------
# c, e, a, s


@char("c")
def c(g: Draw) -> None:
    p = g.p
    s, h = p.stem, p.hair
    x0, x1 = p.sb_round + 4, p.width - p.sb_round - 14
    cx = (x0 + x1) / 2 + 12
    top, bot = p.xh + p.over - h / 2, -p.over + h / 2
    white = top - bot - h
    g.stroke(
        cut(x1 - 4, top - 0.15 * white, h, 150),
        Knot(pt(cx, top), h, dir=180, k=p.sq),
        Knot(pt(x0 + s / 2, p.xh / 2), s, dir=-90, k=p.sq),
        Knot(pt(cx, bot), h, dir=0),
        cut(x1, bot + 0.15 * white, h, 30),
    )


@char("e")
def e(g: Draw) -> None:
    p = g.p
    s, h = p.stem, p.hair
    x0, x1 = p.sb_round + 2, p.width - p.sb_round - 2
    cx = (x0 + x1) / 2
    top, bot = p.xh + p.over - h / 2, -p.over + h / 2
    bh = 0.92 * h
    mid = 0.475 * p.xh  # centre line of the bar: a little below the middle
    below = (mid - bh / 2) - (bot + h / 2)  # the white between the bar and the bottom stroke
    g.stroke(
        Knot(pt(x1 - s / 2, mid - bh / 2), s, pen=0, dir=90, k=p.sq),
        Knot(pt(cx, top), h, dir=180, k=p.sq),
        Knot(pt(x0 + s / 2, p.xh / 2), s, dir=-90, k=p.sq),
        Knot(pt(cx + 10, bot), h, dir=0),
        cut(x1 - 8, bot + 0.32 * below, h, 26),
    )
    g.stroke(*hbar(x0 + s / 2, x1 - s / 2, mid, bh))


@char("a")
def a(g: Draw) -> None:
    p = g.p
    s, h = p.stem, p.hair
    xs = p.xr - 4  # the stem
    x0 = p.sb_round + 8  # the bowl's left edge
    top = p.xh + p.over - h / 2
    whites = p.xh + 2 * p.over - 3 * h  # what the three horizontal strokes leave
    upper = 0.45 * whites  # the white under the top stroke; the bowl's counter takes the rest
    bt = p.xh + p.over - h - upper  # outer top edge of the bowl
    xc = x0 + 0.52 * (xs - x0)
    g.stroke(
        cut(x0 + 0.32 * s, top - 0.30 * upper, h, 30),
        Knot(pt(xc, top), h, dir=0, k=p.sq),
        Knot(pt(xs, top - 1.0 * (xs - xc)), s, pen=0, dir=-90, line=True),
        Knot(pt(xs, 0), s, pen=0),
    )
    bot = -p.over + h / 2
    edge = xs - s / 2 + 3  # just inside the stem
    jt, jb = 0.82 * h, p.join * s  # breadth of the bowl where it leaves the stem, top and bottom
    d_top, d_bot = unit(168), unit(52)
    y_in = (bot + h / 2) + 0.30 * (bt - h - bot - h / 2)  # where the counter's edge meets the stem, below
    xb = x0 + 0.50 * (xs - s / 2 - x0)
    g.stroke(
        Knot(pt(edge, bt - 0.10 * h) - (s / 2) * d_top + (jt / 2) * d_top * 1j, jt, dir=168),
        Knot(pt(xb, bt - h / 2), h, dir=180, k=p.sq),
        Knot(pt(x0 + s / 2, (bt - p.over) / 2), s, dir=-90, k=p.sq),
        Knot(pt(xb + 4, bot), h, dir=0),
        Knot(pt(edge, y_in) - (jb / 2) * d_bot * 1j, jb, dir=52),
    )


@char("s")
def s(g: Draw) -> None:
    p = g.p
    w, h = p.stem, p.hair
    x0, x1 = p.sb_round + 22, p.width - p.sb_round - 22
    cx = (x0 + x1) / 2
    top, bot = p.xh + p.over - h / 2, -p.over + h / 2
    white = top - bot - h
    g.stroke(
        cut(x1 - 10, top - 0.13 * white, h, 152),
        Knot(pt(cx + 2, top), h, dir=180, k=p.sq),
        Knot(pt(x0 + 8 + w / 2, p.xh * 0.735), 0.96 * w, dir=-90),
        Knot(pt(cx, p.xh * 0.515), 1.02 * w, dir=-26),
        Knot(pt(x1 - w / 2, p.xh * 0.265), 0.96 * w, dir=-90, k=p.sq),
        Knot(pt(cx - 2, bot), h, dir=180),
        cut(x0, bot + 0.13 * white, h, 152),
    )


# ---------------------------------------------------------------------------------------------------------------
# the narrow letters: a stem, and a slab, a bar or an elbow to fill the cell


def slab(p: Params) -> float:
    """How far the slab at the top of i, j and l reaches to the left of its stem's edge. (request)"""
    return 0.25 * p.width - 0.25 * p.stem


@char("ı")
def dotlessi(g: Draw) -> None:
    p = g.p
    x = p.mid + 12
    half = 0.33 * p.width + 0.22 * p.stem  # half the length of the bar it stands on
    g.stroke(*vstem(x, 0, p.xh, p.stem))
    g.stroke(*hbar(x - p.stem / 2 - slab(p), x, p.xh - p.hair / 2, p.hair))
    g.stroke(*hbar(x - half, x + half, p.hair / 2, p.hair))


@char("i")
def i(g: Draw) -> None:
    p = g.p
    g.use("ı")
    g.dot(p.mid + 12 - 2, dot_y(p), p.dot)


def j_x(p: Params) -> float:
    """Centre of the stem of j."""
    return p.mid + 86


@char("ȷ")
def dotlessj(g: Draw) -> None:
    p = g.p
    x = j_x(p)
    g.stroke(*elbow(x, p.xh, p.desc, p.sb_round + 18, p.stem, p.hair, p.sq, tail_r(p)))
    g.stroke(*hbar(x - p.stem / 2 - slab(p) - 0.14 * p.width, x, p.xh - p.hair / 2, p.hair))


@char("j")
def j(g: Draw) -> None:
    p = g.p
    g.use("ȷ")
    g.dot(j_x(p) - 2, dot_y(p), p.dot)


@char("l")
def l(g: Draw) -> None:
    p = g.p
    x = p.mid - 24
    g.stroke(*elbow(x, p.asc, 0, p.width - p.sb_round, p.stem, p.hair, p.sq, corner_r(p)))
    g.stroke(*hbar(x - p.stem / 2 - slab(p), x, p.asc - p.hair / 2, p.hair))


@char("t")
def t(g: Draw) -> None:
    p = g.p
    x = p.mid - 50
    g.stroke(*elbow(x, p.xh + 0.74 * (p.asc - p.xh), 0, p.width - p.sb_round, p.stem, p.hair, p.sq, corner_r(p)))
    g.stroke(*hbar(p.sb_round + 6, p.width - p.sb_round - 16, p.xh - p.hair / 2, p.hair))


@char("f")
def f(g: Draw) -> None:
    p = g.p
    x = p.mid - 30
    g.stroke(*elbow(x, 0, p.asc + p.over, p.width - p.sb_round, p.stem, p.hair, p.sq, corner_r(p)))
    g.stroke(*hbar(p.sb_round + 6, p.width - p.sb_round - 30, p.xh - p.hair / 2, p.hair))


@char("r")
def r(g: Draw) -> None:
    p = g.p
    x = p.xl + 20
    end = p.width - p.sb_round
    g.stroke(*vstem(x, 0, p.xh, p.stem))
    a = arch(p, x, end - 30, p.xh + p.over, 0, lean=0.60)
    g.stroke(a[0], a[1], cut(end, p.xh + p.over - p.hair / 2 - 0.09 * p.xh, p.hair, -32))


# ---------------------------------------------------------------------------------------------------------------
# the diagonal letters


@char("k")
def k(g: Draw) -> None:
    p = g.p
    x = p.xl
    t = diag_t(p)
    g.stroke(*vstem(x, 0, p.asc, p.stem))
    arm = bar(x, 0.34 * p.xh, p.width - p.sb_round + 2, p.xh, 0.94 * t, 0, 1)
    g.stroke(Knot(arm[0].z, 0.94 * t, line=True), arm[1])
    f = 0.42  # how far along the arm the leg leaves it
    z = arm[0].z + f * (arm[1].z - arm[0].z)
    leg = bar(z.real, z.imag, p.width - p.sb_round + 12, 0, t, 0, 1)
    g.stroke(Knot(leg[0].z, t, line=True), leg[1])


@char("v")
def v(g: Draw) -> None:
    p = g.p
    t = diag_t(p)
    g.poly(vee(p.sb_round - 6, p.width - p.sb_round + 6, p.xh, 0, t, 0.7 * t))


@char("w")
def w(g: Draw) -> None:
    p = g.p
    t_out, t_in = p.stem * crowd(p, 1.0), p.stem * crowd(p, 2.1)
    side = p.sb / 2 - 15
    dx = nudge(p, right=[(p.width - side, p.xh)])
    x0, x1 = side + dx, p.width - side + dx
    mid = p.mid + dx
    foot = 0.26 * (x1 - x0)  # the lower vertices, from each side
    flat = 0.5 * t_in  # half the breadth of a vertex
    g.stroke(*bar(x0, p.xh, x0 + foot - flat, 0, t_out, -1, -1))
    g.stroke(*bar(x0 + foot + flat, 0, mid - flat, p.xh, t_in, 1, -1))
    g.stroke(*bar(mid + flat, p.xh, x1 - foot - flat, 0, t_in, 1, -1))
    g.stroke(*bar(x1 - foot + flat, 0, x1, p.xh, t_out, 1, 1))


@char("x")
def x(g: Draw) -> None:
    p = g.p
    t = diag_t(p)
    x0, x1 = p.sb_round - 2, p.width - p.sb_round + 2
    pinch = 8  # the top is narrower than the bottom
    g.stroke(*bar(x0, 0, x1 - pinch, p.xh, t, -1, 1))
    g.stroke(*bar(x0 + pinch, p.xh, x1, 0, t, -1, 1))


@char("y")
def y(g: Draw) -> None:
    p = g.p
    t = diag_t(p)
    x0, x1 = p.sb_round - 4, p.width - p.sb_round + 4
    xv = p.mid + 6  # where the two strokes' centre lines meet, on the baseline
    right = bar(x1, p.xh, xv, 0, t, 1, 0)
    slope = (right[0].z.real - xv) / p.xh
    g.stroke(right[0], Knot(pt(xv + slope * p.desc, p.desc), right[0].w, pen=0))
    g.stroke(*bar(x0, p.xh, xv, 0, t, -1, 0))


@char("z")
def z(g: Draw) -> None:
    p = g.p
    x0, x1 = p.sb_round + 28, p.width - p.sb_round - 28
    g.stroke(*hbar(x0 + 6, x1, p.xh - p.hair / 2, p.hair))
    g.stroke(*hbar(x0, x1 + 4, p.hair / 2, p.hair))
    g.stroke(*bar(x1, p.xh, x0, 0, diag_t(p), 1, -1))
