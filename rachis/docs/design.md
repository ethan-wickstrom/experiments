# Design

What this typeface is, who it is for, and the decisions its shapes follow. `drawing.md` is the working method, `decisions.md` records each decision with what it rejected, and `measurements.md` holds the numbers the claims here rest on.

## Brief

A monospaced typeface for one reader: a software engineer and mathematics student who reads code, logs, hashes, Markdown and plain-text mathematics in terminals and editors all day, and who draws terminal interfaces with box-drawing characters. It is read at 12 to 15 px per em, in light and dark themes. At those sizes the x-height subtends 0.12° to 0.19°, at or below the 0.2° critical print size for fluent reading, so it is designed as small print: large x-height, sturdy low-contrast strokes, open counters, and letters told apart by their outlines.

## Principles

1. Literal. A character has one glyph and one cell, and the glyph shows that character and no other. There are no ligatures that replace two characters with a third shape, and nothing changes shape depending on its neighbours.
2. Distinct. Characters that code confuses (`0 O`, `1 l I |`, `5 S`, `8 B`, `2 Z`, `6 b`, `g q 9`, `rn m`, `' \``, `. ,`, `- − – —`) differ in outline, since at reading size an inner mark is a weak cue and the outline is a strong one. Each such difference is measured against reference typefaces.
3. Plain. No ornament. A serif, tail or foot exists only where it tells two characters apart or fills a cell that a narrow letter would leave empty.
4. Aligned to the grid. Every stroke ends in a horizontal or a vertical cut. Operators sit on one axis and share one stroke and one span, so `->`, `=>`, `<=`, `+=` and `|>` line up without being fused.
5. One construction. Every round shape is the same superellipse; every hook is the same rounded elbow; mathematical signs are assembled from the bar, the chevron, the stem, the ring and the dot that draw the ASCII operators.
6. A program. The typeface is generated: glyphs are programs over a small kernel (pens on skeletons, Hobby splines), and weight and slant are parameters. The fonts in `fonts/` are a build product, reproducible from the source.

## Dimensions

1000 units to the em; advance 600. Regular: x-height 540, cap height 714, ascender 756, descender −200, overshoot 10; vertical stems 88 (16% of the x-height), horizontal strokes 74; capital stems 92 and 78. The stem of the letter n leaves a counter of 244 and side bearings of 90, so the gap between two n's is 0.74 of the counter. The operator axis is at 320. The line is 1250 high (980 above the baseline, 270 below). Light (300) has stems of 66, Bold (700) stems of 140; the weight axis is continuous between them. The italic slants its skeletons 10° and keeps the pen upright.

## Forms

Lowercase:

- `a` is double-storey, upright and italic: the single-storey form is misread as `o` and `q`.
- `g` is single-storey with an open hooked tail. `q` has a straight stem that ends in a short foot to the right, the mark handwriting gives it to keep it from `g` and `9`.
- `i` and `j` have a slab to the left at the top; `i` stands on a full bar. `l` has the same slab and turns right into a flat foot. `1` has a flag and a foot, `I` has full serifs top and bottom, and `|` is a plain bar taller and deeper than any letter.
- `t` has a crossbar longer on the right and the same elbow and foot as `l`. `f` hooks right at the top and has no foot. `r` has no foot.
- `e` has its bar a little below the middle and an open aperture. `c`, `e`, `s`, `a` end in vertical cuts.
- `y` has a straight tail. `k`, `v`, `w`, `x`, `z` are straight strokes cut flat.

Capitals: plain grotesque forms. `D` is flat-backed with square corners where `O` is round all over. `B` has a flat stem and unequal bowls. `I` has serifs. `J` has a top bar to the left. `Q` has a tail that crosses the bowl. `M` and `W` keep their vertices inside the cell and thin their inner strokes.

Figures: lining, cap height, all the same advance. `0` is at least 15% narrower than `O` and carries a slash that stays inside its counter (the empty set `∅` and `Ø` have strokes that cross the ring). `1` as above. `2` has a flat base. `3` has a round top and open apertures. `4` is closed. `5` has a flat top bar and a sharp corner. `6` and `9` have open apertures; `9` is `6` turned. `7` has a straight leg and no serif or bar. `8` has a smaller upper bowl.

Punctuation and operators: the period is a round dot 1.7 stems across; the comma is that dot with a tail below the baseline; colon and semicolon stack them. Quotes are straight; the backtick is a heavy stroke falling to the right, larger than any accent. `-`, `+`, `=`, `<`, `>`, `~`, `*` and `−` are centred on the axis; `-` is the minus shortened. `_` nearly fills its cell and leaves a gap that keeps adjacent underscores countable. Brackets, braces, parentheses and the bar span from below the baseline to above the ascender; a brace has a cusp at least a stem and a half deep. `*` has six points. `^` sits at cap height. `@`, `&`, `$`, `%`, `#` are drawn for the cell, not squeezed into it.

Mathematics: signs are built from the operator primitives and sit on the axis. `≤` is `<` over a bar; `≠` is `=` struck by a slash; `→` is the minus ending in the chevron of `>`; `⇒` is `=` ending in it; `↦` adds the stem of `⊢`; `∈` is `⊂` with a bar; `∉` is `∈` struck. `∀`, `∃`, `∑`, `∏` are capital-height. Greek is upright and drawn with the Latin's strokes. Double-struck `ℕ ℤ ℚ ℝ ℂ` double one stem.

Terminal: box-drawing lines are one operator stroke thick (heavy: two), run through the centre of the cell and reach every edge of the line box exactly, so they connect across cells and lines. Block elements divide the cell exactly. Braille dots sit on a 2 by 4 grid. None of these slant in the italic.
