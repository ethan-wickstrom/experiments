"""Strokes: a skeleton of knots, each carrying a pen, expanded into a closed outline.

This is METAFONT's ``penpos``/``penstroke`` model. A knot is a point on the centre line of a stroke, with the
breadth of the pen there and, optionally, the angle of the pen's edge and the direction of travel. The centre line
through the knots is a Hobby spline (straight where a knot says so). The outline is the path through the pen's
right ends, a cap, the path back through its left ends, and a cap.

Every stroke expands to the same number of segments whatever its numbers are, so the masters of a variable font
are point-compatible by construction: a glyph program run with a heavier pen yields the same structure.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from rachis.geom import (
    EPS,
    Cubic,
    Line,
    Node,
    Segment,
    cross,
    dot,
    hobby_directions,
    hobby_segment,
    intersect,
    normalized,
    unit,
)

RIGHT = -1j  # multiplying a direction by this turns it 90 degrees to the right
_GAUSS3 = (
    (0.5 - math.sqrt(0.15), 5.0 / 18.0),
    (0.5, 8.0 / 18.0),
    (0.5 + math.sqrt(0.15), 5.0 / 18.0),
)


@dataclass(frozen=True, slots=True)
class Knot:
    """A point on a stroke's centre line, and the pen there.

    ``w`` is the pen's breadth. ``pen`` is the angle in degrees of the pen's edge, as a line (0 is a horizontal
    edge, which cuts a vertical stem square; 90 is a vertical edge); ``None`` holds the pen perpendicular to the
    path. ``dir`` is the direction of travel in degrees; ``None`` lets the spline choose it. ``line`` makes the
    segment from this knot to the next one straight. ``t_in`` and ``t_out`` are Hobby tensions. ``k`` overrides
    the curve from this knot to the next: its control points are placed at the fraction ``k`` of the way from
    each knot to the point where the two end tangents meet (0.5523 gives a quarter ellipse, larger is squarer).
    """

    z: complex
    w: float
    pen: float | None = None
    dir: float | None = None
    line: bool = False
    t_in: float = 1.0
    t_out: float = 1.0
    k: float | None = None


@dataclass(frozen=True, slots=True)
class Contour:
    """A closed outline: each segment starts where the previous one ends, and the last ends at the first's start."""

    segs: tuple[Segment, ...]

    def area(self) -> float:
        """Signed area, exactly: positive when the contour runs counter-clockwise.

        By Green's theorem it is half the integral of B x B' along the contour. On a cubic the integrand is a
        polynomial of degree 5, which three-point Gauss-Legendre quadrature integrates without error.
        """
        total = 0.0
        for s in self.segs:
            if isinstance(s, Line):
                total += cross(s.p0, s.p1)
                continue
            for t, weight in _GAUSS3:
                u = 1.0 - t
                d = 3 * u * u * (s.c1 - s.p0) + 6 * u * t * (s.c2 - s.c1) + 3 * t * t * (s.p3 - s.c2)
                total += weight * cross(s.at(t), d)
        return total / 2.0

    def reversed(self) -> Contour:
        return Contour(tuple(s.reversed() for s in reversed(self.segs)))

    def oriented(self, counter_clockwise: bool = True) -> Contour:
        return self if (self.area() > 0) == counter_clockwise else self.reversed()

    def mapped(self, f: Callable[[complex], complex]) -> Contour:
        out: list[Segment] = []
        for s in self.segs:
            if isinstance(s, Line):
                out.append(Line(f(s.p0), f(s.p1)))
            else:
                out.append(Cubic(f(s.p0), f(s.c1), f(s.c2), f(s.p3)))
        return Contour(tuple(out))

    def points(self) -> list[complex]:
        """Every on-curve and off-curve point, in order."""
        out: list[complex] = []
        for s in self.segs:
            if isinstance(s, Line):
                out.append(s.p1)
            else:
                out.extend((s.c1, s.c2, s.p3))
        return out

    def signature(self) -> str:
        """The contour's structure, which must agree between the masters of a variable font."""
        return "".join("L" if isinstance(s, Line) else "C" for s in self.segs)


def polygon(points: Sequence[complex]) -> Contour:
    n = len(points)
    return Contour(tuple(Line(points[i], points[(i + 1) % n]) for i in range(n))).oriented()


def rect(x0: float, y0: float, x1: float, y1: float) -> Contour:
    return polygon([complex(x0, y0), complex(x1, y0), complex(x1, y1), complex(x0, y1)])


def superellipse(cx: float, cy: float, rx: float, ry: float, k: float = 0.5523) -> Contour:
    """Four cubic quadrants around (cx, cy). ``k`` is the handle length as a fraction of the radius: 0.5523 gives
    an ellipse, and larger values are squarer (at 1 the shape fills 95% of its box)."""
    c = complex(cx, cy)
    e, n, w, s = c + rx, c + 1j * ry, c - rx, c - 1j * ry
    return Contour(
        (
            Cubic(e, e + 1j * k * ry, n + k * rx, n),
            Cubic(n, n - k * rx, w + 1j * k * ry, w),
            Cubic(w, w - 1j * k * ry, s - k * rx, s),
            Cubic(s, s + k * rx, e - 1j * k * ry, e),
        )
    )


# ---------------------------------------------------------------------------------------------------------------


def _half_pen(knot: Knot, travel: complex) -> complex:
    """The vector from the knot to the pen's right end, for a pen moving along ``travel``."""
    right = normalized(travel) * RIGHT
    if knot.pen is None:
        return right * (knot.w / 2.0)
    u = unit(knot.pen)
    side = dot(u, right)
    if abs(side) < 1e-6:
        raise ValueError(f"the pen at {knot.z} lies along the path")
    return u * (knot.w / 2.0) * (1.0 if side > 0 else -1.0)


def _corner_cubic(z0: complex, z1: complex, d0: complex, d1: complex, k: float) -> Cubic | None:
    apex = intersect(z0, d0, z1, d1)
    if apex is None or dot(apex - z0, d0) <= 0 or dot(z1 - apex, d1) <= 0:
        return None
    return Cubic(z0, z0 + (apex - z0) * k, z1 + (apex - z1) * k, z1)


def _offset_cubic(center: Cubic, h0: complex, h1: complex, side: float, d0: complex, d1: complex) -> Cubic:
    """One side of a curved stroke segment: a cubic with the centre line's end tangents that passes through the
    centre line's midpoint displaced by the interpolated pen. For an arc of a circle and a constant pen it is the
    standard cubic approximation of the concentric arc."""
    p0 = center.p0 + side * h0
    p3 = center.p3 + side * h1
    t0, t1 = normalized(d0), normalized(d1)
    tm = normalized(center.tangent(0.5))
    # the pen at each end, as a complex multiple of the right normal there: breadth and skew together
    pen_mid = (h0 / (t0 * RIGHT) + h1 / (t1 * RIGHT)) / 2.0
    target = center.at(0.5) + side * pen_mid * (tm * RIGHT)
    rhs = (8.0 / 3.0) * (target - (p0 + p3) / 2.0)
    den = cross(t0, t1)
    chord = abs(p3 - p0)
    if abs(den) > 0.05:
        a = cross(rhs, t1) / den
        b = cross(rhs, t0) / den
        if 0.02 * chord < a < 2.0 * chord and 0.02 * chord < b < 2.0 * chord:
            return Cubic(p0, p0 + a * t0, p3 - b * t1, p3)
    # nearly parallel end tangents: scale the centre line's handles with the chord
    c_chord = abs(center.p3 - center.p0)
    r = chord / c_chord if c_chord > EPS else 1.0
    return Cubic(p0, p0 + abs(center.c1 - center.p0) * r * t0, p3 - abs(center.p3 - center.c2) * r * t1, p3)


def centerline(knots: Sequence[Knot], closed: bool = False) -> tuple[list[Segment], list[complex], list[complex]]:
    """The centre line's segments, and the direction of arrival and of departure at every knot."""
    n = len(knots)
    if n < 2:
        raise ValueError("a stroke needs two knots")
    nseg = n if closed else n - 1
    straight = [knots[i].line for i in range(nseg)]
    chord = [knots[(i + 1) % n].z - knots[i].z for i in range(nseg)]

    d_in: list[complex | None] = [None] * n
    d_out: list[complex | None] = [None] * n
    for i in range(n):
        before = (i - 1) % nseg if (closed or i > 0) else None
        after = i if (closed or i < n - 1) else None
        heading = knots[i].dir
        given = unit(heading) if heading is not None else None
        line_in = before is not None and straight[before]
        line_out = after is not None and straight[after]
        if line_in:
            assert before is not None
            d_in[i] = normalized(chord[before])
        if line_out:
            assert after is not None
            d_out[i] = normalized(chord[after])
        if given is not None:
            if not line_in:
                d_in[i] = given
            if not line_out:
                d_out[i] = given
        else:  # a curve leaves a straight segment along the straight segment's direction
            if line_in and not line_out:
                d_out[i] = d_in[i]
            if line_out and not line_in:
                d_in[i] = d_out[i]

    # Solve each maximal run of curved segments as one Hobby spline.
    segs: list[Segment | None] = [None] * nseg
    for i in range(nseg):
        if straight[i]:
            segs[i] = Line(knots[i].z, knots[(i + 1) % n].z)
    if closed and not any(straight):
        nodes = [Node(k.z, d_out[i], t_in=k.t_in, t_out=k.t_out) for i, k in enumerate(knots)]
        dirs = hobby_directions(nodes, closed=True)
        for i in range(n):
            d_in[i] = d_out[i] = dirs[i]
    else:
        starts = [
            i for i in range(nseg) if not straight[i] and (straight[(i - 1) % nseg] if (closed or i > 0) else True)
        ]
        for s in starts:
            run = [s]
            while True:
                nxt = run[-1] + 1
                if not closed and nxt >= nseg:
                    break
                nxt %= nseg
                if straight[nxt] or nxt == s:
                    break
                run.append(nxt)
            idx = [*run, (run[-1] + 1) % n]
            nodes = []
            for j, i in enumerate(idx):
                k = knots[i]
                fixed = d_out[i] if j == 0 else d_in[i] if j == len(idx) - 1 else (d_out[i] or d_in[i])
                nodes.append(Node(k.z, fixed, t_in=k.t_in, t_out=k.t_out))
            dirs = hobby_directions(nodes)
            for j, i in enumerate(idx):
                if j > 0:
                    d_in[i] = dirs[j]
                if j < len(idx) - 1:
                    d_out[i] = dirs[j]
    for i in range(n):  # the open ends
        if d_in[i] is None:
            d_in[i] = d_out[i]
        if d_out[i] is None:
            d_out[i] = d_in[i]

    arrive = [d for d in d_in if d is not None]
    depart = [d for d in d_out if d is not None]
    assert len(arrive) == n and len(depart) == n
    for i in range(nseg):
        if segs[i] is None:
            a, b = knots[i], knots[(i + 1) % n]
            curve = _corner_cubic(a.z, b.z, depart[i], arrive[(i + 1) % n], a.k) if a.k is not None else None
            segs[i] = curve or hobby_segment(a.z, b.z, depart[i], arrive[(i + 1) % n], a.t_out, b.t_in)
    return [s for s in segs if s is not None], arrive, depart


def expand(knots: Sequence[Knot], closed: bool = False) -> list[Contour]:
    """The outline of the stroke through ``knots``: one contour for an open stroke, two (outer, then inner) for a
    closed one. Outer contours run counter-clockwise, inner ones clockwise."""
    n = len(knots)
    segs, arrive, depart = centerline(knots, closed)
    nseg = len(segs)

    # The pen's right-hand offset at each knot, on arrival and on departure. They differ only at a corner.
    h_in: list[complex] = []
    h_out: list[complex] = []
    for i, k in enumerate(knots):
        a, d = arrive[i], depart[i]
        smooth = abs(cross(a, d)) < 1e-6 and dot(a, d) > 0
        if smooth or k.pen is not None:
            h = _half_pen(k, a if smooth else a + d)
            h_in.append(h)
            h_out.append(h)
            continue
        ha, hd = _half_pen(k, a), _half_pen(k, d)
        before = (i - 1) % nseg if (closed or i > 0) else None
        after = i if (closed or i < n - 1) else None
        mitred = (
            before is not None
            and after is not None
            and isinstance(segs[before], Line)
            and isinstance(segs[after], Line)
        )
        if mitred:  # two straight segments meet: each side turns at the intersection of its two edges
            right = intersect(k.z + ha, a, k.z + hd, d)
            assert right is not None
            h = right - k.z
            h_in.append(h)
            h_out.append(h)
        else:
            h_in.append(ha)
            h_out.append(hd)

    sides: list[list[Segment]] = []
    for side in (1.0, -1.0):
        path: list[Segment] = []
        for i in range(nseg):
            j = (i + 1) % n
            seg = segs[i]
            if isinstance(seg, Line):
                path.append(Line(seg.p0 + side * h_out[i], seg.p1 + side * h_in[j]))
            else:
                path.append(_offset_cubic(seg, h_out[i], h_in[j], side, depart[i], arrive[j]))
            last = not closed and i == nseg - 1
            if not last and h_in[j] != h_out[j]:  # a corner between a curve and something else: bevel it
                path.append(Line(knots[j].z + side * h_in[j], knots[j].z + side * h_out[j]))
        sides.append(path)
    right_path, left_path = sides

    if closed:
        a, b = Contour(tuple(right_path)), Contour(tuple(left_path))
        outer, inner = (a, b) if abs(a.area()) >= abs(b.area()) else (b, a)
        return [outer.oriented(True), inner.oriented(False)]
    back = [s.reversed() for s in reversed(left_path)]
    cap_end = Line(right_path[-1].end, back[0].start)
    cap_start = Line(back[-1].end, right_path[0].start)
    return [Contour((*right_path, cap_end, *back, cap_start)).oriented(True)]


def sheared(knot: Knot, slope: float, origin_y: float) -> Knot:
    """``knot`` after the shear x' = x + slope (y - origin_y), which slants a skeleton for an italic.

    A fixed pen is sheared as a vector, so a stem keeps its horizontal thickness and a bar its vertical one; a
    perpendicular pen stays perpendicular to the slanted path, so a curve keeps its breadth.
    """
    if slope == 0.0:
        return knot

    def vec(v: complex) -> complex:
        return complex(v.real + slope * v.imag, v.imag)

    z = complex(knot.z.real + slope * (knot.z.imag - origin_y), knot.z.imag)
    out = replace(knot, z=z)
    if knot.dir is not None:
        d = vec(unit(knot.dir))
        out = replace(out, dir=math.degrees(math.atan2(d.imag, d.real)))
    if knot.pen is not None:
        h = vec(unit(knot.pen) * knot.w)
        out = replace(out, pen=math.degrees(math.atan2(h.imag, h.real)), w=abs(h))
    return out
