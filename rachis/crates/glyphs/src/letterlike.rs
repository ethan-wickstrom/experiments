//! Letterlike symbols: the double-struck letters and figures of mathematics, ℓ, ℏ, ℵ, the Fraktur ℑ and ℜ, ℘,
//! and the signs that are letters turned, circled or struck.
//!
//! A double-struck letter is the plain letter with one of its strokes doubled: two thin strokes `thin(p)` wide
//! with `gap(p)` of white between them, joined at their ends. It is not redrawn: the program takes the plain
//! letter as the master draws it (its skeletons, and the polygons and dots it adds), replaces the one stroke and
//! draws the rest as they are, so that ℝ stays R's sibling whatever R becomes. The doubled stroke is
//!
//! - a straight stem (B D E F H K L M N P R, b d h k m n p q r u): the thin stroke keeps the stem's edge on the
//!   counter's side and the second one stands outside it, so the letter grows by the doubling (`grow`);
//! - a centred stem (I T, i j l t): the pair is centred on it;
//! - a round side (C G O Q S U J, c e o s, the figures): the thin stroke keeps the outer edge and the second
//!   one stands inside, as a straight line that runs to the strokes above and below it;
//! - a straight diagonal (X Z, x y z w, 7): the pair keeps the diagonal's outer corners;
//! - the left stroke of a V or of an A drawn as one polygon (A V Y, v, γ).
//!
//! The thin stroke grows with weight more slowly than the stems (`operators::fine`), so that the white between
//! the two stays open in the Bold at 13 px.

use rachis_kernel::geom::{flatten, intersect};
use rachis_kernel::params::SLANT;
use rachis_kernel::pen::{expand, sheared, skeleton};
use rachis_kernel::{Contour, Draw, Knot, Params, Registry, V, knot, name_of, pt};

use crate::lower::bar;
use crate::operators::fine;
use crate::parts::{cut, hbar, ring, vstem};

// ---------------------------------------------------------------------------------------------------------------
// Measurements this group derives from the parameters.

/// The breadth of each of the two thin strokes of a doubled stroke.
pub fn thin(p: &Params) -> f64 {
    fine(p)
}

/// The white between them. A doubled stroke is read by its white: at 14 px a white as broad as one of the
/// strokes blurs shut and the letter reads as a bold one, so the white is nearly twice a stroke. In the
/// fixed-pitch family the letter has to make room for it inside the cell: there the white is as broad as the
/// Bold's m and w can spare, at every weight. (Thinner strokes around a broader white were tried there and
/// measured worse at the gate's blur: decision T28.)
pub fn gap(p: &Params) -> f64 {
    if p.mono { 82.0 } else { 1.8 * fine(p) }
}

/// How much wider a doubled stroke is than the stroke `s` it replaces.
fn growth(p: &Params, s: f64) -> f64 {
    2.0 * thin(p) + gap(p) - s
}

/// The slope of the slanted forms (ℎ ℏ ℓ ⅅ 𝚤): the italic's, in the upright face as in the italic one.
fn slope() -> f64 {
    SLANT.to_radians().tan()
}

/// The master `p` slanted as the italic is.
fn slanted(p: &Params) -> Params {
    Params { slant: SLANT, ..p.clone() }
}

// ---------------------------------------------------------------------------------------------------------------
// The plain letter, taken apart.

/// Which edge of a stroke a doubling keeps.
#[derive(Clone, Copy, PartialEq, Debug)]
enum Keep {
    /// The left edge; the second stroke stands to its right.
    Left,
    /// The right edge; the second stroke stands to its left.
    Right,
    /// Neither: the pair is centred on the stroke.
    Centre,
}

/// How far the second stroke of a doubled side runs.
#[derive(Clone, Copy, PartialEq, Debug)]
enum Reach {
    /// To the nearest strokes it meets above and below the side's middle, or to the side's own ends.
    Nearest,
    /// To the furthest strokes it meets, crossing any between.
    Outer,
    /// To the side's own ends, closed there by short bars.
    Ends,
}

/// Which way a letter grows when one of its stems is doubled outwards.
#[derive(Clone, Copy, PartialEq, Debug)]
enum Grow {
    None,
    Left,
    Right,
}

/// A plain letter as the master draws it, in upright coordinates: its strokes, and the contours it adds that
/// are not strokes (polygons and dots, already slanted).
struct Plain {
    strokes: Vec<(Vec<Knot>, bool)>,
    rest: Vec<Contour>,
    advance: f64,
    /// The extra strokes and polygons the doubling adds.
    more: Vec<(Vec<Knot>, bool)>,
    polys: Vec<Vec<V>>,
    /// How far everything moves right in the cell.
    dx: f64,
    errors: Vec<String>,
}

fn same_contour(a: &Contour, b: &Contour) -> bool {
    let (pa, pb) = (a.points(), b.points());
    pa.len() == pb.len() && pa.iter().zip(&pb).all(|(u, v)| (*u - *v).abs() < 1e-6)
}

impl Plain {
    /// The glyph `name` as the master draws it in a cell made narrower or wider for a doubling that adds `grow`
    /// to its width on the side `dir`. In the fixed-pitch family the cell is fixed: the letter is drawn half the
    /// growth narrower and placed so that the doubled letter is centred. In the proportional family it keeps its
    /// own width and the advance grows.
    fn of(g: &Draw, name: &str, dir: Grow, grow: f64) -> Plain {
        let p = g.p;
        let grow = if dir == Grow::None { 0.0 } else { grow };
        let width = if p.mono { p.width - grow / 2.0 } else { p.width };
        let q = Params { width, ..p.clone() };
        let mut out = Plain {
            strokes: Vec::new(),
            rest: Vec::new(),
            advance: p.width,
            more: vec![],
            polys: vec![],
            dx: 0.0,
            errors: vec![],
        };
        let Some(glyph) = g.glyph_as(name, &q) else {
            out.errors.push(format!("no glyph {name:?} to double"));
            return out;
        };
        let (s, o) = (p.slant.to_radians().tan(), p.slant_origin());
        let mut drawn = Vec::new();
        for (knots, closed) in &glyph.skeletons {
            if let Ok(cs) = expand(knots, *closed) {
                drawn.extend(cs);
            }
            out.strokes.push((knots.iter().map(|k| sheared(k, -s, o)).collect(), *closed));
        }
        out.rest = glyph.contours.into_iter().filter(|c| !drawn.iter().any(|d| same_contour(c, d))).collect();
        out.errors.extend(glyph.errors);
        if p.mono {
            out.dx = match dir {
                Grow::Left => 0.75 * grow,
                Grow::Right => -0.25 * grow,
                Grow::None => 0.0,
            };
        } else {
            out.advance = glyph.advance + grow;
            out.dx = if dir == Grow::Left { grow } else { 0.0 };
        }
        out
    }

    /// The index of the straight vertical stroke furthest to the left (`left`) or the right, among those at
    /// least half as tall as the tallest.
    fn stem(&self, left: bool) -> Option<usize> {
        let is_stem =
            |ks: &[Knot]| ks.len() == 2 && ks[0].pen == Some(0.0) && (ks[0].z.x - ks[1].z.x).abs() < 0.01 && ks[0].line;
        let height = |ks: &[Knot]| (ks[1].z.y - ks[0].z.y).abs();
        let tallest = self.strokes.iter().filter(|(ks, _)| is_stem(ks)).map(|(ks, _)| height(ks)).fold(0.0, f64::max);
        let mut best: Option<(usize, f64)> = None;
        for (i, (ks, _)) in self.strokes.iter().enumerate() {
            if !is_stem(ks) || height(ks) < 0.5 * tallest {
                continue;
            }
            let x = if left { ks[0].z.x } else { -ks[0].z.x };
            if best.is_none_or(|(_, b)| x < b - 0.5) {
                best = Some((i, x));
            }
        }
        best.map(|(i, _)| i)
    }

    /// The index of the stroke that has the vertical knot furthest out on the left (`left`) or the right.
    fn round(&self, left: bool) -> Option<usize> {
        let mut best: Option<(usize, f64)> = None;
        for (i, (ks, _)) in self.strokes.iter().enumerate() {
            for (j, _) in ks.iter().enumerate() {
                if !vertical(ks, j) {
                    continue;
                }
                let e = edge(&ks[j], left);
                let e = if left { e } else { -e };
                if best.is_none_or(|(_, b)| e < b - 0.5) {
                    best = Some((i, e));
                }
            }
        }
        best.map(|(i, _)| i)
    }

    /// Double the side of the stroke `i` that faces left (`left`) or right: the vertical knots that reach
    /// furthest out on that side become thin, keeping their `keep` edge, and a second thin stroke stands beside
    /// them.
    fn side(&mut self, p: &Params, i: usize, left: bool, keep: Keep, reach: Reach) {
        let (t, w) = (thin(p), gap(p));
        let ks = &self.strokes[i].0;
        let js: Vec<usize> = (0..ks.len()).filter(|&j| vertical(ks, j)).collect();
        let far = js.iter().map(|&j| edge(&ks[j], left)).fold(
            if left { f64::INFINITY } else { f64::NEG_INFINITY },
            |a, b| {
                if left { a.min(b) } else { a.max(b) }
            },
        );
        let js: Vec<usize> = js.into_iter().filter(|&j| (edge(&ks[j], left) - far).abs() < 1.0).collect();
        if js.is_empty() {
            self.errors.push("no side to double".into());
            return;
        }
        let (lo_e, hi_e) = (
            js.iter().map(|&j| ks[j].z.x - ks[j].w / 2.0).fold(f64::INFINITY, f64::min),
            js.iter().map(|&j| ks[j].z.x + ks[j].w / 2.0).fold(f64::NEG_INFINITY, f64::max),
        );
        let (x1, x2) = match keep {
            Keep::Left => (lo_e + t / 2.0, lo_e + 1.5 * t + w),
            Keep::Right => (hi_e - t / 2.0, hi_e - 1.5 * t - w),
            Keep::Centre => {
                let c = (lo_e + hi_e) / 2.0;
                (c - (t + w) / 2.0, c + (t + w) / 2.0)
            }
        };
        let ys: Vec<f64> = js.iter().map(|&j| ks[j].z.y).collect();
        let (y_lo, y_hi) =
            (ys.iter().copied().fold(f64::INFINITY, f64::min), ys.iter().copied().fold(f64::NEG_INFINITY, f64::max));
        for &j in &js {
            let k = &mut self.strokes[i].0[j];
            k.z = pt(x1, k.z.y);
            k.w = t;
        }
        let ym = (y_lo + y_hi) / 2.0;
        let cross = if reach == Reach::Ends { vec![] } else { crossings(&self.strokes, x2) };
        let above: Vec<f64> = cross.iter().copied().filter(|&y| y > ym).collect();
        let below: Vec<f64> = cross.iter().copied().filter(|&y| y < ym).collect();
        let pick_hi = |v: &[f64]| match reach {
            Reach::Outer => v.iter().copied().fold(f64::NEG_INFINITY, f64::max),
            _ => v.iter().copied().fold(f64::INFINITY, f64::min),
        };
        let pick_lo = |v: &[f64]| match reach {
            Reach::Outer => v.iter().copied().fold(f64::INFINITY, f64::min),
            _ => v.iter().copied().fold(f64::NEG_INFINITY, f64::max),
        };
        let (a, b) = (x1.min(x2) - t / 2.0, x1.max(x2) + t / 2.0);
        let top = if above.is_empty() {
            self.more.push((hbar(a, b, y_hi - t / 2.0, t), false));
            y_hi
        } else {
            pick_hi(&above)
        };
        let bot = if below.is_empty() {
            self.more.push((hbar(a, b, y_lo + t / 2.0, t), false));
            y_lo
        } else {
            pick_lo(&below)
        };
        self.more.push((vstem(x2, bot, top, t), false));
    }

    /// Double the stroke `i` when it is a straight stem.
    fn double_stem(&mut self, p: &Params, i: usize, keep: Keep, reach: Reach) {
        self.side(p, i, true, keep, reach);
    }

    /// The index of the straight diagonal stroke that runs down to the right (`down_right`) or up to the right.
    fn diagonal(&self, down_right: bool) -> Option<usize> {
        self.strokes.iter().position(|(ks, _)| {
            ks.len() == 2
                && ks[0].pen.is_some_and(|a| a.abs() < 0.01)
                && ks[1].pen.is_some_and(|a| a.abs() < 0.01)
                && (ks[1].z.y - ks[0].z.y).abs() > 1.0
                && (ks[1].z.x - ks[0].z.x).abs() > 1.0
                && (((ks[1].z.x - ks[0].z.x) * (ks[1].z.y - ks[0].z.y)) < 0.0) == down_right
        })
    }

    /// Double the straight diagonal stroke `i`. At each end the pair keeps the stroke's outer corner (the corner
    /// away from the other end) when `fa` (at the first end) or `fb` (at the second) is 1, and is centred on the
    /// stroke when it is 0; it is closed there by a bar.
    fn double_diagonal(&mut self, p: &Params, i: usize, fa: f64, fb: f64) {
        let (t, w) = (thin(p), gap(p));
        let lean = p.slant.to_radians().tan();
        let total = 2.0 * t + w;
        let ks = self.strokes[i].0.clone();
        let (a, b) = (ks[0], ks[1]);
        let sa = if a.z.x < b.z.x { -1.0 } else { 1.0 };
        let (ea, eb) = (a.z.x + sa * a.w / 2.0, b.z.x - sa * b.w / 2.0);
        let dy = b.z.y - a.z.y;
        let mut h = total;
        let ends =
            |h: f64| (fa * (ea - sa * h / 2.0) + (1.0 - fa) * a.z.x, fb * (eb + sa * h / 2.0) + (1.0 - fb) * b.z.x);
        for _ in 0..16 {
            let (ca, cb) = ends(h);
            let dx = cb - ca + lean * dy;
            h = total * dx.hypot(dy) / dy.abs();
        }
        let (ca, cb) = ends(h);
        let ht = h * t / total; // the horizontal cut of one thin stroke
        let off = (h - ht) / 2.0;
        self.strokes.remove(i);
        for s in [-1.0, 1.0] {
            self.more.push((
                vec![knot(ca + s * off, a.z.y, ht).pen(0.0).line(), knot(cb + s * off, b.z.y, ht).pen(0.0)],
                false,
            ));
        }
        let up = if dy > 0.0 { 1.0 } else { -1.0 };
        self.more.push((hbar(ca - h / 2.0, ca + h / 2.0, a.z.y + up * t / 2.0, t), false));
        self.more.push((hbar(cb - h / 2.0, cb + h / 2.0, b.z.y - up * t / 2.0, t), false));
    }

    /// Double the left stroke of the V (or caret) that the letter draws as one polygon of seven points. A bar
    /// whose end lay in that stroke is moved to the inner of the two thin strokes.
    fn double_vee(&mut self, p: &Params) {
        let (t, w) = (thin(p), gap(p));
        let (s, o) = (p.slant.to_radians().tan(), p.slant_origin());
        let Some(k) = self.rest.iter().position(|c| c.segs.len() == 7 && c.segs.iter().all(|sg| sg.is_line())) else {
            self.errors.push("no V to double".into());
            return;
        };
        let pts = self.rest.remove(k).points();
        // the outer line holds four of the points, the vertex two, the crotch one
        let ys: Vec<f64> = pts.iter().map(|z| z.y).collect();
        let count = |y: f64| ys.iter().filter(|&&v| (v - y).abs() < 0.01).count();
        let y_o = ys.iter().copied().find(|&y| count(y) == 4).unwrap_or(0.0);
        let y_v = ys.iter().copied().find(|&y| count(y) == 2).unwrap_or(0.0);
        let mut outer: Vec<V> = pts.iter().copied().filter(|z| (z.y - y_o).abs() < 0.01).collect();
        let mut vertex: Vec<V> = pts.iter().copied().filter(|z| (z.y - y_v).abs() < 0.01).collect();
        let Some(crotch) = pts.iter().copied().find(|z| (z.y - y_o).abs() >= 0.01 && (z.y - y_v).abs() >= 0.01) else {
            self.errors.push("the V has no crotch".into());
            return;
        };
        outer.sort_by(|a, b| a.x.total_cmp(&b.x));
        vertex.sort_by(|a, b| a.x.total_cmp(&b.x));
        let (tl, tr_in, tr) = (outer[0], outer[2], outer[3]);
        let (vl, vr) = (vertex[0], vertex[1]);
        let at = |a: V, b: V, y: f64| intersect(a, b - a, pt(0.0, y), pt(1.0, 0.0)).unwrap_or(a);
        // the right stroke on its own
        let x_in = at(tr_in, crotch, y_v);
        self.polys.push(vec![tr, tr_in, x_in, vr]);
        // the left stroke's outer edge, and the unit normal into the letter
        let d = (vl - tl).norm();
        let n = if d.left().x > 0.0 { d.left() } else { d.right() };
        let edge_at = |off: f64, y: f64| at(tl + n * off, tl + n * off + d, y);
        let (o1, o2, o3) = (t, t + w, 2.0 * t + w);
        self.polys.push(vec![edge_at(0.0, y_o), edge_at(o1, y_o), edge_at(o1, y_v), edge_at(0.0, y_v)]);
        // the inner thin stroke runs into the right stroke and ends on its outer edge
        let on_right = |off: f64| intersect(tl + n * off, d, tr, vr - tr).unwrap_or(edge_at(off, y_v));
        self.polys.push(vec![edge_at(o2, y_o), edge_at(o3, y_o), on_right(o3), on_right(o2)]);
        let y_j = if y_o > y_v { y_o - t } else { y_o + t };
        self.polys.push(vec![edge_at(0.0, y_o), edge_at(o3, y_o), edge_at(o3, y_j), edge_at(0.0, y_j)]);
        // bars that ended in the stroke end on the inner thin stroke's centre line (upright coordinates)
        for (ks, _) in &mut self.strokes {
            if ks.len() != 2 || ks[0].pen != Some(90.0) || (ks[0].z.y - ks[1].z.y).abs() > 0.01 {
                continue;
            }
            let y = ks[0].z.y;
            let sx = s * (y - o);
            let (l0, l3) = (edge_at(0.0, y).x - sx, edge_at(o3, y).x - sx);
            for k in ks.iter_mut() {
                if k.z.x > l0 - 1.0 && k.z.x < l3 + 1.0 {
                    k.z = pt(edge_at((o2 + o3) / 2.0, y).x - sx, y);
                }
            }
        }
    }

    fn draw(self, g: &mut Draw) {
        let from = g.glyph.contours.len();
        let dx = self.dx;
        let moved = |ks: &[Knot]| ks.iter().map(|k| Knot { z: k.z + pt(dx, 0.0), ..*k }).collect::<Vec<_>>();
        for (ks, closed) in self.strokes.iter().chain(&self.more) {
            if *closed {
                g.stroke_closed(&moved(ks));
            } else {
                g.stroke(&moved(ks));
            }
        }
        for c in self.rest {
            g.add_upright(c.mapped(|z| z + pt(dx, 0.0)));
        }
        for poly in self.polys {
            g.add_upright(rachis_kernel::pen::polygon(&poly.iter().map(|z| *z + pt(dx, 0.0)).collect::<Vec<_>>()));
        }
        g.glyph.advance = self.advance;
        g.glyph.errors.extend(self.errors);
        keep_inside(g, from);
    }
}

/// Whether the knot `j` of a stroke travels vertically: a curve's knot whose direction is vertical, or the end
/// of a straight vertical segment held by a horizontal pen.
fn vertical(ks: &[Knot], j: usize) -> bool {
    let k = &ks[j];
    if k.dir.is_some_and(|d| (d.abs() - 90.0).abs() < 0.01 || (d.abs() - 270.0).abs() < 0.01) {
        return true;
    }
    let straight = |a: &Knot, b: &Knot| a.line && (a.z.x - b.z.x).abs() < 0.01;
    k.pen == Some(0.0) && ((j + 1 < ks.len() && straight(k, &ks[j + 1])) || (j > 0 && straight(&ks[j - 1], k)))
}

/// The outer edge of a vertical knot on the left (`left`) or the right.
fn edge(k: &Knot, left: bool) -> f64 {
    if left { k.z.x - k.w / 2.0 } else { k.z.x + k.w / 2.0 }
}

/// The heights at which the vertical line through `x` crosses the centre lines of `strokes`.
fn crossings(strokes: &[(Vec<Knot>, bool)], x: f64) -> Vec<f64> {
    let mut out = Vec::new();
    for (ks, closed) in strokes {
        let Ok(sk) = skeleton(ks, *closed) else {
            continue;
        };
        for seg in sk.segs() {
            let mut prev = seg.start();
            for q in flatten(&seg, 0.02) {
                if (prev.x - x) * (q.x - x) < 0.0 || (q.x == x && prev.x != x) {
                    out.push(prev.y + (q.y - prev.y) * (x - prev.x) / (q.x - prev.x));
                }
                prev = q;
            }
        }
    }
    out
}

// ---------------------------------------------------------------------------------------------------------------
// The double-struck letters and figures: which stroke of the plain letter is doubled.

/// What to double in a plain letter.
#[derive(Clone, Copy, Debug)]
enum How {
    /// The stem furthest left (true) or right, keeping that edge, growing the letter that way unless `Centre`.
    Stem(bool, Keep),
    /// The round side on the left (true) or right; the second stroke stands inside.
    Side(bool, Reach),
    /// The straight side on the left (true) or right of a stroke that also curves (the stem of a, g): the thin
    /// stroke keeps the counter's edge and the second one stands outside, growing the letter.
    SideOut(bool),
    /// Both round sides, the left one and the right one.
    Sides,
    /// The left round sides of every stroke that has one (the two rings of 8).
    LeftOfEach,
    /// The right round sides of every stroke that has one (the two bowls of 3).
    RightOfEach,
    /// The straight diagonal that runs down to the right (true) or up to the right.
    Diagonal(bool),
    /// The left stroke of the V drawn as a polygon.
    Vee,
}

/// The double-struck form of the glyph `base`, its stems `s` thick.
fn double(g: &mut Draw, base: &str, how: How, s: f64) {
    let p = g.p;
    let grow = match how {
        How::Stem(left, keep) if keep != Keep::Centre => {
            if (keep == Keep::Right) == left {
                if left { Grow::Left } else { Grow::Right }
            } else {
                Grow::None
            }
        }
        How::SideOut(true) => Grow::Left,
        How::SideOut(false) => Grow::Right,
        _ => Grow::None,
    };
    let mut d = Plain::of(g, base, grow, growth(p, s));
    match how {
        How::Stem(left, keep) => match d.stem(left) {
            Some(i) => {
                let reach = if keep == Keep::Centre { Reach::Nearest } else { Reach::Ends };
                d.double_stem(p, i, keep, reach);
            }
            None => d.errors.push(format!("{base}: no stem to double")),
        },
        How::Side(left, reach) => match d.round(left) {
            Some(i) => d.side(p, i, left, if left { Keep::Left } else { Keep::Right }, reach),
            None => d.errors.push(format!("{base}: no round side to double")),
        },
        How::SideOut(left) => match d.round(left) {
            Some(i) => d.side(p, i, left, if left { Keep::Right } else { Keep::Left }, Reach::Ends),
            None => d.errors.push(format!("{base}: no side to double")),
        },
        How::Sides => {
            for left in [true, false] {
                match d.round(left) {
                    Some(i) => d.side(p, i, left, if left { Keep::Left } else { Keep::Right }, Reach::Nearest),
                    None => d.errors.push(format!("{base}: no round side to double")),
                }
            }
        }
        How::LeftOfEach | How::RightOfEach => {
            let left = matches!(how, How::LeftOfEach);
            for i in 0..d.strokes.len() {
                if (0..d.strokes[i].0.len()).any(|j| vertical(&d.strokes[i].0, j) && d.strokes[i].0[j].pen.is_none()) {
                    d.side(p, i, left, if left { Keep::Left } else { Keep::Right }, Reach::Nearest);
                }
            }
        }
        How::Diagonal(down) => match d.diagonal(down) {
            Some(i) => d.double_diagonal(p, i, 1.0, 1.0),
            None => d.errors.push(format!("{base}: no diagonal to double")),
        },
        How::Vee => d.double_vee(p),
    }
    d.draw(g);
}

/// The double-struck capitals, the plain capital each doubles, and how.
const CAPITALS: [(char, char, How); 25] = [
    ('𝔸', 'A', How::Vee),
    ('𝔹', 'B', How::Stem(true, Keep::Right)),
    ('ℂ', 'C', How::Side(true, Reach::Nearest)),
    ('𝔻', 'D', How::Stem(true, Keep::Right)),
    ('𝔼', 'E', How::Stem(true, Keep::Right)),
    ('𝔽', 'F', How::Stem(true, Keep::Right)),
    ('𝔾', 'G', How::Side(true, Reach::Nearest)),
    ('ℍ', 'H', How::Stem(true, Keep::Right)),
    ('𝕀', 'I', How::Stem(true, Keep::Centre)),
    ('𝕁', 'J', How::Side(false, Reach::Nearest)),
    ('𝕂', 'K', How::Stem(true, Keep::Right)),
    ('𝕃', 'L', How::Stem(true, Keep::Right)),
    ('𝕄', 'M', How::Stem(true, Keep::Right)),
    ('ℕ', 'N', How::Stem(true, Keep::Right)),
    ('𝕆', 'O', How::Side(true, Reach::Nearest)),
    ('ℙ', 'P', How::Stem(true, Keep::Right)),
    ('ℚ', 'Q', How::Side(true, Reach::Nearest)),
    ('ℝ', 'R', How::Stem(true, Keep::Right)),
    ('𝕊', 'S', How::Sides),
    ('𝕋', 'T', How::Stem(true, Keep::Centre)),
    ('𝕌', 'U', How::Side(true, Reach::Nearest)),
    ('𝕍', 'V', How::Vee),
    ('𝕏', 'X', How::Diagonal(true)),
    ('𝕐', 'Y', How::Vee),
    ('ℤ', 'Z', How::Diagonal(false)),
];

/// The double-struck lowercase.
const SMALL: [(char, char, How); 26] = [
    ('𝕒', 'a', How::SideOut(false)),
    ('𝕓', 'b', How::Stem(true, Keep::Right)),
    ('𝕔', 'c', How::Side(true, Reach::Nearest)),
    ('𝕕', 'd', How::Stem(false, Keep::Left)),
    ('𝕖', 'e', How::Side(true, Reach::Nearest)),
    ('𝕗', 'f', How::Side(true, Reach::Ends)),
    ('𝕘', 'g', How::SideOut(false)),
    ('𝕙', 'h', How::Stem(true, Keep::Right)),
    ('𝕚', 'ı', How::Stem(true, Keep::Centre)),
    ('𝕛', 'ȷ', How::Side(true, Reach::Ends)),
    ('𝕜', 'k', How::Stem(true, Keep::Right)),
    ('𝕝', 'l', How::Side(true, Reach::Nearest)),
    ('𝕞', 'm', How::Stem(true, Keep::Right)),
    ('𝕟', 'n', How::Stem(true, Keep::Right)),
    ('𝕠', 'o', How::Side(true, Reach::Nearest)),
    ('𝕡', 'p', How::Stem(true, Keep::Right)),
    ('𝕢', 'q', How::Stem(false, Keep::Left)),
    ('𝕣', 'r', How::Stem(true, Keep::Right)),
    ('𝕤', 's', How::Sides),
    ('𝕥', 't', How::Side(true, Reach::Ends)),
    ('𝕦', 'u', How::Stem(false, Keep::Left)),
    ('𝕧', 'v', How::Vee),
    ('𝕨', 'w', How::Diagonal(true)),
    ('𝕩', 'x', How::Diagonal(true)),
    ('𝕪', 'y', How::Diagonal(true)),
    ('𝕫', 'z', How::Diagonal(false)),
];

/// The double-struck figures.
const FIGURES: [(char, &str, How); 10] = [
    ('𝟘', "zero.plain", How::Side(true, Reach::Nearest)),
    ('𝟙', "one", How::Stem(true, Keep::Right)),
    ('𝟚', "two", How::Side(false, Reach::Nearest)),
    ('𝟛', "three", How::RightOfEach),
    ('𝟜', "four", How::Stem(true, Keep::Right)),
    ('𝟝', "five", How::Stem(true, Keep::Left)),
    ('𝟞', "six", How::Side(true, Reach::Outer)),
    ('𝟟', "seven", How::Diagonal(false)),
    ('𝟠', "eight", How::LeftOfEach),
    ('𝟡', "nine", How::Side(false, Reach::Outer)),
];

/// 𝕎: W as four straight strokes, with the first doubled (the cell has no room for a second doubled stroke). W itself is one polygon,
/// which cannot be taken apart, so its construction is repeated here: the outer strokes reach the cell's sides at
/// the cap height, the inner ones meet at 0.80 of it.
fn double_w(g: &mut Draw) {
    let p = g.p;
    let (to, ti) = (p.cap_stem * 0.84, p.cap_stem * 0.72);
    let (x0, x1) = (21.0, p.width - 21.0);
    let v0 = x0 + 0.25 * (x1 - x0);
    let v1 = p.width - v0;
    let top = p.cap * 0.80;
    let strokes = vec![
        (bar(x0, p.cap, v0, 0.0, to, -1.0, 0.0), false),
        (bar(v0, 0.0, p.mid(), top, ti, 0.0, 0.0), false),
        (bar(p.mid(), top, v1, 0.0, ti, 0.0, 0.0), false),
        (bar(v1, 0.0, x1, p.cap, to, 0.0, 1.0), false),
    ];
    let mut d = Plain { strokes, rest: vec![], advance: p.width, more: vec![], polys: vec![], dx: 0.0, errors: vec![] };
    d.double_diagonal(p, 0, 1.0, 0.0);
    d.draw(g);
}

/// The dot of i and j: what the dotted letter has that the dotless one does not.
fn dot_of(g: &mut Draw, dotted: char, dotless: char) {
    let (Some(a), Some(b)) = (g.glyph_of_char(dotted), g.glyph_of_char(dotless)) else {
        return;
    };
    for c in a.contours {
        if !b.contours.iter().any(|d| same_contour(&c, d)) {
            g.add_upright(c);
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Slanted letters: ℎ ℏ ℓ, the double-struck italics, the italic dotless i and j.

/// Add the stroke through `knots` (upright coordinates) slanted as the italic is, in every master.
fn stroke_slanted(g: &mut Draw, knots: &[Knot]) {
    let o = g.p.slant_origin();
    let ks: Vec<Knot> = knots.iter().map(|k| sheared(k, slope(), o)).collect();
    match expand(&ks, false) {
        Ok(cs) => cs.into_iter().for_each(|c| g.add_upright(c)),
        Err(e) => g.glyph.errors.push(e),
    }
}

/// The glyph `name` as the italic draws it, in the upright face as in the italic one.
fn italic_of(g: &mut Draw, name: &str) {
    italic_in(g, name, 0.0);
}

/// [`italic_of`] for a letter drawn `narrow` narrower than its cell and centred in it, to leave room for its lean
/// (the double-struck italics, whose doubled stems already fill the cell).
fn italic_in(g: &mut Draw, name: &str, narrow: f64) {
    let p = g.p;
    let q = Params { width: p.width - narrow, ..slanted(p) };
    let from = g.glyph.contours.len();
    if let Some(other) = g.glyph_as(name, &q) {
        g.glyph.advance = other.advance + narrow;
    }
    g.draw_as(name, &q, narrow / 2.0, 0.0);
    keep_inside(g, from);
}

/// An ink at least this far inside the cell's sides, as the italic lowercase keeps (`lower::nudge`).
const EDGE: f64 = 4.0;

/// Move the contours added since the `from`th so that they stay `EDGE` inside the cell, when the doubling or the
/// slant has carried them out of it. It moves nothing in a glyph that fits.
fn keep_inside(g: &mut Draw, from: usize) {
    let (mut lo, mut hi) = (f64::INFINITY, f64::NEG_INFINITY);
    for c in &g.glyph.contours[from..] {
        if let Some((x0, _, x1, _)) = c.bounds() {
            lo = lo.min(x0);
            hi = hi.max(x1);
        }
    }
    if lo > hi {
        return;
    }
    let dx = (EDGE - lo).max(0.0) - (hi - (g.glyph.advance - EDGE)).max(0.0);
    if dx != 0.0 {
        for c in &mut g.glyph.contours[from..] {
            *c = c.mapped(|z| z + pt(dx, 0.0));
        }
    }
}

fn planck(g: &mut Draw) {
    italic_of(g, "h");
}

/// ℎ with a bar across its ascender, on the slant.
fn hbar_(g: &mut Draw) {
    let p = g.p;
    italic_of(g, "h");
    let y = p.xh + 0.42 * (p.asc - p.xh);
    let h = 0.86 * p.hair;
    let x = p.xl();
    stroke_slanted(g, &hbar(x - 0.62 * p.stem - 40.0, x + 0.62 * p.stem + 70.0, y, h));
}

/// The script l: a loop on the slant. The stroke rises from the left on a hairline, turns over the top, comes
/// down as the stem through its own start, and turns out to the right at the foot.
fn ell(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let x = p.mid() - 30.0; // the stem
    let top = p.asc + p.over - h / 2.0;
    let r = 0.5 * (0.55 * p.counter + s); // half the loop's width on its centre line
    let y_loop = top - 1.3 * r; // where the loop's sides are vertical
    let foot = -p.over + h / 2.0;
    stroke_slanted(
        g,
        &[
            cut(p.sb_round - 10.0, 0.30 * p.xh, 0.9 * h, 30.0),
            knot(x + 2.0 * r - s / 2.0, y_loop, 0.9 * s).dir(90.0),
            knot(x + r, top, h).dir(180.0),
            knot(x, y_loop - 0.2 * r, s).dir(-90.0).line(),
            knot(x, foot + 1.2 * r, s).dir(-90.0).k(p.sq),
            knot(x + r * 1.1, foot, h).dir(0.0),
            cut(p.width - p.sb_round + 4.0, foot + 0.22 * p.xh, h, 50.0),
        ],
    );
}

// ---------------------------------------------------------------------------------------------------------------
// Hebrew letters as mathematics uses them

/// Alef: a diagonal from the top left to the foot on the right, an arm that rises from it to the top right,
/// and a leg that falls from it to a foot on the left.
fn alef(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.cap_stem, p.cap_hair);
    let (x0, x1) = (p.sb_round - 4.0, p.width - p.sb_round + 4.0);
    let t = 0.95 * s;
    // the diagonal, cut flat on the cap height and the baseline
    let a = pt(x0 + 0.5 * t, p.cap);
    let b = pt(x1 - 0.5 * t, 0.0);
    let w = t * (b - a).abs() / p.cap;
    g.stroke(&[knot(a.x, a.y, w).pen(0.0).line(), knot(b.x, b.y, w).pen(0.0)]);
    let on = |f: f64| a + (b - a) * f;
    // the arm leaves the diagonal level, turns a corner and rises as a short stem to the cap height; the leg
    // does the same downwards on the left. The corners are what tell ℵ from X.
    let ts = 0.85 * s;
    let r = 0.11 * p.cap;
    let ja = on(0.40);
    let xa = x1 - ts / 2.0;
    g.stroke(&[
        knot(ja.x, ja.y, h).pen(90.0).line(),
        knot(xa - r, ja.y, h).pen(90.0).dir(0.0).k(p.sq),
        knot(xa, ja.y + r, ts).pen(0.0).dir(90.0).line(),
        knot(xa, p.cap, ts).pen(0.0),
    ]);
    let jl = on(0.60);
    let xl = x0 + ts / 2.0;
    g.stroke(&[
        knot(jl.x, jl.y, h).pen(90.0).line(),
        knot(xl + r, jl.y, h).pen(90.0).dir(180.0).k(p.sq),
        knot(xl, jl.y - r, ts).pen(0.0).dir(-90.0).line(),
        knot(xl, 0.0, ts).pen(0.0),
    ]);
}

// ---------------------------------------------------------------------------------------------------------------
// Fraktur and script capitals that mathematics names: ℑ ℜ ℘

/// The Fraktur I (imaginary part): a stem that hooks out to the left at its foot, under a wave that crosses its
/// top.
fn fraktur_i(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.cap_stem, p.cap_hair);
    let x = p.mid() + 30.0;
    let top = p.cap - h / 2.0;
    g.stroke(&[
        cut(p.sb_round, p.cap * 0.70, h, 70.0),
        knot(p.sb_round + 90.0, top, h).dir(0.0),
        knot(x - 20.0, p.cap * 0.86, h).dir(-30.0),
        knot(x + 120.0, top, h).dir(30.0),
        cut(p.width - p.sb_round, p.cap * 0.88, h, -50.0),
    ]);
    g.stroke(&[
        knot(x, p.cap * 0.88, s).pen(0.0).line(),
        knot(x, p.cap * 0.30, s).pen(0.0).dir(-90.0).k(p.sq),
        knot(x - 140.0, -p.over + h / 2.0, h).dir(180.0),
        cut(p.sb_round + 10.0, p.cap * 0.18, h, 120.0),
    ]);
}

/// The Fraktur R (real part): a stem that comes in from a hairline at its head and flicks left at its foot, a
/// bowl of two humps parted by a notch, and a leg that sweeps out to the right.
fn fraktur_r(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.cap_stem, p.cap_hair);
    let x = p.cxl() + 30.0;
    let top = p.cap + p.over - h / 2.0;
    let bot = -p.over + h / 2.0;
    let waist = p.cap * 0.47;
    let edge = p.width - p.sb_round - 16.0;
    // the stem
    g.stroke(&[
        cut(x - 0.9 * s - 20.0, p.cap * 0.74, h, 70.0),
        knot(x - 0.25 * s, top, h).dir(0.0),
        knot(x, p.cap * 0.76, s).pen(0.0).dir(-90.0).line(),
        knot(x, p.cap * 0.20, s).pen(0.0).dir(-90.0),
        knot(x - 0.8 * s, bot, h).dir(200.0),
    ]);
    // the humps of the bowl: the first rises from the stem to the notch, the second from the notch round to the
    // waist and back into the stem
    let notch = pt(x + 0.46 * (edge - x), p.cap * 0.86);
    let hh = 0.8 * h; // the humps are lighter, to keep the bowl's top open
    g.stroke(&[
        knot(x, p.cap * 0.74, hh).dir(62.0),
        knot(x + 0.25 * (edge - x), top, hh).dir(0.0),
        knot(notch.x, notch.y, hh).dir(-58.0),
    ]);
    g.stroke(&[
        knot(notch.x, notch.y, hh).dir(58.0),
        knot(edge - 0.26 * (edge - x), top, hh).dir(0.0),
        knot(edge - s / 2.0, p.cap * 0.68, s).dir(-90.0),
        knot(x + 0.45 * (edge - x), waist, h).dir(180.0),
        knot(x, waist, h).dir(180.0),
    ]);
    // the leg
    g.stroke(&[
        knot(x + 0.42 * (edge - x), waist, 0.9 * s).dir(-62.0),
        knot(edge - 0.6 * s, p.cap * 0.12, 0.9 * s).dir(-70.0),
        knot(p.width - p.sb_round + 14.0, bot + 0.04 * p.cap, h).dir(15.0),
    ]);
}

/// The Weierstrass p: a hooked head that comes down as a stem below the baseline, loops back up on the left,
/// crosses the stem and becomes a round bowl at the x-height that returns to the stem.
fn weierstrass(g: &mut Draw) {
    let p = g.p;
    let (s, h) = (p.stem, p.hair);
    let (x0, x1) = (p.sb_round, p.width - p.sb_round);
    let xs = x0 + 0.40 * (x1 - x0); // the stem
    let top = p.xh + p.over - h / 2.0;
    let bot = -p.over + h / 2.0;
    let xb = (xs + x1) / 2.0 + 10.0; // the bowl's top and bottom
    g.stroke(&[
        cut(x0 + 6.0, 0.66 * p.xh, 0.9 * h, 62.0),
        knot(x0 + 0.45 * (xs - x0), top, h).dir(0.0),
        knot(xs, 0.52 * p.xh, s).pen(0.0).dir(-90.0).line(),
        knot(xs, 0.0, s).pen(0.0).dir(-90.0),
        knot(x0 + 0.55 * (xs - x0), p.desc + h / 2.0, h).dir(180.0),
        knot(x0 + 0.40 * s, 0.55 * p.desc, 0.8 * s).dir(90.0),
        knot(xs + 0.3 * s, 0.10 * p.xh, 0.85 * h).dir(38.0),
        knot(xb, top, h).dir(0.0),
        knot(x1 - s / 2.0, 0.48 * p.xh, s).dir(-90.0),
        knot(xb - 10.0, bot, h).dir(180.0),
        cut(xs + s / 2.0 + 16.0, 0.16 * p.xh, h, 140.0),
    ]);
}

// ---------------------------------------------------------------------------------------------------------------
// Turned and composed signs: ℮ ℯ ℹ ℅ ⅋ ℧ ℗ ℞

/// The contours of the glyph `c` as the upright master draws it, turned half a circle about the middle of the
/// cell at half the cap height, then slanted with the master.
fn turned(g: &mut Draw, c: char) {
    let p = g.p;
    let q = Params { slant: 0.0, ..p.clone() };
    let Some(glyph) = g.glyph_as(&name_of(c), &q) else {
        g.glyph.errors.push(format!("no glyph {c:?} to turn"));
        return;
    };
    let centre = pt(p.mid(), p.cap / 2.0);
    for contour in glyph.contours {
        g.add(contour.mapped(|z| centre * 2.0 - z));
    }
}

fn turned_ampersand(g: &mut Draw) {
    turned(g, '&');
}

fn inverted_ohm(g: &mut Draw) {
    turned(g, 'Ω');
}

/// The estimated sign: the lowercase e drawn as large as a capital, with its strokes.
fn estimated(g: &mut Draw) {
    let p = g.p;
    let f = 0.80 * p.cap / p.xh;
    let q = Params { stem: p.cap_stem, hair: p.cap_hair, over: p.over, slant: 0.0, ..p.scaled(f) };
    let Some(e) = g.glyph_as("e", &q) else {
        return;
    };
    let (x0, _, x1, _) = e.bounds().unwrap_or((0.0, 0.0, q.width, 0.0));
    let dx = p.mid() - (x0 + x1) / 2.0;
    for c in e.contours {
        g.add(c.mapped(|z| z + pt(dx, 0.0)));
    }
}

/// The script small e: the italic e.
fn script_e(g: &mut Draw) {
    italic_of(g, "e");
}

/// The information source: a bold serif i.
fn information(g: &mut Draw) {
    let p = g.p;
    let q = Params { stem: 1.45 * p.stem, hair: 1.3 * p.hair, dot: 1.25 * p.dot, ..p.clone() };
    g.draw_as("i", &q, 0.0, 0.0);
}

/// Care of: a small c above a small o, either side of a slash.
fn care_of(g: &mut Draw) {
    let p = g.p;
    let f = 0.56;
    let q = Params { stem: 0.62 * p.stem + 14.0, hair: 0.62 * p.hair + 12.0, slant: 0.0, ..p.scaled(f) };
    let (Some(c), Some(o)) = (g.glyph_as("c", &q), g.glyph_as("o", &q)) else {
        return;
    };
    let (dy_c, dy_o) = (p.cap - q.xh - q.over, 0.0);
    for contour in c.contours {
        g.add(contour.mapped(|z| z + pt(-6.0, dy_c)));
    }
    for contour in o.contours {
        g.add(contour.mapped(|z| z + pt(p.width - q.width + 6.0, dy_o)));
    }
    g.stroke(&crate::parts::diag(150.0, 0.0, p.width - 150.0, p.cap, 0.9 * p.hair));
}

/// The sound recording copyright: the circle of ©, around a P.
fn phonogram(g: &mut Draw) {
    let p = g.p;
    let q = Params { slant: 0.0, ..p.clone() };
    let Some(copy) = g.glyph_as(&name_of('©'), &q) else {
        return;
    };
    let (x0, y0, x1, y1) = copy.bounds().unwrap_or((0.0, 0.0, p.width, p.cap));
    let (s, h) = (0.62 * p.stem + 18.0, 0.62 * p.hair + 16.0);
    let (ps, ph) = (0.45 * p.stem + 22.0, 0.45 * p.hair + 20.0); // the P's strokes, lighter: its counter is small
    g.stroke_closed(&ring(x0, y0, x1, y1, s, h, p.sq));
    // the P, drawn with the inner letter's strokes
    let (cx, cy) = ((x0 + x1) / 2.0, (y0 + y1) / 2.0);
    let r = 0.27 * (y1 - y0);
    let xs = cx - 0.62 * r;
    g.stroke(&vstem(xs, cy - r, cy + r, ps));
    g.stroke(&crate::parts::dbowl(xs, cx + 0.78 * r, cy - 0.12 * r, cy + r, ps, ph, p.sq + 0.02, 0.5 * r));
}

/// The prescription sign: R with a stroke across its leg.
fn prescription(g: &mut Draw) {
    let p = g.p;
    g.use_char('R', 0.0, 0.0);
    let t = 0.9 * p.cap_hair;
    let (xa, ya) = (p.mid() + 30.0, -0.16 * p.cap);
    let (xb, yb) = (p.width - p.sb_round - 16.0, 0.30 * p.cap);
    g.stroke(&crate::parts::diag(xa, ya, xb, yb, t));
}

// ---------------------------------------------------------------------------------------------------------------

pub fn register(reg: &mut Registry) {
    reg.module("letterlike");
    for (c, base, how) in CAPITALS {
        reg.ch(c, move |g: &mut Draw| {
            let s = g.p.cap_stem;
            double(g, &name_of(base), how, s);
        });
    }
    for (c, base, how) in FIGURES {
        reg.ch(c, move |g: &mut Draw| {
            let s = g.p.cap_stem;
            double(g, base, how, s);
        });
    }
    for (c, base, how) in SMALL {
        reg.ch(c, move |g: &mut Draw| {
            let s = g.p.stem;
            double(g, &name_of(base), how, s);
            if c == '𝕚' {
                dot_of(g, 'i', 'ı');
            }
            if c == '𝕛' {
                dot_of(g, 'j', 'ȷ');
            }
        });
    }
    reg.ch('𝕎', double_w);
    reg.ch('ℾ', |g: &mut Draw| {
        let s = g.p.cap_stem;
        double(g, &name_of('Γ'), How::Stem(true, Keep::Right), s);
    });
    reg.ch('ℿ', |g: &mut Draw| {
        let s = g.p.cap_stem;
        double(g, &name_of('Π'), How::Stem(true, Keep::Right), s);
    });
    reg.ch('ℽ', |g: &mut Draw| {
        let s = g.p.stem;
        double(g, &name_of('γ'), How::Vee, s);
    });
    // the double-struck italics: the double-struck letters on the slant
    for (c, of) in [('ⅅ', '𝔻'), ('ⅆ', '𝕕'), ('ⅇ', '𝕖'), ('ⅈ', '𝕚'), ('ⅉ', '𝕛')] {
        reg.ch(c, move |g: &mut Draw| italic_in(g, &name_of(of), 60.0));
    }
    reg.ch('𝚤', |g: &mut Draw| italic_of(g, &name_of('ı')));
    reg.ch('𝚥', |g: &mut Draw| italic_of(g, &name_of('ȷ')));
    reg.ch('ℓ', ell);
    reg.ch('ℎ', planck);
    reg.ch('ℏ', hbar_);
    reg.ch('ℵ', alef);
    reg.ch('ℑ', fraktur_i);
    reg.ch('ℜ', fraktur_r);
    reg.ch('℘', weierstrass);
    reg.ch('℮', estimated);
    reg.ch('ℯ', script_e);
    reg.ch('ℹ', information);
    reg.ch('℅', care_of);
    reg.ch('⅋', turned_ampersand);
    reg.ch('℧', inverted_ohm);
    reg.ch('℗', phonogram);
    reg.ch('℞', prescription);
}
