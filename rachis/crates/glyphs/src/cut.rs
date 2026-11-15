//! Cutting a long sign into the pieces a typesetter assembles one of any length from.
//!
//! An arrow, a brace over a group or a bracket under one is a few shapes (a head, a hook, a cusp) joined by a
//! level run whose cross-section is the same everywhere. A typesetter that needs the sign at a given length
//! takes the shapes as they are and repeats a piece of the run between them. This module finds the shapes and
//! the run in the outline of the sign drawn long. It samples the cross-section along the sign, takes the most
//! frequent one for the run's, and cuts the outline plumb, a joint's length into the run on each side of
//! everything that differs from it. Nothing is drawn again, so a piece is the sign's own outline, and a sign
//! whose run is not level (a wave) is found to have no pieces.

use std::collections::BTreeMap;

use rachis_kernel::geom::flatten;
use rachis_kernel::{Contour, Glyph, Seg, V, pt};

/// How far the level run reaches into each piece that joins another: the two overlap by any part of it.
pub const JOINT: f64 = 120.0;

/// The length of the piece of level run that is repeated.
pub const RUN: f64 = 200.0;

/// The distance between two cross-sections that are compared.
const STEP: f64 = 2.0;

/// One piece of a sign cut for assembling: its outline with its left end at the origin, its length, how much
/// of its start and of its end is level run, and whether it is the run itself, which may be repeated.
#[derive(Clone, Debug, PartialEq)]
pub struct Cut {
    pub contours: Vec<Contour>,
    pub length: f64,
    pub start: f64,
    pub end: f64,
    pub run: bool,
}

/// A cross-section: the stretches of a plumb line that are inside the outline, bottom to top.
type Section = Vec<(f64, f64)>;

/// The outlines as closed polygons, within a tenth of a unit.
fn polygons(contours: &[Contour]) -> Vec<Vec<V>> {
    contours.iter().map(|c| c.segs.iter().flat_map(|s| flatten(s, 0.1)).collect()).collect()
}

/// The stretches of the plumb line at `x` that are inside the outline, bottom to top: the cross-section there.
fn cross_section(polygons: &[Vec<V>], x: f64) -> Section {
    let mut crossings: Vec<(f64, i32)> = Vec::new();
    for polygon in polygons {
        for (i, &b) in polygon.iter().enumerate() {
            let a = polygon[(i + polygon.len() - 1) % polygon.len()];
            if (a.x > x) != (b.x > x) {
                let y = a.y + (x - a.x) * (b.y - a.y) / (b.x - a.x);
                crossings.push((y, if b.x > a.x { 1 } else { -1 }));
            }
        }
    }
    crossings.sort_by(|a, b| a.0.total_cmp(&b.0));
    let mut inside = Section::new();
    let (mut winding, mut from) = (0, 0.0);
    for (y, turn) in crossings {
        if winding == 0 {
            from = y;
        }
        winding += turn;
        if winding == 0 {
            match inside.last_mut() {
                // two contours that meet edge to edge are one stretch
                Some(last) if last.1 >= from - SAME => last.1 = y,
                _ => inside.push((from, y)),
            }
        }
    }
    inside
}

/// Two cross-sections are the same if no edge of one is further than this from the other's.
const SAME: f64 = 0.05;

fn same(a: &[(f64, f64)], b: &[(f64, f64)]) -> bool {
    a.len() == b.len() && a.iter().zip(b).all(|(a, b)| (a.0 - b.0).abs() < SAME && (a.1 - b.1).abs() < SAME)
}

/// The cross-section that most of `sections` have: the run's. They are counted by their edges to the nearest
/// unit, and the run's is the middle one of those counted most often, so that an edge which lies between two
/// units is not taken for two cross-sections.
fn most_frequent(sections: &[Section]) -> Option<Section> {
    let units = |s: &Section| s.iter().map(|&(a, b)| (a.round() as i64, b.round() as i64)).collect::<Vec<_>>();
    let mut seen: BTreeMap<Vec<(i64, i64)>, Vec<&Section>> = BTreeMap::new();
    for section in sections {
        seen.entry(units(section)).or_default().push(section);
    }
    // of two counted as often, the one that sorts first
    let (_, members) = seen.iter().max_by(|a, b| a.1.len().cmp(&b.1.len()).then_with(|| b.0.cmp(a.0)))?;
    let middle = |pick: &dyn Fn(&(f64, f64)) -> f64, k: usize| {
        let mut values: Vec<f64> = members.iter().map(|m| pick(&m[k])).collect();
        values.sort_by(f64::total_cmp);
        values[values.len() / 2]
    };
    Some((0..members[0].len()).map(|k| (middle(&|e| e.0, k), middle(&|e| e.1, k))).collect())
}

/// The parameters in (0, 1) at which `seg` crosses the plumb line at `c`, ascending.
fn crossings(seg: &Seg, c: f64) -> Vec<f64> {
    match *seg {
        Seg::Line(a, b) => {
            if (a.x - c) * (b.x - c) < 0.0 {
                vec![(c - a.x) / (b.x - a.x)]
            } else {
                Vec::new()
            }
        }
        Seg::Cubic(p0, c1, c2, p3) => {
            let xs = [p0.x, c1.x, c2.x, p3.x];
            if xs.iter().all(|&x| x > c) || xs.iter().all(|&x| x < c) {
                return Vec::new();
            }
            // Between two stationary points the curve crosses the line at most once. A point on the line counts
            // as left of it, so a crossing that falls exactly on a stationary point is found in one of the two
            // stretches that meet there, and not in both or in neither.
            let mut stops = vec![0.0];
            stops.extend(seg.extrema());
            stops.push(1.0);
            let right = |t: f64| seg.at(t).x > c;
            let mut found = Vec::new();
            for pair in stops.windows(2) {
                let (mut lo, mut hi) = (pair[0], pair[1]);
                if right(lo) == right(hi) {
                    continue;
                }
                for _ in 0..60 {
                    let mid = (lo + hi) / 2.0;
                    if right(lo) == right(mid) {
                        lo = mid;
                    } else {
                        hi = mid;
                    }
                }
                let t = (lo + hi) / 2.0;
                if t > 1e-9 && t < 1.0 - 1e-9 {
                    found.push(t);
                }
            }
            found
        }
    }
}

/// The part of a closed outline on one side of the plumb line at `c` (`right`: the part to its right), closed
/// again along the line. `None` if the outline does not cross the line an even number of times, as a closed
/// outline that does not cross itself must.
fn half(contour: &Contour, c: f64, right: bool) -> Option<Vec<Contour>> {
    let side = |z: V| if right { z.x - c } else { c - z.x };
    let mut pieces: Vec<Seg> = Vec::new();
    for seg in &contour.segs {
        let (mut rest, mut done) = (*seg, 0.0);
        for t in crossings(seg, c) {
            let (before, after) = rest.split((t - done) / (1.0 - done));
            pieces.push(before);
            (rest, done) = (after, t);
        }
        pieces.push(rest);
    }
    let kept: Vec<bool> = pieces.iter().map(|s| side(s.at(0.5)) > 1e-7).collect();
    if kept.iter().all(|&k| k) {
        return Some(vec![contour.clone()]);
    }
    if !kept.iter().any(|&k| k) {
        return Some(Vec::new());
    }
    // the runs of kept pieces: each starts on the line and ends on it
    let n = pieces.len();
    let mut runs: Vec<Vec<Seg>> = Vec::new();
    for first in (0..n).filter(|&i| kept[i] && !kept[(i + n - 1) % n]) {
        let mut run = Vec::new();
        let mut i = first;
        while kept[i] {
            run.push(pieces[i]);
            i = (i + 1) % n;
        }
        runs.push(run);
    }
    // along the line, the outline's inside lies between the first and the second crossing, the third and the
    // fourth, and so on: there a run that ends is closed to the run that starts
    let mut ends: Vec<(f64, usize, bool)> = Vec::new();
    for (k, run) in runs.iter().enumerate() {
        ends.push((run[0].start().y, k, true));
        ends.push((run[run.len() - 1].end().y, k, false));
    }
    ends.sort_by(|a, b| a.0.total_cmp(&b.0));
    let mut next: Vec<Option<usize>> = vec![None; runs.len()];
    for pair in ends.chunks(2) {
        match (pair[0], pair[1]) {
            ((_, starting, true), (_, ending, false)) | ((_, ending, false), (_, starting, true)) => {
                next[ending] = Some(starting);
            }
            _ => return None,
        }
    }
    let mut used = vec![false; runs.len()];
    let mut closed = Vec::new();
    for first in 0..runs.len() {
        if used[first] {
            continue;
        }
        let mut segs: Vec<Seg> = Vec::new();
        let mut k = first;
        loop {
            used[k] = true;
            segs.extend(runs[k].iter().copied());
            let from = pt(c, runs[k][runs[k].len() - 1].end().y);
            let following = next[k]?;
            let to = pt(c, runs[following][0].start().y);
            if (to.y - from.y).abs() > 1e-9 {
                segs.push(Seg::Line(from, to));
            }
            k = following;
            if k == first {
                break;
            }
            if used[k] {
                return None;
            }
        }
        // the ends of the runs are on the line to within rounding: put them on it
        let count = segs.len();
        for i in 0..count {
            let end = segs[i].end();
            if (end.x - c).abs() < 1e-6 {
                let on = pt(c, end.y);
                segs[i] = with_end(&segs[i], on);
                segs[(i + 1) % count] = with_start(&segs[(i + 1) % count], on);
            }
        }
        closed.push(Contour::new(segs));
    }
    Some(closed)
}

fn with_start(seg: &Seg, z: V) -> Seg {
    match *seg {
        Seg::Line(_, b) => Seg::Line(z, b),
        Seg::Cubic(_, c1, c2, p3) => Seg::Cubic(z, c1, c2, p3),
    }
}

fn with_end(seg: &Seg, z: V) -> Seg {
    match *seg {
        Seg::Line(a, _) => Seg::Line(a, z),
        Seg::Cubic(p0, c1, c2, _) => Seg::Cubic(p0, c1, c2, z),
    }
}

/// The stretches of the plumb line at `x` that are inside the outlines, bottom to top.
pub fn up(contours: &[Contour], x: f64) -> Vec<(f64, f64)> {
    cross_section(&polygons(contours), x)
}

/// The stretches of the level line at `y` that are inside the outlines, left to right.
pub fn along(contours: &[Contour], y: f64) -> Vec<(f64, f64)> {
    let turned: Vec<Vec<V>> =
        polygons(contours).iter().map(|poly| poly.iter().map(|z| pt(z.y, z.x)).collect()).collect();
    cross_section(&turned, y)
}

/// What of the outlines lies between the plumb lines at `x0` and `x1`, moved so that `x0` is the origin.
fn band(contours: &[Contour], x0: f64, x1: f64) -> Option<Vec<Contour>> {
    let mut out = Vec::new();
    for contour in contours {
        for part in half(contour, x0, true)? {
            out.extend(half(&part, x1, false)?);
        }
    }
    let by = pt(-x0, 0.0);
    Some(out.iter().map(|c| c.mapped(|z| z + by)).collect())
}

/// The pieces of the sign `g`, left to right, or `None` if it has no level run that is long enough between its
/// shapes: every stretch of run must hold a joint on each side and the piece that is repeated.
pub fn pieces(g: &Glyph) -> Option<Vec<Cut>> {
    let (x0, _, x1, _) = g.bounds()?;
    let polygons = polygons(&g.contours);
    let count = ((x1 - x0) / STEP).floor() as usize;
    if count < 8 {
        return None;
    }
    // the cross-sections a step apart, the first and the last half a step inside the ends
    let at = |i: usize| x0 + STEP * (i as f64 + 0.5);
    let sections: Vec<Section> = (0..count).map(|i| cross_section(&polygons, at(i))).collect();
    let level = most_frequent(&sections)?;
    if level.is_empty() {
        return None;
    }
    // the shapes: every stretch whose cross-section is not the run's, a step wider on each side
    let mut shapes: Vec<(f64, f64)> = Vec::new();
    let mut i = 0;
    while i < count {
        if same(&sections[i], &level) {
            i += 1;
            continue;
        }
        let first = i;
        while i < count && !same(&sections[i], &level) {
            i += 1;
        }
        let from = if first == 0 { x0 } else { at(first) - STEP };
        let to = if i == count { x1 } else { at(i - 1) + STEP };
        match shapes.last_mut() {
            // a shape may have the run's cross-section somewhere, as an arrowhead does where it is as tall
            // as the shaft: a stretch shorter than a joint is not run, and what it parts is one shape
            Some(last) if from - last.1 < JOINT => last.1 = to,
            _ => shapes.push((if from - x0 < JOINT { x0 } else { from }, to)),
        }
    }
    if let Some(last) = shapes.last_mut().filter(|last| x1 - last.1 < JOINT) {
        last.1 = x1;
    }
    // an end of the sign where the run simply stops is a shape with no length: its piece is a joint of run,
    // which keeps the end of the sign from being a piece that is repeated
    if shapes.first().is_none_or(|s| s.0 > x0) {
        shapes.insert(0, (x0, x0));
    }
    if shapes.last().is_none_or(|s| s.1 < x1) {
        shapes.push((x1, x1));
    }
    // between two shapes the run holds a joint for each and the piece that is repeated
    let runs: Vec<(f64, f64)> = shapes.windows(2).map(|pair| (pair[0].1, pair[1].0)).collect();
    if runs.iter().any(|&(a, b)| b - a < RUN + 2.0 * JOINT) {
        return None;
    }
    let (longest_from, longest_to) = *runs.iter().max_by(|a, b| (a.1 - a.0).total_cmp(&(b.1 - b.0)))?;
    let middle = (longest_from + longest_to) / 2.0;
    let run = Cut {
        contours: band(&g.contours, middle - RUN / 2.0, middle + RUN / 2.0)?,
        length: RUN,
        start: RUN,
        end: RUN,
        run: true,
    };
    let mut out = Vec::new();
    for (k, &(from, to)) in shapes.iter().enumerate() {
        let (first, last) = (k == 0, k + 1 == shapes.len());
        let a = if first { x0 } else { from - JOINT };
        let b = if last { x1 } else { to + JOINT };
        out.push(Cut {
            contours: band(&g.contours, a, b)?,
            length: b - a,
            start: if first { 0.0 } else { JOINT },
            end: if last { 0.0 } else { JOINT },
            run: false,
        });
        if !last {
            out.push(run.clone());
        }
    }
    Some(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rect(x0: f64, y0: f64, x1: f64, y1: f64) -> Contour {
        let z = [pt(x0, y0), pt(x0, y1), pt(x1, y1), pt(x1, y0)];
        Contour::new((0..4).map(|i| Seg::Line(z[i], z[(i + 1) % 4])).collect())
    }

    fn glyph(contours: Vec<Contour>) -> Glyph {
        Glyph { name: "test".into(), contours, ..Glyph::default() }
    }

    fn area(contours: &[Contour]) -> f64 {
        contours.iter().map(|c| c.area().abs()).sum()
    }

    #[test]
    fn a_bar_is_a_run_between_two_ends_of_a_joint_each() {
        let cuts = pieces(&glyph(vec![rect(40.0, 200.0, 1040.0, 260.0)])).expect("a bar has a level run");
        assert_eq!(cuts.iter().map(|c| c.run).collect::<Vec<_>>(), [false, true, false]);
        assert_eq!((cuts[0].length, cuts[0].start, cuts[0].end), (JOINT, 0.0, JOINT));
        assert_eq!((cuts[1].length, cuts[1].start, cuts[1].end), (RUN, RUN, RUN));
        assert_eq!((cuts[2].length, cuts[2].start, cuts[2].end), (JOINT, JOINT, 0.0));
        assert!((area(&cuts[1].contours) - RUN * 60.0).abs() < 1e-6);
        assert!((area(&cuts[0].contours) - JOINT * 60.0).abs() < 1e-6);
    }

    #[test]
    fn a_bar_with_a_head_is_an_end_a_run_and_the_head() {
        // a shaft from 0 to 1000 and a block at its right end, taller than it
        let g = glyph(vec![rect(0.0, 200.0, 1000.0, 260.0), rect(900.0, 100.0, 1000.0, 360.0)]);
        let cuts = pieces(&g).expect("a level run");
        assert_eq!(cuts.iter().map(|c| c.run).collect::<Vec<_>>(), [false, true, false]);
        let head = &cuts[2];
        // the head piece is the block and a joint of shaft, to within the step the block was found by
        assert!((head.length - (100.0 + JOINT)).abs() <= 2.0 * STEP, "{}", head.length);
        assert_eq!((head.start, head.end), (JOINT, 0.0));
        let bounds = glyph(head.contours.clone()).bounds().unwrap();
        assert!(bounds.0.abs() < 1e-9 && (bounds.2 - head.length).abs() < 1e-9, "{bounds:?}");
        assert_eq!((bounds.1, bounds.3), (100.0, 360.0));
    }

    #[test]
    fn a_shape_in_the_middle_has_a_run_on_each_side() {
        let g = glyph(vec![rect(0.0, 0.0, 2000.0, 50.0), rect(950.0, 0.0, 1050.0, 200.0)]);
        let cuts = pieces(&g).expect("a level run");
        assert_eq!(cuts.iter().map(|c| c.run).collect::<Vec<_>>(), [false, true, false, true, false]);
        assert_eq!((cuts[2].start, cuts[2].end), (JOINT, JOINT));
        assert!((cuts[2].length - (100.0 + 2.0 * JOINT)).abs() <= 4.0 * STEP);
        // every piece meets its neighbour in the run's cross-section: 50 units from the baseline
        for cut in &cuts {
            let polygons = polygons(&cut.contours);
            for x in [1.0, cut.length - 1.0] {
                let inner = (x < 2.0 && cut.start > 0.0) || (x > 2.0 && cut.end > 0.0);
                if inner {
                    assert_eq!(cross_section(&polygons, x), [(0.0, 50.0)]);
                }
            }
        }
    }

    #[test]
    fn a_shape_that_is_as_tall_as_the_run_somewhere_is_still_one_shape() {
        // a head that widens from a point: where it is as tall as the shaft its cross-section is the shaft's
        let head = Contour::new(vec![
            Seg::Line(pt(0.0, 100.0), pt(200.0, 300.0)),
            Seg::Line(pt(200.0, 300.0), pt(200.0, -100.0)),
            Seg::Line(pt(200.0, -100.0), pt(0.0, 100.0)),
        ]);
        let cuts = pieces(&glyph(vec![head, rect(100.0, 70.0, 1500.0, 130.0)])).expect("a level run");
        assert_eq!(cuts.iter().map(|c| c.run).collect::<Vec<_>>(), [false, true, false]);
        assert!((cuts[0].length - (200.0 + JOINT)).abs() <= 2.0 * STEP, "{}", cuts[0].length);
        assert_eq!(cuts[2].length, JOINT);
    }

    #[test]
    fn an_edge_between_two_tenths_is_one_cross_section() {
        // the bar's edge lies where rounding goes either way, and the outline is not exact
        let wobble = |i: usize| 183.05 + 1e-9 * if i.is_multiple_of(2) { 1.0 } else { -1.0 };
        let top: Vec<V> = (0..=30).map(|i| pt(50.0 * i as f64, wobble(i))).collect();
        let mut points = vec![pt(1500.0, 100.0), pt(0.0, 100.0)];
        points.extend(top);
        let n = points.len();
        let bar = Contour::new((0..n).map(|i| Seg::Line(points[i], points[(i + 1) % n])).collect());
        let cuts = pieces(&glyph(vec![bar])).expect("a level run");
        assert_eq!(cuts.iter().map(|c| c.length).collect::<Vec<_>>(), [JOINT, RUN, JOINT]);
    }

    #[test]
    fn a_curve_is_cut_where_it_crosses_and_closed_along_the_line() {
        // a disc of radius 100 about (0, 0), as four quarter circles: its right half is half its area
        let k = 0.552_284_749_830_793_4 * 100.0;
        let quarter = |a: V, c1: V, c2: V, b: V| Seg::Cubic(a, c1, c2, b);
        let disc = Contour::new(vec![
            quarter(pt(100.0, 0.0), pt(100.0, k), pt(k, 100.0), pt(0.0, 100.0)),
            quarter(pt(0.0, 100.0), pt(-k, 100.0), pt(-100.0, k), pt(-100.0, 0.0)),
            quarter(pt(-100.0, 0.0), pt(-100.0, -k), pt(-k, -100.0), pt(0.0, -100.0)),
            quarter(pt(0.0, -100.0), pt(k, -100.0), pt(100.0, -k), pt(100.0, 0.0)),
        ]);
        let whole = disc.area().abs();
        let right = half(&disc, 30.0, true).expect("a closed outline");
        let left = half(&disc, 30.0, false).expect("a closed outline");
        assert_eq!((right.len(), left.len()), (1, 1));
        assert!((area(&right) + area(&left) - whole).abs() < 1e-6);
        let b = glyph(right).bounds().unwrap();
        assert!((b.0 - 30.0).abs() < 1e-9 && (b.2 - 100.0).abs() < 1e-9, "{b:?}");
        // a line that misses it leaves it whole or leaves nothing
        assert_eq!(half(&disc, 150.0, false), Some(vec![disc.clone()]));
        assert_eq!(half(&disc, 150.0, true), Some(Vec::new()));
    }

    #[test]
    fn a_curve_that_crosses_exactly_where_it_is_highest_is_still_cut() {
        // an arch from (0, 0) to (2, 0): x runs steadily, and the arch is highest at t = 1/2, where x is 1
        let arch = Seg::Cubic(pt(0.0, 0.0), pt(0.5, 1.0), pt(1.5, 1.0), pt(2.0, 0.0));
        assert_eq!(arch.at(0.5).x, 1.0);
        assert!(arch.extrema().contains(&0.5), "{:?}", arch.extrema());
        let found = crossings(&arch, 1.0);
        assert_eq!(found.len(), 1, "{found:?}");
        assert!((found[0] - 0.5).abs() < 1e-9);
        // and so is the closed shape under it: its two halves are the whole
        let shape = Contour::new(vec![arch, Seg::Line(pt(2.0, 0.0), pt(0.0, 0.0))]);
        let (left, right) = (half(&shape, 1.0, false).unwrap(), half(&shape, 1.0, true).unwrap());
        assert_eq!((left.len(), right.len()), (1, 1));
        assert!((area(&left) + area(&right) - shape.area().abs()).abs() < 1e-9);
        assert!((area(&left) - area(&right)).abs() < 1e-9);
    }

    #[test]
    fn a_sign_without_a_level_run_has_no_pieces() {
        // a zigzag: its cross-section is never the same twice in a row
        let mut top: Vec<V> =
            (0..=40).map(|i| pt(25.0 * f64::from(i), if i % 2 == 0 { 60.0 } else { 120.0 })).collect();
        let mut points: Vec<V> = top.iter().map(|z| pt(z.x, z.y - 50.0)).collect();
        top.reverse();
        points.extend(top);
        let n = points.len();
        let wave = Contour::new((0..n).map(|i| Seg::Line(points[i], points[(i + 1) % n])).collect());
        assert_eq!(pieces(&glyph(vec![wave])), None);
        // and a sign too short for a joint and a run has none either
        assert_eq!(pieces(&glyph(vec![rect(0.0, 0.0, 250.0, 50.0), rect(0.0, 0.0, 40.0, 200.0)])), None);
    }
}
