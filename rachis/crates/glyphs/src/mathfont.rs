//! The mathematics font: what Rachis Math has beyond the glyphs of the proportional family's Regular.
//!
//! A formula typesetter asks a font for more than text does. It sets a variable in the italic letter of the
//! Mathematical Alphanumeric Symbols block and a vector in the bold one; it places scripts by constants the font
//! states, moves a superscript right by a letter's italic correction and centres an accent where the font says the
//! letter's top is; and it asks for a delimiter, a radical or a sum in whatever size the formula inside needs.
//!
//! None of this is drawn again. A mathematical italic x is the program of x run with the italic master's
//! parameters, a bold one with the Bold's, a monospaced one with the fixed pitch's. The corrections are measured
//! from the outlines. The constants are counted in the master's own measurements (its axis, its rule, its
//! x-height), and where a constant has no such source it is the median of three sans-serif mathematics fonts at
//! this x-height (Fira Math, Lete Sans Math, Noto Sans Math; decision T30).

use rachis_kernel::geom::flatten;
use rachis_kernel::params::master;
use rachis_kernel::{Draw, Glyph, Params, Registry, name_of, pt};

use crate::operators::{big_bot, big_top, radical_between};

/// What the mathematics font adds, by glyph name. Lengths are in font units, unrounded.
#[derive(Clone, Debug, Default)]
pub struct MathFont {
    /// The glyphs beyond the face's own, to follow them in the font.
    pub glyphs: Vec<Glyph>,
    /// The italic correction of single glyphs.
    pub italic_corrections: Vec<(String, f64)>,
    /// Where the centre of an accent goes over a glyph, from the glyph's origin.
    pub top_accents: Vec<(String, f64)>,
    /// (glyph, its dotless form): what an accent is set on.
    pub dotless: Vec<(String, String)>,
    /// The constants of the `MATH` table, by their names in the OpenType specification.
    pub constants: Vec<(&'static str, f64)>,
    /// The glyphs that grow upwards: delimiters, the radical, the operators with a display size.
    pub vertical: Vec<Stretch>,
    /// The glyphs that grow sideways: arrows, braces over and under, wide accents.
    pub horizontal: Vec<Stretch>,
    /// The larger sizes and the pieces: scripts are placed against them by their own height.
    pub tall: Vec<String>,
    /// Glyphs of the face that the mathematics font draws otherwise, under the same name and code point.
    pub replaced: Vec<Glyph>,
    /// (glyph, its forms for a script and for a script of a script): the alternates of `ssty`.
    pub scripts: Vec<(String, Vec<String>)>,
}

/// A glyph that stretches in one direction: its ready-made sizes, smallest first, each with its length along
/// that direction, and the pieces a size of any length is assembled from (bottom to top, or left to right).
#[derive(Clone, Debug, Default)]
pub struct Stretch {
    pub glyph: String,
    pub variants: Vec<(String, f64)>,
    pub parts: Vec<Piece>,
    pub italic_correction: f64,
}

/// One piece of an assembly: its glyph, how much of its start and of its end is a straight stretch that may
/// overlap its neighbour, its length, and whether it may be repeated.
#[derive(Clone, Debug)]
pub struct Piece {
    pub glyph: String,
    pub start: f64,
    pub end: f64,
    pub advance: f64,
    pub extender: bool,
}

/// The styles of the Mathematical Alphanumeric Symbols that are the family's own letters with other parameters.
#[derive(Clone, Copy, Debug, PartialEq)]
enum Style {
    Bold,
    Italic,
    BoldItalic,
    /// The face is a sans serif: its "sans-serif" letters are its letters.
    Sans,
    SansBold,
    SansItalic,
    SansBoldItalic,
    Mono,
}

impl Style {
    /// The master whose parameters draw the style.
    fn master(self) -> &'static str {
        match self {
            Style::Bold | Style::SansBold => "Text Bold",
            Style::Italic | Style::SansItalic => "Text Italic",
            Style::BoldItalic | Style::SansBoldItalic => "Text Bold Italic",
            Style::Sans => "Text Regular",
            Style::Mono => "Mono Regular",
        }
    }
}

const LATIN: &str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
/// The order of a Greek block: the capitals with ϴ after Ρ, ∇, the lowercase with ς before σ, ∂ and the variant
/// forms.
const GREEK: &str = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡϴΣΤΥΦΧΨΩ∇αβγδεζηθικλμνξοπρςστυφχψω∂ϵϑϰϕϱϖ";
const DIGITS: &str = "0123456789";

/// The blocks: the code point of the first character, the characters in order, the style.
const BLOCKS: [(u32, &str, Style); 16] = [
    (0x1D400, LATIN, Style::Bold),
    (0x1D434, LATIN, Style::Italic),
    (0x1D468, LATIN, Style::BoldItalic),
    (0x1D5A0, LATIN, Style::Sans),
    (0x1D5D4, LATIN, Style::SansBold),
    (0x1D608, LATIN, Style::SansItalic),
    (0x1D63C, LATIN, Style::SansBoldItalic),
    (0x1D670, LATIN, Style::Mono),
    (0x1D6A8, GREEK, Style::Bold),
    (0x1D6E2, GREEK, Style::Italic),
    (0x1D71C, GREEK, Style::BoldItalic),
    (0x1D756, GREEK, Style::SansBold),
    (0x1D790, GREEK, Style::SansBoldItalic),
    (0x1D7CE, DIGITS, Style::Bold),
    (0x1D7E2, DIGITS, Style::Sans),
    (0x1D7EC, DIGITS, Style::SansBold),
];
/// The monospaced figures, after the blocks above (a constant array has one length).
const MONO_DIGITS: (u32, &str, Style) = (0x1D7F6, DIGITS, Style::Mono);

/// The white an italic correction leaves beyond the overhang, as the three reference fonts do (Noto Sans Math
/// adds exactly 20 units at its own size).
const CORRECTION_PAD: f64 = 20.0;

/// How far the ink of the upper half of `g` reaches past its advance: what a superscript has to clear.
fn overhang(g: &Glyph) -> Option<f64> {
    let (_, y0, _, y1) = g.bounds()?;
    let mid = (y0 + y1) / 2.0;
    let mut reach = f64::NEG_INFINITY;
    for c in &g.contours {
        for seg in &c.segs {
            for z in flatten(seg, 1.0) {
                if z.y >= mid {
                    reach = reach.max(z.x);
                }
            }
        }
    }
    reach.is_finite().then_some(reach - g.advance)
}

/// The constants of the table for the master `p`.
///
/// The axis is the master's (the middle of `+`, `−` and `=`), every rule is as thick as the operators' strokes,
/// and accents sit over the x-height or, flattened, over the capitals. The shifts and gaps of scripts,
/// fractions, stacks and limits are the medians of the three reference fonts at this x-height, rounded.
pub fn constants(p: &Params) -> Vec<(&'static str, f64)> {
    let rule = p.op;
    vec![
        ("ScriptPercentScaleDown", 70.0),
        ("ScriptScriptPercentScaleDown", 55.0),
        ("DelimitedSubFormulaMinHeight", 1500.0),
        ("DisplayOperatorMinHeight", 1300.0),
        ("MathLeading", 154.0),
        ("AxisHeight", p.axis),
        ("AccentBaseHeight", accent_base(p)),
        ("FlattenedAccentBaseHeight", p.cap),
        ("SubscriptShiftDown", 235.0),
        ("SubscriptTopMax", 0.8 * p.xh),
        ("SubscriptBaselineDropMin", 213.0),
        ("SuperscriptShiftUp", 393.0),
        ("SuperscriptShiftUpCramped", 277.0),
        ("SuperscriptBottomMin", 0.25 * p.xh),
        ("SuperscriptBaselineDropMax", 369.0),
        ("SubSuperscriptGapMin", 181.0),
        ("SuperscriptBottomMaxWithSubscript", 0.8 * p.xh),
        ("SpaceAfterScript", 42.0),
        ("UpperLimitGapMin", 154.0),
        ("UpperLimitBaselineRiseMin", 160.0),
        ("LowerLimitGapMin", 154.0),
        ("LowerLimitBaselineDropMin", 635.0),
        ("StackTopShiftUp", 480.0),
        ("StackTopDisplayStyleShiftUp", 709.0),
        ("StackBottomShiftDown", 492.0),
        ("StackBottomDisplayStyleShiftDown", 717.0),
        ("StackGapMin", 205.0),
        ("StackDisplayStyleGapMin", 339.0),
        ("StretchStackTopShiftUp", 307.0),
        ("StretchStackBottomShiftDown", 615.0),
        ("StretchStackGapAboveMin", 154.0),
        ("StretchStackGapBelowMin", 154.0),
        ("FractionNumeratorShiftUp", 480.0),
        ("FractionNumeratorDisplayStyleShiftUp", 709.0),
        ("FractionDenominatorShiftDown", 492.0),
        ("FractionDenominatorDisplayStyleShiftDown", 717.0),
        ("FractionNumeratorGapMin", rule),
        ("FractionNumDisplayStyleGapMin", 205.0),
        ("FractionRuleThickness", rule),
        ("FractionDenominatorGapMin", rule),
        ("FractionDenomDisplayStyleGapMin", 151.0),
        ("SkewedFractionHorizontalGap", 353.0),
        ("SkewedFractionVerticalGap", rule),
        ("OverbarVerticalGap", 154.0),
        ("OverbarRuleThickness", rule),
        ("OverbarExtraAscender", 53.0),
        ("UnderbarVerticalGap", 154.0),
        ("UnderbarRuleThickness", rule),
        ("UnderbarExtraDescender", 53.0),
        ("RadicalVerticalGap", 98.0),
        ("RadicalDisplayStyleVerticalGap", 152.0),
        ("RadicalRuleThickness", rule),
        ("RadicalExtraAscender", rule),
        // the degree of a root stands over the radical's short stroke, which is narrower here than in the
        // reference fonts: the radical is drawn back under the degree by most of that stroke's breadth
        ("RadicalKernBeforeDegree", 100.0),
        ("RadicalKernAfterDegree", -170.0),
        ("RadicalDegreeBottomRaisePercent", 64.0),
    ]
}

/// The mathematical alphanumerics the family can draw: each a letter's own program run with the parameters of
/// the master of its style, under the block's code point. A character Unicode left out of a block because it
/// had one already (the italic h is the Planck constant, U+210E) is skipped.
fn alphanumerics(registry: &Registry) -> Vec<Glyph> {
    let mut out = Vec::new();
    for (first, chars, style) in BLOCKS.iter().chain(std::iter::once(&MONO_DIGITS)) {
        let Some(p) = master(style.master()) else { continue };
        for (i, c) in chars.chars().enumerate() {
            let Some(target) = char::from_u32(first + i as u32) else { continue };
            // the holes of the blocks are unassigned code points
            if registry.for_char(target).is_some() || !is_assigned(target) {
                continue;
            }
            let Some(mut g) = registry.for_char(c).and_then(|spec| registry.flat(&spec.name, &p)) else {
                continue;
            };
            g.name = name_of(target);
            g.unicodes = vec![target as u32];
            out.push(g);
        }
    }
    out
}

/// Whether a code point of the Mathematical Alphanumeric Symbols is assigned: the block has holes where a
/// letter was encoded before it (ℎ, ℬ, ℰ and the like live in the Letterlike Symbols).
fn is_assigned(c: char) -> bool {
    !matches!(
        c as u32,
        0x1D455
            | 0x1D49D
            | 0x1D4A0
            | 0x1D4A1
            | 0x1D4A3
            | 0x1D4A4
            | 0x1D4A7
            | 0x1D4A8
            | 0x1D4AD
            | 0x1D4BA
            | 0x1D4BC
            | 0x1D4C4
            | 0x1D506
            | 0x1D50B
            | 0x1D50C
            | 0x1D515
            | 0x1D51D
            | 0x1D53A
            | 0x1D53F
            | 0x1D545
            | 0x1D547
            | 0x1D548
            | 0x1D549
            | 0x1D551
            | 0x1D6A6
            | 0x1D6A7
            | 0x1D7CC
            | 0x1D7CD
    )
}

// ---------------------------------------------------------------------------------------------------------------
// Sizes

/// The delimiters that grow: each is its own program run at the heights of [`HEIGHTS`].
const DELIMITERS: &str = "()[]{}|‖⟨⟩⌊⌋⌈⌉⟦⟧⟪⟫/\\";

/// The heights of a delimiter's sizes, from the bottom of the sign to its top. The master's own delimiter is 940
/// tall. The first two sizes are small steps, because a browser stretches a fence to whatever it holds: 1060
/// covers a letter with a descender and 1350 a capital with an accent, each about the axis (a parenthesis
/// around `y` is 13 per cent taller, not 28). From 1200 the steps are about a third of the master's, as in the
/// three reference fonts. The last is six lines of a matrix: taller than that, a delimiter is assembled, if it
/// can be.
const HEIGHTS: [f64; 14] =
    [1060.0, 1200.0, 1350.0, 1500.0, 1800.0, 2100.0, 2400.0, 2700.0, 3000.0, 3600.0, 4200.0, 4800.0, 5400.0, 6000.0];

/// A delimiter taller than the last size is assembled from the pieces Unicode has for building one over several
/// lines of a terminal, which the family draws already: (delimiter, its pieces from bottom to top with whether
/// each is an extender).
const ASSEMBLIES: [(char, &[(char, bool)]); 13] = [
    ('(', &[('⎝', false), ('⎜', true), ('⎛', false)]),
    (')', &[('⎠', false), ('⎟', true), ('⎞', false)]),
    ('[', &[('⎣', false), ('⎢', true), ('⎡', false)]),
    (']', &[('⎦', false), ('⎥', true), ('⎤', false)]),
    ('{', &[('⎩', false), ('⎪', true), ('⎨', false), ('⎪', true), ('⎧', false)]),
    ('}', &[('⎭', false), ('⎪', true), ('⎬', false), ('⎪', true), ('⎫', false)]),
    ('⌊', &[('⎣', false), ('⎢', true)]),
    ('⌈', &[('⎢', true), ('⎡', false)]),
    ('⌋', &[('⎦', false), ('⎥', true)]),
    ('⌉', &[('⎥', true), ('⎤', false)]),
    ('|', &[('|', true)]),
    ('‖', &[('‖', true)]),
    ('∫', &[('⌡', false), ('⎮', true), ('⌠', false)]),
];

/// The operators that stand before their operands and have a larger form in a displayed formula, and how many
/// times larger: the sums and their kin, then the integrals. At 2.4 times the text's the integral is 2256
/// units tall and reaches past a fraction of plain letters, which is what it has to bind; nine reference
/// fonts scaled to this x-height have 1938 to 2784 (`rachis math --refs`, decision T30).
const SUMS: &str = "∑∏∐⋃⋂⨆⨅⋁⋀⨁⨂⨀⨄⨉";
const INTEGRALS: &str = "∫∬∭∮∯∰";
const DISPLAY: [(&str, f64); 2] = [(SUMS, 1.65), (INTEGRALS, 2.4)];

/// The heights of the radical's sizes. The radical of the text is 804 tall. A radical is not assembled: its long
/// stroke leans, and a piece that repeats would have to stand upright.
const RADICALS: [f64; 12] =
    [1050.0, 1300.0, 1600.0, 1900.0, 2250.0, 2600.0, 3000.0, 3500.0, 4100.0, 4800.0, 5600.0, 6500.0];

/// The master `p` with its delimiters `height` tall, centred on the axis as they are in the master, and their
/// strokes a little heavier: 15 per cent at 3000 units and 25 at the tallest size, between what the reference
/// fonts do.
fn sized(p: &Params, height: f64) -> Params {
    let delim = height / (p.br_top - p.br_bot);
    let heavier = 1.0 + 0.068 * (delim - 1.0).min(3.7);
    Params {
        br_top: p.axis + height / 2.0,
        br_bot: p.axis - height / 2.0,
        delim,
        stem: p.stem * heavier,
        hair: p.hair * heavier,
        op: p.op * heavier,
        ..p.clone()
    }
}

/// `g` as a glyph of the mathematics font alone: under a name of its own, with no code point, no anchors and
/// its components resolved.
fn renamed(mut g: Glyph, name: String) -> Glyph {
    g.name = name;
    g.unicodes.clear();
    g.anchors.clear();
    g.skeletons.clear();
    g
}

fn moved(mut g: Glyph, dx: f64, dy: f64) -> Glyph {
    let by = pt(dx, dy);
    g.contours = g.contours.into_iter().map(|c| c.mapped(|z| z + by)).collect();
    g
}

fn height_of(g: &Glyph) -> f64 {
    g.bounds().map_or(0.0, |(_, y0, _, y1)| y1 - y0)
}

fn width_of(g: &Glyph) -> f64 {
    g.bounds().map_or(0.0, |(x0, _, x1, _)| x1 - x0)
}

/// The sizes of the delimiters and the pieces of their assemblies.
fn delimiters(registry: &Registry, p: &Params, font: &mut MathFont) {
    for c in DELIMITERS.chars() {
        let name = name_of(c);
        if registry.get(&name).is_none() {
            continue;
        }
        let mut stretch = Stretch { glyph: name.clone(), ..Stretch::default() };
        for (k, &height) in HEIGHTS.iter().enumerate() {
            let Some(g) = registry.flat(&name, &sized(p, height)) else { continue };
            let g = renamed(g, format!("{name}.v{}", k + 1));
            stretch.variants.push((g.name.clone(), height_of(&g)));
            font.tall.push(g.name.clone());
            font.glyphs.push(g);
        }
        font.vertical.push(stretch);
    }
    for (c, pieces) in ASSEMBLIES {
        let name = name_of(c);
        let Some(base) = registry.flat(&name, p) else { continue };
        let drawn: Option<Vec<Glyph>> = pieces.iter().map(|&(piece, _)| registry.flat(&name_of(piece), p)).collect();
        let (Some(drawn), Some((left, _, _, _))) = (drawn, base.bounds()) else { continue };
        // the pieces stand in a terminal's cell; here they stand where the delimiter does, in its advance
        let first = drawn.iter().filter_map(|g| g.bounds()).map(|b| b.0).fold(f64::INFINITY, f64::min);
        let mut parts = Vec::new();
        for (i, (g, &(_, extender))) in drawn.into_iter().zip(pieces).enumerate() {
            let mut g = renamed(moved(g, left - first, 0.0), format!("{name}.p{}", i + 1));
            g.advance = base.advance;
            let length = height_of(&g);
            // a piece joins its neighbours along its straight stem: an extender is all stem, a hook half
            let joint = if extender { 0.4 * length } else { 0.25 * length };
            let (bottom, top) = (i == 0, i + 1 == pieces.len());
            parts.push(Piece {
                glyph: g.name.clone(),
                start: if bottom && !extender { 0.0 } else { joint },
                end: if top && !extender { 0.0 } else { joint },
                advance: length,
                extender,
            });
            font.tall.push(g.name.clone());
            font.glyphs.push(g);
        }
        match font.vertical.iter_mut().find(|s| s.glyph == name) {
            Some(stretch) => stretch.parts = parts,
            None => font.vertical.push(Stretch { glyph: name, parts, ..Stretch::default() }),
        }
    }
}

/// How far the radical's own bar runs past the top of its long stroke: a stub for the typesetter's rule to
/// start from. The radical of the text has a long bar, because there nothing continues it.
const RADICAL_STUB: f64 = 36.0;

/// The radical between two heights as a formula needs it: its ink from the operators' margin on the left to its
/// advance on the right, where its bar ends. The typesetter draws the rule over the radicand from the top right
/// corner of the sign, so the sign's own bar must end exactly there, and soon, or the radicand stands off.
fn radical_of(p: &Params, yb: f64, yt: f64, name: String) -> Glyph {
    // the cell whose right end, less the 26 units the program keeps clear, is the stub's end: the long stroke's
    // top corner is at 392
    let width = 392.0 + RADICAL_STUB + 26.0;
    let q = Params { width, slant: 0.0, ..p.clone() };
    let mut g = Draw::new(&q, &name, width, true);
    radical_between(&mut g, yb, yt);
    let glyph = g.glyph;
    let Some((x0, _, x1, _)) = glyph.bounds() else { return glyph };
    let mut glyph = moved(glyph, p.op_l - x0, 0.0);
    glyph.advance = x1 - x0 + p.op_l;
    glyph.name = name;
    glyph.skeletons.clear();
    glyph
}

/// The radical and its sizes. The radical itself is drawn again for the formula, with the short bar.
fn radicals(registry: &Registry, p: &Params, font: &mut MathFont) {
    let c = '√';
    let name = name_of(c);
    if registry.get(&name).is_none() {
        return;
    }
    let (y0, y1) = (big_bot(p), big_top(p));
    let mut own = radical_of(p, y0, y1, name.clone());
    own.unicodes = vec![c as u32];
    font.replaced.push(own);
    let middle = (y0 + y1) / 2.0;
    let mut stretch = Stretch { glyph: name.clone(), ..Stretch::default() };
    for (k, &height) in RADICALS.iter().enumerate() {
        let g = radical_of(p, middle - height / 2.0, middle + height / 2.0, format!("{name}.v{}", k + 1));
        stretch.variants.push((g.name.clone(), height_of(&g)));
        font.tall.push(g.name.clone());
        font.glyphs.push(g);
    }
    font.vertical.push(stretch);
}

/// The display sizes of the operators that have one: the operator's own program run for the master drawn
/// larger, with strokes that grow by a sixth of what the size does, and set back on the axis.
///
/// A sum keeps the room its sign has in the text, larger. An integral is fitted to its ink, because its limits
/// are set beside it: the upper one where its advance ends, the lower one left of that by its lean. The white
/// at each side is the master's, times the root of the size (102 units), which is what the upper limit stands
/// off the hook; the reference fonts keep 32 to 135 there.
fn display_operators(registry: &Registry, p: &Params, font: &mut MathFont) {
    for (chars, times) in DISPLAY {
        let heavier = 1.0 + (times - 1.0) / 6.0;
        let mut q = p.scaled(times);
        (q.stem, q.hair, q.cap_stem, q.cap_hair, q.op) =
            (p.stem * heavier, p.hair * heavier, p.cap_stem * heavier, p.cap_hair * heavier, p.op * heavier);
        q.delim = times;
        for c in chars.chars() {
            let name = name_of(c);
            let Some(g) = registry.flat(&name, &q) else { continue };
            let mut g = renamed(moved(g, 0.0, p.axis - q.axis), format!("{name}.display"));
            if let Some((x0, _, x1, _)) = g.bounds().filter(|_| INTEGRALS.contains(c)) {
                let side = p.op_l * times.sqrt();
                g = moved(g, side - x0, 0.0);
                g.advance = x1 - x0 + 2.0 * side;
            }
            let size = (g.name.clone(), height_of(&g));
            font.tall.push(g.name.clone());
            font.glyphs.push(g);
            match font.vertical.iter_mut().find(|s| s.glyph == name) {
                Some(stretch) => stretch.variants.push(size),
                None => font.vertical.push(Stretch { glyph: name, variants: vec![size], ..Stretch::default() }),
            }
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Sideways

/// The arrows and bars a typesetter stretches over or under a label. One of any length is assembled from the
/// sign's own ends and a piece of its shaft (see `cut`); an arrow whose shaft is not level (⇝) has the sizes of
/// these spans instead.
const ARROWS: &str = "→←↔⇒⇐⇔↦↤↪↩⇀↼⇁↽↠↞↣↢⇝⇄⇆⇉⇇⇌⇋⟶⟵⟷⟹⟸⟺⟼=−";
const ARROW_SPANS: [f64; 4] = [3.3, 5.0, 7.5, 11.0];

/// The spans a sign is drawn across to be cut into the pieces of an assembly: long enough that the level run
/// between two of its shapes holds a joint for each and the piece that is repeated.
const ASSEMBLY_SPAN: f64 = 6.5;

/// The braces, brackets, parentheses and shells that lie over a group and those that lie under one. They have
/// no white at their ends: a typesetter fits them to the width of what they group. The curls of a brace and the
/// turns of a parenthesis grow with the root of its span, so a longer one has three sizes with larger curls,
/// and beyond them it is assembled from pieces with the curls of [`SPANNER_GROWN`] spans. An assembled
/// parenthesis is at least 702 units long and a brace 656, which is why the last size is 717.
const OVER: &str = "⏞⎴⏜⏠";
const UNDER: &str = "⏟⎵⏝⏡";
const SPANNER_SPANS: [f64; 3] = [1.2, 1.4, 1.6];
const SPANNER_GROWN: f64 = 1.69;

/// The white between a group and what lies over or under it. A typesetter that sets these as accents (Typst
/// does) takes it from where the glyph stands in the font: it puts the glyph's own baseline on the group's,
/// raised by what the group is taller than the accent base height. So every size of what lies over has its
/// lowest ink this far above the accent base height, and every size of what lies under hangs this far below
/// the baseline, whatever its curls and cusp do. Nine reference fonts scaled to this x-height keep 54 to 240
/// units above and 43 to 240 below (`rachis math --refs`, decision T30).
const SPANNER_CLEAR: f64 = 110.0;

/// The height a typesetter takes an accent to have been drawn over: the x-height, as for the accents of the
/// text.
fn accent_base(p: &Params) -> f64 {
    p.xh
}

/// How far up `g` has to move to lie over (or under) a group as [`SPANNER_CLEAR`] says.
fn clearance(g: &Glyph, p: &Params, over: bool) -> f64 {
    match g.bounds() {
        Some((_, y0, _, _)) if over => accent_base(p) + SPANNER_CLEAR - y0,
        Some((_, _, _, y1)) => -SPANNER_CLEAR - y1,
        None => 0.0,
    }
}

/// `g` moved up or down until it lies over (or under) a group as [`SPANNER_CLEAR`] says.
fn cleared(g: Glyph, p: &Params, over: bool) -> Glyph {
    let rise = clearance(&g, p, over);
    moved(g, 0.0, rise)
}

/// A sign drawn across [`ASSEMBLY_SPAN`] spans, with the curls of `grown` spans: what is cut into pieces.
fn drawn_long(registry: &Registry, p: &Params, name: &str, grown: f64) -> Option<Glyph> {
    let spec = registry.get(name)?;
    let width = ASSEMBLY_SPAN * (p.width - 2.0 * p.op_l) + 2.0 * p.op_l;
    let long = registry.trial(spec, p, width, grown);
    long.errors.is_empty().then_some(long)
}

/// The pieces a typesetter assembles the sign `name` of any length from: the sign drawn `long` and cut where
/// its level run begins and ends. A piece's ink starts at its origin and ends at its advance, except that the
/// first and the last piece keep `margin` of white outside them; every piece is raised by `rise`. Nothing if
/// the sign has no level run.
fn assembled(long: &Glyph, name: &str, margin: f64, rise: f64) -> Option<(Vec<Glyph>, Vec<Piece>)> {
    let cuts = crate::cut::pieces(long)?;
    let (mut glyphs, mut parts) = (Vec::new(), Vec::new());
    let last = cuts.len() - 1;
    for (i, cut) in cuts.iter().enumerate() {
        let piece = if cut.run { format!("{name}.run") } else { format!("{name}.p{}", i / 2 + 1) };
        let (before, after) = (if i == 0 { margin } else { 0.0 }, if i == last { margin } else { 0.0 });
        if !glyphs.iter().any(|g: &Glyph| g.name == piece) {
            let by = pt(before, rise);
            glyphs.push(Glyph {
                name: piece.clone(),
                advance: before + cut.length + after,
                contours: cut.contours.iter().map(|c| c.mapped(|z| z + by)).collect(),
                ..Glyph::default()
            });
        }
        parts.push(Piece {
            glyph: piece,
            start: cut.start,
            end: cut.end,
            advance: before + cut.length + after,
            extender: cut.run,
        });
    }
    Some((glyphs, parts))
}

/// The accents that are set over a group of letters and are shapes, and how many times as wide as the accent of
/// the text each of their sizes is.
const WIDE_ACCENTS: [char; 3] = ['\u{302}', '\u{30C}', '\u{303}'];
const ACCENT_TIMES: [f64; 5] = [1.7, 2.6, 3.8, 5.4, 7.6];

/// The accents that are a bar or an arrow over (or a bar under) a group: one of any length is assembled, as an
/// arrow on the line is. The macron of the text is drawn [`LONG_MACRON`] times as wide to be cut.
const LONG_ACCENTS: [char; 6] = ['\u{304}', '\u{305}', '\u{332}', '\u{20D6}', '\u{20D7}', '\u{20E1}'];
const LONG_MACRON: f64 = 10.0;

/// A sign's own program run across `span` spans of the master's cell, upright.
fn across(registry: &Registry, p: &Params, name: &str, span: f64) -> Option<Glyph> {
    let spec = registry.get(name)?;
    let width = span * (p.width - 2.0 * p.op_l) + 2.0 * p.op_l;
    Some(registry.trial(spec, p, width, span))
}

/// The sizes and the pieces of what stretches sideways.
fn sideways(registry: &Registry, p: &Params, font: &mut MathFont) {
    let kinds = [
        (ARROWS, &ARROW_SPANS[..], p.op_l, None),
        (OVER, &SPANNER_SPANS[..], 0.0, Some(true)),
        (UNDER, &SPANNER_SPANS[..], 0.0, Some(false)),
    ];
    for (chars, spans, margin, over) in kinds {
        for c in chars.chars() {
            let name = name_of(c);
            let Some(own) = registry.flat(&name, p) else { continue };
            let mut stretch = Stretch { glyph: name.clone(), ..Stretch::default() };
            // an arrow's ends are the same at every length; a brace's curls are those of a longer brace
            let grown = if over.is_some() { SPANNER_GROWN } else { ASSEMBLY_SPAN };
            let pieces = drawn_long(registry, p, &name, grown).and_then(|long| {
                let rise = over.map_or(0.0, |over| clearance(&long, p, over));
                assembled(&long, &name, margin, rise)
            });
            // an arrow that can be assembled needs no sizes: the assembly starts below the arrow's own length
            let spans = if pieces.is_some() && over.is_none() { &[][..] } else { spans };
            for (k, &span) in spans.iter().enumerate() {
                let Some(g) = across(registry, p, &name, span) else { continue };
                let Some((x0, _, x1, _)) = g.bounds() else { continue };
                // a size is only a size if it is longer than the sign itself
                if x1 - x0 <= width_of(&own) + 1.0 {
                    continue;
                }
                let mut g = renamed(moved(g, margin - x0, 0.0), format!("{name}.w{}", k + 1));
                g.advance = x1 - x0 + 2.0 * margin;
                stretch.variants.push((g.name.clone(), x1 - x0));
                font.glyphs.push(match over {
                    Some(over) => cleared(g, p, over),
                    None => g,
                });
            }
            if let Some((glyphs, parts)) = pieces {
                font.glyphs.extend(glyphs);
                stretch.parts = parts;
            }
            if !stretch.variants.is_empty() || !stretch.parts.is_empty() {
                font.horizontal.push(stretch);
            }
            // the sign itself stands where its sizes do: it is the size for a group no wider than it
            if let Some(over) = over {
                font.replaced.push(cleared(own, p, over));
            }
        }
    }
    // A size of an accent has its ink from its origin to its advance and is attached at its middle: a
    // typesetter measures it by its advance (LuaTeX) or by what the table says its length is, and both must be
    // the ink's. Only the accent of the text itself is a mark without an advance.
    for mark in WIDE_ACCENTS {
        let name = name_of(mark);
        let Some(low) = registry.flat(&name, p).and_then(|own| own.bounds()).map(|b| b.1) else { continue };
        let mut stretch = Stretch { glyph: name.clone(), ..Stretch::default() };
        for (k, &times) in ACCENT_TIMES.iter().enumerate() {
            let Some(g) = crate::latin::wide_mark(p, mark, times, &name) else { continue };
            let Some((x0, y0, x1, _)) = g.bounds() else { continue };
            // a wider tilde swings further: it is raised until it comes no nearer the letters than the text's
            let mut g = renamed(moved(g, -x0, (low - y0).max(0.0)), format!("{name}.w{}", k + 1));
            g.mark = false;
            g.advance = x1 - x0;
            font.top_accents.push((g.name.clone(), (x1 - x0) / 2.0));
            stretch.variants.push((g.name.clone(), x1 - x0));
            font.glyphs.push(g);
        }
        if !stretch.variants.is_empty() {
            font.horizontal.push(stretch);
        }
    }
    for mark in LONG_ACCENTS {
        let name = name_of(mark);
        let long = match mark {
            '\u{304}' => crate::latin::wide_mark(p, mark, LONG_MACRON, &name),
            _ => drawn_long(registry, p, &name, ASSEMBLY_SPAN),
        };
        if let Some((glyphs, parts)) = long.and_then(|long| assembled(&long, &name, 0.0, 0.0)) {
            font.glyphs.extend(glyphs);
            font.horizontal.push(Stretch { glyph: name, parts, ..Stretch::default() });
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Scripts

/// A script is set at 70 per cent and a script of a script at 55. A letter only made smaller is too light and
/// too tight to read there, so each letter has two more forms: the family's design for small print (the master
/// for 8 point), at a weight that gives the stroke of the reduced letter 0.85 and 0.78 of the text's. They are
/// the letters' own programs run for a point between the Regular and the Bold of that design.
const SCRIPT_WEIGHTS: [f64; 2] = [0.36, 0.79];

/// What has script forms beside the letters and figures: the signs a script is likely to hold.
const SCRIPT_SIGNS: &str = "+−=<>≤≥≠×·∗/|()[]{},.:;!?∞∈∂∇→←↦∘-*";

/// The primes. A typesetter sets a prime as a superscript: at the size of a script, and raised. So a prime's
/// form for a script is the prime of the text made larger by what a script is made smaller, and standing lower
/// by what a superscript is raised: reduced and raised, it is the prime of the text again. Its form for a
/// script of a script is larger by what that is made smaller, on the same foot, so that the prime of an
/// exponent is no smaller than the text's. All nine reference fonts do this: the first form of their prime is
/// 1.3 to 1.7 times as tall as the prime itself and stands 400 units lower.
const PRIMES: &str = "′″‴⁗‵‶‷";

/// The forms of the primes for scripts.
fn primes(glyphs: &[Glyph], font: &mut MathFont) {
    let constant = |name: &str| font.constants.iter().find(|c| c.0 == name).map(|c| c.1);
    let (Some(first), Some(second), Some(raise)) =
        (constant("ScriptPercentScaleDown"), constant("ScriptScriptPercentScaleDown"), constant("SuperscriptShiftUp"))
    else {
        return;
    };
    for c in PRIMES.chars() {
        let name = name_of(c);
        let Some(own) = glyphs.iter().find(|g| g.name == name) else { continue };
        let Some((_, foot, _, _)) = own.bounds() else { continue };
        // where the foot stands so that a script raised by `raise` has it where the text's prime has its own
        let low = (foot - raise) * 100.0 / first;
        let mut forms = Vec::new();
        for (level, percent) in [first, second].into_iter().enumerate() {
            let k = 100.0 / percent;
            let mut g = renamed(own.clone(), format!("{name}.s{}", level + 1));
            g.contours = g.contours.iter().map(|c| c.mapped(|z| pt(k * z.x, k * (z.y - foot) + low))).collect();
            g.components.clear();
            g.advance = k * own.advance;
            forms.push(g.name.clone());
            font.glyphs.push(g);
        }
        font.scripts.push((name, forms));
    }
}

/// The masters of the script forms: upright and italic, for a script and for a script of a script.
fn script_masters() -> Option<[(Params, Params); 2]> {
    let (regular, bold) = (master("Small Regular")?, master("Small Bold")?);
    let (italic, bold_italic) = (master("Small Italic")?, master("Small Bold Italic")?);
    Some(SCRIPT_WEIGHTS.map(|t| (regular.between(&bold, t), italic.between(&bold_italic, t))))
}

/// The script forms of the letters, figures and signs of `glyphs` (the face's own and the alphanumerics).
fn scripts(registry: &Registry, glyphs: &[Glyph], font: &mut MathFont) {
    let Some(masters) = script_masters() else { return };
    // an italic alphanumeric is its plain letter's program: find the plain letter of each
    let mut sources: Vec<(String, String, bool)> = Vec::new();
    let plain = |c: char| -> bool {
        c.is_ascii_alphanumeric() || ('Α'..='ω').contains(&c) || "ϵϑϰϕϱϖ".contains(c) || SCRIPT_SIGNS.contains(c)
    };
    for g in glyphs {
        let Some(c) = g.unicodes.first().and_then(|&u| char::from_u32(u)) else { continue };
        if plain(c) && registry.for_char(c).is_some() {
            sources.push((g.name.clone(), g.name.clone(), false));
        }
    }
    for (first, chars, style) in BLOCKS {
        if style != Style::Italic {
            continue;
        }
        for (i, c) in chars.chars().enumerate() {
            let (Some(target), Some(spec)) = (char::from_u32(first + i as u32), registry.for_char(c)) else {
                continue;
            };
            if is_assigned(target) && glyphs.iter().any(|g| g.name == name_of(target)) {
                sources.push((name_of(target), spec.name.clone(), true));
            }
        }
    }
    for (target, source, italic) in sources {
        let mut forms = Vec::new();
        for (level, (upright, slanted)) in masters.iter().enumerate() {
            let Some(mut g) = registry.flat(&source, if italic { slanted } else { upright }) else { continue };
            g.name = format!("{target}.s{}", level + 1);
            g.unicodes.clear();
            forms.push(g.name.clone());
            font.glyphs.push(g);
        }
        if forms.len() == masters.len() {
            font.scripts.push((target, forms));
        }
    }
}

/// How far the top of an integral stands to the right of its foot: its italic correction, by which a
/// typesetter moves the lower limit left of the upper one.
fn integral_lean(g: &Glyph) -> Option<f64> {
    let (_, y0, _, y1) = g.bounds()?;
    let reach = |from: f64, to: f64| {
        let mut x = f64::NEG_INFINITY;
        for c in &g.contours {
            for seg in &c.segs {
                for z in flatten(seg, 1.0) {
                    if z.y >= from && z.y <= to {
                        x = x.max(z.x);
                    }
                }
            }
        }
        x
    };
    let third = (y1 - y0) / 3.0;
    let (top, foot) = (reach(y1 - third, y1), reach(y0, y0 + third));
    (top.is_finite() && foot.is_finite()).then_some((top - foot).max(0.0))
}

/// Everything the mathematics font adds to the glyphs `base`, which the master `p` drew for the face.
pub fn build(registry: &Registry, p: &Params, base: &[Glyph]) -> MathFont {
    let mut font = MathFont { constants: constants(p), glyphs: alphanumerics(registry), ..MathFont::default() };
    // the script forms of the letters, before the sizes: a size has no script form
    let lettered: Vec<Glyph> = base.iter().chain(&font.glyphs).cloned().collect();
    scripts(registry, &lettered, &mut font);
    primes(base, &mut font);
    let measured = font.glyphs.len();
    delimiters(registry, p, &mut font);
    radicals(registry, p, &mut font);
    display_operators(registry, p, &mut font);
    sideways(registry, p, &mut font);
    for g in base.iter().chain(&font.glyphs[..measured]) {
        if g.mark {
            // an accent is centred by its own attachment point, which is where its ink's middle was drawn
            if let Some(at) = g.anchors.get("_top") {
                font.top_accents.push((g.name.clone(), at.x));
            }
            continue;
        }
        // a glyph that is another's under a second code point is measured as that one
        let own;
        let drawn = if g.contours.is_empty() && !g.components.is_empty() {
            match registry.flat(&g.name, p) {
                Some(flat) => {
                    own = flat;
                    &own
                }
                None => g,
            }
        } else {
            g
        };
        if let Some(over) = overhang(drawn).filter(|&over| over > 0.0) {
            font.italic_corrections.push((g.name.clone(), over + CORRECTION_PAD));
        }
        if let Some(top) = drawn.anchors.get("top") {
            font.top_accents.push((g.name.clone(), top.x));
        }
    }
    // an integral leans: its lower limit goes under its foot, not under its top
    let integrals: Vec<String> = INTEGRALS.chars().chain("∱∲∳".chars()).map(name_of).collect();
    let leaning: Vec<(String, f64)> = base
        .iter()
        .chain(&font.glyphs)
        .filter(|g| integrals.iter().any(|n| g.name == *n || g.name == format!("{n}.display")))
        .filter_map(|g| Some((g.name.clone(), integral_lean(g)?)))
        .collect();
    for (name, lean) in leaning {
        font.italic_corrections.retain(|(n, _)| *n != name);
        font.italic_corrections.push((name, lean));
    }
    for (dotted, dotless) in [('i', 'ı'), ('j', 'ȷ'), ('𝑖', '𝚤'), ('𝑗', '𝚥')] {
        let name = |c: char| {
            let n = name_of(c);
            (registry.get(&n).is_some() || font.glyphs.iter().any(|g| g.name == n)).then_some(n)
        };
        if let (Some(a), Some(b)) = (name(dotted), name(dotless)) {
            font.dotless.push((a, b));
        }
    }
    font
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeSet;
    use std::sync::OnceLock;

    use rachis_kernel::params::faces;

    use super::*;

    fn text() -> Params {
        master("Text Regular").expect("the proportional Regular")
    }

    /// The registry, the glyphs of the proportional face in its Regular, and the mathematics font built on them.
    fn built() -> &'static (Registry, Vec<Glyph>, MathFont) {
        static BUILT: OnceLock<(Registry, Vec<Glyph>, MathFont)> = OnceLock::new();
        BUILT.get_or_init(|| {
            let registry = crate::registry();
            let face =
                faces().into_iter().find(|f| !f.italic && !f.default_master().mono).expect("a proportional face");
            let p = text();
            let base: Vec<Glyph> =
                registry.specs.iter().filter(|s| face.has(s.module)).map(|s| registry.build(s, &p)).collect();
            let font = build(&registry, &p, &base);
            (registry, base, font)
        })
    }

    fn glyph(name: &str) -> &'static Glyph {
        let (_, base, font) = built();
        font.replaced
            .iter()
            .chain(&font.glyphs)
            .chain(base)
            .find(|g| g.name == name)
            .unwrap_or_else(|| panic!("no glyph {name}"))
    }

    fn stretch(list: &'static [Stretch], c: char) -> &'static Stretch {
        list.iter().find(|s| s.glyph == name_of(c)).unwrap_or_else(|| panic!("{c} does not stretch"))
    }

    #[test]
    fn every_constant_of_the_table_is_stated_once() {
        let names: Vec<&str> = constants(&text()).iter().map(|c| c.0).collect();
        assert_eq!(names.len(), 56);
        assert_eq!(names.iter().collect::<BTreeSet<_>>().len(), 56, "a constant is stated twice");
        let value = |name: &str| constants(&text()).iter().find(|c| c.0 == name).unwrap().1;
        // the rule of a fraction is the stroke of the minus it lies beside, on the minus's height
        assert_eq!(value("AxisHeight"), text().axis);
        assert_eq!(value("FractionRuleThickness"), text().op);
        assert_eq!(value("RadicalRuleThickness"), text().op);
    }

    #[test]
    fn a_mathematical_letter_is_the_letters_program_with_another_masters_parameters() {
        let (registry, _, _) = built();
        for (target, source, from) in [
            ('𝑥', 'x', "Text Italic"),
            ('𝐱', 'x', "Text Bold"),
            ('𝒙', 'x', "Text Bold Italic"),
            ('𝛼', 'α', "Text Italic"),
            ('𝟐', '2', "Text Bold"),
            ('𝚡', 'x', "Mono Regular"),
        ] {
            let drawn = registry.flat(&name_of(source), &master(from).unwrap()).unwrap();
            let g = glyph(&name_of(target));
            assert_eq!(g.unicodes, [target as u32]);
            assert_eq!((g.advance, g.bounds()), (drawn.advance, drawn.bounds()), "{target} is not {source} in {from}");
        }
        // the italic h is the Planck constant, which the family has already: the block's hole stays a hole
        let (_, _, font) = built();
        assert!(!font.glyphs.iter().any(|g| g.unicodes == [0x1D455]));
        assert_eq!(glyph(&name_of('𝚡')).advance, master("Mono Regular").unwrap().width);
    }

    #[test]
    fn a_delimiters_sizes_are_as_tall_as_they_say_and_stand_on_the_axis() {
        let (_, _, font) = built();
        let p = text();
        for c in "([{⟨|⌊⟦/".chars() {
            let s = stretch(&font.vertical, c);
            assert_eq!(s.variants.len(), HEIGHTS.len(), "{c}");
            let mut last = 0.0;
            for ((name, length), &height) in s.variants.iter().zip(&HEIGHTS) {
                let (x0, y0, x1, y1) = glyph(name).bounds().unwrap();
                assert!((y1 - y0 - height).abs() < 0.5, "{name} is {} tall, not {height}", y1 - y0);
                assert!((length - height).abs() < 0.5, "{name} says {length}");
                assert!(((y0 + y1) / 2.0 - p.axis).abs() < 0.5, "{name} is centred on {}", (y0 + y1) / 2.0);
                // a taller size is no narrower: a parenthesis bows further, a bracket's arms are longer
                assert!(x1 - x0 >= last - 0.5, "{name} is {} broad after {last}", x1 - x0);
                last = x1 - x0;
                assert!(font.tall.contains(name), "{name} is not among the tall shapes");
            }
        }
    }

    #[test]
    fn a_tall_delimiter_is_assembled_from_pieces_that_stand_where_it_does() {
        let (_, _, font) = built();
        for (c, extenders) in [
            ('(', vec![false, true, false]),
            (']', vec![false, true, false]),
            ('{', vec![false, true, false, true, false]),
            ('⌈', vec![true, false]),
            ('|', vec![true]),
        ] {
            let s = stretch(&font.vertical, c);
            assert_eq!(s.parts.iter().map(|part| part.extender).collect::<Vec<_>>(), extenders, "{c}");
            let base = glyph(&name_of(c));
            let (left, _, right, _) = base.bounds().unwrap();
            let (mut first, mut last) = (f64::INFINITY, f64::NEG_INFINITY);
            for part in &s.parts {
                let g = glyph(&part.glyph);
                let (x0, y0, x1, y1) = g.bounds().unwrap();
                assert_eq!(g.advance, base.advance, "{} has its delimiter's advance", part.glyph);
                assert!(
                    (part.advance - (y1 - y0)).abs() < 0.5,
                    "{} says {} and is {}",
                    part.glyph,
                    part.advance,
                    y1 - y0
                );
                assert!(part.start <= part.advance && part.end <= part.advance);
                (first, last) = (first.min(x0), last.max(x1));
            }
            // the pieces together are as broad as the delimiter and stand where it does
            assert!((first - left).abs() < 1.0 && (last - right).abs() < 1.0, "{c}: {first}..{last}, {left}..{right}");
            // the ends of the whole are not joints, unless the end is a stem that repeats
            let (bottom, top) = (s.parts.first().unwrap(), s.parts.last().unwrap());
            assert!(bottom.extender || bottom.start == 0.0, "{c} joins below its foot");
            assert!(top.extender || top.end == 0.0, "{c} joins above its head");
            // and every joint is long enough for the least overlap the table states
            for pair in s.parts.windows(2) {
                assert!(pair[0].end >= 20.0 && pair[1].start >= 20.0, "{c}: {} to {}", pair[0].glyph, pair[1].glyph);
            }
        }
    }

    #[test]
    fn the_radical_ends_where_its_bar_ends() {
        let (_, _, font) = built();
        let p = text();
        let s = stretch(&font.vertical, '√');
        assert_eq!(s.variants.len(), RADICALS.len());
        let names = std::iter::once(name_of('√')).chain(s.variants.iter().map(|v| v.0.clone()));
        let heights = std::iter::once(big_top(&p) - big_bot(&p)).chain(RADICALS);
        for (name, height) in names.zip(heights) {
            let g = glyph(&name);
            let (x0, y0, x1, y1) = g.bounds().unwrap();
            // the typesetter's rule starts at the advance, at the top of the sign: the sign's bar ends there
            assert!((g.advance - x1).abs() < 1e-6, "{name}: advance {}, ink to {x1}", g.advance);
            assert!((x0 - p.op_l).abs() < 1e-6, "{name} starts at {x0}");
            assert!((y1 - y0 - height).abs() < 0.5, "{name} is {} tall", y1 - y0);
        }
        // and the formula's radical is not the text's, whose bar is long
        let (registry, _, _) = built();
        let texts = registry.flat(&name_of('√'), &p).unwrap();
        assert!(glyph(&name_of('√')).advance < texts.advance - 100.0);
    }

    #[test]
    fn a_display_operator_is_larger_and_still_on_the_axis() {
        let (_, _, font) = built();
        let p = text();
        let least = constants(&p).iter().find(|c| c.0 == "DisplayOperatorMinHeight").unwrap().1;
        for (chars, times) in DISPLAY {
            for c in chars.chars() {
                let s = stretch(&font.vertical, c);
                let (name, length) = s.variants.last().unwrap();
                assert!(*length >= least, "{name} is {length} tall, under the {least} a display asks for");
                let (_, b0, _, b1) = glyph(&name_of(c)).bounds().unwrap();
                let (_, y0, _, y1) = glyph(name).bounds().unwrap();
                assert!(((y1 - y0) / (b1 - b0) - times).abs() < 0.03, "{name} is {} times {c}", (y1 - y0) / (b1 - b0));
                let off = |lo: f64, hi: f64| (lo + hi) / 2.0 - p.axis;
                assert!((off(y0, y1) - times * off(b0, b1)).abs() < 1.0, "{name} is {} off the axis", off(y0, y1));
            }
        }
        // an integral leans, in the text and more in a display: its lower limit moves left by that
        let lean = |name: &str| font.italic_corrections.iter().find(|c| c.0 == name).map(|c| c.1).unwrap_or(0.0);
        let integral = name_of('∫');
        assert!(lean(&integral) > 100.0, "{}", lean(&integral));
        assert!(lean(&format!("{integral}.display")) > 1.5 * lean(&integral));
        // the display integral's hooks grow with it, and it has the same white at both sides of its ink: its
        // upper limit is set where its advance ends
        for c in INTEGRALS.chars() {
            let g = glyph(&format!("{}.display", name_of(c)));
            let (x0, y0, x1, y1) = g.bounds().unwrap();
            assert!((x0 - (g.advance - x1)).abs() < 1e-6 && x0 > 0.0, "{}: {x0} and {}", g.name, g.advance - x1);
            assert!((x1 - x0) / (y1 - y0) >= 0.36, "{} is {} as broad as tall", g.name, (x1 - x0) / (y1 - y0));
        }
    }

    #[test]
    fn a_letter_has_two_forms_for_scripts_each_heavier_and_wider_set() {
        let (_, _, font) = built();
        let ink = |g: &Glyph| g.contours.iter().map(|c| c.area().abs()).sum::<f64>();
        for c in ['x', '𝑥', 'α', '𝛼', '2', '+'] {
            let name = name_of(c);
            let forms =
                &font.scripts.iter().find(|s| s.0 == name).unwrap_or_else(|| panic!("{c} has no script forms")).1;
            assert_eq!(forms, &[format!("{name}.s1"), format!("{name}.s2")]);
            let (own, first, second) = (glyph(&name), glyph(&forms[0]), glyph(&forms[1]));
            assert!(
                ink(first) > ink(own) && ink(second) > ink(first),
                "{c}: {} {} {}",
                ink(own),
                ink(first),
                ink(second)
            );
            assert!(first.advance > own.advance, "{c}: {} after {}", first.advance, own.advance);
        }
        // a size of a delimiter has no script form
        assert!(!font.scripts.iter().any(|s| s.0.contains(".v")));
    }

    #[test]
    fn a_prime_reduced_and_raised_as_a_superscript_is_the_prime_of_the_text() {
        let (_, _, font) = built();
        let value = |name: &str| font.constants.iter().find(|c| c.0 == name).unwrap().1;
        let (script, raise) = (value("ScriptPercentScaleDown") / 100.0, value("SuperscriptShiftUp"));
        for c in PRIMES.chars() {
            let name = name_of(c);
            let forms = &font.scripts.iter().find(|s| s.0 == name).unwrap_or_else(|| panic!("{c} has no forms")).1;
            let (own, first, second) = (glyph(&name), glyph(&forms[0]), glyph(&forms[1]));
            let (o, a, b) = (own.bounds().unwrap(), first.bounds().unwrap(), second.bounds().unwrap());
            // set as a script and raised, the first form covers what the prime of the text covers
            let set = |z: f64| raise + script * z;
            assert!(
                (set(a.1) - o.1).abs() < 1e-6 && (set(a.3) - o.3).abs() < 1e-6,
                "{c}: {} to {}",
                set(a.1),
                set(a.3)
            );
            assert!(
                (script * (a.2 - a.0) - (o.2 - o.0)).abs() < 1e-6
                    && (script * first.advance - own.advance).abs() < 1e-6
            );
            // the second stands on the same foot and is larger
            assert!((b.1 - a.1).abs() < 1e-6 && b.3 - b.1 > a.3 - a.1, "{c}: {b:?} after {a:?}");
        }
    }

    #[test]
    fn an_accent_has_wider_sizes_measured_by_their_advance() {
        let (_, _, font) = built();
        for c in WIDE_ACCENTS {
            let s = stretch(&font.horizontal, c);
            assert_eq!(s.variants.len(), ACCENT_TIMES.len(), "{c}");
            assert!(s.parts.is_empty(), "an accent that is a shape has no level run to repeat");
            let mut last = glyph(&name_of(c)).bounds().map_or(0.0, |b| b.2 - b.0);
            for (name, length) in &s.variants {
                let g = glyph(name);
                let (x0, _, x1, _) = g.bounds().unwrap();
                // LuaTeX chooses a size by its advance and centres it by half of that: both are the ink's
                assert!(x0.abs() < 1e-6 && (g.advance - x1).abs() < 1e-6, "{name}: {x0}..{x1} of {}", g.advance);
                assert!((length - g.advance).abs() < 1e-6 && g.advance > last, "{name}: {length} after {last}");
                last = g.advance;
                let at = font.top_accents.iter().find(|a| a.0 == *name).unwrap().1;
                assert!((at - g.advance / 2.0).abs() < 1e-6 && !g.mark, "{name} attaches at {at}");
            }
        }
    }

    #[test]
    fn a_bar_or_an_arrow_over_a_group_is_assembled_at_the_accents_own_height() {
        let (registry, _, font) = built();
        let p = text();
        for c in LONG_ACCENTS {
            let s = stretch(&font.horizontal, c);
            assert!(s.variants.is_empty(), "{c}");
            assert_eq!(s.parts.iter().map(|part| part.extender).collect::<Vec<_>>(), [false, true, false], "{c}");
            let own = registry.flat(&name_of(c), &p).unwrap().bounds().unwrap();
            let (contours, length) = laid(s, 0, crate::cut::JOINT);
            let (x0, y0, x1, y1) = Glyph { contours, ..Glyph::default() }.bounds().unwrap();
            assert!((y0 - own.1).abs() < 0.01 && (y1 - own.3).abs() < 0.01, "{c}: {y0}..{y1}, its own {own:?}");
            // no white at the ends, and the least assembly is not much longer than the accent itself
            assert!(x0.abs() < 1e-6 && (length - x1).abs() < 1e-6, "{c}: {x0}..{x1} of {length}");
            assert!(length <= own.2 - own.0 + 60.0, "{c}: the least is {length}, the accent {}", own.2 - own.0);
        }
    }

    /// The pieces of `s` laid end to end with every joint overlapped by `overlap` and the run taken `runs` times:
    /// the outlines, and the length.
    fn laid(s: &Stretch, runs: usize, overlap: f64) -> (Vec<rachis_kernel::Contour>, f64) {
        let (mut contours, mut x) = (Vec::new(), 0.0);
        let mut first = true;
        for part in &s.parts {
            for _ in 0..if part.extender { runs } else { 1 } {
                if !first {
                    x -= overlap;
                }
                first = false;
                let by = pt(x, 0.0);
                contours.extend(glyph(&part.glyph).contours.iter().map(|c| c.mapped(|z| z + by)));
                x += part.advance;
            }
        }
        (contours, x)
    }

    #[test]
    fn an_arrow_of_any_length_is_assembled_from_the_arrows_own_ends_and_shaft() {
        let (registry, _, font) = built();
        let p = text();
        for c in ARROWS.chars() {
            let s = stretch(&font.horizontal, c);
            if c == '⇝' {
                // its shaft is a wave: it has sizes and no pieces
                assert!(s.parts.is_empty() && s.variants.len() >= 3, "{c}");
                continue;
            }
            assert!(s.variants.is_empty(), "{c} has sizes beside its pieces");
            let kinds: Vec<bool> = s.parts.iter().map(|part| part.extender).collect();
            assert_eq!(kinds, [false, true, false], "{c}");
            let (left, run, right) = (&s.parts[0], &s.parts[1], &s.parts[2]);
            assert_eq!(
                (left.start, left.end, right.start, right.end),
                (0.0, crate::cut::JOINT, crate::cut::JOINT, 0.0)
            );
            assert_eq!((run.start, run.end, run.advance), (crate::cut::RUN, crate::cut::RUN, crate::cut::RUN));
            // the least assembled arrow is no longer than the arrow of the text: no length is left out
            let own = registry.flat(&name_of(c), &p).unwrap();
            let least = left.advance + right.advance - crate::cut::JOINT;
            assert!(least <= own.advance + 1.0, "{c}: the least assembly is {least}, the arrow {}", own.advance);
            // laid out with no run, the pieces are the arrow of the text again, to the height of its ink and
            // the white at its sides
            let (contours, length) = laid(s, 0, crate::cut::JOINT);
            let whole = Glyph { contours, ..Glyph::default() };
            let (x0, y0, x1, y1) = whole.bounds().unwrap();
            let (_, b0, _, b1) = own.bounds().unwrap();
            assert!((y0 - b0).abs() < 0.01 && (y1 - b1).abs() < 0.01, "{c}: {y0}..{y1}, the arrow {b0}..{b1}");
            assert!((x0 - p.op_l).abs() < 2.5 && (length - x1 - p.op_l).abs() < 2.5, "{c}: {x0}, {}", length - x1);
        }
    }

    #[test]
    fn a_brace_of_any_length_is_assembled_and_its_cusp_stays_in_the_middle() {
        let (_, _, font) = built();
        for (chars, kinds) in [("⏞⏟", vec![false, true, false, true, false]), ("⎴⎵⏜⏝⏠⏡", vec![false, true, false])]
        {
            for c in chars.chars() {
                let s = stretch(&font.horizontal, c);
                assert_eq!(s.parts.iter().map(|part| part.extender).collect::<Vec<_>>(), kinds, "{c}");
                // no white at the ends, and the two ends are each other's mirror image in length
                let (first, last) = (&s.parts[0], &s.parts[s.parts.len() - 1]);
                assert!((first.advance - last.advance).abs() <= 2.0, "{c}: {} and {}", first.advance, last.advance);
                let (x0, _, x1, _) = glyph(&first.glyph).bounds().unwrap();
                assert!(x0.abs() < 1e-6 && (x1 - first.advance).abs() < 1e-6, "{c}: {x0}..{x1} of {}", first.advance);
                // every length from the last size on can be assembled: with no run the pieces are no longer
                // than the last size, and each run adds less than the joints can take up
                let fixed: f64 = s.parts.iter().filter(|part| !part.extender).map(|part| part.advance).sum();
                let joints = (s.parts.iter().filter(|part| !part.extender).count() - 1) as f64;
                let least = fixed - joints * crate::cut::JOINT;
                let longest = s.variants.last().map_or(0.0, |v| v.1);
                assert!(least <= longest + 1.0, "{c}: the least assembly is {least}, the last size {longest}");
                // the sizes grow from the sign itself
                let mut before = glyph(&s.glyph).bounds().map_or(0.0, |b| b.2 - b.0);
                for (name, length) in &s.variants {
                    assert!(*length > before, "{name} is {length} after {before}");
                    before = *length;
                }
                // all pieces of one sign stand at one height: where they join, their cross-sections agree
                let (contours, _) = laid(s, 1, crate::cut::JOINT);
                let whole = Glyph { contours, ..Glyph::default() };
                let (_, y0, _, y1) = whole.bounds().unwrap();
                let over = OVER.contains(c);
                let p = text();
                if over {
                    assert!((y0 - (p.xh + SPANNER_CLEAR)).abs() < 1e-6, "{c} comes down to {y0}");
                } else {
                    assert!((y1 + SPANNER_CLEAR).abs() < 1e-6, "{c} reaches up to {y1}");
                }
            }
        }
        // the cusp of a brace is the middle piece, with a run on each side: both are repeated equally
        let brace = stretch(&font.horizontal, '⏞');
        let (cusp, y_cusp) = (&brace.parts[2], glyph(&brace.parts[2].glyph).bounds().unwrap().3);
        assert_eq!((cusp.start, cusp.end), (crate::cut::JOINT, crate::cut::JOINT));
        assert!(y_cusp > glyph(&brace.parts[0].glyph).bounds().unwrap().3 + 50.0);
    }

    #[test]
    fn what_lies_over_or_under_a_group_stands_clear_of_it_at_every_size() {
        let (_, _, font) = built();
        let p = text();
        for (chars, over) in [(OVER, true), (UNDER, false)] {
            for c in chars.chars() {
                let s = stretch(&font.horizontal, c);
                assert_eq!(s.variants.len(), SPANNER_SPANS.len(), "{c}");
                // a size has no white at its ends: it is fitted to what it groups
                for (name, _) in &s.variants {
                    let g = glyph(name);
                    let (x0, _, x1, _) = g.bounds().unwrap();
                    assert!(x0.abs() < 1e-6 && (g.advance - x1).abs() < 1e-6, "{name}: {x0}..{x1} of {}", g.advance);
                }
                for name in std::iter::once(&s.glyph).chain(s.variants.iter().map(|v| &v.0)) {
                    let (_, y0, _, y1) = glyph(name).bounds().unwrap();
                    if over {
                        assert!((y0 - (p.xh + SPANNER_CLEAR)).abs() < 1e-6, "{name} comes down to {y0}");
                    } else {
                        assert!((y1 + SPANNER_CLEAR).abs() < 1e-6, "{name} reaches up to {y1}");
                    }
                }
            }
        }
        // and no size of an accent comes nearer the letters than the accent of the text does
        let (registry, _, _) = built();
        for mark in WIDE_ACCENTS {
            let own = registry.flat(&name_of(mark), &p).unwrap().bounds().unwrap().1;
            for (name, _) in &stretch(&font.horizontal, mark).variants {
                let low = glyph(name).bounds().unwrap().1;
                assert!(low >= own - 1e-6, "{name} comes down to {low}, the accent of the text to {own}");
            }
        }
    }

    #[test]
    fn every_glyph_the_font_adds_has_a_name_of_its_own_and_no_error() {
        let (_, base, font) = built();
        let mut names: BTreeSet<&str> = base.iter().map(|g| g.name.as_str()).collect();
        for g in &font.glyphs {
            assert!(g.errors.is_empty(), "{}: {:?}", g.name, g.errors);
            assert!(names.insert(&g.name), "{} is there twice", g.name);
            assert!(g.components.is_empty(), "{} still has components", g.name);
        }
        for g in &font.replaced {
            assert!(base.iter().any(|b| b.name == g.name && b.unicodes == g.unicodes), "{} replaces nothing", g.name);
        }
        // every name the tables use is a glyph
        let known = |name: &String| names.contains(name.as_str());
        assert!(font.italic_corrections.iter().chain(&font.top_accents).all(|e| known(&e.0)));
        assert!(font.tall.iter().all(known));
        assert!(font.scripts.iter().all(|s| known(&s.0) && s.1.iter().all(known)));
        for s in font.vertical.iter().chain(&font.horizontal) {
            assert!(
                known(&s.glyph) && s.variants.iter().all(|v| known(&v.0)) && s.parts.iter().all(|x| known(&x.glyph))
            );
        }
    }
}
