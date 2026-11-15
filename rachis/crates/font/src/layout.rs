//! OpenType layout: `GDEF` glyph classes, `GSUB` single substitutions (stylistic sets, superiors, inferiors) and
//! `GPOS` mark-to-base attachment and pair kerning. On principle there is nothing else: no ligatures, nothing
//! contextual.

use std::collections::{BTreeMap, BTreeSet};

use write_fonts::read::collections::IntSet;
use write_fonts::tables::gdef::Gdef;
use write_fonts::tables::gpos::builders::{AnchorBuilder, MarkToBaseBuilder, PairPosBuilder, ValueRecordBuilder};
use write_fonts::tables::gpos::{Gpos, PositionLookup, PositionLookupList};
use write_fonts::tables::gsub::builders::{AlternateSubBuilder, SingleSubBuilder};
use write_fonts::tables::gsub::{AlternateSubst, Gsub, SubstitutionLookup, SubstitutionLookupList};
use write_fonts::tables::layout::builders::{Builder, LookupBuilder};
use write_fonts::tables::layout::{
    ClassDef, Feature, FeatureList, FeatureParams, FeatureRecord, LangSys, Lookup, LookupFlag, Script, ScriptList,
    ScriptRecord, StylisticSetParams,
};
use write_fonts::tables::variations::ivs_builder::VariationStoreBuilder;
use write_fonts::types::{GlyphId16, Tag};

use crate::names::Names;
use crate::{Built, Error, Family};

/// The scripts every feature is registered under, in tag order. A mathematics font adds `math`, the script a
/// formula is shaped in.
const SCRIPTS: [&[u8; 4]; 3] = [b"DFLT", b"grek", b"latn"];
const MATH_SCRIPT: &[u8; 4] = b"math";

/// The layout tables of one font, and the longest context their lookups read (for `OS/2.usMaxContext`).
pub(crate) struct Layout {
    pub gdef: Gdef,
    pub gsub: Option<Gsub>,
    pub gpos: Option<Gpos>,
    pub max_context: u16,
}

fn tag(s: &str) -> Result<Tag, Error> {
    Tag::new_checked(s.as_bytes()).map_err(|_| Error::Family(format!("{s:?} is not a feature tag")))
}

/// A script list that registers every feature, under each script's default language system.
fn script_list(features: usize, math: bool) -> Result<ScriptList, Error> {
    let indices: Vec<u16> = (0..features)
        .map(|i| u16::try_from(i).map_err(|_| Error::Family("too many features".into())))
        .collect::<Result<_, _>>()?;
    Ok(ScriptList::new(
        SCRIPTS
            .iter()
            .chain(math.then_some(&MATH_SCRIPT))
            .map(|t| ScriptRecord::new(Tag::new(t), Script::new(Some(LangSys::new(indices.clone())), vec![])))
            .collect(),
    ))
}

/// Features from (tag, lookup index, parameters): one feature per tag, its lookups in order, features in tag
/// order as the specification requires.
fn feature_list(entries: Vec<(Tag, u16, Option<FeatureParams>)>) -> FeatureList {
    let mut by_tag: BTreeMap<Tag, (Vec<u16>, Option<FeatureParams>)> = BTreeMap::new();
    for (t, lookup, params) in entries {
        let e = by_tag.entry(t).or_default();
        e.0.push(lookup);
        if e.1.is_none() {
            e.1 = params;
        }
    }
    FeatureList::new(
        by_tag.into_iter().map(|(t, (lookups, params))| FeatureRecord::new(t, Feature::new(params, lookups))).collect(),
    )
}

/// Whether a feature tag is a stylistic set, `ss01` … `ss20`, which may carry a name.
fn is_stylistic_set(t: &str) -> bool {
    t.len() == 4 && t.starts_with("ss") && t[2..].parse::<u8>().is_ok_and(|n| (1..=20).contains(&n))
}

/// The layout tables of a font whose glyphs are `built`. Anchors are the font's own (the default master's in
/// a variable font, the interpolated ones in a static font). Stylistic-set names are added to `names`.
pub(crate) fn layout(family: &Family, built: &Built, names: &mut Names) -> Result<Layout, Error> {
    let gid: BTreeMap<&str, GlyphId16> = built
        .names
        .iter()
        .enumerate()
        .map(|(i, n)| {
            Ok((n.as_str(), GlyphId16::new(u16::try_from(i).map_err(|_| Error::Family("too many glyphs".into()))?)))
        })
        .collect::<Result<_, Error>>()?;
    let mut var_store = VariationStoreBuilder::new(0);
    let mut max_context = 0u16;

    // GDEF: marks are class 3, everything else class 1.
    let classes: ClassDef =
        gid.values().map(|&g| (g, if built.marks[usize::from(g.to_u16())] { 3 } else { 1 })).collect();
    let gdef = Gdef::new(Some(classes), None, None, None);

    // GSUB: one single-substitution lookup per feature entry.
    let mut lookups = Vec::new();
    let mut entries = Vec::new();
    for sub in &family.features {
        let mut b = SingleSubBuilder::default();
        for (from, to) in &sub.pairs {
            if let (Some(&a), Some(&z)) = (gid.get(from.as_str()), gid.get(to.as_str())) {
                b.insert(a, z);
            }
        }
        if b.is_empty() {
            continue;
        }
        let t = tag(&sub.tag)?;
        let params = match &sub.label {
            Some(label) if is_stylistic_set(&sub.tag) => {
                Some(FeatureParams::StylisticSet(StylisticSetParams::new(names.add(label))))
            }
            _ => None,
        };
        let index = u16::try_from(lookups.len()).map_err(|_| Error::Family("too many lookups".into()))?;
        let lookup = LookupBuilder::new_with_lookups(LookupFlag::empty(), None, vec![b]).build(&mut var_store);
        lookups.push(SubstitutionLookup::Single(lookup));
        entries.push((t, index, params));
        max_context = max_context.max(1);
    }
    // and one lookup of alternates per feature of alternates
    for alt in &family.alternates {
        let mut b = AlternateSubBuilder::default();
        for (from, to) in &alt.alternates {
            let targets: Option<Vec<GlyphId16>> = to.iter().map(|n| gid.get(n.as_str()).copied()).collect();
            if let (Some(&a), Some(targets)) = (gid.get(from.as_str()), targets) {
                b.insert(a, targets);
            }
        }
        if b.is_empty() {
            continue;
        }
        let index = u16::try_from(lookups.len()).map_err(|_| Error::Family("too many lookups".into()))?;
        let lookup = LookupBuilder::new_with_lookups(LookupFlag::empty(), None, vec![b]).build(&mut var_store);
        let subtables = lookup.subtables.into_iter().map(|s| AlternateSubst::Format1(s.into_inner())).collect();
        lookups.push(SubstitutionLookup::Alternate(Lookup::new(lookup.lookup_flag, subtables)));
        entries.push((tag(&alt.tag)?, index, None));
        max_context = max_context.max(1);
    }
    let math = family.math.is_some();
    let gsub = if lookups.is_empty() {
        None
    } else {
        let features = feature_list(entries);
        Some(Gsub::new(
            script_list(features.feature_records.len(), math)?,
            features,
            SubstitutionLookupList::new(lookups),
        ))
    };

    // GPOS: mark-to-base from anchors X on bases and _X on marks; kerning pairs.
    let mut lookups: Vec<PositionLookup> = Vec::new();
    let mut entries = Vec::new();
    let mut mark_classes: BTreeSet<&str> = BTreeSet::new();
    let mut marks = MarkToBaseBuilder::default();
    for (i, anchors) in built.anchors.iter().enumerate() {
        if !built.marks[i] {
            continue;
        }
        for (name, &(x, y)) in anchors {
            if let Some(class) = name.strip_prefix('_') {
                let g = GlyphId16::new(u16::try_from(i).map_err(|_| Error::Family("too many glyphs".into()))?);
                marks
                    .insert_mark(g, class, AnchorBuilder::new(x, y))
                    .map_err(|e| Error::Glyph { glyph: built.names[i].clone(), detail: e.to_string() })?;
                mark_classes.insert(class);
            }
        }
    }
    let mut has_bases = false;
    for (i, anchors) in built.anchors.iter().enumerate() {
        if built.marks[i] {
            continue;
        }
        for (name, &(x, y)) in anchors {
            if mark_classes.contains(name.as_str()) {
                let g = GlyphId16::new(u16::try_from(i).map_err(|_| Error::Family("too many glyphs".into()))?);
                marks.insert_base(g, name, AnchorBuilder::new(x, y));
                has_bases = true;
            }
        }
    }
    if has_bases {
        let index = u16::try_from(lookups.len()).map_err(|_| Error::Family("too many lookups".into()))?;
        let lookup = LookupBuilder::new_with_lookups(LookupFlag::empty(), None, vec![marks]).build(&mut var_store);
        lookups.push(lookup.into());
        entries.push((Tag::new(b"mark"), index, None));
        max_context = max_context.max(2);
    }
    let mut kern = PairPosBuilder::default();
    let mut has_kern = false;
    for k in &family.kerning {
        if let (Some(&a), Some(&b)) = (gid.get(k.left.as_str()), gid.get(k.right.as_str())) {
            kern.insert_pair(a, ValueRecordBuilder::new().with_x_advance(k.value), b, ValueRecordBuilder::new());
            has_kern = true;
        }
    }
    if let Some(classes) = &family.kern_classes {
        let set = |names: &[String]| -> IntSet<GlyphId16> {
            names.iter().filter_map(|n| gid.get(n.as_str()).copied()).collect()
        };
        for (first, row) in classes.first.iter().zip(&classes.values) {
            for (second, &value) in classes.second.iter().zip(row) {
                let (a, b) = (set(first), set(second));
                if value != 0 && !a.is_empty() && !b.is_empty() {
                    kern.insert_classes(
                        a,
                        ValueRecordBuilder::new().with_x_advance(value),
                        b,
                        ValueRecordBuilder::new(),
                    );
                    has_kern = true;
                }
            }
        }
    }
    if has_kern {
        let index = u16::try_from(lookups.len()).map_err(|_| Error::Family("too many lookups".into()))?;
        let lookup = LookupBuilder::new_with_lookups(LookupFlag::IGNORE_MARKS, None, vec![kern]).build(&mut var_store);
        lookups.push(PositionLookup::Pair(lookup));
        entries.push((Tag::new(b"kern"), index, None));
        max_context = max_context.max(2);
    }
    let gpos = if lookups.is_empty() {
        None
    } else {
        let features = feature_list(entries);
        Some(Gpos::new(script_list(features.feature_records.len(), math)?, features, PositionLookupList::new(lookups)))
    };
    Ok(Layout { gdef, gsub, gpos, max_context })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stylistic_set_tags() {
        assert!(is_stylistic_set("ss01"));
        assert!(is_stylistic_set("ss20"));
        assert!(!is_stylistic_set("ss21"));
        assert!(!is_stylistic_set("sups"));
    }
}
