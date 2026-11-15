"""Punctuation, brackets and common signs.

The marks a reader of code meets most are drawn large and kept apart by outline: the comma is the period with a
tail, the quotes are straight bars while the backtick is a heavy diagonal, and the three kinds of bracket differ in
width as well as in shape. Brackets share one span (``p.br_bot`` to ``p.br_top``) and one stroke.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from rachis.geom import pt, unit
from rachis.glyph import Draw, Knot, char
from rachis.parts import bowl, cut, dbowl, diag, flip, hbar, mirror, ring, turn, vee, vstem

if TYPE_CHECKING:
    from rachis.params import Params

# ---------------------------------------------------------------------------------------------------------------
# Measurements this group derives from the parameters. Each is a candidate for params.py.


def bracket_stem(p: Params) -> float:
    """The vertical stroke of brackets, braces and parentheses: a little lighter than a letter's stem, because a
    bracket is twice as tall as a lowercase letter."""
    return p.stem * 0.92


def quote_bar(p: Params) -> float:
    """The breadth of the straight quotes: slightly more than a stem."""
    return p.stem * 1.14


def small_strokes(p: Params) -> tuple[float, float]:
    """The vertical and horizontal strokes of parts drawn at reduced size (the rings of the per cent sign, the
    letters inside the copyright sign, the ordinals). They are lighter than text strokes and gain weight more
    slowly, so that small counters stay open in the Bold."""
    return 0.435 * p.stem + 30.0, 0.47 * p.hair + 25.0


def dot_y(p: Params) -> float:
    """The centre of a dot that stands on the baseline: round, so it overshoots."""
    return p.punct - p.over


def mark_foot(p: Params) -> float:
    """Where the stroke of ! and ? ends above its dot."""
    return 2 * p.punct - p.over + 96.0


# ---------------------------------------------------------------------------------------------------------------
# Dots and commas


def comma_shape(g: Draw, cx: float, cy: float, scale: float = 1.0, form: str = "9") -> None:
    """A dot centred on (cx, cy) with a tail. ``form`` "9" is the comma and the closing quote (the tail leaves
    the right of the dot and falls to the left); "6" is that turned half a circle (the opening quote); "p" is the
    comma mirrored (the reversed quote)."""
    p = g.p
    r = p.punct * scale
    drop = scale * (1.7 * p.punct + 108.0)  # from the dot's centre down to the end of the tail
    w0 = 0.92 * r
    tail = [
        Knot(pt(cx + 0.97 * r - w0 / 2, cy), w0, pen=0, dir=-90),
        cut(cx - 0.40 * r, cy - drop, 0.54 * r, -128, pen=0),
    ]
    if form == "6":
        tail = turn(tail, cx, cy)
    elif form == "p":
        tail = mirror(tail, cx)
    g.dot(cx, cy, r)
    g.stroke(*tail)


@char(".")
def period(g: Draw) -> None:
    p = g.p
    g.dot(p.mid, dot_y(p), p.punct)


@char(",")
def comma(g: Draw) -> None:
    p = g.p
    comma_shape(g, p.mid, dot_y(p))


@char(":")
def colon(g: Draw) -> None:
    p = g.p
    g.dot(p.mid, dot_y(p), p.punct)
    g.dot(p.mid, p.xh + p.over - p.punct, p.punct)


@char(";")
def semicolon(g: Draw) -> None:
    p = g.p
    comma_shape(g, p.mid, dot_y(p))
    g.dot(p.mid, p.xh + p.over - p.punct, p.punct)


@char("…")
def ellipsis(g: Draw) -> None:
    p = g.p
    r = 0.5 * p.punct + 16.0
    for cx in (p.mid - 200, p.mid, p.mid + 200):
        g.dot(cx, r - p.over, r)


@char("·")
def periodcentered(g: Draw) -> None:
    p = g.p
    g.dot(p.mid, p.axis, 0.78 * p.punct)


@char("•")
def bullet(g: Draw) -> None:
    p = g.p
    g.dot(p.mid, p.axis, 1.5 * p.punct)


@char("‣")
def triangle_bullet(g: Draw) -> None:
    p = g.p
    h = 1.6 * p.punct
    g.poly([pt(p.mid - 0.8 * h, p.axis + h), pt(p.mid - 0.8 * h, p.axis - h), pt(p.mid + 0.9 * h, p.axis)])


# ---------------------------------------------------------------------------------------------------------------
# Exclamation and question


def exclam_knots(p: Params, x: float, scale: float = 1.0) -> list[Knot]:
    w = p.cap_stem * scale
    return [Knot(pt(x, p.cap), 1.12 * w, pen=0, line=True), Knot(pt(x, mark_foot(p)), 0.84 * w, pen=0)]


def question_knots(p: Params, x0: float, x1: float, xs: float, sw: float, hw: float) -> list[Knot]:
    """The hook of the question mark between ``x0`` and ``x1``, ending in a short stem centred on ``xs``."""
    cx = (x0 + x1) / 2
    top = p.cap + p.over - hw / 2
    return [
        cut(x0, p.cap - 0.175 * p.cap, hw * 1.04, 44),
        Knot(pt(cx, top), hw, dir=0, k=p.sq),
        Knot(pt(x1 - sw / 2, p.cap * 0.735), sw, dir=-90),
        Knot(pt(xs, p.cap * 0.455), sw * 0.96, pen=0, dir=-90, line=True),
        Knot(pt(xs, mark_foot(p)), sw * 0.90, pen=0),
    ]


@char("!")
def exclam(g: Draw) -> None:
    p = g.p
    g.stroke(*exclam_knots(p, p.mid))
    g.dot(p.mid, dot_y(p), p.punct)


@char("¡")
def exclamdown(g: Draw) -> None:
    p = g.p
    g.stroke(*flip(exclam_knots(p, p.mid), p.xh / 2))
    g.dot(p.mid, p.xh - dot_y(p), p.punct)


@char("?")
def question(g: Draw) -> None:
    p = g.p
    xs = p.mid + 6
    g.stroke(*question_knots(p, 122, p.width - 116, xs, p.cap_stem, p.cap_hair))
    g.dot(xs, dot_y(p), p.punct)


@char("¿")
def questiondown(g: Draw) -> None:
    p = g.p
    xs = p.mid + 6
    g.stroke(*turn(question_knots(p, 122, p.width - 116, xs, p.cap_stem, p.cap_hair), p.mid, p.xh / 2))
    g.dot(p.width - xs, p.xh - dot_y(p), p.punct)


@char("‼")
def double_exclam(g: Draw) -> None:
    p = g.p
    r = 0.88 * p.punct
    for x in (p.mid - 128, p.mid + 128):
        g.stroke(*exclam_knots(p, x, 0.92))
        g.dot(x, r - p.over, r)


# ---------------------------------------------------------------------------------------------------------------
# Quotes


QUOTE_DROP = 300.0  # the height of the straight quotes


@char("'")
def quotesingle(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.mid, p.asc - QUOTE_DROP, p.asc, quote_bar(p)))


@char('"')
def quotedbl(g: Draw) -> None:
    p = g.p
    w = quote_bar(p) * 0.94
    d = (w + 84.0) / 2
    g.stroke(*vstem(p.mid - d, p.asc - QUOTE_DROP, p.asc, w))
    g.stroke(*vstem(p.mid + d, p.asc - QUOTE_DROP, p.asc, w))


@char("`")
def grave(g: Draw) -> None:
    p = g.p
    g.stroke(*diag(p.mid - 96, p.asc, p.mid + 96, p.asc - 270, p.stem * 1.12))


QUOTE_SCALE = 0.92  # the dot of a curly quote, relative to the period


def _quote_y(p: Params, form: str) -> float:
    """The centre of a curly quote's dot, so that the quote hangs from the ascender."""
    r = p.punct * QUOTE_SCALE
    drop = QUOTE_SCALE * (1.7 * p.punct + 108.0)
    return p.asc - r if form != "6" else p.asc - drop


@char("’")
def quoteright(g: Draw) -> None:
    p = g.p
    comma_shape(g, p.mid, _quote_y(p, "9"), QUOTE_SCALE, "9")


@char("‘")
def quoteleft(g: Draw) -> None:
    p = g.p
    comma_shape(g, p.mid, _quote_y(p, "6"), QUOTE_SCALE, "6")


@char("‛")
def quotereversed(g: Draw) -> None:
    p = g.p
    comma_shape(g, p.mid, _quote_y(p, "p"), QUOTE_SCALE, "p")


@char("‚")
def quotesinglbase(g: Draw) -> None:
    p = g.p
    comma_shape(g, p.mid, dot_y(p))


DQUOTE_SCALE = 0.84


def _double(g: Draw, cy_of: str, form: str) -> None:
    p = g.p
    r = p.punct * DQUOTE_SCALE
    drop = DQUOTE_SCALE * (1.7 * p.punct + 108.0)
    cy = {"top9": p.asc - r, "top6": p.asc - drop, "base": r - p.over}[cy_of]
    d = r + 38.0
    comma_shape(g, p.mid - d, cy, DQUOTE_SCALE, form)
    comma_shape(g, p.mid + d, cy, DQUOTE_SCALE, form)


@char("”")
def quotedblright(g: Draw) -> None:
    _double(g, "top9", "9")


@char("“")
def quotedblleft(g: Draw) -> None:
    _double(g, "top6", "6")


@char("„")
def quotedblbase(g: Draw) -> None:
    _double(g, "base", "9")


@char("′")
def prime(g: Draw) -> None:
    p = g.p
    w = quote_bar(p)
    g.stroke(
        Knot(pt(p.mid + 52, p.asc), 1.1 * w, pen=0, line=True), Knot(pt(p.mid - 52, p.asc - QUOTE_DROP), 0.7 * w, pen=0)
    )


@char("″")
def dblprime(g: Draw) -> None:
    p = g.p
    w = quote_bar(p) * 0.94
    d = (w + 84.0) / 2
    for x in (p.mid - d, p.mid + d):
        g.stroke(
            Knot(pt(x + 48, p.asc), 1.1 * w, pen=0, line=True), Knot(pt(x - 48, p.asc - QUOTE_DROP), 0.7 * w, pen=0)
        )


# ---------------------------------------------------------------------------------------------------------------
# Brackets


def paren_knots(p: Params) -> list[Knot]:
    """The opening parenthesis."""
    bs = bracket_stem(p)
    x_out = 186.0  # the outer edge of the arc at its middle
    x_tip = 478.0  # the right end of the cuts at top and bottom
    te = p.hair * 0.95
    ym = (p.br_top + p.br_bot) / 2
    d = 41.0  # the angle of the arc at its ends, from the horizontal
    tip = cut(0, p.br_top, te, -180 + d, pen=0)
    xe = x_tip - tip.w / 2
    return [
        cut(xe, p.br_top, te, -180 + d, pen=0, k=p.sq),
        Knot(pt(x_out + bs / 2, ym), bs, dir=-90, k=p.sq),
        cut(xe, p.br_bot, te, -d, pen=0),
    ]


@char("(")
def parenleft(g: Draw) -> None:
    g.stroke(*paren_knots(g.p))


@char(")")
def parenright(g: Draw) -> None:
    g.stroke(*mirror(paren_knots(g.p), g.p.mid))


def bracket(g: Draw, right: bool = False) -> None:
    p = g.p
    bs = bracket_stem(p)
    x0 = 252.0 - 0.45 * p.stem  # the outer edge of the stem
    x1 = 458.0 + 0.38 * p.stem  # the end of the arms
    strokes = [
        vstem(x0 + bs / 2, p.br_bot, p.br_top, bs),
        hbar(x0, x1, p.br_top - p.hair / 2, p.hair),
        hbar(x0, x1, p.br_bot + p.hair / 2, p.hair),
    ]
    for s in strokes:
        g.stroke(*(mirror(s, p.mid) if right else s))


@char("[")
def bracketleft(g: Draw) -> None:
    bracket(g)


@char("]")
def bracketright(g: Draw) -> None:
    bracket(g, right=True)


def brace_half(p: Params) -> list[Knot]:
    """The upper half of the opening brace: arm, shoulder, spine, and the turn into the cusp on the axis."""
    bs = bracket_stem(p)
    h = p.hair
    xs = 282.0 + 0.12 * p.stem  # the spine's centre
    x_tip = 140.0 - 0.36 * p.stem  # the point of the cusp
    x_arm = 476.0 + 0.36 * p.stem  # the end of the arm
    yt = p.br_top - h / 2
    r1 = 112.0  # the shoulder's radius on the centre line
    r2 = 104.0  # the radius of the turn into the cusp
    return [
        Knot(pt(x_arm, yt), h, pen=90, line=True),
        Knot(pt(xs + r1, yt), h, pen=90, dir=180, k=p.sq),
        Knot(pt(xs, yt - r1), bs, pen=0, dir=-90, line=True),
        Knot(pt(xs, p.axis + r2), bs, pen=0, dir=-90, k=p.sq),
        Knot(pt(xs - r2, p.axis), h, pen=90, dir=180, line=True),
        Knot(pt(x_tip, p.axis), h * 0.5, pen=90),
    ]


@char("{")
def braceleft(g: Draw) -> None:
    p = g.p
    half = brace_half(p)
    g.stroke(*half)
    g.stroke(*flip(half, p.axis))


@char("}")
def braceright(g: Draw) -> None:
    p = g.p
    half = mirror(brace_half(p), p.mid)
    g.stroke(*half)
    g.stroke(*flip(half, p.axis))


# ---------------------------------------------------------------------------------------------------------------
# Bars and dashes


@char("_")
def underscore(g: Draw) -> None:
    p = g.p
    g.stroke(*hbar(48, p.width - 48, -30 - p.op / 2, p.op))


def dash_weight(p: Params) -> float:
    """The en and em dash are a little lighter than the minus, which is how they differ from it."""
    return p.op * 0.86


@char("‐")
def hyphen_true(g: Draw) -> None:
    p = g.p
    g.stroke(*hbar(p.mid - 145, p.mid + 145, p.axis, p.op))


@char("‑")
def hyphen_nonbreaking(g: Draw) -> None:
    g.use("‐")


@char("–")
def endash(g: Draw) -> None:
    p = g.p
    g.stroke(*hbar(p.mid - 238, p.mid + 238, p.axis, dash_weight(p)))


@char("‒")
def figuredash(g: Draw) -> None:
    g.use("–")


@char("—")
def emdash(g: Draw) -> None:
    p = g.p
    g.stroke(*hbar(0, p.width, p.axis, dash_weight(p)))


@char("―")
def horizontalbar(g: Draw) -> None:
    g.use("—")


@char(" ")
def nbspace(g: Draw) -> None:
    pass


@char("­")
def softhyphen(g: Draw) -> None:
    g.use("-")


# ---------------------------------------------------------------------------------------------------------------
# Signs drawn for the cell


@char("@")
def at(g: Draw) -> None:
    """An open ring whose right side is the stem of a small bowl: three strokes across the cell, not four."""
    p = g.p
    sw, hw = small_strokes(p)
    sw, hw = sw * 1.06, hw * 1.06
    x0, x1 = 34.0, p.width - 34.0
    y0, y1 = p.desc + 60.0, p.cap + p.over
    xr = x1 - sw / 2
    cx = (x0 + x1) / 2
    top, bot = y1 - hw / 2, y0 + hw / 2
    by0, by1 = p.xh * 0.19, p.xh * 0.90  # the inner bowl
    g.stroke(
        Knot(pt(xr, by0), sw, pen=0, line=True),
        Knot(pt(xr, by1 - 20), sw, pen=0, dir=90, k=p.sq),
        Knot(pt(cx + 6, top), hw, dir=180, k=p.sq),
        Knot(pt(x0 + sw / 2, (y0 + y1) / 2), sw, dir=-90, k=p.sq),
        Knot(pt(cx + 10, bot), hw, dir=0),
        cut(x1 - 62, bot + 46, hw * 1.04, 30),
    )
    inner = bowl(p, p.width - xr, p.width - 196.0, by0, by1, stem=sw, hair=hw, branch=0.26)
    g.stroke(*mirror(inner, p.mid))


@char("&")
def ampersand(g: Draw) -> None:
    """One stroke: up the diagonal from the foot, round the upper bowl, down across to the lower bowl and out
    along the arm."""
    p = g.p
    sw, hw = p.cap_stem, p.cap_hair
    top, bot = p.cap + p.over - hw / 2, -p.over + hw / 2
    x0 = p.sb_round - 14  # the lower bowl's left edge
    xa, xb = 150.0, 432.0  # the upper bowl's sides
    us = 0.45 * sw + 44.0  # the upper bowl's stroke: it gains less weight than the stems, to keep its counter
    right = p.width - 34.0  # the right end of the foot and of the arm
    foot = cut(0, 0, sw * 0.92, 129, pen=0)
    arm = cut(0, 0, hw * 1.04, 64, pen=0)
    g.stroke(
        cut(right - foot.w / 2, 0, sw * 0.92, 129, pen=0),
        Knot(pt(xa + us / 2, p.cap * 0.765), us, dir=90, k=p.sq),
        Knot(pt((xa + xb) / 2, top), hw, dir=0, k=p.sq),
        Knot(pt(xb - us / 2, p.cap * 0.765), us, dir=-90),
        Knot(pt(x0 + sw / 2, p.cap * 0.265), sw, dir=-90, k=p.sq),
        Knot(pt(x0 + 208, bot), hw, dir=0),
        cut(right + 6 - arm.w / 2, p.cap * 0.46, hw * 1.04, 64, pen=0),
    )


@char("$")
def dollar(g: Draw) -> None:
    """S with a stroke that emerges above and below it. A stroke through the middle fills the counters at reading
    size and in the Bold."""
    p = g.p
    g.use("S")
    w = p.cap_stem * 0.92
    reach = 96.0
    g.stroke(*vstem(p.mid + 2, p.cap - p.cap_hair / 2, p.cap + reach, w))
    g.stroke(*vstem(p.mid - 2, -reach, p.cap_hair / 2, w))


def percent_ring(p: Params, x0: float, x1: float, y0: float, y1: float, f: float = 1.0) -> list[Knot]:
    sw, hw = small_strokes(p)
    return ring(x0, y0, x1, y1, sw * f, hw * f, p.sq)


@char("%")
def percent(g: Draw) -> None:
    p = g.p
    _, hw = small_strokes(p)
    w, h = 246.0, 308.0
    g.stroke(*percent_ring(p, 22, 22 + w, p.cap + p.over - h, p.cap + p.over), closed=True)
    g.stroke(*percent_ring(p, p.width - 22 - w, p.width - 22, -p.over, -p.over + h), closed=True)
    g.stroke(*diag(112, 0, p.width - 112, p.cap, hw * 1.08))


@char("‰")
def perthousand(g: Draw) -> None:
    p = g.p
    _, hw = small_strokes(p)
    w, h = 190.0, 270.0
    g.stroke(*percent_ring(p, 8, 8 + w, p.cap + p.over - h, p.cap + p.over, 0.84), closed=True)
    g.stroke(*percent_ring(p, p.width - 4 - 2 * w + 6, p.width - 4 - w + 6, -p.over, -p.over + h, 0.84), closed=True)
    g.stroke(*percent_ring(p, p.width - 4 - w, p.width - 4, -p.over, -p.over + h, 0.84), closed=True)
    g.stroke(*diag(84, 0, 330, p.cap, hw * 0.96))


@char("#")
def numbersign(g: Draw) -> None:
    p = g.p
    sw, hw = small_strokes(p)
    sw, hw = sw * 1.1, hw * 1.1
    dx, dy = 108.0, 122.0
    for x in (p.mid - dx, p.mid + dx):
        g.stroke(*vstem(x, p.axis - 350, p.axis + 350, sw))
    for y in (p.axis - dy, p.axis + dy):
        g.stroke(*hbar(36, p.width - 36, y, hw))


@char("⁇")
def double_question(g: Draw) -> None:
    p = g.p
    sw, hw = small_strokes(p)
    r = 0.80 * p.punct
    for x0 in (22.0, p.mid + 14.0):
        xs = x0 + 150.0
        g.stroke(*question_knots(p, x0, x0 + 264.0, xs, sw * 1.12, hw * 1.12))
        g.dot(xs, r - p.over, r)


@char("¦")
def brokenbar(g: Draw) -> None:
    p = g.p
    gap = 80.0 + 0.5 * p.op  # the break, about the axis
    g.stroke(*vstem(p.mid, p.br_bot, p.axis - gap / 2, p.op))
    g.stroke(*vstem(p.mid, p.axis + gap / 2, p.br_top, p.op))


# ---------------------------------------------------------------------------------------------------------------
# Guillemets


def chevron(x_tip: float, x_end: float, yc: float, hh: float, t: float, flat: float) -> list[complex]:
    """The polygon of a chevron lying on its side: its point at ``x_tip``, its arms ``t`` thick and cut
    horizontally at ``yc - hh`` and ``yc + hh`` with their far corners at ``x_end``, its point cut plumb,
    ``flat`` tall."""
    s = 1.0 if x_end > x_tip else -1.0
    width = abs(x_end - x_tip)
    b = t  # the breadth of an arm along its horizontal cut
    for _ in range(24):
        b = t * math.hypot(width - b, hh) / hh
    run = width - b
    e = (flat / 2) * run / hh
    return [
        pt(x_tip + s * e, yc + flat / 2),
        pt(x_tip + s * run, yc + hh),
        pt(x_tip + s * width, yc + hh),
        pt(x_tip + s * b, yc),
        pt(x_tip + s * width, yc - hh),
        pt(x_tip + s * run, yc - hh),
        pt(x_tip + s * e, yc - flat / 2),
    ]


def guillemets(g: Draw, tips: tuple[float, ...], right: bool) -> None:
    p = g.p
    t = p.stem * 0.84
    for x in tips:
        pts = chevron(x, x + 214.0, p.xh / 2, 190.0, t, p.stem / 3)
        g.poly([pt(p.width - z.real, z.imag) for z in pts] if right else pts)


@char("‹")
def guilsinglleft(g: Draw) -> None:
    guillemets(g, (g.p.mid - 114.0,), False)


@char("›")
def guilsinglright(g: Draw) -> None:
    guillemets(g, (g.p.mid - 114.0,), True)


@char("«")
def guillemotleft(g: Draw) -> None:
    guillemets(g, (72.0, 286.0), False)


@char("»")
def guillemotright(g: Draw) -> None:
    guillemets(g, (72.0, 286.0), True)


# ---------------------------------------------------------------------------------------------------------------
# Reference marks

MARK_BOT = -110.0  # how far the dagger, section and paragraph signs go below the baseline


@char("†")
def dagger(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.mid, MARK_BOT, p.cap, p.cap_stem))
    g.stroke(*hbar(p.mid - 196, p.mid + 196, p.cap * 0.66, p.cap_hair))


@char("‡")
def daggerdbl(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.mid, MARK_BOT, p.cap, p.cap_stem))
    g.stroke(*hbar(p.mid - 196, p.mid + 196, p.cap * 0.66, p.cap_hair))
    g.stroke(*hbar(p.mid - 196, p.mid + 196, p.cap + MARK_BOT - p.cap * 0.66, p.cap_hair))


def section_half(p: Params, x0: float, x1: float, y0: float, y1: float, sw: float, hw: float) -> list[Knot]:
    """The upper stroke of the section sign in the box (x0, y0)-(x1, y1): the top half of an S, its spine, and a
    lower bowl that turns back to run into the spine of the stroke below, a third of the box lower."""
    cx = (x0 + x1) / 2
    hgt = y1 - y0
    h = hgt / 1.5  # the height of one S: two of them overlap by half
    ys = y1 - h  # the foot of this S
    spine = -30.0
    back = unit(spine + 180)
    return [
        cut(x1 - 10, y1 - 0.22 * h, hw * 1.04, 140),
        Knot(pt(cx + 4, y1 - hw / 2), hw, dir=180, k=p.sq),
        Knot(pt(x0 + sw / 2, ys + 0.735 * h), sw, dir=-90),
        Knot(pt(cx, ys + 0.50 * h), sw, dir=spine),
        Knot(pt(x1 - sw / 2, ys + 0.275 * h), sw, dir=-90),
        Knot(pt(cx, y0 + 0.50 * h) - 20 * back, sw, dir=spine + 180),
    ]


@char("§")
def section(g: Draw) -> None:
    """Two S forms, one a third of the height above the other. The lower bowl of the upper one and the upper bowl
    of the lower one close the loop in the middle, each ending inside the other's spine."""
    p = g.p
    sw, hw = p.cap_stem * 0.90, p.cap_hair * 0.90
    x0, x1 = 104.0, p.width - 104.0
    y0, y1 = MARK_BOT - p.over, p.cap + p.over
    half = section_half(p, x0, x1, y0, y1, sw, hw)
    g.stroke(*half)
    g.stroke(*turn(half, p.mid, (y0 + y1) / 2))


@char("¶")
def paragraph(g: Draw) -> None:
    """Two stems and a filled bowl: the bowl is a stroke with its counter covered."""
    p = g.p
    sw, hw = p.cap_stem * 0.80, p.cap_hair
    x1, x2 = p.mid + 22.0, p.mid + 22.0 + sw + 78.0  # the stems
    g.stroke(*vstem(x1, MARK_BOT, p.cap, sw))
    g.stroke(*vstem(x2, MARK_BOT, p.cap, sw))
    g.stroke(*hbar(x1, x2 + sw / 2 + 34, p.cap - hw / 2, hw))
    x_edge, yb = 62.0, p.cap * 0.42
    xf = x1 - 96.0
    yt, ybc = p.cap - hw / 2, yb + hw / 2
    xc = x_edge + p.cap_stem / 2
    ym = (yt + ybc) / 2
    side = [
        Knot(pt(x1, yt), hw, pen=90, line=True),
        Knot(pt(xf, yt), hw, pen=90, dir=180, k=p.sq),
        Knot(pt(xc, ym), p.cap_stem, dir=-90, k=p.sq),
        Knot(pt(xf, ybc), hw, pen=90, dir=0, line=True),
        Knot(pt(x1, ybc), hw, pen=90),
    ]
    g.stroke(*side)
    # cover the counter with a polygon whose corners lie on the stroke's centre line
    k = 0.75 * p.sq
    upper = pt(xc, yt) * k + (pt(xf, yt) + pt(xc, ym)) / 2 * (1 - k)
    lower = pt(xc, ybc) * k + (pt(xf, ybc) + pt(xc, ym)) / 2 * (1 - k)
    g.poly([pt(x1, yt), pt(xf, yt), upper, pt(xc, ym), lower, pt(xf, ybc), pt(x1, ybc)])


# ---------------------------------------------------------------------------------------------------------------
# Small letters and the signs that hold them


def small_ring(p: Params, x0: float, x1: float, y0: float, y1: float, f: float = 1.0) -> list[Knot]:
    sw, hw = small_strokes(p)
    return ring(x0, y0, x1, y1, sw * f, hw * f, p.sq)


def small_c(g: Draw, x0: float, x1: float, y0: float, y1: float, f: float = 1.0) -> None:
    p = g.p
    sw, hw = small_strokes(p)
    sw, hw = sw * f, hw * f
    h = y1 - y0
    cx = (x0 + x1) / 2 + 6
    g.stroke(
        cut(x1, y1 - 0.24 * h, hw * 1.04, 140),
        Knot(pt(cx, y1 - hw / 2), hw, dir=180, k=p.sq),
        Knot(pt(x0 + sw / 2, (y0 + y1) / 2), sw, dir=-90, k=p.sq),
        Knot(pt(cx, y0 + hw / 2), hw, dir=0),
        cut(x1, y0 + 0.24 * h, hw * 1.04, 40),
    )


def small_a(g: Draw, x0: float, x1: float, y0: float, y1: float, f: float = 1.0) -> None:
    """A double-storey a in a box, after the lowercase."""
    p = g.p
    sw, hw = small_strokes(p)
    sw, hw = sw * f, hw * f
    h = y1 - y0
    xr = x1 - sw / 2
    top = y1 - hw / 2
    crest = x0 + 0.48 * (xr - x0)
    g.stroke(
        cut(x0 + 16, y1 - 0.21 * h, hw * 1.04, 40),
        Knot(pt(crest, top), hw, dir=0, k=p.sq),
        Knot(pt(xr, top - 0.9 * (xr - crest)), sw, pen=0, dir=-90, line=True),
        Knot(pt(xr, y0), sw, pen=0),
    )
    bt = y0 + 0.59 * h
    bot = y0 + hw / 2
    j = p.join * sw
    bx = x0 + 0.52 * (xr - sw / 2 - x0)
    g.stroke(
        Knot(pt(xr, bt - hw / 2), hw, pen=90, dir=180, line=True),
        Knot(pt(bx + 16, bt - hw / 2), hw, pen=90, dir=180, k=p.sq),
        Knot(pt(x0 + sw / 2, (bt + y0) / 2), sw, dir=-90, k=p.sq),
        Knot(pt(bx, bot), hw, dir=0),
        Knot(pt(xr - sw / 2 + 3, y0 + 0.19 * h) + (j / 2) * unit(52) * -1j, j, dir=52),
    )


def small_R(g: Draw, x0: float, x1: float, y0: float, y1: float, f: float = 1.0) -> None:
    p = g.p
    sw, hw = small_strokes(p)
    sw, hw = sw * f, hw * f
    h = y1 - y0
    x = x0 + sw / 2
    waist = y0 + 0.45 * h
    g.stroke(*vstem(x, y0, y1, sw))
    g.stroke(*dbowl(x, x1 - 6, waist - hw / 2, y1, sw, hw, p.sq, 0.34 * (x1 - x0)))
    leg = diag(0, waist, x1 - 0.55 * sw, y0, sw * 0.96)[1]
    g.stroke(Knot(pt((x0 + x1) / 2, waist), sw * 0.96, line=True), leg)


def small_T(g: Draw, x0: float, x1: float, y0: float, y1: float, f: float = 1.0) -> None:
    p = g.p
    sw, hw = small_strokes(p)
    g.stroke(*vstem((x0 + x1) / 2, y0, y1, sw * f))
    g.stroke(*hbar(x0, x1, y1 - hw * f / 2, hw * f))


def small_M(g: Draw, x0: float, x1: float, y0: float, y1: float, f: float = 1.0) -> None:
    p = g.p
    sw, _ = small_strokes(p)
    sw *= f
    g.stroke(*vstem(x0 + sw / 2, y0, y1, sw))
    g.stroke(*vstem(x1 - sw / 2, y0, y1, sw))
    g.poly(vee(x0, x1, y1, y0 + 0.30 * (y1 - y0), sw * 0.86, sw * 0.7))


def small_N(g: Draw, x0: float, x1: float, y0: float, y1: float, f: float = 1.0) -> None:
    p = g.p
    sw, _ = small_strokes(p)
    sw *= f
    g.stroke(*vstem(x0 + sw / 2, y0, y1, sw))
    g.stroke(*vstem(x1 - sw / 2, y0, y1, sw))
    d = diag(0, y1, 1, y0, sw * 0.92)
    w = d[0].w * math.hypot(x1 - x0 - sw, y1 - y0) / math.hypot(1, y1 - y0)
    g.poly([pt(x0, y1), pt(x0 + w, y1), pt(x1, y0), pt(x1 - w, y0)])


CIRCLED = (16.0, 584.0)  # the sides of the ring of the copyright and registered signs


def _circle(g: Draw) -> tuple[float, float]:
    """The ring of © and ®; returns the height of its centre and its radius."""
    p = g.p
    x0, x1 = CIRCLED
    r = (x1 - x0) / 2
    cy = p.cap / 2
    g.stroke(*small_ring(p, x0, x1, cy - r, cy + r, 0.86), closed=True)
    return cy, r


@char("©")
def copyright(g: Draw) -> None:
    cy, _ = _circle(g)
    small_c(g, 186, 420, cy - 152, cy + 152, 0.92)


@char("®")
def registered(g: Draw) -> None:
    cy, _ = _circle(g)
    small_R(g, 196, 424, cy - 146, cy + 146, 0.92)


@char("™")
def trademark(g: Draw) -> None:
    p = g.p
    y0 = p.cap - 300
    small_T(g, 10, 262, y0, p.cap, 0.92)
    small_M(g, 298, 590, y0, p.cap, 0.92)


ORDINAL = (150.0, 450.0)


def _ordinal_bar(g: Draw) -> float:
    """The bar under an ordinal; returns the height the letter stands on."""
    p = g.p
    _, hw = small_strokes(p)
    y = p.cap - 420.0
    g.stroke(*hbar(ORDINAL[0], ORDINAL[1], y + hw / 2, hw))
    return y + hw + 64.0


@char("º")
def ordmasculine(g: Draw) -> None:
    p = g.p
    y0 = _ordinal_bar(g)
    g.stroke(*small_ring(p, ORDINAL[0] + 6, ORDINAL[1] - 6, y0 - p.over / 2, p.cap + p.over), closed=True)


@char("ª")
def ordfeminine(g: Draw) -> None:
    p = g.p
    y0 = _ordinal_bar(g)
    small_a(g, ORDINAL[0] + 12, ORDINAL[1] - 14, y0, p.cap + p.over)


@char("°")
def degree(g: Draw) -> None:
    p = g.p
    d = 276.0
    g.stroke(*small_ring(p, p.mid - d / 2, p.mid + d / 2, p.cap + p.over - d, p.cap + p.over), closed=True)


@char("№")
def numero(g: Draw) -> None:
    p = g.p
    _, hw = small_strokes(p)
    small_N(g, 22, 318, 0, p.cap, 0.94)
    x0, x1 = 356.0, p.width - 14.0
    g.stroke(*small_ring(p, x0, x1, p.cap + p.over - 300, p.cap + p.over, 0.9), closed=True)
    g.stroke(*hbar(x0 + 8, x1 - 8, p.cap - 392 + hw / 2, hw * 0.9))


# ---------------------------------------------------------------------------------------------------------------
# Currency


@char("¤")
def currency(g: Draw) -> None:
    p = g.p
    _sw, hw = small_strokes(p)
    cy = p.cap / 2
    r = 158.0
    g.stroke(*small_ring(p, p.mid - r, p.mid + r, cy - r, cy + r, 1.08), closed=True)
    a, b = 0.62 * r, 240.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.stroke(*diag(p.mid + sx * a, cy + sy * a, p.mid + sx * b, cy + sy * b, hw * 1.08))


@char("¢")
def cent(g: Draw) -> None:
    p = g.p
    g.use("c")
    w = p.stem * 0.92
    reach = 96.0
    g.stroke(*vstem(p.mid + 8, p.xh - p.hair / 2, p.xh + reach, w))
    g.stroke(*vstem(p.mid + 8, -reach, p.hair / 2, w))


@char("£")
def sterling(g: Draw) -> None:
    p = g.p
    sw, hw = p.cap_stem, p.cap_hair
    x = 232.0
    top = p.cap + p.over - hw / 2
    g.stroke(
        cut(p.width - 82, p.cap - 0.21 * p.cap, hw * 1.04, 136),
        Knot(pt(x + 150, top), hw, dir=180, k=p.sq),
        Knot(pt(x, p.cap - 0.30 * p.cap), sw, pen=0, dir=-90, line=True),
        Knot(pt(x, 0), sw, pen=0),
    )
    g.stroke(*hbar(84, p.width - 76, hw / 2, hw))
    g.stroke(*hbar(92, p.width - 176, p.cap * 0.46, hw))


@char("¥")
def yen(g: Draw) -> None:
    p = g.p
    sw, hw = p.cap_stem, p.cap_hair
    t = sw * 0.94
    yv = p.cap * 0.40  # where the arms meet the stem
    g.poly(vee(34, p.width - 34, p.cap, yv, t, sw))
    g.stroke(*vstem(p.mid, 0, yv + sw, sw))
    for y in (p.cap * 0.40, p.cap * 0.40 - 1.9 * hw):
        g.stroke(*hbar(p.mid - 190, p.mid + 190, y - hw * 0.45, hw * 0.9))


@char("€")
def euro(g: Draw) -> None:
    p = g.p
    sw, hw = p.cap_stem, p.cap_hair
    x0, x1 = 96.0, p.width - 44.0
    cx = (x0 + x1) / 2 + 20
    top, bot = p.cap + p.over - hw / 2, -p.over + hw / 2
    g.stroke(
        cut(x1, p.cap - 0.20 * p.cap, hw * 1.04, 140),
        Knot(pt(cx, top), hw, dir=180, k=p.sq),
        Knot(pt(x0 + sw / 2, p.cap / 2), sw, dir=-90, k=p.sq),
        Knot(pt(cx, bot), hw, dir=0),
        cut(x1 + 4, 0.20 * p.cap, hw * 1.04, 40),
    )
    for y in (p.cap * 0.5 + 0.95 * hw, p.cap * 0.5 - 0.95 * hw):
        g.stroke(*hbar(22, x1 - 150, y, hw * 0.86))
