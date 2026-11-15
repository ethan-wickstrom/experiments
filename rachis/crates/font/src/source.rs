//! The family checked and prepared for compiling: the variation model, the default master, the glyph order,
//! every glyph's shape in every master, and the style a font file presents.

use std::collections::BTreeMap;

use write_fonts::FontBuilder;

use crate::glyf::{Compiled, GlyfTables, compile_composite, compile_simple};
use crate::model::Model;
use crate::outline::{Path, Shape, check_compatible, glyph_order, ot_round, shape_of};
use crate::{Axis, Error, Family, layout, names, os2, tables};

/// The glyph data of one font (the default master of a variable font, or a static instance), in glyph-id
/// order, as the table builders need it.
pub(crate) struct Built {
    pub names: Vec<String>,
    pub unicodes: Vec<Vec<u32>>,
    pub marks: Vec<bool>,
    pub advances: Vec<u16>,
    pub anchors: Vec<BTreeMap<String, (i16, i16)>>,
    pub glyf: GlyfTables,
}

/// The style a font file presents: its names and style bits.
#[derive(Clone, Debug)]
pub(crate) struct Style {
    /// "SemiBold Italic".
    pub name: String,
    /// The style without "Italic": "SemiBold", or "Regular".
    pub weight_name: String,
    /// `usWeightClass`.
    pub weight: u16,
    pub bold: bool,
    pub italic: bool,
    /// One of the four style-linked styles (Regular, Italic, Bold, Bold Italic).
    pub linked: bool,
}

impl Style {
    pub(crate) fn new(family: &Family, name: &str, location: &[f64]) -> Style {
        let weight_name = if name == "Italic" {
            "Regular".to_owned()
        } else {
            name.strip_suffix(" Italic").unwrap_or(name).to_owned()
        };
        let bold = weight_name == "Bold";
        let weight = family
            .axes
            .iter()
            .position(|a| a.tag == "wght")
            .and_then(|i| location.get(i))
            .map_or(400, |&v| ot_round(v).clamp(1, 1000) as u16);
        Style {
            name: name.to_owned(),
            linked: bold || weight_name == "Regular",
            weight_name,
            weight,
            bold,
            italic: family.italic,
        }
    }
}

/// The family checked and prepared: the model, the default master and the glyph order.
pub(crate) struct Source<'a> {
    pub family: &'a Family,
    pub model: Model,
    pub default_master: usize,
    /// Indices into each master's glyphs, in glyph-id order.
    pub order: Vec<usize>,
    pub names: Vec<String>,
}

/// A user-space value normalised to -1..1 around the axis's default, piecewise linearly.
pub(crate) fn normalise(axis: &Axis, v: f64) -> f64 {
    if v < axis.default && axis.default > axis.min {
        ((v - axis.default) / (axis.default - axis.min)).max(-1.0)
    } else if v > axis.default && axis.max > axis.default {
        ((v - axis.default) / (axis.max - axis.default)).min(1.0)
    } else {
        0.0
    }
}

impl<'a> Source<'a> {
    pub(crate) fn new(family: &'a Family) -> Result<Source<'a>, Error> {
        let fail = |s: String| Err(Error::Family(s));
        for a in &family.axes {
            if a.tag.len() != 4 || !a.tag.bytes().all(|b| (0x20..0x7F).contains(&b)) {
                return fail(format!("axis tag {:?} is not four printable ASCII characters", a.tag));
            }
            if !(a.min <= a.default && a.default <= a.max) {
                return fail(format!("axis {}: min <= default <= max does not hold", a.tag));
            }
        }
        let Some(first) = family.masters.first() else {
            return fail("there are no masters".into());
        };
        let n_axes = family.axes.len();
        let mut locations = Vec::with_capacity(family.masters.len());
        for (m, master) in family.masters.iter().enumerate() {
            if master.location.len() != n_axes {
                return fail(format!("master {m} has {} coordinates for {n_axes} axes", master.location.len()));
            }
            if master.glyphs.len() != first.glyphs.len()
                || master.glyphs.iter().zip(&first.glyphs).any(|(a, b)| a.name != b.name)
            {
                return fail(format!("master {m} does not have the same glyphs in the same order as master 0"));
            }
            locations
                .push(family.axes.iter().zip(&master.location).map(|(a, &v)| normalise(a, v)).collect::<Vec<f64>>());
        }
        for i in &family.instances {
            if i.location.len() != n_axes {
                return fail(format!(
                    "instance {:?} has {} coordinates for {n_axes} axes",
                    i.style_name,
                    i.location.len()
                ));
            }
        }
        let model = Model::new(&locations).map_err(Error::Family)?;
        let default_master = locations.iter().position(|l| l.iter().all(|&v| v == 0.0)).unwrap_or(0);
        let glyphs = &family.masters[default_master].glyphs;
        let mut seen = std::collections::BTreeSet::new();
        for g in glyphs {
            if !seen.insert(g.name.as_str()) {
                return fail(format!("glyph {:?} appears twice", g.name));
            }
        }
        for master in &family.masters {
            if let Some(g) = master.glyphs.iter().find(|g| !g.errors.is_empty()) {
                return Err(Error::Glyph {
                    glyph: g.name.clone(),
                    detail: format!("the glyph program failed: {}", g.errors.join("; ")),
                });
            }
        }
        let order = glyph_order(glyphs);
        let names = order.iter().map(|&i| glyphs[i].name.clone()).collect();
        Ok(Source { family, model, default_master, order, names })
    }

    pub(crate) fn default_glyph(&self, gid: usize) -> &rachis_kernel::Glyph {
        &self.family.masters[self.default_master].glyphs[self.order[gid]]
    }

    /// Every glyph's shape in every master, checked for compatibility: `[gid][master]`.
    pub(crate) fn shapes(&self) -> Result<Vec<Vec<Shape>>, Error> {
        let indices: Vec<BTreeMap<&str, usize>> = self
            .family
            .masters
            .iter()
            .map(|m| m.glyphs.iter().enumerate().map(|(i, g)| (g.name.as_str(), i)).collect())
            .collect();
        let mut out = Vec::with_capacity(self.order.len());
        for (gid, &i) in self.order.iter().enumerate() {
            let shapes = self
                .family
                .masters
                .iter()
                .zip(&indices)
                .map(|(m, index)| shape_of(&m.glyphs, index, i))
                .collect::<Result<Vec<_>, _>>()?;
            check_compatible(&self.names[gid], &shapes)?;
            out.push(shapes);
        }
        Ok(out)
    }

    /// The advance of every glyph in every master, rounded: `[gid][master]`.
    pub(crate) fn advances(&self) -> Result<Vec<Vec<i32>>, Error> {
        self.order
            .iter()
            .enumerate()
            .map(|(gid, &i)| {
                self.family
                    .masters
                    .iter()
                    .map(|m| {
                        let a = ot_round(m.glyphs[i].advance);
                        if (0..=i32::from(u16::MAX)).contains(&a) {
                            Ok(a)
                        } else {
                            Err(Error::Glyph {
                                glyph: self.names[gid].clone(),
                                detail: format!("advance {a} is out of range"),
                            })
                        }
                    })
                    .collect()
            })
            .collect()
    }

    pub(crate) fn built(
        &self,
        advances: Vec<u16>,
        anchors: Vec<BTreeMap<String, (i16, i16)>>,
        glyf: GlyfTables,
    ) -> Built {
        Built {
            names: self.names.clone(),
            unicodes: (0..self.order.len()).map(|g| self.default_glyph(g).unicodes.clone()).collect(),
            marks: (0..self.order.len()).map(|g| self.default_glyph(g).mark).collect(),
            advances,
            anchors,
            glyf,
        }
    }
}

pub(crate) fn round_anchor(name: &str, x: f64, y: f64) -> Result<(i16, i16), Error> {
    let r = |v: f64| {
        i16::try_from(ot_round(v))
            .map_err(|_| Error::Glyph { glyph: name.into(), detail: format!("anchor coordinate {v} is out of range") })
    };
    Ok((r(x)?, r(y)?))
}

/// Add the tables both kinds of font share and serialise the font.
pub(crate) fn finish(
    mut builder: FontBuilder,
    family: &Family,
    built: &Built,
    style: &Style,
    mut names: names::Names,
    stat: write_fonts::tables::stat::Stat,
) -> Result<Vec<u8>, Error> {
    let lay = layout::layout(family, built, &mut names)?;
    tables::add_basic_tables(&mut builder, family, built, style)?;
    tables::add(&mut builder, &os2::os2(family, built, style, lay.max_context))?;
    tables::add(&mut builder, &stat)?;
    tables::add(&mut builder, &lay.gdef)?;
    if let Some(gsub) = &lay.gsub {
        tables::add(&mut builder, gsub)?;
    }
    if let Some(gpos) = &lay.gpos {
        tables::add(&mut builder, gpos)?;
    }
    if let Some(desc) = &family.math {
        tables::add(&mut builder, &crate::math::math(desc, &built.names)?)?;
    }
    tables::add(&mut builder, &names.table())?;
    Ok(builder.build())
}

/// Every glyph compiled in every master, with the same point structure in all of them.
pub(crate) fn compile_masters(src: &Source) -> Result<Vec<Compiled>, Error> {
    let shapes = src.shapes()?;
    let mut compiled = Vec::with_capacity(shapes.len());
    for (gid, ms) in shapes.iter().enumerate() {
        let name = &src.names[gid];
        compiled.push(match &ms[0] {
            Shape::Empty => Compiled::Empty,
            Shape::Simple(_) => {
                let paths: Vec<Vec<Path>> = ms
                    .iter()
                    .map(|s| match s {
                        Shape::Simple(cs) => cs.iter().map(Path::from_contour).collect(),
                        _ => Vec::new(),
                    })
                    .collect();
                compile_simple(name, &paths, true)?
            }
            Shape::Composite(_) => {
                let comps: Vec<Vec<(String, kurbo::Point)>> = ms
                    .iter()
                    .map(|s| match s {
                        Shape::Composite(cs) => {
                            cs.iter().map(|(n, v)| (n.clone(), kurbo::Point::new(v.x, v.y))).collect()
                        }
                        _ => Vec::new(),
                    })
                    .collect();
                compile_composite(name, &comps)?
            }
        });
    }
    Ok(compiled)
}
