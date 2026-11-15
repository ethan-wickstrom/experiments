# Decisions

Every decision the typeface rests on: what was chosen, what was rejected and why. The log is append-only; a reversed decision gets a new entry and the old one is marked superseded. IDs are stable, and `design.md`, `ledger.md` and `measurements.md` cite them. The research each entry cites was done on 2026-11-14 and 2026-11-15; the reports are summarised in `research.md`.

## T01 · The typeface is a program (2026-11-14, active)
- Decision: glyphs are Python functions over a small kernel: knots carrying a pen (METAFONT's `penpos`), centre lines chosen by Hobby's spline, outlines obtained by offsetting the centre line. Weight and slant are parameters. The fonts are a build product.
- Why: the owner is a programmer and a mathematics student, the repository's rule is that every claim is measured, and a program can be measured, tested, diffed and rebuilt. One program yields six masters, so a Light, a Bold and an italic cost parameters, not redrawing. Structure that is the same for every master makes the variable font's interpolation correct by construction.
- Rejected:
  - drawing outlines in a font editor: no editor runs in this environment, and outlines drawn by hand cannot be regenerated when a proportion changes;
  - skia's stroker with boolean union: its output's point structure depends on the numbers, so masters would not interpolate, and it gives no control of joins;
  - METAFONT or MetaPost themselves: they produce bitmaps or need a tracing step (mf2pt1, MetaType1), and neither is installed; the kernel reimplements the two ideas that matter (pen positions, Hobby's spline) in 600 lines with tests;
  - Iosevka's build system: it generates Iosevka's design, and this is a different design.
- Where: `src/rachis/geom.py`, `pen.py`, `glyph.py`, `parts.py`.

## T02 · Monospaced, 600 units to a 1000-unit em (2026-11-14, active)
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

## T05 · One superellipse (2026-11-14, active)
- Decision: every bowl and shoulder is a quadrant whose handles lie at 0.62 of the way to the corner of its box (an ellipse is 0.5523). The centre line has this shape; both sides of the stroke are offsets of it through its midpoint, so a round stroke keeps its breadth around the turn.
- Why: at a 600 advance, squarer rounds enlarge the counters, which is what small print needs, and one constant makes `o`, `n`, `b`, `e`, `0` and `∪` visibly one family.
- Rejected: ellipses (smaller counters at this width); a higher constant (0.70: reads as a rounded rectangle and loses the distinction between `O` and `D`); separate constants for outer and inner contours (the stroke would thin or swell on the diagonal).

## T06 · No ligatures, and nothing contextual (2026-11-14, active)
- Decision: the fonts contain no substitution that replaces two characters by one shape or that changes a glyph because of its neighbours. `calt`, `liga` and `dlig` are absent. The only substitutions are one-for-one alternates the reader asks for (stylistic sets, superiors, inferiors).
- Why: the owner writes in literal language and the typeface does the same: what is on the screen is what is in the file. A ligature shows a character that is not there (`≠` for `!=`), and Unicode has those characters, which this typeface also draws; the two must stay distinguishable. No controlled study compares code read with and without ligatures (a 2023 systematic review of code legibility found none), so there is no measured benefit to weigh against that. Operators are drawn on one axis with one span instead, so `->` leaves 132 units of white between the bar and the chevron and reads as an arrow without being one glyph.
- Rejected: Fira Code style ligatures; cell-preserving joins in `calt` (they keep the character count but make adjacent hyphens uncountable and depend on shaping support that terminals implement unevenly); texture healing (Monaspace: it evens the rhythm of prose, but it is contextual, and it needs alternates for most of the alphabet; ledger I1).

## T07 · Told apart by outline, and measured (2026-11-15, active)
- Decision: confusable characters differ in outline before they differ in an inner mark. `0` is narrower than `O` and its slash stays inside the counter; `D` is flat-backed; `1` has a flag and a foot, `l` a slab and a foot to the right, `I` two serifs, `|` no serif and the height of a bracket; `q` has a foot where `g` has a hook. Each pair is measured with the distance in `measure.py` against reference typefaces, and the build fails if a gate is missed.
- Why: under the blur of reading size, Bouma found that "inner parts are weak cues at best"; three screen typefaces that mark their zero still score 0.14 to 0.22 on `0`/`O` because the outlines coincide, while an unmarked but narrow zero scores 0.31. The pairs behind most real transcription errors are `l 1`, `O 0`, `Z 2`, `1 7` (Bell Laboratories, via Grissinger 2017).
- Rejected: a dotted zero as the default (at small sizes it reads as `8`: Hunt conceded this for Source Code Pro); a slash that crosses the ring (it is `∅` and `Ø`, which a mathematics user needs to tell from zero); figures shorter than capitals (Lucida Console relied on height alone in 1993 and added the slash in 2013).

## T08 · A weight axis from 300 to 700, and an italic that slants skeletons (2026-11-15, active)
- Decision: three masters (Light 300, Regular 400, Bold 700) make a variable font; a second variable font is the italic. The italic shears the skeleton by 10° and leaves the pen as it was, so stems keep their horizontal thickness, bars their vertical thickness and curves their breadth. Static instances are Light, Regular, Medium, SemiBold and Bold in both.
- Why: no study measures the best stroke weight for light text on dark, and readers differ by 35% in which typeface they read fastest (Wallace et al. 2022), so the weight is the reader's to set. Stems of 66 to 134 stay inside the band where reading speed is flat. The median italic angle of 13 code typefaces is 10°. Shearing outlines instead would thin and thicken a round stroke by 9% around the turn.
- Rejected: a slant axis in one file (applications select italics by style linking, which needs a separate italic font); a Thin or Black extreme (outside the band, and a 600 cell cannot hold a Black `m`); a cursive italic with a single-storey `a` (misread as `o` and `q`: Beier and Larson 2010).

## T09 · One line box on every platform (2026-11-15, active)
- Decision: the line is 1250 units: 980 above the baseline, 270 below, with no line gap. The hhea, typo and win metrics agree and `USE_TYPO_METRICS` is set. Box-drawing glyphs fill that box exactly.
- Why: terminals take the cell's height from these tables, and they do not agree on which; equal values give the same cell everywhere. 1.25 is the median default of 16 code typefaces and what Iosevka builds; JetBrains and Input recommend 1.2.
- Rejected: a tighter box (accented capitals reach 940); a line gap (some applications add it above, some below, some ignore it).

## T10 · The fonts are licensed under the SIL Open Font License; the code under Apache-2.0 (2026-11-15, active)
- Decision: files in `fonts/` are under OFL 1.1 (`OFL.txt`), with no Reserved Font Name. The Python source is under the repository's Apache-2.0 licence.
- Why: the OFL is what font users and distributors expect and what lets the fonts be embedded and bundled; the generator is ordinary software.
- Rejected: OFL for the source as well (it has terms written for fonts, not programs); a Reserved Font Name (it forbids even a subsetted web font from keeping the name).
