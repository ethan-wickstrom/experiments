//! TrueType glyphs: simple glyphs with integer points, composites of simple glyphs, and the `glyf` and `loca`
//! tables with the numbers `maxp`, `head` and `hhea` take from them.

use std::collections::BTreeMap;

use write_fonts::read::tables::glyf::CurvePoint;
use write_fonts::tables::glyf::{
    Anchor, Bbox, Component, ComponentFlags, CompositeGlyph, GlyfLocaBuilder, Glyph, SimpleGlyph, Transform,
};
use write_fonts::tables::loca::LocaFormat;
use write_fonts::tables::{glyf::Glyf, loca::Loca};
use write_fonts::types::GlyphId;

use crate::Error;
use crate::outline::{Path, ot_round, quadratic_paths};

/// One glyph in every master (a static font has one master).
#[derive(Clone, Debug)]
pub(crate) enum Compiled {
    /// No outline.
    Empty,
    /// Integer points, the same structure in every master.
    Simple(Vec<SimpleGlyph>),
    /// Components (glyph name, rounded offset) in every master.
    Composite(Vec<Vec<(String, (i16, i16))>>),
}

/// Make the simple glyph `name` from its contours in every master (PostScript direction).
pub(crate) fn compile_simple(name: &str, masters: &[Vec<Path>], overlaps: bool) -> Result<Compiled, Error> {
    let paths = quadratic_paths(name, masters)?;
    let mut glyphs = SimpleGlyph::interpolatable_glyphs_from_bezpaths(&paths)
        .map_err(|e| Error::Glyph { glyph: name.into(), detail: format!("malformed outline: {e:?}") })?;
    for g in &mut glyphs {
        if masters.len() == 1 {
            drop_duplicate_points(g);
        }
        g.recompute_bounding_box();
        g.overlaps = overlaps && g.contours.len() > 1;
    }
    if glyphs.iter().all(|g| g.contours.is_empty()) {
        return Ok(Compiled::Empty);
    }
    Ok(Compiled::Simple(glyphs))
}

/// Remove points that rounding put on top of their neighbour (a static font only: in a variable font every
/// master must keep the same points). Of two equal neighbours where one is on the curve, the off-curve one goes
/// (a quadratic whose control point sits on an end is a straight line); of two equal on-curve points, the second.
/// Contours left with fewer than three points are dropped.
fn drop_duplicate_points(g: &mut SimpleGlyph) {
    let contours = std::mem::take(&mut g.contours);
    for c in contours {
        let mut pts: Vec<CurvePoint> = c.into();
        let mut changed = true;
        while changed && pts.len() > 1 {
            changed = false;
            let n = pts.len();
            for i in 0..n {
                let j = (i + 1) % n;
                let (a, b) = (pts[i], pts[j]);
                if (a.x, a.y) != (b.x, b.y) || !(a.on_curve || b.on_curve) {
                    continue;
                }
                let drop = if !b.on_curve || a.on_curve { j } else { i };
                pts.remove(drop);
                changed = true;
                break;
            }
        }
        if pts.len() >= 3 {
            g.contours.push(pts.into());
        }
    }
}

/// Make the composite glyph `name` from its components' offsets in every master.
pub(crate) fn compile_composite(name: &str, masters: &[Vec<(String, kurbo::Point)>]) -> Result<Compiled, Error> {
    let round = |v: f64| {
        i16::try_from(ot_round(v))
            .map_err(|_| Error::Glyph { glyph: name.into(), detail: format!("component offset {v} is out of range") })
    };
    let mut out = Vec::with_capacity(masters.len());
    for m in masters {
        let mut comps = Vec::with_capacity(m.len());
        for (base, at) in m {
            comps.push((base.clone(), (round(at.x)?, round(at.y)?)));
        }
        out.push(comps);
    }
    Ok(Compiled::Composite(out))
}

/// What `maxp` records about the glyph outlines.
#[derive(Clone, Copy, Debug, Default)]
pub(crate) struct MaxpStats {
    pub points: u16,
    pub contours: u16,
    pub composite_points: u16,
    pub composite_contours: u16,
    pub component_elements: u16,
    pub component_depth: u16,
}

/// The `glyf` and `loca` tables of one master, with each glyph's bounding box and the `maxp` numbers.
pub(crate) struct GlyfTables {
    pub glyf: Glyf,
    pub loca: Loca,
    pub loca_format: LocaFormat,
    pub bboxes: Vec<Option<Bbox>>,
    pub maxp: MaxpStats,
}

/// Build `glyf` and `loca` from master `master` of every glyph, in glyph-id order. `overlap_compound` sets
/// that flag on composites with more than one component (on every composite when `all_composites` is true).
pub(crate) fn build_glyf(
    names: &[String],
    compiled: &[Compiled],
    master: usize,
    overlap_compound: bool,
    all_composites: bool,
) -> Result<GlyfTables, Error> {
    let gid_of: BTreeMap<&str, usize> = names.iter().enumerate().map(|(i, n)| (n.as_str(), i)).collect();
    let mut bboxes: Vec<Option<Bbox>> = vec![None; compiled.len()];
    let mut points: Vec<(u16, u16)> = vec![(0, 0); compiled.len()];
    let mut stats = MaxpStats::default();
    for (i, c) in compiled.iter().enumerate() {
        if let Compiled::Simple(glyphs) = c {
            let g = &glyphs[master];
            bboxes[i] = Some(g.bbox);
            let n: usize = g.contours.iter().map(|c| c.len()).sum();
            let np = u16::try_from(n).map_err(|_| too_big(&names[i]))?;
            let nc = u16::try_from(g.contours.len()).map_err(|_| too_big(&names[i]))?;
            points[i] = (np, nc);
            stats.points = stats.points.max(np);
            stats.contours = stats.contours.max(nc);
        }
    }
    let mut out: Vec<Glyph> = Vec::with_capacity(compiled.len());
    for (i, c) in compiled.iter().enumerate() {
        let glyph = match c {
            Compiled::Empty => Glyph::Empty,
            Compiled::Simple(glyphs) => Glyph::Simple(glyphs[master].clone()),
            Compiled::Composite(masters) => {
                let comps = &masters[master];
                let flag = overlap_compound && (all_composites || comps.len() > 1);
                let mut parts = Vec::with_capacity(comps.len());
                let (mut np, mut nc) = (0u32, 0u32);
                for (k, (base, (dx, dy))) in comps.iter().enumerate() {
                    let gid = *gid_of.get(base.as_str()).ok_or_else(|| Error::Glyph {
                        glyph: names[i].clone(),
                        detail: format!("component {base:?} is not in the font"),
                    })?;
                    let Some(b) = bboxes[gid] else {
                        continue; // a component that came out empty adds nothing
                    };
                    np += u32::from(points[gid].0);
                    nc += u32::from(points[gid].1);
                    let flags = ComponentFlags {
                        round_xy_to_grid: true,
                        overlap_compound: flag && k == 0,
                        ..ComponentFlags::default()
                    };
                    let gid16 = GlyphId::new(u32::try_from(gid).map_err(|_| too_big(base))?);
                    let component =
                        Component::new(gid16, Anchor::Offset { x: *dx, y: *dy }, Transform::default(), flags);
                    let bbox = Bbox {
                        x_min: b.x_min.saturating_add(*dx),
                        y_min: b.y_min.saturating_add(*dy),
                        x_max: b.x_max.saturating_add(*dx),
                        y_max: b.y_max.saturating_add(*dy),
                    };
                    parts.push((component, bbox));
                }
                match CompositeGlyph::try_from_iter(parts) {
                    Ok(g) => {
                        bboxes[i] = Some(g.bbox);
                        stats.composite_points =
                            stats.composite_points.max(u16::try_from(np).map_err(|_| too_big(&names[i]))?);
                        stats.composite_contours =
                            stats.composite_contours.max(u16::try_from(nc).map_err(|_| too_big(&names[i]))?);
                        stats.component_elements =
                            stats.component_elements.max(u16::try_from(comps.len()).map_err(|_| too_big(&names[i]))?);
                        stats.component_depth = 1;
                        Glyph::Composite(g)
                    }
                    Err(_) => Glyph::Empty,
                }
            }
        };
        out.push(glyph);
    }
    let mut builder = GlyfLocaBuilder::new();
    for (i, g) in out.iter().enumerate() {
        builder
            .add_glyph(g)
            .map_err(|e| Error::Glyph { glyph: names[i].clone(), detail: format!("cannot be written: {e}") })?;
    }
    let (glyf, loca, loca_format) = builder.build();
    Ok(GlyfTables { glyf, loca, loca_format, bboxes, maxp: stats })
}

fn too_big(name: &str) -> Error {
    Error::Glyph { glyph: name.into(), detail: "too many points, contours or glyphs".into() }
}
