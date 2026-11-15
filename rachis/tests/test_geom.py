"""The kernel's geometry: Béziers and Hobby's spline."""

from __future__ import annotations

import itertools
import math
import unittest

from rachis.geom import Cubic, Node, hobby, hobby_directions, hobby_segment, intersect, pt, unit, velocity


class Velocity(unittest.TestCase):
    def test_symmetric_arc_is_the_circle_approximation(self) -> None:
        # f(t, t) = 2 / (3 (1 + cos t)): with it, a cubic through two points of a circle hugs the arc between them.
        for deg in (10, 30, 45, 60, 90):
            t = math.radians(deg)
            self.assertAlmostEqual(velocity(t, t), 2 / (3 * (1 + math.cos(t))), places=12)

    def test_quarter_circle_handle_is_kappa(self) -> None:
        seg = hobby_segment(1 + 0j, 1j, 1j, -1 + 0j)
        self.assertAlmostEqual(abs(seg.c1 - seg.p0), 4 / 3 * (math.sqrt(2) - 1), places=12)


class Hobby(unittest.TestCase):
    def test_closed_path_through_a_circle_is_nearly_a_circle(self) -> None:
        for n in (3, 4, 6, 8):
            segs = hobby([Node(unit(360 * i / n)) for i in range(n)], closed=True)
            err = max(abs(abs(s.at(t / 32)) - 1) for s in segs for t in range(33))
            self.assertLess(err, 0.004 if n == 3 else 0.0003, n)

    def test_open_path_through_a_semicircle(self) -> None:
        # (0,0)..(100,100)..(200,0) with curl 1 at both ends lies on the circle about (100, 0).
        segs = hobby([Node(0j), Node(pt(100, 100)), Node(pt(200, 0))])
        for got, want in zip(
            (segs[0].c1, segs[0].c2, segs[1].c1, segs[1].c2),
            (pt(0, 55.228), pt(44.772, 100), pt(155.228, 100), pt(200, 55.228)),
            strict=True,
        ):
            self.assertAlmostEqual(abs(got - want), 0, places=2)

    def test_directions_are_continuous_and_given_ones_are_kept(self) -> None:
        nodes = [Node(0j, dir=unit(90)), Node(pt(120, 160)), Node(pt(300, 140)), Node(pt(420, 0), dir=unit(-90))]
        dirs = hobby_directions(nodes)
        self.assertAlmostEqual(abs(dirs[0] - unit(90)), 0, places=12)
        self.assertAlmostEqual(abs(dirs[3] - unit(-90)), 0, places=12)
        segs = hobby(nodes)
        for a, b in itertools.pairwise(segs):
            ta, tb = a.tangent(1.0), b.tangent(0.0)
            self.assertAlmostEqual(ta.real * tb.imag - ta.imag * tb.real, 0, places=6)

    def test_mock_curvature_is_continuous(self) -> None:
        # At an interior knot the linearised curvature of the two segments agrees: the property the equations solve.
        nodes = [Node(0j), Node(pt(100, 80)), Node(pt(260, 60)), Node(pt(300, -90))]
        dirs = hobby_directions(nodes)
        import cmath

        for k in (1, 2):
            d_in, d_out = nodes[k].z - nodes[k - 1].z, nodes[k + 1].z - nodes[k].z
            th_prev = cmath.phase(dirs[k - 1] / d_in)
            ph_k = cmath.phase(d_in / dirs[k])
            th_k = cmath.phase(dirs[k] / d_out)
            ph_next = cmath.phase(d_out / dirs[k + 1])
            left = ((th_prev + ph_k) - 3 * ph_k) / abs(d_in)
            right = ((th_k + ph_next) - 3 * th_k) / abs(d_out)
            self.assertAlmostEqual(left, right, places=9)

    def test_tension_pulls_towards_the_chord(self) -> None:
        loose = hobby([Node(0j, dir=unit(60)), Node(100 + 0j, dir=unit(-60))])[0]
        tight = hobby([Node(0j, dir=unit(60), t_out=2.0), Node(100 + 0j, dir=unit(-60), t_in=2.0)])[0]
        self.assertLess(tight.at(0.5).imag, loose.at(0.5).imag)

    def test_coincident_knots_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            hobby([Node(0j), Node(0j), Node(1 + 0j)])


class Beziers(unittest.TestCase):
    def test_split_keeps_the_curve(self) -> None:
        c = Cubic(0j, pt(10, 40), pt(60, 50), pt(90, 0))
        a, b = c.split(0.3)
        self.assertAlmostEqual(abs(a.at(0.5) - c.at(0.15)), 0, places=12)
        self.assertAlmostEqual(abs(b.at(0.5) - c.at(0.65)), 0, places=12)

    def test_extrema(self) -> None:
        c = Cubic(0j, pt(0, 50), pt(100, 50), pt(100, 0))
        (t,) = c.extrema()
        self.assertAlmostEqual(t, 0.5)
        self.assertAlmostEqual(c.at(t).imag, 37.5)

    def test_intersect(self) -> None:
        self.assertEqual(intersect(0j, 1 + 0j, pt(5, 5), 1j), pt(5, 0))
        self.assertIsNone(intersect(0j, 1 + 0j, 1j, 2 + 0j))


if __name__ == "__main__":
    unittest.main()
