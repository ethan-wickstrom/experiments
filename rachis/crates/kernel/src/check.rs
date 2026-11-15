//! Structural checks on glyph programs: what must hold before a font is built from them.

use crate::geom::V;
use crate::glyph::{Glyph, Registry};
use crate::params::{Params, faces};

/// Glyphs may reach this far past the cell's sides before the check remarks on it.
const SIDE_ALLOWANCE: f64 = 4.0;

/// Characters without ink that `char::is_whitespace` does not count: the zero-width space, non-joiner and
/// joiner, the word joiner, the byte-order mark, soft hyphen aside (it is drawn), and the blank Braille pattern.
const BLANK: [u32; 6] = [0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x2800];

#[derive(Debug, Default)]
pub struct Report {
    /// What must be fixed.
    pub problems: Vec<String>,
    /// What is worth a look.
    pub notes: Vec<String>,
}

/// Check the glyphs called `names` (every registered glyph when `None`) in all six masters.
pub fn check_glyphs(registry: &Registry, names: Option<&[String]>) -> Report {
    let mut report = Report::default();
    let all: Vec<String>;
    let names = match names {
        Some(n) => n,
        None => {
            all = registry.specs.iter().map(|s| s.name.clone()).collect();
            &all
        }
    };
    for name in names {
        let Some(spec) = registry.get(name) else {
            report.problems.push(format!("{name}: no such glyph"));
            continue;
        };
        for group in faces().into_iter().filter(|f| f.has(spec.module)).map(|f| f.masters) {
            let built: Vec<(&Params, Glyph)> = group.iter().map(|p| (p, registry.build(spec, p))).collect();
            let mut failed = false;
            for (p, g) in &built {
                if p.mono && g.advance != if spec.opt.mark { 0.0 } else { spec.opt.advance.unwrap_or(p.width) } {
                    report.problems.push(format!("{name} [{}]: advance {} in a fixed-pitch face", p.name, g.advance));
                }
                for e in &g.errors {
                    report.problems.push(format!("{name} [{}]: {e}", p.name));
                    failed = true;
                }
            }
            if failed {
                continue;
            }
            let first = built[0].1.signature();
            if built.iter().any(|(_, g)| g.signature() != first) {
                let names: Vec<&str> = group.iter().map(|p| p.name).collect();
                let sigs: Vec<String> = built.iter().map(|(_, g)| g.signature()).collect();
                report.problems.push(format!(
                    "{name}: masters {} differ in structure, so they cannot be interpolated: {}",
                    names.join(", "),
                    sigs.join(" | ")
                ));
            }
            // Between two masters every point of a contour moves in a straight line to its counterpart. If a
            // contour's size passes through zero on the way (a counter that closes in the Bold comes out turned
            // round, or mirrored and wound the other way), or its points do not correspond (the contour starts
            // somewhere else), the shape half-way has almost no area: the masters have one structure and each
            // has an area, and the glyph between them is wrong.
            let area = |points: &[V]| -> f64 {
                let n = points.len();
                (0..n).map(|k| points[k].cross(points[(k + 1) % n])).sum::<f64>() / 2.0
            };
            if built.iter().all(|(_, g)| g.signature() == first) {
                for i in 0..built[0].1.contours.len() {
                    let reference = built[0].1.contours[i].points();
                    for (p, g) in &built[1..] {
                        let here = g.contours[i].points();
                        let between: Vec<V> = reference.iter().zip(&here).map(|(&a, &b)| (a + b) * 0.5).collect();
                        let least = area(&reference).abs().min(area(&here).abs());
                        // a contour mirrored in one direction and wound the other way keeps an area half-way
                        // (a rectangle becomes a kite), but its points cross the whole shape to get there
                        let centre = |points: &[V]| {
                            points.iter().fold(V { x: 0.0, y: 0.0 }, |sum, &z| sum + z)
                                * (1.0 / points.len().max(1) as f64)
                        };
                        let (ca, cb) = (centre(&reference), centre(&here));
                        let furthest =
                            reference.iter().zip(&here).map(|(&a, &b)| ((b - cb) - (a - ca)).abs()).fold(0.0, f64::max);
                        let across = reference.iter().map(|&a| (a - ca).abs()).fold(0.0, f64::max) * 2.0;
                        if area(&between).abs() < 0.25 * least || furthest > 0.6 * across {
                            report.problems.push(format!(
                                "{name} [{}]: contour {i} has no shape half-way to {}: its size passes through zero, \
                                 or its points do not correspond",
                                p.name, built[0].0.name
                            ));
                        }
                    }
                }
            }
            // components are resolved once, in the first master: a glyph that is its own component, directly
            // or through others, is reported there and would overflow the stack anywhere else
            if !built[0].1.components.is_empty()
                && let Some(flat) = registry.flat(name, built[0].0)
            {
                for e in flat.errors {
                    report.problems.push(format!("{name} [{}]: {e}", built[0].0.name));
                }
            }
            for (p, g) in &built {
                for (base, _) in &g.components {
                    if registry.get(base).is_none() {
                        report.problems.push(format!("{name}: component {base:?} is not a glyph"));
                    }
                }
                for (i, c) in g.contours.iter().enumerate() {
                    if c.area().abs() < 1.0 {
                        report.problems.push(format!("{name} [{}]: contour {i} has no area", p.name));
                    }
                    let wild = c.segs.iter().any(|s| {
                        [s.start(), s.end()]
                            .iter()
                            .any(|z| !z.x.is_finite() || !z.y.is_finite() || z.x.abs() > 1e5 || z.y.abs() > 1e5)
                    });
                    if wild {
                        report.problems.push(format!("{name} [{}]: contour {i} has a wild coordinate", p.name));
                    }
                }
                let Some((x0, y0, x1, y1)) = g.bounds() else {
                    // a character that is blank by definition (a space, a joiner, the empty Braille cell) is not a
                    // glyph someone forgot to draw
                    let blank = |c: &u32| char::from_u32(*c).is_some_and(|ch| ch.is_whitespace() || BLANK.contains(c));
                    if g.components.is_empty() && !(spec.unicodes.iter().all(blank) && !spec.unicodes.is_empty()) {
                        report.notes.push(format!("{name} [{}]: empty", p.name));
                    }
                    continue;
                };
                if !spec.opt.upright && !p.italic() && !spec.opt.mark {
                    // only a fixed pitch has cells to stay inside: a proportional j or f may overhang
                    if p.mono && (x0 < -SIDE_ALLOWANCE || x1 > g.advance + SIDE_ALLOWANCE) {
                        report
                            .notes
                            .push(format!("{name} [{}]: reaches outside its cell: x from {x0:.0} to {x1:.0}", p.name));
                    }
                    if y1 > p.asc + 260.0 || y0 < p.desc - 120.0 {
                        report.notes.push(format!("{name} [{}]: very tall or deep: y from {y0:.0} to {y1:.0}", p.name));
                    }
                }
            }
        }
    }
    report
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geom::pt;
    use crate::glyph::Draw;

    #[test]
    fn a_contour_whose_size_passes_through_zero_is_a_problem() {
        let mut registry = Registry::new();
        registry.module("test");
        // a square whose half side is 44 in the Light, 22 in the Regular and -24 in the Bold
        registry.named("closing", |g: &mut Draw| {
            let r = 110.0 - g.p.stem;
            g.poly(&[
                pt(300.0 - r, 100.0 - r),
                pt(300.0 + r, 100.0 - r),
                pt(300.0 + r, 100.0 + r),
                pt(300.0 - r, 100.0 + r),
            ]);
        });
        // a tall rectangle whose width alone passes through zero
        registry.named("narrowing", |g: &mut Draw| {
            let r = 110.0 - g.p.stem;
            g.poly(&[pt(300.0 - r, 0.0), pt(300.0 + r, 0.0), pt(300.0 + r, 400.0), pt(300.0 - r, 400.0)]);
        });
        registry.named("steady", |g: &mut Draw| {
            let r = 200.0 - g.p.stem;
            g.poly(&[
                pt(300.0 - r, 100.0 - r),
                pt(300.0 + r, 100.0 - r),
                pt(300.0 + r, 100.0 + r),
                pt(300.0 - r, 100.0 + r),
            ]);
        });
        let report = check_glyphs(&registry, None);
        for name in ["closing", "narrowing"] {
            assert!(
                report.problems.iter().any(|p| p.starts_with(name) && p.contains("half-way")),
                "{name}: {:?}",
                report.problems
            );
        }
        assert!(!report.problems.iter().any(|p| p.starts_with("steady")), "{:?}", report.problems);
    }

    #[test]
    fn glyph_programs_that_reach_themselves_are_reported_and_do_not_hang() {
        let mut registry = Registry::new();
        registry.module("test");
        registry.named("ouroboros", |g: &mut Draw| {
            let _ = g.glyph_of("ouroboros");
            g.rect(0.0, 0.0, 100.0, 100.0);
        });
        // and one that is its own component, and two that are each other's
        registry.named("self", |g: &mut Draw| g.use_glyph("self", 10.0, 0.0));
        registry.named("left", |g: &mut Draw| g.use_glyph("right", 0.0, 0.0));
        registry.named("right", |g: &mut Draw| g.use_glyph("left", 0.0, 0.0));
        // the real registry runs a program several times for one glyph (its fit, its anchors): a cycle must
        // still end at once
        registry.fit = Some(Box::new(|reg, spec, p| {
            let _ = reg.measure(spec, p, p.width);
            let _ = reg.measure(spec, p, p.width + 1.0);
            None
        }));
        registry.anchors = Some(Box::new(|_, _, upright| {
            let _ = upright();
            Vec::new()
        }));
        let report = check_glyphs(&registry, None);
        for name in ["ouroboros", "self", "left", "right"] {
            assert!(
                report.problems.iter().any(|p| p.starts_with(name) && p.contains("cycle")),
                "{name}: {:?}",
                report.problems
            );
        }
    }
}
