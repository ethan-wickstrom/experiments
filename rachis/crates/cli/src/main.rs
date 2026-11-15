//! Command line of the Rachis typeface.

mod build;
mod digest;
mod measure;
mod proof;

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
        Some("digest") => digest::run(&registry, &args[1..]),
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
                "usage: rachis <build [--out DIR] [--no-statics] [--no-hint] | proof ... | measure ... | digest [--write | --check] [--glyphs] | check [NAMES...] | dump [--module NAME] | list | widths [--master NAME] TEXT | kern [--master NAME] [PAIRS]>"
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

/// Print the advance, the sidebearings and the breadth of the ink of each character of the arguments.
fn widths(registry: &Registry, args: &[String]) -> ExitCode {
    let name = args.iter().position(|a| a == "--master").and_then(|i| args.get(i + 1));
    let Some(p) = master(name.map_or("Text Regular", String::as_str)) else {
        eprintln!("no such master");
        return ExitCode::FAILURE;
    };
    let text: String = args.iter().filter(|a| !a.starts_with("--") && Some(*a) != name).cloned().collect();
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
    ExitCode::SUCCESS
}

/// Print the computed kerning of a master: of the pairs given as two-character arguments, or the count and the
/// largest when none are given.
fn kern(registry: &Registry, args: &[String]) -> ExitCode {
    let name = args.iter().position(|a| a == "--master").and_then(|i| args.get(i + 1));
    let Some(p) = master(name.map_or("Text Regular", String::as_str)) else {
        eprintln!("no such master");
        return ExitCode::FAILURE;
    };
    let pairs = rachis_glyphs::kern::kerning(registry, &p);
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
