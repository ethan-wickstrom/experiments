//! Technical symbols: mathematical delimiters, the pieces of tall brackets, keyboard and interface signs.
//!
//! Delimiters (⌈ ⟨ ⟦ ⟪ ⦃ ⟮ and their kin) are drawn as `punct` draws ( [ {: from `p.br_bot` to `p.br_top`, with
//! the brackets' strokes and in the brackets' place, and they slant in the italic. The angle brackets are not `<` and
//! `>`: they are as tall as a bracket, steep, lighter than `<`, and stand where a bracket stands. A doubled delimiter is
//! drawn with `fine`, its two strokes `double_gap` apart, so that it stays open in the Bold at 13 px.
//!
//! The bracket pieces (⎛ ⎜ ⎝ ⎡ ⎧ ⎨ ⌠ ⎮ and their kin) are stacked on consecutive lines of a terminal to make one
//! tall bracket. Like box drawing, their vertical strokes run to the edges of the line (`p.line_bot`,
//! `p.line_top`), and every piece of one bracket puts that stroke at the same x with the same weight, the
//! bracket's stem, so that the pieces join without a step. Their hooks, corners and cusp are those of ( [ {. They
//! do not slant.
//!
//! The keyboard and interface signs (⌘ ⌃ ⌫ ⎋ and their kin) are geometric: the operators' stroke, or `fine` where
//! strokes crowd, centred on the axis and spanning the operators' span. They do not slant.

use rachis_kernel::{Draw, Knot, Opt, Params, Registry, V, knot, pt};

use crate::operators::{cross, fine, half_span, mirrored, outline, tip};
use crate::parts::{cut_pen, elbow, flip, hbar, mirror, vee, vstem};
use crate::punct::bracket_stem;

// ---------------------------------------------------------------------------------------------------------------
// Measurements the group derives from the parameters

/// The white between the two strokes of a doubled delimiter: about a pixel at 13 px in every weight.
pub fn double_gap(p: &Params) -> f64 {
    70.0 + 0.15 * p.op
}

/// The stroke of the angle brackets: lighter than the bracket's stem and than <.
pub fn angle_stroke(p: &Params) -> f64 {
    0.85 * bracket_stem(p)
}

/// The angle of the strokes of an angle bracket off the vertical, in degrees.
const ANGLE: f64 = 18.0;

/// The same in radians for the master `p`: a taller bracket is steeper, because it gains less in breadth than
/// in height (0.45 of it, about what the reference mathematics fonts do).
fn angle_of(p: &Params) -> f64 {
    (ANGLE.to_radians().tan() * (1.0 + 0.45 * (p.delim - 1.0)) / p.delim).atan()
}

/// How far right of the middle of the cell an opening delimiter is centred, as the opening brackets are.
const LEAN: f64 = 18.0;

/// The middle of the brackets' height.
fn br_mid(p: &Params) -> f64 {
    (p.br_top + p.br_bot) / 2.0
}

/// The parenthesis as `punct` draws it: the outer edge of its arc at the middle and the x of its ends.
fn paren_x(p: &Params) -> (f64, f64) {
    (p.mid() - 114.0, p.mid() + 178.0)
}

/// The ends of the parenthesis's arc: their breadth, and their angle from the horizontal.
fn paren_end(p: &Params) -> (f64, f64) {
    (p.hair * 0.95, 41.0)
}

/// The square bracket as `punct` draws it: the outer edge of its stem and the end of its arms.
fn bracket_x(p: &Params) -> (f64, f64) {
    (p.mid() - 48.0 - 0.45 * p.stem, p.mid() + 158.0 + 0.38 * p.stem)
}

/// The brace as `punct` draws it: the centre of its spine, the point of its cusp, the end of its arms, the radius
/// of its shoulders and of the turn into the cusp (on the centre line).
struct Brace {
    xs: f64,
    x_tip: f64,
    x_arm: f64,
    r1: f64,
    r2: f64,
}

fn brace(p: &Params) -> Brace {
    Brace {
        xs: p.mid() - 18.0 + 0.12 * p.stem,
        x_tip: p.mid() - 220.0 - 0.36 * p.stem,
        x_arm: p.mid() + 150.0 + 0.36 * p.stem,
        r1: 140.0,
        r2: 104.0,
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Primitives

/// Reflect each stroke left to right in the middle of the cell when `right`.
fn strokes(g: &mut Draw, list: &[Vec<Knot>], right: bool) {
    let p = g.p;
    for s in list {
        g.stroke(&if right { mirror(s, p.mid()) } else { s.clone() });
    }
}

/// `knots` turned a quarter of a circle clockwise about `c`.
fn quarter(knots: &[Knot], c: V) -> Vec<Knot> {
    knots
        .iter()
        .map(|k| Knot {
            z: c + pt(k.z.y - c.y, c.x - k.z.x),
            dir: k.dir.map(|d| d - 90.0),
            pen: k.pen.map(|a| a - 90.0),
            ..*k
        })
        .collect()
}

/// A stroke `t` thick through `points` in straight segments with mitred corners, cut at its first end along `ends`
/// and at its last along `end` (90: plumb; 0: level). Copied from `symbols`, where it is private.
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

/// The width of an angle bracket `rise` tall above and below its point, its strokes `t` thick.
fn angle_width(a: f64, rise: f64, t: f64) -> f64 {
    rise * a.tan() + t / a.cos()
}

/// The polygon of an angle bracket pointing left: its outer edges meet at (`x_tip`, `cy`), where it is cut
/// plumb, `flat` tall; its strokes are `t` thick, `a` radians off the vertical, and cut level at `cy` ± `rise`.
fn angle(a: f64, x_tip: f64, cy: f64, rise: f64, t: f64, flat: f64) -> Vec<V> {
    let run = rise * a.tan();
    let b = t / a.cos(); // the stroke's breadth along a level cut
    let e = flat / 2.0 * a.tan();
    vec![
        pt(x_tip + e, cy + flat / 2.0),
        pt(x_tip + run, cy + rise),
        pt(x_tip + run + b, cy + rise),
        pt(x_tip + b, cy),
        pt(x_tip + run + b, cy - rise),
        pt(x_tip + run, cy - rise),
        pt(x_tip + e, cy - flat / 2.0),
    ]
}

/// The upper half of the opening brace from `punct`, with its strokes given: arm, shoulder, spine, and the turn
/// into the cusp on the axis. Its spine is moved `dx`.
fn brace_half(p: &Params, b: &Brace, h: f64, bs: f64, dx: f64) -> Vec<Knot> {
    let yt = p.br_top - h / 2.0;
    let xs = b.xs + dx;
    vec![
        knot(b.x_arm + dx, yt, h).pen(90.0).line(),
        knot(xs + b.r1, yt, h).pen(90.0).dir(180.0).k(p.sq),
        knot(xs, yt - b.r1, bs).pen(0.0).dir(-90.0).line(),
        knot(xs, p.axis + b.r2, bs).pen(0.0).dir(-90.0).k(p.sq),
        knot(xs - b.r2, p.axis, h).pen(90.0).dir(180.0).line(),
        knot(b.x_tip + dx, p.axis, h * 0.5).pen(90.0),
    ]
}

/// The opening parenthesis from `punct` with its stroke given and moved `dx`.
fn paren_knots(p: &Params, bs: f64, te: f64, dx: f64) -> Vec<Knot> {
    let (x_out, x_tip) = paren_x(p);
    let (_, d) = paren_end(p);
    let xe = x_tip - cut_pen(0.0, 0.0, te, -180.0 + d, 0.0).w / 2.0 + dx;
    vec![
        cut_pen(xe, p.br_top, te, -180.0 + d, 0.0).k(p.sq),
        knot(x_out + bs / 2.0 + dx, br_mid(p), bs).dir(-90.0).k(p.sq),
        cut_pen(xe, p.br_bot, te, -d, 0.0),
    ]
}

// ---------------------------------------------------------------------------------------------------------------
// Delimiters

/// ⌈ ⌉ ⌊ ⌋: the square bracket with one arm.
fn ceiling(g: &mut Draw, top: bool, right: bool) {
    let p = g.p;
    let bs = bracket_stem(p);
    let (x0, x1) = bracket_x(p);
    let y = if top { p.br_top - p.hair / 2.0 } else { p.br_bot + p.hair / 2.0 };
    strokes(g, &[vstem(x0 + bs / 2.0, p.br_bot, p.br_top, bs), hbar(x0, x1, y, p.hair)], right);
}

/// ⌜ ⌝ ⌞ ⌟: a short corner of the square bracket, at the height of the capitals or on the baseline.
fn corner(g: &mut Draw, top: bool, right: bool) {
    let p = g.p;
    let bs = bracket_stem(p);
    let (x0, _) = bracket_x(p);
    let x0 = x0 - 20.0;
    let (arm, leg) = (210.0, 0.40 * p.cap); // the length of the arm and of the stem, outer edges
    let (y_edge, y_end, y_arm) =
        if top { (p.cap, p.cap - leg, p.cap - p.hair / 2.0) } else { (0.0, leg, p.hair / 2.0) };
    strokes(
        g,
        &[vstem(x0 + bs / 2.0, y_edge.min(y_end), y_edge.max(y_end), bs), hbar(x0, x0 + arm, y_arm, p.hair)],
        right,
    );
}

/// ⟨ ⟩: as tall as a bracket, steep, lighter than <.
fn angle_bracket(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = angle_stroke(p);
    let a = angle_of(p);
    let rise = (p.br_top - p.br_bot) / 2.0;
    let x_tip = p.mid() + LEAN - angle_width(a, rise, t) / 2.0;
    let pts = angle(a, x_tip, br_mid(p), rise, t, 0.8 * tip(p));
    g.poly(&if right { mirrored(&pts, p.mid()) } else { pts });
}

/// ⟪ ⟫: two angle brackets, one inside the other, with the fine stroke.
fn double_angle(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = fine(p);
    let a = angle_of(p);
    let rise = (p.br_top - p.br_bot) / 2.0;
    let pitch = (t + double_gap(p)) / a.cos();
    let x_tip = p.mid() + LEAN - (angle_width(a, rise, t) + pitch) / 2.0;
    for x in [x_tip, x_tip + pitch] {
        let pts = angle(a, x, br_mid(p), rise, t, 0.8 * tip(p));
        g.poly(&if right { mirrored(&pts, p.mid()) } else { pts });
    }
}

/// ⟦ ⟧: the square bracket with a doubled stem, all of it with the fine stroke.
fn white_bracket(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = fine(p);
    let pitch = t + double_gap(p);
    let (x0, x1) = bracket_x(p);
    let x0 = x0 - 0.5 * pitch;
    strokes(
        g,
        &[
            vstem(x0 + t / 2.0, p.br_bot, p.br_top, t),
            vstem(x0 + t / 2.0 + pitch, p.br_bot, p.br_top, t),
            hbar(x0, x1, p.br_top - t / 2.0, t),
            hbar(x0, x1, p.br_bot + t / 2.0, t),
        ],
        right,
    );
}

/// ⦃ ⦄: the brace with a second stem inside its spine, from arm to arm, all of it with the fine stroke.
fn white_brace(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = fine(p);
    let b = brace(p);
    // the second stem takes room on the cusp's side: the cusp is as much shorter as the brace's is longer than
    // it was before the cell had to hold both
    let b = Brace { x_tip: b.x_tip + 60.0, ..b };
    let pitch = t + double_gap(p);
    let dx = -0.5 * pitch;
    let mut half = brace_half(p, &b, t, t, dx);
    half[0].z.x = b.x_arm; // the arms keep their ends, so that they run on past the second stem
    let low = flip(&half, p.axis);
    let inner = vstem(b.xs + dx + pitch, p.br_bot + t / 2.0, p.br_top - t / 2.0, t);
    strokes(g, &[half, low, inner], right);
}

/// ⟮ ⟯: the parenthesis flattened: a straight stem whose ends turn as the parenthesis does.
fn flat_paren(g: &mut Draw, right: bool) {
    let p = g.p;
    let bs = bracket_stem(p);
    let (te, _) = paren_end(p);
    let d = 34.0; // the angle of the ends from the horizontal
    let x_out = p.mid() - 84.0; // the outer edge of the stem
    let x_tip = p.mid() + 132.0;
    let r = 0.27 * (p.br_top - p.br_bot); // the height of each turn
    let xs = x_out + bs / 2.0;
    let xe = x_tip - cut_pen(0.0, 0.0, te, -180.0 + d, 0.0).w / 2.0;
    let k = vec![
        cut_pen(xe, p.br_top, te, -180.0 + d, 0.0).k(p.sq),
        knot(xs, p.br_top - r, bs).dir(-90.0).line(),
        knot(xs, p.br_bot + r, bs).dir(-90.0).k(p.sq),
        cut_pen(xe, p.br_bot, te, -d, 0.0),
    ];
    strokes(g, &[k], right);
}

/// ⦇ ⦈: the parenthesis with a stem inside it that joins its ends, with the fine stroke.
fn image_bracket(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = fine(p);
    let arc = paren_knots(p, t, t, -20.0);
    let (x_out, _) = paren_x(p);
    let x = x_out - 20.0 + t + double_gap(p) + 0.5 * t + 36.0;
    strokes(g, &[arc, vstem(x, p.br_bot + 30.0, p.br_top - 30.0, t)], right);
}

/// ⟬ ⟭: the tortoise-shell bracket (a stem whose ends turn by straight bevels into short arms) with a doubled
/// stem, with the fine stroke.
fn white_shell(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = fine(p);
    let pitch = t + double_gap(p);
    let (x0, x1) = bracket_x(p);
    let x = x0 - 0.5 * pitch + t / 2.0; // the outer stem's centre line
    let c = 150.0; // the run of the bevels
    let (yt, yb) = (p.br_top - t / 2.0, p.br_bot + t / 2.0);
    let outer =
        path(&[pt(x1, yt), pt(x + c, yt), pt(x, yt - c), pt(x, yb + c), pt(x + c, yb), pt(x1, yb)], t, 90.0, 90.0);
    let inner = vstem(x + pitch, yt - c + pitch, yb + c - pitch, t);
    strokes(g, &[outer, inner], right);
}

// ---------------------------------------------------------------------------------------------------------------
// Bracket pieces

/// ⎛: the stem of ( from the bottom of the line, turning at the middle of the brackets' height as the upper half
/// of ( turns.
fn paren_hook(p: &Params) -> Vec<Knot> {
    let bs = bracket_stem(p);
    let (x_out, x_tip) = paren_x(p);
    let (te, d) = paren_end(p);
    let x = x_out + bs / 2.0;
    let xe = x_tip - cut_pen(0.0, 0.0, te, d, 0.0).w / 2.0;
    vec![
        knot(x, p.line_bot, bs).pen(0.0).line(),
        knot(x, br_mid(p), bs).dir(90.0).k(p.sq),
        cut_pen(xe, p.br_top, te, d, 0.0),
    ]
}

/// The knots of an upper piece turned upside down about the middle of the brackets, the end of its stem moved
/// from the bottom of the line to its top.
fn hook_down(p: &Params, knots: &[Knot]) -> Vec<Knot> {
    let mut k = flip(knots, br_mid(p));
    let foot = 2.0 * br_mid(p) - p.line_bot;
    for kn in k.iter_mut().filter(|kn| (kn.z.y - foot).abs() < 1e-6) {
        kn.z.y = p.line_top;
    }
    k
}

/// ⎛ ⎜ ⎝ and, when `right`, ⎞ ⎟ ⎠. `part`: 1 the upper hook, 0 the extension, -1 the lower hook.
fn paren_piece(g: &mut Draw, part: i32, right: bool) {
    let p = g.p;
    let k = match part {
        1 => paren_hook(p),
        -1 => hook_down(p, &paren_hook(p)),
        _ => {
            let (x_out, _) = paren_x(p);
            vstem(x_out + bracket_stem(p) / 2.0, p.line_bot, p.line_top, bracket_stem(p))
        }
    };
    strokes(g, &[k], right);
}

/// ⎡ ⎢ ⎣ and, when `right`, ⎤ ⎥ ⎦.
fn bracket_piece(g: &mut Draw, part: i32, right: bool) {
    let p = g.p;
    let bs = bracket_stem(p);
    let (x0, x1) = bracket_x(p);
    let x = x0 + bs / 2.0;
    let list = match part {
        1 => vec![vstem(x, p.line_bot, p.br_top, bs), hbar(x0, x1, p.br_top - p.hair / 2.0, p.hair)],
        -1 => vec![vstem(x, p.br_bot, p.line_top, bs), hbar(x0, x1, p.br_bot + p.hair / 2.0, p.hair)],
        _ => vec![vstem(x, p.line_bot, p.line_top, bs)],
    };
    strokes(g, &list, right);
}

/// ⎧: the arm and shoulder of {, its spine running to the bottom of the line.
fn brace_hook(p: &Params) -> Vec<Knot> {
    let mut k = brace_half(p, &brace(p), p.hair, bracket_stem(p), 0.0);
    k.truncate(3);
    k[2] = k[2].line();
    k.push(knot(k[2].z.x, p.line_bot, bracket_stem(p)).pen(0.0));
    k
}

/// The upper half of ⎨: the spine from the top of the line and the turn into the cusp of {.
fn brace_middle(p: &Params) -> Vec<Knot> {
    let k = brace_half(p, &brace(p), p.hair, bracket_stem(p), 0.0);
    let mut out = vec![knot(k[3].z.x, p.line_top, bracket_stem(p)).pen(0.0).line()];
    out.extend_from_slice(&k[3..]);
    out
}

/// ⎧ ⎨ ⎩ ⎪ and, when `right`, ⎫ ⎬ ⎭ (⎪ serves both). `part`: 1 upper, 2 middle, -1 lower, 0 extension.
fn brace_piece(g: &mut Draw, part: i32, right: bool) {
    let p = g.p;
    let list = match part {
        1 => vec![brace_hook(p)],
        -1 => vec![hook_down(p, &brace_hook(p))],
        2 => {
            let up = brace_middle(p);
            let mut down = flip(&up, p.axis);
            down[0].z.y = p.line_bot;
            vec![up, down]
        }
        _ => vec![vstem(brace(p).xs, p.line_bot, p.line_top, bracket_stem(p))],
    };
    strokes(g, &list, right);
}

/// How far the hook of the integral's halves reaches from the stem, to the end of its cut.
fn integral_reach(p: &Params) -> f64 {
    150.0 + 0.25 * p.stem
}

/// ⌠ ⌡ ⎮: the integral cut in halves, its stem in the middle of the cell; the hooks end as the arm of f does.
fn integral_piece(g: &mut Draw, part: i32) {
    let p = g.p;
    let bs = bracket_stem(p);
    let reach = integral_reach(p);
    let r = 0.66 * reach;
    let k = match part {
        1 => elbow(p.mid(), p.line_bot, p.br_top, p.mid() + reach, bs, p.hair, p.sq, r),
        -1 => elbow(p.mid(), p.line_top, p.br_bot, p.mid() - reach, bs, p.hair, p.sq, r),
        _ => vstem(p.mid(), p.line_bot, p.line_top, bs),
    };
    g.stroke(&k);
}

/// ⎰ ⎱: a brace's upper hook over the lower hook of the other brace, in one line: arm, shoulder, spine, shoulder,
/// arm.
fn brace_section(g: &mut Draw, right: bool) {
    let p = g.p;
    let bs = bracket_stem(p);
    let h = p.hair;
    let r = brace(p).r1;
    let xs = p.mid();
    let reach = r + 60.0;
    let (yt, yb) = (p.br_top - h / 2.0, p.br_bot + h / 2.0);
    let k = vec![
        knot(xs + reach, yt, h).pen(90.0).line(),
        knot(xs + r, yt, h).pen(90.0).dir(180.0).k(p.sq),
        knot(xs, yt - r, bs).pen(0.0).dir(-90.0).line(),
        knot(xs, yb + r, bs).pen(0.0).dir(-90.0).k(p.sq),
        knot(xs - r, yb, h).pen(90.0).dir(180.0).line(),
        knot(xs - reach, yb, h).pen(90.0),
    ];
    strokes(g, &[k], right);
}

/// ⎴ ⎵: the square bracket lying over (or under) what it groups: a bar across the span with its ends turned down
/// (or up), at the top (or bottom) of the brackets.
fn horizontal_bracket(g: &mut Draw, top: bool) {
    let p = g.p;
    let t = p.op;
    let depth = 150.0;
    let y = p.br_top - 60.0;
    let list = vec![
        hbar(p.op_l, p.op_r(), y - t / 2.0, t),
        vstem(p.op_l + t / 2.0, y - depth, y, t),
        vstem(p.op_r() - t / 2.0, y - depth, y, t),
    ];
    for s in list {
        g.stroke(&if top { s } else { flip(&s, br_mid(p)) });
    }
}

/// ⏞ ⏟: the brace lying over (or under) what it groups: its arms turn down at the ends of the span, its spine runs
/// across and its cusp points up in the middle.
fn horizontal_brace(g: &mut Draw, top: bool) {
    let p = g.p;
    let t = p.op;
    // a brace drawn across more than the cell has larger curls and a longer cusp, by the square root of what
    // it is longer, so that it is still a brace and not a rule with marks on it
    let k = p.grown.sqrt().min(2.4);
    let (r1, r2) = (70.0 * k, 66.0 * k);
    let ys = p.br_top - 150.0; // the spine's centre line
    let x0 = p.op_l + t / 2.0;
    let half = vec![
        knot(x0, ys - r1 - 50.0 * k, t).pen(0.0).line(),
        knot(x0, ys - r1, t).pen(0.0).dir(90.0).k(p.sq),
        knot(x0 + r1, ys, t).pen(90.0).dir(0.0).line(),
        knot(p.mid() - r2, ys, t).pen(90.0).dir(0.0).k(p.sq),
        knot(p.mid(), ys + r2, t).pen(0.0).dir(90.0).line(),
        knot(p.mid(), ys + r2 + 54.0 * k, 0.5 * t).pen(0.0),
    ];
    for s in [mirror(&half, p.mid()), half] {
        g.stroke(&if top { s } else { flip(&s, br_mid(p)) });
    }
}

/// ⏜ ⏝: the parenthesis lying over (or under) what it groups: an arc that rises from the ends of the span, runs
/// level across the middle and is thin at its ends, as the parenthesis is. Drawn across more than the cell it
/// turns as the brace does, by the square root of what it is longer, and is level between its turns.
fn horizontal_paren(g: &mut Draw, top: bool) {
    let p = g.p;
    let t = p.op;
    let end = 0.55 * t;
    let k = p.grown.sqrt().min(2.4);
    let depth = 118.0 * k;
    let yc = p.br_top - 60.0 - t / 2.0; // the crest's upper edge is the horizontal bracket's
    let (x0, x1) = (p.op_l + end / 2.0, p.op_r() - end / 2.0);
    // the turns never meet: every master draws the same four knots
    let turn = (212.0 * k).min(0.47 * (x1 - x0));
    let a = 2.0 * (depth / turn).atan().to_degrees();
    let knots = vec![
        knot(x0, yc - depth, end).dir(a),
        knot(x0 + turn, yc, t).dir(0.0).line(),
        knot(x1 - turn, yc, t).dir(0.0),
        knot(x1, yc - depth, end).dir(-a),
    ];
    g.stroke(&if top { knots } else { flip(&knots, br_mid(p)) });
}

/// ⏠ ⏡: the tortoise-shell bracket lying over (or under) what it groups: the horizontal bracket with its ends
/// sloping outwards.
fn horizontal_shell(g: &mut Draw, top: bool) {
    let p = g.p;
    let t = p.op;
    let depth: f64 = 150.0;
    let run = 0.62 * depth;
    let y = p.br_top - 60.0;
    let (x0, x1) = (p.op_l, p.op_r());
    let b = t * depth.hypot(run) / depth; // a sloping end's breadth along a level cut
    let inner = b + run * (depth - t) / depth; // where the inner edges meet, from the end of the span
    let points = vec![
        pt(x0, y - depth),
        pt(x0 + run, y),
        pt(x1 - run, y),
        pt(x1, y - depth),
        pt(x1 - b, y - depth),
        pt(x1 - inner, y - t),
        pt(x0 + inner, y - t),
        pt(x0 + b, y - depth),
    ];
    if top {
        g.poly(&points);
    } else {
        let m = br_mid(p);
        g.poly(&points.iter().rev().map(|z| pt(z.x, 2.0 * m - z.y)).collect::<Vec<_>>());
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Keyboard and interface signs

/// Half the width and the height of the arrowhead of ⌃ ⌄ ⌅ ⌆ ⌤ (outer edges).
fn arrowhead(p: &Params) -> (f64, f64) {
    (0.84 * half_span(p), 0.52 * half_span(p) + 0.6 * p.op)
}

/// The arrowhead pointing up (or down) between the heights `y0` (its feet) and `y1` (its point).
fn caret(g: &mut Draw, w: f64, y0: f64, y1: f64) {
    let p = g.p;
    g.poly(&vee(p.mid() - w, p.mid() + w, y0, y1, p.op, tip(p)));
}

fn up_arrowhead(g: &mut Draw) {
    let p = g.p;
    let (w, h) = arrowhead(p);
    caret(g, w, p.axis - h / 2.0, p.axis + h / 2.0);
}

fn down_arrowhead(g: &mut Draw) {
    let p = g.p;
    let (w, h) = arrowhead(p);
    caret(g, w, p.axis + h / 2.0, p.axis - h / 2.0);
}

/// ⌅ ⌆: the arrowhead under one or two bars, centred together on the axis.
fn barred_arrowhead(g: &mut Draw, bars: usize) {
    let p = g.p;
    let (w, h) = arrowhead(p);
    let t = p.op;
    let gap = 0.8 * double_gap(p);
    let total = h + bars as f64 * (gap + t);
    let y0 = p.axis - total / 2.0;
    caret(g, w, y0, y0 + h);
    for i in 0..bars {
        let y = y0 + h + gap + t / 2.0 + i as f64 * (gap + t);
        g.stroke(&hbar(p.mid() - w, p.mid() + w, y, t));
    }
}

/// ⌤: the arrowhead between two bars that run out from its feet to the ends of the span.
fn enter_key(g: &mut Draw) {
    let p = g.p;
    let (_, h) = arrowhead(p);
    let t = p.op;
    let w = 0.56 * half_span(p);
    let y0 = p.axis - h / 2.0;
    caret(g, w, y0, y0 + h);
    let foot = w - 0.5 * t; // inside the foot of each stroke of the arrowhead
    g.stroke(&hbar(p.op_l, p.mid() - foot, y0 + t / 2.0, t));
    g.stroke(&hbar(p.mid() + foot, p.op_r(), y0 + t / 2.0, t));
}

/// ⌐: ¬ reflected.
fn reversed_not(g: &mut Draw) {
    let p = g.p;
    let h = 0.45 * half_span(p);
    let y = p.axis + h - p.op / 2.0;
    g.stroke(&hbar(p.op_l, p.op_r(), y, p.op));
    g.stroke(&vstem(p.op_l + p.op / 2.0, p.axis - h, y, p.op));
}

/// ⌘: a square whose sides run on into a loop at each corner. Drawn as four strokes, one for each corner: half of
/// one side, the loop, half of the next side.
fn place_of_interest(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let f = 0.92; // the radius of a loop's centre line, as a share of half the square's side
    let a = (half_span(p) - t / 2.0) / (1.0 + 2.0 * f); // half the square's side, on the centre line
    let r = f * a;
    let e = 0.5 * t; // how far each stroke runs past the middle of a side, under the next one
    let c = pt(p.mid(), p.axis);
    let k = vec![
        knot(c.x - a, c.y - e, t).line(),
        knot(c.x - a, c.y + a + r, t).dir(90.0).k(p.sq),
        knot(c.x - a - r, c.y + a + 2.0 * r, t).dir(180.0).k(p.sq),
        knot(c.x - a - 2.0 * r, c.y + a + r, t).dir(-90.0).k(p.sq),
        knot(c.x - a - r, c.y + a, t).dir(0.0).line(),
        knot(c.x + e, c.y + a, t),
    ];
    let mut s = k;
    for _ in 0..4 {
        g.stroke(&s);
        s = quarter(&s, c);
    }
}

/// ⌫ ⌦: the erase keys, a pentagon pointing left (or right) with an x in it.
fn erase(g: &mut Draw, right: bool) {
    let p = g.p;
    let t = fine(p);
    let h = 0.80 * half_span(p); // half the height, outer edges
    let (x0, x1) = (p.op_l - 16.0, p.op_r() + 16.0);
    let d = h; // the point is a right angle
    let mut pts =
        vec![pt(x0, p.axis), pt(x0 + d, p.axis - h), pt(x1, p.axis - h), pt(x1, p.axis + h), pt(x0 + d, p.axis + h)];
    let mut cx = x1 - t - 0.5 * (x1 - t - (x0 + 0.62 * d));
    if right {
        pts = mirrored(&pts, p.mid());
        pts.reverse();
        cx = p.width - cx;
    }
    outline(g, &pts, Some(t));
    cross(g, cx, p.axis, 0.42 * (h - t), Some(0.8 * fine(p)));
}

/// ⎋: a circle broken at the upper left, where an arrow leaves it from the centre.
fn escape(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let r = 0.84 * half_span(p); // the circle's outer radius
    let c = pt(p.mid() + 0.02 * r, p.axis - 0.02 * r);
    let rc = r - t / 2.0;
    g.stroke(&[
        knot(c.x, c.y + rc, t).dir(0.0).k(p.sq),
        knot(c.x + rc, c.y, t).dir(-90.0).k(p.sq),
        knot(c.x, c.y - rc, t).dir(180.0).k(p.sq),
        knot(c.x - rc, c.y, t).dir(90.0),
    ]);
    let l = 0.98 * r; // from the centre to the outer corner of the head, across and up
    let tip_ = pt(c.x - l, c.y + l);
    let arm = 0.60 * l;
    let corner = tip_ + pt(t / 2.0, -t / 2.0);
    g.stroke(&path(&[pt(tip_.x + arm, corner.y), corner, pt(corner.x, tip_.y - arm)], t, 90.0, 0.0));
    g.stroke(&[Knot::at(c + pt(0.15 * t, -0.15 * t), t).line(), Knot::at(corner + pt(0.2 * t, -0.2 * t), t)]);
}

/// ⌂: the house: walls, eaves and a pitched roof, outlined.
fn house(g: &mut Draw) {
    let p = g.p;
    let w = 0.88 * half_span(p);
    let (walls, roof) = (0.98 * w, 0.78 * w);
    let y0 = p.axis - (walls + roof) / 2.0;
    let pts = [
        pt(p.mid() - w, y0),
        pt(p.mid() + w, y0),
        pt(p.mid() + w, y0 + walls),
        pt(p.mid(), y0 + walls + roof),
        pt(p.mid() - w, y0 + walls),
    ];
    outline(g, &pts, Some(0.5 * (p.op + fine(p))));
}

/// ⌨: a keyboard reduced to what reads at 16 px: its case, a row of keys and the space bar.
fn keyboard(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let (x0, x1) = (p.op_l - 26.0, p.op_r() + 26.0);
    let h = 0.80 * half_span(p);
    let (y0, y1) = (p.axis - h, p.axis + h);
    outline(g, &[pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1)], Some(t));
    // inside: a margin, a row of keys, a gap, the space bar, a margin, all equal
    let inner = y1 - y0 - 2.0 * t;
    let unit = inner / 5.0;
    let (ix0, ix1) = (x0 + t + unit, x1 - t - unit);
    let keys = 4.0;
    let pitch = (ix1 - ix0 + unit) / keys;
    let ky = y1 - t - unit;
    for i in 0..4 {
        let kx = ix0 + i as f64 * pitch;
        g.rect(kx, ky - unit, kx + pitch - unit, ky);
    }
    let by = y0 + t + unit;
    g.rect(ix0 + pitch, by, ix1 - pitch, by + unit);
}

/// ⏏: the eject key: a triangle pointing up over a bar.
fn eject(g: &mut Draw) {
    let p = g.p;
    let w = 0.82 * half_span(p);
    let (tri, gap, bar) = (0.80 * w, 0.8 * double_gap(p), 1.3 * p.op);
    let y0 = p.axis - (tri + gap + bar) / 2.0;
    g.rect(p.mid() - w, y0, p.mid() + w, y0 + bar);
    let yb = y0 + bar + gap;
    g.poly(&[pt(p.mid() - w, yb), pt(p.mid() + w, yb), pt(p.mid(), yb + tri)]);
}

/// ⌧: the clear key: an x in a box, from corner to corner.
fn x_in_box(g: &mut Draw) {
    let p = g.p;
    let t = 0.5 * (p.op + fine(p));
    let h = 0.80 * half_span(p);
    let (x0, x1) = (p.op_l, p.op_r());
    outline(g, &[pt(x0, p.axis - h), pt(x1, p.axis - h), pt(x1, p.axis + h), pt(x0, p.axis + h)], Some(t));
    let (a, b) = (x0 + t / 2.0, x1 - t / 2.0);
    let (lo, hi) = (p.axis - h + t / 2.0, p.axis + h - t / 2.0);
    let tx = 0.9 * fine(p);
    g.stroke(&[knot(a, lo, tx).line(), knot(b, hi, tx)]);
    g.stroke(&[knot(a, hi, tx).line(), knot(b, lo, tx)]);
}

/// The ring of the circled signs: centred on the axis, a little beyond the span as round shapes are. Returns its
/// outer radius.
fn ring_of(g: &mut Draw, t: f64) -> f64 {
    let p = g.p;
    let r = half_span(p) + p.over;
    crate::operators::circle(g, p.mid(), p.axis, r, None, Some(t));
    r
}

/// ⎈: the helm: a wheel with eight spokes that run on past its rim.
fn helm(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let r = 0.66 * (half_span(p) + p.over);
    crate::operators::circle(g, p.mid(), p.axis, r, None, Some(t));
    let reach = half_span(p) + p.over - 0.5 * t;
    for i in 0..4 {
        let u = V::unit(45.0 * i as f64) * reach;
        g.stroke(&[Knot::at(pt(p.mid(), p.axis) - u, t).line(), Knot::at(pt(p.mid(), p.axis) + u, t)]);
    }
}

/// ⎊: a black triangle pointing down in a circle, clear of it (an outlined one fills in the Bold).
fn circled_triangle_down(g: &mut Draw) {
    let p = g.p;
    let t = fine(p);
    let r = ring_of(g, t) - t - 0.6 * double_gap(p);
    let c = pt(p.mid(), p.axis + 0.12 * r); // a triangle's middle is above its centroid
    let pts: Vec<V> = [270.0, 30.0, 150.0].iter().map(|&a| c + V::unit(a) * r).collect();
    g.poly(&pts);
}

/// ⌀: the diameter sign: a circle crossed at 45 degrees, rounder and smaller than ∅.
fn diameter(g: &mut Draw) {
    let p = g.p;
    let t = 0.5 * (p.op + fine(p));
    let r = 0.74 * half_span(p);
    crate::operators::circle(g, p.mid(), p.axis, r, None, Some(t));
    let d = 0.98 * half_span(p) / std::f64::consts::SQRT_2 + 0.3 * t;
    let u = pt(d, d);
    let c = pt(p.mid(), p.axis);
    g.stroke(&[Knot::at(c - u, 0.5 * (p.op + fine(p))).line(), Knot::at(c + u, 0.5 * (p.op + fine(p)))]);
}

// ---------------------------------------------------------------------------------------------------------------
// Frown and smile

/// ⌢ ⌣: a shallow arc across the span, centred on the axis.
fn arc_sign(g: &mut Draw, frown: bool) {
    let p = g.p;
    let t = p.op;
    let sag = 0.34 * half_span(p); // of the centre line
    let a: f64 = 46.0; // the direction of the ends
    let inset = 0.5 * t * a.to_radians().sin();
    let (x0, x1) = (p.op_l + inset, p.op_r() - inset);
    let (y_end, y_mid) = (p.axis + sag / 2.0, p.axis - sag / 2.0);
    let k = vec![knot(x0, y_end, t).dir(-a), knot(p.mid(), y_mid, t).dir(0.0), knot(x1, y_end, t).dir(a)];
    g.stroke(&if frown { flip(&k, p.axis) } else { k });
}

pub fn register(reg: &mut Registry) {
    reg.module("technical");
    let u = Opt::UPRIGHT;
    // delimiters
    reg.ch('⌈', |g: &mut Draw| ceiling(g, true, false));
    reg.ch('⌉', |g: &mut Draw| ceiling(g, true, true));
    reg.ch('⌊', |g: &mut Draw| ceiling(g, false, false));
    reg.ch('⌋', |g: &mut Draw| ceiling(g, false, true));
    reg.ch('⌜', |g: &mut Draw| corner(g, true, false));
    reg.ch('⌝', |g: &mut Draw| corner(g, true, true));
    reg.ch('⌞', |g: &mut Draw| corner(g, false, false));
    reg.ch('⌟', |g: &mut Draw| corner(g, false, true));
    reg.ch('⟨', |g: &mut Draw| angle_bracket(g, false));
    reg.ch('⟩', |g: &mut Draw| angle_bracket(g, true));
    reg.ch('⟪', |g: &mut Draw| double_angle(g, false));
    reg.ch('⟫', |g: &mut Draw| double_angle(g, true));
    reg.ch('⟦', |g: &mut Draw| white_bracket(g, false));
    reg.ch('⟧', |g: &mut Draw| white_bracket(g, true));
    reg.ch('⦃', |g: &mut Draw| white_brace(g, false));
    reg.ch('⦄', |g: &mut Draw| white_brace(g, true));
    reg.ch('⟮', |g: &mut Draw| flat_paren(g, false));
    reg.ch('⟯', |g: &mut Draw| flat_paren(g, true));
    reg.ch('⦇', |g: &mut Draw| image_bracket(g, false));
    reg.ch('⦈', |g: &mut Draw| image_bracket(g, true));
    reg.ch('⟬', |g: &mut Draw| white_shell(g, false));
    reg.ch('⟭', |g: &mut Draw| white_shell(g, true));
    // bracket pieces
    for (c, part, right) in
        [('⎛', 1, false), ('⎜', 0, false), ('⎝', -1, false), ('⎞', 1, true), ('⎟', 0, true), ('⎠', -1, true)]
    {
        reg.ch_with(c, u, move |g: &mut Draw| paren_piece(g, part, right));
    }
    for (c, part, right) in
        [('⎡', 1, false), ('⎢', 0, false), ('⎣', -1, false), ('⎤', 1, true), ('⎥', 0, true), ('⎦', -1, true)]
    {
        reg.ch_with(c, u, move |g: &mut Draw| bracket_piece(g, part, right));
    }
    for (c, part, right) in [
        ('⎧', 1, false),
        ('⎨', 2, false),
        ('⎩', -1, false),
        ('⎪', 0, false),
        ('⎫', 1, true),
        ('⎬', 2, true),
        ('⎭', -1, true),
    ] {
        reg.ch_with(c, u, move |g: &mut Draw| brace_piece(g, part, right));
    }
    for (c, part) in [('⌠', 1), ('⎮', 0), ('⌡', -1)] {
        reg.ch_with(c, u, move |g: &mut Draw| integral_piece(g, part));
    }
    reg.ch_with('⎰', u, |g: &mut Draw| brace_section(g, false));
    reg.ch_with('⎱', u, |g: &mut Draw| brace_section(g, true));
    reg.ch_with('⎴', u, |g: &mut Draw| horizontal_bracket(g, true));
    reg.ch_with('⎵', u, |g: &mut Draw| horizontal_bracket(g, false));
    reg.ch_with('⏞', u, |g: &mut Draw| horizontal_brace(g, true));
    reg.ch_with('⏟', u, |g: &mut Draw| horizontal_brace(g, false));
    reg.ch_with('⏜', u, |g: &mut Draw| horizontal_paren(g, true));
    reg.ch_with('⏝', u, |g: &mut Draw| horizontal_paren(g, false));
    reg.ch_with('⏠', u, |g: &mut Draw| horizontal_shell(g, true));
    reg.ch_with('⏡', u, |g: &mut Draw| horizontal_shell(g, false));
    // keyboard and interface signs
    reg.ch_with('⌘', u, place_of_interest);
    reg.ch_with('⌃', u, up_arrowhead);
    reg.ch_with('⌄', u, down_arrowhead);
    reg.ch_with('⌅', u, |g: &mut Draw| barred_arrowhead(g, 1));
    reg.ch_with('⌆', u, |g: &mut Draw| barred_arrowhead(g, 2));
    reg.ch_with('⌤', u, enter_key);
    reg.ch_with('⌫', u, |g: &mut Draw| erase(g, false));
    reg.ch_with('⌦', u, |g: &mut Draw| erase(g, true));
    reg.ch_with('⌧', u, x_in_box);
    reg.ch_with('⎋', u, escape);
    reg.ch_with('⌂', u, house);
    reg.ch_with('⌨', u, keyboard);
    reg.ch_with('⌐', u, reversed_not);
    reg.ch_with('⏏', u, eject);
    reg.ch_with('⎈', u, helm);
    reg.ch_with('⎊', u, circled_triangle_down);
    reg.ch_with('⌀', u, diameter);
    // frown and smile
    reg.ch('⌢', |g: &mut Draw| arc_sign(g, true));
    reg.ch('⌣', |g: &mut Draw| arc_sign(g, false));
}
