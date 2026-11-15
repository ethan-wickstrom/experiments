//! The proportional family's widths.
//!
//! In the fixed-pitch family every glyph has the cell of the master. In the proportional family a letter has the
//! width its own shape asks for. Each glyph module says what that is for its glyphs, in a function
//! `fit(name, p) -> Option<Fit>`: the width of the cell its program draws into, counted in the master's
//! sidebearings, stems and counters so that one entry holds at every weight and optical size, and what to add to
//! each sidebearing afterwards. A glyph without an entry keeps the master's cell, as figures, operators, arrows
//! and symbols do: columns of figures align, and a formula's operators are as wide as its figures.

use rachis_kernel::{Fit, Params, Spec};

use crate::{greek, latin, lower, punct, upper};

/// The fit of the glyph `spec` in the master `p`; `None` in the fixed-pitch family.
pub fn fit(spec: &Spec, p: &Params) -> Option<Fit> {
    if p.mono {
        return None;
    }
    match spec.module {
        "lower" => lower::fit(&spec.name, p),
        "upper" => upper::fit(&spec.name, p),
        "punct" => punct::fit(&spec.name, p),
        "greek" => greek::fit(&spec.name, p),
        "latin" => latin::fit(&spec.name, p),
        _ => None,
    }
}
