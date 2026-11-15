//! Lowercase Latin.
//!
//! The round letters are `o` and what is cut from it or joined to a stem; the arched ones are `n`; the narrow
//! ones (`i j l t f r`) are a stem with a slab, a bar or a rounded elbow that fills the cell; the diagonal ones
//! are straight strokes cut flat. Measurements that only this group needs are the helpers at the top.

use rachis_kernel::{Draw, Fit, Knot, Params, Registry, V, knot, pt};

use crate::parts::{Arch, Bowl, arch, bowl, cut, elbow, hbar, lean, mirror, ring, shifted, turn, vee, vstem};

// ---------------------------------------------------------------------------------------------------------------
// Measurements of this group, each derived from the parameters.

/// An italic keeps its ink at least this far inside the cell's sides.
const EDGE: f64 = 4.0;

/// The shift in x that keeps a slanted letter inside its cell. `left` and `right` are the upright positions of the
/// points that the slant carries furthest out on each side. It is 0 for an upright master, and 0 for an italic
/// whose points stay inside.
pub fn nudge(p: &Params, left: &[(f64, f64)], right: &[(f64, f64)]) -> f64 {
    if !p.italic() {
        return 0.0;
    }
    let lo = left.iter().map(|&(x, y)| x + lean(p, y)).fold(f64::INFINITY, f64::min);
    let lo = if left.is_empty() { EDGE } else { lo };
    let hi = right.iter().map(|&(x, y)| x + lean(p, y)).fold(f64::NEG_INFINITY, f64::max);
    let hi = if right.is_empty() { p.width - EDGE } else { hi };
    (EDGE - lo).max(0.0) - (hi - (p.width - EDGE)).max(0.0)
}

/// The factor by which a stroke thins in a letter that has more strokes than the cell has room for (m, w). It
/// falls with the share of the cell that a stem takes, so the Bold thins more than the Light.
pub fn crowd(p: &Params, k: f64) -> f64 {
    1.0 - k * p.stem / p.width
}

/// Thickness of the diagonals of v, x, y, z and k: a little under the stem, as a diagonal looks darker.
pub fn diag_t(p: &Params) -> f64 {
    0.94 * p.stem
}

/// Radius, on the centre line, of the elbow of l, t and f: a fixed inner radius plus half the stem.
pub fn corner_r(p: &Params) -> f64 {
    0.15 * p.xh + p.stem / 2.0
}

/// Radius of the hook of g and j: the curve starts at the baseline and ends on the descender line.
pub fn tail_r(p: &Params) -> f64 {
    -p.desc - p.hair / 2.0
}

/// Height of the centre of the dot of i and j: a sixth of the x-height clear above the stem.
pub fn dot_y(p: &Params) -> f64 {
    p.xh + p.xh / 6.0 + p.dot
}

/// `parts::diag` with its ends given by a corner instead of the centre: a straight stroke `t` thick from height
/// `ay` to `by`, cut horizontally. `ax` is the stroke's left corner at that end when `a_side` is -1, its right
/// corner when +1 and its centre when 0; likewise `bx` and `b_side`.
pub fn bar(ax: f64, ay: f64, bx: f64, by: f64, t: f64, a_side: f64, b_side: f64) -> Vec<Knot> {
    let mut breadth = t;
    let (mut ca, mut cb) = (ax, bx);
    // the breadth of the cut depends on the slope, and the slope on the breadth
    for _ in 0..12 {
        ca = ax - a_side * breadth / 2.0;
        cb = bx - b_side * breadth / 2.0;
        breadth = t * (cb - ca).hypot(by - ay) / (by - ay).abs();
    }
    vec![knot(ca, ay, breadth).pen(0.0).line(), knot(cb, by, breadth).pen(0.0)]
}

/// How far the slab at the top of i, j and l reaches to the left of its stem's edge.
pub fn slab(p: &Params) -> f64 {
    0.25 * p.width - 0.25 * p.stem
}

/// Centre of the stem of j.
pub fn j_x(p: &Params) -> f64 {
    p.mid() + 86.0
}

// ---------------------------------------------------------------------------------------------------------------
// space, and the round and arched letters

fn space(_g: &mut Draw) {}

fn o(g: &mut Draw) {
    let p = g.p;
    g.stroke_closed(&ring(p.sb_round, -p.over, p.width - p.sb_round, p.xh + p.over, p.stem, p.hair, p.sq));
}

fn n(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.xl(), 0.0, p.xh, p.stem));
    g.stroke(&arch(p, p.xl(), p.xr(), p.xh + p.over, 0.0, Arch::default()));
}

fn h(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.xl(), 0.0, p.asc, p.stem));
    g.stroke(&arch(p, p.xl(), p.xr(), p.xh + p.over, 0.0, Arch::default()));
}

fn u(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.xr(), 0.0, p.xh, p.stem));
    g.stroke(&turn(&arch(p, p.xl(), p.xr(), p.xh + p.over, 0.0, Arch::default()), p.mid(), p.xh / 2.0));
}

fn m(g: &mut Draw) {
    let p = g.p;
    // the middle stem is the thinnest
    let (s, s_mid) = (p.stem * crowd(p, 0.70), p.stem * crowd(p, 1.05));
    let h = p.hair * crowd(p, 0.70);
    let side = 0.6 * p.sb - 4.0;
    let dx = nudge(p, &[(side, 0.0)], &[(p.width - side, 0.75 * p.xh)]);
    let (x0, x1, x2) = (side + s / 2.0 + dx, p.mid() + dx, p.width - side - s / 2.0 + dx);
    let top = p.xh + p.over;
    let branch = top - h - 0.11 * p.xh;
    g.stroke(&vstem(x0, 0.0, p.xh, s));
    let first =
        Arch { stem: Some(s_mid), hair: Some(h), branch: Some(branch), spring: 66.0, drop: 1.5, ..Arch::default() };
    g.stroke(&arch(p, x0, x1, top, 0.0, first));
    let second = arch(p, x1, x2, top, 0.0, Arch { stem: Some(s), ..first });
    // it springs from the thinner stem
    let mut knots = shifted(&second[..1], -(s - s_mid) / 2.0);
    knots.extend_from_slice(&second[1..]);
    g.stroke(&knots);
}

fn b(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.xl(), 0.0, p.asc, p.stem));
    g.stroke(&bowl(p, p.xl(), p.width - p.sb_round, -p.over, p.xh + p.over, Bowl::default()));
}

fn d(g: &mut Draw) {
    let p = g.p;
    let dx = nudge(p, &[], &[(p.width - p.sb, p.asc)]);
    g.stroke(&vstem(p.xr() + dx, 0.0, p.asc, p.stem));
    let round = mirror(&bowl(p, p.xl(), p.width - p.sb_round, -p.over, p.xh + p.over, Bowl::default()), p.mid());
    g.stroke(&shifted(&round, dx));
}

fn p_(g: &mut Draw) {
    let p = g.p;
    let dx = nudge(p, &[(p.sb, p.desc)], &[]);
    g.stroke(&vstem(p.xl() + dx, p.desc, p.xh, p.stem));
    g.stroke(&shifted(&bowl(p, p.xl(), p.width - p.sb_round, -p.over, p.xh + p.over, Bowl::default()), dx));
}

fn q(g: &mut Draw) {
    let p = g.p;
    let dx = -0.08 * p.stem; // it stands a little to the left, to leave room for the foot
    g.stroke(&vstem(p.xr() + dx, p.desc, p.xh, p.stem));
    let round = mirror(&bowl(p, p.xl(), p.width - p.sb_round, -p.over, p.xh + p.over, Bowl::default()), p.mid());
    g.stroke(&shifted(&round, dx));
    g.stroke(&hbar(p.xr() + dx, p.width - 0.2 * p.sb_round, p.desc + p.hair / 2.0, p.hair));
}

fn g_(g: &mut Draw) {
    let p = g.p;
    g.stroke(&mirror(&bowl(p, p.xl(), p.width - p.sb_round, -p.over, p.xh + p.over, Bowl::default()), p.mid()));
    g.stroke(&elbow(p.xr(), p.xh, p.desc, p.sb_round + 40.0, p.stem, p.hair, p.sq, tail_r(p)));
}

// ---------------------------------------------------------------------------------------------------------------
// c, e, a, s

fn c(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round + 4.0, p.width - p.sb_round - 14.0);
    let cx = (x0 + x1) / 2.0 + 12.0;
    let (top, bot) = (p.xh + p.over - h / 2.0, -p.over + h / 2.0);
    let white = top - bot - h;
    g.stroke(&[
        cut(x1 - 4.0, top - 0.15 * white, h, 150.0),
        knot(cx, top, h).dir(180.0).k(p.sq),
        knot(x0 + s / 2.0, p.xh / 2.0, s).dir(-90.0).k(p.sq),
        knot(cx, bot, h).dir(0.0),
        cut(x1, bot + 0.15 * white, h, 30.0),
    ]);
}

fn e(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round + 2.0, p.width - p.sb_round - 2.0);
    let cx = (x0 + x1) / 2.0;
    let (top, bot) = (p.xh + p.over - h / 2.0, -p.over + h / 2.0);
    let bh = 0.92 * h;
    let mid = 0.475 * p.xh; // centre line of the bar: a little below the middle
    let below = (mid - bh / 2.0) - (bot + h / 2.0); // the white between the bar and the bottom stroke
    g.stroke(&[
        knot(x1 - s / 2.0, mid - bh / 2.0, s).pen(0.0).dir(90.0).k(p.sq),
        knot(cx, top, h).dir(180.0).k(p.sq),
        knot(x0 + s / 2.0, p.xh / 2.0, s).dir(-90.0).k(p.sq),
        knot(cx + 10.0, bot, h).dir(0.0),
        cut(x1 - 8.0, bot + 0.32 * below, h, 26.0),
    ]);
    g.stroke(&hbar(x0 + s / 2.0, x1 - s / 2.0, mid, bh));
}

fn a(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let xs = p.xr() - 4.0; // the stem
    let x0 = p.sb_round + 8.0; // the bowl's left edge
    let top = p.xh + p.over - h / 2.0;
    let whites = p.xh + 2.0 * p.over - 3.0 * h; // what the three horizontal strokes leave
    let upper = 0.45 * whites; // the white under the top stroke; the bowl's counter takes the rest
    let bt = p.xh + p.over - h - upper; // outer top edge of the bowl
    let xc = x0 + 0.52 * (xs - x0);
    g.stroke(&[
        cut(x0 + 0.32 * s, top - 0.30 * upper, h, 30.0),
        knot(xc, top, h).dir(0.0).k(p.sq),
        knot(xs, top - 1.0 * (xs - xc), s).pen(0.0).dir(-90.0).line(),
        knot(xs, 0.0, s).pen(0.0),
    ]);
    let bot = -p.over + h / 2.0;
    let edge = xs - s / 2.0 + 3.0; // just inside the stem
    let (jt, jb) = (0.82 * h, p.join * s); // breadth of the bowl where it leaves the stem, top and bottom
    let (d_top, d_bot) = (V::unit(168.0), V::unit(52.0));
    let y_in = (bot + h / 2.0) + 0.30 * (bt - h - bot - h / 2.0); // where the counter's edge meets the stem, below
    let xb = x0 + 0.50 * (xs - s / 2.0 - x0);
    g.stroke(&[
        Knot::at(pt(edge, bt - 0.10 * h) - d_top * (s / 2.0) + d_top.left() * (jt / 2.0), jt).dir(168.0),
        knot(xb, bt - h / 2.0, h).dir(180.0).k(p.sq),
        knot(x0 + s / 2.0, (bt - p.over) / 2.0, s).dir(-90.0).k(p.sq),
        knot(xb + 4.0, bot, h).dir(0.0),
        Knot::at(pt(edge, y_in) - d_bot.left() * (jb / 2.0), jb).dir(52.0),
    ]);
}

fn s(g: &mut Draw) {
    let p = g.p;
    let (w, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round + 22.0, p.width - p.sb_round - 22.0);
    let cx = (x0 + x1) / 2.0;
    let (top, bot) = (p.xh + p.over - h / 2.0, -p.over + h / 2.0);
    let white = top - bot - h;
    g.stroke(&[
        cut(x1 - 10.0, top - 0.13 * white, h, 152.0),
        knot(cx + 2.0, top, h).dir(180.0).k(p.sq),
        knot(x0 + 8.0 + w / 2.0, p.xh * 0.735, 0.96 * w).dir(-90.0),
        knot(cx, p.xh * 0.515, 1.02 * w).dir(-26.0),
        knot(x1 - w / 2.0, p.xh * 0.265, 0.96 * w).dir(-90.0).k(p.sq),
        knot(cx - 2.0, bot, h).dir(180.0),
        cut(x0, bot + 0.13 * white, h, 152.0),
    ]);
}

// ---------------------------------------------------------------------------------------------------------------
// the narrow letters: a stem, and a slab, a bar or an elbow to fill the cell

fn dotlessi(g: &mut Draw) {
    let p = g.p;
    let x = p.mid() + 12.0;
    let half = 0.33 * p.width + 0.22 * p.stem; // half the length of the bar it stands on
    g.stroke(&vstem(x, 0.0, p.xh, p.stem));
    g.stroke(&hbar(x - p.stem / 2.0 - slab(p), x, p.xh - p.hair / 2.0, p.hair));
    g.stroke(&hbar(x - half, x + half, p.hair / 2.0, p.hair));
}

fn i(g: &mut Draw) {
    let p = g.p;
    g.use_char('ı', 0.0, 0.0);
    g.dot(p.mid() + 12.0 - 2.0, dot_y(p), p.dot);
}

fn dotlessj(g: &mut Draw) {
    let p = g.p;
    let x = j_x(p);
    g.stroke(&elbow(x, p.xh, p.desc, p.sb_round + 18.0, p.stem, p.hair, p.sq, tail_r(p)));
    g.stroke(&hbar(x - p.stem / 2.0 - slab(p) - 0.14 * p.width, x, p.xh - p.hair / 2.0, p.hair));
}

fn j(g: &mut Draw) {
    let p = g.p;
    g.use_char('ȷ', 0.0, 0.0);
    g.dot(j_x(p) - 2.0, dot_y(p), p.dot);
}

fn l(g: &mut Draw) {
    let p = g.p;
    let x = p.mid() - 24.0;
    g.stroke(&elbow(x, p.asc, 0.0, p.width - p.sb_round, p.stem, p.hair, p.sq, corner_r(p)));
    g.stroke(&hbar(x - p.stem / 2.0 - slab(p), x, p.asc - p.hair / 2.0, p.hair));
}

fn t(g: &mut Draw) {
    let p = g.p;
    let x = p.mid() - 50.0;
    g.stroke(&elbow(x, p.xh + 0.74 * (p.asc - p.xh), 0.0, p.width - p.sb_round, p.stem, p.hair, p.sq, corner_r(p)));
    g.stroke(&hbar(p.sb_round + 6.0, p.width - p.sb_round - 16.0, p.xh - p.hair / 2.0, p.hair));
}

fn f(g: &mut Draw) {
    let p = g.p;
    let x = p.mid() - 30.0;
    g.stroke(&elbow(x, 0.0, p.asc + p.over, p.width - p.sb_round, p.stem, p.hair, p.sq, corner_r(p)));
    g.stroke(&hbar(p.sb_round + 6.0, p.width - p.sb_round - 30.0, p.xh - p.hair / 2.0, p.hair));
}

fn r(g: &mut Draw) {
    let p = g.p;
    let x = p.xl() + 20.0;
    let end = p.width - p.sb_round;
    g.stroke(&vstem(x, 0.0, p.xh, p.stem));
    let a = arch(p, x, end - 30.0, p.xh + p.over, 0.0, Arch { lean: 0.60, ..Arch::default() });
    g.stroke(&[a[0], a[1], cut(end, p.xh + p.over - p.hair / 2.0 - 0.09 * p.xh, p.hair, -32.0)]);
}

// ---------------------------------------------------------------------------------------------------------------
// the diagonal letters

fn k(g: &mut Draw) {
    let p = g.p;
    let x = p.xl();
    let t = diag_t(p);
    g.stroke(&vstem(x, 0.0, p.asc, p.stem));
    let arm = bar(x, 0.34 * p.xh, p.width - p.sb_round + 2.0, p.xh, 0.94 * t, 0.0, 1.0);
    g.stroke(&[Knot::at(arm[0].z, 0.94 * t).line(), arm[1]]);
    let f = 0.42; // how far along the arm the leg leaves it
    let z = arm[0].z + (arm[1].z - arm[0].z) * f;
    let leg = bar(z.x, z.y, p.width - p.sb_round + 12.0, 0.0, t, 0.0, 1.0);
    g.stroke(&[Knot::at(leg[0].z, t).line(), leg[1]]);
}

fn v(g: &mut Draw) {
    let p = g.p;
    let t = diag_t(p);
    g.poly(&vee(p.sb_round - 6.0, p.width - p.sb_round + 6.0, p.xh, 0.0, t, 0.7 * t));
}

fn w(g: &mut Draw) {
    let p = g.p;
    let (t_out, t_in) = (p.stem * crowd(p, 1.0), p.stem * crowd(p, 2.1));
    let side = p.sb / 2.0 - 15.0;
    let dx = nudge(p, &[], &[(p.width - side, p.xh)]);
    let (x0, x1) = (side + dx, p.width - side + dx);
    let mid = p.mid() + dx;
    let foot = 0.26 * (x1 - x0); // the lower vertices, from each side
    let flat = 0.5 * t_in; // half the breadth of a vertex
    g.stroke(&bar(x0, p.xh, x0 + foot - flat, 0.0, t_out, -1.0, -1.0));
    g.stroke(&bar(x0 + foot + flat, 0.0, mid - flat, p.xh, t_in, 1.0, -1.0));
    g.stroke(&bar(mid + flat, p.xh, x1 - foot - flat, 0.0, t_in, 1.0, -1.0));
    g.stroke(&bar(x1 - foot + flat, 0.0, x1, p.xh, t_out, 1.0, 1.0));
}

fn x(g: &mut Draw) {
    let p = g.p;
    let t = diag_t(p);
    let (x0, x1) = (p.sb_round - 2.0, p.width - p.sb_round + 2.0);
    let pinch = 8.0; // the top is narrower than the bottom
    g.stroke(&bar(x0, 0.0, x1 - pinch, p.xh, t, -1.0, 1.0));
    g.stroke(&bar(x0 + pinch, p.xh, x1, 0.0, t, -1.0, 1.0));
}

fn y(g: &mut Draw) {
    let p = g.p;
    let t = diag_t(p);
    let (x0, x1) = (p.sb_round - 4.0, p.width - p.sb_round + 4.0);
    let xv = p.mid() + 6.0; // where the two strokes' centre lines meet, on the baseline
    let right = bar(x1, p.xh, xv, 0.0, t, 1.0, 0.0);
    let slope = (right[0].z.x - xv) / p.xh;
    g.stroke(&[right[0], knot(xv + slope * p.desc, p.desc, right[0].w).pen(0.0)]);
    g.stroke(&bar(x0, p.xh, xv, 0.0, t, -1.0, 0.0));
}

fn z(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (p.sb_round + 28.0, p.width - p.sb_round - 28.0);
    g.stroke(&hbar(x0 + 6.0, x1, p.xh - p.hair / 2.0, p.hair));
    g.stroke(&hbar(x0, x1 + 4.0, p.hair / 2.0, p.hair));
    g.stroke(&bar(x1, p.xh, x0, 0.0, diag_t(p), 1.0, -1.0));
}

pub fn register(reg: &mut Registry) {
    reg.module("lower");
    reg.ch(' ', space);
    reg.ch('o', o);
    reg.ch('n', n);
    reg.ch('h', h);
    reg.ch('u', u);
    reg.ch('m', m);
    reg.ch('b', b);
    reg.ch('d', d);
    reg.ch('p', p_);
    reg.ch('q', q);
    reg.ch('g', g_);
    reg.ch('c', c);
    reg.ch('e', e);
    reg.ch('a', a);
    reg.ch('s', s);
    reg.ch('ı', dotlessi);
    reg.ch('i', i);
    reg.ch('ȷ', dotlessj);
    reg.ch('j', j);
    reg.ch('l', l);
    reg.ch('t', t);
    reg.ch('f', f);
    reg.ch('r', r);
    reg.ch('k', k);
    reg.ch('v', v);
    reg.ch('w', w);
    reg.ch('x', x);
    reg.ch('y', y);
    reg.ch('z', z);
}

/// The proportional family's cells for this module's glyphs.
pub fn fit(_name: &str, _p: &Params) -> Option<Fit> {
    None
}
