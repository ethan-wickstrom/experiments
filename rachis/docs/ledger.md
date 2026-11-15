# Ledger

Every open item of the typeface (a gap, an idea, a deferral, a question, a request to the owner) and every closed one with its resolution. An entry's status changes in the same commit as the change that affects it; entries are closed, never deleted. G is a gap in what exists, I an idea not started, REQ a request to the owner.

## Open

### Gaps

- **G1 · 88 gates of `measurements.md` fail** across the three Regulars (2026-11-15). The gates are the research's targets, and several are above what any reference typeface reaches. The ones that are design work, with the fixed pitch's distance at 14 px and a blur of 1 px: `1 I` 0.223 (gate 0.40; the references score 0.23 to 0.42; three serif lengths of `I` were measured, 196, 150 and 120 units, giving 0.223, 0.195 and 0.226, so the lever is the foot of `1`, not the serifs), `O D` 0.168, `0 8` 0.183, `5 S` 0.200, `8 B` 0.222, `g q` 0.317, `u υ` 0.130, `p ρ` 0.117, `∨ v` 0.143, `− –` 0.115, `⟨ (` 0.182. The double-struck letters against their plain letters (`ℝ R` 0.166) fail a default gate of 0.25 that was set without evidence; that gate needs a reason or removal. `rachis measure --gate` exits 1 until this is settled, and is not among the checks.
- **G2 · Kerning and mark anchors do not vary across the design space.** They are computed at the Regular of the text size and applied at every weight and optical size (T17, T20). The compiler would store per-master values as deltas; `kern::values` already computes them per master.
- **G3 · A few glyphs of some static fonts keep overlapping contours**, because the boolean union went wrong on them and the raster check caught it (T23): 42 glyph instances of 51,670 on 2026-11-15, listed by `rachis build`. Moving the contours apart by a hair, and uniting them one at a time, were tried and cured none.
- **G4 · Glyphs their authors called weak**, to be redrawn: `⎈ ⎋ ⌘ ⌨` in the Bold; `⅒`; `ₘ ᵐ` at 13 px in the Bold; subscripts with descenders reach −272, below the line box; `℘ ℜ 𝕎 𝕨 ℑ ℅`; `ϑ Ϗ ν`; `⇔ ⇕ ⟺` in the Bold at 13 to 16 px, `↝ ↜ ↭ ⇴ ⇼ ↠` in the Bold; `⊰ ⊱ ≼ ≽ ⋞ ⋟ ⟕ ⟖ ⟗ ⩴ ⋎ ⊜ ∜`; `æ` in the fixed pitch, `ð`, `Ǻ ǻ`, the cedilla's hook; the control pictures, `₧ ₨ ✂ ❅ ₾`; the Powerline branch sign at 13 px, the spinner frames, the shades at 13 to 14 px. `ϵ` and `∈` are close at 13 px.
- **G5 · Characters of the coverage survey that are not drawn**: 204 of the 873 of tier 2 (`research/`; tier 1's 1405 are all drawn): Cyrillic (124); arrows `⤊ ⤋ ⟰ ⟱ ⇮ ⇯ ⇶ ↫ ↬ ↯ ➦ ⟴`; the script capitals `ℊ ℋ ℐ ℒ ℛ ℬ ℰ ℱ ℳ ℴ 𝒫`, the Fraktur `ℌ ℨ ℭ`, `ℼ ⅀ ℶ ℷ ℸ`, the Ångström sign; the three-letter control pictures (20), `₯ ☈`; `⎉ ⟅ ⟆`; U+034D; `ϐ` and the archaic Greek numerals; the Roman numerals `Ⅰ` to `Ⅵ`, `↊ ↋`; the enclosed letters.
- **G6 · Box drawing at small sizes.** Where a line's edge falls part-way across a pixel, the overshoot of two neighbouring cells covers it twice and the join shows as a darker bead (T22); the shades alias into a plaid at 13 to 17 px. Hinting the lines to the pixel grid would cure the first.
- **G7 · Hinting.** The static fonts are hinted by ttfautohint and have been looked at only through FreeType; nothing has been looked at on Windows. The variable fonts are unhinted.
- **G8 · fontbakery has not been run on the final fonts.** It was run on the fixed pitch when it had 857 glyphs: the three FAILs then (no code page covered, Greek capitals without lowercase, glyphs below the win descent) should be cleared by the Latin and Greek letters and the line box of T13, which is unverified. The OpenType sanitiser accepts all 38 files.
- **G9 · The proportional family's details.** The ellipsis keeps the cell; parentheses, brackets and braces are the fixed pitch's shapes, wide for a text face; `ď ľ ť` are loose; the Greek letters' widths are stated as cells (`Fit::letter`), not as sidebearings and ink; the three-per-em and other spaces are not kerned against.
- **G10 · Proofing coverage.** The Small masters and the Text Light and Bold were looked at as lines of text, not glyph by glyph; many glyphs drawn on 2026-11-15 were proofed in the Regular and the Bold of the fixed pitch only (each module's author listed what was not proofed).
- **G11 · The proof tool draws a zero-advance mark in the cell after its base**, so bare combining marks cannot be proofed in place.
- **G12 · `rachis check` notes every empty glyph and every overhang of the proportional family** (440 notes), which hides a note that matters.

- **G13 · The specimen page's table of pairs is copied by hand** from `measurements.md` (`specimen/specimen.html`, the `PAIRS` constant), as are the build's figures in its terminal block; they go stale when shapes change. `rachis specimen` should compute them.

### Ideas

- **I1 · An OpenType MATH table** (T25): constants, italic corrections, accent attachment, and delimiters, radicals and integrals of any size made by running their programs at other heights.
- **I2 · Apertures as a parameter**, more open at the small optical size.
- **I3 · A cursive italic** as a stylistic set, for emphasis in prose (T08 keeps the sloped roman as the default).
- **I4 · Case-sensitive forms** (`case`), fractions from figures (`frac`), old-style figures.
- **I5 · A live builder in the specimen**: the kernel compiled to WebAssembly, drawing a glyph as its parameters are moved.
- **I6 · Proportional figures** (`pnum`) for the proportional family (T19).
- **I7 · Texture healing** in the fixed pitch (T06 rejects it as contextual; recorded because it is the known alternative).
- **I8 · Cyrillic** (G5).

### Requests to the owner

None.

## Closed

- **The Python prototype** is deleted (T11); it is in the history up to commit `1492c96`.
- **The name** was checked for collisions (T24).
- **Glyph coverage of tier 1** of the survey is complete: 1405 characters.
