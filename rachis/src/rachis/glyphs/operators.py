"""Operators and mathematical signs.

The group is a system. Every sign is assembled from a few primitives, defined once below: the bar, the stem, the
chevron, the slash, the ring, the dot and the arc. They share one axis (``p.axis``), one stroke (``p.op``) and one
horizontal span (``p.op_l`` to ``p.op_r``), so ``->``, ``=>``, ``<=`` and ``|>`` line up without being fused.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import replace

from rachis.geom import intersect, pt, unit
from rachis.glyph import Draw, Knot, char
from rachis.params import Params
from rachis.parts import cut, diag, elbow, flip, hbar, mirror, ring, vee, vee_x, vstem

# ---------------------------------------------------------------------------------------------------------------
# Measurements the group derives from the parameters


def half_span(p: Params) -> float:
    """Half the operators' span: the plus is this far across and this far up and down from the axis."""
    return (p.op_r - p.op_l) / 2


def fine(p: Params) -> float:
    """The stroke of a part drawn inside another shape, or doubled: it grows with weight more slowly than
    ``p.op``, so that counters stay open in the Bold."""
    return 0.56 * p.op + 18


def tip(p: Params) -> float:
    """The flat of a pointed vertex: a third of a stem."""
    return p.stem / 3


def chevron_rise(p: Params) -> float:
    """How far the open ends of < and > reach above and below the axis (their outer corners)."""
    return 160 + 0.55 * p.op


def rel_rise(p: Params) -> float:
    """The same for a chevron or an arc that stands over a bar: shortened."""
    return 0.87 * chevron_rise(p)


def rel_gap(p: Params) -> float:
    """The white between a relation and the bar or wave under it."""
    return 40 + 0.5 * p.op


def set_rise(p: Params) -> float:
    """How far the arms of the subset and element signs lie above and below the axis (their outer edges)."""
    return 185 + 0.5 * p.op


def stand_top(p: Params) -> float:
    """The top of the signs that stand on the baseline (the cup, the wedge, the divides bar): as far above the
    axis as the baseline is below it, so that they too are centred on the axis."""
    return 2 * p.axis


def big_bot(p: Params) -> float:
    """The bottom of the big operators (sum, product, radical)."""
    return 0.4 * p.br_bot


def big_top(p: Params) -> float:
    """Their top."""
    return p.cap + 30


def over(p: Params, rise: float, low: float) -> tuple[float, float]:
    """Where to put a shape that reaches ``rise`` above and below its centre, and a thing ``low`` tall under it,
    so that the pair is centred on the axis: the centre of the thing below, then the centre of the shape."""
    gap = rel_gap(p)
    bottom = p.axis - (2 * rise + gap + low) / 2
    return bottom + low / 2, bottom + low + gap + rise


# ---------------------------------------------------------------------------------------------------------------
# Primitives


def mirrored(points: Sequence[complex], cx: float) -> list[complex]:
    """A polygon reflected left to right in the line x = cx."""
    return [complex(2 * cx - z.real, z.imag) for z in points]


def bar(g: Draw, y: float, x0: float | None = None, x1: float | None = None, t: float | None = None) -> None:
    """The bar: a horizontal stroke centred on ``y``, across the span unless told otherwise."""
    p = g.p
    g.stroke(*hbar(p.op_l if x0 is None else x0, p.op_r if x1 is None else x1, y, p.op if t is None else t))


def stem(g: Draw, x: float, y0: float, y1: float, t: float | None = None) -> None:
    """The stem: a vertical stroke centred on ``x``."""
    g.stroke(*vstem(x, y0, y1, g.p.op if t is None else t))


def chevron(x_tip: float, x_open: float, cy: float, rise: float, t: float, flat: float) -> list[complex]:
    """The polygon of a chevron: two straight strokes ``t`` thick that meet at a point on (``x_tip``, ``cy``),
    flattened there to ``flat``, and are cut vertically at ``x_open``, their outer corners ``rise`` above and
    below ``cy``."""
    s = 1.0 if x_open > x_tip else -1.0
    dx = abs(x_open - x_tip)
    dy = rise - flat / 2
    wv = t * math.hypot(dx, dy) / dx  # the height of the vertical cut
    crotch = x_open - s * (rise - wv) * dx / dy
    return [
        pt(x_open, cy + rise),
        pt(x_tip, cy + flat / 2),
        pt(x_tip, cy - flat / 2),
        pt(x_open, cy - rise),
        pt(x_open, cy - rise + wv),
        pt(crotch, cy),
        pt(x_open, cy + rise - wv),
    ]


def slash(g: Draw, x0: float, y0: float, x1: float, y1: float, t: float) -> None:
    """The slash: a straight stroke ``t`` thick between two points on its centre line, cut flat."""
    g.stroke(*diag(x0, y0, x1, y1, t))


def rake(x0: float, y0: float, x1: float, y1: float, t: float) -> list[Knot]:
    """A straight stroke ``t`` thick between two points on its centre line, cut vertically: for a stroke nearer
    the horizontal than the vertical, where a flat cut would leave a sliver."""
    w = t * math.hypot(x1 - x0, y1 - y0) / abs(x1 - x0)
    return [Knot(pt(x0, y0), w, pen=90, line=True), Knot(pt(x1, y1), w, pen=90)]


def strike(g: Draw, cx: float, cy: float, dx: float, dy: float, t: float | None = None) -> None:
    """The slash that negates a sign: through (``cx``, ``cy``), reaching ``dx`` across and ``dy`` up and down."""
    slash(g, cx - dx, cy - dy, cx + dx, cy + dy, g.p.op if t is None else t)


def cross(g: Draw, cx: float, cy: float, d: float, t: float | None = None) -> None:
    """The plus turned 45 degrees: two slashes through (``cx``, ``cy``) whose centre lines reach ``d``."""
    t = g.p.op if t is None else t
    slash(g, cx - d, cy - d, cx + d, cy + d, t)
    slash(g, cx - d, cy + d, cx + d, cy - d, t)


def circle(g: Draw, cx: float, cy: float, rx: float, ry: float | None = None, t: float | None = None) -> None:
    """The ring: a superellipse whose outer edge is ``rx`` (and ``ry``) from its centre."""
    p = g.p
    t = p.op if t is None else t
    ry = rx if ry is None else ry
    g.stroke(*ring(cx - rx, cy - ry, cx + rx, cy + ry, t, t, p.sq), closed=True)


def arc(p: Params, x_side: float, x_open: float, y0: float, y1: float, t: float | None = None) -> list[Knot]:
    """The arc: half a superelliptic ring whose round side touches ``x_side`` and whose straight arms, with their
    outer edges on ``y0`` and ``y1``, run to a vertical cut at ``x_open``."""
    t = p.op if t is None else t
    s = 1.0 if x_open > x_side else -1.0
    xa = x_side + s * (y1 - y0) / 2  # where the arms straighten
    yt, yb = y1 - t / 2, y0 + t / 2
    back = 180.0 if s > 0 else 0.0
    return [
        Knot(pt(x_open, yt), t, pen=90, line=True),
        Knot(pt(xa, yt), t, pen=90, dir=back, k=p.sq),
        Knot(pt(x_side + s * t / 2, (y0 + y1) / 2), t, dir=-90, k=p.sq),
        Knot(pt(xa, yb), t, pen=90, dir=180.0 - back, line=True),
        Knot(pt(x_open, yb), t, pen=90),
    ]


def transposed(knots: Sequence[Knot]) -> list[Knot]:
    """Reflect in the diagonal y = x, which exchanges across and up: the arc of the subset sign becomes the cup."""
    return [
        replace(
            k,
            z=complex(k.z.imag, k.z.real),
            dir=None if k.dir is None else 90.0 - k.dir,
            pen=None if k.pen is None else 90.0 - k.pen,
        )
        for k in knots
    ]


def inset(points: Sequence[complex], d: float) -> list[complex]:
    """A convex polygon, given counter-clockwise, with every side moved ``d`` inwards."""
    n = len(points)
    lines = []
    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        u = (b - a) / abs(b - a)
        lines.append((a + d * u * 1j, u))
    out = []
    for i in range(n):
        (a, u), (b, v) = lines[i - 1], lines[i]
        z = intersect(a, u, b, v)
        assert z is not None
        out.append(z)
    return out


def outline(g: Draw, points: Sequence[complex], t: float | None = None) -> None:
    """The outline of a convex polygon (counter-clockwise), ``t`` thick, inside it, with mitred corners."""
    t = g.p.op if t is None else t
    g.stroke(*(Knot(z, t, line=True) for z in inset(points, t / 2)), closed=True)


def box(x0: float, y0: float, x1: float, y1: float) -> list[complex]:
    return [pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1)]


def wave_rise(p: Params) -> float:
    """How far the centre line of the tilde rises and falls."""
    return 60 + 0.14 * p.op


def wave(p: Params, y: float, a: float | None = None, t: float | None = None) -> list[Knot]:
    """The wave of the tilde across the span, centred on ``y``: up on the left, down on the right, cut vertically."""
    t = p.op if t is None else t
    a = wave_rise(p) if a is None else a
    w = p.op_r - p.op_l
    return [
        cut(p.op_l, y - 0.50 * a, t, 40),
        Knot(pt(p.op_l + 0.27 * w, y + a), t, dir=0),
        Knot(pt(p.mid, y), t),
        Knot(pt(p.op_r - 0.27 * w, y - a), t, dir=0),
        cut(p.op_r, y + 0.50 * a, t, 40),
    ]


# ---------------------------------------------------------------------------------------------------------------
# ASCII


@char("-")
def hyphen(g: Draw) -> None:
    p = g.p
    bar(g, p.axis, p.op_l + 30, p.op_r - 30)


@char("−")
def minus(g: Draw) -> None:
    bar(g, g.p.axis)


@char("+")
def plus(g: Draw) -> None:
    p = g.p
    h = half_span(p)
    bar(g, p.axis)
    stem(g, p.mid, p.axis - h, p.axis + h)


def equal_pitch(p: Params) -> float:
    """The distance between the centre lines of the two bars of =: the gap is about 1.7 bars."""
    return 100 + 1.35 * p.op


@char("=")
def equal(g: Draw) -> None:
    p = g.p
    d = equal_pitch(p) / 2
    bar(g, p.axis + d)
    bar(g, p.axis - d)


@char("<")
def less(g: Draw) -> None:
    p = g.p
    g.poly(chevron(p.op_l, p.op_r, p.axis, chevron_rise(p), p.op, tip(p)))


@char(">")
def greater(g: Draw) -> None:
    p = g.p
    g.poly(mirrored(chevron(p.op_l, p.op_r, p.axis, chevron_rise(p), p.op, tip(p)), p.mid))


@char("*")
def asterisk(g: Draw) -> None:
    p = g.p
    r = 170 + 0.45 * p.op  # the upright arms; the slanted ones are longer, so that the sign is as wide as tall
    t = p.op
    stem(g, p.mid, p.axis - r, p.axis + r, t)
    c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
    rd = 1.13 * r
    for sign in (1, -1):
        g.stroke(*rake(p.mid - rd * c, p.axis - sign * rd * s, p.mid + rd * c, p.axis + sign * rd * s, t))


def slash_run(p: Params, back: bool = False) -> float:
    """How far the centre line of / and of the backslash runs across, to each side of the middle. The italic
    would lean the slash further and stand the backslash up; half of that is taken back."""
    if not p.italic:
        return 158.0
    return 158.0 + (40.0 if back else -40.0)


@char("/")
def slash_(g: Draw) -> None:
    p = g.p
    d = slash_run(p)
    slash(g, p.mid - d, p.br_bot, p.mid + d, p.br_top, p.stem * 0.9)


@char("\\")
def backslash(g: Draw) -> None:
    p = g.p
    d = slash_run(p, back=True)
    slash(g, p.mid + d, p.br_bot, p.mid - d, p.br_top, p.stem * 0.9)


@char("|")
def bar_(g: Draw) -> None:
    p = g.p
    stem(g, p.mid, p.br_bot, p.br_top, p.stem)


@char("^")
def asciicircum(g: Draw) -> None:
    p = g.p
    g.poly(vee(p.mid - 210, p.mid + 210, p.cap * 0.47, p.cap, p.op, tip(p)))


@char("~")
def asciitilde(g: Draw) -> None:
    g.stroke(*wave(g.p, g.p.axis))


# ---------------------------------------------------------------------------------------------------------------
# Arithmetic


@char("×")
def multiply(g: Draw) -> None:
    p = g.p
    cross(g, p.mid, p.axis, 0.75 * half_span(p))


def dot_gap(p: Params) -> float:
    """The white between a bar and a dot above or below it."""
    return 44 + 0.3 * p.op


@char("÷")
def divide(g: Draw) -> None:
    p = g.p
    d = p.op / 2 + dot_gap(p) + p.dot
    bar(g, p.axis)
    g.dot(p.mid, p.axis + d, p.dot)
    g.dot(p.mid, p.axis - d, p.dot)


def plus_minus(g: Draw, turned: bool = False) -> None:
    p = g.p
    h = rel_rise(p) + 30
    yb, cy = over(p, h, p.op)
    if turned:
        yb, cy = 2 * p.axis - yb, 2 * p.axis - cy
    bar(g, yb)
    bar(g, cy)
    stem(g, p.mid, cy - h, cy + h)


@char("±")
def plusminus(g: Draw) -> None:
    plus_minus(g)


@char("∓")
def minusplus(g: Draw) -> None:
    plus_minus(g, turned=True)


@char("¬")
def logicalnot(g: Draw) -> None:
    p = g.p
    h = 0.45 * half_span(p)
    y = p.axis + h - p.op / 2
    bar(g, y)
    stem(g, p.op_r - p.op / 2, p.axis - h, y)


@char("⋅")
def dot_operator(g: Draw) -> None:
    p = g.p
    g.dot(p.mid, p.axis, 0.78 * p.punct)


@char("∙")
def bullet_operator(g: Draw) -> None:
    p = g.p
    g.dot(p.mid, p.axis, 1.1 * p.punct)


def small_ring(p: Params) -> float:
    """The outer radius of the ring operator."""
    return 85 + 0.55 * p.op


@char("∘")
def ring_operator(g: Draw) -> None:
    p = g.p
    circle(g, p.mid, p.axis, small_ring(p), t=0.5 * (p.op + fine(p)))


def radical(g: Draw) -> None:
    """The radical: a tick, a short stroke down to a flat vertex, a long stroke up and a bar over what follows."""
    p = g.p
    t = p.op
    yb, yt = big_bot(p), big_top(p)
    ym = p.axis + 30  # the top of the short stroke
    apex = tip(p)
    xv = 218.0  # the vertex
    xl, xr = 92.0, 392.0  # the outer top corners of the two strokes
    left_dir = pt(xv - apex / 2, yb) - pt(xl, ym)
    right_dir = pt(xr, yt) - pt(xv + apex / 2, yb)
    wl = t * abs(left_dir) / abs(left_dir.imag)
    wr = t * abs(right_dir) / abs(right_dir.imag)
    crotch = intersect(pt(xl + wl, ym), left_dir, pt(xr - wr, yt), right_dir)
    assert crotch is not None
    g.poly(
        [
            pt(xl, ym),
            pt(xv - apex / 2, yb),
            pt(xv + apex / 2, yb),
            pt(xr, yt),
            pt(xr - wr, yt),
            crotch,
            pt(xl + wl, ym),
        ]
    )
    g.stroke(*hbar(xr - wr, p.width - 26, yt - t / 2, t))
    g.stroke(*hbar(30, xl + wl, ym - t / 2, t))


@char("√")
def radical_(g: Draw) -> None:
    radical(g)


def small_stroke(p: Params) -> float:
    """The stroke of the small figures and letters set over or inside a sign."""
    return 0.40 * p.op + 12


def small_three(g: Draw, x0: float, x1: float, y0: float, y1: float) -> None:
    p = g.p
    t = small_stroke(p)
    cx, ym = (x0 + x1) / 2, (y0 + y1) / 2 + 0.03 * (y1 - y0)
    h = y1 - y0
    g.stroke(
        cut(x0, y1 - 0.20 * h, t, 48),
        Knot(pt(cx - 2, y1 - t / 2), t, dir=0, k=p.sq),
        Knot(pt(x1 - t / 2 - 4, (y1 + ym) / 2), t, dir=-90, k=p.sq),
        Knot(pt(cx + 4, ym), t, pen=90, dir=180, line=True),
        Knot(pt(cx - 0.16 * (x1 - x0), ym), t, pen=90),
    )
    g.stroke(
        Knot(pt(cx - 0.16 * (x1 - x0), ym), t, pen=90, line=True),
        Knot(pt(cx + 4, ym), t, pen=90, dir=0, k=p.sq),
        Knot(pt(x1 - t / 2, (y0 + ym) / 2), t, dir=-90, k=p.sq),
        Knot(pt(cx - 2, y0 + t / 2), t, dir=180),
        cut(x0 - 4, y0 + 0.20 * h, t, 132),
    )


@char("∛")
def cube_root(g: Draw) -> None:
    p = g.p
    radical(g)
    small_three(g, 44, 44 + 150, p.axis + 30 + 60, big_top(p) - 8)


def loop_rise(p: Params) -> float:
    """The outer half-height of the loops of the infinity sign."""
    return 118 + 0.42 * p.op


@char("∞")
def infinity(g: Draw) -> None:
    p = g.p
    x0, x1 = 34.0, p.width - 34.0
    cx, cy = p.mid, p.axis
    ry = loop_rise(p)
    t = p.op
    tc = 0.92 * fine(p)  # thin where the loops cross
    xr, xl = (cx + x1) / 2 + 12, (cx + x0) / 2 - 12
    a = 42.0
    e = 8 * unit(a)
    g.stroke(
        Knot(pt(cx, cy) - e, tc, dir=a),
        Knot(pt(xr, cy + ry - t / 2), t, dir=0, k=p.sq),
        Knot(pt(x1 - t / 2, cy), t, dir=-90, k=p.sq),
        Knot(pt(xr, cy - ry + t / 2), t, dir=180),
        Knot(pt(cx, cy), tc, dir=180 - a),
        Knot(pt(xl, cy + ry - t / 2), t, dir=180, k=p.sq),
        Knot(pt(x0 + t / 2, cy), t, dir=-90, k=p.sq),
        Knot(pt(xl, cy - ry + t / 2), t, dir=0),
        Knot(pt(cx, cy) + e, tc, dir=a),
    )


@char("∝")
def proportional(g: Draw) -> None:
    p = g.p
    x0, x1 = 52.0, p.op_r
    cy = p.axis
    ry = loop_rise(p)
    t = p.op
    tc = 0.92 * fine(p)
    cx = x0 + 0.60 * (x1 - x0)
    xl = (cx + x0) / 2 - 14
    a = 42.0
    g.stroke(
        cut(x1, cy + ry - 0.56 * t, t, 190),
        Knot(pt(cx, cy), tc, dir=180 + a),
        Knot(pt(xl, cy - ry + t / 2), t, dir=180, k=p.sq),
        Knot(pt(x0 + t / 2, cy), t, dir=90, k=p.sq),
        Knot(pt(xl, cy + ry - t / 2), t, dir=0),
        Knot(pt(cx, cy), tc, dir=-a),
        cut(x1, cy - ry + 0.56 * t, t, 10),
    )


# ---------------------------------------------------------------------------------------------------------------
# Equality and its relatives


def struck(g: Draw, rise: float, t: float | None = None) -> None:
    """The slash through a relation that reaches ``rise`` above and below the axis: it passes through all of it."""
    p = g.p
    dy = rise + 0.9 * p.op
    strike(g, p.mid, p.axis, 0.42 * dy, dy, t)


@char("≠")
def notequal(g: Draw) -> None:
    p = g.p
    g.use("=")
    struck(g, equal_pitch(p) / 2 + p.op / 2)


def triple_pitch(p: Params) -> float:
    """The distance between the centre lines of the bars of the identity sign, closer than those of =."""
    return 70 + 1.25 * p.op


@char("≡")
def equivalence(g: Draw) -> None:
    p = g.p
    for k in (-1, 0, 1):
        bar(g, p.axis + k * triple_pitch(p))


@char("≢")
def notequivalence(g: Draw) -> None:
    p = g.p
    g.use("≡")
    struck(g, triple_pitch(p) + p.op / 2)


@char("∼")
def tilde_operator(g: Draw) -> None:
    g.use("~")


def twin_wave(p: Params) -> tuple[float, float]:
    """The rise of each wave of the almost-equal sign, and the distance between their centres."""
    return 0.72 * wave_rise(p), 60 + 1.35 * p.op


@char("≈")
def approxequal(g: Draw) -> None:
    p = g.p
    a, pitch = twin_wave(p)
    g.stroke(*wave(p, p.axis + pitch / 2, a))
    g.stroke(*wave(p, p.axis - pitch / 2, a))


@char("≉")
def notapproxequal(g: Draw) -> None:
    p = g.p
    a, pitch = twin_wave(p)
    g.use("≈")
    struck(g, pitch / 2 + a + p.op / 2)


@char("≃")
def asymptotically_equal(g: Draw) -> None:
    p = g.p
    a = 0.85 * wave_rise(p)
    yb, cy = over(p, a + p.op / 2, p.op)
    g.stroke(*wave(p, cy, a))
    bar(g, yb)


@char("≅")
def congruent(g: Draw) -> None:
    p = g.p
    a = 0.80 * wave_rise(p)
    pitch = 0.9 * triple_pitch(p)
    yb, cy = over(p, a + p.op / 2, pitch + p.op)
    g.stroke(*wave(p, cy, a))
    bar(g, yb + pitch / 2)
    bar(g, yb - pitch / 2)


def colon_equal(g: Draw, right: bool = False) -> None:
    p = g.p
    r = 0.80 * p.dot
    d = equal_pitch(p) / 2
    xd = p.op_l - 6 + r
    x0 = xd + r + 0.5 * rel_gap(p)
    for s in (1, -1):
        dot_x, a, b = (p.width - xd, p.op_l, p.width - x0) if right else (xd, x0, p.op_r)
        g.dot(dot_x, p.axis + s * d, r)
        bar(g, p.axis + s * d, a, b)


@char("≔")
def colon_equals(g: Draw) -> None:
    colon_equal(g)


@char("≕")
def equals_colon(g: Draw) -> None:
    colon_equal(g, right=True)


def low_equal(g: Draw) -> float:
    """The equals sign lowered and closed up, to leave room for a mark over it. Returns where the mark may
    start."""
    p = g.p
    pitch = 0.80 * equal_pitch(p)
    y0 = 34 + p.op / 2
    bar(g, y0)
    bar(g, y0 + pitch)
    return y0 + pitch + p.op / 2 + 0.75 * rel_gap(p)


@char("≜")
def delta_equal(g: Draw) -> None:
    p = g.p
    y0 = low_equal(g)
    t = small_stroke(p) * 1.15
    y1 = p.cap + 30
    x0, x1 = p.mid - 170, p.mid + 170
    g.poly(vee(x0, x1, y0, y1, t, 0.5 * t))
    g.stroke(*hbar(x0, x1, y0 + t / 2, t))


@char("≟")
def questioned_equal(g: Draw) -> None:
    p = g.p
    y0 = low_equal(g)
    t = small_stroke(p) * 1.25
    r = 0.62 * p.dot
    y1 = p.cap + 36
    x0, x1 = p.mid - 100, p.mid + 100
    foot = y0 + 2 * r + 0.55 * t + 14
    g.stroke(
        cut(x0, y1 - 0.30 * (y1 - foot), t, 52),
        Knot(pt(p.mid, y1 - t / 2), t, dir=0, k=p.sq),
        Knot(pt(x1 - t / 2, y1 - 0.34 * (y1 - foot)), t, dir=-90),
        Knot(pt(p.mid + 4, foot + 0.24 * (y1 - foot)), t, pen=0, dir=-90, line=True),
        Knot(pt(p.mid + 4, foot), t, pen=0),
    )
    g.dot(p.mid + 4, y0 + r, r)


@char("≝")
def defined_equal(g: Draw) -> None:
    p = g.p
    y0 = low_equal(g)
    t = small_stroke(p)
    y1 = p.cap + 36  # the top of d and f
    xh = y0 + 0.66 * (y1 - y0)  # the top of e and of the bowl of d
    w = 148.0
    k = p.sq
    # d
    a, b = p.op_l - 8, p.op_l - 8 + w
    g.stroke(*ring(a, y0, b - 0.3 * t, xh, t, t, k), closed=True)
    g.stroke(*vstem(b - t / 2, y0, y1, t))
    # e
    a, b = p.mid - w / 2 + 4, p.mid + w / 2 + 2
    ym = (y0 + xh) / 2
    g.stroke(
        Knot(pt(b - t / 2, ym), t, pen=0, dir=90, k=k),
        Knot(pt((a + b) / 2, xh - t / 2), t, dir=180, k=k),
        Knot(pt(a + t / 2, ym), t, dir=-90, k=k),
        Knot(pt((a + b) / 2 + 4, y0 + t / 2), t, dir=0),
        cut(b, y0 + 0.30 * (xh - y0), t, 40),
    )
    g.stroke(*hbar(a + t / 2, b - t / 2, ym, 0.9 * t))
    # f
    a, b = p.op_r + 6 - w + 14, p.op_r + 6
    xs = a + 0.40 * (b - a)
    g.stroke(*elbow(xs, y0, y1, b, t, t, k, 0.42 * (b - a)))
    g.stroke(*hbar(a, b - 10, xh - t / 2, t))


# ---------------------------------------------------------------------------------------------------------------
# Order


@char("≤")
def lessequal(g: Draw) -> None:
    p = g.p
    rise = rel_rise(p)
    yb, cy = over(p, rise, p.op)
    g.poly(chevron(p.op_l, p.op_r, cy, rise, p.op, tip(p)))
    bar(g, yb)


@char("≥")
def greaterequal(g: Draw) -> None:
    p = g.p
    rise = rel_rise(p)
    yb, cy = over(p, rise, p.op)
    g.poly(mirrored(chevron(p.op_l, p.op_r, cy, rise, p.op, tip(p)), p.mid))
    bar(g, yb)


def much(g: Draw, right: bool = False) -> None:
    """Two chevrons, one inside the other, drawn with the fine stroke so that the white between them stays."""
    p = g.p
    t = 1.06 * fine(p)
    w = 0.58 * (p.op_r - p.op_l)
    for x in (p.op_l, p.op_r - w):
        c = chevron(x, x + w, p.axis, chevron_rise(p), t, 0.8 * tip(p))
        g.poly(mirrored(c, p.mid) if right else c)


@char("≪")
def muchless(g: Draw) -> None:
    much(g)


@char("≫")
def muchgreater(g: Draw) -> None:
    much(g, right=True)


def curved_chevron(p: Params, cy: float, rise: float, t: float | None = None) -> list[Knot]:
    """The chevron of the precedes sign: its strokes leave the point as those of < do and curl away from the
    axis, to end in flat cuts ``rise`` above and below ``cy``."""
    t = p.op if t is None else t
    a = 17.0  # half the angle at the point
    b = 62.0  # the direction of the strokes at their ends
    v = pt(p.op_l + (t / 2) / math.sin(math.radians(a)), cy)
    run = 60.0
    top = cut(p.op_r - 0.5 * t / math.sin(math.radians(b)), cy + rise, t, 180 + b, pen=0)
    bot = cut(p.op_r - 0.5 * t / math.sin(math.radians(b)), cy - rise, t, -b, pen=0)
    return [
        top,
        Knot(v + run * unit(a), t, line=True),
        Knot(v, t, line=True),
        Knot(v + run * unit(-a), t),
        bot,
    ]


@char("≺")
def precedes(g: Draw) -> None:
    p = g.p
    g.stroke(*curved_chevron(p, p.axis, chevron_rise(p) + 14))


@char("≻")
def succeeds(g: Draw) -> None:
    p = g.p
    g.stroke(*mirror(curved_chevron(p, p.axis, chevron_rise(p) + 14), p.mid))


def less_similar(g: Draw, right: bool = False) -> None:
    p = g.p
    rise = rel_rise(p)
    a = 0.62 * wave_rise(p)
    yw, cy = over(p, rise, 2 * a + p.op)
    c = chevron(p.op_l, p.op_r, cy, rise, p.op, tip(p))
    g.poly(mirrored(c, p.mid) if right else c)
    g.stroke(*wave(p, yw, a))


@char("≲")
def less_or_similar(g: Draw) -> None:
    less_similar(g)


@char("≳")
def greater_or_similar(g: Draw) -> None:
    less_similar(g, right=True)


# ---------------------------------------------------------------------------------------------------------------
# Divides and parallel


def twin_pitch(p: Params, t: float) -> float:
    """The distance between the centre lines of two parallel upright strokes ``t`` thick."""
    return 92 + 0.95 * t


@char("∣")
def divides(g: Draw) -> None:
    p = g.p
    stem(g, p.mid, 0, stand_top(p))


@char("∤")
def notdivides(g: Draw) -> None:
    p = g.p
    g.use("∣")
    strike(g, p.mid, p.axis, 112, 112, 0.5 * (p.op + fine(p)))


@char("∥")
def parallel(g: Draw) -> None:
    p = g.p
    d = twin_pitch(p, p.op) / 2
    stem(g, p.mid - d, 0, stand_top(p))
    stem(g, p.mid + d, 0, stand_top(p))


@char("∦")
def notparallel(g: Draw) -> None:
    p = g.p
    g.use("∥")
    strike(g, p.mid, p.axis, 150, 132, 0.5 * (p.op + fine(p)))


@char("‖")
def double_bar(g: Draw) -> None:
    p = g.p
    t = 0.9 * p.stem
    d = twin_pitch(p, t) / 2
    stem(g, p.mid - d, p.br_bot, p.br_top, t)
    stem(g, p.mid + d, p.br_bot, p.br_top, t)


# ---------------------------------------------------------------------------------------------------------------
# Logic


def cap_diagonal(p: Params) -> float:
    """The thickness of a capital's full diagonal, as the capitals draw A and V."""
    return p.cap_stem * 0.95


@char("∀")
def forall(g: Draw) -> None:
    p = g.p
    t = cap_diagonal(p)
    x0, x1 = p.sb_round - 30, p.width - p.sb_round + 30
    apex = t * 0.72
    g.poly(vee(x0, x1, p.cap, 0, t, apex))
    y = p.cap * 0.75
    xb = vee_x(x0, x1, p.cap, 0, t, apex, y)
    g.stroke(*hbar(xb, p.width - xb, y, p.cap_hair))


def exists(g: Draw) -> None:
    p = g.p
    x = p.width - (p.cxl + 16)
    left = p.sb_round + 14
    g.stroke(*vstem(x, 0, p.cap, p.cap_stem))
    g.stroke(*hbar(left, x, p.cap - p.cap_hair / 2, p.cap_hair))
    g.stroke(*hbar(left + 40, x, p.cap * 0.52, p.cap_hair))
    g.stroke(*hbar(left - 6, x, p.cap_hair / 2, p.cap_hair))


@char("∃")
def exists_(g: Draw) -> None:
    exists(g)


@char("∄")
def notexists(g: Draw) -> None:
    p = g.p
    exists(g)
    strike(g, p.mid - 14, p.cap / 2, 150, p.cap / 2 + 80)


def wedge(g: Draw, y0: float, y1: float) -> None:
    """The chevron turned: feet on ``y0``, the point on ``y1``."""
    p = g.p
    g.poly(vee(p.op_l, p.op_r, y0, y1, p.op, tip(p)))


@char("∧")
def logicaland(g: Draw) -> None:
    wedge(g, 0, stand_top(g.p))


@char("∨")
def logicalor(g: Draw) -> None:
    wedge(g, stand_top(g.p), 0)


@char("⊻")
def xor(g: Draw) -> None:
    p = g.p
    bar(g, p.op / 2)
    wedge(g, stand_top(p), p.op + rel_gap(p))


@char("⊤")
def down_tack(g: Draw) -> None:
    p = g.p
    bar(g, p.cap - p.op / 2)
    stem(g, p.mid, 0, p.cap)


@char("⊥")
def up_tack(g: Draw) -> None:
    p = g.p
    bar(g, p.op / 2)
    stem(g, p.mid, 0, p.cap)


def tack(g: Draw, bars: int = 1, stems: int = 1, right: bool = False) -> None:
    """The turnstile: stems at the left end of the span, bars from them to its right end."""
    p = g.p
    h = half_span(p)
    pitch = twin_pitch(p, p.op) * 0.88
    strokes = [vstem(p.op_l + p.op / 2 + i * pitch, p.axis - h, p.axis + h, p.op) for i in range(stems)]
    x0 = p.op_l + p.op / 2 + (stems - 1) * pitch
    d = equal_pitch(p) / 2
    for y in [p.axis] if bars == 1 else [p.axis + d, p.axis - d]:
        strokes.append(hbar(x0, p.op_r, y, p.op))
    for s in strokes:
        g.stroke(*(mirror(s, p.mid) if right else s))


@char("⊢")
def right_tack(g: Draw) -> None:
    tack(g)


@char("⊣")
def left_tack(g: Draw) -> None:
    tack(g, right=True)


@char("⊨")
def models(g: Draw) -> None:
    tack(g, bars=2)


@char("⊩")
def forces(g: Draw) -> None:
    tack(g, stems=2)


# ---------------------------------------------------------------------------------------------------------------
# Sets


def subset(g: Draw, cy: float, rise: float, right: bool = False, t: float | None = None) -> None:
    p = g.p
    a = arc(p, p.op_l, p.op_r, cy - rise, cy + rise, t)
    g.stroke(*(mirror(a, p.mid) if right else a))


def element(g: Draw, right: bool = False) -> None:
    p = g.p
    subset(g, p.axis, set_rise(p), right)
    b = hbar(p.op_l + p.op / 2, p.op_r, p.axis, 0.92 * p.op)
    g.stroke(*(mirror(b, p.mid) if right else b))


@char("⊂")
def subset_(g: Draw) -> None:
    subset(g, g.p.axis, set_rise(g.p))


@char("⊃")
def superset(g: Draw) -> None:
    subset(g, g.p.axis, set_rise(g.p), right=True)


@char("∈")
def element_(g: Draw) -> None:
    element(g)


@char("∋")
def contains(g: Draw) -> None:
    element(g, right=True)


@char("∉")
def notelement(g: Draw) -> None:
    element(g)
    struck(g, set_rise(g.p))


@char("∌")
def notcontains(g: Draw) -> None:
    element(g, right=True)
    struck(g, set_rise(g.p))


@char("⊄")
def notsubset(g: Draw) -> None:
    subset(g, g.p.axis, set_rise(g.p))
    struck(g, set_rise(g.p))


@char("⊅")
def notsuperset(g: Draw) -> None:
    subset(g, g.p.axis, set_rise(g.p), right=True)
    struck(g, set_rise(g.p))


def subset_equal(g: Draw, right: bool = False) -> tuple[float, float]:
    p = g.p
    rise = rel_rise(p)
    yb, cy = over(p, rise, p.op)
    subset(g, cy, rise, right)
    bar(g, yb)
    return yb, cy + rise


@char("⊆")
def subsetequal(g: Draw) -> None:
    subset_equal(g)


@char("⊇")
def supersetequal(g: Draw) -> None:
    subset_equal(g, right=True)


@char("⊈")
def notsubsetequal(g: Draw) -> None:
    p = g.p
    _, top = subset_equal(g)
    struck(g, top - p.axis)


@char("⊉")
def notsupersetequal(g: Draw) -> None:
    p = g.p
    _, top = subset_equal(g, right=True)
    struck(g, top - p.axis)


def bar_struck(g: Draw, yb: float) -> None:
    """The short slash through the bar alone, of the signs that say 'but not equal'."""
    p = g.p
    d = p.op / 2 + 0.8 * rel_gap(p)
    strike(g, p.mid, yb, 0.62 * d, d, 0.5 * (p.op + fine(p)))


@char("⊊")
def subsetnotequal(g: Draw) -> None:
    yb, _ = subset_equal(g)
    bar_struck(g, yb)


@char("⊋")
def supersetnotequal(g: Draw) -> None:
    yb, _ = subset_equal(g, right=True)
    bar_struck(g, yb)


def cup(g: Draw, down: bool = False) -> None:
    p = g.p
    a = transposed(arc(p, -p.over, stand_top(p), p.op_l, p.op_r))
    g.stroke(*(flip(a, p.axis) if down else a))


@char("∪")
def union(g: Draw) -> None:
    cup(g)


@char("∩")
def intersection(g: Draw) -> None:
    cup(g, down=True)


@char("⊎")
def multiset_union(g: Draw) -> None:
    p = g.p
    cup(g)
    t = fine(p)
    h = 0.42 * half_span(p)
    cy = p.axis + 0.15 * half_span(p)
    g.stroke(*hbar(p.mid - h, p.mid + h, cy, t))
    g.stroke(*vstem(p.mid, cy - h, cy + h, t))


@char("∅")
def emptyset(g: Draw) -> None:
    p = g.p
    ry = 0.5 * (p.xh + 2 * p.over) + 0.1 * p.op
    rx = half_span(p) - 14
    circle(g, p.mid, p.axis, rx, ry)
    dy = ry + 0.9 * p.op
    strike(g, p.mid, p.axis, 0.56 * dy, dy, 0.5 * (p.op + fine(p)))


@char("∖")
def setminus(g: Draw) -> None:
    p = g.p
    h = half_span(p)
    slash(g, p.mid + 0.56 * h, p.axis - h, p.mid - 0.56 * h, p.axis + h, p.op)


def square_cup(g: Draw, down: bool = False) -> None:
    p = g.p
    t = p.op
    xl, xr = p.op_l + t / 2, p.op_r - t / 2
    top = stand_top(p)
    k = [
        Knot(pt(xl, top), t, pen=0, line=True),
        Knot(pt(xl, t / 2), t, line=True),
        Knot(pt(xr, t / 2), t, line=True),
        Knot(pt(xr, top), t, pen=0),
    ]
    g.stroke(*(flip(k, p.axis) if down else k))


@char("⊔")
def square_cup_(g: Draw) -> None:
    square_cup(g)


@char("⊓")
def square_cap(g: Draw) -> None:
    square_cup(g, down=True)


def square_image(g: Draw, cy: float, rise: float, right: bool = False) -> None:
    p = g.p
    t = p.op
    xs = p.op_l + t / 2
    k = [
        Knot(pt(p.op_r, cy + rise - t / 2), t, pen=90, line=True),
        Knot(pt(xs, cy + rise - t / 2), t, line=True),
        Knot(pt(xs, cy - rise + t / 2), t, line=True),
        Knot(pt(p.op_r, cy - rise + t / 2), t, pen=90),
    ]
    g.stroke(*(mirror(k, p.mid) if right else k))


@char("⊏")
def square_image_(g: Draw) -> None:
    square_image(g, g.p.axis, set_rise(g.p))


@char("⊐")
def square_original(g: Draw) -> None:
    square_image(g, g.p.axis, set_rise(g.p), right=True)


def square_image_equal(g: Draw, right: bool = False) -> None:
    p = g.p
    rise = rel_rise(p)
    yb, cy = over(p, rise, p.op)
    square_image(g, cy, rise, right)
    bar(g, yb)


@char("⊑")
def square_image_equal_(g: Draw) -> None:
    square_image_equal(g)


@char("⊒")
def square_original_equal(g: Draw) -> None:
    square_image_equal(g, right=True)


# ---------------------------------------------------------------------------------------------------------------
# Circled and squared operators


def big_ring(g: Draw) -> float:
    """The ring of the circled operators: a little beyond the span, as round shapes are. Returns the radius of
    its inner edge."""
    p = g.p
    r = half_span(p) + p.over
    circle(g, p.mid, p.axis, r)
    return r - p.op


@char("⊕")
def circled_plus(g: Draw) -> None:
    p = g.p
    r = big_ring(g) + 4
    g.stroke(*hbar(p.mid - r, p.mid + r, p.axis, fine(p)))
    g.stroke(*vstem(p.mid, p.axis - r, p.axis + r, fine(p)))


@char("⊖")
def circled_minus(g: Draw) -> None:
    p = g.p
    r = big_ring(g) + 4
    g.stroke(*hbar(p.mid - r, p.mid + r, p.axis, fine(p)))


@char("⊗")
def circled_times(g: Draw) -> None:
    p = g.p
    r = big_ring(g)
    cross(g, p.mid, p.axis, 0.70 * r, fine(p))


@char("⊘")
def circled_slash(g: Draw) -> None:
    p = g.p
    r = big_ring(g)
    strike(g, p.mid, p.axis, 0.70 * r, 0.70 * r, fine(p))


@char("⊙")
def circled_dot(g: Draw) -> None:
    p = g.p
    big_ring(g)
    g.dot(p.mid, p.axis, 0.78 * p.punct)


@char("⊚")
def circled_ring(g: Draw) -> None:
    p = g.p
    r = big_ring(g)
    circle(g, p.mid, p.axis, 0.62 * r, t=0.8 * fine(p))


@char("⊛")
def circled_asterisk(g: Draw) -> None:
    p = g.p
    r = 0.74 * big_ring(g)
    t = 0.8 * fine(p)
    g.stroke(*vstem(p.mid, p.axis - r, p.axis + r, t))
    c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
    for sign in (1, -1):
        g.stroke(*rake(p.mid - r * c, p.axis - sign * r * s, p.mid + r * c, p.axis + sign * r * s, t))


def big_box(g: Draw) -> float:
    """The box of the squared operators: the span, squared on the axis. Returns half its inner width."""
    p = g.p
    h = half_span(p)
    outline(g, box(p.mid - h, p.axis - h, p.mid + h, p.axis + h))
    return h - p.op


@char("⊞")
def squared_plus(g: Draw) -> None:
    p = g.p
    r = big_box(g) + 4
    g.stroke(*hbar(p.mid - r, p.mid + r, p.axis, fine(p)))
    g.stroke(*vstem(p.mid, p.axis - r, p.axis + r, fine(p)))


@char("⊟")
def squared_minus(g: Draw) -> None:
    p = g.p
    r = big_box(g) + 4
    g.stroke(*hbar(p.mid - r, p.mid + r, p.axis, fine(p)))


@char("⊠")
def squared_times(g: Draw) -> None:
    p = g.p
    r = big_box(g)
    cross(g, p.mid, p.axis, r + 4, fine(p))


@char("⊡")
def squared_dot(g: Draw) -> None:
    p = g.p
    big_box(g)
    g.dot(p.mid, p.axis, 0.78 * p.punct)


# ---------------------------------------------------------------------------------------------------------------
# Dots, stars and small shapes


def dots(g: Draw, places: Sequence[tuple[float, float]], r: float | None = None) -> None:
    p = g.p
    r = (0.5 * p.punct + 16) if r is None else r
    for dx, dy in places:
        g.dot(p.mid + dx, p.axis + dy, r)


@char("∴")
def therefore(g: Draw) -> None:
    dots(g, [(0, 150), (-170, -150), (170, -150)], g.p.dot)


@char("∵")
def because(g: Draw) -> None:
    dots(g, [(0, -150), (-170, 150), (170, 150)], g.p.dot)


@char("⋯")
def midline_ellipsis(g: Draw) -> None:
    dots(g, [(-200, 0), (0, 0), (200, 0)])


@char("⋮")
def vertical_ellipsis(g: Draw) -> None:
    dots(g, [(0, -250), (0, 0), (0, 250)])


@char("⋰")
def up_diagonal_ellipsis(g: Draw) -> None:
    dots(g, [(-200, -200), (0, 0), (200, 200)])


@char("⋱")
def down_diagonal_ellipsis(g: Draw) -> None:
    dots(g, [(-200, 200), (0, 0), (200, -200)])


@char("∎")
def end_of_proof(g: Draw) -> None:
    p = g.p
    g.rect(p.mid - 150, 0, p.mid + 150, p.xh)


@char("⋆")
def star_operator(g: Draw) -> None:
    p = g.p
    ro = 190 + 0.3 * p.op
    ri = 0.44 * ro
    c = pt(p.mid, p.axis - 0.05 * ro)
    g.poly([c + (ro if i % 2 == 0 else ri) * unit(90 + 36 * i) for i in range(10)])


@char("⋄")
def diamond_operator(g: Draw) -> None:
    p = g.p
    r = 190 + 0.45 * p.op
    outline(g, [pt(p.mid + r, p.axis), pt(p.mid, p.axis + r), pt(p.mid - r, p.axis), pt(p.mid, p.axis - r)])


def bowtie(g: Draw, left: bool = True, right: bool = True) -> None:
    p = g.p
    t = p.op
    h = chevron_rise(p)
    td = 0.5 * (p.op + fine(p))
    x0, x1 = p.op_l, p.op_r
    w = rake(x0, 0, x1, 2 * h, td)[0].w  # the height of a diagonal's vertical cut
    dy = h - w / 2
    g.stroke(*rake(x0, p.axis - dy, x1, p.axis + dy, td))
    g.stroke(*rake(x0, p.axis + dy, x1, p.axis - dy, td))
    if left:
        stem(g, x0 + t / 2, p.axis - h, p.axis + h, t)
    if right:
        stem(g, x1 - t / 2, p.axis - h, p.axis + h, t)


@char("⋈")
def bowtie_(g: Draw) -> None:
    bowtie(g)


@char("⋉")
def left_semijoin(g: Draw) -> None:
    bowtie(g, right=False)


@char("⋊")
def right_semijoin(g: Draw) -> None:
    bowtie(g, left=False)


def triangle(g: Draw, cy: float, rise: float, right: bool = False) -> None:
    """The outline of a triangle that points left (or right): the chevron closed."""
    p = g.p
    pts = [pt(p.op_l, cy), pt(p.op_r, cy - rise), pt(p.op_r, cy + rise)]
    if right:
        pts = mirrored(pts, p.mid)[::-1]
    outline(g, pts)


@char("⊲")
def normal_subgroup(g: Draw) -> None:
    triangle(g, g.p.axis, chevron_rise(g.p))


@char("⊳")
def contains_normal_subgroup(g: Draw) -> None:
    triangle(g, g.p.axis, chevron_rise(g.p), right=True)


def triangle_equal(g: Draw, right: bool = False) -> None:
    p = g.p
    rise = rel_rise(p)
    yb, cy = over(p, rise, p.op)
    triangle(g, cy, rise, right)
    bar(g, yb)


@char("⊴")
def normal_subgroup_equal(g: Draw) -> None:
    triangle_equal(g)


@char("⊵")
def contains_normal_subgroup_equal(g: Draw) -> None:
    triangle_equal(g, right=True)
