//! The OpenType `MATH` table: what a formula typesetter needs beyond the glyphs. Constants for the layout of
//! scripts, fractions, radicals and limits; for single glyphs the italic correction and where an accent
//! attaches; and for the glyphs that stretch (delimiters, radicals, big operators, wide accents, arrows) the
//! larger variants and the pieces a size of any length is assembled from.

use std::collections::BTreeMap;

use write_fonts::tables::layout::CoverageTable;
use write_fonts::tables::math::{
    GlyphAssembly, GlyphPartRecord, Math as MathTable, MathConstants, MathGlyphConstruction, MathGlyphInfo,
    MathGlyphVariantRecord, MathItalicsCorrectionInfo, MathTopAccentAttachment, MathValueRecord, MathVariants,
    PartFlags,
};
use write_fonts::types::{FWord, GlyphId16, UfWord};

use crate::{Construction, Error, Math};

/// The constants of the table, by the names the OpenType specification gives them, in its order.
pub const CONSTANTS: [&str; 56] = [
    "ScriptPercentScaleDown",
    "ScriptScriptPercentScaleDown",
    "DelimitedSubFormulaMinHeight",
    "DisplayOperatorMinHeight",
    "MathLeading",
    "AxisHeight",
    "AccentBaseHeight",
    "FlattenedAccentBaseHeight",
    "SubscriptShiftDown",
    "SubscriptTopMax",
    "SubscriptBaselineDropMin",
    "SuperscriptShiftUp",
    "SuperscriptShiftUpCramped",
    "SuperscriptBottomMin",
    "SuperscriptBaselineDropMax",
    "SubSuperscriptGapMin",
    "SuperscriptBottomMaxWithSubscript",
    "SpaceAfterScript",
    "UpperLimitGapMin",
    "UpperLimitBaselineRiseMin",
    "LowerLimitGapMin",
    "LowerLimitBaselineDropMin",
    "StackTopShiftUp",
    "StackTopDisplayStyleShiftUp",
    "StackBottomShiftDown",
    "StackBottomDisplayStyleShiftDown",
    "StackGapMin",
    "StackDisplayStyleGapMin",
    "StretchStackTopShiftUp",
    "StretchStackBottomShiftDown",
    "StretchStackGapAboveMin",
    "StretchStackGapBelowMin",
    "FractionNumeratorShiftUp",
    "FractionNumeratorDisplayStyleShiftUp",
    "FractionDenominatorShiftDown",
    "FractionDenominatorDisplayStyleShiftDown",
    "FractionNumeratorGapMin",
    "FractionNumDisplayStyleGapMin",
    "FractionRuleThickness",
    "FractionDenominatorGapMin",
    "FractionDenomDisplayStyleGapMin",
    "SkewedFractionHorizontalGap",
    "SkewedFractionVerticalGap",
    "OverbarVerticalGap",
    "OverbarRuleThickness",
    "OverbarExtraAscender",
    "UnderbarVerticalGap",
    "UnderbarRuleThickness",
    "UnderbarExtraDescender",
    "RadicalVerticalGap",
    "RadicalDisplayStyleVerticalGap",
    "RadicalRuleThickness",
    "RadicalExtraAscender",
    "RadicalKernBeforeDegree",
    "RadicalKernAfterDegree",
    "RadicalDegreeBottomRaisePercent",
];

fn record(v: i16) -> MathValueRecord {
    MathValueRecord::new(FWord::new(v), None)
}

fn unsigned(name: &str, v: i16) -> Result<UfWord, Error> {
    u16::try_from(v)
        .map(UfWord::new)
        .map_err(|_| Error::Family(format!("MATH: {name} is {v}, and may not be negative")))
}

/// The constants table from values by name: every constant exactly once.
fn constants(values: &[(String, i16)]) -> Result<MathConstants, Error> {
    let mut by_name: BTreeMap<&str, i16> = BTreeMap::new();
    for (name, v) in values {
        if !CONSTANTS.contains(&name.as_str()) {
            return Err(Error::Family(format!("MATH: {name:?} is not a constant of the table")));
        }
        if by_name.insert(name, *v).is_some() {
            return Err(Error::Family(format!("MATH: the constant {name} is given twice")));
        }
    }
    let get = |name: &str| {
        by_name.get(name).copied().ok_or_else(|| Error::Family(format!("MATH: the constant {name} is not given")))
    };
    let r = |name: &str| get(name).map(record);
    Ok(MathConstants {
        script_percent_scale_down: get("ScriptPercentScaleDown")?,
        script_script_percent_scale_down: get("ScriptScriptPercentScaleDown")?,
        delimited_sub_formula_min_height: unsigned(
            "DelimitedSubFormulaMinHeight",
            get("DelimitedSubFormulaMinHeight")?,
        )?,
        display_operator_min_height: unsigned("DisplayOperatorMinHeight", get("DisplayOperatorMinHeight")?)?,
        math_leading: r("MathLeading")?,
        axis_height: r("AxisHeight")?,
        accent_base_height: r("AccentBaseHeight")?,
        flattened_accent_base_height: r("FlattenedAccentBaseHeight")?,
        subscript_shift_down: r("SubscriptShiftDown")?,
        subscript_top_max: r("SubscriptTopMax")?,
        subscript_baseline_drop_min: r("SubscriptBaselineDropMin")?,
        superscript_shift_up: r("SuperscriptShiftUp")?,
        superscript_shift_up_cramped: r("SuperscriptShiftUpCramped")?,
        superscript_bottom_min: r("SuperscriptBottomMin")?,
        superscript_baseline_drop_max: r("SuperscriptBaselineDropMax")?,
        sub_superscript_gap_min: r("SubSuperscriptGapMin")?,
        superscript_bottom_max_with_subscript: r("SuperscriptBottomMaxWithSubscript")?,
        space_after_script: r("SpaceAfterScript")?,
        upper_limit_gap_min: r("UpperLimitGapMin")?,
        upper_limit_baseline_rise_min: r("UpperLimitBaselineRiseMin")?,
        lower_limit_gap_min: r("LowerLimitGapMin")?,
        lower_limit_baseline_drop_min: r("LowerLimitBaselineDropMin")?,
        stack_top_shift_up: r("StackTopShiftUp")?,
        stack_top_display_style_shift_up: r("StackTopDisplayStyleShiftUp")?,
        stack_bottom_shift_down: r("StackBottomShiftDown")?,
        stack_bottom_display_style_shift_down: r("StackBottomDisplayStyleShiftDown")?,
        stack_gap_min: r("StackGapMin")?,
        stack_display_style_gap_min: r("StackDisplayStyleGapMin")?,
        stretch_stack_top_shift_up: r("StretchStackTopShiftUp")?,
        stretch_stack_bottom_shift_down: r("StretchStackBottomShiftDown")?,
        stretch_stack_gap_above_min: r("StretchStackGapAboveMin")?,
        stretch_stack_gap_below_min: r("StretchStackGapBelowMin")?,
        fraction_numerator_shift_up: r("FractionNumeratorShiftUp")?,
        fraction_numerator_display_style_shift_up: r("FractionNumeratorDisplayStyleShiftUp")?,
        fraction_denominator_shift_down: r("FractionDenominatorShiftDown")?,
        fraction_denominator_display_style_shift_down: r("FractionDenominatorDisplayStyleShiftDown")?,
        fraction_numerator_gap_min: r("FractionNumeratorGapMin")?,
        fraction_num_display_style_gap_min: r("FractionNumDisplayStyleGapMin")?,
        fraction_rule_thickness: r("FractionRuleThickness")?,
        fraction_denominator_gap_min: r("FractionDenominatorGapMin")?,
        fraction_denom_display_style_gap_min: r("FractionDenomDisplayStyleGapMin")?,
        skewed_fraction_horizontal_gap: r("SkewedFractionHorizontalGap")?,
        skewed_fraction_vertical_gap: r("SkewedFractionVerticalGap")?,
        overbar_vertical_gap: r("OverbarVerticalGap")?,
        overbar_rule_thickness: r("OverbarRuleThickness")?,
        overbar_extra_ascender: r("OverbarExtraAscender")?,
        underbar_vertical_gap: r("UnderbarVerticalGap")?,
        underbar_rule_thickness: r("UnderbarRuleThickness")?,
        underbar_extra_descender: r("UnderbarExtraDescender")?,
        radical_vertical_gap: r("RadicalVerticalGap")?,
        radical_display_style_vertical_gap: r("RadicalDisplayStyleVerticalGap")?,
        radical_rule_thickness: r("RadicalRuleThickness")?,
        radical_extra_ascender: r("RadicalExtraAscender")?,
        radical_kern_before_degree: r("RadicalKernBeforeDegree")?,
        radical_kern_after_degree: r("RadicalKernAfterDegree")?,
        radical_degree_bottom_raise_percent: get("RadicalDegreeBottomRaisePercent")?,
    })
}

/// (glyph id, value) of the entries whose glyph the font has, in glyph-id order: a coverage table and the array
/// beside it list the same glyphs in the same order.
fn by_glyph<T: Clone>(
    entries: &[(String, T)],
    gid: &BTreeMap<&str, GlyphId16>,
    what: &str,
) -> Result<Vec<(GlyphId16, T)>, Error> {
    let mut out: BTreeMap<GlyphId16, T> = BTreeMap::new();
    for (name, value) in entries {
        let Some(&g) = gid.get(name.as_str()) else {
            return Err(Error::Family(format!("MATH: {what} for {name:?}, which is not a glyph of the font")));
        };
        if out.insert(g, value.clone()).is_some() {
            return Err(Error::Family(format!("MATH: two {what}s for {name:?}")));
        }
    }
    Ok(out.into_iter().collect())
}

fn construction(c: &Construction, gid: &BTreeMap<&str, GlyphId16>) -> Result<MathGlyphConstruction, Error> {
    let glyph = |name: &str| {
        gid.get(name).copied().ok_or_else(|| {
            Error::Family(format!("MATH: {name:?}, a size or a piece of {:?}, is not a glyph of the font", c.glyph))
        })
    };
    let variants = c
        .variants
        .iter()
        .map(|(name, advance)| Ok(MathGlyphVariantRecord::new(glyph(name)?, UfWord::new(*advance))))
        .collect::<Result<Vec<_>, Error>>()?;
    let assembly = if c.parts.is_empty() {
        None
    } else {
        let parts = c
            .parts
            .iter()
            .map(|p| {
                let flags = if p.extender { PartFlags::EXTENDER_FLAG } else { PartFlags::empty() };
                Ok(GlyphPartRecord::new(
                    glyph(&p.glyph)?,
                    UfWord::new(p.start),
                    UfWord::new(p.end),
                    UfWord::new(p.advance),
                    flags,
                ))
            })
            .collect::<Result<Vec<_>, Error>>()?;
        Some(GlyphAssembly::new(record(c.italic_correction), parts))
    };
    Ok(MathGlyphConstruction::new(assembly, variants))
}

/// The coverage and the constructions of the glyphs that stretch one way, in glyph-id order.
fn constructions(
    list: &[Construction],
    gid: &BTreeMap<&str, GlyphId16>,
) -> Result<(Option<CoverageTable>, Vec<MathGlyphConstruction>), Error> {
    let entries: Vec<(String, &Construction)> = list.iter().map(|c| (c.glyph.clone(), c)).collect();
    let sorted = by_glyph(&entries, gid, "construction")?;
    if sorted.is_empty() {
        return Ok((None, Vec::new()));
    }
    let coverage: CoverageTable = sorted.iter().map(|(g, _)| *g).collect();
    let built = sorted.iter().map(|(_, c)| construction(c, gid)).collect::<Result<Vec<_>, Error>>()?;
    Ok((Some(coverage), built))
}

/// The `MATH` table of a font whose glyphs are `names`, in glyph-id order.
pub(crate) fn math(desc: &Math, names: &[String]) -> Result<MathTable, Error> {
    let gid: BTreeMap<&str, GlyphId16> = names
        .iter()
        .enumerate()
        .map(|(i, n)| {
            Ok((n.as_str(), GlyphId16::new(u16::try_from(i).map_err(|_| Error::Family("too many glyphs".into()))?)))
        })
        .collect::<Result<_, Error>>()?;
    let italics = by_glyph(&desc.italic_corrections, &gid, "italic correction")?;
    let italics = (!italics.is_empty()).then(|| {
        MathItalicsCorrectionInfo::new(
            italics.iter().map(|(g, _)| *g).collect(),
            italics.iter().map(|(_, v)| record(*v)).collect(),
        )
    });
    let accents = by_glyph(&desc.top_accents, &gid, "accent attachment")?;
    let accents = (!accents.is_empty()).then(|| {
        MathTopAccentAttachment::new(
            accents.iter().map(|(g, _)| *g).collect(),
            accents.iter().map(|(_, v)| record(*v)).collect(),
        )
    });
    let tall: Vec<(String, ())> = desc.extended_shapes.iter().map(|n| (n.clone(), ())).collect();
    let tall = by_glyph(&tall, &gid, "extended shape")?;
    let tall: Option<CoverageTable> = (!tall.is_empty()).then(|| tall.iter().map(|(g, ())| *g).collect());
    let info = MathGlyphInfo::new(italics, accents, tall, None);
    let (vertical_coverage, vertical) = constructions(&desc.vertical, &gid)?;
    let (horizontal_coverage, horizontal) = constructions(&desc.horizontal, &gid)?;
    let variants = MathVariants::new(
        UfWord::new(desc.min_connector_overlap),
        vertical_coverage,
        horizontal_coverage,
        vertical,
        horizontal,
    );
    Ok(MathTable::new(constants(&desc.constants)?, info, variants))
}
