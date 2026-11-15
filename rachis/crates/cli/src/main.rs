//! Command line of the Rachis typeface.

mod build;
mod digest;
mod math;
mod measure;
mod proof;
mod specimen;

use std::fmt::Write as _;
use std::process::ExitCode;

use rachis_kernel::check::check_glyphs;
use rachis_kernel::params::{master, masters};
use rachis_kernel::{Glyph, Registry, Seg};

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let registry = rachis_glyphs::registry();
    match args.first().map(String::as_str) {
        Some("dump") => dump(&registry, &args[1..]),
        Some("check") => check(&registry, &args[1..]),
        Some("build") => build::run(&registry, &args[1..]),
        Some("proof") => proof::run(&registry, &args[1..]),
        Some("measure") => measure::run(&registry, &args[1..]),
        Some("math") => math::run(&registry, &args[1..]),
        Some("digest") => digest::run(&registry, &args[1..]),
        Some("specimen") => specimen::run(&args[1..]),
        Some("widths") => widths(&registry, &args[1..]),
        Some("kern") => kern(&registry, &args[1..]),
        Some("list") => {
            for s in &registry.specs {
                let cps: Vec<String> = s.unicodes.iter().map(|c| format!("U+{c:04X}")).collect();
                println!("{:28} {:16} {}", s.name, cps.join(" "), s.module);
            }
            eprintln!("{} glyphs", registry.len());
            ExitCode::SUCCESS
        }
        _ => {
            eprintln!(
                "usage: rachis <build [--out DIR] [--no-statics] [--no-hint] | proof ... | specimen -o FILE | measure ... | math [--refs DIR] | digest [--write | --check] [--glyphs] | check [NAMES...] | dump [--module NAME] | list | widths [--master NAME] [--refs DIR] TEXT | kern [--master NAME] [--own] [PAIRS]>"
            );
            ExitCode::FAILURE
        }
    }
}

/// Print every outline of every master in a line format that the prototype's dump shares, so the two
/// implementations can be compared number by number.
fn dump(registry: &Registry, args: &[String]) -> ExitCode {
    let module = args.iter().position(|a| a == "--module").and_then(|i| args.get(i + 1));
    let mut out = String::new();
    for p in masters() {
        for spec in &registry.specs {
            if module.is_some_and(|m| m != spec.module) {
                continue;
            }
            write_glyph(&mut out, p.name, &registry.build(spec, &p));
        }
    }
    print!("{out}");
    ExitCode::SUCCESS
}

/// Print the advance, the sidebearings and the breadth of the ink of each character of the arguments. With
/// `--refs DIR`, print beside them what the fonts in that directory give the character, scaled to the master's
/// x-height: the advance and the breadth and height of the ink of each, and their medians. This is how the room
/// of a sign in the proportional family was read from mathematics fonts (decision T27).
fn widths(registry: &Registry, args: &[String]) -> ExitCode {
    let value = |flag: &str| args.iter().position(|a| a == flag).and_then(|i| args.get(i + 1));
    let (name, refs) = (value("--master"), value("--refs"));
    let Some(p) = master(name.map_or("Text Regular", String::as_str)) else {
        eprintln!("no such master");
        return ExitCode::FAILURE;
    };
    let text: String =
        args.iter().filter(|a| !a.starts_with("--") && Some(*a) != name && Some(*a) != refs).cloned().collect();
    let Some(dir) = refs else {
        println!("{:>4} {:>8} {:>6} {:>6} {:>6}   {}", "", "advance", "left", "ink", "right", p.name);
        for c in text.chars() {
            let Some(g) = registry.for_char(c).and_then(|spec| registry.flat(&spec.name, &p)) else {
                println!("{c:>4} missing");
                continue;
            };
            match g.bounds() {
                Some((x0, _, x1, _)) => {
                    println!("{c:>4} {:>8.0} {:>6.0} {:>6.0} {:>6.0}", g.advance, x0, x1 - x0, g.advance - x1)
                }
                None => println!("{c:>4} {:>8.0}", g.advance),
            }
        }
        return ExitCode::SUCCESS;
    };
    let mut faces = match proof::reference_faces_in(std::path::Path::new(dir)) {
        Ok(faces) if !faces.is_empty() => faces,
        Ok(_) => {
            eprintln!("rachis widths: no fonts in {dir}");
            return ExitCode::FAILURE;
        }
        Err(e) => {
            eprintln!("rachis widths: {dir}: {e}");
            return ExitCode::FAILURE;
        }
    };
    use proof::Face as _;
    // advance, breadth and height of the ink of a character, in the font's units
    let size = |face: &mut proof::RefFace, c: char| -> Option<(f64, f64, f64)> {
        let b = face.outline(c)?.compute_tight_bounds()?;
        Some((face.advance_of(c), f64::from(b.width()), f64::from(b.height())))
    };
    let scales: Vec<f64> = faces.iter_mut().map(|f| size(f, 'x').map_or(0.0, |x| p.xh / x.2)).collect();
    let median = |mut v: Vec<f64>| {
        v.sort_by(f64::total_cmp);
        if v.is_empty() { f64::NAN } else { (v[(v.len() - 1) / 2] + v[v.len() / 2]) / 2.0 }
    };
    let names: Vec<String> = faces.iter().map(|f| f.name().to_string()).collect();
    println!("advance, and breadth x height of the ink; reference fonts scaled to an x-height of {}", p.xh);
    println!("{:>4} {:>16}   {:>16}   {}", "", p.name, "median", names.join(", "));
    let cell = |v: Option<(f64, f64, f64)>| match v {
        Some((a, w, h)) => format!("{a:>5.0} {w:>4.0}x{h:<4.0}"),
        None => format!("{:>15}", "-"),
    };
    for c in text.chars() {
        let ours = registry
            .for_char(c)
            .and_then(|spec| registry.flat(&spec.name, &p))
            .and_then(|g| g.bounds().map(|(x0, y0, x1, y1)| (g.advance, x1 - x0, y1 - y0)));
        let theirs: Vec<Option<(f64, f64, f64)>> =
            faces.iter_mut().zip(&scales).map(|(f, &k)| size(f, c).map(|(a, w, h)| (a * k, w * k, h * k))).collect();
        let have: Vec<(f64, f64, f64)> = theirs.iter().flatten().copied().collect();
        let mid = (!have.is_empty()).then(|| {
            (
                median(have.iter().map(|v| v.0).collect()),
                median(have.iter().map(|v| v.1).collect()),
                median(have.iter().map(|v| v.2).collect()),
            )
        });
        let each: Vec<String> = theirs.into_iter().map(cell).collect();
        println!("{c:>4} {}   {}   {}", cell(ours), cell(mid), each.join("  "));
    }
    ExitCode::SUCCESS
}

/// Print the kerning of a master's face as the fonts carry it (or, with `--own`, the kerning computed for that
/// master itself): of the pairs given as two-character arguments, or the classes and the largest when none are.
fn kern(registry: &Registry, args: &[String]) -> ExitCode {
    let name = args.iter().position(|a| a == "--master").and_then(|i| args.get(i + 1));
    let Some(p) = master(name.map_or("Text Regular", String::as_str)) else {
        eprintln!("no such master");
        return ExitCode::FAILURE;
    };
    // `--own` shows the master's own kerning; without it, what the fonts of its face carry
    let own = args.iter().any(|a| a == "--own");
    let pairs =
        if own { rachis_glyphs::kern::kerning(registry, &p) } else { rachis_glyphs::kern::of_face(registry, &p) };
    let wanted: Vec<&String> = args.iter().filter(|a| !a.starts_with("--") && Some(*a) != name).collect();
    let glyph = |c: char| registry.for_char(c).map(|s| s.name.clone()).unwrap_or_default();
    if wanted.is_empty() {
        let classes = rachis_glyphs::kern::classes(registry, &p);
        println!(
            "{} pairs in {}: {} first classes, {} second",
            pairs.len(),
            p.name,
            classes.first.len(),
            classes.second.len()
        );
        for class in classes.first.iter().chain(&classes.second) {
            println!("  {}", class.join(" "));
        }
        let mut sorted = pairs.clone();
        sorted.sort_by(|a, b| a.2.total_cmp(&b.2));
        for (l, r, k) in sorted.iter().take(40).chain(sorted.iter().rev().take(15)) {
            println!("{l:>14} {r:<14} {k:>6.0}");
        }
    }
    for pair in wanted {
        let mut chars = pair.chars();
        let (Some(a), Some(b)) = (chars.next(), chars.next()) else { continue };
        let (l, r) = (glyph(a), glyph(b));
        let k = pairs.iter().find(|(x, y, _)| *x == l && *y == r).map_or(0.0, |t| t.2);
        print!("{a}{b} {k:.0}   ");
    }
    println!();
    ExitCode::SUCCESS
}

fn write_glyph(out: &mut String, master: &str, g: &Glyph) {
    let _ = writeln!(out, "G\t{master}\t{}\t{:.6}", g.name, g.advance);
    for e in &g.errors {
        let _ = writeln!(out, "E\t{e}");
    }
    for c in &g.contours {
        let _ = writeln!(out, "C\t{}", c.segs.len());
        for s in &c.segs {
            match *s {
                Seg::Line(a, b) => {
                    let _ = writeln!(out, "L\t{:.6}\t{:.6}\t{:.6}\t{:.6}", a.x, a.y, b.x, b.y);
                }
                Seg::Cubic(a, b, c, d) => {
                    let _ = writeln!(
                        out,
                        "B\t{:.6}\t{:.6}\t{:.6}\t{:.6}\t{:.6}\t{:.6}\t{:.6}\t{:.6}",
                        a.x, a.y, b.x, b.y, c.x, c.y, d.x, d.y
                    );
                }
            }
        }
    }
    for (name, z) in &g.components {
        let _ = writeln!(out, "K\t{name}\t{:.6}\t{:.6}", z.x, z.y);
    }
    for (name, z) in &g.anchors {
        let _ = writeln!(out, "A\t{name}\t{:.6}\t{:.6}", z.x, z.y);
    }
}

fn check(registry: &Registry, args: &[String]) -> ExitCode {
    let names: Option<&[String]> = if args.is_empty() { None } else { Some(args) };
    let report = check_glyphs(registry, names);
    for n in &report.notes {
        println!("note: {n}");
    }
    for p in &report.problems {
        println!("FAIL: {p}");
    }
    println!(
        "{} problems, {} notes, {} glyphs checked",
        report.problems.len(),
        report.notes.len(),
        names.map_or(registry.len(), <[String]>::len)
    );
    let _ = master("Regular");
    if report.problems.is_empty() { ExitCode::SUCCESS } else { ExitCode::FAILURE }
}
