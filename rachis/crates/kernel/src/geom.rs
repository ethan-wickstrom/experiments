//! Plane geometry on complex numbers: cubic Béziers and Hobby's interpolating splines.
//!
//! A point or vector is a [`V`], read as the complex number `x + iy`. Multiplying by `V::unit(a)` rotates by
//! `a` degrees, and the phase of `b / a` is the turning angle from `a` to `b`, which is why METAFONT, and this
//! kernel after it, do their geometry in the complex plane.
//!
//! The spline is John Hobby's ("Smooth, easy to compute interpolating splines", Discrete & Computational
//! Geometry 1, 1986), in the form METAFONT uses (The METAFONTbook, chapter 14; mf.web, "Choosing control
//! points"). Given knots and, optionally, directions at some of them, it picks the remaining directions so that
//! an approximation of curvature (the "mock curvature", linear in the angles) is continuous at every knot, then
//! places each segment's control points with the velocity function [`velocity`].

use std::ops::{Add, Div, Mul, Neg, Sub};

pub const EPS: f64 = 1e-9;

/// A point or a vector of the plane, as the complex number `x + iy`.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct V {
    pub x: f64,
    pub y: f64,
}

pub const fn pt(x: f64, y: f64) -> V {
    V { x, y }
}

impl V {
    pub const ZERO: V = V { x: 0.0, y: 0.0 };

    /// The unit vector at `degrees` counter-clockwise from the positive x axis.
    pub fn unit(degrees: f64) -> V {
        V::polar(1.0, degrees.to_radians())
    }

    pub fn polar(length: f64, radians: f64) -> V {
        V { x: length * radians.cos(), y: length * radians.sin() }
    }

    pub fn abs(self) -> f64 {
        self.x.hypot(self.y)
    }

    /// The argument in radians, in (-π, π].
    pub fn phase(self) -> f64 {
        self.y.atan2(self.x)
    }

    /// The direction in degrees, in (-180, 180].
    pub fn angle(self) -> f64 {
        self.phase().to_degrees()
    }

    /// The unit vector along `self`. A zero vector has no direction.
    pub fn norm(self) -> V {
        let n = self.abs();
        assert!(n >= EPS, "a zero vector has no direction");
        self / n
    }

    pub fn cross(self, o: V) -> f64 {
        self.x * o.y - self.y * o.x
    }

    pub fn dot(self, o: V) -> f64 {
        self.x * o.x + self.y * o.y
    }

    /// The complex product.
    pub fn cmul(self, o: V) -> V {
        V { x: self.x * o.x - self.y * o.y, y: self.x * o.y + self.y * o.x }
    }

    /// The complex quotient.
    pub fn cdiv(self, o: V) -> V {
        let d = o.x * o.x + o.y * o.y;
        V { x: (self.x * o.x + self.y * o.y) / d, y: (self.y * o.x - self.x * o.y) / d }
    }

    /// Turned 90 degrees to the right (multiplied by -i).
    pub fn right(self) -> V {
        V { x: self.y, y: -self.x }
    }

    /// Turned 90 degrees to the left (multiplied by i).
    pub fn left(self) -> V {
        V { x: -self.y, y: self.x }
    }

    pub fn lerp(self, o: V, t: f64) -> V {
        self + (o - self) * t
    }
}

impl Add for V {
    type Output = V;
    fn add(self, o: V) -> V {
        V { x: self.x + o.x, y: self.y + o.y }
    }
}

impl Sub for V {
    type Output = V;
    fn sub(self, o: V) -> V {
        V { x: self.x - o.x, y: self.y - o.y }
    }
}

impl Neg for V {
    type Output = V;
    fn neg(self) -> V {
        V { x: -self.x, y: -self.y }
    }
}

impl Mul<f64> for V {
    type Output = V;
    fn mul(self, k: f64) -> V {
        V { x: self.x * k, y: self.y * k }
    }
}

impl Mul<V> for f64 {
    type Output = V;
    fn mul(self, v: V) -> V {
        V { x: self * v.x, y: self * v.y }
    }
}

impl Div<f64> for V {
    type Output = V;
    fn div(self, k: f64) -> V {
        V { x: self.x / k, y: self.y / k }
    }
}

/// Where the line through `p` along `u` meets the line through `q` along `v`; `None` if they are parallel.
pub fn intersect(p: V, u: V, q: V, v: V) -> Option<V> {
    let den = u.cross(v);
    if den.abs() < EPS * (u.abs() * v.abs()).max(1.0) {
        return None;
    }
    Some(p + u * ((q - p).cross(v) / den))
}

/// A straight line or a cubic Bézier.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Seg {
    Line(V, V),
    Cubic(V, V, V, V),
}

impl Seg {
    pub fn start(&self) -> V {
        match *self {
            Seg::Line(p0, _) | Seg::Cubic(p0, ..) => p0,
        }
    }

    pub fn end(&self) -> V {
        match *self {
            Seg::Line(_, p1) => p1,
            Seg::Cubic(.., p3) => p3,
        }
    }

    pub fn is_line(&self) -> bool {
        matches!(self, Seg::Line(..))
    }

    pub fn at(&self, t: f64) -> V {
        match *self {
            Seg::Line(p0, p1) => p0.lerp(p1, t),
            Seg::Cubic(p0, c1, c2, p3) => {
                let s = 1.0 - t;
                p0 * (s * s * s) + c1 * (3.0 * s * s * t) + c2 * (3.0 * s * t * t) + p3 * (t * t * t)
            }
        }
    }

    /// The derivative at `t`; at an end of a cubic whose handle has zero length, the limit direction.
    pub fn tangent(&self, t: f64) -> V {
        match *self {
            Seg::Line(p0, p1) => p1 - p0,
            Seg::Cubic(p0, c1, c2, p3) => {
                let s = 1.0 - t;
                let d = (c1 - p0) * (3.0 * s * s) + (c2 - c1) * (6.0 * s * t) + (p3 - c2) * (3.0 * t * t);
                if d.abs() > EPS {
                    d
                } else if t < 0.5 {
                    if (c2 - p0).abs() > EPS { c2 - p0 } else { p3 - p0 }
                } else if (p3 - c1).abs() > EPS {
                    p3 - c1
                } else {
                    p3 - p0
                }
            }
        }
    }

    /// The raw derivative of a cubic at `t` (zero where a handle has zero length).
    pub fn derivative(&self, t: f64) -> V {
        match *self {
            Seg::Line(p0, p1) => p1 - p0,
            Seg::Cubic(p0, c1, c2, p3) => {
                let s = 1.0 - t;
                (c1 - p0) * (3.0 * s * s) + (c2 - c1) * (6.0 * s * t) + (p3 - c2) * (3.0 * t * t)
            }
        }
    }

    /// De Casteljau's subdivision at `t`.
    pub fn split(&self, t: f64) -> (Seg, Seg) {
        match *self {
            Seg::Line(p0, p1) => {
                let m = p0.lerp(p1, t);
                (Seg::Line(p0, m), Seg::Line(m, p1))
            }
            Seg::Cubic(p0, c1, c2, p3) => {
                let a = p0.lerp(c1, t);
                let b = c1.lerp(c2, t);
                let c = c2.lerp(p3, t);
                let d = a.lerp(b, t);
                let e = b.lerp(c, t);
                let m = d.lerp(e, t);
                (Seg::Cubic(p0, a, d, m), Seg::Cubic(m, e, c, p3))
            }
        }
    }

    pub fn reversed(&self) -> Seg {
        match *self {
            Seg::Line(p0, p1) => Seg::Line(p1, p0),
            Seg::Cubic(p0, c1, c2, p3) => Seg::Cubic(p3, c2, c1, p0),
        }
    }

    pub fn mapped(&self, f: &impl Fn(V) -> V) -> Seg {
        match *self {
            Seg::Line(p0, p1) => Seg::Line(f(p0), f(p1)),
            Seg::Cubic(p0, c1, c2, p3) => Seg::Cubic(f(p0), f(c1), f(c2), f(p3)),
        }
    }

    /// Parameters strictly inside (0, 1) where x or y is stationary, ascending.
    pub fn extrema(&self) -> Vec<f64> {
        let Seg::Cubic(p0, c1, c2, p3) = *self else {
            return Vec::new();
        };
        let mut found = Vec::new();
        for part in [|v: V| v.x, |v: V| v.y] {
            let (q0, q1, q2, q3) = (part(p0), part(c1), part(c2), part(p3));
            // derivative / 3 = a t^2 + b t + c
            let a = -q0 + 3.0 * q1 - 3.0 * q2 + q3;
            let b = 2.0 * (q0 - 2.0 * q1 + q2);
            let c = q1 - q0;
            found.extend(quadratic_roots(a, b, c).into_iter().filter(|&t| 1e-4 < t && t < 1.0 - 1e-4));
        }
        found.sort_by(f64::total_cmp);
        found
    }
}

fn quadratic_roots(a: f64, b: f64, c: f64) -> Vec<f64> {
    if a.abs() < 1e-12 {
        return if b.abs() < 1e-12 { Vec::new() } else { vec![-c / b] };
    }
    let disc = b * b - 4.0 * a * c;
    if disc < 0.0 {
        return Vec::new();
    }
    let r = disc.sqrt();
    let q = if b != 0.0 { -0.5 * (b + r.copysign(b)) } else { 0.5 * r };
    let mut roots = vec![q / a];
    if q.abs() > 1e-12 {
        roots.push(c / q);
    }
    roots
}

/// Points along `seg` after its start, ending at its end, within `tolerance` of the curve.
pub fn flatten(seg: &Seg, tolerance: f64) -> Vec<V> {
    match *seg {
        Seg::Line(_, p1) => vec![p1],
        Seg::Cubic(p0, c1, c2, p3) => {
            // the second difference bounds the deviation of a cubic from its chord
            let dd = (p0 - c1 * 2.0 + c2).abs().max((c1 - c2 * 2.0 + p3).abs());
            let n = ((0.75 * dd / tolerance).sqrt().ceil() as usize).max(1);
            (1..=n).map(|i| seg.at(i as f64 / n as f64)).collect()
        }
    }
}

/// The exact bounding box of a chain of segments: (x0, y0, x1, y1).
pub fn segment_bounds<'a>(segs: impl IntoIterator<Item = &'a Seg>) -> Option<(f64, f64, f64, f64)> {
    let mut b: Option<(f64, f64, f64, f64)> = None;
    let mut add = |p: V| {
        b = Some(match b {
            None => (p.x, p.y, p.x, p.y),
            Some((x0, y0, x1, y1)) => (x0.min(p.x), y0.min(p.y), x1.max(p.x), y1.max(p.y)),
        });
    };
    for s in segs {
        add(s.start());
        add(s.end());
        for t in s.extrema() {
            add(s.at(t));
        }
    }
    b
}

// ---------------------------------------------------------------------------------------------------------------
// Hobby's spline

/// METAFONT's velocity function f(θ, φ): the distance of a control point from its knot, as a fraction of the
/// chord, for a segment that leaves at angle θ and arrives at angle φ (radians, both measured from the chord).
///
/// For θ = φ it is 2 / (3 (1 + cos θ)), which makes the cubic through two points of a circle the standard
/// approximation of the arc between them.
pub fn velocity(theta: f64, phi: f64) -> f64 {
    let (st, ct) = theta.sin_cos();
    let (sf, cf) = phi.sin_cos();
    let num = 2.0 + 2f64.sqrt() * (st - sf / 16.0) * (sf - st / 16.0) * (ct - cf);
    let den = 3.0 * (1.0 + 0.5 * (5f64.sqrt() - 1.0) * ct + 0.5 * (3.0 - 5f64.sqrt()) * cf);
    num / den
}

/// The cubic from `z0` to `z1` that leaves along `d0` and arrives along `d1`. `t0` and `t1` are METAFONT's
/// tensions at the two ends: 1 is the default, larger values pull the curve towards the chord.
pub fn hobby_segment(z0: V, z1: V, d0: V, d1: V, t0: f64, t1: f64) -> Seg {
    let chord = z1 - z0;
    let theta = d0.cdiv(chord).phase();
    let phi = chord.cdiv(d1).phase();
    let c1 = z0 + chord.cmul(V::polar(velocity(theta, phi) / t0, theta));
    let c2 = z1 - chord.cmul(V::polar(velocity(phi, theta) / t1, -phi));
    Seg::Cubic(z0, c1, c2, z1)
}

/// A knot of a Hobby spline.
///
/// `dir`, when given, is the direction of travel through the knot. `curl` applies only at the ends of an open
/// path with no direction there: the mock curvature at the end is `curl` times the mock curvature at its
/// neighbour. `t_in` and `t_out` are the tensions of the segments arriving at and leaving the knot.
#[derive(Clone, Copy, Debug)]
pub struct Node {
    pub z: V,
    pub dir: Option<V>,
    pub curl: f64,
    pub t_in: f64,
    pub t_out: f64,
}

impl Node {
    pub fn new(z: V) -> Node {
        Node { z, dir: None, curl: 1.0, t_in: 1.0, t_out: 1.0 }
    }

    pub fn dir(mut self, d: V) -> Node {
        self.dir = Some(d);
        self
    }

    pub fn tension(mut self, t_in: f64, t_out: f64) -> Node {
        self.t_in = t_in;
        self.t_out = t_out;
        self
    }
}

/// The direction of travel (a unit vector) at every node of the spline through `nodes`.
pub fn hobby_directions(nodes: &[Node], closed: bool) -> Result<Vec<V>, String> {
    let n = nodes.len();
    if n < 2 {
        return Err("a path needs two knots".into());
    }
    let nseg = if closed { n } else { n - 1 };
    if (0..nseg).any(|i| (nodes[(i + 1) % n].z - nodes[i].z).abs() < EPS) {
        return Err("consecutive knots coincide".into());
    }
    if n == 2 && !closed && nodes[0].dir.is_none() && nodes[1].dir.is_none() {
        let d = (nodes[1].z - nodes[0].z).norm();
        return Ok(vec![d, d]);
    }

    let delta: Vec<V> = (0..nseg).map(|k| nodes[(k + 1) % n].z - nodes[k].z).collect();
    let dist: Vec<f64> = delta.iter().map(|d| d.abs()).collect();

    // Unknowns: theta[k] for the departure from knot k along segment k, phi[k] for the arrival at knot k along
    // segment k-1. Index theta at 2k and phi at 2k+1. Knots with no such segment keep a trivial equation.
    let size = 2 * n;
    let th = |k: usize| 2 * (k % n);
    let ph = |k: usize| 2 * (k % n) + 1;
    let mut rows: Vec<Vec<f64>> = Vec::with_capacity(size);
    let mut rhs: Vec<f64> = Vec::with_capacity(size);

    for k in 0..n {
        let node = &nodes[k];
        let has_in = closed || k > 0;
        let has_out = closed || k < n - 1;
        if has_in && has_out {
            let before = if closed { (k + n - 1) % n } else { k - 1 };
            let d_in = delta[before];
            let d_out = delta[k % nseg];
            if let Some(dir) = node.dir {
                let mut r = vec![0.0; size];
                r[th(k)] = 1.0;
                rows.push(r);
                rhs.push(dir.cdiv(d_out).phase());
                let mut r = vec![0.0; size];
                r[ph(k)] = 1.0;
                rows.push(r);
                rhs.push(d_in.cdiv(dir).phase());
                continue;
            }
            let psi = d_out.cdiv(d_in).phase();
            // the direction is continuous: theta_k + phi_k + psi_k = 0
            let mut r = vec![0.0; size];
            r[th(k)] = 1.0;
            r[ph(k)] = 1.0;
            rows.push(r);
            rhs.push(-psi);
            // the mock curvature is continuous:
            //   tb_k^2 / d_{k-1} * ((theta_{k-1} + phi_k) / ta_{k-1} - 3 phi_k)
            // = ta_k^2 / d_k     * ((theta_k + phi_{k+1}) / tb_{k+1} - 3 theta_k)
            let prev = &nodes[(k + n - 1) % n];
            let next = &nodes[(k + 1) % n];
            let left = node.t_in * node.t_in / dist[before];
            let right = node.t_out * node.t_out / dist[k % nseg];
            let mut r = vec![0.0; size];
            r[th(k + n - 1)] += left / prev.t_out;
            r[ph(k)] += left / prev.t_out - 3.0 * left;
            r[th(k)] -= right / next.t_in - 3.0 * right;
            r[ph(k + 1)] -= right / next.t_in;
            rows.push(r);
            rhs.push(0.0);
        } else if has_out {
            // the first knot of an open path
            let next = &nodes[1];
            let mut r = vec![0.0; size];
            r[ph(k)] = 1.0; // unused unknown
            rows.push(r);
            rhs.push(0.0);
            let mut r = vec![0.0; size];
            if let Some(dir) = node.dir {
                r[th(0)] = 1.0;
                rows.push(r);
                rhs.push(dir.cdiv(delta[0]).phase());
            } else {
                // curvature at knot 0 = curl * curvature at knot 1, both on segment 0
                let (a, b, g) = (node.t_out, next.t_in, node.curl);
                r[th(0)] = a * a * (1.0 / b - 3.0) - g * b * b / a;
                r[ph(1)] = a * a / b - g * b * b * (1.0 / a - 3.0);
                rows.push(r);
                rhs.push(0.0);
            }
        } else {
            // the last knot of an open path
            let prev = &nodes[n - 2];
            let mut r = vec![0.0; size];
            r[th(k)] = 1.0; // unused unknown
            rows.push(r);
            rhs.push(0.0);
            let mut r = vec![0.0; size];
            if let Some(dir) = node.dir {
                r[ph(k)] = 1.0;
                rows.push(r);
                rhs.push(delta[n - 2].cdiv(dir).phase());
            } else {
                let (a, b, g) = (prev.t_out, node.t_in, node.curl);
                r[ph(k)] = b * b * (1.0 / a - 3.0) - g * a * a / b;
                r[th(k - 1)] = b * b / a - g * a * a * (1.0 / b - 3.0);
                rows.push(r);
                rhs.push(0.0);
            }
        }
    }

    let sol = solve(rows, rhs)?;
    let mut dirs = Vec::with_capacity(n);
    for k in 0..n {
        if closed || k < n - 1 {
            dirs.push(delta[k % nseg].cmul(V::polar(1.0, sol[th(k)])).norm());
        } else {
            dirs.push(delta[n - 2].cmul(V::polar(1.0, -sol[ph(k)])).norm());
        }
    }
    Ok(dirs)
}

/// The cubic segments of Hobby's spline through `nodes`.
pub fn hobby(nodes: &[Node], closed: bool) -> Result<Vec<Seg>, String> {
    let dirs = hobby_directions(nodes, closed)?;
    let n = nodes.len();
    let nseg = if closed { n } else { n - 1 };
    Ok((0..nseg)
        .map(|k| {
            let (a, b) = (&nodes[k], &nodes[(k + 1) % n]);
            hobby_segment(a.z, b.z, dirs[k], dirs[(k + 1) % n], a.t_out, b.t_in)
        })
        .collect())
}

// ---------------------------------------------------------------------------------------------------------------
// Superellipses

/// The exponent of the superellipse |x/a|^n + |y/b|^n = 1 whose diagonal point is where a single cubic with handles
/// at the fraction `k` of the way to the corner has its midpoint. `k` = 0.5523 gives 2, the ellipse.
pub fn lame_exponent(k: f64) -> f64 {
    0.5f64.ln() / ((4.0 + 3.0 * k) / 8.0).ln()
}

/// How far the superellipse of exponent `n` reaches along its diagonal, as a fraction of the way to the corner of
/// its box: 2^(-1/n). It is 0.7071 for an ellipse and 0.7579 for Piet Hein's n = 5/2.
pub fn lame_reach(n: f64) -> f64 {
    0.5f64.powf(1.0 / n)
}

/// The handle lengths (alpha, beta) of the two cubics that best fit a quadrant of the superellipse of exponent `n`.
///
/// In the quadrant's own frame the curve runs from (1, 0) to (0, 1) through the diagonal point (s, s), s = 2^(-1/n).
/// The first cubic is (1, 0), (1, alpha), (s + beta, s - beta), (s, s) and the second is its mirror image, so the
/// curve keeps its tangents at the extremes and on the diagonal and has the same curvature on both sides of the
/// diagonal. Alpha and beta minimise the squared deviation of |u|^n + |v|^n from 1 along the cubic. For n = 2 the
/// result is the usual two-cubic approximation of a quarter circle.
pub fn lame_handles(n: f64) -> (f64, f64) {
    // the fit is a search, and a font asks for the same few exponents many thousands of times
    static FITS: std::sync::Mutex<Vec<(u64, (f64, f64))>> = std::sync::Mutex::new(Vec::new());
    let key = n.to_bits();
    if let Some(&(_, fit)) = FITS.lock().unwrap_or_else(|e| e.into_inner()).iter().find(|(k, _)| *k == key) {
        return fit;
    }
    let fit = fit_lame_handles(n);
    let mut fits = FITS.lock().unwrap_or_else(|e| e.into_inner());
    if fits.len() < 64 {
        fits.push((key, fit));
    }
    fit
}

fn fit_lame_handles(n: f64) -> (f64, f64) {
    let s = lame_reach(n);
    let error = |alpha: f64, beta: f64| -> f64 {
        let c = Seg::Cubic(pt(1.0, 0.0), pt(1.0, alpha), pt(s + beta, s - beta), pt(s, s));
        (1..32)
            .map(|j| {
                let q = c.at(j as f64 / 32.0);
                let e = (q.x.abs().powf(n) + q.y.abs().powf(n)).powf(1.0 / n) - 1.0;
                e * e
            })
            .sum()
    };
    // a pattern search from the circle's values; the error is smooth and has one minimum in the region searched
    let (mut alpha, mut beta) = (0.2652, 0.1875);
    let mut best = error(alpha, beta);
    let mut step = 0.05;
    while step > 1e-10 {
        let mut improved = false;
        for (da, db) in [(step, 0.0), (-step, 0.0), (0.0, step), (0.0, -step)] {
            let (a, b) = (alpha + da, beta + db);
            if a <= 0.0 || b <= 0.0 || b >= s {
                continue;
            }
            let e = error(a, b);
            if e < best {
                (alpha, beta, best) = (a, b, e);
                improved = true;
            }
        }
        if !improved {
            step /= 2.0;
        }
    }
    (alpha, beta)
}

/// A superelliptic corner as two cubics: from `z0`, leaving along `d0`, to `z1`, arriving along `d1`, inside the
/// parallelogram those two tangents span. The superellipse of exponent `n` is drawn in that parallelogram's own
/// frame, so the construction commutes with any affine map (a slant, a stretch). `None` if the tangents do not
/// meet ahead of `z0` and behind `z1`.
pub fn lame_corner(z0: V, z1: V, d0: V, d1: V, n: f64) -> Option<[Seg; 2]> {
    let apex = intersect(z0, d0, z1, d1)?;
    if (apex - z0).dot(d0) <= 0.0 || (z1 - apex).dot(d1) <= 0.0 {
        return None;
    }
    let (e1, e2) = (apex - z1, apex - z0);
    let centre = z0 - e1;
    let at = |u: f64, v: f64| centre + e1 * u + e2 * v;
    let s = lame_reach(n);
    let (alpha, beta) = lame_handles(n);
    Some([
        Seg::Cubic(z0, at(1.0, alpha), at(s + beta, s - beta), at(s, s)),
        Seg::Cubic(at(s, s), at(s - beta, s + beta), at(alpha, 1.0), z1),
    ])
}

/// Gaussian elimination with partial pivoting. The systems here have at most a few dozen unknowns.
fn solve(a: Vec<Vec<f64>>, b: Vec<f64>) -> Result<Vec<f64>, String> {
    let n = b.len();
    let mut m: Vec<Vec<f64>> = a
        .into_iter()
        .zip(b)
        .map(|(mut row, rhs)| {
            row.push(rhs);
            row
        })
        .collect();
    for col in 0..n {
        let mut pivot = col;
        for r in col + 1..n {
            if m[r][col].abs() > m[pivot][col].abs() {
                pivot = r;
            }
        }
        if m[pivot][col].abs() < 1e-12 {
            return Err("the spline's equations are singular".into());
        }
        m.swap(col, pivot);
        let (above, below) = m.split_at_mut(col + 1);
        let pivot_row = &above[col];
        for row in below {
            let f = row[col] / pivot_row[col];
            if f != 0.0 {
                for (x, &v) in row[col..].iter_mut().zip(&pivot_row[col..]) {
                    *x -= f * v;
                }
            }
        }
    }
    let mut x = vec![0.0; n];
    for r in (0..n).rev() {
        let s: f64 = (r + 1..n).map(|c| m[r][c] * x[c]).sum();
        x[r] = (m[r][n] - s) / m[r][r];
    }
    Ok(x)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn velocity_of_a_symmetric_arc_is_the_circle_approximation() {
        for deg in [10.0f64, 30.0, 45.0, 60.0, 90.0] {
            let t = deg.to_radians();
            assert!((velocity(t, t) - 2.0 / (3.0 * (1.0 + t.cos()))).abs() < 1e-12);
        }
    }

    #[test]
    fn quarter_circle_handle_is_kappa() {
        let Seg::Cubic(p0, c1, ..) = hobby_segment(pt(1.0, 0.0), pt(0.0, 1.0), pt(0.0, 1.0), pt(-1.0, 0.0), 1.0, 1.0)
        else {
            unreachable!()
        };
        assert!(((c1 - p0).abs() - 4.0 / 3.0 * (2f64.sqrt() - 1.0)).abs() < 1e-12);
    }

    #[test]
    fn closed_path_through_a_circle_is_nearly_a_circle() {
        for (n, tolerance) in [(3usize, 0.004), (4, 0.0003), (6, 0.0003), (8, 0.0003)] {
            let nodes: Vec<Node> = (0..n).map(|i| Node::new(V::unit(360.0 * i as f64 / n as f64))).collect();
            let segs = hobby(&nodes, true).unwrap();
            let err = segs
                .iter()
                .flat_map(|s| (0..=32).map(move |t| (s.at(t as f64 / 32.0).abs() - 1.0).abs()))
                .fold(0.0, f64::max);
            assert!(err < tolerance, "{n}: {err}");
        }
    }

    #[test]
    fn open_path_through_a_semicircle() {
        // (0,0)..(100,100)..(200,0) with curl 1 at both ends lies on the circle about (100, 0).
        let segs =
            hobby(&[Node::new(pt(0.0, 0.0)), Node::new(pt(100.0, 100.0)), Node::new(pt(200.0, 0.0))], false).unwrap();
        let want = [pt(0.0, 55.228), pt(44.772, 100.0), pt(155.228, 100.0), pt(200.0, 55.228)];
        let mut got = Vec::new();
        for s in &segs {
            let Seg::Cubic(_, c1, c2, _) = *s else { unreachable!() };
            got.extend([c1, c2]);
        }
        for (g, w) in got.iter().zip(want) {
            assert!((*g - w).abs() < 0.01, "{g:?} {w:?}");
        }
    }

    #[test]
    fn mock_curvature_is_continuous() {
        let nodes = [
            Node::new(pt(0.0, 0.0)),
            Node::new(pt(100.0, 80.0)),
            Node::new(pt(260.0, 60.0)),
            Node::new(pt(300.0, -90.0)),
        ];
        let dirs = hobby_directions(&nodes, false).unwrap();
        for k in [1usize, 2] {
            let d_in = nodes[k].z - nodes[k - 1].z;
            let d_out = nodes[k + 1].z - nodes[k].z;
            let th_prev = dirs[k - 1].cdiv(d_in).phase();
            let ph_k = d_in.cdiv(dirs[k]).phase();
            let th_k = dirs[k].cdiv(d_out).phase();
            let ph_next = d_out.cdiv(dirs[k + 1]).phase();
            let left = ((th_prev + ph_k) - 3.0 * ph_k) / d_in.abs();
            let right = ((th_k + ph_next) - 3.0 * th_k) / d_out.abs();
            assert!((left - right).abs() < 1e-9);
        }
    }

    #[test]
    fn given_directions_are_kept_and_tension_pulls_towards_the_chord() {
        let nodes = [
            Node::new(pt(0.0, 0.0)).dir(V::unit(90.0)),
            Node::new(pt(120.0, 160.0)),
            Node::new(pt(300.0, 140.0)),
            Node::new(pt(420.0, 0.0)).dir(V::unit(-90.0)),
        ];
        let dirs = hobby_directions(&nodes, false).unwrap();
        assert!((dirs[0] - V::unit(90.0)).abs() < 1e-12);
        assert!((dirs[3] - V::unit(-90.0)).abs() < 1e-12);
        let loose =
            hobby(&[Node::new(pt(0.0, 0.0)).dir(V::unit(60.0)), Node::new(pt(100.0, 0.0)).dir(V::unit(-60.0))], false)
                .unwrap();
        let tight = hobby(
            &[
                Node::new(pt(0.0, 0.0)).dir(V::unit(60.0)).tension(1.0, 2.0),
                Node::new(pt(100.0, 0.0)).dir(V::unit(-60.0)).tension(2.0, 1.0),
            ],
            false,
        )
        .unwrap();
        assert!(tight[0].at(0.5).y < loose[0].at(0.5).y);
    }

    #[test]
    fn coincident_knots_are_refused() {
        assert!(hobby(&[Node::new(V::ZERO), Node::new(V::ZERO), Node::new(pt(1.0, 0.0))], false).is_err());
    }

    #[test]
    fn split_keeps_the_curve_and_extrema_are_found() {
        let c = Seg::Cubic(pt(0.0, 0.0), pt(10.0, 40.0), pt(60.0, 50.0), pt(90.0, 0.0));
        let (a, b) = c.split(0.3);
        assert!((a.at(0.5) - c.at(0.15)).abs() < 1e-12);
        assert!((b.at(0.5) - c.at(0.65)).abs() < 1e-12);
        let c = Seg::Cubic(pt(0.0, 0.0), pt(0.0, 50.0), pt(100.0, 50.0), pt(100.0, 0.0));
        let e = c.extrema();
        assert_eq!(e.len(), 1);
        assert!((e[0] - 0.5).abs() < 1e-12);
        assert!((c.at(e[0]).y - 37.5).abs() < 1e-12);
    }

    #[test]
    fn lines_intersect_unless_parallel() {
        assert_eq!(intersect(V::ZERO, pt(1.0, 0.0), pt(5.0, 5.0), pt(0.0, 1.0)), Some(pt(5.0, 0.0)));
        assert_eq!(intersect(V::ZERO, pt(1.0, 0.0), pt(0.0, 1.0), pt(2.0, 0.0)), None);
    }

    #[test]
    fn a_lame_quadrant_with_exponent_two_is_a_circle() {
        let [a, b] = lame_corner(pt(1.0, 0.0), pt(0.0, 1.0), pt(0.0, 1.0), pt(-1.0, 0.0), 2.0).unwrap();
        for s in [a, b] {
            for j in 0..=32 {
                assert!((s.at(j as f64 / 32.0).abs() - 1.0).abs() < 2e-5);
            }
        }
    }

    #[test]
    fn a_lame_quadrant_follows_the_superellipse_and_is_flat_at_its_extremes() {
        for n in [2.25, 2.5, 3.0, 3.5] {
            let [a, b] = lame_corner(pt(300.0, 0.0), pt(0.0, 200.0), pt(0.0, 1.0), pt(-1.0, 0.0), n).unwrap();
            let mut worst: f64 = 0.0;
            for s in [a, b] {
                for j in 0..=64 {
                    let q = s.at(j as f64 / 64.0);
                    let r = ((q.x / 300.0).abs().powf(n) + (q.y / 200.0).abs().powf(n)).powf(1.0 / n);
                    worst = worst.max((r - 1.0).abs());
                }
            }
            assert!(worst < 0.004, "n = {n}: {worst}");
            // the diagonal point is exact
            assert!((a.end() - pt(300.0, 200.0) * lame_reach(n)).abs() < 1e-9);
        }
        assert!((lame_exponent(0.5523) - 2.0).abs() < 0.001);
        assert!((lame_reach(2.5) - 0.757_858).abs() < 1e-6);
    }
}
