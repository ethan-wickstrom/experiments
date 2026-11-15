//! Names: the `name` table, and the two tables that place a font in its family by name, `fvar` (axes and
//! named instances) and `STAT` (the style attributes of each axis value).

use std::collections::BTreeMap;

use write_fonts::OffsetMarker;
use write_fonts::tables::fvar::{AxisInstanceArrays, Fvar, InstanceRecord, VariationAxisRecord};
use write_fonts::tables::name::{Name, NameRecord};
use write_fonts::tables::stat::{AxisRecord, AxisValue, AxisValueTableFlags, Stat};
use write_fonts::types::{Fixed, NameId, Tag};

use crate::{AxisLabel, Error, Family, Instance, Style, meta};

/// The name records of a font, Windows platform only (3, 1, 0x409).
#[derive(Clone, Debug, Default)]
pub(crate) struct Names {
    records: BTreeMap<u16, String>,
}

/// The first name ID a font may use for its own strings.
const FIRST_FONT_SPECIFIC: u16 = 256;

impl Names {
    /// Set a predefined name ID.
    pub(crate) fn set(&mut self, id: u16, s: &str) {
        self.records.insert(id, s.to_owned());
    }

    /// A font-specific name ID (256 or more) for `s`, reusing one that already holds it.
    pub(crate) fn add(&mut self, s: &str) -> NameId {
        if let Some((&id, _)) = self.records.range(FIRST_FONT_SPECIFIC..).find(|(_, v)| v.as_str() == s) {
            return NameId::new(id);
        }
        let next = self.records.range(FIRST_FONT_SPECIFIC..).next_back().map_or(FIRST_FONT_SPECIFIC, |(&id, _)| id + 1);
        self.records.insert(next, s.to_owned());
        NameId::new(next)
    }

    /// The string of a name ID, if set.
    pub(crate) fn get(&self, id: u16) -> Option<&str> {
        self.records.get(&id).map(String::as_str)
    }

    /// The `name` table.
    pub(crate) fn table(&self) -> Name {
        let records = self
            .records
            .iter()
            .map(|(&id, s)| NameRecord::new(3, 1, 0x409, NameId::new(id), OffsetMarker::new(s.clone())))
            .collect();
        Name::new(records)
    }
}

/// A PostScript name part: the string without spaces.
pub(crate) fn ps(s: &str) -> String {
    s.chars().filter(|c| !c.is_whitespace()).collect()
}

/// The PostScript name of a style: "RachisMono-SemiBoldItalic".
pub(crate) fn postscript_name(family: &Family, style_name: &str) -> String {
    format!("{}-{}", ps(&family.name), ps(style_name))
}

/// The names of a font of `family` in `style`: the four style-linked styles (Regular, Italic, Bold, Bold
/// Italic) name the family in ID 1 and the style in ID 2; every other style makes a family of its own for
/// software that knows four styles (ID 1 "Family Light", ID 2 "Regular" or "Italic") and gives the real family
/// and style in IDs 16 and 17.
pub(crate) fn style_names(family: &Family, style: &Style) -> Names {
    let mut n = Names::default();
    let full = format!("{} {}", family.name, style.name);
    let psname = postscript_name(family, &style.name);
    n.set(0, meta::COPYRIGHT);
    if style.linked {
        n.set(1, &family.name);
        n.set(2, &style.name);
    } else {
        n.set(1, &format!("{} {}", family.name, style.weight_name));
        n.set(2, if style.italic { "Italic" } else { "Regular" });
        n.set(16, &family.name);
        n.set(17, &style.name);
    }
    let vendor = String::from_utf8_lossy(meta::VENDOR).into_owned();
    n.set(3, &format!("{};{vendor};{psname}", meta::version_string()));
    n.set(4, &full);
    n.set(5, &format!("Version {}", meta::version_string()));
    n.set(6, &psname);
    n.set(10, meta::DESCRIPTION);
    n.set(11, meta::VENDOR_URL);
    n.set(13, meta::LICENSE);
    n.set(14, meta::LICENSE_URL);
    n
}

/// The variations PostScript name prefix, name ID 25: "RachisMono", or "RachisMonoItalic" for an italic family.
pub(crate) fn variations_prefix(family: &Family) -> String {
    format!("{}{}", ps(&family.name), if family.italic { "Italic" } else { "" })
}

/// The `fvar` table, adding the axis and instance names to `names`. The instance at the default location reuses
/// name IDs 2 (or 17) and 6.
pub(crate) fn fvar(family: &Family, names: &mut Names) -> Fvar {
    let axes = family
        .axes
        .iter()
        .map(|a| {
            VariationAxisRecord::new(
                Tag::new_checked(a.tag.as_bytes()).unwrap_or(Tag::new(b"    ")),
                Fixed::from_f64(a.min),
                Fixed::from_f64(a.default),
                Fixed::from_f64(a.max),
                0,
                names.add(&a.name),
            )
        })
        .collect();
    let defaults: Vec<f64> = family.axes.iter().map(|a| a.default).collect();
    let subfamily_id = if names.get(17).is_some() { 17 } else { 2 };
    let instances = family
        .instances
        .iter()
        .map(|i| {
            let is_default = i.location == defaults;
            let (sub, psid) = if is_default {
                (NameId::new(subfamily_id), NameId::new(6))
            } else {
                (names.add(&i.style_name), names.add(&postscript_name(family, &i.style_name)))
            };
            InstanceRecord {
                subfamily_name_id: sub,
                flags: 0,
                coordinates: i.location.iter().map(|&v| Fixed::from_f64(v)).collect(),
                post_script_name_id: Some(psid),
            }
        })
        .collect();
    Fvar::new(AxisInstanceArrays::new(axes, instances))
}

fn fixed(v: f64) -> Fixed {
    Fixed::from_f64(v)
}

/// One axis value of `STAT`. Format 2 when the label has a range, format 3 when it is linked (never on the
/// weight axis: kitty ignores format 3 when it matches style names), format 1 otherwise.
fn axis_value(index: u16, tag: &str, label: &AxisLabel, names: &mut Names) -> AxisValue {
    let flags =
        if label.elidable { AxisValueTableFlags::ELIDABLE_AXIS_VALUE_NAME } else { AxisValueTableFlags::empty() };
    let name = names.add(&label.name);
    if let Some((lo, hi)) = label.range {
        return AxisValue::format_2(index, flags, name, fixed(label.value), fixed(lo), fixed(hi));
    }
    match label.linked {
        Some(linked) if tag != "wght" => AxisValue::format_3(index, flags, name, fixed(label.value), fixed(linked)),
        _ => AxisValue::format_1(index, flags, name, fixed(label.value)),
    }
}

/// The `ital` axis value of an upright family (Roman, elidable, linked to the italic) or an italic one.
fn ital_label(italic: bool) -> AxisLabel {
    if italic {
        AxisLabel { name: "Italic".into(), value: 1.0, elidable: false, linked: None, range: None }
    } else {
        AxisLabel { name: "Roman".into(), value: 0.0, elidable: true, linked: Some(1.0), range: None }
    }
}

/// The `STAT` table. For a variable font (`instance` is `None`) every label of every axis is a value; for a
/// static font, one value per axis: the label at the instance's location, or a value named by its number.
/// An `ital` axis is added after the family's axes unless the family has one.
pub(crate) fn stat(family: &Family, instance: Option<&Instance>, names: &mut Names) -> Result<Stat, Error> {
    let mut records = Vec::new();
    let mut values = Vec::new();
    for (i, a) in family.axes.iter().enumerate() {
        let index = u16::try_from(i).map_err(|_| Error::Family("too many axes".into()))?;
        let tag = Tag::new_checked(a.tag.as_bytes())
            .map_err(|_| Error::Family(format!("axis tag {:?} is not a tag", a.tag)))?;
        records.push(AxisRecord::new(tag, names.add(&a.name), index));
        match instance {
            None => {
                for label in &a.labels {
                    values.push(axis_value(index, &a.tag, label, names));
                }
            }
            Some(inst) => {
                let v = inst.location.get(i).copied().unwrap_or(a.default);
                let label = a.labels.iter().find(|l| l.value == v).cloned().unwrap_or(AxisLabel {
                    name: format!("{v}"),
                    value: v,
                    elidable: false,
                    linked: None,
                    range: None,
                });
                let label = AxisLabel { range: None, ..label };
                values.push(axis_value(index, &a.tag, &label, names));
            }
        }
    }
    if !family.axes.iter().any(|a| a.tag == "ital") {
        let index = u16::try_from(family.axes.len()).map_err(|_| Error::Family("too many axes".into()))?;
        records.push(AxisRecord::new(Tag::new(b"ital"), names.add("Italic"), index));
        values.push(axis_value(index, "ital", &ital_label(family.italic), names));
    }
    Ok(Stat::new(records, values, NameId::new(2)))
}
