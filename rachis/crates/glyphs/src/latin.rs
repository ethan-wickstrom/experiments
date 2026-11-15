//! Accented Latin: the combining marks, the spacing accents, the anchors of the base letters, the precomposed
//! letters, and the letters of Latin-1 and Latin Extended-A that are drawn in full.
//!
//! Four layers. The marks are drawn once, each as a function of a centre and a zone, and registered twice: as the
//! combining character, centred in its own cell over a lowercase letter (a terminal draws a combining mark in the
//! cell of its base), and as an unencoded `.case` form, flatter and closer, over a capital or an ascender. Where
//! a mark attaches is measured on the base letter as it is drawn (`anchors`), never copied from the base's
//! program, so the marks follow when a base letter changes. The precomposed letters are one table from the
//! character to a base and its marks, and one loop that places them as components by anchor. The special letters
//! (æ œ ß ð þ ŋ ...) are drawn in full or built from a measured base letter and a stroke.

#![allow(non_snake_case)]

use std::sync::OnceLock;

use rachis_kernel::geom::flatten;
use rachis_kernel::{Draw, Glyph, Knot, Opt, Params, Registry, Spec, V, knot, name_of, name_of_code, pt};

use crate::lower;
use crate::lower::{bar, corner_r, crowd, dot_y as i_dot_y, nudge};
use crate::parts::{Arch, arch, bowl, cut, dbowl, elbow, hbar, ring, turn, vee, vstem};
use crate::text::{Ask, around, beside, cap_ink, ink};

// ---------------------------------------------------------------------------------------------------------------
// Measurements of this group, each derived from the parameters.

/// The stroke of a mark: a little under the hairline, so that it reads at 13 px without competing with the
/// letter.
pub fn mark_t(p: &Params) -> f64 {
    0.86 * p.hair
}

/// The stroke of the circumflex and the caron: lighter than `mark_t`, because two diagonals meet in a small
/// space and the notch must stay open in the Bold.
fn chevron_t(p: &Params) -> f64 {
    0.74 * p.hair
}

/// The height of the zone of a tall mark (acute, circumflex) above a lowercase letter. It grows a little with the
/// stroke, so that a Bold chevron keeps its notch.
fn mark_h(p: &Params) -> f64 {
    118.0 + 0.5 * p.hair
}

/// The white between the x-height and the bottom of a mark above a lowercase letter.
fn mark_gap(p: &Params) -> f64 {
    0.9 * p.hair + 12.0
}

/// The same two for a mark above a capital: flatter and closer, so that the line holds accented capitals.
fn case_h(p: &Params) -> f64 {
    0.78 * mark_h(p)
}

fn case_gap(p: &Params) -> f64 {
    0.6 * p.cap_hair + 12.0
}

/// The white between the baseline and the top of a mark that hangs detached below it (the comma below).
fn below_gap(p: &Params) -> f64 {
    0.2 * p.hair + 40.0
}

/// Radius of the dot of the small comma (comma below, turned comma above, the apostrophe of ŉ).
fn comma_r(p: &Params) -> f64 {
    0.45 * p.punct + 22.0
}

/// From the centre of a small comma's dot to the end of its tail.
fn comma_drop(p: &Params) -> f64 {
    0.8 * comma_r(p) + 66.0
}

/// The breadth of the ogonek where it leaves the letter.
fn ogonek_w(p: &Params) -> f64 {
    1.04 * mark_t(p)
}

/// The squareness of a capital's bowls, as in `upper`.
fn sqc(p: &Params) -> f64 {
    p.sq + 0.02
}

/// Where a mark is drawn: the bottom of its zone `y0`, the zone's height `h`, how far a round mark may dip below
/// `y0` (`dip`), the height of the centre of a dot (`dot`), and `f`, 1 over a lowercase letter and less over a
/// capital, where the marks are flatter.
#[derive(Clone, Copy, Debug)]
struct Zone {
    y0: f64,
    h: f64,
    dip: f64,
    dot: f64,
    f: f64,
}

/// The height of the centre of the dot of i, measured on i, so that every dot above a lowercase letter agrees
/// with it.
fn i_dot(g: &Draw) -> f64 {
    let p = g.p;
    match g.glyph_of_char('i').and_then(|i| i.bounds()) {
        Some((_, _, _, y1)) => y1 - p.dot,
        None => i_dot_y(p),
    }
}

fn lower_zone(g: &Draw) -> Zone {
    let p = g.p;
    Zone { y0: p.xh + mark_gap(p), h: mark_h(p), dip: 0.25 * mark_gap(p), dot: i_dot(g), f: 1.0 }
}

fn case_zone(g: &Draw) -> Zone {
    let p = g.p;
    let dot = p.cap + 0.86 * (i_dot(g) - p.xh);
    Zone { y0: p.cap + case_gap(p), h: case_h(p), dip: 0.5 * case_gap(p), dot, f: 0.8 }
}

// ---------------------------------------------------------------------------------------------------------------
// Measuring a drawn glyph

/// Every glyph program, for resolving the components of a glyph that the registry hands the anchor function
/// unresolved.
fn library() -> &'static Registry {
    static LIBRARY: OnceLock<Registry> = OnceLock::new();
    LIBRARY.get_or_init(crate::registry)
}

/// `g` with its components drawn into it as contours, by the master `p`.
fn resolved(mut g: Glyph, p: &Params) -> Glyph {
    for (name, offset) in std::mem::take(&mut g.components) {
        if let Some(part) = library().flat(&name, p) {
            g.contours.extend(part.contours.into_iter().map(|c| c.mapped(|z| z + offset)));
        }
    }
    g
}

/// The stretches of ink of `g` on the horizontal line at height `y`, from the left, as (left edge, right edge),
/// overlapping strokes merged.
fn spans(g: &Glyph, y: f64) -> Vec<(f64, f64)> {
    crossings(g, |z| (z.y, z.x), y)
}

/// The stretches of ink of `g` on the vertical line at `x`, from the bottom, as (bottom edge, top edge).
fn vspans(g: &Glyph, x: f64) -> Vec<(f64, f64)> {
    crossings(g, |z| (z.x, z.y), x)
}

/// The stretches where the outline of `g` covers the line `across = v`, by the non-zero rule; `axis` maps a
/// point to (across, along).
fn crossings(g: &Glyph, axis: impl Fn(V) -> (f64, f64), v: f64) -> Vec<(f64, f64)> {
    let mut hits: Vec<(f64, i32)> = Vec::new();
    for c in &g.contours {
        let Some(first) = c.segs.first() else { continue };
        let mut a = axis(first.start());
        for s in &c.segs {
            for z in flatten(s, 0.05) {
                let b = axis(z);
                if (a.0 <= v) != (b.0 <= v) {
                    let along = a.1 + (b.1 - a.1) * (v - a.0) / (b.0 - a.0);
                    hits.push((along, if b.0 > a.0 { 1 } else { -1 }));
                }
                a = b;
            }
        }
    }
    hits.sort_by(|a, b| a.0.total_cmp(&b.0));
    let mut out: Vec<(f64, f64)> = Vec::new();
    let (mut winding, mut start) = (0, 0.0);
    for (along, turn) in hits {
        if winding == 0 {
            start = along;
        }
        winding += turn;
        if winding == 0 {
            match out.last_mut() {
                Some(last) if start - last.1 < 0.5 => last.1 = along,
                _ => out.push((start, along)),
            }
        }
    }
    out
}

/// The middle of all the ink of `g` at height `y`, from its leftmost to its rightmost edge.
fn ink_mid(g: &Glyph, y: f64) -> Option<f64> {
    let s = spans(g, y);
    Some((s.first()?.0 + s.last()?.1) / 2.0)
}

/// The glyph of `c` as this master draws it upright, components resolved: for measuring a base letter.
fn upright_of(g: &Draw, c: char) -> Option<Glyph> {
    g.glyph_as(&name_of(c), &Params { slant: 0.0, ..g.p.clone() })
}

/// The leftmost (`which` 0) or rightmost (`which` 1) stretch of ink of `g` at height `y`, or a stand-in when it
/// has none there.
fn stretch(g: &Glyph, y: f64, which: usize, fallback: (f64, f64)) -> (f64, f64) {
    let s = spans(g, y);
    let pick = if which == 0 { s.first() } else { s.last() };
    pick.copied().unwrap_or(fallback)
}

// ---------------------------------------------------------------------------------------------------------------
// The anchors of the base letters

/// The base letters that carry anchors.
const BASES: &str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZıȷæøÆØ";

/// Where marks attach to a base letter: `top` (above), `bottom` (a detached mark below), `cedilla` and `ogonek`
/// (attached below), measured on the letter as drawn, in the upright coordinates of its own cell. A mark above
/// an x-height letter lands on the x-height; above a capital, on the cap height; above an ascender, on its top
/// (and takes the capital form of the mark).
pub fn anchors(spec: &Spec, p: &Params, upright: &dyn Fn() -> Glyph) -> Vec<(&'static str, f64, f64)> {
    let mut found = letter_anchors(spec, p, upright);
    // the rules and the stroke that lie over a whole character (U+0305, U+0332, U+0338) sit at heights of
    // their own: they attach to the middle of the cell of any letter or figure, on the baseline
    if RULED.contains(&spec.module) && !spec.opt.mark && !spec.unicodes.is_empty() {
        found.push(("rule", p.width / 2.0, 0.0));
    }
    found
}

/// The modules whose glyphs take a rule or a stroke over them.
const RULED: [&str; 6] = ["lower", "upper", "digits", "greek", "latin", "letterlike"];

/// The anchors of a letter that takes accents.
fn letter_anchors(spec: &Spec, p: &Params, upright: &dyn Fn() -> Glyph) -> Vec<(&'static str, f64, f64)> {
    let Some(c) = spec.unicodes.first().and_then(|&u| char::from_u32(u)).filter(|c| BASES.contains(*c)) else {
        return Vec::new();
    };
    let g = resolved(upright(), &Params { slant: 0.0, ..p.clone() });
    let Some((x0, y0, x1, y1)) = g.bounds() else {
        return Vec::new();
    };
    let cap = c.is_uppercase();
    let (stem, hair, height) = if cap { (p.cap_stem, p.cap_hair, p.cap) } else { (p.stem, p.hair, p.xh) };
    let tall = !cap && y1 > p.xh + 0.5 * (p.asc - p.xh);
    let mid = (x0 + x1) / 2.0;

    // above: the middle of the ink just under the top, or of the stem of a narrow or tall letter
    let (top_x, top_y) = if tall {
        (ink_mid(&g, (p.xh + y1) / 2.0).unwrap_or(mid), y1)
    } else if "ıȷij".contains(c) {
        (ink_mid(&g, 0.5 * p.xh).unwrap_or(mid), p.xh)
    } else {
        (ink_mid(&g, height - 0.5 * hair).unwrap_or(mid), height)
    };
    // optical corrections, where the middle of the ink is not where the eye puts the letter's middle
    let top_x = top_x
        + match c {
            'r' => -0.30 * stem,
            'a' => -0.10 * stem,
            'h' => 0.5 * (mid - top_x),
            'L' => 0.35 * stem,
            'P' | 'F' => -0.12 * stem,
            'J' => 0.10 * stem,
            _ => 0.0,
        };

    // below: the middle of the ink just over the baseline
    let low = ink_mid(&g, 0.5 * hair).unwrap_or(mid);
    let bottom_y = if y0 < -0.5 * (-p.desc) { y0 } else { 0.0 };
    let cedilla_x = match c {
        't' | 'T' => 0.5 * (low + ink_mid(&g, 0.5 * height).unwrap_or(low)),
        _ => low,
    };

    // the ogonek: under the foot of a right stem, or under the right of a round or barred bottom
    let right_foot = stretch(&g, 1.5 * hair, 1, (x1 - stem, x1)).1;
    let ogonek_x = match c {
        'a' | 'u' | 'A' => right_foot - 0.5 * ogonek_w(p) - 0.04 * stem,
        'i' | 'ı' | 'I' => ink_mid(&g, 0.5 * height).unwrap_or(mid) + 0.30 * stem,
        'e' => x0 + 0.60 * (x1 - x0),
        'E' => x1 - 0.5 * ogonek_w(p) - 0.9 * stem,
        _ => mid + 0.18 * (x1 - x0),
    };

    vec![("top", top_x, top_y), ("bottom", low, bottom_y), ("cedilla", cedilla_x, 0.0), ("ogonek", ogonek_x, 0.0)]
}

// ---------------------------------------------------------------------------------------------------------------
// The shapes of the marks. Each draws itself centred on `cx` in a zone.

type Shape = fn(&mut Draw, f64, Zone);

/// One stroke of an acute (`side` 1) or a grave (-1): steep, heavier at the head than at the foot, its ends cut
/// square to the stroke, its ink from the zone's floor to `scale` of its height. The foot is nearer the letter's
/// middle than the head.
fn slash(g: &mut Draw, cx: f64, z: Zone, side: f64, scale: f64, weight: f64) {
    let p = g.p;
    let t = mark_t(p) * weight;
    let angle = (58.0 - 15.0 * (1.0 - z.f)).to_radians();
    let (wf, wh) = (0.82 * t, 1.12 * t);
    let yf = z.y0 + 0.5 * wf * angle.cos();
    let yh = z.y0 + scale * z.h - 0.5 * wh * angle.cos();
    let run = (yh - yf) / angle.tan();
    let x = cx + side * 0.14 * run;
    g.stroke(&[knot(x - side * run / 2.0, yf, wf).line(), knot(x + side * run / 2.0, yh, wh)]);
}

/// The acute and the grave are the tallest marks: a single stroke needs the length to read as a direction.
const SLASH_H: f64 = 1.16;

fn acute(g: &mut Draw, cx: f64, z: Zone) {
    slash(g, cx, z, 1.0, SLASH_H, 1.0);
}

fn grave(g: &mut Draw, cx: f64, z: Zone) {
    slash(g, cx, z, -1.0, SLASH_H, 1.0);
}

/// Two acutes, shorter and lighter, far enough apart that they never close into one shape or read as two dots.
fn double_acute(g: &mut Draw, cx: f64, z: Zone) {
    let p = g.p;
    let t = 0.9 * mark_t(p);
    let step = t / (58.0f64).to_radians().sin() + 0.62 * p.hair + 34.0;
    for x in [cx - step / 2.0 + 0.04 * step, cx + step / 2.0 + 0.04 * step] {
        slash(g, x, z, 1.0, 1.04, 0.9);
    }
}

/// Half the width of the circumflex and the caron. It grows with the stroke, so that the notch stays open.
fn chevron_half(p: &Params) -> f64 {
    104.0 + 0.8 * chevron_t(p)
}

/// The circumflex (`up`) and the caron: two straight strokes that meet in a narrow flat, their feet cut level.
/// The caron's point is sharper than the circumflex's, so that the two are told apart by more than direction.
fn chevron(g: &mut Draw, cx: f64, z: Zone, up: bool) {
    let p = g.p;
    let t = chevron_t(p);
    let half = chevron_half(p);
    let h = 0.96 * z.h;
    if up {
        g.poly(&vee(cx - half, cx + half, z.y0, z.y0 + h, t, 0.42 * t));
    } else {
        g.poly(&vee(cx - half, cx + half, z.y0 + h, z.y0, t, 0.22 * t));
    }
}

fn circumflex(g: &mut Draw, cx: f64, z: Zone) {
    chevron(g, cx, z, true);
}

fn caron(g: &mut Draw, cx: f64, z: Zone) {
    chevron(g, cx, z, false);
}

/// A full double curve, its swing large enough that it never reads as a macron at 13 px.
fn tilde(g: &mut Draw, cx: f64, z: Zone) {
    let p = g.p;
    let t = 0.9 * mark_t(p);
    let a = 124.0 + 0.5 * t; // half its length
    let amp = 0.17 * z.h + 0.12 * t; // how far the centre line swings either side of its middle
    let cy = z.y0 + 0.06 * z.h + amp + t / 2.0;
    g.stroke(&[
        knot(cx - a, cy - 0.30 * amp, 0.94 * t).dir(48.0),
        knot(cx - 0.42 * a, cy + amp, t).dir(0.0),
        knot(cx + 0.42 * a, cy - amp, t).dir(0.0),
        knot(cx + a, cy + 0.30 * amp, 0.94 * t).dir(48.0),
    ]);
}

fn macron(g: &mut Draw, cx: f64, z: Zone) {
    let p = g.p;
    let t = 0.92 * mark_t(p);
    let a = 118.0 + 0.5 * t;
    g.stroke(&hbar(cx - a, cx + a, z.y0 + 0.30 * z.h + t / 2.0, t));
}

/// A round cup, half an ellipse, its horns cut level: round where the caron is pointed.
fn breve(g: &mut Draw, cx: f64, z: Zone) {
    let p = g.p;
    let t = mark_t(p);
    let tip = 0.86 * t;
    let a = 110.0 + 0.5 * t - tip / 2.0; // from the middle to the centre line of a horn
    let top = z.y0 + 0.86 * z.h;
    let bot = z.y0 - 0.3 * z.dip;
    g.stroke(&[
        knot(cx - a, top, tip).pen(0.0).dir(-90.0),
        knot(cx, bot + t / 2.0, t).dir(0.0),
        knot(cx + a, top, tip).pen(0.0).dir(90.0),
    ]);
}

fn dot_above(g: &mut Draw, cx: f64, z: Zone) {
    let p = g.p;
    g.dot(cx, z.dot, p.dot);
}

/// Two dots a little smaller than the dot of i, a dot and a half apart.
fn diaeresis(g: &mut Draw, cx: f64, z: Zone) {
    let p = g.p;
    let r = 0.86 * p.dot;
    let d = r + 0.5 * (0.9 * r + 50.0); // from the middle to the centre of each dot
    g.dot(cx - d, z.dot, r);
    g.dot(cx + d, z.dot, r);
}

/// The stroke of the ring at its sides; it gains weight more slowly than the hairline, so that the counter stays
/// open in the Bold. The top and bottom are a little lighter.
fn ring_t(p: &Params) -> f64 {
    0.45 * p.hair + 22.0
}

/// The ring's outer half-width.
fn ring_rx(p: &Params) -> f64 {
    60.0 + 0.9 * ring_t(p)
}

/// A closed ring that comes nearer the letter than a flat mark, as round shapes do. Over a capital it is a little
/// flatter.
fn ring_above(g: &mut Draw, cx: f64, z: Zone) {
    let p = g.p;
    let t = ring_t(p);
    let rx = ring_rx(p);
    let ry = rx * (0.94 - 0.4 * (1.0 - z.f));
    let bot = z.y0 - 1.4 * z.dip;
    g.stroke_closed(&ring(cx - rx, bot, cx + rx, bot + 2.0 * ry, t, 0.84 * t, 0.62));
}

/// A small comma: a dot centred on (cx, cy) and a tail that leaves its right side and falls to the left, as the
/// comma of the punctuation does; `turned` turns it half a circle (the tail rises to the right).
fn comma_mark(g: &mut Draw, cx: f64, cy: f64, turned: bool) {
    let p = g.p;
    let r = comma_r(p);
    let w0 = 0.92 * r;
    let mut tail = vec![
        knot(cx + 0.97 * r - w0 / 2.0, cy, w0).pen(0.0).dir(-90.0),
        crate::parts::cut_pen(cx - 0.40 * r, cy - comma_drop(p), 0.56 * r, -128.0, 0.0),
    ];
    if turned {
        tail = turn(&tail, cx, cy);
    }
    g.dot(cx, cy, r);
    g.stroke(&tail);
}

/// The turned comma above, the form of the cedilla over g.
fn turned_comma(g: &mut Draw, cx: f64, z: Zone) {
    let p = g.p;
    comma_mark(g, cx, z.y0 - 0.3 * z.dip + comma_r(p), true);
}

/// The comma below: detached, its dot's top `below_gap` under the baseline.
fn comma_below(g: &mut Draw, cx: f64) {
    let p = g.p;
    comma_mark(g, cx, -below_gap(p) - comma_r(p), false);
}

/// The cedilla: a short stem that grows out of the letter's bottom stroke and a hook that swings right and back
/// left under it. It is attached, where the comma below is not.
fn cedilla(g: &mut Draw, cx: f64) {
    let p = g.p;
    let t = 0.92 * mark_t(p);
    let hc = 0.84 * t;
    let rx = 66.0 + 0.25 * t; // half the width of the hook, on its centre line
    let ry = 50.0 + 0.1 * t;
    let yt = -(38.0 + 0.25 * p.hair); // the centre line of the hook's top
    let yb = yt - 2.0 * ry;
    g.stroke(&vstem(cx, yt - hc / 2.0 + 2.0, 0.5 * p.hair, t));
    g.stroke(&[
        knot(cx - t / 2.0, yt, hc).dir(0.0),
        knot(cx + rx, yt - ry, 1.06 * t).dir(-90.0),
        cut(cx - 1.15 * rx, yb + 0.16 * ry, hc, 168.0),
    ]);
}

/// The ogonek: it leaves the letter downwards, swings left, and ends in a tail that rises to the right.
fn ogonek(g: &mut Draw, cx: f64) {
    let p = g.p;
    let t = mark_t(p);
    let w = ogonek_w(p);
    let rx = 62.0 + 0.4 * t;
    let yb = -(160.0 + 0.3 * t); // the centre line of the bottom of the swing
    g.stroke(&[
        knot(cx, 0.45 * p.hair, w).pen(0.0).dir(-100.0),
        knot(cx - rx, 0.55 * yb, 1.02 * t).dir(-90.0),
        knot(cx - 0.05 * rx, yb, 0.86 * t).dir(0.0),
        cut(cx + 1.05 * rx, yb + 0.16 * (-yb), 0.5 * t, 28.0),
    ]);
}

/// The thickness of the lines that join from cell to cell (the overline): that of the low line.
fn rule_t(g: &Draw) -> f64 {
    match g.glyph_of_char('_').and_then(|u| u.bounds()) {
        Some((_, y0, _, y1)) => y1 - y0,
        None => g.p.op,
    }
}

/// The marks above, by the combining character.
const ABOVE: [(char, Shape); 12] = [
    ('\u{300}', grave),
    ('\u{301}', acute),
    ('\u{302}', circumflex),
    ('\u{303}', tilde),
    ('\u{304}', macron),
    ('\u{306}', breve),
    ('\u{307}', dot_above),
    ('\u{308}', diaeresis),
    ('\u{30A}', ring_above),
    ('\u{30B}', double_acute),
    ('\u{30C}', caron),
    ('\u{312}', turned_comma),
];

/// The glyph name of the form of a mark above that sits over a capital or an ascender.
fn case_name(mark: char) -> String {
    name_of(mark) + ".case"
}

/// The ring and the acute of ǻ in one mark: the ring smaller and lower, the acute short, close above it.
fn ring_acute(g: &mut Draw, cx: f64, z: Zone) {
    let p = g.p;
    let rx = 0.8 * ring_rx(p);
    let t = 0.84 * ring_t(p);
    let ry = rx * (0.84 - 0.6 * (1.0 - z.f));
    let bot = z.y0 - 1.6 * z.dip;
    g.stroke_closed(&ring(cx - rx, bot, cx + rx, bot + 2.0 * ry, t, 0.84 * t, 0.62));
    let above = Zone { y0: bot + 2.0 * ry + 0.25 * p.hair + 10.0, h: 0.62 * z.h, ..z };
    slash(g, cx + 0.15 * rx, above, 1.0, 1.0, 0.9);
}

// ---------------------------------------------------------------------------------------------------------------
// Placing marks on a base

/// Which anchor of the base a mark attaches to.
fn attachment(mark: char) -> &'static str {
    match mark {
        '\u{326}' => "bottom",
        '\u{327}' => "cedilla",
        '\u{328}' => "ogonek",
        _ => "top",
    }
}

/// Place the glyph called `mark_name` as a component so that its anchor `_<anchor>` lands on the base's
/// `anchor`. Both glyphs are measured as this master draws them, slanted in an italic, so the offset is exact.
fn place(g: &mut Draw, base: &Glyph, mark_name: &str, anchor: &str, dx: f64) {
    let Some(mark) = g.glyph_of(mark_name) else {
        g.glyph.errors.push(format!("no mark {mark_name:?}"));
        return;
    };
    let (Some(&to), Some(&from)) = (base.anchors.get(anchor), mark.anchors.get(&format!("_{anchor}"))) else {
        g.glyph.errors.push(format!("{} has no anchor {anchor:?} for {mark_name:?}", base.name));
        return;
    };
    g.glyph.components.push((mark_name.into(), to - from + pt(dx, 0.0)));
}

/// The name of the form of `mark` that goes on `base`: the capital form over a capital or an ascender.
fn mark_for(p: &Params, base: &Glyph, mark: char) -> String {
    let high = base.anchors.get("top").is_some_and(|z| z.y > p.xh + 1.0);
    if attachment(mark) == "top" && high { case_name(mark) } else { name_of(mark) }
}

/// A precomposed letter: the base as a component, with its advance, and each mark placed on it by anchor.
fn compose(g: &mut Draw, base: char, marks: &str) {
    let Some(b) = g.glyph_of_char(base) else {
        g.glyph.errors.push(format!("no base {base:?}"));
        return;
    };
    g.glyph.advance = b.advance;
    g.use_char(base, 0.0, 0.0);
    for m in marks.chars() {
        let name = mark_for(g.p, &b, m);
        place(g, &b, &name, attachment(m), 0.0);
    }
}

/// The precomposed letters: the character, its base and its marks. Accented i and j stand on the dotless forms;
/// the letters whose "cedilla" is a comma (Latvian, Romanian) take the comma below, and g takes the turned comma
/// above.
const COMPOSED: &[(char, char, &str)] = &[
    ('À', 'A', "\u{300}"),
    ('Á', 'A', "\u{301}"),
    ('Â', 'A', "\u{302}"),
    ('Ã', 'A', "\u{303}"),
    ('Ä', 'A', "\u{308}"),
    ('Å', 'A', "\u{30A}"),
    ('Ç', 'C', "\u{327}"),
    ('È', 'E', "\u{300}"),
    ('É', 'E', "\u{301}"),
    ('Ê', 'E', "\u{302}"),
    ('Ë', 'E', "\u{308}"),
    ('Ì', 'I', "\u{300}"),
    ('Í', 'I', "\u{301}"),
    ('Î', 'I', "\u{302}"),
    ('Ï', 'I', "\u{308}"),
    ('Ñ', 'N', "\u{303}"),
    ('Ò', 'O', "\u{300}"),
    ('Ó', 'O', "\u{301}"),
    ('Ô', 'O', "\u{302}"),
    ('Õ', 'O', "\u{303}"),
    ('Ö', 'O', "\u{308}"),
    ('Ù', 'U', "\u{300}"),
    ('Ú', 'U', "\u{301}"),
    ('Û', 'U', "\u{302}"),
    ('Ü', 'U', "\u{308}"),
    ('Ý', 'Y', "\u{301}"),
    ('à', 'a', "\u{300}"),
    ('á', 'a', "\u{301}"),
    ('â', 'a', "\u{302}"),
    ('ã', 'a', "\u{303}"),
    ('ä', 'a', "\u{308}"),
    ('å', 'a', "\u{30A}"),
    ('ç', 'c', "\u{327}"),
    ('è', 'e', "\u{300}"),
    ('é', 'e', "\u{301}"),
    ('ê', 'e', "\u{302}"),
    ('ë', 'e', "\u{308}"),
    ('ì', 'ı', "\u{300}"),
    ('í', 'ı', "\u{301}"),
    ('î', 'ı', "\u{302}"),
    ('ï', 'ı', "\u{308}"),
    ('ñ', 'n', "\u{303}"),
    ('ò', 'o', "\u{300}"),
    ('ó', 'o', "\u{301}"),
    ('ô', 'o', "\u{302}"),
    ('õ', 'o', "\u{303}"),
    ('ö', 'o', "\u{308}"),
    ('ù', 'u', "\u{300}"),
    ('ú', 'u', "\u{301}"),
    ('û', 'u', "\u{302}"),
    ('ü', 'u', "\u{308}"),
    ('ý', 'y', "\u{301}"),
    ('ÿ', 'y', "\u{308}"),
    ('Ā', 'A', "\u{304}"),
    ('ā', 'a', "\u{304}"),
    ('Ă', 'A', "\u{306}"),
    ('ă', 'a', "\u{306}"),
    ('Ą', 'A', "\u{328}"),
    ('ą', 'a', "\u{328}"),
    ('Ć', 'C', "\u{301}"),
    ('ć', 'c', "\u{301}"),
    ('Ĉ', 'C', "\u{302}"),
    ('ĉ', 'c', "\u{302}"),
    ('Ċ', 'C', "\u{307}"),
    ('ċ', 'c', "\u{307}"),
    ('Č', 'C', "\u{30C}"),
    ('č', 'c', "\u{30C}"),
    ('Ď', 'D', "\u{30C}"),
    ('Ē', 'E', "\u{304}"),
    ('ē', 'e', "\u{304}"),
    ('Ĕ', 'E', "\u{306}"),
    ('ĕ', 'e', "\u{306}"),
    ('Ė', 'E', "\u{307}"),
    ('ė', 'e', "\u{307}"),
    ('Ę', 'E', "\u{328}"),
    ('ę', 'e', "\u{328}"),
    ('Ě', 'E', "\u{30C}"),
    ('ě', 'e', "\u{30C}"),
    ('Ĝ', 'G', "\u{302}"),
    ('ĝ', 'g', "\u{302}"),
    ('Ğ', 'G', "\u{306}"),
    ('ğ', 'g', "\u{306}"),
    ('Ġ', 'G', "\u{307}"),
    ('ġ', 'g', "\u{307}"),
    ('Ģ', 'G', "\u{326}"),
    ('ģ', 'g', "\u{312}"),
    ('Ĥ', 'H', "\u{302}"),
    ('ĥ', 'h', "\u{302}"),
    ('Ĩ', 'I', "\u{303}"),
    ('ĩ', 'ı', "\u{303}"),
    ('Ī', 'I', "\u{304}"),
    ('ī', 'ı', "\u{304}"),
    ('Ĭ', 'I', "\u{306}"),
    ('ĭ', 'ı', "\u{306}"),
    ('Į', 'I', "\u{328}"),
    ('į', 'i', "\u{328}"),
    ('İ', 'I', "\u{307}"),
    ('Ĵ', 'J', "\u{302}"),
    ('ĵ', 'ȷ', "\u{302}"),
    ('Ķ', 'K', "\u{326}"),
    ('ķ', 'k', "\u{326}"),
    ('Ĺ', 'L', "\u{301}"),
    ('ĺ', 'l', "\u{301}"),
    ('Ļ', 'L', "\u{326}"),
    ('ļ', 'l', "\u{326}"),
    ('Ń', 'N', "\u{301}"),
    ('ń', 'n', "\u{301}"),
    ('Ņ', 'N', "\u{326}"),
    ('ņ', 'n', "\u{326}"),
    ('Ň', 'N', "\u{30C}"),
    ('ň', 'n', "\u{30C}"),
    ('Ō', 'O', "\u{304}"),
    ('ō', 'o', "\u{304}"),
    ('Ŏ', 'O', "\u{306}"),
    ('ŏ', 'o', "\u{306}"),
    ('Ő', 'O', "\u{30B}"),
    ('ő', 'o', "\u{30B}"),
    ('Ŕ', 'R', "\u{301}"),
    ('ŕ', 'r', "\u{301}"),
    ('Ŗ', 'R', "\u{326}"),
    ('ŗ', 'r', "\u{326}"),
    ('Ř', 'R', "\u{30C}"),
    ('ř', 'r', "\u{30C}"),
    ('Ś', 'S', "\u{301}"),
    ('ś', 's', "\u{301}"),
    ('Ŝ', 'S', "\u{302}"),
    ('ŝ', 's', "\u{302}"),
    ('Ş', 'S', "\u{327}"),
    ('ş', 's', "\u{327}"),
    ('Š', 'S', "\u{30C}"),
    ('š', 's', "\u{30C}"),
    ('Ţ', 'T', "\u{327}"),
    ('ţ', 't', "\u{327}"),
    ('Ť', 'T', "\u{30C}"),
    ('Ũ', 'U', "\u{303}"),
    ('ũ', 'u', "\u{303}"),
    ('Ū', 'U', "\u{304}"),
    ('ū', 'u', "\u{304}"),
    ('Ŭ', 'U', "\u{306}"),
    ('ŭ', 'u', "\u{306}"),
    ('Ů', 'U', "\u{30A}"),
    ('ů', 'u', "\u{30A}"),
    ('Ű', 'U', "\u{30B}"),
    ('ű', 'u', "\u{30B}"),
    ('Ų', 'U', "\u{328}"),
    ('ų', 'u', "\u{328}"),
    ('Ŵ', 'W', "\u{302}"),
    ('ŵ', 'w', "\u{302}"),
    ('Ŷ', 'Y', "\u{302}"),
    ('ŷ', 'y', "\u{302}"),
    ('Ÿ', 'Y', "\u{308}"),
    ('Ź', 'Z', "\u{301}"),
    ('ź', 'z', "\u{301}"),
    ('Ż', 'Z', "\u{307}"),
    ('ż', 'z', "\u{307}"),
    ('Ž', 'Z', "\u{30C}"),
    ('ž', 'z', "\u{30C}"),
    ('Ǽ', 'Æ', "\u{301}"),
    ('ǽ', 'æ', "\u{301}"),
    ('Ǿ', 'Ø', "\u{301}"),
    ('ǿ', 'ø', "\u{301}"),
    ('Ș', 'S', "\u{326}"),
    ('ș', 's', "\u{326}"),
    ('Ț', 'T', "\u{326}"),
    ('ț', 't', "\u{326}"),
    ('Ẁ', 'W', "\u{300}"),
    ('ẁ', 'w', "\u{300}"),
    ('Ẃ', 'W', "\u{301}"),
    ('ẃ', 'w', "\u{301}"),
    ('Ẅ', 'W', "\u{308}"),
    ('ẅ', 'w', "\u{308}"),
    ('Ỳ', 'Y', "\u{300}"),
    ('ỳ', 'y', "\u{300}"),
];

// ---------------------------------------------------------------------------------------------------------------
// The caron beside a stem (ď ľ ť Ľ), the middle dot (ŀ Ŀ), ŉ and the ij digraphs

/// The apostrophe-shaped caron that Czech and Slovak put beside an ascender: a wedge, cut level at both ends,
/// that narrows and leans to the left as it falls. Its left edge at the top is `x`, its top `top`.
fn caron_beside(g: &mut Draw, x: f64, top: f64, h: f64) {
    let p = g.p;
    let (wt, wb) = (caron_w(p), 0.56 * mark_t(p));
    let lean = 0.26 * h;
    g.stroke(&[knot(x + wt / 2.0, top, wt).pen(0.0).line(), knot(x + wt / 2.0 - lean, top - h, wb).pen(0.0)]);
}

/// The width the caron beside a stem takes, with the white that keeps it off the stem.
fn caron_room(p: &Params) -> f64 {
    caron_gap(p) + caron_w(p)
}

/// The breadth of the top of the caron beside a stem: as heavy as a stem, so that it survives 13 px.
fn caron_w(p: &Params) -> f64 {
    0.62 * p.hair + 0.4 * p.stem
}

fn caron_gap(p: &Params) -> f64 {
    0.4 * p.hair + 14.0
}

/// A copy of `p` for drawing a letter narrowed by `by` in a fixed-pitch cell: the cell and the sidebearings
/// shrink, the counters keep their width.
fn narrowed(p: &Params, by: f64) -> Params {
    Params { width: p.width - by, sb: p.sb - by / 2.0, sb_round: p.sb_round - by / 2.0, slant: p.slant, ..p.clone() }
}

/// ď ľ ť Ľ: the base, and the caron beside its stem at the top. In the fixed-pitch family a base whose stem
/// stands at the right (d) is drawn narrower, so that the caron stays in the cell; in the proportional one the
/// cell grows instead.
fn caron_stem(g: &mut Draw, base: char) {
    let p = g.p.clone();
    let room = caron_room(&p);
    let right_stem = base == 'd';
    // the narrowed d: half its round sidebearing, and a cell that puts the caron's right edge just inside
    let up = Params { slant: 0.0, ..p.clone() };
    let local = if p.mono && right_stem {
        Params { width: p.width - (room - p.sb + 6.0), sb_round: 0.5 * p.sb_round, ..up }
    } else {
        up
    };
    let Some(b) = g.glyph_as(&name_of(base), &local) else {
        g.glyph.errors.push(format!("no base {base:?}"));
        return;
    };
    let Some((_, _, _, top)) = b.bounds() else { return };
    let cap = base.is_uppercase();
    let at = if cap { 0.80 * p.cap } else { 0.5 * (p.xh + top) };
    let (_, stem_r) = stretch(&b, at, if right_stem { 1 } else { 0 }, (p.mid(), p.mid()));
    let full = g.glyph_of_char(base).map(|f| f.advance).unwrap_or(p.width);
    if p.mono && right_stem {
        g.draw_as(&name_of(base), &Params { slant: p.slant, ..local }, 0.0, 0.0);
        g.glyph.advance = full;
    } else {
        g.use_char(base, 0.0, 0.0);
        g.glyph.advance = full + if p.mono || !right_stem { 0.0 } else { room };
    }
    let h = if cap { case_h(&p) } else { mark_h(&p) };
    let top = if cap { p.cap } else { top };
    caron_beside(g, stem_r + caron_gap(&p), top, h);
}

/// ŀ and Ŀ: a dot in the white beside the stem, at the height of the middle of the letter.
fn middle_dot(g: &mut Draw, base: char) {
    let p = g.p;
    let Some(b) = upright_of(g, base) else { return };
    let cap = base.is_uppercase();
    let y = if cap { 0.48 * p.cap } else { 0.56 * p.xh };
    let (_, stem_r) = stretch(&b, y, 0, (p.mid(), p.mid()));
    let r = 0.88 * p.dot;
    let gap = 0.5 * p.hair + 34.0;
    g.same_as_char(base);
    g.glyph.anchors.clear();
    g.dot(stem_r + gap + r, y, r);
}

/// ŉ: an apostrophe before n. The fixed-pitch family narrows the n by the apostrophe's room.
fn n_apostrophe(g: &mut Draw) {
    let p = g.p.clone();
    let r = comma_r(&p);
    // the apostrophe hangs above the x-height, so it may stand over the n's stem
    let room = r + 0.3 * p.sb + 6.0;
    let cy = p.asc - r;
    if p.mono {
        g.draw_as("n", &narrowed(&p, room), room, 0.0);
        comma_mark(g, 0.3 * p.sb + r, cy, false);
    } else {
        let adv = g.glyph_of_char('n').map(|n| n.advance).unwrap_or(p.width);
        g.use_char('n', room, 0.0);
        g.glyph.advance = adv + room;
        comma_mark(g, p.sb + r, cy, false);
    }
}

/// ĳ: i and j. The fixed-pitch family draws each in half the cell, narrowed; the proportional one sets them side
/// by side.
fn ij(g: &mut Draw) {
    let p = g.p.clone();
    if p.mono {
        // i drawn in half the cell; j drawn here with a smaller hook, its stem a counter of n to the right of the
        // i's; the pair centred in the cell
        let ip = Params { width: p.width / 2.0, sb: 0.75 * p.sb, sb_round: 0.75 * p.sb_round, ..p.clone() };
        let up = Params { slant: 0.0, ..ip.clone() };
        let Some(i) = g.glyph_as("i", &up) else { return };
        let Some((x0, _, _, top)) = i.bounds() else { return };
        let (il, ir) = stretch(&i, 0.5 * p.xh, 0, (x0, x0 + p.stem));
        let s = ir - il;
        let xj = ir + 0.62 * p.counter + s / 2.0;
        let shift = 0.5 * (p.width - (xj + s / 2.0 - x0)) - x0;
        let x = xj + shift;
        let r = 0.72 * (-p.desc - p.hair / 2.0);
        g.draw_as("i", &ip, shift, 0.0);
        g.stroke(&elbow(x, p.xh, p.desc, x - 1.3 * r, s, p.hair, p.sq, r));
        g.stroke(&hbar(x - s / 2.0 - 0.9 * lower::slab(&ip), x, p.xh - p.hair / 2.0, p.hair));
        g.dot(x - 2.0, top - p.dot, p.dot);
    } else {
        let i = g.glyph_of_char('i').map(|i| i.advance).unwrap_or(p.width);
        let j = g.glyph_of_char('j').map(|j| j.advance).unwrap_or(p.width);
        let tuck = 0.5 * p.sb; // the j's tail runs under the i
        g.use_char('i', 0.0, 0.0);
        g.use_char('j', i - tuck, 0.0);
        g.glyph.advance = i + j - tuck;
    }
}

/// Ĳ: a plain stem and a narrowed J in the fixed-pitch cell; I and J side by side in the proportional family.
fn IJ(g: &mut Draw) {
    let p = g.p.clone();
    if p.mono {
        let jw = 0.74 * p.width;
        let jp = Params { width: jw, cap_sb: p.cap_sb - 0.3 * (p.width - jw), ..p.clone() };
        let x = p.cap_sb + p.cap_stem / 2.0 - 10.0;
        g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
        g.draw_as("J", &jp, p.width - jw + 6.0, 0.0);
    } else {
        let i = g.glyph_of_char('I').map(|i| i.advance).unwrap_or(p.width);
        let j = g.glyph_of_char('J').map(|j| j.advance).unwrap_or(p.width);
        g.use_char('I', 0.0, 0.0);
        g.use_char('J', i, 0.0);
        g.glyph.advance = i + j;
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Letters made from a measured base and a stroke

/// A base letter as a component with a straight stroke through it, cut square: ø Ø (a slash), Ł ł (a bar that
/// rises to the right).
fn struck(g: &mut Draw, base: char, from: V, to: V, t: f64) {
    let adv = g.glyph_of_char(base).map(|b| b.advance).unwrap_or(g.p.width);
    g.use_char(base, 0.0, 0.0);
    g.glyph.advance = adv;
    g.stroke(&[Knot::at(from, t).line(), Knot::at(to, t)]);
}

fn oslash(g: &mut Draw) {
    let p = g.p;
    let Some((x0, y0, x1, y1)) = upright_of(g, 'o').and_then(|o| o.bounds()) else { return };
    let (dx, dy) = (0.10 * (x1 - x0), 0.10 * p.xh);
    struck(g, 'o', pt(x0 + dx, y0 - dy), pt(x1 - dx, y1 + dy), 0.94 * p.hair);
}

fn Oslash(g: &mut Draw) {
    let p = g.p;
    let Some((x0, y0, x1, y1)) = upright_of(g, 'O').and_then(|o| o.bounds()) else { return };
    let (dx, dy) = (0.06 * (x1 - x0), 0.07 * p.cap);
    struck(g, 'O', pt(x0 + dx, y0 - dy), pt(x1 - dx, y1 + dy), 0.94 * p.cap_hair);
}

/// The bar of Ł and ł: centred a little right of the stem's centre, rising to the right at about 33 degrees.
fn lslash_bar(g: &mut Draw, base: char, y: f64, stem: f64, t: f64) {
    let p = g.p;
    let Some(b) = upright_of(g, base) else { return };
    let (l, r) = stretch(&b, y, 0, (p.mid() - stem / 2.0, p.mid() + stem / 2.0));
    let cx = (l + r) / 2.0 + 0.12 * stem;
    let half = 0.55 * stem + 72.0;
    let rise = 0.64 * half;
    struck(g, base, pt(cx - half, y - rise), pt(cx + half, y + rise), t);
}

fn Lslash(g: &mut Draw) {
    let p = g.p;
    lslash_bar(g, 'L', 0.46 * p.cap, p.cap_stem, 0.92 * p.cap_hair);
}

fn lslash(g: &mut Draw) {
    let p = g.p;
    lslash_bar(g, 'l', 0.5 * (p.xh + 0.2 * (p.asc - p.xh)), p.stem, 0.92 * p.hair);
}

/// A base letter with a level bar across its stem: Ð Đ đ ħ Ħ Ŧ ŧ. `y` is the bar's centre line, `left` and
/// `right` how far it reaches past the stem's edges.
fn barred(g: &mut Draw, base: char, which: usize, y: f64, left: f64, right: f64, t: f64) {
    let p = g.p;
    let Some(b) = upright_of(g, base) else { return };
    let (l, r) = stretch(&b, y, which, (p.mid(), p.mid()));
    let adv = g.glyph_of_char(base).map(|b| b.advance).unwrap_or(p.width);
    g.use_char(base, 0.0, 0.0);
    g.glyph.advance = adv;
    g.stroke(&hbar(l - left, r + right, y, t));
}

fn Eth(g: &mut Draw) {
    let p = g.p;
    let s = p.cap_stem;
    barred(g, 'D', 0, 0.48 * p.cap, 0.55 * p.cap_sb + 4.0, 0.9 * s + 30.0, 0.9 * p.cap_hair);
}

/// The bar of đ and ħ: in the middle of the ascender, clear of the bowl and the arch.
fn ascender_bar(p: &Params) -> f64 {
    p.xh + 0.58 * (p.asc - p.xh)
}

fn dcroat(g: &mut Draw) {
    let p = g.p;
    barred(g, 'd', 1, ascender_bar(p), 1.1 * p.stem + 40.0, 0.36 * p.sb, 0.86 * p.hair);
}

fn hbar_(g: &mut Draw) {
    let p = g.p;
    barred(g, 'h', 0, ascender_bar(p), 0.62 * p.sb, 1.1 * p.stem + 34.0, 0.86 * p.hair);
}

fn Hbar(g: &mut Draw) {
    let p = g.p;
    let Some(b) = upright_of(g, 'H') else { return };
    let Some((x0, _, x1, _)) = b.bounds() else { return };
    // the crossbar, measured in the middle of the letter; the second bar splits the white above it
    let cross = vspans(&b, (x0 + x1) / 2.0).last().map(|s| s.1).unwrap_or(0.55 * p.cap);
    let t = 0.88 * p.cap_hair;
    let y = 0.5 * (cross + p.cap) - 0.04 * (p.cap - cross);
    let reach = 0.42 * p.cap_sb + 6.0;
    let adv = g.glyph_of_char('H').map(|h| h.advance).unwrap_or(p.width);
    g.use_char('H', 0.0, 0.0);
    g.glyph.advance = adv;
    g.stroke(&hbar(x0 - reach, x1 + reach, y, t));
}

fn Tbar(g: &mut Draw) {
    let p = g.p;
    let s = p.cap_stem;
    barred(g, 'T', 0, 0.47 * p.cap, 0.75 * s + 36.0, 0.75 * s + 36.0, 0.9 * p.cap_hair);
}

fn tbar(g: &mut Draw) {
    let p = g.p;
    let s = p.stem;
    barred(g, 't', 0, 0.42 * p.xh, 0.62 * s + 30.0, 0.62 * s + 30.0, 0.86 * p.hair);
}

/// ĸ: k with its stem cut at the x-height. The program of k draws it, told that the ascender is that short.
fn kgreenlandic(g: &mut Draw) {
    let p = g.p.clone();
    let short = Params { asc: p.xh, ..p.clone() };
    let adv = g.glyph_as("k", &short).map(|k| k.advance).unwrap_or(p.width);
    g.draw_as("k", &short, 0.0, 0.0);
    g.glyph.advance = adv;
}

/// ſ: the stem and hook of f, measured on f, without the bar.
fn longs(g: &mut Draw) {
    let p = g.p;
    let Some(f) = upright_of(g, 'f') else { return };
    let Some((_, _, x1, y1)) = f.bounds() else { return };
    let (l, r) = stretch(&f, 0.3 * p.xh, 0, (p.mid() - p.stem / 2.0, p.mid() + p.stem / 2.0));
    let adv = g.glyph_of_char('f').map(|f| f.advance).unwrap_or(p.width);
    g.glyph.advance = adv;
    g.stroke(&elbow((l + r) / 2.0, 0.0, y1, x1, r - l, p.hair, p.sq, corner_r(p)));
}

// ---------------------------------------------------------------------------------------------------------------
// Letters drawn in full

/// ƒ: a long stem with the hook of f at the top and the hook of j at the bottom, and the bar of f.
fn florin(g: &mut Draw) {
    let p = g.p;
    let x = p.mid() + 14.0;
    let dx = nudge(p, &[(p.sb_round, p.desc)], &[(p.width - p.sb_round + 10.0, p.asc)]);
    let x = x + dx;
    let r = corner_r(p);
    let split = 0.38 * p.xh;
    g.stroke(&elbow(x, split - 1.0, p.asc + p.over, p.width - p.sb_round + 10.0 + dx, p.stem, p.hair, p.sq, r));
    g.stroke(&elbow(x, split + 1.0, p.desc - p.over, p.sb_round - 4.0 + dx, p.stem, p.hair, p.sq, r));
    g.stroke(&hbar(p.sb_round + 30.0 + dx, p.width - p.sb_round - 34.0 + dx, p.xh - p.hair / 2.0, p.hair));
}

/// ŋ: n whose right leg runs on below the baseline and turns left into the hook of j.
fn eng(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.xl(), 0.0, p.xh, p.stem));
    let a = arch(p, p.xl(), p.xr(), p.xh + p.over, 0.0, Arch::default());
    let tail = elbow(p.xr(), 0.0, p.desc, p.xr() - 0.62 * (p.xr() - p.xl()), p.stem, p.hair, p.sq, 0.5 * (-p.desc));
    g.stroke(&[a[0], a[1], a[2], tail[1], tail[2], tail[3]]);
}

/// Ŋ: N whose right stem runs on below the baseline and turns left into a hook, the form Sami readers expect.
fn Eng(g: &mut Draw) {
    let p = g.p;
    let Some(n) = upright_of(g, 'N') else { return };
    let (l, r) = stretch(&n, 0.5 * p.cap, 1, (p.cxr() - p.cap_stem / 2.0, p.cxr() + p.cap_stem / 2.0));
    let adv = g.glyph_of_char('N').map(|n| n.advance).unwrap_or(p.width);
    g.use_char('N', 0.0, 0.0);
    g.glyph.advance = adv;
    let x = (l + r) / 2.0;
    let x_end = x - 0.45 * (x - p.cxl());
    let radius = 0.42 * (-p.desc);
    g.stroke(&elbow(x, 0.10 * p.cap, p.desc + 24.0, x_end, r - l, p.cap_hair, sqc(p), radius));
}

/// ß: a stem that arches over into a small upper bowl, which closes at a waist near the x-height, and a larger
/// lower bowl that ends near the stem.
fn germandbls(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let x = p.xl();
    let top = p.asc + p.over;
    let x_up = p.width - p.sb_round - 34.0; // the upper bowl's outer edge
    let x_lo = p.width - p.sb_round + 2.0; // the lower bowl's outer edge
    let waist = 0.94 * p.xh; // the centre line where the two bowls meet
    let xa = x + 0.48 * (x_up - x);
    let bot = -p.over + h / 2.0;
    let shoulder = top - 0.36 * (x_up - xa) - h;
    g.stroke(&[
        knot(x, 0.0, s).pen(0.0).line(),
        knot(x, shoulder, s).pen(0.0).dir(90.0).k(p.sq),
        knot(xa, top - h / 2.0, h).dir(0.0).k(p.sq),
        knot(x_up - 0.92 * s / 2.0, 0.5 * (top + waist) + 0.04 * p.xh, 0.92 * s).dir(-90.0).k(p.sq),
        knot(x + s / 2.0 + 0.42 * (x_up - x - s), waist, 0.92 * h).dir(180.0),
    ]);
    let xw = x + s / 2.0 + 0.36 * (x_lo - x - s);
    g.stroke(&[
        knot(xw, waist, 0.92 * h).dir(0.0).k(p.sq),
        knot(x_lo - s / 2.0, 0.5 * (waist + bot) - 0.03 * p.xh, s).dir(-90.0).k(p.sq),
        knot(x + s / 2.0 + 0.55 * (x_lo - x - s), bot, h).dir(180.0),
        cut(x + s / 2.0 + 30.0, bot + 0.06 * p.xh, h, 160.0),
    ]);
}

/// ẞ: a stem, a flat top that turns into a diagonal falling to the middle of the letter, and a bowl below.
fn Germandbls(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.cap_stem, p.cap_hair);
    let x = p.cxl() + 10.0;
    let x1 = p.width - p.sb_round + 4.0;
    let xr = x1 - 0.10 * (x1 - x); // where the top turns into the diagonal
    let r = 0.16 * p.cap;
    let ym = 0.56 * p.cap; // the diagonal's foot, on the bowl's centre line
    let xm = x + s / 2.0 + 0.40 * (x1 - x - s);
    g.stroke(&[
        knot(x, 0.0, s).pen(0.0).line(),
        knot(x, p.cap - r, s).pen(0.0).dir(90.0).k(sqc(p)),
        knot(x + r, p.cap - h / 2.0, h).pen(90.0).dir(0.0).line(),
        knot(xr, p.cap - h / 2.0, h).pen(90.0),
    ]);
    g.stroke(&bar(xr, p.cap, xm, ym, 0.9 * s, 1.0, 0.0));
    let bot = -p.over + h / 2.0;
    g.stroke(&[
        knot(xm - 0.1 * s, ym - h / 2.0 + 0.3 * h, h).dir(0.0).k(sqc(p)),
        knot(x1 - s / 2.0, 0.5 * (ym + bot) - 0.02 * p.cap, s).dir(-90.0).k(sqc(p)),
        knot(x + s / 2.0 + 0.50 * (x1 - x - s), bot, h).dir(180.0),
        cut(x + s / 2.0 + 24.0, bot + 0.07 * p.cap, h, 162.0),
    ]);
}

/// Þ: a stem with a bowl that hangs between the cap height and the baseline.
fn Thorn(g: &mut Draw) {
    let p = g.p;
    let x = p.cxl() + 16.0;
    let edge = p.width - (p.sb_round - 12.0) - 14.0;
    g.stroke(&vstem(x, 0.0, p.cap, p.cap_stem));
    let (y0, y1) = (0.17 * p.cap, 0.81 * p.cap);
    g.stroke(&dbowl(x, edge, y0, y1, p.cap_stem, p.cap_hair, sqc(p), 0.36 * (edge - x)));
}

/// þ: the bowl of b on a stem that runs from the descender to the ascender.
fn thorn(g: &mut Draw) {
    let p = g.p;
    let dx = nudge(p, &[(p.sb, p.desc)], &[]);
    g.stroke(&vstem(p.xl() + dx, p.desc, p.asc, p.stem));
    let round = bowl(p, p.xl(), p.width - p.sb_round, -p.over, p.xh + p.over, crate::parts::Bowl::default());
    g.stroke(&crate::parts::shifted(&round, dx));
}

/// ð: a bowl whose right side rises past the x-height and sweeps back to the left, crossed by a short bar.
fn eth(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round + 4.0, p.width - p.sb_round - 2.0);
    let top = 0.92 * p.xh + p.over; // the bowl is a little lower than o
    g.stroke_closed(&ring(x0, -p.over, x1, top, s, h, p.sq));
    let xc = x1 - s / 2.0;
    let crest = p.asc + p.over - h / 2.0;
    let w = x1 - x0;
    g.stroke(&[
        knot(xc, 0.40 * top, s).dir(90.0),
        knot(xc - 0.07 * w, top + 0.45 * (crest - top), 0.94 * s).dir(110.0),
        knot(x0 + 0.22 * w, crest, 0.9 * h).dir(165.0),
    ]);
    let yb = top + 0.52 * (crest - top);
    let xb = xc - 0.13 * w;
    let half = 0.5 * s + 66.0;
    g.stroke(&[knot(xb - half, yb - 0.36 * half, 0.86 * h).line(), knot(xb + half, yb + 0.36 * half, 0.86 * h)]);
}

/// æ: the a's bowl and arch and the e's bowl and bar, sharing one stem. In the fixed-pitch cell the strokes thin
/// as those of m do.
fn ae(g: &mut Draw) {
    let p = g.p;
    let s = p.stem * crowd(p, 0.80);
    let h = p.hair * crowd(p, 0.55);
    let x0 = 0.45 * p.sb_round + 4.0; // outer edges of the two bowls
    let x1 = p.width - 0.45 * p.sb_round - 4.0;
    let xs = x0 + 0.48 * (x1 - x0); // the shared stem
    let top = p.xh + p.over - h / 2.0;
    let bot = -p.over + h / 2.0;
    let whites = p.xh + 2.0 * p.over - 3.0 * h;
    let upper = 0.45 * whites;
    let bt = p.xh + p.over - h - upper; // outer top of the a's bowl
    let xc = x0 + 0.52 * (xs - x0);
    let corner = 0.85 * (xs - xc);
    // the a's arch, down the stem to where the e's bottom turns out of it
    let y_turn = 0.42 * p.xh;
    g.stroke(&[
        cut(x0 + 0.30 * s, top - 0.30 * upper, h, 30.0),
        knot(xc, top, h).dir(0.0).k(p.sq),
        knot(xs, top - corner, s).pen(0.0).dir(-90.0).line(),
        knot(xs, y_turn, s).pen(0.0).dir(-90.0).k(p.sq),
        knot(xs + 0.5 * (x1 - xs), bot, h).dir(0.0),
        cut(x1 - 6.0, bot + 0.12 * p.xh, h, 26.0),
    ]);
    // the a's bowl
    let edge = xs - s / 2.0 + 3.0;
    let xb = x0 + 0.50 * (xs - s / 2.0 - x0);
    let (jt, jb) = (0.82 * h, p.join * s);
    let (d_top, d_bot) = (V::unit(168.0), V::unit(52.0));
    let y_in = (bot + h / 2.0) + 0.30 * (bt - h - bot - h / 2.0);
    g.stroke(&[
        Knot::at(pt(edge, bt - 0.10 * h) - d_top * (s / 2.0) + d_top.left() * (jt / 2.0), jt).dir(168.0),
        knot(xb, bt - h / 2.0, h).dir(180.0).k(p.sq),
        knot(x0 + s / 2.0, (bt - p.over) / 2.0, s).dir(-90.0).k(p.sq),
        knot(xb + 4.0, bot, h).dir(0.0),
        Knot::at(pt(edge, y_in) - d_bot.left() * (jb / 2.0), jb).dir(52.0),
    ]);
    // the e's arch, from the stem over to the bar
    let bh = 0.92 * h;
    let mid = 0.50 * p.xh;
    let xe = xs + 0.5 * (x1 - xs);
    let d = V::unit(64.0);
    let j = p.join * s;
    g.stroke(&[
        Knot::at(pt(xs + s / 2.0 - 3.0, p.xh - 0.26 * p.xh) + d.left() * (j / 2.0), j).dir(64.0),
        knot(xe, top, h).dir(0.0).k(p.sq),
        knot(x1 - s / 2.0, mid - bh / 2.0, s).pen(0.0).dir(-90.0),
    ]);
    g.stroke(&hbar(xs, x1 - s / 2.0, mid, bh));
}

/// œ: the o's bowl and the e's bowl, sharing the side between them.
fn oe(g: &mut Draw) {
    let p = g.p;
    let s = p.stem * crowd(p, 0.80);
    let h = p.hair * crowd(p, 0.55);
    let x0 = 0.45 * p.sb_round + 2.0;
    let x1 = p.width - 0.45 * p.sb_round - 4.0;
    let xs = x0 + 0.50 * (x1 - x0); // the centre line of the shared side
    g.stroke_closed(&ring(x0, -p.over, xs + s / 2.0, p.xh + p.over, s, h, p.sq));
    let top = p.xh + p.over - h / 2.0;
    let bot = -p.over + h / 2.0;
    let bh = 0.92 * h;
    let mid = 0.50 * p.xh;
    let xe = xs + 0.5 * (x1 - xs);
    g.stroke(&[
        knot(x1 - s / 2.0, mid - bh / 2.0, s).pen(0.0).dir(90.0).k(p.sq),
        knot(xe, top, h).dir(180.0).k(p.sq),
        knot(xs, p.xh / 2.0, s).dir(-90.0).k(p.sq),
        knot(xe + 6.0, bot, h).dir(0.0),
        cut(x1 - 6.0, bot + 0.12 * p.xh, h, 26.0),
    ]);
    g.stroke(&hbar(xs, x1 - s / 2.0, mid, bh));
}

/// The arms of the E of Æ and Œ, from the stem centred on `xs` to the right edge `x1`.
fn e_arms(g: &mut Draw, xs: f64, x1: f64, h: f64) {
    let p = g.p;
    g.stroke(&hbar(xs, x1, p.cap - h / 2.0, h));
    g.stroke(&hbar(xs, x1 - 0.12 * (x1 - xs), p.cap * 0.52, h));
    g.stroke(&hbar(xs, x1 + 6.0, h / 2.0, h));
}

/// Æ: the left leg and bar of A, and the stem and arms of E.
fn AE(g: &mut Draw) {
    let p = g.p;
    let s = p.cap_stem * crowd(p, 0.70);
    let h = p.cap_hair * crowd(p, 0.55);
    let x0 = p.sb_round - 34.0;
    let x1 = p.width - p.sb_round + 4.0;
    let xs = x0 + 0.53 * (x1 - x0); // the E's stem
    let t = 0.95 * s;
    let leg = bar(x0, 0.0, xs + s / 2.0, p.cap, t, -1.0, 1.0);
    g.stroke(&leg);
    g.stroke(&vstem(xs, 0.0, p.cap, s));
    // the A's bar, from the leg's centre line to the stem
    let y = 0.30 * p.cap;
    let f = y / p.cap;
    let xl = leg[0].z.x + f * (leg[1].z.x - leg[0].z.x);
    g.stroke(&hbar(xl, xs, y, h));
    e_arms(g, xs, x1, h);
}

/// Œ: the left half of O, closed by the stem of E, and the arms of E.
fn OE(g: &mut Draw) {
    let p = g.p;
    let s = p.cap_stem * crowd(p, 0.70);
    let h = p.cap_hair * crowd(p, 0.55);
    let x0 = p.sb_round - 24.0;
    let x1 = p.width - p.sb_round + 4.0;
    let xs = x0 + 0.55 * (x1 - x0);
    g.stroke(&vstem(xs, 0.0, p.cap, s));
    let bowl_r = xs - (x0 + s / 2.0);
    g.stroke(&[
        knot(xs, p.cap - h / 2.0, h).pen(90.0).dir(180.0).line(),
        knot(xs - 0.3 * bowl_r, p.cap - h / 2.0, h).dir(180.0).k(sqc(p)),
        knot(x0 + s / 2.0, p.cap / 2.0, s).dir(-90.0).k(sqc(p)),
        knot(xs - 0.3 * bowl_r, h / 2.0, h).dir(0.0).line(),
        knot(xs, h / 2.0, h).pen(90.0),
    ]);
    e_arms(g, xs, x1, h);
}

// ---------------------------------------------------------------------------------------------------------------
// Registration

/// Register a mark above twice: the combining character over a lowercase letter, and its capital form.
fn register_above(reg: &mut Registry, c: char, shape: Shape) {
    reg.ch_with(c, Opt::MARK, move |g: &mut Draw| {
        let p = g.p;
        let z = lower_zone(g);
        shape(g, p.mid(), z);
        g.anchor("_top", p.mid(), p.xh);
    });
    reg.glyph(&case_name(c), &[], Opt::MARK, move |g: &mut Draw| {
        let p = g.p;
        let z = case_zone(g);
        shape(g, p.mid(), z);
        g.anchor("_top", p.mid(), p.cap);
    });
}

/// A spacing accent: the shape of a mark centred in a cell of its own, where it would sit over a lowercase
/// letter.
fn register_spacing(reg: &mut Registry, cp: u32, shape: Shape) {
    reg.code(cp, Opt::default(), move |g: &mut Draw| {
        let p = g.p;
        let z = lower_zone(g);
        shape(g, p.mid(), z);
    });
}

pub fn register(reg: &mut Registry) {
    reg.module("latin");

    // combining marks
    for (c, shape) in ABOVE {
        register_above(reg, c, shape);
    }
    reg.ch_with('\u{326}', Opt::MARK, |g: &mut Draw| {
        let p = g.p;
        comma_below(g, p.mid());
        g.anchor("_bottom", p.mid(), 0.0);
    });
    reg.ch_with('\u{327}', Opt::MARK, |g: &mut Draw| {
        let p = g.p;
        cedilla(g, p.mid());
        g.anchor("_cedilla", p.mid(), 0.0);
    });
    reg.ch_with('\u{328}', Opt::MARK, |g: &mut Draw| {
        let p = g.p;
        ogonek(g, p.mid());
        g.anchor("_ogonek", p.mid(), 0.0);
    });
    // lines that join from cell to cell, an overlay, and two marks below
    reg.ch_with('\u{305}', Opt::MARK, |g: &mut Draw| {
        let p = g.p;
        let t = rule_t(g);
        let y = p.cap + case_gap(p);
        g.rect(0.0, y, p.width, y + t);
        g.anchor("_rule", p.mid(), 0.0);
    });
    reg.ch_with('\u{332}', Opt::MARK, |g: &mut Draw| {
        let p = g.p;
        let (y0, y1) = match g.glyph_of_char('_').and_then(|u| u.bounds()) {
            Some((_, y0, _, y1)) => (y0, y1),
            None => (-30.0 - p.op, -30.0),
        };
        g.rect(0.0, y0, p.width, y1);
        g.anchor("_rule", p.mid(), 0.0);
    });
    reg.ch_with('\u{338}', Opt::MARK, |g: &mut Draw| {
        let p = g.p;
        let (a, b) = (pt(p.mid() - 0.27 * p.width, -0.08 * p.cap), pt(p.mid() + 0.27 * p.width, 1.08 * p.cap));
        g.stroke(&[Knot::at(a, 0.9 * p.hair).line(), Knot::at(b, 0.9 * p.hair)]);
        g.anchor("_rule", p.mid(), 0.0);
    });
    reg.ch_with('\u{330}', Opt::MARK, |g: &mut Draw| {
        let p = g.p;
        let z = lower_zone(g);
        let t = 0.9 * mark_t(p);
        let ink = 0.06 * z.h + 2.0 * (0.17 * z.h + 0.12 * t) + t; // the tilde's height, as `tilde` draws it
        tilde(g, p.mid(), Zone { y0: -below_gap(p) - ink, ..z });
        g.anchor("_bottom", p.mid(), 0.0);
    });
    reg.ch_with('\u{32A}', Opt::MARK, |g: &mut Draw| {
        let p = g.p;
        let t = 0.86 * mark_t(p);
        let a = 0.62 * chevron_half(p);
        let top = -below_gap(p);
        let legs = 0.5 * mark_h(p);
        g.stroke(&hbar(p.mid() - a, p.mid() + a, top - t / 2.0, t));
        g.stroke(&vstem(p.mid() - a + t / 2.0, top - legs, top - t / 2.0, t));
        g.stroke(&vstem(p.mid() + a - t / 2.0, top - legs, top - t / 2.0, t));
        g.anchor("_bottom", p.mid(), 0.0);
    });
    reg.glyph("uni030A0301", &[], Opt::MARK, |g: &mut Draw| {
        let p = g.p;
        let z = lower_zone(g);
        ring_acute(g, p.mid(), z);
        g.anchor("_top", p.mid(), p.xh);
    });
    reg.glyph("uni030A0301.case", &[], Opt::MARK, |g: &mut Draw| {
        let p = g.p;
        let z = case_zone(g);
        ring_acute(g, p.mid(), z);
        g.anchor("_top", p.mid(), p.cap);
    });

    // letters drawn in full, or from a measured base; the precomposed letters may stand on them
    reg.ch('æ', ae);
    reg.ch('Æ', AE);
    reg.ch('œ', oe);
    reg.ch('Œ', OE);
    reg.ch('ø', oslash);
    reg.ch('Ø', Oslash);
    reg.ch('ß', germandbls);
    reg.ch('ẞ', Germandbls);
    reg.ch('Ð', Eth);
    reg.ch('Đ', |g: &mut Draw| g.same_as_char('Ð'));
    reg.ch('ð', eth);
    reg.ch('Þ', Thorn);
    reg.ch('þ', thorn);
    reg.ch('đ', dcroat);
    reg.ch('Ħ', Hbar);
    reg.ch('ħ', hbar_);
    reg.ch('ĸ', kgreenlandic);
    reg.ch('Ł', Lslash);
    reg.ch('ł', lslash);
    reg.ch('Ŋ', Eng);
    reg.ch('ŋ', eng);
    reg.ch('Ŧ', Tbar);
    reg.ch('ŧ', tbar);
    reg.ch('ſ', longs);
    reg.ch('ƒ', florin);

    // precomposed letters
    for &(c, base, marks) in COMPOSED {
        reg.ch(c, move |g: &mut Draw| compose(g, base, marks));
    }
    reg.ch('ǻ', |g: &mut Draw| {
        compose(g, 'a', "");
        let Some(b) = g.glyph_of_char('a') else { return };
        place(g, &b, "uni030A0301", "top", 0.0);
    });
    reg.ch('Ǻ', |g: &mut Draw| {
        compose(g, 'A', "");
        let Some(b) = g.glyph_of_char('A') else { return };
        place(g, &b, "uni030A0301.case", "top", 0.0);
    });
    reg.ch('ď', |g: &mut Draw| caron_stem(g, 'd'));
    reg.ch('ľ', |g: &mut Draw| caron_stem(g, 'l'));
    reg.ch('ť', |g: &mut Draw| caron_stem(g, 't'));
    reg.ch('Ľ', |g: &mut Draw| caron_stem(g, 'L'));
    reg.ch('ŀ', |g: &mut Draw| middle_dot(g, 'l'));
    reg.ch('Ŀ', |g: &mut Draw| middle_dot(g, 'L'));
    reg.ch('ŉ', n_apostrophe);
    reg.ch('ĳ', ij);
    reg.ch('Ĳ', IJ);

    // spacing accents
    register_spacing(reg, 0x00A8, diaeresis);
    register_spacing(reg, 0x00AF, macron);
    register_spacing(reg, 0x00B4, acute);
    register_spacing(reg, 0x02C6, circumflex);
    register_spacing(reg, 0x02C7, caron);
    register_spacing(reg, 0x02C9, macron);
    register_spacing(reg, 0x02D8, breve);
    register_spacing(reg, 0x02D9, dot_above);
    register_spacing(reg, 0x02DA, ring_above);
    register_spacing(reg, 0x02DC, tilde);
    register_spacing(reg, 0x02DD, double_acute);
    reg.code(0x00B8, Opt::default(), |g: &mut Draw| {
        let p = g.p;
        cedilla(g, p.mid());
    });
    reg.code(0x02DB, Opt::default(), |g: &mut Draw| {
        let p = g.p;
        ogonek(g, p.mid());
    });
    reg.code(0x02F3, Opt::default(), |g: &mut Draw| {
        let p = g.p;
        let rx = 0.8 * ring_rx(p);
        let t = 0.94 * ring_t(p);
        let top = -below_gap(p) + 0.5 * p.hair;
        g.stroke_closed(&ring(p.mid() - rx, top - 1.7 * rx, p.mid() + rx, top, t, 0.84 * t, 0.62));
    });
    reg.code(0x02BC, Opt::default(), |g: &mut Draw| g.same_as_char('’'));
}

/// What this module's glyphs ask of the proportional family. The letters built on a measured base take that
/// base's advance in their programs; the letters drawn in full ask for sidebearings and ink as the letters they
/// are made like do; the spacing accents ask for a little room at each side.
pub fn ask(name: &str, p: &Params) -> Option<Ask> {
    let (sb, round, cap_sb) = (p.sb, p.sb_round, p.cap_sb);
    let cap_round = 1.04 * round;
    let spacing = |cps: &[u32]| cps.iter().any(|&cp| name_of_code(cp) == name);
    match name {
        "ae" => around(0.9 * round, ink(p, 3.0, 1.85), 0.9 * round),
        "oe" => around(round, ink(p, 3.0, 2.0), 0.9 * round),
        "AE" => around(0.14 * cap_round, cap_ink(p, 2.0, 2.85), 0.96 * cap_round),
        "OE" => around(cap_round, cap_ink(p, 2.0, 2.85), 0.96 * cap_round),
        "germandbls" => around(sb, ink(p, 2.0, 1.1), round),
        "eng" => around(sb, ink(p, 2.0, 1.0), 0.95 * sb),
        "thorn" => around(sb, ink(p, 2.0, 1.119), round),
        "eth" => around(round, ink(p, 2.0, 1.222), round),
        "florin" => beside(0.3 * sb, 0.2 * sb),
        "uni1E9E" => around(cap_sb, cap_ink(p, 2.0, 1.40), 0.9 * cap_round),
        "Thorn" => around(cap_sb, cap_ink(p, 2.0, 1.16), 0.72 * cap_round),
        "Eng" => around(cap_sb, cap_ink(p, 2.0, 1.476), cap_sb),
        _ if spacing(&[0x00B4, 0x02D9, 0x00B8, 0x02DB]) => beside(0.7 * sb, 0.7 * sb),
        _ if spacing(&[0x00A8, 0x00AF, 0x02C6, 0x02C7, 0x02C9, 0x02D8, 0x02DA, 0x02DC, 0x02DD, 0x02F3]) => {
            beside(0.5 * sb, 0.5 * sb)
        }
        _ => None,
    }
}
