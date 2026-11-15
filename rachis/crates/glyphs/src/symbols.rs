//! Symbols for terminal interfaces: status marks, bullets, geometric shapes, keys and small pictograms.
//!
//! Every glyph here fills one cell and is registered upright: these are signs, not text, and an italic must not
//! slant them. They follow one system.
//!
//! Centre. Centred shapes sit on (p.mid, centre(p)), a little above the operator axis, so that a disc looks centred
//! beside lowercase and beside capitals and figures.
//!
//! Size classes. A class is the side of its square. The disc of a class is ROUND times as wide and the diamond
//! DIAMOND_W by DIAMOND_H, so that the three look the same size side by side; a triangle is TRI_BASE by TRI_DEPTH.
//! Filled shapes grow a little with weight (`grow`), as the period does. An outlined shape has the outer size of
//! the filled one and a stroke of `line(p, cls)`: p.op for the full-size classes, less for the small ones, whose
//! counters would otherwise close in the Bold.
//!
//! Strokes. Shapes and keys use p.op. Check marks and crosses use `mark` (1.15 p.op) and their heavy variants
//! `heavy`. Pictograms with several strokes in one cell use `fine`, which grows more slowly than p.op so that
//! the Bold stays open.

use rachis_kernel::geom::intersect;
use rachis_kernel::pen::{centerline, polygon, superellipse};
use rachis_kernel::{Contour, Draw, Knot, Opt, Params, Registry, Seg, V, knot, pt};

use crate::parts::{elbow, hbar, ring, vstem};

// ---------------------------------------------------------------------------------------------------------------
// the system

// Half the side of the square of each class, before `grow`.
const LARGE: f64 = 244.0; // ◯ ☐: as large as a cell allows with air around it
const FULL: f64 = 220.0; // ■ ● ◆ ▲ ▶ and the status marks: the default
const MIDDLE: f64 = 180.0; // ◼ ◻: Unicode's "medium"
const LESSER: f64 = 154.0; // ◾ ◽: Unicode's "medium small"
const SMALL: f64 = 131.0; // ▪ ▫ ◦ ▸ ▾
const TINY: f64 = 88.0; // ⬝ ⬞

const ROUND: f64 = 1.10; // a disc is this much wider than the square it has to match
const DIAMOND_W: f64 = 1.20; // a diamond's width and height, likewise
const DIAMOND_H: f64 = 1.28;
const TRI_BASE: f64 = 1.14; // a triangle's base and its depth from base to point
const TRI_DEPTH: f64 = 1.02;
const TRI_SHIFT: f64 = 0.06; // a triangle is moved towards its point by this fraction of its depth, to look centred
const POINTER_LEN: f64 = 1.22; // a pointer (► ◄) is longer and flatter than a triangle
const POINTER_BASE: f64 = 0.80;

/// The height centred shapes are centred on.
fn centre(p: &Params) -> f64 {
    p.axis + 12.0
}

/// Filled shapes are a little larger in heavier weights: 0.97 in the Light, 1.00 in the Regular, 1.05 in the
/// Bold.
fn grow(p: &Params) -> f64 {
    0.88 + 0.0016 * p.op
}

fn half(p: &Params, cls: f64) -> f64 {
    cls * grow(p)
}

/// The stroke of an outlined shape of a class. The full-size classes use the operator stroke; smaller ones use a
/// stroke that is lighter and grows more slowly, so that the counter survives in the Bold.
fn line(p: &Params, cls: f64) -> f64 {
    let share = 1.0_f64.min(0.0_f64.max((cls - TINY) / (FULL - TINY))); // 0 for the tiny class, 1 from the full class up
    p.op * (0.36 + 0.64 * share) + 24.0 * (1.0 - share)
}

/// The stroke of check marks and crosses.
fn mark(p: &Params) -> f64 {
    1.15 * p.op
}

/// The stroke of the heavy check marks, crosses and ornaments: 1.5 times `mark` in the Regular, relatively more
/// in the Light and less in the Bold, where the cell has no room for more.
fn heavy(p: &Params) -> f64 {
    0.95 * p.op + 58.0
}

/// The stroke of pictograms that put several strokes in one cell.
fn fine(p: &Params) -> f64 {
    0.55 * p.op + 26.0
}

// ---------------------------------------------------------------------------------------------------------------
// parts of this group

/// The polygon `points` (counter-clockwise) with every edge moved inwards by `d`.
fn inset(points: &[V], d: f64) -> Vec<V> {
    let n = points.len();
    let mut lines = Vec::new();
    for i in 0..n {
        let (a, b) = (points[i], points[(i + 1) % n]);
        let u = (b - a) / (b - a).abs();
        lines.push((a + u.left() * d, u));
    }
    let mut out = Vec::new();
    for i in 0..n {
        let (q0, u0) = lines[(i + n - 1) % n];
        let (q1, u1) = lines[i];
        let z = intersect(q0, u0, q1, u1).expect("adjacent edges are not parallel");
        out.push(z);
    }
    out
}

/// The polygon `points` (counter-clockwise) drawn as an outline `t` thick with mitred corners. Its outer edge is
/// the polygon itself.
fn outline(g: &mut Draw, points: &[V], t: f64) {
    let knots: Vec<Knot> = inset(points, t / 2.0)
        .into_iter()
        .map(|z| Knot::at(z, t).line())
        .collect();
    g.stroke_closed(&knots);
}

/// A polygon cut out of the shape that contains it.
fn hole(g: &mut Draw, points: &[V]) {
    g.add(polygon(points).reversed());
}

fn square(cx: f64, cy: f64, hx: f64, hy: f64) -> Vec<V> {
    vec![
        pt(cx - hx, cy - hy),
        pt(cx + hx, cy - hy),
        pt(cx + hx, cy + hy),
        pt(cx - hx, cy + hy),
    ]
}

fn diamond(cx: f64, cy: f64, hx: f64, hy: f64) -> Vec<V> {
    vec![
        pt(cx, cy - hy),
        pt(cx + hx, cy),
        pt(cx, cy + hy),
        pt(cx - hx, cy),
    ]
}

/// An isosceles triangle pointing along `heading` (degrees), its bounding box centred on (cx, cy) before the
/// optical shift towards the point.
fn triangle(cx: f64, cy: f64, base: f64, depth: f64, heading: f64) -> Vec<V> {
    let d = V::unit(heading);
    let c = pt(cx, cy) + d * depth * TRI_SHIFT;
    let back = c - d * depth / 2.0;
    vec![
        back - d.left() * base / 2.0,
        c + d * depth / 2.0,
        back + d.left() * base / 2.0,
    ]
}

fn tri(p: &Params, cls: f64, heading: f64) -> Vec<V> {
    let s = 2.0 * half(p, cls);
    triangle(p.mid(), centre(p), TRI_BASE * s, TRI_DEPTH * s, heading)
}

fn pointer(p: &Params, cls: f64, heading: f64) -> Vec<V> {
    let s = 2.0 * half(p, cls);
    triangle(
        p.mid(),
        centre(p),
        POINTER_BASE * s,
        POINTER_LEN * s,
        heading,
    )
}

fn disc(g: &mut Draw, cx: f64, cy: f64, r: f64) {
    let k = g.p.dot_k;
    g.dot_xy(cx, cy, r, r, k);
}

/// A ring `t` thick whose outer edge has the radius `r`.
fn circle(g: &mut Draw, cx: f64, cy: f64, r: f64, t: f64) {
    let k = g.p.dot_k;
    g.stroke_closed(&ring(cx - r, cy - r, cx + r, cy + r, t, t, k));
}

/// `1j ** q`, exactly.
fn i_pow(q: i32) -> V {
    match q.rem_euclid(4) {
        0 => pt(1.0, 0.0),
        1 => pt(0.0, 1.0),
        2 => pt(-1.0, 0.0),
        _ => pt(0.0, -1.0),
    }
}

/// `count` quadrants of the disc of radius `r`, counter-clockwise from the quadrant `first` (0 is east to
/// north), closed through the centre.
fn sector(g: &mut Draw, cx: f64, cy: f64, r: f64, first: i32, count: i32) {
    let k = g.p.dot_k;
    let c = pt(cx, cy);
    let mut segs: Vec<Seg> = Vec::new();
    for q in first..first + count {
        let (a, b) = (i_pow(q), i_pow(q + 1));
        segs.push(Seg::Cubic(
            c + r * a,
            c + r * a + k * r * b,
            c + r * b + k * r * a,
            c + r * b,
        ));
    }
    let (last, start) = (segs[segs.len() - 1].end(), segs[0].start());
    if count == 2 {
        segs.push(Seg::Line(last, start));
    } else {
        segs.extend([Seg::Line(last, c), Seg::Line(c, start)]);
    }
    g.add(Contour::new(segs).oriented(true));
}

/// A straight stroke `t` thick along `heading` from the distance `r0` to `r1` from `c`, cut square: the arm of
/// a star, an asterisk or a wheel.
fn spoke(c: V, r0: f64, r1: f64, heading: f64, t: f64) -> Vec<V> {
    let d = V::unit(heading);
    let n = d.left() * t / 2.0;
    vec![
        c + d * r0 - n,
        c + d * r1 - n,
        c + d * r1 + n,
        c + d * r0 + n,
    ]
}

/// An arrow head: two straight strokes `t` thick, mitred at `tip` (a point on the centre line) and cut
/// horizontally at their ends, which lie `back` to the right of the tip (negative: to the left) and `rise` above
/// and below it.
fn chevron(tip: V, back: f64, rise: f64, t: f64) -> Vec<Knot> {
    let b = t * back.hypot(rise) / rise.abs();
    vec![
        Knot::at(tip + pt(back, rise), b).pen(0.0).line(),
        Knot::at(tip, t).line(),
        Knot::at(tip + pt(back, -rise), b).pen(0.0),
    ]
}

/// A stroke `t` thick through `points` in straight segments with mitred corners. Its first end is cut along
/// `ends` (90: plumb, for a stroke that ends horizontal; 0: level) and its last end along `end` (in Python it
/// defaults to `ends`).
fn path(points: &[V], t: f64, ends: f64, end: f64) -> Vec<Knot> {
    let breadth = |a: V, b: V, pen: f64| -> f64 {
        let d = (b - a) / (b - a).abs();
        t / d.cmul(V::unit(-pen)).y.abs()
    };
    let n = points.len();
    let first = Knot::at(points[0], breadth(points[0], points[1], ends))
        .pen(ends)
        .line();
    let last = Knot::at(points[n - 1], breadth(points[n - 2], points[n - 1], end)).pen(end);
    let mut out = vec![first];
    out.extend(points[1..n - 1].iter().map(|&z| Knot::at(z, t).line()));
    out.push(last);
    out
}

/// The polygon of a check mark or of any V with unequal legs: the outer corners of its two ends are `a` and `b`,
/// both ends are cut level, the strokes are `t` thick, and the vertex is cut flat, `apex` wide, centred on `low`.
fn tick(a: V, low: V, b: V, t: f64, apex: f64) -> Vec<V> {
    let (fl, fr) = (low - pt(apex / 2.0, 0.0), low + pt(apex / 2.0, 0.0));
    let (ul, ur) = ((fl - a) / (fl - a).abs(), (b - fr) / (b - fr).abs());
    let (il, ir) = (a + ul.left() * t, fr + ur.left() * t); // points on the two inner edges
    let crotch = intersect(il, ul, ir, ur).expect("the legs are not parallel");
    let a_in = intersect(il, ul, a, pt(1.0, 0.0)).expect("the left leg is not level");
    let b_in = intersect(ir, ur, b, pt(1.0, 0.0)).expect("the right leg is not level");
    vec![a, fl, fr, b, b_in, crotch, a_in]
}

/// The area enclosed by the closed path through `knots`.
#[allow(dead_code)]
fn fill(g: &mut Draw, knots: &[Knot]) {
    match centerline(knots, true) {
        Ok((segs, _, _)) => g.add(Contour::new(segs).oriented(true)),
        Err(e) => g.glyph.errors.push(e),
    }
}

// ---------------------------------------------------------------------------------------------------------------
// squares

fn black_square(g: &mut Draw, cls: f64) {
    let p = g.p;
    g.poly(&square(p.mid(), centre(p), half(p, cls), half(p, cls)));
}

fn white_square(g: &mut Draw, cls: f64) {
    let p = g.p;
    outline(
        g,
        &square(p.mid(), centre(p), half(p, cls), half(p, cls)),
        line(p, cls),
    );
}

fn white_square_rounded(g: &mut Draw) {
    let p = g.p;
    let t = p.op;
    let h = half(p, FULL) - t / 2.0;
    let r = 0.52 * h; // the corner's radius on the centre line
    let (cx, cy) = (p.mid(), centre(p));
    let k = p.dot_k;
    g.stroke_closed(&[
        knot(cx + h, cy - h + r, t).dir(90.0).line(),
        knot(cx + h, cy + h - r, t).dir(90.0).k(k),
        knot(cx + h - r, cy + h, t).dir(180.0).line(),
        knot(cx - h + r, cy + h, t).dir(180.0).k(k),
        knot(cx - h, cy + h - r, t).dir(-90.0).line(),
        knot(cx - h, cy - h + r, t).dir(-90.0).k(k),
        knot(cx - h + r, cy - h, t).dir(0.0).line(),
        knot(cx + h - r, cy - h, t).dir(0.0).k(k),
    ]);
}

fn white_square_containing_black(g: &mut Draw) {
    let p = g.p;
    let h = half(p, FULL);
    let t = fine(p);
    outline(g, &square(p.mid(), centre(p), h, h), t);
    g.poly(&square(p.mid(), centre(p), 0.50 * (h - t), 0.50 * (h - t)));
}

// ---------------------------------------------------------------------------------------------------------------
// rectangles and parallelograms

/// Half the length and half the breadth of the rectangles ▬ ▭ (and, turned, ▮ ▯).
fn bar_box(p: &Params) -> (f64, f64) {
    (half(p, LARGE), 0.42 * half(p, FULL))
}

fn black_rectangle(g: &mut Draw) {
    let p = g.p;
    let (hx, hy) = bar_box(p);
    g.poly(&square(p.mid(), centre(p), hx, hy));
}

fn white_rectangle(g: &mut Draw) {
    let p = g.p;
    let (hx, hy) = bar_box(p);
    outline(g, &square(p.mid(), centre(p), hx, hy), line(p, SMALL));
}

fn black_vertical_rectangle(g: &mut Draw) {
    let p = g.p;
    let (hy, hx) = bar_box(p);
    g.poly(&square(p.mid(), centre(p), 1.24 * hx, 1.12 * hy));
}

fn white_vertical_rectangle(g: &mut Draw) {
    let p = g.p;
    let (hy, hx) = bar_box(p);
    outline(
        g,
        &square(p.mid(), centre(p), 1.24 * hx, 1.12 * hy),
        line(p, LESSER),
    );
}

fn parallelogram(p: &Params) -> Vec<V> {
    let (hx, hy) = (half(p, LARGE) + 22.0, 0.56 * half(p, FULL));
    let lean = 0.42 * hy;
    let (cx, cy) = (p.mid(), centre(p));
    vec![
        pt(cx - hx, cy - hy),
        pt(cx + hx - 2.0 * lean, cy - hy),
        pt(cx + hx, cy + hy),
        pt(cx - hx + 2.0 * lean, cy + hy),
    ]
}

fn black_parallelogram(g: &mut Draw) {
    g.poly(&parallelogram(g.p));
}

fn white_parallelogram(g: &mut Draw) {
    let p = g.p;
    outline(g, &parallelogram(p), line(p, SMALL));
}

// ---------------------------------------------------------------------------------------------------------------
// triangles and pointers

type Shape = fn(&Params, f64, f64) -> Vec<V>;

fn black_triangle(g: &mut Draw, cls: f64, heading: f64, shape: Shape) {
    g.poly(&shape(g.p, cls, heading));
}

fn white_triangle(g: &mut Draw, cls: f64, heading: f64, shape: Shape) {
    let p = g.p;
    outline(g, &shape(p, cls, heading), line(p, cls));
}

fn corner_triangle(g: &mut Draw, sx: f64, sy: f64) {
    let p = g.p;
    let h = half(p, FULL);
    let c = pt(p.mid(), centre(p));
    // the right angle is in the corner (sx, sy); the other two corners are its neighbours
    g.poly(&[
        c + pt(sx * h, sy * h),
        c + pt(-sx * h, sy * h),
        c + pt(sx * h, -sy * h),
    ]);
}

// ---------------------------------------------------------------------------------------------------------------
// diamonds

fn diamond_(p: &Params, cls: f64) -> Vec<V> {
    let h = half(p, cls);
    diamond(p.mid(), centre(p), DIAMOND_W * h, DIAMOND_H * h)
}

fn black_diamond(g: &mut Draw) {
    g.poly(&diamond_(g.p, FULL));
}

fn white_diamond(g: &mut Draw) {
    let p = g.p;
    outline(g, &diamond_(p, FULL), p.op);
}

fn white_diamond_containing_black(g: &mut Draw) {
    let p = g.p;
    let d = diamond_(p, FULL);
    let t = fine(p);
    outline(g, &d, t);
    let c = pt(p.mid(), centre(p));
    let inner: Vec<V> = d.iter().map(|&z| c + (z - c) * 0.40).collect();
    g.poly(&inner);
}

fn lozenge(g: &mut Draw) {
    let p = g.p;
    let cy = p.cap / 2.0;
    outline(
        g,
        &diamond(p.mid(), cy, 0.86 * half(p, FULL), cy + 3.0 * p.over),
        p.op,
    );
}

// ---------------------------------------------------------------------------------------------------------------
// circles

fn r_(p: &Params, cls: f64) -> f64 {
    ROUND * half(p, cls)
}

fn black_circle(g: &mut Draw) {
    let p = g.p;
    disc(g, p.mid(), centre(p), r_(p, FULL));
}

fn white_circle(g: &mut Draw) {
    let p = g.p;
    circle(g, p.mid(), centre(p), r_(p, FULL), p.op);
}

fn large_circle(g: &mut Draw) {
    let p = g.p;
    circle(g, p.mid(), centre(p), r_(p, LARGE), p.op);
}

fn white_bullet(g: &mut Draw) {
    let p = g.p;
    circle(g, p.mid(), centre(p), r_(p, SMALL), line(p, SMALL));
}

fn dotted_circle(g: &mut Draw) {
    let p = g.p;
    let r_dot = 0.26 * p.op + 14.0;
    let r = r_(p, FULL) - r_dot;
    for i in 0..8 {
        let z = pt(p.mid(), centre(p)) + r * V::unit(90.0 - 45.0 * f64::from(i));
        g.dot_xy(z.x, z.y, r_dot, r_dot, p.dot_k);
    }
}

fn fisheye(g: &mut Draw) {
    let p = g.p;
    let (r, t) = (r_(p, FULL), fine(p));
    circle(g, p.mid(), centre(p), r, t);
    disc(g, p.mid(), centre(p), 0.56 * (r - t));
}

fn bullseye(g: &mut Draw) {
    let p = g.p;
    let (r, t) = (r_(p, FULL), fine(p));
    circle(g, p.mid(), centre(p), r, t);
    circle(g, p.mid(), centre(p), 0.60 * (r - t) + 0.3 * t, 0.9 * t);
}

fn circle_with_vertical_fill(g: &mut Draw) {
    let p = g.p;
    let (r, t) = (r_(p, FULL), fine(p));
    let (cx, cy) = (p.mid(), centre(p));
    circle(g, cx, cy, r, t);
    let w = 0.30 * p.op + 20.0;
    let ri = r - t / 2.0; // the bars end inside the ring
    let step = 0.50 * (r - t);
    for dx in [-step, 0.0, step] {
        let hy = (ri * ri - (dx.abs() + w / 2.0).powi(2)).sqrt();
        g.rect(cx + dx - w / 2.0, cy - hy, cx + dx + w / 2.0, cy + hy);
    }
}

fn part_filled(g: &mut Draw, first: i32, count: i32) {
    let p = g.p;
    circle(g, p.mid(), centre(p), r_(p, FULL), p.op);
    sector(g, p.mid(), centre(p), r_(p, FULL), first, count);
}

fn left_half_black_circle(g: &mut Draw) {
    let p = g.p;
    sector(
        g,
        p.mid() + 0.25 * r_(p, FULL),
        centre(p),
        r_(p, FULL),
        1,
        2,
    );
}

fn right_half_black_circle(g: &mut Draw) {
    let p = g.p;
    sector(
        g,
        p.mid() - 0.25 * r_(p, FULL),
        centre(p),
        r_(p, FULL),
        3,
        2,
    );
}

// ---------------------------------------------------------------------------------------------------------------
// check marks and crosses

/// A short leg from the left and a long one that rises to the cap height, meeting on the baseline.
fn check(g: &mut Draw, t: f64) {
    let p = g.p;
    g.poly(&tick(
        pt(p.op_l - 14.0, 0.47 * p.cap),
        pt(p.mid() - 64.0, -p.over),
        pt(p.op_r() + 14.0, p.cap),
        t,
        0.5 * t,
    ));
}

fn check_mark(g: &mut Draw) {
    let t = mark(g.p);
    check(g, t);
}

fn heavy_check_mark(g: &mut Draw) {
    let t = heavy(g.p);
    check(g, t);
}

/// A symmetric cross of two diagonals in the box of half-size (hx, hy), cut level.
fn saltire(g: &mut Draw, hx: f64, hy: f64, t: f64) {
    let p = g.p;
    let (cx, cy) = (p.mid(), centre(p));
    let b = t * (2.0 * hx).hypot(2.0 * hy) / (2.0 * hy);
    let x = hx - b / 2.0;
    g.stroke(&path(
        &[pt(cx - x, cy - hy), pt(cx + x, cy + hy)],
        t,
        0.0,
        0.0,
    ));
    g.stroke(&path(
        &[pt(cx - x, cy + hy), pt(cx + x, cy - hy)],
        t,
        0.0,
        0.0,
    ));
}

fn multiplication_x(g: &mut Draw) {
    let p = g.p;
    let h = half(p, FULL);
    saltire(g, h, h, mark(p));
}

fn heavy_multiplication_x(g: &mut Draw) {
    let p = g.p;
    let h = half(p, FULL);
    saltire(g, h, h, heavy(p));
}

/// Two straight strokes that cross above the middle: a long one rising to the right, as tall as the check mark,
/// and a shorter, steeper one falling to the right.
fn ballot_x_(g: &mut Draw, t: f64) {
    let p = g.p;
    let (y0, y1) = (24.0, p.cap - 70.0);
    let b = 1.28 * t; // about the breadth of a level cut
    g.stroke(&path(
        &[
            pt(p.op_l - 26.0 + b / 2.0, y0),
            pt(p.op_r() + 26.0 - b / 2.0, y1),
        ],
        t,
        0.0,
        0.0,
    ));
    g.stroke(&path(
        &[
            pt(p.op_l + 22.0 + b / 2.0, y1 - 50.0),
            pt(p.op_r() - 64.0 - b / 2.0, y0 + 40.0),
        ],
        t,
        0.0,
        0.0,
    ));
}

fn ballot_x(g: &mut Draw) {
    let t = mark(g.p);
    ballot_x_(g, t);
}

fn heavy_ballot_x(g: &mut Draw) {
    let t = heavy(g.p);
    ballot_x_(g, t);
}

fn greek_cross(g: &mut Draw, t: f64, gap: f64) {
    let p = g.p;
    let (cx, cy) = (p.mid(), centre(p));
    let h = half(p, FULL);
    if gap != 0.0 {
        for heading in [0.0, 90.0, 180.0, 270.0] {
            g.poly(&spoke(pt(cx, cy), gap, h, heading, t));
        }
    } else {
        g.rect(cx - h, cy - t / 2.0, cx + h, cy + t / 2.0);
        g.rect(cx - t / 2.0, cy - h, cx + t / 2.0, cy + h);
    }
}

fn heavy_greek_cross(g: &mut Draw) {
    let t = heavy(g.p) * 1.06;
    greek_cross(g, t, 0.0);
}

fn open_centre_cross(g: &mut Draw) {
    let p = g.p;
    greek_cross(g, mark(p), 0.5 * mark(p) + 26.0);
}

fn heavy_open_centre_cross(g: &mut Draw) {
    let p = g.p;
    greek_cross(g, heavy(p) * 1.06, 0.30 * heavy(p) + 30.0);
}

// ---------------------------------------------------------------------------------------------------------------
// the user's interface: keys and small pictograms

fn trigram_heaven(g: &mut Draw) {
    trigram(g, [1, 1, 1]);
}

/// Three bars; `solid` says, from the bottom up, which are whole (1) and which are broken (0).
fn trigram(g: &mut Draw, solid: [u8; 3]) {
    let p = g.p;
    let t = 0.60 * p.op + 40.0;
    let (hx, hy) = (half(p, FULL) * 1.10, half(p, FULL));
    let (cx, cy) = (p.mid(), centre(p));
    let gap = 0.20 * hx + 0.25 * t;
    for (i, whole) in solid.into_iter().enumerate() {
        let y = cy + (i as f64 - 1.0) * (hy - t / 2.0);
        if whole != 0 {
            g.stroke(&hbar(cx - hx, cx + hx, y, t));
        } else {
            g.stroke(&hbar(cx - hx, cx - gap, y, t));
            g.stroke(&hbar(cx + gap, cx + hx, y, t));
        }
    }
}

fn return_symbol(g: &mut Draw) {
    let p = g.p;
    let t = p.op;
    let y = centre(p) - 116.0; // the shaft
    let top = centre(p) + half(p, FULL) + 44.0;
    let x = p.op_r() - 6.0 - t / 2.0; // the stem that comes down
    let rise = 0.4 * t + 84.0;
    let tip = pt(p.op_l - 26.0 + 0.75 * t, y); // the head's outer point is about 0.75 t to the left of this
    g.stroke(&elbow(x, top, y - t / 2.0, tip.x, t, t, p.sq, 100.0));
    g.stroke(&chevron(tip, rise, rise, t));
}

/// The alternative and option keys share one step: x of the left end, of the two bends and of the right end,
/// then the height of the low line and of the high one.
fn step(p: &Params) -> (f64, f64, f64, f64, f64, f64) {
    let cy = centre(p);
    let rise = 0.86 * half(p, FULL);
    (
        p.op_l - 16.0,
        p.mid() - 92.0,
        p.mid() + 60.0,
        p.op_r() + 16.0,
        cy - rise,
        cy + rise,
    )
}

fn alternative_key(g: &mut Draw) {
    let p = g.p;
    let (x0, xa, xb, x1, lo, hi) = step(p);
    g.stroke(&path(
        &[pt(x0, lo), pt(xa, lo), pt(xb, hi), pt(x1, hi)],
        p.op,
        90.0,
        90.0,
    ));
    g.stroke(&hbar(xb + 0.2 * p.op + 4.0, x1, lo, p.op));
}

fn option_key(g: &mut Draw) {
    let p = g.p;
    let (x0, xa, xb, x1, lo, hi) = step(p);
    g.stroke(&path(
        &[pt(x0, hi), pt(xa, hi), pt(xb, lo), pt(x1, lo)],
        p.op,
        90.0,
        90.0,
    ));
    g.stroke(&hbar(xb + 0.2 * p.op + 4.0, x1, hi, p.op));
}

fn black_hourglass(g: &mut Draw) {
    let p = g.p;
    let (hx, hy) = (0.84 * half(p, FULL), 1.16 * half(p, FULL));
    let w = 0.22 * p.op + 10.0; // half the waist
    let (cx, cy) = (p.mid(), centre(p));
    g.poly(&[
        pt(cx - hx, cy - hy),
        pt(cx + hx, cy - hy),
        pt(cx + w, cy),
        pt(cx + hx, cy + hy),
        pt(cx - hx, cy + hy),
        pt(cx - w, cy),
    ]);
}

fn white_hourglass(g: &mut Draw) {
    let p = g.p;
    let (hx, hy) = (0.84 * half(p, FULL), 1.16 * half(p, FULL));
    let (cx, cy) = (p.mid(), centre(p));
    let t = line(p, SMALL);
    // Two outlined triangles whose centre lines meet in the middle: their strokes cross there.
    let reach = (t / 2.0) * hx.hypot(hy) / hx; // how far a mitred point lies beyond its centre line's vertex
    outline(
        g,
        &[
            pt(cx - hx, cy + hy),
            pt(cx, cy - reach),
            pt(cx + hx, cy + hy),
        ],
        t,
    );
    outline(
        g,
        &[
            pt(cx + hx, cy - hy),
            pt(cx, cy + reach),
            pt(cx - hx, cy - hy),
        ],
        t,
    );
}

fn two_joined_squares(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let h = 0.80 * half(p, FULL); // half the side of each square
    let off = 0.36 * half(p, FULL); // each is moved this far from the centre, one down and left, one up and right
    let gap = 0.2 * t + 28.0;
    let (cx, cy) = (p.mid(), centre(p));
    outline(g, &square(cx - off, cy - off, h, h), t);
    // the square behind: what the one in front leaves visible
    let (x0, x1) = (cx + off - h + t / 2.0, cx + off + h - t / 2.0);
    let (y0, y1) = (cy + off - h + t / 2.0, cy + off + h - t / 2.0);
    let (front_top, front_right) = (cy - off + h, cx - off + h);
    g.stroke(&path(
        &[
            pt(x0, front_top + gap),
            pt(x0, y1),
            pt(x1, y1),
            pt(x1, y0),
            pt(front_right + gap, y0),
        ],
        t,
        0.0,
        90.0,
    ));
}

fn stopwatch(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let r = 1.10 * half(p, FULL);
    let (cx, cy) = (p.mid(), centre(p) - 52.0);
    circle(g, cx, cy, r, t);
    // the button: a stem and a cap
    let top = cy + r + 0.8 * t + 44.0;
    g.stroke(&vstem(cx, cy + r - t / 2.0, top, t));
    g.stroke(&hbar(cx - 1.3 * t, cx + 1.3 * t, top - t / 2.0, t));
    // the hands, at three o'clock
    let reach = r - t;
    g.stroke(&path(
        &[
            pt(cx, cy + 0.70 * reach),
            pt(cx, cy),
            pt(cx + 0.56 * reach, cy),
        ],
        0.9 * t,
        0.0,
        90.0,
    ));
}

fn warning_sign(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let hx = p.mid() - 12.0;
    let (y0, y1) = (28.0, p.cap - 60.0);
    outline(
        g,
        &[pt(p.mid() - hx, y0), pt(p.mid() + hx, y0), pt(p.mid(), y1)],
        t,
    );
    // the bang: a stem and a dot, low in the triangle where it is wide
    let w = 0.95 * t;
    let dot_y = y0 + t + 30.0 + w / 2.0;
    g.rect(
        p.mid() - w / 2.0,
        dot_y - w / 2.0,
        p.mid() + w / 2.0,
        dot_y + w / 2.0,
    );
    let stem_y = dot_y + w / 2.0 + 34.0;
    g.rect(
        p.mid() - w / 2.0,
        stem_y,
        p.mid() + w / 2.0,
        stem_y + 0.26 * (y1 - y0),
    );
}

fn lower_right_pencil(g: &mut Draw) {
    pencil_(g, -45.0);
}

fn pencil(g: &mut Draw) {
    pencil_(g, 0.0);
}

/// A pencil pointing along `heading`: a cap, the barrel, and the sharpened point, separated by slits.
fn pencil_(g: &mut Draw, heading: f64) {
    let p = g.p;
    let c = pt(p.mid(), centre(p));
    let d = V::unit(heading);
    let n = d.left();
    let length = 2.0 * half(p, LARGE) * (if heading != 0.0 { 1.22 } else { 1.0 });
    let w = 0.40 * half(p, FULL); // half the barrel's breadth
    let slit = 0.24 * p.op + 22.0;
    let cone = 2.1 * w;
    let capl = 0.9 * w;
    let u0 = -length / 2.0;

    let at = |u: f64, v: f64| -> V { c + d * u + n * v };

    g.poly(&[at(u0, -w), at(u0 + capl, -w), at(u0 + capl, w), at(u0, w)]);
    let (b0, b1) = (u0 + capl + slit, length / 2.0 - cone - slit);
    g.poly(&[at(b0, -w), at(b1, -w), at(b1, w), at(b0, w)]);
    g.poly(&[
        at(length / 2.0 - cone, -w),
        at(length / 2.0, 0.0),
        at(length / 2.0 - cone, w),
    ]);
}

// ---------------------------------------------------------------------------------------------------------------
// stars, asterisks and ornaments

/// A star with `points` points of radius `r`; its inner corners lie at `waist` times `r`.
fn star(c: V, points: u32, r: f64, waist: f64, heading: f64) -> Vec<V> {
    let step = 180.0 / f64::from(points);
    (0..2 * points)
        .map(|i| {
            c + (if i % 2 == 0 { r } else { waist * r }) * V::unit(heading + f64::from(i) * step)
        })
        .collect()
}

fn scaled(points: &[V], c: V, f: f64) -> Vec<V> {
    points.iter().map(|&z| c + (z - c) * f).collect()
}

/// A star (or any polygon whose edges are all equally far from `c`) with its edges moved inwards by `t`: the
/// same star, smaller.
fn star_inset(points: &[V], c: V, t: f64) -> Vec<V> {
    let (a, b) = (points[0] - c, points[1] - c);
    let apothem = (a.x * b.y - a.y * b.x).abs() / (b - a).abs();
    scaled(points, c, 1.0 - t / apothem)
}

fn four_star(p: &Params) -> (Vec<V>, V) {
    let c = pt(p.mid(), centre(p));
    (star(c, 4, 1.10 * half(p, LARGE), 0.40, 90.0), c)
}

fn black_four_pointed_star(g: &mut Draw) {
    g.poly(&four_star(g.p).0);
}

fn white_four_pointed_star(g: &mut Draw) {
    let p = g.p;
    let (s, c) = four_star(p);
    g.poly(&s);
    hole(g, &star_inset(&s, c, line(p, SMALL)));
}

fn five_star(p: &Params) -> (Vec<V>, V) {
    let r = 1.12 * half(p, LARGE);
    let c = pt(p.mid(), centre(p) - 0.06 * r); // the star's box is centred, not its middle
    (star(c, 5, r, 0.47, 90.0), c)
}

fn black_star(g: &mut Draw) {
    g.poly(&five_star(g.p).0);
}

fn white_star(g: &mut Draw) {
    let p = g.p;
    let (s, c) = five_star(p);
    g.poly(&s);
    hole(g, &star_inset(&s, c, line(p, SMALL)));
}

fn eight_pointed_black_star(g: &mut Draw) {
    let p = g.p;
    g.poly(&star(
        pt(p.mid(), centre(p)),
        8,
        1.06 * half(p, LARGE),
        0.56,
        90.0,
    ));
}

/// `spokes` bars through the centre, the first one upright, cut square.
fn asterisk(g: &mut Draw, spokes: u32, t: f64, r: f64) {
    let c = pt(g.p.mid(), centre(g.p));
    for i in 0..spokes {
        g.poly(&spoke(
            c,
            -r,
            r,
            90.0 + f64::from(i) * 180.0 / f64::from(spokes),
            t,
        ));
    }
}

fn heavy_asterisk(g: &mut Draw) {
    let p = g.p;
    asterisk(g, 3, 0.92 * heavy(p), 1.08 * half(p, FULL));
}

fn eight_spoked_asterisk(g: &mut Draw) {
    let p = g.p;
    asterisk(g, 4, 0.92 * fine(p), 1.10 * half(p, FULL));
}

/// A heavy chevron that points right (`sign` 1) or left (-1), `height` and `depth` being fractions of the full
/// class.
fn angle_ornament(g: &mut Draw, sign: f64, height: f64, depth: f64) {
    let p = g.p;
    let t = heavy(p);
    let rise = height * half(p, FULL);
    let back = depth * half(p, FULL);
    let reach = (t / 2.0) * back.hypot(rise) / rise; // from the centre line to the outline, at the point and at the cuts
    let tip = pt(p.mid() + sign * (back / 2.0), centre(p));
    g.stroke(&chevron(tip, -sign * back, rise, t));
    let _ = reach;
}

fn black_diamond_minus_white_x(g: &mut Draw) {
    let p = g.p;
    let reach = DIAMOND_W * half(p, FULL);
    let gap = (0.40 * p.op + 16.0) / 2.0_f64.sqrt();
    let (a, b) = ((reach + gap) / 2.0, (reach - gap) / 2.0);
    for d in [pt(1.0, 0.0), pt(0.0, 1.0), pt(-1.0, 0.0), pt(0.0, -1.0)] {
        let c = pt(p.mid(), centre(p)) + a * d;
        g.poly(&diamond(c.x, c.y, b, b));
    }
}

// ---------------------------------------------------------------------------------------------------------------
// ballot boxes

/// Draws the box; returns its centre and half its inner side.
fn ballot_box_(g: &mut Draw) -> (f64, f64, f64) {
    let p = g.p;
    let h = 0.96 * half(p, LARGE);
    let t = fine(p);
    outline(g, &square(p.mid(), centre(p), h, h), t);
    (p.mid(), centre(p), h - t)
}

fn ballot_box(g: &mut Draw) {
    ballot_box_(g);
}

fn ballot_box_with_check(g: &mut Draw) {
    let (cx, cy, h) = ballot_box_(g);
    let t = 1.05 * fine(g.p);
    g.poly(&tick(
        pt(cx - 0.80 * h, cy + 0.10 * h),
        pt(cx - 0.20 * h, cy - 0.74 * h),
        pt(cx + 0.80 * h, cy + 0.76 * h),
        t,
        0.5 * t,
    ));
}

fn ballot_box_with_x(g: &mut Draw) {
    let (cx, cy, h) = ballot_box_(g);
    let t = 1.0 * fine(g.p);
    let e = 0.74 * h;
    let b = t * 2.0_f64.sqrt();
    g.stroke(&path(
        &[pt(cx - e + b / 2.0, cy - e), pt(cx + e - b / 2.0, cy + e)],
        t,
        0.0,
        0.0,
    ));
    g.stroke(&path(
        &[pt(cx - e + b / 2.0, cy + e), pt(cx + e - b / 2.0, cy - e)],
        t,
        0.0,
        0.0,
    ));
}

// ---------------------------------------------------------------------------------------------------------------
// pictograms

fn high_voltage(g: &mut Draw) {
    let p = g.p;
    let (hx, hy) = (0.92 * half(p, FULL), p.cap / 2.0 + 2.0 * p.over);
    let c = pt(p.mid(), p.cap / 2.0);
    let shape = [
        (0.34, 1.0),
        (-0.86, -0.12),
        (-0.06, -0.12),
        (-0.38, -1.0),
        (0.86, 0.16),
        (0.08, 0.16),
    ];
    let points: Vec<V> = shape.iter().map(|&(x, y)| c + pt(x * hx, y * hy)).collect();
    g.poly(&points);
}

fn gear(g: &mut Draw) {
    let p = g.p;
    let c = pt(p.mid(), centre(p));
    let r = 1.16 * half(p, FULL);
    let root = 0.76 * r;
    let teeth = 8;
    let pitch = 360.0 / f64::from(teeth);
    let mut outline_pts: Vec<V> = Vec::new();
    for i in 0..teeth {
        let a = 90.0 + f64::from(i) * pitch;
        outline_pts.extend([
            c + root * V::unit(a - 0.31 * pitch),
            c + r * V::unit(a - 0.17 * pitch),
            c + r * V::unit(a + 0.17 * pitch),
            c + root * V::unit(a + 0.31 * pitch),
        ]);
    }
    g.poly(&outline_pts);
    g.add(superellipse(c.x, c.y, 0.36 * r, 0.36 * r, p.dot_k).reversed());
}

/// Draws the pole; returns the flag's box.
fn flag(g: &mut Draw) -> (f64, f64, f64, f64) {
    let p = g.p;
    let t = fine(p);
    let x = p.op_l + 40.0 + t / 2.0;
    g.stroke(&vstem(x, 0.0, p.cap, t));
    (x, p.cap - 1.56 * half(p, FULL), p.op_r() + 4.0, p.cap)
}

fn black_flag(g: &mut Draw) {
    let (x0, y0, x1, y1) = flag(g);
    g.rect(x0, y0, x1, y1);
}

fn white_flag(g: &mut Draw) {
    let (x0, y0, x1, y1) = flag(g);
    let t = fine(g.p);
    outline(
        g,
        &[
            pt(x0 - t / 2.0, y0),
            pt(x1, y0),
            pt(x1, y1),
            pt(x0 - t / 2.0, y1),
        ],
        t,
    );
}

pub fn register(reg: &mut Registry) {
    reg.module("symbols");
    let u = Opt::UPRIGHT;
    for (c, cls) in [
        ('■', FULL),
        ('◼', MIDDLE),
        ('◾', LESSER),
        ('▪', SMALL),
        ('⬝', TINY),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| black_square(g, cls));
    }
    for (c, cls) in [
        ('□', FULL),
        ('◻', MIDDLE),
        ('◽', LESSER),
        ('▫', SMALL),
        ('⬞', TINY),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| white_square(g, cls));
    }
    reg.ch_with('▢', u, white_square_rounded);
    reg.ch_with('▣', u, white_square_containing_black);
    reg.ch_with('▬', u, black_rectangle);
    reg.ch_with('▭', u, white_rectangle);
    reg.ch_with('▮', u, black_vertical_rectangle);
    reg.ch_with('▯', u, white_vertical_rectangle);
    reg.ch_with('▰', u, black_parallelogram);
    reg.ch_with('▱', u, white_parallelogram);
    for (c, cls, h) in [
        ('▲', FULL, 90.0),
        ('▼', FULL, -90.0),
        ('▶', FULL, 0.0),
        ('◀', FULL, 180.0),
        ('▴', SMALL, 90.0),
        ('▾', SMALL, -90.0),
        ('▸', SMALL, 0.0),
        ('◂', SMALL, 180.0),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| black_triangle(g, cls, h, tri));
    }
    for (c, cls, h) in [
        ('△', FULL, 90.0),
        ('▽', FULL, -90.0),
        ('▷', FULL, 0.0),
        ('◁', FULL, 180.0),
        ('▵', SMALL, 90.0),
        ('▿', SMALL, -90.0),
        ('▹', SMALL, 0.0),
        ('◃', SMALL, 180.0),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| white_triangle(g, cls, h, tri));
    }
    reg.ch_with('►', u, |g: &mut Draw| {
        black_triangle(g, FULL, 0.0, pointer)
    });
    reg.ch_with('◄', u, |g: &mut Draw| {
        black_triangle(g, FULL, 180.0, pointer)
    });
    reg.ch_with('▻', u, |g: &mut Draw| {
        white_triangle(g, FULL, 0.0, pointer)
    });
    reg.ch_with('◅', u, |g: &mut Draw| {
        white_triangle(g, FULL, 180.0, pointer)
    });
    for (c, sx, sy) in [
        ('◢', 1.0, -1.0),
        ('◣', -1.0, -1.0),
        ('◤', -1.0, 1.0),
        ('◥', 1.0, 1.0),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| corner_triangle(g, sx, sy));
    }
    reg.ch_with('◆', u, black_diamond);
    reg.ch_with('◇', u, white_diamond);
    reg.ch_with('◈', u, white_diamond_containing_black);
    reg.ch_with('◊', u, lozenge);
    reg.ch_with('●', u, black_circle);
    reg.ch_with('○', u, white_circle);
    reg.ch_with('◯', u, large_circle);
    reg.ch_with('◦', u, white_bullet);
    reg.ch_with('◌', u, dotted_circle);
    reg.ch_with('◉', u, fisheye);
    reg.ch_with('◎', u, bullseye);
    reg.ch_with('◍', u, circle_with_vertical_fill);
    for (c, first, count) in [
        ('◐', 1, 2), // left half black
        ('◑', 3, 2), // right half
        ('◒', 2, 2), // lower half
        ('◓', 0, 2), // upper half
        ('◔', 0, 1), // upper right quadrant
        ('◕', 2, 3), // all but the upper left quadrant
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| part_filled(g, first, count));
    }
    reg.ch_with('◖', u, left_half_black_circle);
    reg.ch_with('◗', u, right_half_black_circle);
    reg.ch_with('✓', u, check_mark);
    reg.ch_with('✔', u, heavy_check_mark);
    reg.ch_with('✕', u, multiplication_x);
    reg.ch_with('✖', u, heavy_multiplication_x);
    reg.ch_with('✗', u, ballot_x);
    reg.ch_with('✘', u, heavy_ballot_x);
    reg.ch_with('✚', u, heavy_greek_cross);
    reg.ch_with('✛', u, open_centre_cross);
    reg.ch_with('✜', u, heavy_open_centre_cross);
    reg.ch_with('☰', u, trigram_heaven);
    for (c, bits) in [
        ('☱', [1, 1, 0]),
        ('☲', [1, 0, 1]),
        ('☳', [1, 0, 0]),
        ('☴', [0, 1, 1]),
        ('☵', [0, 1, 0]),
        ('☶', [0, 0, 1]),
        ('☷', [0, 0, 0]),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| trigram(g, bits));
    }
    reg.ch_with('⏎', u, return_symbol);
    reg.ch_with('⎇', u, alternative_key);
    reg.ch_with('⌥', u, option_key);
    reg.ch_with('⧗', u, black_hourglass);
    reg.ch_with('⧖', u, white_hourglass);
    reg.ch_with('⧉', u, two_joined_squares);
    reg.ch_with('⏱', u, stopwatch);
    reg.ch_with('⚠', u, warning_sign);
    reg.ch_with('✎', u, lower_right_pencil);
    reg.ch_with('✏', u, pencil);
    reg.ch_with('✦', u, black_four_pointed_star);
    reg.ch_with('✧', u, white_four_pointed_star);
    reg.ch_with('★', u, black_star);
    reg.ch_with('☆', u, white_star);
    reg.ch_with('✴', u, eight_pointed_black_star);
    reg.ch_with('✱', u, heavy_asterisk);
    reg.ch_with('✳', u, eight_spoked_asterisk);
    for (c, sign, height, depth) in [
        ('❯', 1.0, 1.16, 0.84),
        ('❮', -1.0, 1.16, 0.84),
        ('❱', 1.0, 1.56, 0.62),
        ('❰', -1.0, 1.56, 0.62),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| {
            angle_ornament(g, sign, height, depth)
        });
    }
    reg.ch_with('❖', u, black_diamond_minus_white_x);
    reg.ch_with('☐', u, ballot_box);
    reg.ch_with('☑', u, ballot_box_with_check);
    reg.ch_with('☒', u, ballot_box_with_x);
    reg.ch_with('⚡', u, high_voltage);
    reg.ch_with('⚙', u, gear);
    reg.ch_with('⚑', u, black_flag);
    reg.ch_with('⚐', u, white_flag);
}
