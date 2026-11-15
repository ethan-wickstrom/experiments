//! The room signs take in the proportional family.
//!
//! In the fixed-pitch family every sign has the cell. In the proportional family the signs of arithmetic and
//! comparison still do: they are as wide as a figure, so columns align and `+`, `=` and `<` are one size. Every
//! other sign has the room its shape wants. An arrow is longer than a letter is wide, a relation between sets is
//! wider than a plus, and a dot or a bar needs no cell at all.
//!
//! A sign's [`Room`] says how far its program draws across, counted in spans of the master's cell (the span is
//! the cell without the operators' margins), and how much white stands at each side of its ink. The programs are
//! the fixed pitch's: they draw across the span they are given, and what should grow with it grows by
//! [`Params::grown`]. The spans were read from three sans-serif mathematics fonts that grew out of text faces
//! (Fira Math, Lete Sans Math, Noto Sans Math) at Rachis's x-height, and gathered into a few classes (decision
//! T27).

use rachis_kernel::{Fit, Params, Registry, Spec};

/// How a sign stands in the proportional family.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Room {
    /// How far the program draws across, in spans of the master's cell.
    pub span: f64,
    /// The white at each side of the ink, in operators' margins (`Params::op_l`).
    pub margin: f64,
}

const fn room(span: f64, margin: f64) -> Option<Room> {
    Some(Room { span, margin })
}

/// A sign drawn across `span` spans, between the operators' margins.
const fn wide(span: f64) -> Option<Room> {
    room(span, 1.0)
}

/// The span of an arrow: the three reference fonts draw `→` 1.83 to 2.05 spans long.
pub const ARROW: f64 = 1.9;
/// The span of a long arrow, twice the reference fonts' `→` less a little, as theirs is.
pub const LONG_ARROW: f64 = 3.3;
/// The span of a relation between sets, a cup, a wedge.
pub const RELATION: f64 = 1.3;
/// The span of a circled or boxed operator, a tack, a turnstile.
pub const ROUND: f64 = 1.45;
/// The span of an operator that stands before its operands (the sum, the product).
pub const BIG: f64 = 1.5;
/// The span of a bullet, a status mark or a geometric shape.
pub const SHAPE: f64 = 1.25;

/// The room of the sign `c`; `None` for a sign that keeps the master's cell.
#[rustfmt::skip]
pub fn of(c: char) -> Option<Room> {
    match c {
        // dots, rings and small signs: their own ink between the margins
        '⋅' | '∙' | '∘' | '∊' | '∍' | '⋴' | '⋼' | '⋷' | '⋾' | '∁' | '≬' | '∎' | '∔' | '⊺' | '⊹' | '⊦' | '⊧' | '⨟'
        | '⟊' | '⟠' | '≀' | '∬' | '∭' | '∯' | '∰' => wide(1.0),
        '∗' => wide(1.4),
        // bars: relations, so they stand a little further from their neighbours
        '∣' | '∥' | '‖' | '∶' | '⋮' | '⦂' => room(1.0, 1.5),
        '∤' | '∦' => wide(1.0),

        // relations between sets, cups and caps, wedges, and their square and triangular kin
        '⊂' | '⊃' | '∈' | '∋' | '∉' | '∌' | '⊄' | '⊅' | '⊆' | '⊇' | '⊈' | '⊉' | '⊊' | '⊋' | '⋐' | '⋑' | '⟃' | '⟄'
        | '⋳' | '⋻' | '⋵' | '⋶' | '⋽' | '⋸' | '⋹' | '⋲' | '⋺' | '⋿'
        | '∪' | '∩' | '⊎' | '⊔' | '⊓' | '⊌' | '⊍' | '⋒' | '⋓' | '⋔' | '⟒' | '⫙'
        | '∧' | '∨' | '⊻' | '⊼' | '⊽' | '⋎' | '⋏' | '⟑' | '⟇' | '⟓' | '⟔'
        | '⊏' | '⊐' | '⊑' | '⊒' | '⋢' | '⋣' | '⋤' | '⋥'
        | '⊲' | '⊳' | '⊴' | '⊵' | '⋪' | '⋫' | '⋬' | '⋭'
        | '∝' | '≔' | '≕' | '∴' | '∵' | '∷' | '⋰' | '⋱' | '∹' | '⋆' | '∿' | '∾'
        | '∟' | '⊾' | '⟀' | '∠' | '∡' | '∢' | '⊿' | '√' | '∛' | '∜' | '∖' | '∕' => wide(RELATION),
        '⟈' | '⟉' => wide(1.7),

        // tacks and turnstiles, circled and boxed operators, bowties
        '⊤' | '⊥' | '⊢' | '⊣' | '⊨' | '⫤' | '⫪' | '⫫' | '⟂' | '⟘' | '⟙'
        | '⊕' | '⊖' | '⊗' | '⊘' | '⊙' | '⊚' | '⊛' | '⊜' | '⊝' | '⦾' | '⦿' | '∅'
        | '⊞' | '⊟' | '⊠' | '⊡' | '⧄' | '⧅' | '⧆' | '⧇'
        | '⋈' | '⋉' | '⋊' | '⋋' | '⋌' | '⋯' | '⧺' | '⟎' | '⟏' | '⟡' | '⟢' | '⟣' | '⊸' | '⟜' => wide(ROUND),
        '⊩' | '⊪' | '⊫' | '⊬' | '⊭' | '≪' | '≫' | '⩴' => wide(1.7),
        '⟤' | '⟥' | '⟐' | '⟁' => wide(1.6),
        '⊮' | '⊯' | '⊶' | '⊷' | '⟕' | '⟖' | '⟋' | '⟍' => wide(1.9),
        '⋘' | '⋙' | '⟝' | '⟞' | '⟗' | '⨝' => wide(2.2),
        '⟚' | '⟛' => wide(2.8),
        '∞' => room(1.55, 0.6),

        // the operators that stand before their operands
        '∑' | '∏' | '∐' | '⋀' | '⋁' | '⋂' | '⋃' | '⨄' | '⨅' | '⨆' | '⨿' | '⨀' | '⨁' | '⨂' | '⨉' => wide(BIG),

        // arrows along the line
        '→' | '←' | '↔' | '↛' | '↚' | '↮' | '↝' | '↜' | '↭' | '⇝' | '⇜' | '↣' | '↢' | '↠' | '↞' | '↦' | '↤' | '↪'
        | '↩' | '↼' | '↽' | '⇀' | '⇁' | '⇐' | '⇒' | '⇔' | '⇍' | '⇏' | '⇎' | '⤆' | '⤇' | '⇚' | '⇛' | '⭅' | '⭆'
        | '⇠' | '⇢' | '⇤' | '⇥' | '⇴' | '⇷' | '⇸' | '⇹' | '⇺' | '⇻' | '⇼' | '⇽' | '⇾' | '⇿'
        | '⇄' | '⇆' | '⇉' | '⇇' | '↹' | '⇌' | '⇋' | '⥤' => wide(ARROW),
        '⟵' | '⟶' | '⟷' | '⟻' | '⟼' | '⟸' | '⟹' | '⟺' | '⟽' | '⟾' | '⟿' => wide(LONG_ARROW),
        // arrows up and down are as long, and stand in the white a figure has
        '↑' | '↓' | '↕' | '↟' | '↡' | '↥' | '↧' | '↾' | '↿' | '⇂' | '⇃' | '⇑' | '⇓' | '⇕' | '⇞' | '⇟' | '⇡' | '⇣'
        | '⇈' | '⇊' | '⇅' | '⇵' | '↨' => room(ARROW, 1.35),
        '↗' | '↖' | '↙' | '↘' | '⇖' | '⇗' | '⇘' | '⇙' => wide(ARROW),
        // arrows that turn, and the drawn ones
        '↳' | '↲' | '↱' | '↰' | '↴' | '↵' | '↶' | '↷' | '↺' | '↻' | '↸' | '⇱' | '⇲' => wide(ROUND),
        '⇨' | '⇦' | '⇧' | '⇩' | '⇳' | '⇪' | '⇫' | '⇬' | '⇭' | '⇰' | '➡' | '⬅' | '⬆' | '⬇' | '⬌' | '⬍' | '➔' | '➜'
        | '➝' | '➞' | '➛' => wide(BIG),

        // signs of prose that are wider than a figure in every text face
        '@' => room(1.5, 0.5),
        '%' => room(1.35, 0.6),
        '‰' => room(1.9, 0.6),
        '‱' => room(2.5, 0.6),
        '&' => room(1.25, 0.6),
        '©' | '®' | '℗' => room(1.3, 0.6),
        '™' => room(1.4, 0.4),
        '№' => room(1.35, 0.6),
        '§' | '‼' => room(1.0, 0.9),
        '⁇' | '⁈' | '⁉' => room(1.4, 0.9),
        '½' | '¼' | '¾' | '⅐' | '⅑' | '⅓' | '⅔' | '⅕' | '⅖' | '⅗' | '⅘' | '⅙' | '⅚' | '⅛' | '⅜' | '⅝' | '⅞' | '⅒' | '⅟'
        | '↉' => room(1.25, 0.5),

        // delimiters stand as close to what they hold as brackets do
        '⌈' | '⌉' | '⌊' | '⌋' | '⟦' | '⟧' | '⟬' | '⟭' | '⦃' | '⦄' | '⟨' | '⟩' | '⟪' | '⟫' | '⟮' | '⟯' | '⦇' | '⦈'
        | '⌜' | '⌝' | '⌞' | '⌟' => room(1.0, 0.8),
        _ => None,
    }
}

/// The fit of the sign `spec` in the master `p` of the proportional family: the cell its program draws in, and
/// what is taken from or added to its sides so that its ink stands between the margins of its room. `None` for a
/// sign that keeps the master's cell.
pub fn fit(registry: &Registry, spec: &Spec, p: &Params) -> Option<Fit> {
    if spec.opt.mark {
        return None;
    }
    let listed = spec.unicodes.iter().find_map(|&c| char::from_u32(c).and_then(of));
    // bullets, status marks and geometric shapes are all a quarter larger than in the fixed pitch's cell
    let room = listed.or_else(|| (spec.module == "symbols").then_some(Room { span: SHAPE, margin: 1.0 }))?;
    let width = room.span * (p.width - 2.0 * p.op_l) + 2.0 * p.op_l;
    let trial = registry.trial(spec, p, width);
    if trial.contours.is_empty() {
        // another sign under a second code point: it comes with that sign's room
        return None;
    }
    let (x0, x1) = registry.ends(&trial, p)?;
    let side = room.margin * p.op_l;
    Some(Fit { width, left: side - x0, right: side - (width - x1) })
}

#[cfg(test)]
mod tests {
    use rachis_kernel::name_of;
    use rachis_kernel::params::masters;

    use super::*;

    /// The advance of a character's glyph in the master `p`, and the box of its ink.
    fn drawn(r: &Registry, c: char, p: &Params) -> (f64, (f64, f64, f64, f64)) {
        let g = r.flat(&name_of(c), p).unwrap_or_else(|| panic!("no glyph for {c}"));
        (g.advance, g.bounds().unwrap_or_else(|| panic!("{c} has no ink")))
    }

    #[test]
    fn a_sign_has_the_cell_in_the_fixed_pitch_family_and_its_own_room_in_the_other() {
        let r = crate::registry();
        for p in masters().into_iter().filter(|p| !p.italic()) {
            let span = p.width - 2.0 * p.op_l;
            // to a hundredth of a unit: the box of a curve is found by solving for its extremes
            let near = |a: f64, b: f64| (a - b).abs() < 0.01;
            // the signs of arithmetic and comparison are as wide as a figure in both families
            for c in "+−=<>×÷±≤≥≠≈≡".chars() {
                assert!(near(drawn(&r, c, &p).0, p.width), "{c} in {}: {}", p.name, drawn(&r, c, &p).0);
            }
            let (arrow, (ax0, _, ax1, _)) = drawn(&r, '→', &p);
            let (element, (ex0, ey0, ex1, ey1)) = drawn(&r, '∈', &p);
            let (up, (ux0, uy0, ux1, uy1)) = drawn(&r, '↑', &p);
            let (dot, (dx0, _, dx1, _)) = drawn(&r, '⋅', &p);
            if p.mono {
                for (c, advance) in [('→', arrow), ('∈', element), ('↑', up), ('⋅', dot)] {
                    assert!(near(advance, p.width), "{c} in {}: {advance}", p.name);
                }
                continue;
            }
            // an arrow draws across its span and stands between the operators' margins
            assert!(near(ax1 - ax0, ARROW * span), "→ in {}: ink {}", p.name, ax1 - ax0);
            assert!(near(ax0, p.op_l) && near(arrow - ax1, p.op_l), "→ in {}: {ax0} {}", p.name, arrow - ax1);
            // a relation between sets is wider than a plus and as much taller as it is wider
            assert!(near(ex1 - ex0, RELATION * span), "∈ in {}: ink {}", p.name, ex1 - ex0);
            assert!(near(element, RELATION * span + 2.0 * p.op_l), "∈ in {}: {element}", p.name);
            assert!(near(ey1 - ey0, RELATION * 2.0 * (185.0 + 0.5 * p.op)), "∈ in {}: {} tall", p.name, ey1 - ey0);
            // an arrow up is as long as an arrow along the line, and has the white of its room at its sides
            assert!(near(uy1 - uy0, ax1 - ax0), "↑ in {}: {} long, → {}", p.name, uy1 - uy0, ax1 - ax0);
            assert!(near(up, ux1 - ux0 + 2.0 * 1.35 * p.op_l), "↑ in {}: {up}", p.name);
            // a dot takes the room of its ink, not a cell
            assert!(near(dot, dx1 - dx0 + 2.0 * p.op_l) && dot < 0.6 * p.width, "⋅ in {}: {dot}", p.name);
        }
    }

    #[test]
    fn a_sign_under_a_second_code_point_has_the_first_ones_room() {
        let r = crate::registry();
        for p in masters() {
            let (a, b) = (r.flat(&name_of('↺'), &p).unwrap(), r.flat(&name_of('⟲'), &p).unwrap());
            assert_eq!((a.advance, a.bounds()), (b.advance, b.bounds()), "{}", p.name);
        }
    }

    #[test]
    fn turnstiles_are_one_height_whatever_their_width() {
        let r = crate::registry();
        for p in masters().into_iter().filter(|p| !p.italic()) {
            let height = |c: char| {
                let (_, (_, y0, _, y1)) = drawn(&r, c, &p);
                y1 - y0
            };
            for c in ['⊨', '⊩', '⊫', '⟚'] {
                assert!((height(c) - height('⊢')).abs() < 1e-6, "{c} in {}: {} and {}", p.name, height(c), height('⊢'));
            }
        }
    }
}
