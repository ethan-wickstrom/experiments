//! Strokes: a skeleton of knots, each carrying a pen, expanded into a closed outline.
//!
//! This is METAFONT's `penpos`/`penstroke` model. A knot is a point on the centre line of a stroke, with the
//! breadth of the pen there and, optionally, the angle of the pen's edge and the direction of travel. The centre
//! line through the knots is a Hobby spline (straight where a knot says so). The outline is the path through the
//! pen's right ends, a cap, the path back through its left ends, and a cap.
//!
//! Every stroke expands to the same number of segments whatever its numbers are, so the masters of a variable
//! font are point-compatible by construction: a glyph program run with a heavier pen yields the same structure.

use crate::geom::{EPS, Node, Seg, V, hobby_directions, hobby_segment, intersect, lame_corner, pt, segment_bounds};

/// A point on a stroke's centre line, and the pen there.
///
/// `w` is the pen's breadth. `pen` is the angle in degrees of the pen's edge, as a line (0 is a horizontal edge,
/// which cuts a vertical stem square; 90 is a vertical edge); `None` holds the pen perpendicular to the path.
/// `dir` is the direction of travel in degrees; `None` lets the spline choose it. `line` makes the segment from
/// this knot to the next one straight. `t_in` and `t_out` are Hobby tensions. `k` overrides the curve from this
/// knot to the next: its control points are placed at the fraction `k` of the way from each knot to the point
/// where the two end tangents meet (0.5523 gives a quarter ellipse, larger is squarer).
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Knot {
    pub z: V,
    pub w: f64,
    pub pen: Option<f64>,
    pub dir: Option<f64>,
    pub line: bool,
    pub t_in: f64,
    pub t_out: f64,
    pub k: Option<f64>,
    /// Makes the curve from this knot to the next a quadrant of the superellipse of this exponent (2 is an
    /// ellipse, 5/2 is Piet Hein's), as two cubics. It takes precedence over `k`.
    pub n: Option<f64>,
}

/// A knot at (x, y) with a pen `w` broad, held perpendicular to the path.
pub fn knot(x: f64, y: f64, w: f64) -> Knot {
    Knot::at(pt(x, y), w)
}

impl Knot {
    pub fn at(z: V, w: f64) -> Knot {
        Knot { z, w, pen: None, dir: None, line: false, t_in: 1.0, t_out: 1.0, k: None, n: None }
    }

    /// Hold the pen's edge at `degrees`.
    pub fn pen(mut self, degrees: f64) -> Knot {
        self.pen = Some(degrees);
        self
    }

    /// Travel through the knot along `degrees`.
    pub fn dir(mut self, degrees: f64) -> Knot {
        self.dir = Some(degrees);
        self
    }

    /// Make the segment to the next knot straight.
    pub fn line(mut self) -> Knot {
        self.line = true;
        self
    }

    /// Make the curve to the next knot a superelliptic corner of squareness `k`.
    pub fn k(mut self, k: f64) -> Knot {
        self.k = Some(k);
        self
    }

    /// Make the curve to the next knot a quadrant of the superellipse of exponent `n`.
    pub fn n(mut self, n: f64) -> Knot {
        self.n = Some(n);
        self
    }

    pub fn tension(mut self, t_in: f64, t_out: f64) -> Knot {
        self.t_in = t_in;
        self.t_out = t_out;
        self
    }
}

/// A closed outline: each segment starts where the previous one ends, and the last ends at the first's start.
#[derive(Clone, Debug, PartialEq)]
pub struct Contour {
    pub segs: Vec<Seg>,
}

const GAUSS3: [(f64, f64); 3] = [
    (0.112_701_665_379_258_3, 5.0 / 18.0), // 0.5 - sqrt(0.15)
    (0.5, 8.0 / 18.0),
    (0.887_298_334_620_741_7, 5.0 / 18.0), // 0.5 + sqrt(0.15)
];

impl Contour {
    pub fn new(segs: Vec<Seg>) -> Contour {
        Contour { segs }
    }

    /// Signed area, exactly: positive when the contour runs counter-clockwise.
    ///
    /// By Green's theorem it is half the integral of B × B′ along the contour. On a cubic the integrand is a
    /// polynomial of degree 5, which three-point Gauss–Legendre quadrature integrates without error.
    pub fn area(&self) -> f64 {
        let mut total = 0.0;
        for s in &self.segs {
            match *s {
                Seg::Line(p0, p1) => total += p0.cross(p1),
                Seg::Cubic(..) => {
                    for (t, weight) in GAUSS3 {
                        total += weight * s.at(t).cross(s.derivative(t));
                    }
                }
            }
        }
        total / 2.0
    }

    pub fn reversed(&self) -> Contour {
        Contour { segs: self.segs.iter().rev().map(Seg::reversed).collect() }
    }

    pub fn oriented(self, counter_clockwise: bool) -> Contour {
        if (self.area() > 0.0) == counter_clockwise { self } else { self.reversed() }
    }

    pub fn mapped(&self, f: impl Fn(V) -> V) -> Contour {
        Contour { segs: self.segs.iter().map(|s| s.mapped(&f)).collect() }
    }

    /// Every on-curve and off-curve point, in order.
    pub fn points(&self) -> Vec<V> {
        let mut out = Vec::new();
        for s in &self.segs {
            match *s {
                Seg::Line(_, p1) => out.push(p1),
                Seg::Cubic(_, c1, c2, p3) => out.extend([c1, c2, p3]),
            }
        }
        out
    }

    /// The contour's structure, which must agree between the masters of a variable font.
    pub fn signature(&self) -> String {
        self.segs.iter().map(|s| if s.is_line() { 'L' } else { 'C' }).collect()
    }

    pub fn bounds(&self) -> Option<(f64, f64, f64, f64)> {
        segment_bounds(&self.segs)
    }
}

pub fn polygon(points: &[V]) -> Contour {
    let n = points.len();
    Contour::new((0..n).map(|i| Seg::Line(points[i], points[(i + 1) % n])).collect()).oriented(true)
}

pub fn rect(x0: f64, y0: f64, x1: f64, y1: f64) -> Contour {
    polygon(&[pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1)])
}

/// Four cubic quadrants around (cx, cy). `k` is the handle length as a fraction of the radius: 0.5523 gives an
/// ellipse, and larger values are squarer (at 1 the shape fills 95% of its box).
pub fn superellipse(cx: f64, cy: f64, rx: f64, ry: f64, k: f64) -> Contour {
    let c = pt(cx, cy);
    let (e, n, w, s) = (c + pt(rx, 0.0), c + pt(0.0, ry), c - pt(rx, 0.0), c - pt(0.0, ry));
    let (hx, hy) = (pt(k * rx, 0.0), pt(0.0, k * ry));
    Contour::new(vec![
        Seg::Cubic(e, e + hy, n + hx, n),
        Seg::Cubic(n, n - hx, w + hy, w),
        Seg::Cubic(w, w - hy, s - hx, s),
        Seg::Cubic(s, s + hx, e - hy, e),
    ])
}

// ---------------------------------------------------------------------------------------------------------------

/// The vector from the knot to the pen's right end, for a pen moving along `travel`.
fn half_pen(knot: &Knot, travel: V) -> Result<V, String> {
    let right = travel.norm().right();
    let Some(angle) = knot.pen else {
        return Ok(right * (knot.w / 2.0));
    };
    let u = V::unit(angle);
    let side = u.dot(right);
    if side.abs() < 1e-6 {
        return Err(format!("the pen at ({}, {}) lies along the path", knot.z.x, knot.z.y));
    }
    Ok(u * (knot.w / 2.0) * if side > 0.0 { 1.0 } else { -1.0 })
}

fn corner_cubic(z0: V, z1: V, d0: V, d1: V, k: f64) -> Option<Seg> {
    let apex = intersect(z0, d0, z1, d1)?;
    if (apex - z0).dot(d0) <= 0.0 || (z1 - apex).dot(d1) <= 0.0 {
        return None;
    }
    Some(Seg::Cubic(z0, z0 + (apex - z0) * k, z1 + (apex - z1) * k, z1))
}

/// One side of a curved stroke segment: a cubic with the centre line's end tangents that passes through the
/// centre line's midpoint displaced by the interpolated pen. For an arc of a circle and a constant pen it is the
/// standard cubic approximation of the concentric arc.
fn offset_cubic(center: &Seg, h0: V, h1: V, side: f64, d0: V, d1: V) -> Seg {
    let Seg::Cubic(c0, cc1, cc2, c3) = *center else { unreachable!("offset_cubic takes a cubic") };
    let p0 = c0 + h0 * side;
    let p3 = c3 + h1 * side;
    let (t0, t1) = (d0.norm(), d1.norm());
    let tm = center.tangent(0.5).norm();
    // the pen at each end, as a complex multiple of the right normal there: breadth and skew together
    let pen_mid = (h0.cdiv(t0.right()) + h1.cdiv(t1.right())) / 2.0;
    let target = center.at(0.5) + pen_mid.cmul(tm.right()) * side;
    let rhs = (target - (p0 + p3) / 2.0) * (8.0 / 3.0);
    let den = t0.cross(t1);
    let chord = (p3 - p0).abs();
    if den.abs() > 0.05 {
        let a = rhs.cross(t1) / den;
        let b = rhs.cross(t0) / den;
        if 0.02 * chord < a && a < 2.0 * chord && 0.02 * chord < b && b < 2.0 * chord {
            return Seg::Cubic(p0, p0 + t0 * a, p3 - t1 * b, p3);
        }
    }
    // nearly parallel end tangents: scale the centre line's handles with the chord
    let c_chord = (c3 - c0).abs();
    let r = if c_chord > EPS { chord / c_chord } else { 1.0 };
    Seg::Cubic(p0, p0 + t0 * ((cc1 - c0).abs() * r), p3 - t1 * ((c3 - cc2).abs() * r), p3)
}

/// The centre line of a stroke: for each interval between two knots its segments (one, or two for a superelliptic
/// corner), and the direction of arrival and of departure at every knot.
pub struct Skeleton {
    pub pieces: Vec<Vec<Seg>>,
    pub arrive: Vec<V>,
    pub depart: Vec<V>,
}

impl Skeleton {
    /// The centre line's segments in order, without the division into intervals.
    pub fn segs(&self) -> Vec<Seg> {
        self.pieces.iter().flatten().copied().collect()
    }
}

/// The centre line through `knots`, interval by interval.
pub fn skeleton(knots: &[Knot], closed: bool) -> Result<Skeleton, String> {
    let n = knots.len();
    if n < 2 {
        return Err("a stroke needs two knots".into());
    }
    let nseg = if closed { n } else { n - 1 };
    let straight: Vec<bool> = (0..nseg).map(|i| knots[i].line).collect();
    let chord: Vec<V> = (0..nseg).map(|i| knots[(i + 1) % n].z - knots[i].z).collect();
    if chord.iter().any(|c| c.abs() < EPS) {
        return Err("consecutive knots coincide".into());
    }

    let mut d_in: Vec<Option<V>> = vec![None; n];
    let mut d_out: Vec<Option<V>> = vec![None; n];
    for i in 0..n {
        let before = if closed {
            Some((i + n - 1) % n)
        } else if i > 0 {
            Some(i - 1)
        } else {
            None
        };
        let after = if closed || i < n - 1 { Some(i) } else { None };
        let given = knots[i].dir.map(V::unit);
        let line_in = before.is_some_and(|b| straight[b]);
        let line_out = after.is_some_and(|a| straight[a]);
        if let (true, Some(b)) = (line_in, before) {
            d_in[i] = Some(chord[b].norm());
        }
        if let (true, Some(a)) = (line_out, after) {
            d_out[i] = Some(chord[a].norm());
        }
        if let Some(g) = given {
            if !line_in {
                d_in[i] = Some(g);
            }
            if !line_out {
                d_out[i] = Some(g);
            }
        } else {
            // a curve leaves a straight segment along the straight segment's direction
            if line_in && !line_out {
                d_out[i] = d_in[i];
            }
            if line_out && !line_in {
                d_in[i] = d_out[i];
            }
        }
    }

    // Solve each maximal run of curved segments as one Hobby spline.
    if closed && !straight.iter().any(|&s| s) {
        let nodes: Vec<Node> = knots
            .iter()
            .enumerate()
            .map(|(i, k)| Node { z: k.z, dir: d_out[i], curl: 1.0, t_in: k.t_in, t_out: k.t_out })
            .collect();
        let dirs = hobby_directions(&nodes, true)?;
        for i in 0..n {
            d_in[i] = Some(dirs[i]);
            d_out[i] = Some(dirs[i]);
        }
    } else {
        for s in 0..nseg {
            let starts_run =
                !straight[s] && if closed { straight[(s + nseg - 1) % nseg] } else { s == 0 || straight[s - 1] };
            if !starts_run {
                continue;
            }
            let mut run = vec![s];
            loop {
                let mut next = run[run.len() - 1] + 1;
                if !closed && next >= nseg {
                    break;
                }
                next %= nseg;
                if straight[next] || next == s {
                    break;
                }
                run.push(next);
            }
            let mut idx = run.clone();
            idx.push((run[run.len() - 1] + 1) % n);
            let last = idx.len() - 1;
            let nodes: Vec<Node> = idx
                .iter()
                .enumerate()
                .map(|(j, &i)| {
                    let fixed = if j == 0 {
                        d_out[i]
                    } else if j == last {
                        d_in[i]
                    } else {
                        d_out[i].or(d_in[i])
                    };
                    Node { z: knots[i].z, dir: fixed, curl: 1.0, t_in: knots[i].t_in, t_out: knots[i].t_out }
                })
                .collect();
            let dirs = hobby_directions(&nodes, false)?;
            for (j, &i) in idx.iter().enumerate() {
                if j > 0 {
                    d_in[i] = Some(dirs[j]);
                }
                if j < last {
                    d_out[i] = Some(dirs[j]);
                }
            }
        }
    }
    let mut arrive = Vec::with_capacity(n);
    let mut depart = Vec::with_capacity(n);
    for i in 0..n {
        // the open ends
        let a = d_in[i].or(d_out[i]).ok_or("a knot has no direction")?;
        let d = d_out[i].or(d_in[i]).ok_or("a knot has no direction")?;
        arrive.push(a);
        depart.push(d);
    }

    let mut pieces = Vec::with_capacity(nseg);
    for i in 0..nseg {
        let (a, b) = (&knots[i], &knots[(i + 1) % n]);
        if straight[i] {
            pieces.push(vec![Seg::Line(a.z, b.z)]);
            continue;
        }
        let j = (i + 1) % n;
        if let Some(two) = a.n.and_then(|e| lame_corner(a.z, b.z, depart[i], arrive[j], e)) {
            pieces.push(two.to_vec());
            continue;
        }
        let corner = a.k.and_then(|k| corner_cubic(a.z, b.z, depart[i], arrive[j], k));
        pieces.push(vec![corner.unwrap_or_else(|| hobby_segment(a.z, b.z, depart[i], arrive[j], a.t_out, b.t_in))]);
    }
    Ok(Skeleton { pieces, arrive, depart })
}

/// The outline of the stroke through `knots`: one contour for an open stroke, two (outer, then inner) for a
/// closed one. Outer contours run counter-clockwise, inner ones clockwise.
pub fn expand(knots: &[Knot], closed: bool) -> Result<Vec<Contour>, String> {
    let n = knots.len();
    let Skeleton { pieces, arrive, depart } = skeleton(knots, closed)?;
    let nseg = pieces.len();
    let straight = |i: usize| pieces[i][0].is_line();

    // The pen's right-hand offset at each knot, on arrival and on departure. They differ only at a corner.
    let mut h_in: Vec<V> = Vec::with_capacity(n);
    let mut h_out: Vec<V> = Vec::with_capacity(n);
    for (i, k) in knots.iter().enumerate() {
        let (a, d) = (arrive[i], depart[i]);
        let smooth = a.cross(d).abs() < 1e-6 && a.dot(d) > 0.0;
        if smooth || k.pen.is_some() {
            let h = half_pen(k, if smooth { a } else { a + d })?;
            h_in.push(h);
            h_out.push(h);
            continue;
        }
        let (ha, hd) = (half_pen(k, a)?, half_pen(k, d)?);
        let before = if closed {
            Some((i + nseg - 1) % nseg)
        } else if i > 0 {
            Some(i - 1)
        } else {
            None
        };
        let after = if closed || i < n - 1 { Some(i) } else { None };
        let mitred = matches!((before, after), (Some(b), Some(f)) if straight(b) && straight(f));
        if mitred {
            // two straight segments meet: each side turns at the intersection of its two edges
            let right = intersect(k.z + ha, a, k.z + hd, d).ok_or("a mitre has no corner")?;
            h_in.push(right - k.z);
            h_out.push(right - k.z);
        } else {
            h_in.push(ha);
            h_out.push(hd);
        }
    }

    let mut sides: Vec<Vec<Seg>> = Vec::with_capacity(2);
    for side in [1.0, -1.0] {
        let mut path: Vec<Seg> = Vec::new();
        for i in 0..nseg {
            let j = (i + 1) % n;
            // the pen at each end of the interval, as a complex multiple of the right normal there, so that it
            // can be blended along the interval: breadth and skew together
            let (r0, r1) = (h_out[i].cdiv(depart[i].right()), h_in[j].cdiv(arrive[j].right()));
            let count = pieces[i].len();
            for (m, piece) in pieces[i].iter().enumerate() {
                let (d_a, h_a) = if m == 0 {
                    (depart[i], h_out[i])
                } else {
                    let d = piece.tangent(0.0).norm();
                    (d, r0.lerp(r1, m as f64 / count as f64).cmul(d.right()))
                };
                let (d_b, h_b) = if m + 1 == count {
                    (arrive[j], h_in[j])
                } else {
                    let d = piece.tangent(1.0).norm();
                    (d, r0.lerp(r1, (m + 1) as f64 / count as f64).cmul(d.right()))
                };
                match *piece {
                    Seg::Line(p0, p1) => path.push(Seg::Line(p0 + h_a * side, p1 + h_b * side)),
                    Seg::Cubic(..) => path.push(offset_cubic(piece, h_a, h_b, side, d_a, d_b)),
                }
            }
            let last = !closed && i == nseg - 1;
            if !last && h_in[j] != h_out[j] {
                // a corner between a curve and something else: bevel it
                path.push(Seg::Line(knots[j].z + h_in[j] * side, knots[j].z + h_out[j] * side));
            }
        }
        sides.push(path);
    }
    let left_path = sides.pop().expect("two sides");
    let right_path = sides.pop().expect("two sides");

    if closed {
        let (a, b) = (Contour::new(right_path), Contour::new(left_path));
        let (outer, inner) = if a.area().abs() >= b.area().abs() { (a, b) } else { (b, a) };
        return Ok(vec![outer.oriented(true), inner.oriented(false)]);
    }
    let back: Vec<Seg> = left_path.iter().rev().map(Seg::reversed).collect();
    let cap_end = Seg::Line(right_path[right_path.len() - 1].end(), back[0].start());
    let cap_start = Seg::Line(back[back.len() - 1].end(), right_path[0].start());
    let mut all = right_path;
    all.push(cap_end);
    all.extend(back);
    all.push(cap_start);
    Ok(vec![Contour::new(all).oriented(true)])
}

/// `knot` after the shear x' = x + slope (y - origin_y), which slants a skeleton for an italic.
///
/// A fixed pen is sheared as a vector, so a stem keeps its horizontal thickness and a bar its vertical one; a
/// perpendicular pen stays perpendicular to the slanted path, so a curve keeps its breadth.
pub fn sheared(knot: &Knot, slope: f64, origin_y: f64) -> Knot {
    if slope == 0.0 {
        return *knot;
    }
    let vec = |v: V| pt(v.x + slope * v.y, v.y);
    let mut out = *knot;
    out.z = pt(knot.z.x + slope * (knot.z.y - origin_y), knot.z.y);
    if let Some(dir) = knot.dir {
        let d = vec(V::unit(dir));
        out.dir = Some(d.y.atan2(d.x).to_degrees());
    }
    if let Some(pen) = knot.pen {
        let h = vec(V::unit(pen) * knot.w);
        out.pen = Some(h.y.atan2(h.x).to_degrees());
        out.w = h.abs();
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geom::flatten;

    fn crossings(contours: &[Contour], y: Option<f64>, x: Option<f64>) -> Vec<f64> {
        let mut out = Vec::new();
        for c in contours {
            let mut prev = c.segs[0].start();
            for s in &c.segs {
                for q in flatten(s, 0.01) {
                    if let Some(y) = y
                        && (prev.y - y) * (q.y - y) < 0.0
                    {
                        out.push(prev.x + (q.x - prev.x) * (y - prev.y) / (q.y - prev.y));
                    }
                    if let Some(x) = x
                        && (prev.x - x) * (q.x - x) < 0.0
                    {
                        out.push(prev.y + (q.y - prev.y) * (x - prev.x) / (q.x - prev.x));
                    }
                    prev = q;
                }
            }
        }
        out.sort_by(f64::total_cmp);
        out
    }

    fn vstem(x: f64, y0: f64, y1: f64, w: f64) -> [Knot; 2] {
        [knot(x, y0, w).pen(0.0).line(), knot(x, y1, w).pen(0.0)]
    }

    fn ring(x0: f64, y0: f64, x1: f64, y1: f64, sw: f64, hw: f64, k: f64) -> [Knot; 4] {
        let (cx, cy) = ((x0 + x1) / 2.0, (y0 + y1) / 2.0);
        let (rx, ry) = ((x1 - x0) / 2.0 - sw / 2.0, (y1 - y0) / 2.0 - hw / 2.0);
        [
            knot(cx + rx, cy, sw).dir(90.0).k(k),
            knot(cx, cy + ry, hw).dir(180.0).k(k),
            knot(cx - rx, cy, sw).dir(-90.0).k(k),
            knot(cx, cy - ry, hw).dir(0.0).k(k),
        ]
    }

    #[test]
    fn a_stem_is_a_rectangle() {
        let c = &expand(&vstem(100.0, 0.0, 500.0, 80.0), false).unwrap()[0];
        assert_eq!(c.bounds(), Some((60.0, 0.0, 140.0, 500.0)));
        assert_eq!(c.signature(), "LLLL");
        assert!((c.area() - 80.0 * 500.0).abs() < 1e-9);
    }

    #[test]
    fn the_outline_runs_counter_clockwise_whichever_way_the_pen_travels() {
        assert!(expand(&vstem(100.0, 0.0, 500.0, 80.0), false).unwrap()[0].area() > 0.0);
        assert!(expand(&vstem(100.0, 500.0, 0.0, 80.0), false).unwrap()[0].area() > 0.0);
    }

    #[test]
    fn two_straight_segments_meet_in_a_mitre() {
        let c = &expand(&[knot(0.0, 100.0, 20.0).line(), knot(0.0, 0.0, 20.0).line(), knot(100.0, 0.0, 20.0)], false)
            .unwrap()[0];
        let corners: Vec<(i64, i64)> =
            c.segs.iter().map(|s| (s.end().x.round() as i64, s.end().y.round() as i64)).collect();
        assert!(corners.contains(&(-10, -10)));
        assert!(corners.contains(&(10, 10)));
        assert_eq!(c.segs.len(), 6);
    }

    #[test]
    fn a_pen_along_the_path_is_refused() {
        assert!(expand(&[knot(0.0, 0.0, 20.0).pen(90.0).line(), knot(0.0, 100.0, 20.0).pen(90.0)], false).is_err());
    }

    #[test]
    fn a_ring_has_an_outer_and_an_inner_contour() {
        let c = expand(&ring(0.0, 0.0, 400.0, 500.0, 80.0, 60.0, 0.5523), true).unwrap();
        assert!(c[0].area() > 0.0 && c[1].area() < 0.0);
        let round = |b: (f64, f64, f64, f64)| {
            ((b.0 * 1e6).round() / 1e6, (b.1 * 1e6).round() / 1e6, (b.2 * 1e6).round() / 1e6, (b.3 * 1e6).round() / 1e6)
        };
        assert_eq!(round(c[0].bounds().unwrap()), (0.0, 0.0, 400.0, 500.0));
        assert_eq!(round(c[1].bounds().unwrap()), (80.0, 60.0, 320.0, 440.0));
    }

    #[test]
    fn a_circular_ring_keeps_its_breadth_all_round() {
        let c = expand(&ring(-250.0, -250.0, 250.0, 250.0, 80.0, 80.0, 0.5523), true).unwrap();
        for (contour, r) in [(&c[0], 250.0), (&c[1], 170.0)] {
            for s in &contour.segs {
                for q in flatten(s, 0.01) {
                    assert!((q.abs() - r).abs() < 0.12);
                }
            }
        }
    }

    #[test]
    fn a_squarish_ring_keeps_its_breadth_on_the_diagonal() {
        let c = expand(&ring(-250.0, -250.0, 250.0, 250.0, 80.0, 80.0, 0.66), true).unwrap();
        let d = 0.5f64.sqrt();
        let reach = |contour: &Contour| {
            contour.segs.iter().flat_map(|s| flatten(s, 0.01)).map(|q| q.x * d + q.y * d).fold(f64::MIN, f64::max)
        };
        assert!((reach(&c[0]) - reach(&c[1]) - 80.0).abs() < 0.5);
    }

    #[test]
    fn a_curve_leaves_a_straight_segment_smoothly() {
        let c =
            &expand(&[knot(0.0, 0.0, 40.0).line(), knot(0.0, 100.0, 40.0), knot(100.0, 200.0, 40.0).dir(0.0)], false)
                .unwrap()[0];
        assert_eq!(c.signature(), "LCLCLL");
        let Some(Seg::Cubic(p0, c1, ..)) = c.segs.iter().find(|s| !s.is_line()).copied() else { unreachable!() };
        assert!((c1 - p0).x.abs() < 1e-9);
    }

    #[test]
    fn structure_does_not_depend_on_breadth() {
        let thin = expand(&ring(0.0, 0.0, 400.0, 500.0, 40.0, 30.0, 0.62), true).unwrap();
        let fat = expand(&ring(0.0, 0.0, 400.0, 500.0, 140.0, 110.0, 0.62), true).unwrap();
        let sig = |v: &[Contour]| v.iter().map(Contour::signature).collect::<Vec<_>>();
        assert_eq!(sig(&thin), sig(&fat));
    }

    #[test]
    fn a_sheared_stem_keeps_its_horizontal_thickness_and_a_bar_its_vertical_one() {
        let slope = 10f64.to_radians().tan();
        let stem: Vec<Knot> = vstem(100.0, 0.0, 500.0, 80.0).iter().map(|k| sheared(k, slope, 0.0)).collect();
        let c = expand(&stem, false).unwrap();
        let x = crossings(&c, Some(250.0), None);
        assert!((x[1] - x[0] - 80.0).abs() < 1e-9);
        let bar = [knot(0.0, 300.0, 60.0).pen(90.0).line(), knot(400.0, 300.0, 60.0).pen(90.0)];
        let bar: Vec<Knot> = bar.iter().map(|k| sheared(k, slope, 0.0)).collect();
        let c = expand(&bar, false).unwrap();
        let y = crossings(&c, None, Some(200.0));
        assert!((y[1] - y[0] - 60.0).abs() < 1e-9);
    }

    #[test]
    fn shapes_run_counter_clockwise() {
        assert!((rect(0.0, 0.0, 10.0, 20.0).area() - 200.0).abs() < 1e-9);
        assert!((superellipse(0.0, 0.0, 100.0, 100.0, 0.5523).area() - std::f64::consts::PI * 1e4).abs() < 12.0);
    }
}
