//! Operators and mathematical signs.
//!
//! The group is a system. Every sign is assembled from a few primitives, defined once below: the bar, the stem, the
//! chevron, the slash, the ring, the dot and the arc. They share one axis (`p.axis`), one stroke (`p.op`) and one
//! horizontal span (`p.op_l` to `p.op_r`), so `->`, `=>`, `<=` and `|>` line up without being fused.

use rachis_kernel::geom::intersect;
use rachis_kernel::{Draw, Knot, Params, Registry, V, knot, pt};

use crate::parts::{cut, cut_pen, diag, elbow, flip, hbar, mirror, ring, vee, vee_x, vstem};

// ---------------------------------------------------------------------------------------------------------------
// Measurements the group derives from the parameters

/// Half the operators' span: the plus is this far across and this far up and down from the axis.
pub fn half_span(p: &Params) -> f64 {
    (p.op_r() - p.op_l) / 2.0
}

/// Half the span of the master's own cell, whatever cell the sign is drawn in.
pub fn standard_half_span(p: &Params) -> f64 {
    (p.cell - 2.0 * p.op_l) / 2.0
}

/// How much taller than in the master's own cell a relation between sets is drawn: as much as its span is wider,
/// and no more than the span of that kind. A relation with something beside it is wider and no taller, so the
/// kind has one height.
pub fn relation_growth(p: &Params) -> f64 {
    p.grown().min(crate::signs::RELATION)
}

/// The same for tacks and turnstiles, circled and boxed operators and bowties.
pub fn round_growth(p: &Params) -> f64 {
    p.grown().min(crate::signs::ROUND)
}

/// Half the height of a turnstile: half the span in the master's own cell, and as tall in every wider one.
pub fn tack_rise(p: &Params) -> f64 {
    standard_half_span(p) * round_growth(p)
}

/// The stroke of a part drawn inside another shape, or doubled: it grows with weight more slowly than
/// `p.op`, so that counters stay open in the Bold.
pub fn fine(p: &Params) -> f64 {
    0.56 * p.op + 18.0
}

/// The flat of a pointed vertex: a third of a stem.
pub fn tip(p: &Params) -> f64 {
    p.stem / 3.0
}

/// How far the open ends of < and > reach above and below the axis (their outer corners).
pub fn chevron_rise(p: &Params) -> f64 {
    160.0 + 0.55 * p.op
}

/// The same for a chevron or an arc that stands over a bar: shortened. In a wider cell it grows with the span.
pub fn rel_rise(p: &Params) -> f64 {
    0.87 * chevron_rise(p) * relation_growth(p)
}

/// The white between a relation and the bar or wave under it.
pub fn rel_gap(p: &Params) -> f64 {
    40.0 + 0.5 * p.op
}

/// How far the arms of the subset and element signs lie above and below the axis (their outer edges). In a
/// wider cell it grows with the span, so the sign keeps its proportions.
pub fn set_rise(p: &Params) -> f64 {
    (185.0 + 0.5 * p.op) * relation_growth(p)
}

/// The top of the signs that stand on the baseline (the cup, the wedge, the divides bar): as far above the
/// axis as the baseline is below it, so that they too are centred on the axis.
pub fn stand_top(p: &Params) -> f64 {
    2.0 * p.axis
}

/// The bottom of the big operators (sum, product, radical).
pub fn big_bot(p: &Params) -> f64 {
    0.4 * p.br_bot
}

/// Their top.
pub fn big_top(p: &Params) -> f64 {
    p.cap + 30.0
}

/// Where to put a shape that reaches `rise` above and below its centre, and a thing `low` tall under it,
/// so that the pair is centred on the axis: the centre of the thing below, then the centre of the shape.
pub fn over(p: &Params, rise: f64, low: f64) -> (f64, f64) {
    let gap = rel_gap(p);
    let bottom = p.axis - (2.0 * rise + gap + low) / 2.0;
    (bottom + low / 2.0, bottom + low + gap + rise)
}

// ---------------------------------------------------------------------------------------------------------------
// Primitives

/// A polygon reflected left to right in the line x = cx.
pub fn mirrored(points: &[V], cx: f64) -> Vec<V> {
    points.iter().map(|z| pt(2.0 * cx - z.x, z.y)).collect()
}

/// The bar: a horizontal stroke centred on `y`, across the span unless told otherwise.
pub fn bar(g: &mut Draw, y: f64, x0: Option<f64>, x1: Option<f64>, t: Option<f64>) {
    let p = g.p;
    g.stroke(&hbar(x0.unwrap_or(p.op_l), x1.unwrap_or(p.op_r()), y, t.unwrap_or(p.op)));
}

/// The stem: a vertical stroke centred on `x`.
pub fn stem(g: &mut Draw, x: f64, y0: f64, y1: f64, t: Option<f64>) {
    let p = g.p;
    g.stroke(&vstem(x, y0, y1, t.unwrap_or(p.op)));
}

/// The polygon of a chevron: two straight strokes `t` thick that meet at a point on (`x_tip`, `cy`),
/// flattened there to `flat`, and are cut vertically at `x_open`, their outer corners `rise` above and
/// below `cy`.
pub fn chevron(x_tip: f64, x_open: f64, cy: f64, rise: f64, t: f64, flat: f64) -> Vec<V> {
    let s = if x_open > x_tip { 1.0 } else { -1.0 };
    let dx = (x_open - x_tip).abs();
    let dy = rise - flat / 2.0;
    let wv = t * dx.hypot(dy) / dx; // the height of the vertical cut
    let crotch = x_open - s * (rise - wv) * dx / dy;
    vec![
        pt(x_open, cy + rise),
        pt(x_tip, cy + flat / 2.0),
        pt(x_tip, cy - flat / 2.0),
        pt(x_open, cy - rise),
        pt(x_open, cy - rise + wv),
        pt(crotch, cy),
        pt(x_open, cy + rise - wv),
    ]
}

/// The slash: a straight stroke `t` thick between two points on its centre line, cut flat.
pub fn slash(g: &mut Draw, x0: f64, y0: f64, x1: f64, y1: f64, t: f64) {
    g.stroke(&diag(x0, y0, x1, y1, t));
}

/// A straight stroke `t` thick between two points on its centre line, cut vertically: for a stroke nearer
/// the horizontal than the vertical, where a flat cut would leave a sliver.
pub fn rake(x0: f64, y0: f64, x1: f64, y1: f64, t: f64) -> Vec<Knot> {
    let w = t * (x1 - x0).hypot(y1 - y0) / (x1 - x0).abs();
    vec![knot(x0, y0, w).pen(90.0).line(), knot(x1, y1, w).pen(90.0)]
}

/// The slash that negates a sign: through (`cx`, `cy`), reaching `dx` across and `dy` up and down.
pub fn strike(g: &mut Draw, cx: f64, cy: f64, dx: f64, dy: f64, t: Option<f64>) {
    let t = t.unwrap_or(g.p.op);
    slash(g, cx - dx, cy - dy, cx + dx, cy + dy, t);
}

/// The plus turned 45 degrees: two slashes through (`cx`, `cy`) whose centre lines reach `d`.
pub fn cross(g: &mut Draw, cx: f64, cy: f64, d: f64, t: Option<f64>) {
    let t = t.unwrap_or(g.p.op);
    slash(g, cx - d, cy - d, cx + d, cy + d, t);
    slash(g, cx - d, cy + d, cx + d, cy - d, t);
}

/// The ring: a superellipse whose outer edge is `rx` (and `ry`) from its centre.
pub fn circle(g: &mut Draw, cx: f64, cy: f64, rx: f64, ry: Option<f64>, t: Option<f64>) {
    let p = g.p;
    let t = t.unwrap_or(p.op);
    let ry = ry.unwrap_or(rx);
    g.stroke_closed(&ring(cx - rx, cy - ry, cx + rx, cy + ry, t, t, p.sq));
}

/// The arc: half a superelliptic ring whose round side touches `x_side` and whose straight arms, with their
/// outer edges on `y0` and `y1`, run to a vertical cut at `x_open`.
pub fn arc(p: &Params, x_side: f64, x_open: f64, y0: f64, y1: f64, t: Option<f64>) -> Vec<Knot> {
    let t = t.unwrap_or(p.op);
    let s = if x_open > x_side { 1.0 } else { -1.0 };
    let xa = x_side + s * (y1 - y0) / 2.0; // where the arms straighten
    let (yt, yb) = (y1 - t / 2.0, y0 + t / 2.0);
    let back = if s > 0.0 { 180.0 } else { 0.0 };
    vec![
        knot(x_open, yt, t).pen(90.0).line(),
        knot(xa, yt, t).pen(90.0).dir(back).k(p.sq),
        knot(x_side + s * t / 2.0, (y0 + y1) / 2.0, t).dir(-90.0).k(p.sq),
        knot(xa, yb, t).pen(90.0).dir(180.0 - back).line(),
        knot(x_open, yb, t).pen(90.0),
    ]
}

/// Reflect in the diagonal y = x, which exchanges across and up: the arc of the subset sign becomes the cup.
pub fn transposed(knots: &[Knot]) -> Vec<Knot> {
    knots
        .iter()
        .map(|k| Knot { z: pt(k.z.y, k.z.x), dir: k.dir.map(|d| 90.0 - d), pen: k.pen.map(|a| 90.0 - a), ..*k })
        .collect()
}

/// A convex polygon, given counter-clockwise, with every side moved `d` inwards.
pub fn inset(points: &[V], d: f64) -> Vec<V> {
    let n = points.len();
    let mut lines = Vec::with_capacity(n);
    for i in 0..n {
        let (a, b) = (points[i], points[(i + 1) % n]);
        let u = (b - a) / (b - a).abs();
        lines.push((a + (u * d).left(), u));
    }
    let mut out = Vec::with_capacity(n);
    for i in 0..n {
        let ((a, u), (b, v)) = (lines[(i + n - 1) % n], lines[i]);
        let z = intersect(a, u, b, v).expect("the sides of a polygon meet");
        out.push(z);
    }
    out
}

/// The outline of a convex polygon (counter-clockwise), `t` thick, inside it, with mitred corners.
pub fn outline(g: &mut Draw, points: &[V], t: Option<f64>) {
    let t = t.unwrap_or(g.p.op);
    let knots: Vec<Knot> = inset(points, t / 2.0).into_iter().map(|z| Knot::at(z, t).line()).collect();
    g.stroke_closed(&knots);
}

pub fn box_(x0: f64, y0: f64, x1: f64, y1: f64) -> Vec<V> {
    vec![pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1)]
}

/// How far the centre line of the tilde rises and falls.
pub fn wave_rise(p: &Params) -> f64 {
    60.0 + 0.14 * p.op
}

/// The wave of the tilde across the span, centred on `y`: up on the left, down on the right, cut vertically.
pub fn wave(p: &Params, y: f64, a: Option<f64>, t: Option<f64>) -> Vec<Knot> {
    let t = t.unwrap_or(p.op);
    let a = a.unwrap_or_else(|| wave_rise(p));
    let w = p.op_r() - p.op_l;
    vec![
        cut(p.op_l, y - 0.50 * a, t, 40.0),
        knot(p.op_l + 0.27 * w, y + a, t).dir(0.0),
        knot(p.mid(), y, t),
        knot(p.op_r() - 0.27 * w, y - a, t).dir(0.0),
        cut(p.op_r(), y + 0.50 * a, t, 40.0),
    ]
}

// ---------------------------------------------------------------------------------------------------------------
// ASCII

fn hyphen(g: &mut Draw) {
    let p = g.p;
    bar(g, p.axis, Some(p.op_l + 30.0), Some(p.op_r() - 30.0), None);
}

fn minus(g: &mut Draw) {
    bar(g, g.p.axis, None, None, None);
}

fn plus(g: &mut Draw) {
    let p = g.p;
    let h = half_span(p);
    bar(g, p.axis, None, None, None);
    stem(g, p.mid(), p.axis - h, p.axis + h, None);
}

/// The distance between the centre lines of the two bars of =: the gap is about 1.7 bars.
pub fn equal_pitch(p: &Params) -> f64 {
    100.0 + 1.35 * p.op
}

fn equal(g: &mut Draw) {
    let p = g.p;
    let d = equal_pitch(p) / 2.0;
    bar(g, p.axis + d, None, None, None);
    bar(g, p.axis - d, None, None, None);
}

fn less(g: &mut Draw) {
    let p = g.p;
    g.poly(&chevron(p.op_l, p.op_r(), p.axis, chevron_rise(p), p.op, tip(p)));
}

fn greater(g: &mut Draw) {
    let p = g.p;
    g.poly(&mirrored(&chevron(p.op_l, p.op_r(), p.axis, chevron_rise(p), p.op, tip(p)), p.mid()));
}

fn asterisk(g: &mut Draw) {
    let p = g.p;
    let r = 170.0 + 0.45 * p.op; // the upright arms; the slanted ones are longer, so that the sign is as wide as tall
    let t = p.op;
    stem(g, p.mid(), p.axis - r, p.axis + r, Some(t));
    let (c, s) = (30f64.to_radians().cos(), 30f64.to_radians().sin());
    let rd = 1.13 * r;
    for sign in [1.0, -1.0] {
        g.stroke(&rake(p.mid() - rd * c, p.axis - sign * rd * s, p.mid() + rd * c, p.axis + sign * rd * s, t));
    }
}

/// How far the centre line of / and of the backslash runs across, to each side of the middle. The italic
/// would lean the slash further and stand the backslash up; half of that is taken back.
pub fn slash_run(p: &Params, back: bool) -> f64 {
    if !p.italic() {
        return 158.0;
    }
    158.0 + if back { 40.0 } else { -40.0 }
}

fn slash_(g: &mut Draw) {
    let p = g.p;
    let d = slash_run(p, false);
    slash(g, p.mid() - d, p.br_bot, p.mid() + d, p.br_top, p.stem * 0.9);
}

fn backslash(g: &mut Draw) {
    let p = g.p;
    let d = slash_run(p, true);
    slash(g, p.mid() + d, p.br_bot, p.mid() - d, p.br_top, p.stem * 0.9);
}

fn bar_(g: &mut Draw) {
    let p = g.p;
    stem(g, p.mid(), p.br_bot, p.br_top, Some(p.stem));
}

fn asciicircum(g: &mut Draw) {
    let p = g.p;
    g.poly(&vee(p.mid() - 210.0, p.mid() + 210.0, p.cap * 0.47, p.cap, p.op, tip(p)));
}

fn asciitilde(g: &mut Draw) {
    let p = g.p;
    g.stroke(&wave(p, p.axis, None, None));
}

// ---------------------------------------------------------------------------------------------------------------
// Arithmetic

fn multiply(g: &mut Draw) {
    let p = g.p;
    cross(g, p.mid(), p.axis, 0.75 * half_span(p), None);
}

/// The white between a bar and a dot above or below it.
pub fn dot_gap(p: &Params) -> f64 {
    44.0 + 0.3 * p.op
}

fn divide(g: &mut Draw) {
    let p = g.p;
    let d = p.op / 2.0 + dot_gap(p) + p.dot;
    bar(g, p.axis, None, None, None);
    g.dot(p.mid(), p.axis + d, p.dot);
    g.dot(p.mid(), p.axis - d, p.dot);
}

pub fn plus_minus(g: &mut Draw, turned: bool) {
    let p = g.p;
    let h = rel_rise(p) + 30.0;
    let (mut yb, mut cy) = over(p, h, p.op);
    if turned {
        (yb, cy) = (2.0 * p.axis - yb, 2.0 * p.axis - cy);
    }
    bar(g, yb, None, None, None);
    bar(g, cy, None, None, None);
    stem(g, p.mid(), cy - h, cy + h, None);
}

fn plusminus(g: &mut Draw) {
    plus_minus(g, false);
}

fn minusplus(g: &mut Draw) {
    plus_minus(g, true);
}

fn logicalnot(g: &mut Draw) {
    let p = g.p;
    let h = 0.45 * half_span(p);
    let y = p.axis + h - p.op / 2.0;
    bar(g, y, None, None, None);
    stem(g, p.op_r() - p.op / 2.0, p.axis - h, y, None);
}

fn dot_operator(g: &mut Draw) {
    let p = g.p;
    g.dot(p.mid(), p.axis, 0.78 * p.punct);
}

fn bullet_operator(g: &mut Draw) {
    let p = g.p;
    g.dot(p.mid(), p.axis, 1.1 * p.punct);
}

/// The outer radius of the ring operator.
pub fn small_ring(p: &Params) -> f64 {
    85.0 + 0.55 * p.op
}

fn ring_operator(g: &mut Draw) {
    let p = g.p;
    circle(g, p.mid(), p.axis, small_ring(p), None, Some(0.5 * (p.op + fine(p))));
}

/// The radical: a tick, a short stroke down to a flat vertex, a long stroke up and a bar over what follows.
pub fn radical(g: &mut Draw) {
    let p = g.p;
    let t = p.op;
    let (yb, yt) = (big_bot(p), big_top(p));
    let ym = p.axis + 30.0; // the top of the short stroke
    let apex = tip(p);
    let xv = 218.0; // the vertex
    let (xl, xr) = (92.0, 392.0); // the outer top corners of the two strokes
    let left_dir = pt(xv - apex / 2.0, yb) - pt(xl, ym);
    let right_dir = pt(xr, yt) - pt(xv + apex / 2.0, yb);
    let wl = t * left_dir.abs() / left_dir.y.abs();
    let wr = t * right_dir.abs() / right_dir.y.abs();
    let crotch =
        intersect(pt(xl + wl, ym), left_dir, pt(xr - wr, yt), right_dir).expect("the strokes of the radical meet");
    g.poly(&[
        pt(xl, ym),
        pt(xv - apex / 2.0, yb),
        pt(xv + apex / 2.0, yb),
        pt(xr, yt),
        pt(xr - wr, yt),
        crotch,
        pt(xl + wl, ym),
    ]);
    g.stroke(&hbar(xr - wr, p.width - 26.0, yt - t / 2.0, t));
    g.stroke(&hbar(30.0, xl + wl, ym - t / 2.0, t));
}

fn radical_(g: &mut Draw) {
    radical(g);
}

/// The stroke of the small figures and letters set over or inside a sign.
pub fn small_stroke(p: &Params) -> f64 {
    0.40 * p.op + 12.0
}

pub fn small_three(g: &mut Draw, x0: f64, x1: f64, y0: f64, y1: f64) {
    let p = g.p;
    let t = small_stroke(p);
    let (cx, ym) = ((x0 + x1) / 2.0, (y0 + y1) / 2.0 + 0.03 * (y1 - y0));
    let h = y1 - y0;
    g.stroke(&[
        cut(x0, y1 - 0.20 * h, t, 48.0),
        knot(cx - 2.0, y1 - t / 2.0, t).dir(0.0).k(p.sq),
        knot(x1 - t / 2.0 - 4.0, (y1 + ym) / 2.0, t).dir(-90.0).k(p.sq),
        knot(cx + 4.0, ym, t).pen(90.0).dir(180.0).line(),
        knot(cx - 0.16 * (x1 - x0), ym, t).pen(90.0),
    ]);
    g.stroke(&[
        knot(cx - 0.16 * (x1 - x0), ym, t).pen(90.0).line(),
        knot(cx + 4.0, ym, t).pen(90.0).dir(0.0).k(p.sq),
        knot(x1 - t / 2.0, (y0 + ym) / 2.0, t).dir(-90.0).k(p.sq),
        knot(cx - 2.0, y0 + t / 2.0, t).dir(180.0),
        cut(x0 - 4.0, y0 + 0.20 * h, t, 132.0),
    ]);
}

fn cube_root(g: &mut Draw) {
    let p = g.p;
    radical(g);
    small_three(g, 44.0, 44.0 + 150.0, p.axis + 30.0 + 60.0, big_top(p) - 8.0);
}

/// The outer half-height of the loops of the infinity sign. In a wider cell it grows with the span.
pub fn loop_rise(p: &Params) -> f64 {
    (118.0 + 0.42 * p.op) * p.grown()
}

fn infinity(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (34.0, p.width - 34.0);
    let (cx, cy) = (p.mid(), p.axis);
    let ry = loop_rise(p);
    let t = p.op;
    let tc = 0.92 * fine(p); // thin where the loops cross
    let (xr, xl) = ((cx + x1) / 2.0 + 12.0, (cx + x0) / 2.0 - 12.0);
    let a = 42.0;
    let e = 8.0 * V::unit(a);
    g.stroke(&[
        Knot::at(pt(cx, cy) - e, tc).dir(a),
        knot(xr, cy + ry - t / 2.0, t).dir(0.0).k(p.sq),
        knot(x1 - t / 2.0, cy, t).dir(-90.0).k(p.sq),
        knot(xr, cy - ry + t / 2.0, t).dir(180.0),
        knot(cx, cy, tc).dir(180.0 - a),
        knot(xl, cy + ry - t / 2.0, t).dir(180.0).k(p.sq),
        knot(x0 + t / 2.0, cy, t).dir(-90.0).k(p.sq),
        knot(xl, cy - ry + t / 2.0, t).dir(0.0),
        Knot::at(pt(cx, cy) + e, tc).dir(a),
    ]);
}

fn proportional(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (52.0, p.op_r());
    let cy = p.axis;
    let ry = loop_rise(p);
    let t = p.op;
    let tc = 0.92 * fine(p);
    let cx = x0 + 0.60 * (x1 - x0);
    let xl = (cx + x0) / 2.0 - 14.0;
    let a = 42.0;
    g.stroke(&[
        cut(x1, cy + ry - 0.56 * t, t, 190.0),
        knot(cx, cy, tc).dir(180.0 + a),
        knot(xl, cy - ry + t / 2.0, t).dir(180.0).k(p.sq),
        knot(x0 + t / 2.0, cy, t).dir(90.0).k(p.sq),
        knot(xl, cy + ry - t / 2.0, t).dir(0.0),
        knot(cx, cy, tc).dir(-a),
        cut(x1, cy - ry + 0.56 * t, t, 10.0),
    ]);
}

// ---------------------------------------------------------------------------------------------------------------
// Equality and its relatives

/// The slash through a relation that reaches `rise` above and below the axis: it passes through all of it.
pub fn struck(g: &mut Draw, rise: f64, t: Option<f64>) {
    let p = g.p;
    let dy = rise + 0.9 * p.op;
    strike(g, p.mid(), p.axis, 0.42 * dy, dy, t);
}

fn notequal(g: &mut Draw) {
    let p = g.p;
    g.use_char('=', 0.0, 0.0);
    struck(g, equal_pitch(p) / 2.0 + p.op / 2.0, None);
}

/// The distance between the centre lines of the bars of the identity sign, closer than those of =.
pub fn triple_pitch(p: &Params) -> f64 {
    70.0 + 1.25 * p.op
}

fn equivalence(g: &mut Draw) {
    let p = g.p;
    for k in [-1.0, 0.0, 1.0] {
        bar(g, p.axis + k * triple_pitch(p), None, None, None);
    }
}

fn notequivalence(g: &mut Draw) {
    let p = g.p;
    g.use_char('≡', 0.0, 0.0);
    struck(g, triple_pitch(p) + p.op / 2.0, None);
}

fn tilde_operator(g: &mut Draw) {
    g.use_char('~', 0.0, 0.0);
}

/// The rise of each wave of the almost-equal sign, and the distance between their centres.
pub fn twin_wave(p: &Params) -> (f64, f64) {
    (0.72 * wave_rise(p), 60.0 + 1.35 * p.op)
}

fn approxequal(g: &mut Draw) {
    let p = g.p;
    let (a, pitch) = twin_wave(p);
    g.stroke(&wave(p, p.axis + pitch / 2.0, Some(a), None));
    g.stroke(&wave(p, p.axis - pitch / 2.0, Some(a), None));
}

fn notapproxequal(g: &mut Draw) {
    let p = g.p;
    let (a, pitch) = twin_wave(p);
    g.use_char('≈', 0.0, 0.0);
    struck(g, pitch / 2.0 + a + p.op / 2.0, None);
}

fn asymptotically_equal(g: &mut Draw) {
    let p = g.p;
    let a = 0.85 * wave_rise(p);
    let (yb, cy) = over(p, a + p.op / 2.0, p.op);
    g.stroke(&wave(p, cy, Some(a), None));
    bar(g, yb, None, None, None);
}

fn congruent(g: &mut Draw) {
    let p = g.p;
    let a = 0.80 * wave_rise(p);
    let pitch = 0.9 * triple_pitch(p);
    let (yb, cy) = over(p, a + p.op / 2.0, pitch + p.op);
    g.stroke(&wave(p, cy, Some(a), None));
    bar(g, yb + pitch / 2.0, None, None, None);
    bar(g, yb - pitch / 2.0, None, None, None);
}

pub fn colon_equal(g: &mut Draw, right: bool) {
    let p = g.p;
    let r = 0.80 * p.dot;
    let d = equal_pitch(p) / 2.0;
    let xd = p.op_l - 6.0 + r;
    let x0 = xd + r + 0.5 * rel_gap(p);
    for s in [1.0, -1.0] {
        let (dot_x, a, b) = if right { (p.width - xd, p.op_l, p.width - x0) } else { (xd, x0, p.op_r()) };
        g.dot(dot_x, p.axis + s * d, r);
        bar(g, p.axis + s * d, Some(a), Some(b), None);
    }
}

fn colon_equals(g: &mut Draw) {
    colon_equal(g, false);
}

fn equals_colon(g: &mut Draw) {
    colon_equal(g, true);
}

/// The equals sign lowered and closed up, to leave room for a mark over it. Returns where the mark may
/// start.
pub fn low_equal(g: &mut Draw) -> f64 {
    let p = g.p;
    let pitch = 0.80 * equal_pitch(p);
    let y0 = 34.0 + p.op / 2.0;
    bar(g, y0, None, None, None);
    bar(g, y0 + pitch, None, None, None);
    y0 + pitch + p.op / 2.0 + 0.75 * rel_gap(p)
}

fn delta_equal(g: &mut Draw) {
    let p = g.p;
    let y0 = low_equal(g);
    let t = small_stroke(p) * 1.15;
    let y1 = p.cap + 30.0;
    let (x0, x1) = (p.mid() - 170.0, p.mid() + 170.0);
    g.poly(&vee(x0, x1, y0, y1, t, 0.5 * t));
    g.stroke(&hbar(x0, x1, y0 + t / 2.0, t));
}

fn questioned_equal(g: &mut Draw) {
    let p = g.p;
    let y0 = low_equal(g);
    let t = small_stroke(p) * 1.25;
    let r = 0.62 * p.dot;
    let y1 = p.cap + 36.0;
    let (x0, x1) = (p.mid() - 100.0, p.mid() + 100.0);
    let foot = y0 + 2.0 * r + 0.55 * t + 14.0;
    g.stroke(&[
        cut(x0, y1 - 0.30 * (y1 - foot), t, 52.0),
        knot(p.mid(), y1 - t / 2.0, t).dir(0.0).k(p.sq),
        knot(x1 - t / 2.0, y1 - 0.34 * (y1 - foot), t).dir(-90.0),
        knot(p.mid() + 4.0, foot + 0.24 * (y1 - foot), t).pen(0.0).dir(-90.0).line(),
        knot(p.mid() + 4.0, foot, t).pen(0.0),
    ]);
    g.dot(p.mid() + 4.0, y0 + r, r);
}

fn defined_equal(g: &mut Draw) {
    let p = g.p;
    let y0 = low_equal(g);
    let t = small_stroke(p);
    let y1 = p.cap + 36.0; // the top of d and f
    let xh = y0 + 0.66 * (y1 - y0); // the top of e and of the bowl of d
    let w = 148.0;
    let k = p.sq;
    // d
    let (a, b) = (p.op_l - 8.0, p.op_l - 8.0 + w);
    g.stroke_closed(&ring(a, y0, b - 0.3 * t, xh, t, t, k));
    g.stroke(&vstem(b - t / 2.0, y0, y1, t));
    // e
    let (a, b) = (p.mid() - w / 2.0 + 4.0, p.mid() + w / 2.0 + 2.0);
    let ym = (y0 + xh) / 2.0;
    g.stroke(&[
        knot(b - t / 2.0, ym, t).pen(0.0).dir(90.0).k(k),
        knot((a + b) / 2.0, xh - t / 2.0, t).dir(180.0).k(k),
        knot(a + t / 2.0, ym, t).dir(-90.0).k(k),
        knot((a + b) / 2.0 + 4.0, y0 + t / 2.0, t).dir(0.0),
        cut(b, y0 + 0.30 * (xh - y0), t, 40.0),
    ]);
    g.stroke(&hbar(a + t / 2.0, b - t / 2.0, ym, 0.9 * t));
    // f
    let (a, b) = (p.op_r() + 6.0 - w + 14.0, p.op_r() + 6.0);
    let xs = a + 0.40 * (b - a);
    g.stroke(&elbow(xs, y0, y1, b, t, t, k, 0.42 * (b - a)));
    g.stroke(&hbar(a, b - 10.0, xh - t / 2.0, t));
}

// ---------------------------------------------------------------------------------------------------------------
// Order

fn lessequal(g: &mut Draw) {
    let p = g.p;
    let rise = rel_rise(p);
    let (yb, cy) = over(p, rise, p.op);
    g.poly(&chevron(p.op_l, p.op_r(), cy, rise, p.op, tip(p)));
    bar(g, yb, None, None, None);
}

fn greaterequal(g: &mut Draw) {
    let p = g.p;
    let rise = rel_rise(p);
    let (yb, cy) = over(p, rise, p.op);
    g.poly(&mirrored(&chevron(p.op_l, p.op_r(), cy, rise, p.op, tip(p)), p.mid()));
    bar(g, yb, None, None, None);
}

/// Two chevrons, one inside the other, drawn with the fine stroke so that the white between them stays.
pub fn much(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = 1.06 * fine(p);
    let w = 0.58 * (p.op_r() - p.op_l);
    for x in [p.op_l, p.op_r() - w] {
        let c = chevron(x, x + w, p.axis, chevron_rise(p), t, 0.8 * tip(p));
        g.poly(&if right { mirrored(&c, p.mid()) } else { c });
    }
}

fn muchless(g: &mut Draw) {
    much(g, false);
}

fn muchgreater(g: &mut Draw) {
    much(g, true);
}

/// The chevron of the precedes sign: its strokes leave the point as those of < do and curl away from the
/// axis, to end in flat cuts `rise` above and below `cy`.
pub fn curved_chevron(p: &Params, cy: f64, rise: f64, t: Option<f64>) -> Vec<Knot> {
    let t = t.unwrap_or(p.op);
    let a: f64 = 17.0; // half the angle at the point
    let b: f64 = 62.0; // the direction of the strokes at their ends
    let v = pt(p.op_l + (t / 2.0) / a.to_radians().sin(), cy);
    let run = 60.0;
    let top = cut_pen(p.op_r() - 0.5 * t / b.to_radians().sin(), cy + rise, t, 180.0 + b, 0.0);
    let bot = cut_pen(p.op_r() - 0.5 * t / b.to_radians().sin(), cy - rise, t, -b, 0.0);
    vec![top, Knot::at(v + run * V::unit(a), t).line(), Knot::at(v, t).line(), Knot::at(v + run * V::unit(-a), t), bot]
}

fn precedes(g: &mut Draw) {
    let p = g.p;
    g.stroke(&curved_chevron(p, p.axis, chevron_rise(p) + 14.0, None));
}

fn succeeds(g: &mut Draw) {
    let p = g.p;
    g.stroke(&mirror(&curved_chevron(p, p.axis, chevron_rise(p) + 14.0, None), p.mid()));
}

pub fn less_similar(g: &mut Draw, right: bool) {
    let p = g.p;
    let rise = rel_rise(p);
    let a = 0.62 * wave_rise(p);
    let (yw, cy) = over(p, rise, 2.0 * a + p.op);
    let c = chevron(p.op_l, p.op_r(), cy, rise, p.op, tip(p));
    g.poly(&if right { mirrored(&c, p.mid()) } else { c });
    g.stroke(&wave(p, yw, Some(a), None));
}

fn less_or_similar(g: &mut Draw) {
    less_similar(g, false);
}

fn greater_or_similar(g: &mut Draw) {
    less_similar(g, true);
}

// ---------------------------------------------------------------------------------------------------------------
// Divides and parallel

/// The distance between the centre lines of two parallel upright strokes `t` thick.
pub fn twin_pitch(_p: &Params, t: f64) -> f64 {
    92.0 + 0.95 * t
}

fn divides(g: &mut Draw) {
    let p = g.p;
    stem(g, p.mid(), 0.0, stand_top(p), None);
}

fn notdivides(g: &mut Draw) {
    let p = g.p;
    g.use_char('∣', 0.0, 0.0);
    strike(g, p.mid(), p.axis, 112.0, 112.0, Some(0.5 * (p.op + fine(p))));
}

fn parallel(g: &mut Draw) {
    let p = g.p;
    let d = twin_pitch(p, p.op) / 2.0;
    stem(g, p.mid() - d, 0.0, stand_top(p), None);
    stem(g, p.mid() + d, 0.0, stand_top(p), None);
}

fn notparallel(g: &mut Draw) {
    let p = g.p;
    g.use_char('∥', 0.0, 0.0);
    strike(g, p.mid(), p.axis, 150.0, 132.0, Some(0.5 * (p.op + fine(p))));
}

fn double_bar(g: &mut Draw) {
    let p = g.p;
    let t = 0.9 * p.stem;
    let d = twin_pitch(p, t) / 2.0;
    stem(g, p.mid() - d, p.br_bot, p.br_top, Some(t));
    stem(g, p.mid() + d, p.br_bot, p.br_top, Some(t));
}

// ---------------------------------------------------------------------------------------------------------------
// Logic

/// The thickness of a capital's full diagonal, as the capitals draw A and V.
pub fn cap_diagonal(p: &Params) -> f64 {
    p.cap_stem * 0.95
}

fn forall(g: &mut Draw) {
    let p = g.p;
    let t = cap_diagonal(p);
    let (x0, x1) = (p.sb_round - 30.0, p.width - p.sb_round + 30.0);
    let apex = t * 0.72;
    g.poly(&vee(x0, x1, p.cap, 0.0, t, apex));
    let y = p.cap * 0.75;
    let xb = vee_x(x0, x1, p.cap, 0.0, t, apex, y);
    g.stroke(&hbar(xb, p.width - xb, y, p.cap_hair));
}

pub fn exists(g: &mut Draw) {
    let p = g.p;
    let x = p.width - (p.cxl() + 16.0);
    let left = p.sb_round + 14.0;
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    g.stroke(&hbar(left, x, p.cap - p.cap_hair / 2.0, p.cap_hair));
    g.stroke(&hbar(left + 40.0, x, p.cap * 0.52, p.cap_hair));
    g.stroke(&hbar(left - 6.0, x, p.cap_hair / 2.0, p.cap_hair));
}

fn exists_(g: &mut Draw) {
    exists(g);
}

fn notexists(g: &mut Draw) {
    let p = g.p;
    exists(g);
    strike(g, p.mid() - 14.0, p.cap / 2.0, 150.0, p.cap / 2.0 + 80.0, None);
}

/// The chevron turned: feet on `y0`, the point on `y1`.
pub fn wedge(g: &mut Draw, y0: f64, y1: f64) {
    let p = g.p;
    g.poly(&vee(p.op_l, p.op_r(), y0, y1, p.op, tip(p)));
}

fn logicaland(g: &mut Draw) {
    wedge(g, 0.0, stand_top(g.p));
}

fn logicalor(g: &mut Draw) {
    wedge(g, stand_top(g.p), 0.0);
}

fn xor(g: &mut Draw) {
    let p = g.p;
    bar(g, p.op / 2.0, None, None, None);
    wedge(g, stand_top(p), p.op + rel_gap(p));
}

fn down_tack(g: &mut Draw) {
    let p = g.p;
    bar(g, p.cap - p.op / 2.0, None, None, None);
    stem(g, p.mid(), 0.0, p.cap, None);
}

fn up_tack(g: &mut Draw) {
    let p = g.p;
    bar(g, p.op / 2.0, None, None, None);
    stem(g, p.mid(), 0.0, p.cap, None);
}

/// The turnstile: stems at the left end of the span, bars from them to its right end.
pub fn tack(g: &mut Draw, bars: usize, stems: usize, right: bool) {
    let p = g.p;
    let h = tack_rise(p);
    let pitch = twin_pitch(p, p.op) * 0.88;
    let mut strokes: Vec<Vec<Knot>> =
        (0..stems).map(|i| vstem(p.op_l + p.op / 2.0 + i as f64 * pitch, p.axis - h, p.axis + h, p.op)).collect();
    let x0 = p.op_l + p.op / 2.0 + (stems as f64 - 1.0) * pitch;
    let d = equal_pitch(p) / 2.0;
    let ys = if bars == 1 { vec![p.axis] } else { vec![p.axis + d, p.axis - d] };
    for y in ys {
        strokes.push(hbar(x0, p.op_r(), y, p.op));
    }
    for s in &strokes {
        g.stroke(&if right { mirror(s, p.mid()) } else { s.clone() });
    }
}

fn right_tack(g: &mut Draw) {
    tack(g, 1, 1, false);
}

fn left_tack(g: &mut Draw) {
    tack(g, 1, 1, true);
}

fn models(g: &mut Draw) {
    tack(g, 2, 1, false);
}

fn forces(g: &mut Draw) {
    tack(g, 1, 2, false);
}

// ---------------------------------------------------------------------------------------------------------------
// Sets

pub fn subset(g: &mut Draw, cy: f64, rise: f64, right: bool, t: Option<f64>) {
    let p = g.p;
    let a = arc(p, p.op_l, p.op_r(), cy - rise, cy + rise, t);
    g.stroke(&if right { mirror(&a, p.mid()) } else { a });
}

pub fn element(g: &mut Draw, right: bool) {
    let p = g.p;
    subset(g, p.axis, set_rise(p), right, None);
    let b = hbar(p.op_l + p.op / 2.0, p.op_r(), p.axis, 0.92 * p.op);
    g.stroke(&if right { mirror(&b, p.mid()) } else { b });
}

fn subset_(g: &mut Draw) {
    subset(g, g.p.axis, set_rise(g.p), false, None);
}

fn superset(g: &mut Draw) {
    subset(g, g.p.axis, set_rise(g.p), true, None);
}

fn element_(g: &mut Draw) {
    element(g, false);
}

fn contains(g: &mut Draw) {
    element(g, true);
}

fn notelement(g: &mut Draw) {
    element(g, false);
    struck(g, set_rise(g.p), None);
}

fn notcontains(g: &mut Draw) {
    element(g, true);
    struck(g, set_rise(g.p), None);
}

fn notsubset(g: &mut Draw) {
    subset(g, g.p.axis, set_rise(g.p), false, None);
    struck(g, set_rise(g.p), None);
}

fn notsuperset(g: &mut Draw) {
    subset(g, g.p.axis, set_rise(g.p), true, None);
    struck(g, set_rise(g.p), None);
}

pub fn subset_equal(g: &mut Draw, right: bool) -> (f64, f64) {
    let p = g.p;
    let rise = rel_rise(p);
    let (yb, cy) = over(p, rise, p.op);
    subset(g, cy, rise, right, None);
    bar(g, yb, None, None, None);
    (yb, cy + rise)
}

fn subsetequal(g: &mut Draw) {
    subset_equal(g, false);
}

fn supersetequal(g: &mut Draw) {
    subset_equal(g, true);
}

fn notsubsetequal(g: &mut Draw) {
    let p = g.p;
    let (_, top) = subset_equal(g, false);
    struck(g, top - p.axis, None);
}

fn notsupersetequal(g: &mut Draw) {
    let p = g.p;
    let (_, top) = subset_equal(g, true);
    struck(g, top - p.axis, None);
}

/// The slash through the bar alone, of the signs that say 'but not equal'. It is all that tells ⊊ from ⊆, so it
/// is as long as it can be: up to the relation above the bar, and further down, where nothing is in its way.
pub fn bar_struck(g: &mut Draw, yb: f64) {
    let p = g.p;
    let (up, down) = (p.op / 2.0 + 0.9 * rel_gap(p), p.op / 2.0 + 1.7 * rel_gap(p));
    let d = (up + down) / 2.0;
    strike(g, p.mid(), yb + (up - down) / 2.0, 0.62 * d, d, Some(0.5 * (p.op + fine(p))));
}

fn subsetnotequal(g: &mut Draw) {
    let (yb, _) = subset_equal(g, false);
    bar_struck(g, yb);
}

fn supersetnotequal(g: &mut Draw) {
    let (yb, _) = subset_equal(g, true);
    bar_struck(g, yb);
}

pub fn cup(g: &mut Draw, down: bool) {
    let p = g.p;
    let a = transposed(&arc(p, -p.over, stand_top(p), p.op_l, p.op_r(), None));
    g.stroke(&if down { flip(&a, p.axis) } else { a });
}

fn union(g: &mut Draw) {
    cup(g, false);
}

fn intersection(g: &mut Draw) {
    cup(g, true);
}

fn multiset_union(g: &mut Draw) {
    let p = g.p;
    cup(g, false);
    let t = fine(p);
    let h = 0.42 * half_span(p);
    let cy = p.axis + 0.15 * half_span(p);
    g.stroke(&hbar(p.mid() - h, p.mid() + h, cy, t));
    g.stroke(&vstem(p.mid(), cy - h, cy + h, t));
}

/// A ring with a slash that runs out of it on both sides. The ring is no taller than it is wide: in the fixed
/// pitch's cell that makes it a circle, well short of the slashed zero it would otherwise be taken for.
fn emptyset(g: &mut Draw) {
    let p = g.p;
    let rx = half_span(p) - 14.0;
    let ry = (0.5 * (p.xh + 2.0 * p.over) + 0.1 * p.op).min(rx);
    circle(g, p.mid(), p.axis, rx, Some(ry), None);
    let dy = ry + 0.9 * p.op;
    strike(g, p.mid(), p.axis, 0.56 * dy, dy, Some(0.5 * (p.op + fine(p))));
}

fn setminus(g: &mut Draw) {
    let p = g.p;
    let h = half_span(p);
    slash(g, p.mid() + 0.56 * h, p.axis - h, p.mid() - 0.56 * h, p.axis + h, p.op);
}

pub fn square_cup(g: &mut Draw, down: bool) {
    let p = g.p;
    let t = p.op;
    let (xl, xr) = (p.op_l + t / 2.0, p.op_r() - t / 2.0);
    let top = stand_top(p);
    let k = vec![
        knot(xl, top, t).pen(0.0).line(),
        knot(xl, t / 2.0, t).line(),
        knot(xr, t / 2.0, t).line(),
        knot(xr, top, t).pen(0.0),
    ];
    g.stroke(&if down { flip(&k, p.axis) } else { k });
}

fn square_cup_(g: &mut Draw) {
    square_cup(g, false);
}

fn square_cap(g: &mut Draw) {
    square_cup(g, true);
}

pub fn square_image(g: &mut Draw, cy: f64, rise: f64, right: bool) {
    let p = g.p;
    let t = p.op;
    let xs = p.op_l + t / 2.0;
    let k = vec![
        knot(p.op_r(), cy + rise - t / 2.0, t).pen(90.0).line(),
        knot(xs, cy + rise - t / 2.0, t).line(),
        knot(xs, cy - rise + t / 2.0, t).line(),
        knot(p.op_r(), cy - rise + t / 2.0, t).pen(90.0),
    ];
    g.stroke(&if right { mirror(&k, p.mid()) } else { k });
}

fn square_image_(g: &mut Draw) {
    square_image(g, g.p.axis, set_rise(g.p), false);
}

fn square_original(g: &mut Draw) {
    square_image(g, g.p.axis, set_rise(g.p), true);
}

pub fn square_image_equal(g: &mut Draw, right: bool) {
    let p = g.p;
    let rise = rel_rise(p);
    let (yb, cy) = over(p, rise, p.op);
    square_image(g, cy, rise, right);
    bar(g, yb, None, None, None);
}

fn square_image_equal_(g: &mut Draw) {
    square_image_equal(g, false);
}

fn square_original_equal(g: &mut Draw) {
    square_image_equal(g, true);
}

// ---------------------------------------------------------------------------------------------------------------
// Circled and squared operators

/// The ring of the circled operators: a little beyond the span, as round shapes are. Returns the radius of
/// its inner edge.
pub fn big_ring(g: &mut Draw) -> f64 {
    let p = g.p;
    let r = half_span(p) + p.over;
    circle(g, p.mid(), p.axis, r, None, None);
    r - p.op
}

fn circled_plus(g: &mut Draw) {
    let p = g.p;
    let r = big_ring(g) + 4.0;
    g.stroke(&hbar(p.mid() - r, p.mid() + r, p.axis, fine(p)));
    g.stroke(&vstem(p.mid(), p.axis - r, p.axis + r, fine(p)));
}

fn circled_minus(g: &mut Draw) {
    let p = g.p;
    let r = big_ring(g) + 4.0;
    g.stroke(&hbar(p.mid() - r, p.mid() + r, p.axis, fine(p)));
}

fn circled_times(g: &mut Draw) {
    let p = g.p;
    let r = big_ring(g);
    cross(g, p.mid(), p.axis, 0.70 * r, Some(fine(p)));
}

fn circled_slash(g: &mut Draw) {
    let p = g.p;
    let r = big_ring(g);
    strike(g, p.mid(), p.axis, 0.70 * r, 0.70 * r, Some(fine(p)));
}

fn circled_dot(g: &mut Draw) {
    let p = g.p;
    big_ring(g);
    g.dot(p.mid(), p.axis, 0.78 * p.punct);
}

fn circled_ring(g: &mut Draw) {
    let p = g.p;
    let r = big_ring(g);
    circle(g, p.mid(), p.axis, 0.62 * r, None, Some(0.8 * fine(p)));
}

fn circled_asterisk(g: &mut Draw) {
    let p = g.p;
    let r = 0.74 * big_ring(g);
    let t = 0.8 * fine(p);
    g.stroke(&vstem(p.mid(), p.axis - r, p.axis + r, t));
    let (c, s) = (30f64.to_radians().cos(), 30f64.to_radians().sin());
    for sign in [1.0, -1.0] {
        g.stroke(&rake(p.mid() - r * c, p.axis - sign * r * s, p.mid() + r * c, p.axis + sign * r * s, t));
    }
}

/// The box of the squared operators: the span, squared on the axis. Returns half its inner width.
pub fn big_box(g: &mut Draw) -> f64 {
    let p = g.p;
    let h = half_span(p);
    outline(g, &box_(p.mid() - h, p.axis - h, p.mid() + h, p.axis + h), None);
    h - p.op
}

fn squared_plus(g: &mut Draw) {
    let p = g.p;
    let r = big_box(g) + 4.0;
    g.stroke(&hbar(p.mid() - r, p.mid() + r, p.axis, fine(p)));
    g.stroke(&vstem(p.mid(), p.axis - r, p.axis + r, fine(p)));
}

fn squared_minus(g: &mut Draw) {
    let p = g.p;
    let r = big_box(g) + 4.0;
    g.stroke(&hbar(p.mid() - r, p.mid() + r, p.axis, fine(p)));
}

fn squared_times(g: &mut Draw) {
    let p = g.p;
    let r = big_box(g);
    cross(g, p.mid(), p.axis, r + 4.0, Some(fine(p)));
}

fn squared_dot(g: &mut Draw) {
    let p = g.p;
    big_box(g);
    g.dot(p.mid(), p.axis, 0.78 * p.punct);
}

// ---------------------------------------------------------------------------------------------------------------
// Dots, stars and small shapes

/// Dots at `places`, counted from the middle of the cell on the axis. In a wider cell they stand as much
/// further apart as the span is wider.
pub fn dots(g: &mut Draw, places: &[(f64, f64)], r: Option<f64>) {
    let p = g.p;
    let r = r.unwrap_or(0.5 * p.punct + 16.0);
    let k = p.grown();
    for &(dx, dy) in places {
        g.dot(p.mid() + k * dx, p.axis + k * dy, r);
    }
}

fn therefore(g: &mut Draw) {
    let r = g.p.dot;
    dots(g, &[(0.0, 150.0), (-170.0, -150.0), (170.0, -150.0)], Some(r));
}

fn because(g: &mut Draw) {
    let r = g.p.dot;
    dots(g, &[(0.0, -150.0), (-170.0, 150.0), (170.0, 150.0)], Some(r));
}

fn midline_ellipsis(g: &mut Draw) {
    dots(g, &[(-200.0, 0.0), (0.0, 0.0), (200.0, 0.0)], None);
}

fn vertical_ellipsis(g: &mut Draw) {
    dots(g, &[(0.0, -250.0), (0.0, 0.0), (0.0, 250.0)], None);
}

fn up_diagonal_ellipsis(g: &mut Draw) {
    dots(g, &[(-200.0, -200.0), (0.0, 0.0), (200.0, 200.0)], None);
}

fn down_diagonal_ellipsis(g: &mut Draw) {
    dots(g, &[(-200.0, 200.0), (0.0, 0.0), (200.0, -200.0)], None);
}

fn end_of_proof(g: &mut Draw) {
    let p = g.p;
    g.rect(p.mid() - 150.0, 0.0, p.mid() + 150.0, p.xh);
}

fn star_operator(g: &mut Draw) {
    let p = g.p;
    let ro = (190.0 + 0.3 * p.op) * p.grown();
    let ri = 0.44 * ro;
    let c = pt(p.mid(), p.axis - 0.05 * ro);
    let points: Vec<V> =
        (0..10).map(|i| c + (if i % 2 == 0 { ro } else { ri }) * V::unit(90.0 + 36.0 * i as f64)).collect();
    g.poly(&points);
}

fn diamond_operator(g: &mut Draw) {
    let p = g.p;
    let r = 190.0 + 0.45 * p.op;
    outline(
        g,
        &[pt(p.mid() + r, p.axis), pt(p.mid(), p.axis + r), pt(p.mid() - r, p.axis), pt(p.mid(), p.axis - r)],
        None,
    );
}

pub fn bowtie(g: &mut Draw, left: bool, right: bool) {
    let p = g.p;
    let t = p.op;
    let h = chevron_rise(p) * round_growth(p);
    let td = 0.5 * (p.op + fine(p));
    let (x0, x1) = (p.op_l, p.op_r());
    let w = rake(x0, 0.0, x1, 2.0 * h, td)[0].w; // the height of a diagonal's vertical cut
    let dy = h - w / 2.0;
    g.stroke(&rake(x0, p.axis - dy, x1, p.axis + dy, td));
    g.stroke(&rake(x0, p.axis + dy, x1, p.axis - dy, td));
    if left {
        stem(g, x0 + t / 2.0, p.axis - h, p.axis + h, Some(t));
    }
    if right {
        stem(g, x1 - t / 2.0, p.axis - h, p.axis + h, Some(t));
    }
}

fn bowtie_(g: &mut Draw) {
    bowtie(g, true, true);
}

fn left_semijoin(g: &mut Draw) {
    bowtie(g, true, false);
}

fn right_semijoin(g: &mut Draw) {
    bowtie(g, false, true);
}

/// The outline of a triangle that points left (or right): the chevron closed.
pub fn triangle(g: &mut Draw, cy: f64, rise: f64, right: bool) {
    let p = g.p;
    let mut pts = vec![pt(p.op_l, cy), pt(p.op_r(), cy - rise), pt(p.op_r(), cy + rise)];
    if right {
        pts = mirrored(&pts, p.mid());
        pts.reverse();
    }
    outline(g, &pts, None);
}

fn normal_subgroup(g: &mut Draw) {
    triangle(g, g.p.axis, chevron_rise(g.p) * relation_growth(g.p), false);
}

fn contains_normal_subgroup(g: &mut Draw) {
    triangle(g, g.p.axis, chevron_rise(g.p) * relation_growth(g.p), true);
}

pub fn triangle_equal(g: &mut Draw, right: bool) {
    let p = g.p;
    let rise = rel_rise(p);
    let (yb, cy) = over(p, rise, p.op);
    triangle(g, cy, rise, right);
    bar(g, yb, None, None, None);
}

fn normal_subgroup_equal(g: &mut Draw) {
    triangle_equal(g, false);
}

fn contains_normal_subgroup_equal(g: &mut Draw) {
    triangle_equal(g, true);
}

pub fn register(reg: &mut Registry) {
    reg.module("operators");
    reg.ch('-', hyphen);
    reg.ch('−', minus);
    reg.ch('+', plus);
    reg.ch('=', equal);
    reg.ch('<', less);
    reg.ch('>', greater);
    reg.ch('*', asterisk);
    reg.ch('/', slash_);
    reg.ch('\\', backslash);
    reg.ch('|', bar_);
    reg.ch('^', asciicircum);
    reg.ch('~', asciitilde);
    reg.ch('×', multiply);
    reg.ch('÷', divide);
    reg.ch('±', plusminus);
    reg.ch('∓', minusplus);
    reg.ch('¬', logicalnot);
    reg.ch('⋅', dot_operator);
    reg.ch('∙', bullet_operator);
    reg.ch('∘', ring_operator);
    reg.ch('√', radical_);
    reg.ch('∛', cube_root);
    reg.ch('∞', infinity);
    reg.ch('∝', proportional);
    reg.ch('≠', notequal);
    reg.ch('≡', equivalence);
    reg.ch('≢', notequivalence);
    reg.ch('∼', tilde_operator);
    reg.ch('≈', approxequal);
    reg.ch('≉', notapproxequal);
    reg.ch('≃', asymptotically_equal);
    reg.ch('≅', congruent);
    reg.ch('≔', colon_equals);
    reg.ch('≕', equals_colon);
    reg.ch('≜', delta_equal);
    reg.ch('≟', questioned_equal);
    reg.ch('≝', defined_equal);
    reg.ch('≤', lessequal);
    reg.ch('≥', greaterequal);
    reg.ch('≪', muchless);
    reg.ch('≫', muchgreater);
    reg.ch('≺', precedes);
    reg.ch('≻', succeeds);
    reg.ch('≲', less_or_similar);
    reg.ch('≳', greater_or_similar);
    reg.ch('∣', divides);
    reg.ch('∤', notdivides);
    reg.ch('∥', parallel);
    reg.ch('∦', notparallel);
    reg.ch('‖', double_bar);
    reg.ch('∀', forall);
    reg.ch('∃', exists_);
    reg.ch('∄', notexists);
    reg.ch('∧', logicaland);
    reg.ch('∨', logicalor);
    reg.ch('⊻', xor);
    reg.ch('⊤', down_tack);
    reg.ch('⊥', up_tack);
    reg.ch('⊢', right_tack);
    reg.ch('⊣', left_tack);
    reg.ch('⊨', models);
    reg.ch('⊩', forces);
    reg.ch('⊂', subset_);
    reg.ch('⊃', superset);
    reg.ch('∈', element_);
    reg.ch('∋', contains);
    reg.ch('∉', notelement);
    reg.ch('∌', notcontains);
    reg.ch('⊄', notsubset);
    reg.ch('⊅', notsuperset);
    reg.ch('⊆', subsetequal);
    reg.ch('⊇', supersetequal);
    reg.ch('⊈', notsubsetequal);
    reg.ch('⊉', notsupersetequal);
    reg.ch('⊊', subsetnotequal);
    reg.ch('⊋', supersetnotequal);
    reg.ch('∪', union);
    reg.ch('∩', intersection);
    reg.ch('⊎', multiset_union);
    reg.ch('∅', emptyset);
    reg.ch('∖', setminus);
    reg.ch('⊔', square_cup_);
    reg.ch('⊓', square_cap);
    reg.ch('⊏', square_image_);
    reg.ch('⊐', square_original);
    reg.ch('⊑', square_image_equal_);
    reg.ch('⊒', square_original_equal);
    reg.ch('⊕', circled_plus);
    reg.ch('⊖', circled_minus);
    reg.ch('⊗', circled_times);
    reg.ch('⊘', circled_slash);
    reg.ch('⊙', circled_dot);
    reg.ch('⊚', circled_ring);
    reg.ch('⊛', circled_asterisk);
    reg.ch('⊞', squared_plus);
    reg.ch('⊟', squared_minus);
    reg.ch('⊠', squared_times);
    reg.ch('⊡', squared_dot);
    reg.ch('∴', therefore);
    reg.ch('∵', because);
    reg.ch('⋯', midline_ellipsis);
    reg.ch('⋮', vertical_ellipsis);
    reg.ch('⋰', up_diagonal_ellipsis);
    reg.ch('⋱', down_diagonal_ellipsis);
    reg.ch('∎', end_of_proof);
    reg.ch('⋆', star_operator);
    reg.ch('⋄', diamond_operator);
    reg.ch('⋈', bowtie_);
    reg.ch('⋉', left_semijoin);
    reg.ch('⋊', right_semijoin);
    reg.ch('⊲', normal_subgroup);
    reg.ch('⊳', contains_normal_subgroup);
    reg.ch('⊴', normal_subgroup_equal);
    reg.ch('⊵', contains_normal_subgroup_equal);
}
