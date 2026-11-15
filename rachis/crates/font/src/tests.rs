//! Tests that compile fonts and read them back with read-fonts and skrifa: a small synthetic family with two
//! axes, proportional advances, components, a mark and kerning; and the Rachis Mono family itself.

use std::collections::BTreeMap;

use rachis_kernel::pen::{rect, superellipse};
use rachis_kernel::{Glyph, V, pt};
use read_fonts::types::Tag;
use read_fonts::{FontRef, TableProvider};
use skrifa::instance::{LocationRef, Size};
use skrifa::outline::{DrawSettings, OutlinePen};
use skrifa::{GlyphId, MetadataProvider, string::StringId};

use super::*;
use crate::glyf::Compiled;
use crate::source::{Source, compile_masters, normalise};

// ---------------------------------------------------------------------------------------------------------------
// helpers

fn glyph(name: &str, advance: f64, unicodes: &[u32]) -> Glyph {
    Glyph { name: name.into(), advance, unicodes: unicodes.to_vec(), ..Glyph::default() }
}

fn label(name: &str, value: f64, elidable: bool) -> AxisLabel {
    AxisLabel { name: name.into(), value, elidable, linked: None, range: None }
}

fn metrics(fixed_pitch: bool, italic_angle: f64) -> Metrics {
    Metrics {
        upm: 1000,
        ascender: 1000,
        descender: -250,
        x_height: 500,
        cap_height: 700,
        italic_angle,
        underline_position: -100,
        underline_thickness: 60,
        strikeout_position: 300,
        strikeout_size: 60,
        fixed_pitch,
    }
}

/// A synthetic master: `w` is the stem weight, `n` how narrow (0 normal, 1 condensed).
fn synthetic_glyphs(w: f64, n: f64) -> Vec<Glyph> {
    let width = 600.0 - 150.0 * n + w;
    let mut out = Vec::new();
    // listed out of order on purpose: the compiler must sort them
    let mut v = glyph("V", width, &[0x56]);
    v.contours.push(rachis_kernel::pen::polygon(&[
        pt(40.0, 700.0),
        pt(40.0 + w, 700.0),
        pt(width / 2.0 + w / 2.0, 0.0),
        pt(width / 2.0 - w / 2.0, 0.0),
    ]));
    out.push(v);
    let mut a = glyph("A", width, &[0x41]);
    a.contours.push(rect(50.0, 0.0, 50.0 + w, 700.0));
    a.contours.push(rect(50.0, 300.0, width - 50.0, 300.0 + w * 0.8));
    a.contours.push(rect(width - 50.0 - w, 0.0, width - 50.0, 700.0));
    a.anchors.insert("top".into(), pt(width / 2.0, 700.0));
    out.push(a);
    let mut alt = glyph("A.alt", width, &[]);
    alt.contours.push(superellipse(width / 2.0, 350.0, width / 2.0 - 40.0, 350.0, 0.6));
    alt.contours.push(superellipse(width / 2.0, 350.0, width / 2.0 - 40.0 - w, 350.0 - w, 0.6).reversed());
    out.push(alt);
    let mut acute = glyph("acutecomb", 0.0, &[0x301]);
    acute.mark = true;
    acute.contours.push(rect(-40.0, 750.0, 40.0 + w * 0.3, 850.0));
    acute.anchors.insert("_top".into(), pt(0.0, 700.0));
    out.push(acute);
    let mut aacute = glyph("Aacute", width, &[0xC1]);
    aacute.components.push(("A".into(), V::ZERO));
    aacute.components.push(("acutecomb".into(), pt(width / 2.0 + 0.25, 0.0)));
    out.push(aacute);
    // nested: a composite of a composite, and an empty component that is left out
    let mut nested = glyph("Aacute.ss", width, &[]);
    nested.components.push(("Aacute".into(), pt(10.0, 0.0)));
    nested.components.push(("space".into(), pt(0.0, 0.0)));
    out.push(nested);
    // contours and a component: decomposed into a simple glyph
    let mut mixed = glyph("Abar", width, &[0x100]);
    mixed.contours.push(rect(0.0, 800.0, width, 860.0));
    mixed.components.push(("A".into(), V::ZERO));
    out.push(mixed);
    out.push(glyph("space", 300.0 + w, &[0x20]));
    let mut notdef = glyph(".notdef", 500.0, &[]);
    notdef.contours.push(rect(50.0, 0.0, 450.0, 700.0));
    notdef.contours.push(rect(100.0, 50.0, 400.0, 650.0).reversed());
    out.push(notdef);
    out
}

/// Two axes: weight 100..900 (default 400) and width 75..100 (default 100), four masters including the
/// corner, proportional advances.
fn synthetic_family() -> Family {
    let master = |wght: f64, wdth: f64| Master {
        location: vec![wght, wdth],
        glyphs: synthetic_glyphs(40.0 + (wght - 100.0) / 8.0, (100.0 - wdth) / 25.0),
    };
    Family {
        name: "Test Sans".into(),
        italic: false,
        axes: vec![
            Axis {
                tag: "wght".into(),
                name: "Weight".into(),
                min: 100.0,
                default: 400.0,
                max: 900.0,
                labels: vec![
                    label("Thin", 100.0, false),
                    AxisLabel { linked: Some(700.0), ..label("Regular", 400.0, true) },
                    label("Black", 900.0, false),
                ],
            },
            Axis {
                tag: "wdth".into(),
                name: "Width".into(),
                min: 75.0,
                default: 100.0,
                max: 100.0,
                labels: vec![
                    AxisLabel { range: Some((75.0, 87.5)), ..label("Condensed", 75.0, false) },
                    AxisLabel { linked: Some(75.0), ..label("Normal", 100.0, true) },
                ],
            },
        ],
        masters: vec![
            master(100.0, 100.0),
            master(400.0, 100.0),
            master(900.0, 100.0),
            master(400.0, 75.0),
            master(900.0, 75.0),
        ],
        instances: vec![
            Instance { style_name: "Regular".into(), location: vec![400.0, 100.0] },
            Instance { style_name: "Bold".into(), location: vec![700.0, 100.0] },
            Instance { style_name: "Black Condensed".into(), location: vec![900.0, 75.0] },
        ],
        metrics: metrics(false, 0.0),
        features: vec![
            SingleSub {
                tag: "ss01".into(),
                label: Some("Round A".into()),
                pairs: vec![("A".into(), "A.alt".into()), ("Z".into(), "Z.alt".into())],
            },
            SingleSub { tag: "salt".into(), label: None, pairs: vec![("missing".into(), "A".into())] },
        ],
        kerning: vec![KernPair { left: "A".into(), right: "V".into(), value: -40 }],
        kern_classes: None,
    }
}

/// The Rachis Mono family as `rachis build` makes it (upright or italic).
fn rachis_family(italic: bool) -> Family {
    use rachis_kernel::params::{italic_masters, regular, upright_masters};
    let registry = rachis_glyphs::registry();
    let masters = if italic { italic_masters() } else { upright_masters() };
    let weights = [("Light", 300.0), ("Regular", 400.0), ("Medium", 500.0), ("SemiBold", 600.0), ("Bold", 700.0)];
    let style = |w: &str| match (italic, w) {
        (false, w) => w.to_owned(),
        (true, "Regular") => "Italic".to_owned(),
        (true, w) => format!("{w} Italic"),
    };
    Family {
        name: "Rachis Mono".into(),
        italic,
        axes: vec![Axis {
            tag: "wght".into(),
            name: "Weight".into(),
            min: 300.0,
            default: 400.0,
            max: 700.0,
            labels: weights.iter().map(|&(n, v)| label(n, v, n == "Regular")).collect(),
        }],
        masters: masters
            .iter()
            .map(|p| Master { location: vec![p.wght], glyphs: rachis_kernel::build_all(&registry, p) })
            .collect(),
        instances: weights.iter().map(|&(n, v)| Instance { style_name: style(n), location: vec![v] }).collect(),
        metrics: Metrics {
            x_height: regular().xh as i16,
            cap_height: regular().cap as i16,
            ..metrics(true, if italic { 10.0 } else { 0.0 })
        },
        features: vec![SingleSub {
            tag: "ss01".into(),
            label: Some("Dotted zero".into()),
            pairs: vec![("zero".into(), "zero.dot".into())],
        }],
        kerning: Vec::new(),
        kern_classes: None,
    }
}

/// Every point a pen receives: on-curve points and control points.
#[derive(Default)]
struct Points(Vec<(f32, f32)>);

impl OutlinePen for Points {
    fn move_to(&mut self, x: f32, y: f32) {
        self.0.push((x, y));
    }
    fn line_to(&mut self, x: f32, y: f32) {
        self.0.push((x, y));
    }
    fn quad_to(&mut self, cx: f32, cy: f32, x: f32, y: f32) {
        self.0.extend([(cx, cy), (x, y)]);
    }
    fn curve_to(&mut self, a: f32, b: f32, c: f32, d: f32, x: f32, y: f32) {
        self.0.extend([(a, b), (c, d), (x, y)]);
    }
    fn close(&mut self) {}
}

/// The points of a TrueType glyph with its implied on-curve points made explicit.
fn explicit_points(g: &write_fonts::tables::glyf::SimpleGlyph, dx: f32, dy: f32) -> Vec<(f32, f32)> {
    let mut out = Vec::new();
    for c in &g.contours {
        let pts: Vec<_> = c.iter().collect();
        for (i, p) in pts.iter().enumerate() {
            let next = pts[(i + 1) % pts.len()];
            out.push((f32::from(p.x) + dx, f32::from(p.y) + dy));
            if !p.on_curve && !next.on_curve {
                out.push((
                    (f32::from(p.x) + f32::from(next.x)) / 2.0 + dx,
                    (f32::from(p.y) + f32::from(next.y)) / 2.0 + dy,
                ));
            }
        }
    }
    out
}

/// The largest distance from a point of either set to the nearest point of the other.
fn set_distance(a: &[(f32, f32)], b: &[(f32, f32)]) -> f32 {
    let one_way = |a: &[(f32, f32)], b: &[(f32, f32)]| {
        a.iter()
            .map(|p| b.iter().map(|q| ((p.0 - q.0).powi(2) + (p.1 - q.1).powi(2)).sqrt()).fold(f32::MAX, f32::min))
            .fold(0.0f32, f32::max)
    };
    if a.is_empty() && b.is_empty() {
        return 0.0;
    }
    one_way(a, b).max(one_way(b, a))
}

fn name(font: &FontRef, id: u16) -> Option<String> {
    font.localized_strings(StringId::new(id)).english_or_first().map(|s| s.to_string())
}

fn tags(font: &FontRef) -> Vec<String> {
    font.table_directory.table_records().iter().map(|r| r.tag().to_string()).collect()
}

/// Instancing the variable font at every master's location gives that master's rounded points and advance, for
/// every glyph. Points that IUP leaves to interpolation may be off by the IUP tolerance for each region that
/// applies at the location (one at every master of a one-axis family). Returns the largest distance found.
fn check_masters_reproduced(family: &Family, bytes: &[u8]) -> f32 {
    let font = FontRef::new(bytes).unwrap();
    let src = Source::new(family).unwrap();
    let compiled = compile_masters(&src).unwrap();
    let advances = src.advances().unwrap();
    let outlines = font.outline_glyphs();
    let mut worst = 0.0f32;
    for (m, master) in family.masters.iter().enumerate() {
        let settings: Vec<(&str, f32)> =
            family.axes.iter().zip(&master.location).map(|(a, &v)| (a.tag.as_str(), v as f32)).collect();
        let location = font.axes().location(settings);
        let gm = font.glyph_metrics(Size::unscaled(), &location);
        let normalised: Vec<f64> = family.axes.iter().zip(&master.location).map(|(a, &v)| normalise(a, v)).collect();
        let active = src.model.scalars(&normalised)[1..].iter().filter(|&&s| s != 0.0).count();
        // each active region may be off by the tolerance of the delta optimisation, and rounding adds a half
        let tolerance = variation::IUP_TOLERANCE as f32 * active as f32 + 0.5 + 1e-3;
        for (gid, c) in compiled.iter().enumerate() {
            let id = GlyphId::new(gid as u32);
            assert_eq!(
                gm.advance_width(id),
                Some(advances[gid][m] as f32),
                "advance of {} in master {m}",
                src.names[gid]
            );
            let expected = match c {
                Compiled::Empty => Vec::new(),
                Compiled::Simple(gs) => explicit_points(&gs[m], 0.0, 0.0),
                Compiled::Composite(ms) => ms[m]
                    .iter()
                    .flat_map(|(base, (dx, dy))| {
                        let j = src.names.iter().position(|n| n == base).unwrap();
                        match &compiled[j] {
                            Compiled::Simple(gs) => explicit_points(&gs[m], f32::from(*dx), f32::from(*dy)),
                            _ => Vec::new(),
                        }
                    })
                    .collect(),
            };
            let mut pen = Points::default();
            let g = outlines.get(id).unwrap();
            g.draw(DrawSettings::unhinted(Size::unscaled(), LocationRef::from(&location)), &mut pen).unwrap();
            let d = set_distance(&expected, &pen.0);
            assert!(d <= tolerance, "{} in master {m}: {d}", src.names[gid]);
            worst = worst.max(d);
        }
    }
    println!(
        "{}: {} glyphs x {} masters reproduced, largest point distance {worst}",
        family.name,
        compiled.len(),
        family.masters.len()
    );
    worst
}

// ---------------------------------------------------------------------------------------------------------------
// the synthetic family

#[test]
fn glyph_order_puts_notdef_marks_encoded_unencoded() {
    let f = synthetic_family();
    let src = Source::new(&f).unwrap();
    assert_eq!(src.names, vec![".notdef", "acutecomb", "space", "A", "V", "Aacute", "Abar", "A.alt", "Aacute.ss"]);
}

#[test]
fn synthetic_variable_font_reads_back() {
    let f = synthetic_family();
    let bytes = variable_ttf(&f).unwrap();
    let font = FontRef::new(&bytes).unwrap();
    let t = tags(&font);
    for want in [
        "GDEF", "GPOS", "GSUB", "HVAR", "OS/2", "STAT", "cmap", "fvar", "gasp", "glyf", "gvar", "head", "hhea", "hmtx",
        "loca", "maxp", "name", "post", "prep",
    ] {
        assert!(t.contains(&want.to_string()), "{want} missing from {t:?}");
    }
    assert!(!t.contains(&"avar".to_string()) && !t.contains(&"MVAR".to_string()));
    // fvar: two axes, three instances with PostScript names
    let fvar = font.fvar().unwrap();
    assert_eq!(fvar.axis_count(), 2);
    let instances: Vec<_> = font.named_instances().iter().collect();
    assert_eq!(instances.len(), 3);
    let ps: Vec<Option<String>> =
        instances.iter().map(|i| i.postscript_name_id().and_then(|id| name(&font, id.to_u16()))).collect();
    assert_eq!(
        ps,
        vec![Some("TestSans-Regular".into()), Some("TestSans-Bold".into()), Some("TestSans-BlackCondensed".into())]
    );
    assert_eq!(name(&font, 25).as_deref(), Some("TestSans"));
    // STAT: format 3 off the weight axis, format 2 for a range, format 1 for Regular even though it is linked
    let stat = font.stat().unwrap();
    let formats: Vec<u16> =
        stat.offset_to_axis_values().unwrap().unwrap().axis_values().iter().map(|v| v.unwrap().format()).collect();
    // Thin, Regular, Black, Condensed, Normal, Roman
    assert_eq!(formats, vec![1, 1, 1, 2, 3, 3]);
    assert_eq!(stat.design_axis_count(), 3);
    // proportional: xAvgCharWidth is the mean of the non-zero advances; PANOSE proportion is "any"
    let os2 = font.os2().unwrap();
    assert_eq!(os2.panose_10()[3], 0);
    assert_eq!(font.post().unwrap().is_fixed_pitch(), 0);
    // the HVAR advances at every master, and the outlines
    let worst = check_masters_reproduced(&f, &bytes);
    assert!(worst <= 1.5, "{worst}");
    // GDEF classes, layout features
    let gdef = font.gdef().unwrap();
    let classes = gdef.glyph_class_def().unwrap().unwrap();
    assert_eq!(classes.get(GlyphId16::new(1)), 3); // acutecomb
    assert_eq!(classes.get(GlyphId16::new(3)), 1); // A
    let feature_tags = |list: read_fonts::tables::layout::FeatureList| -> Vec<String> {
        list.feature_records().iter().map(|r| r.feature_tag().to_string()).collect()
    };
    let gsub = font.gsub().unwrap();
    assert_eq!(feature_tags(gsub.feature_list().unwrap()), vec!["ss01"]); // salt had no glyphs: skipped
    let gpos = font.gpos().unwrap();
    assert_eq!(feature_tags(gpos.feature_list().unwrap()), vec!["kern", "mark"]);
    let scripts: Vec<String> =
        gsub.script_list().unwrap().script_records().iter().map(|r| r.script_tag().to_string()).collect();
    assert_eq!(scripts, vec!["DFLT", "grek", "latn"]);
}

use write_fonts::types::GlyphId16;

#[test]
fn synthetic_composites_and_overlaps() {
    let f = synthetic_family();
    let bytes = variable_ttf(&f).unwrap();
    let font = FontRef::new(&bytes).unwrap();
    let glyf = font.glyf().unwrap();
    let loca = font.loca(None).unwrap();
    let get = |gid: u32| loca.get_glyf(read_fonts::types::GlyphId::new(gid), &glyf).unwrap().unwrap();
    use read_fonts::tables::glyf::Glyph as G;
    // A: three overlapping contours, flagged
    match get(3) {
        G::Simple(s) => {
            assert_eq!(s.number_of_contours(), 3);
            assert!(s.has_overlapping_contours());
        }
        _ => panic!("A should be simple"),
    }
    // Aacute.ss: Aacute flattened into A and acutecomb moved by 10; the empty space left out
    match get(8) {
        G::Composite(c) => {
            let comps: Vec<_> = c.components().collect();
            assert_eq!(comps.len(), 2);
            assert_eq!(comps[0].glyph.to_u32(), 3);
            assert_eq!(comps[1].glyph.to_u32(), 1);
            assert!(comps[0].flags.contains(read_fonts::tables::glyf::CompositeGlyphFlags::OVERLAP_COMPOUND));
        }
        _ => panic!("Aacute.ss should be composite"),
    }
    // Abar: contours and a component, decomposed
    match get(6) {
        G::Simple(s) => assert_eq!(s.number_of_contours(), 4),
        _ => panic!("Abar should be simple"),
    }

    // the static font: overlaps removed, composites kept, no variation tables
    let inst = &f.instances[1];
    let s = static_ttf_report(&f, inst).unwrap();
    assert!(s.kept_overlaps.is_empty(), "{:?}", s.kept_overlaps);
    let font = FontRef::new(&s.bytes).unwrap();
    let t = tags(&font);
    for gone in ["fvar", "gvar", "HVAR"] {
        assert!(!t.contains(&gone.to_string()));
    }
    let glyf = font.glyf().unwrap();
    let loca = font.loca(None).unwrap();
    let get = |gid: u32| loca.get_glyf(read_fonts::types::GlyphId::new(gid), &glyf).unwrap().unwrap();
    match get(3) {
        G::Simple(s) => {
            assert_eq!(s.number_of_contours(), 1, "the three bars of A are one contour");
            assert!(!s.has_overlapping_contours());
        }
        _ => panic!(),
    }
    match get(0) {
        G::Simple(s) => assert_eq!(s.number_of_contours(), 2, ".notdef keeps its counter"),
        _ => panic!(),
    }
    assert!(matches!(get(5), G::Composite(_)));
    // the Bold instance at wght 700 sits between masters: its advance is the model's value there
    let gm = font.glyph_metrics(Size::unscaled(), LocationRef::default());
    // the advance is linear in the stem weight, which is linear in wght: 600 + 40 + (700 - 100) / 8
    let expect: f64 = 600.0 + 40.0 + (700.0 - 100.0) / 8.0;
    assert_eq!(gm.advance_width(GlyphId::new(3)), Some(outline::ot_round(expect) as f32));
    // names of a style outside the linked four
    let b = static_ttf(&f, &f.instances[2]).unwrap();
    let font = FontRef::new(&b).unwrap();
    assert_eq!(name(&font, 1).as_deref(), Some("Test Sans Black Condensed"));
    assert_eq!(name(&font, 2).as_deref(), Some("Regular"));
    assert_eq!(name(&font, 16).as_deref(), Some("Test Sans"));
    assert_eq!(name(&font, 17).as_deref(), Some("Black Condensed"));
    assert_eq!(name(&font, 6).as_deref(), Some("TestSans-BlackCondensed"));
}

#[test]
fn incompatible_masters_are_refused_by_name() {
    let mut f = synthetic_family();
    f.masters[2].glyphs[0].contours.pop(); // V loses its contour in one master
    let e = variable_ttf(&f).unwrap_err();
    assert!(matches!(&e, Error::Incompatible { glyph, .. } if glyph == "V"), "{e}");
    let mut f = synthetic_family();
    f.masters[1].location = vec![450.0, 100.0];
    assert!(matches!(variable_ttf(&f), Err(Error::Family(_))));
}

#[test]
fn the_same_family_gives_the_same_bytes() {
    let f = synthetic_family();
    assert_eq!(variable_ttf(&f).unwrap(), variable_ttf(&f).unwrap());
    assert_eq!(static_ttf(&f, &f.instances[2]).unwrap(), static_ttf(&f, &f.instances[2]).unwrap());
    let w = woff2(&variable_ttf(&f).unwrap()).unwrap();
    assert_eq!(&w[..4], b"wOF2");
}

// ---------------------------------------------------------------------------------------------------------------
// Rachis Mono

#[test]
fn rachis_variable_font() {
    let f = rachis_family(false);
    let bytes = variable_ttf(&f).unwrap();
    let font = FontRef::new(&bytes).unwrap();
    let t = tags(&font);
    let want: Vec<String> = [
        "GDEF", "GPOS", "GSUB", "HVAR", "OS/2", "STAT", "cmap", "fvar", "gasp", "glyf", "gvar", "head", "hhea", "hmtx",
        "loca", "maxp", "name", "post", "prep",
    ]
    .iter()
    .map(|s| s.to_string())
    .collect();
    assert_eq!(t, want, "GPOS places the combining marks on the letters' anchors");
    // names
    assert_eq!(name(&font, 1).as_deref(), Some("Rachis Mono"));
    assert_eq!(name(&font, 2).as_deref(), Some("Regular"));
    assert_eq!(name(&font, 3).as_deref(), Some("1.000;NONE;RachisMono-Regular"));
    assert_eq!(name(&font, 4).as_deref(), Some("Rachis Mono Regular"));
    assert_eq!(name(&font, 5).as_deref(), Some("Version 1.000"));
    assert_eq!(name(&font, 6).as_deref(), Some("RachisMono-Regular"));
    assert_eq!(name(&font, 25).as_deref(), Some("RachisMono"));
    assert_eq!(name(&font, 9), None, "no designer");
    // metrics
    let hhea = font.hhea().unwrap();
    let os2 = font.os2().unwrap();
    assert_eq!((hhea.ascender().to_i16(), hhea.descender().to_i16(), hhea.line_gap().to_i16()), (1000, -250, 0));
    assert_eq!((os2.s_typo_ascender(), os2.s_typo_descender(), os2.s_typo_line_gap()), (1000, -250, 0));
    assert_eq!((os2.us_win_ascent(), os2.us_win_descent()), (1000, 250));
    assert_eq!(os2.fs_selection().bits(), 0x00C0);
    assert_eq!(os2.us_weight_class(), 400);
    assert_eq!(os2.x_avg_char_width(), 600);
    assert_eq!(os2.panose_10(), &[2, 11, 5, 9, 0, 0, 0, 0, 0, 0]);
    // Latin 1, Latin 2, Greek, Turkish and Baltic are fully covered
    assert_eq!(os2.ul_code_page_range_1().map(|bits| bits & 0x9B), Some(0x9B));
    assert_eq!(font.post().unwrap().is_fixed_pitch(), 1);
    let head = font.head().unwrap();
    assert_eq!(head.flags().bits(), 0b11);
    assert_eq!(head.created().as_secs(), meta::EPOCH + meta::MAC_EPOCH_OFFSET);
    assert_eq!(head.lowest_rec_ppem(), 6);
    assert_eq!(font.table_data(Tag::new(b"prep")).unwrap().as_bytes(), &PREP);
    // advances: 600 and 0 for marks only; numberOfHMetrics trimmed
    let hmtx = font.hmtx().unwrap();
    let advances: std::collections::BTreeSet<u16> = (0..font.maxp().unwrap().num_glyphs())
        .filter_map(|g| hmtx.advance(read_fonts::types::GlyphId::new(u32::from(g))))
        .collect();
    assert_eq!(advances.into_iter().collect::<Vec<_>>(), vec![0, 600], "the cell, and nothing for marks");
    // cmap: every encoded glyph
    let charmap = font.charmap();
    let encoded: usize = f.masters[0].glyphs.iter().map(|g| g.unicodes.len()).sum();
    assert_eq!(charmap.mappings().count(), encoded);
    assert!(charmap.map('0').is_some());
    // HVAR is the minimal table: one zero delta set
    let hvar = font.hvar().unwrap();
    assert_eq!(hvar.item_variation_store().unwrap().variation_region_list().unwrap().region_count(), 0);
    // instancing at Light, Regular and Bold reproduces each master's rounded points, upright and italic: a
    // point whose delta is left to be inferred lands within the optimisation's half unit of its place, which
    // after rounding is at most one unit
    let worst = check_masters_reproduced(&f, &bytes);
    assert!(worst <= 1.0, "{worst}");
    let italic = rachis_family(true);
    let worst = check_masters_reproduced(&italic, &variable_ttf(&italic).unwrap());
    assert!(worst <= 1.0, "{worst}");
}

#[test]
fn rachis_static_fonts() {
    let f = rachis_family(true);
    let s = static_ttf_report(&f, &f.instances[3]).unwrap(); // SemiBold Italic
    let font = FontRef::new(&s.bytes).unwrap();
    assert_eq!(name(&font, 1).as_deref(), Some("Rachis Mono SemiBold"));
    assert_eq!(name(&font, 2).as_deref(), Some("Italic"));
    assert_eq!(name(&font, 16).as_deref(), Some("Rachis Mono"));
    assert_eq!(name(&font, 17).as_deref(), Some("SemiBold Italic"));
    assert_eq!(name(&font, 6).as_deref(), Some("RachisMono-SemiBoldItalic"));
    let os2 = font.os2().unwrap();
    assert_eq!(os2.us_weight_class(), 600);
    assert_eq!(os2.fs_selection().bits(), 0x0081);
    assert_eq!(os2.panose_10()[2], 7);
    assert_eq!(font.head().unwrap().mac_style().bits(), 2);
    assert_eq!(font.post().unwrap().italic_angle().to_f64(), -10.0);
    let hhea = font.hhea().unwrap();
    assert_eq!((hhea.caret_slope_rise(), hhea.caret_slope_run()), (1000, 176));
    let stat = font.stat().unwrap();
    assert_eq!(stat.axis_value_count(), 2, "one value per axis");
    let b = static_ttf(&f, &f.instances[4]).unwrap(); // Bold Italic
    let font = FontRef::new(&b).unwrap();
    assert_eq!(name(&font, 1).as_deref(), Some("Rachis Mono"));
    assert_eq!(name(&font, 2).as_deref(), Some("Bold Italic"));
    assert_eq!(name(&font, 16), None);
    assert_eq!(font.os2().unwrap().fs_selection().bits(), 0x00A1);
    assert_eq!(font.head().unwrap().mac_style().bits(), 3);
}

/// The union check over every glyph of every static font of the fixed pitch: fewer than one glyph in five
/// hundred keeps its overlaps (those are the ones whose union the raster check rejected).
#[test]
fn nearly_every_static_glyph_loses_its_overlaps() {
    let mut kept = BTreeMap::new();
    let mut glyphs = 0;
    for italic in [false, true] {
        let f = rachis_family(italic);
        for inst in &f.instances {
            let s = static_ttf_report(&f, inst).unwrap();
            glyphs += FontRef::new(&s.bytes).unwrap().maxp().unwrap().num_glyphs() as usize;
            for (g, why) in s.kept_overlaps {
                kept.insert(format!("{} {g}", inst.style_name), why.to_string());
            }
        }
    }
    assert_eq!(glyphs, 10 * rachis_glyphs::registry().len());
    // the sweep goes wrong on a few glyphs in ten thousand; the check keeps their contours as drawn
    assert!(kept.len() * 500 < glyphs, "{kept:#?}");
}
