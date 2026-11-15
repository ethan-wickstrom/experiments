//! The variation tables of the variable font: `gvar` (how every point moves) and `HVAR` (how advances change),
//! from the regions and deltas of the variation model.

use kurbo::{Point, Vec2};
use write_fonts::tables::gvar::iup::iup_delta_optimize;
use write_fonts::tables::gvar::{GlyphDelta, GlyphDeltas, GlyphVariations, Gvar, Tent};
use write_fonts::tables::hvar::Hvar;
use write_fonts::tables::variations::{
    DeltaSetIndexMap, ItemVariationData, ItemVariationStore, RegionAxisCoordinates, VariationRegion,
    VariationRegionList, ivs_builder::VariationStoreBuilder,
};
use write_fonts::types::{F2Dot14, GlyphId};

use crate::Error;
use crate::glyf::Compiled;
use crate::model::Model;
use crate::outline::ot_round;

/// The largest error, in font units, that IUP optimisation may leave in an interpolated delta.
pub const IUP_TOLERANCE: f64 = 0.5;

/// Everything `gvar` needs about one glyph: its compiled shape in every master and its advance in every
/// master (rounded).
pub(crate) struct GlyphSource<'a> {
    pub compiled: &'a Compiled,
    pub advances: &'a [i32],
}

/// A tent of the model as `gvar` and the item variation store write it.
fn f2(v: f64) -> F2Dot14 {
    F2Dot14::from_f32(v as f32)
}

/// The `gvar` table: for each glyph and each non-default master's region, the deltas of its points (outline
/// points of a simple glyph with IUP optimisation, component offsets of a composite, then the four phantom
/// points), computed on the rounded master coordinates; regions where nothing moves are left out.
pub(crate) fn gvar(
    names: &[String],
    glyphs: &[GlyphSource],
    model: &Model,
    default_master: usize,
    vertical: (i32, i32),
) -> Result<Gvar, Error> {
    let regions = model.regions();
    let simple: Vec<bool> = glyphs.iter().map(|g| matches!(g.compiled, Compiled::Simple(_))).collect();
    let gid_of: std::collections::BTreeMap<&str, usize> =
        names.iter().enumerate().map(|(i, n)| (n.as_str(), i)).collect();
    let mut variations = Vec::with_capacity(glyphs.len());
    for (gid, g) in glyphs.iter().enumerate() {
        let masters = g.advances.len();
        // Each master's points: the outline (or the component offsets), then the four phantom points.
        let mut points: Vec<Vec<(i32, i32)>> = vec![Vec::new(); masters];
        let mut ends: Vec<usize> = Vec::new();
        let is_simple = match g.compiled {
            Compiled::Empty => false,
            Compiled::Simple(ms) => {
                let mut n = 0;
                for c in &ms[default_master].contours {
                    n += c.len();
                    ends.push(n - 1);
                }
                for (m, sg) in ms.iter().enumerate() {
                    points[m] =
                        sg.contours.iter().flat_map(|c| c.iter()).map(|p| (i32::from(p.x), i32::from(p.y))).collect();
                }
                true
            }
            Compiled::Composite(ms) => {
                for (m, comps) in ms.iter().enumerate() {
                    points[m] = comps
                        .iter()
                        .filter(|(base, _)| gid_of.get(base.as_str()).is_some_and(|&j| simple[j]))
                        .map(|(_, (x, y))| (i32::from(*x), i32::from(*y)))
                        .collect();
                }
                false
            }
        };
        let n_outline = points[default_master].len();
        if points.iter().any(|p| p.len() != n_outline) {
            return Err(Error::Incompatible {
                glyph: names[gid].clone(),
                detail: "the masters have different numbers of points".into(),
            });
        }
        for (m, p) in points.iter_mut().enumerate() {
            p.extend([(0, 0), (g.advances[m], 0), (0, vertical.0), (0, vertical.1)]);
        }
        let n = points[default_master].len();
        // Deltas, coordinate by coordinate, in model order (the first is the default value itself).
        let mut per_region: Vec<Vec<(i32, i32)>> = vec![vec![(0, 0); n]; regions.len()];
        let mut xs = vec![0.0; masters];
        let mut ys = vec![0.0; masters];
        for k in 0..n {
            for m in 0..masters {
                xs[m] = f64::from(points[m][k].0);
                ys[m] = f64::from(points[m][k].1);
            }
            let dx = model.deltas(&xs);
            let dy = model.deltas(&ys);
            for r in 0..regions.len() {
                per_region[r][k] = (ot_round(dx[r + 1]), ot_round(dy[r + 1]));
            }
        }
        let coords: Vec<Point> =
            points[default_master].iter().map(|&(x, y)| Point::new(f64::from(x), f64::from(y))).collect();
        let mut tuples = Vec::new();
        for (r, deltas) in per_region.iter().enumerate() {
            if deltas.iter().all(|&d| d == (0, 0)) {
                continue;
            }
            let glyph_deltas: Vec<GlyphDelta> = if is_simple {
                let vecs = deltas.iter().map(|&(x, y)| Vec2::new(f64::from(x), f64::from(y))).collect();
                iup_delta_optimize(vecs, coords.clone(), IUP_TOLERANCE, &ends).map_err(|e| Error::Glyph {
                    glyph: names[gid].clone(),
                    detail: format!("IUP optimisation failed: {e:?}"),
                })?
            } else {
                deltas
                    .iter()
                    .map(|&(x, y)| Ok(GlyphDelta::required(to_i16(x, gid, names)?, to_i16(y, gid, names)?)))
                    .collect::<Result<_, Error>>()?
            };
            let tents = regions[r].iter().map(|&(lo, peak, hi)| Tent::new(f2(peak), Some((f2(lo), f2(hi))))).collect();
            tuples.push(GlyphDeltas::new(tents, glyph_deltas));
        }
        let gid16 = u32::try_from(gid).map_err(|_| Error::Family("too many glyphs".into()))?;
        variations.push(GlyphVariations::new(GlyphId::new(gid16), tuples));
    }
    let axes = u16::try_from(model.axis_count()).map_err(|_| Error::Family("too many axes".into()))?;
    Gvar::new(variations, axes).map_err(|e| Error::Table(format!("gvar: {e:?}")))
}

fn to_i16(v: i32, gid: usize, names: &[String]) -> Result<i16, Error> {
    i16::try_from(v)
        .map_err(|_| Error::Glyph { glyph: names[gid].clone(), detail: format!("delta {v} is out of range") })
}

/// The region of the model's `r`-th non-default master, as the item variation store writes it.
fn region(tents: &[(f64, f64, f64)]) -> VariationRegion {
    VariationRegion::new(
        tents.iter().map(|&(lo, peak, hi)| RegionAxisCoordinates::new(f2(lo), f2(peak), f2(hi))).collect(),
    )
}

/// The `HVAR` table. `advances[gid][master]` are the rounded advances. When no advance changes between masters
/// (a fixed-pitch family), the table is the minimal one: one item with no deltas, and an advance mapping with
/// a single entry, which applies to every glyph.
pub(crate) fn hvar(advances: &[Vec<i32>], model: &Model) -> Result<Hvar, Error> {
    let axes = u16::try_from(model.axis_count()).map_err(|_| Error::Family("too many axes".into()))?;
    let invariant = advances.iter().all(|a| a.iter().all(|&v| Some(&v) == a.first()));
    if invariant {
        let data = ItemVariationData::new(1, 0, Vec::new(), Vec::new());
        let store = ItemVariationStore::new(VariationRegionList::new(axes, Vec::new()), vec![Some(data)]);
        let map: DeltaSetIndexMap = std::iter::once(0u32).collect();
        return Ok(Hvar::new(store, Some(map), None, None));
    }
    let regions: Vec<VariationRegion> = model.regions().iter().map(|t| region(t)).collect();
    let mut builder = VariationStoreBuilder::new(axes);
    let mut ids = Vec::with_capacity(advances.len());
    for a in advances {
        let values: Vec<f64> = a.iter().map(|&v| f64::from(v)).collect();
        let deltas = model.deltas(&values);
        let row: Vec<(VariationRegion, i32)> =
            regions.iter().enumerate().map(|(r, reg)| (reg.clone(), ot_round(deltas[r + 1]))).collect();
        ids.push(builder.add_deltas(row));
    }
    let (store, remap) = builder.build();
    let mut mapping = Vec::with_capacity(ids.len());
    for id in ids {
        let v = remap.get(id).ok_or_else(|| Error::Table("HVAR: a delta set was lost".into()))?;
        mapping.push((u32::from(v.delta_set_outer_index) << 16) | u32::from(v.delta_set_inner_index));
    }
    let map: DeltaSetIndexMap = mapping.into_iter().collect();
    Ok(Hvar::new(store, Some(map), None, None))
}
