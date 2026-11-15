# Design

What this typeface is, who it is for, and the decisions its shapes follow. `drawing.md` is the working method, `decisions.md` records each decision with what it rejected, `measurements.md` holds the numbers the claims here rest on, and `ledger.md` lists what is open.

## Brief

A family for one reader: a software engineer and mathematics student who reads code, logs and hashes in terminals and editors, and textbooks, technical writing and mathematics in documents and browsers, and who wants dense technical text to read without effort at small sizes. There are two families, drawn by the same programs:

- **Rachis Mono**, fixed pitch, for code, terminals and plain-text mathematics. It is read at 12 to 15 px per em, where the x-height subtends 0.12° to 0.19°, at or below the 0.2° critical print size for fluent reading.
- **Rachis**, proportional, for prose with notation in it: paragraphs, formulas, captions, footnotes, the scripts of formulas. It has an optical-size axis, because the small sizes are where technical text is densest.

Both are designed as small print: a large x-height, sturdy low-contrast strokes, open counters, generous room between letters, and characters told apart by their outlines.

## Principles

1. Literal. A character has one glyph, and the glyph shows that character and no other. There are no ligatures that replace two characters with a third shape, and nothing changes shape because of its neighbours (T06).
2. Distinct. Characters that technical text confuses (`0 O`, `1 l I |`, `5 S`, `8 B`, `2 Z`, `6 b`, `g q 9`, `rn m`, `. ,`, `- − – —`, `v ν ∨`, `x χ ×`, `∑ Σ`, `ε ∈ ϵ`, `⟨ <`) differ in outline, since at reading size an inner mark is a weak cue and the outline a strong one. Each difference is measured against reference typefaces (T07, `measurements.md`).
3. Plain. No ornament. A serif, tail or foot exists only where it tells two characters apart or, in the fixed pitch, fills a cell that a narrow letter would leave empty.
4. Aligned to the grid. Every stroke ends in a horizontal or a vertical cut (T04). Operators sit on one axis and share one stroke and one span, so `->`, `=>`, `<=`, `+=` and `|>` line up without being fused, and `→` is as tall and as heavy as `->`.
5. One construction. Every round shape is the same superellipse, of exponent 5/2 (T12); every hook is the same rounded elbow; mathematical signs and arrows are assembled from the bar, the chevron, the stem, the ring and the dot that draw the ASCII operators.
6. A program. The typeface is generated (T01, T11): glyphs are programs over a small kernel, and weight, optical size, slant and pitch are parameters. One program draws a letter in eighteen masters. The fonts in `fonts/` are a build product, reproducible to the byte.

## Dimensions

1000 units to the em. The line is 1250 high, 1000 above the baseline and 250 below (T13).

| | x-height | cap | ascender | descender | stem | hairline | sidebearing (straight, round) | counter of n | cell |
|---|---|---|---|---|---|---|---|---|---|
| Mono Light | 540 | 714 | 756 | −200 | 66 | 57 | 98, 74 | 272 | 600 |
| Mono Regular | 540 | 714 | 756 | −200 | 88 | 74 | 90, 66 | 244 | 600 |
| Mono Bold | 540 | 714 | 756 | −200 | 134 | 108 | 70, 50 | 192 | 600 |
| Text Light | 540 | 714 | 756 | −200 | 66 | 57 | 88, 62 | 276 | 580 |
| Text Regular | 540 | 714 | 756 | −200 | 88 | 74 | 82, 56 | 252 | 580 |
| Text Bold | 540 | 714 | 756 | −200 | 134 | 108 | 66, 44 | 204 | 580 |
| Small Regular | 554 | 714 | 756 | −200 | 92 | 81 | 92, 66 | 264 | 600 |

The Regular stem is 16% of the x-height, inside the band of 12 to 31% where reading speed is flat (T03). In the fixed pitch the gap between two n's is 0.74 of the counter. In the proportional family n is 588 wide, o 596, i 252, m 903, H 724, the word space 258; these follow the medians of nine text faces at the same x-height (T14, T15). The operator axis is at 320. The weight axis runs from 300 to 700; the italic slants its skeletons 10° and keeps the pen upright (T08). The optical-size axis of Rachis runs from 8 to 16: the Small masters have the larger x-height, heavier and less contrasted strokes, and more room (T16).

## Forms

Lowercase, both families:

- `a` is double-storey, upright and italic: the single-storey form is misread as `o` and `q`.
- `g` is single-storey with an open hooked tail.
- `e` has its bar a little below the middle and an open aperture. `c`, `e`, `s`, `a` end in vertical cuts.
- `y` has a straight tail. `k`, `v`, `w`, `x`, `z` are straight strokes cut flat.

What the fixed pitch does to fill its cell, and the proportional family does not:

| | Rachis Mono | Rachis |
|---|---|---|
| `i`, `j` | a slab to the left at the top; `i` stands on a full bar | a stem and a dot; the hook of `j` hangs to the left |
| `l` | the same slab, and a long flat foot to the right | a stem with a short tail to the right |
| `t`, `f` | long crossbars and a wide foot or hook | short bar, compact foot; the hook of `f` clears a following `i` or `l` without a ligature |
| `r` | stands right of the edge | at the sidebearing, with a short arm |
| `m`, `w`, `M`, `W` | strokes thinned, vertices kept inside the cell | full strokes; the diagonals of `M` reach the baseline |
| `q` | a short foot, to tell it from `g` and `9` | a plain stem |
| `I` | full serifs | short serifs |
| `J` | a top bar to the left | none |
| `0` | slashed, the slash inside the counter | plain and narrow; `zero` gives the slash |
| `-` | the minus shortened | a hyphen |

`1` has a flag and a foot, `I` serifs, `l` a tail or a foot, and `|` is a plain bar taller and deeper than any letter: the four differ in outline in both families (T18).

Capitals: plain grotesque forms. `D` is flat-backed with square corners where `O` is round all over. `B` has a flat stem and unequal bowls. `Q` has a tail that crosses the bowl.

Figures: lining, cap height, all one advance in both families (T19). `1` as above. `2` has a flat base. `4` is closed. `5` has a flat top bar and a sharp corner. `6` and `9` have open apertures. `7` has a straight leg. `8` has a smaller upper bowl. Superior and inferior figures and letters are drawn at their own size with strokes of their own, not scaled (T21).

Punctuation and operators: the period is a round dot; the comma is that dot with a tail that ends nearly as broad as the dot and well to its left (T28); colon and semicolon stack them. Quotes are straight; the backtick is a heavy stroke falling to the right. `+`, `=`, `<`, `>`, `~`, `*` and `−` are centred on the axis. Brackets, braces, parentheses and the bar span from below the baseline to above the ascender. `@`, `&`, `$`, `%`, `#` are drawn for the cell, not squeezed into it.

Signs in the two families: in Rachis Mono every sign has the cell. In Rachis the figures and the signs of arithmetic and comparison have the figure's cell, so columns align, and every other sign has the room its shape wants: an arrow 1.9 spans of the cell, a relation between sets 1.3, a circled operator or a turnstile 1.45; `@`, `%` and `&` are as wide as a text face draws them, and the ellipsis is three periods (T27). `∅` is a circle with a slash that runs out of it, `ρ` has a tail that swings left, a doubled stroke has a white nearly twice as broad as its strokes, and the brace has a long cusp and round shoulders (T28).

Accents: sturdy, steep and well clear of the letter, for 12 to 16 px: the acute steep, the diaeresis with dots the size of the dot of i, the tilde a real double curve, the caron pointed and the breve round. Capitals take flatter forms. Every mark sits on an anchor measured from the letter it is on (T20).

Greek: upright, drawn with the Latin's parts, and told from the Latin at a glance: ν has a curved right stroke, υ no stem, ω two round bowls, ρ no spur, σ a flat top running out to the right, χ descends, κ has no ascender, φ is the open form and ϕ the ring with a stem.

Mathematics: signs are built from the operator primitives and sit on the axis. `≤` is `<` over a bar; `≠` is `=` struck by a slash; `→` is the minus ending in a head as tall as `>`; `⇒` is `=` ending in a larger one; `↦` adds the stem of `⊢`. The n-ary operators `∑ ∏ ⋂ ⋃ ⨁` are larger than the binary ones and centred on the axis like brackets; `∑` and `∏` are taller than `Σ` and `Π` and reach below the baseline. `∫` runs the height of a bracket. `∂` is a figure. `⟨ ⟩` are full-height brackets with an obtuse angle, lighter than `<`. Double-struck letters are the plain capitals with one stroke doubled, the gap kept open in the Bold. Bracket pieces `⎛ ⎜ ⎝` tile across lines as box drawing does.

Terminal (Rachis Mono only): box-drawing lines are 60 units, the underline's thickness, in every weight (heavy: 120), run through the centre of the cell and overshoot it so that cells and lines join (T22). Rounded corners have a radius of 0.42 of the advance. Block elements divide the cell exactly. Braille dots sit on a 2 by 4 grid. Powerline separators, the branch-drawing set, progress indicators and sextants are included. None of these slant in the italic.

## Spacing

The fixed pitch has one advance. The proportional family is spaced as a text face: every letter asks for its sidebearings and the breadth of its ink (T15), and pairs that the sidebearings cannot serve are kerned by a computation over the outlines (T17): To −77, AV −80, r. −74. Two lowercase letters are never moved together, so r n, c l and v v keep their distance from m, d and w.

## Coverage

2109 glyphs in Rachis Mono and 1529 in Rachis: ASCII, Latin-1, Latin Extended-A and the parts of Latin Extended-B and Additional that European languages use; monotonic Greek and the mathematical variants; superscripts, subscripts and fractions; 336 mathematical operators and relations; 140 arrows; delimiters and bracket pieces; double-struck and letterlike letters; currency; typographic spaces; geometric shapes and symbols; and in the fixed pitch, box drawing, blocks, Braille, Powerline, branch drawing and sextants. The list came from a survey of what code, proof assistants, plain-text mathematics and terminal programs use (`research/`); what it names and the fonts lack is in `ledger.md` (G5).
