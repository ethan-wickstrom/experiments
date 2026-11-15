//! `rachis math`: what the mathematics font holds, and how it compares with other mathematics fonts.
//!
//! Without options the command counts the glyphs Rachis Math has beyond the proportional Regular and lists
//! what stretches, with its sizes and its pieces. With `--refs DIR` it compiles the font and reads it back as
//! it reads every font in `DIR` that has a `MATH` table, scaled to Rachis's x-height: the constants beside
//! their median, the display integral, where the braces over and under a group stand, how a wide accent is
//! measured, and the boxes a line and a glyph's clipping are taken from. These are the numbers decision T30
//! quotes.

use std::fmt::Write as _;
use std::path::Path;
use std::process::ExitCode;

use rachis_glyphs::mathfont::{MathFont, Stretch};
use rachis_kernel::Registry;
use skrifa::GlyphId;
use skrifa::outline::DrawSettings;
use skrifa::prelude::{FontRef, LocationRef, MetadataProvider, Size};
use skrifa::raw::TableProvider;
use skrifa::raw::tables::math::MathGlyphConstruction;
use tiny_skia::PathBuilder;

use crate::build;
use crate::proof::SkiaPen;

const USAGE: &str = "usage: rachis math [--refs DIR]";

/// Add a line to the report.
macro_rules! say {
    ($out:expr, $($arg:tt)*) => {{
        let _ = writeln!($out, $($arg)*);
    }};
}

/// Run `rachis math [--refs DIR]`.
pub fn run(registry: &Registry, args: &[String]) -> ExitCode {
    let refs = match args {
        [] => None,
        [flag, dir] if flag == "--refs" => Some(dir),
        _ => {
            eprintln!("{USAGE}");
            return ExitCode::FAILURE;
        }
    };
    let mut out = String::new();
    let result = match refs {
        None => summary(registry, &mut out),
        Some(dir) => compare(registry, Path::new(dir), &mut out),
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
