//! The kernel of the Rachis typeface.
//!
//! A glyph is a program over this kernel: it places knots that carry a pen, the kernel draws a centre line
//! through them and returns the outline the pen leaves. See `docs/drawing.md`.

pub mod check;
pub mod geom;
pub mod glyph;
pub mod names;
pub mod params;
pub mod pen;

pub use geom::{Seg, V, pt};
pub use glyph::{Draw, Fit, Glyph, Opt, Registry, Spec, build, build_all};
pub use names::{name_of, name_of_code};
pub use params::{Face, Params};
pub use pen::{Contour, Knot, knot};
