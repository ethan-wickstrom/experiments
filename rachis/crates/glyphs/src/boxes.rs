//! Box drawing, block elements, braille patterns, sextants, the Powerline symbols, the branch-drawing symbols
//! and the progress indicators: the glyphs a terminal's grid is drawn with. Only the fixed-pitch family has them.
//!
//! These glyphs are placed by arithmetic. Each is drawn in its cell (x from 0 to the advance, y from the bottom of
//! the line, `p.line_bot`, to its top, `p.line_top`) so that it meets the glyph in the next cell and on the next
//! line. Applications round the cell to whole pixels, up or down, and some set lines further apart than the
//! font's line box, so a line that stopped exactly at the cell's edge would leave a hairline gap at most sizes:
//! horizontal lines run on past the cell by `over_x` at both ends, vertical lines by `over_y` above and below,
//! and blocks and Powerline separators by `block_over` on the edges that lie on the cell's edge (never at an
//! inner edge, so that a half block is exactly half). Shades and dashed lines stop at the cell's edge: their
//! patterns are drawn so that they continue into the next cell, and two overlapping patterns would darken.
//!
//! Lines do not get bolder with the text: a table's rules must not change when a cell is bold. A light line is
//! as thick as the underline in every master, a heavy line twice that, and a double line is light, gap, light.
//! None of these glyphs slants in the italic.
//!
//! No contour of a line, block or junction overlaps another. A rasteriser that sums the areas of contours
//! (FreeType does) counts an overlap twice, which darkens the pixel in the corner of a junction, so every
//! junction is drawn as the outline of the union of its arms. The curves of the branch-drawing symbols meet
//! their straight lines tangentially, where a sliver of overlap cannot be avoided, and the Powerline icons are
//! strokes like the letters'.

use std::collections::{BTreeMap, BTreeSet};

use rachis_kernel::pen::superellipse;
use rachis_kernel::{Contour, Draw, Knot, Opt, Params, Registry, Seg, V, knot, name_of, pt};

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

/// The thickness of a light line, as a fraction of the em: the underline's thickness (`post.underlineThickness`,
/// 60 units), which is also what Ghostty and WezTerm draw their own box lines with, so that a table looks the
/// same whether the terminal or the font draws it. It is the same in every master.
const LIGHT: f64 = 0.06;

/// How far a horizontal line runs past each side of the cell, as a fraction of the em: it closes the gap a cell
/// rounded up to whole pixels leaves (0.78 px at 13 px).
const OVER_X: f64 = 0.03;

/// How far a vertical line runs past the line box above and below, as a fraction of the em: a vertical line is
/// 1.45 em long, so it reaches the next line at every line height up to that (the 1.2, 1.3 and 1.35 em that
/// JetBrains' editor, Zed's terminal and VS Code's editor set among them), and in a line box rounded to whole
/// pixels.
const OVER_Y: f64 = 0.10;

/// How far blocks and Powerline separators reach past the cell's edges, as a fraction of the em: enough to
/// cover the half pixel by which a line pitch rounded to whole pixels can exceed the line box, small enough not
/// to show as a step where a block meets an empty cell.
const BLOCK_OVER: f64 = 0.03;

/// The clear space between the dashes of a dashed line, along the line: the same for 2, 3 and 4 dashes to the
/// cell, and the same in every weight. Half of it lies at each end of the cell, so dashes continue evenly across
/// cells.
const DASH_GAP: f64 = 80.0;

/// The radius of the centre line of a rounded corner, as a fraction of the cell's width.
const ARC: f64 = 0.42;

/// The thickness of a light line.
pub fn light(p: &Params) -> f64 {
    LIGHT * p.upm
}

/// The thickness of a heavy line.
pub fn heavy(p: &Params) -> f64 {
    2.0 * light(p)
}

/// How far the centre line of each line of a double line lies from the centre line of the pair: the gap
/// between the two lines is a light line's thickness.
pub fn double_offset(p: &Params) -> f64 {
    light(p)
}

/// How far a horizontal line runs past each side of the cell.
pub fn over_x(p: &Params) -> f64 {
    OVER_X * p.upm
}

/// How far a vertical line runs past the line box above and below.
pub fn over_y(p: &Params) -> f64 {
    OVER_Y * p.upm
}

/// How far blocks and separators reach past the cell's edges.
pub fn block_over(p: &Params) -> f64 {
    BLOCK_OVER * p.upm
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

/// A rectangle for each line of each arm, from past the cell's edge to where the line ends.
pub fn arm_rects(p: &Params, arms: &str) -> Vec<Rect> {
    let c = cell(p);
    let (ox, oy) = (over_x(p), over_y(p));
    let a: Vec<char> = arms.chars().collect();
    let (left, right, up, down) = (a[0], a[1], a[2], a[3]);
    if arms.contains('h') && arms.contains('d') {
        panic!("no character joins a heavy line to a double one");
    }
    let mut rects: Vec<Rect> = Vec::new();
    for (style, opposite, towards_origin) in [(left, right, true), (right, left, false)] {
        for (offset, t) in strips(p, style) {
            let reach = past_centre(p, style, offset, opposite, down, up);
            let (xa, xb) = if towards_origin { (c.x0 - ox, c.cx + reach) } else { (c.cx - reach, c.x1 + ox) };
            rects.push((xa, c.cy + offset - t / 2.0, xb, c.cy + offset + t / 2.0));
        }
    }
    for (style, opposite, towards_origin) in [(down, up, true), (up, down, false)] {
        for (offset, t) in strips(p, style) {
            let reach = past_centre(p, style, offset, opposite, left, right);
            let (ya, yb) = if towards_origin { (c.y0 - oy, c.cy + reach) } else { (c.cy - reach, c.y1 + oy) };
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

/// The radius of a rounded corner's centre line.
pub fn arc_radius(p: &Params) -> f64 {
    ARC * cell(p).w()
}

/// The rounded corner that joins the arm going down to the arm going right (╭): a light line up the centre
/// of the cell, a quarter turn of the typeface's own elbow whose ends lie on the centre lines of the straight
/// lines, and a light line to the right edge. Both straight lines run past the cell as straight lines do.
pub fn arc_knots(p: &Params) -> Vec<Knot> {
    let c = cell(p);
    let t = light(p);
    let r = arc_radius(p);
    vec![
        knot(c.cx, c.y0 - over_y(p), t).pen(0.0).line(),
        knot(c.cx, c.cy - r, t).pen(0.0).dir(90.0).k(p.sq),
        knot(c.cx + r, c.cy, t).pen(90.0).dir(0.0).line(),
        knot(c.x1 + over_x(p), c.cy, t).pen(90.0),
    ]
}

/// Only the quarter turn of that corner, from the vertical centre line to the horizontal one.
pub fn turn_knots(p: &Params) -> Vec<Knot> {
    let c = cell(p);
    let t = light(p);
    let r = arc_radius(p);
    vec![knot(c.cx, c.cy - r, t).pen(0.0).dir(90.0).k(p.sq), knot(c.cx + r, c.cy, t).pen(90.0).dir(0.0)]
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

/// How far a diagonal's centre line runs on past the cell's corners: across by a horizontal line's overshoot,
/// and up or down by as much as the diagonal's slope makes of that.
fn diagonal_ends(p: &Params) -> (f64, f64) {
    let c = cell(p);
    (over_x(p), over_x(p) * c.h() / c.w())
}

/// ╱ diagonal from the lower left corner to the upper right
fn diagonal_rising(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    let h = diagonal_half(p);
    let (ex, ey) = diagonal_ends(p);
    let (x0, y0, x1, y1) = (c.x0 - ex, c.y0 - ey, c.x1 + ex, c.y1 + ey);
    g.poly(&[pt(x0 - h, y0), pt(x0 + h, y0), pt(x1 + h, y1), pt(x1 - h, y1)]);
}

/// ╲ diagonal from the upper left corner to the lower right
fn diagonal_falling(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    let h = diagonal_half(p);
    let (ex, ey) = diagonal_ends(p);
    let (x0, y0, x1, y1) = (c.x0 - ex, c.y0 - ey, c.x1 + ex, c.y1 + ey);
    g.poly(&[pt(x1 - h, y0), pt(x1 + h, y0), pt(x0 + h, y1), pt(x0 - h, y1)]);
}

/// ╳ both diagonals, as one outline
fn diagonal_cross(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    let h = diagonal_half(p);
    let v = h * c.h() / c.w(); // from the centre to the crotch above and below it
    let (ex, ey) = diagonal_ends(p);
    let (x0, y0, x1, y1) = (c.x0 - ex, c.y0 - ey, c.x1 + ex, c.y1 + ey);
    g.poly(&[
        pt(x0 - h, y0),
        pt(x0 + h, y0),
        pt(c.cx, c.cy - v),
        pt(x1 - h, y0),
        pt(x1 + h, y0),
        pt(c.cx + h, c.cy),
        pt(x1 + h, y1),
        pt(x1 - h, y1),
        pt(c.cx, c.cy + v),
        pt(x0 + h, y1),
        pt(x0 - h, y1),
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
    // Symbols for Legacy Computing: the sextants, 2 × 3 mosaics. Bit k of n (k = 0 … 5) is sextant k + 1:
    // 1 and 2 the upper row, left and right, 3 and 4 the middle, 5 and 6 the lower. The code points run
    // through n = 1 … 62 in order, leaving out the left half (1, 3, 5: n = 21) and the right half (n = 42),
    // which are ▌ and ▐.
    for (cp, n) in (0x1FB00..).zip((1..63u32).filter(|&n| n != 21 && n != 42)) {
        let parts = (0..6u32)
            .filter(|k| n >> k & 1 != 0)
            .map(|k| {
                let (col, row) = ((k % 2) as f64, (k / 2) as f64); // row 0 is the top
                (col / 2.0, (2.0 - row) / 3.0, (col + 1.0) / 2.0, (3.0 - row) / 3.0)
            })
            .collect();
        b.push((cp, parts));
    }
    b.extend([
        (0x1FB7C, vec![(0.0, 0.0, 0.125, 1.0), (0.0, 0.0, 1.0, 0.125)]), // 🭼 left and lower eighths
        (0x1FB7D, vec![(0.0, 0.0, 0.125, 1.0), (0.0, 0.875, 1.0, 1.0)]), // 🭽 left and upper eighths
        (0x1FB7E, vec![(0.875, 0.0, 1.0, 1.0), (0.0, 0.875, 1.0, 1.0)]), // 🭾 right and upper eighths
        (0x1FB7F, vec![(0.875, 0.0, 1.0, 1.0), (0.0, 0.0, 1.0, 0.125)]), // 🭿 right and lower eighths
        (0x1FB82, vec![(0.0, 0.75, 1.0, 1.0)]),                          // 🮂 upper quarter
        (0x1FB85, vec![(0.0, 0.25, 1.0, 1.0)]),                          // 🮅 upper three quarters
    ]);
    b
}

/// The rectangle between the given fractions of the cell, reaching `block_over` past each side that lies on the
/// cell's edge; an inner edge stays exactly where the fraction puts it.
pub fn block_rect(p: &Params, (fx0, fy0, fx1, fy1): Rect) -> Rect {
    let (x0, y0, x1, y1) = cell(p).part(fx0, fy0, fx1, fy1);
    let o = block_over(p);
    let out = |f: f64, edge: f64| if f == edge { o } else { 0.0 };
    (x0 - out(fx0, 0.0), y0 - out(fy0, 0.0), x1 + out(fx1, 1.0), y1 + out(fy1, 1.0))
}

fn block(g: &mut Draw, parts: &[Rect]) {
    let p = g.p;
    let rects: Vec<Rect> = parts.iter().map(|&r| block_rect(p, r)).collect();
    fill(g, &rects);
}

/// Shades. The pattern is a grid of rectangles, SHADE_X across the cell and SHADE_Y up it (25 units square in the
/// 600 × 1250 cell), so fine that at reading sizes it is an even grey. It repeats every two rectangles both ways,
/// and both counts are even, so it goes on unbroken into the next cell and the next line. The pattern stops at
/// the cell's edges: two overlapping patterns would darken where they overlap. The counts, not the size, are
/// fixed, so the pattern divides a cell of any width.
const SHADE_X: i64 = 24;
const SHADE_Y: i64 = 50;

pub fn shade_counts() -> (i64, i64) {
    (SHADE_X, SHADE_Y)
}

fn square(c: &Cell, i: i64, j: i64) -> Rect {
    let (sx, sy) = (c.w() / SHADE_X as f64, c.h() / SHADE_Y as f64);
    let (i, j) = (i as f64, j as f64);
    (c.x0 + i * sx, c.y0 + j * sy, c.x0 + (i + 1.0) * sx, c.y0 + (j + 1.0) * sy)
}

/// ░ light shade: one square in four
fn shade_light(g: &mut Draw) {
    let p = g.p;
    let c = cell(p);
    let (nx, ny) = shade_counts();
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
    let (nx, ny) = shade_counts();
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
    let (nx, ny) = shade_counts();
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
//
// A separator stands between two coloured segments of a status line: its ink is the colour of one segment and
// the cell's background the colour of the other, so it must fill the cell to its edges, and reach past the
// edges that it shares with a segment as a block does, or a hairline of the wrong colour shows. Its points and
// curves lie exactly on the cell's edges and corners. A separator that is a line is a light line.

/// The point of the line through `a` and `b` at height `y`.
fn at_height(a: V, b: V, y: f64) -> V {
    pt(a.x + (b.x - a.x) * (y - a.y) / (b.y - a.y), y)
}

/// The point of the line through `a` and `b` at `x`.
fn at_x(a: V, b: V, x: f64) -> V {
    pt(x, a.y + (b.y - a.y) * (x - a.x) / (b.x - a.x))
}

fn pointing_left(points: &[V], c: &Cell) -> Vec<V> {
    points.iter().map(|z| pt(c.x0 + c.x1 - z.x, z.y)).collect()
}

fn upside_down(points: &[V], c: &Cell) -> Vec<V> {
    points.iter().map(|z| pt(z.x, c.y0 + c.y1 - z.y)).collect()
}

/// The triangle that fills the cell's height: flat on the left edge, pointed at the middle of the right. Its
/// sloping sides run through the cell's left corners and on past them to `block_over` beyond the left edge.
pub fn arrow_points(p: &Params) -> Vec<V> {
    let c = cell(p);
    let tip = pt(c.x1, c.cy);
    let x = c.x0 - block_over(p);
    vec![at_x(tip, pt(c.x0, c.y0), x), tip, at_x(tip, pt(c.x0, c.y1), x)]
}

/// The two sloping sides of that triangle as light lines, inside it, cut plumb at its left side.
pub fn chevron_points(p: &Params) -> Vec<V> {
    let c = cell(p);
    let slope = c.w().hypot(c.h() / 2.0);
    let v = light(p) * slope / c.w(); // the line's thickness measured up the cell's edge
    let h = light(p) * slope / (c.h() / 2.0); // and measured along the centre line
    let a = arrow_points(p);
    vec![a[0], a[1], a[2], a[2] - pt(0.0, v), pt(c.x1 - h, c.cy), a[0] + pt(0.0, v)]
}

/// The arrow with the rest of the cell filled and the arrow left open: the cell less a triangle pointing at the
/// middle of its left edge, reaching `block_over` past the cell on every side.
pub fn notch_points(p: &Params) -> Vec<V> {
    let c = cell(p);
    let o = block_over(p);
    let tip = pt(c.x0, c.cy);
    let (bottom, top) = (at_x(tip, pt(c.x1, c.y0), c.x1 + o), at_x(tip, pt(c.x1, c.y1), c.x1 + o));
    vec![pt(c.x0 - o, bottom.y), bottom, tip, top, pt(c.x0 - o, top.y)]
}

fn arrow_right(g: &mut Draw) {
    let p = g.p;
    g.poly(&arrow_points(p));
}

fn chevron_right(g: &mut Draw) {
    let p = g.p;
    g.poly(&chevron_points(p));
}

fn arrow_left(g: &mut Draw) {
    let p = g.p;
    g.poly(&pointing_left(&arrow_points(p), &cell(p)));
}

fn chevron_left(g: &mut Draw) {
    let p = g.p;
    g.poly(&pointing_left(&chevron_points(p), &cell(p)));
}

/// U+E0D7: the cell with ▶ cut out of it
fn notch_right(g: &mut Draw) {
    let p = g.p;
    g.poly(&pointing_left(&notch_points(p), &cell(p)));
}

/// U+E0D6: the cell with ◀ cut out of it
fn notch_left(g: &mut Draw) {
    let p = g.p;
    g.poly(&notch_points(p));
}

/// Half of the typeface's superellipse, from the lower left corner of `c` round by the middle of its right edge
/// to the upper left corner, drawn `inset` inside it.
fn half_round(c: &Cell, inset: f64, k: f64) -> (Seg, Seg) {
    let (bottom, tip, top) = (pt(c.x0, c.y0 + inset), pt(c.x1 - inset, c.cy), pt(c.x0, c.y1 - inset));
    let (rx, ry) = (tip.x - c.x0, c.cy - bottom.y);
    (
        Seg::Cubic(bottom, bottom + pt(k * rx, 0.0), tip - pt(0.0, k * ry), tip),
        Seg::Cubic(tip, tip + pt(0.0, k * ry), top + pt(k * rx, 0.0), top),
    )
}

/// The half round of U+E0B4 to U+E0B7: its flat side `block_over` past the cell's left edge, its ends as far
/// past the top and bottom, its round side touching the right edge.
pub fn round_contour(p: &Params, outline: bool, left: bool) -> Contour {
    let c = cell(p);
    let o = block_over(p);
    let reach = Cell { x0: c.x0 - o, y0: c.y0 - o, x1: c.x1, y1: c.y1 + o, cx: c.cx, cy: c.cy };
    let (a, b) = half_round(&reach, 0.0, p.sq);
    let segs = if outline {
        let (e, f) = half_round(&reach, light(p), p.sq);
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

/// The triangle below the cell's falling diagonal (◣, U+E0B8): its long side runs through the upper left and the
/// lower right corners and on past them, and its two short sides lie `block_over` outside the cell.
pub fn corner_points(p: &Params) -> Vec<V> {
    let c = cell(p);
    let o = block_over(p);
    let (a, b) = (pt(c.x0, c.y1), pt(c.x1, c.y0));
    vec![pt(c.x0 - o, c.y0 - o), at_height(a, b, c.y0 - o), at_x(a, b, c.x0 - o)]
}

/// U+E0B8 to U+E0BE: the four triangles that halve the cell along a diagonal, by the corner they fill.
fn corner_triangle(g: &mut Draw, right: bool, upper: bool) {
    let p = g.p;
    let c = cell(p);
    let mut points = corner_points(p);
    if right {
        points = pointing_left(&points, &c);
    }
    if upper {
        points = upside_down(&points, &c);
    }
    g.poly(&points);
}

/// U+E0D2: the cell less a light line along its middle and a triangle pointing from its right edge to the
/// middle: two trapezoids. Ghostty draws it so.
fn trapezoids(g: &mut Draw, left: bool) {
    let p = g.p;
    let c = cell(p);
    let o = block_over(p);
    let gap = light(p) / 2.0;
    let (corner, inner) = (pt(c.x1, c.y1), pt(c.cx, c.cy + gap));
    let top = vec![pt(c.x0 - o, c.y1 + o), at_height(corner, inner, c.y1 + o), inner, pt(c.x0 - o, c.cy + gap)];
    for mut points in [top.clone(), upside_down(&top, &c)] {
        if left {
            points = pointing_left(&points, &c);
        }
        g.poly(&points);
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Powerline: the status-line icons
//
// These stand beside text, so they are drawn as signs are: on the text's heights, with the operators' stroke,
// which grows with the weight.

/// U+E0A0 branch: a stem, a commit on the right, and the branch that leaves the stem for it.
fn branch(g: &mut Draw) {
    let p = g.p;
    let (xs, xb) = (p.mid() - 0.22 * p.width, p.mid() + 0.22 * p.width);
    let (bottom, top) = (0.6 * p.desc, p.cap);
    let r = 1.5 * p.dot;
    g.stroke(&[knot(xs, bottom, p.op).line(), knot(xs, top, p.op)]);
    g.dot(xb, top - r, r);
    g.stroke(&[knot(xb, top - r, p.op).dir(-90.0), knot(xs, 0.3 * p.cap, p.op).dir(-90.0)]);
}

/// The small capitals of U+E0A1 and U+E0A3: the master at `SMALL` of its size, with strokes a little lighter
/// than its capitals' so that they read beside them.
const SMALL: f64 = 0.52;

fn small_caps(p: &Params) -> Params {
    let mut q = p.scaled(SMALL);
    q.stem = 0.7 * p.stem;
    q.hair = 0.7 * p.hair;
    q.cap_stem = 0.7 * p.cap_stem;
    q.cap_hair = 0.7 * p.cap_hair;
    q
}

/// U+E0A1 (LN, line number) and U+E0A3 (CN, column number): two small capitals, one above the other, the upper
/// one's top at the capitals' height.
fn stacked(g: &mut Draw, upper: char, lower: char) {
    let p = g.p;
    let q = small_caps(p);
    let dx = (p.width - q.width) / 2.0;
    let gap = 0.13 * p.cap;
    let y_upper = p.cap - q.cap;
    g.draw_as(&name_of(upper), &q, dx, y_upper);
    g.draw_as(&name_of(lower), &q, dx, y_upper - gap - q.cap);
}

/// U+E0A2 padlock: a shackle over a solid body with a keyhole.
fn padlock(g: &mut Draw) {
    let p = g.p;
    // the body keeps its width in every weight, so that the Bold's shackle keeps a counter
    let (x0, x1) = (p.op_l + 0.05 * p.width, p.op_r() - 0.05 * p.width);
    let (y0, y1) = (0.4 * p.desc, 0.78 * p.xh);
    g.rect(x0, y0, x1, y1);
    let hole = superellipse(p.mid(), (y0 + y1) / 2.0, 0.55 * p.op, 1.2 * p.op, p.dot_k);
    g.add(hole.reversed());
    // the shackle, a little lighter than the body's edges: its legs stand on the body 27% of the way in
    let w = 0.85 * p.op;
    let (xa, xb) = (x0 + 0.27 * (x1 - x0), x1 - 0.27 * (x1 - x0));
    let r = (xb - xa) / 2.0;
    let top = p.cap + p.over - w / 2.0;
    g.stroke(&[
        knot(xa, y1, w).line(),
        knot(xa, top - r, w).dir(90.0).k(p.sq),
        knot(p.mid(), top, w).dir(0.0).k(p.sq),
        knot(xb, top - r, w).dir(-90.0).line(),
        knot(xb, y1, w),
    ]);
}

// ---------------------------------------------------------------------------------------------------------------
// Branch drawing (U+F5D0 to U+F60D)
//
// The symbols kitty draws for git graphs (kitty PR 7681): light lines, rounded corners and commit nodes. They
// join the light box-drawing lines: the same thickness, centre lines, overshoot and rounded corner. A symbol is
// its straight lines (h, v), its corners (each by the two arms it joins) and, for a node, a dot or a ring and the
// arms that leave it.

/// The arms of a rounded corner: which way it runs across (right?) and up or down (up?).
#[derive(Clone, Copy)]
struct Corner {
    right: bool,
    up: bool,
}

const BR: Corner = Corner { right: true, up: false }; // ╭
const BL: Corner = Corner { right: false, up: false }; // ╮
const TR: Corner = Corner { right: true, up: true }; // ╰
const TL: Corner = Corner { right: false, up: true }; // ╯

/// code point, horizontal line, vertical line, corners. The names call a corner by the sides its arms go to:
/// arc(br), bottom and right, is ╭ (BR here), arc(tl) is ╯; kitty's `decorations.c` draws the same sets.
const BRANCHES: [(u32, bool, bool, &[Corner]); 20] = [
    (0xF5DA, false, true, &[TR]),
    (0xF5DB, false, true, &[BR]),
    (0xF5DC, false, false, &[TR, BR]),
    (0xF5DD, false, true, &[TL]),
    (0xF5DE, false, true, &[BL]),
    (0xF5DF, false, false, &[TL, BL]),
    (0xF5E0, true, false, &[BL]),
    (0xF5E1, true, false, &[BR]),
    (0xF5E2, false, false, &[BR, BL]),
    (0xF5E3, true, false, &[TL]),
    (0xF5E4, true, false, &[TR]),
    (0xF5E5, false, false, &[TR, TL]),
    (0xF5E6, false, true, &[TL, TR]),
    (0xF5E7, false, true, &[BL, BR]),
    (0xF5E8, true, false, &[BL, TL]),
    (0xF5E9, true, false, &[TR, BR]),
    (0xF5EA, false, true, &[TL, BR]),
    (0xF5EB, false, true, &[TR, BL]),
    (0xF5EC, true, false, &[TL, BR]),
    (0xF5ED, true, false, &[TR, BL]),
];

/// Lines, corners: draw the straight parts as the union of rectangles, and each corner's quarter turn as a
/// stroke that starts and ends on them.
fn branches(g: &mut Draw, h: bool, v: bool, corners: &[Corner]) {
    let p = g.p;
    let c = cell(p);
    let (t, r) = (light(p), arc_radius(p));
    let (ox, oy) = (over_x(p), over_y(p));
    let mut rects: Vec<Rect> = Vec::new();
    if h {
        rects.push((c.x0 - ox, c.cy - t / 2.0, c.x1 + ox, c.cy + t / 2.0));
    }
    if v {
        rects.push((c.cx - t / 2.0, c.y0 - oy, c.cx + t / 2.0, c.y1 + oy));
    }
    for k in corners {
        if !h {
            let (xa, xb) = if k.right { (c.cx + r, c.x1 + ox) } else { (c.x0 - ox, c.cx - r) };
            rects.push((xa, c.cy - t / 2.0, xb, c.cy + t / 2.0));
        }
        if !v {
            let (ya, yb) = if k.up { (c.cy + r, c.y1 + oy) } else { (c.y0 - oy, c.cy - r) };
            rects.push((c.cx - t / 2.0, ya, c.cx + t / 2.0, yb));
        }
    }
    fill(g, &rects);
    for k in corners {
        let mut knots = turn_knots(p);
        if !k.right {
            knots = mirror(&knots, c.cx);
        }
        if k.up {
            knots = flip(&knots, c.cy);
        }
        g.stroke(&knots);
    }
}

/// U+F5D2 to U+F5D5: a light line that breaks into dashes growing shorter towards one side of the cell, as kitty
/// draws it: n dashes at a pitch of 1/n of the cell, the k-th (from 0) (n − k)/(n + 1) of the pitch long. The
/// first starts past the edge it fades from, as a line does.
fn fading(g: &mut Draw, n: usize, horizontal: bool, towards_end: bool) {
    let p = g.p;
    let c = cell(p);
    let t = light(p);
    let (len, over) = if horizontal { (c.w(), over_x(p)) } else { (c.h(), over_y(p)) };
    let pitch = len / n as f64;
    for k in 0..n {
        let kf = k as f64;
        let (mut a, b) = (kf * pitch, kf * pitch + pitch * (n as f64 - kf) / (n as f64 + 1.0));
        if k == 0 {
            a -= over;
        }
        // distances from the edge the line fades from: the left, or the top
        let (a, b) = if towards_end { (a, b) } else { (len - b, len - a) };
        if horizontal {
            g.rect(c.x0 + a, c.cy - t / 2.0, c.x0 + b, c.cy + t / 2.0);
        } else {
            g.rect(c.cx - t / 2.0, c.y1 - b, c.cx + t / 2.0, c.y1 - a);
        }
    }
}

/// The radius of a commit node, as a fraction of the cell's width: a ring that leaves a fifth of the cell clear
/// beside it.
const NODE: f64 = 0.4;

/// U+F5EE to U+F60D: a commit node, filled or hollow, with light lines from it to the given sides of the cell.
/// A line stops just inside the node's edge, so that it meets the round without a notch.
fn node(g: &mut Draw, solid: bool, sides: &str) {
    let p = g.p;
    let c = cell(p);
    let t = light(p);
    let r = NODE * c.w();
    let (ox, oy) = (over_x(p), over_y(p));
    let stop = r - t / 4.0;
    let mut rects: Vec<Rect> = Vec::new();
    for side in sides.chars() {
        rects.push(match side {
            'l' => (c.x0 - ox, c.cy - t / 2.0, c.cx - stop, c.cy + t / 2.0),
            'r' => (c.cx + stop, c.cy - t / 2.0, c.x1 + ox, c.cy + t / 2.0),
            'u' => (c.cx - t / 2.0, c.cy + stop, c.cx + t / 2.0, c.y1 + oy),
            _ => (c.cx - t / 2.0, c.y0 - oy, c.cx + t / 2.0, c.cy - stop),
        });
    }
    fill(g, &rects);
    g.dot_xy(c.cx, c.cy, r, r, p.dot_k);
    if !solid {
        let inner = superellipse(c.cx, c.cy, r - t, r - t, p.dot_k);
        g.add(inner.reversed());
    }
}

/// The sides a node's lines go to, for each pair of code points (filled, then hollow) from U+F5EE.
const NODES: [&str; 16] =
    ["", "r", "l", "lr", "d", "u", "ud", "rd", "ld", "ur", "ul", "udr", "udl", "dlr", "ulr", "udlr"];

// ---------------------------------------------------------------------------------------------------------------
// Progress indicators (U+EE00 to U+EE0B, from Fira Code)
//
// A progress bar is a frame of light lines a little taller than the capitals, centred on the operators' axis, in
// three parts: a left end, a middle that repeats, and a right end. Filled, the frame holds a bar that runs on
// into the next cell. The spinner is six frames of an arc turning round a circle of the operators' span.

/// The bottom and the top of the progress bar's frame.
fn bar_band(p: &Params) -> (f64, f64) {
    let half = 0.42 * p.cap;
    (p.axis - half, p.axis + half)
}

/// The clear space between the frame and the bar inside it.
fn bar_gap(p: &Params) -> f64 {
    1.5 * light(p)
}

/// One part of the bar, drawn as the left end (`end` < 0), the middle (0) or the right end (> 0).
fn progress(g: &mut Draw, end: i32, filled: bool) {
    let p = g.p;
    let c = cell(p);
    let (t, ox, gap) = (light(p), over_x(p), bar_gap(p));
    let (y0, y1) = (bar_band(p).0, bar_band(p).1);
    let (mut x0, mut x1) = (c.x0 - ox, c.x1 + ox);
    let mut rects: Vec<Rect> = Vec::new();
    if end < 0 {
        x0 = p.op_l;
        rects.push((x0, y0, x0 + t, y1));
    }
    if end > 0 {
        x1 = p.op_r();
        rects.push((x1 - t, y0, x1, y1));
    }
    rects.push((x0, y0, x1, y0 + t));
    rects.push((x0, y1 - t, x1, y1));
    fill(g, &rects);
    if filled {
        let a = if end < 0 { x0 + t + gap } else { x0 };
        let b = if end > 0 { x1 - t - gap } else { x1 };
        g.rect(a, y0 + t + gap, b, y1 - t - gap);
    }
}

/// The spinner's frames, as the arc each draws: from and to, in degrees counter-clockwise from the right. They
/// are kitty's, which measures clockwise with y down.
const SPINNER: [(f64, f64); 6] =
    [(55.0, 125.0), (-30.0, 90.0), (-110.0, 45.0), (-180.0, 0.0), (140.0, 280.0), (90.0, 190.0)];

fn spinner(g: &mut Draw, from: f64, to: f64) {
    let p = g.p;
    let t = light(p);
    let r = (p.op_r() - p.op_l - t) / 2.0;
    let centre = pt(p.mid(), p.axis);
    let pieces = ((to - from) / 90.0).ceil() as usize;
    let knots: Vec<Knot> = (0..=pieces)
        .map(|k| {
            let a = from + (to - from) * k as f64 / pieces as f64;
            let z = centre + V::unit(a) * r;
            knot(z.x, z.y, t).dir(a + 90.0)
        })
        .collect();
    g.stroke(&knots);
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
    // Powerline
    reg.code(0xE0A0, Opt::UPRIGHT, branch);
    reg.code(0xE0A1, Opt::UPRIGHT, |g: &mut Draw| stacked(g, 'L', 'N'));
    reg.code(0xE0A2, Opt::UPRIGHT, padlock);
    reg.code(0xE0A3, Opt::UPRIGHT, |g: &mut Draw| stacked(g, 'C', 'N'));
    reg.code(0xE0B0, Opt::UPRIGHT, arrow_right);
    reg.code(0xE0B1, Opt::UPRIGHT, chevron_right);
    reg.code(0xE0B2, Opt::UPRIGHT, arrow_left);
    reg.code(0xE0B3, Opt::UPRIGHT, chevron_left);
    for (cp, outline, left) in
        [(0xE0B4, false, false), (0xE0B5, true, false), (0xE0B6, false, true), (0xE0B7, true, true)]
    {
        reg.code(cp, Opt::UPRIGHT, move |g: &mut Draw| round(g, outline, left));
    }
    for (cp, right, upper) in
        [(0xE0B8, false, false), (0xE0BA, true, false), (0xE0BC, false, true), (0xE0BE, true, true)]
    {
        reg.code(cp, Opt::UPRIGHT, move |g: &mut Draw| corner_triangle(g, right, upper));
    }
    // the line separators are the box-drawing diagonals: E0B9 and E0BF the falling one, E0BB and E0BD the rising
    for (cp, line) in [(0xE0B9, '╲'), (0xE0BB, '╱'), (0xE0BD, '╱'), (0xE0BF, '╲')] {
        reg.code(cp, Opt::UPRIGHT, move |g: &mut Draw| g.same_as_char(line));
    }
    reg.code(0xE0D2, Opt::UPRIGHT, |g: &mut Draw| trapezoids(g, false));
    reg.code(0xE0D4, Opt::UPRIGHT, |g: &mut Draw| trapezoids(g, true));
    reg.code(0xE0D6, Opt::UPRIGHT, notch_left);
    reg.code(0xE0D7, Opt::UPRIGHT, notch_right);
    // progress indicators
    for (k, (end, filled)) in
        [(-1, false), (0, false), (1, false), (-1, true), (0, true), (1, true)].into_iter().enumerate()
    {
        reg.code(0xEE00 + k as u32, Opt::UPRIGHT, move |g: &mut Draw| progress(g, end, filled));
    }
    for (k, (from, to)) in SPINNER.into_iter().enumerate() {
        reg.code(0xEE06 + k as u32, Opt::UPRIGHT, move |g: &mut Draw| spinner(g, from, to));
    }
    // branch drawing
    reg.code(0xF5D0, Opt::UPRIGHT, |g: &mut Draw| g.same_as_char('─'));
    reg.code(0xF5D1, Opt::UPRIGHT, |g: &mut Draw| g.same_as_char('│'));
    for (k, (n, horizontal, towards_end)) in
        [(4, true, true), (4, true, false), (5, false, true), (5, false, false)].into_iter().enumerate()
    {
        reg.code(0xF5D2 + k as u32, Opt::UPRIGHT, move |g: &mut Draw| fading(g, n, horizontal, towards_end));
    }
    for (k, corner) in ['╭', '╮', '╰', '╯'].into_iter().enumerate() {
        reg.code(0xF5D6 + k as u32, Opt::UPRIGHT, move |g: &mut Draw| g.same_as_char(corner));
    }
    for (cp, h, v, corners) in BRANCHES {
        reg.code(cp, Opt::UPRIGHT, move |g: &mut Draw| branches(g, h, v, corners));
    }
    for (k, sides) in NODES.into_iter().enumerate() {
        for (j, solid) in [true, false].into_iter().enumerate() {
            reg.code(0xF5EE + 2 * k as u32 + j as u32, Opt::UPRIGHT, move |g: &mut Draw| node(g, solid, sides));
        }
    }
}
