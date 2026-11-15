//! Greek, and the letters mathematics borrows: variant Greek forms, double-struck capitals, ℓ, ℏ, ℵ.
//!
//! The Greek is the Latin's typeface: the same strokes, heights and superellipse. A capital that has the shape of a
//! Latin capital is that glyph as a component. Letters with three vertical strokes in the cell (Φ Ψ φ ψ ω) take the
//! thinner stroke of `_three`, as m and w do.

// The programs keep the Python names, and the Greek capitals and lowercase differ only in case (Gamma, gamma).
#![allow(non_snake_case)]

use rachis_kernel::{Draw, Knot, Params, Registry, V, knot, pt};

use crate::parts::{Arch, Bowl, arch, bowl, cut, cut_pen, diag, elbow, hbar, mirror, ring, turn, vee, vstem};

// ---------------------------------------------------------------------------------------------------------------
// Measurements this group derives from the parameters.

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
    g.use_char('\u{03a9}', 0.0, 0.0);
}

// ---------------------------------------------------------------------------------------------------------------
// Lowercase

fn omicron(g: &mut Draw) {
    g.use_char('o', 0.0, 0.0);
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
    let x0 = p.sb_round + 36.0;
    g.stroke_closed(&ring(x0, -p.over, p.width - x0, p.asc + p.over, p.stem, p.hair, p.sq));
    g.stroke(&hbar(x0 + p.stem / 2.0, p.width - x0 - p.stem / 2.0, p.asc / 2.0, p.hair * 0.94));
}

fn iota(g: &mut Draw) {
    let p = g.p;
    g.stroke(&elbow(p.mid() - 40.0, p.xh, 0.0, p.width - p.sb_round - 50.0, p.stem, p.hair, p.sq, 112.0));
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
    g.use_char('μ', 0.0, 0.0);
}

pub fn register(reg: &mut Registry) {
    reg.module("greek");
    for (greek, latin) in SAME {
        reg.ch(greek, move |g: &mut Draw| g.use_char(latin, 0.0, 0.0));
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
}
