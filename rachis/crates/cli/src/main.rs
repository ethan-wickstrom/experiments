//! Command line of the Rachis typeface.

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
        Some("proof") => proof::run(&registry, &args[1..]),
        Some("list") => {
            for s in &registry.specs {
                let cps: Vec<String> = s.unicodes.iter().map(|c| format!("U+{c:04X}")).collect();
                println!("{:28} {:16} {}", s.name, cps.join(" "), s.module);
            }
            eprintln!("{} glyphs", registry.len());
            ExitCode::SUCCESS
        }
        _ => {
            eprintln!("usage: rachis <proof ... | check [NAMES...] | dump [--module NAME] | list>");
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
