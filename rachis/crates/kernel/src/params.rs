//! The parameters of a master: every measurement a glyph program may read.
//!
//! Lengths are in font units, 1000 to the em, and the advance is 600. A master is a point on the weight axis,
//! upright or italic. The variable font interpolates between the weights, so everything that differs between them
//! must be a number here, never a branch in a glyph program.

#[derive(Clone, Debug, PartialEq)]
pub struct Params {
    pub name: &'static str,
    pub wght: f64,
    /// Degrees; positive leans right.
    pub slant: f64,

    pub upm: f64,
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
}

pub const SLANT: f64 = 10.0;

pub fn regular() -> Params {
    Params {
        name: "Regular",
        wght: 400.0,
        slant: 0.0,
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
        line_top: 980.0,
        line_bot: -270.0,
        stem: 88.0,
        hair: 74.0,
        cap_stem: 92.0,
        cap_hair: 78.0,
        join: 0.52,
        sq: 0.62,
        dot_k: 0.60,
        dot: 60.0,
        punct: 80.0,
        op: 74.0,
        op_l: 66.0,
        sb: 90.0,
        sb_round: 66.0,
        cap_sb: 80.0,
        fig_sb: 98.0,
    }
}

pub fn light() -> Params {
    Params {
        name: "Light",
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
        ..regular()
    }
}

pub fn bold() -> Params {
    Params {
        name: "Bold",
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
        ..regular()
    }
}

fn italic_of(p: Params) -> Params {
    let name = match p.name {
        "Regular" => "Italic",
        "Light" => "Light Italic",
        "Bold" => "Bold Italic",
        other => other,
    };
    Params {
        name,
        slant: SLANT,
        ..p
    }
}

pub fn upright_masters() -> Vec<Params> {
    vec![light(), regular(), bold()]
}

pub fn italic_masters() -> Vec<Params> {
    upright_masters().into_iter().map(italic_of).collect()
}

pub fn masters() -> Vec<Params> {
    let mut all = upright_masters();
    all.extend(italic_masters());
    all
}

pub fn master(name: &str) -> Option<Params> {
    masters().into_iter().find(|p| p.name == name)
}
