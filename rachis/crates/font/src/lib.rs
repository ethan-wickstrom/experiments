//! The compiler of the Rachis typeface: drawn masters to OpenType font files.
//!
//! A [`Family`] holds the masters (every glyph drawn at a few points of the design space), the axes that span
//! that space, the named instances, the metrics and the layout features. [`variable_ttf`] compiles it into a
//! variable TrueType font that keeps the overlapping strokes; [`static_ttf`] evaluates the same variation
//! model at one instance, removes the overlaps and compiles a static font, so that a static font is the
//! variable font at that point; [`woff2`] compresses either for the web.
//!
//! The output is reproducible: the same family gives the same bytes (no clocks; every map that reaches the
//! output is ordered).

#![warn(missing_docs)]

pub mod model;

mod glyf;
mod instance;
mod layout;
mod math;
pub mod meta;
mod names;
mod os2;
mod outline;
mod source;
mod tables;
mod variation;

use std::collections::BTreeMap;

use sha2::Digest;
use write_fonts::FontBuilder;

pub use instance::{CHECK_MAX_PIXEL, CHECK_MAX_TOTAL, CHECK_PPEM, UnionFailure};
pub use math::CONSTANTS as MATH_CONSTANTS;
pub use outline::QUADRATIC_TOLERANCE;
pub use tables::{GASP_BEHAVIOR, HEAD_FLAGS, PREP};
pub use variation::IUP_TOLERANCE;

use glyf::{Compiled, build_glyf, compile_composite, compile_simple};
use outline::ot_round;
pub(crate) use source::{Built, Style};
use source::{Source, compile_masters, finish, normalise, round_anchor};

/// A design axis of a family.
#[derive(Clone, Debug, PartialEq)]
pub struct Axis {
    /// The four-letter axis tag, e.g. `wght`.
    pub tag: String,
    /// The axis name shown to users, e.g. "Weight".
    pub name: String,
    /// The smallest user-space value.
    pub min: f64,
    /// The default user-space value: the default master sits here.
    pub default: f64,
    /// The largest user-space value.
    pub max: f64,
    /// The named values of the axis, for `STAT`.
    pub labels: Vec<AxisLabel>,
}

/// A named value on an axis, as `STAT` records it.
#[derive(Clone, Debug, PartialEq)]
pub struct AxisLabel {
    /// The name, e.g. "SemiBold".
    pub name: String,
    /// The user-space value.
    pub value: f64,
    /// Whether the name may be left out of a style name (e.g. "Regular").
    pub elidable: bool,
    /// The value of the style this one is linked to (STAT format 3), e.g. Regular 400 to Bold 700. Ignored on
    /// the weight axis, where Regular must stay format 1 or 2 for kitty.
    pub linked: Option<f64>,
    /// The range of values the name covers (STAT format 2).
    pub range: Option<(f64, f64)>,
}

/// One master: every glyph drawn at one point of the design space.
#[derive(Clone, Debug)]
pub struct Master {
    /// One user-space value per axis.
    pub location: Vec<f64>,
    /// The glyphs: the same names in the same order in every master.
    pub glyphs: Vec<rachis_kernel::Glyph>,
}

/// A named instance: one static font, and one named point of the variable font.
#[derive(Clone, Debug, PartialEq)]
pub struct Instance {
    /// The style name: "SemiBold", "Bold Italic", …
    pub style_name: String,
    /// One user-space value per axis.
    pub location: Vec<f64>,
}

/// The family's metrics, the same in every master and every instance.
#[derive(Clone, Debug, PartialEq)]
pub struct Metrics {
    /// Units per em.
    pub upm: u16,
    /// The top of the line box (hhea, typo and win ascender; in a mathematics font the win ascent is the top of
    /// its tallest glyph).
    pub ascender: i16,
    /// The bottom of the line box, negative (hhea and typo descender; win descent is its absolute value, or in
    /// a mathematics font the depth of its deepest glyph).
    pub descender: i16,
    /// `OS/2.sxHeight`.
    pub x_height: i16,
    /// `OS/2.sCapHeight`.
    pub cap_height: i16,
    /// Degrees; positive leans right.
    pub italic_angle: f64,
    /// `post.underlinePosition`: the top of the underline.
    pub underline_position: i16,
    /// `post.underlineThickness`.
    pub underline_thickness: i16,
    /// `OS/2.yStrikeoutPosition`: the top of the strikeout stroke.
    pub strikeout_position: i16,
    /// `OS/2.yStrikeoutSize`.
    pub strikeout_size: i16,
    /// Whether every glyph has the same advance (marks have none).
    pub fixed_pitch: bool,
}

/// A feature of single substitutions, e.g. `ss01` zero → zero.dot.
#[derive(Clone, Debug, PartialEq)]
pub struct SingleSub {
    /// The feature tag.
    pub tag: String,
    /// The name of a stylistic set (`ssNN` only), shown by applications.
    pub label: Option<String>,
    /// (glyph, replacement) by glyph name. Pairs whose glyphs are missing are skipped.
    pub pairs: Vec<(String, String)>,
}

/// A kerning pair: the advance of `left` changes by `value` before `right`.
#[derive(Clone, Debug, PartialEq)]
pub struct KernPair {
    /// The first glyph's name.
    pub left: String,
    /// The second glyph's name.
    pub right: String,
    /// The adjustment in font units.
    pub value: i16,
}

/// Kerning between classes of glyphs: every glyph of `first[i]` followed by any glyph of `second[j]` has its
/// advance changed by `values[i][j]`. A glyph is in at most one class on each side.
#[derive(Clone, Debug, PartialEq)]
pub struct KernClasses {
    /// The classes of first glyphs, by glyph name.
    pub first: Vec<Vec<String>>,
    /// The classes of second glyphs, by glyph name.
    pub second: Vec<Vec<String>>,
    /// One row for each class of first glyphs, one adjustment in font units for each class of second glyphs.
    pub values: Vec<Vec<i16>>,
}

/// A feature that offers alternates of a glyph, chosen by the feature's value: `ssty` 1 and 2 are a letter's
/// forms for the scripts and the scripts of scripts of a formula.
#[derive(Clone, Debug, PartialEq)]
pub struct AlternateSub {
    /// The feature tag.
    pub tag: String,
    /// (glyph, its alternates in order) by glyph name. Entries whose glyphs are missing are skipped.
    pub alternates: Vec<(String, Vec<String>)>,
}

/// One piece of a glyph assembled to any length: a glyph, how much of it may overlap the piece before and the
/// piece after, its length along the direction of growth, and whether it may be repeated or left out.
#[derive(Clone, Debug, PartialEq)]
pub struct Part {
    /// The piece's glyph name.
    pub glyph: String,
    /// The length of the connector at its start (bottom or left).
    pub start: u16,
    /// The length of the connector at its end (top or right).
    pub end: u16,
    /// Its full length.
    pub advance: u16,
    /// Whether it is an extender.
    pub extender: bool,
}

/// How a glyph stretches in one direction: its larger sizes, smallest first, and the pieces of an assembly.
#[derive(Clone, Debug, PartialEq)]
pub struct Construction {
    /// The glyph that stretches, by name.
    pub glyph: String,
    /// (glyph name, its length along the direction of growth) for each ready-made size.
    pub variants: Vec<(String, u16)>,
    /// The pieces of the assembly, from bottom to top or from left to right; empty for none.
    pub parts: Vec<Part>,
    /// The italic correction of the assembled glyph.
    pub italic_correction: i16,
}

/// What the `MATH` table of a mathematics font is compiled from, by glyph name.
#[derive(Clone, Debug, PartialEq)]
pub struct Math {
    /// Every constant of the table, by its name in the OpenType specification ([`MATH_CONSTANTS`]).
    pub constants: Vec<(String, i16)>,
    /// The italic correction of single glyphs.
    pub italic_corrections: Vec<(String, i16)>,
    /// Where the centre of an accent goes over a glyph, from the glyph's origin.
    pub top_accents: Vec<(String, i16)>,
    /// Glyphs taller than the line that scripts are placed against by their own height.
    pub extended_shapes: Vec<String>,
    /// The glyphs that grow upwards.
    pub vertical: Vec<Construction>,
    /// The glyphs that grow sideways.
    pub horizontal: Vec<Construction>,
    /// The least overlap of two pieces of an assembly.
    pub min_connector_overlap: u16,
}

/// Everything a font file is compiled from.
#[derive(Clone, Debug)]
pub struct Family {
    /// The family name, e.g. "Rachis Mono".
    pub name: String,
    /// Whether this is the italic family (its default instance is "Italic").
    pub italic: bool,
    /// The design axes.
    pub axes: Vec<Axis>,
    /// The masters; exactly one sits at the default location.
    pub masters: Vec<Master>,
    /// The named instances.
    pub instances: Vec<Instance>,
    /// The metrics.
    pub metrics: Metrics,
    /// Single-substitution features.
    pub features: Vec<SingleSub>,
    /// Kerning pairs.
    pub kerning: Vec<KernPair>,
    /// Kerning between classes.
    pub kern_classes: Option<KernClasses>,
    /// Features of alternates.
    pub alternates: Vec<AlternateSub>,
    /// The `MATH` table, for a mathematics font.
    pub math: Option<Math>,
}

/// What can go wrong when compiling.
#[derive(Clone, Debug, PartialEq)]
pub enum Error {
    /// The family description is inconsistent (axes, masters, locations, instances).
    Family(String),
    /// A glyph's masters do not have the same structure.
    Incompatible {
        /// The glyph's name.
        glyph: String,
        /// What differs.
        detail: String,
    },
    /// A glyph cannot be compiled.
    Glyph {
        /// The glyph's name.
        glyph: String,
        /// Why.
        detail: String,
    },
    /// A table could not be written.
    Table(String),
    /// WOFF2 compression failed.
    Woff2(String),
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Error::Family(e) => write!(f, "family: {e}"),
            Error::Incompatible { glyph, detail } => {
                write!(f, "glyph {glyph:?}: masters are incompatible: {detail}")
            }
            Error::Glyph { glyph, detail } => write!(f, "glyph {glyph:?}: {detail}"),
            Error::Table(e) => write!(f, "table: {e}"),
            Error::Woff2(e) => write!(f, "woff2: {e}"),
        }
    }
}

impl std::error::Error for Error {}

/// A static font and what the compiler had to give up on.
#[derive(Clone, Debug)]
pub struct StaticFont {
    /// The font file.
    pub bytes: Vec<u8>,
    /// Glyphs whose overlaps could not be removed (they keep overlapping contours and the overlap flag), with
    /// the reason.
    pub kept_overlaps: Vec<(String, UnionFailure)>,
}

/// The variable TrueType font of `family`: the default master's outlines, `gvar` deltas to every other master,
/// overlaps kept (and flagged), named instances in `fvar`, and `STAT`.
pub fn variable_ttf(family: &Family) -> Result<Vec<u8>, Error> {
    let src = Source::new(family)?;
    if family.axes.is_empty() {
        return Err(Error::Family("a variable font needs at least one axis".into()));
    }
    let advances = src.advances()?;
    let compiled = compile_masters(&src)?;
    let dm = src.default_master;
    let glyf = build_glyf(&src.names, &compiled, dm, true, true)?;
    let m = &family.metrics;
    let sources: Vec<variation::GlyphSource> =
        compiled.iter().zip(&advances).map(|(c, a)| variation::GlyphSource { compiled: c, advances: a }).collect();
    let gvar = variation::gvar(&src.names, &sources, &src.model, dm, (i32::from(m.ascender), i32::from(m.descender)))?;
    let hvar = variation::hvar(&advances, &src.model)?;

    let default_advances = advances.iter().map(|a| a[dm] as u16).collect();
    let anchors = (0..src.order.len())
        .map(|g| {
            src.default_glyph(g)
                .anchors
                .iter()
                .map(|(k, v)| Ok((k.clone(), round_anchor(&src.names[g], v.x, v.y)?)))
                .collect()
        })
        .collect::<Result<_, Error>>()?;
    let built = src.built(default_advances, anchors, glyf);

    let defaults: Vec<f64> = family.axes.iter().map(|a| a.default).collect();
    let default_name = family
        .instances
        .iter()
        .find(|i| i.location == defaults)
        .map_or(if family.italic { "Italic" } else { "Regular" }, |i| i.style_name.as_str());
    let style = Style::new(family, default_name, &defaults);
    let mut names = names::style_names(family, &style);
    names.set(25, &names::variations_prefix(family));
    let fvar = names::fvar(family, &mut names);
    let stat = names::stat(family, None, &mut names)?;

    let mut builder = FontBuilder::new();
    tables::add(&mut builder, &fvar)?;
    tables::add(&mut builder, &gvar)?;
    tables::add(&mut builder, &hvar)?;
    finish(builder, family, &built, &style, names, stat)
}

/// The static TrueType font of `instance`: [`static_ttf_report`] without the report.
pub fn static_ttf(family: &Family, instance: &Instance) -> Result<Vec<u8>, Error> {
    static_ttf_report(family, instance).map(|s| s.bytes)
}

/// The static TrueType font of `instance`: the variation model evaluated at its location on the unrounded
/// outlines, overlaps removed (each union checked by rasterising), then converted to quadratics and rounded.
/// Glyphs whose union failed or changed the shape keep their overlapping contours and are reported.
pub fn static_ttf_report(family: &Family, instance: &Instance) -> Result<StaticFont, Error> {
    let src = Source::new(family)?;
    if instance.location.len() != family.axes.len() {
        return Err(Error::Family(format!(
            "instance {:?} has {} coordinates for {} axes",
            instance.style_name,
            instance.location.len(),
            family.axes.len()
        )));
    }
    let location: Vec<f64> = family.axes.iter().zip(&instance.location).map(|(a, &v)| normalise(a, v)).collect();
    let weights = instance::master_weights(&src.model, &location);
    let shapes = src.shapes()?;
    let upm = f64::from(family.metrics.upm);

    // Remove overlaps glyph by glyph, on as many threads as there are cores.
    let interpolated: Vec<instance::InstanceShape> =
        shapes.iter().map(|ms| instance::interpolate(ms, &weights)).collect();
    let unions = instance::parallel_unions(&interpolated, upm);

    let mut compiled = Vec::with_capacity(shapes.len());
    let mut kept = Vec::new();
    for (gid, (shape, union)) in interpolated.iter().zip(unions).enumerate() {
        let name = &src.names[gid];
        compiled.push(match shape {
            instance::InstanceShape::Empty => Compiled::Empty,
            instance::InstanceShape::Simple(paths) => match union {
                Some(Ok(merged)) => compile_simple(name, &[merged], false)?,
                Some(Err(why)) => {
                    kept.push((name.clone(), why));
                    compile_simple(name, std::slice::from_ref(paths), true)?
                }
                None => compile_simple(name, std::slice::from_ref(paths), true)?,
            },
            instance::InstanceShape::Composite(comps) => compile_composite(name, std::slice::from_ref(comps))?,
        });
    }
    let glyf = build_glyf(&src.names, &compiled, 0, true, false)?;
    let mut advances = Vec::with_capacity(src.order.len());
    for (gid, &i) in src.order.iter().enumerate() {
        let a = ot_round(instance::mix(&weights, family.masters.iter().map(|m| m.glyphs[i].advance)));
        advances.push(u16::try_from(a).map_err(|_| Error::Glyph {
            glyph: src.names[gid].clone(),
            detail: format!("advance {a} is out of range"),
        })?);
    }
    let mut anchors = Vec::with_capacity(src.order.len());
    for (gid, &i) in src.order.iter().enumerate() {
        let mut out = BTreeMap::new();
        for name in src.default_glyph(gid).anchors.keys() {
            let get = |m: &Master| m.glyphs[i].anchors.get(name).copied().unwrap_or_default();
            let x = instance::mix(&weights, family.masters.iter().map(|m| get(m).x));
            let y = instance::mix(&weights, family.masters.iter().map(|m| get(m).y));
            out.insert(name.clone(), round_anchor(&src.names[gid], x, y)?);
        }
        anchors.push(out);
    }
    let built = src.built(advances, anchors, glyf);
    let style = Style::new(family, &instance.style_name, &instance.location);
    let mut names = names::style_names(family, &style);
    let stat = names::stat(family, Some(instance), &mut names)?;
    let bytes = finish(FontBuilder::new(), family, &built, &style, names, stat)?;
    Ok(StaticFont { bytes, kept_overlaps: kept })
}

/// The font compressed as WOFF2 (Brotli quality 11), deterministically.
pub fn woff2(ttf: &[u8]) -> Result<Vec<u8>, Error> {
    ttf2woff2::encode(ttf, ttf2woff2::BrotliQuality::default()).map_err(|e| Error::Woff2(e.to_string()))
}

/// The SHA-256 of `data` in lower-case hexadecimal, as `sha256sum` prints it.
pub fn sha256_hex(data: &[u8]) -> String {
    let digest = sha2::Sha256::digest(data);
    digest.iter().map(|b| format!("{b:02x}")).collect()
}

#[cfg(test)]
mod tests;
