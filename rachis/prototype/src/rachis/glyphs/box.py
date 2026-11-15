"""Box drawing, block elements, braille patterns and the Powerline symbols.

These glyphs are placed by arithmetic. Each is drawn in its cell (x from 0 to the advance, y from the bottom of the
line to its top) so that it meets the glyph in the next cell and on the next line exactly. None of them slants in
the italic.

No contour here overlaps another. A rasteriser that sums the areas of contours (FreeType does) counts an overlap
twice, which darkens the pixel in the corner of a junction, so every junction is drawn as the outline of the union
of its arms.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import NamedTuple

from rachis.geom import Cubic, Line, pt
from rachis.glyph import Draw, Knot, glyph
from rachis.names import name_of
from rachis.params import Params
from rachis.parts import flip, mirror
from rachis.pen import Contour

Rect = tuple[float, float, float, float]  # x0, y0, x1, y1

# ---------------------------------------------------------------------------------------------------------------
# The cell and the lines


class Cell(NamedTuple):
    """The rectangle a glyph of this module fills or runs across, and its centre."""

    x0: float
    y0: float
    x1: float
    y1: float
    cx: float
    cy: float

    @property
    def w(self) -> float:
        return self.x1 - self.x0

    @property
    def h(self) -> float:
        return self.y1 - self.y0

    def part(self, fx0: float, fy0: float, fx1: float, fy1: float) -> Rect:
        """The rectangle between the given fractions of the cell's width and height."""
        return (self.x0 + fx0 * self.w, self.y0 + fy0 * self.h, self.x0 + fx1 * self.w, self.y0 + fy1 * self.h)


def cell(p: Params) -> Cell:
    return Cell(0.0, p.line_bot, p.width, p.line_top, p.width / 2.0, (p.line_top + p.line_bot) / 2.0)


# The clear space between the two lines of a double line. It does not grow with weight: it is as wide as the Bold's
# light line, so the two lines stay apart at every weight, and at 13 px it is 1.4 px in all of them.
DOUBLE_GAP = 110.0

# The clear space between the dashes of a dashed line, along the line: the same for 2, 3 and 4 dashes to the cell,
# and the same in every weight. Half of it lies at each end of the cell, so dashes continue evenly across cells.
DASH_GAP = 80.0

# The radius of the centre line of a rounded corner, as a fraction of half the cell's width.
ARC = 0.5


def light(p: Params) -> float:
    """The thickness of a light line: one operator stroke."""
    return p.op


def heavy(p: Params) -> float:
    """The thickness of a heavy line. It needs no upper limit to stay apart from a double line, which is broader
    by ``DOUBLE_GAP`` at every weight and open in the middle."""
    return 2.0 * p.op


def double_offset(p: Params) -> float:
    """How far the centre line of each line of a double line lies from the centre line of the pair."""
    return (light(p) + DOUBLE_GAP) / 2.0


# ---------------------------------------------------------------------------------------------------------------
# The union of rectangles


def union(rects: Sequence[Rect]) -> list[list[complex]]:
    """The outlines of the union of rectangles: one counter-clockwise list of corners for each connected piece.

    Each outline starts at its lowest corner (the leftmost of those), and the outlines are in the order of those
    corners, so that masters whose rectangles lie in the same order give the same points in the same order. Pieces
    that touch only at a corner stay separate. The shapes of this module enclose no holes.
    """

    def key(v: float) -> float:
        return round(v, 6)

    xs = sorted({key(v) for r in rects for v in (r[0], r[2])})
    ys = sorted({key(v) for r in rects for v in (r[1], r[3])})
    ix = {v: i for i, v in enumerate(xs)}
    iy = {v: j for j, v in enumerate(ys)}
    inside = {
        (i, j)
        for x0, y0, x1, y1 in rects
        for i in range(ix[key(x0)], ix[key(x1)])
        for j in range(iy[key(y0)], iy[key(y1)])
    }
    # every edge between a filled square of the grid and an empty one, directed with the filled one on its left
    leaving: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for i, j in inside:
        for a, b, (di, dj) in (
            ((i, j), (i + 1, j), (0, -1)),
            ((i + 1, j), (i + 1, j + 1), (1, 0)),
            ((i + 1, j + 1), (i, j + 1), (0, 1)),
            ((i, j + 1), (i, j), (-1, 0)),
        ):
            if (i + di, j + dj) not in inside:
                leaving.setdefault(a, []).append(b)

    loops: list[list[complex]] = []
    while leaving:
        start = min(leaving, key=lambda v: (v[1], v[0]))
        path = [start]
        heading = (1, 0)
        while True:
            at = path[-1]
            choices = leaving[at]
            # where two pieces touch at a corner there are two ways on: turn left, which keeps the pieces apart
            left = (at[0] - heading[1], at[1] + heading[0])
            nxt = left if len(choices) > 1 and left in choices else choices[0]
            choices.remove(nxt)
            if not choices:
                del leaving[at]
            heading = (nxt[0] - at[0], nxt[1] - at[1])
            if nxt == start:
                break
            path.append(nxt)
        corners = [
            v
            for k, v in enumerate(path)
            if (v[0] - path[k - 1][0], v[1] - path[k - 1][1])
            != (path[(k + 1) % len(path)][0] - v[0], path[(k + 1) % len(path)][1] - v[1])
        ]
        loop = [pt(xs[i], ys[j]) for i, j in corners]
        area = sum((a.real * b.imag - a.imag * b.real) for a, b in zip(loop, [*loop[1:], loop[0]], strict=True))
        if area <= 0:
            raise ValueError("the union of these rectangles encloses a hole")
        loops.append(loop)
    return loops


def fill(g: Draw, rects: Sequence[Rect]) -> None:
    """Add the union of ``rects`` to the glyph."""
    for loop in union(rects):
        g.poly(loop)


def upright(cp: int) -> Callable[[Callable[[Draw], None]], Callable[[Draw], None]]:
    """Register the glyph of one character of this module: it keeps out of the italic's slant."""
    return glyph(name_of(cp), cp, upright=True)


# ---------------------------------------------------------------------------------------------------------------
# Box drawing: lines, corners, tees and crosses

# The arms of each character, as its Unicode name states them: left, right, up, down. An arm is absent (.), light
# (l; the names of the double set call it single), heavy (h) or double (d). A key is the first code point of a run
# of consecutive characters.
ARMS = {
    0x2500: "ll.. hh.. ..ll ..hh",  # ─ ━ │ ┃
    0x250C: ".l.l .h.l .l.h .h.h l..l h..l l..h h..h",  # ┌ ┍ ┎ ┏ ┐ ┑ ┒ ┓
    0x2514: ".ll. .hl. .lh. .hh. l.l. h.l. l.h. h.h.",  # └ ┕ ┖ ┗ ┘ ┙ ┚ ┛
    0x251C: ".lll .hll .lhl .llh .lhh .hhl .hlh .hhh",  # ├ ┝ ┞ ┟ ┠ ┡ ┢ ┣
    0x2524: "l.ll h.ll l.hl l.lh l.hh h.hl h.lh h.hh",  # ┤ ┥ ┦ ┧ ┨ ┩ ┪ ┫
    0x252C: "ll.l hl.l lh.l hh.l ll.h hl.h lh.h hh.h",  # ┬ ┭ ┮ ┯ ┰ ┱ ┲ ┳
    0x2534: "lll. hll. lhl. hhl. llh. hlh. lhh. hhh.",  # ┴ ┵ ┶ ┷ ┸ ┹ ┺ ┻
    0x253C: "llll hlll lhll hhll llhl lllh llhh hlhl",  # ┼ ┽ ┾ ┿ ╀ ╁ ╂ ╃
    0x2544: "lhhl hllh lhlh hhhl hhlh hlhh lhhh hhhh",  # ╄ ╅ ╆ ╇ ╈ ╉ ╊ ╋
    0x2550: "dd.. ..dd .d.l .l.d .d.d d..l l..d d..d",  # ═ ║ ╒ ╓ ╔ ╕ ╖ ╗
    0x2558: ".dl. .ld. .dd. d.l. l.d. d.d. .dll .ldd",  # ╘ ╙ ╚ ╛ ╜ ╝ ╞ ╟
    0x2560: ".ddd d.ll l.dd d.dd dd.l ll.d dd.d ddl.",  # ╠ ╡ ╢ ╣ ╤ ╥ ╦ ╧
    0x2568: "lld. ddd. ddll lldd dddd",  # ╨ ╩ ╪ ╫ ╬
    0x2574: "l... ..l. .l.. ...l h... ..h. .h.. ...h",  # ╴ ╵ ╶ ╷ ╸ ╹ ╺ ╻
    0x257C: "lh.. ..lh hl.. ..hl",  # ╼ ╽ ╾ ╿
}

_RANK = ".lhd"


def strips(p: Params, style: str) -> list[tuple[float, float]]:
    """The lines of an arm: for each, its centre line's offset from the cell's centre line, and its thickness."""
    if style == "l":
        return [(0.0, light(p))]
    if style == "h":
        return [(0.0, heavy(p))]
    if style == "d":
        return [(-double_offset(p), light(p)), (double_offset(p), light(p))]
    return []


def breadth(p: Params, style: str) -> float:
    """From an arm's centre line to its outer edge."""
    return {"l": light(p) / 2.0, "h": heavy(p) / 2.0, "d": double_offset(p) + light(p) / 2.0}.get(style, 0.0)


def past_centre(p: Params, style: str, offset: float, opposite: str, low: str, high: str) -> float:
    """How far past the centre of the cell one line of an arm runs; negative when it stops short of the centre.

    ``low`` and ``high`` are the arms that cross this one, on the side of negative and of positive offsets.

    A light or heavy line runs to the far side of the line it meets, so that a corner is square and a tee has no
    notch; with nothing to meet, it stops at the centre. The outer line of a double corner does the same, and its
    inner line stops inside the inner line of the other arm. A single line that meets a double line across its
    path stops inside the nearer of the two lines, unless it goes on from the other side.
    """
    inner = double_offset(p) - light(p) / 2.0  # from the centre to the inner edge of a double arm's line
    if style != "d":
        doubles = (low == "d") + (high == "d")
        if doubles == 2:
            return 0.0 if opposite != "." else -inner
        return breadth(p, max(low, high, key=_RANK.index))
    near, far = (low, high) if offset < 0 else (high, low)
    if near == "d":
        return -inner
    return breadth(p, near if near != "." else far)


def arm_rects(p: Params, arms: str) -> list[Rect]:
    """A rectangle for each line of each arm, from the cell's edge to where the line ends."""
    c = cell(p)
    left, right, up, down = arms
    if "h" in arms and "d" in arms:
        raise ValueError("no character joins a heavy line to a double one")
    rects: list[Rect] = []
    for style, opposite, towards_origin in ((left, right, True), (right, left, False)):
        for offset, t in strips(p, style):
            reach = past_centre(p, style, offset, opposite, down, up)
            xa, xb = (c.x0, c.cx + reach) if towards_origin else (c.cx - reach, c.x1)
            rects.append((xa, c.cy + offset - t / 2.0, xb, c.cy + offset + t / 2.0))
    for style, opposite, towards_origin in ((down, up, True), (up, down, False)):
        for offset, t in strips(p, style):
            reach = past_centre(p, style, offset, opposite, left, right)
            ya, yb = (c.y0, c.cy + reach) if towards_origin else (c.cy - reach, c.y1)
            rects.append((c.cx + offset - t / 2.0, ya, c.cx + offset + t / 2.0, yb))
    return rects


def _junction(cp: int, arms: str) -> None:
    @upright(cp)
    def program(g: Draw) -> None:
        fill(g, arm_rects(g.p, arms))


for _first, _row in ARMS.items():
    for _k, _arms in enumerate(_row.split()):
        _junction(_first + _k, _arms)


# ---------------------------------------------------------------------------------------------------------------
# Box drawing: dashed lines, rounded corners, diagonals

# code point: dashes to the cell, weight, horizontal
DASHED = {
    0x2504: (3, "l", True),  # ┄
    0x2505: (3, "h", True),  # ┅
    0x2506: (3, "l", False),  # ┆
    0x2507: (3, "h", False),  # ┇
    0x2508: (4, "l", True),  # ┈
    0x2509: (4, "h", True),  # ┉
    0x250A: (4, "l", False),  # ┊
    0x250B: (4, "h", False),  # ┋
    0x254C: (2, "l", True),  # ╌
    0x254D: (2, "h", True),  # ╍
    0x254E: (2, "l", False),  # ╎
    0x254F: (2, "h", False),  # ╏
}


def _dashed(cp: int, count: int, style: str, horizontal: bool) -> None:
    @upright(cp)
    def program(g: Draw) -> None:
        c = cell(g.p)
        t = breadth(g.p, style)
        period = (c.w if horizontal else c.h) / count
        for k in range(count):
            a, b = k * period + DASH_GAP / 2.0, (k + 1) * period - DASH_GAP / 2.0
            if horizontal:
                g.rect(c.x0 + a, c.cy - t, c.x0 + b, c.cy + t)
            else:
                g.rect(c.cx - t, c.y0 + a, c.cx + t, c.y0 + b)


for _cp, _spec in DASHED.items():
    _dashed(_cp, *_spec)


def arc_knots(p: Params) -> list[Knot]:
    """The rounded corner that joins the arm going down to the arm going right (╭): a light line up the centre
    of the cell, a quarter turn of the typeface's own elbow, and a light line to the right edge."""
    c = cell(p)
    t = light(p)
    r = ARC * c.w / 2.0
    return [
        Knot(pt(c.cx, c.y0), t, pen=0, line=True),
        Knot(pt(c.cx, c.cy - r), t, pen=0, dir=90, k=p.sq),
        Knot(pt(c.cx + r, c.cy), t, pen=90, dir=0, line=True),
        Knot(pt(c.x1, c.cy), t, pen=90),
    ]


@upright(0x256D)  # ╭ arc down and right
def arc_down_right(g: Draw) -> None:
    g.stroke(*arc_knots(g.p))


@upright(0x256E)  # ╮ arc down and left
def arc_down_left(g: Draw) -> None:
    g.stroke(*mirror(arc_knots(g.p), cell(g.p).cx))


@upright(0x256F)  # ╯ arc up and left
def arc_up_left(g: Draw) -> None:
    c = cell(g.p)
    g.stroke(*flip(mirror(arc_knots(g.p), c.cx), c.cy))


@upright(0x2570)  # ╰ arc up and right
def arc_up_right(g: Draw) -> None:
    g.stroke(*flip(arc_knots(g.p), cell(g.p).cy))


def diagonal_half(p: Params) -> float:
    """Half the breadth, measured along the cell's top edge, of a light line from corner to corner of the cell."""
    c = cell(p)
    return light(p) * math.hypot(c.w, c.h) / c.h / 2.0


@upright(0x2571)  # ╱ diagonal from the lower left corner to the upper right
def diagonal_rising(g: Draw) -> None:
    c = cell(g.p)
    h = diagonal_half(g.p)
    g.poly([pt(c.x0 - h, c.y0), pt(c.x0 + h, c.y0), pt(c.x1 + h, c.y1), pt(c.x1 - h, c.y1)])


@upright(0x2572)  # ╲ diagonal from the upper left corner to the lower right
def diagonal_falling(g: Draw) -> None:
    c = cell(g.p)
    h = diagonal_half(g.p)
    g.poly([pt(c.x1 - h, c.y0), pt(c.x1 + h, c.y0), pt(c.x0 + h, c.y1), pt(c.x0 - h, c.y1)])


@upright(0x2573)  # ╳ both diagonals, as one outline
def diagonal_cross(g: Draw) -> None:
    c = cell(g.p)
    h = diagonal_half(g.p)
    v = h * c.h / c.w  # from the centre to the crotch above and below it
    g.poly(
        [
            pt(c.x0 - h, c.y0),
            pt(c.x0 + h, c.y0),
            pt(c.cx, c.cy - v),
            pt(c.x1 - h, c.y0),
            pt(c.x1 + h, c.y0),
            pt(c.cx + h, c.cy),
            pt(c.x1 + h, c.y1),
            pt(c.x1 - h, c.y1),
            pt(c.cx, c.cy + v),
            pt(c.x0 + h, c.y1),
            pt(c.x0 - h, c.y1),
            pt(c.cx - h, c.cy),
        ]
    )


# ---------------------------------------------------------------------------------------------------------------
# Block elements

_LL, _LR, _UL, _UR = (0.0, 0.0, 0.5, 0.5), (0.5, 0.0, 1.0, 0.5), (0.0, 0.5, 0.5, 1.0), (0.5, 0.5, 1.0, 1.0)

# The parts of the cell each block fills, as fractions of its width and height: x0, y0, x1, y1.
BLOCKS: dict[int, tuple[Rect, ...]] = {
    0x2580: ((0.0, 0.5, 1.0, 1.0),),  # ▀ upper half
    **{0x2580 + k: ((0.0, 0.0, 1.0, k / 8.0),) for k in range(1, 9)},  # ▁ ▂ ▃ ▄ ▅ ▆ ▇ █ lower eighths, full
    **{0x2590 - k: ((0.0, 0.0, k / 8.0, 1.0),) for k in range(1, 8)},  # ▉ ▊ ▋ ▌ ▍ ▎ ▏ left eighths
    0x2590: ((0.5, 0.0, 1.0, 1.0),),  # ▐ right half
    0x2594: ((0.0, 0.875, 1.0, 1.0),),  # ▔ upper eighth
    0x2595: ((0.875, 0.0, 1.0, 1.0),),  # ▕ right eighth
    0x2596: (_LL,),  # ▖
    0x2597: (_LR,),  # ▗
    0x2598: (_UL,),  # ▘
    0x2599: (_UL, _LL, _LR),  # ▙
    0x259A: (_UL, _LR),  # ▚
    0x259B: (_UL, _UR, _LL),  # ▛
    0x259C: (_UL, _UR, _LR),  # ▜
    0x259D: (_UR,),  # ▝
    0x259E: (_UR, _LL),  # ▞
    0x259F: (_UR, _LL, _LR),  # ▟
}


def _block(cp: int, parts: tuple[Rect, ...]) -> None:
    @upright(cp)
    def program(g: Draw) -> None:
        c = cell(g.p)
        fill(g, [c.part(*f) for f in parts])


for _cp, _parts in BLOCKS.items():
    _block(_cp, _parts)

# Shades. The pattern is a grid of squares SHADE on a side, so fine that at reading sizes it is an even grey, and
# it repeats every two squares both ways: twelve times across the cell and twenty-five times up it, so it goes on
# unbroken into the next cell and the next line.
SHADE = 25.0


def shade_counts(c: Cell) -> tuple[int, int]:
    nx, ny = round(c.w / SHADE), round(c.h / SHADE)
    if nx % 2 or ny % 2 or nx * SHADE != c.w or ny * SHADE != c.h:
        raise ValueError("the shade pattern does not divide the cell")
    return nx, ny


def _square(c: Cell, i: int, j: int) -> Rect:
    return (c.x0 + i * SHADE, c.y0 + j * SHADE, c.x0 + (i + 1) * SHADE, c.y0 + (j + 1) * SHADE)


@upright(0x2591)  # ░ light shade: one square in four
def shade_light(g: Draw) -> None:
    c = cell(g.p)
    nx, ny = shade_counts(c)
    for j in range(0, ny, 2):
        for i in range(0, nx, 2):
            g.rect(*_square(c, i, j))


@upright(0x2592)  # ▒ medium shade: a chequerboard, two squares in four
def shade_medium(g: Draw) -> None:
    c = cell(g.p)
    nx, ny = shade_counts(c)
    for j in range(ny):
        for i in range(j % 2, nx, 2):
            g.rect(*_square(c, i, j))


@upright(0x2593)  # ▓ dark shade: the cell with one square in four cut out of it
def shade_dark(g: Draw) -> None:
    c = cell(g.p)
    nx, ny = shade_counts(c)
    g.rect(c.x0, c.y0, c.x1, c.y1)
    for j in range(1, ny, 2):
        for i in range(1, nx, 2):
            x0, y0, x1, y1 = _square(c, i, j)
            g.add(
                Contour(
                    (
                        Line(pt(x0, y0), pt(x0, y1)),
                        Line(pt(x0, y1), pt(x1, y1)),
                        Line(pt(x1, y1), pt(x1, y0)),
                        Line(pt(x1, y0), pt(x0, y0)),
                    )
                )
            )


# ---------------------------------------------------------------------------------------------------------------
# Braille patterns

# The radius of a braille dot, as a fraction of the period's.
BRAILLE_DOT = 0.9


def braille_pitch(p: Params) -> float:
    """The distance between neighbouring dots, the same across and up.

    Two columns and four rows cannot both continue evenly into the next cell with one pitch: across, the cell
    wants half its width, and up, a quarter of its height. This pitch splits the difference, so that the step
    from one cell to the next is as much too short across as it is too long up (16 and 18 units in 308).
    """
    c = cell(p)
    return 2.0 * round((c.w + c.h) / 12.0)


def braille_centres(p: Params) -> list[complex]:
    """The centres of dots 1 to 8: 1, 2, 3 down the left column, 4, 5, 6 down the right, then 7 and 8 below."""
    c = cell(p)
    d = braille_pitch(p)
    xl, xr = c.cx - d / 2.0, c.cx + d / 2.0
    rows = [c.cy + (1.5 - k) * d for k in range(4)]
    return [
        pt(xl, rows[0]),
        pt(xl, rows[1]),
        pt(xl, rows[2]),
        pt(xr, rows[0]),
        pt(xr, rows[1]),
        pt(xr, rows[2]),
        pt(xl, rows[3]),
        pt(xr, rows[3]),
    ]


def _braille(bits: int) -> None:
    @upright(0x2800 + bits)
    def program(g: Draw) -> None:
        r = BRAILLE_DOT * g.p.punct
        for k, z in enumerate(braille_centres(g.p)):
            if bits >> k & 1:
                g.dot(z.real, z.imag, r)


for _bits in range(256):
    _braille(_bits)


# ---------------------------------------------------------------------------------------------------------------
# Powerline: separators


def _pointing_left(points: Sequence[complex], c: Cell) -> list[complex]:
    return [pt(c.x0 + c.x1 - z.real, z.imag) for z in points]


def arrow_points(c: Cell) -> list[complex]:
    """The triangle that fills the cell's height: flat on the left edge, pointed at the middle of the right."""
    return [pt(c.x0, c.y0), pt(c.x1, c.cy), pt(c.x0, c.y1)]


def chevron_points(p: Params) -> list[complex]:
    """The two sloping sides of that triangle as light lines, cut plumb by the cell's left edge."""
    c = cell(p)
    slope = math.hypot(c.w, c.h / 2.0)
    v = light(p) * slope / c.w  # the line's thickness measured up the cell's edge
    h = light(p) * slope / (c.h / 2.0)  # and measured along the centre line
    return [pt(c.x0, c.y0), pt(c.x1, c.cy), pt(c.x0, c.y1), pt(c.x0, c.y1 - v), pt(c.x1 - h, c.cy), pt(c.x0, c.y0 + v)]


@upright(0xE0B0)
def arrow_right(g: Draw) -> None:
    g.poly(arrow_points(cell(g.p)))


@upright(0xE0B1)
def chevron_right(g: Draw) -> None:
    g.poly(chevron_points(g.p))


@upright(0xE0B2)
def arrow_left(g: Draw) -> None:
    c = cell(g.p)
    g.poly(_pointing_left(arrow_points(c), c))


@upright(0xE0B3)
def chevron_left(g: Draw) -> None:
    g.poly(_pointing_left(chevron_points(g.p), cell(g.p)))


def _half_round(c: Cell, inset: float, k: float) -> tuple[Cubic, Cubic]:
    """Half of the typeface's superellipse, from the cell's lower left corner round by the middle of its right edge
    to the upper left corner, drawn ``inset`` inside the cell."""
    bottom, tip, top = pt(c.x0, c.y0 + inset), pt(c.x1 - inset, c.cy), pt(c.x0, c.y1 - inset)
    rx, ry = tip.real - c.x0, c.cy - bottom.imag
    return (
        Cubic(bottom, bottom + k * rx, tip - 1j * k * ry, tip),
        Cubic(tip, tip + 1j * k * ry, top + k * rx, top),
    )


def round_contour(p: Params, outline: bool, left: bool) -> Contour:
    c = cell(p)
    a, b = _half_round(c, 0.0, p.sq)
    if outline:
        e, f = _half_round(c, light(p), p.sq)
        segs = (a, b, Line(b.p3, f.p3), f.reversed(), e.reversed(), Line(e.p0, a.p0))
    else:
        segs = (a, b, Line(b.p3, a.p0))
    shape = Contour(segs)
    if left:
        shape = shape.mapped(lambda z: pt(c.x0 + c.x1 - z.real, z.imag)).reversed()
    return shape


def _round(cp: int, outline: bool, left: bool) -> None:
    @upright(cp)
    def program(g: Draw) -> None:
        g.add(round_contour(g.p, outline, left))


_round(0xE0B4, outline=False, left=False)
_round(0xE0B5, outline=True, left=False)
_round(0xE0B6, outline=False, left=True)
_round(0xE0B7, outline=True, left=True)
