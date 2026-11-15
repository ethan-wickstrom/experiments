"""Plane geometry on complex numbers: cubic Béziers and Hobby's interpolating splines.

A point or vector is a ``complex``: ``x + iy``. Multiplying by ``unit(a)`` rotates by ``a`` degrees, and
``phase(b / a)`` is the turning angle from ``a`` to ``b``, which is why METAFONT, and this kernel after it, do
their geometry in the complex plane.

The spline is John Hobby's ("Smooth, easy to compute interpolating splines", Discrete & Computational Geometry 1,
1986), in the form METAFONT uses (The METAFONTbook, chapter 14; mf.web, "Choosing control points"). Given knots
and, optionally, directions at some of them, it picks the remaining directions so that an approximation of
curvature (the "mock curvature", linear in the angles) is continuous at every knot, then places each segment's
control points with the velocity function ``velocity``.
"""

from __future__ import annotations

import cmath
import math
from collections.abc import Sequence
from dataclasses import dataclass

EPS = 1e-9


def pt(x: float, y: float) -> complex:
    return complex(x, y)


def unit(degrees: float) -> complex:
    """The unit vector at ``degrees`` counter-clockwise from the positive x axis."""
    return cmath.rect(1.0, math.radians(degrees))


def angle(v: complex) -> float:
    """The direction of ``v`` in degrees, in (-180, 180]."""
    return math.degrees(cmath.phase(v))


def normalized(v: complex) -> complex:
    n = abs(v)
    if n < EPS:
        raise ValueError("a zero vector has no direction")
    return v / n


def cross(a: complex, b: complex) -> float:
    return a.real * b.imag - a.imag * b.real


def dot(a: complex, b: complex) -> float:
    return a.real * b.real + a.imag * b.imag


def lerp(a: complex, b: complex, t: float) -> complex:
    return a + (b - a) * t


def intersect(p: complex, u: complex, q: complex, v: complex) -> complex | None:
    """Where the line through ``p`` along ``u`` meets the line through ``q`` along ``v``; None if parallel."""
    den = cross(u, v)
    if abs(den) < EPS * max(1.0, abs(u) * abs(v)):
        return None
    return p + u * (cross(q - p, v) / den)


@dataclass(frozen=True, slots=True)
class Line:
    p0: complex
    p1: complex

    def at(self, t: float) -> complex:
        return lerp(self.p0, self.p1, t)

    def tangent(self, t: float) -> complex:
        return self.p1 - self.p0

    def reversed(self) -> Line:
        return Line(self.p1, self.p0)

    @property
    def start(self) -> complex:
        return self.p0

    @property
    def end(self) -> complex:
        return self.p1


@dataclass(frozen=True, slots=True)
class Cubic:
    p0: complex
    c1: complex
    c2: complex
    p3: complex

    def at(self, t: float) -> complex:
        s = 1.0 - t
        return s * s * s * self.p0 + 3 * s * s * t * self.c1 + 3 * s * t * t * self.c2 + t * t * t * self.p3

    def tangent(self, t: float) -> complex:
        """The derivative at ``t``; at an end whose handle has zero length, the limit direction."""
        s = 1.0 - t
        d = 3 * s * s * (self.c1 - self.p0) + 6 * s * t * (self.c2 - self.c1) + 3 * t * t * (self.p3 - self.c2)
        if abs(d) > EPS:
            return d
        if t < 0.5:
            return self.c2 - self.p0 if abs(self.c2 - self.p0) > EPS else self.p3 - self.p0
        return self.p3 - self.c1 if abs(self.p3 - self.c1) > EPS else self.p3 - self.p0

    def split(self, t: float) -> tuple[Cubic, Cubic]:
        """De Casteljau's subdivision at ``t``."""
        a = lerp(self.p0, self.c1, t)
        b = lerp(self.c1, self.c2, t)
        c = lerp(self.c2, self.p3, t)
        d = lerp(a, b, t)
        e = lerp(b, c, t)
        m = lerp(d, e, t)
        return Cubic(self.p0, a, d, m), Cubic(m, e, c, self.p3)

    def reversed(self) -> Cubic:
        return Cubic(self.p3, self.c2, self.c1, self.p0)

    @property
    def start(self) -> complex:
        return self.p0

    @property
    def end(self) -> complex:
        return self.p3

    def extrema(self) -> list[float]:
        """Parameters strictly inside (0, 1) where x or y is stationary, ascending."""
        found: list[float] = []
        for part in (lambda z: z.real, lambda z: z.imag):
            p0, p1, p2, p3 = part(self.p0), part(self.c1), part(self.c2), part(self.p3)
            # derivative / 3 = a t^2 + b t + c
            a = -p0 + 3 * p1 - 3 * p2 + p3
            b = 2 * (p0 - 2 * p1 + p2)
            c = p1 - p0
            found.extend(t for t in _quadratic_roots(a, b, c) if 1e-4 < t < 1 - 1e-4)
        return sorted(found)


Segment = Line | Cubic


def _quadratic_roots(a: float, b: float, c: float) -> list[float]:
    if abs(a) < 1e-12:
        return [] if abs(b) < 1e-12 else [-c / b]
    disc = b * b - 4 * a * c
    if disc < 0:
        return []
    r = math.sqrt(disc)
    q = -0.5 * (b + math.copysign(r, b)) if b != 0 else 0.5 * r
    roots = [q / a]
    if abs(q) > 1e-12:
        roots.append(c / q)
    return roots


def flatten(seg: Segment, tolerance: float = 0.25) -> list[complex]:
    """Points along ``seg`` after its start, ending at its end, within ``tolerance`` of the curve."""
    if isinstance(seg, Line):
        return [seg.p1]
    # the second difference bounds the deviation of a cubic from its chord
    dd = max(abs(seg.p0 - 2 * seg.c1 + seg.c2), abs(seg.c1 - 2 * seg.c2 + seg.p3))
    n = max(1, math.ceil(math.sqrt(0.75 * dd / tolerance)))
    return [seg.at(i / n) for i in range(1, n + 1)]


def bounds(points: Sequence[complex]) -> tuple[float, float, float, float]:
    xs = [p.real for p in points]
    ys = [p.imag for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def segment_bounds(segs: Sequence[Segment]) -> tuple[float, float, float, float]:
    """The exact bounding box of a chain of segments."""
    pts: list[complex] = []
    for s in segs:
        pts.extend((s.start, s.end))
        if isinstance(s, Cubic):
            pts.extend(s.at(t) for t in s.extrema())
    return bounds(pts)


# ---------------------------------------------------------------------------------------------------------------
# Hobby's spline


def velocity(theta: float, phi: float) -> float:
    """METAFONT's velocity function f(θ, φ): the distance of a control point from its knot, as a fraction of the
    chord, for a segment that leaves at angle θ and arrives at angle φ (radians, both measured from the chord).

    For θ = φ it is 2 / (3 (1 + cos θ)), which makes the cubic through two points of a circle the standard
    approximation of the arc between them.
    """
    st, ct = math.sin(theta), math.cos(theta)
    sf, cf = math.sin(phi), math.cos(phi)
    num = 2.0 + math.sqrt(2.0) * (st - sf / 16.0) * (sf - st / 16.0) * (ct - cf)
    den = 3.0 * (1.0 + 0.5 * (math.sqrt(5.0) - 1.0) * ct + 0.5 * (3.0 - math.sqrt(5.0)) * cf)
    return num / den


def hobby_segment(z0: complex, z1: complex, d0: complex, d1: complex, t0: float = 1.0, t1: float = 1.0) -> Cubic:
    """The cubic from ``z0`` to ``z1`` that leaves along ``d0`` and arrives along ``d1``.

    ``t0`` and ``t1`` are METAFONT's tensions at the two ends: 1 is the default, larger values pull the curve
    towards the chord.
    """
    chord = z1 - z0
    theta = cmath.phase(d0 / chord)
    phi = cmath.phase(chord / d1)
    c1 = z0 + chord * cmath.rect(velocity(theta, phi) / t0, theta)
    c2 = z1 - chord * cmath.rect(velocity(phi, theta) / t1, -phi)
    return Cubic(z0, c1, c2, z1)


@dataclass(frozen=True, slots=True)
class Node:
    """A knot of a Hobby spline.

    ``dir``, when given, is the direction of travel through the knot. ``curl`` applies only at the ends of an open
    path with no direction there: the mock curvature at the end is ``curl`` times the mock curvature at its
    neighbour (1 approximates a circular arc, 0 a parabola-like flattening). ``t_in`` and ``t_out`` are the
    tensions of the segments arriving at and leaving the knot.
    """

    z: complex
    dir: complex | None = None
    curl: float = 1.0
    t_in: float = 1.0
    t_out: float = 1.0


def hobby_directions(nodes: Sequence[Node], closed: bool = False) -> list[complex]:
    """The direction of travel (a unit vector) at every node of the spline through ``nodes``."""
    n = len(nodes)
    if n < 2:
        raise ValueError("a path needs two knots")
    if any(abs(nodes[(i + 1) % n].z - nodes[i].z) < EPS for i in range(n if closed else n - 1)):
        raise ValueError("consecutive knots coincide")
    if n == 2 and not closed:
        a, b = nodes
        chord = b.z - a.z
        if a.dir is None and b.dir is None:
            return [normalized(chord), normalized(chord)]

    nseg = n if closed else n - 1
    delta = [nodes[(k + 1) % n].z - nodes[k].z for k in range(nseg)]
    dist = [abs(d) for d in delta]

    # Unknowns: theta[k] for the departure from knot k along segment k, phi[k] for the arrival at knot k along
    # segment k-1. Index theta at 2k and phi at 2k+1. Knots with no such segment keep a trivial equation.
    size = 2 * n
    rows: list[list[float]] = []
    rhs: list[float] = []

    def row() -> list[float]:
        return [0.0] * size

    def th(k: int) -> int:
        return 2 * (k % n)

    def ph(k: int) -> int:
        return 2 * (k % n) + 1

    for k in range(n):
        node = nodes[k]
        has_in = closed or k > 0
        has_out = closed or k < n - 1
        if has_in and has_out:
            d_in, d_out = delta[(k - 1) % nseg], delta[k % nseg]
            if node.dir is not None:
                r = row()
                r[th(k)] = 1.0
                rows.append(r)
                rhs.append(cmath.phase(node.dir / d_out))
                r = row()
                r[ph(k)] = 1.0
                rows.append(r)
                rhs.append(cmath.phase(d_in / node.dir))
                continue
            psi = cmath.phase(d_out / d_in)
            # the direction is continuous: theta_k + phi_k + psi_k = 0
            r = row()
            r[th(k)] = 1.0
            r[ph(k)] = 1.0
            rows.append(r)
            rhs.append(-psi)
            # the mock curvature is continuous:
            #   tb_k^2 / d_{k-1} * ((theta_{k-1} + phi_k) / ta_{k-1} - 3 phi_k)
            # = ta_k^2 / d_k     * ((theta_k + phi_{k+1}) / tb_{k+1} - 3 theta_k)
            prev, nxt = nodes[(k - 1) % n], nodes[(k + 1) % n]
            left = node.t_in**2 / dist[(k - 1) % nseg]
            right = node.t_out**2 / dist[k % nseg]
            r = row()
            r[th(k - 1)] += left / prev.t_out
            r[ph(k)] += left / prev.t_out - 3.0 * left
            r[th(k)] -= right / nxt.t_in - 3.0 * right
            r[ph(k + 1)] -= right / nxt.t_in
            rows.append(r)
            rhs.append(0.0)
        elif has_out:  # the first knot of an open path
            nxt = nodes[1]
            r = row()
            r[ph(k)] = 1.0  # unused unknown
            rows.append(r)
            rhs.append(0.0)
            r = row()
            if node.dir is not None:
                r[th(0)] = 1.0
                rows.append(r)
                rhs.append(cmath.phase(node.dir / delta[0]))
            else:
                # curvature at knot 0 = curl * curvature at knot 1, both on segment 0
                a, b, g = node.t_out, nxt.t_in, node.curl
                r[th(0)] = a * a * (1.0 / b - 3.0) - g * b * b / a
                r[ph(1)] = a * a / b - g * b * b * (1.0 / a - 3.0)
                rows.append(r)
                rhs.append(0.0)
        else:  # the last knot of an open path
            prev = nodes[n - 2]
            r = row()
            r[th(k)] = 1.0  # unused unknown
            rows.append(r)
            rhs.append(0.0)
            r = row()
            if node.dir is not None:
                r[ph(k)] = 1.0
                rows.append(r)
                rhs.append(cmath.phase(delta[n - 2] / node.dir))
            else:
                a, b, g = prev.t_out, node.t_in, node.curl
                r[ph(k)] = b * b * (1.0 / a - 3.0) - g * a * a / b
                r[th(k - 1)] = b * b / a - g * a * a * (1.0 / b - 3.0)
                rows.append(r)
                rhs.append(0.0)

    sol = _solve(rows, rhs)
    dirs: list[complex] = []
    for k in range(n):
        if closed or k < n - 1:
            dirs.append(normalized(delta[k % nseg] * cmath.rect(1.0, sol[th(k)])))
        else:
            dirs.append(normalized(delta[n - 2] * cmath.rect(1.0, -sol[ph(k)])))
    return dirs


def hobby(nodes: Sequence[Node], closed: bool = False) -> list[Cubic]:
    """The cubic segments of Hobby's spline through ``nodes``."""
    dirs = hobby_directions(nodes, closed)
    n = len(nodes)
    out: list[Cubic] = []
    for k in range(n if closed else n - 1):
        a, b = nodes[k], nodes[(k + 1) % n]
        out.append(hobby_segment(a.z, b.z, dirs[k], dirs[(k + 1) % n], a.t_out, b.t_in))
    return out


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting. The systems here have at most a few dozen unknowns."""
    n = len(b)
    m = [[*row, rhs] for row, rhs in zip(a, b, strict=True)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise ValueError("the spline's equations are singular")
        m[col], m[pivot] = m[pivot], m[col]
        for r in range(col + 1, n):
            f = m[r][col] / m[col][col]
            if f != 0.0:
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))) / m[r][r]
    return x
