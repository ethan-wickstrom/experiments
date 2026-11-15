//! Uppercase Latin.
//!
//! Plain grotesque capitals on the capital stems `p.cxl()` and `p.cxr()`. Verticals are `p.cap_stem` thick, bars
//! and the tops and bottoms of bowls `p.cap_hair`; diagonals are a stated fraction of one of them. Round sides stop
//! `ox(p)` short of the cell's edge. A letter with a stem on the left and an open or round right side (B D E F K L
//! P R) sits a little right of H's stem, so that its visual centre is the cell's.
//!
//! Straight strokes are placed by their corners, not by their centre lines, because a diagonal's corners are what
//! must meet a stem, a bar or the cell (`span`, `reach`, `vee`). Those parts know the italic's slant, so a
//! diagonal keeps its thickness when the skeleton leans.

#![allow(non_snake_case)]

use rachis_kernel::geom::intersect;
use rachis_kernel::{Draw, Fit, Knot, Params, Registry, V, knot, pt};

use crate::parts::{cut, dbowl, hbar, ring, vstem};

// ---------------------------------------------------------------------------------------------------------------
// Measurements this group derives from the parameters.

/// How far the round side of a capital (O, Q, D; C and G on the left) stays from the cell's edge.
fn ox(p: &Params) -> f64 {
    p.sb_round - 12.0
}

/// The squareness of a capital's bowls: a little squarer than the lowercase's, because they are taller.
fn sqc(p: &Params) -> f64 {
    p.sq + 0.02
}

/// The thickness of a capital's full diagonal (A K V X Y Z, the leg of R): it looks as heavy as a stem.
fn dt(p: &Params) -> f64 {
    p.cap_stem * 0.95
}

/// How far to the right an italic moves a point for each unit of height.
fn lean(p: &Params) -> f64 {
    p.slant.to_radians().tan()
}

// ---------------------------------------------------------------------------------------------------------------
// Parts only the capitals use.

/// The length `w` of the horizontal cut of a straight stroke that is `t` thick once the master's slant is
/// applied, and whose centre line advances `dx - c * w` while it climbs `dy` (negative when it descends).
/// `c` is 0 when `dx` is measured along one edge of the stroke, 1 when it is measured from the outer end of
/// one cut to the outer end of the other (the stroke lies inside that box), -1 when it is measured between their
/// inner ends, and a half or minus a half when it is measured from the middle of one cut to an end of the other.
fn cut_len(p: &Params, dx: f64, dy: f64, t: f64, c: f64) -> f64 {
    let dx = dx + lean(p) * dy;
    let a = dy * dy - c * c * t * t;
    let b = c * t * t * dx;
    (-b + (b * b + a * t * t * (dx * dx + dy * dy)).sqrt()) / a
}

/// A straight stroke `t` thick, cut flat at both ends, from the height `ya` to the height `yb`. Its cut at
/// `ya` has its left end (`sa` = -1) or its right end (`sa` = 1) at `xa`; likewise `xb` and `sb`. With
/// equal sides, one edge of the stroke runs from (xa, ya) to (xb, yb); with opposite sides the stroke fills the
/// box between the two points from corner to corner.
fn span(p: &Params, xa: f64, ya: f64, sa: f64, xb: f64, yb: f64, sb: f64, t: f64) -> Vec<Knot> {
    let w = cut_len(p, xb - xa, yb - ya, t, (sb - sa) / 2.0);
    vec![knot(xa - sa * w / 2.0, ya, w).pen(0.0).line(), knot(xb - sb * w / 2.0, yb, w).pen(0.0)]
}

/// A straight stroke `t` thick, cut flat at both ends, whose first cut is centred on (xc, yc), where another
/// stroke hides it, and whose cut at the height `ye` has its left end (`se` = -1) or its right end (`se` = 1)
/// at `xe`.
fn reach(p: &Params, xc: f64, yc: f64, xe: f64, se: f64, ye: f64, t: f64) -> Vec<Knot> {
    let w = cut_len(p, xe - xc, ye - yc, t, se / 2.0);
    vec![knot(xc, yc, w).pen(0.0).line(), knot(xe - se * w / 2.0, ye, w).pen(0.0)]
}

/// The lengths of the cuts of the left and the right stroke of `vee`. They differ only in an italic.
fn vee_cuts(p: &Params, x0: f64, x1: f64, y_top: f64, y_bot: f64, t: f64, apex: f64) -> (f64, f64) {
    let mid = (x0 + x1) / 2.0;
    let dy = y_bot - y_top;
    (cut_len(p, mid - apex / 2.0 - x0, dy, t, 0.0), cut_len(p, mid + apex / 2.0 - x1, dy, t, 0.0))
}

/// The polygon of a V, as `parts::vee`: outer corners at `x0` and `x1` on `y_top`, strokes `t` thick,
/// a flat vertex `apex` wide on `y_bot`; a caret when `y_bot` is above `y_top`. Unlike `parts::vee` it
/// keeps both strokes `t` thick in an italic, where one of them leans further than the other.
fn vee(p: &Params, x0: f64, x1: f64, y_top: f64, y_bot: f64, t: f64, apex: f64) -> Vec<V> {
    let mid = (x0 + x1) / 2.0;
    let (wl, wr) = vee_cuts(p, x0, x1, y_top, y_bot, t, apex);
    let (tl, tr) = (pt(x0, y_top), pt(x1, y_top));
    let (vl, vr) = (pt(mid - apex / 2.0, y_bot), pt(mid + apex / 2.0, y_bot));
    let crotch = intersect(tl + pt(wl, 0.0), vl - tl, tr - pt(wr, 0.0), vr - tr).expect("the strokes of a V meet");
    vec![tl, vl, vr, tr, tr - pt(wr, 0.0), crotch, tl + pt(wl, 0.0)]
}

/// The x of the centre lines of the two strokes of `vee` at the height `y`: where a crossbar ends.
fn vee_x(p: &Params, x0: f64, x1: f64, y_top: f64, y_bot: f64, t: f64, apex: f64, y: f64) -> (f64, f64) {
    let mid = (x0 + x1) / 2.0;
    let (wl, wr) = vee_cuts(p, x0, x1, y_top, y_bot, t, apex);
    let f = (y - y_top) / (y_bot - y_top);
    (x0 + wl / 2.0 + f * (mid - apex / 2.0 - x0), x1 - wr / 2.0 + f * (mid + apex / 2.0 - x1))
}

/// Where the line through the two points of `a` crosses the line through the two points of `b`.
fn meet(a: (V, V), b: (V, V)) -> V {
    intersect(a.0, a.1 - a.0, b.0, b.1 - b.0).expect("the lines meet")
}

// ---------------------------------------------------------------------------------------------------------------
// stems and bars

fn H(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.cxl(), 0.0, p.cap, p.cap_stem));
    g.stroke(&vstem(p.cxr(), 0.0, p.cap, p.cap_stem));
    g.stroke(&hbar(p.cxl(), p.cxr(), p.cap * 0.51, p.cap_hair));
}

fn I(g: &mut Draw) {
    let p = g.p;
    // the serifs are as long as the foot of the figure one
    g.stroke(&vstem(p.mid(), 0.0, p.cap, p.cap_stem));
    g.stroke(&hbar(p.mid() - 196.0, p.mid() + 196.0, p.cap - p.cap_hair / 2.0, p.cap_hair));
    g.stroke(&hbar(p.mid() - 196.0, p.mid() + 196.0, p.cap_hair / 2.0, p.cap_hair));
}

fn T(g: &mut Draw) {
    let p = g.p;
    let x0 = p.sb_round - 20.0;
    g.stroke(&vstem(p.mid(), 0.0, p.cap, p.cap_stem));
    g.stroke(&hbar(x0, p.width - x0, p.cap - p.cap_hair / 2.0, p.cap_hair));
}

fn L(g: &mut Draw) {
    let p = g.p;
    let x = p.cxl() + 34.0;
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    g.stroke(&hbar(x, p.width - p.sb_round - 2.0, p.cap_hair / 2.0, p.cap_hair));
}

fn E(g: &mut Draw) {
    let p = g.p;
    let x = p.cxl() + 16.0;
    let right = p.width - p.sb_round - 14.0;
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    g.stroke(&hbar(x, right, p.cap - p.cap_hair / 2.0, p.cap_hair));
    g.stroke(&hbar(x, right - 40.0, p.cap * 0.52, p.cap_hair));
    g.stroke(&hbar(x, right + 6.0, p.cap_hair / 2.0, p.cap_hair));
}

fn F(g: &mut Draw) {
    let p = g.p;
    let x = p.cxl() + 24.0;
    let right = p.width - p.sb_round - 8.0;
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    g.stroke(&hbar(x, right, p.cap - p.cap_hair / 2.0, p.cap_hair));
    g.stroke(&hbar(x, right - 44.0, p.cap * 0.49, p.cap_hair));
}

// ---------------------------------------------------------------------------------------------------------------
// rounds

fn O(g: &mut Draw) {
    let p = g.p;
    let x0 = ox(p);
    g.stroke_closed(&ring(x0, -p.over, p.width - x0, p.cap + p.over, p.cap_stem, p.cap_hair, sqc(p)));
}

fn Q(g: &mut Draw) {
    let p = g.p;
    let x0 = ox(p);
    g.stroke_closed(&ring(x0, -p.over, p.width - x0, p.cap + p.over, p.cap_stem, p.cap_hair, sqc(p)));
    // the tail starts a little inside the counter, so that it crosses the bowl, and ends below the baseline
    g.stroke(&reach(
        p,
        p.mid() + 26.0,
        p.cap_hair + 0.075 * p.cap,
        p.mid() + 176.0,
        1.0,
        -0.20 * p.cap,
        p.cap_hair * 1.04,
    ));
}

fn C(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (ox(p) + 14.0, p.width - ox(p) - 12.0);
    let cx = (x0 + x1) / 2.0 + 14.0;
    let (top, bot) = (p.cap + p.over - p.cap_hair / 2.0, -p.over + p.cap_hair / 2.0);
    g.stroke(&[
        cut(x1, p.cap - 148.0, p.cap_hair * 1.04, 138.0),
        knot(cx, top, p.cap_hair).dir(180.0).k(sqc(p)),
        knot(x0 + p.cap_stem / 2.0, p.cap / 2.0, p.cap_stem).dir(-90.0).k(sqc(p)),
        knot(cx, bot, p.cap_hair).dir(0.0),
        cut(x1 + 4.0, 144.0, p.cap_hair * 1.04, 40.0),
    ]);
}

fn G(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (ox(p) + 6.0, p.width - ox(p) - 16.0);
    let cx = (x0 + x1) / 2.0 + 8.0;
    let (top, bot) = (p.cap + p.over - p.cap_hair / 2.0, -p.over + p.cap_hair / 2.0);
    let xs = x1 - p.cap_stem / 2.0; // the spur: a short stem that rises from the bowl to the bar
    let bar = p.cap * 0.44;
    g.stroke(&[
        cut(x1 - 6.0, p.cap - 148.0, p.cap_hair * 1.04, 138.0),
        knot(cx, top, p.cap_hair).dir(180.0).k(sqc(p)),
        knot(x0 + p.cap_stem / 2.0, p.cap / 2.0, p.cap_stem).dir(-90.0).k(sqc(p)),
        knot(cx, bot, p.cap_hair).dir(0.0).k(sqc(p)),
        knot(xs, bot + 0.24 * p.cap, p.cap_stem).pen(0.0).dir(90.0).line(),
        knot(xs, bar + p.cap_hair / 2.0, p.cap_stem).pen(0.0),
    ]);
    g.stroke(&hbar(xs - 0.42 * (x1 - x0), xs, bar, p.cap_hair));
}

fn S(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (ox(p) + 20.0, p.width - ox(p) - 20.0);
    let cx = (x0 + x1) / 2.0;
    let (top, bot) = (p.cap + p.over - p.cap_hair / 2.0, -p.over + p.cap_hair / 2.0);
    let w = p.cap_stem;
    g.stroke(&[
        cut(x1 - 10.0, p.cap - 150.0, p.cap_hair * 1.04, 140.0),
        knot(cx + 4.0, top, p.cap_hair).dir(180.0).k(p.sq),
        knot(x0 + w / 2.0 + 8.0, p.cap * 0.745, w).dir(-90.0),
        knot(cx, p.cap * 0.515, w * 1.02).dir(-27.0),
        knot(x1 - w / 2.0, p.cap * 0.262, w).dir(-90.0).k(p.sq),
        knot(cx - 4.0, bot, p.cap_hair).dir(180.0),
        cut(x0 - 8.0, 148.0, p.cap_hair * 1.04, 140.0),
    ]);
}

fn U(g: &mut Draw) {
    let p = g.p;
    let bot = -p.over + p.cap_hair / 2.0;
    let ys = bot + 1.08 * (p.mid() - p.cxl()); // where the stems end and the bottom begins
    g.stroke(&[
        knot(p.cxl(), p.cap, p.cap_stem).pen(0.0).line(),
        knot(p.cxl(), ys, p.cap_stem).pen(0.0).dir(-90.0).k(sqc(p)),
        knot(p.mid(), bot, p.cap_hair).dir(0.0).k(sqc(p)),
        knot(p.cxr(), ys, p.cap_stem).pen(0.0).dir(90.0).line(),
        knot(p.cxr(), p.cap, p.cap_stem).pen(0.0),
    ]);
}

fn J(g: &mut Draw) {
    let p = g.p;
    let x = p.cxr() - 22.0;
    let x_end = ox(p) + 22.0;
    let yc = p.cap_hair / 2.0;
    // the elbow of j, wider than it is high
    let (rx, ry) = (0.66 * (x - x_end), 0.31 * p.cap);
    g.stroke(&[
        knot(x, p.cap, p.cap_stem).pen(0.0).line(),
        knot(x, yc + ry, p.cap_stem).pen(0.0).dir(-90.0).k(sqc(p)),
        knot(x - rx, yc, p.cap_hair).pen(90.0).dir(180.0).line(),
        knot(x_end, yc, p.cap_hair).pen(90.0),
    ]);
    g.stroke(&hbar(x - 0.60 * (x - x_end), x, p.cap - p.cap_hair / 2.0, p.cap_hair));
}

// ---------------------------------------------------------------------------------------------------------------
// stems with bowls

fn D(g: &mut Draw) {
    let p = g.p;
    let x = p.cxl() + 6.0;
    let edge = p.width - ox(p);
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    g.stroke(&dbowl(x, edge, 0.0, p.cap, p.cap_stem, p.cap_hair, sqc(p), 0.26 * (edge - x)));
}

fn P(g: &mut Draw) {
    let p = g.p;
    let x = p.cxl() + 16.0;
    let edge = p.width - ox(p) - 4.0;
    let waist = p.cap * 0.43;
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    g.stroke(&dbowl(x, edge, waist - p.cap_hair / 2.0, p.cap, p.cap_stem, p.cap_hair, sqc(p), 0.36 * (edge - x)));
}

fn R(g: &mut Draw) {
    let p = g.p;
    let x = p.cxl() + 8.0;
    let edge = p.width - ox(p) - 22.0;
    let waist = p.cap * 0.455;
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    g.stroke(&dbowl(x, edge, waist - p.cap_hair / 2.0, p.cap, p.cap_stem, p.cap_hair, sqc(p), 0.36 * (edge - x)));
    g.stroke(&reach(p, p.mid() + 4.0, waist, p.width - ox(p) + 2.0, 1.0, 0.0, dt(p)));
}

fn B(g: &mut Draw) {
    let p = g.p;
    let x = p.cxl() + 8.0;
    let (upper, lower) = (p.width - ox(p) - 38.0, p.width - ox(p) - 10.0);
    let waist = p.cap * 0.53;
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    g.stroke(&dbowl(
        x,
        upper,
        waist - p.cap_hair / 2.0,
        p.cap,
        p.cap_stem * 0.96,
        p.cap_hair,
        sqc(p),
        0.42 * (upper - x),
    ));
    g.stroke(&dbowl(x, lower, 0.0, waist + p.cap_hair / 2.0, p.cap_stem, p.cap_hair, sqc(p), 0.42 * (lower - x)));
}

// ---------------------------------------------------------------------------------------------------------------
// diagonals

fn A(g: &mut Draw) {
    let p = g.p;
    let t = dt(p);
    let (x0, x1) = (p.sb_round - 30.0, p.width - p.sb_round + 30.0);
    let apex = t * 0.72;
    g.poly(&vee(p, x0, x1, 0.0, p.cap, t, apex));
    let y = p.cap * 0.25;
    let (xl, xr) = vee_x(p, x0, x1, 0.0, p.cap, t, apex, y);
    g.stroke(&hbar(xl, xr, y, p.cap_hair));
}

fn V(g: &mut Draw) {
    let p = g.p;
    let t = dt(p);
    let x0 = p.sb_round - 28.0;
    g.poly(&vee(p, x0, p.width - x0, p.cap, 0.0, t, t * 0.80));
}

fn Y(g: &mut Draw) {
    let p = g.p;
    let x0 = p.sb_round - 30.0;
    let yj = p.cap * 0.40; // where the arms reach the stem
    g.poly(&vee(p, x0, p.width - x0, p.cap, yj, dt(p), p.cap_stem));
    g.stroke(&vstem(p.mid(), 0.0, yj + 0.3 * p.cap_stem, p.cap_stem));
}

fn X(g: &mut Draw) {
    let p = g.p;
    let t = dt(p);
    let (x0, x1) = (p.sb_round - 22.0, p.width - p.sb_round + 22.0);
    g.stroke(&span(p, x0, 0.0, -1.0, x1 - 8.0, p.cap, 1.0, t));
    g.stroke(&span(p, x1, 0.0, 1.0, x0 + 8.0, p.cap, -1.0, t));
}

fn Z(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (p.sb_round + 4.0, p.width - p.sb_round - 4.0);
    g.stroke(&hbar(x0 + 8.0, x1, p.cap - p.cap_hair / 2.0, p.cap_hair));
    g.stroke(&hbar(x0, x1 + 6.0, p.cap_hair / 2.0, p.cap_hair));
    g.stroke(&span(p, x0, 0.0, -1.0, x1, p.cap, 1.0, dt(p)));
}

fn K(g: &mut Draw) {
    let p = g.p;
    let x = p.cxl() + 4.0;
    let t = dt(p);
    let xe = p.width - p.sb_round + 26.0;
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    // the arm starts on a vertical cut inside the stem and ends with its corner at (xe, cap)
    let (xs, ya) = (x + 0.12 * p.cap_stem, p.cap * 0.36);
    let w = cut_len(p, xe - xs, p.cap - ya, t, 0.5);
    let slope = (xe - w / 2.0 - xs) / (p.cap - ya);
    g.stroke(&[knot(xs, ya, w / slope).pen(90.0).line(), knot(xe - w / 2.0, p.cap, w).pen(0.0)]);
    // the leg leaves the arm a third of the way up it
    let yj = ya + 0.34 * (p.cap - ya);
    g.stroke(&reach(p, xs + slope * (yj - ya), yj, xe + 8.0, 1.0, 0.0, t));
}

fn N(g: &mut Draw) {
    let p = g.p;
    let s = p.cap_stem * 0.96;
    let (x0, x1) = (p.cap_sb, p.width - p.cap_sb);
    g.stroke(&vstem(x0 + s / 2.0, 0.0, p.cap, s));
    g.stroke(&vstem(x1 - s / 2.0, 0.0, p.cap, s));
    g.stroke(&span(p, x1, 0.0, 1.0, x0, p.cap, -1.0, p.cap_stem * 0.88));
}

fn M(g: &mut Draw) {
    let p = g.p;
    let s = p.cap_stem * 0.90;
    let x0 = p.cap_sb - 20.0;
    let x1 = p.width - x0;
    g.stroke(&vstem(x0 + s / 2.0, 0.0, p.cap, s));
    g.stroke(&vstem(x1 - s / 2.0, 0.0, p.cap, s));
    let t = p.cap_hair * 0.88; // thinned, and by more in the Bold, so that the three counters stay open
    g.poly(&vee(p, x0 + 0.35 * s, x1 - 0.35 * s, p.cap, p.cap * 0.30, t, 0.7 * t));
}

fn W(g: &mut Draw) {
    let p = g.p;
    let (to, ti) = (p.cap_stem * 0.84, p.cap_stem * 0.72); // outer and inner strokes
    let (x0, x1) = (21.0, p.width - 21.0);
    let a = 0.5 * ti; // the flat of each vertex
    let v0 = x0 + 0.25 * (x1 - x0); // the middle of the left vertex
    let v1 = p.width - v0;
    let top = p.cap * 0.80; // the height of the middle vertex
    let wo_l = cut_len(p, v0 - a / 2.0 - x0, -p.cap, to, 0.0);
    let wo_r = cut_len(p, v1 + a / 2.0 - x1, -p.cap, to, 0.0);
    let wi_l = cut_len(p, p.mid() - v0 - a, top, ti, -1.0);
    let wi_r = cut_len(p, p.mid() - v1 + a, top, ti, 1.0);
    // each stroke's two edges, as pairs of points
    let outer_l = (pt(x0 + wo_l, p.cap), pt(v0 - a / 2.0 + wo_l, 0.0)); // the inner edge of the left outer stroke
    let outer_r = (pt(x1 - wo_r, p.cap), pt(v1 + a / 2.0 - wo_r, 0.0));
    let upper_l = (pt(v0 + a / 2.0 - wi_l, 0.0), pt(p.mid() - a / 2.0, top)); // the upper edge of the left inner stroke
    let upper_r = (pt(v1 - a / 2.0 + wi_r, 0.0), pt(p.mid() + a / 2.0, top));
    let lower_l = (pt(v0 + a / 2.0, 0.0), pt(p.mid() - a / 2.0 + wi_l, top)); // its lower edge
    let lower_r = (pt(v1 - a / 2.0, 0.0), pt(p.mid() + a / 2.0 - wi_r, top));
    g.poly(&[
        pt(x0, p.cap),
        pt(v0 - a / 2.0, 0.0),
        lower_l.0,
        meet(lower_l, lower_r),
        lower_r.0,
        pt(v1 + a / 2.0, 0.0),
        pt(x1, p.cap),
        outer_r.0,
        meet(outer_r, upper_r),
        upper_r.1,
        upper_l.1,
        meet(outer_l, upper_l),
        outer_l.0,
    ]);
}

pub fn register(reg: &mut Registry) {
    reg.module("upper");
    reg.ch('H', H);
    reg.ch('I', I);
    reg.ch('T', T);
    reg.ch('L', L);
    reg.ch('E', E);
    reg.ch('F', F);
    reg.ch('O', O);
    reg.ch('Q', Q);
    reg.ch('C', C);
    reg.ch('G', G);
    reg.ch('S', S);
    reg.ch('U', U);
    reg.ch('J', J);
    reg.ch('D', D);
    reg.ch('P', P);
    reg.ch('R', R);
    reg.ch('B', B);
    reg.ch('A', A);
    reg.ch('V', V);
    reg.ch('Y', Y);
    reg.ch('X', X);
    reg.ch('Z', Z);
    reg.ch('K', K);
    reg.ch('N', N);
    reg.ch('M', M);
    reg.ch('W', W);
}

/// The proportional family's cells for this module's glyphs.
pub fn fit(_name: &str, _p: &Params) -> Option<Fit> {
    None
}
