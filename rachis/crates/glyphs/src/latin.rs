//! Not ported yet.

use rachis_kernel::{Fit, Params, Registry};

pub fn register(_reg: &mut Registry) {}

/// The proportional family's cells for this module's glyphs.
pub fn fit(_name: &str, _p: &Params) -> Option<Fit> {
    None
}
