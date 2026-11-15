//! Parts: the skeletons that letters share, as lists of knots.
//!
//! A part returns knots and draws nothing, so a glyph program can mirror or turn it before stroking it: `u` is
//! `n` turned half a circle, `d` is `b` mirrored. The symmetries are those of the rectangle: [`mirror`]
//! (left-right), [`flip`] (top-bottom) and [`turn`] (both).

use rachis_kernel::{Knot, Params, V, knot, pt};

/// Reflect left to right in the vertical line x = cx.
pub fn mirror(knots: &[Knot], cx: f64) -> Vec<Knot> {
    knots
        .iter()
        .map(|k| Knot {
            z: pt(2.0 * cx - k.z.x, k.z.y),
            dir: k.dir.map(|d| 180.0 - d),
            pen: k.pen.map(|a| 180.0 - a),
            ..*k
        })
        .collect()
}

/// Reflect top to bottom in the horizontal line y = cy.
pub fn flip(knots: &[Knot], cy: f64) -> Vec<Knot> {
    knots
        .iter()
        .map(|k| Knot {
            z: pt(k.z.x, 2.0 * cy - k.z.y),
            dir: k.dir.map(|d| -d),
            pen: k.pen.map(|a| -a),
            ..*k
        })
        .collect()
}

/// Rotate half a circle about (cx, cy).
pub fn turn(knots: &[Knot], cx: f64, cy: f64) -> Vec<Knot> {
    knots
        .iter()
        .map(|k| Knot {
            z: pt(2.0 * cx - k.z.x, 2.0 * cy - k.z.y),
            dir: k.dir.map(|d| d + 180.0),
            ..*k
        })
        .collect()
}

/// `knots` moved `dx` to the right.
pub fn shifted(knots: &[Knot], dx: f64) -> Vec<Knot> {
    knots
        .iter()
        .map(|k| Knot {
            z: pt(k.z.x + dx, k.z.y),
            ..*k
        })
        .collect()
}

/// `knots` moved by (dx, dy).
pub fn moved(knots: &[Knot], dx: f64, dy: f64) -> Vec<Knot> {
    knots
        .iter()
        .map(|k| Knot {
            z: pt(k.z.x + dx, k.z.y + dy),
            ..*k
        })
        .collect()
}

/// A vertical stroke centred on x, cut square at y0 and y1.
pub fn vstem(x: f64, y0: f64, y1: f64, w: f64) -> Vec<Knot> {
    vec![knot(x, y0, w).pen(0.0).line(), knot(x, y1, w).pen(0.0)]
}

/// A horizontal stroke centred on y, cut square at x0 and x1.
pub fn hbar(x0: f64, x1: f64, y: f64, w: f64) -> Vec<Knot> {
    vec![knot(x0, y, w).pen(90.0).line(), knot(x1, y, w).pen(90.0)]
}

/// A closed bowl whose outer edge touches the box (x0, y0)-(x1, y1): `sw` thick at the sides, `hw` at top and
/// bottom. Stroke it with `stroke_closed`.
pub fn ring(x0: f64, y0: f64, x1: f64, y1: f64, sw: f64, hw: f64, k: f64) -> Vec<Knot> {
    let (cx, cy) = ((x0 + x1) / 2.0, (y0 + y1) / 2.0);
    let (rx, ry) = ((x1 - x0) / 2.0 - sw / 2.0, (y1 - y0) / 2.0 - hw / 2.0);
    vec![
        knot(cx + rx, cy, sw).dir(90.0).k(k),
        knot(cx, cy + ry, hw).dir(180.0).k(k),
        knot(cx - rx, cy, sw).dir(-90.0).k(k),
        knot(cx, cy - ry, hw).dir(0.0).k(k),
    ]
}

/// Options of [`arch`]. `branch` is the height where the arch's lower edge leaves the left stem. `lean` places
/// the crest across the counter (0.5 is the middle). `spring` is the direction, in degrees, in which the arch
/// leaves the stem. `drop` is the height of the shoulder's curve as a multiple of its width.
#[derive(Clone, Copy, Debug)]
pub struct Arch {
    pub stem: Option<f64>,
    pub hair: Option<f64>,
    pub branch: Option<f64>,
    pub lean: f64,
    pub spring: f64,
    pub drop: f64,
}

impl Default for Arch {
    fn default() -> Arch {
        Arch {
            stem: None,
            hair: None,
            branch: None,
            lean: 0.54,
            spring: 58.0,
            drop: 1.08,
        }
    }
}

/// The shoulder of n: it springs from the right edge of the stem centred on `xl`, crests with its outer edge at
/// `top`, and comes down as a stem centred on `xr` to `foot`.
pub fn arch(p: &Params, xl: f64, xr: f64, top: f64, foot: f64, o: Arch) -> Vec<Knot> {
    let s = o.stem.unwrap_or(p.stem);
    let h = o.hair.unwrap_or(p.hair);
    let branch = o.branch.unwrap_or(top - 0.30 * p.xh);
    let j = p.join * s;
    let d = V::unit(o.spring);
    let start = pt(xl + s / 2.0 - 3.0, branch) + d.left() * (j / 2.0);
    let (inner_l, inner_r) = (xl + s / 2.0, xr - s / 2.0);
    let xa = inner_l + o.lean * (inner_r - inner_l);
    let crest = top - h / 2.0;
    let shoulder = crest - o.drop * (xr - xa);
    vec![
        Knot::at(start, j).dir(o.spring),
        knot(xa, crest, h).dir(0.0).k(p.sq),
        knot(xr, shoulder, s).pen(0.0).dir(-90.0).line(),
        knot(xr, foot, s).pen(0.0),
    ]
}

/// Options of [`bowl`].
#[derive(Clone, Copy, Debug)]
pub struct Bowl {
    pub stem: Option<f64>,
    pub hair: Option<f64>,
    pub branch: f64,
    pub spring: f64,
    pub lean: f64,
}

impl Default for Bowl {
    fn default() -> Bowl {
        Bowl {
            stem: None,
            hair: None,
            branch: 0.30,
            spring: 58.0,
            lean: 0.50,
        }
    }
}

/// The bowl of b: it springs from the right edge of the stem centred on `xl`, reaches `x_edge` with its outer
/// edge, and returns to the stem. Its outer edge spans `y0` to `y1`.
pub fn bowl(p: &Params, xl: f64, x_edge: f64, y0: f64, y1: f64, o: Bowl) -> Vec<Knot> {
    let s = o.stem.unwrap_or(p.stem);
    let h = o.hair.unwrap_or(p.hair);
    let j = p.join * s;
    let height = y1 - y0;
    let (d_top, d_bot) = (V::unit(o.spring), V::unit(180.0 - o.spring));
    let edge = xl + s / 2.0 - 3.0;
    let start = pt(edge, y1 - o.branch * height) + d_top.left() * (j / 2.0);
    let end = pt(edge, y0 + o.branch * height) + d_bot.left() * (j / 2.0);
    let inner_l = xl + s / 2.0;
    let xa = inner_l + o.lean * (x_edge - s - inner_l);
    let xc = x_edge - s / 2.0;
    vec![
        Knot::at(start, j).dir(o.spring),
        knot(xa, y1 - h / 2.0, h).dir(0.0).k(p.sq),
        knot(xc, (y0 + y1) / 2.0, s).dir(-90.0).k(p.sq),
        knot(xa, y0 + h / 2.0, h).dir(180.0),
        Knot::at(end, j).dir(180.0 - o.spring),
    ]
}

/// A knot whose pen is held vertical and is broad enough that the stroke, travelling along `dir`, is `t` thick:
/// the way to end a curved stroke with a vertical cut.
pub fn cut(x: f64, y: f64, t: f64, dir: f64) -> Knot {
    cut_pen(x, y, t, dir, 90.0)
}

/// [`cut`] with the pen held at the angle `pen` (0 for a horizontal cut).
pub fn cut_pen(x: f64, y: f64, t: f64, dir: f64, pen: f64) -> Knot {
    let breadth = t / (dir - pen).to_radians().sin().abs();
    knot(x, y, breadth).pen(pen).dir(dir)
}

/// A straight stroke `t` thick from (x0, y0) to (x1, y1), cut horizontally at both ends. The points are on its
/// centre line.
pub fn diag(x0: f64, y0: f64, x1: f64, y1: f64, t: f64) -> Vec<Knot> {
    let breadth = t * (x1 - x0).hypot(y1 - y0) / (y1 - y0).abs();
    vec![
        knot(x0, y0, breadth).pen(0.0).line(),
        knot(x1, y1, breadth).pen(0.0),
    ]
}

/// A stem centred on `x` that runs from `y_from` towards `y_edge`, turns a rounded corner and ends as a
/// horizontal foot whose outer edge lies on `y_edge` and whose vertical cut is at `x_end`. `r` is the radius of
/// the corner on the centre line. It is the tail of l, t and j and the hook of f.
pub fn elbow(
    x: f64,
    y_from: f64,
    y_edge: f64,
    x_end: f64,
    sw: f64,
    hw: f64,
    k: f64,
    r: f64,
) -> Vec<Knot> {
    let down = y_from > y_edge;
    let right = x_end > x;
    let yc = if down {
        y_edge + hw / 2.0
    } else {
        y_edge - hw / 2.0
    };
    vec![
        knot(x, y_from, sw).pen(0.0).line(),
        knot(x, if down { yc + r } else { yc - r }, sw)
            .pen(0.0)
            .dir(if down { -90.0 } else { 90.0 })
            .k(k),
        knot(if right { x + r } else { x - r }, yc, hw)
            .pen(90.0)
            .dir(if right { 0.0 } else { 180.0 })
            .line(),
        knot(x_end, yc, hw).pen(90.0),
    ]
}

/// The polygon of a V: outer top corners at `x0` and `x1`, strokes `t` thick, a flat vertex `apex` wide on
/// `y_bot`. Negative heights turn it into a caret.
pub fn vee(x0: f64, x1: f64, y_top: f64, y_bot: f64, t: f64, apex: f64) -> Vec<V> {
    let mid = (x0 + x1) / 2.0;
    let dx = (mid - apex / 2.0) - x0;
    let dy = y_top - y_bot;
    let wh = t * dx.hypot(dy) / dy.abs();
    let crotch = pt(mid, y_top - dy * (mid - x0 - wh) / dx);
    vec![
        pt(x0, y_top),
        pt(mid - apex / 2.0, y_bot),
        pt(mid + apex / 2.0, y_bot),
        pt(x1, y_top),
        pt(x1 - wh, y_top),
        crotch,
        pt(x0 + wh, y_top),
    ]
}

/// The x of the centre line of the left stroke of `vee(...)` at height `y`: where a crossbar ends.
pub fn vee_x(x0: f64, x1: f64, y_top: f64, y_bot: f64, t: f64, apex: f64, y: f64) -> f64 {
    let mid = (x0 + x1) / 2.0;
    let dx = (mid - apex / 2.0) - x0;
    let dy = y_top - y_bot;
    let wh = t * dx.hypot(dy) / dy.abs();
    x0 + wh / 2.0 + dx * (y_top - y) / dy
}

/// The bowl of D, P, B and R: a bar from the stem centred on `xl` along the top, a round side whose outer edge
/// reaches `x_edge`, and a bar back along the bottom. The outer edge spans `y0` to `y1`; `flat` is the length of
/// the straight part of each bar, measured from `xl`.
pub fn dbowl(
    xl: f64,
    x_edge: f64,
    y0: f64,
    y1: f64,
    sw: f64,
    hw: f64,
    k: f64,
    flat: f64,
) -> Vec<Knot> {
    let (yt, yb) = (y1 - hw / 2.0, y0 + hw / 2.0);
    let xc = x_edge - sw / 2.0;
    vec![
        knot(xl, yt, hw).pen(90.0).line(),
        knot(xl + flat, yt, hw).pen(90.0).dir(0.0).k(k),
        knot(xc, (yt + yb) / 2.0, sw).dir(-90.0).k(k),
        knot(xl + flat, yb, hw).pen(90.0).dir(180.0).line(),
        knot(xl, yb, hw).pen(90.0),
    ]
}

/// How far the italic's shear moves a point at height `y` to the right; 0 in an upright master.
pub fn lean(p: &Params, y: f64) -> f64 {
    p.slant.to_radians().tan() * (y - p.slant_origin())
}
