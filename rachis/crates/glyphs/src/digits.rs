//! Figures: the ten digits, their superior and inferior forms with the signs that accompany them, and the fractions.
//!
//! Every figure is a construction in a `Frame`: a box, the strokes to draw with and the overshoot. The full-size
//! figures, the superiors and the numerators and denominators of the fractions are the same ten constructions in
//! four frames, each with strokes of its own, so a small figure is drawn for its size and is not a reduced outline.
//! An inferior is its superior, lowered.

use rachis_kernel::{Draw, Knot, Params, Registry, V, knot, pt};

use crate::parts::{Arch, arch, cut, cut_pen, hbar, mirror, ring, turn, vstem};

// ---------------------------------------------------------------------------------------------------------------
// frames

/// The box a figure is drawn in and the pen it is drawn with. Flat strokes touch `y0` and `y1`; round ones
/// pass them by `over`. A position inside it is a fraction of its width or height (`x`, `y`).
#[derive(Clone, Copy, Debug)]
struct Frame {
    x0: f64,
    x1: f64,
    y0: f64,
    y1: f64,
    stem: f64, // vertical strokes, and bowls at their sides
    hair: f64, // horizontal strokes, and bowls at their top and bottom
    over: f64,
    sq: f64,   // squareness of bowls
    join: f64, // breadth of a bowl where it leaves a stem, as a fraction of the stem
}

impl Frame {
    fn w(&self) -> f64 {
        self.x1 - self.x0
    }

    fn h(&self) -> f64 {
        self.y1 - self.y0
    }

    fn cx(&self) -> f64 {
        (self.x0 + self.x1) / 2.0
    }

    fn cy(&self) -> f64 {
        (self.y0 + self.y1) / 2.0
    }

    /// The outer edge of a round top.
    fn top(&self) -> f64 {
        self.y1 + self.over
    }

    /// The outer edge of a round bottom.
    fn bot(&self) -> f64 {
        self.y0 - self.over
    }

    fn x(&self, t: f64) -> f64 {
        self.x0 + t * self.w()
    }

    fn y(&self, t: f64) -> f64 {
        self.y0 + t * self.h()
    }
}

// Proportions of the small forms. A superior is SMALL_H of the cap height tall and SMALL_W of a full-size figure
// wide, which is 0.62 of the advance in the Regular. A fraction's digits are narrower, to leave room for its bar.
const SMALL_H: f64 = 0.56;
const SMALL_W: f64 = 0.92;
const SMALL_RISE: f64 = 40.0; // a superior's top above the cap height, and an inferior's bottom above the descender
const FRAC_H: f64 = 0.52;
const FRAC_W: f64 = 0.42; // of the advance
const FRAC_EDGE: f64 = 18.0; // from the cell's side to a fraction's digit
const FIG_SQ: f64 = 0.02; // figures are a little squarer than the lowercase, as the capitals are
const ZERO_SQ: f64 = 0.01; // and the zero a little more: a tall narrow ring looks pointed

/// The vertical stroke of the small forms: about 0.72 of the full-size stroke in the Regular. It gains weight
/// more slowly than the text does, so that the Light survives at 13 px and small counters stay open in the Bold.
fn small_stem(p: &Params) -> f64 {
    0.435 * p.stem + 30.0
}

fn small_hair(p: &Params) -> f64 {
    0.47 * p.hair + 25.0
}

fn full(p: &Params) -> Frame {
    Frame {
        x0: p.fig_sb,
        x1: p.width - p.fig_sb,
        y0: 0.0,
        y1: p.cap,
        stem: p.cap_stem,
        hair: p.cap_hair,
        over: p.over,
        sq: p.sq + FIG_SQ,
        join: p.join,
    }
}

fn small(p: &Params, x0: f64, x1: f64, y0: f64, y1: f64) -> Frame {
    Frame {
        x0,
        x1,
        y0,
        y1,
        stem: small_stem(p),
        hair: small_hair(p),
        over: 0.6 * p.over,
        sq: p.sq + FIG_SQ,
        join: p.join,
    }
}

fn superior(p: &Params) -> Frame {
    let half = SMALL_W * (p.width / 2.0 - p.fig_sb);
    let top = p.cap + SMALL_RISE;
    small(p, p.mid() - half, p.mid() + half, top - SMALL_H * p.cap, top)
}

/// How far an inferior sits below the superior it repeats.
fn inferior_shift(p: &Params) -> f64 {
    (p.desc + SMALL_RISE) - (p.cap + SMALL_RISE - SMALL_H * p.cap)
}

fn numerator(p: &Params) -> Frame {
    let top = p.cap + SMALL_RISE;
    small(p, FRAC_EDGE, FRAC_EDGE + FRAC_W * p.width, top - FRAC_H * p.cap, top)
}

fn denominator(p: &Params) -> Frame {
    let bottom = p.desc + SMALL_RISE;
    small(p, p.width - FRAC_EDGE - FRAC_W * p.width, p.width - FRAC_EDGE, bottom, bottom + FRAC_H * p.cap)
}

// ---------------------------------------------------------------------------------------------------------------
// parts

/// `parts::diag` with an end given by a corner instead of its centre: a straight stroke `t` thick from
/// height `ay` to `by`, cut flat. `ax` is the stroke's left corner at that end when `a_side` is -1, its
/// right corner when +1 and its centre when 0; likewise `bx` and `b_side`. (The same part as `bar` in the
/// lowercase: a candidate for parts.py.)
fn diag_from(ax: f64, ay: f64, bx: f64, by: f64, t: f64, a_side: f64, b_side: f64) -> Vec<Knot> {
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

// ---------------------------------------------------------------------------------------------------------------
// the ten constructions

fn draw_zero_ring(g: &mut Draw, f: Frame) {
    g.stroke_closed(&ring(f.x0, f.bot(), f.x1, f.top(), f.stem, f.hair, f.sq + ZERO_SQ));
}

/// A ring and a slash from lower left to upper right. The slash is the diagonal of the box of the ring's centre
/// line, as far as the middle of the ring's corners: it joins the ring from inside and never reaches its outer
/// edge. Its breadth follows the counter as well as the pen, so that a bold counter stays open beside it.
fn draw_zero(g: &mut Draw, f: Frame) {
    draw_zero_ring(g, f);
    let counter = f.w() - 2.0 * f.stem;
    let t = 0.50 * f.hair + 0.11 * counter;
    let m = 0.5 + 0.375 * (f.sq + ZERO_SQ); // where a superelliptic corner crosses the diagonal of its box
    let (dx, dy) = (m * (f.w() - f.stem) / 2.0, m * (f.h() + 2.0 * f.over - f.hair) / 2.0);
    g.stroke(&[knot(f.cx() - dx, f.cy() - dy, t).line(), knot(f.cx() + dx, f.cy() + dy, t)]);
}

fn draw_zero_dot(g: &mut Draw, f: Frame) {
    draw_zero_ring(g, f);
    let rx = 0.92 * f.stem * (f.w() - 2.0 * f.stem) / f.w(); // follows the counter, as the slash does
    let k = g.p.dot_k;
    g.dot_xy(f.cx(), f.cy(), rx, 1.6 * rx, k);
}

/// A stem, a diagonal flag cut flat, and a foot on both sides.
fn draw_one(g: &mut Draw, f: Frame) {
    let (s, h) = (f.stem, f.hair);
    let x = f.cx() + 0.04 * f.w();
    g.stroke(&vstem(x, f.y0, f.y1, s));
    g.stroke(&hbar(f.x(0.015), f.x(0.985), f.y0 + h / 2.0, h));
    g.stroke(&diag_from(x + s / 2.0, f.y1, f.x(0.03), f.y(0.765), h, 1.0, -1.0));
}

/// A round top, a straight neck and a flat base.
fn draw_two(g: &mut Draw, f: Frame) {
    let (s, h) = (f.stem, f.hair);
    let neck = diag_from(f.x(0.60), f.y(0.40), f.x0, f.y0, 0.96 * s, 0.0, -1.0);
    let mut knots = vec![
        cut(f.x(0.03), f.y(0.79), h * 1.04, 44.0),
        knot(f.x(0.49), f.top() - h / 2.0, h).dir(0.0).k(f.sq),
        knot(f.x(0.98) - s / 2.0, f.y(0.705), s).dir(-90.0),
    ];
    knots.extend_from_slice(&neck);
    g.stroke(&knots);
    g.stroke(&hbar(f.x0, f.x1, f.y0 + h / 2.0, h));
}

/// Two bowls open to the left that share a waist stroke; the upper one is smaller.
fn draw_three(g: &mut Draw, f: Frame) {
    let (s, h) = (f.stem, f.hair);
    let yw = f.y(0.535);
    let (top, bot) = (f.top() - h / 2.0, f.bot() + h / 2.0);
    let (xw, xj) = (f.x(0.36), f.x(0.52));
    g.stroke(&[
        cut(f.x(0.05), f.y(0.805), h * 1.04, 42.0),
        knot(f.x(0.47), top, h).dir(0.0).k(f.sq),
        knot(f.x(0.95) - s / 2.0, (top + yw) / 2.0, s).dir(-90.0).k(f.sq),
        knot(xj, yw, h).pen(90.0).dir(180.0).line(),
        knot(xw, yw, h).pen(90.0),
    ]);
    g.stroke(&[
        knot(xw, yw, h).pen(90.0).line(),
        knot(xj, yw, h).pen(90.0).dir(0.0).k(f.sq),
        knot(f.x1 - s / 2.0, (yw + bot) / 2.0, s).dir(-90.0).k(f.sq),
        knot(f.x(0.47), bot, h).dir(180.0),
        cut(f.x(0.0), f.y(0.19), h * 1.04, 138.0),
    ]);
}

/// Closed: a diagonal, a bar that runs past the stem, and the stem.
fn draw_four(g: &mut Draw, f: Frame) {
    let (s, h) = (f.stem, f.hair);
    let xs = f.x(0.90) - s / 2.0;
    let yb = f.y(0.225);
    g.stroke(&vstem(xs, f.y0, f.y1, s));
    g.stroke(&hbar(f.x(-0.04), f.x(1.04), yb, h));
    g.stroke(&diag_from(f.x(-0.04), yb - h / 2.0, xs + s / 2.0, f.y1, 1.06 * h, -1.0, 1.0));
}

/// A flat top, a sharp corner, a short stem, and a bowl that leaves it as an arch.
fn draw_five(g: &mut Draw, f: Frame) {
    let (s, h) = (f.stem, f.hair);
    let xs = f.x(0.09) + s / 2.0;
    let yt = f.y(0.63); // the bowl's outer top
    let branch = f.y(0.47);
    g.stroke(&hbar(xs - s / 2.0, f.x(0.94), f.y1 - h / 2.0, h));
    g.stroke(&vstem(xs, branch, f.y1, s));
    let j = f.join * s;
    let spring = 52.0;
    g.stroke(&[
        Knot::at(pt(xs + s / 2.0 - 3.0, branch) + (V::unit(spring) * (j / 2.0)).left(), j).dir(spring),
        knot(f.x(0.52), yt - h / 2.0, h).dir(0.0).k(f.sq),
        knot(f.x1 - s / 2.0, (yt + f.bot()) / 2.0 - 0.01 * f.h(), s).dir(-90.0).k(f.sq),
        knot(f.x(0.47), f.bot() + h / 2.0, h).dir(180.0),
        cut(f.x(-0.01), f.y(0.185), h * 1.04, 140.0),
    ]);
}

/// The skeleton of 6: from the terminal at the top right down the back, round the bowl and into the back
/// again. 9 is the same skeleton turned.
fn six(f: Frame) -> Vec<Knot> {
    let (s, h) = (f.stem, f.hair);
    let yb = f.y(0.62); // the bowl's outer top
    let j = f.join * s;
    let arrive = 180.0 + 46.0;
    let end = pt(f.x0 + s - 3.0, f.y(0.455)) - (V::unit(arrive) * (j / 2.0)).left();
    vec![
        cut(f.x(0.93), f.y(0.83), h * 1.04, 142.0),
        knot(f.x(0.53), f.top() - h / 2.0, h).dir(180.0).k(f.sq),
        knot(f.x0 + s / 2.0, f.y(0.44), s).dir(-90.0).k(f.sq),
        knot(f.x(0.51), f.bot() + h / 2.0, h).dir(0.0).k(f.sq),
        knot(f.x1 - s / 2.0, (yb + f.bot()) / 2.0, s).dir(90.0).k(f.sq),
        knot(f.x(0.54), yb - h / 2.0, h).dir(180.0),
        Knot::at(end, j).dir(arrive),
    ]
}

fn draw_six(g: &mut Draw, f: Frame) {
    g.stroke(&six(f));
}

/// A flat top and a straight leg cut flat.
fn draw_seven(g: &mut Draw, f: Frame) {
    let (s, h) = (f.stem, f.hair);
    g.stroke(&hbar(f.x0, f.x1, f.y1 - h / 2.0, h));
    g.stroke(&diag_from(f.x1, f.y1, f.x(0.36), f.y0, 0.96 * s, 1.0, 0.0));
}

/// Two rings that share the stroke at the waist; the upper one is smaller and narrower.
fn draw_eight(g: &mut Draw, f: Frame) {
    let (s, h) = (f.stem, f.hair);
    let yw = f.y(0.535);
    let inset = 0.05 * f.w();
    g.stroke_closed(&ring(f.x0, f.bot(), f.x1, yw + h / 2.0, s, h, f.sq));
    g.stroke_closed(&ring(f.x0 + inset, yw - h / 2.0, f.x1 - inset, f.top(), 0.96 * s, h, f.sq));
}

fn draw_nine(g: &mut Draw, f: Frame) {
    g.stroke(&turn(&six(f), f.cx(), f.cy()));
}

type Construction = fn(&mut Draw, Frame);

const DRAW: [(char, Construction); 10] = [
    ('0', draw_zero),
    ('1', draw_one),
    ('2', draw_two),
    ('3', draw_three),
    ('4', draw_four),
    ('5', draw_five),
    ('6', draw_six),
    ('7', draw_seven),
    ('8', draw_eight),
    ('9', draw_nine),
];

/// The construction of `digit` in [`DRAW`] (the Python dict lookup `DRAW[digit]`).
fn draw_of(digit: char) -> Construction {
    DRAW.iter().find(|&&(c, _)| c == digit).map(|&(_, draw)| draw).expect("a digit")
}

// ---------------------------------------------------------------------------------------------------------------
// the signs and letters that accompany the small figures

const SMALL_SPAN: f64 = 0.62; // a small sign's span, as a fraction of the full-size operators' span

/// The small operators' axis: as far up the small figures as the axis is up the full-size ones.
fn small_axis(p: &Params, f: Frame) -> f64 {
    f.y(p.axis / p.cap)
}

fn small_half_span(p: &Params) -> f64 {
    SMALL_SPAN * (p.width / 2.0 - p.op_l)
}

fn draw_small_minus(g: &mut Draw, f: Frame) {
    let p = g.p;
    let r = small_half_span(p);
    g.stroke(&hbar(p.mid() - r, p.mid() + r, small_axis(p, f), f.hair));
}

fn draw_small_plus(g: &mut Draw, f: Frame) {
    let p = g.p;
    let r = small_half_span(p);
    let y = small_axis(p, f);
    g.stroke(&hbar(p.mid() - r, p.mid() + r, y, f.hair));
    g.stroke(&vstem(p.mid(), y - r, y + r, f.hair));
}

fn draw_small_equal(g: &mut Draw, f: Frame) {
    let p = g.p;
    let r = small_half_span(p);
    let y = small_axis(p, f);
    let d = (0.10 * f.h() + 1.35 * f.hair) / 2.0; // half the distance between the bars' centre lines
    g.stroke(&hbar(p.mid() - r, p.mid() + r, y + d, f.hair));
    g.stroke(&hbar(p.mid() - r, p.mid() + r, y - d, f.hair));
}

/// The opening parenthesis of the small forms: an arc cut flat at its ends, a little taller and deeper than
/// the small figures, as the full-size one is than the full-size figures.
fn small_paren(f: Frame) -> Vec<Knot> {
    let (y_top, y_bot) = (f.y(1.08), f.y(-0.14));
    let te = 0.95 * f.hair;
    let slope = 41.0; // the angle of the arc at its ends, from the horizontal
    let x_tip = f.x(0.80); // the right end of the cuts
    let half_cut = cut_pen(0.0, 0.0, te, -180.0 + slope, 0.0).w / 2.0;
    vec![
        cut_pen(x_tip - half_cut, y_top, te, -180.0 + slope, 0.0).k(f.sq),
        knot(f.x(0.27) + 0.46 * f.stem, (y_top + y_bot) / 2.0, 0.92 * f.stem).dir(-90.0).k(f.sq),
        cut_pen(x_tip - half_cut, y_bot, te, -slope, 0.0),
    ]
}

fn draw_small_parenleft(g: &mut Draw, f: Frame) {
    g.stroke(&small_paren(f));
}

fn draw_small_parenright(g: &mut Draw, f: Frame) {
    g.stroke(&mirror(&small_paren(f), f.cx()));
}

/// The height of a small lowercase letter above the small figures' baseline.
fn small_xh(p: &Params, f: Frame) -> f64 {
    f.h() * p.xh / p.cap
}

fn draw_small_n(g: &mut Draw, f: Frame) {
    let p = g.p;
    let s = f.stem;
    let xh = small_xh(p, f);
    let (xl, xr) = (f.x(0.10) + s / 2.0, f.x(0.90) - s / 2.0);
    g.stroke(&vstem(xl, f.y0, f.y0 + xh, s));
    g.stroke(&arch(
        p,
        xl,
        xr,
        f.y0 + xh + f.over,
        f.y0,
        Arch { stem: Some(s), hair: Some(f.hair), branch: Some(f.y0 + 0.68 * xh), ..Arch::default() },
    ));
}

fn draw_small_i(g: &mut Draw, f: Frame) {
    let p = g.p;
    let (s, h) = (f.stem, f.hair);
    let xh = small_xh(p, f);
    let x = f.cx() + 0.03 * f.w();
    let r = 0.5 * p.dot + 12.0; // the dot, reduced as the strokes are
    g.stroke(&vstem(x, f.y0, f.y0 + xh, s));
    g.stroke(&hbar(f.x(0.12), x, f.y0 + xh - h / 2.0, h));
    g.stroke(&hbar(f.x(0.10), f.x(0.90), f.y0 + h / 2.0, h));
    g.dot(x - 0.25 * s, f.y0 + xh + xh / 6.0 + r, r);
}

// ---------------------------------------------------------------------------------------------------------------
// glyphs

fn figure(reg: &mut Registry, digit: char, sup: char, inf: char) {
    let draw = draw_of(digit);
    reg.ch(digit, move |g: &mut Draw| {
        let p = g.p;
        draw(g, full(p));
    });
    small_pair(reg, draw, sup, Some(inf));
}

/// A superior form and, where there is one, the inferior that repeats it lower down.
fn small_pair(reg: &mut Registry, draw: Construction, sup: char, inf: Option<char>) {
    reg.ch(sup, move |g: &mut Draw| {
        let p = g.p;
        draw(g, superior(p));
    });
    let Some(inf) = inf else {
        return;
    };
    reg.ch(inf, move |g: &mut Draw| {
        let p = g.p;
        g.use_char(sup, 0.0, inferior_shift(p));
    });
}

fn zero_dot(g: &mut Draw) {
    let p = g.p;
    draw_zero_dot(g, full(p));
}

fn zero_plain(g: &mut Draw) {
    let p = g.p;
    draw_zero_ring(g, full(p));
}

/// A small numerator at the top left, a small denominator at the bottom right, and a bar between them.
fn fraction(reg: &mut Registry, character: char, over: char, under: char) {
    reg.ch(character, move |g: &mut Draw| {
        let p = g.p;
        let (n, d) = (numerator(p), denominator(p));
        draw_of(over)(g, n);
        draw_of(under)(g, d);
        // the bar passes midway between the numerator's lower right corner and the denominator's upper left one
        let (cx, cy) = ((n.x1 + d.x0) / 2.0, (n.y0 + d.y1) / 2.0);
        let rise = 0.30 * (n.y1 - d.y0);
        let run = rise / 52.0_f64.to_radians().tan();
        g.stroke(&diag_from(cx - run, cy - rise, cx + run, cy + rise, 0.9 * n.hair, 0.0, 0.0));
    });
}

pub fn register(reg: &mut Registry) {
    reg.module("digits");
    for ((digit, sup), inf) in "0123456789".chars().zip("⁰¹²³⁴⁵⁶⁷⁸⁹".chars()).zip("₀₁₂₃₄₅₆₇₈₉".chars())
    {
        figure(reg, digit, sup, inf);
    }
    small_pair(reg, draw_small_plus, '⁺', Some('₊'));
    small_pair(reg, draw_small_minus, '⁻', Some('₋'));
    small_pair(reg, draw_small_equal, '⁼', Some('₌'));
    small_pair(reg, draw_small_parenleft, '⁽', Some('₍'));
    small_pair(reg, draw_small_parenright, '⁾', Some('₎'));
    small_pair(reg, draw_small_n, 'ⁿ', None);
    small_pair(reg, draw_small_i, 'ⁱ', None);
    reg.named("zero.dot", zero_dot);
    reg.named("zero.plain", zero_plain);
    fraction(reg, '½', '1', '2');
    fraction(reg, '¼', '1', '4');
    fraction(reg, '¾', '3', '4');
}
