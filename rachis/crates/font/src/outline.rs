//! From drawn glyphs to TrueType outlines: the glyph order, components resolved into the shapes a `glyf` table
//! can hold, contour direction, and the conversion of cubic curves to quadratic ones over all masters at once.

use std::collections::BTreeMap;

use kurbo::{BezPath, CubicBez, PathEl, Point};
use rachis_kernel::{Glyph, Seg, V};

use crate::Error;

/// The largest distance, in font units, between a cubic curve and the quadratic spline that replaces it:
/// 0.001 em at 1000 units per em, the default of fontTools' cu2qu.
pub const QUADRATIC_TOLERANCE: f64 = 1.0;

/// How deep components may nest before a reference cycle is assumed.
const MAX_COMPONENT_DEPTH: usize = 32;

/// The glyph order: `.notdef`, every combining mark, the encoded glyphs by their lowest code point, then the
/// unencoded glyphs by name. Returns indices into `glyphs`.
pub(crate) fn glyph_order(glyphs: &[Glyph]) -> Vec<usize> {
    let notdef = glyphs.iter().position(|g| g.name == ".notdef");
    let rest = |i: &usize| Some(*i) != notdef;
    let mut marks: Vec<usize> = (0..glyphs.len()).filter(rest).filter(|&i| glyphs[i].mark).collect();
    marks.sort_by(|&a, &b| order_key(&glyphs[a]).cmp(&order_key(&glyphs[b])));
    let mut encoded: Vec<usize> =
        (0..glyphs.len()).filter(rest).filter(|&i| !glyphs[i].mark && !glyphs[i].unicodes.is_empty()).collect();
    encoded.sort_by(|&a, &b| order_key(&glyphs[a]).cmp(&order_key(&glyphs[b])));
    let mut unencoded: Vec<usize> =
        (0..glyphs.len()).filter(rest).filter(|&i| !glyphs[i].mark && glyphs[i].unicodes.is_empty()).collect();
    unencoded.sort_by(|&a, &b| glyphs[a].name.cmp(&glyphs[b].name));
    notdef.into_iter().chain(marks).chain(encoded).chain(unencoded).collect()
}

/// Encoded glyphs sort by their lowest code point, unencoded ones after them by name.
fn order_key(g: &Glyph) -> (u32, &str) {
    (g.unicodes.iter().copied().min().unwrap_or(u32::MAX), &g.name)
}

/// What a glyph becomes in a `glyf` table, in one master.
#[derive(Clone, Debug)]
pub(crate) enum Shape {
    /// No outline.
    Empty,
    /// Contours, with the outlines of any components copied in (PostScript direction, as drawn).
    Simple(Vec<rachis_kernel::Contour>),
    /// Components that are all simple glyphs: (name, offset).
    Composite(Vec<(String, V)>),
}

impl Shape {
    /// The structure that must agree between masters.
    fn signature(&self) -> String {
        match self {
            Shape::Empty => "empty".into(),
            Shape::Simple(contours) => {
                contours.iter().map(rachis_kernel::Contour::signature).collect::<Vec<_>>().join(" ")
            }
            Shape::Composite(components) => {
                components.iter().map(|(name, _)| format!("@{name}")).collect::<Vec<_>>().join(" ")
            }
        }
    }
}

/// The shape of `glyphs[i]` in one master. `index` maps glyph names to positions in `glyphs`.
pub(crate) fn shape_of(glyphs: &[Glyph], index: &BTreeMap<&str, usize>, i: usize) -> Result<Shape, Error> {
    let g = &glyphs[i];
    if !g.contours.is_empty() {
        let mut out = Vec::new();
        decompose(glyphs, index, g, V::ZERO, &mut out, 0, &g.name)?;
        return Ok(Shape::Simple(out));
    }
    if g.components.is_empty() {
        return Ok(Shape::Empty);
    }
    let mut out = Vec::new();
    flatten(glyphs, index, g, V::ZERO, &mut out, 0, &g.name)?;
    Ok(if out.is_empty() { Shape::Empty } else { Shape::Composite(out) })
}

fn lookup<'g>(
    glyphs: &'g [Glyph],
    index: &BTreeMap<&str, usize>,
    name: &str,
    owner: &str,
    depth: usize,
) -> Result<&'g Glyph, Error> {
    if depth > MAX_COMPONENT_DEPTH {
        return Err(Error::Glyph {
            glyph: owner.into(),
            detail: "components nest too deep (a reference cycle?)".into(),
        });
    }
    index.get(name).map(|&j| &glyphs[j]).ok_or_else(|| Error::Glyph {
        glyph: owner.into(),
        detail: format!("component {name:?} is not a glyph of the family"),
    })
}

/// Copy the contours of `g` and, recursively, of its components into `out`, moved by `offset`.
fn decompose(
    glyphs: &[Glyph],
    index: &BTreeMap<&str, usize>,
    g: &Glyph,
    offset: V,
    out: &mut Vec<rachis_kernel::Contour>,
    depth: usize,
    owner: &str,
) -> Result<(), Error> {
    for c in &g.contours {
        if c.segs.is_empty() {
            continue;
        }
        out.push(if offset == V::ZERO { c.clone() } else { c.mapped(|z| V { x: z.x + offset.x, y: z.y + offset.y }) });
    }
    for (name, off) in &g.components {
        let base = lookup(glyphs, index, name, owner, depth + 1)?;
        let at = V { x: offset.x + off.x, y: offset.y + off.y };
        decompose(glyphs, index, base, at, out, depth + 1, owner)?;
    }
    Ok(())
}

/// The simple glyphs that `g`'s components place, with nested composites flattened and empty glyphs left out.
fn flatten(
    glyphs: &[Glyph],
    index: &BTreeMap<&str, usize>,
    g: &Glyph,
    offset: V,
    out: &mut Vec<(String, V)>,
    depth: usize,
    owner: &str,
) -> Result<(), Error> {
    for (name, off) in &g.components {
        let base = lookup(glyphs, index, name, owner, depth + 1)?;
        let at = V { x: offset.x + off.x, y: offset.y + off.y };
        if !base.contours.is_empty() {
            out.push((name.clone(), at));
        } else if !base.components.is_empty() {
            flatten(glyphs, index, base, at, out, depth + 1, owner)?;
        }
    }
    Ok(())
}

/// Require every master's shape of the glyph `name` to have the same structure.
pub(crate) fn check_compatible(name: &str, shapes: &[Shape]) -> Result<(), Error> {
    let Some(first) = shapes.first() else {
        return Ok(());
    };
    let want = first.signature();
    for (m, s) in shapes.iter().enumerate().skip(1) {
        let got = s.signature();
        if got != want {
            return Err(Error::Incompatible {
                glyph: name.into(),
                detail: format!("master 0 has [{want}], master {m} has [{got}]"),
            });
        }
    }
    Ok(())
}

/// A piece of a closed contour: where it goes from the end of the previous piece.
#[derive(Clone, Copy, Debug, PartialEq)]
enum Piece {
    Line(Point),
    Cubic(Point, Point, Point),
}

impl Piece {
    fn end(&self) -> Point {
        match *self {
            Piece::Line(p) | Piece::Cubic(_, _, p) => p,
        }
    }
}

/// A closed contour as a start point and pieces; the last piece ends at the start.
#[derive(Clone, Debug)]
pub(crate) struct Path {
    start: Point,
    pieces: Vec<Piece>,
}

fn kp(v: V) -> Point {
    Point::new(v.x, v.y)
}

impl Path {
    /// A drawn contour.
    pub(crate) fn from_contour(c: &rachis_kernel::Contour) -> Path {
        let start = c.segs.first().map_or(Point::ZERO, |s| kp(s.start()));
        let pieces = c
            .segs
            .iter()
            .map(|s| match *s {
                Seg::Line(_, b) => Piece::Line(kp(b)),
                Seg::Cubic(_, c1, c2, b) => Piece::Cubic(kp(c1), kp(c2), kp(b)),
            })
            .collect();
        Path::closed(start, pieces)
    }

    /// Every closed subpath of a kurbo path. Quadratic pieces are raised to cubics, which is exact.
    pub(crate) fn from_bezpath(path: &BezPath) -> Vec<Path> {
        let mut out = Vec::new();
        let mut start = Point::ZERO;
        let mut current = Point::ZERO;
        let mut pieces: Vec<Piece> = Vec::new();
        for el in path.elements() {
            match *el {
                PathEl::MoveTo(p) => {
                    if !pieces.is_empty() {
                        out.push(Path::closed(start, std::mem::take(&mut pieces)));
                    }
                    start = p;
                    current = p;
                }
                PathEl::LineTo(p) => {
                    pieces.push(Piece::Line(p));
                    current = p;
                }
                PathEl::QuadTo(c, p) => {
                    let c1 = current + (c - current) * (2.0 / 3.0);
                    let c2 = p + (c - p) * (2.0 / 3.0);
                    pieces.push(Piece::Cubic(c1, c2, p));
                    current = p;
                }
                PathEl::CurveTo(c1, c2, p) => {
                    pieces.push(Piece::Cubic(c1, c2, p));
                    current = p;
                }
                PathEl::ClosePath => {
                    if !pieces.is_empty() {
                        out.push(Path::closed(start, std::mem::take(&mut pieces)));
                    }
                    current = start;
                }
            }
        }
        if !pieces.is_empty() {
            out.push(Path::closed(start, pieces));
        }
        out
    }

    /// Make the contour end exactly at its start: a closing line where the last piece stops short, the last
    /// curve's end moved onto the start where it misses it by rounding error.
    fn closed(start: Point, mut pieces: Vec<Piece>) -> Path {
        if let Some(last) = pieces.last_mut() {
            let end = last.end();
            if end.distance(start) > 1e-3 {
                pieces.push(Piece::Line(start));
            } else {
                match last {
                    Piece::Line(p) | Piece::Cubic(_, _, p) => *p = start,
                }
            }
        }
        Path { start, pieces }
    }

    /// The same contour run the other way, from the same start point.
    pub(crate) fn reversed(&self) -> Path {
        let mut ends: Vec<Point> = vec![self.start];
        ends.extend(self.pieces.iter().map(Piece::end));
        // ends[i] is where piece i starts, ends[i + 1] where it ends.
        let pieces = (0..self.pieces.len())
            .rev()
            .map(|i| match self.pieces[i] {
                Piece::Line(_) => Piece::Line(ends[i]),
                Piece::Cubic(c1, c2, _) => Piece::Cubic(c2, c1, ends[i]),
            })
            .collect();
        Path { start: self.start, pieces }
    }

    /// The contour as a kurbo path (cubic), closed.
    pub(crate) fn to_bezpath(&self) -> BezPath {
        let mut p = BezPath::new();
        p.move_to(self.start);
        for piece in &self.pieces {
            match *piece {
                Piece::Line(b) => p.line_to(b),
                Piece::Cubic(c1, c2, b) => p.curve_to(c1, c2, b),
            }
        }
        p.close_path();
        p
    }

    /// A point on the contour: the middle of its first piece.
    pub(crate) fn point_on(&self) -> Point {
        match self.pieces.first() {
            None => self.start,
            Some(Piece::Line(b)) => self.start.midpoint(*b),
            Some(Piece::Cubic(c1, c2, b)) => kurbo::ParamCurve::eval(&CubicBez::new(self.start, *c1, *c2, *b), 0.5),
        }
    }

    /// The signed area: positive when the contour runs counter-clockwise (y up).
    pub(crate) fn area(&self) -> f64 {
        kurbo::Shape::area(&self.to_bezpath())
    }

    /// The same structure with new coordinates, in the order [`Path::coordinates`] gives them.
    pub(crate) fn with_coordinates(&self, coords: &[Point]) -> Path {
        let mut it = coords.iter().copied();
        let mut next = || it.next().unwrap_or(Point::ZERO);
        let start = next();
        let pieces = self
            .pieces
            .iter()
            .map(|piece| match piece {
                Piece::Line(_) => Piece::Line(next()),
                Piece::Cubic(..) => {
                    let (c1, c2, b) = (next(), next(), next());
                    Piece::Cubic(c1, c2, b)
                }
            })
            .collect();
        Path { start, pieces }
    }

    /// Every coordinate of the contour, in order: the start, then each piece's points.
    pub(crate) fn coordinates(&self) -> Vec<Point> {
        let mut out = vec![self.start];
        for piece in &self.pieces {
            match *piece {
                Piece::Line(b) => out.push(b),
                Piece::Cubic(c1, c2, b) => out.extend([c1, c2, b]),
            }
        }
        out
    }
}

/// Convert one glyph's contours in every master to quadratic TrueType paths, turned to the TrueType direction.
/// `masters[m]` holds master `m`'s contours, in the PostScript direction (outer contours counter-clockwise);
/// all masters must have the same structure. Each cubic is converted over all masters at once, so that every
/// master gets the same number of points. The closing line of a contour is left implied.
pub(crate) fn quadratic_paths(name: &str, masters: &[Vec<Path>]) -> Result<Vec<BezPath>, Error> {
    let mut out = vec![BezPath::new(); masters.len()];
    let Some(first) = masters.first() else {
        return Ok(out);
    };
    for c in 0..first.len() {
        let reversed: Vec<Path> = masters.iter().map(|m| m[c].reversed()).collect();
        let n = reversed[0].pieces.len();
        if reversed.iter().any(|p| p.pieces.len() != n) {
            return Err(incompatible(name, c));
        }
        for (m, p) in reversed.iter().enumerate() {
            out[m].move_to(p.start);
        }
        let mut current: Vec<Point> = reversed.iter().map(|p| p.start).collect();
        for i in 0..n {
            let last = i + 1 == n;
            match reversed[0].pieces[i] {
                Piece::Line(_) => {
                    for (m, p) in reversed.iter().enumerate() {
                        let Piece::Line(b) = p.pieces[i] else {
                            return Err(incompatible(name, c));
                        };
                        if !last {
                            out[m].line_to(b);
                        }
                        current[m] = b;
                    }
                }
                Piece::Cubic(..) => {
                    let mut cubics = Vec::with_capacity(reversed.len());
                    for (m, p) in reversed.iter().enumerate() {
                        let Piece::Cubic(c1, c2, b) = p.pieces[i] else {
                            return Err(incompatible(name, c));
                        };
                        cubics.push(CubicBez::new(current[m], c1, c2, b));
                        current[m] = b;
                    }
                    let splines =
                        kurbo::cubics_to_quadratic_splines(&cubics, QUADRATIC_TOLERANCE).ok_or_else(|| {
                            Error::Glyph {
                                glyph: name.into(),
                                detail: format!("contour {c}: a cubic could not be made quadratic"),
                            }
                        })?;
                    for (m, spline) in splines.iter().enumerate() {
                        for q in spline.to_quads() {
                            out[m].quad_to(q.p1, q.p2);
                        }
                    }
                }
            }
        }
        for path in &mut out {
            path.close_path();
        }
    }
    Ok(out)
}

fn incompatible(name: &str, contour: usize) -> Error {
    Error::Incompatible { glyph: name.into(), detail: format!("contour {contour} differs between masters") }
}

/// Round a coordinate as fontTools' `otRound` does: floor(v + 0.5).
pub(crate) fn ot_round(v: f64) -> i32 {
    (v + 0.5).floor() as i32
}

#[cfg(test)]
mod tests {
    use super::*;
    use rachis_kernel::pen::{polygon, superellipse};
    use rachis_kernel::pt;

    #[test]
    fn reversal_keeps_the_start_and_flips_the_area() {
        let c = superellipse(100.0, 100.0, 80.0, 60.0, 0.6);
        let p = Path::from_contour(&c);
        let r = p.reversed();
        assert!(p.area() > 0.0);
        assert!((p.area() + r.area()).abs() < 1e-6);
        assert_eq!(p.start, r.start);
        assert_eq!(r.pieces.last().map(Piece::end), Some(r.start));
    }

    #[test]
    fn masters_stay_compatible_after_quadratic_conversion() {
        // A thin and a fat ellipse with very different curvature: cu2qu would choose different splits for each
        // alone.
        let thin = Path::from_contour(&superellipse(300.0, 300.0, 280.0, 20.0, 0.62));
        let fat = Path::from_contour(&superellipse(300.0, 300.0, 40.0, 290.0, 0.75));
        let paths = quadratic_paths("o", &[vec![thin.clone()], vec![fat.clone()]]).unwrap();
        let kinds = |p: &BezPath| p.elements().iter().map(std::mem::discriminant).collect::<Vec<_>>();
        assert_eq!(kinds(&paths[0]), kinds(&paths[1]));
        // TrueType direction: clockwise, so the area is negative.
        assert!(kurbo::Shape::area(&paths[0]) < 0.0);
        // Within the tolerance of the cubic: compare the areas.
        let rel = (kurbo::Shape::area(&paths[1]).abs() - fat.area()).abs() / fat.area();
        assert!(rel < 2e-3, "{rel}");
        let glyphs = write_fonts::tables::glyf::SimpleGlyph::interpolatable_glyphs_from_bezpaths(&paths).unwrap();
        let n0: usize = glyphs[0].contours.iter().map(|c| c.len()).sum();
        let n1: usize = glyphs[1].contours.iter().map(|c| c.len()).sum();
        assert_eq!(n0, n1);
    }

    #[test]
    fn the_closing_line_is_implied() {
        let square = polygon(&[pt(0.0, 0.0), pt(100.0, 0.0), pt(100.0, 100.0), pt(0.0, 100.0)]);
        let paths = quadratic_paths("square", &[vec![Path::from_contour(&square)]]).unwrap();
        let g = write_fonts::tables::glyf::SimpleGlyph::from_bezpath(&paths[0]).unwrap();
        assert_eq!(g.contours[0].len(), 4);
    }

    #[test]
    fn incompatible_masters_name_the_glyph() {
        let a = Shape::Composite(vec![("one".into(), V::ZERO)]);
        let b = Shape::Composite(vec![("two".into(), V::ZERO)]);
        let e = check_compatible("frac", &[a, b]).unwrap_err();
        assert!(e.to_string().contains("frac"), "{e}");
    }

    #[test]
    fn ot_round_rounds_halves_up() {
        assert_eq!(ot_round(0.5), 1);
        assert_eq!(ot_round(-0.5), 0);
        assert_eq!(ot_round(-1.5), -1);
        assert_eq!(ot_round(2.49), 2);
    }
}
