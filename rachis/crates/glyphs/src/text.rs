//! The proportional family's widths.
//!
//! In the fixed-pitch family every glyph has the cell of the master. In the proportional family a letter has the
//! width its own shape asks for. Each glyph module says what that is for its glyphs, as a type designer spaces a
//! face: the sidebearing on each side and the breadth of the ink between them ([`Ask`]), counted in the master's
//! sidebearings, stems and counters so that one entry holds at every weight and optical size. The cell a program
//! must be given to draw ink that broad, and what it leaves at its sides, are measured from the program itself.
//! A glyph without an entry keeps the master's cell, as figures and the signs of arithmetic do: columns of
//! figures align, and a formula's plus and equals are as wide as its figures. The other signs have the room that
//! `signs.rs` gives them.

use rachis_kernel::{Fit, Params, Registry, Spec};

use crate::{greek, latin, lower, punct, signs, typography, upper};

/// What a letter asks of the proportional family: its sidebearings, and the breadth of its ink.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Ask {
    pub left: f64,
    /// `None` when the program draws a shape of a size of its own, whatever cell it is given.
    pub ink: Option<f64>,
    pub right: f64,
}

/// Sidebearings `left` and `right` around ink `ink` broad.
pub fn around(left: f64, ink: f64, right: f64) -> Option<Ask> {
    Some(Ask { left, ink: Some(ink), right })
}

/// Sidebearings `left` and `right` around whatever the program draws.
pub fn beside(left: f64, right: f64) -> Option<Ask> {
    Some(Ask { left, ink: None, right })
}

/// The ink of a letter with `stems` stems and `counters` counters of n: the sum that grows with weight as a
/// letter of that structure does.
pub fn ink(p: &Params, stems: f64, counters: f64) -> f64 {
    stems * p.stem + counters * p.counter
}

/// The same for a capital, whose stems are the capitals'.
pub fn cap_ink(p: &Params, stems: f64, counters: f64) -> f64 {
    stems * p.cap_stem + counters * p.counter
}

/// The space between words.
pub fn word_space(p: &Params) -> f64 {
    0.5 * p.stem + 0.85 * p.counter
}

/// What the signs that prose uses as punctuation ask: they live with the operators, whose room is otherwise in
/// `signs.rs`.
fn sign(name: &str, p: &Params) -> Option<Ask> {
    let sb = p.sb;
    match name {
        "hyphen" => around(0.5 * sb, 0.95 * p.counter, 0.5 * sb),
        "slash" | "backslash" => around(0.14 * sb, 1.3 * p.counter, 0.14 * sb),
        "bar" => beside(1.2 * sb, 1.2 * sb),
        "asterisk" => around(0.5 * sb, 1.4 * p.counter, 0.5 * sb),
        _ => None,
    }
}

/// Superior and inferior figures and signs: in a formula they follow a letter closely, so they take the room of
/// their ink and a small sidebearing, not the figures' cell. Fractions keep the cell.
fn script_figure(spec: &Spec, p: &Params) -> Option<Ask> {
    let small = |c: &u32| matches!(*c, 0x00B2 | 0x00B3 | 0x00B9 | 0x2070..=0x209F);
    spec.unicodes.iter().any(small).then_some(Ask { left: 0.32 * p.sb, ink: None, right: 0.32 * p.sb })
}

/// The cell and the sidebearing adjustments that give the glyph what it asks for.
fn resolve(registry: &Registry, spec: &Spec, p: &Params, want: Ask) -> Option<Fit> {
    // the first cell is a guess; a program's ink grows by as much as its cell does, so one correction lands
    let mut width = want.left + want.ink.unwrap_or(p.width) + want.right;
    let mut ends = registry.measure(spec, p, width);
    if let Some(target) = want.ink {
        for _ in 0..4 {
            let (x0, x1) = ends?;
            if (x1 - x0 - target).abs() < 0.01 {
                break;
            }
            width += target - (x1 - x0);
            ends = registry.measure(spec, p, width);
        }
    }
    let Some((x0, x1)) = ends else {
        // a blank glyph: the ask is the advance
        return Some(Fit::new(want.left + want.ink.unwrap_or(0.0) + want.right));
    };
    Some(Fit { width, left: want.left - x0, right: want.right - (width - x1), grown: 1.0 })
}

/// The fit of the glyph `spec` in the master `p`; `None` in the fixed-pitch family.
pub fn fit(registry: &Registry, spec: &Spec, p: &Params) -> Option<Fit> {
    if p.mono {
        return None;
    }
    let want = match spec.module {
        "lower" => lower::ask(&spec.name, p),
        "upper" => upper::ask(&spec.name, p),
        "punct" => punct::ask(&spec.name, p),
        "operators" => sign(&spec.name, p),
        "digits" => script_figure(spec, p),
        "greek" => return greek::fit(&spec.name, p),
        "typography" => return typography::fit(registry, &spec.name, p).or_else(|| signs::fit(registry, spec, p)),
        "latin" => latin::ask(&spec.name, p),
        _ => None,
    };
    let Some(want) = want else {
        // no letter's width: a sign's room, or the master's cell
        return signs::fit(registry, spec, p);
    };
    resolve(registry, spec, p, want)
}
