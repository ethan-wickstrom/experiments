//! `rachis proof`: pictures of glyphs for the eye to judge.
//!
//! An outline sheet draws each glyph large, with its contours, points and handles, the font's horizontal lines
//! and, on request, the knots and pens of its strokes. A text sheet sets lines of text at several sizes the way a
//! terminal does, optionally beside the same lines in reference fonts.

use std::collections::{BTreeSet, HashMap};
use std::path::PathBuf;
use std::process::ExitCode;

use rachis_kernel::params::{master, masters, regular};
use rachis_kernel::pen::skeleton;
use rachis_kernel::{Glyph, Knot, Params, Registry, Seg, V};
use skrifa::instance::Location;
use skrifa::outline::{DrawSettings, OutlinePen};
use skrifa::prelude::{FontRef, LocationRef, MetadataProvider, Size};
use tiny_skia::{Color, FillRule, Paint, Path, PathBuilder, Pixmap, PixmapPaint, Rect, Stroke, Transform};

const USAGE: &str = "usage:
  rachis proof --outline ITEM... -o OUT.png [--master NAME | --masters] [--em 420] [--columns 4] [--no-points] [--skeleton]
  rachis proof --text LINE... -o OUT.png [--sizes 96 48 24 16 13] [--scale 3] [--dark] [--master NAME | --masters] [--compare]";

/// Every option the command knows; a list of values (`--outline`, `--text`, `--sizes`) ends at the next of these.
const OPTIONS: [&str; 15] = [
    "--outline",
    "--text",
    "-o",
    "--out",
    "--master",
    "--masters",
    "--em",
    "--columns",
    "--no-points",
    "--skeleton",
    "--sizes",
    "--scale",
    "--dark",
    "--compare",
    "--help",
];

/// Reference fonts for `--compare`, by the start of their file names, in the order they are shown.
const REFERENCES: [&str; 6] =
    ["JetBrainsMono[", "IBMPlexMono-Regular", "SourceCodePro[", "FiraCode[", "Iosevka-Regular", "CommitMono"];

/// How deep components may nest before the rest is ignored (a guard against a component cycle).
const MAX_COMPONENT_DEPTH: usize = 8;

/// Draw a proof as the arguments ask and write it as a PNG; print its path and size.
pub fn run(registry: &Registry, args: &[String]) -> ExitCode {
    let opts = match Opts::parse(args) {
        Ok(opts) => opts,
        Err(e) => {
            eprintln!("rachis proof: {e}\n{USAGE}");
            return ExitCode::FAILURE;
        }
    };
    let chosen = if opts.all_masters {
        masters()
    } else if let Some(p) = master(&opts.master) {
        vec![p]
    } else {
        let names: Vec<&str> = masters().iter().map(|p| p.name).collect();
        eprintln!("rachis proof: no master named {:?}; there are: {}", opts.master, names.join(", "));
        return ExitCode::FAILURE;
    };
    let mut labels = Labeller::new(registry);
    let sheet = match &opts.mode {
        Mode::Outline(items) => outline_proof(registry, &chosen, items, &opts, &mut labels),
        Mode::Text(lines) => Ok(text_proof(registry, &chosen, lines, &opts, &mut labels)),
    };
    let sheet = match sheet.and_then(|s| s.ok_or_else(|| "the image would be too large".to_string())) {
        Ok(sheet) => sheet,
        Err(e) => {
            eprintln!("rachis proof: {e}");
            return ExitCode::FAILURE;
        }
    };
    if let Err(e) = save(&sheet, &opts.out) {
        eprintln!("rachis proof: cannot write {}: {e}", opts.out.display());
        return ExitCode::FAILURE;
    }
    println!("{} {}x{}", opts.out.display(), sheet.width(), sheet.height());
    ExitCode::SUCCESS
}

fn save(sheet: &Pixmap, out: &std::path::Path) -> Result<(), String> {
    if let Some(dir) = out.parent().filter(|d| !d.as_os_str().is_empty()) {
        std::fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    }
    sheet.save_png(out).map_err(|e| e.to_string())
}

// ---------------------------------------------------------------------------------------------------------------
// Arguments

enum Mode {
    Outline(Vec<String>),
    Text(Vec<String>),
}

struct Opts {
    mode: Mode,
    out: PathBuf,
    master: String,
    all_masters: bool,
    em: f64,
    columns: usize,
    points: bool,
    skeleton: bool,
    sizes: Vec<u32>,
    scale: u32,
    dark: bool,
    compare: bool,
}

impl Opts {
    fn parse(args: &[String]) -> Result<Opts, String> {
        let (mut outline, mut text, mut out) = (None, None, None);
        let mut opts = Opts {
            mode: Mode::Text(Vec::new()),
            out: PathBuf::new(),
            master: "Regular".into(),
            all_masters: false,
            em: 420.0,
            columns: 4,
            points: true,
            skeleton: false,
            sizes: vec![96, 48, 24, 16, 13],
            scale: 3,
            dark: false,
            compare: false,
        };
        let mut i = 0;
        while i < args.len() {
            let flag = args[i].as_str();
            i += 1;
            match flag {
                "--outline" => outline = Some(values(args, &mut i)),
                "--text" => text = Some(values(args, &mut i)),
                "-o" | "--out" => out = Some(PathBuf::from(value(args, &mut i, flag)?)),
                "--master" => opts.master = value(args, &mut i, flag)?.to_string(),
                "--masters" => opts.all_masters = true,
                "--em" => opts.em = number(value(args, &mut i, flag)?, flag, 10.0, 4000.0)?,
                "--columns" => opts.columns = number(value(args, &mut i, flag)?, flag, 1, 1000)?,
                "--no-points" => opts.points = false,
                "--skeleton" => opts.skeleton = true,
                "--sizes" => {
                    let sizes = values(args, &mut i);
                    opts.sizes = sizes.iter().map(|s| number(s, flag, 4, 1000)).collect::<Result<_, _>>()?;
                }
                "--scale" => opts.scale = number(value(args, &mut i, flag)?, flag, 1, 16)?,
                "--dark" => opts.dark = true,
                "--compare" => opts.compare = true,
                "--help" => return Err("help".into()),
                _ => return Err(format!("unknown argument {flag:?}")),
            }
        }
        opts.mode = match (outline, text) {
            (Some(items), None) if !items.is_empty() => Mode::Outline(items),
            (None, Some(lines)) if !lines.is_empty() => Mode::Text(lines),
            (Some(_), Some(_)) => return Err("give either --outline or --text, not both".into()),
            _ => return Err("give --outline ITEM... or --text LINE...".into()),
        };
        if opts.sizes.is_empty() {
            return Err("--sizes needs at least one size".into());
        }
        opts.out = out.ok_or("give the output file with -o")?;
        Ok(opts)
    }
}

/// The arguments from `i` up to the next option.
fn values(args: &[String], i: &mut usize) -> Vec<String> {
    let start = *i;
    while *i < args.len() && !OPTIONS.contains(&args[*i].as_str()) {
        *i += 1;
    }
    args[start..*i].to_vec()
}

/// The one argument after option `flag`.
fn value<'a>(args: &'a [String], i: &mut usize, flag: &str) -> Result<&'a str, String> {
    let v = args.get(*i).ok_or_else(|| format!("{flag} needs a value"))?;
    *i += 1;
    Ok(v)
}

fn number<T: std::str::FromStr + PartialOrd + std::fmt::Display>(
    s: &str,
    flag: &str,
    lo: T,
    hi: T,
) -> Result<T, String> {
    match s.parse::<T>() {
        Ok(n) if n >= lo && n <= hi => Ok(n),
        _ => Err(format!("{flag} takes a number from {lo} to {hi}, not {s:?}")),
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Glyphs

/// The glyphs of one master, each built on first use.
struct Built<'r> {
    registry: &'r Registry,
    params: Params,
    cache: HashMap<String, Glyph>,
}

/// A glyph with its components resolved: every contour and skeleton moved into place.
#[derive(Default)]
struct Resolved {
    contours: Vec<Vec<Seg>>,
    skeletons: Vec<(Vec<Knot>, bool)>,
}

impl<'r> Built<'r> {
    fn new(registry: &'r Registry, params: Params) -> Built<'r> {
        Built { registry, params, cache: HashMap::new() }
    }

    fn glyph(&mut self, name: &str) -> Option<&Glyph> {
        let registry = self.registry;
        let spec = registry.get(name)?;
        let params = &self.params;
        Some(self.cache.entry(name.to_string()).or_insert_with(|| registry.build(spec, params)))
    }

    fn resolved(&mut self, name: &str) -> Resolved {
        let mut out = Resolved::default();
        self.collect(name, V::ZERO, 0, &mut out);
        out
    }

    fn collect(&mut self, name: &str, offset: V, depth: usize, out: &mut Resolved) {
        if depth > MAX_COMPONENT_DEPTH {
            return;
        }
        let Some(g) = self.glyph(name) else {
            return;
        };
        let moved = |s: &Seg| s.mapped(&|z| z + offset);
        out.contours.extend(g.contours.iter().map(|c| c.segs.iter().map(moved).collect()));
        out.skeletons.extend(g.skeletons.iter().map(|(knots, closed)| {
            let knots = knots.iter().map(|k| Knot { z: k.z + offset, ..*k });
            (knots.collect(), *closed)
        }));
        for (base, d) in g.components.clone() {
            self.collect(&base, offset + d, depth + 1, out);
        }
    }
}

/// The glyph names an `--outline` item stands for: itself if it names a glyph, else the glyphs of its characters.
fn glyph_names(registry: &Registry, items: &[String]) -> Vec<String> {
    let mut names: Vec<String> = Vec::new();
    let mut missing = BTreeSet::new();
    for item in items {
        let found: Vec<String> = if registry.get(item).is_some() {
            vec![item.clone()]
        } else {
            item.chars()
                .filter_map(|c| match registry.for_char(c) {
                    Some(spec) => Some(spec.name.clone()),
                    None => {
                        missing.insert(c);
                        None
                    }
                })
                .collect()
        };
        for name in found {
            if !names.contains(&name) {
                names.push(name);
            }
        }
    }
    note_missing(&missing, "");
    names
}

fn note_missing(missing: &BTreeSet<char>, place: &str) {
    if !missing.is_empty() {
        let cps: Vec<String> = missing.iter().map(|&c| format!("U+{:04X}", c as u32)).collect();
        eprintln!("note: no glyph for {}{place}", cps.join(" "));
    }
}

/// A path in font units (y up) through `contours`.
fn contours_path<'a>(contours: impl IntoIterator<Item = &'a Vec<Seg>>) -> Option<Path> {
    let mut pb = PathBuilder::new();
    for segs in contours {
        push_contour(&mut pb, segs, &|z| z);
    }
    pb.finish()
}

/// Append one closed contour, mapping each point through `f`.
fn push_contour(pb: &mut PathBuilder, segs: &[Seg], f: &impl Fn(V) -> V) {
    push_open(pb, segs, f);
    if !segs.is_empty() {
        pb.close();
    }
}

/// Append a chain of segments without closing it, mapping each point through `f`.
fn push_open(pb: &mut PathBuilder, segs: &[Seg], f: &impl Fn(V) -> V) {
    let Some(first) = segs.first() else {
        return;
    };
    let p = f(first.start());
    pb.move_to(p.x as f32, p.y as f32);
    for seg in segs {
        match *seg {
            Seg::Line(_, b) => {
                let b = f(b);
                pb.line_to(b.x as f32, b.y as f32);
            }
            Seg::Cubic(_, b, c, d) => {
                let (b, c, d) = (f(b), f(c), f(d));
                pb.cubic_to(b.x as f32, b.y as f32, c.x as f32, c.y as f32, d.x as f32, d.y as f32);
            }
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Drawing

fn rgba(r: u8, g: u8, b: u8, a: u8) -> Color {
    Color::from_rgba8(r, g, b, a)
}

fn paint(colour: Color) -> Paint<'static> {
    let mut p = Paint::default();
    p.set_color(colour);
    p.anti_alias = true;
    p
}

fn blank(width: u32, height: u32, bg: Color) -> Option<Pixmap> {
    let mut pix = Pixmap::new(width.max(1), height.max(1))?;
    pix.fill(bg);
    Some(pix)
}

fn fill(pix: &mut Pixmap, path: &Path, colour: Color, transform: Transform) {
    pix.fill_path(path, &paint(colour), FillRule::Winding, transform, None);
}

fn stroke(pix: &mut Pixmap, path: &Path, colour: Color, width: f32) {
    let s = Stroke { width, ..Stroke::default() };
    pix.stroke_path(path, &paint(colour), &s, Transform::identity(), None);
}

fn line(pix: &mut Pixmap, a: V, b: V, colour: Color, width: f32) {
    let mut pb = PathBuilder::new();
    pb.move_to(a.x as f32, a.y as f32);
    pb.line_to(b.x as f32, b.y as f32);
    if let Some(path) = pb.finish() {
        stroke(pix, &path, colour, width);
    }
}

fn square(pix: &mut Pixmap, c: V, half: f32, colour: Color) {
    let (x, y) = (c.x as f32, c.y as f32);
    if let Some(r) = Rect::from_ltrb(x - half, y - half, x + half, y + half) {
        pix.fill_rect(r, &paint(colour), Transform::identity(), None);
    }
}

fn circle(pix: &mut Pixmap, c: V, r: f32, colour: Color, filled: bool) {
    if let Some(path) = PathBuilder::from_circle(c.x as f32, c.y as f32, r) {
        if filled {
            fill(pix, &path, colour, Transform::identity());
        } else {
            stroke(pix, &path, colour, 1.2);
        }
    }
}

/// `images` one under another on a sheet as wide as the widest.
fn stack(images: &[Pixmap], bg: Color) -> Option<Pixmap> {
    let width = images.iter().map(Pixmap::width).max()?;
    let mut sheet = blank(width, images.iter().map(Pixmap::height).sum(), bg)?;
    let mut y = 0;
    for im in images {
        sheet.draw_pixmap(0, y, im.as_ref(), &PixmapPaint::default(), Transform::identity(), None);
        y += im.height() as i32;
    }
    Some(sheet)
}

/// `image` enlarged `k` times by pixel replication.
fn enlarge(image: &Pixmap, k: u32) -> Option<Pixmap> {
    let (w, h) = (image.width(), image.height());
    let mut big = Pixmap::new(w * k, h * k)?;
    let src = image.pixels();
    let dst = big.pixels_mut();
    for y in 0..(h * k) {
        for x in 0..(w * k) {
            dst[(y * w * k + x) as usize] = src[((y / k) * w + x / k) as usize];
        }
    }
    Some(big)
}

/// Labels written with Rachis's own glyphs: the Regular master at 14 px, in grey.
struct Labeller<'r> {
    face: OurFace<'r>,
}

impl<'r> Labeller<'r> {
    const SIZE: u32 = 14;

    fn new(registry: &'r Registry) -> Labeller<'r> {
        Labeller { face: OurFace::new(registry, regular()) }
    }

    fn cell(&self) -> f64 {
        (self.face.advance() * f64::from(Self::SIZE) / self.face.upm()).round()
    }

    /// The width of `text` in pixels; characters the typeface lacks take no room.
    fn width(&self, text: &str) -> u32 {
        let drawn = text.chars().filter(|&c| self.face.has(c)).count();
        (drawn as f64 * self.cell()) as u32
    }

    /// Write `text` with its baseline at `y`, starting at `x`.
    fn draw(&mut self, pix: &mut Pixmap, text: &str, x: f64, y: f64) {
        let k = f64::from(Self::SIZE) / self.face.upm();
        let cell = self.cell();
        let mut x = x.round();
        let drawn: Vec<char> = text.chars().filter(|&c| self.face.has(c)).collect();
        for c in drawn {
            if let Some(path) = self.face.outline(c) {
                fill(pix, &path, rgba(125, 125, 125, 255), glyph_transform(k, x, y.round()));
            }
            x += cell;
        }
    }
}

/// Font units (y up) to pixels: scaled by `k`, origin at (x, baseline).
fn glyph_transform(k: f64, x: f64, baseline: f64) -> Transform {
    Transform::from_row(k as f32, 0.0, 0.0, -k as f32, x as f32, baseline as f32)
}

// ---------------------------------------------------------------------------------------------------------------
// Outline mode

/// Outline mode: one cell per glyph for each master asked for, stacked and, for several masters, labelled.
fn outline_proof(
    registry: &Registry,
    chosen: &[Params],
    items: &[String],
    opts: &Opts,
    labels: &mut Labeller,
) -> Result<Option<Pixmap>, String> {
    let names = glyph_names(registry, items);
    if names.is_empty() {
        return Err("none of the items names a glyph".into());
    }
    let white = rgba(255, 255, 255, 255);
    let mut sheets = Vec::new();
    for p in chosen {
        let mut built = Built::new(registry, p.clone());
        let Some(sheet) = outline_sheet(&mut built, &names, opts, labels) else {
            return Ok(None);
        };
        if chosen.len() > 1 {
            sheets.push(titled(sheet, p.name, labels, white));
        } else {
            sheets.push(Some(sheet));
        }
    }
    Ok(sheets.into_iter().collect::<Option<Vec<_>>>().and_then(|s| stack(&s, white)))
}

/// `sheet` under a strip with `title` written in it.
fn titled(sheet: Pixmap, title: &str, labels: &mut Labeller, bg: Color) -> Option<Pixmap> {
    let strip = 28;
    let mut out = blank(sheet.width(), sheet.height() + strip, bg)?;
    labels.draw(&mut out, title, 8.0, 20.0);
    line(
        &mut out,
        V { x: 0.0, y: f64::from(strip) - 0.5 },
        V { x: f64::from(sheet.width()), y: f64::from(strip) - 0.5 },
        rgba(200, 200, 200, 255),
        1.0,
    );
    out.draw_pixmap(0, strip as i32, sheet.as_ref(), &PixmapPaint::default(), Transform::identity(), None);
    Some(out)
}

/// The cells of one master: `--columns` per row, `--em` pixels per 1000 units.
fn outline_sheet(built: &mut Built, names: &[String], opts: &Opts, labels: &mut Labeller) -> Option<Pixmap> {
    let s = opts.em / 1000.0;
    let (top, bottom) = (built.params.asc + 110.0, built.params.desc - 90.0);
    let advances: Vec<f64> = names.iter().map(|n| built.glyph(n).map_or(0.0, |g| g.advance)).collect();
    let widest = advances.iter().copied().fold(0.0, f64::max);
    let cell_w = ((widest + 160.0) * s).ceil() as u32;
    let cell_h = ((top - bottom) * s).ceil() as u32;
    let columns = opts.columns.min(names.len());
    let rows = names.len().div_ceil(columns);
    let mut pix = blank(cell_w * columns as u32, cell_h * rows as u32, rgba(255, 255, 255, 255))?;
    for (i, (name, &advance)) in names.iter().zip(&advances).enumerate() {
        let cell = Cell {
            x0: f64::from(cell_w) * (i % columns) as f64 + 80.0 * s,
            y0: f64::from(cell_h) * (i / columns) as f64,
            top,
            s,
        };
        let glyph = built.resolved(name);
        draw_guides(&mut pix, &cell, &built.params, advance, bottom);
        labels.draw(&mut pix, name, cell.x0 - 72.0 * s, cell.y0 + 18.0);
        draw_outline(&mut pix, &cell, &glyph.contours, opts.points);
        if opts.skeleton {
            draw_skeletons(&mut pix, &cell, &glyph.skeletons);
        }
    }
    Some(pix)
}

/// Where a glyph's origin sits in the sheet and how font units map to pixels there.
struct Cell {
    x0: f64,
    y0: f64,
    top: f64,
    s: f64,
}

impl Cell {
    fn px(&self, z: V) -> V {
        V { x: self.x0 + z.x * self.s, y: self.y0 + (self.top - z.y) * self.s }
    }

    fn at(&self, x: f64, y: f64) -> V {
        self.px(V { x, y })
    }
}

/// The baseline, x-height, cap height, ascender and descender, and the cell's left and right edges.
fn draw_guides(pix: &mut Pixmap, cell: &Cell, p: &Params, advance: f64, bottom: f64) {
    let grey = rgba(150, 150, 150, 160);
    for (y, colour) in [
        (0.0, rgba(210, 50, 50, 170)),
        (p.xh, rgba(60, 120, 210, 160)),
        (p.cap, rgba(50, 160, 80, 160)),
        (p.asc, grey),
        (p.desc, grey),
    ] {
        line(pix, cell.at(-70.0, y), cell.at(advance + 70.0, y), colour, 1.0);
    }
    for x in [0.0, advance] {
        line(pix, cell.at(x, bottom + 30.0), cell.at(x, cell.top - 30.0), grey, 1.0);
    }
}

/// Each contour filled on its own in translucent black, so overlaps show darker, then stroked; then its points.
fn draw_outline(pix: &mut Pixmap, cell: &Cell, contours: &[Vec<Seg>], points: bool) {
    for segs in contours {
        let mut pb = PathBuilder::new();
        push_contour(&mut pb, segs, &|z| cell.px(z));
        if let Some(path) = pb.finish() {
            fill(pix, &path, rgba(0, 0, 0, 46), Transform::identity());
            stroke(pix, &path, rgba(0, 0, 0, 255), 2.0);
        }
    }
    if !points {
        return;
    }
    let orange = rgba(215, 95, 25, 255);
    for seg in contours.iter().flatten() {
        if let Seg::Cubic(a, b, c, d) = *seg {
            for (on, off) in [(a, b), (d, c)] {
                line(pix, cell.px(on), cell.px(off), rgba(215, 95, 25, 190), 1.0);
                circle(pix, cell.px(off), 3.0, orange, false);
            }
        }
    }
    for seg in contours.iter().flatten() {
        square(pix, cell.px(seg.end()), 3.0, rgba(20, 80, 200, 255));
    }
}

/// Each stroke's centre line, a dot at every knot and the pen across it: at its own angle, else perpendicular to
/// the centre line there (to the chord to the next knot when the centre line cannot be drawn).
fn draw_skeletons(pix: &mut Pixmap, cell: &Cell, skeletons: &[(Vec<Knot>, bool)]) {
    let magenta = rgba(200, 30, 170, 230);
    for (knots, closed) in skeletons {
        let travel = match skeleton(knots, *closed) {
            Ok(sk) => {
                let (segs, arrive, depart) = (sk.segs(), sk.arrive, sk.depart);
                let mut pb = PathBuilder::new();
                push_open(&mut pb, &segs, &|z| cell.px(z));
                if let Some(path) = pb.finish() {
                    stroke(pix, &path, rgba(200, 30, 170, 110), 1.0);
                }
                arrive.iter().zip(&depart).map(|(&a, &d)| a + d).collect()
            }
            Err(_) => chords(knots, *closed),
        };
        for (k, t) in knots.iter().zip(travel) {
            let across = match k.pen {
                Some(deg) => Some(V::unit(deg)),
                None if t.abs() > 1e-9 => Some((t / t.abs()).left()),
                None => None,
            };
            if let Some(u) = across {
                let half = u * (k.w / 2.0);
                line(pix, cell.px(k.z - half), cell.px(k.z + half), magenta, 1.5);
            }
            circle(pix, cell.px(k.z), 3.0, magenta, true);
        }
    }
}

/// The direction from each knot to the next (from the one before, at the end of an open stroke).
fn chords(knots: &[Knot], closed: bool) -> Vec<V> {
    let n = knots.len();
    (0..n)
        .map(|i| match (i + 1 < n || closed, i > 0) {
            (true, _) => knots[(i + 1) % n].z - knots[i].z,
            (false, true) => knots[i].z - knots[i - 1].z,
            (false, false) => V::ZERO,
        })
        .collect()
}

// ---------------------------------------------------------------------------------------------------------------
// Text mode

/// A typeface a text sheet can set: one of our masters, or a reference font.
trait Face {
    fn name(&self) -> &str;
    fn upm(&self) -> f64;
    /// The advance of every character, in font units.
    fn advance(&self) -> f64;
    fn has(&self, c: char) -> bool;
    /// The outline of `c` in font units, y up; `None` when it is blank or missing.
    fn outline(&mut self, c: char) -> Option<Path>;
}

/// One master of Rachis as a face.
struct OurFace<'r> {
    built: Built<'r>,
    paths: HashMap<char, Option<Path>>,
}

impl<'r> OurFace<'r> {
    fn new(registry: &'r Registry, params: Params) -> OurFace<'r> {
        OurFace { built: Built::new(registry, params), paths: HashMap::new() }
    }
}

impl Face for OurFace<'_> {
    fn name(&self) -> &str {
        self.built.params.name
    }

    fn upm(&self) -> f64 {
        self.built.params.upm
    }

    fn advance(&self) -> f64 {
        self.built.params.width
    }

    fn has(&self, c: char) -> bool {
        self.built.registry.for_char(c).is_some()
    }

    fn outline(&mut self, c: char) -> Option<Path> {
        if let Some(path) = self.paths.get(&c) {
            return path.clone();
        }
        let path = self
            .built
            .registry
            .for_char(c)
            .map(|spec| spec.name.clone())
            .and_then(|name| contours_path(&self.built.resolved(&name).contours));
        self.paths.insert(c, path.clone());
        path
    }
}

/// A reference font from `$RACHIS_REFS`, at weight 400 when it is variable.
struct RefFace {
    family: String,
    data: Vec<u8>,
    location: Location,
    upm: f64,
    advance: f64,
}

impl RefFace {
    fn load(path: &std::path::Path, family: String) -> Result<RefFace, String> {
        let data = std::fs::read(path).map_err(|e| e.to_string())?;
        let font = FontRef::new(&data).map_err(|e| e.to_string())?;
        let location = font.axes().location([("wght", 400.0)]);
        let upm = f64::from(font.metrics(Size::unscaled(), &location).units_per_em);
        let advance = ['0', 'M', ' ']
            .iter()
            .find_map(|&c| {
                let gid = font.charmap().map(c)?;
                font.glyph_metrics(Size::unscaled(), &location).advance_width(gid)
            })
            .ok_or("no advance for '0', 'M' or space")?;
        Ok(RefFace { family, data, location, upm, advance: f64::from(advance) })
    }
}

impl Face for RefFace {
    fn name(&self) -> &str {
        &self.family
    }

    fn upm(&self) -> f64 {
        self.upm
    }

    fn advance(&self) -> f64 {
        self.advance
    }

    fn has(&self, c: char) -> bool {
        FontRef::new(&self.data).is_ok_and(|f| f.charmap().map(c).is_some())
    }

    fn outline(&mut self, c: char) -> Option<Path> {
        let font = FontRef::new(&self.data).ok()?;
        let glyph = font.outline_glyphs().get(font.charmap().map(c)?)?;
        let mut pen = SkiaPen(PathBuilder::new());
        let settings = DrawSettings::unhinted(Size::unscaled(), LocationRef::from(&self.location));
        glyph.draw(settings, &mut pen).ok()?;
        pen.0.finish()
    }
}

/// Collects a reference glyph's outline into a tiny-skia path.
struct SkiaPen(PathBuilder);

impl OutlinePen for SkiaPen {
    fn move_to(&mut self, x: f32, y: f32) {
        self.0.move_to(x, y);
    }

    fn line_to(&mut self, x: f32, y: f32) {
        self.0.line_to(x, y);
    }

    fn quad_to(&mut self, cx0: f32, cy0: f32, x: f32, y: f32) {
        self.0.quad_to(cx0, cy0, x, y);
    }

    fn curve_to(&mut self, cx0: f32, cy0: f32, cx1: f32, cy1: f32, x: f32, y: f32) {
        self.0.cubic_to(cx0, cy0, cx1, cy1, x, y);
    }

    fn close(&mut self) {
        self.0.close();
    }
}

/// The reference fonts found in `$RACHIS_REFS`, in `REFERENCES` order.
fn reference_faces() -> Vec<RefFace> {
    let Some(dir) = std::env::var_os("RACHIS_REFS") else {
        eprintln!("note: --compare needs RACHIS_REFS, a directory of reference fonts");
        return Vec::new();
    };
    let mut files: Vec<PathBuf> = std::fs::read_dir(&dir)
        .map(|entries| entries.filter_map(|e| e.ok().map(|e| e.path())).collect())
        .unwrap_or_default();
    files.sort();
    let file_name = |p: &PathBuf| p.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
    let mut faces = Vec::new();
    for prefix in REFERENCES {
        let Some(path) = files.iter().find(|p| {
            let name = file_name(p);
            name.starts_with(prefix) && (name.ends_with(".ttf") || name.ends_with(".otf"))
        }) else {
            continue;
        };
        let name = file_name(path);
        let family = name.split(['[', '-', '.']).next().unwrap_or(&name).to_string();
        match RefFace::load(path, family) {
            Ok(face) => faces.push(face),
            Err(e) => eprintln!("note: cannot read {}: {e}", path.display()),
        }
    }
    faces
}

/// The characters of `lines` that `face` has no glyph for.
fn missing_chars(face: &dyn Face, lines: &[String]) -> BTreeSet<char> {
    lines.iter().flat_map(|l| l.chars()).filter(|&c| !face.has(c)).collect()
}

/// Colours of a text sheet.
struct Ink {
    bg: Color,
    fg: Color,
}

impl Ink {
    fn new(dark: bool) -> Ink {
        if dark {
            Ink { bg: rgba(0x12, 0x12, 0x14, 255), fg: rgba(0xe8, 0xe8, 0xe4, 255) }
        } else {
            Ink { bg: rgba(255, 255, 255, 255), fg: rgba(0x10, 0x10, 0x10, 255) }
        }
    }
}

/// Text mode: every line at every size, stacked by size; within a size, our masters and then the reference fonts,
/// labelled in a left gutter when there is more than one face or `--masters` was asked for.
fn text_proof(
    registry: &Registry,
    chosen: &[Params],
    lines: &[String],
    opts: &Opts,
    labels: &mut Labeller,
) -> Option<Pixmap> {
    let ink = Ink::new(opts.dark);
    let mut faces: Vec<Box<dyn Face + '_>> = Vec::new();
    for p in chosen {
        faces.push(Box::new(OurFace::new(registry, p.clone())));
    }
    note_missing(&missing_chars(faces[0].as_ref(), lines), "");
    if opts.compare {
        for face in reference_faces() {
            note_missing(&missing_chars(&face, lines), &format!(" in {}", face.family));
            faces.push(Box::new(face));
        }
    }
    let labelled = opts.all_masters || faces.len() > 1;
    let gutter = if labelled { faces.iter().map(|f| labels.width(f.name())).max().unwrap_or(0) + 24 } else { 0 };
    let mut blocks = Vec::new();
    for &size in &opts.sizes {
        let factor = if size <= 24 { opts.scale } else { 1 };
        for face in &mut faces {
            let mut block = set_lines(face.as_mut(), lines, size, &ink)?;
            if factor > 1 {
                block = enlarge(&block, factor)?;
            }
            let label = labelled.then(|| face.name().to_string());
            let baseline = f64::from(first_baseline(size) * factor);
            blocks.push(with_gutter(block, gutter, label.as_deref(), baseline, labels, &ink)?);
        }
    }
    stack(&blocks, ink.bg)
}

/// The top margin of a text block, and the baseline of its first line below the block's top.
fn first_baseline(size: u32) -> u32 {
    size / 4 + size
}

/// `lines` set in `face` at `size` pixels per em on a terminal grid: integer cells, integer baselines.
fn set_lines(face: &mut dyn Face, lines: &[String], size: u32, ink: &Ink) -> Option<Pixmap> {
    let k = f64::from(size) / face.upm();
    let cell = (face.advance() * k).round().max(1.0);
    let pitch = (1.25 * f64::from(size)).round();
    let margin = f64::from(size / 2);
    let columns = lines.iter().map(|l| l.chars().count()).max().unwrap_or(0);
    let width = 2.0 * margin + columns as f64 * cell;
    let height = f64::from(size / 4) * 2.0 + pitch * lines.len() as f64;
    let mut pix = blank(width as u32, height as u32, ink.bg)?;
    for (row, text) in lines.iter().enumerate() {
        let baseline = f64::from(first_baseline(size)) + row as f64 * pitch;
        for (col, c) in text.chars().enumerate() {
            if let Some(path) = face.outline(c) {
                let x = margin + col as f64 * cell;
                fill(&mut pix, &path, ink.fg, glyph_transform(k, x, baseline));
            }
        }
    }
    Some(pix)
}

/// `block` to the right of a gutter `gutter` pixels wide, with `label` in the gutter on the baseline `baseline`.
fn with_gutter(
    block: Pixmap,
    gutter: u32,
    label: Option<&str>,
    baseline: f64,
    labels: &mut Labeller,
    ink: &Ink,
) -> Option<Pixmap> {
    let Some(label) = label else {
        return Some(block);
    };
    let mut out = blank(gutter + block.width(), block.height(), ink.bg)?;
    out.draw_pixmap(gutter as i32, 0, block.as_ref(), &PixmapPaint::default(), Transform::identity(), None);
    labels.draw(&mut out, label, 10.0, baseline);
    Some(out)
}
