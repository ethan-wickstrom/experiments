//! The glyph programs of the typeface, one module per group, and the parts they share.

pub mod arrows;
pub mod boxes;
pub mod digits;
pub mod greek;
pub mod latin;
pub mod lower;
pub mod operators;
pub mod parts;
pub mod punct;
pub mod special;
pub mod symbols;
pub mod upper;

use rachis_kernel::Registry;

/// Every glyph program of the typeface.
pub fn registry() -> Registry {
    let mut r = Registry::new();
    special::register(&mut r);
    lower::register(&mut r);
    upper::register(&mut r);
    digits::register(&mut r);
    punct::register(&mut r);
    operators::register(&mut r);
    arrows::register(&mut r);
    greek::register(&mut r);
    latin::register(&mut r);
    symbols::register(&mut r);
    boxes::register(&mut r);
    r
}
