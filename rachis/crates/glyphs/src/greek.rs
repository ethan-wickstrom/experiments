//! Greek: the monotonic alphabet with its tonos and dialytika, the variant letters of mathematics (ϑ ϕ ϖ ϰ ϱ ϵ),
//! the kai symbol and the Greek signs.
//!
//! The Greek is the Latin's typeface: the same strokes, heights, parts and superellipse. A capital that has the
//! shape of a Latin capital is that glyph as a component. Letters with three vertical strokes in the cell (Φ Ψ φ
//! ϕ ψ ω ϖ) take thinner strokes, as m and w do. Every letter that looks like a Latin letter, a figure or a sign is
//! told apart from it by the feature a mathematician reads it by: ν's right stroke is curved, υ and ω are round
//! at the bottom, ρ has no spur, σ's top runs out flat, ι has no dot and a foot, χ descends.
//!
//! The marks are drawn here: the tonos is a steep stroke a little lighter than a hair, the dialytika i's dots. A
//! letter with a mark is its base as a component with the mark placed over the base's outline; a capital takes
//! its tonos to its upper left.

// The programs keep the Python names, and the Greek capitals and lowercase differ only in case (Gamma, gamma).
#![allow(non_snake_case)]

use rachis_kernel::{Draw, Fit, Glyph, Knot, Params, Registry, V, knot, name_of, pt};

use crate::parts::{Arch, Bowl, arch, bowl, cut, cut_pen, diag, elbow, hbar, mirror, ring, turn, vee, vstem};

// ---------------------------------------------------------------------------------------------------------------
// Measurements this group derives from the parameters. The lowercase's are the Latin lowercase's.

/// The factor by which a stroke thins in a letter with more strokes than the cell has room for, as in m and w.
fn crowd(p: &Params, k: f64) -> f64 {
    1.0 - k * p.stem / p.width
}

/// Thickness of a lowercase diagonal: a little under the stem, as a diagonal looks darker.
fn diag_t(p: &Params) -> f64 {
    0.94 * p.stem
}

/// Radius, on the centre line, of the elbow of t, and of τ's foot.
fn corner_r(p: &Params) -> f64 {
    0.15 * p.xh + p.stem / 2.0
}

/// Radius of the hook of g and j, and of ϗ.
fn tail_r(p: &Params) -> f64 {
    -p.desc - p.hair / 2.0
}

/// A straight stroke `t` thick from height `ay` to `by`, cut horizontally; `ax` is its left corner at that end
/// when `a_side` is -1, its right corner when +1 and its centre when 0; likewise `bx` and `b_side`. As
/// `lower::bar`.
fn bar(ax: f64, ay: f64, bx: f64, by: f64, t: f64, a_side: f64, b_side: f64) -> Vec<Knot> {
    let mut breadth = t;
    let (mut ca, mut cb) = (ax, bx);
    for _ in 0..12 {
        ca = ax - a_side * breadth / 2.0;
        cb = bx - b_side * breadth / 2.0;
        breadth = t * (cb - ca).hypot(by - ay) / (by - ay).abs();
    }
    vec![knot(ca, ay, breadth).pen(0.0).line(), knot(cb, by, breadth).pen(0.0)]
}

/// The box of the Latin O, which Θ, Ω and the double-struck rounds share.
fn cap_round(p: &Params) -> (f64, f64, f64, f64) {
    let x0 = p.sb_round - 8.0;
    (x0, -p.over, p.width - x0, p.cap + p.over)
}

/// The stroke of a capital that puts three verticals in the cell (Φ, Ψ).
fn cap_three(p: &Params) -> f64 {
    0.5 * (p.cap_stem + p.cap_hair)
}

// ---------------------------------------------------------------------------------------------------------------
// Capitals that are Latin capitals: registered in `register`, each the Latin capital as a component.

/// The Greek capitals that have the shape of a Latin capital, and that capital.
const SAME: [(char, char); 14] = [
    ('Α', 'A'),
    ('Β', 'B'),
    ('Ε', 'E'),
    ('Ζ', 'Z'),
    ('Η', 'H'),
    ('Ι', 'I'),
    ('Κ', 'K'),
    ('Μ', 'M'),
    ('Ν', 'N'),
    ('Ο', 'O'),
    ('Ρ', 'P'),
    ('Τ', 'T'),
    ('Υ', 'Y'),
    ('Χ', 'X'),
];

// ---------------------------------------------------------------------------------------------------------------
// Capitals

fn Gamma(g: &mut Draw) {
    let p = g.p;
    let x = p.cxl() + 30.0;
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    g.stroke(&hbar(x, p.width - p.sb_round - 10.0, p.cap - p.cap_hair / 2.0, p.cap_hair));
}

/// Outer feet, stroke and apex of Λ and Δ: the Latin A's.
fn caret(p: &Params) -> (f64, f64, f64, f64) {
    let t = p.cap_stem * 0.96;
    (p.sb_round - 34.0, p.width - p.sb_round + 34.0, t, t * 0.92)
}

fn Delta(g: &mut Draw) {
    let p = g.p;
    let (x0, x1, t, apex) = caret(p);
    g.poly(&vee(x0, x1, 0.0, p.cap, t, apex));
    let inset = (p.mid() - apex / 2.0 - x0) * p.cap_hair / p.cap; // where the outer edge is at the bar's top
    g.stroke(&hbar(x0 + inset, x1 - inset, p.cap_hair / 2.0, p.cap_hair));
}

fn Lambda(g: &mut Draw) {
    let p = g.p;
    let (x0, x1, t, apex) = caret(p);
    g.poly(&vee(x0, x1, 0.0, p.cap, t, apex));
}

fn Theta(g: &mut Draw) {
    let p = g.p;
    let (x0, y0, x1, y1) = cap_round(p);
    g.stroke_closed(&ring(x0, y0, x1, y1, p.cap_stem, p.cap_hair, p.sq + 0.02));
    let half = 0.27 * (x1 - x0 - 2.0 * p.cap_stem); // the bar floats: a gap of 0.23 of the counter on each side
    g.stroke(&hbar(p.mid() - half, p.mid() + half, p.cap / 2.0, p.cap_hair));
}

fn Xi(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (p.sb_round + 10.0, p.width - p.sb_round - 10.0);
    let h = p.cap_hair;
    g.stroke(&hbar(x0, x1, p.cap - h / 2.0, h));
    g.stroke(&hbar(x0 + 62.0, x1 - 62.0, p.cap / 2.0, h));
    g.stroke(&hbar(x0, x1, h / 2.0, h));
}

fn Pi(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.cxl(), 0.0, p.cap, p.cap_stem));
    g.stroke(&vstem(p.cxr(), 0.0, p.cap, p.cap_stem));
    g.stroke(&hbar(p.cxl() - p.cap_stem / 2.0, p.cxr() + p.cap_stem / 2.0, p.cap - p.cap_hair / 2.0, p.cap_hair));
}

fn Sigma(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (p.sb_round + 16.0, p.width - p.sb_round - 16.0);
    let (h, t) = (p.cap_hair, p.cap_stem * 0.96);
    let xv = p.mid() - 26.0; // the centre line's vertex; the mitre's point lies half a stroke further right
    let mut xa = x0 + t / 2.0;
    for _ in 0..3 {
        // the diagonal's left edge starts on x0
        xa = x0 + diag(xa, p.cap, xv, p.cap / 2.0, t)[0].w / 2.0;
    }
    let w = diag(xa, p.cap, xv, p.cap / 2.0, t)[0].w;
    g.stroke(&[knot(xa, p.cap, w).pen(0.0).line(), knot(xv, p.cap / 2.0, t).line(), knot(xa, 0.0, w).pen(0.0)]);
    g.stroke(&hbar(xa, x1, p.cap - h / 2.0, h));
    g.stroke(&hbar(xa, x1 + 4.0, h / 2.0, h));
}

fn Phi(g: &mut Draw) {
    let p = g.p;
    let t = cap_three(p);
    let x0 = p.sb_round - 24.0;
    g.stroke_closed(&ring(x0, p.cap * 0.14, p.width - x0, p.cap * 0.86, t, p.cap_hair * 0.94, p.sq + 0.02));
    g.stroke(&vstem(p.mid(), 0.0, p.cap, t));
}

fn Psi(g: &mut Draw) {
    let p = g.p;
    let t = cap_three(p);
    let h = p.cap_hair * 0.94;
    let xa = p.sb_round - 22.0 + t / 2.0;
    let bottom = p.cap * 0.27;
    let turn_ = p.cap * 0.56;
    g.stroke(&[
        knot(xa, p.cap, t).pen(0.0).line(),
        knot(xa, turn_, t).pen(0.0).dir(-90.0).k(p.sq),
        knot(p.mid(), bottom + h / 2.0, h).dir(0.0).k(p.sq),
        knot(p.width - xa, turn_, t).pen(0.0).dir(90.0).line(),
        knot(p.width - xa, p.cap, t).pen(0.0),
    ]);
    g.stroke(&vstem(p.mid(), 0.0, p.cap, t));
}

fn Omega(g: &mut Draw) {
    let p = g.p;
    let (x0, _, x1, y1) = cap_round(p);
    let (s, h) = (p.cap_stem, p.cap_hair);
    let lean = 58.0; // the direction, from the horizontal, in which the ring comes down onto its feet
    let end = cut_pen(0.0, h * 0.5, s, -180.0 + lean, 0.0);
    let gap = 0.17 * (x1 - x0 - 2.0 * s); // half the opening between the ring's two ends
    let xn = p.mid() - gap - end.w / 2.0;
    let side = p.cap * 0.52;
    g.stroke(&[
        cut_pen(xn, h * 0.5, s, 180.0 - lean, 0.0),
        knot(x0 + s / 2.0, side, s).dir(90.0).k(p.sq + 0.02),
        knot(p.mid(), y1 - h / 2.0, h).dir(0.0).k(p.sq + 0.02),
        knot(x1 - s / 2.0, side, s).dir(-90.0),
        cut_pen(p.width - xn, h * 0.5, s, -180.0 + lean, 0.0),
    ]);
    let foot = xn + end.w / 2.0 + 4.0;
    g.stroke(&hbar(x0 - 6.0, foot, h / 2.0, h));
    g.stroke(&hbar(p.width - foot, x1 + 6.0, h / 2.0, h));
}

fn ohm(g: &mut Draw) {
    g.same_as_char('\u{03a9}');
}

// ---------------------------------------------------------------------------------------------------------------
// Lowercase

fn omicron(g: &mut Draw) {
    g.same_as_char('o');
}

fn alpha(g: &mut Draw) {
    let p = g.p;
    let xs = p.xr() - 36.0; // the stem stands left of d's, and its foot takes the room
    g.stroke(&mirror(
        &bowl(p, p.width - xs, p.width - p.sb_round + 6.0, -p.over, p.xh + p.over, Bowl::default()),
        p.mid(),
    ));
    g.stroke(&elbow(xs, p.xh, 0.0, p.width - p.sb_round + 22.0, p.stem, p.hair, p.sq, 84.0));
}

fn beta(g: &mut Draw) {
    let p = g.p;
    let xs = p.xl() + 2.0;
    let (s, h) = (p.stem, p.hair);
    let (top, bot) = (p.asc + p.over - h / 2.0, -p.over + h / 2.0);
    let waist = p.asc * 0.56;
    let (edge_hi, edge_lo) = (p.width - p.sb_round - 40.0, p.width - p.sb_round - 4.0);
    let inner = xs + s / 2.0;
    let xa = inner + 0.46 * (edge_hi - s - inner);
    let bar = inner + 0.30 * (edge_hi - s - inner); // the waist's bar stops short of the stem
    g.stroke(&[
        knot(xs, p.desc, s).pen(0.0).line(),
        knot(xs, p.asc - 0.8 * (xa - xs), s).pen(0.0).dir(90.0).k(p.sq),
        knot(xa, top, h).dir(0.0).k(p.sq),
        knot(edge_hi - s * 0.48, (waist + top) / 2.0, s * 0.96).dir(-90.0).k(p.sq),
        knot(xa + 16.0, waist, h).pen(90.0).dir(180.0).line(),
        knot(bar, waist, h).pen(90.0),
    ]);
    let j = p.join * s;
    let y_end = bot + 0.30 * (waist - bot);
    g.stroke(&[
        knot(bar, waist, h).pen(90.0).line(),
        knot(xa + 26.0, waist, h).pen(90.0).dir(0.0).k(p.sq),
        knot(edge_lo - s / 2.0, (waist + bot) / 2.0, s).dir(-90.0).k(p.sq),
        knot(inner + 0.5 * (edge_lo - s - inner), bot, h).dir(180.0),
        Knot::at(pt(inner - 3.0, y_end) + ((j / 2.0) * V::unit(122.0)).left(), j).dir(122.0),
    ]);
}

fn gamma(g: &mut Draw) {
    let p = g.p;
    let t = p.stem * 0.94;
    let yv = p.xh * 0.13;
    g.poly(&vee(p.sb_round + 6.0, p.width - p.sb_round - 6.0, p.xh, yv, t, p.stem * 0.9));
    g.stroke(&vstem(p.mid(), p.desc, yv + p.stem * 0.6, p.stem));
}

fn delta(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round + 8.0, p.width - p.sb_round - 8.0);
    let cx = (x0 + x1) / 2.0;
    let (y0, y1) = (-p.over, p.xh * 0.86);
    g.stroke_closed(&ring(x0, y0, x1, y1, s, h, p.sq));
    let (rx, ry) = ((x1 - x0 - s) / 2.0, (y1 - y0 - h) / 2.0);
    g.stroke(&[
        cut(x1 - 40.0, p.asc - 78.0, h * 1.04, 148.0),
        knot(cx + 6.0, p.asc + p.over - h / 2.0, h).dir(180.0).k(p.sq),
        knot(x0 + 74.0 + s / 2.0, p.asc - 128.0, s * 0.9).dir(-82.0),
        knot(cx + 0.70 * rx, (y0 + y1) / 2.0 + 0.80 * ry, (s + h) / 2.0).dir(-42.0),
    ]);
}

fn epsilon(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round + 22.0, p.width - p.sb_round - 22.0);
    let cx = (x0 + x1) / 2.0;
    let (top, bot) = (p.xh + p.over - h / 2.0, -p.over + h / 2.0);
    let waist = p.xh * 0.52;
    let tongue = cx + 30.0;
    g.stroke(&[
        cut(x1 - 10.0, p.xh - 108.0, h * 1.04, 144.0),
        knot(cx + 6.0, top, h).dir(180.0).k(p.sq),
        knot(x0 + 22.0 + s / 2.0, (top + waist) / 2.0, s * 0.96).dir(-90.0).k(p.sq),
        knot(cx - 30.0, waist, h).pen(90.0).dir(0.0).line(),
        knot(tongue, waist, h).pen(90.0),
    ]);
    g.stroke(&[
        knot(tongue, waist, h).pen(90.0).line(),
        knot(cx - 34.0, waist, h).pen(90.0).dir(180.0).k(p.sq),
        knot(x0 + s / 2.0, (waist + bot) / 2.0, s).dir(-90.0).k(p.sq),
        knot(cx + 4.0, bot, h).dir(0.0),
        cut(x1, 106.0, h * 1.04, 36.0),
    ]);
}

/// The end of ζ, ξ and ς: a bar travelling right at height `y` turns down at `x` and stops, cut flat, below the
/// baseline.
fn tail(p: &Params, x: f64, y: f64) -> Vec<Knot> {
    let r = 0.9 * p.stem;
    vec![
        knot(x - r, y, p.hair).dir(0.0).k(p.sq),
        knot(x, y - r, p.stem * 0.92).pen(0.0).dir(-90.0),
        cut_pen(x - 18.0, p.desc * 0.82, p.stem * 0.84, -104.0, 0.0),
    ]
}

fn zeta(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round + 26.0, p.width - p.sb_round - 26.0);
    g.stroke(&hbar(x0, x1, p.asc - h / 2.0, h));
    let yb = h / 2.0;
    let mut knots = vec![
        cut_pen(x1 - 52.0, p.asc - h / 2.0, h * 1.06, -128.0, 0.0),
        knot(x0 + 14.0 + s / 2.0, p.asc * 0.34, s).dir(-90.0).k(p.sq),
        knot(p.mid() - 10.0, yb, h).dir(0.0).line(),
    ];
    knots.extend_from_slice(&tail(p, x1 - 20.0 - s / 2.0, yb));
    g.stroke(&knots);
}

fn xi(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round + 26.0, p.width - p.sb_round - 26.0);
    let (yt, yb) = (p.asc - h / 2.0, h / 2.0);
    let waist = p.asc * 0.58;
    let cx = p.mid();
    let tongue = x1 - 62.0;
    g.stroke(&[
        knot(x1 - 14.0, yt, h).pen(90.0).line(),
        knot(cx, yt, h).pen(90.0).dir(180.0).k(p.sq),
        knot(x0 + 36.0 + s / 2.0, (yt + waist) / 2.0, s * 0.96).dir(-90.0).k(p.sq),
        knot(cx, waist, h).pen(90.0).dir(0.0).line(),
        knot(tongue, waist, h).pen(90.0),
    ]);
    let mut knots = vec![
        knot(tongue, waist, h).pen(90.0).line(),
        knot(cx - 10.0, waist, h).pen(90.0).dir(180.0).k(p.sq),
        knot(x0 + s / 2.0, (waist + yb) / 2.0, s).dir(-90.0).k(p.sq),
        knot(cx - 10.0, yb, h).dir(0.0).line(),
    ];
    knots.extend_from_slice(&tail(p, x1 - 20.0 - s / 2.0, yb));
    g.stroke(&knots);
}

fn eta(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.xl(), 0.0, p.xh, p.stem));
    g.stroke(&arch(p, p.xl(), p.xr(), p.xh + p.over, p.desc, Arch::default()));
}

fn theta(g: &mut Draw) {
    let p = g.p;
    let x0 = p.sb_round + 24.0; // narrower than o and 0, and as tall as the ascenders
    g.stroke_closed(&ring(x0, -p.over, p.width - x0, p.asc + p.over, p.stem, p.hair, p.sq));
    g.stroke(&hbar(x0 + p.stem / 2.0, p.width - x0 - p.stem / 2.0, p.asc / 2.0, p.hair * 0.94));
}

fn iota(g: &mut Draw) {
    let p = g.p;
    // a stem and a foot to its right, centred together: the cell of the proportional family is just that wide
    let foot = iota_foot(p);
    let x = p.mid() - (p.stem + foot) / 2.0 + p.stem / 2.0 + 0.02 * p.counter;
    g.stroke(&elbow(x, p.xh, 0.0, x + p.stem / 2.0 + foot, p.stem, p.hair, p.sq, 0.13 * p.xh + p.stem / 2.0));
}

/// How far ι's foot reaches past its stem.
fn iota_foot(p: &Params) -> f64 {
    0.45 * p.counter
}

fn kappa(g: &mut Draw) {
    let p = g.p;
    let x = p.xl() + 10.0;
    let t = p.stem * 0.94;
    let xr = p.width - p.sb_round + 2.0;
    g.stroke(&vstem(x, 0.0, p.xh, p.stem));
    g.stroke(&[knot(x, p.xh * 0.34, t).line(), diag(0.0, 0.0, xr - 54.0, p.xh, t)[1]]);
    g.stroke(&[knot(x + 112.0, p.xh * 0.52, t).line(), diag(0.0, p.xh, xr - 46.0, 0.0, t)[1]]);
}

fn lambda_(g: &mut Draw) {
    let p = g.p;
    let t = p.stem * 0.96;
    let (xa, xb) = (p.sb_round + 84.0, p.width - p.sb_round - 28.0); // the long stroke's centre line, top and bottom
    let xc = p.sb_round + 40.0; // the leg's foot
    let yj = p.xh * 0.72;
    let xj = xa + (xb - xa) * (p.asc - yj) / p.asc;
    g.stroke(&diag(xa, p.asc, xb, 0.0, t));
    g.stroke(&[knot(xj, yj, t).line(), diag(xj, yj, xc, 0.0, t)[1]]);
}

fn mu(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.xl(), p.desc, p.xh, p.stem));
    g.stroke(&vstem(p.xr(), 0.0, p.xh, p.stem));
    g.stroke(&turn(&arch(p, p.xl(), p.xr(), p.xh + p.over, 0.0, Arch::default()), p.mid(), p.xh / 2.0));
}

fn micro(g: &mut Draw) {
    g.same_as_char('μ');
}

fn nu(g: &mut Draw) {
    let p = g.p;
    let (s, t) = (p.stem, diag_t(p));
    let (x0, x1) = (p.sb + 6.0, p.width - p.sb_round + 2.0); // outer edges: the straight side and the round one
    let xv = x0 + 0.30 * (x1 - x0); // the vertex, on the baseline: the left stroke is steep
    g.stroke(&bar(x0, p.xh, xv, 0.0, t, -1.0, 0.0));
    // the right stroke leaves the vertex as a diagonal, rises as a curve and ends upright
    g.stroke(&[
        cut_pen(xv + 0.10 * t, 0.0, t, 42.0, 0.0),
        knot(x1 - s / 2.0, 0.66 * p.xh, 0.98 * s).dir(86.0),
        cut_pen(x1 - s / 2.0 - 0.012 * p.xh, p.xh, 0.96 * s, 94.0, 0.0),
    ]);
}

fn pi(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (xa, xb) = (p.sb_round - 12.0, p.width - p.sb_round + 12.0); // the bar overhangs both legs
    let (x0, x1) = (p.xl() + 6.0, p.xr() - 18.0);
    let yt = p.xh - h / 2.0;
    g.stroke(&hbar(xa, xb, yt, h));
    g.stroke(&vstem(x0, 0.0, yt, s));
    g.stroke(&elbow(x1, yt, 0.0, xb - 6.0, s, h, p.sq, 0.06 * p.xh + s / 2.0));
}

/// The bowl of ρ and ϱ, and the centre line of the stem that carries it. The stem is p's; the bowl's top left
/// flows into it with no spur.
fn rho_bowl(p: &Params) -> (Vec<Knot>, f64) {
    let x0 = p.sb + 2.0;
    (ring(x0, -p.over, p.width - p.sb_round, p.xh + p.over, p.stem, p.hair, p.sq), x0 + p.stem / 2.0)
}

fn rho(g: &mut Draw) {
    let p = g.p;
    let (bowl, x) = rho_bowl(p);
    g.stroke_closed(&bowl);
    g.stroke(&vstem(x, p.desc, p.xh / 2.0, p.stem));
}

fn rho_sym(g: &mut Draw) {
    let p = g.p;
    let (bowl, x) = rho_bowl(p);
    g.stroke_closed(&bowl);
    // the stem turns right below the baseline, under the bowl
    let x_end = p.width - p.sb_round - 0.10 * p.width;
    g.stroke(&elbow(x, p.xh / 2.0, p.desc, x_end, p.stem, p.hair, p.sq, 0.62 * tail_r(p)));
}

fn sigma(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let x0 = p.sb_round;
    let xe = p.width - p.sb_round + 10.0; // the end of the flat top stroke
    let x1 = x0 + 0.80 * (xe - x0); // the bowl's right edge
    // the bowl's top is flat, on the x-height, where the top stroke runs out of it
    g.stroke_closed(&ring(x0, -p.over, x1, p.xh, s, h, p.sq));
    g.stroke(&hbar((x0 + x1) / 2.0, xe, p.xh - h / 2.0, h));
}

fn sigma_final(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round + 12.0, p.width - p.sb_round - 12.0);
    let cx = (x0 + x1) / 2.0 + 12.0;
    let top = p.xh + p.over - h / 2.0;
    let yb = h / 2.0; // the bottom stroke, which turns into the tail
    let white = top - yb - h;
    let x_tail = x1 - 16.0 - s / 2.0;
    let mut knots = vec![
        cut(x1 - 4.0, top - 0.16 * white, h, 150.0),
        knot(cx, top, h).dir(180.0).k(p.sq),
        knot(x0 + s / 2.0, 0.50 * p.xh, s).dir(-90.0).k(p.sq),
        knot(x0 + 0.42 * (x_tail - x0), yb, h).dir(0.0).line(),
    ];
    knots.extend_from_slice(&tail(p, x_tail, yb));
    g.stroke(&knots);
}

fn tau(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (xa, xb) = (p.sb_round + 4.0, p.width - p.sb_round - 4.0);
    let x = xa + 0.40 * (xb - xa); // the stem stands left of the middle; its foot takes the room on the right
    let yt = p.xh - h / 2.0;
    g.stroke(&hbar(xa, xb, yt, h));
    g.stroke(&elbow(x, yt, 0.0, x + corner_r(p) + 0.20 * p.counter, s, h, p.sq, corner_r(p)));
}

fn upsilon(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let xa = p.xl() - 2.0; // the left arm is straight
    let x1 = p.width - p.sb_round; // the right one is round
    let xc = (xa - s / 2.0 + x1) / 2.0;
    let ym = 0.44 * p.xh;
    g.stroke(&[
        knot(xa, p.xh, s).pen(0.0).line(),
        knot(xa, ym, s).pen(0.0).dir(-90.0).k(p.sq),
        knot(xc, -p.over + h / 2.0, h).dir(0.0).k(p.sq),
        knot(x1 - s / 2.0, ym + 0.04 * p.xh, s).dir(90.0),
        cut_pen(x1 - s / 2.0 - 0.025 * p.xh, p.xh, 0.96 * s, 96.0, 0.0),
    ]);
}

/// The stroke of a letter that puts three verticals in the cell (φ ϕ ψ ω ϖ), the stroke of its middle vertical,
/// and the stroke of its bowls' tops and bottoms: thinner than n's, as m's are.
fn three(p: &Params) -> (f64, f64, f64) {
    (p.stem * crowd(p, 0.70), p.stem * crowd(p, 1.05), p.hair * crowd(p, 0.70))
}

/// The outer edges of a letter that puts three verticals in the cell: in the fixed-pitch cell they come closer to
/// its sides than a round letter's, as m's do; a proportional cell is wide enough for the round sidebearing.
fn wide(p: &Params) -> (f64, f64) {
    let side = if p.mono { 0.6 * p.sb_round + 4.0 } else { p.sb_round };
    (side, p.width - side)
}

fn phi(g: &mut Draw) {
    let p = g.p;
    let (s, s_mid, h) = three(p);
    let (x0, x1) = wide(p);
    let mid = p.mid();
    let ym = 0.46 * p.xh;
    let top = p.xh + p.over - h / 2.0;
    let xq = (mid + x1 - s / 2.0) / 2.0; // the crest of the loop, which comes down into the stem
    g.stroke(&[
        cut_pen(x0 + s / 2.0 + 0.03 * p.xh, p.xh, s, -96.0, 0.0),
        knot(x0 + s / 2.0, ym, s).dir(-90.0).k(p.sq),
        knot(mid, -p.over + h / 2.0, h).dir(0.0).k(p.sq),
        knot(x1 - s / 2.0, ym + 0.04 * p.xh, s).dir(90.0).k(p.sq),
        knot(xq, top, h).dir(180.0).k(p.sq),
        knot(mid, top - 1.3 * (xq - mid), s_mid).pen(0.0).dir(-90.0).line(),
        knot(mid, p.desc, s_mid).pen(0.0),
    ]);
}

fn phi_sym(g: &mut Draw) {
    let p = g.p;
    let (s, s_mid, h) = three(p);
    let (x0, x1) = wide(p);
    g.stroke_closed(&ring(x0 + 10.0, -p.over, x1 - 10.0, p.xh + p.over, s, h, p.sq));
    g.stroke(&vstem(p.mid(), p.desc, p.asc, s_mid));
}

fn chi(g: &mut Draw) {
    let p = g.p;
    let (t, h) = (diag_t(p), p.hair);
    let (x0, x1) = (p.sb_round - 4.0, p.width - p.sb_round + 4.0);
    let (cx, cy) = ((x0 + x1) / 2.0, (p.xh + p.desc) / 2.0);
    // the straight stroke, from top right to bottom left
    let e = 0.10 * (x1 - x0);
    g.stroke(&bar(x1 - e, p.xh, x0 + e, p.desc, t, 1.0, -1.0));
    // the main stroke, from top left to bottom right: its ends turn horizontal
    let (ax, ay) = (x0 + 0.24 * (x1 - x0), p.xh - 0.16 * (p.xh - p.desc));
    let slope = pt(cx - ax, cy - ay).angle();
    let (bx, by) = (2.0 * cx - ax, 2.0 * cy - ay);
    g.stroke(&[
        knot(x0 + 0.02 * (x1 - x0), p.xh - h / 2.0, h).dir(0.0),
        knot(ax, ay, t).dir(slope).line(),
        knot(bx, by, t).dir(slope),
        knot(x1 - 0.02 * (x1 - x0), p.desc + h / 2.0, h).dir(0.0),
    ]);
}

fn psi(g: &mut Draw) {
    let p = g.p;
    let (s, s_mid, h) = three(p);
    let (x0, x1) = wide(p);
    let ym = 0.46 * p.xh;
    g.stroke(&[
        knot(x0 + s / 2.0, p.xh, s).pen(0.0).line(),
        knot(x0 + s / 2.0, ym, s).pen(0.0).dir(-90.0).k(p.sq),
        knot(p.mid(), -p.over + h / 2.0, h).dir(0.0).k(p.sq),
        knot(x1 - s / 2.0, ym, s).pen(0.0).dir(90.0).line(),
        knot(x1 - s / 2.0, p.xh, s).pen(0.0),
    ]);
    g.stroke(&vstem(p.mid(), p.desc, p.asc, s_mid));
}

/// The left half of ω and ϖ: an outer arm from `top` round a bowl to the middle vertical, which stops at
/// `mid_top`.
fn omega_half(p: &Params, x0: f64, top: Knot, mid_top: f64) -> Vec<Knot> {
    let (s, s_mid, h) = three(p);
    let mid = p.mid();
    let ym = 0.40 * p.xh;
    vec![
        top,
        knot(x0 + s / 2.0, ym, s).dir(-90.0).k(p.sq),
        knot((x0 + s / 2.0 + mid) / 2.0, -p.over + h / 2.0, h).dir(0.0).k(p.sq),
        knot(mid, ym, s_mid).pen(0.0).dir(90.0).line(),
        knot(mid, mid_top, s_mid).pen(0.0),
    ]
}

fn omega(g: &mut Draw) {
    let p = g.p;
    let (s, _, _) = three(p);
    let (x0, _) = wide(p);
    // the outer arms lean in a little at the top
    let top = cut_pen(x0 + s / 2.0 + 0.03 * p.xh, p.xh, s, -96.0, 0.0);
    let half = omega_half(p, x0, top, 0.64 * p.xh);
    g.stroke(&half);
    g.stroke(&mirror(&half, p.mid()));
}

fn pi_sym(g: &mut Draw) {
    let p = g.p;
    let (s, _, h) = three(p);
    let (x0, x1) = wide(p);
    let yt = p.xh - h / 2.0;
    g.stroke(&hbar(x0, x1, yt, h));
    let inset = 0.20 * s; // the bar overhangs the arms
    let top = knot(x0 + inset + s / 2.0, yt, s).pen(0.0).dir(-90.0).line();
    let half = omega_half(p, x0 + inset, top, 0.60 * p.xh);
    g.stroke(&half);
    g.stroke(&mirror(&half, p.mid()));
}

fn theta_sym(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let over = 0.5 * s + 24.0; // how far the bar runs out past the bowl
    let (x0, x1) = (p.sb_round - 4.0, p.width - p.sb_round + 8.0 - over); // the bowl
    let xl = x1 - 2.0 * s - 0.5 * p.counter; // the outer left of the loop at the top
    let top = p.asc + p.over - h / 2.0;
    let yc = 0.80 * p.xh; // the bar the loop ends in
    let xr = x1 - s / 2.0;
    g.stroke(&[
        cut_pen(x0 + s / 2.0 + 0.03 * p.xh, 0.78 * p.xh, s, -96.0, 0.0),
        knot(x0 + s / 2.0, 0.34 * p.xh, s).dir(-90.0).k(p.sq),
        knot((x0 + x1) / 2.0, -p.over + h / 2.0, h).dir(0.0).k(p.sq),
        knot(xr, 0.40 * p.xh, s).pen(0.0).dir(90.0).line(),
        knot(xr, yc + 0.30 * (top - yc), s).pen(0.0).dir(90.0).k(p.sq),
        knot((xl + x1) / 2.0, top, h).dir(180.0).k(p.sq),
        knot(xl + s / 2.0, (top + yc) / 2.0, 0.96 * s).dir(-90.0).k(p.sq),
        knot(xl + s / 2.0 + 0.55 * (xr - xl), yc, h).dir(0.0).line(),
        knot(x1 + over, yc, h).pen(90.0),
    ]);
}

fn kappa_sym(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (xa, xb) = (p.xl() + 8.0, p.xr() - 8.0);
    let r = 0.06 * p.xh + s / 2.0;
    // a stem that turns left at the top, a stem that turns right at the foot, and the diagonal between them
    g.stroke(&elbow(xa, 0.0, p.xh, xa - r - 0.02 * p.width, s, h, p.sq, r));
    g.stroke(&elbow(xb, p.xh, 0.0, xb + r + 0.02 * p.width, s, h, p.sq, r));
    g.stroke(&bar(xa - s / 2.0, 0.0, xb + s / 2.0, p.xh, diag_t(p), -1.0, 1.0));
}

fn kai(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (xa, xb) = (p.xl() + 4.0, p.xr() - 4.0);
    g.stroke(&vstem(xa, 0.0, p.xh, s));
    g.stroke(&bar(xa - s / 2.0, 0.0, xb + s / 2.0, p.xh, diag_t(p), -1.0, 1.0));
    // the right stem goes on below the baseline and hooks back to the left, as j's does
    g.stroke(&elbow(xb, p.xh, p.desc, xb - tail_r(p) - 0.06 * p.width, s, h, p.sq, tail_r(p)));
}

fn Kai(g: &mut Draw) {
    let p = g.p;
    let s = p.cap_stem;
    let t = 0.95 * s;
    let x = p.cxl() + 4.0;
    let xe = p.width - p.sb_round + 20.0;
    g.stroke(&vstem(x, 0.0, p.cap, s));
    let ya = 0.36 * p.cap;
    g.stroke(&bar(x, ya, xe, p.cap, t, 0.0, 1.0));
    // the leg leaves the arm and, past the baseline, turns down and ends below it, as ζ's tail does
    let f = 0.34;
    let (xj, yj) = (x + f * (xe - t / 2.0 - x), ya + f * (p.cap - ya));
    let (xf, yf) = (xe - 0.9 * t, 0.14 * p.cap);
    let d = pt(xf - xj, yf - yj).angle();
    g.stroke(&[
        knot(xj, yj, t / (-d).to_radians().sin()).pen(0.0).line(),
        knot(xf, yf, t).dir(d),
        knot(xf + 0.30 * t, 0.30 * p.desc, 0.92 * s).dir(-90.0),
        cut_pen(xf + 0.05 * t, 0.86 * p.desc, 0.86 * s, -104.0, 0.0),
    ]);
}

fn epsilon_lunate(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round + 20.0, p.width - p.sb_round - 18.0);
    let cx = (x0 + x1) / 2.0 + 10.0;
    let (top, bot) = (p.xh + p.over - h / 2.0, -p.over + h / 2.0);
    let white = top - bot - h;
    g.stroke(&[
        cut(x1 - 4.0, top - 0.15 * white, h, 150.0),
        knot(cx, top, h).dir(180.0).k(p.sq),
        knot(x0 + s / 2.0, p.xh / 2.0, s).dir(-90.0).k(p.sq),
        knot(cx, bot, h).dir(0.0),
        cut(x1, bot + 0.15 * white, h, 30.0),
    ]);
    g.stroke(&hbar(x0 + s / 2.0, x1 - 0.24 * (x1 - x0), p.xh / 2.0, 0.92 * h));
}

// ---------------------------------------------------------------------------------------------------------------
// Tonos and dialytika, and the letters that carry them

/// The slope of the tonos, in degrees from the horizontal: nearly upright, as modern Greek type has it.
const TONOS_SLOPE: f64 = 72.0;

/// The tonos's thickness across the stroke: lighter than a stem, as an accent is, but sturdy.
fn tonos_t(p: &Params) -> f64 {
    0.85 * p.hair
}

/// The tonos's height.
fn tonos_h(p: &Params) -> f64 {
    0.30 * p.xh + 0.5 * p.hair
}

/// How far the tonos's centre line leans right over its height.
fn tonos_run(p: &Params) -> f64 {
    tonos_h(p) / TONOS_SLOPE.to_radians().tan()
}

/// The tonos whose bottom cut is centred on (x, y). It thickens a little towards the top, as a pen stroke does.
fn tonos_knots(p: &Params, x: f64, y: f64) -> Vec<Knot> {
    let w = tonos_t(p) / TONOS_SLOPE.to_radians().sin(); // the horizontal cut of a stroke that thick
    vec![knot(x, y, 0.84 * w).pen(0.0).line(), knot(x + tonos_run(p), y + tonos_h(p), 1.16 * w).pen(0.0)]
}

/// The horizontal extent of the tonos whose bottom cut is centred on x: (left, right).
fn tonos_span(p: &Params, x: f64) -> (f64, f64) {
    let w = tonos_t(p) / TONOS_SLOPE.to_radians().sin();
    (x - 0.42 * w, x + tonos_run(p) + 0.58 * w)
}

/// The bottom of a mark over a lowercase letter: as far above the x-height as i's dot.
fn mark_y(p: &Params) -> f64 {
    p.xh + p.xh / 6.0
}

/// The bottom of a mark over a capital.
fn cap_mark_y(p: &Params) -> f64 {
    p.cap + 0.10 * p.xh
}

/// The distance from the middle of a dialytika to the centre of each dot: the dots are i's, a little less than a
/// dot apart.
fn dots_half(p: &Params) -> f64 {
    1.35 * p.dot + 14.0
}

/// How far above the bottom of the dots a tonos between them starts: only its foot stands between them, so they
/// need not be much further apart than a dialytika's.
fn lift(p: &Params) -> f64 {
    0.9 * p.dot
}

/// The horizontal extent, between the heights of the dots, of the tonos that stands between them, from the centre
/// of its bottom cut.
fn foot_span(p: &Params) -> (f64, f64) {
    let w = tonos_t(p) / TONOS_SLOPE.to_radians().sin();
    let k = (2.0 * p.dot - lift(p)) / tonos_h(p); // the share of the tonos's height between the dots
    (-0.42 * w, tonos_run(p) * k + (0.42 + 0.16 * k) * w)
}

/// The distance from the middle of a dialytika tonos to the centre of each dot.
fn dots_half_wide(p: &Params) -> f64 {
    let (l, r) = foot_span(p);
    0.5 * (r - l) + 0.45 * p.dot + p.dot
}

/// Draw a tonos centred on x, with its bottom at y.
fn tonos_at(g: &mut Draw, x: f64, y: f64) {
    let p = g.p;
    g.stroke(&tonos_knots(p, x - tonos_run(p) / 2.0, y));
}

/// Draw a dialytika centred on x, with its bottom at y.
fn dialytika_at(g: &mut Draw, x: f64, y: f64) {
    let p = g.p;
    let d = dots_half(p);
    g.dot(x - d, y + p.dot, p.dot);
    g.dot(x + d, y + p.dot, p.dot);
}

/// Draw a dialytika with a tonos between its dots, centred on x, with its bottom at y.
fn dialytika_tonos_at(g: &mut Draw, x: f64, y: f64) {
    let p = g.p;
    let d = dots_half_wide(p);
    g.dot(x - d, y + p.dot, p.dot);
    g.dot(x + d, y + p.dot, p.dot);
    let (l, r) = foot_span(p);
    g.stroke(&tonos_knots(p, x - (l + r) / 2.0, y + lift(p)));
}

fn tonos(g: &mut Draw) {
    let p = g.p;
    tonos_at(g, p.mid(), mark_y(p));
}

fn dialytika_tonos(g: &mut Draw) {
    let p = g.p;
    dialytika_tonos_at(g, p.mid(), mark_y(p));
}

/// The leftmost and rightmost ink of `glyph` between the heights y0 and y1.
fn ink_between(glyph: &Glyph, y0: f64, y1: f64) -> (f64, f64) {
    let (mut lo, mut hi) = (f64::INFINITY, f64::NEG_INFINITY);
    for seg in glyph.contours.iter().flat_map(|c| c.segs.iter()) {
        for i in 0..=48 {
            let z = seg.at(f64::from(i) / 48.0);
            if z.y >= y0 && z.y <= y1 {
                lo = lo.min(z.x);
                hi = hi.max(z.x);
            }
        }
    }
    (lo, hi)
}

/// Which marks a letter carries.
#[derive(Clone, Copy)]
enum Mark {
    Tonos,
    Dialytika,
    Both,
}

/// A lowercase letter with a mark: the base as a component, with its advance, and the mark centred over the part
/// of it that stands between the x-height and half of it (over ι, a little right of its stem, towards its foot).
fn lower_marked(g: &mut Draw, base: char, mark: Mark) {
    let p = g.p;
    let upright = Params { slant: 0.0, ..p.clone() };
    let Some(b) = g.glyph_as(&name_of(base), &upright) else {
        g.glyph.errors.push(format!("no base {base}"));
        return;
    };
    let (lo, hi) = ink_between(&b, 0.5 * p.xh, p.xh + p.over);
    let x = if base == 'ι' { lo + p.stem / 2.0 + 0.2 * iota_foot(p) } else { (lo + hi) / 2.0 };
    g.use_char(base, 0.0, 0.0);
    g.glyph.advance = b.advance;
    match mark {
        Mark::Tonos => tonos_at(g, x, mark_y(p)),
        Mark::Dialytika => dialytika_at(g, x, mark_y(p)),
        Mark::Both => dialytika_tonos_at(g, x, mark_y(p)),
    }
}

/// A capital with a tonos. The tonos stands to the upper left of the letter, a third of it beside the letter's
/// top and the rest above; the letter moves right until, at every height they share, its ink is a stated distance
/// from the tonos. In the fixed-pitch cell the letter is drawn narrower by as much as it moves, less part of its
/// right sidebearing, so that both fit the cell; in the proportional family the cell grows instead.
fn cap_tonos(g: &mut Draw, base: char) {
    let p = g.p;
    let name = name_of(base);
    let upright = Params { slant: 0.0, ..p.clone() };
    let (h, run) = (tonos_h(p), tonos_run(p));
    let yb = p.cap - 0.35 * h;
    let w = tonos_t(p) / TONOS_SLOPE.to_radians().sin();
    let x = 0.42 * w + 0.10 * p.cap_sb; // the tonos's bottom cut: its left edge keeps that margin
    let clear = 0.35 * p.cap_sb;
    let bases = |q: &Params| g.glyph_as(&name, q).unwrap_or_default();
    // how far the letter as `q` draws it must move right to clear the tonos
    let shift = |b: &Glyph| -> f64 {
        let mut need = f64::NEG_INFINITY;
        for i in 0..=10 {
            let f = 0.35 * f64::from(i) / 10.0;
            let y = yb + f * h;
            let edge = x + f * run + (0.42 + 0.16 * f) * w; // the tonos's right edge at this height
            let (lo, _) = ink_between(b, y - 0.03 * h, y + 0.03 * h);
            need = need.max(edge + clear - lo);
        }
        // Α's apex is far right of the tonos at every weight, so it never moves; every other letter must
        need.max(0.0)
    };
    let b = bases(&upright);
    let mut dx = shift(&b);
    if p.mono {
        let rsb = b.advance - b.bounds().map_or(b.advance, |bb| bb.2);
        let narrow = |dx: f64| Params { width: p.width - dx + 0.4 * rsb, ..upright.clone() };
        for _ in 0..3 {
            dx = shift(&bases(&narrow(dx)));
        }
        g.draw_as(&name, &Params { slant: p.slant, ..narrow(dx) }, dx, 0.0);
    } else {
        g.use_char(base, dx, 0.0);
        g.glyph.advance = b.advance + dx;
    }
    g.stroke(&tonos_knots(p, x, yb));
}

/// A capital with a dialytika, centred over the letter's top.
fn cap_dialytika(g: &mut Draw, base: char) {
    let p = g.p;
    let upright = Params { slant: 0.0, ..p.clone() };
    let Some(b) = g.glyph_as(&name_of(base), &upright) else {
        g.glyph.errors.push(format!("no base {base}"));
        return;
    };
    let (lo, hi) = ink_between(&b, 0.5 * p.cap, p.cap + p.over);
    g.use_char(base, 0.0, 0.0);
    g.glyph.advance = b.advance;
    dialytika_at(g, (lo + hi) / 2.0, cap_mark_y(p));
}

/// The Greek letters with a mark, each with its base and its mark.
const MARKED: [(char, char, Mark); 13] = [
    ('ά', 'α', Mark::Tonos),
    ('έ', 'ε', Mark::Tonos),
    ('ή', 'η', Mark::Tonos),
    ('ί', 'ι', Mark::Tonos),
    ('ό', 'ο', Mark::Tonos),
    ('ύ', 'υ', Mark::Tonos),
    ('ώ', 'ω', Mark::Tonos),
    ('ϊ', 'ι', Mark::Dialytika),
    ('ϋ', 'υ', Mark::Dialytika),
    ('ΐ', 'ι', Mark::Both),
    ('ΰ', 'υ', Mark::Both),
    ('Ϊ', 'Ι', Mark::Dialytika),
    ('Ϋ', 'Υ', Mark::Dialytika),
];

/// The capitals with a tonos, and their bases.
const CAP_TONOS: [(char, char); 7] =
    [('Ά', 'Α'), ('Έ', 'Ε'), ('Ή', 'Η'), ('Ί', 'Ι'), ('Ό', 'Ο'), ('Ύ', 'Υ'), ('Ώ', 'Ω')];

// ---------------------------------------------------------------------------------------------------------------
// Signs

/// The keraia, the numeral sign: the tonos's stroke at the top of the capitals.
fn numeral_sign(g: &mut Draw) {
    let p = g.p;
    g.stroke(&tonos_knots(p, p.mid() - tonos_run(p) / 2.0, p.cap - tonos_h(p)));
}

/// The lower numeral sign: the same stroke, below the baseline.
fn lower_numeral_sign(g: &mut Draw) {
    let p = g.p;
    g.stroke(&tonos_knots(p, p.mid() - tonos_run(p) / 2.0, -tonos_h(p) - 0.5 * p.over));
}

fn question_greek(g: &mut Draw) {
    g.same_as_char(';');
}

/// The ano teleia, the Greek semicolon: a dot as high as the colon's upper one.
fn ano_teleia(g: &mut Draw) {
    let p = g.p;
    g.dot(p.mid(), p.xh + p.over - p.punct, p.punct);
}

pub fn register(reg: &mut Registry) {
    reg.module("greek");
    for (greek, latin) in SAME {
        reg.ch(greek, move |g: &mut Draw| g.same_as_char(latin));
    }
    reg.ch('Γ', Gamma);
    reg.ch('Δ', Delta);
    reg.ch('Λ', Lambda);
    reg.ch('Θ', Theta);
    reg.ch('Ξ', Xi);
    reg.ch('Π', Pi);
    reg.ch('Σ', Sigma);
    reg.ch('Φ', Phi);
    reg.ch('Ψ', Psi);
    reg.ch('Ω', Omega);
    reg.ch('\u{2126}', ohm); // the ohm sign
    reg.ch('ο', omicron);
    reg.ch('α', alpha);
    reg.ch('β', beta);
    reg.ch('γ', gamma);
    reg.ch('δ', delta);
    reg.ch('ε', epsilon);
    reg.ch('ζ', zeta);
    reg.ch('ξ', xi);
    reg.ch('η', eta);
    reg.ch('θ', theta);
    reg.ch('ι', iota);
    reg.ch('κ', kappa);
    reg.ch('λ', lambda_);
    reg.ch('μ', mu);
    reg.ch('µ', micro); // the micro sign
    reg.ch('ν', nu);
    reg.ch('π', pi);
    reg.ch('ρ', rho);
    reg.ch('ς', sigma_final);
    reg.ch('σ', sigma);
    reg.ch('τ', tau);
    reg.ch('υ', upsilon);
    reg.ch('φ', phi);
    reg.ch('χ', chi);
    reg.ch('ψ', psi);
    reg.ch('ω', omega);
    reg.ch('ϑ', theta_sym);
    reg.ch('ϕ', phi_sym);
    reg.ch('ϖ', pi_sym);
    reg.ch('ϰ', kappa_sym);
    reg.ch('ϱ', rho_sym);
    reg.ch('ϵ', epsilon_lunate);
    reg.ch('ϗ', kai);
    reg.ch('Ϗ', Kai);
    reg.ch('\u{0384}', tonos);
    reg.ch('\u{0385}', dialytika_tonos);
    reg.ch('\u{0374}', numeral_sign);
    reg.ch('\u{0375}', lower_numeral_sign);
    reg.ch('\u{037e}', question_greek);
    reg.ch('\u{0387}', ano_teleia);
    for (c, base, mark) in MARKED {
        reg.ch(
            c,
            move |g: &mut Draw| {
                if base.is_uppercase() { cap_dialytika(g, base) } else { lower_marked(g, base, mark) }
            },
        );
    }
    for (c, base) in CAP_TONOS {
        reg.ch(c, move |g: &mut Draw| cap_tonos(g, base));
    }
}

/// The proportional family's cells for this module's glyphs, in the Latin's terms: n is two stems and a counter
/// (`Fit::letter(p, 2.0, 1.0)`), and a round letter takes n's cell and the round sidebearing inside it. A capital
/// counts the capital's sidebearings and stems. A letter that is another glyph, or a letter with a mark, takes
/// its base's advance in its program.
pub fn fit(name: &str, p: &Params) -> Option<Fit> {
    let c = name.strip_prefix("uni").and_then(|h| u32::from_str_radix(h, 16).ok()).and_then(char::from_u32)?;
    let lc = |stems: f64, counters: f64| Some(Fit::letter(p, stems, counters));
    let cap = |stems: f64, counters: f64| Some(Fit::new(2.0 * p.cap_sb + stems * p.cap_stem + counters * p.counter));
    // a sign: the ink and a sidebearing on each side
    let sign = |ink: f64| Some(Fit::new(2.0 * p.sb + ink));
    let (l, r) = tonos_span(p, 0.0);
    match c {
        'Γ' => cap(1.0, 1.15),
        'Δ' | 'Λ' => cap(2.0, 1.45),
        'Θ' | 'Ω' => cap(2.0, 1.5),
        'Ξ' | 'Σ' => cap(2.0, 1.2),
        'Π' => cap(2.0, 1.35),
        'Φ' | 'Ψ' => cap(3.0, 1.55),
        'Ϗ' => cap(2.0, 1.3),
        'α' => lc(2.0, 1.15),
        'β' | 'γ' | 'δ' | 'ν' | 'θ' | 'κ' => lc(2.0, 0.95),
        'ε' | 'ζ' | 'ξ' | 'ϵ' => lc(2.0, 0.75),
        'ς' => lc(2.0, 0.7),
        'τ' => lc(2.0, 0.8),
        'η' | 'λ' | 'μ' | 'ρ' | 'υ' | 'χ' | 'ϑ' | 'ϰ' | 'ϱ' | 'ϗ' => lc(2.0, 1.0),
        'π' | 'σ' => lc(2.0, 1.2),
        'ι' => lc(1.0, 0.45),
        'φ' | 'ψ' | 'ϕ' => lc(3.0, 1.45),
        'ω' | 'ϖ' => lc(3.0, 1.6),
        '\u{0384}' | '\u{0374}' | '\u{0375}' => sign(r - l),
        '\u{0385}' => sign(2.0 * (dots_half_wide(p) + p.dot)),
        '\u{0387}' => sign(2.0 * p.punct),
        _ => None,
    }
}
