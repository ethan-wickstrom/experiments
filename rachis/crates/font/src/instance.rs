//! Static instances: the variation model evaluated at one location on the unrounded outlines, and the removal
//! of overlaps, checked by rasterising each glyph before and after.

use kurbo::{BezPath, PathEl, Point};
use linesweeper::{BinaryOp, FillRule, binary_op};

use crate::model::Model;
use crate::outline::{Path, Shape};

/// Pixels per em at which a glyph is rasterised before and after its overlaps are removed.
pub const CHECK_PPEM: f64 = 200.0;

/// The largest difference allowed in one pixel's coverage (0..=255) between the glyph before and after overlap
/// removal.
pub const CHECK_MAX_PIXEL: u8 = 96;

/// The largest total difference allowed, in whole pixels of coverage, between the glyph before and after.
pub const CHECK_MAX_TOTAL: f64 = 2.0;

/// Each master's weight at `location` (normalised): a value at the location is the sum of each master's value
/// times its weight. This is the model itself, applied to the masters one at a time.
pub(crate) fn master_weights(model: &Model, location: &[f64]) -> Vec<f64> {
    let n = model.len();
    let scalars = model.scalars(location);
    (0..n)
        .map(|m| {
            let mut unit = vec![0.0; n];
            unit[m] = 1.0;
            model.deltas(&unit).iter().zip(&scalars).map(|(d, s)| d * s).sum()
        })
        .collect()
}

/// The weighted sum of one value in every master.
pub(crate) fn mix(weights: &[f64], values: impl IntoIterator<Item = f64>) -> f64 {
    weights.iter().zip(values).map(|(w, v)| w * v).sum()
}

fn mix_points(weights: &[f64], points: &[Point]) -> Point {
    Point::new(mix(weights, points.iter().map(|p| p.x)), mix(weights, points.iter().map(|p| p.y)))
}

/// A glyph's shape at one location.
pub(crate) enum InstanceShape {
    Empty,
    /// Contours in the PostScript direction.
    Simple(Vec<Path>),
    /// Components: (name, offset).
    Composite(Vec<(String, Point)>),
}

/// The shape at the location whose master weights are `weights`. `shapes` holds the glyph in every master,
/// with the same structure (checked by the caller).
pub(crate) fn interpolate(shapes: &[Shape], weights: &[f64]) -> InstanceShape {
    match shapes.first() {
        None | Some(Shape::Empty) => InstanceShape::Empty,
        Some(Shape::Simple(first)) => {
            let mut out = Vec::with_capacity(first.len());
            for c in 0..first.len() {
                let paths: Vec<Path> = shapes
                    .iter()
                    .map(|s| match s {
                        Shape::Simple(cs) => Path::from_contour(&cs[c]),
                        _ => Path::from_contour(&first[c]),
                    })
                    .collect();
                let coords: Vec<Vec<Point>> = paths.iter().map(Path::coordinates).collect();
                let mixed: Vec<Point> = (0..coords[0].len())
                    .map(|k| {
                        let column: Vec<Point> = coords.iter().map(|cs| cs[k]).collect();
                        mix_points(weights, &column)
                    })
                    .collect();
                out.push(paths[0].with_coordinates(&mixed));
            }
            InstanceShape::Simple(out)
        }
        Some(Shape::Composite(first)) => {
            let comps = (0..first.len())
                .map(|k| {
                    let column: Vec<Point> = shapes
                        .iter()
                        .map(|s| match s {
                            Shape::Composite(cs) => Point::new(cs[k].1.x, cs[k].1.y),
                            _ => Point::new(first[k].1.x, first[k].1.y),
                        })
                        .collect();
                    (first[k].0.clone(), mix_points(weights, &column))
                })
                .collect();
            InstanceShape::Composite(comps)
        }
    }
}

/// Why a glyph keeps its overlapping contours.
#[derive(Clone, Debug, PartialEq)]
pub enum UnionFailure {
    /// The boolean operation failed.
    Failed(String),
    /// The union does not look like the glyph: the largest pixel difference, the total difference in pixels,
    /// and the box that holds the pixels that differ, in font units (x0, y0, x1, y1).
    Differs(u8, f64, Option<[f64; 4]>),
}

impl std::fmt::Display for UnionFailure {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            UnionFailure::Failed(e) => write!(f, "the union failed: {e}"),
            UnionFailure::Differs(max, total, place) => {
                write!(
                    f,
                    "the union differs from the glyph at {CHECK_PPEM} px/em: {max}/255 in one pixel, \
                     {total:.2} px in all"
                )?;
                match place {
                    Some([x0, y0, x1, y1]) => write!(f, ", between ({x0:.0}, {y0:.0}) and ({x1:.0}, {y1:.0})"),
                    None => Ok(()),
                }
            }
        }
    }
}

/// The union of all the contours under the non-zero rule, as contours in the PostScript direction (outer
/// counter-clockwise, holes clockwise).
pub(crate) fn union(paths: &[Path]) -> Result<Vec<Path>, UnionFailure> {
    let mut all = BezPath::new();
    for p in paths {
        all.extend(p.to_bezpath());
    }
    let contours = binary_op(&all, &BezPath::new(), FillRule::NonZero, BinaryOp::Union)
        .map_err(|e| UnionFailure::Failed(e.to_string()))?;
    Ok(oriented(&contours))
}

/// The contours of a union in the PostScript direction, without the slivers the sweep leaves where curves
/// touch (a few millionths of a unit wide). (Pieces too short to survive rounding are removed after rounding,
/// in `glyf.rs`.)
fn oriented(contours: &linesweeper::topology::Contours) -> Vec<Path> {
    let raw: Vec<Path> = contours
        .contours()
        .flat_map(|c| Path::from_bezpath(&c.path))
        .filter(|p| p.area().abs() > MIN_CONTOUR_AREA)
        .collect();
    // The contours of a union do not cross, so a contour's depth is the number of others that enclose any
    // point of it; even depths are outer contours (counter-clockwise), odd ones holes.
    let beziers: Vec<BezPath> = raw.iter().map(Path::to_bezpath).collect();
    let mut out = Vec::with_capacity(raw.len());
    for (i, path) in raw.iter().enumerate() {
        let probe = probe(i, &beziers);
        let depth = beziers.iter().enumerate().filter(|&(j, b)| j != i && kurbo::Shape::winding(b, probe) != 0).count();
        let outer = depth % 2 == 0;
        let ccw = path.area() > 0.0;
        out.push(if outer == ccw { path.clone() } else { path.reversed() });
    }
    out
}

/// A point of the contour `own` from which to ask which of the other contours enclose it: of the points a
/// third, a half and two thirds along each of its pieces, the one whose height is furthest from the height
/// of every point of the other contours.
///
/// The winding number is counted along a level ray. Two contours of a union often have level edges on one
/// line (the top of a bar on either side of a stem, the squares of a boxed plus), which the sweep returns a
/// few billionths of a unit apart. A ray from the middle of such an edge runs along the other contour's edge,
/// crosses it or not by that noise, and a counter was then taken for an outer contour and filled.
fn probe(own: usize, contours: &[BezPath]) -> Point {
    let heights: Vec<f64> = contours
        .iter()
        .enumerate()
        .filter(|&(j, _)| j != own)
        .flat_map(|(_, b)| b.elements())
        .flat_map(|el| match *el {
            PathEl::MoveTo(p) | PathEl::LineTo(p) => vec![p.y],
            PathEl::QuadTo(c, p) => vec![c.y, p.y],
            PathEl::CurveTo(c1, c2, p) => vec![c1.y, c2.y, p.y],
            PathEl::ClosePath => vec![],
        })
        .collect();
    let clear = |p: &Point| heights.iter().map(|y| (y - p.y).abs()).fold(f64::INFINITY, f64::min);
    contours[own]
        .segments()
        .flat_map(|seg| [1.0 / 3.0, 0.5, 2.0 / 3.0].map(|t| kurbo::ParamCurve::eval(&seg, t)))
        .max_by(|a, b| clear(a).total_cmp(&clear(b)))
        .unwrap_or(Point::ZERO)
}

/// Remove the overlaps of `paths` and check the result against the input by rasterising both. The sweep that
/// computes the union goes wrong on a few inputs in ten thousand (moving the contours apart by a hair, or
/// uniting them one at a time, does not cure those); the check catches them, and the glyph then keeps its
/// overlapping contours, which every rasteriser fills correctly.
pub(crate) fn remove_overlaps(paths: &[Path], upm: f64) -> Result<Vec<Path>, UnionFailure> {
    let out = union(paths)?;
    let (max, total) = compare(paths, &out, upm);
    if max > CHECK_MAX_PIXEL || total > CHECK_MAX_TOTAL {
        return Err(UnionFailure::Differs(max, total, difference_box(paths, &out, upm)));
    }
    Ok(out)
}

/// Contours of the union with a smaller area than this, in square font units, are slivers and are dropped.
const MIN_CONTOUR_AREA: f64 = 0.5;

/// The flattening tolerance of the raster check, in pixels.
const FLATTEN_TOLERANCE: f64 = 0.001;

/// The two sub-sample offsets of the raster check's frames, in samples.
const RASTER_OFFSETS: [(f64, f64); 2] = [(0.1, 0.7), (0.37, 0.11)];

/// Samples per pixel in each direction in the raster check.
const SUPERSAMPLE: u32 = 4;

/// Rasterise both outlines (non-zero fill, 4 × 4 samples per pixel) at [`CHECK_PPEM`] and return the largest difference
/// in one pixel and the total difference in pixels.
pub(crate) fn compare(a: &[Path], b: &[Path], upm: f64) -> (u8, f64) {
    // Two frames, offset differently: a straight edge that runs exactly through sample points in one frame
    // (where the rasteriser's tie-breaking depends on where the edge was split) does not in the other. A real
    // difference shows in both; the second frame is drawn only when the first disagrees, and the smaller
    // result is kept.
    let mut best: Option<(u8, f64)> = None;
    for offset in RASTER_OFFSETS {
        let Some((_, ra, rb)) = rasters_at(a, b, upm, offset) else {
            return (0, 0.0);
        };
        if ra.is_empty() && rb.is_empty() {
            return (u8::MAX, f64::INFINITY);
        }
        let mut max = 0u8;
        let mut total = 0u64;
        for (p, q) in ra.iter().zip(&rb) {
            let d = p.abs_diff(*q);
            max = max.max(d);
            total += u64::from(d);
        }
        let r = (max, total as f64 / 255.0);
        if best.is_none_or(|b| r.1 < b.1) {
            best = Some(r);
        }
        if max <= CHECK_MAX_PIXEL && r.1 <= CHECK_MAX_TOTAL {
            break; // agreement in one frame is enough
        }
    }
    best.unwrap_or((0, 0.0))
}

/// The pixels of the raster check's frame around the outlines, at each side.
const RASTER_MARGIN: f64 = 2.0;

/// The box that holds the points of both outlines: (x0, y0, x1, y1). `None` when both are empty.
fn frame(a: &[Path], b: &[Path]) -> Option<(f64, f64, f64, f64)> {
    let bounds = |ps: &[Path]| {
        ps.iter().flat_map(Path::coordinates).fold(None, |acc: Option<(f64, f64, f64, f64)>, p| {
            Some(match acc {
                None => (p.x, p.y, p.x, p.y),
                Some((x0, y0, x1, y1)) => (x0.min(p.x), y0.min(p.y), x1.max(p.x), y1.max(p.y)),
            })
        })
    };
    match (bounds(a), bounds(b)) {
        (None, None) => None,
        (Some(r), None) | (None, Some(r)) => Some(r),
        (Some(r), Some(s)) => Some((r.0.min(s.0), r.1.min(s.1), r.2.max(s.2), r.3.max(s.3))),
    }
}

/// The box that holds the pixels in which the two outlines differ by more than [`CHECK_MAX_PIXEL`], in font
/// units: where to look when a union is refused.
fn difference_box(a: &[Path], b: &[Path], upm: f64) -> Option<[f64; 4]> {
    let (x0, _, _, y1) = frame(a, b)?;
    let (w, ra, rb) = rasters_at(a, b, upm, RASTER_OFFSETS[0])?;
    let scale = CHECK_PPEM / upm;
    let mut found: Option<[f64; 4]> = None;
    for (i, (p, q)) in ra.iter().zip(&rb).enumerate() {
        if p.abs_diff(*q) <= CHECK_MAX_PIXEL {
            continue;
        }
        let (col, row) = ((i as u32 % w) as f64, (i as u32 / w) as f64);
        let (x, y) = (x0 + (col - RASTER_MARGIN) / scale, y1 - (row - RASTER_MARGIN) / scale);
        let (right, low) = (x + 1.0 / scale, y - 1.0 / scale);
        found = Some(match found {
            None => [x, low, right, y],
            Some([a0, b0, a1, b1]) => [a0.min(x), b0.min(low), a1.max(right), b1.max(y)],
        });
    }
    found
}

/// Both outlines rasterised in the same frame, shifted by `offset` samples: (width, coverage of `a`, coverage
/// of `b`), row by row; `None` when both are empty, two empty images when the rasteriser could not make them.
pub(crate) fn rasters_at(a: &[Path], b: &[Path], upm: f64, offset: (f64, f64)) -> Option<(u32, Vec<u8>, Vec<u8>)> {
    let (x0, y0, x1, y1) = frame(a, b)?;
    let scale = CHECK_PPEM / upm;
    let margin = RASTER_MARGIN;
    let w = ((x1 - x0) * scale + 2.0 * margin).ceil().max(1.0) as u32;
    let h = ((y1 - y0) * scale + 2.0 * margin).ceil().max(1.0) as u32;
    // Each pixel is sampled SUPERSAMPLE × SUPERSAMPLE times without anti-aliasing (the non-zero rule at each
    // sample point, which leaves no seams where contours overlap), and the samples are averaged.
    let n = SUPERSAMPLE;
    let fine = scale * f64::from(n);
    let draw = |ps: &[Path]| -> Option<Vec<u8>> {
        let (fw, fh) = (w * n, h * n);
        let mut mask = tiny_skia::Mask::new(fw, fh)?;
        let mut pb = tiny_skia::PathBuilder::new();
        let tx = |p: Point| {
            (
                ((p.x - x0) * fine + margin * f64::from(n) + offset.0) as f32,
                ((y1 - p.y) * fine + margin * f64::from(n) + offset.1) as f32,
            )
        };
        // Curves are flattened here, finely, so that the rasteriser's own flattening, which depends on how a
        // curve happens to be split, does not show up as a difference.
        for p in ps {
            kurbo::flatten(p.to_bezpath(), FLATTEN_TOLERANCE / scale, |el| match el {
                PathEl::MoveTo(q) => {
                    let (x, y) = tx(q);
                    pb.move_to(x, y);
                }
                PathEl::LineTo(q) => {
                    let (x, y) = tx(q);
                    pb.line_to(x, y);
                }
                PathEl::ClosePath => pb.close(),
                PathEl::QuadTo(..) | PathEl::CurveTo(..) => {}
            });
        }
        if let Some(path) = pb.finish() {
            mask.fill_path(&path, tiny_skia::FillRule::Winding, false, tiny_skia::Transform::identity());
        }
        let data = mask.data();
        let mut out = vec![0u8; (w * h) as usize];
        let per = n * n;
        for y in 0..h {
            for x in 0..w {
                let mut sum = 0u32;
                for sy in 0..n {
                    let row = ((y * n + sy) * fw + x * n) as usize;
                    sum += data[row..row + n as usize].iter().map(|&v| u32::from(v)).sum::<u32>();
                }
                out[(y * w + x) as usize] = ((sum + per / 2) / per) as u8;
            }
        }
        Some(out)
    };
    match (draw(a), draw(b)) {
        (Some(ra), Some(rb)) => Some((w, ra, rb)),
        _ => Some((w, Vec::new(), Vec::new())),
    }
}

type UnionResult = Option<Result<Vec<Path>, UnionFailure>>;

/// The union of each simple glyph's contours (`None` for other glyphs), computed on several threads.
pub(crate) fn parallel_unions(shapes: &[InstanceShape], upm: f64) -> Vec<UnionResult> {
    let threads = std::thread::available_parallelism().map_or(1, |n| n.get()).clamp(1, 16);
    let chunk = shapes.len().div_ceil(threads).max(1);
    let run = |s: &InstanceShape| -> UnionResult {
        match s {
            InstanceShape::Simple(paths) => Some(
                std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| remove_overlaps(paths, upm)))
                    .unwrap_or_else(|_| Err(UnionFailure::Failed("the boolean operation panicked".into()))),
            ),
            _ => None,
        }
    };
    std::thread::scope(|scope| {
        let handles: Vec<_> = shapes
            .chunks(chunk)
            .map(|part| (part.len(), scope.spawn(move || part.iter().map(run).collect::<Vec<_>>())))
            .collect();
        handles
            .into_iter()
            .flat_map(|(n, h)| {
                h.join().unwrap_or_else(|_| vec![Some(Err(UnionFailure::Failed("a worker panicked".into()))); n])
            })
            .collect()
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use rachis_kernel::pen::{polygon, rect};
    use rachis_kernel::pt;

    fn paths(cs: &[rachis_kernel::Contour]) -> Vec<Path> {
        cs.iter().map(Path::from_contour).collect()
    }

    #[test]
    fn two_crossing_bars_become_one_contour_that_looks_the_same() {
        let plus = paths(&[rect(100.0, 250.0, 500.0, 350.0), rect(250.0, 100.0, 350.0, 500.0)]);
        let merged = remove_overlaps(&plus, 1000.0).unwrap();
        assert_eq!(merged.len(), 1);
        let area: f64 = merged.iter().map(Path::area).sum();
        assert!((area - (2.0 * 40_000.0 - 10_000.0)).abs() < 1e-3, "{area}");
        let (max, total) = compare(&plus, &merged, 1000.0);
        assert!(max <= 2 && total < 0.1, "{max} {total}");
    }

    #[test]
    fn a_counter_stays_a_hole() {
        // .notdef: an outer box and a reversed inner box
        let boxed = paths(&[rect(80.0, 0.0, 520.0, 714.0), rect(140.0, 60.0, 460.0, 654.0).reversed()]);
        let merged = remove_overlaps(&boxed, 1000.0).unwrap();
        assert_eq!(merged.len(), 2);
        let mut areas: Vec<f64> = merged.iter().map(Path::area).collect();
        areas.sort_by(f64::total_cmp);
        assert!(areas[0] < 0.0 && areas[1] > 0.0);
    }

    #[test]
    fn a_counter_is_asked_for_away_from_the_level_edges_it_shares_a_line_with() {
        // a box with a spur: the top of its lower bar is the counter's lower edge to the right of the first
        // stem and the outline's edge to the left of it, on one line but for the noise a sweep leaves
        let outer = polygon(&[
            pt(0.0, 0.0),
            pt(600.0, 0.0),
            pt(600.0, 700.0),
            pt(200.0, 700.0),
            pt(200.0, 100.0 + 1e-9),
            pt(0.0, 100.0 - 1e-9),
        ]);
        let counter = polygon(&[pt(300.0, 100.0), pt(500.0, 100.0), pt(500.0, 600.0), pt(300.0, 600.0)]);
        let beziers: Vec<BezPath> = [&outer, &counter].map(|c| Path::from_contour(c).to_bezpath()).to_vec();
        // the middle of the counter's first piece is on that line, and a level ray from it is what went wrong
        let first = kurbo::ParamCurve::eval(&beziers[1].segments().next().unwrap(), 0.5);
        assert_eq!(first.y, 100.0);
        let chosen = probe(1, &beziers);
        assert!((chosen.y - 100.0).abs() > 50.0 && (chosen.y - 700.0).abs() > 50.0, "{chosen:?}");
        assert_ne!(kurbo::Shape::winding(&beziers[0], chosen), 0, "the counter lies inside the outline");
        // and the outline is enclosed by nothing
        assert_eq!(kurbo::Shape::winding(&beziers[1], probe(0, &beziers)), 0);
    }

    #[test]
    fn the_check_catches_a_changed_shape() {
        let a = paths(&[rect(0.0, 0.0, 500.0, 500.0)]);
        let b = paths(&[polygon(&[pt(0.0, 0.0), pt(500.0, 0.0), pt(500.0, 480.0), pt(0.0, 500.0)])]);
        let (_, total) = compare(&a, &b, 1000.0);
        assert!(total > CHECK_MAX_TOTAL, "{total}");
    }

    #[test]
    fn weights_reproduce_the_masters() {
        let m = Model::new(&[vec![-1.0], vec![0.0], vec![1.0]]).unwrap();
        let w = master_weights(&m, &[0.5]);
        assert!((mix(&w, [60.0, 88.0, 134.0]) - 111.0).abs() < 1e-12);
        let w = master_weights(&m, &[-1.0]);
        assert!((mix(&w, [60.0, 88.0, 134.0]) - 60.0).abs() < 1e-12);
    }
}

#[cfg(test)]
mod exactness {
    use super::*;
    use std::collections::BTreeMap;

    /// Every point of the union's boundary lies on the input's boundary, for every glyph of every master:
    /// linesweeper splits curves but does not move them.
    #[test]
    fn the_union_lies_on_the_input() {
        let reg = rachis_glyphs::registry();
        let mut worst_all: f64 = 0.0;
        let mut strays: Vec<String> = Vec::new();
        let (mut glyphs, mut rejected) = (0, 0);
        for p in rachis_kernel::params::masters() {
            let all = rachis_kernel::build_all(&reg, &p);
            let index: BTreeMap<&str, usize> = all.iter().enumerate().map(|(i, g)| (g.name.as_str(), i)).collect();
            for gi in 0..all.len() {
                let Ok(Shape::Simple(cs)) = crate::outline::shape_of(&all, &index, gi) else {
                    continue;
                };
                let paths: Vec<Path> = cs.iter().map(Path::from_contour).collect();
                // a union the raster check rejects never reaches a font; the others must lie on the input
                let Ok(out) = remove_overlaps(&paths, p.upm) else {
                    rejected += 1;
                    continue;
                };
                let segs: Vec<kurbo::PathSeg> =
                    paths.iter().flat_map(|p| p.to_bezpath().segments().collect::<Vec<_>>()).collect();
                let mut worst: f64 = 0.0;
                for o in &out {
                    for seg in o.to_bezpath().segments() {
                        for k in 0..=4 {
                            let q = kurbo::ParamCurve::eval(&seg, f64::from(k) / 4.0);
                            let d = segs
                                .iter()
                                .map(|s| kurbo::ParamCurveNearest::nearest(s, q, 1e-9).distance_sq.sqrt())
                                .fold(f64::MAX, f64::min);
                            worst = worst.max(d);
                        }
                    }
                }
                // a sliver thinner than the check can see may leave the input by a few units
                if worst >= 5.0 {
                    strays.push(format!("{} [{}]: {worst:.2}", all[gi].name, p.name));
                }
                worst_all = worst_all.max(worst);
                glyphs += 1;
            }
        }
        println!(
            "{glyphs} glyph masters: the union is at most {worst_all:.6} units from the input; {rejected} rejected"
        );
        assert!(strays.is_empty(), "{strays:#?}");
        assert!(rejected * 500 < glyphs, "{rejected} unions of {glyphs} rejected");
    }
}
