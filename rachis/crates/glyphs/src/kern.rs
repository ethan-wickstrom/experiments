//! Kerning, computed from the outlines.
//!
//! The sidebearings in the widths tables space a letter against the average neighbour. A pair of letters whose
//! shapes leave more white between them than that (T and o, A and V, r and a full stop) is kerned: moved
//! together by a part of the excess. The white of a pair is measured where the two letters stand side by side:
//! on every row of that zone, the distance from the ink of the left letter to the ink of the right one, counted
//! no further than a fixed depth, since white far inside a letter does not read as space between letters. Two
//! straight stems at their standard sidebearings measure the standard; a pair that measures more is closed by
//! a fraction of the difference, and a pair whose inks come too near is opened.
//!
//! The computation can run for any master. The fonts carry the kerning of each face's default master (the
//! Regular at the size for text) at every weight and size, and the proof tools show that same kerning
//! ([`of_face`]), so that a proof shows what a font does.

use rachis_kernel::geom::flatten;
use rachis_kernel::{Glyph, Params, Registry};

/// The distance between rows, in font units.
const STEP: f64 = 10.0;
/// How deep the white of a row is counted, as a multiple of the pair's standard distance. At this depth a round
/// side at the round sidebearing measures what a straight side at the straight one does, so the widths tables
/// and the kerning agree about pairs that need nothing.
const DEPTH: f64 = 1.6;
/// The share of a pair's excess white that kerning takes away.
const GAIN: f64 = 0.75;
/// Kerns smaller than this are not worth a table entry.
const LEAST: f64 = 10.0;
/// Kerning never brings two inks nearer than this share of the standard distance between two stems: the arm
/// of r stays clear of n, so that the two are not read as m.
const NEAREST: f64 = 0.55;
/// Two inks nearer than this share of the standard distance are moved apart.
const TOUCHING: f64 = 0.16;
/// Glyphs whose kerning against every neighbour differs by no more than this are one class.
const ALIKE: f64 = 9.0;

/// The glyphs that are kerned: letters, accented letters (each by its own outline: an accent that overhangs
/// its letter must keep clear of the neighbour), and the punctuation that stands against them.
const MODULES: [&str; 4] = ["lower", "upper", "punct", "latin"];
const SIGNS: [&str; 3] = ["hyphen", "slash", "backslash"];
/// Glyphs of those modules that stand apart from words, or in columns, and are left alone.
const APART: [&str; 15] = [
    "space",
    "nbspace",
    "at",
    "ampersand",
    "dollar",
    "percent",
    "uni2030",
    "numbersign",
    "section",
    "paragraph",
    "copyright",
    "registered",
    "uni2122",
    "uni2116",
    "currency",
];

/// The sides of one glyph: on every row, how far the ink stands from the left edge and from the right edge of
/// the advance; infinite where the row has no ink.
struct Sides {
    name: String,
    capital: bool,
    left: Vec<f64>,
    right: Vec<f64>,
    /// The first and the last row with ink.
    rows: (usize, usize),
}

fn sides(glyph: &Glyph, capital: bool, y0: f64, count: usize) -> Option<Sides> {
    let mut left = vec![f64::INFINITY; count];
    let mut right = vec![f64::INFINITY; count];
    for contour in &glyph.contours {
        let mut points = Vec::new();
        for seg in &contour.segs {
            // each segment gives the points after its start, so the pieces chain into the closed outline
            points.extend(flatten(seg, 0.5));
        }
        for (i, a) in points.iter().enumerate() {
            let b = points[(i + 1) % points.len()];
            let (lo, hi) = if a.y < b.y { (a.y, b.y) } else { (b.y, a.y) };
            if hi <= lo {
                continue;
            }
            // the rows this edge crosses; rows sit a little off the integers, clear of the outlines' points
            let first = ((lo - y0) / STEP - 0.37).ceil().max(0.0) as usize;
            let mut row = first;
            while row < count {
                let y = y0 + (row as f64 + 0.37) * STEP;
                if y >= hi {
                    break;
                }
                let x = a.x + (b.x - a.x) * (y - a.y) / (b.y - a.y);
                left[row] = left[row].min(x);
                right[row] = right[row].min(glyph.advance - x);
                row += 1;
            }
        }
    }
    let first = left.iter().position(|x| x.is_finite())?;
    let last = left.iter().rposition(|x| x.is_finite())?;
    Some(Sides { name: glyph.name.clone(), capital, left, right, rows: (first, last) })
}

/// Brackets enclose: the white inside one is not space between letters, so nothing is moved into it.
const OPENING: [&str; 3] = ["parenleft", "bracketleft", "braceleft"];
const CLOSING: [&str; 3] = ["parenright", "bracketright", "braceright"];

/// How far the right glyph must move (negative: nearer) for the pair to stand as two stems do.
fn kern(a: &Sides, b: &Sides, p: &Params) -> f64 {
    let standard = if a.capital { p.cap_sb } else { p.sb } + if b.capital { p.cap_sb } else { p.sb };
    let (first, last) = (a.rows.0.max(b.rows.0), a.rows.1.min(b.rows.1));
    if last < first {
        return 0.0;
    }
    // only rows where both have ink count: white beside one glyph alone is not space between the two
    let depth = DEPTH * standard;
    let (mut white, mut nearest, mut shared) = (0.0, f64::INFINITY, 0usize);
    for row in first..=last {
        let gap = a.right[row] + b.left[row];
        if gap.is_finite() {
            white += gap.min(depth);
            nearest = nearest.min(gap);
            shared += 1;
        }
    }
    if (shared as f64) * STEP < 0.1 * p.xh {
        return 0.0; // the two never stand side by side: a colon and a hyphen, a quote and a full stop
    }
    let mean = white / shared as f64;
    let enclosed = OPENING.contains(&a.name.as_str()) || CLOSING.contains(&b.name.as_str());
    let closer = if enclosed { 0.0 } else { (GAIN * (standard - mean)).min(0.0) };
    // close no further than the nearest inks allow; open a pair whose inks touch or cross
    let allowed = (NEAREST * standard - nearest).min(0.0);
    closer.max(allowed).max(TOUCHING * standard - nearest)
}

/// The kerning of a face: classes of glyphs that kern alike on their right side and on their left side, decided
/// on the face's default master.
pub struct Classes {
    /// Glyphs as the left member of a pair, grouped by how their right sides kern.
    pub first: Vec<Vec<String>>,
    /// Glyphs as the right member of a pair, grouped by how their left sides kern.
    pub second: Vec<Vec<String>>,
}

/// The sides of every kerned glyph of the master `p`, drawn upright: an italic is kerned as its upright.
fn all_sides(registry: &Registry, p: &Params) -> Vec<Sides> {
    let upright = Params { slant: 0.0, ..p.clone() };
    let y0 = upright.desc - 60.0;
    let count = ((upright.asc + 120.0 - y0) / STEP) as usize;
    registry
        .specs
        .iter()
        .filter(|s| (MODULES.contains(&s.module) || SIGNS.contains(&s.name.as_str())) && !s.opt.mark)
        .filter(|s| !APART.contains(&s.name.as_str()))
        .filter_map(|s| {
            // a capital stands at the capitals' sidebearing; unencoded glyphs are not letters of a text
            let capital = char::from_u32(*s.unicodes.first()?)?.is_uppercase();
            sides(&registry.flat(&s.name, &upright)?, capital, y0, count)
        })
        .collect()
}

/// Group `count` items so that two are together when `row(i)` and `row(j)` differ nowhere by more than `ALIKE`.
fn group(count: usize, row: impl Fn(usize) -> Vec<f64>) -> Vec<Vec<usize>> {
    let rows: Vec<Vec<f64>> = (0..count).map(row).collect();
    let mut groups: Vec<Vec<usize>> = Vec::new();
    for i in 0..count {
        let home = groups.iter_mut().find(|g| rows[g[0]].iter().zip(&rows[i]).all(|(a, b)| (a - b).abs() <= ALIKE));
        match home {
            Some(g) => g.push(i),
            None => groups.push(vec![i]),
        }
    }
    groups
}

/// The kerning classes of a face, from its default master `p`. Empty for a fixed-pitch face.
pub fn classes(registry: &Registry, p: &Params) -> Classes {
    if p.mono {
        return Classes { first: Vec::new(), second: Vec::new() };
    }
    let all = all_sides(registry, p);
    let upright = Params { slant: 0.0, ..p.clone() };
    let table: Vec<Vec<f64>> = all.iter().map(|a| all.iter().map(|b| kern(a, b, &upright)).collect()).collect();
    let names = |groups: Vec<Vec<usize>>| -> Vec<Vec<String>> {
        groups.into_iter().map(|g| g.into_iter().map(|i| all[i].name.clone()).collect()).collect()
    };
    let first = group(all.len(), |i| table[i].clone());
    let second = group(all.len(), |j| table.iter().map(|row| row[j]).collect());
    // a class that kerns with nothing needs no entry
    let quiet = |row: Vec<f64>| row.iter().all(|k| k.abs() < LEAST);
    let first = first.into_iter().filter(|g| !quiet(table[g[0]].clone())).collect();
    let second = second.into_iter().filter(|g| !quiet(table.iter().map(|row| row[g[0]]).collect())).collect();
    Classes { first: names(first), second: names(second) }
}

/// The kerning of the master `p` between the classes `classes`: one row for each class of first glyphs, one
/// value for each class of second glyphs, in font units. A class is measured on its first member.
pub fn values(registry: &Registry, p: &Params, classes: &Classes) -> Vec<Vec<f64>> {
    let all = all_sides(registry, p);
    let upright = Params { slant: 0.0, ..p.clone() };
    let of = |name: &String| all.iter().find(|s| &s.name == name);
    classes
        .first
        .iter()
        .map(|a| {
            classes
                .second
                .iter()
                .map(|b| match (of(&a[0]), of(&b[0])) {
                    (Some(a), Some(b)) => {
                        let k = kern(a, b, &upright).round();
                        if k.abs() >= LEAST { k } else { 0.0 }
                    }
                    _ => 0.0,
                })
                .collect()
        })
        .collect()
}

/// The kerning the fonts of `p`'s face carry, pair by pair: that of the face's default master, whatever the
/// weight and size of `p`. For proofs and for `rachis kern`.
pub fn of_face(registry: &Registry, p: &Params) -> Vec<(String, String, f64)> {
    let face = rachis_kernel::params::faces().into_iter().find(|f| f.masters.iter().any(|m| m.name == p.name));
    match face {
        Some(face) => kerning(registry, face.default_master()),
        None => kerning(registry, p),
    }
}

/// The kerning of the master `p` itself, pair by pair: (left glyph, right glyph, adjustment).
pub fn kerning(registry: &Registry, p: &Params) -> Vec<(String, String, f64)> {
    let classes = classes(registry, p);
    let table = values(registry, p, &classes);
    let mut pairs = Vec::new();
    for (a, row) in classes.first.iter().zip(&table) {
        for (b, &k) in classes.second.iter().zip(row) {
            if k != 0.0 {
                pairs.extend(a.iter().flat_map(|l| b.iter().map(move |r| (l.clone(), r.clone(), k))));
            }
        }
    }
    pairs
}
