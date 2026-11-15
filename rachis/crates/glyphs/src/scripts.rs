//! Superscript and subscript letters: the modifier letters and the Latin and Greek inferiors.
//!
//! A script letter is not a reduced outline and not a new drawing: it is the program of its base letter run again
//! in a small master, `script_params`, the way the superior figures of `digits` are their constructions run again
//! in a small frame. The small master is the master scaled so that its x-height stands to a superior figure as
//! the x-height stands to the cap height, with the small figures' strokes and wider sidebearings and counters than
//! a plain reduction gives, which is what an optical size does. Superscripts stand on the superior figures'
//! baseline and subscripts on the inferior figures', so that `x₁ₙ` and `2ⁿ¹` sit on one line and have one colour.
//!
//! A letter whose base is not registered is left out; it switches on when the base appears. ⁿ and ⁱ are drawn by
//! hand in `digits`; ₙ and ᵢ are those, lowered, as an inferior figure is its superior lowered.

use rachis_kernel::{Draw, Glyph, Params, Registry, name_of, pt};

use crate::digits::{SMALL_H, inferior_shift, small_hair, small_stem, superior_base};

// ---------------------------------------------------------------------------------------------------------------
// the small master

/// How much wider than a plain reduction the small letters' sidebearings and counters are: a small letter needs
/// more white in proportion to stay open at the size it is read.
const WIDE_SB: f64 = 1.25;
const WIDE_COUNTER: f64 = 1.17;

/// The master the script letters are drawn with: `p` at the superior figures' size, with their strokes.
pub fn script_params(p: &Params) -> Params {
    let f = SMALL_H;
    let s = p.scaled(f);
    let (stem, hair) = (small_stem(p), small_hair(p));
    let (sb, sb_round) = (WIDE_SB * s.sb, WIDE_SB * s.sb_round);
    let counter = WIDE_COUNTER * s.counter;
    Params {
        stem,
        hair,
        cap_stem: stem * p.cap_stem / p.stem,
        cap_hair: hair * p.cap_hair / p.hair,
        dot: 0.5 * p.dot + 12.0, // as the dot of ⁱ
        over: 0.6 * p.over,      // as the small figures'
        sb,
        sb_round,
        cap_sb: WIDE_SB * s.cap_sb,
        fig_sb: WIDE_SB * s.fig_sb,
        counter,
        // the cell of n: two sidebearings, two stems and the counter, as in the full-size master
        width: 2.0 * sb + 2.0 * stem + counter,
        ..s
    }
}

/// Where a script letter stands: on the superiors' baseline or the inferiors'.
#[derive(Clone, Copy)]
enum Place {
    Sup,
    Sub,
}

fn baseline(p: &Params, place: Place) -> f64 {
    match place {
        Place::Sup => superior_base(p),
        Place::Sub => superior_base(p) + inferior_shift(p),
    }
}

/// The side margin the proportional family adds to a small letter's own advance: none, because the small
/// master's sidebearings are already wider in proportion than the text's, as a small size needs.
fn pad(_p: &Params) -> f64 {
    0.0
}

/// Add the outline of `small`, a glyph of the small master, standing on `y` and centred in the cell (the
/// fixed-pitch family) or with its own advance (the proportional one). `turned` turns it half round first.
fn place(g: &mut Draw, small: Glyph, sp: &Params, y: f64, turned: bool) {
    let p = g.p;
    let dx = if p.mono {
        (p.width - small.advance) / 2.0
    } else {
        g.glyph.advance = small.advance + 2.0 * pad(p);
        pad(p)
    };
    // The small glyph is sheared about its own slant origin and this one about the master's: move it along the
    // slant so that it leans from the same line as the superior figures.
    let slope = p.slant.to_radians().tan();
    let offset = pt(dx + slope * (y + sp.slant_origin() - p.slant_origin()), y);
    // a half turn about the point the shear leaves in place keeps an italic leaning the same way
    let centre = pt(small.advance / 2.0, sp.slant_origin());
    g.glyph.errors.extend(small.errors);
    for c in small.contours {
        let c = if turned { c.mapped(|z| centre + centre - z) } else { c };
        g.add_upright(c.mapped(|z| z + offset));
    }
}

/// The letter `base` drawn by its own program in the small master, at `place`.
fn script(g: &mut Draw, base: char, at: Place, turned: bool) {
    let p = g.p;
    let sp = script_params(p);
    match g.glyph_as(&name_of(base), &sp) {
        Some(small) => place(g, small, &sp, baseline(p, at), turned),
        None => g.glyph.errors.push(format!("cannot draw a script {base:?}: no such glyph")),
    }
}

// ---------------------------------------------------------------------------------------------------------------
// glyphs

/// The superscript letters and the letter each is drawn from. ᵍ is the single-storey g, which is Rachis's g; ᵋ
/// and ᶥ are the Latin open e and iota, whose shapes are the Greek ε and ι; ᶲ is the Latin phi, the Greek φ.
const SUPERIORS: [(char, char); 56] = [
    ('ⁿ', 'n'),
    ('ⁱ', 'i'),
    ('ᵃ', 'a'),
    ('ᵇ', 'b'),
    ('ᶜ', 'c'),
    ('ᵈ', 'd'),
    ('ᵉ', 'e'),
    ('ᶠ', 'f'),
    ('ᵍ', 'g'),
    ('ʰ', 'h'),
    ('ʲ', 'j'),
    ('ᵏ', 'k'),
    ('ˡ', 'l'),
    ('ᵐ', 'm'),
    ('ᵒ', 'o'),
    ('ᵖ', 'p'),
    ('ʳ', 'r'),
    ('ˢ', 's'),
    ('ᵗ', 't'),
    ('ᵘ', 'u'),
    ('ᵛ', 'v'),
    ('ʷ', 'w'),
    ('ˣ', 'x'),
    ('ʸ', 'y'),
    ('ᶻ', 'z'),
    ('ᵅ', 'α'),
    ('ᵝ', 'β'),
    ('ᵞ', 'γ'),
    ('ᵠ', 'φ'),
    ('ᵡ', 'χ'),
    ('ᵋ', 'ε'),
    ('ᶥ', 'ι'),
    ('ᶲ', 'φ'),
    ('ᶿ', 'θ'),
    ('ᴬ', 'A'),
    ('ᴮ', 'B'),
    ('ꟲ', 'C'),
    ('ᴰ', 'D'),
    ('ᴱ', 'E'),
    ('ꟳ', 'F'),
    ('ᴳ', 'G'),
    ('ᴴ', 'H'),
    ('ᴵ', 'I'),
    ('ᴶ', 'J'),
    ('ᴷ', 'K'),
    ('ᴸ', 'L'),
    ('ᴹ', 'M'),
    ('ᴺ', 'N'),
    ('ᴼ', 'O'),
    ('ᴾ', 'P'),
    ('ꟴ', 'Q'),
    ('ᴿ', 'R'),
    ('ᵀ', 'T'),
    ('ᵁ', 'U'),
    ('ⱽ', 'V'),
    ('ᵂ', 'W'),
];

/// The subscript letters and the letter each is drawn from.
const INFERIORS: [(char, char); 22] = [
    ('ₙ', 'n'),
    ('ᵢ', 'i'),
    ('ₐ', 'a'),
    ('ₑ', 'e'),
    ('ₒ', 'o'),
    ('ₓ', 'x'),
    ('ₕ', 'h'),
    ('ₖ', 'k'),
    ('ₗ', 'l'),
    ('ₘ', 'm'),
    ('ₚ', 'p'),
    ('ₛ', 's'),
    ('ₜ', 't'),
    ('ᵣ', 'r'),
    ('ᵤ', 'u'),
    ('ᵥ', 'v'),
    ('ⱼ', 'j'),
    ('ᵦ', 'β'),
    ('ᵧ', 'γ'),
    ('ᵨ', 'ρ'),
    ('ᵩ', 'φ'),
    ('ᵪ', 'χ'),
];

pub fn register(reg: &mut Registry) {
    reg.module("scripts");
    for (character, base) in SUPERIORS {
        if reg.get(&name_of(base)).is_some() {
            reg.ch(character, move |g: &mut Draw| script(g, base, Place::Sup, false));
        }
    }
    for (character, base) in INFERIORS {
        if reg.get(&name_of(base)).is_some() {
            reg.ch(character, move |g: &mut Draw| script(g, base, Place::Sub, false));
        }
    }
    // ₔ: the schwa is the e turned half round
    if reg.get(&name_of('e')).is_some() {
        reg.ch('ₔ', |g: &mut Draw| script(g, 'e', Place::Sub, true));
    }
}
