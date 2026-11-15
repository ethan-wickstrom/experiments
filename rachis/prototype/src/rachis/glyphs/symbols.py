"""Symbols for terminal interfaces: status marks, bullets, geometric shapes, keys and small pictograms.

Every glyph here fills one cell and is registered upright: these are signs, not text, and an italic must not
slant them. They follow one system.

Centre. Centred shapes sit on (p.mid, centre(p)), a little above the operator axis, so that a disc looks centred
beside lowercase and beside capitals and figures.

Size classes. A class is the side of its square. The disc of a class is ROUND times as wide and the diamond
DIAMOND_W by DIAMOND_H, so that the three look the same size side by side; a triangle is TRI_BASE by TRI_DEPTH.
Filled shapes grow a little with weight (``grow``), as the period does. An outlined shape has the outer size of
the filled one and a stroke of ``line(p, cls)``: p.op for the full-size classes, less for the small ones, whose
counters would otherwise close in the Bold.

Strokes. Shapes and keys use p.op. Check marks and crosses use ``mark`` (1.15 p.op) and their heavy variants
``heavy``. Pictograms with several strokes in one cell use ``fine``, which grows more slowly than p.op so that
the Bold stays open.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from rachis.geom import Cubic, Line, intersect, pt, unit
from rachis.glyph import Draw, Knot, char
from rachis.params import Params
from rachis.parts import elbow, hbar, ring, vstem
from rachis.pen import Contour, centerline, polygon, superellipse

Program = Callable[[Draw], None]


def sym(character: str) -> Callable[[Program], Program]:
    """Register a symbol: one character, never slanted."""
    return char(character, upright=True)


# -- the system -------------------------------------------------------------------------------------------------

# Half the side of the square of each class, before ``grow``.
LARGE = 244.0  # ◯ ☐: as large as a cell allows with air around it
FULL = 220.0  # ■ ● ◆ ▲ ▶ and the status marks: the default
MIDDLE = 180.0  # ◼ ◻: Unicode's "medium"
LESSER = 154.0  # ◾ ◽: Unicode's "medium small"
SMALL = 131.0  # ▪ ▫ ◦ ▸ ▾
TINY = 88.0  # ⬝ ⬞

ROUND = 1.10  # a disc is this much wider than the square it has to match
DIAMOND_W = 1.20  # a diamond's width and height, likewise
DIAMOND_H = 1.28
TRI_BASE = 1.14  # a triangle's base and its depth from base to point
TRI_DEPTH = 1.02
TRI_SHIFT = 0.06  # a triangle is moved towards its point by this fraction of its depth, to look centred
POINTER_LEN = 1.22  # a pointer (► ◄) is longer and flatter than a triangle
POINTER_BASE = 0.80


def centre(p: Params) -> float:
    """The height centred shapes are centred on."""
    return p.axis + 12.0


def grow(p: Params) -> float:
    """Filled shapes are a little larger in heavier weights: 0.97 in the Light, 1.00 in the Regular, 1.05 in
    the Bold."""
    return 0.88 + 0.0016 * p.op


def half(p: Params, cls: float) -> float:
    return cls * grow(p)


def line(p: Params, cls: float) -> float:
    """The stroke of an outlined shape of a class. The full-size classes use the operator stroke; smaller ones
    use a stroke that is lighter and grows more slowly, so that the counter survives in the Bold."""
    share = min(1.0, max(0.0, (cls - TINY) / (FULL - TINY)))  # 0 for the tiny class, 1 from the full class up
    return p.op * (0.36 + 0.64 * share) + 24.0 * (1.0 - share)


def mark(p: Params) -> float:
    """The stroke of check marks and crosses."""
    return 1.15 * p.op


def heavy(p: Params) -> float:
    """The stroke of the heavy check marks, crosses and ornaments: 1.5 times ``mark`` in the Regular, relatively
    more in the Light and less in the Bold, where the cell has no room for more."""
    return 0.95 * p.op + 58.0


def fine(p: Params) -> float:
    """The stroke of pictograms that put several strokes in one cell."""
    return 0.55 * p.op + 26.0


# -- parts of this group ----------------------------------------------------------------------------------------


def inset(points: Sequence[complex], d: float) -> list[complex]:
    """The polygon ``points`` (counter-clockwise) with every edge moved inwards by ``d``."""
    n = len(points)
    lines = []
    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        u = (b - a) / abs(b - a)
        lines.append((a + u * 1j * d, u))
    out = []
    for i in range(n):
        q0, u0 = lines[i - 1]
        q1, u1 = lines[i]
        z = intersect(q0, u0, q1, u1)
        assert z is not None
        out.append(z)
    return out


def outline(g: Draw, points: Sequence[complex], t: float) -> None:
    """The polygon ``points`` (counter-clockwise) drawn as an outline ``t`` thick with mitred corners. Its outer
    edge is the polygon itself."""
    g.stroke(*[Knot(z, t, line=True) for z in inset(points, t / 2)], closed=True)


def hole(g: Draw, points: Sequence[complex]) -> None:
    """A polygon cut out of the shape that contains it."""
    g.add(polygon(list(points)).reversed())


def square(cx: float, cy: float, hx: float, hy: float | None = None) -> list[complex]:
    hy = hx if hy is None else hy
    return [pt(cx - hx, cy - hy), pt(cx + hx, cy - hy), pt(cx + hx, cy + hy), pt(cx - hx, cy + hy)]


def diamond(cx: float, cy: float, hx: float, hy: float) -> list[complex]:
    return [pt(cx, cy - hy), pt(cx + hx, cy), pt(cx, cy + hy), pt(cx - hx, cy)]


def triangle(cx: float, cy: float, base: float, depth: float, heading: float) -> list[complex]:
    """An isosceles triangle pointing along ``heading`` (degrees), its bounding box centred on (cx, cy) before
    the optical shift towards the point."""
    d = unit(heading)
    c = pt(cx, cy) + d * depth * TRI_SHIFT
    back = c - d * depth / 2
    return [back - d * 1j * base / 2, c + d * depth / 2, back + d * 1j * base / 2]


def tri(p: Params, cls: float, heading: float) -> list[complex]:
    s = 2 * half(p, cls)
    return triangle(p.mid, centre(p), TRI_BASE * s, TRI_DEPTH * s, heading)


def pointer(p: Params, cls: float, heading: float) -> list[complex]:
    s = 2 * half(p, cls)
    return triangle(p.mid, centre(p), POINTER_BASE * s, POINTER_LEN * s, heading)


def disc(g: Draw, cx: float, cy: float, r: float) -> None:
    g.dot(cx, cy, r, k=g.p.dot_k)


def circle(g: Draw, cx: float, cy: float, r: float, t: float) -> None:
    """A ring ``t`` thick whose outer edge has the radius ``r``."""
    g.stroke(*ring(cx - r, cy - r, cx + r, cy + r, t, t, g.p.dot_k), closed=True)


def sector(g: Draw, cx: float, cy: float, r: float, first: int, count: int) -> None:
    """``count`` quadrants of the disc of radius ``r``, counter-clockwise from the quadrant ``first`` (0 is
    east to north), closed through the centre."""
    k = g.p.dot_k
    c = pt(cx, cy)
    segs: list[Line | Cubic] = []
    for q in range(first, first + count):
        a, b = 1j**q, 1j ** (q + 1)
        segs.append(Cubic(c + r * a, c + r * a + k * r * b, c + r * b + k * r * a, c + r * b))
    if count == 2:
        segs.append(Line(segs[-1].p3, segs[0].p0))
    else:
        segs.extend((Line(segs[-1].p3, c), Line(c, segs[0].p0)))
    g.add(Contour(tuple(segs)).oriented())


def spoke(c: complex, r0: float, r1: float, heading: float, t: float) -> list[complex]:
    """A straight stroke ``t`` thick along ``heading`` from the distance ``r0`` to ``r1`` from ``c``, cut
    square: the arm of a star, an asterisk or a wheel."""
    d = unit(heading)
    n = d * 1j * t / 2
    return [c + d * r0 - n, c + d * r1 - n, c + d * r1 + n, c + d * r0 + n]


def chevron(tip: complex, back: float, rise: float, t: float) -> list[Knot]:
    """An arrow head: two straight strokes ``t`` thick, mitred at ``tip`` (a point on the centre line) and cut
    horizontally at their ends, which lie ``back`` to the right of the tip (negative: to the left) and ``rise``
    above and below it."""
    b = t * math.hypot(back, rise) / abs(rise)
    return [
        Knot(tip + pt(back, rise), b, pen=0, line=True),
        Knot(tip, t, line=True),
        Knot(tip + pt(back, -rise), b, pen=0),
    ]


def path(*points: complex, t: float, ends: float = 90.0, end: float | None = None) -> list[Knot]:
    """A stroke ``t`` thick through ``points`` in straight segments with mitred corners. Its first end is cut
    along ``ends`` (90: plumb, for a stroke that ends horizontal; 0: level) and its last end along ``end``
    (default: the same)."""
    end = ends if end is None else end

    def breadth(a: complex, b: complex, pen: float) -> float:
        d = (b - a) / abs(b - a)
        return t / abs((d * unit(-pen)).imag)

    first = Knot(points[0], breadth(points[0], points[1], ends), pen=ends, line=True)
    last = Knot(points[-1], breadth(points[-2], points[-1], end), pen=end)
    return [first, *[Knot(z, t, line=True) for z in points[1:-1]], last]


def tick(a: complex, low: complex, b: complex, t: float, apex: float) -> list[complex]:
    """The polygon of a check mark or of any V with unequal legs: the outer corners of its two ends are ``a``
    and ``b``, both ends are cut level, the strokes are ``t`` thick, and the vertex is cut flat, ``apex`` wide,
    centred on ``low``."""
    fl, fr = low - apex / 2, low + apex / 2
    ul, ur = (fl - a) / abs(fl - a), (b - fr) / abs(b - fr)
    il, ir = a + ul * 1j * t, fr + ur * 1j * t  # points on the two inner edges
    crotch = intersect(il, ul, ir, ur)
    a_in = intersect(il, ul, a, 1 + 0j)
    b_in = intersect(ir, ur, b, 1 + 0j)
    assert crotch is not None and a_in is not None and b_in is not None
    return [a, fl, fr, b, b_in, crotch, a_in]


def fill(g: Draw, *knots: Knot) -> None:
    """The area enclosed by the closed path through ``knots``."""
    segs, _, _ = centerline(list(knots), closed=True)
    g.add(Contour(tuple(segs)).oriented())


# -- squares ----------------------------------------------------------------------------------------------------


def _black_square(character: str, cls: float) -> None:
    @sym(character)
    def program(g: Draw) -> None:
        p = g.p
        g.poly(square(p.mid, centre(p), half(p, cls)))


def _white_square(character: str, cls: float) -> None:
    @sym(character)
    def program(g: Draw) -> None:
        p = g.p
        outline(g, square(p.mid, centre(p), half(p, cls)), line(p, cls))


for _c, _cls in (("■", FULL), ("◼", MIDDLE), ("◾", LESSER), ("▪", SMALL), ("⬝", TINY)):
    _black_square(_c, _cls)
for _c, _cls in (("□", FULL), ("◻", MIDDLE), ("◽", LESSER), ("▫", SMALL), ("⬞", TINY)):
    _white_square(_c, _cls)


@sym("▢")
def white_square_rounded(g: Draw) -> None:
    p = g.p
    t = p.op
    h = half(p, FULL) - t / 2
    r = 0.52 * h  # the corner's radius on the centre line
    cx, cy = p.mid, centre(p)
    k = p.dot_k
    g.stroke(
        Knot(pt(cx + h, cy - h + r), t, dir=90, line=True),
        Knot(pt(cx + h, cy + h - r), t, dir=90, k=k),
        Knot(pt(cx + h - r, cy + h), t, dir=180, line=True),
        Knot(pt(cx - h + r, cy + h), t, dir=180, k=k),
        Knot(pt(cx - h, cy + h - r), t, dir=-90, line=True),
        Knot(pt(cx - h, cy - h + r), t, dir=-90, k=k),
        Knot(pt(cx - h + r, cy - h), t, dir=0, line=True),
        Knot(pt(cx + h - r, cy - h), t, dir=0, k=k),
        closed=True,
    )


@sym("▣")
def white_square_containing_black(g: Draw) -> None:
    p = g.p
    h = half(p, FULL)
    t = fine(p)
    outline(g, square(p.mid, centre(p), h), t)
    g.poly(square(p.mid, centre(p), 0.50 * (h - t)))


# -- rectangles and parallelograms ------------------------------------------------------------------------------


def _bar_box(p: Params) -> tuple[float, float]:
    """Half the length and half the breadth of the rectangles ▬ ▭ (and, turned, ▮ ▯)."""
    return half(p, LARGE), 0.42 * half(p, FULL)


@sym("▬")
def black_rectangle(g: Draw) -> None:
    p = g.p
    hx, hy = _bar_box(p)
    g.poly(square(p.mid, centre(p), hx, hy))


@sym("▭")
def white_rectangle(g: Draw) -> None:
    p = g.p
    hx, hy = _bar_box(p)
    outline(g, square(p.mid, centre(p), hx, hy), line(p, SMALL))


@sym("▮")
def black_vertical_rectangle(g: Draw) -> None:
    p = g.p
    hy, hx = _bar_box(p)
    g.poly(square(p.mid, centre(p), 1.24 * hx, 1.12 * hy))


@sym("▯")
def white_vertical_rectangle(g: Draw) -> None:
    p = g.p
    hy, hx = _bar_box(p)
    outline(g, square(p.mid, centre(p), 1.24 * hx, 1.12 * hy), line(p, LESSER))


def _parallelogram(p: Params) -> list[complex]:
    hx, hy = half(p, LARGE) + 22, 0.56 * half(p, FULL)
    lean = 0.42 * hy
    cx, cy = p.mid, centre(p)
    return [
        pt(cx - hx, cy - hy),
        pt(cx + hx - 2 * lean, cy - hy),
        pt(cx + hx, cy + hy),
        pt(cx - hx + 2 * lean, cy + hy),
    ]


@sym("▰")
def black_parallelogram(g: Draw) -> None:
    g.poly(_parallelogram(g.p))


@sym("▱")
def white_parallelogram(g: Draw) -> None:
    outline(g, _parallelogram(g.p), line(g.p, SMALL))


# -- triangles and pointers -------------------------------------------------------------------------------------


def _black_triangle(character: str, cls: float, heading: float, shape: Callable = tri) -> None:
    @sym(character)
    def program(g: Draw) -> None:
        g.poly(shape(g.p, cls, heading))


def _white_triangle(character: str, cls: float, heading: float, shape: Callable = tri) -> None:
    @sym(character)
    def program(g: Draw) -> None:
        outline(g, shape(g.p, cls, heading), line(g.p, cls))


for _c, _cls, _h in (
    ("▲", FULL, 90), ("▼", FULL, -90), ("▶", FULL, 0), ("◀", FULL, 180),
    ("▴", SMALL, 90), ("▾", SMALL, -90), ("▸", SMALL, 0), ("◂", SMALL, 180),
):  # fmt: skip
    _black_triangle(_c, _cls, _h)
for _c, _cls, _h in (
    ("△", FULL, 90), ("▽", FULL, -90), ("▷", FULL, 0), ("◁", FULL, 180),
    ("▵", SMALL, 90), ("▿", SMALL, -90), ("▹", SMALL, 0), ("◃", SMALL, 180),
):  # fmt: skip
    _white_triangle(_c, _cls, _h)
_black_triangle("►", FULL, 0, pointer)
_black_triangle("◄", FULL, 180, pointer)
_white_triangle("▻", FULL, 0, pointer)
_white_triangle("◅", FULL, 180, pointer)


def _corner_triangle(character: str, sx: int, sy: int) -> None:
    @sym(character)
    def program(g: Draw) -> None:
        p = g.p
        h = half(p, FULL)
        c = pt(p.mid, centre(p))
        # the right angle is in the corner (sx, sy); the other two corners are its neighbours
        g.poly([c + pt(sx * h, sy * h), c + pt(-sx * h, sy * h), c + pt(sx * h, -sy * h)])


_corner_triangle("◢", 1, -1)
_corner_triangle("◣", -1, -1)
_corner_triangle("◤", -1, 1)
_corner_triangle("◥", 1, 1)


# -- diamonds ---------------------------------------------------------------------------------------------------


def _diamond(p: Params, cls: float = FULL) -> list[complex]:
    h = half(p, cls)
    return diamond(p.mid, centre(p), DIAMOND_W * h, DIAMOND_H * h)


@sym("◆")
def black_diamond(g: Draw) -> None:
    g.poly(_diamond(g.p))


@sym("◇")
def white_diamond(g: Draw) -> None:
    outline(g, _diamond(g.p), g.p.op)


@sym("◈")
def white_diamond_containing_black(g: Draw) -> None:
    p = g.p
    d = _diamond(p)
    t = fine(p)
    outline(g, d, t)
    c = pt(p.mid, centre(p))
    g.poly([c + (z - c) * 0.40 for z in d])


@sym("◊")
def lozenge(g: Draw) -> None:
    p = g.p
    cy = p.cap / 2
    outline(g, diamond(p.mid, cy, 0.86 * half(p, FULL), cy + 3 * p.over), p.op)


# -- circles ----------------------------------------------------------------------------------------------------


def _r(p: Params, cls: float = FULL) -> float:
    return ROUND * half(p, cls)


@sym("●")
def black_circle(g: Draw) -> None:
    p = g.p
    disc(g, p.mid, centre(p), _r(p))


@sym("○")
def white_circle(g: Draw) -> None:
    p = g.p
    circle(g, p.mid, centre(p), _r(p), p.op)


@sym("◯")
def large_circle(g: Draw) -> None:
    p = g.p
    circle(g, p.mid, centre(p), _r(p, LARGE), p.op)


@sym("◦")
def white_bullet(g: Draw) -> None:
    p = g.p
    circle(g, p.mid, centre(p), _r(p, SMALL), line(p, SMALL))


@sym("◌")
def dotted_circle(g: Draw) -> None:
    p = g.p
    r_dot = 0.26 * p.op + 14
    r = _r(p) - r_dot
    for i in range(8):
        z = pt(p.mid, centre(p)) + r * unit(90 - 45 * i)
        g.dot(z.real, z.imag, r_dot, k=p.dot_k)


@sym("◉")
def fisheye(g: Draw) -> None:
    p = g.p
    r, t = _r(p), fine(p)
    circle(g, p.mid, centre(p), r, t)
    disc(g, p.mid, centre(p), 0.56 * (r - t))


@sym("◎")
def bullseye(g: Draw) -> None:
    p = g.p
    r, t = _r(p), fine(p)
    circle(g, p.mid, centre(p), r, t)
    circle(g, p.mid, centre(p), 0.60 * (r - t) + 0.3 * t, 0.9 * t)


@sym("◍")
def circle_with_vertical_fill(g: Draw) -> None:
    p = g.p
    r, t = _r(p), fine(p)
    cx, cy = p.mid, centre(p)
    circle(g, cx, cy, r, t)
    w = 0.30 * p.op + 20
    ri = r - t / 2  # the bars end inside the ring
    step = 0.50 * (r - t)
    for dx in (-step, 0.0, step):
        hy = math.sqrt(ri * ri - (abs(dx) + w / 2) ** 2)
        g.rect(cx + dx - w / 2, cy - hy, cx + dx + w / 2, cy + hy)


def _part_filled(character: str, first: int, count: int) -> None:
    @sym(character)
    def program(g: Draw) -> None:
        p = g.p
        circle(g, p.mid, centre(p), _r(p), p.op)
        sector(g, p.mid, centre(p), _r(p), first, count)


_part_filled("◐", 1, 2)  # left half black
_part_filled("◑", 3, 2)  # right half
_part_filled("◒", 2, 2)  # lower half
_part_filled("◓", 0, 2)  # upper half
_part_filled("◔", 0, 1)  # upper right quadrant
_part_filled("◕", 2, 3)  # all but the upper left quadrant


@sym("◖")
def left_half_black_circle(g: Draw) -> None:
    p = g.p
    sector(g, p.mid + 0.25 * _r(p), centre(p), _r(p), 1, 2)


@sym("◗")
def right_half_black_circle(g: Draw) -> None:
    p = g.p
    sector(g, p.mid - 0.25 * _r(p), centre(p), _r(p), 3, 2)


# -- check marks and crosses ------------------------------------------------------------------------------------


def _check(g: Draw, t: float) -> None:
    """A short leg from the left and a long one that rises to the cap height, meeting on the baseline."""
    p = g.p
    g.poly(tick(pt(p.op_l - 14, 0.47 * p.cap), pt(p.mid - 64, -p.over), pt(p.op_r + 14, p.cap), t, 0.5 * t))


@sym("✓")
def check_mark(g: Draw) -> None:
    _check(g, mark(g.p))


@sym("✔")
def heavy_check_mark(g: Draw) -> None:
    _check(g, heavy(g.p))


def _saltire(g: Draw, hx: float, hy: float, t: float) -> None:
    """A symmetric cross of two diagonals in the box of half-size (hx, hy), cut level."""
    p = g.p
    cx, cy = p.mid, centre(p)
    b = t * math.hypot(2 * hx, 2 * hy) / (2 * hy)
    x = hx - b / 2
    g.stroke(*path(pt(cx - x, cy - hy), pt(cx + x, cy + hy), t=t, ends=0))
    g.stroke(*path(pt(cx - x, cy + hy), pt(cx + x, cy - hy), t=t, ends=0))


@sym("✕")
def multiplication_x(g: Draw) -> None:
    p = g.p
    h = half(p, FULL)
    _saltire(g, h, h, mark(p))


@sym("✖")
def heavy_multiplication_x(g: Draw) -> None:
    p = g.p
    h = half(p, FULL)
    _saltire(g, h, h, heavy(p))


def _ballot_x(g: Draw, t: float) -> None:
    """Two straight strokes that cross above the middle: a long one rising to the right, as tall as the check
    mark, and a shorter, steeper one falling to the right."""
    p = g.p
    y0, y1 = 24.0, p.cap - 70
    b = 1.28 * t  # about the breadth of a level cut
    g.stroke(*path(pt(p.op_l - 26 + b / 2, y0), pt(p.op_r + 26 - b / 2, y1), t=t, ends=0))
    g.stroke(*path(pt(p.op_l + 22 + b / 2, y1 - 50), pt(p.op_r - 64 - b / 2, y0 + 40), t=t, ends=0))


@sym("✗")
def ballot_x(g: Draw) -> None:
    _ballot_x(g, mark(g.p))


@sym("✘")
def heavy_ballot_x(g: Draw) -> None:
    _ballot_x(g, heavy(g.p))


def _greek_cross(g: Draw, t: float, gap: float = 0.0) -> None:
    p = g.p
    cx, cy = p.mid, centre(p)
    h = half(p, FULL)
    if gap:
        for heading in (0, 90, 180, 270):
            g.poly(spoke(pt(cx, cy), gap, h, heading, t))
    else:
        g.rect(cx - h, cy - t / 2, cx + h, cy + t / 2)
        g.rect(cx - t / 2, cy - h, cx + t / 2, cy + h)


@sym("✚")
def heavy_greek_cross(g: Draw) -> None:
    _greek_cross(g, heavy(g.p) * 1.06)


@sym("✛")
def open_centre_cross(g: Draw) -> None:
    p = g.p
    _greek_cross(g, mark(p), 0.5 * mark(p) + 26)


@sym("✜")
def heavy_open_centre_cross(g: Draw) -> None:
    p = g.p
    _greek_cross(g, heavy(p) * 1.06, 0.30 * heavy(p) + 30)


# -- the user's interface: keys and small pictograms ------------------------------------------------------------


@sym("☰")
def trigram_heaven(g: Draw) -> None:
    _trigram(g, (1, 1, 1))


def _trigram(g: Draw, solid: tuple[int, int, int]) -> None:
    """Three bars; ``solid`` says, from the bottom up, which are whole (1) and which are broken (0)."""
    p = g.p
    t = 0.60 * p.op + 40
    hx, hy = half(p, FULL) * 1.10, half(p, FULL)
    cx, cy = p.mid, centre(p)
    gap = 0.20 * hx + 0.25 * t
    for i, whole in enumerate(solid):
        y = cy + (i - 1) * (hy - t / 2)
        if whole:
            g.stroke(*hbar(cx - hx, cx + hx, y, t))
        else:
            g.stroke(*hbar(cx - hx, cx - gap, y, t))
            g.stroke(*hbar(cx + gap, cx + hx, y, t))


for _c, _bits in (
    ("☱", (1, 1, 0)), ("☲", (1, 0, 1)), ("☳", (1, 0, 0)), ("☴", (0, 1, 1)),
    ("☵", (0, 1, 0)), ("☶", (0, 0, 1)), ("☷", (0, 0, 0)),
):  # fmt: skip

    def _make(bits: tuple[int, int, int]) -> Program:
        def program(g: Draw) -> None:
            _trigram(g, bits)

        return program

    sym(_c)(_make(_bits))


@sym("⏎")
def return_symbol(g: Draw) -> None:
    p = g.p
    t = p.op
    y = centre(p) - 116  # the shaft
    top = centre(p) + half(p, FULL) + 44
    x = p.op_r - 6 - t / 2  # the stem that comes down
    rise = 0.4 * t + 84
    tip = pt(p.op_l - 26 + 0.75 * t, y)  # the head's outer point is about 0.75 t to the left of this
    g.stroke(*elbow(x, top, y - t / 2, tip.real, t, t, p.sq, 100))
    g.stroke(*chevron(tip, rise, rise, t))


def _step(p: Params) -> tuple[float, float, float, float, float, float]:
    """The alternative and option keys share one step: x of the left end, of the two bends and of the right
    end, then the height of the low line and of the high one."""
    cy = centre(p)
    rise = 0.86 * half(p, FULL)
    return p.op_l - 16, p.mid - 92, p.mid + 60, p.op_r + 16, cy - rise, cy + rise


@sym("⎇")
def alternative_key(g: Draw) -> None:
    p = g.p
    x0, xa, xb, x1, lo, hi = _step(p)
    g.stroke(*path(pt(x0, lo), pt(xa, lo), pt(xb, hi), pt(x1, hi), t=p.op))
    g.stroke(*hbar(xb + 0.2 * p.op + 4, x1, lo, p.op))


@sym("⌥")
def option_key(g: Draw) -> None:
    p = g.p
    x0, xa, xb, x1, lo, hi = _step(p)
    g.stroke(*path(pt(x0, hi), pt(xa, hi), pt(xb, lo), pt(x1, lo), t=p.op))
    g.stroke(*hbar(xb + 0.2 * p.op + 4, x1, hi, p.op))


@sym("⧗")
def black_hourglass(g: Draw) -> None:
    p = g.p
    hx, hy = 0.84 * half(p, FULL), 1.16 * half(p, FULL)
    w = 0.22 * p.op + 10  # half the waist
    cx, cy = p.mid, centre(p)
    g.poly([
        pt(cx - hx, cy - hy), pt(cx + hx, cy - hy), pt(cx + w, cy), pt(cx + hx, cy + hy),
        pt(cx - hx, cy + hy), pt(cx - w, cy),
    ])  # fmt: skip


@sym("⧖")
def white_hourglass(g: Draw) -> None:
    p = g.p
    hx, hy = 0.84 * half(p, FULL), 1.16 * half(p, FULL)
    cx, cy = p.mid, centre(p)
    t = line(p, SMALL)
    # Two outlined triangles whose centre lines meet in the middle: their strokes cross there.
    reach = (t / 2) * math.hypot(hx, hy) / hx  # how far a mitred point lies beyond its centre line's vertex
    outline(g, [pt(cx - hx, cy + hy), pt(cx, cy - reach), pt(cx + hx, cy + hy)], t)
    outline(g, [pt(cx + hx, cy - hy), pt(cx, cy + reach), pt(cx - hx, cy - hy)], t)


@sym("⧉")
def two_joined_squares(g: Draw) -> None:
    p = g.p
    t = fine(p)
    h = 0.80 * half(p, FULL)  # half the side of each square
    off = 0.36 * half(p, FULL)  # each is moved this far from the centre, one down and left, one up and right
    gap = 0.2 * t + 28
    cx, cy = p.mid, centre(p)
    outline(g, square(cx - off, cy - off, h), t)
    # the square behind: what the one in front leaves visible
    x0, x1 = cx + off - h + t / 2, cx + off + h - t / 2
    y0, y1 = cy + off - h + t / 2, cy + off + h - t / 2
    front_top, front_right = cy - off + h, cx - off + h
    g.stroke(
        *path(
            pt(x0, front_top + gap), pt(x0, y1), pt(x1, y1), pt(x1, y0), pt(front_right + gap, y0), t=t, ends=0, end=90
        )
    )


@sym("⏱")
def stopwatch(g: Draw) -> None:
    p = g.p
    t = fine(p)
    r = 1.10 * half(p, FULL)
    cx, cy = p.mid, centre(p) - 52
    circle(g, cx, cy, r, t)
    # the button: a stem and a cap
    top = cy + r + 0.8 * t + 44
    g.stroke(*vstem(cx, cy + r - t / 2, top, t))
    g.stroke(*hbar(cx - 1.3 * t, cx + 1.3 * t, top - t / 2, t))
    # the hands, at three o'clock
    reach = r - t
    g.stroke(*path(pt(cx, cy + 0.70 * reach), pt(cx, cy), pt(cx + 0.56 * reach, cy), t=0.9 * t, ends=0, end=90))


@sym("⚠")
def warning_sign(g: Draw) -> None:
    p = g.p
    t = fine(p)
    hx = p.mid - 12
    y0, y1 = 28.0, p.cap - 60
    outline(g, [pt(p.mid - hx, y0), pt(p.mid + hx, y0), pt(p.mid, y1)], t)
    # the bang: a stem and a dot, low in the triangle where it is wide
    w = 0.95 * t
    dot_y = y0 + t + 30 + w / 2
    g.rect(p.mid - w / 2, dot_y - w / 2, p.mid + w / 2, dot_y + w / 2)
    stem_y = dot_y + w / 2 + 34
    g.rect(p.mid - w / 2, stem_y, p.mid + w / 2, stem_y + 0.26 * (y1 - y0))


@sym("✎")
def lower_right_pencil(g: Draw) -> None:
    _pencil(g, -45.0)


@sym("✏")
def pencil(g: Draw) -> None:
    _pencil(g, 0.0)


def _pencil(g: Draw, heading: float) -> None:
    """A pencil pointing along ``heading``: a cap, the barrel, and the sharpened point, separated by slits."""
    p = g.p
    c = pt(p.mid, centre(p))
    d = unit(heading)
    n = d * 1j
    length = 2 * half(p, LARGE) * (1.22 if heading else 1.0)
    w = 0.40 * half(p, FULL)  # half the barrel's breadth
    slit = 0.24 * p.op + 22
    cone = 2.1 * w
    capl = 0.9 * w
    u0 = -length / 2

    def at(u: float, v: float) -> complex:
        return c + d * u + n * v

    g.poly([at(u0, -w), at(u0 + capl, -w), at(u0 + capl, w), at(u0, w)])
    b0, b1 = u0 + capl + slit, length / 2 - cone - slit
    g.poly([at(b0, -w), at(b1, -w), at(b1, w), at(b0, w)])
    g.poly([at(length / 2 - cone, -w), at(length / 2, 0), at(length / 2 - cone, w)])


# -- stars, asterisks and ornaments -----------------------------------------------------------------------------


def star(c: complex, points: int, r: float, waist: float, heading: float = 90.0) -> list[complex]:
    """A star with ``points`` points of radius ``r``; its inner corners lie at ``waist`` times ``r``."""
    step = 180.0 / points
    return [c + (r if i % 2 == 0 else waist * r) * unit(heading + i * step) for i in range(2 * points)]


def scaled(points: Sequence[complex], c: complex, f: float) -> list[complex]:
    return [c + (z - c) * f for z in points]


def star_inset(points: Sequence[complex], c: complex, t: float) -> list[complex]:
    """A star (or any polygon whose edges are all equally far from ``c``) with its edges moved inwards by
    ``t``: the same star, smaller."""
    a, b = points[0] - c, points[1] - c
    apothem = abs(a.real * b.imag - a.imag * b.real) / abs(b - a)
    return scaled(points, c, 1 - t / apothem)


def _four_star(p: Params) -> tuple[list[complex], complex]:
    c = pt(p.mid, centre(p))
    return star(c, 4, 1.10 * half(p, LARGE), 0.40), c


@sym("✦")
def black_four_pointed_star(g: Draw) -> None:
    g.poly(_four_star(g.p)[0])


@sym("✧")
def white_four_pointed_star(g: Draw) -> None:
    s, c = _four_star(g.p)
    g.poly(s)
    hole(g, star_inset(s, c, line(g.p, SMALL)))


def _five_star(p: Params) -> tuple[list[complex], complex]:
    r = 1.12 * half(p, LARGE)
    c = pt(p.mid, centre(p) - 0.06 * r)  # the star's box is centred, not its middle
    return star(c, 5, r, 0.47), c


@sym("★")
def black_star(g: Draw) -> None:
    g.poly(_five_star(g.p)[0])


@sym("☆")
def white_star(g: Draw) -> None:
    s, c = _five_star(g.p)
    g.poly(s)
    hole(g, star_inset(s, c, line(g.p, SMALL)))


@sym("✴")
def eight_pointed_black_star(g: Draw) -> None:
    p = g.p
    g.poly(star(pt(p.mid, centre(p)), 8, 1.06 * half(p, LARGE), 0.56))


def _asterisk(g: Draw, spokes: int, t: float, r: float) -> None:
    """``spokes`` bars through the centre, the first one upright, cut square."""
    c = pt(g.p.mid, centre(g.p))
    for i in range(spokes):
        g.poly(spoke(c, -r, r, 90.0 + i * 180.0 / spokes, t))


@sym("✱")
def heavy_asterisk(g: Draw) -> None:
    p = g.p
    _asterisk(g, 3, 0.92 * heavy(p), 1.08 * half(p, FULL))


@sym("✳")
def eight_spoked_asterisk(g: Draw) -> None:
    p = g.p
    _asterisk(g, 4, 0.92 * fine(p), 1.10 * half(p, FULL))


def _angle_ornament(character: str, sign: int, height: float, depth: float) -> None:
    """A heavy chevron that points right (``sign`` 1) or left (-1), ``height`` and ``depth`` being fractions of
    the full class."""

    @sym(character)
    def program(g: Draw) -> None:
        p = g.p
        t = heavy(p)
        rise = height * half(p, FULL)
        back = depth * half(p, FULL)
        reach = (
            (t / 2) * math.hypot(back, rise) / rise
        )  # from the centre line to the outline, at the point and at the cuts
        tip = pt(p.mid + sign * (back / 2), centre(p))
        g.stroke(*chevron(tip, -sign * back, rise, t))
        _ = reach


_angle_ornament("❯", 1, 1.16, 0.84)
_angle_ornament("❮", -1, 1.16, 0.84)
_angle_ornament("❱", 1, 1.56, 0.62)
_angle_ornament("❰", -1, 1.56, 0.62)


@sym("❖")
def black_diamond_minus_white_x(g: Draw) -> None:
    p = g.p
    reach = DIAMOND_W * half(p, FULL)
    gap = (0.40 * p.op + 16) / math.sqrt(2)
    a, b = (reach + gap) / 2, (reach - gap) / 2
    for d in (1, 1j, -1, -1j):
        c = pt(p.mid, centre(p)) + a * d
        g.poly(diamond(c.real, c.imag, b, b))


# -- ballot boxes -----------------------------------------------------------------------------------------------


def _ballot_box(g: Draw) -> tuple[float, float, float]:
    """Draws the box; returns its centre and half its inner side."""
    p = g.p
    h = 0.96 * half(p, LARGE)
    t = fine(p)
    outline(g, square(p.mid, centre(p), h), t)
    return p.mid, centre(p), h - t


@sym("☐")
def ballot_box(g: Draw) -> None:
    _ballot_box(g)


@sym("☑")
def ballot_box_with_check(g: Draw) -> None:
    cx, cy, h = _ballot_box(g)
    t = 1.05 * fine(g.p)
    g.poly(
        tick(
            pt(cx - 0.80 * h, cy + 0.10 * h),
            pt(cx - 0.20 * h, cy - 0.74 * h),
            pt(cx + 0.80 * h, cy + 0.76 * h),
            t,
            0.5 * t,
        )
    )


@sym("☒")
def ballot_box_with_x(g: Draw) -> None:
    cx, cy, h = _ballot_box(g)
    t = 1.0 * fine(g.p)
    e = 0.74 * h
    b = t * math.sqrt(2)
    g.stroke(*path(pt(cx - e + b / 2, cy - e), pt(cx + e - b / 2, cy + e), t=t, ends=0))
    g.stroke(*path(pt(cx - e + b / 2, cy + e), pt(cx + e - b / 2, cy - e), t=t, ends=0))


# -- pictograms -------------------------------------------------------------------------------------------------


@sym("⚡")
def high_voltage(g: Draw) -> None:
    p = g.p
    hx, hy = 0.92 * half(p, FULL), p.cap / 2 + 2 * p.over
    c = pt(p.mid, p.cap / 2)
    shape = [(0.34, 1.0), (-0.86, -0.12), (-0.06, -0.12), (-0.38, -1.0), (0.86, 0.16), (0.08, 0.16)]
    g.poly([c + pt(x * hx, y * hy) for x, y in shape])


@sym("⚙")
def gear(g: Draw) -> None:
    p = g.p
    c = pt(p.mid, centre(p))
    r = 1.16 * half(p, FULL)
    root = 0.76 * r
    teeth = 8
    pitch = 360.0 / teeth
    outline_pts: list[complex] = []
    for i in range(teeth):
        a = 90.0 + i * pitch
        outline_pts.extend((
            c + root * unit(a - 0.31 * pitch), c + r * unit(a - 0.17 * pitch),
            c + r * unit(a + 0.17 * pitch), c + root * unit(a + 0.31 * pitch),
        ))  # fmt: skip
    g.poly(outline_pts)
    g.add(superellipse(c.real, c.imag, 0.36 * r, 0.36 * r, p.dot_k).reversed())


def _flag(g: Draw) -> tuple[float, float, float, float]:
    """Draws the pole; returns the flag's box."""
    p = g.p
    t = fine(p)
    x = p.op_l + 40 + t / 2
    g.stroke(*vstem(x, 0, p.cap, t))
    return x, p.cap - 1.56 * half(p, FULL), p.op_r + 4, p.cap


@sym("⚑")
def black_flag(g: Draw) -> None:
    x0, y0, x1, y1 = _flag(g)
    g.rect(x0, y0, x1, y1)


@sym("⚐")
def white_flag(g: Draw) -> None:
    x0, y0, x1, y1 = _flag(g)
    t = fine(g.p)
    outline(g, [pt(x0 - t / 2, y0), pt(x1, y0), pt(x1, y1), pt(x0 - t / 2, y1)], t)
