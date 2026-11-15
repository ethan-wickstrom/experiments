# Decisions

Every decision the typeface rests on: what was chosen, what was rejected and why. The log is append-only; a reversed decision gets a new entry and the old one is marked superseded. IDs are stable, and `design.md`, `ledger.md` and `measurements.md` cite them. The research each entry cites was done on 2026-11-14 and 2026-11-15; the reports are in `research/`.

## T01 · The typeface is a program (2026-11-14, active; the language is amended by T11)
- Decision: glyphs are Python functions over a small kernel: knots carrying a pen (METAFONT's `penpos`), centre lines chosen by Hobby's spline, outlines obtained by offsetting the centre line. Weight and slant are parameters. The fonts are a build product.
- Why: the owner is a programmer and a mathematics student, the repository's rule is that every claim is measured, and a program can be measured, tested, diffed and rebuilt. One program yields six masters, so a Light, a Bold and an italic cost parameters, not redrawing. Structure that is the same for every master makes the variable font's interpolation correct by construction.
- Rejected:
  - drawing outlines in a font editor: no editor runs in this environment, and outlines drawn by hand cannot be regenerated when a proportion changes;
  - skia's stroker with boolean union: its output's point structure depends on the numbers, so masters would not interpolate, and it gives no control of joins;
  - METAFONT or MetaPost themselves: they produce bitmaps or need a tracing step (mf2pt1, MetaType1), and neither is installed; the kernel reimplements the two ideas that matter (pen positions, Hobby's spline) in 600 lines with tests;
  - Iosevka's build system: it generates Iosevka's design, and this is a different design.
- Where: `src/rachis/geom.py`, `pen.py`, `glyph.py`, `parts.py`.

## T02 · Monospaced, 600 units to a 1000-unit em (2026-11-14, active for Rachis Mono; T14 adds a proportional family)
- Decision: every glyph advances 600; combining marks advance 0.
- Why: 60% of the em is the stated convention (Hunt for Source Code Pro) and the measured one: 10 of 16 current code typefaces. At 12 to 14 px the centre-to-centre distance of 0.6 em is 0.16° to 0.25°, already at the critical spacing for crowding near fixation (0.1° to 0.2°), so a narrower cell would cost legibility at exactly the sizes the typeface is read at.
- Rejected: 500 (Iosevka's economy: more columns, but letters inside the crowding limit); 620 and wider (Monaspace, Intel One Mono: more room for m and w, fewer columns, and no 1:2 relation with a CJK fallback at 1200).

## T03 · Proportions for small print (2026-11-14, active)
- Decision: x-height 540, cap height 714, ascender 756, descender −200; Regular stem 88 (16.3% of the x-height), horizontal strokes 74 (stem to hair 1.19); n counter 244, side bearings 90.
- Why: code at 12 to 14 px has an x-height of 0.12° to 0.19°, at or under the 0.2° critical print size, so the design follows what is known about small print. Typefaces designed for screens average an x-height of 0.52 em (SD 0.03); the reference code faces measure 0.49 to 0.55. Reading speed is flat for stems between 12% and 31% of the x-height and falls outside that band (Bernard et al. 2013); the references sit at 16 to 17%. DIN 1450 asks for an n counter near half the x-height (here 0.45) and a gap between letters of 70 to 78% of that counter (here 0.74). Ascenders rise 42 above the capitals, Lucida's rule, which keeps `l` from `I` and keeps acronyms from dominating a line.
- Rejected: x-height 550 or more (JetBrains Mono, Maple Mono: larger letters, but advance over x-height falls under 1.09 and letters condense, the failure Hunt names); x-height under 500 (Source Code Pro, Intel One Mono: calmer, but fewer pixels where the information is).

## T04 · Every stroke ends on the grid (2026-11-14, active)
- Decision: stems and diagonals end in horizontal cuts, curved strokes in vertical cuts. There are no angled, flared or ball terminals.
- Why: at 13 px a cut aligned to the pixel grid renders as a clean edge and an angled one as a grey ramp, and line terminations are the features readers use most to identify letters (Fiset et al. 2008). A vertical cut on `c`, `e`, `s` and `a` keeps the aperture open, where a horizontal cut would require the stroke to curl back and close it. One rule for every terminal is also the plainest.
- Rejected: horizontal cuts on curved strokes (JetBrains Mono, IBM Plex Mono: crisp, but apertures close); cuts perpendicular to the stroke (Fira, Source Code Pro: open, but at an arbitrary angle to the grid).

## T05 · One superellipse (2026-11-14, superseded by T12: the shape is now a true superellipse)
- Decision: every bowl and shoulder is a quadrant whose handles lie at 0.62 of the way to the corner of its box (an ellipse is 0.5523). The centre line has this shape; both sides of the stroke are offsets of it through its midpoint, so a round stroke keeps its breadth around the turn.
- Why: at a 600 advance, squarer rounds enlarge the counters, which is what small print needs, and one constant makes `o`, `n`, `b`, `e`, `0` and `∪` visibly one family.
- Rejected: ellipses (smaller counters at this width); a higher constant (0.70: reads as a rounded rectangle and loses the distinction between `O` and `D`); separate constants for outer and inner contours (the stroke would thin or swell on the diagonal).

## T06 · No ligatures, and nothing contextual (2026-11-14, active)
- Decision: the fonts contain no substitution that replaces two characters by one shape or that changes a glyph because of its neighbours. `calt`, `liga` and `dlig` are absent. The only substitutions are one-for-one alternates the reader asks for (stylistic sets, superiors, inferiors).
- Why: the owner writes in literal language and the typeface does the same: what is on the screen is what is in the file. A ligature shows a character that is not there (`≠` for `!=`), and Unicode has those characters, which this typeface also draws; the two must stay distinguishable. No controlled study compares code read with and without ligatures (a 2023 systematic review of code legibility found none), so there is no measured benefit to weigh against that. Operators are drawn on one axis with one span instead, so `->` leaves 132 units of white between the bar and the chevron and reads as an arrow without being one glyph.
- Rejected: Fira Code style ligatures; cell-preserving joins in `calt` (they keep the character count but make adjacent hyphens uncountable and depend on shaping support that terminals implement unevenly); texture healing (Monaspace: it evens the rhythm of prose, but it is contextual, and it needs alternates for most of the alphabet; ledger I7).

## T07 · Told apart by outline, and measured (2026-11-15, active)
- Decision: confusable characters differ in outline before they differ in an inner mark. `0` is narrower than `O` and its slash stays inside the counter; `D` is flat-backed; `1` has a flag and a foot, `l` a slab and a foot to the right, `I` two serifs, `|` no serif and the height of a bracket; `q` has a foot where `g` has a hook. Each pair is measured with the distance in `measure.py` against reference typefaces, and the build fails if a gate is missed.
- Why: under the blur of reading size, Bouma found that "inner parts are weak cues at best"; three screen typefaces that mark their zero still score 0.14 to 0.22 on `0`/`O` because the outlines coincide, while an unmarked but narrow zero scores 0.31. The pairs behind most real transcription errors are `l 1`, `O 0`, `Z 2`, `1 7` (Bell Laboratories, via Grissinger 2017).
- Rejected: a dotted zero as the default (at small sizes it reads as `8`: Hunt conceded this for Source Code Pro); a slash that crosses the ring (it is `∅` and `Ø`, which a mathematics user needs to tell from zero); figures shorter than capitals (Lucida Console relied on height alone in 1993 and added the slash in 2013).

## T08 · A weight axis from 300 to 700, and an italic that slants skeletons (2026-11-15, active)
- Decision: three masters (Light 300, Regular 400, Bold 700) make a variable font; a second variable font is the italic. The italic shears the skeleton by 10° and leaves the pen as it was, so stems keep their horizontal thickness, bars their vertical thickness and curves their breadth. Static instances are Light, Regular, Medium, SemiBold and Bold in both.
- Why: no study measures the best stroke weight for light text on dark, and readers differ by 35% in which typeface they read fastest (Wallace et al. 2022), so the weight is the reader's to set. Stems of 66 to 134 stay inside the band where reading speed is flat. The median italic angle of 13 code typefaces is 10°. Shearing outlines instead would thin and thicken a round stroke by 9% around the turn.
- Rejected: a slant axis in one file (applications select italics by style linking, which needs a separate italic font); a Thin or Black extreme (outside the band, and a 600 cell cannot hold a Black `m`); a cursive italic with a single-storey `a` (misread as `o` and `q`: Beier and Larson 2010).

## T09 · One line box on every platform (2026-11-15, amended by T13: 1000 above, 250 below)
- Decision: the line is 1250 units: 980 above the baseline, 270 below, with no line gap. The hhea, typo and win metrics agree and `USE_TYPO_METRICS` is set. Box-drawing glyphs fill that box exactly.
- Why: terminals take the cell's height from these tables, and they do not agree on which; equal values give the same cell everywhere. 1.25 is the median default of 16 code typefaces and what Iosevka builds; JetBrains and Input recommend 1.2.
- Rejected: a tighter box (accented capitals reach 940); a line gap (some applications add it above, some below, some ignore it).

## T10 · The fonts are licensed under the SIL Open Font License; the code under Apache-2.0 (2026-11-15, active; the source is now Rust, T11)
- Decision: files in `fonts/` are under OFL 1.1 (`OFL.txt`), with no Reserved Font Name. The Python source is under the repository's Apache-2.0 licence.
- Why: the OFL is what font users and distributors expect and what lets the fonts be embedded and bundled; the generator is ordinary software.
- Rejected: OFL for the source as well (it has terms written for fonts, not programs); a Reserved Font Name (it forbids even a subsetted web font from keeping the name).

## T11 · The generator is written in Rust (2026-11-15, active)
- Decision: the kernel, the glyph programs, the font compiler and the command line are a Rust workspace (`crates/kernel`, `crates/glyphs`, `crates/font`, `crates/cli`). The compiler writes OpenType tables with `write-fonts`, converts cubics to quadratics with `kurbo`, removes overlaps with `linesweeper` and compresses with `ttf2woff2`. `unsafe` is forbidden. The Python prototype of T01 is deleted; it is in the history up to commit `1492c96`.
- Why: the owner asked for lower-level languages. A typed kernel also makes a glyph program's mistakes compile errors, and the whole family (2109 glyphs, 18 masters) checks its structure in half a second and builds 38 font files in about fifteen.
- How the port was verified: every outline of every master agreed with the prototype's to 1e-6 (857 glyphs, 6 masters) before the design moved on, and the compiler's fonts agreed with fontmake's on the same outlines (advances, character map, and renderings at 200 px per em within a quarter of a pixel's coverage).
- Rejected: keeping Python and fontmake (the request; and a build of seconds instead of minutes changes how often shapes get looked at); C (no font-writing library of the quality of `write-fonts`, and no memory safety); writing the tables by hand (the binary formats are where font bugs live).
- Where: `Cargo.toml`, `crates/`.

## T12 · Every round is a superellipse of exponent 5/2 (2026-11-15, active; supersedes T05)
- Decision: a round corner is a quadrant of the Lamé curve |x/a|^n + |y/b|^n = 1 with n = 5/2, drawn as two cubics fitted to the curve, inside the parallelogram of the corner's two tangents, so that a slant or a stretch of the corner is the superellipse of the slanted or stretched box. The parameter `sq` = 0.688 is the single-cubic handle length that the exponent corresponds to (n = ln ½ / ln((4 + 3·sq)/8)); a knot's `.k(p.sq)` asks for the corner.
- Why: one cubic with long handles is not a superellipse: its curvature peaks twice and it is flat for too short a stretch at the extremes, which at 13 px shows as bowls that neither sit flat on the baseline nor turn evenly. The two-cubic fit keeps the tangents at the extremes and on the diagonal and has the same curvature on both sides of the diagonal. 5/2 is Piet Hein's value: the roundest shape that still reads as squared, and the squarest that still reads as round.
- Rejected: the single cubic at 0.62 (T05); n = 2.4 (sq 0.66: compared on proofs at 44, 15 and 13 px, the counters of a e s close sooner in the Bold); circular arcs with straight sides (the DIN construction: a visible join where the curvature jumps).
- Where: `crates/kernel/src/geom.rs` (`lame_exponent`, `lame_handles`, `lame_corner`), `pen.rs`.

## T13 · The line box is 1000 above the baseline and 250 below (2026-11-15, active; amends T09)
- Decision: ascender 1000, descender −250, no line gap, in hhea, typo and win alike. Box-drawing and block glyphs fill exactly that box.
- Why: both numbers are multiples of a quarter of the em, so a terminal's cell is a whole number of pixels high at every size that is a multiple of 4 px, and at 16 px (the commonest) the baseline falls on a pixel boundary. The height is still 1.25 em.
- Rejected: 980/−270 (T09: the same height, but neither edge on the pixel grid at 16 px).

## T14 · Two families from one set of programs: Rachis Mono and a proportional Rachis (2026-11-15, active; amends T02)
- Decision: the same glyph programs draw a fixed-pitch family (Rachis Mono, every advance 600) and a proportional one (Rachis). A master carries `mono`; a program may branch on it, because the two are different fonts and never interpolate. The branches are the forms that exist only to fill a cell: `i j l t f r m w I J M W q`, the slashed zero, the hyphen. Everything else is one program at two widths. Box drawing, blocks and Powerline are left out of the proportional family.
- Why: the owner asked for effortless reading of dense technical text at small sizes: textbooks, technical writing, mathematics, programming. Code and terminals want a fixed pitch; prose with notation is read in a proportional face, where the evidence gives about 5% faster reading at comfortable sizes (the fixed pitch wins only near the acuity limit: `research/legibility-science.md`). Drawing both from one source keeps a formula, a sentence and a line of code in one design: same x-height, same strokes, same signs.
- A measurement that shaped it: nine text faces (Inter, Source Sans 3, IBM Plex Sans, Atkinson Hyperlegible Next, Noto Sans, Open Sans, DejaVu Sans, Roboto Flex, Fira Sans) scaled to an x-height of 540 have a median n of 600 units and a median figure of 593. The fixed pitch's letters n o b d p q e a c g were already text letters; only the narrow and the wide ones had to change.
- Rejected: the fixed pitch alone (it is not what the request describes); a second, separately drawn typeface (two designs to keep consistent, where a programmed face can derive one from the other); contextual width adjustment inside the fixed pitch (T06).
- Where: `crates/kernel/src/params.rs` (`faces`), `crates/glyphs/src/text.rs`, the `if p.mono` branches in `lower.rs`, `upper.rs`, `digits.rs`.

## T15 · A proportional letter asks for its sidebearings and its ink; the cell is measured (2026-11-15, active)
- Decision: each letter of the proportional family states its left sidebearing, the breadth of its ink and its right sidebearing (`Ask`), in the master's units: so many straight sidebearings (`sb`), round ones (`sb_round`), stems and counters of n. The build runs the letter's program, measures where its ink ends, and finds the cell that gives the ink asked for. The first values are the medians of the nine text faces of T14 for each letter.
- Why: this is how a type designer spaces a face (a stem stands so far from the edge, a round side less, a diagonal less again), written as arithmetic that holds at every weight and optical size: a Bold n is two bold stems and a bold counter, and comes out 3% wider than the Regular as in the references. A table of advances would need a row per master and would know nothing of the shapes.
- Rejected: advances per master by hand (18 masters); deriving sidebearings from the outlines alone by an area rule (it places letters evenly but cannot know that a design wants its arch side tighter than its stem side); kerning classes instead of sidebearings (kerning is for pairs, T17).
- Where: `crates/glyphs/src/text.rs` (`Ask`, `resolve`), `ask` in `lower.rs`, `upper.rs`, `punct.rs`, `latin.rs`.

## T16 · An optical-size axis from 8 to 16 on the proportional family (2026-11-15, active)
- Decision: Rachis has `opsz` from 8 to 16 with the default at 16. The master for 16 is the text design. The master for 8 is the same programs with a larger x-height (+14), strokes 5% heavier in the Light and Regular (not in the Bold), horizontals another 4% heavier (less contrast), sidebearings +10, counters +12, dots 8% larger and a cell 20 wider for figures and signs. Above 16 nothing changes. Static families are built at both ends: Rachis and Rachis Small.
- Why: the request is for small sizes, and what a small size needs is known (larger x-height, sturdier and less contrasted strokes, more room in and between letters); in a programmed face each is a parameter. Browsers set the axis from the font size by themselves. The same arithmetic, pushed further, draws the letters of superscripts and subscripts (T21), which is what Computer Modern does with its 7 and 5 point designs.
- Rejected: one design for all sizes (footnotes, captions and scripts are the dense part of technical text); a third master for display sizes (the family is for text; a larger default would give software without the axis the wrong design at 10 to 12); the default at 8 (software without the axis would set body text in the caption design).
- Where: `small_of` in `crates/kernel/src/params.rs`; `family` in `crates/cli/src/build.rs`.

## T17 · Kerning is computed from the outlines (2026-11-15, active)
- Decision: for every pair of letters and punctuation of the proportional family, the build measures the white between the two inks on every row where they stand side by side, counted no deeper than 1.6 times the pair's standard distance; a pair with more white than two stems at their sidebearings is closed by three quarters of the excess, never nearer than 0.55 of the standard distance, and a pair whose inks come within 0.16 of it is opened. Glyphs whose rows of the table agree within 9 units form a class; the font stores class kerning. Brackets are never closed into.
- Why: T o, A V, r followed by a full stop and P followed by one are holes in a line at any size, and the sidebearings cannot close them. The depth of 1.6 was chosen so that a round side at the round sidebearing measures what a straight side does: the kerning then agrees with the widths table about the pairs that need nothing (n n, o o, n o are 0). The floor of 0.55 keeps the arm of r off n, so that r n is not read as m.
- Measured: To −77, AV −80, LT −79, r. −74, P. −77, (j +33, rn 0, nn 0 in the Regular.
- Rejected: no kerning (the holes); a hand-made table (it would have to be redone for every weight and whenever a shape changes); closing the whole excess (letters look glued; professional tables close a part).
- Limit: the values are those of the Regular at the text size, applied at every weight and size (ledger G2).
- Where: `crates/glyphs/src/kern.rs`; `rachis kern`.

## T18 · What tells characters apart in the proportional family (2026-11-15, active)
- Decision: `l` keeps a tail, `1` its flag and foot, `I` short serifs, and the bar its height: the four differ in outline without filling a cell. `i` and `j` are a stem and a dot. `q` loses the foot it needs in a cell. The zero is plain and narrower than `O`; the feature `zero` gives the slashed one, `ss01` the dotted one. The hyphen-minus is a hyphen; the minus sign stays as wide as the figures.
- Why: T07's rule (outline before inner mark) holds for both families; what changes is which outlines are available. A slashed zero in a formula reads as the empty set.
- Rejected: a plain `I` (it is `l` without the tail at 12 px); a slab on `i` (it widens the commonest narrow letter and spots the texture).
- Where: `lower.rs`, `upper.rs`, `digits.rs`.

## T19 · Figures, operators, arrows and symbols keep one cell in the proportional family (2026-11-15, active)
- Decision: in Rachis every figure, sign, arrow and symbol has the advance of the cell: 580 at the text size, 600 at the small size. Only letters and punctuation have widths of their own.
- Why: columns of figures align without a feature, and a formula's operators are as wide as its figures, as in the fixed pitch. The median figure of the nine text faces is 593 at this x-height, so a 580 cell is a text figure, not a typewriter's.
- Rejected: proportional figures by default (tables and code in running text are the commoner case for this reader; ledger I6 keeps them as a feature to add).

## T20 · Marks are drawn in a cell of their own, and placed on anchors measured from the letters (2026-11-15, active)
- Decision: a combining mark is drawn centred in a cell, where it would stand over a lowercase letter, and has no advance. Each base letter gets anchors (`top`, `bottom`, `cedilla`, `ogonek`) computed from its drawn upright outline with a small optical correction per letter; an italic shears them with the letter. A precomposed letter is its base and its marks as components at the difference of the anchors. Capitals take flatter forms of the marks so that the Bold stays under the line box.
- Why: terminals draw a combining mark's glyph in the cell of its base, so a mark drawn at a negative offset (the text-font convention) lands in the wrong cell there (`research/terminal-rendering.md`); shaped text uses the anchors. Measuring the anchors means a redrawn letter keeps its accents in place.
- Rejected: marks at x = −advance; anchors written as constants in each base program.
- Limit: the font's mark positioning uses the Regular's anchors at every weight (ledger G2). The precomposed letters are exact at every weight, because components interpolate.
- Where: `crates/glyphs/src/latin.rs`; the `anchors` hook in `crates/kernel/src/glyph.rs`.

## T21 · Small letters and figures are drawn small, not scaled (2026-11-15, active)
- Decision: superscript and subscript letters are the letters' own programs run with a small master: every length times 0.56, then strokes set to 0.78 of the full strokes, sidebearings and counters wider in proportion. Superior and inferior figures and the fractions are the figures' constructions in a small frame with the same strokes.
- Why: a scaled-down letter has strokes 0.56 as heavy and disappears beside the text; this is the reason optical sizes exist.
- Rejected: scaled components (too light); new constructions for each small letter (two alphabets to maintain).
- Where: `crates/glyphs/src/scripts.rs`, `digits.rs`.

## T22 · Terminal graphics follow the terminals' conventions and not the text's weight (2026-11-15, active)
- Decision: a light box-drawing line is 60 units, the underline's thickness, in every weight; heavy is twice that; a double line is light, gap, light. Lines overshoot the cell by 0.03 em across and 0.10 em up and down; rounded corners have a radius of 0.42 of the advance; blocks overshoot only at the cell's outer edges; shades and dashes do not overshoot. Powerline separators, the branch-drawing set, progress indicators and sextants follow kitty's and Ghostty's geometry.
- Why: a table's rules must not thicken when its text is bold, and neighbouring cells must join at every size and line spacing (`research/terminal-rendering.md`).
- Known cost: where a line's edge falls part-way across a pixel, the overshoot of two neighbours covers that pixel twice; JetBrains Mono, with the same overshoot, shows the same.
- Where: `crates/glyphs/src/boxes.rs`.

## T23 · A static font is the variable font at one point, with its overlaps removed and checked (2026-11-15, active)
- Decision: the variable fonts keep each stroke as its own contour. A static font evaluates the same variation model at its instance, unites the contours, and compares the union with the input by rasterising both at 200 px per em; a glyph whose union differs by more than 96/255 in a pixel or 2 pixels in all keeps its contours as drawn. Static TrueType fonts are hinted with ttfautohint; the variable fonts are not hinted. WOFF2 is made of the variable fonts only.
- Why: overlapping contours are what makes the masters interpolate, and every rasteriser fills them correctly; some tools (cutters, some PDF writers) want them removed, which a static font can afford. The boolean operation goes wrong on about one glyph in a thousand (ledger G3), and a wrong outline must not ship.
- Rejected: trusting the union; removing overlaps in the variable fonts (the masters would stop matching).
- Where: `crates/font/src/instance.rs`.

## T24 · The name is Rachis (2026-11-15, active)
- Decision: the family is called Rachis: the proportional face Rachis, the fixed-pitch one Rachis Mono, the static family at the small size Rachis Small. A rachis is the midrib of a frond, which is the name of the first project in this repository.
- Checked: two web searches on 2026-11-15 for a typeface, font family or foundry of that name found none; the nearest names are Rachin (Sensatype Studio), MTC Rachstela (Martype) and Rachana (a Malayalam typeface of Swathanthra Malayalam Computing). A search is not a trademark clearance.

## T25 · No MATH table in this version (2026-11-15, active)
- Decision: the fonts cover mathematics as Unicode text (operators, relations, arrows, Greek, double-struck letters, superscripts and subscripts, delimiters, bracket pieces), not as a font for a formula typesetter. They carry no OpenType MATH table.
- Why: a MATH table that is wrong is worse than none: a typesetter would trust its constants, italic corrections and delimiter variants. Doing it properly is a project of its own (ledger I1), and a programmed face is well placed for it: a delimiter of any height is the same program with another height.

