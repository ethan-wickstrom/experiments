"""Figures: the ten digits, their superior and inferior forms with the signs that accompany them, and the fractions.

Every figure is a construction in a ``Frame``: a box, the strokes to draw with and the overshoot. The full-size
figures, the superiors and the numerators and denominators of the fractions are the same ten constructions in
four frames, each with strokes of its own, so a small figure is drawn for its size and is not a reduced outline.
An inferior is its superior, lowered.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import NamedTuple

from rachis.geom import pt, unit
from rachis.glyph import Draw, Knot, char, glyph
from rachis.params import Params
from rachis.parts import arch, cut, hbar, mirror, ring, turn, vstem

# -- frames -------------------------------------------------------------------------------------------------------


class Frame(NamedTuple):
    """The box a figure is drawn in and the pen it is drawn with. Flat strokes touch ``y0`` and ``y1``; round ones
    pass them by ``over``. A position inside it is a fraction of its width or height (``x``, ``y``)."""

    x0: float
    x1: float
    y0: float
    y1: float
    stem: float  # vertical strokes, and bowls at their sides
    hair: float  # horizontal strokes, and bowls at their top and bottom
    over: float
    sq: float  # squareness of bowls
    join: float  # breadth of a bowl where it leaves a stem, as a fraction of the stem

    @property
    def w(self) -> float:
        return self.x1 - self.x0

    @property
    def h(self) -> float:
        return self.y1 - self.y0

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0

    @property
    def top(self) -> float:
        """The outer edge of a round top."""
        return self.y1 + self.over

    @property
    def bot(self) -> float:
        """The outer edge of a round bottom."""
        return self.y0 - self.over

    def x(self, t: float) -> float:
        return self.x0 + t * self.w

    def y(self, t: float) -> float:
        return self.y0 + t * self.h


# Proportions of the small forms. A superior is SMALL_H of the cap height tall and SMALL_W of a full-size figure
# wide, which is 0.62 of the advance in the Regular. A fraction's digits are narrower, to leave room for its bar.
SMALL_H = 0.56
SMALL_W = 0.92
SMALL_RISE = 40.0  # a superior's top above the cap height, and an inferior's bottom above the descender
FRAC_H = 0.52
FRAC_W = 0.42  # of the advance
FRAC_EDGE = 18.0  # from the cell's side to a fraction's digit
FIG_SQ = 0.02  # figures are a little squarer than the lowercase, as the capitals are
ZERO_SQ = 0.01  # and the zero a little more: a tall narrow ring looks pointed


def small_stem(p: Params) -> float:
    """The vertical stroke of the small forms: about 0.72 of the full-size stroke in the Regular. It gains weight
    more slowly than the text does, so that the Light survives at 13 px and small counters stay open in the Bold."""
    return 0.435 * p.stem + 30.0


def small_hair(p: Params) -> float:
    return 0.47 * p.hair + 25.0


def full(p: Params) -> Frame:
    return Frame(p.fig_sb, p.width - p.fig_sb, 0.0, p.cap, p.cap_stem, p.cap_hair, p.over, p.sq + FIG_SQ, p.join)


def _small(p: Params, x0: float, x1: float, y0: float, y1: float) -> Frame:
    return Frame(x0, x1, y0, y1, small_stem(p), small_hair(p), 0.6 * p.over, p.sq + FIG_SQ, p.join)


def superior(p: Params) -> Frame:
    half = SMALL_W * (p.width / 2.0 - p.fig_sb)
    top = p.cap + SMALL_RISE
    return _small(p, p.mid - half, p.mid + half, top - SMALL_H * p.cap, top)


def inferior_shift(p: Params) -> float:
    """How far an inferior sits below the superior it repeats."""
    return (p.desc + SMALL_RISE) - (p.cap + SMALL_RISE - SMALL_H * p.cap)


def numerator(p: Params) -> Frame:
    top = p.cap + SMALL_RISE
    return _small(p, FRAC_EDGE, FRAC_EDGE + FRAC_W * p.width, top - FRAC_H * p.cap, top)


def denominator(p: Params) -> Frame:
    bottom = p.desc + SMALL_RISE
    return _small(p, p.width - FRAC_EDGE - FRAC_W * p.width, p.width - FRAC_EDGE, bottom, bottom + FRAC_H * p.cap)


# -- parts --------------------------------------------------------------------------------------------------------


def diag_from(
    ax: float, ay: float, bx: float, by: float, t: float, a_side: float = 0.0, b_side: float = 0.0
) -> list[Knot]:
    """``parts.diag`` with an end given by a corner instead of its centre: a straight stroke ``t`` thick from
    height ``ay`` to ``by``, cut flat. ``ax`` is the stroke's left corner at that end when ``a_side`` is -1, its
    right corner when +1 and its centre when 0; likewise ``bx`` and ``b_side``. (The same part as ``bar`` in the
    lowercase: a candidate for parts.py.)"""
    breadth = t
    ca, cb = ax, bx
    for _ in range(12):  # the breadth of the cut depends on the slope, and the slope on the breadth
        ca, cb = ax - a_side * breadth / 2, bx - b_side * breadth / 2
        breadth = t * math.hypot(cb - ca, by - ay) / abs(by - ay)
    return [Knot(pt(ca, ay), breadth, pen=0, line=True), Knot(pt(cb, by), breadth, pen=0)]


# -- the ten constructions ----------------------------------------------------------------------------------------


def draw_zero_ring(g: Draw, f: Frame) -> None:
    g.stroke(*ring(f.x0, f.bot, f.x1, f.top, f.stem, f.hair, f.sq + ZERO_SQ), closed=True)


def draw_zero(g: Draw, f: Frame) -> None:
    """A ring and a slash from lower left to upper right. The slash is the diagonal of the box of the ring's centre
    line, as far as the middle of the ring's corners: it joins the ring from inside and never reaches its outer
    edge. Its breadth follows the counter as well as the pen, so that a bold counter stays open beside it."""
    draw_zero_ring(g, f)
    counter = f.w - 2 * f.stem
    t = 0.50 * f.hair + 0.11 * counter
    m = 0.5 + 0.375 * (f.sq + ZERO_SQ)  # where a superelliptic corner crosses the diagonal of its box
    dx, dy = m * (f.w - f.stem) / 2, m * (f.h + 2 * f.over - f.hair) / 2
    g.stroke(Knot(pt(f.cx - dx, f.cy - dy), t, line=True), Knot(pt(f.cx + dx, f.cy + dy), t))


def draw_zero_dot(g: Draw, f: Frame) -> None:
    draw_zero_ring(g, f)
    rx = 0.92 * f.stem * (f.w - 2 * f.stem) / f.w  # follows the counter, as the slash does
    g.dot(f.cx, f.cy, rx, 1.6 * rx)


def draw_one(g: Draw, f: Frame) -> None:
    """A stem, a diagonal flag cut flat, and a foot on both sides."""
    s, h = f.stem, f.hair
    x = f.cx + 0.04 * f.w
    g.stroke(*vstem(x, f.y0, f.y1, s))
    g.stroke(*hbar(f.x(0.015), f.x(0.985), f.y0 + h / 2, h))
    g.stroke(*diag_from(x + s / 2, f.y1, f.x(0.03), f.y(0.765), h, 1, -1))


def draw_two(g: Draw, f: Frame) -> None:
    """A round top, a straight neck and a flat base."""
    s, h = f.stem, f.hair
    neck = diag_from(f.x(0.60), f.y(0.40), f.x0, f.y0, 0.96 * s, 0, -1)
    g.stroke(
        cut(f.x(0.03), f.y(0.79), h * 1.04, 44),
        Knot(pt(f.x(0.49), f.top - h / 2), h, dir=0, k=f.sq),
        Knot(pt(f.x(0.98) - s / 2, f.y(0.705)), s, dir=-90),
        *neck,
    )
    g.stroke(*hbar(f.x0, f.x1, f.y0 + h / 2, h))


def draw_three(g: Draw, f: Frame) -> None:
    """Two bowls open to the left that share a waist stroke; the upper one is smaller."""
    s, h = f.stem, f.hair
    yw = f.y(0.535)
    top, bot = f.top - h / 2, f.bot + h / 2
    xw, xj = f.x(0.36), f.x(0.52)
    g.stroke(
        cut(f.x(0.05), f.y(0.805), h * 1.04, 42),
        Knot(pt(f.x(0.47), top), h, dir=0, k=f.sq),
        Knot(pt(f.x(0.95) - s / 2, (top + yw) / 2), s, dir=-90, k=f.sq),
        Knot(pt(xj, yw), h, pen=90, dir=180, line=True),
        Knot(pt(xw, yw), h, pen=90),
    )
    g.stroke(
        Knot(pt(xw, yw), h, pen=90, line=True),
        Knot(pt(xj, yw), h, pen=90, dir=0, k=f.sq),
        Knot(pt(f.x1 - s / 2, (yw + bot) / 2), s, dir=-90, k=f.sq),
        Knot(pt(f.x(0.47), bot), h, dir=180),
        cut(f.x(0.0), f.y(0.19), h * 1.04, 138),
    )


def draw_four(g: Draw, f: Frame) -> None:
    """Closed: a diagonal, a bar that runs past the stem, and the stem."""
    s, h = f.stem, f.hair
    xs = f.x(0.90) - s / 2
    yb = f.y(0.225)
    g.stroke(*vstem(xs, f.y0, f.y1, s))
    g.stroke(*hbar(f.x(-0.04), f.x(1.04), yb, h))
    g.stroke(*diag_from(f.x(-0.04), yb - h / 2, xs + s / 2, f.y1, 1.06 * h, -1, 1))


def draw_five(g: Draw, f: Frame) -> None:
    """A flat top, a sharp corner, a short stem, and a bowl that leaves it as an arch."""
    s, h = f.stem, f.hair
    xs = f.x(0.09) + s / 2
    yt = f.y(0.63)  # the bowl's outer top
    branch = f.y(0.47)
    g.stroke(*hbar(xs - s / 2, f.x(0.94), f.y1 - h / 2, h))
    g.stroke(*vstem(xs, branch, f.y1, s))
    j = f.join * s
    spring = 52.0
    g.stroke(
        Knot(pt(xs + s / 2 - 3, branch) + (j / 2) * unit(spring) * 1j, j, dir=spring),
        Knot(pt(f.x(0.52), yt - h / 2), h, dir=0, k=f.sq),
        Knot(pt(f.x1 - s / 2, (yt + f.bot) / 2 - 0.01 * f.h), s, dir=-90, k=f.sq),
        Knot(pt(f.x(0.47), f.bot + h / 2), h, dir=180),
        cut(f.x(-0.01), f.y(0.185), h * 1.04, 140),
    )


def six(f: Frame) -> list[Knot]:
    """The skeleton of 6: from the terminal at the top right down the back, round the bowl and into the back
    again. 9 is the same skeleton turned."""
    s, h = f.stem, f.hair
    yb = f.y(0.62)  # the bowl's outer top
    j = f.join * s
    arrive = 180.0 + 46.0
    end = pt(f.x0 + s - 3, f.y(0.455)) - (j / 2) * unit(arrive) * 1j
    return [
        cut(f.x(0.93), f.y(0.83), h * 1.04, 142),
        Knot(pt(f.x(0.53), f.top - h / 2), h, dir=180, k=f.sq),
        Knot(pt(f.x0 + s / 2, f.y(0.44)), s, dir=-90, k=f.sq),
        Knot(pt(f.x(0.51), f.bot + h / 2), h, dir=0, k=f.sq),
        Knot(pt(f.x1 - s / 2, (yb + f.bot) / 2), s, dir=90, k=f.sq),
        Knot(pt(f.x(0.54), yb - h / 2), h, dir=180),
        Knot(end, j, dir=arrive),
    ]


def draw_six(g: Draw, f: Frame) -> None:
    g.stroke(*six(f))


def draw_seven(g: Draw, f: Frame) -> None:
    """A flat top and a straight leg cut flat."""
    s, h = f.stem, f.hair
    g.stroke(*hbar(f.x0, f.x1, f.y1 - h / 2, h))
    g.stroke(*diag_from(f.x1, f.y1, f.x(0.36), f.y0, 0.96 * s, 1, 0))


def draw_eight(g: Draw, f: Frame) -> None:
    """Two rings that share the stroke at the waist; the upper one is smaller and narrower."""
    s, h = f.stem, f.hair
    yw = f.y(0.535)
    inset = 0.05 * f.w
    g.stroke(*ring(f.x0, f.bot, f.x1, yw + h / 2, s, h, f.sq), closed=True)
    g.stroke(*ring(f.x0 + inset, yw - h / 2, f.x1 - inset, f.top, 0.96 * s, h, f.sq), closed=True)


def draw_nine(g: Draw, f: Frame) -> None:
    g.stroke(*turn(six(f), f.cx, f.cy))


Construction = Callable[[Draw, Frame], None]

DRAW: dict[str, Construction] = {
    "0": draw_zero,
    "1": draw_one,
    "2": draw_two,
    "3": draw_three,
    "4": draw_four,
    "5": draw_five,
    "6": draw_six,
    "7": draw_seven,
    "8": draw_eight,
    "9": draw_nine,
}

# -- the signs and letters that accompany the small figures -------------------------------------------------------

SMALL_SPAN = 0.62  # a small sign's span, as a fraction of the full-size operators' span


def small_axis(p: Params, f: Frame) -> float:
    """The small operators' axis: as far up the small figures as the axis is up the full-size ones."""
    return f.y(p.axis / p.cap)


def small_half_span(p: Params) -> float:
    return SMALL_SPAN * (p.width / 2.0 - p.op_l)


def draw_small_minus(g: Draw, f: Frame) -> None:
    p = g.p
    r = small_half_span(p)
    g.stroke(*hbar(p.mid - r, p.mid + r, small_axis(p, f), f.hair))


def draw_small_plus(g: Draw, f: Frame) -> None:
    p = g.p
    r = small_half_span(p)
    y = small_axis(p, f)
    g.stroke(*hbar(p.mid - r, p.mid + r, y, f.hair))
    g.stroke(*vstem(p.mid, y - r, y + r, f.hair))


def draw_small_equal(g: Draw, f: Frame) -> None:
    p = g.p
    r = small_half_span(p)
    y = small_axis(p, f)
    d = (0.10 * f.h + 1.35 * f.hair) / 2  # half the distance between the bars' centre lines
    g.stroke(*hbar(p.mid - r, p.mid + r, y + d, f.hair))
    g.stroke(*hbar(p.mid - r, p.mid + r, y - d, f.hair))


def small_paren(f: Frame) -> list[Knot]:
    """The opening parenthesis of the small forms: an arc cut flat at its ends, a little taller and deeper than
    the small figures, as the full-size one is than the full-size figures."""
    y_top, y_bot = f.y(1.08), f.y(-0.14)
    te = 0.95 * f.hair
    slope = 41.0  # the angle of the arc at its ends, from the horizontal
    x_tip = f.x(0.80)  # the right end of the cuts
    half_cut = cut(0, 0, te, -180 + slope, pen=0).w / 2
    return [
        cut(x_tip - half_cut, y_top, te, -180 + slope, pen=0, k=f.sq),
        Knot(pt(f.x(0.27) + 0.46 * f.stem, (y_top + y_bot) / 2), 0.92 * f.stem, dir=-90, k=f.sq),
        cut(x_tip - half_cut, y_bot, te, -slope, pen=0),
    ]


def draw_small_parenleft(g: Draw, f: Frame) -> None:
    g.stroke(*small_paren(f))


def draw_small_parenright(g: Draw, f: Frame) -> None:
    g.stroke(*mirror(small_paren(f), f.cx))


def small_xh(p: Params, f: Frame) -> float:
    """The height of a small lowercase letter above the small figures' baseline."""
    return f.h * p.xh / p.cap


def draw_small_n(g: Draw, f: Frame) -> None:
    p = g.p
    s = f.stem
    xh = small_xh(p, f)
    xl, xr = f.x(0.10) + s / 2, f.x(0.90) - s / 2
    g.stroke(*vstem(xl, f.y0, f.y0 + xh, s))
    g.stroke(*arch(p, xl, xr, f.y0 + xh + f.over, f.y0, stem=s, hair=f.hair, branch=f.y0 + 0.68 * xh))


def draw_small_i(g: Draw, f: Frame) -> None:
    p = g.p
    s, h = f.stem, f.hair
    xh = small_xh(p, f)
    x = f.cx + 0.03 * f.w
    r = 0.5 * p.dot + 12.0  # the dot, reduced as the strokes are
    g.stroke(*vstem(x, f.y0, f.y0 + xh, s))
    g.stroke(*hbar(f.x(0.12), x, f.y0 + xh - h / 2, h))
    g.stroke(*hbar(f.x(0.10), f.x(0.90), f.y0 + h / 2, h))
    g.dot(x - 0.25 * s, f.y0 + xh + xh / 6 + r, r)


# -- glyphs -------------------------------------------------------------------------------------------------------


def _figure(digit: str, sup: str, inf: str) -> None:
    draw = DRAW[digit]

    @char(digit)
    def full_size(g: Draw) -> None:
        draw(g, full(g.p))

    _small_pair(draw, sup, inf)


def _small_pair(draw: Construction, sup: str, inf: str | None = None) -> None:
    """A superior form and, where there is one, the inferior that repeats it lower down."""

    @char(sup)
    def superior_form(g: Draw) -> None:
        draw(g, superior(g.p))

    if inf is None:
        return

    @char(inf)
    def inferior_form(g: Draw) -> None:
        g.use(sup, 0.0, inferior_shift(g.p))


for _digit, _sup, _inf in zip("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹", "₀₁₂₃₄₅₆₇₈₉", strict=True):
    _figure(_digit, _sup, _inf)

_small_pair(draw_small_plus, "⁺", "₊")
_small_pair(draw_small_minus, "⁻", "₋")
_small_pair(draw_small_equal, "⁼", "₌")
_small_pair(draw_small_parenleft, "⁽", "₍")
_small_pair(draw_small_parenright, "⁾", "₎")
_small_pair(draw_small_n, "ⁿ")
_small_pair(draw_small_i, "ⁱ")


@glyph("zero.dot")
def zero_dot(g: Draw) -> None:
    draw_zero_dot(g, full(g.p))


@glyph("zero.plain")
def zero_plain(g: Draw) -> None:
    draw_zero_ring(g, full(g.p))


def _fraction(character: str, over: str, under: str) -> None:
    """A small numerator at the top left, a small denominator at the bottom right, and a bar between them."""

    @char(character)
    def fraction(g: Draw) -> None:
        p = g.p
        n, d = numerator(p), denominator(p)
        DRAW[over](g, n)
        DRAW[under](g, d)
        # the bar passes midway between the numerator's lower right corner and the denominator's upper left one
        cx, cy = (n.x1 + d.x0) / 2, (n.y0 + d.y1) / 2
        rise = 0.30 * (n.y1 - d.y0)
        run = rise / math.tan(math.radians(52.0))
        g.stroke(*diag_from(cx - run, cy - rise, cx + run, cy + rise, 0.9 * n.hair))


_fraction("½", "1", "2")
_fraction("¼", "1", "4")
_fraction("¾", "3", "4")
