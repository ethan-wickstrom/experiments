//! Structural checks on glyph programs: what must hold before a font is built from them.

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
