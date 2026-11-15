"""The parameters of a master: every measurement a glyph program may read.

Lengths are in font units, 1000 to the em, and the advance is 600. A master is a point on the weight axis, upright
or italic. The variable font interpolates between the three weights, so everything that differs between them must
be a number here, never a branch in a glyph program.
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class Params:
    name: str = "Regular"
    wght: float = 400.0
    slant: float = 0.0  # degrees; positive leans right

    upm: int = 1000
    width: float = 600.0

    # heights
    cap: float = 714.0
    xh: float = 540.0
    asc: float = 756.0
    desc: float = -200.0
    over: float = 10.0  # overshoot of round shapes past a flat one
    axis: float = 320.0  # the height operators are centred on
    br_top: float = 790.0  # top of brackets, braces, parentheses and the bar
    br_bot: float = -150.0  # their bottom
    line_top: float = 980.0  # top of the line: box drawing and blocks fill line_bot … line_top
    line_bot: float = -270.0

    # strokes
    stem: float = 88.0  # vertical strokes of the lowercase
    hair: float = 74.0  # horizontal strokes of the lowercase, and bowls at their top and bottom
    cap_stem: float = 92.0
    cap_hair: float = 78.0
    join: float = 0.52  # breadth of an arch where it leaves a stem, as a fraction of the stem

    # shapes
    sq: float = 0.62  # squareness of bowls: handle length as a fraction of the way to the corner; 0.5523 is an ellipse
    dot_k: float = 0.60
    dot: float = 60.0  # radius of the dot of i and j
    punct: float = 80.0  # radius of the period
    op: float = 74.0  # thickness of the strokes of operators
    op_l: float = 66.0  # left end of an operator's bar; the right end mirrors it

    # spacing
    sb: float = 90.0  # sidebearing of a straight lowercase stem
    sb_round: float = 66.0  # sidebearing of a round side
    cap_sb: float = 80.0  # sidebearing of a straight capital stem
    fig_sb: float = 98.0  # sidebearing of a figure's round side

    @property
    def italic(self) -> bool:
        return self.slant != 0.0

    @property
    def slant_origin(self) -> float:
        """The height an italic's shear leaves in place, so that slanted glyphs stay centred in their cells."""
        return self.xh / 2.0

    # x positions (centre lines) of the lowercase's standard stems
    @property
    def xl(self) -> float:
        return self.sb + self.stem / 2.0

    @property
    def xr(self) -> float:
        return self.width - self.sb - self.stem / 2.0

    # x positions (centre lines) of the capitals' standard stems
    @property
    def cxl(self) -> float:
        return self.cap_sb + self.cap_stem / 2.0

    @property
    def cxr(self) -> float:
        return self.width - self.cap_sb - self.cap_stem / 2.0

    @property
    def mid(self) -> float:
        return self.width / 2.0

    @property
    def op_r(self) -> float:
        return self.width - self.op_l


REGULAR = Params()
LIGHT = replace(
    REGULAR,
    name="Light",
    wght=300.0,
    stem=66.0,
    hair=57.0,
    cap_stem=69.0,
    cap_hair=60.0,
    join=0.56,
    dot=48.0,
    punct=62.0,
    op=56.0,
    sb=98.0,
    sb_round=74.0,
    cap_sb=90.0,
    fig_sb=106.0,
)
BOLD = replace(
    REGULAR,
    name="Bold",
    wght=700.0,
    stem=134.0,
    hair=108.0,
    cap_stem=140.0,
    cap_hair=112.0,
    join=0.44,
    over=11.0,
    dot=84.0,
    punct=102.0,
    op=108.0,
    sb=70.0,
    sb_round=50.0,
    cap_sb=62.0,
    fig_sb=78.0,
)

SLANT = 10.0


def _italic(p: Params) -> Params:
    return replace(p, name="Italic" if p.name == "Regular" else f"{p.name} Italic", slant=SLANT)


UPRIGHT_MASTERS = (LIGHT, REGULAR, BOLD)
ITALIC_MASTERS = tuple(_italic(p) for p in UPRIGHT_MASTERS)
MASTERS: dict[str, Params] = {p.name: p for p in (*UPRIGHT_MASTERS, *ITALIC_MASTERS)}
