//! Typographic spaces, invisible characters, the rarer punctuation of General Punctuation, and currency signs.
//!
//! Spaces. In the fixed-pitch family every space that takes room takes one cell, because that is what a terminal
//! assumes; in the proportional family each has its typographic width (`fit`). The zero-width characters have no
//! advance in either.
//!
//! Punctuation is built from the glyphs of punct.rs, so that it matches them: the leaders are the period's dot,
//! the reversed primes are the primes mirrored, the double low line is two underscores. Where punct.rs keeps a
//! measurement private, it is copied here with the same number (the prime's drop, the question mark's hook).
//!
//! Currency signs keep the figures' cell in both families and stand on the baseline, as tall as the capitals.
//! A sign that is a capital with bars (₽ ₮ ₦ ₩ ₱ ₭ ₲ ₡ ₣ ₿ ฿ ₵) places the capital as a component and draws the
//! bars over it, measured from the capital as its own program draws it, so it follows the capital when that
//! changes. Bars are `bar_t`, thinner than the capitals' hair and growing more slowly, so that the counters they
//! cross stay open in the Bold. Ticks above and below a letter, as in $ and ¢, stand outside it and do not cross
//! its counters.

use rachis_kernel::{Contour, Draw, Fit, Glyph, Knot, Opt, Params, Registry, knot, name_of, name_of_code, pt};

use crate::operators::rake;
use crate::parts::{cut, cut_pen, dbowl, diag, elbow, hbar, vstem};
use crate::punct::{dot_y, mark_foot, quote_bar, small_strokes};

// ---------------------------------------------------------------------------------------------------------------
// measurements of this group

/// The bars and slashes that cross a currency sign's letter.
fn bar_t(p: &Params) -> f64 {
    0.55 * p.cap_hair + 24.0
}

/// The ticks above and below a letter, as in $: lighter than its stem.
fn tick_t(p: &Params) -> f64 {
    0.62 * p.cap_stem + 10.0
}

/// How far the ticks of $ reach beyond the letter (punct.rs).
const TICK_REACH: f64 = 96.0;

/// The height of the straight quotes and primes (punct.rs `QUOTE_DROP`).
const QUOTE_DROP: f64 = 300.0;

// ---------------------------------------------------------------------------------------------------------------
// building on other glyphs

/// The glyph of `c` as this master draws it, upright: for measuring it, or for drawing it mirrored.
fn upright(g: &Draw, c: char) -> Option<Glyph> {
    let up = Params { slant: 0.0, ..g.p.clone() };
    g.glyph_as(&name_of(c), &up)
}

/// Place the glyph of `c` as a component, centred in this glyph's cell, and return its upright bounds there.
fn base(g: &mut Draw, c: char) -> (f64, f64, f64, f64) {
    let p = g.p;
    let Some(glyph) = upright(g, c) else {
        g.glyph.errors.push(format!("no glyph for {c:?}"));
        return (0.0, 0.0, p.width, p.cap);
    };
    let dx = (p.width - glyph.advance) / 2.0;
    g.use_char(c, dx, 0.0);
    let (x0, y0, x1, y1) = glyph.bounds().unwrap_or((0.0, 0.0, glyph.advance, p.cap));
    (x0 + dx, y0, x1 + dx, y1)
}

/// The glyph of `c` mirrored left to right, centred in this glyph's cell (an italic slants the result as it slants
/// everything else). Returns its upright bounds here.
fn mirrored(g: &mut Draw, c: char) -> (f64, f64, f64, f64) {
    let p = g.p;
    let Some(glyph) = upright(g, c) else {
        g.glyph.errors.push(format!("no glyph for {c:?}"));
        return (0.0, 0.0, p.width, p.cap);
    };
    let (w, dx) = (glyph.advance, (p.width - glyph.advance) / 2.0);
    let (x0, y0, x1, y1) = glyph.bounds().unwrap_or((0.0, 0.0, w, p.cap));
    for contour in glyph.contours {
        g.add(contour.mapped(|z| pt(w - z.x + dx, z.y)).reversed());
    }
    (w - x1 + dx, y0, w - x0 + dx, y1)
}

/// The advance of the glyph called `name` in the master `p`.
fn advance_of(registry: &Registry, name: &str, p: &Params) -> f64 {
    registry.get(name).map_or(p.width, |spec| registry.build(spec, p).advance)
}

// ---------------------------------------------------------------------------------------------------------------
// spaces

fn space(_g: &mut Draw) {}

/// The spaces that take room: code point, and width in the proportional family as a fraction of the em, or a
/// negative number for a width taken from another glyph (-1 the figures' cell, -2 the period).
const SPACES: [(u32, f64); 13] = [
    (0x2000, 0.5),        // en quad
    (0x2001, 1.0),        // em quad
    (0x2002, 0.5),        // en space
    (0x2003, 1.0),        // em space
    (0x2004, 1.0 / 3.0),  // three-per-em
    (0x2005, 0.25),       // four-per-em
    (0x2006, 1.0 / 6.0),  // six-per-em
    (0x2007, -1.0),       // figure space
    (0x2008, -2.0),       // punctuation space
    (0x2009, 0.2),        // thin space
    (0x200A, 0.1),        // hair space
    (0x202F, 0.2),        // narrow no-break space
    (0x205F, 4.0 / 18.0), // medium mathematical space
];

/// The characters with no width: zero width space, non-joiner, joiner, word joiner, zero width no-break space.
const ZERO_WIDTH: [u32; 5] = [0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF];

// ---------------------------------------------------------------------------------------------------------------
// leaders, primes, lines

fn one_dot_leader(g: &mut Draw) {
    g.use_char('.', 0.0, 0.0);
}

/// The dots of the ellipsis (punct.rs), two of them, at the ellipsis's pitch.
fn two_dot_leader(g: &mut Draw) {
    let p = g.p;
    let r = 0.5 * p.punct + 16.0;
    for cx in [p.mid() - 100.0, p.mid() + 100.0] {
        g.dot(cx, r - p.over, r);
    }
}

/// `n` primes side by side, as ″ draws two, lighter and closer as there are more; mirrored for the reversed ones.
fn primes(g: &mut Draw, n: usize, reversed: bool) {
    let p = g.p;
    let (w, pitch, lean) = match n {
        3 => (0.74 * quote_bar(p), 0.60 * 0.74 * quote_bar(p) + 100.0, 48.0),
        _ => (0.60 * quote_bar(p), 0.50 * 0.60 * quote_bar(p) + 80.0, 42.0),
    };
    let s = if reversed { -1.0 } else { 1.0 };
    let first = p.mid() - pitch * (n as f64 - 1.0) / 2.0;
    for i in 0..n {
        let x = first + pitch * i as f64;
        g.stroke(&[
            knot(x + s * lean, p.asc, 1.1 * w).pen(0.0).line(),
            knot(x - s * lean, p.asc - QUOTE_DROP, 0.7 * w).pen(0.0),
        ]);
    }
}

/// The underscore of punct.rs: its ends and the height of its top edge.
const LOW_LINE: (f64, f64) = (48.0, -30.0);

fn double_low_line(g: &mut Draw) {
    let p = g.p;
    let t = 0.5 * p.op + 14.0;
    let gap = 0.5 * t + 40.0; // a pixel at 16 px
    let (x0, top) = LOW_LINE;
    g.stroke(&hbar(x0, p.width - x0, top - t / 2.0, t));
    g.stroke(&hbar(x0, p.width - x0, top - 1.5 * t - gap, t));
}

fn overline(g: &mut Draw) {
    let p = g.p;
    let (x0, _) = LOW_LINE;
    // as long as the underscore, its top on the top of the brackets
    g.stroke(&hbar(x0, p.width - x0, p.br_top - p.op / 2.0, p.op));
}

fn fraction_slash(g: &mut Draw) {
    let p = g.p;
    let (_, hw) = small_strokes(p);
    let (y0, y1) = (-20.0, p.cap + 20.0);
    let run = (y1 - y0) / 60f64.to_radians().tan() / 2.0;
    g.stroke(&diag(p.mid() - run, y0, p.mid() + run, y1, 1.1 * hw));
}

fn hyphen_bullet(g: &mut Draw) {
    let p = g.p;
    g.stroke(&hbar(p.mid() - 104.0, p.mid() + 104.0, p.axis, 1.45 * p.op));
}

/// [ with a quill: a short bar from its stem into the bracket, half way up.
fn quill_bracket(g: &mut Draw, right: bool) {
    let p = g.p;
    let c = if right { ']' } else { '[' };
    let (x0, y0, x1, y1) = base(g, c);
    let len = 0.55 * (x1 - x0);
    let y = (y0 + y1) / 2.0;
    if right {
        g.stroke(&hbar(x1 - len, x1, y, p.hair));
    } else {
        g.stroke(&hbar(x0, x0 + len, y, p.hair));
    }
}

fn low_asterisk(g: &mut Draw) {
    let p = g.p;
    // the asterisk is centred on the axis; this one hangs from half the x-height
    let r = 170.0 + 0.45 * p.op;
    g.use_char('*', 0.0, 0.62 * p.xh - r - p.axis);
}

fn swung_dash(g: &mut Draw) {
    let p = g.p;
    let t = 0.86 * p.op;
    let a = 70.0 + 0.14 * p.op;
    let (x0, x1) = (34.0, p.width - 34.0);
    let w = x1 - x0;
    g.stroke(&[
        cut(x0, p.axis - 0.5 * a, t, 40.0),
        knot(x0 + 0.27 * w, p.axis + a, t).dir(0.0),
        knot(p.mid(), p.axis, t),
        knot(x1 - 0.27 * w, p.axis - a, t).dir(0.0),
        cut(x1, p.axis + 0.5 * a, t, 40.0),
    ]);
}

/// ‿ (`up` false) and ⁀: a shallow arc across the cell, under the baseline or over the ascender.
fn tie(g: &mut Draw, up: bool) {
    let p = g.p;
    let t = 0.80 * p.op;
    let slope: f64 = 52.0;
    let half_cut = 0.5 * t / slope.to_radians().sin(); // the ends are cut level, and stay inside the cell
    let (x0, x1) = (6.0 + half_cut, p.width - 6.0 - half_cut);
    let (end, mid) = if up { (p.asc - 20.0, p.asc + 90.0) } else { (-20.0, -130.0) };
    let s = if up { 1.0 } else { -1.0 };
    g.stroke(&[
        cut_pen(x0, end, t, s * slope, 0.0),
        knot(p.mid(), mid, t).dir(0.0),
        cut_pen(x1, end, t, -s * slope, 0.0),
    ]);
}

fn flower(g: &mut Draw) {
    let p = g.p;
    let (cx, cy) = (p.mid(), p.axis);
    let (rx, ry) = (0.20 * p.op + 52.0, 0.20 * p.op + 20.0);
    let d = rx + 0.30 * p.op + 34.0; // the petals' centres from the middle
    for i in 0..8 {
        let a = (90.0 + 45.0 * f64::from(i)).to_radians();
        let (c, s) = (a.cos(), a.sin());
        let petal: Contour = rachis_kernel::pen::superellipse(0.0, 0.0, rx, ry, 0.56)
            .mapped(|z| pt(cx + d * c + z.x * c - z.y * s, cy + d * s + z.x * s + z.y * c));
        g.add(petal);
    }
    g.dot(cx, cy, 0.6 * ry + 0.2 * p.op);
}

/// ‱: the per mille sign with a third ring below, the rings narrower and lighter so that four fit.
fn per_ten_thousand(g: &mut Draw) {
    let p = g.p;
    let (sw, hw) = small_strokes(p);
    let f = 0.62;
    let (w, h) = (184.0, 250.0);
    let ring = |x0: f64, y0: f64| crate::parts::ring(x0, y0, x0 + w, y0 + h, sw * f, hw * f, p.sq);
    g.stroke_closed(&ring(8.0, p.cap + p.over - h));
    let gap = (p.width - 12.0 - 3.0 * w) / 2.0;
    for i in 0..3 {
        g.stroke_closed(&ring(6.0 + f64::from(i) * (w + gap), -p.over));
    }
    g.stroke(&diag(70.0, h + 30.0, 340.0, p.cap, hw * 0.9));
}

// ---------------------------------------------------------------------------------------------------------------
// interrobang and its kin

/// The hook and stem of a question mark in the box (x0, y0)-(x1, y1), `y0` being the baseline its dot stands on
/// and `foot` where the stem ends: `question_knots` of punct.rs, with the cap height made the box's height.
#[allow(clippy::too_many_arguments)]
pub fn question_knots(
    p: &Params,
    x0: f64,
    x1: f64,
    y0: f64,
    y1: f64,
    xs: f64,
    foot: f64,
    sw: f64,
    hw: f64,
) -> Vec<Knot> {
    let h = y1 - y0;
    let cx = (x0 + x1) / 2.0;
    let top = y1 + p.over * h / p.cap - hw / 2.0;
    vec![
        cut(x0, y1 - 0.175 * h, hw * 1.04, 44.0),
        knot(cx, top, hw).dir(0.0).k(p.sq),
        knot(x1 - sw / 2.0, y0 + 0.735 * h, sw).dir(-90.0),
        knot(xs, y0 + 0.455 * h, sw * 0.96).pen(0.0).dir(-90.0).line(),
        knot(xs, foot, sw * 0.90).pen(0.0),
    ]
}

/// The stroke of ! at `x` (punct.rs `exclam_knots`).
fn exclam_knots(p: &Params, x: f64, scale: f64) -> Vec<Knot> {
    let w = p.cap_stem * scale;
    vec![knot(x, p.cap, 1.12 * w).pen(0.0).line(), knot(x, mark_foot(p), 0.84 * w).pen(0.0)]
}

fn interrobang(g: &mut Draw) {
    let p = g.p;
    let xs = p.mid() + 6.0;
    g.stroke(&question_knots(p, 122.0, p.width - 116.0, 0.0, p.cap, xs, mark_foot(p), p.cap_stem, p.cap_hair));
    g.stroke(&exclam_knots(p, xs, 0.86));
    g.dot(xs, dot_y(p), p.punct);
}

fn exclam_question(g: &mut Draw) {
    let p = g.p;
    let (sw, hw) = small_strokes(p);
    let r = 0.80 * p.punct;
    let xe = p.mid() - 150.0;
    g.stroke(&exclam_knots(p, xe, 0.92));
    g.dot(xe, r - p.over, r);
    let x0 = p.mid() - 30.0;
    let xs = x0 + 150.0;
    g.stroke(&question_knots(p, x0, x0 + 264.0, 0.0, p.cap, xs, mark_foot(p), sw * 1.12, hw * 1.12));
    g.dot(xs, r - p.over, r);
}

// ---------------------------------------------------------------------------------------------------------------
// currency: capitals with bars

/// A bar across the cell at `y`, from `x0` to `x1`.
fn cross_bar(g: &mut Draw, x0: f64, x1: f64, y: f64) {
    let t = bar_t(g.p);
    g.stroke(&hbar(x0, x1, y, t));
}

/// Ticks above and below a letter at `x`, as in $.
fn ticks(g: &mut Draw, x: f64, top: f64, bottom: f64) {
    let p = g.p;
    let t = tick_t(p);
    g.stroke(&vstem(x, top - p.cap_hair / 2.0, top + TICK_REACH, t));
    g.stroke(&vstem(x, bottom - TICK_REACH, bottom + p.cap_hair / 2.0, t));
}

/// How far a bar reaches past the letter it crosses.
fn overhang(p: &Params) -> f64 {
    0.30 * p.cap_stem + 22.0
}

fn franc(g: &mut Draw) {
    let p = g.p;
    let (x0, _, _, _) = base(g, 'F');
    let xs = x0 + p.cap_stem / 2.0;
    cross_bar(g, xs - p.cap_stem / 2.0 - 1.1 * overhang(p), xs + 2.0 * p.cap_stem, 0.24 * p.cap);
}

fn ruble(g: &mut Draw) {
    let p = g.p;
    let (x0, _, x1, _) = base(g, 'P');
    cross_bar(g, x0 - 1.1 * overhang(p), x0 + 0.62 * (x1 - x0), 0.22 * p.cap);
}

fn peso(g: &mut Draw) {
    let p = g.p;
    let (x0, _, x1, _) = base(g, 'P');
    // two bars: one along the top of the bowl, one through the middle of its counter, so that the counter is
    // halved and not filled
    let (lo, hi) = (0.43 * p.cap + p.cap_hair / 2.0, p.cap - p.cap_hair);
    let t = bar_t(p);
    cross_bar(g, x0 - 1.1 * overhang(p), x1 + 0.5 * overhang(p), p.cap - t / 2.0);
    cross_bar(g, x0 - 1.1 * overhang(p), x1 + 0.5 * overhang(p), (lo + hi) / 2.0);
}

fn tugrik(g: &mut Draw) {
    let p = g.p;
    let (x0, _, x1, _) = base(g, 'T');
    let half = 0.36 * (x1 - x0);
    let t = bar_t(p);
    for y in [0.30 * p.cap, 0.53 * p.cap] {
        g.stroke(&rake(p.mid() - half, y - 0.32 * half, p.mid() + half, y + 0.32 * half, t));
    }
}

fn naira(g: &mut Draw) {
    let p = g.p;
    let (x0, _, x1, _) = base(g, 'N');
    for y in [0.37 * p.cap, 0.63 * p.cap] {
        cross_bar(g, x0 - overhang(p), x1 + overhang(p), y);
    }
}

fn won(g: &mut Draw) {
    let p = g.p;
    let (x0, _, x1, _) = base(g, 'W');
    for y in [0.40 * p.cap, 0.64 * p.cap] {
        cross_bar(g, x0, x1, y);
    }
}

fn kip(g: &mut Draw) {
    let p = g.p;
    let (x0, _, x1, _) = base(g, 'K');
    cross_bar(g, x0 - overhang(p), x1 - 0.1 * (x1 - x0), 0.47 * p.cap);
}

fn guarani(g: &mut Draw) {
    let p = g.p;
    let (x0, y0, x1, y1) = base(g, 'G');
    let x = (x0 + x1) / 2.0 + 6.0;
    g.stroke(&vstem(x, y0 - TICK_REACH, y1 + TICK_REACH, bar_t(p)));
}

fn cedi(g: &mut Draw) {
    let (x0, y0, x1, y1) = base(g, 'C');
    ticks(g, (x0 + x1) / 2.0 + 14.0, y1, y0);
}

fn colon_sign(g: &mut Draw) {
    let p = g.p;
    let (x0, y0, x1, y1) = base(g, 'C');
    let t = bar_t(p);
    let cx = (x0 + x1) / 2.0 + 14.0;
    let run = 0.13 * (y1 - y0);
    for dx in [-58.0, 58.0] {
        g.stroke(&diag(cx + dx - run, y0 - 0.7 * TICK_REACH, cx + dx + run, y1 + 0.7 * TICK_REACH, t));
    }
}

fn bitcoin(g: &mut Draw) {
    let (x0, y0, x1, y1) = base(g, 'B');
    for f in [0.28, 0.60] {
        ticks(g, x0 + f * (x1 - x0), y1, y0);
    }
}

fn baht(g: &mut Draw) {
    let (x0, y0, x1, y1) = base(g, 'B');
    ticks(g, x0 + 0.46 * (x1 - x0), y1, y0);
}

fn hryvnia(g: &mut Draw) {
    let p = g.p;
    let (x0, _, x1, _) = mirrored(g, 'S');
    for y in [0.40 * p.cap, 0.60 * p.cap] {
        cross_bar(g, x0 - 0.5 * overhang(p), x1 + 0.5 * overhang(p), y);
    }
}

fn dong(g: &mut Draw) {
    let p = g.p;
    let (_, _, x1, _) = base(g, 'd');
    let xs = x1 - p.stem / 2.0;
    let t = bar_t(p);
    g.stroke(&hbar(
        xs - 0.5 * p.stem - 1.7 * overhang(p),
        xs + 0.5 * p.stem + overhang(p),
        p.xh + 0.55 * (p.asc - p.xh),
        t,
    ));
    let (x0, _) = LOW_LINE;
    g.stroke(&hbar(x0 + 40.0, p.width - x0 - 40.0, -0.20 * p.cap, t));
}

// ---------------------------------------------------------------------------------------------------------------
// currency: signs of their own

/// The sides of a currency sign drawn for the cell: as the figures'.
fn fig_box(p: &Params) -> (f64, f64) {
    (p.fig_sb - 16.0, p.width - p.fig_sb + 16.0)
}

fn lira(g: &mut Draw) {
    // £ (punct.rs) with two bars
    let p = g.p;
    let (sw, hw) = (p.cap_stem, p.cap_hair);
    let x = 232.0;
    let top = p.cap + p.over - hw / 2.0;
    g.stroke(&[
        cut(p.width - 82.0, p.cap - 0.21 * p.cap, hw * 1.04, 136.0),
        knot(x + 150.0, top, hw).dir(180.0).k(p.sq),
        knot(x, p.cap - 0.30 * p.cap, sw).pen(0.0).dir(-90.0).line(),
        knot(x, 0.0, sw).pen(0.0),
    ]);
    g.stroke(&hbar(84.0, p.width - 76.0, hw / 2.0, hw));
    let t = bar_t(p);
    for y in [p.cap * 0.50 + 0.85 * t, p.cap * 0.50 - 0.85 * t] {
        g.stroke(&hbar(92.0, p.width - 176.0, y - 0.1 * p.cap, t));
    }
}

fn rupee(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = fig_box(p);
    let (sw, hw) = (p.cap_stem, p.cap_hair);
    let w = x1 - x0;
    g.stroke(&hbar(x0, x1, p.cap - hw / 2.0, hw));
    let y2 = 0.70 * p.cap;
    g.stroke(&hbar(x0, x1, y2, hw));
    // the bowl hangs from the top bar and returns to the left at its waist
    let xl = x0 + 0.30 * w;
    let waist = 0.40 * p.cap;
    g.stroke(&dbowl(xl, x1 - 0.10 * w, waist - hw / 2.0, p.cap, sw, hw, p.sq + 0.02, 0.10 * w));
    g.stroke(&hbar(x0, xl + 2.0, waist, hw));
    // the leg, from the left end of the waist down to the right
    let t = 0.95 * sw;
    let top_l = x0 + 0.12 * w;
    let bot_r = x1 - 0.06 * w;
    let b = t * 1.35;
    g.stroke(&diag(top_l + b / 2.0, waist, bot_r - b / 2.0, 0.0, t));
}

fn turkish_lira(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = fig_box(p);
    let (sw, hw) = (p.cap_stem, p.cap_hair);
    let w = x1 - x0;
    let xs = x0 + 0.30 * w;
    g.stroke(&[
        knot(xs, p.cap, sw).pen(0.0).line(),
        knot(xs, 0.34 * p.cap, sw).pen(0.0).dir(-90.0),
        knot(xs + 0.40 * (x1 - xs), -p.over + hw / 2.0, hw).dir(0.0),
        cut_pen(x1 - sw / 2.0 + 6.0, 0.46 * p.cap, sw * 0.96, 96.0, 0.0),
    ]);
    let t = bar_t(p);
    for y in [0.46 * p.cap, 0.66 * p.cap] {
        g.stroke(&rake(x0 - 6.0, y - 46.0, xs + 0.62 * (x1 - xs), y + 52.0, t));
    }
}

/// The strokes of a capital that shares the cell with a small letter (₧ ₨): lighter than a capital's, and gaining
/// weight more slowly, so that two letters in one cell stay open in the Bold.
fn pair_strokes(p: &Params) -> (f64, f64) {
    (0.62 * p.cap_stem + 20.0, 0.62 * p.cap_hair + 18.0)
}

/// The strokes of the small letter beside it.
fn pair_small(p: &Params) -> (f64, f64) {
    (0.62 * p.stem + 16.0, 0.62 * p.hair + 16.0)
}

fn peseta(g: &mut Draw) {
    // P and a small t, side by side
    let p = g.p;
    let (sw, hw) = pair_strokes(p);
    let x = p.fig_sb - 52.0 + sw / 2.0;
    let edge = 0.60 * p.width;
    let waist = 0.43 * p.cap;
    g.stroke(&vstem(x, 0.0, p.cap, sw));
    g.stroke(&dbowl(x, edge, waist - hw / 2.0, p.cap, sw, hw, p.sq + 0.02, 0.30 * (edge - x)));
    let (ts, th) = pair_small(p);
    let xt = edge + 0.36 * (p.width - edge);
    let r = 0.12 * p.xh + ts / 2.0;
    g.stroke(&elbow(xt, 0.80 * p.cap, 0.0, p.width - 20.0, ts, th, p.sq, r));
    g.stroke(&hbar(edge + 34.0, p.width - 26.0, 0.62 * p.cap - th / 2.0, th));
}

fn tenge(g: &mut Draw) {
    let p = g.p;
    let hw = p.cap_hair;
    let x0 = p.sb_round - 20.0; // the T of upper.rs
    let gap = 0.9 * hw + 20.0;
    g.stroke(&hbar(x0, p.width - x0, p.cap - hw / 2.0, hw));
    let y = p.cap - 1.5 * hw - gap;
    g.stroke(&hbar(x0, p.width - x0, y, hw));
    g.stroke(&vstem(p.mid(), 0.0, y, p.cap_stem));
}

fn manat(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = fig_box(p);
    let sw = p.cap_stem * 0.92;
    let top = 0.70 * p.cap;
    let (xl, xr) = (x0 + sw / 2.0, x1 - sw / 2.0);
    let ys = top - 0.9 * (xr - xl) / 2.0;
    g.stroke(&[
        knot(xl, 0.0, sw).pen(0.0).line(),
        knot(xl, ys, sw).pen(0.0).dir(90.0).k(p.sq),
        knot(p.mid(), top - p.cap_hair / 2.0, p.cap_hair).dir(0.0).k(p.sq),
        knot(xr, ys, sw).pen(0.0).dir(-90.0).line(),
        knot(xr, 0.0, sw).pen(0.0),
    ]);
    g.stroke(&vstem(p.mid(), 0.0, p.cap + 30.0, 0.86 * sw));
}

fn sheqel(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (p.width / 2.0 - 250.0, p.width / 2.0 + 250.0);
    let sw = 0.42 * p.cap_stem + 32.0; // four uprights in a cell
    let w = x1 - x0;
    let (a, b, c, d) = (x0 + sw / 2.0, x0 + 0.33 * w, x0 + 0.67 * w, x1 - sw / 2.0);
    let r = 0.5 * (c - a);
    let yt = p.cap - sw / 2.0;
    // a ∩ from the left foot over to a stem that stops short of the baseline
    g.stroke(&[
        knot(a, 0.0, sw).pen(0.0).line(),
        knot(a, yt - r, sw).pen(0.0).dir(90.0).k(p.sq),
        knot((a + c) / 2.0, yt, sw).dir(0.0).k(p.sq),
        knot(c, yt - r, sw).pen(0.0).dir(-90.0).line(),
        knot(c, 0.36 * p.cap, sw).pen(0.0),
    ]);
    // and a ∪ from a stem that starts short of the cap height down and up to the right top
    let yb = sw / 2.0;
    let r2 = 0.5 * (d - b);
    g.stroke(&[
        knot(b, 0.64 * p.cap, sw).pen(0.0).line(),
        knot(b, yb + r2, sw).pen(0.0).dir(-90.0).k(p.sq),
        knot((b + d) / 2.0, yb, sw).dir(0.0).k(p.sq),
        knot(d, yb + r2, sw).pen(0.0).dir(90.0).line(),
        knot(d, p.cap, sw).pen(0.0),
    ]);
}

fn lari(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = fig_box(p);
    let (sw, hw) = (p.cap_stem, p.cap_hair);
    let cx = (x0 + x1) / 2.0;
    let top = 0.80 * p.cap;
    // a round arch, its left leg running down into a bar along the baseline
    g.stroke(&[
        cut_pen(x1 - sw / 2.0, 0.30 * p.cap, sw, 90.0, 0.0),
        knot(x1 - sw / 2.0, 0.42 * p.cap, sw).dir(90.0),
        knot(cx, top - hw / 2.0, hw).dir(180.0).k(p.sq),
        knot(x0 + sw / 2.0, 0.40 * p.cap, sw).dir(-90.0).k(p.sq),
        knot(cx - 0.1 * (x1 - x0), hw / 2.0, hw).pen(90.0).dir(0.0).line(),
        knot(x1, hw / 2.0, hw).pen(90.0),
    ]);
    let t = tick_t(p);
    for dx in [-0.16, 0.16] {
        g.stroke(&vstem(cx + dx * (x1 - x0), top - hw, p.cap + 40.0, 0.9 * t));
    }
}

fn rupee_sign(g: &mut Draw) {
    // R and a small s
    let p = g.p;
    let (sw, hw) = pair_strokes(p);
    let x = p.fig_sb - 52.0 + sw / 2.0;
    let edge = 0.58 * p.width;
    let waist = 0.46 * p.cap;
    g.stroke(&vstem(x, 0.0, p.cap, sw));
    g.stroke(&dbowl(x, edge - 10.0, waist - hw / 2.0, p.cap, sw, hw, p.sq + 0.02, 0.32 * (edge - x)));
    g.stroke(&diag(x + 0.40 * (edge - x), waist, edge - 0.45 * sw, 0.0, 0.95 * sw));
    // the s, at the x-height, narrowed
    let (s, h) = pair_small(p);
    let (x0, x1) = (edge + 16.0, p.width - 18.0);
    let cx = (x0 + x1) / 2.0;
    let (top, bot) = (p.xh + p.over - h / 2.0, -p.over + h / 2.0);
    let white = top - bot - h;
    g.stroke(&[
        cut(x1 - 6.0, top - 0.13 * white, h, 152.0),
        knot(cx + 2.0, top, h).dir(180.0).k(p.sq),
        knot(x0 + 4.0 + s / 2.0, p.xh * 0.735, 0.96 * s).dir(-90.0),
        knot(cx, p.xh * 0.515, 1.02 * s).dir(-30.0),
        knot(x1 - s / 2.0, p.xh * 0.265, 0.96 * s).dir(-90.0).k(p.sq),
        knot(cx - 2.0, bot, h).dir(180.0),
        cut(x0, bot + 0.13 * white, h, 152.0),
    ]);
}

// ---------------------------------------------------------------------------------------------------------------

pub fn register(reg: &mut Registry) {
    reg.module("typography");
    for (cp, _) in SPACES {
        reg.code(cp, Opt::default(), space);
    }
    let zero = Opt { advance: Some(0.0), ..Opt::default() };
    for cp in ZERO_WIDTH {
        reg.code(cp, zero, space);
    }
    reg.ch('․', one_dot_leader);
    reg.ch('‥', two_dot_leader);
    reg.ch('‴', |g: &mut Draw| primes(g, 3, false));
    reg.ch('⁗', |g: &mut Draw| primes(g, 4, false));
    reg.ch('‵', |g: &mut Draw| {
        mirrored(g, '′');
    });
    reg.ch('‶', |g: &mut Draw| {
        mirrored(g, '″');
    });
    reg.ch('‷', |g: &mut Draw| primes(g, 3, true));
    reg.ch('‟', |g: &mut Draw| {
        mirrored(g, '”');
    });
    reg.ch('‗', double_low_line);
    reg.ch('‾', overline);
    reg.ch('⁄', fraction_slash);
    reg.ch('⁃', hyphen_bullet);
    reg.ch('⁅', |g: &mut Draw| quill_bracket(g, false));
    reg.ch('⁆', |g: &mut Draw| quill_bracket(g, true));
    reg.ch('⁎', low_asterisk);
    reg.ch('⁓', swung_dash);
    reg.ch('‿', |g: &mut Draw| tie(g, false));
    reg.ch('⁀', |g: &mut Draw| tie(g, true));
    reg.ch('⁕', flower);
    reg.ch('‱', per_ten_thousand);
    reg.ch('‽', interrobang);
    reg.ch('⁉', exclam_question);
    // currency
    reg.ch('₣', franc);
    reg.ch('₤', lira);
    reg.ch('₧', peseta);
    reg.ch('₫', dong);
    reg.ch('₮', tugrik);
    reg.ch('₴', hryvnia);
    reg.ch('₹', rupee);
    reg.ch('₺', turkish_lira);
    reg.ch('₽', ruble);
    reg.ch('₡', colon_sign);
    reg.ch('₦', naira);
    reg.ch('₨', rupee_sign);
    reg.ch('₩', won);
    reg.ch('₪', sheqel);
    reg.ch('₭', kip);
    reg.ch('₱', peso);
    reg.ch('₲', guarani);
    reg.ch('₵', cedi);
    reg.ch('₸', tenge);
    reg.ch('₼', manat);
    reg.ch('₾', lari);
    reg.ch('₿', bitcoin);
    reg.ch('฿', baht);
}

/// The proportional family's cells for this module's glyphs: the spaces' typographic widths, and the cells of
/// the glyphs that are other glyphs of punct.rs placed or mirrored.
pub fn fit(registry: &Registry, name: &str, p: &Params) -> Option<Fit> {
    let em = p.upm;
    let period = || advance_of(registry, "period", p);
    for (cp, w) in SPACES {
        if name == name_of_code(cp) {
            let width = if w == -1.0 {
                p.width
            } else if w == -2.0 {
                period()
            } else {
                w * em
            };
            return Some(Fit::new(width));
        }
    }
    let same = |other: &str| Some(Fit::new(advance_of(registry, other, p)));
    match name {
        "uni2024" => same("period"),
        "uni2025" => Some(Fit::new(advance_of(registry, "uni2026", p) - 200.0)),
        "uni2035" => same("uni2032"),
        "uni2036" => same("uni2033"),
        "uni201F" => same("uni201D"),
        "uni2017" | "uni203E" => same("underscore"),
        "uni2045" => same("bracketleft"),
        "uni2046" => same("bracketright"),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use rachis_kernel::params::masters;

    use super::*;

    #[test]
    fn spaces_are_a_cell_in_the_fixed_pitch_family_and_typographic_in_the_other() {
        let r = crate::registry();
        for p in masters() {
            let advance = |cp: u32| r.build(r.get(&name_of_code(cp)).unwrap(), &p).advance;
            for cp in ZERO_WIDTH {
                assert_eq!(advance(cp), 0.0, "U+{cp:04X} in {}", p.name);
            }
            if p.mono {
                for (cp, _) in SPACES {
                    assert_eq!(advance(cp), p.width, "U+{cp:04X} in {}", p.name);
                }
            } else {
                let expected = [
                    (0x2001, 1000.0),
                    (0x2003, 1000.0),
                    (0x2000, 500.0),
                    (0x2002, 500.0),
                    (0x2005, 250.0),
                    (0x2007, p.width),
                    (0x2009, 200.0),
                    (0x200A, 100.0),
                    (0x202F, 200.0),
                ];
                for (cp, w) in expected {
                    assert!((advance(cp) - w).abs() < 1e-9, "U+{cp:04X} in {}: {}", p.name, advance(cp));
                }
                assert!((advance(0x2004) - 1000.0 / 3.0).abs() < 1e-9);
                assert!((advance(0x2006) - 1000.0 / 6.0).abs() < 1e-9);
                assert!((advance(0x205F) - 2000.0 / 9.0).abs() < 1e-9);
                assert_eq!(advance(0x2008), r.build(r.get("period").unwrap(), &p).advance);
            }
        }
    }
}
