//! `rachis specimen`: the specimen page, with the built web fonts and its figure inside it, as one HTML file.
//!
//! The page's source is `specimen/specimen.html`. It names what it needs as `{{font:FILE}}` (a file of
//! `fonts/webfonts`) and `{{image:FILE}}` (a file of `specimen/`), and each is replaced by the file in base64.
//! `{{distance:MASTER:PAIR}}` is replaced by that pair's distance in the snapshot `rachis measure --check` holds
//! the typeface to (`tests/snapshot/distances.tsv`), and `{{size:FILE}}` by the size in bytes of a file of
//! `fonts`, so the page cannot quote a distance or a size the fonts no longer have.

use std::path::{Path, PathBuf};
use std::process::ExitCode;

const TEMPLATE: &str = include_str!("../../../specimen/specimen.html");

/// `data` in base64 with padding.
fn base64(data: &[u8]) -> String {
    const ALPHABET: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity(data.len().div_ceil(3) * 4);
    for chunk in data.chunks(3) {
        let n = chunk.iter().fold(0u32, |n, &b| n << 8 | u32::from(b)) << (8 * (3 - chunk.len()));
        for i in 0..4 {
            if i <= chunk.len() {
                out.push(ALPHABET[(n >> (18 - 6 * i) & 63) as usize] as char);
            } else {
                out.push('=');
            }
        }
    }
    out
}

/// The page with every `{{kind:FILE}}` replaced by the file's base64, read from `dir`.
fn inline(page: &str, kind: &str, dir: &Path) -> Result<String, String> {
    let open = format!("{{{{{kind}:");
    let mut out = String::with_capacity(page.len());
    let mut rest = page;
    while let Some(at) = rest.find(&open) {
        let after = &rest[at + open.len()..];
        let end = after.find("}}").ok_or_else(|| format!("an unclosed {open}"))?;
        let path = dir.join(&after[..end]);
        let data = std::fs::read(&path).map_err(|e| format!("{}: {e}", path.display()))?;
        out.push_str(&rest[..at]);
        out.push_str(&base64(&data));
        rest = &after[end + 2..];
    }
    out.push_str(rest);
    Ok(out)
}

/// The page with every `{{distance:MASTER:PAIR}}` replaced by the distance the snapshot `recorded` gives that
/// pair of that master.
fn distances(page: &str, recorded: &str) -> Result<String, String> {
    let open = "{{distance:";
    let mut out = String::with_capacity(page.len());
    let mut rest = page;
    while let Some(at) = rest.find(open) {
        let after = &rest[at + open.len()..];
        let end = after.find("}}").ok_or_else(|| format!("an unclosed {open}"))?;
        let (master, pair) =
            after[..end].split_once(':').ok_or_else(|| format!("no pair in {open}{}", &after[..end]))?;
        let value = recorded
            .lines()
            .map(|line| line.split('\t').collect::<Vec<_>>())
            .find(|parts| parts.len() == 3 && parts[0] == master && parts[1] == pair)
            .map(|parts| parts[2].to_string())
            .ok_or_else(|| format!("the snapshot has no distance of {pair:?} in {master:?}"))?;
        out.push_str(&rest[..at]);
        out.push_str(&value);
        rest = &after[end + 2..];
    }
    out.push_str(rest);
    Ok(out)
}

/// The page with every `{{size:FILE}}` replaced by the size in bytes of that file of `dir`.
fn sizes(page: &str, dir: &Path) -> Result<String, String> {
    let open = "{{size:";
    let mut out = String::with_capacity(page.len());
    let mut rest = page;
    while let Some(at) = rest.find(open) {
        let after = &rest[at + open.len()..];
        let end = after.find("}}").ok_or_else(|| format!("an unclosed {open}"))?;
        let path = dir.join(&after[..end]);
        let bytes = std::fs::metadata(&path).map_err(|e| format!("{}: {e}", path.display()))?.len();
        out.push_str(&rest[..at]);
        out.push_str(&bytes.to_string());
        rest = &after[end + 2..];
    }
    out.push_str(rest);
    Ok(out)
}

/// Run `rachis specimen [--fonts DIR] [--figures DIR] -o FILE`.
pub fn run(args: &[String]) -> ExitCode {
    let value = |flag: &str| args.iter().position(|a| a == flag).and_then(|i| args.get(i + 1)).map(PathBuf::from);
    let fonts = value("--fonts").unwrap_or_else(|| PathBuf::from("fonts"));
    let figures = value("--figures").unwrap_or_else(|| PathBuf::from("specimen"));
    let Some(out) = value("-o") else {
        eprintln!("usage: rachis specimen [--fonts DIR] [--figures DIR] -o FILE");
        return ExitCode::FAILURE;
    };
    let snapshot = crate::measure::snapshot_path();
    let page = std::fs::read_to_string(&snapshot)
        .map_err(|e| format!("{}: {e}", snapshot.display()))
        .and_then(|recorded| distances(TEMPLATE, &recorded))
        .and_then(|page| sizes(&page, &fonts))
        .and_then(|page| inline(&page, "font", &fonts.join("webfonts")))
        .and_then(|page| inline(&page, "image", &figures));
    match page.and_then(|page| std::fs::write(&out, &page).map(|()| page.len()).map_err(|e| e.to_string())) {
        Ok(bytes) => {
            println!("{bytes:>9}  {}", out.display());
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("rachis specimen: {e}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{base64, distances};

    #[test]
    fn a_distance_is_taken_from_the_snapshot_and_a_pair_it_lacks_is_an_error() {
        let recorded = "Mono Regular\t0 O\t0.495\nText Regular\t0 O\t0.539\n";
        let page = "[{{distance:Mono Regular:0 O}}, {{distance:Text Regular:0 O}}]";
        assert_eq!(distances(page, recorded).as_deref(), Ok("[0.495, 0.539]"));
        assert!(distances("{{distance:Mono Regular:p ρ}}", recorded).is_err());
        assert!(distances("{{distance:Mono Regular}}", recorded).is_err());
    }

    #[test]
    fn base64_pads_and_matches_the_standard_vectors() {
        // RFC 4648, section 10
        for (plain, coded) in [
            ("", ""),
            ("f", "Zg=="),
            ("fo", "Zm8="),
            ("foo", "Zm9v"),
            ("foob", "Zm9vYg=="),
            ("fooba", "Zm9vYmE="),
            ("foobar", "Zm9vYmFy"),
        ] {
            assert_eq!(base64(plain.as_bytes()), coded);
        }
    }
}
