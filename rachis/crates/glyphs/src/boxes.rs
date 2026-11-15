//! Box drawing, block elements, braille patterns and the Powerline symbols.
//!
//! These glyphs are placed by arithmetic. Each is drawn in its cell (x from 0 to the advance, y from the bottom of
//! the line to its top) so that it meets the glyph in the next cell and on the next line exactly. None of them
//! slants in the italic.
//!
//! No contour here overlaps another. A rasteriser that sums the areas of contours (FreeType does) counts an
//! overlap twice, which darkens the pixel in the corner of a junction, so every junction is drawn as the outline
//! of the union of its arms.

use std::collections::{BTreeMap, BTreeSet};

use rachis_kernel::{Contour, Draw, Knot, Opt, Params, Registry, Seg, V, knot, pt};

use crate::parts::{flip, mirror};

type Rect = (f64, f64, f64, f64); // x0, y0, x1, y1

// ---------------------------------------------------------------------------------------------------------------
// The cell and the lines

/// The rectangle a glyph of this module fills or runs across, and its centre.
#[derive(Clone, Copy, Debug)]
pub struct Cell {
    pub x0: f64,
    pub y0: f64,
    pub x1: f64,
    pub y1: f64,
    pub cx: f64,
    pub cy: f64,
}

impl Cell {
    pub fn w(&self) -> f64 {
        self.x1 - self.x0
    }

    pub fn h(&self) -> f64 {
        self.y1 - self.y0
    }

    /// The rectangle between the given fractions of the cell's width and height.
    pub fn part(&self, fx0: f64, fy0: f64, fx1: f64, fy1: f64) -> Rect {
        (self.x0 + fx0 * self.w(), self.y0 + fy0 * self.h(), self.x0 + fx1 * self.w(), self.y0 + fy1 * self.h())
    }
}

pub fn cell(p: &Params) -> Cell {
    Cell {
        x0: 0.0,
        y0: p.line_bot,
        x1: p.width,
        y1: p.line_top,
        cx: p.width / 2.0,
        cy: (p.line_top + p.line_bot) / 2.0,
    }
}

/// The clear space between the two lines of a double line. It does not grow with weight: it is as wide as the
/// Bold's light line, so the two lines stay apart at every weight, and at 13 px it is 1.4 px in all of them.
const DOUBLE_GAP: f64 = 110.0;

/// The clear space between the dashes of a dashed line, along the line: the same for 2, 3 and 4 dashes to the
/// cell, and the same in every weight. Half of it lies at each end of the cell, so dashes continue evenly across
/// cells.
const DASH_GAP: f64 = 80.0;

/// The radius of the centre line of a rounded corner, as a fraction of half the cell's width.
const ARC: f64 = 0.5;

/// The thickness of a light line: one operator stroke.
pub fn light(p: &Params) -> f64 {
    p.op
}

/// The thickness of a heavy line. It needs no upper limit to stay apart from a double line, which is broader
/// by `DOUBLE_GAP` at every weight and open in the middle.
pub fn heavy(p: &Params) -> f64 {
    2.0 * p.op
}

/// How far the centre line of each line of a double line lies from the centre line of the pair.
pub fn double_offset(p: &Params) -> f64 {
    (light(p) + DOUBLE_GAP) / 2.0
}

// ---------------------------------------------------------------------------------------------------------------
// The union of rectangles

/// The outlines of the union of rectangles: one counter-clockwise list of corners for each connected piece.
///
/// Each outline starts at its lowest corner (the leftmost of those), and the outlines are in the order of those
/// corners, so that masters whose rectangles lie in the same order give the same points in the same order. Pieces
/// that touch only at a corner stay separate. The shapes of this module enclose no holes.
pub fn union(rects: &[Rect]) -> Vec<Vec<V>> {
    fn key(v: f64) -> i64 {
        (v * 1e6).round() as i64
    }

    let xs: Vec<i64> = rects.iter().flat_map(|r| [key(r.0), key(r.2)]).collect::<BTreeSet<_>>().into_iter().collect();
    let ys: Vec<i64> = rects.iter().flat_map(|r| [key(r.1), key(r.3)]).collect::<BTreeSet<_>>().into_iter().collect();
    let ix: BTreeMap<i64, i64> = xs.iter().enumerate().map(|(i, &v)| (v, i as i64)).collect();
    let iy: BTreeMap<i64, i64> = ys.iter().enumerate().map(|(j, &v)| (v, j as i64)).collect();
    let mut inside: BTreeSet<(i64, i64)> = BTreeSet::new();
    for &(x0, y0, x1, y1) in rects {
        for i in ix[&key(x0)]..ix[&key(x1)] {
            for j in iy[&key(y0)]..iy[&key(y1)] {
                inside.insert((i, j));
            }
        }
    }
    // every edge between a filled square of the grid and an empty one, directed with the filled one on its left
    let mut leaving: BTreeMap<(i64, i64), Vec<(i64, i64)>> = BTreeMap::new();
    for &(i, j) in &inside {
        for (a, b, (di, dj)) in [
            ((i, j), (i + 1, j), (0, -1)),
            ((i + 1, j), (i + 1, j + 1), (1, 0)),
            ((i + 1, j + 1), (i, j + 1), (0, 1)),
            ((i, j + 1), (i, j), (-1, 0)),
        ] {
            if !inside.contains(&(i + di, j + dj)) {
                leaving.entry(a).or_default().push(b);
            }
        }
    }

    let mut loops: Vec<Vec<V>> = Vec::new();
    while !leaving.is_empty() {
        let start = *leaving.keys().min_by_key(|v| (v.1, v.0)).unwrap();
        let mut path = vec![start];
        let mut heading = (1, 0);
        loop {
            let at = *path.last().unwrap();
            let choices = leaving.get_mut(&at).unwrap();
            // where two pieces touch at a corner there are two ways on: turn left, which keeps the pieces apart
            let left = (at.0 - heading.1, at.1 + heading.0);
            let nxt = if choices.len() > 1 && choices.contains(&left) { left } else { choices[0] };
            let pos = choices.iter().position(|&c| c == nxt).unwrap();
            choices.remove(pos);
            if choices.is_empty() {
                leaving.remove(&at);
            }
            heading = (nxt.0 - at.0, nxt.1 - at.1);
            if nxt == start {
                break;
            }
            path.push(nxt);
        }
        let n = path.len();
        let corners: Vec<(i64, i64)> = (0..n)
            .filter(|&k| {
                let v = path[k];
                let prev = path[(k + n - 1) % n];
                let next = path[(k + 1) % n];
                (v.0 - prev.0, v.1 - prev.1) != (next.0 - v.0, next.1 - v.1)
            })
            .map(|k| path[k])
            .collect();
        let lp: Vec<V> =
            corners.iter().map(|&(i, j)| pt(xs[i as usize] as f64 / 1e6, ys[j as usize] as f64 / 1e6)).collect();
        let m = lp.len();
        let area: f64 = (0..m)
            .map(|k| {
                let (a, b) = (lp[k], lp[(k + 1) % m]);
                a.x * b.y - a.y * b.x
            })
            .sum();
        if area <= 0.0 {
            panic!("the union of these rectangles encloses a hole");
        }
        loops.push(lp);
    }
    loops
}

/// Add the union of `rects` to the glyph.
pub fn fill(g: &mut Draw, rects: &[Rect]) {
    for lp in union(rects) {
        g.poly(&lp);
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Box drawing: lines, corners, tees and crosses

/// The arms of each character, as its Unicode name states them: left, right, up, down. An arm is absent (.),
/// light (l; the names of the double set call it single), heavy (h) or double (d). A key is the first code point
/// of a run of consecutive characters.
const ARMS: [(u32, &str); 15] = [
    (0x2500, "ll.. hh.. ..ll ..hh"),                     // ─ ━ │ ┃
    (0x250C, ".l.l .h.l .l.h .h.h l..l h..l l..h h..h"), // ┌ ┍ ┎ ┏ ┐ ┑ ┒ ┓
    (0x2514, ".ll. .hl. .lh. .hh. l.l. h.l. l.h. h.h."), // └ ┕ ┖ ┗ ┘ ┙ ┚ ┛
    (0x251C, ".lll .hll .lhl .llh .lhh .hhl .hlh .hhh"), // ├ ┝ ┞ ┟ ┠ ┡ ┢ ┣
    (0x2524, "l.ll h.ll l.hl l.lh l.hh h.hl h.lh h.hh"), // ┤ ┥ ┦ ┧ ┨ ┩ ┪ ┫
    (0x252C, "ll.l hl.l lh.l hh.l ll.h hl.h lh.h hh.h"), // ┬ ┭ ┮ ┯ ┰ ┱ ┲ ┳
    (0x2534, "lll. hll. lhl. hhl. llh. hlh. lhh. hhh."), // ┴ ┵ ┶ ┷ ┸ ┹ ┺ ┻
    (0x253C, "llll hlll lhll hhll llhl lllh llhh hlhl"), // ┼ ┽ ┾ ┿ ╀ ╁ ╂ ╃
    (0x2544, "lhhl hllh lhlh hhhl hhlh hlhh lhhh hhhh"), // ╄ ╅ ╆ ╇ ╈ ╉ ╊ ╋
    (0x2550, "dd.. ..dd .d.l .l.d .d.d d..l l..d d..d"), // ═ ║ ╒ ╓ ╔ ╕ ╖ ╗
    (0x2558, ".dl. .ld. .dd. d.l. l.d. d.d. .dll .ldd"), // ╘ ╙ ╚ ╛ ╜ ╝ ╞ ╟
    (0x2560, ".ddd d.ll l.dd d.dd dd.l ll.d dd.d ddl."), // ╠ ╡ ╢ ╣ ╤ ╥ ╦ ╧
    (0x2568, "lld. ddd. ddll lldd dddd"),                // ╨ ╩ ╪ ╫ ╬
    (0x2574, "l... ..l. .l.. ...l h... ..h. .h.. ...h"), // ╴ ╵ ╶ ╷ ╸ ╹ ╺ ╻
    (0x257C, "lh.. ..lh hl.. ..hl"),                     // ╼ ╽ ╾ ╿
];

const RANK: &str = ".lhd";

/// The lines of an arm: for each, its centre line's offset from the cell's centre line, and its thickness.
pub fn strips(p: &Params, style: char) -> Vec<(f64, f64)> {
    match style {
        'l' => vec![(0.0, light(p))],
        'h' => vec![(0.0, heavy(p))],
        'd' => vec![(-double_offset(p), light(p)), (double_offset(p), light(p))],
        _ => vec![],
    }
}

/// From an arm's centre line to its outer edge.
pub fn breadth(p: &Params, style: char) -> f64 {
    match style {
        'l' => light(p) / 2.0,
        'h' => heavy(p) / 2.0,
        'd' => double_offset(p) + light(p) / 2.0,
        _ => 0.0,
    }
}

/// How far past the centre of the cell one line of an arm runs; negative when it stops short of the centre.
///
/// `low` and `high` are the arms that cross this one, on the side of negative and of positive offsets.
///
/// A light or heavy line runs to the far side of the line it meets, so that a corner is square and a tee has no
/// notch; with nothing to meet, it stops at the centre. The outer line of a double corner does the same, and its
/// inner line stops inside the inner line of the other arm. A single line that meets a double line across its
/// path stops inside the nearer of the two lines, unless it goes on from the other side.
pub fn past_centre(p: &Params, style: char, offset: f64, opposite: char, low: char, high: char) -> f64 {
    let inner = double_offset(p) - light(p) / 2.0; // from the centre to the inner edge of a double arm's line
    if style != 'd' {
        let doubles = (low == 'd') as i32 + (high == 'd') as i32;
        if doubles == 2 {
            return if opposite != '.' { 0.0 } else { -inner };
        }
        let rank = |s: char| RANK.find(s).unwrap();
        // max() keeps the first of equals, as Python's does
        let top = if rank(high) > rank(low) { high } else { low };
        return breadth(p, top);
    }
    let (near, far) = if offset < 0.0 { (low, high) } else { (high, low) };
    if near == 'd' {
        return -inner;
    }
    breadth(p, if near != '.' { near } else { far })
}

/// A rectangle for each line of each arm, from the cell's edge to where the line ends.
pub fn arm_rects(p: &Params, arms: &str) -> Vec<Rect> {
    let c = cell(p);
    let a: Vec<char> = arms.chars().collect();
    let (left, right, up, down) = (a[0], a[1], a[2], a[3]);
    if arms.contains('h') && arms.contains('d') {
        panic!("no character joins a heavy line to a double one");
    }
    let mut rects: Vec<Rect> = Vec::new();
    for (style, opposite, towards_origin) in [(left, right, true), (right, left, false)] {
        for (offset, t) in strips(p, style) {
            let reach = past_centre(p, style, offset, opposite, down, up);
            let (xa, xb) = if towards_origin { (c.x0, c.cx + reach) } else { (c.cx - reach, c.x1) };
            rects.push((xa, c.cy + offset - t / 2.0, xb, c.cy + offset + t / 2.0));
        }
    }
    for (style, opposite, towards_origin) in [(down, up, true), (up, down, false)] {
        for (offset, t) in strips(p, style) {
            let reach = past_centre(p, style, offset, opposite, left, right);
            let (ya, yb) = if towards_origin { (c.y0, c.cy + reach) } else { (c.cy - reach, c.y1) };
            rects.push((c.cx + offset - t / 2.0, ya, c.cx + offset + t / 2.0, yb));
        }
    }
    rects
}

// ---------------------------------------------------------------------------------------------------------------
// Box drawing: dashed lines, rounded corners, diagonals

/// code point: dashes to the cell, weight, horizontal
const DASHED: [(u32, f64, char, bool); 12] = [
    (0x2504, 3.0, 'l', true),  // ┄
    (0x2505, 3.0, 'h', true),  // ┅
    (0x2506, 3.0, 'l', false), // ┆
    (0x2507, 3.0, 'h', false), // ┇
    (0x2508, 4.0, 'l', true),  // ┈
    (0x2509, 4.0, 'h', true),  // ┉
    (0x250A, 4.0, 'l', false), // ┊
    (0x250B, 4.0, 'h', false), // ┋
    (0x254C, 2.0, 'l', true),  // ╌
    (0x254D, 2.0, 'h', true),  // ╍
    (0x254E, 2.0, 'l', false), // ╎
    (0x254F, 2.0, 'h', false), // ╏
];

fn dashed(g: &mut Draw, count: f64, style: char, horizontal: bool) {
    let p = g.p;
    let c = cell(p);
    let t = breadth(p, style);
    let period = (if horizontal { c.w() } else { c.h() }) / count;
    for k in 0..count as i32 {
        let k = k as f64;
        let (a, b) = (k * period + DASH_GAP / 2.0, (k + 1.0) * period - DASH_GAP / 2.0);
        if horizontal {
            g.rect(c.x0 + a, c.cy - t, c.x0 + b, c.cy + t);
        } else {
            g.rect(c.cx - t, c.y0 + a, c.cx + t, c.y0 + b);
        }
    }
}

/// The rounded corner that joins the arm going down to the arm going right (╭): a light line up the centre
/// of the cell, a quarter turn of the typeface's own elbow, and a light line to the right edge.
pub fn arc_knots(p: &Params) -> Vec<Knot> {
    let c = cell(p);
    let t = light(p);
    let r = ARC * c.w() / 2.0;
    vec![
        knot(c.cx, c.y0, t).pen(0.0).line(),
        knot(c.cx, c.cy - r, t).pen(0.0).dir(90.0).k(p.sq),
        knot(c.cx + r, c.cy, t).pen(90.0).dir(0.0).line(),
        knot(c.x1, c.cy, t).pen(90.0),
    ]
}

/// ╭ arc down and right
fn arc_down_right(g: &mut Draw) {
    let p = g.p;
    g.stroke(&arc_knots(p));
}

/// ╮ arc down and left
fn arc_down_left(g: &mut Draw) {
    let p = g.p;
    g.stroke(&mirror(&arc_knots(p), cell(p).cx));
}

/// ╯ arc up and left
fn arc_up_left(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    g.stroke(&flip(&mirror(&arc_knots(p), c.cx), c.cy));
}

/// ╰ arc up and right
fn arc_up_right(g: &mut Draw) {
    let p = g.p;
    g.stroke(&flip(&arc_knots(p), cell(p).cy));
}

/// Half the breadth, measured along the cell's top edge, of a light line from corner to corner of the cell.
pub fn diagonal_half(p: &Params) -> f64 {
    let c = cell(p);
    light(p) * c.w().hypot(c.h()) / c.h() / 2.0
}

/// ╱ diagonal from the lower left corner to the upper right
fn diagonal_rising(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    let h = diagonal_half(p);
    g.poly(&[pt(c.x0 - h, c.y0), pt(c.x0 + h, c.y0), pt(c.x1 + h, c.y1), pt(c.x1 - h, c.y1)]);
}

/// ╲ diagonal from the upper left corner to the lower right
fn diagonal_falling(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    let h = diagonal_half(p);
    g.poly(&[pt(c.x1 - h, c.y0), pt(c.x1 + h, c.y0), pt(c.x0 + h, c.y1), pt(c.x0 - h, c.y1)]);
}

/// ╳ both diagonals, as one outline
fn diagonal_cross(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    let h = diagonal_half(p);
    let v = h * c.h() / c.w(); // from the centre to the crotch above and below it
    g.poly(&[
        pt(c.x0 - h, c.y0),
        pt(c.x0 + h, c.y0),
        pt(c.cx, c.cy - v),
        pt(c.x1 - h, c.y0),
        pt(c.x1 + h, c.y0),
        pt(c.cx + h, c.cy),
        pt(c.x1 + h, c.y1),
        pt(c.x1 - h, c.y1),
        pt(c.cx, c.cy + v),
        pt(c.x0 + h, c.y1),
        pt(c.x0 - h, c.y1),
        pt(c.cx - h, c.cy),
    ]);
}

// ---------------------------------------------------------------------------------------------------------------
// Block elements

const LL: Rect = (0.0, 0.0, 0.5, 0.5);
const LR: Rect = (0.5, 0.0, 1.0, 0.5);
const UL: Rect = (0.0, 0.5, 0.5, 1.0);
const UR: Rect = (0.5, 0.5, 1.0, 1.0);

/// The parts of the cell each block fills, as fractions of its width and height: x0, y0, x1, y1.
fn blocks() -> Vec<(u32, Vec<Rect>)> {
    let mut b: Vec<(u32, Vec<Rect>)> = vec![(0x2580, vec![(0.0, 0.5, 1.0, 1.0)])]; // ▀ upper half
    // ▁ ▂ ▃ ▄ ▅ ▆ ▇ █ lower eighths, full
    for k in 1..9u32 {
        b.push((0x2580 + k, vec![(0.0, 0.0, 1.0, k as f64 / 8.0)]));
    }
    // ▉ ▊ ▋ ▌ ▍ ▎ ▏ left eighths
    for k in 1..8u32 {
        b.push((0x2590 - k, vec![(0.0, 0.0, k as f64 / 8.0, 1.0)]));
    }
    b.extend([
        (0x2590, vec![(0.5, 0.0, 1.0, 1.0)]),   // ▐ right half
        (0x2594, vec![(0.0, 0.875, 1.0, 1.0)]), // ▔ upper eighth
        (0x2595, vec![(0.875, 0.0, 1.0, 1.0)]), // ▕ right eighth
        (0x2596, vec![LL]),                     // ▖
        (0x2597, vec![LR]),                     // ▗
        (0x2598, vec![UL]),                     // ▘
        (0x2599, vec![UL, LL, LR]),             // ▙
        (0x259A, vec![UL, LR]),                 // ▚
        (0x259B, vec![UL, UR, LL]),             // ▛
        (0x259C, vec![UL, UR, LR]),             // ▜
        (0x259D, vec![UR]),                     // ▝
        (0x259E, vec![UR, LL]),                 // ▞
        (0x259F, vec![UR, LL, LR]),             // ▟
    ]);
    b
}

fn block(g: &mut Draw, parts: &[Rect]) {
    let p = g.p;
    let c = cell(p);
    let rects: Vec<Rect> = parts.iter().map(|&(a, b, d, e)| c.part(a, b, d, e)).collect();
    fill(g, &rects);
}

/// Shades. The pattern is a grid of squares SHADE on a side, so fine that at reading sizes it is an even grey, and
/// it repeats every two squares both ways: twelve times across the cell and twenty-five times up it, so it goes on
/// unbroken into the next cell and the next line.
const SHADE: f64 = 25.0;

pub fn shade_counts(c: &Cell) -> (i64, i64) {
    // the quotients are whole numbers (checked below), so no half is ever rounded
    let (nx, ny) = ((c.w() / SHADE).round(), (c.h() / SHADE).round());
    if nx % 2.0 != 0.0 || ny % 2.0 != 0.0 || nx * SHADE != c.w() || ny * SHADE != c.h() {
        panic!("the shade pattern does not divide the cell");
    }
    (nx as i64, ny as i64)
}

fn square(c: &Cell, i: i64, j: i64) -> Rect {
    let (i, j) = (i as f64, j as f64);
    (c.x0 + i * SHADE, c.y0 + j * SHADE, c.x0 + (i + 1.0) * SHADE, c.y0 + (j + 1.0) * SHADE)
}

/// ░ light shade: one square in four
fn shade_light(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    let (nx, ny) = shade_counts(&c);
    for j in (0..ny).step_by(2) {
        for i in (0..nx).step_by(2) {
            let (x0, y0, x1, y1) = square(&c, i, j);
            g.rect(x0, y0, x1, y1);
        }
    }
}

/// ▒ medium shade: a chequerboard, two squares in four
fn shade_medium(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    let (nx, ny) = shade_counts(&c);
    for j in 0..ny {
        for i in (j % 2..nx).step_by(2) {
            let (x0, y0, x1, y1) = square(&c, i, j);
            g.rect(x0, y0, x1, y1);
        }
    }
}

/// ▓ dark shade: the cell with one square in four cut out of it
fn shade_dark(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    let (nx, ny) = shade_counts(&c);
    g.rect(c.x0, c.y0, c.x1, c.y1);
    for j in (1..ny).step_by(2) {
        for i in (1..nx).step_by(2) {
            let (x0, y0, x1, y1) = square(&c, i, j);
            g.add(Contour::new(vec![
                Seg::Line(pt(x0, y0), pt(x0, y1)),
                Seg::Line(pt(x0, y1), pt(x1, y1)),
                Seg::Line(pt(x1, y1), pt(x1, y0)),
                Seg::Line(pt(x1, y0), pt(x0, y0)),
            ]));
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Braille patterns

/// The radius of a braille dot, as a fraction of the period's.
const BRAILLE_DOT: f64 = 0.9;

/// The distance between neighbouring dots, the same across and up.
///
/// Two columns and four rows cannot both continue evenly into the next cell with one pitch: across, the cell
/// wants half its width, and up, a quarter of its height. This pitch splits the difference, so that the step
/// from one cell to the next is as much too short across as it is too long up (16 and 18 units in 308).
pub fn braille_pitch(p: &Params) -> f64 {
    let c = cell(p);
    2.0 * ((c.w() + c.h()) / 12.0).round()
}

/// The centres of dots 1 to 8: 1, 2, 3 down the left column, 4, 5, 6 down the right, then 7 and 8 below.
pub fn braille_centres(p: &Params) -> Vec<V> {
    let c = cell(p);
    let d = braille_pitch(p);
    let (xl, xr) = (c.cx - d / 2.0, c.cx + d / 2.0);
    let rows: Vec<f64> = (0..4).map(|k| c.cy + (1.5 - k as f64) * d).collect();
    vec![
        pt(xl, rows[0]),
        pt(xl, rows[1]),
        pt(xl, rows[2]),
        pt(xr, rows[0]),
        pt(xr, rows[1]),
        pt(xr, rows[2]),
        pt(xl, rows[3]),
        pt(xr, rows[3]),
    ]
}

fn braille(g: &mut Draw, bits: u32) {
    let p = g.p;
    let r = BRAILLE_DOT * p.punct;
    for (k, z) in braille_centres(p).into_iter().enumerate() {
        if bits >> k & 1 != 0 {
            g.dot(z.x, z.y, r);
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Powerline: separators

fn pointing_left(points: &[V], c: &Cell) -> Vec<V> {
    points.iter().map(|z| pt(c.x0 + c.x1 - z.x, z.y)).collect()
}

/// The triangle that fills the cell's height: flat on the left edge, pointed at the middle of the right.
pub fn arrow_points(c: &Cell) -> Vec<V> {
    vec![pt(c.x0, c.y0), pt(c.x1, c.cy), pt(c.x0, c.y1)]
}

/// The two sloping sides of that triangle as light lines, cut plumb by the cell's left edge.
pub fn chevron_points(p: &Params) -> Vec<V> {
    let c = cell(p);
    let slope = c.w().hypot(c.h() / 2.0);
    let v = light(p) * slope / c.w(); // the line's thickness measured up the cell's edge
    let h = light(p) * slope / (c.h() / 2.0); // and measured along the centre line
    vec![pt(c.x0, c.y0), pt(c.x1, c.cy), pt(c.x0, c.y1), pt(c.x0, c.y1 - v), pt(c.x1 - h, c.cy), pt(c.x0, c.y0 + v)]
}

fn arrow_right(g: &mut Draw) {
    let p = g.p;
    g.poly(&arrow_points(&cell(p)));
}

fn chevron_right(g: &mut Draw) {
    let p = g.p;
    g.poly(&chevron_points(p));
}

fn arrow_left(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    g.poly(&pointing_left(&arrow_points(&c), &c));
}

fn chevron_left(g: &mut Draw) {
    let p = g.p;
    g.poly(&pointing_left(&chevron_points(p), &cell(p)));
}

/// Half of the typeface's superellipse, from the cell's lower left corner round by the middle of its right edge
/// to the upper left corner, drawn `inset` inside the cell.
fn half_round(c: &Cell, inset: f64, k: f64) -> (Seg, Seg) {
    let (bottom, tip, top) = (pt(c.x0, c.y0 + inset), pt(c.x1 - inset, c.cy), pt(c.x0, c.y1 - inset));
    let (rx, ry) = (tip.x - c.x0, c.cy - bottom.y);
    (
        Seg::Cubic(bottom, bottom + pt(k * rx, 0.0), tip - pt(0.0, k * ry), tip),
        Seg::Cubic(tip, tip + pt(0.0, k * ry), top + pt(k * rx, 0.0), top),
    )
}

pub fn round_contour(p: &Params, outline: bool, left: bool) -> Contour {
    let c = cell(p);
    let (a, b) = half_round(&c, 0.0, p.sq);
    let segs = if outline {
        let (e, f) = half_round(&c, light(p), p.sq);
        vec![a, b, Seg::Line(b.end(), f.end()), f.reversed(), e.reversed(), Seg::Line(e.start(), a.start())]
    } else {
        vec![a, b, Seg::Line(b.end(), a.start())]
    };
    let mut shape = Contour::new(segs);
    if left {
        shape = shape.mapped(|z| pt(c.x0 + c.x1 - z.x, z.y)).reversed();
    }
    shape
}

fn round(g: &mut Draw, outline: bool, left: bool) {
    let p = g.p;
    g.add(round_contour(p, outline, left));
}

pub fn register(reg: &mut Registry) {
    reg.module("box");
    for (first, row) in ARMS {
        for (k, arms) in row.split_whitespace().enumerate() {
            reg.code(first + k as u32, Opt::UPRIGHT, move |g: &mut Draw| {
                let p = g.p;
                fill(g, &arm_rects(p, arms));
            });
        }
    }
    for (cp, count, style, horizontal) in DASHED {
        reg.code(cp, Opt::UPRIGHT, move |g: &mut Draw| dashed(g, count, style, horizontal));
    }
    reg.code(0x256D, Opt::UPRIGHT, arc_down_right);
    reg.code(0x256E, Opt::UPRIGHT, arc_down_left);
    reg.code(0x256F, Opt::UPRIGHT, arc_up_left);
    reg.code(0x2570, Opt::UPRIGHT, arc_up_right);
    reg.code(0x2571, Opt::UPRIGHT, diagonal_rising);
    reg.code(0x2572, Opt::UPRIGHT, diagonal_falling);
    reg.code(0x2573, Opt::UPRIGHT, diagonal_cross);
    for (cp, parts) in blocks() {
        reg.code(cp, Opt::UPRIGHT, move |g: &mut Draw| block(g, &parts));
    }
    reg.code(0x2591, Opt::UPRIGHT, shade_light);
    reg.code(0x2592, Opt::UPRIGHT, shade_medium);
    reg.code(0x2593, Opt::UPRIGHT, shade_dark);
    for bits in 0..256u32 {
        reg.code(0x2800 + bits, Opt::UPRIGHT, move |g: &mut Draw| braille(g, bits));
    }
    reg.code(0xE0B0, Opt::UPRIGHT, arrow_right);
    reg.code(0xE0B1, Opt::UPRIGHT, chevron_right);
    reg.code(0xE0B2, Opt::UPRIGHT, arrow_left);
    reg.code(0xE0B3, Opt::UPRIGHT, chevron_left);
    for (cp, outline, left) in
        [(0xE0B4, false, false), (0xE0B5, true, false), (0xE0B6, false, true), (0xE0B7, true, true)]
    {
        reg.code(cp, Opt::UPRIGHT, move |g: &mut Draw| round(g, outline, left));
    }
}
