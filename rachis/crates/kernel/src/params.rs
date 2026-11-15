//! The parameters of a master: every measurement a glyph program may read.
//!
//! Lengths are in font units, 1000 to the em. A master is a point in the design space of one face: a weight, an
//! optical size, upright or italic, in the fixed-pitch family (every advance 600) or the proportional one. A
//! variable font interpolates between the masters of a face, so everything that differs between them must be a
//! number here, never a branch in a glyph program. The two families are different fonts, so a program may branch
//! on [`Params::mono`].

#[derive(Clone, Debug, PartialEq)]
pub struct Params {
    pub name: &'static str,
    pub wght: f64,
    /// The size in points the master is drawn for.
    pub opsz: f64,
    /// Degrees; positive leans right.
    pub slant: f64,
    /// Fixed pitch: every glyph has the advance `width`.
    pub mono: bool,

    pub upm: f64,
    /// The advance of the cell: of every glyph in the fixed-pitch family, and of figures, operators and symbols in
    /// the proportional one. A glyph program reads its own advance here.
    pub width: f64,

    // heights
    pub cap: f64,
    pub xh: f64,
    pub asc: f64,
    pub desc: f64,
    /// Overshoot of round shapes past a flat one.
    pub over: f64,
    /// The height operators are centred on.
    pub axis: f64,
    /// Top of brackets, braces, parentheses and the bar.
    pub br_top: f64,
    pub br_bot: f64,
    /// Top of the line: box drawing and blocks fill line_bot … line_top.
    pub line_top: f64,
    pub line_bot: f64,

    // strokes
    /// Vertical strokes of the lowercase.
    pub stem: f64,
    /// Horizontal strokes of the lowercase, and bowls at their top and bottom.
    pub hair: f64,
    pub cap_stem: f64,
    pub cap_hair: f64,
    /// Breadth of an arch where it leaves a stem, as a fraction of the stem.
    pub join: f64,

    // shapes
    /// Squareness of bowls: handle length as a fraction of the way to the corner; 0.5523 is an ellipse.
    pub sq: f64,
    /// Whether rounds are true superellipses (two cubics a quadrant, flat at the extremes) and not single cubics.
    pub lame: bool,
    pub dot_k: f64,
    /// Radius of the dot of i and j.
    pub dot: f64,
    /// Radius of the period.
    pub punct: f64,
    /// Thickness of the strokes of operators.
    pub op: f64,
    /// Left end of an operator's bar; the right end mirrors it.
    pub op_l: f64,

    // spacing
    /// Sidebearing of a straight lowercase stem.
    pub sb: f64,
    /// Sidebearing of a round side.
    pub sb_round: f64,
    /// Sidebearing of a straight capital stem.
    pub cap_sb: f64,
    /// Sidebearing of a figure's round side.
    pub fig_sb: f64,
    /// The counter of n: the unit the proportional family's widths are counted in.
    pub counter: f64,
}

impl Params {
    pub fn italic(&self) -> bool {
        self.slant != 0.0
    }

    /// The height an italic's shear leaves in place, so that slanted glyphs stay centred in their cells.
    pub fn slant_origin(&self) -> f64 {
        self.xh / 2.0
    }

    // x positions (centre lines) of the lowercase's standard stems
    pub fn xl(&self) -> f64 {
        self.sb + self.stem / 2.0
    }

    pub fn xr(&self) -> f64 {
        self.width - self.sb - self.stem / 2.0
    }

    // x positions (centre lines) of the capitals' standard stems
    pub fn cxl(&self) -> f64 {
        self.cap_sb + self.cap_stem / 2.0
    }

    pub fn cxr(&self) -> f64 {
        self.width - self.cap_sb - self.cap_stem / 2.0
    }

    pub fn mid(&self) -> f64 {
        self.width / 2.0
    }

    pub fn op_r(&self) -> f64 {
        self.width - self.op_l
    }

    /// The same master drawn `f` times as large: every length multiplied, every ratio and angle kept. The name
    /// and the place in the design space stay. For glyphs that contain small letters and figures: the caller
    /// then sets the strokes and the spacing the small size needs, as an optical size does.
    pub fn scaled(&self, f: f64) -> Params {
        Params {
            width: self.width * f,
            cap: self.cap * f,
            xh: self.xh * f,
            asc: self.asc * f,
            desc: self.desc * f,
            over: self.over * f,
            axis: self.axis * f,
            br_top: self.br_top * f,
            br_bot: self.br_bot * f,
            line_top: self.line_top * f,
            line_bot: self.line_bot * f,
            stem: self.stem * f,
            hair: self.hair * f,
            cap_stem: self.cap_stem * f,
            cap_hair: self.cap_hair * f,
            dot: self.dot * f,
            punct: self.punct * f,
            op: self.op * f,
            op_l: self.op_l * f,
            sb: self.sb * f,
            sb_round: self.sb_round * f,
            cap_sb: self.cap_sb * f,
            fig_sb: self.fig_sb * f,
            counter: self.counter * f,
            ..self.clone()
        }
    }
}

pub const SLANT: f64 = 10.0;

/// The optical sizes of the proportional family's masters, in points: the small one is for captions, footnotes
/// and the scripts of formulas, the other for running text and everything larger.
pub const OPSZ_SMALL: f64 = 8.0;
pub const OPSZ_TEXT: f64 = 16.0;

/// The fixed-pitch Regular: the master every other one is described as a change to.
pub fn regular() -> Params {
    Params {
        name: "Mono Regular",
        wght: 400.0,
        opsz: OPSZ_TEXT,
        slant: 0.0,
        mono: true,
        upm: 1000.0,
        width: 600.0,
        cap: 714.0,
        xh: 540.0,
        asc: 756.0,
        desc: -200.0,
        over: 10.0,
        axis: 320.0,
        br_top: 790.0,
        br_bot: -150.0,
        line_top: 1000.0,
        line_bot: -250.0,
        stem: 88.0,
        hair: 74.0,
        cap_stem: 92.0,
        cap_hair: 78.0,
        join: 0.52,
        sq: 0.688,
        lame: true,
        dot_k: 0.60,
        dot: 60.0,
        punct: 80.0,
        op: 74.0,
        op_l: 66.0,
        sb: 90.0,
        sb_round: 66.0,
        cap_sb: 80.0,
        fig_sb: 98.0,
        counter: 244.0,
    }
}

pub fn light() -> Params {
    Params {
        name: "Mono Light",
        wght: 300.0,
        stem: 66.0,
        hair: 57.0,
        cap_stem: 69.0,
        cap_hair: 60.0,
        join: 0.56,
        dot: 48.0,
        punct: 62.0,
        op: 56.0,
        sb: 98.0,
        sb_round: 74.0,
        cap_sb: 90.0,
        fig_sb: 106.0,
        counter: 272.0,
        ..regular()
    }
}

pub fn bold() -> Params {
    Params {
        name: "Mono Bold",
        wght: 700.0,
        stem: 134.0,
        hair: 108.0,
        cap_stem: 140.0,
        cap_hair: 112.0,
        join: 0.44,
        over: 11.0,
        dot: 84.0,
        punct: 102.0,
        op: 108.0,
        sb: 70.0,
        sb_round: 50.0,
        cap_sb: 62.0,
        fig_sb: 78.0,
        counter: 192.0,
        ..regular()
    }
}

/// The proportional family's master for running text: the fixed-pitch master of the same weight with the spacing
/// of a text face. The letters n, o and their kin keep their widths; what changes is in the widths table of the
/// glyph programs.
fn text_of(p: Params) -> Params {
    let (name, sb, sb_round, cap_sb, counter) = match p.name {
        "Mono Light" => ("Text Light", 88.0, 66.0, 96.0, 276.0),
        "Mono Bold" => ("Text Bold", 66.0, 46.0, 68.0, 204.0),
        _ => ("Text Regular", 82.0, 60.0, 88.0, 252.0),
    };
    Params { name, mono: false, sb, sb_round, cap_sb, counter, ..p }
}

/// The proportional family's master for small sizes, from its master for text: a larger x-height, heavier
/// strokes with less contrast between them, wider letters, more space between them, larger dots.
fn small_of(p: Params) -> Params {
    let name = match p.name {
        "Text Light" => "Small Light",
        "Text Bold" => "Small Bold",
        _ => "Small Regular",
    };
    let heavier = if p.wght > 600.0 { 1.0 } else { 1.05 };
    Params {
        name,
        opsz: OPSZ_SMALL,
        xh: p.xh + 14.0,
        stem: (p.stem * heavier).round(),
        hair: (p.hair * heavier * 1.04).round(),
        cap_stem: (p.cap_stem * heavier).round(),
        cap_hair: (p.cap_hair * heavier * 1.04).round(),
        dot: (p.dot * 1.08).round(),
        punct: (p.punct * 1.08).round(),
        op: (p.op * heavier).round(),
        sb: p.sb + 10.0,
        sb_round: p.sb_round + 10.0,
        cap_sb: p.cap_sb + 10.0,
        fig_sb: p.fig_sb + 6.0,
        counter: p.counter + 12.0,
        width: p.width + 20.0,
        ..p
    }
}

fn italic_of(p: Params) -> Params {
    let name = match p.name {
        "Mono Regular" => "Mono Italic",
        "Mono Light" => "Mono Light Italic",
        "Mono Bold" => "Mono Bold Italic",
        "Text Regular" => "Text Italic",
        "Text Light" => "Text Light Italic",
        "Text Bold" => "Text Bold Italic",
        "Small Regular" => "Small Italic",
        "Small Light" => "Small Light Italic",
        "Small Bold" => "Small Bold Italic",
        other => other,
    };
    Params { name, slant: SLANT, ..p }
}

/// One font file's worth of masters: a variable font interpolates between them, so their glyphs must have the
/// same structure.
#[derive(Clone, Debug)]
pub struct Face {
    /// The family name, as applications list it.
    pub family: &'static str,
    /// The stem of the file names.
    pub file: &'static str,
    pub italic: bool,
    /// Glyph modules the face leaves out.
    pub omit: &'static [&'static str],
    pub masters: Vec<Params>,
}

impl Face {
    /// Whether the face has the glyphs of the module called `module`.
    pub fn has(&self, module: &str) -> bool {
        !self.omit.contains(&module)
    }

    /// The master the others are deltas from: Regular, at the size for running text.
    pub fn default_master(&self) -> &Params {
        self.masters
            .iter()
            .find(|p| p.wght == 400.0 && p.opsz == OPSZ_TEXT)
            .expect("every face has a Regular at the size for text")
    }
}

/// The fixed-pitch family's upright masters: Light, Regular, Bold.
pub fn upright_masters() -> Vec<Params> {
    vec![light(), regular(), bold()]
}

/// The fixed-pitch family's italic masters.
pub fn italic_masters() -> Vec<Params> {
    upright_masters().into_iter().map(italic_of).collect()
}

/// The proportional family's upright masters: three weights at each of the two optical sizes.
pub fn text_masters() -> Vec<Params> {
    let text: Vec<Params> = upright_masters().into_iter().map(text_of).collect();
    let small: Vec<Params> = text.iter().cloned().map(small_of).collect();
    text.into_iter().chain(small).collect()
}

/// The four faces: the two families, each upright and italic.
pub fn faces() -> Vec<Face> {
    let italics = |ms: Vec<Params>| ms.into_iter().map(italic_of).collect();
    // lines and blocks that tile a terminal's grid have no meaning between letters of different widths
    const GRID: &[&str] = &["box"];
    vec![
        Face { family: "Rachis Mono", file: "RachisMono", italic: false, omit: &[], masters: upright_masters() },
        Face { family: "Rachis Mono", file: "RachisMono-Italic", italic: true, omit: &[], masters: italic_masters() },
        Face { family: "Rachis", file: "Rachis", italic: false, omit: GRID, masters: text_masters() },
        Face { family: "Rachis", file: "Rachis-Italic", italic: true, omit: GRID, masters: italics(text_masters()) },
    ]
}

/// Every master of every face.
pub fn masters() -> Vec<Params> {
    faces().into_iter().flat_map(|f| f.masters).collect()
}

/// A master by its name: "Mono Regular", "Text Bold Italic", "Small Light". A name without a family is the
/// fixed-pitch one's.
pub fn master(name: &str) -> Option<Params> {
    let all = masters();
    all.iter()
        .find(|p| p.name == name)
        .or_else(|| all.iter().find(|p| p.name.strip_prefix("Mono ") == Some(name)))
        .cloned()
}
