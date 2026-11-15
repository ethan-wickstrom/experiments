//! `rachis math`: what the mathematics font holds, and how it compares with other mathematics fonts.
//!
//! Without options the command counts the glyphs Rachis Math has beyond the proportional Regular and lists
//! what stretches, with its sizes and its pieces. With `--refs DIR` it compiles the font and reads it back as
//! it reads every font in `DIR` that has a `MATH` table, scaled to Rachis's x-height: the constants beside
//! their median, the display integral, where the braces over and under a group stand, how a wide accent is
//! measured, the prime's form for a script, and the boxes a line and a glyph's clipping are taken from. These are the numbers decision T30
//! quotes.
//!
//! With `--script` it measures how far each script capital of the compiled font stands from the italic capital
//! and the upright capital it could be read as, and from the nearest other script capital, with the distance of
//! `rachis measure`; with `--refs DIR` beside the same distances in every font of `DIR` that has the three
//! alphabets. These are the numbers decision T31 quotes, and a test holds the font to the target.

use std::fmt::Write as _;
use std::path::Path;
use std::process::ExitCode;

use rachis_glyphs::calligraphic;
use rachis_glyphs::mathfont::{MathFont, Stretch};
use rachis_kernel::Registry;
use skrifa::GlyphId;
use skrifa::outline::DrawSettings;
use skrifa::prelude::{FontRef, LocationRef, MetadataProvider, Size};
use skrifa::raw::TableProvider;
use skrifa::raw::tables::math::MathGlyphConstruction;
use tiny_skia::PathBuilder;

use crate::build;
use crate::measure::{Align, Glyphs, TARGET_VIEW, VIEWS, pair_distance};
use crate::proof::{RefFace, SkiaPen};

const USAGE: &str = "usage: rachis math [--refs DIR]\n       rachis math --script [--refs DIR]";

/// Add a line to the report.
macro_rules! say {
    ($out:expr, $($arg:tt)*) => {{
        let _ = writeln!($out, $($arg)*);
    }};
}

/// Run `rachis math [--refs DIR]` or `rachis math --script [--refs DIR]`.
pub fn run(registry: &Registry, args: &[String]) -> ExitCode {
    let (script, rest) = match args {
        [flag, rest @ ..] if flag == "--script" => (true, rest),
        _ => (false, args),
    };
    let refs = match rest {
        [] => None,
        [flag, dir] if flag == "--refs" => Some(Path::new(dir)),
        _ => {
            eprintln!("{USAGE}");
            return ExitCode::FAILURE;
        }
    };
    let mut out = String::new();
    let result = match (script, refs) {
        (true, dir) => scripts(registry, dir, &mut out),
        (false, None) => summary(registry, &mut out),
        (false, Some(dir)) => compare(registry, dir, &mut out),
    };
    // written in one piece, and a reader that stops early (`| head`) is not an error
    let _ = std::io::Write::write_all(&mut std::io::stdout().lock(), out.as_bytes());
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("rachis math: {e}");
            ExitCode::FAILURE
        }
    }
}

/// What a glyph the mathematics font adds is, by the ending of its name.
fn kind(name: &str) -> &'static str {
    let ending = name.rsplit_once('.').map_or("", |(_, e)| e);
    let numbered = |letter: char| ending.strip_prefix(letter).is_some_and(|n| n.parse::<u32>().is_ok());
    if numbered('s') {
        "forms for scripts"
    } else if numbered('v') {
        "taller sizes"
    } else if ending == "display" {
        "display sizes of operators"
    } else if numbered('w') {
        "longer sizes"
    } else if numbered('p') || ending == "run" {
        "pieces of what is assembled sideways"
    } else {
        "letters and figures of the mathematical alphabets"
    }
}

/// The least length an assembly can have: its pieces without the one that is repeated, every joint overlapped
/// as far as the shorter of its two connectors allows.
fn least(s: &Stretch) -> f64 {
    let fixed: Vec<_> = s.parts.iter().filter(|part| !part.extender).collect();
    let length: f64 = fixed.iter().map(|part| part.advance).sum();
    length - fixed.windows(2).map(|pair| pair[0].end.min(pair[1].start)).sum::<f64>()
}

fn character(registry: &Registry, name: &str) -> String {
    let code = registry.get(name).and_then(|spec| spec.unicodes.first().copied()).and_then(char::from_u32);
    match code {
        // a combining mark is shown on a dotted circle
        Some(c) if ('\u{300}'..'\u{370}').contains(&c) || ('\u{20D0}'..'\u{2100}').contains(&c) => format!("◌{c}"),
        Some(c) => c.to_string(),
        None => name.to_string(),
    }
}

fn list(out: &mut String, registry: &Registry, title: &str, unit: &str, all: &[Stretch]) {
    say!(out, "\n{title} ({}):", all.len());
    for s in all {
        let sizes = match (s.variants.first(), s.variants.last()) {
            (Some(first), Some(last)) => {
                format!("{} sizes, {:.0} to {:.0} {unit}", s.variants.len(), first.1, last.1)
            }
            _ => "no sizes".to_string(),
        };
        let pieces = if s.parts.is_empty() {
            "no pieces".to_string()
        } else {
            let lengths: Vec<String> = s
                .parts
                .iter()
                .map(|part| format!("{:.0}{}", part.advance, if part.extender { "*" } else { "" }))
                .collect();
            format!("pieces {} (from {:.0})", lengths.join(" "), least(s))
        };
        say!(out, "  {:<3} {sizes}; {pieces}", character(registry, &s.glyph));
    }
}

/// Count what the mathematics font holds and list what stretches.
fn summary(registry: &Registry, out: &mut String) -> Result<(), String> {
    let (base, math): (Vec<_>, MathFont) = build::math_glyphs(registry)?;
    say!(
        out,
        "Rachis Math: {} glyphs: {} of the proportional Regular ({} of them drawn otherwise) and {} of its own",
        base.len() + math.glyphs.len(),
        base.len(),
        math.replaced.len(),
        math.glyphs.len()
    );
    let mut kinds: Vec<(&str, usize)> = Vec::new();
    for g in &math.glyphs {
        match kinds.iter_mut().find(|k| k.0 == kind(&g.name)) {
            Some(k) => k.1 += 1,
            None => kinds.push((kind(&g.name), 1)),
        }
    }
    for (name, count) in kinds {
        say!(out, "  {count:>5}  {name}");
    }
    say!(
        out,
        "{} italic corrections, {} accent attachments, {} glyphs with forms for scripts, {} dotless forms",
        math.italic_corrections.len(),
        math.top_accents.len(),
        math.scripts.len(),
        math.dotless.len()
    );
    list(out, registry, "grows upwards", "tall", &math.vertical);
    list(out, registry, "grows sideways", "long", &math.horizontal);
    say!(out, "\na piece marked * is repeated; \"from\" is the least length the pieces assemble to");
    Ok(())
}

/// A font with a `MATH` table, and the factor that brings its lengths to Rachis's x-height.
struct Face {
    name: String,
    data: Vec<u8>,
    scale: f64,
}

impl Face {
    fn new(name: String, data: Vec<u8>, x_height: f64) -> Option<Face> {
        let mut face = Face { name, data, scale: 1.0 };
        face.font().math().ok()?;
        let x = face.bounds(face.glyph('x')?)?;
        face.scale = x_height / (x.3 - x.1);
        Some(face)
    }

    fn font(&self) -> FontRef<'_> {
        FontRef::new(&self.data).expect("the font was parsed when it was loaded")
    }

    fn glyph(&self, c: char) -> Option<GlyphId> {
        self.font().charmap().map(c)
    }

    /// The glyph's ink, in the font's units: (x0, y0, x1, y1).
    fn bounds(&self, glyph: GlyphId) -> Option<(f64, f64, f64, f64)> {
        let font = self.font();
        let outline = font.outline_glyphs().get(glyph)?;
        let mut pen = SkiaPen(PathBuilder::new());
        outline.draw(DrawSettings::unhinted(Size::unscaled(), LocationRef::default()), &mut pen).ok()?;
        let b = pen.0.finish()?.compute_tight_bounds()?;
        Some((f64::from(b.left()), f64::from(b.top()), f64::from(b.right()), f64::from(b.bottom())))
    }

    fn advance(&self, glyph: GlyphId) -> f64 {
        let font = self.font();
        font.glyph_metrics(Size::unscaled(), LocationRef::default()).advance_width(glyph).map_or(0.0, f64::from)
    }

    /// The constants of the table in the specification's order, unscaled.
    fn constants(&self) -> Option<Vec<f64>> {
        let font = self.font();
        let math = font.math().ok()?;
        let data = math.math_constants().ok()?.offset_data().as_bytes().to_vec();
        let signed = |at: usize| data.get(at..at + 2).map(|b| f64::from(i16::from_be_bytes([b[0], b[1]])));
        let unsigned = |at: usize| data.get(at..at + 2).map(|b| f64::from(u16::from_be_bytes([b[0], b[1]])));
        // two percentages, two heights, 51 values each followed by the offset of a device table, a percentage
        let mut out = vec![signed(0)?, signed(2)?, unsigned(4)?, unsigned(6)?];
        for k in 0..51 {
            out.push(signed(8 + 4 * k)?);
        }
        out.push(signed(8 + 4 * 51)?);
        Some(out)
    }

    fn constant(&self, name: &str) -> Option<f64> {
        let at = rachis_font::MATH_CONSTANTS.iter().position(|n| *n == name)?;
        self.constants()?.get(at).copied()
    }

    /// The sizes of `c` (glyph and stated length) and how many pieces it is assembled from, upwards or sideways.
    fn construction(&self, c: char, upwards: bool) -> Option<(Vec<(GlyphId, f64)>, usize)> {
        let font = self.font();
        let variants = font.math().ok()?.math_variants().ok()?;
        let glyph = self.glyph(c)?;
        let (coverage, constructions) = if upwards {
            (variants.vert_glyph_coverage()?.ok()?, variants.vert_glyph_constructions())
        } else {
            (variants.horiz_glyph_coverage()?.ok()?, variants.horiz_glyph_constructions())
        };
        let index = coverage.get(glyph)?;
        let construction: MathGlyphConstruction = constructions.get(index as usize).ok()?;
        let sizes = construction
            .math_glyph_variant_records()
            .iter()
            .map(|r| (GlyphId::from(r.variant_glyph()), f64::from(r.advance_measurement().to_u16())))
            .collect();
        let pieces = construction.glyph_assembly().and_then(Result::ok).map_or(0, |a| a.part_records().len());
        Some((sizes, pieces))
    }

    /// The first form `glyph` has for a script: its first alternate, or its substitute, under `ssty`.
    fn script_form(&self, glyph: GlyphId) -> Option<GlyphId> {
        use skrifa::raw::tables::gsub::{AlternateSubst, SingleSubst, SubstitutionSubtables};
        let font = self.font();
        let gsub = font.gsub().ok()?;
        let features = gsub.feature_list().ok()?;
        let lookups = gsub.lookup_list().ok()?;
        for record in features.feature_records().iter().filter(|r| r.feature_tag() == skrifa::Tag::new(b"ssty")) {
            let feature = record.feature(features.offset_data()).ok()?;
            for index in feature.lookup_list_indices() {
                let lookup = lookups.lookups().get(usize::from(index.get())).ok()?;
                match lookup.subtables().ok()? {
                    SubstitutionSubtables::Alternate(tables) => {
                        for table in tables.iter().flatten() {
                            // the formats with 16-bit glyph ids are the ones these fonts use
                            let AlternateSubst::Format1(table) = table else { continue };
                            if let Some(at) = table.coverage().ok().and_then(|c| c.get(glyph)) {
                                let set = table.alternate_sets().get(at as usize).ok()?;
                                return set.alternate_glyph_ids().first().map(|g| GlyphId::from(g.get()));
                            }
                        }
                    }
                    SubstitutionSubtables::Single(tables) => {
                        for table in tables.iter().flatten() {
                            match table {
                                SingleSubst::Format1(t) => {
                                    if t.coverage().ok().and_then(|c| c.get(glyph)).is_some() {
                                        let to = glyph.to_u32() as i32 + i32::from(t.delta_glyph_id());
                                        return Some(GlyphId::new(to as u32 & 0xFFFF));
                                    }
                                }
                                SingleSubst::Format2(t) => {
                                    if let Some(at) = t.coverage().ok().and_then(|c| c.get(glyph)) {
                                        return t
                                            .substitute_glyph_ids()
                                            .get(at as usize)
                                            .map(|g| GlyphId::from(g.get()));
                                    }
                                }
                                _ => {}
                            }
                        }
                    }
                    _ => {}
                }
            }
        }
        None
    }

    fn italic_correction(&self, glyph: GlyphId) -> Option<f64> {
        let font = self.font();
        let info = font.math().ok()?.math_glyph_info().ok()?.math_italics_correction_info()?.ok()?;
        let index = info.coverage().ok()?.get(glyph)?;
        info.italics_correction().get(index as usize).map(|r| f64::from(r.value().to_i16()))
    }
}

/// The median of `values`; of an even number, the mean of the middle two.
fn median(mut values: Vec<f64>) -> Option<f64> {
    values.sort_by(f64::total_cmp);
    (!values.is_empty()).then(|| (values[(values.len() - 1) / 2] + values[values.len() / 2]) / 2.0)
}

/// The constants that are not lengths: they are compared as they stand.
const PERCENTAGES: [&str; 3] =
    ["ScriptPercentScaleDown", "ScriptScriptPercentScaleDown", "RadicalDegreeBottomRaisePercent"];

fn compare(registry: &Registry, dir: &Path, out: &mut String) -> Result<(), String> {
    let family = build::math_family(registry)?;
    let bytes = rachis_font::static_ttf(&family, &family.instances[0]).map_err(|e| e.to_string())?;
    let x_height = f64::from(family.metrics.x_height);
    let own = Face::new("Rachis Math".into(), bytes, x_height).ok_or("the mathematics font has no x")?;
    let mut files: Vec<_> = std::fs::read_dir(dir)
        .map_err(|e| format!("{}: {e}", dir.display()))?
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| p.extension().is_some_and(|x| x.eq_ignore_ascii_case("ttf") || x.eq_ignore_ascii_case("otf")))
        .collect();
    files.sort();
    let refs: Vec<Face> = files
        .iter()
        .filter_map(|path| {
            let name = path.file_stem()?.to_string_lossy().into_owned();
            Face::new(name, std::fs::read(path).ok()?, x_height)
        })
        .collect();
    if refs.is_empty() {
        return Err(format!("no font with a MATH table in {}", dir.display()));
    }
    let names: Vec<&str> = refs.iter().map(|f| f.name.as_str()).collect();
    say!(out, "reference fonts, each scaled to an x-height of {x_height:.0}: {}", names.join(", "));

    say!(out, "\nconstants ({:>6} {:>6}   each reference; * where Rachis is not the median)", "Rachis", "median");
    for name in rachis_font::MATH_CONSTANTS {
        let scaled = |f: &Face| {
            let k = if PERCENTAGES.contains(&name) { 1.0 } else { f.scale };
            f.constant(name).map(|v| v * k)
        };
        let ours = scaled(&own).ok_or("a constant is missing")?;
        let theirs: Vec<f64> = refs.iter().filter_map(scaled).collect();
        let middle = median(theirs.clone()).unwrap_or(f64::NAN);
        let each: Vec<String> = theirs.iter().map(|v| format!("{v:>5.0}")).collect();
        let mark = if (ours - middle).abs() > 1.0 { "*" } else { " " };
        say!(out, "  {name:<40} {ours:>6.0} {middle:>6.0} {mark} {}", each.join(" "));
    }

    say!(out, "\nthe integral of a display: height, times the text's, breadth to height, white left and right, lean");
    for f in std::iter::once(&own).chain(&refs) {
        let row = (|| {
            let text = f.bounds(f.glyph('∫')?)?;
            let floor = f.constant("DisplayOperatorMinHeight")?;
            let (sizes, _) = f.construction('∫', true)?;
            // a display takes the first size that is at least as tall as the font asks of a display operator
            let glyph = sizes.iter().find(|s| s.1 >= floor).or(sizes.last())?.0;
            let (x0, y0, x1, y1) = f.bounds(glyph)?;
            let lean = f.italic_correction(glyph).unwrap_or(0.0);
            Some(format!(
                "{:>5.0} {:>5.2} {:>5.2} {:>5.0} {:>5.0} {:>5.0}",
                (y1 - y0) * f.scale,
                (y1 - y0) / (text.3 - text.1),
                (x1 - x0) / (y1 - y0),
                x0 * f.scale,
                (f.advance(glyph) - x1) * f.scale,
                lean * f.scale
            ))
        })();
        say!(out, "  {:<28} {}", f.name, row.unwrap_or_else(|| "-".into()));
    }

    say!(out, "\nwhat lies over or under a group: lowest ink of ⏞ above the accent base height, highest ink of ⏟");
    say!(out, "below the baseline, least and most over the sign and its sizes; pieces of ⏞, of → and of ◌⃗");
    for f in std::iter::once(&own).chain(&refs) {
        let base = f.constant("AccentBaseHeight").unwrap_or(0.0);
        let range = |c: char, clear: &dyn Fn((f64, f64, f64, f64)) -> f64| {
            let glyph = f.glyph(c)?;
            let sizes = f.construction(c, false).map_or(Vec::new(), |s| s.0);
            let all: Vec<f64> = std::iter::once(glyph)
                .chain(sizes.iter().map(|s| s.0))
                .filter_map(|g| f.bounds(g))
                .map(|b| clear(b) * f.scale)
                .collect();
            let (low, high) = (all.iter().copied().reduce(f64::min)?, all.iter().copied().reduce(f64::max)?);
            Some(format!("{low:>4.0} to {high:>4.0}"))
        };
        let pieces = |c: char| f.construction(c, false).map_or(0, |s| s.1);
        say!(
            out,
            "  {:<28} over {}   under {}   pieces {} {} {}",
            f.name,
            range('⏞', &|b| b.1 - base).unwrap_or_else(|| format!("{:>12}", "-")),
            range('⏟', &|b| -b.3).unwrap_or_else(|| format!("{:>12}", "-")),
            pieces('⏞'),
            pieces('→'),
            pieces('\u{20D7}')
        );
    }

    say!(out, "\nthe first wider size of the circumflex: its advance, and where its ink starts and ends");
    for f in std::iter::once(&own).chain(&refs) {
        let row = (|| {
            let own_glyph = f.glyph('\u{302}')?;
            let (sizes, _) = f.construction('\u{302}', false)?;
            let glyph = sizes.iter().map(|s| s.0).find(|g| *g != own_glyph)?;
            let b = f.bounds(glyph)?;
            Some(format!("{:>5.0}   {:>5.0} to {:>5.0}", f.advance(glyph) * f.scale, b.0 * f.scale, b.2 * f.scale))
        })();
        say!(out, "  {:<28} {}", f.name, row.unwrap_or_else(|| "no wider size".into()));
    }

    say!(out, "\nthe prime and its first form for a script: how many times as tall the form is, and how far its");
    say!(out, "foot stands below the prime's");
    for f in std::iter::once(&own).chain(&refs) {
        let row = (|| {
            let prime = f.glyph('′')?;
            let (own_box, form_box) = (f.bounds(prime)?, f.bounds(f.script_form(prime)?)?);
            Some(format!(
                "{:>5.2} {:>5.0}",
                (form_box.3 - form_box.1) / (own_box.3 - own_box.1),
                (own_box.1 - form_box.1) * f.scale
            ))
        })();
        say!(out, "  {:<28} {}", f.name, row.unwrap_or_else(|| "no form".into()));
    }

    say!(out, "\nthe line (typo ascender and descender) and where a glyph is clipped (win ascent and descent), in");
    say!(out, "thousandths of an em, and the top and the bottom of the font's tallest and deepest glyphs");
    for f in std::iter::once(&own).chain(&refs) {
        let font = f.font();
        let row = (|| {
            let (os2, head) = (font.os2().ok()?, font.head().ok()?);
            let em = 1000.0 / f64::from(head.units_per_em());
            Some(format!(
                "{:>5.0} {:>5.0}   {:>5.0} {:>5.0}   {:>5.0} {:>5.0}",
                f64::from(os2.s_typo_ascender()) * em,
                -f64::from(os2.s_typo_descender()) * em,
                f64::from(os2.us_win_ascent()) * em,
                f64::from(os2.us_win_descent()) * em,
                f64::from(head.y_max()) * em,
                -f64::from(head.y_min()) * em
            ))
        })();
        say!(out, "  {:<28} {}", f.name, row.unwrap_or_else(|| "-".into()));
    }
    Ok(())
}

/// A script capital of a font beside the capitals it could be read as.
struct Near {
    letter: char,
    /// Its distance from the italic capital of the same letter.
    italic: f64,
    /// From the upright capital.
    upright: f64,
    /// The script capital it is nearest to, and how near.
    other: char,
    nearest: f64,
}

/// The script capitals of one font.
struct Script {
    name: String,
    rows: Vec<Near>,
}

impl Script {
    /// `None` when the font lacks a script capital, or the italic or upright capital it is measured against.
    fn of(mut face: RefFace) -> Option<Script> {
        let letters: Vec<(char, char, char)> = ('A'..='Z')
            .zip(calligraphic::CAPITALS)
            .zip(0x1D434..)
            .filter_map(|((upright, (script, _)), italic)| Some((upright, char::from_u32(italic)?, script)))
            .collect();
        let glyphs = Glyphs::load(&mut face, Align::Centre, letters.iter().flat_map(|&(a, b, c)| [a, b, c]));
        let image = |c: char| glyphs.image(&c.to_string(), VIEWS[TARGET_VIEW]);
        let mut images = Vec::new();
        for &(upright, italic, script) in &letters {
            images.push((image(upright)?, image(italic)?, image(script)?));
        }
        let rows = (0..letters.len())
            .map(|i| {
                let own = &images[i].2;
                let (other, nearest) = (0..letters.len())
                    .filter(|&j| j != i)
                    .map(|j| (letters[j].0, pair_distance(own, &images[j].2, Align::Centre)))
                    .min_by(|a, b| a.1.total_cmp(&b.1))
                    .expect("there are 26 letters");
                Near {
                    letter: letters[i].0,
                    italic: pair_distance(own, &images[i].1, Align::Centre),
                    upright: pair_distance(own, &images[i].0, Align::Centre),
                    other,
                    nearest,
                }
            })
            .collect();
        Some(Script { name: face.family, rows })
    }

    /// The median of a distance over the letters, and the letter that has the least of it.
    fn column(&self, pick: impl Fn(&Near) -> f64) -> (f64, char, f64) {
        let least = self.rows.iter().min_by(|a, b| pick(a).total_cmp(&pick(b))).expect("26 rows");
        (median(self.rows.iter().map(&pick).collect()).unwrap_or(f64::NAN), least.letter, pick(least))
    }
}

/// `rachis math --script`: how far the script capitals stand from the capitals they could be read as.
fn scripts(registry: &Registry, dir: Option<&Path>, out: &mut String) -> Result<(), String> {
    let family = build::math_family(registry)?;
    let bytes = rachis_font::static_ttf(&family, &family.instances[0]).map_err(|e| e.to_string())?;
    let x_height = f64::from(family.metrics.x_height);
    let mut sides = vec![("Rachis Math".to_string(), Face::new("Rachis Math".into(), bytes.clone(), x_height))];
    let own = RefFace::from_bytes(bytes, "Rachis Math".into())
        .ok()
        .and_then(Script::of)
        .ok_or("the mathematics font lacks a script capital")?;
    let mut refs = Vec::new();
    if let Some(dir) = dir {
        let mut files: Vec<_> = std::fs::read_dir(dir)
            .map_err(|e| format!("{}: {e}", dir.display()))?
            .filter_map(|e| e.ok().map(|e| e.path()))
            .filter(|p| p.extension().is_some_and(|x| x.eq_ignore_ascii_case("ttf") || x.eq_ignore_ascii_case("otf")))
            .collect();
        files.sort();
        for path in files {
            let name = path.file_stem().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
            match RefFace::load(&path, name.clone()).ok().and_then(Script::of) {
                Some(s) => {
                    refs.push(s);
                    sides.push((name.clone(), std::fs::read(&path).ok().and_then(|d| Face::new(name, d, x_height))));
                }
                None => say!(out, "{name}: no script capitals beside italic and upright ones"),
            }
        }
    }
    let view = VIEWS[TARGET_VIEW];
    say!(
        out,
        "the script capitals at {} px per em under a blur of {} px: the distance of each from the italic capital, \
         from the upright capital and from the nearest other script capital",
        view.px,
        view.sigma
    );
    let picks: [fn(&Near) -> f64; 3] = [|r| r.italic, |r| r.upright, |r| r.nearest];
    say!(out, "\n{:<28} {:<16} {:<16} {:<16}", "", "from the italic", "from the upright", "from the nearest");
    say!(out, "{:<28} {:<16} {:<16} {:<16}", "font", "median  least", "median  least", "median  least");
    for s in std::iter::once(&own).chain(&refs) {
        let cells = picks.map(|pick| {
            let (middle, letter, least) = s.column(pick);
            format!("{middle:.3}   {least:.3} {letter}")
        });
        say!(out, "{:<28} {:<16} {:<16} {:<16}", s.name, cells[0], cells[1], cells[2]);
    }
    say!(out, "\n{:<8} {:<26} {:<26} {:<26}", "", "from the italic", "from the upright", "from the nearest");
    let others = if refs.is_empty() { String::new() } else { format!("median of {}", refs.len()) };
    let head = format!("{:<12} {:<13}", "Rachis", others);
    say!(out, "{:<8} {head} {head} {head}", "letter");
    for (i, row) in own.rows.iter().enumerate() {
        let theirs = picks.map(|pick| {
            median(refs.iter().map(|s| pick(&s.rows[i])).collect()).map_or(String::new(), |v| format!("{v:.3}"))
        });
        say!(
            out,
            "{:<8} {:<12} {:<13} {:<12} {:<13} {:<12} {:<13}",
            row.letter,
            format!("{:.3}", row.italic),
            theirs[0],
            format!("{:.3}", row.upright),
            theirs[1],
            format!("{:.3} {}", row.nearest, row.other),
            theirs[2]
        );
    }
    say!(
        out,
        "\nthe white at the sides of a script capital (less than none where its ink stands past its advance) and \
         its italic correction: medians of the 26, at an x-height of {x_height:.0}"
    );
    say!(out, "{:<28} {:>6} {:>6} {:>11}", "font", "left", "right", "correction");
    for (name, face) in &sides {
        let Some(face) = face else { continue };
        let of = |pick: &dyn Fn(GlyphId, (f64, f64, f64, f64)) -> f64| {
            let values = calligraphic::CAPITALS
                .iter()
                .filter_map(|(c, _)| face.glyph(*c).and_then(|g| Some(pick(g, face.bounds(g)?) * face.scale)))
                .collect();
            median(values).unwrap_or(f64::NAN)
        };
        let (left, right) = (of(&|_, b| b.0), of(&|g, b| face.advance(g) - b.2));
        let correction = of(&|g, _| face.italic_correction(g).unwrap_or(0.0));
        say!(out, "{name:<28} {left:>6.0} {right:>6.0} {correction:>11.0}");
    }
    if !refs.is_empty() {
        say!(out, "\neach letter from its italic capital, font by font");
        let all: Vec<&Script> = std::iter::once(&own).chain(&refs).collect();
        let short = |name: &str| name.chars().filter(|c| c.is_alphanumeric()).take(9).collect::<String>();
        let heads: Vec<String> = all.iter().map(|s| format!("{:<9}", short(&s.name))).collect();
        say!(out, "{:<8} {}", "letter", heads.join(" "));
        for i in 0..own.rows.len() {
            let cells: Vec<String> = all.iter().map(|s| format!("{:<9.3}", s.rows[i].italic)).collect();
            say!(out, "{:<8} {}", own.rows[i].letter, cells.join(" "));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A reader has to tell a script capital from the italic and the upright capital of the same letter, which
    /// mean other things in the same formula, and from every other script capital: none comes nearer than the
    /// target `rachis measure` sets for a pair of notation.
    #[test]
    fn no_script_capital_of_the_mathematics_font_is_near_a_capital_it_could_be_read_as() {
        let registry = rachis_glyphs::registry();
        let family = build::math_family(&registry).expect("the mathematics font");
        let bytes = rachis_font::static_ttf(&family, &family.instances[0]).expect("it compiles");
        let script =
            RefFace::from_bytes(bytes, "Rachis Math".into()).ok().and_then(Script::of).expect("its script capitals");
        let target = crate::measure::MATH.expect("a target");
        assert_eq!(script.rows.len(), 26);
        for Near { letter, italic, upright, other, nearest } in &script.rows {
            assert!(*italic >= target, "script {letter} is {italic:.3} from the italic {letter}");
            assert!(*upright >= target, "script {letter} is {upright:.3} from the upright {letter}");
            assert!(*nearest >= target, "script {letter} is {nearest:.3} from script {other}");
        }
    }
}
