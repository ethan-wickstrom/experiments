"""Strokes: the outline a pen leaves along a skeleton."""

from __future__ import annotations

import math
import unittest

from rachis.geom import Cubic, Line, flatten, pt, segment_bounds
from rachis.parts import cut, diag, flip, mirror, ring, turn, vstem
from rachis.pen import Contour, Knot, expand, rect, sheared, superellipse


def crossings(contours: list[Contour], *, y: float | None = None, x: float | None = None) -> list[float]:
    """Where a horizontal line at ``y`` (or a vertical one at ``x``) crosses the contours, ascending."""
    out: list[float] = []
    for c in contours:
        prev = c.segs[0].start
        for s in c.segs:
            for q in flatten(s, 0.01):
                if y is not None and (prev.imag - y) * (q.imag - y) < 0:
                    out.append(prev.real + (q.real - prev.real) * (y - prev.imag) / (q.imag - prev.imag))
                if x is not None and (prev.real - x) * (q.real - x) < 0:
                    out.append(prev.imag + (q.imag - prev.imag) * (x - prev.real) / (q.real - prev.real))
                prev = q
    return sorted(out)


class Straight(unittest.TestCase):
    def test_a_stem_is_a_rectangle(self) -> None:
        (c,) = expand(vstem(100, 0, 500, 80))
        self.assertEqual(segment_bounds(c.segs), (60, 0, 140, 500))
        self.assertEqual(c.signature(), "LLLL")
        self.assertAlmostEqual(c.area(), 80 * 500)

    def test_the_outline_runs_counter_clockwise_whichever_way_the_pen_travels(self) -> None:
        up = expand(vstem(100, 0, 500, 80))[0]
        down = expand(vstem(100, 500, 0, 80))[0]
        self.assertGreater(up.area(), 0)
        self.assertGreater(down.area(), 0)

    def test_a_diagonal_cut_horizontally_keeps_its_thickness(self) -> None:
        (c,) = expand(diag(100, 0, 400, 500, 60))
        x0, x1 = crossings([c], y=250)
        angle = math.atan2(500, 300)
        self.assertAlmostEqual((x1 - x0) * math.sin(angle), 60, places=6)
        self.assertEqual(segment_bounds(c.segs)[1::2], (0, 500))

    def test_two_straight_segments_meet_in_a_mitre(self) -> None:
        (c,) = expand([Knot(pt(0, 100), 20, line=True), Knot(0j, 20, line=True), Knot(pt(100, 0), 20)])
        corners = {(round(s.end.real), round(s.end.imag)) for s in c.segs}
        self.assertIn((-10, -10), corners)
        self.assertIn((10, 10), corners)
        self.assertEqual(len(c.segs), 6)

    def test_a_pen_along_the_path_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            expand([Knot(0j, 20, pen=90, line=True), Knot(pt(0, 100), 20, pen=90)])


class Curved(unittest.TestCase):
    def test_a_ring_has_an_outer_and_an_inner_contour(self) -> None:
        outer, inner = expand(ring(0, 0, 400, 500, 80, 60, 0.5523), closed=True)
        self.assertGreater(outer.area(), 0)
        self.assertLess(inner.area(), 0)
        self.assertEqual(tuple(round(v, 6) for v in segment_bounds(outer.segs)), (0, 0, 400, 500))
        self.assertEqual(tuple(round(v, 6) for v in segment_bounds(inner.segs)), (80, 60, 320, 440))

    def test_a_circular_ring_keeps_its_breadth_all_round(self) -> None:
        outer, inner = expand(ring(-250, -250, 250, 250, 80, 80, 0.5523), closed=True)
        for c, r in ((outer, 250.0), (inner, 170.0)):
            for s in c.segs:
                for q in flatten(s, 0.01):
                    self.assertAlmostEqual(abs(q), r, delta=0.12)

    def test_a_squarish_ring_keeps_its_breadth_on_the_diagonal(self) -> None:
        # The sides are offsets of the centre line through its midpoint, so the stroke does not thin or swell there.
        outer, inner = expand(ring(-250, -250, 250, 250, 80, 80, 0.66), closed=True)
        d = math.sqrt(0.5)
        far = max(q.real * d + q.imag * d for s in outer.segs for q in flatten(s, 0.01))
        near = max(q.real * d + q.imag * d for s in inner.segs for q in flatten(s, 0.01))
        self.assertAlmostEqual(far - near, 80, delta=0.5)

    def test_a_curve_leaves_a_straight_segment_smoothly(self) -> None:
        (c,) = expand([Knot(0j, 40, line=True), Knot(pt(0, 100), 40), Knot(pt(100, 200), 40, dir=0)])
        kinds = c.signature()
        self.assertEqual(kinds, "LCLCLL")
        first_curve = next(s for s in c.segs if isinstance(s, Cubic))
        self.assertAlmostEqual((first_curve.c1 - first_curve.p0).real, 0, places=9)

    def test_a_vertical_cut_ends_a_curve_on_one_x(self) -> None:
        (c,) = expand([Knot(pt(0, 0), 60, dir=0), cut(200, 80, 60, 40)])
        ends = [s for s in c.segs if isinstance(s, Line)]
        self.assertTrue(any(abs(s.p0.real - 200) < 1e-9 and abs(s.p1.real - 200) < 1e-9 for s in ends))

    def test_structure_does_not_depend_on_breadth(self) -> None:
        thin = expand(ring(0, 0, 400, 500, 40, 30, 0.62), closed=True)
        fat = expand(ring(0, 0, 400, 500, 140, 110, 0.62), closed=True)
        self.assertEqual([c.signature() for c in thin], [c.signature() for c in fat])


class Symmetries(unittest.TestCase):
    def test_turn_is_mirror_then_flip(self) -> None:
        knots = [Knot(pt(10, 20), 30, pen=0, dir=80), Knot(pt(90, 140), 30, dir=10)]
        a = turn(knots, 50, 60)
        b = flip(mirror(knots, 50), 60)
        for ka, kb in zip(a, b, strict=True):
            self.assertAlmostEqual(abs(ka.z - kb.z), 0)
            assert ka.dir is not None and kb.dir is not None
            self.assertAlmostEqual(math.cos(math.radians(ka.dir - kb.dir)), 1.0)

    def test_mirrored_stroke_is_the_mirror_image(self) -> None:
        knots = [Knot(pt(10, 0), 30, pen=0, dir=90), Knot(pt(90, 140), 24, dir=0), cut(170, 90, 24, -40)]
        (a,) = expand(knots)
        (b,) = expand(mirror(knots, 100))
        ax0, ay0, ax1, ay1 = segment_bounds(a.segs)
        bx0, by0, bx1, by1 = segment_bounds(b.segs)
        self.assertAlmostEqual(200 - ax1, bx0)
        self.assertAlmostEqual(200 - ax0, bx1)
        self.assertAlmostEqual(ay0, by0)
        self.assertAlmostEqual(ay1, by1)
        self.assertAlmostEqual(a.area(), b.area())


class Shear(unittest.TestCase):
    def test_a_sheared_stem_keeps_its_horizontal_thickness(self) -> None:
        slope = math.tan(math.radians(10))
        (c,) = expand([sheared(k, slope, 0.0) for k in vstem(100, 0, 500, 80)])
        x0, x1 = crossings([c], y=250)
        self.assertAlmostEqual(x1 - x0, 80, places=9)
        self.assertEqual(segment_bounds(c.segs)[1::2], (0, 500))

    def test_a_sheared_bar_keeps_its_vertical_thickness(self) -> None:
        slope = math.tan(math.radians(10))
        bar = [Knot(pt(0, 300), 60, pen=90, line=True), Knot(pt(400, 300), 60, pen=90)]
        (c,) = expand([sheared(k, slope, 0.0) for k in bar])
        y0, y1 = crossings([c], x=200)
        self.assertAlmostEqual(y1 - y0, 60, places=9)


class Shapes(unittest.TestCase):
    def test_rect_and_superellipse_run_counter_clockwise(self) -> None:
        self.assertAlmostEqual(rect(0, 0, 10, 20).area(), 200)
        self.assertAlmostEqual(superellipse(0, 0, 100, 100).area(), math.pi * 1e4, delta=12)
        self.assertAlmostEqual(superellipse(0, 0, 100, 50, k=1.0).area(), 0.95 * 4 * 100 * 50, delta=1)


if __name__ == "__main__":
    unittest.main()
