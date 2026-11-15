//! Punctuation, brackets and common signs.
//!
//! The marks a reader of code meets most are drawn large and kept apart by outline: the comma is the period with a
//! tail, the quotes are straight bars while the backtick is a heavy diagonal, and the three kinds of bracket differ in
//! width as well as in shape. Brackets share one span (`p.br_bot` to `p.br_top`) and one stroke.

use rachis_kernel::{Draw, Knot, Params, Registry, V, knot, pt};

use crate::parts::{Bowl, bowl, cut, cut_pen, dbowl, diag, flip, hbar, mirror, ring, turn, vee, vstem};

// ---------------------------------------------------------------------------------------------------------------
// Measurements this group derives from the parameters. Each is a candidate for params.py.

/// The vertical stroke of brackets, braces and parentheses: a little lighter than a letter's stem, because a
/// bracket is twice as tall as a lowercase letter.
pub fn bracket_stem(p: &Params) -> f64 {
    p.stem * 0.92
}

/// The breadth of the straight quotes: slightly more than a stem.
pub fn quote_bar(p: &Params) -> f64 {
    p.stem * 1.14
}

/// The vertical and horizontal strokes of parts drawn at reduced size (the rings of the per cent sign, the
/// letters inside the copyright sign, the ordinals). They are lighter than text strokes and gain weight more
/// slowly, so that small counters stay open in the Bold.
pub fn small_strokes(p: &Params) -> (f64, f64) {
    (0.435 * p.stem + 30.0, 0.47 * p.hair + 25.0)
}

/// The centre of a dot that stands on the baseline: round, so it overshoots.
pub fn dot_y(p: &Params) -> f64 {
    p.punct - p.over
}

/// Where the stroke of ! and ? ends above its dot.
pub fn mark_foot(p: &Params) -> f64 {
    2.0 * p.punct - p.over + 96.0
}

// ---------------------------------------------------------------------------------------------------------------
// Dots and commas

/// A dot centred on (cx, cy) with a tail. `form` "9" is the comma and the closing quote (the tail leaves
/// the right of the dot and falls to the left); "6" is that turned half a circle (the opening quote); "p" is the
/// comma mirrored (the reversed quote).
fn comma_shape(g: &mut Draw, cx: f64, cy: f64, scale: f64, form: &str) {
    let p = g.p;
    let r = p.punct * scale;
    let drop = scale * (1.7 * p.punct + 108.0); // from the dot's centre down to the end of the tail
    let w0 = 0.92 * r;
    let mut tail = vec![
        knot(cx + 0.97 * r - w0 / 2.0, cy, w0).pen(0.0).dir(-90.0),
        cut_pen(cx - 0.40 * r, cy - drop, 0.54 * r, -128.0, 0.0),
    ];
    if form == "6" {
        tail = turn(&tail, cx, cy);
    } else if form == "p" {
        tail = mirror(&tail, cx);
    }
    g.dot(cx, cy, r);
    g.stroke(&tail);
}

fn period(g: &mut Draw) {
    let p = g.p;
    g.dot(p.mid(), dot_y(p), p.punct);
}

fn comma(g: &mut Draw) {
    let p = g.p;
    comma_shape(g, p.mid(), dot_y(p), 1.0, "9");
}

fn colon(g: &mut Draw) {
    let p = g.p;
    g.dot(p.mid(), dot_y(p), p.punct);
    g.dot(p.mid(), p.xh + p.over - p.punct, p.punct);
}

fn semicolon(g: &mut Draw) {
    let p = g.p;
    comma_shape(g, p.mid(), dot_y(p), 1.0, "9");
    g.dot(p.mid(), p.xh + p.over - p.punct, p.punct);
}

fn ellipsis(g: &mut Draw) {
    let p = g.p;
    let r = 0.5 * p.punct + 16.0;
    for cx in [p.mid() - 200.0, p.mid(), p.mid() + 200.0] {
        g.dot(cx, r - p.over, r);
    }
}

fn periodcentered(g: &mut Draw) {
    let p = g.p;
    g.dot(p.mid(), p.axis, 0.78 * p.punct);
}

fn bullet(g: &mut Draw) {
    let p = g.p;
    g.dot(p.mid(), p.axis, 1.5 * p.punct);
}

fn triangle_bullet(g: &mut Draw) {
    let p = g.p;
    let h = 1.6 * p.punct;
    g.poly(&[pt(p.mid() - 0.8 * h, p.axis + h), pt(p.mid() - 0.8 * h, p.axis - h), pt(p.mid() + 0.9 * h, p.axis)]);
}

// ---------------------------------------------------------------------------------------------------------------
// Exclamation and question

fn exclam_knots(p: &Params, x: f64, scale: f64) -> Vec<Knot> {
    let w = p.cap_stem * scale;
    vec![knot(x, p.cap, 1.12 * w).pen(0.0).line(), knot(x, mark_foot(p), 0.84 * w).pen(0.0)]
}

/// The hook of the question mark between `x0` and `x1`, ending in a short stem centred on `xs`.
fn question_knots(p: &Params, x0: f64, x1: f64, xs: f64, sw: f64, hw: f64) -> Vec<Knot> {
    let cx = (x0 + x1) / 2.0;
    let top = p.cap + p.over - hw / 2.0;
    vec![
        cut(x0, p.cap - 0.175 * p.cap, hw * 1.04, 44.0),
        knot(cx, top, hw).dir(0.0).k(p.sq),
        knot(x1 - sw / 2.0, p.cap * 0.735, sw).dir(-90.0),
        knot(xs, p.cap * 0.455, sw * 0.96).pen(0.0).dir(-90.0).line(),
        knot(xs, mark_foot(p), sw * 0.90).pen(0.0),
    ]
}

fn exclam(g: &mut Draw) {
    let p = g.p;
    g.stroke(&exclam_knots(p, p.mid(), 1.0));
    g.dot(p.mid(), dot_y(p), p.punct);
}

fn exclamdown(g: &mut Draw) {
    let p = g.p;
    g.stroke(&flip(&exclam_knots(p, p.mid(), 1.0), p.xh / 2.0));
    g.dot(p.mid(), p.xh - dot_y(p), p.punct);
}

fn question(g: &mut Draw) {
    let p = g.p;
    let xs = p.mid() + 6.0;
    g.stroke(&question_knots(p, 122.0, p.width - 116.0, xs, p.cap_stem, p.cap_hair));
    g.dot(xs, dot_y(p), p.punct);
}

fn questiondown(g: &mut Draw) {
    let p = g.p;
    let xs = p.mid() + 6.0;
    g.stroke(&turn(&question_knots(p, 122.0, p.width - 116.0, xs, p.cap_stem, p.cap_hair), p.mid(), p.xh / 2.0));
    g.dot(p.width - xs, p.xh - dot_y(p), p.punct);
}

fn double_exclam(g: &mut Draw) {
    let p = g.p;
    let r = 0.88 * p.punct;
    for x in [p.mid() - 128.0, p.mid() + 128.0] {
        g.stroke(&exclam_knots(p, x, 0.92));
        g.dot(x, r - p.over, r);
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Quotes

/// the height of the straight quotes
const QUOTE_DROP: f64 = 300.0;

fn quotesingle(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.mid(), p.asc - QUOTE_DROP, p.asc, quote_bar(p)));
}

fn quotedbl(g: &mut Draw) {
    let p = g.p;
    let w = quote_bar(p) * 0.94;
    let d = (w + 84.0) / 2.0;
    g.stroke(&vstem(p.mid() - d, p.asc - QUOTE_DROP, p.asc, w));
    g.stroke(&vstem(p.mid() + d, p.asc - QUOTE_DROP, p.asc, w));
}

fn grave(g: &mut Draw) {
    let p = g.p;
    g.stroke(&diag(p.mid() - 96.0, p.asc, p.mid() + 96.0, p.asc - 270.0, p.stem * 1.12));
}

/// the dot of a curly quote, relative to the period
const QUOTE_SCALE: f64 = 0.92;

/// The centre of a curly quote's dot, so that the quote hangs from the ascender.
fn _quote_y(p: &Params, form: &str) -> f64 {
    let r = p.punct * QUOTE_SCALE;
    let drop = QUOTE_SCALE * (1.7 * p.punct + 108.0);
    if form != "6" { p.asc - r } else { p.asc - drop }
}

fn quoteright(g: &mut Draw) {
    let p = g.p;
    comma_shape(g, p.mid(), _quote_y(p, "9"), QUOTE_SCALE, "9");
}

fn quoteleft(g: &mut Draw) {
    let p = g.p;
    comma_shape(g, p.mid(), _quote_y(p, "6"), QUOTE_SCALE, "6");
}

fn quotereversed(g: &mut Draw) {
    let p = g.p;
    comma_shape(g, p.mid(), _quote_y(p, "p"), QUOTE_SCALE, "p");
}

fn quotesinglbase(g: &mut Draw) {
    let p = g.p;
    comma_shape(g, p.mid(), dot_y(p), 1.0, "9");
}

const DQUOTE_SCALE: f64 = 0.84;

fn _double(g: &mut Draw, cy_of: &str, form: &str) {
    let p = g.p;
    let r = p.punct * DQUOTE_SCALE;
    let drop = DQUOTE_SCALE * (1.7 * p.punct + 108.0);
    let cy = match cy_of {
        "top9" => p.asc - r,
        "top6" => p.asc - drop,
        "base" => r - p.over,
        _ => unreachable!(),
    };
    let d = r + 38.0;
    comma_shape(g, p.mid() - d, cy, DQUOTE_SCALE, form);
    comma_shape(g, p.mid() + d, cy, DQUOTE_SCALE, form);
}

fn quotedblright(g: &mut Draw) {
    _double(g, "top9", "9");
}

fn quotedblleft(g: &mut Draw) {
    _double(g, "top6", "6");
}

fn quotedblbase(g: &mut Draw) {
    _double(g, "base", "9");
}

fn prime(g: &mut Draw) {
    let p = g.p;
    let w = quote_bar(p);
    g.stroke(&[
        knot(p.mid() + 52.0, p.asc, 1.1 * w).pen(0.0).line(),
        knot(p.mid() - 52.0, p.asc - QUOTE_DROP, 0.7 * w).pen(0.0),
    ]);
}

fn dblprime(g: &mut Draw) {
    let p = g.p;
    let w = quote_bar(p) * 0.94;
    let d = (w + 84.0) / 2.0;
    for x in [p.mid() - d, p.mid() + d] {
        g.stroke(&[
            knot(x + 48.0, p.asc, 1.1 * w).pen(0.0).line(),
            knot(x - 48.0, p.asc - QUOTE_DROP, 0.7 * w).pen(0.0),
        ]);
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Brackets

/// The opening parenthesis.
fn paren_knots(p: &Params) -> Vec<Knot> {
    let bs = bracket_stem(p);
    let x_out = 186.0; // the outer edge of the arc at its middle
    let x_tip = 478.0; // the right end of the cuts at top and bottom
    let te = p.hair * 0.95;
    let ym = (p.br_top + p.br_bot) / 2.0;
    let d = 41.0; // the angle of the arc at its ends, from the horizontal
    let tip = cut_pen(0.0, p.br_top, te, -180.0 + d, 0.0);
    let xe = x_tip - tip.w / 2.0;
    vec![
        cut_pen(xe, p.br_top, te, -180.0 + d, 0.0).k(p.sq),
        knot(x_out + bs / 2.0, ym, bs).dir(-90.0).k(p.sq),
        cut_pen(xe, p.br_bot, te, -d, 0.0),
    ]
}

fn parenleft(g: &mut Draw) {
    g.stroke(&paren_knots(g.p));
}

fn parenright(g: &mut Draw) {
    g.stroke(&mirror(&paren_knots(g.p), g.p.mid()));
}

fn bracket(g: &mut Draw, right: bool) {
    let p = g.p;
    let bs = bracket_stem(p);
    let x0 = 252.0 - 0.45 * p.stem; // the outer edge of the stem
    let x1 = 458.0 + 0.38 * p.stem; // the end of the arms
    let strokes = [
        vstem(x0 + bs / 2.0, p.br_bot, p.br_top, bs),
        hbar(x0, x1, p.br_top - p.hair / 2.0, p.hair),
        hbar(x0, x1, p.br_bot + p.hair / 2.0, p.hair),
    ];
    for s in strokes {
        g.stroke(&(if right { mirror(&s, p.mid()) } else { s }));
    }
}

fn bracketleft(g: &mut Draw) {
    bracket(g, false);
}

fn bracketright(g: &mut Draw) {
    bracket(g, true);
}

/// The upper half of the opening brace: arm, shoulder, spine, and the turn into the cusp on the axis.
fn brace_half(p: &Params) -> Vec<Knot> {
    let bs = bracket_stem(p);
    let h = p.hair;
    let xs = 282.0 + 0.12 * p.stem; // the spine's centre
    let x_tip = 140.0 - 0.36 * p.stem; // the point of the cusp
    let x_arm = 476.0 + 0.36 * p.stem; // the end of the arm
    let yt = p.br_top - h / 2.0;
    let r1 = 112.0; // the shoulder's radius on the centre line
    let r2 = 104.0; // the radius of the turn into the cusp
    vec![
        knot(x_arm, yt, h).pen(90.0).line(),
        knot(xs + r1, yt, h).pen(90.0).dir(180.0).k(p.sq),
        knot(xs, yt - r1, bs).pen(0.0).dir(-90.0).line(),
        knot(xs, p.axis + r2, bs).pen(0.0).dir(-90.0).k(p.sq),
        knot(xs - r2, p.axis, h).pen(90.0).dir(180.0).line(),
        knot(x_tip, p.axis, h * 0.5).pen(90.0),
    ]
}

fn braceleft(g: &mut Draw) {
    let p = g.p;
    let half = brace_half(p);
    g.stroke(&half);
    g.stroke(&flip(&half, p.axis));
}

fn braceright(g: &mut Draw) {
    let p = g.p;
    let half = mirror(&brace_half(p), p.mid());
    g.stroke(&half);
    g.stroke(&flip(&half, p.axis));
}

// ---------------------------------------------------------------------------------------------------------------
// Bars and dashes

fn underscore(g: &mut Draw) {
    let p = g.p;
    g.stroke(&hbar(48.0, p.width - 48.0, -30.0 - p.op / 2.0, p.op));
}

/// The en and em dash are a little lighter than the minus, which is how they differ from it.
fn dash_weight(p: &Params) -> f64 {
    p.op * 0.86
}

fn hyphen_true(g: &mut Draw) {
    let p = g.p;
    g.stroke(&hbar(p.mid() - 145.0, p.mid() + 145.0, p.axis, p.op));
}

fn hyphen_nonbreaking(g: &mut Draw) {
    g.use_char('‐', 0.0, 0.0);
}

fn endash(g: &mut Draw) {
    let p = g.p;
    g.stroke(&hbar(p.mid() - 238.0, p.mid() + 238.0, p.axis, dash_weight(p)));
}

fn figuredash(g: &mut Draw) {
    g.use_char('–', 0.0, 0.0);
}

fn emdash(g: &mut Draw) {
    let p = g.p;
    g.stroke(&hbar(0.0, p.width, p.axis, dash_weight(p)));
}

fn horizontalbar(g: &mut Draw) {
    g.use_char('—', 0.0, 0.0);
}

fn nbspace(_g: &mut Draw) {}

fn softhyphen(g: &mut Draw) {
    g.use_char('-', 0.0, 0.0);
}

// ---------------------------------------------------------------------------------------------------------------
// Signs drawn for the cell

/// An open ring whose right side is the stem of a small bowl: three strokes across the cell, not four.
fn at(g: &mut Draw) {
    let p = g.p;
    let (sw, hw) = small_strokes(p);
    let (sw, hw) = (sw * 1.06, hw * 1.06);
    let (x0, x1) = (34.0, p.width - 34.0);
    let (y0, y1) = (p.desc + 60.0, p.cap + p.over);
    let xr = x1 - sw / 2.0;
    let cx = (x0 + x1) / 2.0;
    let (top, bot) = (y1 - hw / 2.0, y0 + hw / 2.0);
    let (by0, by1) = (p.xh * 0.19, p.xh * 0.90); // the inner bowl
    g.stroke(&[
        knot(xr, by0, sw).pen(0.0).line(),
        knot(xr, by1 - 20.0, sw).pen(0.0).dir(90.0).k(p.sq),
        knot(cx + 6.0, top, hw).dir(180.0).k(p.sq),
        knot(x0 + sw / 2.0, (y0 + y1) / 2.0, sw).dir(-90.0).k(p.sq),
        knot(cx + 10.0, bot, hw).dir(0.0),
        cut(x1 - 62.0, bot + 46.0, hw * 1.04, 30.0),
    ]);
    let inner = bowl(
        p,
        p.width - xr,
        p.width - 196.0,
        by0,
        by1,
        Bowl { stem: Some(sw), hair: Some(hw), branch: 0.26, ..Bowl::default() },
    );
    g.stroke(&mirror(&inner, p.mid()));
}

/// One stroke: up the diagonal from the foot, round the upper bowl, down across to the lower bowl and out
/// along the arm.
fn ampersand(g: &mut Draw) {
    let p = g.p;
    let (sw, hw) = (p.cap_stem, p.cap_hair);
    let (top, bot) = (p.cap + p.over - hw / 2.0, -p.over + hw / 2.0);
    let x0 = p.sb_round - 14.0; // the lower bowl's left edge
    let (xa, xb) = (150.0, 432.0); // the upper bowl's sides
    let us = 0.45 * sw + 44.0; // the upper bowl's stroke: it gains less weight than the stems, to keep its counter
    let right = p.width - 34.0; // the right end of the foot and of the arm
    let foot = cut_pen(0.0, 0.0, sw * 0.92, 129.0, 0.0);
    let arm = cut_pen(0.0, 0.0, hw * 1.04, 64.0, 0.0);
    g.stroke(&[
        cut_pen(right - foot.w / 2.0, 0.0, sw * 0.92, 129.0, 0.0),
        knot(xa + us / 2.0, p.cap * 0.765, us).dir(90.0).k(p.sq),
        knot((xa + xb) / 2.0, top, hw).dir(0.0).k(p.sq),
        knot(xb - us / 2.0, p.cap * 0.765, us).dir(-90.0),
        knot(x0 + sw / 2.0, p.cap * 0.265, sw).dir(-90.0).k(p.sq),
        knot(x0 + 208.0, bot, hw).dir(0.0),
        cut_pen(right + 6.0 - arm.w / 2.0, p.cap * 0.46, hw * 1.04, 64.0, 0.0),
    ]);
}

/// S with a stroke that emerges above and below it. A stroke through the middle fills the counters at reading
/// size and in the Bold.
fn dollar(g: &mut Draw) {
    let p = g.p;
    g.use_char('S', 0.0, 0.0);
    let w = p.cap_stem * 0.92;
    let reach = 96.0;
    g.stroke(&vstem(p.mid() + 2.0, p.cap - p.cap_hair / 2.0, p.cap + reach, w));
    g.stroke(&vstem(p.mid() - 2.0, -reach, p.cap_hair / 2.0, w));
}

fn percent_ring(p: &Params, x0: f64, x1: f64, y0: f64, y1: f64, f: f64) -> Vec<Knot> {
    let (sw, hw) = small_strokes(p);
    ring(x0, y0, x1, y1, sw * f, hw * f, p.sq)
}

fn percent(g: &mut Draw) {
    let p = g.p;
    let (_, hw) = small_strokes(p);
    let (w, h) = (246.0, 308.0);
    g.stroke_closed(&percent_ring(p, 22.0, 22.0 + w, p.cap + p.over - h, p.cap + p.over, 1.0));
    g.stroke_closed(&percent_ring(p, p.width - 22.0 - w, p.width - 22.0, -p.over, -p.over + h, 1.0));
    g.stroke(&diag(112.0, 0.0, p.width - 112.0, p.cap, hw * 1.08));
}

fn perthousand(g: &mut Draw) {
    let p = g.p;
    let (_, hw) = small_strokes(p);
    let (w, h) = (190.0, 270.0);
    g.stroke_closed(&percent_ring(p, 8.0, 8.0 + w, p.cap + p.over - h, p.cap + p.over, 0.84));
    g.stroke_closed(&percent_ring(
        p,
        p.width - 4.0 - 2.0 * w + 6.0,
        p.width - 4.0 - w + 6.0,
        -p.over,
        -p.over + h,
        0.84,
    ));
    g.stroke_closed(&percent_ring(p, p.width - 4.0 - w, p.width - 4.0, -p.over, -p.over + h, 0.84));
    g.stroke(&diag(84.0, 0.0, 330.0, p.cap, hw * 0.96));
}

fn numbersign(g: &mut Draw) {
    let p = g.p;
    let (sw, hw) = small_strokes(p);
    let (sw, hw) = (sw * 1.1, hw * 1.1);
    let (dx, dy) = (108.0, 122.0);
    for x in [p.mid() - dx, p.mid() + dx] {
        g.stroke(&vstem(x, p.axis - 350.0, p.axis + 350.0, sw));
    }
    for y in [p.axis - dy, p.axis + dy] {
        g.stroke(&hbar(36.0, p.width - 36.0, y, hw));
    }
}

fn double_question(g: &mut Draw) {
    let p = g.p;
    let (sw, hw) = small_strokes(p);
    let r = 0.80 * p.punct;
    for x0 in [22.0, p.mid() + 14.0] {
        let xs = x0 + 150.0;
        g.stroke(&question_knots(p, x0, x0 + 264.0, xs, sw * 1.12, hw * 1.12));
        g.dot(xs, r - p.over, r);
    }
}

fn brokenbar(g: &mut Draw) {
    let p = g.p;
    let gap = 80.0 + 0.5 * p.op; // the break, about the axis
    g.stroke(&vstem(p.mid(), p.br_bot, p.axis - gap / 2.0, p.op));
    g.stroke(&vstem(p.mid(), p.axis + gap / 2.0, p.br_top, p.op));
}

// ---------------------------------------------------------------------------------------------------------------
// Guillemets

/// The polygon of a chevron lying on its side: its point at `x_tip`, its arms `t` thick and cut
/// horizontally at `yc - hh` and `yc + hh` with their far corners at `x_end`, its point cut plumb,
/// `flat` tall.
fn chevron(x_tip: f64, x_end: f64, yc: f64, hh: f64, t: f64, flat: f64) -> Vec<V> {
    let s = if x_end > x_tip { 1.0 } else { -1.0 };
    let width = (x_end - x_tip).abs();
    let mut b = t; // the breadth of an arm along its horizontal cut
    for _ in 0..24 {
        b = t * (width - b).hypot(hh) / hh;
    }
    let run = width - b;
    let e = (flat / 2.0) * run / hh;
    vec![
        pt(x_tip + s * e, yc + flat / 2.0),
        pt(x_tip + s * run, yc + hh),
        pt(x_tip + s * width, yc + hh),
        pt(x_tip + s * b, yc),
        pt(x_tip + s * width, yc - hh),
        pt(x_tip + s * run, yc - hh),
        pt(x_tip + s * e, yc - flat / 2.0),
    ]
}

fn guillemets(g: &mut Draw, tips: &[f64], right: bool) {
    let p = g.p;
    let t = p.stem * 0.84;
    for &x in tips {
        let pts = chevron(x, x + 214.0, p.xh / 2.0, 190.0, t, p.stem / 3.0);
        if right {
            let mirrored: Vec<V> = pts.iter().map(|z| pt(p.width - z.x, z.y)).collect();
            g.poly(&mirrored);
        } else {
            g.poly(&pts);
        }
    }
}

fn guilsinglleft(g: &mut Draw) {
    guillemets(g, &[g.p.mid() - 114.0], false);
}

fn guilsinglright(g: &mut Draw) {
    guillemets(g, &[g.p.mid() - 114.0], true);
}

fn guillemotleft(g: &mut Draw) {
    guillemets(g, &[72.0, 286.0], false);
}

fn guillemotright(g: &mut Draw) {
    guillemets(g, &[72.0, 286.0], true);
}

// ---------------------------------------------------------------------------------------------------------------
// Reference marks

/// how far the dagger, section and paragraph signs go below the baseline
const MARK_BOT: f64 = -110.0;

fn dagger(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.mid(), MARK_BOT, p.cap, p.cap_stem));
    g.stroke(&hbar(p.mid() - 196.0, p.mid() + 196.0, p.cap * 0.66, p.cap_hair));
}

fn daggerdbl(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.mid(), MARK_BOT, p.cap, p.cap_stem));
    g.stroke(&hbar(p.mid() - 196.0, p.mid() + 196.0, p.cap * 0.66, p.cap_hair));
    g.stroke(&hbar(p.mid() - 196.0, p.mid() + 196.0, p.cap + MARK_BOT - p.cap * 0.66, p.cap_hair));
}

/// The upper stroke of the section sign in the box (x0, y0)-(x1, y1): the top half of an S, its spine, and a
/// lower bowl that turns back to run into the spine of the stroke below, a third of the box lower.
fn section_half(p: &Params, x0: f64, x1: f64, y0: f64, y1: f64, sw: f64, hw: f64) -> Vec<Knot> {
    let cx = (x0 + x1) / 2.0;
    let hgt = y1 - y0;
    let h = hgt / 1.5; // the height of one S: two of them overlap by half
    let ys = y1 - h; // the foot of this S
    let spine = -30.0;
    let back = V::unit(spine + 180.0);
    vec![
        cut(x1 - 10.0, y1 - 0.22 * h, hw * 1.04, 140.0),
        knot(cx + 4.0, y1 - hw / 2.0, hw).dir(180.0).k(p.sq),
        knot(x0 + sw / 2.0, ys + 0.735 * h, sw).dir(-90.0),
        knot(cx, ys + 0.50 * h, sw).dir(spine),
        knot(x1 - sw / 2.0, ys + 0.275 * h, sw).dir(-90.0),
        Knot::at(pt(cx, y0 + 0.50 * h) - 20.0 * back, sw).dir(spine + 180.0),
    ]
}

/// Two S forms, one a third of the height above the other. The lower bowl of the upper one and the upper bowl
/// of the lower one close the loop in the middle, each ending inside the other's spine.
fn section(g: &mut Draw) {
    let p = g.p;
    let (sw, hw) = (p.cap_stem * 0.90, p.cap_hair * 0.90);
    let (x0, x1) = (104.0, p.width - 104.0);
    let (y0, y1) = (MARK_BOT - p.over, p.cap + p.over);
    let half = section_half(p, x0, x1, y0, y1, sw, hw);
    g.stroke(&half);
    g.stroke(&turn(&half, p.mid(), (y0 + y1) / 2.0));
}

/// Two stems and a filled bowl: the bowl is a stroke with its counter covered.
fn paragraph(g: &mut Draw) {
    let p = g.p;
    let (sw, hw) = (p.cap_stem * 0.80, p.cap_hair);
    let (x1, x2) = (p.mid() + 22.0, p.mid() + 22.0 + sw + 78.0); // the stems
    g.stroke(&vstem(x1, MARK_BOT, p.cap, sw));
    g.stroke(&vstem(x2, MARK_BOT, p.cap, sw));
    g.stroke(&hbar(x1, x2 + sw / 2.0 + 34.0, p.cap - hw / 2.0, hw));
    let (x_edge, yb) = (62.0, p.cap * 0.42);
    let xf = x1 - 96.0;
    let (yt, ybc) = (p.cap - hw / 2.0, yb + hw / 2.0);
    let xc = x_edge + p.cap_stem / 2.0;
    let ym = (yt + ybc) / 2.0;
    let side = [
        knot(x1, yt, hw).pen(90.0).line(),
        knot(xf, yt, hw).pen(90.0).dir(180.0).k(p.sq),
        knot(xc, ym, p.cap_stem).dir(-90.0).k(p.sq),
        knot(xf, ybc, hw).pen(90.0).dir(0.0).line(),
        knot(x1, ybc, hw).pen(90.0),
    ];
    g.stroke(&side);
    // cover the counter with a polygon whose corners lie on the stroke's centre line
    let k = 0.75 * p.sq;
    let upper = pt(xc, yt) * k + (pt(xf, yt) + pt(xc, ym)) / 2.0 * (1.0 - k);
    let lower = pt(xc, ybc) * k + (pt(xf, ybc) + pt(xc, ym)) / 2.0 * (1.0 - k);
    g.poly(&[pt(x1, yt), pt(xf, yt), upper, pt(xc, ym), lower, pt(xf, ybc), pt(x1, ybc)]);
}

// ---------------------------------------------------------------------------------------------------------------
// Small letters and the signs that hold them

fn small_ring(p: &Params, x0: f64, x1: f64, y0: f64, y1: f64, f: f64) -> Vec<Knot> {
    let (sw, hw) = small_strokes(p);
    ring(x0, y0, x1, y1, sw * f, hw * f, p.sq)
}

fn small_c(g: &mut Draw, x0: f64, x1: f64, y0: f64, y1: f64, f: f64) {
    let p = g.p;
    let (sw, hw) = small_strokes(p);
    let (sw, hw) = (sw * f, hw * f);
    let h = y1 - y0;
    let cx = (x0 + x1) / 2.0 + 6.0;
    g.stroke(&[
        cut(x1, y1 - 0.24 * h, hw * 1.04, 140.0),
        knot(cx, y1 - hw / 2.0, hw).dir(180.0).k(p.sq),
        knot(x0 + sw / 2.0, (y0 + y1) / 2.0, sw).dir(-90.0).k(p.sq),
        knot(cx, y0 + hw / 2.0, hw).dir(0.0),
        cut(x1, y0 + 0.24 * h, hw * 1.04, 40.0),
    ]);
}

/// A double-storey a in a box, after the lowercase.
fn small_a(g: &mut Draw, x0: f64, x1: f64, y0: f64, y1: f64, f: f64) {
    let p = g.p;
    let (sw, hw) = small_strokes(p);
    let (sw, hw) = (sw * f, hw * f);
    let h = y1 - y0;
    let xr = x1 - sw / 2.0;
    let top = y1 - hw / 2.0;
    let crest = x0 + 0.48 * (xr - x0);
    g.stroke(&[
        cut(x0 + 16.0, y1 - 0.21 * h, hw * 1.04, 40.0),
        knot(crest, top, hw).dir(0.0).k(p.sq),
        knot(xr, top - 0.9 * (xr - crest), sw).pen(0.0).dir(-90.0).line(),
        knot(xr, y0, sw).pen(0.0),
    ]);
    let bt = y0 + 0.59 * h;
    let bot = y0 + hw / 2.0;
    let j = p.join * sw;
    let bx = x0 + 0.52 * (xr - sw / 2.0 - x0);
    g.stroke(&[
        knot(xr, bt - hw / 2.0, hw).pen(90.0).dir(180.0).line(),
        knot(bx + 16.0, bt - hw / 2.0, hw).pen(90.0).dir(180.0).k(p.sq),
        knot(x0 + sw / 2.0, (bt + y0) / 2.0, sw).dir(-90.0).k(p.sq),
        knot(bx, bot, hw).dir(0.0),
        Knot::at(pt(xr - sw / 2.0 + 3.0, y0 + 0.19 * h) + ((j / 2.0) * V::unit(52.0)).right(), j).dir(52.0),
    ]);
}

#[allow(non_snake_case)]
fn small_R(g: &mut Draw, x0: f64, x1: f64, y0: f64, y1: f64, f: f64) {
    let p = g.p;
    let (sw, hw) = small_strokes(p);
    let (sw, hw) = (sw * f, hw * f);
    let h = y1 - y0;
    let x = x0 + sw / 2.0;
    let waist = y0 + 0.45 * h;
    g.stroke(&vstem(x, y0, y1, sw));
    g.stroke(&dbowl(x, x1 - 6.0, waist - hw / 2.0, y1, sw, hw, p.sq, 0.34 * (x1 - x0)));
    let leg = diag(0.0, waist, x1 - 0.55 * sw, y0, sw * 0.96)[1];
    g.stroke(&[knot((x0 + x1) / 2.0, waist, sw * 0.96).line(), leg]);
}

#[allow(non_snake_case)]
fn small_T(g: &mut Draw, x0: f64, x1: f64, y0: f64, y1: f64, f: f64) {
    let p = g.p;
    let (sw, hw) = small_strokes(p);
    g.stroke(&vstem((x0 + x1) / 2.0, y0, y1, sw * f));
    g.stroke(&hbar(x0, x1, y1 - hw * f / 2.0, hw * f));
}

#[allow(non_snake_case)]
fn small_M(g: &mut Draw, x0: f64, x1: f64, y0: f64, y1: f64, f: f64) {
    let p = g.p;
    let (sw, _) = small_strokes(p);
    let sw = sw * f;
    g.stroke(&vstem(x0 + sw / 2.0, y0, y1, sw));
    g.stroke(&vstem(x1 - sw / 2.0, y0, y1, sw));
    g.poly(&vee(x0, x1, y1, y0 + 0.30 * (y1 - y0), sw * 0.86, sw * 0.7));
}

#[allow(non_snake_case)]
fn small_N(g: &mut Draw, x0: f64, x1: f64, y0: f64, y1: f64, f: f64) {
    let p = g.p;
    let (sw, _) = small_strokes(p);
    let sw = sw * f;
    g.stroke(&vstem(x0 + sw / 2.0, y0, y1, sw));
    g.stroke(&vstem(x1 - sw / 2.0, y0, y1, sw));
    let d = diag(0.0, y1, 1.0, y0, sw * 0.92);
    let w = d[0].w * (x1 - x0 - sw).hypot(y1 - y0) / 1.0_f64.hypot(y1 - y0);
    g.poly(&[pt(x0, y1), pt(x0 + w, y1), pt(x1, y0), pt(x1 - w, y0)]);
}

/// the sides of the ring of the copyright and registered signs
const CIRCLED: (f64, f64) = (16.0, 584.0);

/// The ring of © and ®; returns the height of its centre and its radius.
fn _circle(g: &mut Draw) -> (f64, f64) {
    let p = g.p;
    let (x0, x1) = CIRCLED;
    let r = (x1 - x0) / 2.0;
    let cy = p.cap / 2.0;
    g.stroke_closed(&small_ring(p, x0, x1, cy - r, cy + r, 0.86));
    (cy, r)
}

fn copyright(g: &mut Draw) {
    let (cy, _) = _circle(g);
    small_c(g, 186.0, 420.0, cy - 152.0, cy + 152.0, 0.92);
}

fn registered(g: &mut Draw) {
    let (cy, _) = _circle(g);
    small_R(g, 196.0, 424.0, cy - 146.0, cy + 146.0, 0.92);
}

fn trademark(g: &mut Draw) {
    let p = g.p;
    let y0 = p.cap - 300.0;
    small_T(g, 10.0, 262.0, y0, p.cap, 0.92);
    small_M(g, 298.0, 590.0, y0, p.cap, 0.92);
}

const ORDINAL: (f64, f64) = (150.0, 450.0);

/// The bar under an ordinal; returns the height the letter stands on.
fn _ordinal_bar(g: &mut Draw) -> f64 {
    let p = g.p;
    let (_, hw) = small_strokes(p);
    let y = p.cap - 420.0;
    g.stroke(&hbar(ORDINAL.0, ORDINAL.1, y + hw / 2.0, hw));
    y + hw + 64.0
}

fn ordmasculine(g: &mut Draw) {
    let p = g.p;
    let y0 = _ordinal_bar(g);
    g.stroke_closed(&small_ring(p, ORDINAL.0 + 6.0, ORDINAL.1 - 6.0, y0 - p.over / 2.0, p.cap + p.over, 1.0));
}

fn ordfeminine(g: &mut Draw) {
    let p = g.p;
    let y0 = _ordinal_bar(g);
    small_a(g, ORDINAL.0 + 12.0, ORDINAL.1 - 14.0, y0, p.cap + p.over, 1.0);
}

fn degree(g: &mut Draw) {
    let p = g.p;
    let d = 276.0;
    g.stroke_closed(&small_ring(p, p.mid() - d / 2.0, p.mid() + d / 2.0, p.cap + p.over - d, p.cap + p.over, 1.0));
}

fn numero(g: &mut Draw) {
    let p = g.p;
    let (_, hw) = small_strokes(p);
    small_N(g, 22.0, 318.0, 0.0, p.cap, 0.94);
    let (x0, x1) = (356.0, p.width - 14.0);
    g.stroke_closed(&small_ring(p, x0, x1, p.cap + p.over - 300.0, p.cap + p.over, 0.9));
    g.stroke(&hbar(x0 + 8.0, x1 - 8.0, p.cap - 392.0 + hw / 2.0, hw * 0.9));
}

// ---------------------------------------------------------------------------------------------------------------
// Currency

fn currency(g: &mut Draw) {
    let p = g.p;
    let (_sw, hw) = small_strokes(p);
    let cy = p.cap / 2.0;
    let r = 158.0;
    g.stroke_closed(&small_ring(p, p.mid() - r, p.mid() + r, cy - r, cy + r, 1.08));
    let (a, b) = (0.62 * r, 240.0);
    for sx in [-1.0, 1.0] {
        for sy in [-1.0, 1.0] {
            g.stroke(&diag(p.mid() + sx * a, cy + sy * a, p.mid() + sx * b, cy + sy * b, hw * 1.08));
        }
    }
}

fn cent(g: &mut Draw) {
    let p = g.p;
    g.use_char('c', 0.0, 0.0);
    let w = p.stem * 0.92;
    let reach = 96.0;
    g.stroke(&vstem(p.mid() + 8.0, p.xh - p.hair / 2.0, p.xh + reach, w));
    g.stroke(&vstem(p.mid() + 8.0, -reach, p.hair / 2.0, w));
}

fn sterling(g: &mut Draw) {
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
    g.stroke(&hbar(92.0, p.width - 176.0, p.cap * 0.46, hw));
}

fn yen(g: &mut Draw) {
    let p = g.p;
    let (sw, hw) = (p.cap_stem, p.cap_hair);
    let t = sw * 0.94;
    let yv = p.cap * 0.40; // where the arms meet the stem
    g.poly(&vee(34.0, p.width - 34.0, p.cap, yv, t, sw));
    g.stroke(&vstem(p.mid(), 0.0, yv + sw, sw));
    for y in [p.cap * 0.40, p.cap * 0.40 - 1.9 * hw] {
        g.stroke(&hbar(p.mid() - 190.0, p.mid() + 190.0, y - hw * 0.45, hw * 0.9));
    }
}

fn euro(g: &mut Draw) {
    let p = g.p;
    let (sw, hw) = (p.cap_stem, p.cap_hair);
    let (x0, x1) = (96.0, p.width - 44.0);
    let cx = (x0 + x1) / 2.0 + 20.0;
    let (top, bot) = (p.cap + p.over - hw / 2.0, -p.over + hw / 2.0);
    g.stroke(&[
        cut(x1, p.cap - 0.20 * p.cap, hw * 1.04, 140.0),
        knot(cx, top, hw).dir(180.0).k(p.sq),
        knot(x0 + sw / 2.0, p.cap / 2.0, sw).dir(-90.0).k(p.sq),
        knot(cx, bot, hw).dir(0.0),
        cut(x1 + 4.0, 0.20 * p.cap, hw * 1.04, 40.0),
    ]);
    for y in [p.cap * 0.5 + 0.95 * hw, p.cap * 0.5 - 0.95 * hw] {
        g.stroke(&hbar(22.0, x1 - 150.0, y, hw * 0.86));
    }
}

pub fn register(reg: &mut Registry) {
    reg.module("punct");
    reg.ch('.', period);
    reg.ch(',', comma);
    reg.ch(':', colon);
    reg.ch(';', semicolon);
    reg.ch('…', ellipsis);
    reg.ch('·', periodcentered);
    reg.ch('•', bullet);
    reg.ch('‣', triangle_bullet);
    reg.ch('!', exclam);
    reg.ch('¡', exclamdown);
    reg.ch('?', question);
    reg.ch('¿', questiondown);
    reg.ch('‼', double_exclam);
    reg.ch('\'', quotesingle);
    reg.ch('"', quotedbl);
    reg.ch('`', grave);
    reg.ch('’', quoteright);
    reg.ch('‘', quoteleft);
    reg.ch('‛', quotereversed);
    reg.ch('‚', quotesinglbase);
    reg.ch('”', quotedblright);
    reg.ch('“', quotedblleft);
    reg.ch('„', quotedblbase);
    reg.ch('′', prime);
    reg.ch('″', dblprime);
    reg.ch('(', parenleft);
    reg.ch(')', parenright);
    reg.ch('[', bracketleft);
    reg.ch(']', bracketright);
    reg.ch('{', braceleft);
    reg.ch('}', braceright);
    reg.ch('_', underscore);
    reg.ch('‐', hyphen_true);
    reg.ch('‑', hyphen_nonbreaking);
    reg.ch('–', endash);
    reg.ch('‒', figuredash);
    reg.ch('—', emdash);
    reg.ch('―', horizontalbar);
    reg.ch('\u{a0}', nbspace);
    reg.ch('\u{ad}', softhyphen);
    reg.ch('@', at);
    reg.ch('&', ampersand);
    reg.ch('$', dollar);
    reg.ch('%', percent);
    reg.ch('‰', perthousand);
    reg.ch('#', numbersign);
    reg.ch('⁇', double_question);
    reg.ch('¦', brokenbar);
    reg.ch('‹', guilsinglleft);
    reg.ch('›', guilsinglright);
    reg.ch('«', guillemotleft);
    reg.ch('»', guillemotright);
    reg.ch('†', dagger);
    reg.ch('‡', daggerdbl);
    reg.ch('§', section);
    reg.ch('¶', paragraph);
    reg.ch('©', copyright);
    reg.ch('®', registered);
    reg.ch('™', trademark);
    reg.ch('º', ordmasculine);
    reg.ch('ª', ordfeminine);
    reg.ch('°', degree);
    reg.ch('№', numero);
    reg.ch('¤', currency);
    reg.ch('¢', cent);
    reg.ch('£', sterling);
    reg.ch('¥', yen);
    reg.ch('€', euro);
}
