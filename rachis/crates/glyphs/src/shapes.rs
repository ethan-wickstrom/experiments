//! Geometric shapes that `symbols.rs` lacks, the miscellaneous symbols people type (card suits, music signs, faces,
//! weather), a few dingbats, control pictures and the replacement character.
//!
//! The shapes are variations on the shapes of `symbols.rs` and keep its system exactly: the same centre, the same
//! size classes and the same strokes, so that ◧ is □ with its left half filled, ◴ is ○ with a quadrant marked off and
//! ▤ is □ hatched. The measurements of that system are private to `symbols.rs`; the ones used here are copied below
//! with the same names and numbers, and must change with them.
//!
//! Lines drawn inside a shape (hatching, the radii of ◴, the bisector of ◫) use `fine` (operators.rs), which grows
//! with weight more slowly than `p.op`, so that the counters stay open in the Bold. Hatching is lighter still.
//!
//! The pictograms (suits, notes, faces) are cap-height signs centred in the cell. Filled and outlined twins (♥ ♡,
//! ♦ ♢) are one construction: the outline is a stroke along a centre line, and the filled form is that stroke plus
//! the area its centre line encloses, so the two have the same outer edge.
//!
//! Every glyph is registered upright, as in `symbols.rs`: these are signs, and an italic must not slant them.

use rachis_kernel::geom::{intersect, lame_exponent};
use rachis_kernel::pen::{expand, polygon, skeleton, superellipse};
use rachis_kernel::{Contour, Draw, Knot, Opt, Params, Registry, Seg, V, knot, pt};

use crate::operators::{fine, rake};
use crate::parts::{cut_pen, diag, flip, hbar, mirror, ring, vstem};
use crate::typography::question_knots;

// ---------------------------------------------------------------------------------------------------------------
// the system of symbols.rs (copied: keep in step with it)

const LARGE: f64 = 244.0;
const FULL: f64 = 220.0;
const SMALL: f64 = 131.0;
const ROUND: f64 = 1.10;
const DIAMOND_W: f64 = 1.20;
const DIAMOND_H: f64 = 1.28;
const TRI_BASE: f64 = 1.14;
const TRI_DEPTH: f64 = 1.02;
const TRI_SHIFT: f64 = 0.06;

fn centre(p: &Params) -> f64 {
    p.axis + 12.0
}

fn grow(p: &Params) -> f64 {
    0.88 + 0.0016 * p.op
}

fn half(p: &Params, cls: f64) -> f64 {
    cls * grow(p)
}

fn r_(p: &Params, cls: f64) -> f64 {
    ROUND * half(p, cls)
}

/// `fine` of symbols.rs: the stroke of a pictogram with several strokes in one cell.
fn fine_pict(p: &Params) -> f64 {
    0.55 * p.op + 26.0
}

/// The stroke of check marks and crosses in symbols.rs.
fn mark(p: &Params) -> f64 {
    1.15 * p.op
}

// ---------------------------------------------------------------------------------------------------------------
// measurements of this group

/// The stroke of hatching: lighter than `fine`, so that three lines and four gaps fit in □ in the Bold.
fn hatch(p: &Params) -> f64 {
    0.30 * p.op + 22.0
}

/// The height the pictograms are centred on: half the cap height.
fn pict_y(p: &Params) -> f64 {
    p.cap / 2.0
}

// ---------------------------------------------------------------------------------------------------------------
// parts (some copied from symbols.rs, which keeps them private)

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
        out.push(intersect(q0, u0, q1, u1).expect("adjacent edges are not parallel"));
    }
    out
}

/// The polygon `points`, in either order, made counter-clockwise.
fn ccw(points: &[V]) -> Vec<V> {
    let n = points.len();
    let area: f64 = (0..n).map(|i| points[i].cross(points[(i + 1) % n])).sum();
    if area >= 0.0 { points.to_vec() } else { points.iter().rev().copied().collect() }
}

/// The polygon `points` drawn as an outline `t` thick with mitred corners. Its outer edge is the polygon itself.
fn outline(g: &mut Draw, points: &[V], t: f64) {
    let knots: Vec<Knot> = inset(&ccw(points), t / 2.0).into_iter().map(|z| Knot::at(z, t).line()).collect();
    g.stroke_closed(&knots);
}

fn square(cx: f64, cy: f64, hx: f64, hy: f64) -> Vec<V> {
    vec![pt(cx - hx, cy - hy), pt(cx + hx, cy - hy), pt(cx + hx, cy + hy), pt(cx - hx, cy + hy)]
}

fn disc(g: &mut Draw, cx: f64, cy: f64, r: f64) {
    let k = g.p.dot_k;
    g.dot_xy(cx, cy, r, r, k);
}

/// A ring `t` thick whose outer edge has the radius `r`: ○ of symbols.rs.
fn circle(g: &mut Draw, cx: f64, cy: f64, r: f64, t: f64) {
    let k = g.p.dot_k;
    g.stroke_closed(&ring(cx - r, cy - r, cx + r, cy + r, t, t, k));
}

/// A quadrant of the circle of radius `r` about `c` from the direction `a` to the direction `b` (unit vectors), as
/// the discs of symbols.rs draw it.
fn quadrant(c: V, r: f64, a: V, b: V, k: f64) -> Seg {
    Seg::Cubic(c + a * r, c + a * r + b * (k * r), c + b * r + a * (k * r), c + b * r)
}

/// `count` quadrants of the disc of radius `r`, counter-clockwise from the quadrant `first` (0 is east to north),
/// closed through the centre (or across, for a half).
fn sector(c: V, r: f64, first: i32, count: i32, k: f64) -> Contour {
    let unit = |q: i32| match q.rem_euclid(4) {
        0 => pt(1.0, 0.0),
        1 => pt(0.0, 1.0),
        2 => pt(-1.0, 0.0),
        _ => pt(0.0, -1.0),
    };
    let mut segs: Vec<Seg> = (first..first + count).map(|q| quadrant(c, r, unit(q), unit(q + 1), k)).collect();
    let (last, start) = (segs[segs.len() - 1].end(), segs[0].start());
    if count == 2 {
        segs.push(Seg::Line(last, start));
    } else {
        segs.extend([Seg::Line(last, c), Seg::Line(c, start)]);
    }
    Contour::new(segs).oriented(true)
}

/// Knots with superelliptic corners made into the master's rounds, as `Draw::stroke` does before it expands them:
/// for outlines built from a skeleton directly.
fn rounded(p: &Params, knots: &[Knot]) -> Vec<Knot> {
    knots
        .iter()
        .map(|k| match (p.lame, k.k, k.n) {
            (true, Some(sq), None) => Knot { n: Some(lame_exponent(sq)), ..*k },
            _ => *k,
        })
        .collect()
}

/// The centre lines of open strokes laid end to end, each one from where the last ended, as one filled contour:
/// the area that a closed outline drawn as several strokes encloses. A stroke given with `true` is run backwards.
fn enclosed(g: &mut Draw, parts: &[(&[Knot], bool)]) {
    let p = g.p;
    let mut segs: Vec<Seg> = Vec::new();
    for (knots, back) in parts {
        match skeleton(&rounded(p, knots), false) {
            Ok(sk) => {
                let s = sk.segs();
                if *back {
                    segs.extend(s.iter().rev().map(Seg::reversed));
                } else {
                    segs.extend(s);
                }
            }
            Err(e) => {
                g.glyph.errors.push(e);
                return;
            }
        }
    }
    g.add(Contour::new(segs).oriented(true));
}

/// The outline of the stroke through `knots`, cut out of the shapes under it.
fn carve(g: &mut Draw, knots: &[Knot]) {
    let p = g.p;
    match expand(&rounded(p, knots), false) {
        Ok(contours) => {
            for c in contours {
                g.add(c.oriented(false));
            }
        }
        Err(e) => g.glyph.errors.push(e),
    }
}

/// A round dot cut out of the shapes under it.
fn carve_dot(g: &mut Draw, cx: f64, cy: f64, r: f64) {
    let k = g.p.dot_k;
    g.add(superellipse(cx, cy, r, r, k).oriented(false));
}

/// A stroke `t` thick through `points` in straight segments with mitred corners, its ends cut along `ends` and
/// `end` (90: plumb; 0: level). Copied from symbols.rs.
fn path(points: &[V], t: f64, ends: f64, end: f64) -> Vec<Knot> {
    let breadth = |a: V, b: V, pen: f64| -> f64 {
        let d = (b - a) / (b - a).abs();
        t / d.cmul(V::unit(-pen)).y.abs()
    };
    let n = points.len();
    let first = Knot::at(points[0], breadth(points[0], points[1], ends)).pen(ends).line();
    let last = Knot::at(points[n - 1], breadth(points[n - 2], points[n - 1], end)).pen(end);
    let mut out = vec![first];
    out.extend(points[1..n - 1].iter().map(|&z| Knot::at(z, t).line()));
    out.push(last);
    out
}

/// A star with `points` points of radius `r`; its inner corners lie at `waist` times `r`. Copied from symbols.rs.
fn star(c: V, points: u32, r: f64, waist: f64, heading: f64) -> Vec<V> {
    let step = 180.0 / f64::from(points);
    (0..2 * points)
        .map(|i| c + (if i % 2 == 0 { r } else { waist * r }) * V::unit(heading + f64::from(i) * step))
        .collect()
}

/// A straight stroke `t` thick along `heading` from the distance `r0` to `r1` from `c`, cut square. Copied from
/// symbols.rs.
fn spoke(c: V, r0: f64, r1: f64, heading: f64, t: f64) -> Vec<V> {
    let d = V::unit(heading);
    let n = d.left() * t / 2.0;
    vec![c + d * r0 - n, c + d * r1 - n, c + d * r1 + n, c + d * r0 + n]
}

/// The convex polygon `points` cut by the half-plane on the left of the line through `a` along `u`.
fn clip(points: &[V], a: V, u: V) -> Vec<V> {
    let inside = |z: V| u.cross(z - a) >= 0.0;
    let n = points.len();
    let mut out = Vec::new();
    for i in 0..n {
        let (z0, z1) = (points[i], points[(i + 1) % n]);
        if inside(z0) {
            out.push(z0);
        }
        if inside(z0) != inside(z1)
            && let Some(z) = intersect(z0, z1 - z0, a, u)
        {
            out.push(z);
        }
    }
    out
}

// ---------------------------------------------------------------------------------------------------------------
// squares: □ with something in it

/// The centre and half the side of □.
fn sq_box(p: &Params) -> (f64, f64, f64) {
    (p.mid(), centre(p), half(p, FULL))
}

/// □ drawn with the stroke `t`.
fn white_square(g: &mut Draw, t: f64) {
    let (cx, cy, h) = sq_box(g.p);
    outline(g, &square(cx, cy, h, h), t);
}

/// □ with the polygon `fill` (in units of half its side, from its centre) filled.
fn square_part(g: &mut Draw, fill: &[(f64, f64)]) {
    let p = g.p;
    let (cx, cy, h) = sq_box(p);
    white_square(g, p.op);
    let pts: Vec<V> = fill.iter().map(|&(x, y)| pt(cx + x * h, cy + y * h)).collect();
    g.poly(&pts);
}

/// □ hatched: `lines` says which families of lines, as headings in degrees (0 horizontal, 90 vertical, 45 rising,
/// -45 falling). The outline is `fine`, as in ▣, so that three lines and four gaps fit in the Bold.
fn hatched(g: &mut Draw, lines: &[f64]) {
    let p = g.p;
    let (cx, cy, h) = sq_box(p);
    let t = fine_pict(p);
    white_square(g, t);
    let inner = h - t; // half the side of the counter
    let pitch = inner / 2.0; // four gaps across the counter, measured square to the lines
    let w = hatch(p);
    let e = h - t / 2.0; // the lines end inside the outline
    let bounds = square(cx, cy, e, e);
    let c = pt(cx, cy);
    for &heading in lines {
        let d = V::unit(heading);
        let n = d.left();
        let slanted = heading % 90.0 != 0.0;
        let ks: &[f64] = if slanted { &[-2.0, -1.0, 0.0, 1.0, 2.0] } else { &[-1.0, 0.0, 1.0] };
        for &k in ks {
            let o = c + n * (k * pitch);
            let band = clip(&clip(&bounds, o - n * (w / 2.0), d), o + n * (w / 2.0), -d);
            g.poly(&band);
        }
    }
}

/// □ with lines from its centre to the middles of two sides, marking off the quadrant between them. `sx` and
/// `sy` say which: -1 left or below, 1 right or above.
fn square_quadrant(g: &mut Draw, sx: f64, sy: f64) {
    let p = g.p;
    let (cx, cy, h) = sq_box(p);
    white_square(g, p.op);
    let t = fine(p);
    let edge = h - p.op / 2.0;
    g.stroke(&vstem(cx, cy - sy * t / 2.0, cy + sy * edge, t));
    g.stroke(&hbar(cx + sx * edge, cx - sx * t / 2.0, cy, t));
}

fn square_bisected(g: &mut Draw) {
    let p = g.p;
    let (cx, cy, h) = sq_box(p);
    white_square(g, p.op);
    let edge = h - p.op / 2.0;
    g.stroke(&vstem(cx, cy - edge, cy + edge, fine(p)));
}

fn dotted_square(g: &mut Draw) {
    let p = g.p;
    let (cx, cy, h) = sq_box(p);
    // three dashes a side, a square one at each corner and one in each middle
    let t = 0.8 * p.op + 6.0;
    for (x, y) in [(-1.0, -1.0), (0.0, -1.0), (1.0, -1.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (-1.0, 1.0), (-1.0, 0.0)]
    {
        let (zx, zy) = (cx + x * (h - t / 2.0), cy + y * (h - t / 2.0));
        g.rect(zx - t / 2.0, zy - t / 2.0, zx + t / 2.0, zy + t / 2.0);
    }
}

// ---------------------------------------------------------------------------------------------------------------
// triangles

/// The corners of △ of symbols.rs: left foot, apex, right foot.
fn tri_up(p: &Params) -> (V, V, V) {
    let s = 2.0 * half(p, FULL);
    let (base, depth) = (TRI_BASE * s, TRI_DEPTH * s);
    let c = pt(p.mid(), centre(p) + depth * TRI_SHIFT);
    let y0 = c.y - depth / 2.0;
    (pt(c.x - base / 2.0, y0), pt(c.x, y0 + depth), pt(c.x + base / 2.0, y0))
}

fn white_up_triangle(g: &mut Draw, t: f64) {
    let (a, b, c) = tri_up(g.p);
    outline(g, &[a, c, b], t);
}

fn triangle_with_dot(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    white_up_triangle(g, t);
    let (a, b, c) = tri_up(p);
    let (base, side) = ((c - a).abs(), (b - a).abs());
    let r_in = (b.y - a.y) * base / (base + 2.0 * side); // the inscribed circle
    let r = 0.25 * r_in + 0.08 * p.op;
    disc(g, b.x, a.y + r_in, r);
}

fn triangle_half(g: &mut Draw, left: bool) {
    let p = g.p;
    white_up_triangle(g, p.op);
    let (a, b, c) = tri_up(p);
    let foot = if left { a } else { c };
    g.poly(&[foot, b, pt(b.x, a.y)]);
}

/// A right triangle outlined, its right angle in the corner (sx, sy) of the square of ■.
fn corner_triangle(g: &mut Draw, sx: f64, sy: f64) {
    let p = g.p;
    let (cx, cy, h) = sq_box(p);
    let c = pt(cx, cy);
    // `fine`: a right triangle's counter is small, and with the stroke of △ it closes in the Bold
    outline(g, &[c + pt(sx * h, sy * h), c + pt(-sx * h, sy * h), c + pt(sx * h, -sy * h)], fine(p));
}

// ---------------------------------------------------------------------------------------------------------------
// diamonds and the hexagon

fn diamond_pts(p: &Params) -> Vec<V> {
    let h = half(p, FULL);
    let (cx, cy, hx, hy) = (p.mid(), centre(p), DIAMOND_W * h, DIAMOND_H * h);
    vec![pt(cx, cy - hy), pt(cx + hx, cy), pt(cx, cy + hy), pt(cx - hx, cy)]
}

/// ◇ with half of it filled: the half on the side `heading` points to.
fn diamond_half(g: &mut Draw, heading: f64) {
    let p = g.p;
    let d = diamond_pts(p);
    outline(g, &d, p.op);
    let c = pt(p.mid(), centre(p));
    let u = V::unit(heading);
    let fill = clip(&d, c, u.right()); // the half where (z - c) · u ≥ 0
    g.poly(&fill);
}

fn black_hexagon(g: &mut Draw) {
    let p = g.p;
    let r = 1.13 * half(p, FULL);
    let c = pt(p.mid(), centre(p));
    let pts: Vec<V> = (0..6).map(|i| c + V::unit(90.0 + 60.0 * f64::from(i)) * r).collect();
    g.poly(&pts);
}

// ---------------------------------------------------------------------------------------------------------------
// circles: ○ in parts, and the inverse shapes

fn white_circle(g: &mut Draw) -> (V, f64) {
    let p = g.p;
    let (c, r) = (pt(p.mid(), centre(p)), r_(p, FULL));
    circle(g, c.x, c.y, r, p.op);
    (c, r)
}

/// ○ with lines from its centre to its edge on the sides (sx, 0) and (0, sy), marking off a quadrant.
fn circle_quadrant(g: &mut Draw, sx: f64, sy: f64) {
    let p = g.p;
    let (c, r) = white_circle(g);
    let t = fine(p);
    let edge = r - p.op / 2.0;
    g.stroke(&vstem(c.x, c.y - sy * t / 2.0, c.y + sy * edge, t));
    g.stroke(&hbar(c.x + sx * edge, c.x - sx * t / 2.0, c.y, t));
}

/// The centre-line knots of ○ at east, north, west and south.
fn circle_knots(p: &Params) -> [Knot; 4] {
    let (cx, cy) = (p.mid(), centre(p));
    let rc = r_(p, FULL) - p.op / 2.0;
    let (t, k) = (p.op, p.dot_k);
    [knot(cx + rc, cy, t).k(k), knot(cx, cy + rc, t).k(k), knot(cx - rc, cy, t).k(k), knot(cx, cy - rc, t).k(k)]
}

/// The arc of ○ from the quadrant point `from` (0 east, 1 north, 2 west, 3 south) through `count` quadrants,
/// counter-clockwise.
fn circle_arc(g: &mut Draw, from: usize, count: usize) {
    let ks = circle_knots(g.p);
    let knots: Vec<Knot> = (0..=count)
        .map(|i| {
            let q = (from + i) % 4;
            ks[q].dir(90.0 * q as f64 + 90.0)
        })
        .collect();
    g.stroke(&knots);
}

/// The ring of ◙: how wide the white ring is. It narrows a little with weight, as the black round it grows.
fn inverse_ring(p: &Params) -> f64 {
    120.0 - 0.3 * p.op
}

fn inverse_bullet(g: &mut Draw) {
    let p = g.p;
    g.rect(0.0, p.line_bot, p.width, p.line_top);
    carve_dot(g, p.mid(), centre(p), r_(p, SMALL));
}

fn inverse_white_circle(g: &mut Draw) {
    let p = g.p;
    let (cx, cy, r) = (p.mid(), centre(p), r_(p, FULL));
    g.rect(0.0, p.line_bot, p.width, p.line_top);
    carve_dot(g, cx, cy, r);
    disc(g, cx, cy, r - inverse_ring(p));
}

/// The upper (`up`) or lower half of ◙, cut at the centre of its ring.
fn inverse_half(g: &mut Draw, up: bool) {
    let p = g.p;
    let (k, r) = (p.dot_k, r_(p, FULL));
    let s = if up { 1.0 } else { -1.0 };
    let c = pt(p.mid(), centre(p));
    let far = if up { p.line_top } else { p.line_bot };
    let (e, w, n) = (pt(1.0, 0.0), pt(-1.0, 0.0), pt(0.0, s));
    // the half of the cell with a half disc notched out of its straight edge
    let segs = vec![
        Seg::Line(pt(0.0, c.y), c + w * r),
        quadrant(c, r, w, n, k),
        quadrant(c, r, n, e, k),
        Seg::Line(c + e * r, pt(p.width, c.y)),
        Seg::Line(pt(p.width, c.y), pt(p.width, far)),
        Seg::Line(pt(p.width, far), pt(0.0, far)),
        Seg::Line(pt(0.0, far), pt(0.0, c.y)),
    ];
    g.add(Contour::new(segs).oriented(true));
    g.add(sector(c, r - inverse_ring(p), if up { 0 } else { 2 }, 2, k));
}

fn heavy_circle(g: &mut Draw) {
    let p = g.p;
    circle(g, p.mid(), centre(p), r_(p, LARGE), 0.95 * p.op + 58.0);
}

/// ○ with one or two dots in it, or ● with one or two dots cut out of it: ⚆ ⚇ ⚈ ⚉.
fn circle_dots(g: &mut Draw, black: bool, two: bool) {
    let p = g.p;
    let (cx, cy, r) = (p.mid(), centre(p), r_(p, FULL));
    let t = fine(p);
    let rd = 0.20 * r + 0.1 * p.op;
    if black {
        disc(g, cx, cy, r);
    } else {
        circle(g, cx, cy, r, t);
    }
    let xs: &[f64] = if two { &[-0.40, 0.40] } else { &[0.40] };
    for &x in xs {
        if black {
            carve_dot(g, cx + x * r, cy, rd);
        } else {
            disc(g, cx + x * r, cy, rd);
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------
// stars

fn six_pointed_star(g: &mut Draw) {
    let p = g.p;
    g.poly(&star(pt(p.mid(), centre(p)), 6, 1.08 * half(p, LARGE), 0.50, 90.0));
}

fn eight_pointed_rectilinear(g: &mut Draw, heavy: bool) {
    let p = g.p;
    let r = 1.08 * half(p, LARGE);
    g.poly(&star(pt(p.mid(), centre(p)), 8, r, if heavy { 0.50 } else { 0.38 }, 90.0));
}

fn twelve_pointed_star(g: &mut Draw) {
    let p = g.p;
    g.poly(&star(pt(p.mid(), centre(p)), 12, 1.08 * half(p, LARGE), 0.62, 90.0));
}

fn sixteen_pointed_asterisk(g: &mut Draw) {
    let p = g.p;
    let c = pt(p.mid(), centre(p));
    let r = 1.06 * half(p, LARGE);
    let t = 0.28 * p.op + 20.0;
    for i in 0..8 {
        g.poly(&spoke(c, -r, r, 90.0 + f64::from(i) * 22.5, t));
    }
}

fn black_small_star(g: &mut Draw) {
    let p = g.p;
    let r = 1.12 * half(p, SMALL) * 1.15;
    let c = pt(p.mid(), centre(p) - 0.06 * r);
    g.poly(&star(c, 5, r, 0.47, 90.0));
}

fn circled_white_star(g: &mut Draw) {
    let p = g.p;
    let (cx, cy, r) = (p.mid(), centre(p), r_(p, LARGE));
    disc(g, cx, cy, r);
    let rs = 0.80 * r;
    let s = star(pt(cx, cy - 0.06 * rs), 5, rs, 0.47, 90.0);
    g.add(polygon(&s).oriented(false));
}

// ---------------------------------------------------------------------------------------------------------------
// card suits

/// The suits are as tall as the capitals and centred in the cell; this is half their width.
fn suit_half(p: &Params) -> f64 {
    0.5 * (p.op_r() - p.op_l) + 26.0
}

/// The stroke of the outlined suits.
fn suit_line(p: &Params) -> f64 {
    0.85 * p.op + 8.0
}

/// The centre line of the left half of a heart whose outer edge spans `y0` (its point) to `y1` (its lobes) and
/// half the width `a`, drawn with a pen `t` broad. The lobe is a circle; the side is the tangent to it from the
/// point. The line runs from the point up the side, round the lobe and down into the cleft, and is cut plumb on
/// the middle line at both ends so that it meets its mirror image there in a mitre.
fn heart_half(cx: f64, y0: f64, y1: f64, a: f64, t: f64) -> Vec<Knot> {
    let ac = a - t / 2.0; // the half width on the centre line
    let overlap = 0.74; // how far apart the two lobes' centres are, as a fraction of their radius, each side
    let r = ac / (1.0 + overlap);
    let o = pt(cx - overlap * r, y1 - t / 2.0 - r);
    // the point, its outer corner on y0: the mitre reaches (t / 2) / sin(half its angle) below the centre line
    let mut bottom = pt(cx, y0 + t);
    let mut u = pt(0.0, 1.0);
    for _ in 0..4 {
        let v = o - bottom;
        let d = v.abs();
        let turn = (r / d).asin();
        u = (v / d).cmul(V::unit(turn.to_degrees()));
        bottom = pt(cx, y0 + (t / 2.0) / -u.x);
    }
    // the side bows out a little: it leaves the point turned outwards and meets the lobe at its widest
    let leave = u.angle() + 9.0;
    let cleft_y = o.y + (r * r - (cx - o.x).powi(2)).sqrt();
    let cleft_dir = pt(cleft_y - o.y, -(cx - o.x)).angle();
    vec![
        cut_pen(bottom.x, bottom.y, t, leave, 90.0),
        knot(o.x - r, o.y, t).dir(90.0),
        knot(o.x, o.y + r, t).dir(0.0),
        cut_pen(cx, cleft_y, t, cleft_dir, 90.0),
    ]
}

/// ♥ (`black`) or ♡, its point at `y0` and its lobes at `y1`.
fn heart(g: &mut Draw, y0: f64, y1: f64, black: bool) {
    let p = g.p;
    let (cx, a, t) = (p.mid(), suit_half(p), suit_line(p));
    let left = heart_half(cx, y0, y1, a, t);
    let right = mirror(&left, cx);
    g.stroke(&left);
    g.stroke(&right);
    if black {
        enclosed(g, &[(&left, false), (&right, true)]);
    }
}

fn heart_suit(g: &mut Draw, black: bool) {
    let p = g.p;
    heart(g, -2.0 * p.over, p.cap + p.over, black);
}

/// The quarter of a diamond's centre line from its top to its right corner; the sides are slightly hollow.
/// How much hollower than straight a diamond's sides leave its corners, in degrees.
const HOLLOW: f64 = 6.0;

fn diamond_quarter(cx: f64, cy: f64, a: f64, b: f64, t: f64) -> Vec<Knot> {
    let (top, right) = (pt(cx, cy + b), pt(cx + a, cy));
    let chord = (right - top).angle();
    vec![cut_pen(top.x, top.y, t, chord - HOLLOW, 90.0), cut_pen(right.x, right.y, t, chord + HOLLOW, 0.0)]
}

fn diamond_suit(g: &mut Draw, black: bool) {
    let p = g.p;
    let t = suit_line(p);
    let (cx, cy) = (p.mid(), pict_y(p));
    // the outer points: on the cap height and the baseline, overshooting them as pointed shapes do, and as wide
    // as the other suits less a little; the mitres reach (t / 2) / sin(half their angle) past the centre line
    let (outer_b, outer_a) = (p.cap / 2.0 + 2.0 * p.over, 0.92 * suit_half(p));
    let (mut a, mut b) = (outer_a - t, outer_b - t);
    for _ in 0..6 {
        let chord = pt(a, -b).angle().to_radians();
        let (d_top, d_side) = (chord - HOLLOW.to_radians(), chord + HOLLOW.to_radians());
        b = outer_b - (t / 2.0) / d_top.cos().abs();
        a = outer_a - (t / 2.0) / d_side.sin().abs();
    }
    let ur = diamond_quarter(cx, cy, a, b, t);
    let ul = mirror(&ur, cx);
    let lr = flip(&ur, cy);
    let ll = flip(&ul, cy);
    for q in [&ur, &ul, &lr, &ll] {
        g.stroke(q);
    }
    if black {
        enclosed(g, &[(&ur, false), (&lr, true), (&ll, false), (&ul, true)]);
    }
}

/// The stem of ♠ and ♣: from the body at `y1` down to a foot that flares out to `w` each side of the middle.
fn suit_stem(g: &mut Draw, y1: f64, w: f64) {
    let p = g.p;
    let cx = p.mid();
    let neck = 0.20 * p.op + 12.0; // half the stem's breadth where it leaves the body
    let y0 = 0.0;
    let k = 0.55;
    let (a, b) = (pt(cx - neck, y1), pt(cx - w, y0));
    let (c, d) = (pt(cx + w, y0), pt(cx + neck, y1));
    // the sides are hollow: they leave the body straight down and reach the foot nearly level
    let left = Seg::Cubic(a, a + pt(0.0, -(y1 - y0) * k), b + pt((w - neck) * k, 0.0), b);
    let right = Seg::Cubic(c, c + pt(-(w - neck) * k, 0.0), d + pt(0.0, -(y1 - y0) * k), d);
    g.add(Contour::new(vec![left, Seg::Line(b, c), right, Seg::Line(d, a)]).oriented(true));
}

fn spade(g: &mut Draw) {
    let p = g.p;
    let (cx, a, t) = (p.mid(), suit_half(p), suit_line(p));
    // a heart turned over, its point on the cap height, its lobes well above the baseline
    let (y0, y1) = (0.22 * p.cap, p.cap + 2.0 * p.over);
    let mid = (y0 + y1) / 2.0;
    let left = flip(&heart_half(cx, 2.0 * mid - y1, 2.0 * mid - y0, a, t), mid);
    let right = mirror(&left, cx);
    g.stroke(&left);
    g.stroke(&right);
    enclosed(g, &[(&left, false), (&right, true)]);
    suit_stem(g, y0 + 0.30 * (y1 - y0), 0.42 * a);
}

fn club(g: &mut Draw) {
    let p = g.p;
    let (cx, a) = (p.mid(), suit_half(p));
    let r = 0.47 * a; // the leaves
    let top = p.cap + p.over - r;
    let side = (cx - a + r, top - 1.62 * r);
    disc(g, cx, top, r);
    disc(g, side.0, side.1, r);
    disc(g, 2.0 * cx - side.0, side.1, r);
    // the middle, where the three leaves meet
    g.poly(&[
        pt(cx, top - 0.2 * r),
        pt(side.0 + 0.3 * r, side.1 - 0.1 * r),
        pt(2.0 * cx - side.0 - 0.3 * r, side.1 - 0.1 * r),
    ]);
    suit_stem(g, side.1, 0.42 * a);
}

// ---------------------------------------------------------------------------------------------------------------
// music

/// The stroke of a note's stem and of the upright strokes of the accidentals: thin, as engraved.
fn music_thin(p: &Params) -> f64 {
    0.50 * p.op + 16.0
}

/// The stroke of a beam and of the cross strokes of the accidentals: thick.
fn music_thick(p: &Params) -> f64 {
    1.1 * p.op + 22.0
}

/// A note head: an ellipse tilted up to the right, centred on (cx, cy), `rx` by `ry`. Returns where a stem on its
/// right side stands.
fn note_head(g: &mut Draw, cx: f64, cy: f64, rx: f64, ry: f64) -> f64 {
    let tilt = 20f64.to_radians();
    let (c, s) = (tilt.cos(), tilt.sin());
    let head = superellipse(0.0, 0.0, rx, ry, 0.56).mapped(|z| pt(cx + z.x * c - z.y * s, cy + z.x * s + z.y * c));
    g.add(head);
    // the rightmost point of the tilted ellipse
    cx + (rx * rx * c * c + ry * ry * s * s).sqrt()
}

/// How far a stem stands inside the head's rightmost point.
fn stem_in(p: &Params) -> f64 {
    music_thin(p) / 2.0
}

fn quarter_note(g: &mut Draw) -> (f64, f64) {
    let p = g.p;
    let (rx, ry) = (118.0, 82.0);
    let (cx, cy) = (p.mid() - 72.0, 76.0);
    let xs = note_head(g, cx, cy, rx, ry) - stem_in(p);
    let top = p.cap + 20.0;
    g.stroke(&vstem(xs, cy + 20.0, top, music_thin(p)));
    (xs, top)
}

fn crotchet(g: &mut Draw) {
    quarter_note(g);
}

fn eighth_note(g: &mut Draw) {
    let p = g.p;
    let (xs, top) = quarter_note(g);
    let ts = music_thin(p);
    // the flag: it leaves the stem thick, swells down and to the right and tapers into a hook
    g.stroke(&[
        knot(xs - ts / 2.0 + 0.6 * music_thick(p) / 2.0, top - 0.6 * music_thick(p) / 2.0, 0.6 * music_thick(p))
            .dir(-38.0),
        knot(xs + 150.0, top - 210.0, 0.55 * music_thick(p)).dir(-80.0),
        knot(xs + 104.0, top - 400.0, 0.30 * music_thick(p)).dir(-120.0),
    ]);
}

fn beamed_eighths(g: &mut Draw) {
    let p = g.p;
    let (rx, ry) = (96.0, 68.0);
    let ts = music_thin(p);
    let x0 = p.op_l - 14.0 + rx;
    let x1 = p.op_r() - 14.0 - rx * 0.9;
    let (y0, y1) = (62.0, 132.0); // the second head is a step higher
    let s0 = note_head(g, x0, y0, rx, ry) - stem_in(p);
    let s1 = note_head(g, x1, y1, rx, ry) - stem_in(p);
    let (top0, top1) = (p.cap - 10.0, p.cap + 50.0);
    let beam = music_thick(p);
    g.stroke(&vstem(s0, y0 + 20.0, top0, ts));
    g.stroke(&vstem(s1, y1 + 20.0, top1, ts));
    let (xa, xb) = (s0 - ts / 2.0, s1 + ts / 2.0);
    let slope = (top1 - top0) / (s1 - s0);
    g.stroke(&rake(xa, top0 - beam / 2.0 + slope * (xa - s0), xb, top0 - beam / 2.0 + slope * (xb - s0), beam));
}

/// The span of the accidentals: centred on the axis, as # is.
fn acc_span(p: &Params) -> (f64, f64) {
    (p.axis - 370.0, p.axis + 370.0)
}

/// How far a cross stroke of ♯ and ♮ rises across its length.
const ACC_RISE: f64 = 0.36;

fn sharp(g: &mut Draw) {
    let p = g.p;
    let (lo, hi) = acc_span(p);
    let (thin, thick) = (music_thin(p), music_thick(p));
    let d = 82.0; // the uprights, each side of the middle
    let off = 0.07 * (hi - lo); // the right upright stands higher than the left
    g.stroke(&vstem(p.mid() - d, lo, hi - off, thin));
    g.stroke(&vstem(p.mid() + d, lo + off, hi, thin));
    let half_len = d + 92.0;
    for y in [p.axis - 120.0, p.axis + 120.0] {
        let rise = ACC_RISE * half_len;
        g.stroke(&rake(p.mid() - half_len, y - rise, p.mid() + half_len, y + rise, thick));
    }
}

fn natural(g: &mut Draw) {
    let p = g.p;
    let (lo, hi) = acc_span(p);
    let (thin, thick) = (music_thin(p), music_thick(p));
    let d = 78.0;
    let (xl, xr) = (p.mid() - d, p.mid() + d);
    let (xa, xb) = (xl - thin / 2.0, xr + thin / 2.0); // the cross strokes end flush with the uprights
    let rise = ACC_RISE * (xb - xa) / 2.0;
    let (y_up, y_dn) = (p.axis + 116.0, p.axis - 116.0); // the middles of the two cross strokes
    let edge = |y: f64, x: f64, s: f64| y + rise * (2.0 * (x - p.mid()) / (xb - xa)) + s * thick / 2.0;
    g.stroke(&vstem(xl, edge(y_dn, xl, -1.0) + 0.0, hi, thin));
    g.stroke(&vstem(xr, lo, edge(y_up, xr, 1.0), thin));
    for y in [y_up, y_dn] {
        g.stroke(&rake(xa, y - rise, xb, y + rise, thick));
    }
}

fn flat(g: &mut Draw) {
    let p = g.p;
    let thin = music_thin(p);
    let xs = p.mid() - 110.0;
    let (lo, hi) = (-p.over, p.cap + 50.0);
    g.stroke(&vstem(xs, lo, hi, thin));
    // the bowl: thin where it leaves the stem, heavy on the right, running to a point at the foot of the stem
    let top = 0.50 * p.cap;
    let right = p.mid() + 172.0;
    let heavy = 0.9 * p.op + 28.0;
    g.stroke(&[
        knot(xs, top - 0.22 * p.cap, thin).dir(48.0),
        knot(xs + 0.50 * (right - xs), top - 0.5 * thin, 0.9 * thin).dir(0.0),
        knot(right - heavy / 2.0, top - 0.24 * p.cap, heavy).dir(-90.0),
        knot(xs + thin / 2.0 + 10.0, lo + 0.6 * thin, 0.5 * thin).dir(-150.0),
    ]);
}

// ---------------------------------------------------------------------------------------------------------------
// other signs and pictograms

/// The stroke of the gender signs: lighter than an operator's in the Bold, where their rings would close.
fn gender_line(p: &Params) -> f64 {
    0.55 * p.op + 30.0
}

/// The gender signs' ring: its outer radius.
const GENDER_R: f64 = 182.0;

/// The foot of ♀ and ☿, below the baseline as the dagger's.
const FEMALE_BOT: f64 = -110.0;

fn female(g: &mut Draw) {
    let p = g.p;
    let t = gender_line(p);
    let (cx, r) = (p.mid(), GENDER_R);
    let cy = p.cap + p.over - r;
    circle(g, cx, cy, r, t);
    let y0 = FEMALE_BOT;
    g.stroke(&vstem(cx, y0, cy - r + t / 2.0, t));
    let yb = (cy - r + y0) / 2.0 + 6.0;
    g.stroke(&hbar(cx - 0.70 * r, cx + 0.70 * r, yb, t));
}

fn male(g: &mut Draw) {
    let p = g.p;
    let t = gender_line(p);
    let r = 0.90 * GENDER_R;
    // the ring at the left, the arrow at 45 degrees from its centre to the right side of the cell; in a cell
    // this narrow the sign is less tall than ♀, so it is centred on the middle of ♀'s height
    let cx = p.op_l - 6.0 + r;
    let tip_x = p.op_r() + 6.0 - t / 2.0;
    let d = tip_x - cx;
    let cy = (FEMALE_BOT + p.cap + r - d - t / 2.0) / 2.0;
    circle(g, cx, cy, r, t);
    let tip = pt(tip_x, cy + d);
    let start = pt(cx, cy) + V::unit(45.0) * (r - t / 2.0);
    let arm = 0.62 * r + 0.4 * t;
    g.stroke(&path(&[start, tip], t, 45.0 + 90.0, 45.0 + 90.0));
    g.stroke(&path(&[pt(tip.x - arm, tip.y), tip, pt(tip.x, tip.y - arm)], t, 90.0, 0.0));
}

fn mercury(g: &mut Draw) {
    let p = g.p;
    let t = gender_line(p);
    // ♀ with a smaller ring, to leave room for the horns: the lower half of a small ring that sits on it
    let (cx, r) = (p.mid(), 0.78 * GENDER_R);
    let (rh, th) = (0.78 * r, 0.75 * t); // the horns are lighter, so that they stay open
    let cy = p.cap + 20.0 - r - 1.25 * rh + th / 2.0;
    circle(g, cx, cy, r, t);
    let y0 = FEMALE_BOT;
    g.stroke(&vstem(cx, y0, cy - r + t / 2.0, t));
    let yb = (cy - r + y0) / 2.0 + 6.0;
    g.stroke(&hbar(cx - 0.80 * r, cx + 0.80 * r, yb, t));
    let ch = cy + r + rh - th / 2.0;
    g.stroke(&[
        knot(cx - rh + th / 2.0, ch + 0.25 * rh, th).pen(0.0).dir(-90.0).k(p.dot_k),
        knot(cx, ch - rh + th / 2.0, th).dir(0.0).k(p.dot_k),
        knot(cx + rh - th / 2.0, ch + 0.25 * rh, th).pen(0.0).dir(90.0),
    ]);
}

fn latin_cross(g: &mut Draw) {
    let p = g.p;
    let t = 0.75 * p.op + 40.0;
    let (cx, h) = (p.mid(), 1.14 * half(p, LARGE));
    let (y0, y1) = (pict_y(p) - h, pict_y(p) + h);
    g.stroke(&vstem(cx, y0, y1, t));
    let yb = y1 - 0.30 * (y1 - y0);
    g.stroke(&hbar(cx - 0.34 * (y1 - y0), cx + 0.34 * (y1 - y0), yb, t));
}

fn maltese_cross(g: &mut Draw) {
    let p = g.p;
    let c = pt(p.mid(), centre(p));
    let r = 1.08 * half(p, LARGE);
    let w = 0.10 * r; // half the arms' breadth at the centre
    for i in 0..4 {
        let d = V::unit(90.0 * f64::from(i));
        let n = d.left();
        // each arm widens to a notched end
        g.poly(&[c - n * w, c + d * r - n * 0.62 * r, c + d * 0.78 * r, c + d * r + n * 0.62 * r, c + n * w]);
    }
}

fn cloud(g: &mut Draw) {
    let p = g.p;
    let h = half(p, LARGE);
    let (cx, base) = (p.mid(), pict_y(p) - 0.62 * h);
    let (rl, rm, rr) = (0.40 * h, 0.62 * h, 0.48 * h);
    let (xl, xm, xr) = (cx - 1.02 * h + rl, cx - 0.10 * h, cx + 1.02 * h - rr);
    disc(g, xl, base + rl, rl);
    disc(g, xm, base + 0.95 * rm + 0.20 * h, rm);
    disc(g, xr, base + rr, rr);
    g.rect(xl, base, xr, base + rl);
}

/// ⛈: a cloud with a bolt of lightning and rain falling from it.
fn thunder_cloud(g: &mut Draw) {
    let p = g.p;
    let h = 0.86 * half(p, LARGE);
    let (cx, base) = (p.mid(), pict_y(p) + 0.05 * h);
    let (rl, rm, rr) = (0.40 * h, 0.62 * h, 0.48 * h);
    let (xl, xm, xr) = (cx - 1.02 * h + rl, cx - 0.10 * h, cx + 1.02 * h - rr);
    disc(g, xl, base + rl, rl);
    disc(g, xm, base + 0.95 * rm + 0.20 * h, rm);
    disc(g, xr, base + rr, rr);
    g.rect(xl, base, xr, base + rl);
    // the bolt, from under the cloud's middle down to the baseline
    let gap = 0.6 * fine(p) + 10.0;
    let (top, bot) = (base - gap, -p.over);
    g.poly(&[
        pt(cx - 0.05 * h, top),
        pt(cx + 0.38 * h, top),
        pt(cx + 0.10 * h, (top + bot) / 2.0 + 0.04 * h),
        pt(cx + 0.36 * h, (top + bot) / 2.0 + 0.04 * h),
        pt(cx - 0.18 * h, bot),
        pt(cx + 0.02 * h, (top + bot) / 2.0 - 0.06 * h),
        pt(cx - 0.24 * h, (top + bot) / 2.0 - 0.06 * h),
    ]);
    // rain on both sides
    let t = 0.5 * fine(p) + 8.0;
    for x in [xl - 0.15 * h, xr + 0.05 * h] {
        g.stroke(&diag(x + 0.10 * h, top - 0.06 * h, x - 0.06 * h, bot + 0.22 * h, t));
    }
}

/// A face: ○ (or ●, with its features cut out), two eyes and a mouth, smiling (`smile` 1) or frowning (-1).
fn face(g: &mut Draw, black: bool, smile: f64) {
    let p = g.p;
    let (cx, cy, r) = (p.mid(), centre(p), r_(p, LARGE) * 0.98);
    let t = fine(p);
    if black {
        disc(g, cx, cy, r);
    } else {
        circle(g, cx, cy, r, t);
    }
    let re = 0.11 * r + 0.08 * p.op;
    let (ex, ey) = (0.34 * r, cy + 0.24 * r);
    let tm = 0.9 * t;
    // the corners of the mouth and its middle: a smile dips, a frown arches, both in the lower half
    let mx = 0.46 * r;
    let (ends, middle) = if smile > 0.0 { (cy - 0.18 * r, cy - 0.50 * r) } else { (cy - 0.54 * r, cy - 0.28 * r) };
    let mouth = [
        knot(cx - mx, ends, tm).dir(-48.0 * smile),
        knot(cx, middle, tm).dir(0.0),
        knot(cx + mx, ends, tm).dir(48.0 * smile),
    ];
    if black {
        carve_dot(g, cx - ex, ey, re);
        carve_dot(g, cx + ex, ey, re);
        carve(g, &mouth);
    } else {
        disc(g, cx - ex, ey, re);
        disc(g, cx + ex, ey, re);
        g.stroke(&mouth);
    }
}

/// ☼ and ☀: a ring or a disc with eight rays.
fn sun(g: &mut Draw, black: bool) {
    let p = g.p;
    let c = pt(p.mid(), centre(p));
    let r = r_(p, LARGE);
    let t = fine(p);
    let core = 0.50 * r;
    if black {
        disc(g, c.x, c.y, core);
    } else {
        circle(g, c.x, c.y, core, t);
    }
    for i in 0..8 {
        g.poly(&spoke(c, core + 0.16 * r, r, 90.0 + 45.0 * f64::from(i), t));
    }
}

fn moon(g: &mut Draw) {
    let p = g.p;
    let h = 1.12 * half(p, LARGE);
    let (cx, cy) = (p.mid() - 0.10 * h, pict_y(p));
    // a crescent: one stroke whose pen swells from the horns to the middle
    let w = 0.46 * h;
    g.stroke(&[
        knot(cx + 0.45 * h, cy + 0.93 * h, 14.0).dir(160.0),
        knot(cx - 0.62 * h + w / 2.0, cy, w).dir(-90.0),
        knot(cx + 0.45 * h, cy - 0.93 * h, 14.0).dir(20.0),
    ]);
}

/// A die: a rounded square with pips at the positions (in units of a third of its inner half side).
fn die(g: &mut Draw, pips: &[(f64, f64)]) {
    let p = g.p;
    let t = fine(p);
    let h = half(p, FULL);
    let (cx, cy) = (p.mid(), centre(p));
    let hc = h - t / 2.0;
    let r = 0.40 * hc;
    let k = p.dot_k;
    g.stroke_closed(&[
        knot(cx + hc, cy - hc + r, t).dir(90.0).line(),
        knot(cx + hc, cy + hc - r, t).dir(90.0).k(k),
        knot(cx + hc - r, cy + hc, t).dir(180.0).line(),
        knot(cx - hc + r, cy + hc, t).dir(180.0).k(k),
        knot(cx - hc, cy + hc - r, t).dir(-90.0).line(),
        knot(cx - hc, cy - hc + r, t).dir(-90.0).k(k),
        knot(cx - hc + r, cy - hc, t).dir(0.0).line(),
        knot(cx + hc - r, cy - hc, t).dir(0.0).k(k),
    ]);
    let step = 0.52 * (h - t);
    let rp = 0.15 * (h - t) + 0.06 * p.op;
    for &(x, y) in pips {
        disc(g, cx + x * step, cy + y * step, rp);
    }
}

fn envelope(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let (hx, hy) = (half(p, LARGE), 0.70 * half(p, FULL));
    let (cx, cy) = (p.mid(), centre(p));
    outline(g, &square(cx, cy, hx, hy), t);
    // the flap: a V from the top corners to below the middle
    let reach = (t / 2.0) * (hx.hypot(hy)) / hx;
    let (x0, x1, top) = (cx - hx + 0.8 * t, cx + hx - 0.8 * t, cy + hy - t / 2.0);
    g.stroke(&path(&[pt(x0, top), pt(cx, cy - 0.15 * hy + reach), pt(x1, top)], t, 0.0, 0.0));
}

// ---------------------------------------------------------------------------------------------------------------
// control pictures and the replacement character

fn open_box(g: &mut Draw) {
    let p = g.p;
    let t = 0.9 * p.op;
    let (x0, x1) = (p.op_l + t / 2.0, p.op_r() - t / 2.0);
    let (y, top) = (t / 2.0, 0.38 * p.xh);
    g.stroke(&path(&[pt(x0, top), pt(x0, y), pt(x1, y), pt(x1, top)], t, 0.0, 0.0));
}

fn replacement(g: &mut Draw) {
    let p = g.p;
    let (cx, cy) = (p.mid(), pict_y(p));
    let a = 0.5 * (p.width - 2.0 * p.op_l) + 40.0;
    let b = p.cap / 2.0 + 60.0;
    g.poly(&[pt(cx, cy - b), pt(cx + a, cy), pt(cx, cy + b), pt(cx - a, cy)]);
    // the question mark, cut out
    let (sw, hw) = (0.56 * p.cap_stem + 18.0, 0.56 * p.cap_hair + 16.0);
    let r = 0.52 * p.punct + 12.0;
    let (y0, y1) = (cy - 0.50 * b, cy + 0.50 * b);
    let (x0, x1) = (cx - 0.40 * a, cx + 0.40 * a);
    let foot = y0 + 2.0 * r + 0.10 * (y1 - y0);
    let xs = (x0 + x1) / 2.0 + 0.02 * (x1 - x0);
    let knots = question_knots(p, x0, x1, y0, y1, xs, foot, sw, hw);
    carve(g, &knots);
    carve_dot(g, xs, y0 + r, r);
}

/// A control picture: a two-letter abbreviation in small capitals set down a diagonal from the top left, as
/// Unicode shows them. Each letter is the capital's own program run at a small size with strokes of its own, as
/// `digits.rs` draws its small figures: a little heavier than the full-size strokes scaled, so that the letters
/// hold at 16 px. (The three-letter pictures are not drawn: at 16 px their letters are four pixels tall.)
fn control_picture(g: &mut Draw, text: &str) {
    let p = g.p;
    let f = 0.55;
    let q = Params {
        mono: true,
        slant: 0.0,
        cap_stem: f * p.cap_stem + 16.0,
        cap_hair: f * p.cap_hair + 14.0,
        stem: f * p.stem + 16.0,
        hair: f * p.hair + 14.0,
        ..p.scaled(f)
    };
    let (w, h) = (q.width, q.cap);
    // the first letter's top a little above the cap height, the second on the baseline
    let top = p.cap + 30.0;
    for (i, c) in text.chars().enumerate() {
        let i = i as f64;
        let (dx, dy) = (i * (p.width - w), (1.0 - i) * (top - h));
        if c == 'I' {
            // the capital I has serifs drawn for the full-size cell; here it is a plain stem
            g.stroke(&vstem(dx + w / 2.0, dy, dy + h, q.cap_stem));
        } else {
            g.draw_as(&rachis_kernel::name_of(c), &q, dx, dy);
        }
    }
}

/// The glyph called `name`, upright, mirrored or not, centred in this cell. An upright glyph placed in an italic
/// master as a component would lean; this one is drawn as the upright master draws it.
fn upright_glyph(g: &mut Draw, name: &str, flipped: bool) -> Option<(f64, f64, f64, f64)> {
    let p = g.p;
    let up = Params { slant: 0.0, ..p.clone() };
    let Some(glyph) = g.glyph_as(name, &up) else {
        g.glyph.errors.push(format!("no glyph {name:?}"));
        return None;
    };
    let (w, dx) = (glyph.advance, (p.width - glyph.advance) / 2.0);
    for c in &glyph.contours {
        if flipped {
            g.add(c.mapped(|z| pt(w - z.x + dx, z.y)).reversed());
        } else {
            g.add(c.mapped(|z| pt(z.x + dx, z.y)));
        }
    }
    glyph
        .bounds()
        .map(|(x0, y0, x1, y1)| if flipped { (w - x1 + dx, y0, w - x0 + dx, y1) } else { (x0 + dx, y0, x1 + dx, y1) })
}

/// ␢: b with a bar through its ascender, as ƀ.
fn blank_symbol(g: &mut Draw) {
    let p = g.p;
    if let Some((x0, _, _, _)) = upright_glyph(g, "b", false) {
        let xs = x0 + p.stem / 2.0;
        g.stroke(&hbar(xs - p.stem / 2.0 - 70.0, xs + p.stem / 2.0 + 90.0, p.xh + 0.55 * (p.asc - p.xh), fine(p)));
    }
}

/// ␥: three slashes.
fn delete_form_two(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let (y0, y1) = (p.axis - 190.0, p.axis + 190.0);
    for dx in [-120.0, 0.0, 120.0] {
        g.stroke(&diag(p.mid() + dx - 110.0, y0, p.mid() + dx + 110.0, y1, t));
    }
}

/// ☖ and ☗: a shogi piece, a pentagon with a pointed roof.
fn shogi(g: &mut Draw, black: bool) {
    let p = g.p;
    let h = half(p, LARGE);
    let (cx, y0, y1) = (p.mid(), pict_y(p) - 1.05 * h, pict_y(p) + 1.12 * h);
    let pts = vec![
        pt(cx - 0.86 * h, y0),
        pt(cx + 0.86 * h, y0),
        pt(cx + 0.70 * h, y1 - 0.62 * h),
        pt(cx, y1),
        pt(cx - 0.70 * h, y1 - 0.62 * h),
    ];
    if black {
        g.poly(&pts);
    } else {
        outline(g, &pts, p.op);
    }
}

/// ☡: the caution sign, a Z with a slanted top.
fn caution(g: &mut Draw) {
    let p = g.p;
    let t = mark(p);
    let h = 1.10 * half(p, LARGE);
    let (cx, cy) = (p.mid(), pict_y(p));
    let (x0, x1) = (cx - 0.82 * h + t / 2.0, cx + 0.82 * h - t / 2.0);
    let (y0, y1) = (cy - h + t / 2.0, cy + h - t / 2.0);
    g.stroke(&path(&[pt(x0, y1 - 0.30 * h), pt(x1, y1), pt(x0, y0), pt(x1, y0 + 0.30 * h)], t, 90.0, 90.0));
}

/// ✂: two rings for the fingers on the left and two blades crossing towards the right.
fn scissors(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let h = half(p, LARGE);
    let (cx, cy) = (p.mid(), centre(p));
    let rr = 0.40 * h;
    let (rx, ry) = (cx - 1.04 * h + rr, 0.52 * h);
    let tr = 0.36 * p.op + 24.0;
    circle(g, rx, cy + ry, rr, tr);
    circle(g, rx, cy - ry, rr, tr);
    let tip = cx + 1.06 * h;
    for s in [1.0, -1.0] {
        // a blade leaves its ring towards the pivot and runs on, tapering, to the far side
        let start = pt(rx, cy + s * ry) + V::unit(-s * 36.0) * (rr - t / 2.0);
        g.stroke(&[Knot::at(start, 1.2 * t), knot(tip, cy - s * 0.30 * h, 0.35 * t)]);
    }
    disc(g, cx - 0.12 * h, cy, 0.45 * t);
}

/// ✽: eight teardrop spokes round a white centre.
fn teardrop_asterisk(g: &mut Draw) {
    let p = g.p;
    let c = pt(p.mid(), centre(p));
    let r = 1.08 * half(p, LARGE);
    for i in 0..8 {
        let d = V::unit(90.0 + 45.0 * f64::from(i));
        let (w0, w1) = (0.04 * r, 0.30 * r + 0.1 * p.op);
        g.stroke(&[
            Knot::at(c + d * (0.16 * r), w0).dir(d.angle()),
            Knot::at(c + d * (r - w1 / 2.0), w1).dir(d.angle()).line(),
            Knot::at(c + d * r, 0.5 * w1),
        ]);
    }
}

/// ❅: a snowflake, three bars through the middle, each arm with a V near its end.
fn snowflake(g: &mut Draw) {
    let p = g.p;
    let c = pt(p.mid(), centre(p));
    let r = 1.08 * half(p, LARGE);
    let t = 0.55 * fine(p) + 12.0;
    for i in 0..6 {
        let a = 90.0 + 60.0 * f64::from(i);
        let d = V::unit(a);
        g.poly(&spoke(c, 0.0, r, a, t));
        let base = c + d * (0.48 * r);
        for s in [-1.0, 1.0] {
            g.poly(&spoke(base, -t / 2.0, 0.34 * r, a + s * 45.0, t));
        }
    }
    disc(g, c.x, c.y, 0.8 * t);
}

/// ❬ (`sign` -1) and ❭: a medium angle bracket, taller than < and drawn heavier.
fn angle_ornament(g: &mut Draw, sign: f64) {
    let p = g.p;
    let t = 0.75 * (0.95 * p.op + 58.0);
    let rise = 1.40 * half(p, FULL);
    let back = 0.56 * half(p, FULL);
    let tip = pt(p.mid() + sign * back / 2.0, centre(p));
    let b = t * back.hypot(rise) / rise;
    g.stroke(&[
        Knot::at(tip + pt(-sign * back, rise), b).pen(0.0).line(),
        Knot::at(tip, t).line(),
        Knot::at(tip + pt(-sign * back, -rise), b).pen(0.0),
    ]);
}

pub fn register(reg: &mut Registry) {
    reg.module("shapes");
    let u = Opt::UPRIGHT;
    // squares
    for (c, lines) in [
        ('▤', &[0.0][..]),
        ('▥', &[90.0][..]),
        ('▦', &[0.0, 90.0][..]),
        ('▧', &[-45.0][..]),
        ('▨', &[45.0][..]),
        ('▩', &[45.0, -45.0][..]),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| hatched(g, lines));
    }
    for (c, fill) in [
        ('◧', &[(-1.0, -1.0), (0.0, -1.0), (0.0, 1.0), (-1.0, 1.0)][..]),
        ('◨', &[(0.0, -1.0), (1.0, -1.0), (1.0, 1.0), (0.0, 1.0)][..]),
        ('◩', &[(-1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)][..]),
        ('◪', &[(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0)][..]),
        ('⬒', &[(-1.0, 0.0), (1.0, 0.0), (1.0, 1.0), (-1.0, 1.0)][..]),
        ('⬓', &[(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (-1.0, 0.0)][..]),
        ('⬔', &[(-1.0, 1.0), (1.0, -1.0), (1.0, 1.0)][..]),
        ('⬕', &[(-1.0, 1.0), (-1.0, -1.0), (1.0, -1.0)][..]),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| square_part(g, fill));
    }
    reg.ch_with('◫', u, square_bisected);
    for (c, sx, sy) in [('◰', -1.0, 1.0), ('◱', -1.0, -1.0), ('◲', 1.0, -1.0), ('◳', 1.0, 1.0)] {
        reg.ch_with(c, u, move |g: &mut Draw| square_quadrant(g, sx, sy));
    }
    reg.ch_with('⬚', u, dotted_square);
    // triangles
    reg.ch_with('◬', u, triangle_with_dot);
    reg.ch_with('◭', u, |g: &mut Draw| triangle_half(g, true));
    reg.ch_with('◮', u, |g: &mut Draw| triangle_half(g, false));
    for (c, sx, sy) in [('◸', -1.0, 1.0), ('◹', 1.0, 1.0), ('◺', -1.0, -1.0), ('◿', 1.0, -1.0)] {
        reg.ch_with(c, u, move |g: &mut Draw| corner_triangle(g, sx, sy));
    }
    // diamonds, hexagon
    for (c, heading) in [('⬖', 180.0), ('⬗', 0.0), ('⬘', 90.0), ('⬙', -90.0)] {
        reg.ch_with(c, u, move |g: &mut Draw| diamond_half(g, heading));
    }
    reg.ch_with('⬢', u, black_hexagon);
    // circles
    for (c, sx, sy) in [('◴', -1.0, 1.0), ('◵', -1.0, -1.0), ('◶', 1.0, -1.0), ('◷', 1.0, 1.0)] {
        reg.ch_with(c, u, move |g: &mut Draw| circle_quadrant(g, sx, sy));
    }
    for (c, from, count) in [('◜', 1, 1), ('◝', 0, 1), ('◞', 3, 1), ('◟', 2, 1), ('◠', 0, 2), ('◡', 2, 2)] {
        reg.ch_with(c, u, move |g: &mut Draw| circle_arc(g, from, count));
    }
    reg.ch_with('◘', u, inverse_bullet);
    reg.ch_with('◙', u, inverse_white_circle);
    reg.ch_with('◚', u, |g: &mut Draw| inverse_half(g, true));
    reg.ch_with('◛', u, |g: &mut Draw| inverse_half(g, false));
    reg.ch_with('⭘', u, heavy_circle);
    for (c, black, two) in [('⚆', false, false), ('⚇', false, true), ('⚈', true, false), ('⚉', true, true)] {
        reg.ch_with(c, u, move |g: &mut Draw| circle_dots(g, black, two));
    }
    // stars
    reg.ch_with('✶', u, six_pointed_star);
    reg.ch_with('✷', u, |g: &mut Draw| eight_pointed_rectilinear(g, false));
    reg.ch_with('✸', u, |g: &mut Draw| eight_pointed_rectilinear(g, true));
    reg.ch_with('✹', u, twelve_pointed_star);
    reg.ch_with('✺', u, sixteen_pointed_asterisk);
    reg.ch_with('⭑', u, black_small_star);
    reg.ch_with('✪', u, circled_white_star);
    // suits
    reg.ch_with('♠', u, spade);
    reg.ch_with('♣', u, club);
    reg.ch_with('♥', u, |g: &mut Draw| heart_suit(g, true));
    reg.ch_with('♡', u, |g: &mut Draw| heart_suit(g, false));
    reg.ch_with('♦', u, |g: &mut Draw| diamond_suit(g, true));
    reg.ch_with('♢', u, |g: &mut Draw| diamond_suit(g, false));
    // music
    reg.ch_with('♩', u, crotchet);
    reg.ch_with('♪', u, eighth_note);
    reg.ch_with('♫', u, beamed_eighths);
    reg.ch_with('♭', u, flat);
    reg.ch_with('♮', u, natural);
    reg.ch_with('♯', u, sharp);
    // signs and pictograms
    reg.ch_with('♀', u, female);
    reg.ch_with('♂', u, male);
    reg.ch_with('☿', u, mercury);
    reg.ch_with('✝', u, latin_cross);
    reg.ch_with('✠', u, maltese_cross);
    reg.ch_with('☁', u, cloud);
    reg.ch_with('⛈', u, thunder_cloud);
    reg.ch_with('☺', u, |g: &mut Draw| face(g, false, 1.0));
    reg.ch_with('☻', u, |g: &mut Draw| face(g, true, 1.0));
    reg.ch_with('☹', u, |g: &mut Draw| face(g, false, -1.0));
    reg.ch_with('☼', u, |g: &mut Draw| sun(g, false));
    reg.ch_with('☀', u, |g: &mut Draw| sun(g, true));
    reg.ch_with('☾', u, moon);
    for (c, pips) in [
        ('⚀', &[(0.0, 0.0)][..]),
        ('⚁', &[(-1.0, 1.0), (1.0, -1.0)][..]),
        ('⚂', &[(-1.0, 1.0), (0.0, 0.0), (1.0, -1.0)][..]),
        ('⚃', &[(-1.0, 1.0), (1.0, 1.0), (-1.0, -1.0), (1.0, -1.0)][..]),
        ('⚄', &[(-1.0, 1.0), (1.0, 1.0), (0.0, 0.0), (-1.0, -1.0), (1.0, -1.0)][..]),
        ('⚅', &[(-1.0, 1.0), (1.0, 1.0), (-1.0, 0.0), (1.0, 0.0), (-1.0, -1.0), (1.0, -1.0)][..]),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| die(g, pips));
    }
    reg.ch_with('✉', u, envelope);
    // control pictures, replacement
    reg.ch_with('␣', u, open_box);
    reg.ch_with('\u{fffd}', u, replacement);
    for (cp, text) in [
        (0x2408, "BS"),
        (0x2409, "HT"),
        (0x240A, "LF"),
        (0x240B, "VT"),
        (0x240C, "FF"),
        (0x240D, "CR"),
        (0x240E, "SO"),
        (0x240F, "SI"),
        (0x2419, "EM"),
        (0x241C, "FS"),
        (0x241D, "GS"),
        (0x241E, "RS"),
        (0x241F, "US"),
        (0x2420, "SP"),
        (0x2424, "NL"),
    ] {
        reg.code(cp, u, move |g: &mut Draw| control_picture(g, text));
    }
    reg.ch_with('␢', u, blank_symbol);
    reg.ch_with('␥', u, delete_form_two);
    reg.ch_with('␦', u, |g: &mut Draw| {
        upright_glyph(g, "question", true);
    });
    reg.ch_with('☖', u, |g: &mut Draw| shogi(g, false));
    reg.ch_with('☗', u, |g: &mut Draw| shogi(g, true));
    reg.ch_with('☡', u, caution);
    reg.ch_with('✂', u, scissors);
    reg.ch_with('✽', u, teardrop_asterisk);
    reg.ch_with('❅', u, snowflake);
    reg.ch_with('❬', u, |g: &mut Draw| angle_ornament(g, -1.0));
    reg.ch_with('❭', u, |g: &mut Draw| angle_ornament(g, 1.0));
}
