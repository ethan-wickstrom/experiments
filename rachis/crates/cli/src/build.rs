//! `rachis build`: draw the masters of every face, compile the variable fonts and the static fonts, hint the
//! statics, compress the variable fonts for the web, and write a manifest of SHA-256 sums.

use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode, Stdio};
use std::time::Instant;

use rachis_font::{Axis, AxisLabel, Family, Instance, KernClasses, Master, Metrics, SingleSub};
use rachis_glyphs::kern;
use rachis_kernel::params::{Face, OPSZ_SMALL, OPSZ_TEXT, Params, faces};
use rachis_kernel::{Glyph, Registry, name_of};

/// The named weights: (style name, `wght`).
const WEIGHTS: [(&str, f64); 5] =
    [("Light", 300.0), ("Regular", 400.0), ("Medium", 500.0), ("SemiBold", 600.0), ("Bold", 700.0)];

/// Superior and inferior forms: each character with its superscript and its subscript character. A feature
/// lists the pairs whose glyphs the face has.
const SUPERIORS: [(&str, &str); 2] =
    [("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾"), ("abcdefghijklmnoprstuvwxyz", "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ")];
const INFERIORS: [(&str, &str); 2] =
    [("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎"), ("aehijklmnoprstuvx", "ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ")];

/// ttfautohint's options: no version string in the name table, hint from 7 to 48 ppem, natural stem widths for
/// grayscale and DirectWrite ClearType, quantized for GDI ClearType.
const AUTOHINT_ARGS: [&str; 4] =
    ["--no-info", "--hinting-range-min=7", "--hinting-range-max=48", "--stem-width-mode=nqn"];

struct Options {
    out: PathBuf,
    statics: bool,
    hint: bool,
}

fn parse(args: &[String]) -> Result<Options, String> {
    let mut o = Options { out: PathBuf::from("fonts"), statics: true, hint: true };
    let mut it = args.iter();
    while let Some(a) = it.next() {
        match a.as_str() {
            "--out" => o.out = PathBuf::from(it.next().ok_or("--out needs a directory")?),
            "--no-statics" => o.statics = false,
            "--no-hint" => o.hint = false,
            other => return Err(format!("unknown option {other:?}")),
        }
    }
    Ok(o)
}

/// The style name of a weight in the upright or the italic family.
fn style_name(weight: &str, italic: bool) -> String {
    match (italic, weight) {
        (false, w) => w.to_owned(),
        (true, "Regular") => "Italic".to_owned(),
        (true, w) => format!("{w} Italic"),
    }
}

fn single(tag: &str, label: Option<&str>, pairs: Vec<(String, String)>) -> SingleSub {
    SingleSub { tag: tag.into(), label: label.map(Into::into), pairs }
}

/// The pairs of `tables` whose two glyphs are both in the face.
fn char_pairs(registry: &Registry, face: &Face, tables: &[(&str, &str)]) -> Vec<(String, String)> {
    let has = |c: char| registry.for_char(c).is_some_and(|s| face.has(s.module));
    tables
        .iter()
        .flat_map(|(from, to)| from.chars().zip(to.chars()))
        .filter(|&(a, b)| has(a) && has(b))
        .map(|(a, b)| (name_of(a), name_of(b)))
        .collect()
}

fn label(name: &str, value: f64, elidable: bool, range: Option<(f64, f64)>) -> AxisLabel {
    AxisLabel { name: name.into(), value, elidable, linked: None, range }
}

/// Every glyph of the face as the master `p` draws it, in registration order.
fn draw(registry: &Registry, face: &Face, p: &Params) -> Vec<Glyph> {
    registry.specs.iter().filter(|s| face.has(s.module)).map(|s| registry.build(s, p)).collect()
}

/// The kerning classes of a proportional face with their values in its default master. Every weight and size of
/// the face, and its static family at the small size, carry these values (ledger G2).
fn kerning(registry: &Registry, face: &Face) -> Option<KernClasses> {
    let p = face.default_master();
    if p.mono {
        return None;
    }
    let classes = kern::classes(registry, p);
    let values = kern::values(registry, p, &classes);
    Some(KernClasses {
        first: classes.first,
        second: classes.second,
        values: values.iter().map(|row| row.iter().map(|&k| k as i16).collect()).collect(),
    })
}

/// One face as the compiler takes it. `small` builds the static family of the small optical size instead: its
/// masters alone, under a family name of its own, for software that cannot use an optical-size axis.
fn family(registry: &Registry, face: &Face, small: bool) -> Family {
    let default = face.default_master();
    let sized = !small && face.masters.iter().any(|p| p.opsz != default.opsz);
    let masters: Vec<&Params> = face.masters.iter().filter(|p| sized || (p.opsz == OPSZ_SMALL) == small).collect();
    let weights = WEIGHTS.iter().map(|&(name, value)| label(name, value, name == "Regular", None)).collect();
    let weight =
        Axis { tag: "wght".into(), name: "Weight".into(), min: 300.0, default: 400.0, max: 700.0, labels: weights };
    let middle = (OPSZ_SMALL + OPSZ_TEXT) / 2.0;
    let size = Axis {
        tag: "opsz".into(),
        name: "Optical Size".into(),
        min: OPSZ_SMALL,
        default: OPSZ_TEXT,
        max: OPSZ_TEXT,
        labels: vec![
            label("Small", OPSZ_SMALL, false, Some((OPSZ_SMALL, middle))),
            label("Text", OPSZ_TEXT, true, Some((middle, OPSZ_TEXT))),
        ],
    };
    let at = |wght: f64, opsz: f64| if sized { vec![opsz, wght] } else { vec![wght] };
    let drawn: Vec<Master> =
        masters.iter().map(|p| Master { location: at(p.wght, p.opsz), glyphs: draw(registry, face, p) }).collect();
    let reference = masters.iter().find(|p| p.wght == 400.0).copied().unwrap_or(default);
    let zero = name_of('0');
    Family {
        name: if small { format!("{} Small", face.family) } else { face.family.into() },
        italic: face.italic,
        axes: if sized { vec![size, weight] } else { vec![weight] },
        masters: drawn,
        instances: WEIGHTS
            .iter()
            .map(|&(name, wght)| Instance { style_name: style_name(name, face.italic), location: at(wght, OPSZ_TEXT) })
            .collect(),
        metrics: Metrics {
            upm: 1000,
            ascender: reference.line_top.round() as i16,
            descender: reference.line_bot.round() as i16,
            x_height: reference.xh.round() as i16,
            cap_height: reference.cap.round() as i16,
            italic_angle: reference.slant,
            underline_position: -100,
            underline_thickness: 60,
            strikeout_position: 300,
            strikeout_size: 60,
            fixed_pitch: reference.mono,
        },
        features: vec![
            single("zero", None, vec![(zero.clone(), "zero.slash".into())]),
            single("ss01", Some("Dotted zero"), vec![(zero.clone(), "zero.dot".into())]),
            single("ss02", Some("Plain zero"), vec![(zero, "zero.plain".into())]),
            single("sups", None, char_pairs(registry, face, &SUPERIORS)),
            single("subs", None, char_pairs(registry, face, &INFERIORS)),
            single("sinf", None, char_pairs(registry, face, &INFERIORS)),
        ],
        kerning: Vec::new(),
        kern_classes: kerning(registry, face),
    }
}

/// Run `rachis build [--out DIR] [--no-statics] [--no-hint]`.
pub fn run(registry: &Registry, args: &[String]) -> ExitCode {
    let options = match parse(args) {
        Ok(o) => o,
        Err(e) => {
            eprintln!("rachis build: {e}\nusage: rachis build [--out DIR] [--no-statics] [--no-hint]");
            return ExitCode::FAILURE;
        }
    };
    match build(registry, &options) {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("rachis build: {e}");
            ExitCode::FAILURE
        }
    }
}

fn build(registry: &Registry, o: &Options) -> Result<(), String> {
    let start = Instant::now();
    let hinter = if o.hint && o.statics { autohint_available() } else { false };
    if o.hint && o.statics && !hinter {
        println!("ttfautohint is not installed: the static fonts are left unhinted");
    }
    for sub in ["variable", "ttf", "webfonts"] {
        let d = o.out.join(sub);
        if d.exists() {
            std::fs::remove_dir_all(&d).map_err(|e| format!("{}: {e}", d.display()))?;
        }
    }
    let mut files: Vec<(String, Vec<u8>)> = Vec::new();
    let mut kept: Vec<String> = Vec::new();
    for face in faces() {
        let fam = family(registry, &face, false);
        let axes: Vec<&str> = fam.axes.iter().map(|a| a.tag.as_str()).collect();
        let vf = rachis_font::variable_ttf(&fam).map_err(|e| e.to_string())?;
        files.push((format!("variable/{}[{}].ttf", face.file, axes.join(",")), vf));
        if !o.statics {
            continue;
        }
        // the static families: the face at its size for text, and its small size where it has one
        let stem = face.file.trim_end_matches("-Italic");
        let mut statics = vec![(stem.to_string(), fam)];
        if face.masters.iter().any(|p| p.opsz == OPSZ_SMALL) {
            statics.push((format!("{stem}Small"), family(registry, &face, true)));
        }
        for (stem, fam) in &statics {
            for inst in &fam.instances {
                let s = rachis_font::static_ttf_report(fam, inst).map_err(|e| e.to_string())?;
                let file = format!("ttf/{stem}-{}.ttf", inst.style_name.replace(' ', ""));
                for (glyph, why) in &s.kept_overlaps {
                    kept.push(format!("{file}: {glyph}: {why}"));
                }
                files.push((file, s.bytes));
            }
        }
    }
    if hinter {
        hint_all(&mut files)?;
    }
    let mut webfonts = Vec::new();
    for (path, bytes) in files.iter().filter(|(path, _)| path.starts_with("variable/")) {
        let name =
            Path::new(path).file_stem().and_then(|s| s.to_str()).ok_or_else(|| format!("{path}: no file name"))?;
        webfonts.push((format!("webfonts/{name}.woff2"), rachis_font::woff2(bytes).map_err(|e| e.to_string())?));
    }
    files.extend(webfonts);
    files.sort_by(|a, b| a.0.cmp(&b.0));

    let mut manifest = String::new();
    for (path, bytes) in &files {
        let full = o.out.join(path);
        if let Some(dir) = full.parent() {
            std::fs::create_dir_all(dir).map_err(|e| format!("{}: {e}", dir.display()))?;
        }
        std::fs::write(&full, bytes).map_err(|e| format!("{}: {e}", full.display()))?;
        manifest.push_str(&format!("{}  {path}\n", rachis_font::sha256_hex(bytes)));
        println!("{:>9}  {}", bytes.len(), full.display());
    }
    let sums = o.out.join("SHA256SUMS");
    std::fs::write(&sums, manifest).map_err(|e| format!("{}: {e}", sums.display()))?;
    println!("{:>9}  {}", "", sums.display());
    if kept.is_empty() {
        println!("overlaps removed from every glyph of every static font");
    } else {
        println!("{} glyphs keep their overlapping contours:", kept.len());
        for k in &kept {
            println!("  {k}");
        }
    }
    println!(
        "{} files in {:.2} s{}",
        files.len(),
        start.elapsed().as_secs_f64(),
        if hinter { " (statics hinted)" } else { "" }
    );
    Ok(())
}

/// Hint every static font, each in its own ttfautohint process, all at once.
fn hint_all(files: &mut [(String, Vec<u8>)]) -> Result<(), String> {
    std::thread::scope(|scope| {
        let jobs: Vec<_> = files
            .iter_mut()
            .filter(|(path, _)| path.starts_with("ttf/"))
            .map(|(path, bytes)| {
                scope.spawn(move || -> Result<(), String> {
                    *bytes = autohint(bytes).map_err(|e| format!("{path}: {e}"))?;
                    Ok(())
                })
            })
            .collect();
        jobs.into_iter().try_for_each(|j| j.join().map_err(|_| "a hinting thread panicked".to_string())?)
    })
}

fn autohint_available() -> bool {
    Command::new("ttfautohint")
        .arg("--version")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .is_ok_and(|s| s.success())
}

/// Hint a static font with ttfautohint, at the build's fixed epoch so the output is reproducible, and set
/// `head.flags` bit 3 (integer ppem), which a hinted font should have.
fn autohint(ttf: &[u8]) -> Result<Vec<u8>, String> {
    use std::io::Write as _;
    let mut child = Command::new("ttfautohint")
        .args(AUTOHINT_ARGS)
        .env("SOURCE_DATE_EPOCH", rachis_font::meta::EPOCH.to_string())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("ttfautohint: {e}"))?;
    let mut stdin = child.stdin.take().ok_or("ttfautohint: no stdin")?;
    let input = ttf.to_vec();
    let writer = std::thread::spawn(move || stdin.write_all(&input));
    let out = child.wait_with_output().map_err(|e| format!("ttfautohint: {e}"))?;
    writer
        .join()
        .map_err(|_| "ttfautohint: the writer panicked".to_string())?
        .map_err(|e| format!("ttfautohint: {e}"))?;
    if !out.status.success() {
        return Err(format!("ttfautohint failed: {}", String::from_utf8_lossy(&out.stderr)));
    }
    set_head_flag_bit(out.stdout, 3)
}

/// Set one bit of `head.flags` and fix the `head` table's checksum and the font's checksum adjustment.
fn set_head_flag_bit(mut font: Vec<u8>, bit: u16) -> Result<Vec<u8>, String> {
    let u16_at = |f: &[u8], i: usize| f.get(i..i + 2).map(|b| u16::from_be_bytes([b[0], b[1]]));
    let u32_at = |f: &[u8], i: usize| f.get(i..i + 4).map(|b| u32::from_be_bytes([b[0], b[1], b[2], b[3]]));
    let bad = || "the hinted font is malformed".to_string();
    let tables = usize::from(u16_at(&font, 4).ok_or_else(bad)?);
    let record = (0..tables).map(|i| 12 + 16 * i).find(|&r| font.get(r..r + 4) == Some(b"head")).ok_or_else(bad)?;
    let offset = u32_at(&font, record + 8).ok_or_else(bad)? as usize;
    let length = u32_at(&font, record + 12).ok_or_else(bad)? as usize;
    let flags = u16_at(&font, offset + 16).ok_or_else(bad)? | (1 << bit);
    font[offset + 16..offset + 18].copy_from_slice(&flags.to_be_bytes());
    font[offset + 8..offset + 12].copy_from_slice(&[0; 4]);
    let checksum = |data: &[u8]| {
        data.chunks(4).fold(0u32, |acc, c| {
            let mut w = [0u8; 4];
            w[..c.len()].copy_from_slice(c);
            acc.wrapping_add(u32::from_be_bytes(w))
        })
    };
    let head = font.get(offset..offset + length).ok_or_else(bad)?;
    let head_sum = checksum(head);
    font[record + 4..record + 8].copy_from_slice(&head_sum.to_be_bytes());
    let adjustment = 0xB1B0_AFBAu32.wrapping_sub(checksum(&font));
    font[offset + 8..offset + 12].copy_from_slice(&adjustment.to_be_bytes());
    Ok(font)
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeSet;

    use skrifa::instance::Size;
    use skrifa::raw::TableProvider;
    use skrifa::{FontRef, MetadataProvider};

    use super::*;

    fn face(file: &str) -> Face {
        faces().into_iter().find(|f| f.file == file).expect("the face exists")
    }

    /// The kerning between two glyphs by name: 0 when either is in no class.
    fn value(k: &KernClasses, left: &str, right: &str) -> i16 {
        let class = |classes: &[Vec<String>], name: &str| classes.iter().position(|c| c.iter().any(|n| n == name));
        match (class(&k.first, left), class(&k.second, right)) {
            (Some(i), Some(j)) => k.values[i][j],
            _ => 0,
        }
    }

    #[test]
    fn the_proportional_face_compiles_with_two_axes_and_kerning() {
        let registry = rachis_glyphs::registry();
        let fam = family(&registry, &face("Rachis"), false);
        assert_eq!(fam.masters.len(), 6);
        let bytes = rachis_font::variable_ttf(&fam).expect("the face compiles");
        let font = FontRef::new(&bytes).expect("a font");
        let axes: Vec<String> = font.axes().iter().map(|a| a.tag().to_string()).collect();
        assert_eq!(axes, ["opsz", "wght"]);
        // n is wider at the small size, and wider in the Bold
        let n = font.charmap().map('n').expect("n");
        let advance = |axis: &str, at: f32| {
            let location = font.axes().location([(axis, at)]);
            font.glyph_metrics(Size::unscaled(), &location).advance_width(n).expect("an advance")
        };
        assert!(advance("opsz", 8.0) > advance("opsz", 16.0));
        assert!(advance("wght", 700.0) > advance("wght", 400.0));
        let features: Vec<String> = font
            .gpos()
            .and_then(|gpos| gpos.feature_list())
            .map(|list| list.feature_records().iter().map(|r| r.feature_tag().to_string()).collect())
            .expect("GPOS");
        assert!(features.iter().any(|t| t == "kern") && features.iter().any(|t| t == "mark"), "{features:?}");
        assert_eq!(font.post().expect("post").is_fixed_pitch(), 0);
    }

    #[test]
    fn kerning_closes_open_pairs_and_keeps_accents_clear() {
        let registry = rachis_glyphs::registry();
        let k = kerning(&registry, &face("Rachis")).expect("the proportional face is kerned");
        assert!(value(&k, "T", "o") < -50 && value(&k, "A", "V") < -50 && value(&k, "r", "period") < -50);
        // two stems at their sidebearings need nothing, and the arm of r stays clear of n
        assert_eq!((value(&k, "n", "n"), value(&k, "n", "o"), value(&k, "r", "n")), (0, 0, 0));
        // an accent that overhangs its letter is not pulled under the bar of T
        assert!(value(&k, "T", "dotlessi") < -50);
        assert!(value(&k, "T", "icircumflex") >= 0 && value(&k, "T", "idieresis") >= 0);
        // inks that never stand side by side are left alone
        assert_eq!((value(&k, "colon", "hyphen"), value(&k, "hyphen", "colon")), (0, 0));
        // a digraph kerns on its right as its right letter does
        assert_eq!(value(&k, "IJ", "period"), value(&k, "J", "period"));
        // nothing is moved into a bracket
        assert_eq!((value(&k, "H", "bracketright"), value(&k, "bracketleft", "H")), (0, 0));
        for classes in [&k.first, &k.second] {
            let mut seen = BTreeSet::new();
            for name in classes.iter().flatten() {
                assert!(seen.insert(name), "{name} is in two classes");
            }
        }
    }

    #[test]
    fn the_small_static_family_is_the_face_at_its_small_size() {
        let registry = rachis_glyphs::registry();
        let small = family(&registry, &face("Rachis"), true);
        assert_eq!(small.name, "Rachis Small");
        assert_eq!(small.axes.iter().map(|a| a.tag.as_str()).collect::<Vec<_>>(), ["wght"]);
        assert!(small.masters.len() == 3 && small.metrics.x_height > 540);
        assert_eq!(small.kern_classes, family(&registry, &face("Rachis"), false).kern_classes);
    }

    #[test]
    fn the_fixed_pitch_face_has_one_axis_and_no_kerning() {
        let registry = rachis_glyphs::registry();
        let fam = family(&registry, &face("RachisMono"), false);
        assert_eq!(fam.axes.iter().map(|a| a.tag.as_str()).collect::<Vec<_>>(), ["wght"]);
        assert!(fam.kern_classes.is_none() && fam.metrics.fixed_pitch);
    }
}
