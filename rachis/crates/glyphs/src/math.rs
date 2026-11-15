//! Mathematical operators and relations beyond the core of `operators.rs`: the n-ary operators, the integrals,
//! the partial differential and the triangles, the angles, and the negated, doubled and dotted relations.
//!
//! The group belongs to the system of `operators.rs` and is assembled from its primitives: the same axis
//! (`p.axis`), stroke (`p.op`, and `fine` for doubled parts) and span (`p.op_l` to `p.op_r`). A relation here
//! takes the parts of the relation it extends: ≇ is ≅ struck as ≠ is struck, ⪯ is ≺ over the bar of ≤.
//!
//! Three kinds are new. The n-ary operators (∑ ∏ ⋂ ⨁ ...) are their binary signs enlarged: centred on the axis
//! as brackets are, from below the baseline to above the cap height, wider than the span and drawn with
//! `nary_stroke`. The integrals are a slanted pen stroke that swells in the middle and tapers into hooks, from
//! `p.br_bot` to `p.br_top`. ∂ is a figure: cap height, with the strokes and the bowl logic of 6.

use rachis_kernel::{Draw, Knot, Opt, Params, Registry, V, knot, pt};

use crate::operators::{
    arc, bar, big_box, big_ring, box_, chevron, chevron_rise, circle, cross, curved_chevron, dot_gap, equal_pitch,
    fine, half_span, mirrored, outline, over, radical, rake, rel_gap, rel_rise, set_rise, slash, slash_run, small_ring,
    small_stroke, square_image, stand_top, stem, strike, struck, subset, tack, tack_rise, tip, transposed,
    triple_pitch, twin_pitch, twin_wave, wave, wave_rise, wedge,
};
use crate::parts::{Arch, arch, cut, cut_pen, diag, flip, hbar, mirror, moved, vee, vstem};

// ---------------------------------------------------------------------------------------------------------------
// Measurements the group derives from the parameters

/// Half the height of the n-ary operators: centred on the axis as the brackets are, and 0.92 as tall, so that
/// they reach a little above the cap height and about half the descender below the baseline.
pub fn nary_rise(p: &Params) -> f64 {
    0.46 * (p.br_top - p.br_bot)
}

/// Half the width of the n-ary operators: a little wider than the span.
pub fn nary_half(p: &Params) -> f64 {
    half_span(p) + 28.0
}

/// The stroke of the n-ary operators: heavier than `p.op` by as much as they are larger.
pub fn nary_stroke(p: &Params) -> f64 {
    1.1 * p.op
}

/// The stroke of a relation with three or four levels (≋ ≣): `fine`, so that the white between the levels
/// stays wider than a level at 13 px, and the Bold stays open.
pub fn level_stroke(p: &Params) -> f64 {
    fine(p)
}

/// The distance between the centre lines of the waves of ≋ and of the bars of ≣: about that of ≡, growing
/// slowly with weight so that the Bold stays within the x-height and a little.
pub fn level_pitch(p: &Params) -> f64 {
    128.0 + 0.45 * p.op
}

// ---------------------------------------------------------------------------------------------------------------
// N-ary operators

/// The box of an n-ary operator: left, right, bottom and top outer edges.
fn nary_box(p: &Params) -> (f64, f64, f64, f64) {
    let (h, r) = (nary_half(p), nary_rise(p));
    (p.mid() - h, p.mid() + h, p.axis - r, p.axis + r)
}

/// The zigzag of the summation sign: two straight strokes `t` thick, cut horizontally on `top` and `bot` with
/// their inner edges starting on `xl`, that meet in a point on `xt` flattened to `flat`.
fn zigzag(xl: f64, xt: f64, top: f64, bot: f64, t: f64, flat: f64) -> Vec<V> {
    let cy = (top + bot) / 2.0;
    let dy = top - cy - flat / 2.0;
    let mut wh = t; // the width of the horizontal cut
    for _ in 0..4 {
        let dx = xt - xl - wh;
        wh = t * dx.hypot(dy) / dy;
    }
    let dx = xt - xl - wh;
    let xc = xl + dx * (top - cy) / dy; // the crotch, on the inner edges
    vec![
        pt(xl, top),
        pt(xl + wh, top),
        pt(xt, cy + flat / 2.0),
        pt(xt, cy - flat / 2.0),
        pt(xl + wh, bot),
        pt(xl, bot),
        pt(xc, cy),
    ]
}

fn summation(g: &mut Draw) {
    let p = g.p;
    let t = nary_stroke(p);
    let (xl, xr, bot, top) = nary_box(p);
    let xt = p.mid() + 0.36 * nary_half(p);
    g.poly(&zigzag(xl + 6.0, xt, top, bot, t, tip(p)));
    bar(g, top - t / 2.0, Some(xl + 6.0), Some(xr - 6.0), Some(t));
    bar(g, bot + t / 2.0, Some(xl + 6.0), Some(xr), Some(t));
}

/// The product sign, or (`down`) the coproduct: two stems under a bar that overhangs them.
fn product(g: &mut Draw, down: bool) {
    let p = g.p;
    let t = nary_stroke(p);
    let (xl, xr, bot, top) = nary_box(p);
    let inset = 0.55 * t + t / 2.0; // the overhang, to the stems' centre lines
    let strokes = [
        hbar(xl, xr, top - t / 2.0, t),
        vstem(xl + inset, bot, top - t / 2.0, t),
        vstem(xr - inset, bot, top - t / 2.0, t),
    ];
    for s in strokes {
        g.stroke(&if down { flip(&s, p.axis) } else { s });
    }
}

fn nary_product(g: &mut Draw) {
    product(g, false);
}

fn nary_coproduct(g: &mut Draw) {
    product(g, true);
}

/// ⋀ and (`down`) ⋁: the wedge enlarged.
fn nary_wedge(g: &mut Draw, down: bool) {
    let p = g.p;
    let (xl, xr, bot, top) = nary_box(p);
    let (y0, y1) = if down { (top, bot) } else { (bot, top) };
    g.poly(&vee(xl, xr, y0, y1, nary_stroke(p), tip(p)));
}

fn nary_and(g: &mut Draw) {
    nary_wedge(g, false);
}

fn nary_or(g: &mut Draw) {
    nary_wedge(g, true);
}

/// The cup enlarged; `down` turns it into the cap.
fn nary_cup(g: &mut Draw, down: bool) {
    let p = g.p;
    let (xl, xr, bot, top) = nary_box(p);
    let a = transposed(&arc(p, bot - p.over, top, xl, xr, Some(nary_stroke(p))));
    g.stroke(&if down { flip(&a, p.axis) } else { a });
}

fn nary_union(g: &mut Draw) {
    nary_cup(g, false);
}

fn nary_intersection(g: &mut Draw) {
    nary_cup(g, true);
}

fn nary_union_plus(g: &mut Draw) {
    let p = g.p;
    nary_cup(g, false);
    let t = 1.1 * fine(p);
    let h = 0.40 * nary_half(p);
    let cy = p.axis - 0.10 * nary_rise(p);
    g.stroke(&hbar(p.mid() - h, p.mid() + h, cy, t));
    g.stroke(&vstem(p.mid(), cy - h, cy + h, t));
}

/// The square cup enlarged; `down` turns it into the square cap.
fn nary_square(g: &mut Draw, down: bool) {
    let p = g.p;
    let t = nary_stroke(p);
    let (xl, xr, bot, top) = nary_box(p);
    let (a, b) = (xl + 10.0 + t / 2.0, xr - 10.0 - t / 2.0);
    let k = vec![
        knot(a, top, t).pen(0.0).line(),
        knot(a, bot + t / 2.0, t).line(),
        knot(b, bot + t / 2.0, t).line(),
        knot(b, top, t).pen(0.0),
    ];
    g.stroke(&if down { flip(&k, p.axis) } else { k });
}

fn nary_square_cap(g: &mut Draw) {
    nary_square(g, true);
}

fn nary_square_cup(g: &mut Draw) {
    nary_square(g, false);
}

/// The ring of the n-ary circled operators. Returns the radii of its inner edge, across and up.
fn nary_ring(g: &mut Draw) -> (f64, f64) {
    let p = g.p;
    let t = nary_stroke(p);
    let r = p.mid() - 16.0 + p.over; // as wide as the cell allows
    circle(g, p.mid(), p.axis, r, Some(NARY_TALL * r), Some(t));
    (r - t, NARY_TALL * r - t)
}

/// How much taller than wide the ring of the n-ary circled operators is: the cell limits its width, and the
/// height is what tells ⨁ from ⊕.
const NARY_TALL: f64 = 1.12;

/// The stroke of what the n-ary circled operators hold.
fn nary_inner(p: &Params) -> f64 {
    1.12 * fine(p)
}

fn nary_circled_dot(g: &mut Draw) {
    let p = g.p;
    nary_ring(g);
    g.dot(p.mid(), p.axis, p.punct);
}

fn nary_circled_plus(g: &mut Draw) {
    let p = g.p;
    let (rx, ry) = nary_ring(g);
    let t = nary_inner(p);
    g.stroke(&hbar(p.mid() - rx - 4.0, p.mid() + rx + 4.0, p.axis, t));
    g.stroke(&vstem(p.mid(), p.axis - ry - 4.0, p.axis + ry + 4.0, t));
}

fn nary_circled_times(g: &mut Draw) {
    let p = g.p;
    let (r, _) = nary_ring(g);
    cross(g, p.mid(), p.axis, 0.70 * r, Some(nary_inner(p)));
}

// ---------------------------------------------------------------------------------------------------------------
// Integrals

/// The skeleton of the integral: from the hook at the top right over the crest, down the slanted spine through
/// (`cx`, the middle of the brackets) and round into the hook at the bottom left. It is symmetric about its
/// centre. `run` is how far the hooks reach to each side of `cx`; `t` is the breadth of the spine, which tapers
/// to the hooks.
fn integral_knots(p: &Params, cx: f64, run: f64, t: f64) -> Vec<Knot> {
    let (yt, yb) = (p.br_top, p.br_bot);
    let cy = (yt + yb) / 2.0;
    let (tc, te) = (0.74 * t, 0.50 * t); // at the crest, at the ends
    let hook = 0.165 * (yt - yb); // how far the ends hang below the crest
    let lean: f64 = 8.0; // the spine's angle from the vertical
    let u = lean.to_radians().tan();
    // the crest lies beyond where the spine's line meets the top, so that the turn into the spine is a plain
    // superelliptic corner
    let xc = u * (yt - cy) + 0.16 * run;
    let dl = 0.12 * (yt - yb); // the straight middle of the spine reaches this far from its centre
    let tm = 0.5 * (t + tc);
    vec![
        knot(cx + run - te / 2.0, yt - hook, te).dir(96.0),
        knot(cx + xc, yt - tc / 2.0, tc).dir(180.0).k(0.66),
        knot(cx + u * dl, cy + dl, tm).dir(-90.0 - lean).line(),
        knot(cx, cy, t).dir(-90.0 - lean).line(),
        knot(cx - u * dl, cy - dl, tm).dir(-90.0 - lean).k(0.66),
        knot(cx - xc, yb + tc / 2.0, tc).dir(180.0),
        knot(cx - run + te / 2.0, yb + hook, te).dir(96.0),
    ]
}

/// The breadth of the integral's spine.
fn integral_stroke(p: &Params) -> f64 {
    1.3 * p.op
}

/// How far the hooks of one integral reach to each side of its centre.
fn integral_run(p: &Params) -> f64 {
    175.0 + 0.55 * p.op
}

fn integral(g: &mut Draw) {
    let p = g.p;
    g.stroke(&integral_knots(p, p.mid(), integral_run(p), integral_stroke(p)));
}

/// `n` integrals side by side in one cell: closer, narrower and lighter the more there are.
fn integrals(g: &mut Draw, n: usize) {
    let p = g.p;
    let k = n as f64 - 1.0;
    let run = integral_run(p) * (1.0 - 0.18 * k);
    let t = integral_stroke(p) * (1.0 - 0.14 * k);
    let pitch = 2.0 * run * (0.66 - 0.06 * k);
    for i in 0..n {
        let cx = p.mid() + (i as f64 - k / 2.0) * pitch;
        g.stroke(&integral_knots(p, cx, run, t));
    }
}

/// The ring of the contour integrals, around the middle of `n` integrals.
fn contour_ring(g: &mut Draw, n: usize) {
    let p = g.p;
    let r = 98.0 + 0.3 * p.op + 52.0 * (n as f64 - 1.0);
    let rx = r + 18.0 * (n as f64 - 1.0);
    circle(g, p.mid(), p.axis, rx, Some(r), Some(0.92 * fine(p)));
}

fn contour_integral(g: &mut Draw) {
    integral(g);
    contour_ring(g, 1);
}

// ---------------------------------------------------------------------------------------------------------------
// Letter-like signs

/// ∂: a figure, built as 6 is mirrored, whose back leans over to the left and ends in a hook above the bowl.
fn partial(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.cap_stem, p.cap_hair);
    let (x0, x1) = (p.fig_sb - 4.0, p.width - p.fig_sb + 4.0);
    let x = |f: f64| x0 + f * (x1 - x0);
    let y = |f: f64| f * p.cap;
    let sq = p.sq + 0.02;
    let (top, bot) = (p.cap + p.over, -p.over);
    let yb = y(0.60); // the bowl's outer top
    let j = p.join * s;
    let arrive = -48.0;
    let end = pt(x1 - s + 3.0, y(0.40)) + (V::unit(arrive) * (j / 2.0)).left();
    g.stroke(&[
        cut(x(0.07), y(0.76), h * 1.04, 46.0),
        knot(x(0.47), top - h / 2.0, h).dir(0.0).k(sq),
        knot(x1 - s / 2.0, y(0.38), s).dir(-90.0).k(sq),
        knot(x(0.49), bot + h / 2.0, h).dir(180.0).k(sq),
        knot(x0 + s / 2.0, (yb + bot) / 2.0, s).dir(90.0).k(sq),
        knot(x(0.47), yb - h / 2.0, h).dir(0.0),
        Knot::at(end, j).dir(arrive),
    ]);
}

/// ∆ and (`down`) ∇: Δ's outline, its two diagonals and its base all as heavy as the mean of Δ's diagonal and
/// its base.
fn increment(g: &mut Draw, down: bool) {
    let p = g.p;
    let td = p.cap_stem * 0.96; // Δ's diagonals
    let (x0, x1, apex) = (p.sb_round - 34.0, p.width - p.sb_round + 34.0, td * 0.92);
    let t = 0.5 * (td + p.cap_hair);
    let (y_feet, y_point) = if down { (p.cap, 0.0) } else { (0.0, p.cap) };
    g.poly(&vee(x0, x1, y_feet, y_point, t, apex));
    let inset = (p.mid() - apex / 2.0 - x0) * t / p.cap; // where the outer edge is at the bar's inner edge
    let yb = if down { p.cap - t / 2.0 } else { t / 2.0 };
    g.stroke(&hbar(x0 + inset, x1 - inset, yb, t));
}

fn increment_(g: &mut Draw) {
    increment(g, false);
}

fn nabla(g: &mut Draw) {
    increment(g, true);
}

// ---------------------------------------------------------------------------------------------------------------
// Angles and perpendiculars

/// The height of the angle signs.
fn angle_top(p: &Params) -> f64 {
    p.xh + 0.5 * p.over
}

/// ∠: a bar on the baseline and an arm that rises from its left end to the top, both `t` thick; the arm's
/// horizontal cut ends over the bar's right end. Returns the arm's angle.
fn angle_shape(g: &mut Draw, t: f64) -> f64 {
    let p = g.p;
    let (xl, xr, top) = (p.op_l, p.op_r(), angle_top(p));
    // the arm's angle, such that its cut ends on xr: top·cot θ + t/sin θ = xr - xl
    let mut th: f64 = 50f64.to_radians();
    for _ in 0..8 {
        let w = xr - xl - t / th.sin();
        th = (top / w).atan();
    }
    let xo = xl + top / th.tan(); // the outer edge of the arm at the top
    let xb = xl + t / (th / 2.0).tan(); // the inner corner
    g.poly(&[pt(xl, 0.0), pt(xr, 0.0), pt(xr, t), pt(xb, t), pt(xo + t / th.sin(), top), pt(xo, top)]);
    th
}

fn angle(g: &mut Draw) {
    let t = g.p.op;
    angle_shape(g, t);
}

fn right_angle(g: &mut Draw) {
    let p = g.p;
    let t = p.op;
    let xs = p.op_l + t / 2.0;
    g.stroke(&[
        knot(xs, angle_top(p), t).pen(0.0).line(),
        knot(xs, t / 2.0, t).line(),
        knot(p.op_r(), t / 2.0, t).pen(90.0),
    ]);
}

fn perpendicular(g: &mut Draw) {
    let p = g.p;
    bar(g, p.op / 2.0, None, None, None);
    stem(g, p.mid(), 0.0, stand_top(p), None);
}

// ---------------------------------------------------------------------------------------------------------------
// Slashes, stars and dots

fn division_slash(g: &mut Draw) {
    let p = g.p;
    let h = half_span(p);
    slash(g, p.mid() - 0.56 * h, p.axis - h, p.mid() + 0.56 * h, p.axis + h, p.op);
}

fn big_solidus(g: &mut Draw) {
    let p = g.p;
    let d = slash_run(p, false) + 50.0;
    let e = 60.0; // beyond the brackets
    slash(g, p.mid() - d, p.br_bot - e, p.mid() + d, p.br_top + e, 1.06 * p.op);
}

/// The asterisk operator: six arms, smaller and lighter than *, on the axis.
fn asterisk_operator(g: &mut Draw) {
    let p = g.p;
    let r = 0.56 * half_span(p) + 0.3 * p.op;
    let t = 0.5 * (p.op + fine(p)) + 4.0;
    stem(g, p.mid(), p.axis - r, p.axis + r, Some(t));
    let (c, s) = (30f64.to_radians().cos(), 30f64.to_radians().sin());
    let rd = 1.08 * r;
    for sign in [1.0, -1.0] {
        g.stroke(&rake(p.mid() - rd * c, p.axis - sign * rd * s, p.mid() + rd * c, p.axis + sign * rd * s, t));
    }
}

/// The radius of the dots of the ratio signs, and how far their centres are from the axis.
fn ratio_dots(p: &Params) -> (f64, f64) {
    (p.dot, 150.0)
}

fn ratio(g: &mut Draw) {
    let p = g.p;
    let (r, d) = ratio_dots(p);
    g.dot(p.mid(), p.axis + d, r);
    g.dot(p.mid(), p.axis - d, r);
}

fn proportion(g: &mut Draw) {
    let p = g.p;
    let (r, d) = ratio_dots(p);
    for (dx, dy) in [(-d, d), (d, d), (-d, -d), (d, -d)] {
        g.dot(p.mid() + dx, p.axis + dy, r);
    }
}

/// The height of the centre of a dot over a bar centred on `y`.
fn dot_over(p: &Params, y: f64) -> f64 {
    y + p.op / 2.0 + dot_gap(p) + p.dot
}

fn dot_minus(g: &mut Draw) {
    let p = g.p;
    bar(g, p.axis, None, None, None);
    g.dot(p.mid(), dot_over(p, p.axis), p.dot);
}

/// The tilde stood upright: its wave runs up the span's length on the axis.
fn wreath(g: &mut Draw) {
    let p = g.p;
    let w = wave(p, p.mid(), Some(0.9 * wave_rise(p)), None);
    g.stroke(&moved(&transposed(&w), 0.0, p.axis - p.mid()));
}

// ---------------------------------------------------------------------------------------------------------------
// Relations

/// The top of the wave of ≅, above the axis.
fn congruent_top(p: &Params) -> f64 {
    let a = 0.80 * wave_rise(p);
    let pitch = 0.9 * triple_pitch(p);
    let (_, cy) = over(p, a + p.op / 2.0, pitch + p.op);
    cy + a + p.op / 2.0
}

fn not_congruent(g: &mut Draw) {
    let p = g.p;
    g.use_char('≅', 0.0, 0.0);
    struck(g, congruent_top(p) - p.axis, None);
}

fn triple_tilde(g: &mut Draw) {
    let p = g.p;
    let (a, _) = twin_wave(p);
    let t = level_stroke(p);
    for k in [-1.0, 0.0, 1.0] {
        g.stroke(&wave(p, p.axis + k * level_pitch(p), Some(a), Some(t)));
    }
}

fn strictly_equivalent(g: &mut Draw) {
    let p = g.p;
    let t = level_stroke(p);
    for k in [-1.5, -0.5, 0.5, 1.5] {
        bar(g, p.axis + k * level_pitch(p), None, None, Some(t));
    }
}

/// A shallow arc across the span, centred on `y` at its middle; it bows down (a smile) or up.
fn bow(p: &Params, y: f64, sag: f64, smile: bool, t: f64) -> Vec<Knot> {
    let s = if smile { 1.0 } else { -1.0 };
    let a = (2.0 * sag / (0.5 * (p.op_r() - p.op_l))).atan().to_degrees();
    vec![cut(p.op_l, y + s * sag, t, -s * a), knot(p.mid(), y, t).dir(0.0), cut(p.op_r(), y + s * sag, t, s * a)]
}

/// The sag of the arcs of ≍.
fn bow_sag(p: &Params) -> f64 {
    0.82 * wave_rise(p)
}

fn equivalent_to(g: &mut Draw) {
    let p = g.p;
    let d = equal_pitch(p) / 2.0;
    g.stroke(&bow(p, p.axis + d - 0.4 * bow_sag(p), bow_sag(p), true, p.op));
    g.stroke(&bow(p, p.axis - d + 0.4 * bow_sag(p), bow_sag(p), false, p.op));
}

fn approaches_limit(g: &mut Draw) {
    let p = g.p;
    let d = equal_pitch(p) / 2.0;
    g.use_char('=', 0.0, 0.0);
    g.dot(p.mid(), dot_over(p, p.axis + d), p.dot);
}

/// The equals sign lowered for a mark over it (as ≜ has it), and the height the mark may start at.
fn low_equal(g: &mut Draw) -> f64 {
    crate::operators::low_equal(g)
}

fn ring_equal(g: &mut Draw) {
    let p = g.p;
    let y0 = low_equal(g);
    let r = small_ring(p);
    circle(g, p.mid(), y0 + r, r, None, Some(0.5 * (p.op + fine(p))));
}

fn circled_equals(g: &mut Draw) {
    let p = g.p;
    let ri = big_ring(g);
    let d = 0.30 * equal_pitch(p) + 0.1 * p.op;
    let t = fine(p);
    // the bars reach into the ring: its inner edge is a superellipse of exponent about 5/2
    let n = 2.5;
    let x = ri * (1.0 - (d / ri).powf(n)).powf(1.0 / n) + 6.0;
    for s in [1.0, -1.0] {
        g.stroke(&hbar(p.mid() - x, p.mid() + x, p.axis + s * d, t));
    }
}

fn not_less(g: &mut Draw) {
    g.use_char('<', 0.0, 0.0);
    struck(g, chevron_rise(g.p), None);
}

fn not_greater(g: &mut Draw) {
    g.use_char('>', 0.0, 0.0);
    struck(g, chevron_rise(g.p), None);
}

/// The top of the chevron of ≤, above the axis.
fn lessequal_top(p: &Params) -> f64 {
    let rise = rel_rise(p);
    let (_, cy) = over(p, rise, p.op);
    cy + rise
}

fn not_less_equal(g: &mut Draw) {
    let p = g.p;
    g.use_char('≤', 0.0, 0.0);
    struck(g, lessequal_top(p) - p.axis, None);
}

fn not_greater_equal(g: &mut Draw) {
    let p = g.p;
    g.use_char('≥', 0.0, 0.0);
    struck(g, lessequal_top(p) - p.axis, None);
}

/// ⊼ and (`down`) ⊽: the wedge under a bar.
fn barred_wedge(g: &mut Draw, down: bool) {
    let p = g.p;
    let top = stand_top(p);
    bar(g, top - p.op / 2.0, None, None, None);
    let low = top - p.op - rel_gap(p);
    if down {
        wedge(g, low, 0.0);
    } else {
        wedge(g, 0.0, low);
    }
}

fn nand(g: &mut Draw) {
    barred_wedge(g, false);
}

fn nor(g: &mut Draw) {
    barred_wedge(g, true);
}

/// The curly wedge: the strokes leave the point as those of ∨ do and curl outwards, as the precedes sign's
/// do, to end in flat cuts on `y_open`. Its point is on `y_point`.
fn curly_wedge(p: &Params, y_point: f64, y_open: f64) -> Vec<Knot> {
    let t = p.op;
    let s = if y_open > y_point { 1.0 } else { -1.0 };
    let a: f64 = 25.0; // half the angle at the point
    let e: f64 = 34.0; // the direction of the strokes at their ends, from the vertical
    let v = pt(p.mid(), y_point + s * (t / 2.0) / a.to_radians().sin());
    let run = 110.0;
    let up = |deg: f64| V::unit(90.0 * s + deg);
    let xe = 0.5 * t / e.to_radians().cos();
    let left = cut_pen(p.op_l + xe, y_open, t, -90.0 * s + e * s, 0.0);
    let right = cut_pen(p.op_r() - xe, y_open, t, 90.0 * s - e * s, 0.0);
    vec![left, Knot::at(v + run * up(a * s), t).line(), Knot::at(v, t).line(), Knot::at(v + run * up(-a * s), t), right]
}

fn curly_or(g: &mut Draw) {
    let p = g.p;
    g.stroke(&curly_wedge(p, 0.0, stand_top(p)));
}

fn vector_product(g: &mut Draw) {
    let p = g.p;
    cross(g, p.mid(), p.axis, 0.88 * half_span(p), Some(1.12 * p.op));
}

fn amalgamation(g: &mut Draw) {
    let p = g.p;
    let t = p.op;
    let inset = 0.55 * t + t / 2.0;
    let top = stand_top(p);
    g.stroke(&hbar(p.op_l, p.op_r(), t / 2.0, t));
    g.stroke(&vstem(p.op_l + inset, t / 2.0, top, t));
    g.stroke(&vstem(p.op_r() - inset, t / 2.0, top, t));
}

fn double_colon_equal(g: &mut Draw) {
    let p = g.p;
    let r = 0.6 * p.dot;
    let d = equal_pitch(p) / 2.0;
    let x1 = 26.0 + r;
    let x2 = x1 + 2.0 * r + 0.6 * rel_gap(p);
    let x0 = x2 + r + 0.5 * rel_gap(p);
    for s in [1.0, -1.0] {
        g.dot(x1, p.axis + s * d, r);
        g.dot(x2, p.axis + s * d, r);
        bar(g, p.axis + s * d, Some(x0), Some(p.width - 26.0), None);
    }
}

/// ⪯ and (`right`) ⪰: the precedes sign over the bar of ≤.
fn precedes_equal(g: &mut Draw, right: bool) {
    let p = g.p;
    let rise = rel_rise(p) + 12.0;
    let (yb, cy) = over(p, rise, p.op);
    let c = curved_chevron(p, cy, rise, None);
    g.stroke(&if right { mirror(&c, p.mid()) } else { c });
    bar(g, yb, None, None, None);
}

fn precedes_above_equal(g: &mut Draw) {
    precedes_equal(g, false);
}

fn succeeds_above_equal(g: &mut Draw) {
    precedes_equal(g, true);
}

fn vertical_bar_double_left_turnstile(g: &mut Draw) {
    tack(g, 2, 1, true);
}

/// ∊ and (`right`) ∍: the element sign made smaller, as a lowercase is.
fn small_element(g: &mut Draw, right: bool) {
    let p = g.p;
    let rise = 0.74 * set_rise(p);
    let (xl, xr) = (p.op_l + 54.0, p.op_r() - 54.0);
    let a = arc(p, xl, xr, p.axis - rise, p.axis + rise, None);
    let b = hbar(xl + p.op / 2.0, xr, p.axis, 0.92 * p.op);
    for s in [a, b] {
        g.stroke(&if right { mirror(&s, p.mid()) } else { s });
    }
}

fn small_element_of(g: &mut Draw) {
    small_element(g, false);
}

/// A small 4 in the box (x0, y0)-(x1, y1), as `small_three` draws a 3: a diagonal, a bar and a stem.
fn small_four(g: &mut Draw, x0: f64, x1: f64, y0: f64, y1: f64) {
    let p = g.p;
    let t = small_stroke(p);
    let xs = x0 + 0.70 * (x1 - x0); // the stem
    let yb = y0 + 0.30 * (y1 - y0); // the bar
    g.stroke(&vstem(xs, y0, y1, t));
    g.stroke(&hbar(x0, x1, yb, 0.9 * t));
    let w = t * (xs - x0).hypot(y1 - yb) / (y1 - yb);
    g.poly(&[pt(x0, yb - 0.45 * t), pt(x0 + w, yb - 0.45 * t), pt(xs + t / 2.0, y1), pt(xs + t / 2.0 - w, y1)]);
}

fn fourth_root(g: &mut Draw) {
    let p = g.p;
    radical(g);
    small_four(g, 40.0, 40.0 + 160.0, p.axis + 30.0 + 60.0, crate::operators::big_top(p) - 8.0);
}

// ---------------------------------------------------------------------------------------------------------------
// Negated relations: a relation of the system struck through as ≠ is

/// The half-height of the glyph of `c` as this master draws it, about its middle.
fn half_height(g: &Draw, c: char) -> f64 {
    match g.glyph_of_char(c).and_then(|b| b.bounds()) {
        Some((_, y0, _, y1)) => (y1 - y0) / 2.0,
        None => half_span(g.p),
    }
}

/// The glyph of `c`, struck through all of its height.
fn negated(g: &mut Draw, c: char) {
    let rise = half_height(g, c);
    g.use_char(c, 0.0, 0.0);
    struck(g, rise, None);
}

/// The stroke of the short slash that strikes one part of a relation.
fn part_strike(p: &Params) -> f64 {
    0.5 * (p.op + fine(p))
}

/// The short slash through a part `half` high on either side of `y`.
fn strike_part(g: &mut Draw, y: f64, half: f64) {
    let p = g.p;
    let d = half + 0.8 * rel_gap(p);
    strike(g, p.mid(), y, 0.62 * d, d, Some(part_strike(p)));
}

// ---------------------------------------------------------------------------------------------------------------
// Tildes and waves

/// The wave of the tilde reflected left to right: down on the left, up on the right.
fn reversed_wave(p: &Params, y: f64, a: Option<f64>, t: Option<f64>) -> Vec<Knot> {
    mirror(&wave(p, y, a, t), p.mid())
}

fn reversed_tilde(g: &mut Draw) {
    let p = g.p;
    g.stroke(&reversed_wave(p, p.axis, None, None));
}

fn sine_wave(g: &mut Draw) {
    let p = g.p;
    g.stroke(&wave(p, p.axis, Some(1.35 * wave_rise(p)), None));
}

/// ∾: the lazy S lying down, its ends curled under its humps.
fn inverted_lazy_s(g: &mut Draw) {
    let p = g.p;
    let t = p.op;
    let a = loop_height(p);
    let (x0, x1, cy) = (p.op_l, p.op_r(), p.axis);
    let w = x1 - x0;
    g.stroke(&[
        knot(x0 + 0.24 * w, cy - 0.30 * a, 0.8 * t).dir(160.0),
        knot(x0 + t / 2.0, cy + 0.15 * a, t).dir(90.0).k(p.sq),
        knot(x0 + 0.22 * w, cy + a - t / 2.0, t).dir(0.0),
        knot(p.mid(), cy, 0.92 * t).dir(-40.0),
        knot(x1 - 0.22 * w, cy - a + t / 2.0, t).dir(0.0).k(p.sq),
        knot(x1 - t / 2.0, cy - 0.15 * a, t).dir(90.0),
        knot(x1 - 0.24 * w, cy + 0.30 * a, 0.8 * t).dir(160.0),
    ]);
}

/// The outer half-height of ∾.
fn loop_height(p: &Params) -> f64 {
    96.0 + 0.4 * p.op
}

/// A wave over one bar, the pair centred on the axis; `reversed` waves the other way, `low` puts the bar
/// above.
fn wave_bar(g: &mut Draw, reversed: bool, low: bool) {
    let p = g.p;
    let a = 0.85 * wave_rise(p);
    let (mut yb, mut cy) = over(p, a + p.op / 2.0, p.op);
    if low {
        (yb, cy) = (2.0 * p.axis - yb, 2.0 * p.axis - cy);
    }
    g.stroke(&if reversed { reversed_wave(p, cy, Some(a), None) } else { wave(p, cy, Some(a), None) });
    bar(g, yb, None, None, None);
}

fn minus_tilde(g: &mut Draw) {
    wave_bar(g, false, true);
}

fn reversed_tilde_equals(g: &mut Draw) {
    wave_bar(g, true, false);
}

fn all_equal(g: &mut Draw) {
    let p = g.p;
    let a = 0.80 * wave_rise(p);
    let pitch = 0.9 * triple_pitch(p);
    let (yb, cy) = over(p, a + p.op / 2.0, pitch + p.op);
    g.stroke(&reversed_wave(p, cy, Some(a), None));
    bar(g, yb + pitch / 2.0, None, None, None);
    bar(g, yb - pitch / 2.0, None, None, None);
}

/// ≆: ≅ with its bars struck.
fn approx_not_equal(g: &mut Draw) {
    let p = g.p;
    let a = 0.80 * wave_rise(p);
    let pitch = 0.9 * triple_pitch(p);
    let (yb, _) = over(p, a + p.op / 2.0, pitch + p.op);
    g.use_char('≅', 0.0, 0.0);
    strike_part(g, yb, pitch / 2.0 + p.op / 2.0);
}

/// ≊: the two waves of ≈ over a bar, in the rhythm of three levels.
fn almost_equal_or_equal(g: &mut Draw) {
    let p = g.p;
    let (a, _) = twin_wave(p);
    let t = level_stroke(p);
    let u = level_pitch(p);
    g.stroke(&wave(p, p.axis + u, Some(a), Some(t)));
    g.stroke(&wave(p, p.axis, Some(a), Some(t)));
    bar(g, p.axis - u, None, None, Some(t));
}

/// ∻: the tilde between a dot above and a dot below.
fn homothetic(g: &mut Draw) {
    let p = g.p;
    let a = wave_rise(p);
    let d = a + p.op / 2.0 + dot_gap(p) + p.dot;
    g.stroke(&wave(p, p.axis, None, None));
    g.dot(p.mid(), p.axis + d, p.dot);
    g.dot(p.mid(), p.axis - d, p.dot);
}

// ---------------------------------------------------------------------------------------------------------------
// Equals with marks

/// A bar across the span with a half ring on its middle, rising (or, `down`, falling) from it.
fn bumped_bar(g: &mut Draw, y: f64, down: bool) {
    let p = g.p;
    let t = p.op;
    let rb = 0.34 * half_span(p) + 0.3 * t; // the bump's centre line
    let s = if down { -1.0 } else { 1.0 };
    let y0 = y - s * t / 2.0; // the arc starts at the far edge of the bar, so that it closes the bar's ends
    bar(g, y, None, Some(p.mid() - rb), None);
    bar(g, y, Some(p.mid() + rb), None, None);
    g.stroke(&[
        knot(p.mid() - rb, y0, t).pen(0.0).dir(90.0 * s).line(),
        knot(p.mid() - rb, y, t).pen(0.0).dir(90.0 * s).k(p.sq),
        knot(p.mid(), y + s * rb, t).dir(0.0).k(p.sq),
        knot(p.mid() + rb, y, t).pen(0.0).dir(-90.0 * s).line(),
        knot(p.mid() + rb, y0, t).pen(0.0),
    ]);
}

fn geometrically_equivalent(g: &mut Draw) {
    let p = g.p;
    let d = 0.5 * equal_pitch(p);
    bumped_bar(g, p.axis + d, false);
    bumped_bar(g, p.axis - d, true);
}

fn difference_between(g: &mut Draw) {
    let p = g.p;
    let d = 0.5 * equal_pitch(p);
    let y = p.axis - 0.25 * (0.30 * half_span(p));
    bumped_bar(g, y + d, false);
    bar(g, y - d, None, None, None);
}

fn geometrically_equal(g: &mut Draw) {
    let p = g.p;
    let d = equal_pitch(p) / 2.0;
    g.use_char('=', 0.0, 0.0);
    let y = dot_over(p, p.axis + d);
    g.dot(p.mid(), y, p.dot);
    g.dot(p.mid(), 2.0 * p.axis - y, p.dot);
}

/// ≒ and (`right`) ≓: = with a dot over its left end and one under its right end, or the other way.
fn image_of(g: &mut Draw, right: bool) {
    let p = g.p;
    let d = equal_pitch(p) / 2.0;
    g.use_char('=', 0.0, 0.0);
    let y = dot_over(p, p.axis + d);
    let x = p.op_l + p.dot + 6.0;
    let (xa, xb) = if right { (p.width - x, x) } else { (x, p.width - x) };
    g.dot(xa, y, p.dot);
    g.dot(xb, 2.0 * p.axis - y, p.dot);
}

fn image_of_left(g: &mut Draw) {
    image_of(g, false);
}

fn image_of_right(g: &mut Draw) {
    image_of(g, true);
}

/// ≖: a ring between the bars of =, which stop at it.
fn ring_in_equal(g: &mut Draw) {
    let p = g.p;
    let d = equal_pitch(p) / 2.0;
    let r = d + p.op / 2.0;
    circle(g, p.mid(), p.axis, r, None, Some(fine(p)));
    for s in [1.0, -1.0] {
        bar(g, p.axis + s * d, None, Some(p.mid() - 0.62 * r), None);
        bar(g, p.axis + s * d, Some(p.mid() + 0.62 * r), None, None);
    }
}

/// The box a mark over the lowered equals sign is drawn in: left, right, bottom, top.
fn mark_box(g: &mut Draw, half: f64) -> (f64, f64, f64, f64) {
    let p = g.p;
    let y0 = low_equal(g);
    (p.mid() - half, p.mid() + half, y0, p.cap + 10.0)
}

fn corresponds_to(g: &mut Draw) {
    let p = g.p;
    let (x0, x1, y0, _) = mark_box(g, 150.0);
    let t = small_stroke(p) * 1.15;
    let a = transposed(&arc(p, y0 + 190.0, y0, x0, x1, Some(t)));
    g.stroke(&a);
}

fn estimates(g: &mut Draw) {
    let p = g.p;
    let (x0, x1, y0, y1) = mark_box(g, 150.0);
    let t = small_stroke(p) * 1.15;
    g.poly(&vee(x0, x1, y0, y1 - 40.0, t, 0.5 * t));
}

fn equiangular(g: &mut Draw) {
    let p = g.p;
    let (x0, x1, y0, y1) = mark_box(g, 150.0);
    let t = small_stroke(p) * 1.15;
    g.poly(&vee(x0, x1, y1 - 40.0, y0, t, 0.5 * t));
}

fn star_equals(g: &mut Draw) {
    let p = g.p;
    let (_, _, y0, y1) = mark_box(g, 150.0);
    let ro = 0.5 * (y1 - y0) + 10.0;
    let ri = 0.44 * ro;
    let c = pt(p.mid(), y0 + 0.92 * ro);
    let points: Vec<V> =
        (0..10).map(|i| c + (if i % 2 == 0 { ro } else { ri }) * V::unit(90.0 + 36.0 * i as f64)).collect();
    g.poly(&points);
}

/// ≞: a small m over the lowered equals sign.
fn measured_by(g: &mut Draw) {
    let p = g.p;
    let (x0, x1, y0, _) = mark_box(g, 160.0);
    let t = small_stroke(p);
    let top = y0 + 0.62 * (x1 - x0);
    let xm = (x0 + x1) / 2.0;
    let (xl, xr) = (x0 + t / 2.0, x1 - t / 2.0);
    let o = Arch { stem: Some(t), hair: Some(t), branch: Some(top - 0.35 * (top - y0)), ..Arch::default() };
    g.stroke(&vstem(xl, y0, top, t));
    g.stroke(&arch(p, xl, xm, top, y0, o));
    g.stroke(&arch(p, xm, xr, top, y0, o));
}

/// ≬: two arcs that bow towards each other and cross, as ) and ( would.
fn between(g: &mut Draw) {
    let p = g.p;
    let t = 0.5 * (p.op + fine(p));
    let h = 1.15 * half_span(p);
    let (xe, xm) = (0.40 * half_span(p), 0.30 * half_span(p)); // the ends and the middle, from the centre
    for s in [1.0, -1.0] {
        let k = vec![
            cut_pen(p.mid() - s * xe, p.axis + h, t, -90.0 + s * 28.0, 0.0),
            knot(p.mid() + s * xm, p.axis, t).dir(-90.0),
            cut_pen(p.mid() - s * xe, p.axis - h, t, -90.0 - s * 28.0, 0.0),
        ];
        g.stroke(&k);
    }
}

/// ⋕: = crossed by two upright strokes, as ∥ is drawn.
fn equal_and_parallel(g: &mut Draw) {
    let p = g.p;
    let h = half_span(p);
    let d = 0.5 * twin_pitch(p, p.op);
    g.use_char('=', 0.0, 0.0);
    stem(g, p.mid() - d, p.axis - h, p.axis + h, None);
    stem(g, p.mid() + d, p.axis - h, p.axis + h, None);
}

// ---------------------------------------------------------------------------------------------------------------
// Order

/// The layout of a relation of three levels: a shape over two bars, all `level_stroke` thick. Returns the
/// centre of the shape, its rise, and the centres of the two bars.
fn three_levels(p: &Params) -> (f64, f64, f64, f64) {
    let t = level_stroke(p);
    let rise = 0.72 * rel_rise(p);
    let pitch = 0.8 * level_pitch(p);
    let gap = 0.9 * rel_gap(p);
    let total = 2.0 * rise + gap + pitch + t;
    let bottom = p.axis - total / 2.0;
    let lo = bottom + t / 2.0;
    (bottom + total - rise, rise, lo + pitch, lo)
}

/// ≦ and (`right`) ≧: the chevron over two bars.
fn less_double_equal(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = level_stroke(p);
    let (cy, rise, hi, lo) = three_levels(p);
    let c = chevron(p.op_l, p.op_r(), cy, rise, t, tip(p));
    g.poly(&if right { mirrored(&c, p.mid()) } else { c });
    bar(g, hi, None, None, Some(t));
    bar(g, lo, None, None, Some(t));
}

fn less_over_equal(g: &mut Draw) {
    less_double_equal(g, false);
}

fn greater_over_equal(g: &mut Draw) {
    less_double_equal(g, true);
}

fn less_not_equal(g: &mut Draw, right: bool) {
    let p = g.p;
    less_double_equal(g, right);
    let (_, _, hi, lo) = three_levels(p);
    strike_part(g, (hi + lo) / 2.0, (hi - lo) / 2.0 + level_stroke(p) / 2.0);
}

fn less_but_not_equal(g: &mut Draw) {
    less_not_equal(g, false);
}

fn greater_but_not_equal(g: &mut Draw) {
    less_not_equal(g, true);
}

/// ≶ and (`swap`) ≷: two chevrons pointing opposite ways, interleaved: the lower arm of the upper one and
/// the upper arm of the lower one are parallel, a bar's width and a gap apart.
fn less_greater(g: &mut Draw, swap: bool) {
    let p = g.p;
    let t = p.op;
    let rise = 0.8 * rel_rise(p);
    let span = p.op_r() - p.op_l;
    let sec = (rise / span).atan().cos().recip();
    let sep = rise + (t + 0.8 * rel_gap(p)) * sec; // between the two centres
    let up = chevron(p.op_l, p.op_r(), p.axis + sep / 2.0, rise, t, tip(p));
    let down = mirrored(&chevron(p.op_l, p.op_r(), p.axis - sep / 2.0, rise, t, tip(p)), p.mid());
    if swap {
        g.poly(&flip_points(&up, p.axis));
        g.poly(&flip_points(&down, p.axis));
    } else {
        g.poly(&up);
        g.poly(&down);
    }
}

/// A polygon reflected top to bottom in the line y = cy.
fn flip_points(points: &[V], cy: f64) -> Vec<V> {
    points.iter().map(|z| pt(z.x, 2.0 * cy - z.y)).collect()
}

fn less_or_greater(g: &mut Draw) {
    less_greater(g, false);
}

fn greater_or_less(g: &mut Draw) {
    less_greater(g, true);
}

/// ⋚ and (`swap`) ⋛: < over a bar over >, flattened to stay within the x-height and a little.
fn less_equal_greater(g: &mut Draw, swap: bool) {
    let p = g.p;
    let t = level_stroke(p);
    let rise = 0.64 * rel_rise(p);
    let gap = 0.65 * rel_gap(p);
    let d = t / 2.0 + gap + rise;
    let up = chevron(p.op_l, p.op_r(), p.axis + d, rise, t, tip(p));
    let down = mirrored(&chevron(p.op_l, p.op_r(), p.axis - d, rise, t, tip(p)), p.mid());
    let (a, b) = if swap { (mirrored(&up, p.mid()), mirrored(&down, p.mid())) } else { (up, down) };
    g.poly(&a);
    g.poly(&b);
    bar(g, p.axis, None, None, Some(t));
}

fn less_equal_or_greater(g: &mut Draw) {
    less_equal_greater(g, false);
}

fn greater_equal_or_less(g: &mut Draw) {
    less_equal_greater(g, true);
}

/// ⋜ and (`right`) ⋝: the bar over the chevron.
fn equal_or_less(g: &mut Draw, right: bool) {
    let p = g.p;
    let rise = rel_rise(p);
    let (yb, cy) = over(p, rise, p.op);
    let (yb, cy) = (2.0 * p.axis - yb, 2.0 * p.axis - cy);
    let c = chevron(p.op_l, p.op_r(), cy, rise, p.op, tip(p));
    g.poly(&if right { mirrored(&c, p.mid()) } else { c });
    bar(g, yb, None, None, None);
}

fn equal_or_less_(g: &mut Draw) {
    equal_or_less(g, false);
}

fn equal_or_greater(g: &mut Draw) {
    equal_or_less(g, true);
}

/// The stroke that follows the lower arm of the precedes sign (centred on `cy`, `rise`) at a distance:
/// the curved bar of ≼.
fn curved_bar(p: &Params, cy: f64, rise: f64) -> Vec<Knot> {
    let t = p.op;
    let a: f64 = 17.0;
    let b: f64 = 50.0;
    let run = 60.0;
    let v = pt(p.op_l + (t / 2.0) / a.to_radians().sin(), cy);
    let d = (t + rel_gap(p)) / a.to_radians().cos(); // below the arm, where the arm is straight
    let e = 0.8 * d; // below its end
    let end_x = p.op_r() - 0.5 * t / b.to_radians().sin() - 0.45 * d;
    vec![
        cut(p.op_l + 6.0, cy - d, t, -a).line(),
        Knot::at(v + run * V::unit(-a) - pt(0.0, d), t),
        cut_pen(end_x, cy - rise - e, t, -b, 0.0),
    ]
}

/// The drop of the curved bar's end below the end of the arm.
fn curved_bar_drop(p: &Params) -> f64 {
    0.8 * (p.op + rel_gap(p)) / 17f64.to_radians().cos()
}

/// ≼ and (`right`) ≽: the precedes sign over a bar curved as its lower arm is.
fn precedes_curved_equal(g: &mut Draw, right: bool, low: bool) {
    let p = g.p;
    let e = curved_bar_drop(p);
    let rise = rel_rise(p) + 0.5 * (rel_gap(p) + p.op - e);
    let cy = p.axis + e / 2.0;
    let mut c = curved_chevron(p, cy, rise, None);
    let mut b = curved_bar(p, cy, rise);
    if low {
        c = flip(&c, p.axis);
        b = flip(&b, p.axis);
    }
    for s in [c, b] {
        g.stroke(&if right { mirror(&s, p.mid()) } else { s });
    }
}

fn precedes_or_equal(g: &mut Draw) {
    precedes_curved_equal(g, false, false);
}

fn succeeds_or_equal(g: &mut Draw) {
    precedes_curved_equal(g, true, false);
}

fn equal_or_precedes(g: &mut Draw) {
    precedes_curved_equal(g, false, true);
}

fn equal_or_succeeds(g: &mut Draw) {
    precedes_curved_equal(g, true, true);
}

/// The layout of a sign over a tilde, as ≲ has it: the centre of the wave and of the sign, its rise, and the
/// wave's rise.
fn over_tilde(p: &Params) -> (f64, f64, f64, f64) {
    let rise = rel_rise(p);
    let a = 0.62 * wave_rise(p);
    let (yw, cy) = over(p, rise, 2.0 * a + p.op);
    (yw, cy, rise, a)
}

/// ≾ and (`right`) ≿: the precedes sign over the tilde.
fn precedes_similar(g: &mut Draw, right: bool) {
    let p = g.p;
    let (yw, cy, rise, a) = over_tilde(p);
    let c = curved_chevron(p, cy, rise, None);
    g.stroke(&if right { mirror(&c, p.mid()) } else { c });
    g.stroke(&wave(p, yw, Some(a), None));
}

fn precedes_or_equivalent(g: &mut Draw) {
    precedes_similar(g, false);
}

fn succeeds_or_equivalent(g: &mut Draw) {
    precedes_similar(g, true);
}

/// A sign over a tilde, with the tilde struck: ≲ ≳ ≾ ≿ but not equivalent.
fn not_equivalent_below(g: &mut Draw, c: char) {
    let p = g.p;
    let (yw, _, _, a) = over_tilde(p);
    g.use_char(c, 0.0, 0.0);
    strike_part(g, yw, a + p.op / 2.0);
}

/// ⋤ and (`right`) ⋥: ⊑ with its bar struck.
fn square_image_not_equal(g: &mut Draw, c: char) {
    let p = g.p;
    let (yb, _) = over(p, rel_rise(p), p.op);
    g.use_char(c, 0.0, 0.0);
    strike_part(g, yb, p.op / 2.0);
}

/// Where a dot of radius `r` sits in the mouth of a chevron that points left and opens on `p.op_r`: near the
/// open end, where the mouth is widest, so that the Bold keeps white around it.
fn mouth_dot_x(p: &Params, r: f64) -> f64 {
    p.op_r() - 1.5 * r
}

/// ⋖ and (`right`) ⋗: the chevron with a dot in its mouth.
fn less_dot(g: &mut Draw, right: bool) {
    let p = g.p;
    g.use_char(if right { '>' } else { '<' }, 0.0, 0.0);
    let r = 0.6 * p.dot;
    let x = mouth_dot_x(p, r);
    g.dot(if right { p.width - x } else { x }, p.axis, r);
}

fn less_with_dot(g: &mut Draw) {
    less_dot(g, false);
}

fn greater_with_dot(g: &mut Draw) {
    less_dot(g, true);
}

/// ⋘ and (`right`) ⋙: three chevrons, as ≪ draws two.
fn very_much(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = 0.96 * fine(p);
    let span = p.op_r() - p.op_l;
    let w = 0.46 * span;
    for k in 0..3 {
        let x = p.op_l + k as f64 * (span - w) / 2.0;
        let c = chevron(x, x + w, p.axis, chevron_rise(p), t, 0.8 * tip(p));
        g.poly(&if right { mirrored(&c, p.mid()) } else { c });
    }
}

fn very_much_less(g: &mut Draw) {
    very_much(g, false);
}

fn very_much_greater(g: &mut Draw) {
    very_much(g, true);
}

/// ⊰ and (`right`) ⊱: the precedes sign whose lower arm curls under into a hook.
fn precedes_under(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = p.op;
    let rise = chevron_rise(p);
    let cy = p.axis + 0.22 * rise;
    let a: f64 = 17.0;
    let v = pt(p.op_l + (t / 2.0) / a.to_radians().sin(), cy);
    let top = cut_pen(p.op_r() - 0.5 * t / 62f64.to_radians().sin(), cy + 0.8 * rise, t, 180.0 + 62.0, 0.0);
    let span = p.op_r() - p.op_l;
    let low = cy - 1.25 * rise; // the bottom of the curl
    let k = vec![
        top,
        Knot::at(v + 60.0 * V::unit(a), t).line(),
        Knot::at(v, t).line(),
        Knot::at(v + 60.0 * V::unit(-a), t),
        knot(p.op_l + 0.72 * span, cy - 0.62 * rise, t).dir(-62.0),
        knot(p.op_l + 0.60 * span, low + t / 2.0, t).dir(180.0),
        knot(p.op_l + 0.36 * span, low + 0.28 * rise, 0.8 * t).dir(110.0),
    ];
    g.stroke(&if right { mirror(&k, p.mid()) } else { k });
}

fn precedes_under_relation(g: &mut Draw) {
    precedes_under(g, false);
}

fn succeeds_under_relation(g: &mut Draw) {
    precedes_under(g, true);
}

/// ⩿: the chevron over a bar slanted as its lower arm, with a dot in its mouth.
fn less_slanted_equal_dot(g: &mut Draw) {
    let p = g.p;
    let t = p.op;
    let rise = rel_rise(p);
    let span = p.op_r() - p.op_l;
    let slope = (rise - tip(p) / 2.0) / span;
    let d = (t + rel_gap(p)) * slope.hypot(1.0); // the bar's centre line below the arm's
    let wv = t * slope.hypot(1.0); // the height of the bar's vertical cut
    // centre the whole: the arm's top at cy + rise, the bar's right end at cy - rise - d + t/2 - wv/2
    let cy = p.axis + 0.5 * (d + wv / 2.0 - t / 2.0);
    g.poly(&chevron(p.op_l, p.op_r(), cy, rise, t, tip(p)));
    let y0 = cy - d + t / 2.0 - wv / 2.0 + tip(p) / 2.0 - t / 2.0;
    g.stroke(&rake(p.op_l, y0 + 0.0, p.op_r(), y0 - slope * span, t));
    let r = 0.45 * p.dot;
    g.dot(mouth_dot_x(p, r), cy, r);
}

// ---------------------------------------------------------------------------------------------------------------
// Turnstiles and tacks

/// A turnstile of `stems` uprights `t` thick and `bars` bars, the uprights `pitch` apart.
fn turnstile(g: &mut Draw, bars: usize, stems: usize, t: f64, pitch: f64, right: bool) {
    let p = g.p;
    let h = tack_rise(p);
    let mut strokes: Vec<Vec<Knot>> =
        (0..stems).map(|i| vstem(p.op_l + t / 2.0 + i as f64 * pitch, p.axis - h, p.axis + h, t)).collect();
    let x0 = p.op_l + t / 2.0 + (stems as f64 - 1.0) * pitch;
    let d = equal_pitch(p) / 2.0;
    let ys = if bars == 1 { vec![p.axis] } else { vec![p.axis + d, p.axis - d] };
    for y in ys {
        strokes.push(hbar(x0, p.op_r(), y, p.op));
    }
    for s in &strokes {
        g.stroke(&if right { mirror(s, p.mid()) } else { s.clone() });
    }
}

fn triple_bar_turnstile(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    turnstile(g, 1, 3, t, 0.80 * twin_pitch(p, t), false);
}

fn double_bar_double_turnstile(g: &mut Draw) {
    tack(g, 2, 2, false);
}

/// ⊦ and (`bars` 2) ⊧: the short turnstile, half as tall and long.
fn short_tack(g: &mut Draw, bars: usize) {
    let p = g.p;
    let h = 0.62 * half_span(p);
    let x = p.op_l + 60.0 + p.op / 2.0;
    stem(g, x, p.axis - h, p.axis + h, None);
    let d = 0.42 * equal_pitch(p);
    let ys = if bars == 1 { vec![p.axis] } else { vec![p.axis + d, p.axis - d] };
    for y in ys {
        bar(g, y, Some(x), Some(p.op_r() - 60.0), None);
    }
}

fn assertion(g: &mut Draw) {
    short_tack(g, 1);
}

fn models_short(g: &mut Draw) {
    short_tack(g, 2);
}

fn not_turnstile(g: &mut Draw, c: char) {
    negated(g, c);
}

/// ⫪ and (`up`) ⫫: the tack with two stems.
fn double_tack(g: &mut Draw, up: bool) {
    let p = g.p;
    let d = 0.5 * twin_pitch(p, p.op);
    let y = if up { p.op / 2.0 } else { p.cap - p.op / 2.0 };
    bar(g, y, None, None, None);
    stem(g, p.mid() - d, 0.0, p.cap, None);
    stem(g, p.mid() + d, 0.0, p.cap, None);
}

fn double_down_tack(g: &mut Draw) {
    double_tack(g, false);
}

fn double_up_tack(g: &mut Draw) {
    double_tack(g, true);
}

/// ⟘ and (`down`) ⟙: the tack as large as an n-ary operator.
fn large_tack(g: &mut Draw, down: bool) {
    let p = g.p;
    let t = nary_stroke(p);
    let (xl, xr, bot, top) = nary_box(p);
    let y = if down { top - t / 2.0 } else { bot + t / 2.0 };
    bar(g, y, Some(xl), Some(xr), Some(t));
    stem(g, p.mid(), bot, top, Some(t));
}

fn large_up_tack(g: &mut Draw) {
    large_tack(g, false);
}

fn large_down_tack(g: &mut Draw) {
    large_tack(g, true);
}

/// ⟚ and (`bars` 1) ⟛: two uprights in the middle, and bars from each out to the span's ends.
fn two_way_turnstile(g: &mut Draw, bars: usize) {
    let p = g.p;
    let h = tack_rise(p);
    let d = 0.5 * twin_pitch(p, p.op) * 0.88;
    stem(g, p.mid() - d, p.axis - h, p.axis + h, None);
    stem(g, p.mid() + d, p.axis - h, p.axis + h, None);
    let e = equal_pitch(p) / 2.0;
    let ys = if bars == 1 { vec![p.axis] } else { vec![p.axis + e, p.axis - e] };
    for y in ys {
        bar(g, y, None, Some(p.mid() - d), None);
        bar(g, y, Some(p.mid() + d), None, None);
    }
}

fn left_right_double_turnstile(g: &mut Draw) {
    two_way_turnstile(g, 2);
}

fn left_right_tack(g: &mut Draw) {
    two_way_turnstile(g, 1);
}

/// ⟝ and (`left`) ⟞: the turnstile drawn out to the cell's ends.
fn long_tack(g: &mut Draw, left: bool) {
    let p = g.p;
    let h = 0.86 * tack_rise(p);
    let x0 = 26.0 + p.op / 2.0;
    let k = [vstem(x0, p.axis - h, p.axis + h, p.op), hbar(x0, p.width - 26.0, p.axis, p.op)];
    for s in k {
        g.stroke(&if left { mirror(&s, p.mid()) } else { s });
    }
}

fn long_right_tack(g: &mut Draw) {
    long_tack(g, false);
}

fn long_left_tack(g: &mut Draw) {
    long_tack(g, true);
}

fn up_tack_circle(g: &mut Draw) {
    let p = g.p;
    let r = small_ring(p);
    let top = stand_top(p) - 2.0 * r + 0.5 * p.op;
    bar(g, p.op / 2.0, None, None, None);
    stem(g, p.mid(), 0.0, top, None);
    circle(g, p.mid(), top + r - 0.5 * p.op, r, None, Some(0.5 * (p.op + fine(p))));
}

/// ⊺: a small down tack that reaches below the baseline.
fn intercalate(g: &mut Draw) {
    let p = g.p;
    let h = 0.62 * half_span(p);
    let top = p.xh;
    bar(g, top - p.op / 2.0, Some(p.mid() - h), Some(p.mid() + h), None);
    stem(g, p.mid(), 0.45 * p.desc, top, None);
}

/// ⊸ and (`left`) ⟜: a bar ending in a ring.
fn ring_bar(g: &mut Draw, left: bool) {
    let p = g.p;
    let r = small_ring(p) + 6.0;
    let xr = p.width - (p.op_l + r - 30.0);
    let k = hbar(30.0, xr - r + 4.0, p.axis, p.op);
    g.stroke(&if left { mirror(&k, p.mid()) } else { k });
    circle(g, if left { p.width - xr } else { xr }, p.axis, r, None, Some(0.5 * (p.op + fine(p))));
}

fn original_of(g: &mut Draw) {
    let p = g.p;
    let r = small_ring(p) + 6.0;
    let xl = p.op_l + r - 30.0;
    let xr = p.width - xl;
    circle(g, xl, p.axis, r, None, Some(0.5 * (p.op + fine(p))));
    g.dot(xr, p.axis, r);
    bar(g, p.axis, Some(xl + r - 4.0), Some(xr), Some(fine(p)));
}

fn image_of_(g: &mut Draw) {
    let p = g.p;
    let r = small_ring(p) + 6.0;
    let xl = p.op_l + r - 30.0;
    let xr = p.width - xl;
    g.dot(xl, p.axis, r);
    circle(g, xr, p.axis, r, None, Some(0.5 * (p.op + fine(p))));
    bar(g, p.axis, Some(xl), Some(xr - r + 4.0), Some(fine(p)));
}

fn multimap(g: &mut Draw) {
    ring_bar(g, false);
}

fn left_multimap(g: &mut Draw) {
    ring_bar(g, true);
}

// ---------------------------------------------------------------------------------------------------------------
// Sets and elements

/// ∁: the complement, a C of the operators' stroke at cap height.
fn complement(g: &mut Draw) {
    let p = g.p;
    let t = p.op;
    let (xs, xo) = (p.op_l + 34.0, p.op_r() - 20.0);
    let (y0, y1) = (-p.over, p.cap + p.over);
    let xa = xs + 0.58 * (xo - xs);
    g.stroke(&[
        knot(xo, y1 - t / 2.0, t).pen(90.0).line(),
        knot(xa, y1 - t / 2.0, t).pen(90.0).dir(180.0).k(p.sq),
        knot(xs + t / 2.0, (y0 + y1) / 2.0, t).dir(-90.0).k(p.sq),
        knot(xa, y0 + t / 2.0, t).pen(90.0).dir(0.0).line(),
        knot(xo, y0 + t / 2.0, t).pen(90.0),
    ]);
}

fn small_contains(g: &mut Draw) {
    small_element(g, true);
}

/// The element sign with something added: drawn with its arc and bar, mirrored for the contains forms.
fn element_parts(g: &mut Draw, right: bool, xl: f64, bar_from: f64, rise: f64) {
    let p = g.p;
    let a = arc(p, xl, p.op_r(), p.axis - rise, p.axis + rise, None);
    let b = hbar(bar_from, p.op_r(), p.axis, 0.92 * p.op);
    for s in [a, b] {
        g.stroke(&if right { mirror(&s, p.mid()) } else { s });
    }
}

/// ⋲ and (`right`) ⋺: the bar drawn out beyond the arc.
fn element_long_bar(g: &mut Draw, right: bool) {
    let p = g.p;
    element_parts(g, right, p.op_l + 60.0, 26.0, set_rise(p));
}

/// ⋳ ⋴ and their contains forms: a short upright at the inner end of the bar.
fn element_end_bar(g: &mut Draw, right: bool, small: bool) {
    let p = g.p;
    let f = if small { 0.74 } else { 1.0 };
    let rise = f * set_rise(p);
    let xl = if small { p.op_l + 54.0 } else { p.op_l };
    let xr = if small { p.op_r() - 54.0 } else { p.op_r() };
    let t = 0.92 * p.op;
    let a = arc(p, xl, xr, p.axis - rise, p.axis + rise, None);
    let b = hbar(xl + p.op / 2.0, xr - 0.5 * t, p.axis, t);
    let h = 0.5 * rise;
    let s = vstem(xr - 0.5 * t, p.axis - h, p.axis + h, t);
    for k in [a, b, s] {
        g.stroke(&if right { mirror(&k, p.mid()) } else { k });
    }
}

/// ⋵ ⋶ ⋷ ⋸ and their contains forms: the element sign lowered or raised, with a dot or a bar over or under.
fn element_mark(g: &mut Draw, right: bool, small: bool, mark: char) {
    let p = g.p;
    let f = if small { 0.74 } else { 0.86 };
    let rise = f * set_rise(p);
    let (xl, xr) = if small { (p.op_l + 54.0, p.op_r() - 54.0) } else { (p.op_l, p.op_r()) };
    let markh = if mark == '.' { 2.0 * p.dot } else { p.op };
    let gap = 0.8 * rel_gap(p);
    let total = 2.0 * rise + gap + markh;
    let below = mark == '_';
    let cy = if below { p.axis + total / 2.0 - rise } else { p.axis - total / 2.0 + rise };
    let ym = if below { cy - rise - gap - markh / 2.0 } else { cy + rise + gap + markh / 2.0 };
    let a = arc(p, xl, xr, cy - rise, cy + rise, None);
    let b = hbar(xl + p.op / 2.0, xr, cy, 0.92 * p.op);
    for k in [a, b] {
        g.stroke(&if right { mirror(&k, p.mid()) } else { k });
    }
    if mark == '.' {
        g.dot(p.mid(), ym, p.dot);
    } else {
        bar(g, ym, Some(xl), Some(xr), None);
    }
}

/// ⋹: the element sign with two bars in its mouth.
fn element_two_bars(g: &mut Draw) {
    let p = g.p;
    let rise = set_rise(p);
    subset(g, p.axis, rise, false, None);
    let d = 0.30 * equal_pitch(p) + 0.1 * p.op;
    for s in [1.0, -1.0] {
        bar(g, p.axis + s * d, Some(p.op_l + p.op / 2.0), None, Some(fine(p)));
    }
}

/// ⋿: the element sign squared.
fn bag_membership(g: &mut Draw) {
    let p = g.p;
    square_image(g, p.axis, set_rise(p), false);
    bar(g, p.axis, Some(p.op_l + p.op / 2.0), None, Some(0.92 * p.op));
}

/// ⟒ and (`down`) ⫙: the element sign turned to open upwards (or downwards).
fn element_turned(g: &mut Draw, down: bool) {
    let p = g.p;
    let r = set_rise(p);
    let (y0, y1) = (p.axis - half_span(p) - 20.0, p.axis + half_span(p) + 20.0);
    let a = transposed(&arc(p, y0 - p.over, y1, p.mid() - r, p.mid() + r, None));
    let s = vstem(p.mid(), y0 + p.op / 2.0, y1, 0.92 * p.op);
    for k in [a, s] {
        g.stroke(&if down { flip(&k, p.axis) } else { k });
    }
}

fn element_opening_up(g: &mut Draw) {
    element_turned(g, false);
}

fn element_opening_down(g: &mut Draw) {
    element_turned(g, true);
}

/// ⋐ and (`right`) ⋑: two subset arcs, one inside the other.
fn double_subset(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = fine(p);
    let rise = set_rise(p);
    let pitch = t + 0.9 * rel_gap(p) + 10.0;
    let outer = arc(p, p.op_l, p.op_r(), p.axis - rise, p.axis + rise, Some(t));
    let inner = arc(p, p.op_l + pitch, p.op_r(), p.axis - rise + pitch, p.axis + rise - pitch, Some(t));
    for k in [outer, inner] {
        g.stroke(&if right { mirror(&k, p.mid()) } else { k });
    }
}

fn double_subset_(g: &mut Draw) {
    double_subset(g, false);
}

fn double_superset(g: &mut Draw) {
    double_subset(g, true);
}

/// ⋓ and (`down`) ⋒: two cups, one inside the other.
fn double_cup(g: &mut Draw, down: bool) {
    let p = g.p;
    let t = fine(p);
    let pitch = t + 0.9 * rel_gap(p) + 10.0;
    let top = stand_top(p);
    let outer = transposed(&arc(p, -p.over, top, p.op_l, p.op_r(), Some(t)));
    let inner = transposed(&arc(p, pitch - p.over, top, p.op_l + pitch, p.op_r() - pitch, Some(t)));
    for k in [outer, inner] {
        g.stroke(&if down { flip(&k, p.axis) } else { k });
    }
}

fn double_union(g: &mut Draw) {
    double_cup(g, false);
}

fn double_intersection(g: &mut Draw) {
    double_cup(g, true);
}

fn pitchfork(g: &mut Draw) {
    let p = g.p;
    g.use_char('∩', 0.0, 0.0);
    stem(g, p.mid(), 0.0, stand_top(p) + 0.12 * stand_top(p), Some(fine(p) + 6.0));
}

fn multiset(g: &mut Draw) {
    let p = g.p;
    g.use_char('∪', 0.0, 0.0);
    let t = fine(p);
    let h = 0.46 * half_span(p);
    let cy = p.axis + 0.15 * half_span(p);
    let rise = 0.55 * h;
    g.stroke(&hbar(p.mid() - h + 0.4 * t, p.mid() + h, cy, t));
    g.poly(&chevron(p.mid() - h, p.mid() - h + 1.2 * rise, cy, rise, t, 0.8 * tip(p)));
}

fn multiset_multiplication(g: &mut Draw) {
    let p = g.p;
    g.use_char('∪', 0.0, 0.0);
    g.dot(p.mid(), p.axis + 0.15 * half_span(p), 0.85 * p.dot);
}

/// ⟃ and (`right`) ⟄: the subset sign with a small ring in its mouth.
fn open_subset(g: &mut Draw, right: bool) {
    let p = g.p;
    subset(g, p.axis, set_rise(p), right, None);
    let r = 0.85 * small_ring(p);
    let x = p.op_l + p.op + 0.9 * rel_gap(p) + r - 10.0;
    circle(g, if right { p.width - x } else { x }, p.axis, r, None, Some(fine(p)));
}

fn open_subset_(g: &mut Draw) {
    open_subset(g, false);
}

fn open_superset(g: &mut Draw) {
    open_subset(g, true);
}

/// ⟈ and (`right`) ⟉: a slash and a subset sign in one cell, narrowed.
fn solidus_subset(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = 0.92 * p.op;
    let rise = 0.86 * set_rise(p);
    let w = 150.0;
    let a = arc(p, 26.0 + w + 0.6 * rel_gap(p), p.width - 26.0, p.axis - rise, p.axis + rise, Some(t));
    let s = diag(26.0 + w - 0.4 * t, p.axis - rise, 26.0 + 0.4 * t, p.axis + rise, t);
    for k in [a, s] {
        g.stroke(&if right { mirror(&k, p.mid()) } else { k });
    }
}

fn reverse_solidus_subset(g: &mut Draw) {
    solidus_subset(g, false);
}

fn superset_solidus(g: &mut Draw) {
    solidus_subset(g, true);
}

// ---------------------------------------------------------------------------------------------------------------
// Logic

fn curly_and(g: &mut Draw) {
    let p = g.p;
    g.stroke(&curly_wedge(p, stand_top(p), 0.0));
}

/// ⟑ and (`down`) ⟇: the wedge with a dot inside.
fn wedge_dot(g: &mut Draw, down: bool) {
    let p = g.p;
    let top = stand_top(p);
    if down {
        wedge(g, top, 0.0);
    } else {
        wedge(g, 0.0, top);
    }
    let y = if down { 0.62 * top } else { 0.38 * top };
    g.dot(p.mid(), y, 0.8 * p.dot);
}

fn and_with_dot(g: &mut Draw) {
    wedge_dot(g, false);
}

fn or_with_dot(g: &mut Draw) {
    wedge_dot(g, true);
}

/// ⟎ and (`down`) ⟏: the wedge in the box of the squared operators.
fn squared_wedge(g: &mut Draw, down: bool) {
    let p = g.p;
    let r = big_box(g) - 0.8 * rel_gap(p);
    // the wedge's stroke is a share of its size: with the fine stroke its two arms meet in the Bold, where the
    // box is small, and the shape closes
    let t = 0.38 * r;
    let (y0, y1) = if down { (p.axis + r, p.axis - r) } else { (p.axis - r, p.axis + r) };
    g.poly(&vee(p.mid() - r, p.mid() + r, y0, y1, t, 0.8 * tip(p)));
}

fn squared_and(g: &mut Draw) {
    squared_wedge(g, false);
}

fn squared_or(g: &mut Draw) {
    squared_wedge(g, true);
}

/// ⋋ and (`right`) ⋌: a long stroke falling from the top left to the bottom right, and a short one from its
/// middle to the bottom left.
fn semidirect(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = p.op;
    let top = stand_top(p);
    let long = diag(p.op_l + 0.5 * t, top, p.op_r() - 0.5 * t, 0.0, t);
    let short = diag(p.mid(), 0.5 * top, p.op_l + 0.5 * t, 0.0, t);
    for k in [long, short] {
        g.stroke(&if right { mirror(&k, p.mid()) } else { k });
    }
}

fn left_semidirect(g: &mut Draw) {
    semidirect(g, false);
}

fn right_semidirect(g: &mut Draw) {
    semidirect(g, true);
}

// ---------------------------------------------------------------------------------------------------------------
// Arithmetic and small operators

fn dot_plus(g: &mut Draw) {
    let p = g.p;
    let h = 0.80 * half_span(p);
    let dy = dot_gap(p) + 2.0 * p.dot;
    let cy = p.axis - dy / 2.0;
    bar(g, cy, Some(p.mid() - h), Some(p.mid() + h), None);
    stem(g, p.mid(), cy - h, cy + h, None);
    g.dot(p.mid(), cy + h + dot_gap(p) + p.dot, p.dot);
}

/// ∹: a bar on the left and the dots of the ratio sign on the right.
fn excess(g: &mut Draw) {
    let p = g.p;
    let (r, d) = ratio_dots(p);
    let x = p.op_r() - r;
    bar(g, p.axis, None, Some(x - r - 0.9 * rel_gap(p)), None);
    g.dot(x, p.axis + d, r);
    g.dot(x, p.axis - d, r);
}

fn geometric_proportion(g: &mut Draw) {
    let p = g.p;
    let (r, d) = ratio_dots(p);
    bar(g, p.axis, None, None, None);
    for (dx, dy) in [(-d, d), (d, d), (-d, -d), (d, -d)] {
        g.dot(p.mid() + dx, p.axis + dy, r);
    }
}

fn division_times(g: &mut Draw) {
    let p = g.p;
    let h = half_span(p);
    cross(g, p.mid(), p.axis, 0.56 * h, Some(0.5 * (p.op + fine(p))));
    bar(g, p.axis, None, None, Some(0.5 * (p.op + fine(p))));
    let d = 0.56 * h + 0.5 * p.op + dot_gap(p) + p.dot;
    g.dot(p.mid(), p.axis + d, p.dot);
    g.dot(p.mid(), p.axis - d, p.dot);
}

/// ⊹: the arms of a plus, apart from its middle.
fn hermitian(g: &mut Draw) {
    let p = g.p;
    let h = 0.86 * half_span(p);
    let gap = 0.42 * h;
    let t = p.op;
    bar(g, p.axis, Some(p.mid() - h), Some(p.mid() - gap), Some(t));
    bar(g, p.axis, Some(p.mid() + gap), Some(p.mid() + h), Some(t));
    stem(g, p.mid(), p.axis - h, p.axis - gap, Some(t));
    stem(g, p.mid(), p.axis + gap, p.axis + h, Some(t));
}

fn double_plus(g: &mut Draw) {
    let p = g.p;
    let h = half_span(p);
    let d = 0.5 * twin_pitch(p, p.op);
    bar(g, p.axis, None, None, None);
    stem(g, p.mid() - d, p.axis - 0.8 * h, p.axis + 0.8 * h, None);
    stem(g, p.mid() + d, p.axis - 0.8 * h, p.axis + 0.8 * h, None);
}

fn n_ary_times(g: &mut Draw) {
    let p = g.p;
    let t = nary_stroke(p);
    let (xl, xr, bot, top) = nary_box(p);
    let w = diag(xl, bot, xr, top, t)[0].w;
    slash(g, xl + w / 2.0, bot, xr - w / 2.0, top, t);
    slash(g, xr - w / 2.0, bot, xl + w / 2.0, top, t);
}

/// ⨝: the bowtie, as tall as the n-ary operators reach above the cap height's half.
fn join(g: &mut Draw) {
    let p = g.p;
    let t = p.op;
    let h = 1.3 * chevron_rise(p);
    let td = 0.5 * (p.op + fine(p));
    let (x0, x1) = (p.op_l - 30.0, p.op_r() + 30.0);
    let w = rake(x0, 0.0, x1, 2.0 * h, td)[0].w;
    let dy = h - w / 2.0;
    g.stroke(&rake(x0, p.axis - dy, x1, p.axis + dy, td));
    g.stroke(&rake(x0, p.axis + dy, x1, p.axis - dy, td));
    stem(g, x0 + t / 2.0, p.axis - h, p.axis + h, Some(t));
    stem(g, x1 - t / 2.0, p.axis - h, p.axis + h, Some(t));
}

/// ⟕ ⟖ ⟗: the bowtie narrowed, with bars drawn out from the top and bottom of one or both of its sides.
fn outer_join(g: &mut Draw, left: bool, right: bool) {
    let p = g.p;
    let t = 0.92 * p.op;
    let h = chevron_rise(p);
    let td = 0.5 * (p.op + fine(p));
    let ext = 92.0;
    let x0 = if left { 26.0 + ext } else { p.op_l };
    let x1 = if right { p.width - 26.0 - ext } else { p.op_r() };
    let w = rake(x0, 0.0, x1, 2.0 * h, td)[0].w;
    let dy = h - w / 2.0;
    g.stroke(&rake(x0, p.axis - dy, x1, p.axis + dy, td));
    g.stroke(&rake(x0, p.axis + dy, x1, p.axis - dy, td));
    stem(g, x0 + t / 2.0, p.axis - h, p.axis + h, Some(t));
    stem(g, x1 - t / 2.0, p.axis - h, p.axis + h, Some(t));
    for s in [1.0, -1.0] {
        let y = p.axis + s * (h - t / 2.0);
        if left {
            bar(g, y, Some(26.0), Some(x0 + t / 2.0), Some(t));
        }
        if right {
            bar(g, y, Some(x1 - t / 2.0), Some(p.width - 26.0), Some(t));
        }
    }
}

fn left_outer_join(g: &mut Draw) {
    outer_join(g, true, false);
}

fn right_outer_join(g: &mut Draw) {
    outer_join(g, false, true);
}

fn full_outer_join(g: &mut Draw) {
    outer_join(g, true, true);
}

/// ⨟: a small ring over a comma, on the axis.
fn schema_composition(g: &mut Draw) {
    let p = g.p;
    let r = 0.9 * small_ring(p);
    let t = 0.5 * (p.op + fine(p));
    let yr = p.axis + 0.55 * stand_top(p) - r;
    circle(g, p.mid(), yr, r, None, Some(t));
    let yd = p.axis - 0.18 * stand_top(p);
    let rd = 1.05 * p.punct;
    g.dot(p.mid(), yd, rd);
    g.stroke(&[
        knot(p.mid() + rd - 0.5 * t, yd, t).dir(-90.0),
        knot(p.mid() - 0.6 * rd, yd - 2.6 * rd, 0.5 * t).dir(-130.0),
    ]);
}

fn z_type_colon(g: &mut Draw) {
    let p = g.p;
    let r = p.punct;
    let d = 0.5 * stand_top(p) - r;
    g.dot(p.mid(), p.axis + d, r);
    g.dot(p.mid(), p.axis - d, r);
}

// ---------------------------------------------------------------------------------------------------------------
// Circled and squared

fn circled_dash(g: &mut Draw) {
    let p = g.p;
    let r = big_ring(g);
    g.stroke(&hbar(p.mid() - 0.58 * r, p.mid() + 0.58 * r, p.axis, p.op));
}

fn circled_white_bullet(g: &mut Draw) {
    let p = g.p;
    let r = big_ring(g);
    // the inner ring's stroke is a share of its radius, so its counter stays open at every weight
    circle(g, p.mid(), p.axis, 0.6 * r, None, Some(0.45 * 0.6 * r));
}

fn circled_bullet(g: &mut Draw) {
    let p = g.p;
    let r = big_ring(g);
    g.dot(p.mid(), p.axis, 0.52 * r);
}

fn squared_slash(g: &mut Draw, falling: bool) {
    let p = g.p;
    let r = big_box(g) + 4.0;
    let s = if falling { -1.0 } else { 1.0 };
    slash(g, p.mid() - r, p.axis - s * r, p.mid() + r, p.axis + s * r, fine(p));
}

fn squared_rising(g: &mut Draw) {
    squared_slash(g, false);
}

fn squared_falling(g: &mut Draw) {
    squared_slash(g, true);
}

fn squared_asterisk(g: &mut Draw) {
    let p = g.p;
    let r = 0.74 * big_box(g);
    let t = 0.8 * fine(p);
    g.stroke(&vstem(p.mid(), p.axis - r, p.axis + r, t));
    let (c, s) = (30f64.to_radians().cos(), 30f64.to_radians().sin());
    for sign in [1.0, -1.0] {
        g.stroke(&rake(p.mid() - r * c, p.axis - sign * r * s, p.mid() + r * c, p.axis + sign * r * s, t));
    }
}

fn squared_small_circle(g: &mut Draw) {
    let p = g.p;
    let r = big_box(g);
    circle(g, p.mid(), p.axis, 0.62 * r, None, Some(0.7 * fine(p)));
}

/// A square of the squared operators' size shifted `dx` along, with a tick from the middle of one side.
fn ticked_square(g: &mut Draw, right: bool) {
    let p = g.p;
    let h = half_span(p) - 40.0;
    let s = if right { -1.0 } else { 1.0 };
    let cx = p.mid() + s * 40.0;
    outline(g, &box_(cx - h, p.axis - h, cx + h, p.axis + h), None);
    let (a, b) = if right { (cx + h - 4.0, p.width - 26.0) } else { (26.0, cx - h + 4.0) };
    bar(g, p.axis, Some(a), Some(b), None);
}

fn square_left_tick(g: &mut Draw) {
    ticked_square(g, false);
}

fn square_right_tick(g: &mut Draw) {
    ticked_square(g, true);
}

// ---------------------------------------------------------------------------------------------------------------
// Diamonds and triangles

fn diamond_dot(g: &mut Draw) {
    let p = g.p;
    let (rx, ry) = (half_span(p) + 10.0, 1.24 * half_span(p));
    let c = pt(p.mid(), p.axis);
    outline(g, &[c + pt(rx, 0.0), c + pt(0.0, ry), c - pt(rx, 0.0), c - pt(0.0, ry)], None);
    g.dot(p.mid(), p.axis, 0.65 * p.dot);
}

fn lozenge_rule(g: &mut Draw) {
    let p = g.p;
    let (rx, ry) = (0.62 * half_span(p), 1.5 * half_span(p));
    let c = pt(p.mid(), p.axis);
    let t = 0.5 * (p.op + fine(p));
    outline(g, &[c + pt(rx, 0.0), c + pt(0.0, ry), c - pt(rx, 0.0), c - pt(0.0, ry)], Some(t));
    bar(g, p.axis, Some(p.mid() - rx), Some(p.mid() + rx), Some(t));
}

/// The concave-sided diamond: four strokes that bow in between its points, each cut along the axis through
/// the point so that two sides meet there in a sharp point; `tick` draws a bar out from its left (-1) or right
/// (1) point.
fn concave_diamond(g: &mut Draw, tick: f64) {
    let p = g.p;
    let t = fine(p);
    let f = 1.0 - 0.14 * tick.abs(); // the ticked ones are smaller, to leave room for the tick
    let rx = f * half_span(p);
    let ry = f * 1.16 * half_span(p);
    let cx = p.mid() - 50.0 * tick;
    let c = pt(cx, p.axis);
    let pts = [c + pt(rx, 0.0), c + pt(0.0, ry), c - pt(rx, 0.0), c - pt(0.0, ry)];
    let pens = [0.0, 90.0, 0.0, 90.0]; // the axis through each point
    let bend = 11.0; // how far each side leaves its chord, in degrees
    for i in 0..4 {
        let j = (i + 1) % 4;
        let (a, b) = (pts[i], pts[j]);
        let chord = (b - a).angle();
        let (da, db) = (chord + bend, chord - bend);
        let ka = cut_pen(a.x, a.y, t, da, pens[i]);
        let kb = cut_pen(b.x, b.y, t, db, pens[j]);
        // the cuts are centred on the points; move them in by half a cut, so that the points are where they say
        let inward =
            |k: Knot, z: V| Knot::at(k.z + (c - z) * (0.5 * k.w / (c - z).abs()), k.w).pen(k.pen.unwrap_or(0.0));
        g.stroke(&[inward(ka, a).dir(da), inward(kb, b).dir(db)]);
    }
    if tick != 0.0 {
        let x = cx + tick * (rx - 10.0);
        let end = if tick > 0.0 { p.width - 26.0 } else { 26.0 };
        let (a, b) = if tick > 0.0 { (x, end) } else { (end, x) };
        bar(g, p.axis, Some(a), Some(b), Some(t));
    }
}

fn concave_diamond_(g: &mut Draw) {
    concave_diamond(g, 0.0);
}

fn concave_diamond_left(g: &mut Draw) {
    concave_diamond(g, -1.0);
}

fn concave_diamond_right(g: &mut Draw) {
    concave_diamond(g, 1.0);
}

/// ⟁: a triangle with a small one inside.
fn triangle_in_triangle(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (p.op_l - 20.0, p.op_r() + 20.0);
    let top = p.cap;
    outline(g, &[pt(x0, 0.0), pt(x1, 0.0), pt(p.mid(), top)], None);
    let s = 0.54;
    let cy = 0.35 * top;
    let (a, b) = (p.mid() - s * (x1 - x0) / 2.0, p.mid() + s * (x1 - x0) / 2.0);
    let h = s * top;
    outline(g, &[pt(a, cy - h / 3.0), pt(b, cy - h / 3.0), pt(p.mid(), cy + 2.0 * h / 3.0)], Some(0.6 * fine(p)));
}

fn right_triangle(g: &mut Draw) {
    let p = g.p;
    outline(g, &[pt(p.op_l, 0.0), pt(p.op_r(), 0.0), pt(p.op_r(), angle_top(p))], None);
}

// ---------------------------------------------------------------------------------------------------------------
// Angles, integrals and the rest

/// The arc of the measured angles: centred on (`cx`, `cy`), radius `r` on its centre line, from `a0` to
/// `a1` degrees.
fn angle_arc(p: &Params, cx: f64, cy: f64, r: f64, a0: f64, a1: f64) -> Vec<Knot> {
    let t = fine(p);
    let am = (a0 + a1) / 2.0;
    [a0, am, a1].iter().map(|&a| Knot::at(pt(cx, cy) + r * V::unit(a), t).dir(a + 90.0)).collect()
}

fn measured_angle(g: &mut Draw) {
    let p = g.p;
    let th = angle_shape(g, p.op).to_degrees();
    let r = 0.56 * (p.op_r() - p.op_l);
    g.stroke(&angle_arc(p, p.op_l, 0.0, r, 0.0, th + 12.0));
}

fn spherical_angle(g: &mut Draw) {
    let p = g.p;
    g.use_char('<', 0.0, 0.0);
    let span = p.op_r() - p.op_l;
    let th = (chevron_rise(p) / span).atan().to_degrees();
    g.stroke(&angle_arc(p, p.op_l, p.axis, 0.62 * span, -th - 12.0, th + 12.0));
}

fn right_angle_arc(g: &mut Draw) {
    let p = g.p;
    right_angle(g);
    let r = 0.50 * (p.op_r() - p.op_l);
    let x = p.op_l + p.op / 2.0;
    g.stroke(&angle_arc(p, x, p.op / 2.0, r, 0.0, 90.0));
}

/// ⟀: the right angle with a ray from its corner at 45 degrees.
fn three_dimensional_angle(g: &mut Draw) {
    let p = g.p;
    right_angle(g);
    let t = p.op;
    let x0 = p.op_l + 0.5 * t;
    let reach = 0.66 * (p.op_r() - x0);
    g.stroke(&diag(x0 + 0.5 * t, 0.5 * t, x0 + reach, reach, t));
}

fn mathematical_diagonal(g: &mut Draw, falling: bool) {
    let p = g.p;
    let (y0, y1) = (0.5 * p.desc, p.cap + 40.0);
    let w = diag(p.op_l, y0, p.op_r(), y1, p.op)[0].w;
    let (a, b) = (p.op_l + w / 2.0, p.op_r() - w / 2.0);
    if falling {
        slash(g, b, y0, a, y1, p.op);
    } else {
        slash(g, a, y0, b, y1, p.op);
    }
}

fn rising_diagonal(g: &mut Draw) {
    mathematical_diagonal(g, false);
}

fn falling_diagonal(g: &mut Draw) {
    mathematical_diagonal(g, true);
}

/// ⟌: a closing parenthesis on the left with a bar from its top across the cell.
fn long_division(g: &mut Draw) {
    let p = g.p;
    let t = p.op;
    let (y0, y1) = (p.br_bot + 60.0, p.cap + 30.0);
    let x = p.op_l - 20.0;
    g.stroke(&[
        knot(x, y1 - t / 2.0, t).pen(90.0).dir(0.0),
        knot(x + 110.0, (y0 + y1) / 2.0, 1.1 * t).dir(-90.0),
        cut_pen(x + 10.0, y0, 0.9 * t, 235.0, 0.0),
    ]);
    bar(g, y1 - t / 2.0, Some(x), Some(p.width - 20.0), None);
}

fn vertical_bar_horizontal_stroke(g: &mut Draw) {
    let p = g.p;
    stem(g, p.mid(), 0.0, stand_top(p), None);
    let h = 0.36 * half_span(p);
    bar(g, p.axis, Some(p.mid() - h), Some(p.mid() + h), None);
}

/// ⟓ and (`upper`) ⟔: a corner with a dot inside it.
fn corner_dot(g: &mut Draw, upper: bool) {
    let p = g.p;
    let t = p.op;
    let top = stand_top(p);
    let k = vec![
        knot(p.op_r() - t / 2.0, top, t).pen(0.0).line(),
        knot(p.op_r() - t / 2.0, t / 2.0, t).line(),
        knot(p.op_l, t / 2.0, t).pen(90.0),
    ];
    let k = if upper { flip(&mirror(&k, p.mid()), p.axis) } else { k };
    g.stroke(&k);
    let (x, y) = (p.mid() + 40.0, 0.5 * top - 30.0);
    let (x, y) = if upper { (p.width - x, 2.0 * p.axis - y) } else { (x, y) };
    g.dot(x, y, 0.85 * p.dot);
}

fn lower_right_corner_dot(g: &mut Draw) {
    corner_dot(g, false);
}

fn upper_left_corner_dot(g: &mut Draw) {
    corner_dot(g, true);
}

fn double_integral(g: &mut Draw) {
    integrals(g, 2);
}

fn triple_integral(g: &mut Draw) {
    integrals(g, 3);
}

fn surface_integral(g: &mut Draw) {
    integrals(g, 2);
    contour_ring(g, 2);
}

fn volume_integral(g: &mut Draw) {
    integrals(g, 3);
    contour_ring(g, 3);
}

/// A small arrowhead on the contour ring's right side, pointing down (clockwise) or up.
fn ring_arrow(g: &mut Draw, clockwise: bool) {
    let p = g.p;
    let r = 98.0 + 0.3 * p.op;
    let x = p.mid() + r - 0.46 * fine(p);
    let w = 0.8 * fine(p) + 22.0; // half the head's width
    let len = 0.8 * r;
    let s = if clockwise { -1.0 } else { 1.0 };
    g.poly(&[pt(x, p.axis + s * 0.5 * len), pt(x - w, p.axis - s * 0.5 * len), pt(x + w, p.axis - s * 0.5 * len)]);
}

fn clockwise_contour(g: &mut Draw) {
    contour_integral(g);
    ring_arrow(g, true);
}

fn anticlockwise_contour(g: &mut Draw) {
    contour_integral(g);
    ring_arrow(g, false);
}

/// ∱: the integral with an arrowed half ring on its right.
fn clockwise_integral(g: &mut Draw) {
    let p = g.p;
    integral(g);
    let r = 98.0 + 0.3 * p.op;
    let t = 0.92 * fine(p);
    let c = pt(p.mid(), p.axis);
    g.stroke(&[
        Knot::at(c + (r - t / 2.0) * V::unit(110.0), t).dir(20.0),
        Knot::at(c + (r - t / 2.0) * V::unit(0.0), t).dir(-90.0),
        Knot::at(c + (r - t / 2.0) * V::unit(-80.0), t).dir(-170.0),
    ]);
    ring_arrow(g, true);
}

pub fn register(reg: &mut Registry) {
    reg.module("math");
    // n-ary operators
    reg.ch('∑', summation);
    reg.ch('∏', nary_product);
    reg.ch('∐', nary_coproduct);
    reg.ch('⋀', nary_and);
    reg.ch('⋁', nary_or);
    reg.ch('⋂', nary_intersection);
    reg.ch('⋃', nary_union);
    reg.ch('⨄', nary_union_plus);
    reg.ch('⨅', nary_square_cap);
    reg.ch('⨆', nary_square_cup);
    reg.ch('⨀', nary_circled_dot);
    reg.ch('⨁', nary_circled_plus);
    reg.ch('⨂', nary_circled_times);
    // integrals
    reg.ch_with('∫', Opt::UPRIGHT, integral);
    reg.ch_with('∮', Opt::UPRIGHT, contour_integral);
    // letter-like signs
    reg.ch('∂', partial);
    reg.ch('∆', increment_);
    reg.ch('∇', nabla);
    // angles
    reg.ch('∠', angle);
    reg.ch('∟', right_angle);
    reg.ch('⟂', perpendicular);
    // slashes, stars, dots
    reg.ch('∕', division_slash);
    reg.ch('⧸', big_solidus);
    reg.ch('∗', asterisk_operator);
    reg.ch('∶', ratio);
    reg.ch('∷', proportion);
    reg.ch('∸', dot_minus);
    reg.ch('≀', wreath);
    reg.ch('∜', fourth_root);
    // relations
    reg.ch('≇', not_congruent);
    reg.ch('≋', triple_tilde);
    reg.ch('≣', strictly_equivalent);
    reg.ch('≍', equivalent_to);
    reg.ch('≐', approaches_limit);
    reg.ch('≗', ring_equal);
    reg.ch('⊜', circled_equals);
    reg.ch('≮', not_less);
    reg.ch('≯', not_greater);
    reg.ch('≰', not_less_equal);
    reg.ch('≱', not_greater_equal);
    reg.ch('⊼', nand);
    reg.ch('⊽', nor);
    reg.ch('⋎', curly_or);
    reg.ch('⨯', vector_product);
    reg.ch('⨿', amalgamation);
    reg.ch('⩴', double_colon_equal);
    reg.ch('⪯', precedes_above_equal);
    reg.ch('⪰', succeeds_above_equal);
    reg.ch('⫤', vertical_bar_double_left_turnstile);
    reg.ch('∊', small_element_of);
    // tier 2: negated relations
    reg.ch('≁', |g: &mut Draw| negated(g, '∼'));
    reg.ch('≄', |g: &mut Draw| negated(g, '≃'));
    reg.ch('≭', |g: &mut Draw| negated(g, '≍'));
    reg.ch('⊀', |g: &mut Draw| negated(g, '≺'));
    reg.ch('⊁', |g: &mut Draw| negated(g, '≻'));
    reg.ch('⋠', |g: &mut Draw| negated(g, '≼'));
    reg.ch('⋡', |g: &mut Draw| negated(g, '≽'));
    reg.ch('⋢', |g: &mut Draw| negated(g, '⊑'));
    reg.ch('⋣', |g: &mut Draw| negated(g, '⊒'));
    reg.ch('⋪', |g: &mut Draw| negated(g, '⊲'));
    reg.ch('⋫', |g: &mut Draw| negated(g, '⊳'));
    reg.ch('⋬', |g: &mut Draw| negated(g, '⊴'));
    reg.ch('⋭', |g: &mut Draw| negated(g, '⊵'));
    reg.ch('≸', |g: &mut Draw| negated(g, '≶'));
    reg.ch('≹', |g: &mut Draw| negated(g, '≷'));
    reg.ch('≴', |g: &mut Draw| negated(g, '≲'));
    reg.ch('≵', |g: &mut Draw| negated(g, '≳'));
    reg.ch('⊬', |g: &mut Draw| not_turnstile(g, '⊢'));
    reg.ch('⊭', |g: &mut Draw| not_turnstile(g, '⊨'));
    reg.ch('⊮', |g: &mut Draw| not_turnstile(g, '⊩'));
    reg.ch('⊯', |g: &mut Draw| not_turnstile(g, '⊫'));
    reg.ch('≆', approx_not_equal);
    reg.ch('≨', less_but_not_equal);
    reg.ch('≩', greater_but_not_equal);
    reg.ch('⋦', |g: &mut Draw| not_equivalent_below(g, '≲'));
    reg.ch('⋧', |g: &mut Draw| not_equivalent_below(g, '≳'));
    reg.ch('⋨', |g: &mut Draw| not_equivalent_below(g, '≾'));
    reg.ch('⋩', |g: &mut Draw| not_equivalent_below(g, '≿'));
    reg.ch('⋤', |g: &mut Draw| square_image_not_equal(g, '⊑'));
    reg.ch('⋥', |g: &mut Draw| square_image_not_equal(g, '⊒'));
    // tier 2: stacked and doubled relations
    reg.ch('≦', less_over_equal);
    reg.ch('≧', greater_over_equal);
    reg.ch('≶', less_or_greater);
    reg.ch('≷', greater_or_less);
    reg.ch('⋚', less_equal_or_greater);
    reg.ch('⋛', greater_equal_or_less);
    reg.ch('⋜', equal_or_less_);
    reg.ch('⋝', equal_or_greater);
    reg.ch('≼', precedes_or_equal);
    reg.ch('≽', succeeds_or_equal);
    reg.ch('⋞', equal_or_precedes);
    reg.ch('⋟', equal_or_succeeds);
    reg.ch('≾', precedes_or_equivalent);
    reg.ch('≿', succeeds_or_equivalent);
    reg.ch('⋖', less_with_dot);
    reg.ch('⋗', greater_with_dot);
    reg.ch('⋘', very_much_less);
    reg.ch('⋙', very_much_greater);
    reg.ch('⩿', less_slanted_equal_dot);
    reg.ch('⊰', precedes_under_relation);
    reg.ch('⊱', succeeds_under_relation);
    // tier 2: tildes and equals with marks
    reg.ch('∽', reversed_tilde);
    reg.ch('∿', sine_wave);
    reg.ch('∾', inverted_lazy_s);
    reg.ch('≂', minus_tilde);
    reg.ch('⋍', reversed_tilde_equals);
    reg.ch('≌', all_equal);
    reg.ch('≊', almost_equal_or_equal);
    reg.ch('∻', homothetic);
    reg.ch('≎', geometrically_equivalent);
    reg.ch('≏', difference_between);
    reg.ch('≑', geometrically_equal);
    reg.ch('≒', image_of_left);
    reg.ch('≓', image_of_right);
    reg.ch('≖', ring_in_equal);
    reg.ch('≘', corresponds_to);
    reg.ch('≙', estimates);
    reg.ch('≚', equiangular);
    reg.ch('≛', star_equals);
    reg.ch('≞', measured_by);
    reg.ch('⋕', equal_and_parallel);
    reg.ch('≬', between);
    // tier 2: turnstiles and tacks
    reg.ch('⊦', assertion);
    reg.ch('⊧', models_short);
    reg.ch('⊪', triple_bar_turnstile);
    reg.ch('⊫', double_bar_double_turnstile);
    reg.ch('⫪', double_down_tack);
    reg.ch('⫫', double_up_tack);
    reg.ch('⟘', large_up_tack);
    reg.ch('⟙', large_down_tack);
    reg.ch('⟚', left_right_double_turnstile);
    reg.ch('⟛', left_right_tack);
    reg.ch('⟝', long_right_tack);
    reg.ch('⟞', long_left_tack);
    reg.ch('⟟', up_tack_circle);
    reg.ch('⊺', intercalate);
    reg.ch('⊶', original_of);
    reg.ch('⊷', image_of_);
    reg.ch('⊸', multimap);
    reg.ch('⟜', left_multimap);
    // tier 2: sets and elements
    reg.ch('∁', complement);
    reg.ch('∍', small_contains);
    reg.ch('⋲', |g: &mut Draw| element_long_bar(g, false));
    reg.ch('⋺', |g: &mut Draw| element_long_bar(g, true));
    reg.ch('⋳', |g: &mut Draw| element_end_bar(g, false, false));
    reg.ch('⋻', |g: &mut Draw| element_end_bar(g, true, false));
    reg.ch('⋴', |g: &mut Draw| element_end_bar(g, false, true));
    reg.ch('⋼', |g: &mut Draw| element_end_bar(g, true, true));
    reg.ch('⋵', |g: &mut Draw| element_mark(g, false, false, '.'));
    reg.ch('⋶', |g: &mut Draw| element_mark(g, false, false, '-'));
    reg.ch('⋽', |g: &mut Draw| element_mark(g, true, false, '-'));
    reg.ch('⋷', |g: &mut Draw| element_mark(g, false, true, '-'));
    reg.ch('⋾', |g: &mut Draw| element_mark(g, true, true, '-'));
    reg.ch('⋸', |g: &mut Draw| element_mark(g, false, false, '_'));
    reg.ch('⋹', element_two_bars);
    reg.ch('⋿', bag_membership);
    reg.ch('⟒', element_opening_up);
    reg.ch('⫙', element_opening_down);
    reg.ch('⋐', double_subset_);
    reg.ch('⋑', double_superset);
    reg.ch('⋒', double_intersection);
    reg.ch('⋓', double_union);
    reg.ch('⋔', pitchfork);
    reg.ch('⊌', multiset);
    reg.ch('⊍', multiset_multiplication);
    reg.ch('⟃', open_subset_);
    reg.ch('⟄', open_superset);
    reg.ch('⟈', reverse_solidus_subset);
    reg.ch('⟉', superset_solidus);
    // tier 2: logic
    reg.ch('⋏', curly_and);
    reg.ch('⟑', and_with_dot);
    reg.ch('⟇', or_with_dot);
    reg.ch('⟎', squared_and);
    reg.ch('⟏', squared_or);
    reg.ch('⋋', left_semidirect);
    reg.ch('⋌', right_semidirect);
    // tier 2: arithmetic and small operators
    reg.ch('∔', dot_plus);
    reg.ch('∹', excess);
    reg.ch('∺', geometric_proportion);
    reg.ch('⋇', division_times);
    reg.ch('⊹', hermitian);
    reg.ch('⧺', double_plus);
    reg.ch('⨉', n_ary_times);
    reg.ch('⨝', join);
    reg.ch('⟕', left_outer_join);
    reg.ch('⟖', right_outer_join);
    reg.ch('⟗', full_outer_join);
    reg.ch('⨟', schema_composition);
    reg.ch('⦂', z_type_colon);
    // tier 2: circled, squared, diamonds, triangles
    reg.ch('⊝', circled_dash);
    reg.ch('⦾', circled_white_bullet);
    reg.ch('⦿', circled_bullet);
    reg.ch('⧄', squared_rising);
    reg.ch('⧅', squared_falling);
    reg.ch('⧆', squared_asterisk);
    reg.ch('⧇', squared_small_circle);
    reg.ch('⟤', square_left_tick);
    reg.ch('⟥', square_right_tick);
    reg.ch('⟐', diamond_dot);
    reg.ch('⟠', lozenge_rule);
    reg.ch('⟡', concave_diamond_);
    reg.ch('⟢', concave_diamond_left);
    reg.ch('⟣', concave_diamond_right);
    reg.ch('⟁', triangle_in_triangle);
    reg.ch('⊿', right_triangle);
    // tier 2: angles, integrals, diagonals and corners
    reg.ch('∡', measured_angle);
    reg.ch('∢', spherical_angle);
    reg.ch('⊾', right_angle_arc);
    reg.ch('⟀', three_dimensional_angle);
    reg.ch('⟋', rising_diagonal);
    reg.ch('⟍', falling_diagonal);
    reg.ch('⟌', long_division);
    reg.ch('⟊', vertical_bar_horizontal_stroke);
    reg.ch('⟓', lower_right_corner_dot);
    reg.ch('⟔', upper_left_corner_dot);
    reg.ch_with('∬', Opt::UPRIGHT, double_integral);
    reg.ch_with('∭', Opt::UPRIGHT, triple_integral);
    reg.ch_with('∯', Opt::UPRIGHT, surface_integral);
    reg.ch_with('∰', Opt::UPRIGHT, volume_integral);
    reg.ch_with('∱', Opt::UPRIGHT, clockwise_integral);
    reg.ch_with('∲', Opt::UPRIGHT, clockwise_contour);
    reg.ch_with('∳', Opt::UPRIGHT, anticlockwise_contour);
}
