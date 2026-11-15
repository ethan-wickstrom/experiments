//! Glyphs that are not characters.

use rachis_kernel::pen::rect;
use rachis_kernel::{Draw, Opt, Registry};

/// What a font shows for a character it lacks: an empty box, cap-height tall.
fn notdef(g: &mut Draw) {
    let p = g.p;
    let (x0, x1) = (p.cap_sb, p.width - p.cap_sb);
    let t = p.op * 0.8;
    g.add_upright(rect(x0, 0.0, x1, p.cap));
    g.add_upright(rect(x0 + t, t, x1 - t, p.cap - t).reversed());
}

pub fn register(reg: &mut Registry) {
    reg.module("special");
    reg.glyph(".notdef", &[], Opt::UPRIGHT, notdef);
}
