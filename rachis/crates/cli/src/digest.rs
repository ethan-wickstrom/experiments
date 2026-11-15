//! `rachis digest`: a regression snapshot of the outlines.
//!
//! For every face and master, and every glyph module the face has, one SHA-256 over the module's glyphs in
//! registration order: each glyph's name, advance, contours (every segment, coordinates rounded to 1/100 unit),
//! components and anchors. A change to a glyph program, a part or the kernel shows as the master/module pairs whose
//! digest moved; `--glyphs` prints one digest per glyph, for `diff` to find which.

use std::collections::BTreeMap;
use std::fmt::Write as _;
use std::path::PathBuf;
use std::process::ExitCode;

use rachis_kernel::params::faces;
use rachis_kernel::{Glyph, Params, Registry, Seg};
use sha2::{Digest, Sha256};

const USAGE: &str = "usage: rachis digest [--write | --check] [--glyphs]";

/// The snapshot, under the workspace root.
pub fn snapshot_path() -> PathBuf {
    let crate_dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR"));
    let root = crate_dir.parent().and_then(std::path::Path::parent).unwrap_or(crate_dir);
    root.join("tests/snapshot/outlines.sha256")
}

/// A coordinate in hundredths of a unit, so that -0.001 and 0.001 agree.
fn hundredths(v: f64) -> i64 {
    (v * 100.0).round() as i64
}

/// The text a glyph's digest is taken over: one line per item, coordinates in hundredths of a unit.
fn glyph_text(g: &Glyph) -> String {
    let mut out = String::new();
    let _ = writeln!(out, "G {} {}", g.name, hundredths(g.advance));
    for c in &g.contours {
        let _ = writeln!(out, "C {}", c.segs.len());
        for s in &c.segs {
            match *s {
                Seg::Line(a, b) => {
                    let _ = writeln!(
                        out,
                        "L {} {} {} {}",
                        hundredths(a.x),
                        hundredths(a.y),
                        hundredths(b.x),
                        hundredths(b.y)
                    );
                }
                Seg::Cubic(a, b, c, d) => {
                    let pts = [a, b, c, d].map(|z| format!("{} {}", hundredths(z.x), hundredths(z.y)));
                    let _ = writeln!(out, "B {}", pts.join(" "));
                }
            }
        }
    }
    for (name, z) in &g.components {
        let _ = writeln!(out, "K {name} {} {}", hundredths(z.x), hundredths(z.y));
    }
    for (name, z) in &g.anchors {
        let _ = writeln!(out, "A {name} {} {}", hundredths(z.x), hundredths(z.y));
    }
    out
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

/// The glyphs of `p` in registration order, for the modules `has` accepts: (module, glyph, text to digest).
fn glyph_texts(registry: &Registry, p: &Params, has: &dyn Fn(&str) -> bool) -> Vec<(&'static str, String, String)> {
    registry
        .specs
        .iter()
        .filter(|s| has(s.module))
        .map(|s| {
            let g = registry.build(s, p);
            (s.module, g.name.clone(), glyph_text(&g))
        })
        .collect()
}

/// The lines of the snapshot: `digest<TAB>master<TAB>module<TAB>glyph count`, masters in the order of `faces()`,
/// modules in registration order; or with `per_glyph`, `digest<TAB>master<TAB>module<TAB>glyph`.
pub fn lines(registry: &Registry, per_glyph: bool) -> Vec<String> {
    let jobs: Vec<(Params, Vec<&'static str>)> = faces()
        .into_iter()
        .flat_map(|f| {
            let omit = f.omit;
            f.masters.into_iter().map(move |p| (p, omit.to_vec()))
        })
        .collect();
    let per_master: Vec<Vec<String>> = std::thread::scope(|s| {
        let handles: Vec<_> = jobs
            .iter()
            .map(|(p, omit)| {
                s.spawn(move || {
                    let texts = glyph_texts(registry, p, &|m| !omit.contains(&m));
                    master_lines(p.name, &texts, per_glyph)
                })
            })
            .collect();
        handles.into_iter().map(|h| h.join().expect("a digest thread panicked")).collect()
    });
    per_master.into_iter().flatten().collect()
}

fn master_lines(master: &str, texts: &[(&'static str, String, String)], per_glyph: bool) -> Vec<String> {
    if per_glyph {
        return texts
            .iter()
            .map(|(module, name, t)| format!("{}\t{master}\t{module}\t{name}", hex(&Sha256::digest(t.as_bytes()))))
            .collect();
    }
    let mut modules: Vec<&str> = Vec::new();
    for (m, _, _) in texts {
        if !modules.contains(m) {
            modules.push(m);
        }
    }
    modules
        .iter()
        .map(|&m| {
            let mut h = Sha256::new();
            let mut count = 0;
            for (_, _, t) in texts.iter().filter(|(module, _, _)| *module == m) {
                h.update(t.as_bytes());
                count += 1;
            }
            format!("{}\t{master}\t{m}\t{count}", hex(&h.finalize()))
        })
        .collect()
}

/// The (master, module) pairs whose lines differ between two snapshots, in words.
pub fn differences(old: &str, new: &str) -> Vec<String> {
    let parse = |text: &str| -> BTreeMap<(String, String), String> {
        text.lines()
            .filter(|l| !l.trim().is_empty())
            .filter_map(|l| {
                let f: Vec<&str> = l.split('\t').collect();
                (f.len() == 4).then(|| ((f[1].to_string(), f[2].to_string()), format!("{} {}", f[0], f[3])))
            })
            .collect()
    };
    let (old, new) = (parse(old), parse(new));
    let mut out = Vec::new();
    for (key, v) in &new {
        match old.get(key) {
            None => out.push(format!("added: {} / {}", key.0, key.1)),
            Some(o) if o != v => out.push(format!("changed: {} / {}", key.0, key.1)),
            _ => {}
        }
    }
    for key in old.keys().filter(|k| !new.contains_key(*k)) {
        out.push(format!("removed: {} / {}", key.0, key.1));
    }
    out
}

pub fn run(registry: &Registry, args: &[String]) -> ExitCode {
    let (mut write, mut check, mut per_glyph) = (false, false, false);
    for a in args {
        match a.as_str() {
            "--write" => write = true,
            "--check" => check = true,
            "--glyphs" => per_glyph = true,
            _ => {
                eprintln!("rachis digest: unknown argument {a:?}\n{USAGE}");
                return ExitCode::FAILURE;
            }
        }
    }
    if write && check || per_glyph && (write || check) {
        eprintln!("rachis digest: --write, --check and --glyphs go alone\n{USAGE}");
        return ExitCode::FAILURE;
    }
    let text: String = lines(registry, per_glyph).iter().map(|l| format!("{l}\n")).collect();
    let path = snapshot_path();
    if write {
        if let Some(dir) = path.parent()
            && let Err(e) = std::fs::create_dir_all(dir)
        {
            eprintln!("rachis digest: cannot create {}: {e}", dir.display());
            return ExitCode::FAILURE;
        }
        if let Err(e) = std::fs::write(&path, &text) {
            eprintln!("rachis digest: cannot write {}: {e}", path.display());
            return ExitCode::FAILURE;
        }
        eprintln!("wrote {} ({} lines)", path.display(), text.lines().count());
        return ExitCode::SUCCESS;
    }
    if check {
        let old = match std::fs::read_to_string(&path) {
            Ok(t) => t,
            Err(e) => {
                eprintln!("rachis digest: cannot read {}: {e}", path.display());
                return ExitCode::FAILURE;
            }
        };
        let diffs = differences(&old, &text);
        for d in &diffs {
            println!("{d}");
        }
        if diffs.is_empty() {
            println!("outlines match the snapshot ({} master/module pairs)", text.lines().count());
            return ExitCode::SUCCESS;
        }
        println!(
            "{} master/module pairs differ from {}; `rachis digest --write` records the change",
            diffs.len(),
            path.display()
        );
        return ExitCode::FAILURE;
    }
    // a closed pipe (`| head`) ends the output quietly
    let _ = std::io::Write::write_all(&mut std::io::stdout(), text.as_bytes());
    ExitCode::SUCCESS
}

#[cfg(test)]
mod tests {
    use super::*;
    use rachis_kernel::V;

    #[test]
    fn rounding_to_hundredths_ignores_signs_of_zero_and_noise() {
        assert_eq!(hundredths(-0.001), 0);
        assert_eq!(hundredths(0.004), 0);
        assert_eq!(hundredths(12.345_6), 1235);
        let mut g = Glyph { name: "a".into(), advance: 600.0, ..Glyph::default() };
        let t0 = glyph_text(&g);
        g.advance = 600.001;
        assert_eq!(glyph_text(&g), t0);
        g.components.push(("b".into(), V { x: 1.0, y: 2.0 }));
        assert_ne!(glyph_text(&g), t0);
    }

    #[test]
    fn differences_name_the_pairs() {
        let old = "aa\tMono Regular\tlower\t3\nbb\tMono Regular\tupper\t2\n";
        let new = "aa\tMono Regular\tlower\t3\ncc\tMono Regular\tupper\t2\ndd\tMono Bold\tlower\t3\n";
        assert_eq!(differences(old, new), vec!["added: Mono Bold / lower", "changed: Mono Regular / upper"]);
        assert!(differences(old, old).is_empty());
    }
}
