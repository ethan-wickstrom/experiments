"""Accented Latin: combining marks, spacing accents, precomposed letters and the letters drawn in full.

Three layers. The marks are drawn once, each as a function of a centre and a zone, and registered twice: as the
combining character, sitting over a lowercase letter in the previous cell, and as an unencoded ``.cap`` form,
flattened, sitting over a capital. The precomposed letters are a table from the character to a base and its
marks, derived from Unicode's decompositions, and one loop that registers them as components. The special letters
(æ œ ß ð þ ŋ ...) are drawn in full or built from a base letter and a stroke.

Where a mark attaches is measured on the base letter as it is drawn (``ink``), not copied from the base's
program, so the accents follow when a base letter moves.
"""

from __future__ import annotations

import functools
import itertools
import math
from collections.abc import Callable

from rachis.geom import flatten, pt
from rachis.glyph import REGISTRY, Draw, Knot, Spec, build, char, glyph
from rachis.names import name_of
from rachis.params import Params
from rachis.parts import cut, diag, hbar, ring, vee

# ---------------------------------------------------------------------------------------------------------------
# Measurements of this group. Each is derived from the parameters; those marked (request) stand in for a parameter
# that params.py does not have yet.

MARK_GAP = 70.0  # from the x-height to the bottom of a mark above a lowercase letter
MARK_H = 184.0  # the height of the tall marks (acute, circumflex, caron) above a lowercase letter
CAP_GAP = 54.0  # from the cap height to the bottom of a mark above a capital
CAP_SCALE = 0.8  # marks above capitals are this much as tall
BELOW_GAP = 56.0  # from the baseline down to a detached mark below
PREV = -300.0  # a combining mark is drawn over the middle of the previous cell


def mark_t(p: Params) -> float:
    """The stroke of an accent. It is about the hairline in the Regular and gains weight more slowly, so that a
    chevron or a ring keeps its counter in the Bold. (request)"""
    return 28.0 + 0.58 * p.hair


def slope(p: Params) -> float:
    return math.tan(math.radians(p.slant))


# ---------------------------------------------------------------------------------------------------------------
# Measuring a base letter: where its ink is, in upright coordinates


@functools.cache
def _polylines(spec: Spec, p: Params) -> tuple[tuple[complex, ...], ...]:
    """The outline of a glyph in the master ``p`` as closed polylines, components resolved, with the italic's shear
    undone."""
    g = build(spec, p)
    k = 0.0 if spec.upright else slope(p)
    out: list[tuple[complex, ...]] = []
    for c in g.contours:
        pts = [c.segs[0].start]
        for s in c.segs:
            pts.extend(flatten(s, 0.5))
        out.append(tuple(complex(z.real - k * (z.imag - p.slant_origin), z.imag) for z in pts))
    for base, off in g.components:
        if base in REGISTRY:
            d = complex(off.real - k * off.imag, off.imag)
            out.extend(tuple(z + d for z in poly) for poly in _polylines(REGISTRY[base], p))
    return tuple(out)


def ink(p: Params, name: str, y: float) -> list[tuple[float, float]]:
    """The stretches of ink of the glyph ``name`` on the horizontal line at height ``y``, from the left, as
    (left edge, right edge). Empty when the glyph is not drawn yet or has no ink there."""
    if len(name) == 1:
        name = name_of(name)
    if name not in REGISTRY:
        return []
    crossings: list[tuple[float, int]] = []
    for poly in _polylines(REGISTRY[name], p):
        for a, b in itertools.pairwise(poly):
            if (a.imag - y) * (b.imag - y) < 0:
                x = a.real + (b.real - a.real) * (y - a.imag) / (b.imag - a.imag)
                crossings.append((x, 1 if b.imag > a.imag else -1))
    crossings.sort()
    spans: list[tuple[float, float]] = []
    winding, start = 0, 0.0
    for x, turn_ in crossings:
        if winding == 0:
            start = x
        winding += turn_
        if winding == 0:
            if spans and start - spans[-1][1] < 1.0:
                spans[-1] = (spans[-1][0], x)
            else:
                spans.append((start, x))
    return spans


def top_of(p: Params, name: str) -> float:
    """The height of the top of the glyph ``name``; the x-height when it is not drawn yet."""
    if len(name) == 1:
        name = name_of(name)
    if name not in REGISTRY:
        return p.xh
    return max(z.imag for poly in _polylines(REGISTRY[name], p) for z in poly)


def stem_of(p: Params, name: str, y: float, which: int, fallback: float) -> float:
    """The centre of one stretch of ink of ``name`` at height ``y``: ``which`` 0 is the leftmost, -1 the rightmost.
    ``fallback`` when the glyph is not drawn yet."""
    spans = ink(p, name, y)
    if not spans:
        return fallback
    x0, x1 = spans[which]
    return (x0 + x1) / 2


def edge_of(p: Params, name: str, y: float, side: int, fallback: float) -> float:
    """The left (``side`` -1) or right (+1) end of the ink of ``name`` at height ``y``."""
    spans = ink(p, name, y)
    if not spans:
        return fallback
    return spans[0][0] if side < 0 else spans[-1][1]


def dot_center(p: Params) -> float:
    """The height of the centre of the dot of i, measured on i, so that every dot above agrees with it."""
    return top_of(p, "i") - p.dot if "i" in REGISTRY else p.xh + p.xh / 6 + p.dot


# ---------------------------------------------------------------------------------------------------------------
# The shapes of the marks. Each draws itself centred on ``cx`` in a zone that starts at ``y0`` and is ``s`` times
# as tall as the zone over a lowercase letter (1 there, CAP_SCALE over a capital).

Shape = Callable[[Draw, float, float, float], None]


def acute_run(p: Params) -> float:
    """How far the centre line of an acute moves sideways over its height."""
    return 84.0


def grave(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    run = acute_run(p)
    x = cx - 12  # its foot is nearer the letter's middle than its head
    g.stroke(*diag(x + run / 2, y0, x - run / 2, y0 + MARK_H * s, 1.06 * mark_t(p)))


def acute(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    run = acute_run(p)
    x = cx + 12
    g.stroke(*diag(x - run / 2, y0, x + run / 2, y0 + MARK_H * s, 1.06 * mark_t(p)))


def double_acute(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    t = 0.94 * mark_t(p)
    run = 0.84 * acute_run(p)
    h = MARK_H * s
    breadth = t * math.hypot(run, h) / h
    step = breadth + 0.62 * p.hair  # from one stroke to the next
    for x in (cx + 12 - step / 2, cx + 12 + step / 2):
        g.stroke(*diag(x - run / 2, y0, x + run / 2, y0 + h, t))


def chevron_half(p: Params) -> float:
    """Half the width of the circumflex and the caron: it grows with the stroke so that the notch stays open."""
    return 100.0 + 0.9 * mark_t(p)


def circumflex(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    t = mark_t(p)
    half = chevron_half(p)
    g.poly(vee(cx - half, cx + half, y0, y0 + MARK_H * s, t, 0.42 * t))


def caron(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    t = mark_t(p)
    half = chevron_half(p)
    g.poly(vee(cx - half, cx + half, y0 + MARK_H * s, y0, t, 0.42 * t))


def tilde(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    t = mark_t(p)
    a = 124.0 + 0.5 * t  # half its length
    amp = 30.0 * (0.4 + 0.6 * s)  # how far the centre line swings
    cy = y0 + 0.5 * MARK_H * s
    g.stroke(
        cut(cx - a, cy - 0.3 * amp, 0.92 * t, 40),
        Knot(pt(cx - 0.46 * a, cy + amp), t, dir=0),
        Knot(pt(cx + 0.46 * a, cy - amp), t, dir=0),
        cut(cx + a, cy + 0.3 * amp, 0.92 * t, 40),
    )


def macron(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    t = 0.96 * mark_t(p)
    g.stroke(*hbar(cx - 150, cx + 150, y0 + 0.46 * MARK_H * s, t))


def breve(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    t = mark_t(p)
    tip = 0.86 * t
    a = 150.0 - tip / 2
    bot, top = y0 + 0.06 * MARK_H * s, y0 + 0.86 * MARK_H * s
    g.stroke(
        Knot(pt(cx - a, top), tip, pen=0, dir=-90, k=p.sq),
        Knot(pt(cx, bot + t / 2), t, dir=0, k=p.sq),
        Knot(pt(cx + a, top), tip, pen=0, dir=90),
    )


def dot_y(p: Params, y0: float, s: float) -> float:
    """The centre of a dot in a zone: over a lowercase letter it is the dot of i."""
    rise = dot_center(p) - p.dot - p.xh - MARK_GAP  # how far the dot of i floats above the zone's floor
    return y0 + rise * s + p.dot


def dot_above(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    g.dot(cx, dot_y(p, y0, s), p.dot)


def dieresis(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    r = 0.86 * p.dot
    d = 66.0 + 0.58 * r  # from the middle to the centre of each dot
    for x in (cx - d, cx + d):
        g.dot(x, dot_y(p, y0, s), r)


def ring_above(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    hw = 14.0 + 0.42 * p.hair
    sw = 1.1 * hw
    rx = 66.0 + 0.5 * p.hair
    ry = rx * (0.52 + 0.45 * s)
    bot = y0 - 16.0  # a round shape comes nearer the letter than a flat one
    g.stroke(*ring(cx - rx, bot, cx + rx, bot + 2 * ry, sw, hw, p.sq), closed=True)


def comma_mark(g: Draw, cx: float, cy: float, up: bool = False) -> None:
    """A small comma: a dot centred on (cx, cy) and a tail that leaves its right side and falls to the left. With
    ``up`` it is turned half a circle. It is the comma of the punctuation at about half size. (request: a shared
    part)"""
    p = g.p
    r = comma_r(p)
    w0 = 0.92 * r
    sign = -1.0 if up else 1.0
    g.dot(cx, cy, r)
    g.stroke(
        Knot(pt(cx + sign * (r - w0 / 2), cy + sign * 0.10 * r), w0, pen=0, dir=-90 * sign),
        cut(cx - sign * 0.40 * r, cy - sign * comma_drop(p), 0.52 * r, -128 if not up else 52, pen=0),
    )


def comma_r(p: Params) -> float:
    return 0.55 * p.punct


def comma_drop(p: Params) -> float:
    """From the centre of a small comma's dot to the end of its tail."""
    return 1.5 * comma_r(p) + 50.0


def turned_comma_above(g: Draw, cx: float, y0: float, s: float) -> None:
    p = g.p
    comma_mark(g, cx, y0 + comma_r(p), up=True)


# ---------------------------------------------------------------------------------------------------------------
# Combining marks above, and their forms for capitals

ABOVE: dict[str, Shape] = {
    "̀": grave,
    "́": acute,
    "̂": circumflex,
    "̃": tilde,
    "̄": macron,
    "̆": breve,
    "̇": dot_above,
    "̈": dieresis,
    "̊": ring_above,
    "̋": double_acute,
    "̌": caron,
    "̒": turned_comma_above,
}


def cap_name(mark: str) -> str:
    """The glyph name of the form of a mark that sits over a capital."""
    return name_of(mark) + ".cap"


def _register_above(mark: str, shape: Shape) -> None:
    @char(mark, mark=True)
    def lower(g: Draw) -> None:
        p = g.p
        shape(g, PREV, p.xh + MARK_GAP, 1.0)
        g.anchor("_top", PREV, p.xh)

    @glyph(cap_name(mark), mark=True)
    def upper(g: Draw) -> None:
        p = g.p
        shape(g, PREV, p.cap + CAP_GAP, CAP_SCALE)
        g.anchor("_top", PREV, p.cap)


for _mark, _shape in ABOVE.items():
    _register_above(_mark, _shape)
